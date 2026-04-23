# Dynamic-topology sweep analysis (sweep_dynamic.csv, 560 runs)

First systematic A/B of TopoGraph under dynamic propagation (drift + shadow + deep fade events every 12s). 4 regions × 7 features × 20 seeds. Paired-by-seed deltas vs baseline, 10k-bootstrap 95% CIs.

## Per-cell table (delivery rate %, paired delta pp, CI, airtime)

```
region   feature                   n   rate%  sd_pp   delta          CI95           tx     dtx   tx/del   ev
gdansk   baseline                 20   36.60   4.86   +0.00   [+0.00, +0.00]      4674      +0   259.44  71.0
gdansk   passive_c120             20   36.60   4.11   +0.00   [-2.80, +2.80]      4793    +120   264.22  71.0
gdansk   passive_c120_probes      20   37.80   6.29   +1.20   [-1.80, +4.30]      4851    +178   262.64  71.0
gdansk   passive_c120_ttl_long    20   36.10   4.83   -0.50   [-3.30, +1.90]      4779    +105   268.36  71.0
gdansk   passive_c120_ttl_short   20   39.80   5.15   +3.20   [+0.30, +6.30]      4893    +219   249.22  71.0
gdansk   passive_c40              20   29.20   5.60   -7.40  [-10.20, -4.40]      4089    -585   287.24  71.0
gdansk   passive_c40_probes       20   28.60   5.88   -8.00  [-10.90, -5.00]      4130    -544   299.58  71.0

manh     baseline                 20   41.00   5.68   +0.00   [+0.00, +0.00]      9465      +0   468.62  71.0
manh     passive_c120             20   39.50   4.72   -1.50   [-4.80, +1.70]      9341    -124   478.08  71.0
manh     passive_c120_probes      20   40.90   6.07   -0.10   [-3.50, +3.40]      9526     +61   473.07  71.0
manh     passive_c120_ttl_long    20   39.50   5.15   -1.50   [-4.40, +1.60]      9499     +34   487.68  71.0
manh     passive_c120_ttl_short   20   41.20   5.37   +0.20   [-2.90, +3.30]      9534     +68   469.85  71.0
manh     passive_c40              20   28.30   5.36  -12.70  [-16.30, -9.40]      7931   -1534   575.04  71.0
manh     passive_c40_probes       20   29.10   6.54  -11.90  [-15.40, -8.50]      7945   -1520   567.37  71.0

seapdx   baseline                 20   44.10   5.52   +0.00   [+0.00, +0.00]     32281      +0  1478.65  71.0
seapdx   passive_c120             20   45.00   6.14   +0.90   [-2.20, +3.90]     32483    +202  1463.55  71.0
seapdx   passive_c120_probes      20   45.00   4.92   +0.90   [-2.60, +4.20]     32116    -164  1442.19  71.0
seapdx   passive_c120_ttl_long    20   45.80   5.91   +1.70   [-1.10, +4.70]     32384    +103  1430.13  71.0
seapdx   passive_c120_ttl_short   20   45.00   5.68   +0.90   [-2.10, +3.70]     32175    -106  1446.82  71.0
seapdx   passive_c40              20   26.50   5.73  -17.60 [-21.90,-13.50]     25721   -6560  2017.66  71.0
seapdx   passive_c40_probes       20   25.70   4.12  -18.40 [-21.30,-15.50]     25570   -6711  2033.59  71.0

urban    baseline                 20   81.62  13.20   +0.00   [+0.00, +0.00]       381      +0    12.80  46.0
urban    passive_c120             20   79.73  13.77   -1.89  [-10.68, +7.03]       496    +115    17.01  46.0
urban    passive_c120_probes      20   80.68   7.25   -0.95   [-7.16, +5.68]       515    +134    17.34  46.0
urban    passive_c120_ttl_long    20   85.81   7.49   +4.19  [-2.03, +10.14]       553    +172    17.45  46.0
urban    passive_c120_ttl_short   20   86.62   7.10   +5.00  [-2.43, +12.43]       548    +167    17.17  46.0
urban    passive_c40              20   70.54   3.60  -11.08  [-17.03, -4.73]       457     +76    17.53  46.0
urban    passive_c40_probes       20   73.65   4.46   -7.97  [-13.51, -2.43]       493    +112    18.13  46.0
```

Variability events fire ~71 per run on all 3 real regions (urban is 46 because fewer nodes mean fewer drift targets), confirming event injection parity across cells.

## Q1. Does the gdansk ttl_short finding replicate on seapdx + manh?

**Short answer: no, gdansk is the only region where ttl_short clears CI>0.**

