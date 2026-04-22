#!/usr/bin/env python3
"""ANSI text heatmap: for a given feature, show (topology × workload) grid
colored by delivery delta vs baseline. Red=worse delivery, green=better,
yellow=tx-heavy."""
import csv
import statistics
import sys
from collections import defaultdict

def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            for k, v in list(r.items()):
                if v == "" or v is None: r[k] = None
                elif k == "seed": r[k] = int(v)
                else:
                    try: r[k] = int(v)
                    except Exception:
                        try: r[k] = float(v)
                        except Exception: pass
            rows.append(r)
    return rows

ANSI = {
    "GREEN":  "\033[42m\033[30m",   # big win
    "lgreen": "\033[102m\033[30m",  # moderate win
    "grey":   "\033[47m\033[30m",   # neutral
    "yellow": "\033[43m\033[30m",   # delivery ok but tx up
    "red":    "\033[41m\033[37m",   # delivery loss
    "RED":    "\033[101m\033[37m",  # big delivery loss
    "reset":  "\033[0m",
}

def color_for(ddel, dtx):
    """Pick a color based on delivery delta (dominant) + tx delta."""
    if ddel is None: return "grey"
    if ddel < -20: return "RED"
    if ddel < -5: return "red"
    if ddel > 15: return "GREEN"
    if ddel > 5: return "lgreen"
    # Neutral delivery — differentiate by tx impact
    if dtx is None: return "grey"
    if dtx < -10: return "GREEN"
    if dtx < -3: return "lgreen"
    if dtx > 10: return "yellow"
    return "grey"

def cell(ddel, dtx):
    c = color_for(ddel, dtx)
    if ddel is None:
        return f"{ANSI[c]}  ---  {ANSI['reset']}"
    return f"{ANSI[c]} {ddel:>+3.0f}%/{dtx:>+3.0f} {ANSI['reset']}"

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sweep_v2.csv"
    rows = load(path)

    groups = defaultdict(list)
    for r in rows:
        if r.get("rc") != 0: continue
        k = (r["topology"], r["workload"], r.get("advert", "medium"), r["feature"])
        groups[k].append(r)

    # For each (topo, wl, adv, feat), compute means
    agg = {}
    for k, items in groups.items():
        agg[k] = {
            "delivered": statistics.mean(x["delivered"] for x in items if x.get("delivered") is not None) if any(x.get("delivered") is not None for x in items) else None,
            "sent":      statistics.mean(x["sent"] for x in items if x.get("sent") is not None) if any(x.get("sent") is not None for x in items) else None,
            "radio_tx":  statistics.mean(x["radio_tx"] for x in items if x.get("radio_tx") is not None) if any(x.get("radio_tx") is not None for x in items) else None,
        }

    topologies = sorted({k[0] for k in agg})
    workloads = sorted({k[1] for k in agg})
    adverts = sorted({k[2] for k in agg})
    features = sorted({k[3] for k in agg})

    for feat in features:
        if feat == "baseline": continue
        for adv in adverts:
            print(f"\n{'='*92}")
            print(f"{feat}  (advert={adv})  vs baseline   —  cell = Δdel_pp / Δtx_pct  (colors: green=win, red=delivery loss, yellow=tx heavy)")
            print(f"{'='*92}")
            # Header row
            print(f"{'topology':<20}" + "".join(f"{wl:^14}" for wl in workloads))
            for topo in topologies:
                line = f"{topo:<20}"
                for wl in workloads:
                    b = agg.get((topo, wl, adv, "baseline"))
                    r = agg.get((topo, wl, adv, feat))
                    if not b or not r or not b.get("sent") or not b.get("radio_tx"):
                        line += cell(None, None)
                        continue
                    b_del = b["delivered"] / b["sent"]
                    r_del = r["delivered"] / r["sent"] if r["sent"] else 0
                    ddel = 100 * (r_del - b_del)
                    dtx = 100 * (r["radio_tx"] - b["radio_tx"]) / b["radio_tx"]
                    line += cell(ddel, dtx)
                print(line)

if __name__ == "__main__":
    main()
