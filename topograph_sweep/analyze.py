#!/usr/bin/env python3
"""Aggregate sweep_v1.csv — compare baseline / passive / probes_on per topology×workload."""
import csv
import statistics
from collections import defaultdict

def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            for k, v in list(r.items()):
                if v == "" or v is None: r[k] = None
                elif k in ("seed",):
                    r[k] = int(v)
                else:
                    try: r[k] = int(v)
                    except Exception:
                        try: r[k] = float(v)
                        except Exception: pass
            rows.append(r)
    return rows

def agg(rows):
    """group by (topo, wl, feat); average across seeds."""
    groups = defaultdict(list)
    for r in rows:
        k = (r["topology"], r["workload"], r["feature"])
        groups[k].append(r)
    out = {}
    for k, items in groups.items():
        out[k] = {
            "n": len(items),
            "delivered": statistics.mean(x["delivered"] for x in items if x.get("delivered") is not None),
            "sent":      statistics.mean(x["sent"]      for x in items if x.get("sent")      is not None),
            "radio_tx":  statistics.mean(x["radio_tx"]  for x in items if x.get("radio_tx")  is not None),
            "collisions": statistics.mean(x["collisions"] for x in items if x.get("collisions") is not None),
            "alice_flood": statistics.mean(x["alice_flood"] for x in items if x.get("alice_flood") is not None),
            "alice_direct": statistics.mean(x["alice_direct"] for x in items if x.get("alice_direct") is not None),
            "probes_fired": statistics.mean(x["probes_fired"] for x in items if x.get("probes_fired") is not None),
            "ackpath_tx": statistics.mean(x["ackpath_tx"] for x in items if x.get("ackpath_tx") is not None),
        }
    return out

def main():
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sweep_v1.csv"
    rows = load(path)
    g = agg(rows)

    topos = sorted({k[0] for k in g})
    wls   = sorted({k[1] for k in g})
    feats = ["baseline", "passive", "probes_on"]

    # Summary table: per-topology, per-workload comparison
    print(f"{'topo':<10} {'wl':<6} {'feat':<10} {'del':>6} {'tx':>5} {'col':>5} {'af':>4} {'ad':>4} {'pf':>3}  {'Δtx%':>6} {'Δcol%':>6} {'Δdel':>6}")
    print("-"*100)
    for topo in topos:
        for wl in wls:
            base = g.get((topo, wl, "baseline"))
            if not base: continue
            for feat in feats:
                row = g.get((topo, wl, feat))
                if not row: continue
                dtx = 100*(row["radio_tx"] - base["radio_tx"]) / base["radio_tx"] if base["radio_tx"] else 0
                dcol = 100*(row["collisions"] - base["collisions"]) / base["collisions"] if base["collisions"] else 0
                ddel_pct = 100*(row["delivered"]/row["sent"] - base["delivered"]/base["sent"]) if base["sent"] and row["sent"] else 0
                print(f"{topo:<10} {wl:<6} {feat:<10} "
                      f"{row['delivered']:>4.1f}/{row['sent']:<2.0f} {row['radio_tx']:>5.0f} {row['collisions']:>5.0f} "
                      f"{row['alice_flood']:>4.1f} {row['alice_direct']:>4.1f} {row['probes_fired']:>3.1f}  "
                      f"{dtx:>+6.1f} {dcol:>+6.1f} {ddel_pct:>+5.1f}%")
            print()

    # Grand summary: passive vs baseline, probes_on vs baseline, across all configs
    def delta_summary(feat):
        dtxs, dcols, ddels = [], [], []
        for topo in topos:
            for wl in wls:
                base = g.get((topo, wl, "baseline"))
                row  = g.get((topo, wl, feat))
                if not base or not row or not base["radio_tx"] or not base["sent"]: continue
                dtxs.append(100*(row["radio_tx"] - base["radio_tx"]) / base["radio_tx"])
                dcols.append(100*(row["collisions"] - base["collisions"]) / base["collisions"] if base["collisions"] else 0)
                ddels.append(100*(row["delivered"]/row["sent"] - base["delivered"]/base["sent"]))
        return dtxs, dcols, ddels

    for feat in ("passive", "probes_on"):
        dtxs, dcols, ddels = delta_summary(feat)
        def fmt(xs):
            return f"mean={statistics.mean(xs):+.1f}  med={statistics.median(xs):+.1f}  min={min(xs):+.1f}  max={max(xs):+.1f}"
        print(f"=== {feat} vs baseline (across {len(dtxs)} topo×wl combos) ===")
        print(f"  radio_tx %:    {fmt(dtxs)}")
        print(f"  collisions %:  {fmt(dcols)}")
        print(f"  delivery pp:   {fmt(ddels)}")
        print()

if __name__ == "__main__":
    main()