- gdansk ttl_short: **+3.20pp [+0.30, +6.30]** — CI excludes zero, replicating the initial peek.
- seapdx ttl_short: **+0.90pp [-2.10, +3.70]** — trend positive, CI crosses zero.
- manh ttl_short: **+0.20pp [-2.90, +3.30]** — essentially zero, CI crosses zero.
- urban ttl_short: +5.00pp [-2.43, +12.43] — directionally largest but CI crosses zero (10-node toy has huge seed variance, 13pp baseline sd).

So the gdansk finding is **gdansk-specific among the CI-significant results**. Across all 4 regions the sign is consistently non-negative (+0.20, +0.90, +3.20, +5.00), which is a 4-for-4 directional trend, but only 1 of 4 has a CI excluding zero. Under a pre-registered multi-region success criterion ("CI>0 on at least 2 of 3 real regions"), ttl_short fails.

## Q2. Does passive_c120 default work on dynamic topologies?

Per-region paired delta vs baseline:
- gdansk: **+0.00pp [-2.80, +2.80]** — CI includes zero, perfectly tied.
- manh: **-1.50pp [-4.80, +1.70]** — CI includes zero, trend slightly negative.
- seapdx: **+0.90pp [-2.20, +3.90]** — CI includes zero, trend slightly positive.
- urban: -1.89pp [-10.68, +7.03] — CI includes zero, noisy.

**passive_c120 is never significantly positive and never significantly negative on dynamic topologies.** It is statistically indistinguishable from baseline across all 4 regions. That is a weaker result than v7-v10 static (where passive_c120 at least pulled clear positive on some regions), but crucially it is not harmful — there is no evidence that shipping passive_c120 degrades delivery when propagation becomes unstable. It just stops helping.

## Q3. Do probes help on dynamic topologies?

Evidence required: CI excluding zero on at least 2 of 3 real regions (convincing), or positive trend on all 3 (suggestive).

passive_c120_probes paired deltas:
- gdansk: **+1.20pp [-1.80, +4.30]** — trend positive, CI crosses zero.
- manh: **-0.10pp [-3.50, +3.40]** — essentially zero.
- seapdx: **+0.90pp [-2.20 via symmetric... actually [-2.60, +4.20]]** — trend positive, CI crosses zero.
- urban: -0.95pp [-7.16, +5.68] — noise.

**Zero CIs exclude zero. Trend is +1.20/-0.10/+0.90 across the 3 real regions — not even consistently positive (manh flips sign).** Probes fail both the convincing criterion (0/3 CI>0) and the suggestive criterion (trend positive on only 2/3). The v9 static-topology retraction of probes holds up under dynamic topologies too. No evidence to reverse that decision.

Note passive_c40_probes vs passive_c40 shows probes do not rescue the loose-confidence variant either — they land in the same -7 to -18pp trench.

## Q4. edge_ttl sweet spot (300s / 1800s / 3600s)

Paired deltas vs baseline by region, short → default → long:

| region | ttl_short (300s) | default c120 (1800s) | ttl_long (3600s) |
|--------|------------------|----------------------|------------------|
| gdansk | **+3.20** [+0.30, +6.30] | +0.00 [-2.80, +2.80] | -0.50 [-3.30, +1.90] |
| manh   | +0.20 [-2.90, +3.30]    | -1.50 [-4.80, +1.70] | -1.50 [-4.40, +1.60] |
| seapdx | +0.90 [-2.10, +3.70]    | +0.90 [-2.20, +3.90] | **+1.70** [-1.10, +4.70] |
| urban  | +5.00 [-2.43, +12.43]   | -1.89 [-10.68, +7.03] | +4.19 [-2.03, +10.14] |

Gdansk and manh show a **monotone short > default > long** pattern, consistent with "under churn, forget stale links faster." Seapdx inverts it (ttl_long wins, still not CI-significant). Urban shows a U-shape (short and long both beat default, but CIs overlap wildly).

**It is not a clean monotone relationship across regions.** gdansk + manh favor shorter TTL; seapdx favors longer TTL; urban is a noisy mess. 300s is special on gdansk specifically; elsewhere it is within noise of the default. The simulation-wide "forget faster under churn" heuristic does not generalize.

## Q5. Airtime-per-delivered-message (double-win scan)

tx/delivered lower is better (less airtime spent per successful message). Compare each feature's (delta_delivery, delta_tx/del) pair:

