#!/usr/bin/env python3
"""Slice by advert cadence to see its interaction with features."""
import csv, statistics, sys
from collections import defaultdict

def load(p):
    rows=[]
    with open(p) as f:
        for r in csv.DictReader(f):
            for k,v in list(r.items()):
                if v=="" or v is None: r[k]=None
                elif k=="seed": r[k]=int(v)
                else:
                    try: r[k]=int(v)
                    except:
                        try: r[k]=float(v)
                        except: pass
            rows.append(r)
    return rows

def main():
    path=sys.argv[1] if len(sys.argv)>1 else "/tmp/sweep_v3.csv"
    rows=[r for r in load(path) if r.get("rc")==0]
    # avg across seeds, keep advert dimension
    g=defaultdict(list)
    for r in rows:
        k=(r["topology"],r["workload"],r["advert"],r["feature"])
        g[k].append(r)
    agg={}
    for k,items in g.items():
        agg[k]={
            "del": statistics.mean(x["delivered"] for x in items if x.get("delivered") is not None) if any(x.get("delivered") is not None for x in items) else None,
            "sent": statistics.mean(x["sent"] for x in items if x.get("sent") is not None) if any(x.get("sent") is not None for x in items) else None,
            "tx": statistics.mean(x["radio_tx"] for x in items if x.get("radio_tx") is not None) if any(x.get("radio_tx") is not None for x in items) else None,
        }

    topos = sorted({k[0] for k in agg})
    wls   = sorted({k[1] for k in agg})
    advs  = sorted({k[2] for k in agg})

    # For each feature, for each advert cadence, grand summary
    feats = sorted({k[3] for k in agg})

    for feat in feats:
        if feat == "baseline": continue
        print(f"\n=== {feat} vs baseline, SLICED BY ADVERT CADENCE ===")
        print(f"  {'advert':<10} {'n':>4} {'Δtx%(med)':>10} {'Δdel_pp(med)':>13} {'Δdel_pp(mean)':>14} {'wins':>5} {'loss':>5}")
        for adv in advs:
            dtxs, ddels = [], []
            wins=losses=0
            for t in topos:
                for w in wls:
                    b=agg.get((t,w,adv,"baseline"))
                    r=agg.get((t,w,adv,feat))
                    if not b or not r or not b.get("sent") or not b.get("tx"): continue
                    dtx = 100*(r["tx"]-b["tx"])/b["tx"]
                    dtxs.append(dtx)
                    bd = b["del"]/b["sent"]
                    rd = r["del"]/r["sent"] if r["sent"] else 0
                    dd = 100*(rd-bd)
                    ddels.append(dd)
                    if dd > 5: wins += 1
                    elif dd < -5: losses += 1
            if not dtxs: continue
            print(f"  {adv:<10} {len(dtxs):>4} {statistics.median(dtxs):>+10.1f} "
                  f"{statistics.median(ddels):>+13.1f} {statistics.mean(ddels):>+14.1f} "
                  f"{wins:>5} {losses:>5}")

    # Long chain + probes: the standout cell from v2
    print(f"\n\n=== LONG CHAIN (chain_15) BEHAVIOR ACROSS FEATURES × ADVERT × WORKLOAD ===")
    for adv in advs:
        print(f"\n-- advert={adv} --")
        print(f"  {'feature':<15} " + "".join(f"{w:>10}" for w in wls))
        for feat in feats:
            line=f"  {feat:<15}"
            for w in wls:
                b=agg.get(("chain_15",w,adv,"baseline"))
                r=agg.get(("chain_15",w,adv,feat))
                if not b or not r or not b.get("sent") or not r.get("sent"):
                    line += f"{'---':>10}"
                    continue
                bd=100*b["del"]/b["sent"]; rd=100*r["del"]/r["sent"]
                dd=rd-bd
                line += f"{rd:>6.0f}%{dd:>+4.0f}"
            print(line)

if __name__=="__main__": main()
