#!/usr/bin/env python3
"""Parallel sweep harness for TopoGraph A/B testing on simv2.

Generates JSON configs for (topology × workload × feature) and runs them
in parallel via ProcessPoolExecutor. Parses output, emits CSV summary.
"""
import argparse
import concurrent.futures as cf
import copy
import json
import os
import re
import subprocess
import sys
import time

SIM_ROOT = "/home/eve/meshcore_simv2"
ORCHESTRATOR = f"{SIM_ROOT}/build/orchestrator/orchestrator"
OUT_DIR = "/tmp/sweep_out"

# ---- topology builders ----

def topo_chain(n_repeaters=4, chain_snr=10, bridge=None):
    """alice — R1 — R2 — ... — Rn — frank, optional long-range bridge."""
    nodes = [{"name": "alice", "role": "companion"}]
    for i in range(n_repeaters):
        nodes.append({"name": f"R{i}", "role": "repeater"})
    nodes.append({"name": "frank", "role": "companion"})

    links = [{"from": "alice", "to": "R0", "snr": chain_snr, "rssi": -70}]
    for i in range(n_repeaters - 1):
        links.append({"from": f"R{i}", "to": f"R{i+1}", "snr": chain_snr, "rssi": -70})
    links.append({"from": f"R{n_repeaters-1}", "to": "frank", "snr": chain_snr, "rssi": -70})
    if bridge:
        a, b, snr = bridge
        links.append({"from": a, "to": b, "snr": snr, "rssi": -90})
    return nodes, links

def topo_grid(rows, cols, n_companions=4, neighbor_snr=8, diag_snr=4):
    nodes = []
    for r in range(rows):
        for c in range(cols):
            nodes.append({"name": f"r{r}_{c}", "role": "repeater"})
    # Companions at corners / midpoints
    corners = [(0,0), (0, cols-1), (rows-1, cols-1), (rows-1, 0)]
    companion_names = ["alice", "bob", "carol", "dave", "eve", "frank"]
    positions = corners[:min(n_companions, 4)]
    links = []
    for r in range(rows):
        for c in range(cols):
            if c+1 < cols:
                links.append({"from": f"r{r}_{c}", "to": f"r{r}_{c+1}", "snr": neighbor_snr, "rssi": -80})
            if r+1 < rows:
                links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c}", "snr": neighbor_snr, "rssi": -80})
            if r+1 < rows and c+1 < cols:
                links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c+1}", "snr": diag_snr, "rssi": -95})
            if r+1 < rows and c-1 >= 0:
                links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c-1}", "snr": diag_snr, "rssi": -95})
    for i, (r, c) in enumerate(positions):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": f"r{r}_{c}", "snr": neighbor_snr, "rssi": -80})
    return nodes, links

def topo_star(n_spokes=5, spoke_snr=8):
    """Central repeater hub with N companions around it (1-hop topology)."""
    nodes = [{"name": "hub", "role": "repeater"}]
    companion_names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo"]
    links = []
    for i in range(n_spokes):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hub", "snr": spoke_snr, "rssi": -80})
    return nodes, links

TOPOLOGIES = {
    "chain_6":       lambda: topo_chain(n_repeaters=4, chain_snr=10,
                                         bridge=("R0", "R3", 3)),
    "chain_10":      lambda: topo_chain(n_repeaters=8, chain_snr=10),
    "grid_3x3":      lambda: topo_grid(3, 3, n_companions=4, neighbor_snr=8),
    "grid_5x5":      lambda: topo_grid(5, 5, n_companions=4, neighbor_snr=8),
    "star_5":        lambda: topo_star(n_spokes=5, spoke_snr=8),
    "star_8":        lambda: topo_star(n_spokes=8, spoke_snr=8),
}

# ---- workload builders ----

def workload_light(peers):
    """3 messages from alice to distant peers, late in sim."""
    return [
        {"at_ms": 540000, "node": "alice", "command": f"msg {peers[0]} ping1"},
        {"at_ms": 570000, "node": "alice", "command": f"msg {peers[1]} ping2"} if len(peers) > 1 else None,
        {"at_ms": 600000, "node": "alice", "command": f"msg {peers[2]} ping3"} if len(peers) > 2 else None,
    ]

def workload_burst(peers):
    """Bursty: 6 messages to 1 peer in quick succession."""
    peer = peers[0]
    return [{"at_ms": 540000 + 15000*i, "node": "alice", "command": f"msg {peer} burst{i}"} for i in range(6)]

def workload_heavy(peers):
    """Many messages spread across all peers."""
    out = []
    t = 400000
    for i in range(12):
        peer = peers[i % len(peers)]
        out.append({"at_ms": t, "node": "alice", "command": f"msg {peer} heavy{i}"})
        t += 25000
    return out

WORKLOADS = {
    "light": workload_light,
    "burst": workload_burst,
    "heavy": workload_heavy,
}

# ---- feature variants ----

FEATURES = {
    # name: (firmware, pre-commands before adverts)
    "baseline":     (None,       []),
    "passive":      ("fw_topo",  []),
    "probes_on":    ("fw_topo",  [{"at_ms": 3000, "node": "alice", "command": "probes on"}]),
}

# ---- advert schedules ----

def adverts_medium(companion_names, repeater_names):
    """Moderate: 4 advert rounds from all companions."""
    cmds = []
    t = 30000
    for round_ in range(4):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += 120000
    return cmds

# ---- config assembly ----

