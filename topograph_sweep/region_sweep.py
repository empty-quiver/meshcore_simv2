#!/usr/bin/env python3
"""Run feature matrix against a pre-generated regional test config.

For each (region × feature × seed), clone the base test config, override
alice's firmware to fw_topo (if the feature needs it), inject the feature's
pre-commands, and run the orchestrator. Aggregate into a CSV.
"""
import argparse
import concurrent.futures as cf
import copy
import json
import os
import re
import subprocess
import time

SIM_ROOT = "/home/eve/meshcore_simv2"
ORCHESTRATOR = f"{SIM_ROOT}/build/orchestrator/orchestrator"
OUT_DIR = "/tmp/region_sweep_out"

FEATURES = {
    "baseline":    (None, []),
    "passive":     ("fw_topo", []),
    "passive_c120": ("fw_topo", [{"command": "confidence 120"}]),
    "probes_on":   ("fw_topo", [{"command": "probes on"}]),
    "probes_c120": ("fw_topo", [{"command": "confidence 120"}, {"command": "probes on"}]),
}

REGIONS = ["gdansk", "seapdx", "manh"]

METRIC_RE = {
    "radio_tx":   re.compile(r"Radio: (\d+) TX"),
    "radio_rx":   re.compile(r"Radio: \d+ TX, (\d+) RX"),
    "collisions": re.compile(r"Radio: \d+ TX, \d+ RX, (\d+) collision"),
    "ackpath_tx": re.compile(r"ACK\+path radio: (\d+) TX"),
    "delivered":  re.compile(r"Delivery: (\d+)/(\d+) messages"),
}

def parse(out):
    m = {}
    for k, rx in METRIC_RE.items():
        hit = rx.search(out)
        if hit:
            if k == "delivered":
                m["delivered"] = int(hit.group(1)); m["sent"] = int(hit.group(2))
            else:
                m[k] = int(hit.group(1))
    probes = 0
    alice_flood = alice_direct = 0
    tfx = tdx = 0
    for line in out.splitlines():
        if "[TOPO-probe" in line and "fired trace" in line:
            probes += 1
        if "node_stats" in line and "sent_flood" in line and '"node":"alice"' in line:
            try:
                j = json.loads(line)
                alice_flood = j.get("sent_flood", 0)
                alice_direct = j.get("sent_direct", 0)
            except: pass
        if "node_stats" in line and "flood_tx" in line:
            try:
                j = json.loads(line)
                if j.get("stats_type") == "packets":
                    d = j["data"]
                    tfx += d.get("flood_tx", 0); tdx += d.get("direct_tx", 0)
            except: pass
    m["probes_fired"] = probes
    m["alice_flood"] = alice_flood
    m["alice_direct"] = alice_direct
    m["total_flood_tx"] = tfx
    m["total_direct_tx"] = tdx
    return m

def build_variant(region, feature, seed):
    base_path = f"{SIM_ROOT}/simulation/{region}_test.json"
    with open(base_path) as f:
        cfg = json.load(f)
    fw, pre_cmds = FEATURES[feature]
    cfg = copy.deepcopy(cfg)
    cfg["_name"] = f"reg_{region}_{feature}_s{seed}"
    cfg["simulation"]["seed"] = seed
    # Override alice firmware
    if fw:
        for n in cfg["nodes"]:
            if n["name"] == "alice":
                n["firmware"] = fw
        cfg["_requires_plugins"] = [fw]
    # Inject pre-commands at t=3000
    pre = [{"at_ms": 3000, "node": "alice", "command": c["command"]} for c in pre_cmds]
    cfg["commands"] = pre + cfg.get("commands", [])
    cfg["commands"].sort(key=lambda c: c["at_ms"])
    out_path = f"{OUT_DIR}/{cfg['_name']}.json"
    with open(out_path, "w") as f:
        json.dump(cfg, f, indent=2); f.write("\n")
    return out_path

def run(path):
    t0 = time.time()
    try:
        r = subprocess.run([ORCHESTRATOR, path], capture_output=True, text=True,
                           timeout=900, cwd=SIM_ROOT)
        m = parse(r.stdout + r.stderr)
        m["wall_s"] = time.time() - t0
        m["rc"] = r.returncode
        return m
    except subprocess.TimeoutExpired:
        return {"rc": -1, "error": "timeout", "wall_s": time.time() - t0}
    except Exception as e:
        return {"rc": -2, "error": str(e), "wall_s": time.time() - t0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)   # big regional runs; keep lower
    ap.add_argument("--regions", default=",".join(REGIONS))
    ap.add_argument("--features", default=",".join(FEATURES.keys()))
    ap.add_argument("--seeds", default="42,101,202")
    ap.add_argument("--csv", default="/tmp/region_results.csv")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    combos = []
    for r in args.regions.split(","):
        for f in args.features.split(","):
            for s in args.seeds.split(","):
                combos.append((r, f, int(s)))
    print(f"{len(combos)} runs, {args.workers} workers")

    paths = [(r, f, s, build_variant(r, f, s)) for (r, f, s) in combos]
    results = []
    t_start = time.time()
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run, p[3]): p for p in paths}
        for fut in cf.as_completed(futs):
            r, f, s, _ = futs[fut]
            m = fut.result()
            m.update({"region": r, "feature": f, "seed": s})
            results.append(m)
            print(f"[{len(results)}/{len(combos)}] {r}/{f}/s{s}  "
                  f"rc={m.get('rc')} del={m.get('delivered','?')}/{m.get('sent','?')} "
                  f"tx={m.get('radio_tx','?')} t={m.get('wall_s',0):.1f}s "
                  f"elapsed={time.time()-t_start:.0f}s")
    cols = ["region", "feature", "seed", "delivered", "sent",
            "alice_flood", "alice_direct", "radio_tx", "radio_rx", "collisions",
            "ackpath_tx", "total_flood_tx", "total_direct_tx", "probes_fired",
            "wall_s", "rc"]
    with open(args.csv, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in results:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"wrote {args.csv}")

if __name__ == "__main__":
    main()
