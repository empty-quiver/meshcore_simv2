#!/usr/bin/env python3
"""Enhanced analyzer for sweep_v2.csv — handles topology/workload/advert/feature/seed axes.

Produces:
 1. Grand-summary table: each feature's mean/median delta vs baseline (across all configs)
 2. Topology-class summary: group topos into classes (chain/grid/star/etc) and show where
    each feature wins or loses
 3. Heatmap-ish table per feature: (topology × workload) → delivery delta, tx delta
 4. "Where passive/probes WIN" vs "Where passive/probes LOSE" extreme lists
"""
import csv
import statistics
import sys
from collections import defaultdict

def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            for k, v in list(r.items()):
                if v == "" or v is None:
                    r[k] = None
                elif k == "seed":
                    r[k] = int(v)
                else:
                    try: r[k] = int(v)
                    except Exception:
                        try: r[k] = float(v)
                        except Exception: pass
            rows.append(r)
    return rows

def group_by_config(rows):
    """group by (topo, wl, advert, feature); average across seeds."""
    groups = defaultdict(list)
    for r in rows:
        if r.get("rc") != 0: continue
        k = (r["topology"], r["workload"], r.get("advert", "medium"), r["feature"])
        groups[k].append(r)
    out = {}
    for k, items in groups.items():
        out[k] = {}
        for field in ("delivered", "sent", "radio_tx", "radio_rx", "collisions",
                      "ackpath_tx", "total_flood_tx", "total_direct_tx",
                      "alice_flood", "alice_direct", "probes_fired"):
            vals = [x[field] for x in items if x.get(field) is not None]
            if vals: out[k][field] = statistics.mean(vals)
        out[k]["n"] = len(items)
    return out

def topo_class(topo):
    if topo.startswith("chain"):   return "chain"
    if topo.startswith("grid"):    return "grid"
    if topo.startswith("star") or topo.startswith("dstar"): return "star"
    if topo.startswith("tree"):    return "tree"
    return "other"