def build_config(topo_name, workload_name, feature_name, duration_ms=700000, seed=42):
    nodes, links = TOPOLOGIES[topo_name]()
    comp_names = [n["name"] for n in nodes if n["role"] == "companion"]
    rep_names  = [n["name"] for n in nodes if n["role"] == "repeater"]
    peers = [n for n in comp_names if n != "alice"]
    if not peers:
        raise ValueError(f"{topo_name}: no non-alice companions")

    fw, pre_cmds = FEATURES[feature_name]
    nodes2 = copy.deepcopy(nodes)
    for n in nodes2:
        if fw and n["name"] == "alice":
            n["firmware"] = fw

    cmds = []
    if fw:
        cmds.extend(copy.deepcopy(pre_cmds))
    cmds.extend(adverts_medium(comp_names, rep_names))
    wl = [c for c in WORKLOADS[workload_name](peers) if c is not None]
    cmds.extend(wl)
    cmds.sort(key=lambda c: c["at_ms"])

    cfg = {
        "_name": f"sweep_{topo_name}_{workload_name}_{feature_name}",
        "_desc": f"Sweep: {topo_name} / {workload_name} / {feature_name}",
        "simulation": {
            "duration_ms": duration_ms, "step_ms": 4, "warmup_ms": 10000,
            "hot_start": False, "seed": seed,
        },
        "nodes": nodes2,
        "topology": {"links": links},
        "commands": cmds,
        "expect": [],
    }
    if fw:
        cfg["_requires_plugins"] = [fw]
    return cfg

# ---- runner ----

METRIC_RE = {
    "radio_tx":     re.compile(r"Radio: (\d+) TX"),
    "radio_rx":     re.compile(r"Radio: \d+ TX, (\d+) RX"),
    "collisions":   re.compile(r"Radio: \d+ TX, \d+ RX, (\d+) collision"),
    "ackpath_tx":   re.compile(r"ACK\+path radio: (\d+) TX"),
    "delivered":    re.compile(r"Delivery: (\d+)/(\d+) messages"),
}

def parse_metrics(out):
    m = {}
    for k, rx in METRIC_RE.items():
        mm = rx.search(out)
        if mm:
            if k == "delivered":
                m["delivered"] = int(mm.group(1))
                m["sent"] = int(mm.group(2))
            else:
                m[k] = int(mm.group(1))
    # per-node totals
    tfx = tdx = 0; alice_flood = alice_direct = 0; probes_fired = 0
    for line in out.splitlines():
        if "[TOPO-probe" in line and "fired trace" in line:
            probes_fired += 1
        if "node_stats" not in line:
            continue
        try:
            j = json.loads(line)
            if "flood_tx" in line and j.get("stats_type") == "packets":
                d = j["data"]
                tfx += d.get("flood_tx", 0); tdx += d.get("direct_tx", 0)
            elif j.get("node") == "alice" and "sent_flood" in line:
                alice_flood = j.get("sent_flood", 0)
                alice_direct = j.get("sent_direct", 0)
        except Exception:
            pass
    m["total_flood_tx"] = tfx
    m["total_direct_tx"] = tdx
    m["alice_flood"] = alice_flood
    m["alice_direct"] = alice_direct
    m["probes_fired"] = probes_fired
    return m

def run_single(cfg_path):
    t0 = time.time()
    try:
        r = subprocess.run([ORCHESTRATOR, cfg_path], capture_output=True,
                           text=True, timeout=1800, cwd=SIM_ROOT)
        out = r.stdout + r.stderr
        m = parse_metrics(out)
        m["wall_s"] = time.time() - t0
        m["rc"] = r.returncode
        return m
    except subprocess.TimeoutExpired:
        return {"rc": -1, "error": "timeout", "wall_s": time.time() - t0}
    except Exception as e:
        return {"rc": -2, "error": str(e), "wall_s": time.time() - t0}

# ---- main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--duration", type=int, default=700000)
    ap.add_argument("--topologies", default="chain_6,chain_10,grid_3x3,grid_5x5,star_5,star_8")
    ap.add_argument("--workloads",  default="light,burst,heavy")
    ap.add_argument("--features",   default="baseline,passive,probes_on")
    ap.add_argument("--seeds",      default="42")
    ap.add_argument("--csv",        default="/tmp/sweep_results.csv")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    combos = []
    for topo in args.topologies.split(","):
        for wl in args.workloads.split(","):
            for feat in args.features.split(","):
                for seed in args.seeds.split(","):
                    combos.append((topo, wl, feat, int(seed)))
    print(f"{len(combos)} configs, {args.workers} workers")

    # Generate configs
    config_paths = []
    for topo, wl, feat, seed in combos:
        cfg = build_config(topo, wl, feat, duration_ms=args.duration, seed=seed)
        path = f"{OUT_DIR}/{cfg['_name']}_s{seed}.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2); f.write("\n")
        config_paths.append((topo, wl, feat, seed, path))

    # Parallel run
    results = []
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_single, p[4]): p for p in config_paths}
        done = 0
        for fut in cf.as_completed(futures):
            topo, wl, feat, seed, path = futures[fut]
            m = fut.result()
            m.update({"topology": topo, "workload": wl, "feature": feat, "seed": seed})
            results.append(m)
            done += 1
            print(f"[{done}/{len(combos)}] {topo}/{wl}/{feat} seed={seed} "
                  f"rc={m.get('rc')} del={m.get('delivered','?')}/{m.get('sent','?')} "
                  f"tx={m.get('radio_tx','?')} t={m.get('wall_s',0):.1f}s")

    # CSV dump
    cols = ["topology", "workload", "feature", "seed",
            "delivered", "sent", "alice_flood", "alice_direct",
            "radio_tx", "radio_rx", "collisions", "ackpath_tx",
            "total_flood_tx", "total_direct_tx", "probes_fired",
            "wall_s", "rc"]
    with open(args.csv, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in results:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"wrote {args.csv}")

if __name__ == "__main__":
    main()
