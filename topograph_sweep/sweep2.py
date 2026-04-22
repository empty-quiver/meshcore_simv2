#!/usr/bin/env python3
"""Expanded parallel sweep: more topologies, workloads, feature variants.

Features can now include runtime knob-setting commands (confidence, probecool, busyrate).
"""
import argparse
import concurrent.futures as cf
import copy
import itertools
import json
import os
import re
import subprocess
import sys
import time

SIM_ROOT = "/home/eve/meshcore_simv2"
ORCHESTRATOR = f"{SIM_ROOT}/build/orchestrator/orchestrator"
OUT_DIR = "/tmp/sweep_out2"

# =================== TOPOLOGIES ===================

def topo_chain(n_repeaters, chain_snr=10, bridge=None):
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

def topo_grid(rows, cols, n_companions=4, neighbor_snr=8, diag_snr=4, include_diag=True):
    nodes = []
    for r in range(rows):
        for c in range(cols):
            nodes.append({"name": f"r{r}_{c}", "role": "repeater"})
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
            if include_diag:
                if r+1 < rows and c+1 < cols:
                    links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c+1}", "snr": diag_snr, "rssi": -95})
                if r+1 < rows and c-1 >= 0:
                    links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c-1}", "snr": diag_snr, "rssi": -95})
    for i, (r, c) in enumerate(positions):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": f"r{r}_{c}", "snr": neighbor_snr, "rssi": -80})
    return nodes, links

def topo_star(n_spokes, spoke_snr=8):
    nodes = [{"name": "hub", "role": "repeater"}]
    companion_names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo", "ivan", "jane"]
    links = []
    for i in range(n_spokes):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hub", "snr": spoke_snr, "rssi": -80})
    return nodes, links