def fmt_pct(x):
    return f"{x:+.1f}%" if x is not None else "n/a"

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sweep_v2.csv"
    rows = load(path)
    g = group_by_config(rows)
    features = sorted({k[3] for k in g})
    topologies = sorted({k[0] for k in g})
    workloads = sorted({k[1] for k in g})
    adverts = sorted({k[2] for k in g})

    print(f"loaded {len(rows)} rows, {len(g)} unique configs across "
          f"{len(topologies)} topos × {len(workloads)} workloads × "
          f"{len(adverts)} advert schedules × {len(features)} features")
    print(f"features: {features}")
    print()

    # ===== Grand summary per feature =====
    print("=" * 78)
    print("GRAND SUMMARY: each feature's deltas vs baseline, across all configs")
    print("=" * 78)
    for feat in features:
        if feat == "baseline": continue
        dtx, dcol, ddel_pp, n_win, n_loss, n_neutral = [], [], [], 0, 0, 0
        for topo in topologies:
            for wl in workloads:
                for adv in adverts:
                    b = g.get((topo, wl, adv, "baseline"))
                    r = g.get((topo, wl, adv, feat))
                    if not b or not r: continue
                    if not b.get("radio_tx") or not b.get("sent"): continue
                    dtx.append(100 * (r["radio_tx"] - b["radio_tx"]) / b["radio_tx"])
                    if b.get("collisions"):
                        dcol.append(100 * (r["collisions"] - b["collisions"]) / b["collisions"])
                    b_del = b["delivered"] / b["sent"] if b["sent"] else 0
                    r_del = r["delivered"] / r["sent"] if r["sent"] else 0
                    dd = 100 * (r_del - b_del)
                    ddel_pp.append(dd)
                    # Count clear wins/losses
                    if dd < -5: n_loss += 1
                    elif dd > 5: n_win += 1
                    else: n_neutral += 1
        if not dtx:
            print(f"  {feat}: no data"); continue
        def st(xs):
            if not xs: return "n/a"
            return f"mean={statistics.mean(xs):+.1f}  med={statistics.median(xs):+.1f}  p10={sorted(xs)[len(xs)//10]:+.1f}  p90={sorted(xs)[9*len(xs)//10]:+.1f}  min={min(xs):+.1f}  max={max(xs):+.1f}"
        print(f"\n--- {feat} vs baseline (n={len(dtx)} configs) ---")
        print(f"  radio_tx %:    {st(dtx)}")
        print(f"  collisions %:  {st(dcol)}")
        print(f"  delivery pp:   {st(ddel_pp)}")
        print(f"  delivery wins (>+5pp): {n_win}   losses (<-5pp): {n_loss}   neutral: {n_neutral}")
    print()

    # ===== Per-topology-class summary =====
    print("=" * 78)
    print("PER TOPOLOGY CLASS: delivery & tx delta vs baseline")
    print("=" * 78)
    for feat in features:
        if feat == "baseline": continue
        by_class = defaultdict(lambda: {"dtx": [], "ddel_pp": []})
        for topo in topologies:
            cls = topo_class(topo)
            for wl in workloads:
                for adv in adverts:
                    b = g.get((topo, wl, adv, "baseline"))
                    r = g.get((topo, wl, adv, feat))
                    if not b or not r or not b.get("radio_tx") or not b.get("sent"): continue
                    by_class[cls]["dtx"].append(100 * (r["radio_tx"] - b["radio_tx"]) / b["radio_tx"])
                    b_del = b["delivered"] / b["sent"]
                    r_del = r["delivered"] / r["sent"] if r["sent"] else 0
                    by_class[cls]["ddel_pp"].append(100 * (r_del - b_del))
        print(f"\n--- {feat} ---")
        print(f"  {'class':<10} {'n':>4} {'Δtx% (med)':>12} {'Δtx% (mean)':>12} {'Δdel_pp (med)':>14} {'Δdel_pp (mean)':>15}")
        for cls in ("chain", "grid", "star", "tree", "other"):
            d = by_class.get(cls)
            if not d or not d["dtx"]: continue
            print(f"  {cls:<10} {len(d['dtx']):>4} "
                  f"{statistics.median(d['dtx']):>+12.1f} {statistics.mean(d['dtx']):>+12.1f} "
                  f"{statistics.median(d['ddel_pp']):>+14.1f} {statistics.mean(d['ddel_pp']):>+15.1f}")
    print()

    # ===== Full per-topology × workload × feature table =====
    print("=" * 78)
    print("DETAIL: per (topology, workload), delivery % and tx delta for each feature")
    print("=" * 78)
    print(f"{'topo':<18} {'wl':<7} {'feat':<15} {'del%':>7} {'Δdel_pp':>9} {'tx':>6} {'Δtx%':>7} {'col':>6} {'pf':>4}")
    print("-" * 84)
    for topo in topologies:
        for wl in workloads:
            for adv in adverts:
                b = g.get((topo, wl, adv, "baseline"))
                if not b: continue
                b_del_pct = 100 * b["delivered"] / b["sent"] if b["sent"] else 0
                for feat in features:
                    r = g.get((topo, wl, adv, feat))
                    if not r: continue
                    del_pct = 100 * r["delivered"] / r["sent"] if r["sent"] else 0
                    ddel = del_pct - b_del_pct
                    dtx = 100 * (r["radio_tx"] - b["radio_tx"]) / b["radio_tx"] if b.get("radio_tx") else 0
                    print(f"{topo:<18} {wl:<7} {feat:<15} "
                          f"{del_pct:>6.1f}% {ddel:>+8.1f} "
                          f"{r.get('radio_tx',0):>6.0f} {dtx:>+6.1f}% "
                          f"{r.get('collisions',0):>6.0f} {r.get('probes_fired',0):>4.1f}")
                print()

if __name__ == "__main__":
    main()