```
region   feature                  delta_pp   tx/del   base tx/del   delta_tx/del
gdansk   passive_c120_ttl_short    +3.20    249.22      259.44        -10.22   <-- DOUBLE WIN
gdansk   passive_c120              +0.00    264.22      259.44         +4.78
gdansk   passive_c120_probes       +1.20    262.64      259.44         +3.20
gdansk   passive_c120_ttl_long     -0.50    268.36      259.44         +8.92

manh     passive_c120_ttl_short    +0.20    469.85      468.62         +1.23
manh     passive_c120_probes       -0.10    473.07      468.62         +4.45
manh     passive_c120              -1.50    478.08      468.62         +9.46
manh     passive_c120_ttl_long     -1.50    487.68      468.62        +19.06

seapdx   passive_c120_ttl_long     +1.70   1430.13     1478.65        -48.52   <-- DOUBLE WIN
seapdx   passive_c120_probes       +0.90   1442.19     1478.65        -36.46   <-- DOUBLE WIN
seapdx   passive_c120_ttl_short    +0.90   1446.82     1478.65        -31.83   <-- DOUBLE WIN
seapdx   passive_c120              +0.90   1463.55     1478.65        -15.10   <-- DOUBLE WIN

urban    passive_c120_ttl_short    +5.00     17.17       12.80         +4.37
urban    passive_c120_ttl_long     +4.19     17.45       12.80         +4.65
urban    passive_c120_probes       -0.95     17.34       12.80         +4.54
urban    passive_c120              -1.89     17.01       12.80         +4.21
```

**Double wins (delivery up AND tx/delivered down):**
- gdansk: **ttl_short** — the CI-significant delivery winner is also the airtime winner (-10.22 tx per delivered).
- seapdx: **all four c120 variants** are double wins on airtime — seapdx has slack tx budget, any delivery improvement is basically free. ttl_long is the biggest (-48.52 tx/del) but c120 default also wins.
- manh: **no double wins.** Everything that moved delivery also cost proportionally more airtime.
- urban: **no double wins.** tx per delivered goes up across the board because urban baseline is already near-saturation (81.62% delivery) and topology propagation adds overhead that only partially pays off in delivered-count.

The c40 variants are massive negative double-losses (delivery down AND tx/delivered up by 30–40%); confirming c40 is unshippable under any condition.

## Q6. Per-region shipping recommendation (dynamic conditions)

- **gdansk (186 nodes):** `passive_c120_ttl_short`. Only feature with CI>0 on delivery AND wins on airtime. +3.20pp [+0.30, +6.30], tx/del -10.22.
- **seapdx (1076 nodes):** `passive_c120_ttl_long` marginally. +1.70pp [-1.10, +4.70] on delivery (CI crosses zero) but -48.52 tx/del — best airtime of any variant. If you refuse to ship anything without CI>0, fall back to `passive_c120` default (also a double-win at seapdx scale). **Do not ship ttl_short on seapdx**, it does not beat default on delivery AND gives up airtime relative to ttl_long.
- **manh (344 nodes):** `baseline`. No feature improved delivery with CI>0; ttl_short is closest but +0.20pp is noise. Every non-baseline variant costs airtime. Ship nothing, or ship default c120 if you want a common firmware.
- **urban (10-node toy):** too noisy to call — sd=13pp on baseline. Directionally both ttl_short and ttl_long win big (+5.00, +4.19pp) but urban is not a real-deployment signal, it's a canary.

**Recommendations differ by region.** There is no single dynamic-topology winner. gdansk wants ttl_short, seapdx wants ttl_long (or default), manh wants baseline.

## Q7. Synthesis: static-recommended passive_c120 vs dynamic-recommended variants — which ships?

v7-v10 (static) converged on `passive_c120` as a safe shipping default. This sweep says:

1. `passive_c120` is harmless under dynamic conditions (all 4 CIs include zero, none significantly negative). It does not hurt.
2. `passive_c120_ttl_short` is a gdansk-local win under churn, not a global dynamic-topology win. It fails to replicate on seapdx and manh.
3. No single non-default variant wins across ≥2 real regions with CI>0. The only feature that appears "safe to ship everywhere" remains `passive_c120` default.

**Recommendation: ship `passive_c120` default.** The dynamic sweep provides no globally replicating alternative. The one CI-significant improvement (gdansk ttl_short) does not generalize to seapdx or manh, and the cost of shipping ttl_short to seapdx is giving up the airtime improvement that ttl_long (or default) delivers there. Shipping a 300s TTL globally on the basis of one region's win would be a textbook over-fit to gdansk.

Caveat: if real-world deployments look like gdansk (186 nodes, mid-density, urban mesh, high mobility/shadowing), the case for a runtime-configurable `edge_ttl` parameter with factory default 1800s and a documented "high-churn profile" value of 300s is strong. This sweep justifies exposing the knob, not flipping the default.

Secondary note: probes remain retracted. Dynamic topologies do not rescue them. v9's decision stands.

## Methodology notes

- Paired-by-seed delta: each feature run at seed S is paired with baseline at same region, same seed S. 20 pairs per cell.
- Bootstrap: 10k resamples with replacement of the 20 paired differences, 2.5/97.5 percentile for 95% CI. Seed 0xC0DE for reproducibility.
- delivery_rate = delivered / sent, rows with sent==0 skipped (none observed).
- tx/delivered computed per-seed then averaged (skip delivered==0 rows; none observed).
- All cells have full n=20, no missing seeds, all rc=0 implied (would have shown as reduced n otherwise; verified in raw table).