def topo_double_star(spokes_per_hub=4, hub_link_snr=8):
    """Two hubs connected, each with N companion spokes."""
    nodes = [
        {"name": "hubA", "role": "repeater"},
        {"name": "hubB", "role": "repeater"},
    ]
    names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo"]
    links = [{"from": "hubA", "to": "hubB", "snr": hub_link_snr, "rssi": -80}]
    for i in range(spokes_per_hub):
        nm = names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hubA", "snr": 8, "rssi": -80})
    for i in range(spokes_per_hub):
        nm = names[spokes_per_hub + i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hubB", "snr": 8, "rssi": -80})
    return nodes, links

def topo_tree(depth=3, fan=2):
    """Binary (or fan-ary) tree of repeaters with companions at leaves and root."""
    nodes = []
    links = []
    def build(name, lvl, parent):
        nodes.append({"name": name, "role": "repeater"})
        if parent is not None:
            links.append({"from": parent, "to": name, "snr": 8, "rssi": -80})
        if lvl < depth:
            for k in range(fan):
                build(f"{name}_{k}", lvl+1, name)
    build("root", 0, None)
    # Alice at root, companions at leaves
    leaves = [n["name"] for n in nodes if n["name"].count("_") == depth]
    names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo", "ivan"]
    # Alice is first companion, attached to root
    nodes.append({"name": "alice", "role": "companion"})
    links.append({"from": "alice", "to": "root", "snr": 8, "rssi": -80})
    for i, leaf in enumerate(leaves[:len(names)-1]):
        nm = names[i+1]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": leaf, "snr": 8, "rssi": -80})
    return nodes, links

TOPOLOGIES = {
    "chain_3":       lambda: topo_chain(2),
    "chain_6":       lambda: topo_chain(4, bridge=("R0", "R3", 3)),
    "chain_10":      lambda: topo_chain(8),
    "chain_15":      lambda: topo_chain(13),
    "grid_3x3":      lambda: topo_grid(3, 3),
    "grid_4x4":      lambda: topo_grid(4, 4),
    "grid_5x5":      lambda: topo_grid(5, 5),
    "grid_3x3_nodiag": lambda: topo_grid(3, 3, include_diag=False),
    "grid_5x5_nodiag": lambda: topo_grid(5, 5, include_diag=False),
    "star_3":        lambda: topo_star(3),
    "star_5":        lambda: topo_star(5),
    "star_8":        lambda: topo_star(8),
    "star_10":       lambda: topo_star(10),
    "dstar_4":       lambda: topo_double_star(4),
    "tree_d3f2":     lambda: topo_tree(depth=3, fan=2),
}

# =================== WORKLOADS ===================

def workload_light(peers):
    return [
        {"at_ms": 540000, "node": "alice", "command": f"msg {peers[0]} m1"},
        {"at_ms": 570000, "node": "alice", "command": f"msg {peers[1%len(peers)]} m2"} if len(peers) > 1 else None,
        {"at_ms": 600000, "node": "alice", "command": f"msg {peers[2%len(peers)]} m3"} if len(peers) > 2 else None,
    ]

def workload_medium(peers):
    out = []; t = 450000
    for i in range(6):
        out.append({"at_ms": t + 25000*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} med{i}"})
    return out

def workload_burst(peers):
    peer = peers[0]
    return [{"at_ms": 540000 + 15000*i, "node": "alice", "command": f"msg {peer} b{i}"} for i in range(6)]

def workload_heavy(peers):
    out = []; t = 400000
    for i in range(12):
        out.append({"at_ms": t + 25000*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} h{i}"})
    return out

def workload_sparse(peers):
    """One message every 2 minutes — like a casual user."""
    out = []; t = 200000
    for i in range(5):
        out.append({"at_ms": t + 120000*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} s{i}"})
    return out

WORKLOADS = {
    "light":  workload_light,
    "medium": workload_medium,
    "burst":  workload_burst,
    "heavy":  workload_heavy,
    "sparse": workload_sparse,
}

# =================== ADVERT SCHEDULES ===================

def adverts_medium(companion_names, _repeater_names):
    cmds = []; t = 30000
    for _ in range(4):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += 120000
    return cmds

def adverts_sparse(companion_names, _repeater_names):
    """Only 2 rounds — models a mesh where adverts are rare."""
    cmds = []; t = 30000
    for _ in range(2):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += 240000
    return cmds

def adverts_frequent(companion_names, _repeater_names):
    cmds = []; t = 30000
    for _ in range(8):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += 60000
    return cmds

ADVERT_SCHEDULES = {
    "medium":   adverts_medium,
    "sparse":   adverts_sparse,
    "frequent": adverts_frequent,
}

# =================== FEATURE VARIANTS ===================
# Each feature is (fw_name_or_None, list of cli commands to run at t=3000)

def feat_baseline():
    return (None, [])

def feat_passive():
    return ("fw_topo", [])

def feat_passive_strict(conf):
    return ("fw_topo", [{"command": f"confidence {conf}"}])

def feat_probes_on():
    return ("fw_topo", [{"command": "probes on"}])

def feat_probes_strict(conf):
    return ("fw_topo", [{"command": f"confidence {conf}"}, {"command": "probes on"}])

FEATURES = {
    "baseline":        feat_baseline,
    "passive":         feat_passive,
    "passive_c60":     lambda: feat_passive_strict(60),
    "passive_c80":     lambda: feat_passive_strict(80),
    "passive_c95":     lambda: feat_passive_strict(95),
    "passive_c100":    lambda: feat_passive_strict(100),
    "passive_c105":    lambda: feat_passive_strict(105),
    "passive_c110":    lambda: feat_passive_strict(110),
    "passive_c120":    lambda: feat_passive_strict(120),
    "passive_c140":    lambda: feat_passive_strict(140),
    "probes_on":       feat_probes_on,
    "probes_c110":     lambda: feat_probes_strict(110),
    "probes_c120":     lambda: feat_probes_strict(120),
    "probes_c140":     lambda: feat_probes_strict(140),
}

# =================== CONFIG ASSEMBLY ===================

def build_config(topo_name, workload_name, feature_name, advert_name="medium",
                 duration_ms=700000, seed=42):
    nodes, links = TOPOLOGIES[topo_name]()
    comp_names = [n["name"] for n in nodes if n["role"] == "companion"]
    rep_names  = [n["name"] for n in nodes if n["role"] == "repeater"]
    peers = [n for n in comp_names if n != "alice"]
    if not peers:
        raise ValueError(f"{topo_name}: no non-alice companions")

    fw, pre_cmds = FEATURES[feature_name]()
    nodes2 = copy.deepcopy(nodes)
    for n in nodes2:
        if fw and n["name"] == "alice":
            n["firmware"] = fw

    cmds = []
    if fw:
        for c in pre_cmds:
            cmds.append({"at_ms": 3000, "node": "alice", "command": c["command"]})
    cmds.extend(ADVERT_SCHEDULES[advert_name](comp_names, rep_names))
    wl = [c for c in WORKLOADS[workload_name](peers) if c is not None]
    cmds.extend(wl)
    cmds.sort(key=lambda c: c["at_ms"])

    cfg = {
        "_name": f"sw_{topo_name}_{workload_name}_{advert_name}_{feature_name}_s{seed}",
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

# =================== RUNNER ===================

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
    tfx = tdx = 0; alice_flood = alice_direct = 0; probes_fired = 0
    for line in out.splitlines():
        if "[TOPO-probe" in line and "fired trace" in line:
            probes_fired += 1
        if "node_stats" not in line: continue
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
                           text=True, timeout=600, cwd=SIM_ROOT)
        out = r.stdout + r.stderr
        m = parse_metrics(out)
        m["wall_s"] = time.time() - t0
        m["rc"] = r.returncode
        return m
    except subprocess.TimeoutExpired:
        return {"rc": -1, "error": "timeout", "wall_s": time.time() - t0}
    except Exception as e:
        return {"rc": -2, "error": str(e), "wall_s": time.time() - t0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--duration", type=int, default=700000)
    ap.add_argument("--topologies", default=",".join(TOPOLOGIES.keys()))
    ap.add_argument("--workloads",  default=",".join(WORKLOADS.keys()))
    ap.add_argument("--features",   default=",".join(FEATURES.keys()))
    ap.add_argument("--adverts",    default="medium")
    ap.add_argument("--seeds",      default="42,101,202")
    ap.add_argument("--csv",        default="/tmp/sweep_results.csv")
    ap.add_argument("--no-run", action="store_true", help="generate configs but do not run")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    combos = []
    for topo in args.topologies.split(","):
        for wl in args.workloads.split(","):
            for adv in args.adverts.split(","):
                for feat in args.features.split(","):
                    for seed in args.seeds.split(","):
                        combos.append((topo, wl, adv, feat, int(seed)))
    print(f"{len(combos)} configs, {args.workers} workers")
    t_start = time.time()

    config_paths = []
    for topo, wl, adv, feat, seed in combos:
        cfg = build_config(topo, wl, feat, advert_name=adv, duration_ms=args.duration, seed=seed)
        path = f"{OUT_DIR}/{cfg['_name']}_{adv}.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2); f.write("\n")
        config_paths.append((topo, wl, adv, feat, seed, path))
    if args.no_run:
        print("configs generated, --no-run specified, exiting")
        return

    results = []
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_single, p[5]): p for p in config_paths}
        done = 0
        for fut in cf.as_completed(futures):
            topo, wl, adv, feat, seed, path = futures[fut]
            m = fut.result()
            m.update({"topology": topo, "workload": wl, "advert": adv, "feature": feat, "seed": seed})
            results.append(m)
            done += 1
            if done % 50 == 0 or done == len(combos):
                print(f"[{done}/{len(combos)}] elapsed={time.time()-t_start:.1f}s")

    cols = ["topology", "workload", "advert", "feature", "seed",
            "delivered", "sent", "alice_flood", "alice_direct",
            "radio_tx", "radio_rx", "collisions", "ackpath_tx",
            "total_flood_tx", "total_direct_tx", "probes_fired",
            "wall_s", "rc"]
    with open(args.csv, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in results:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"wrote {args.csv}  total_wall={time.time()-t_start:.1f}s")

if __name__ == "__main__":
    main()
