# Dynamic-topology realistic-traffic sweep analysis (sweep_dynamic_realistic.csv, 420 runs)

Second systematic A/B of TopoGraph under dynamic propagation, this time with multi-pair bursty chat (7 pairs x 3 sessions x 4 msgs = 84 unicasts per run) plus 46 channel broadcasts. 3 real regions x 7 features x 20 seeds. Compared seed-for-seed against /tmp/sweep_dynamic.csv (same regions, same 20 seeds, same variability events, simpler single-pair 50-unicast + 16-channel traffic). Variability event counts match exactly (71.0 per run on all three regions in both sweeps), so any delta here is from the traffic mix, not from churn.

Both sweeps: rc=0 on all runs, sent==0 on zero runs, n=20 paired per cell.

## Combined per-cell table (delivery rate %, paired delta pp vs baseline, 95% bootstrap CI, airtime)

```
region   feature                  traffic      rate%   sd_pp   delta         CI95            tx     dtx       tx/del   dtx/del
gdansk   baseline                 base         36.60    4.86   +0.00   [+0.00, +0.00]      4674      +0      259.44     +0.00
gdansk   baseline                 realistic    32.74    3.91   +0.00   [+0.00, +0.00]      7860      +0      289.63     +0.00
gdansk   passive_c120             base         36.60    4.11   +0.00   [-2.80, +2.80]      4793    +120      264.22     +4.79
gdansk   passive_c120             realistic    33.04    3.27   +0.30   [-1.79, +2.56]      8103    +243      294.33     +4.69
gdansk   passive_c120_probes      base         37.80    6.29   +1.20   [-1.80, +4.30]      4851    +178      262.64     +3.21
gdansk   passive_c120_probes      realistic    33.75    3.69   +1.01   [-1.19, +3.51]      8103    +243      288.74     -0.90
gdansk   passive_c120_ttl_short   base         39.80    5.15   +3.20   [+0.30, +6.30]      4893    +219      249.22    -10.22
gdansk   passive_c120_ttl_short   realistic    34.17    4.13   +1.43   [-0.89, +3.75]      8158    +298      287.44     -2.19
gdansk   passive_c120_ttl_long    base         36.10    4.83   -0.50   [-3.30, +2.00]      4779    +105      268.36     +8.92
gdansk   passive_c120_ttl_long    realistic    32.68    4.91   -0.06   [-2.86, +2.80]      8144    +283      303.34    +13.71
gdansk   passive_c40              base         29.20    5.60   -7.40  [-10.20, -4.40]      4089    -585      287.24    +27.80
gdansk   passive_c40              realistic    27.50    4.05   -5.24   [-7.20, -3.15]      7461    -399      328.69    +39.06
gdansk   passive_c40_probes       base         28.60    5.88   -8.00  [-10.80, -5.00]      4130    -544      299.58    +40.15
gdansk   passive_c40_probes       realistic    28.39    3.93   -4.35   [-5.95, -2.68]      7596    -264      323.42    +33.79

manh     baseline                 base         41.00    5.68   +0.00   [+0.00, +0.00]      9465      +0      468.62     +0.00
manh     baseline                 realistic    34.35    3.75   +0.00   [+0.00, +0.00]     15398      +0      539.16     +0.00
manh     passive_c120             base         39.50    4.72   -1.50   [-4.70, +1.80]      9341    -124      478.08     +9.46
manh     passive_c120             realistic    34.29    3.22   -0.06   [-2.26, +2.20]     15560    +163      543.88     +4.72
manh     passive_c120_probes      base         40.90    6.07   -0.10   [-3.50, +3.30]      9526     +61      473.07     +4.45
manh     passive_c120_probes      realistic    34.58    3.69   +0.24   [-2.32, +2.62]     15786    +389      549.10     +9.94
manh     passive_c120_ttl_short   base         41.20    5.37   +0.20   [-3.10, +3.30]      9534     +68      469.85     +1.23
manh     passive_c120_ttl_short   realistic    35.24    3.51   +0.89   [-1.01, +2.92]     15637    +240      533.03     -6.12
manh     passive_c120_ttl_long    base         39.50    5.15   -1.50   [-4.40, +1.50]      9499     +34      487.68    +19.06
manh     passive_c120_ttl_long    realistic    33.15    4.00   -1.19   [-3.57, +1.25]     15502    +105      564.06    +24.90
manh     passive_c40              base         28.30    5.36  -12.70  [-16.20, -9.30]      7931   -1534      575.04   +106.42
manh     passive_c40              realistic    28.04    4.45   -6.31   [-9.17, -3.51]     14499    -899      630.67    +91.52
manh     passive_c40_probes       base         29.10    6.54  -11.90  [-15.40, -8.40]      7945   -1520      567.37    +98.75
manh     passive_c40_probes       realistic    28.93    4.37   -5.42   [-7.86, -3.04]     14668    -730      616.49    +77.33

seapdx   baseline                 base         44.10    5.52   +0.00   [+0.00, +0.00]     32281      +0     1478.65     +0.00
seapdx   baseline                 realistic    37.68    5.17   +0.00   [+0.00, +0.00]     53579      +0     1716.65     +0.00
seapdx   passive_c120             base         45.00    6.14   +0.90   [-2.20, +3.80]     32483    +202     1463.55    -15.10
seapdx   passive_c120             realistic    38.99    3.21   +1.31   [-1.43, +4.11]     54879   +1300     1685.41    -31.25
seapdx   passive_c120_probes      base         45.00    4.92   +0.90   [-2.50, +4.30]     32117    -164     1442.19    -36.46
seapdx   passive_c120_probes      realistic    39.11    3.77   +1.43   [-1.19, +3.99]     54673   +1094     1674.28    -42.37
seapdx   passive_c120_ttl_short   base         45.00    5.68   +0.90   [-2.10, +3.70]     32175    -106     1446.82    -31.82
seapdx   passive_c120_ttl_short   realistic    40.30    4.39   +2.62   [-0.60, +5.65]     55450   +1871     1654.55    -62.11
seapdx   passive_c120_ttl_long    base         45.80    5.91   +1.70   [-1.10, +4.70]     32384    +103     1430.13    -48.52
seapdx   passive_c120_ttl_long    realistic    40.00    3.15   +2.32   [+0.00, +4.64]     54573    +994     1631.71    -84.94
seapdx   passive_c40              base         26.50    5.73  -17.60 [-21.90, -13.40]     25721   -6560     2017.66   +539.01
seapdx   passive_c40              realistic    30.06    3.92   -7.62  [-10.42, -4.88]     48856   -4723     1956.26   +239.61
seapdx   passive_c40_probes       base         25.70    4.12  -18.40 [-21.30, -15.50]     25570   -6711     2033.59   +554.94
seapdx   passive_c40_probes       realistic    29.11    2.74   -8.57  [-11.07, -6.13]     49146   -4433     2021.77   +305.12
```

Baseline radio_tx scales ~1.63-1.68x from base to realistic across the three regions (gdansk 4674 -> 7860, manh 9465 -> 15398, seapdx 32281 -> 53579), consistent with the 1.68x sent-message increase (84 vs 50). No region is disproportionately taxed on airtime.

## Q1. Does realistic traffic change the feature ranking?

Sign agreement between base and realistic deltas, per (region, feature):

```
region   feature                   base delta    real delta    sign same?
gdansk   passive_c120                +0.00         +0.30        yes (both ~zero)
gdansk   passive_c120_probes         +1.20         +1.01        yes (+, shrunk)
gdansk   passive_c120_ttl_short      +3.20         +1.43        yes (+, shrunk)
gdansk   passive_c120_ttl_long       -0.50         -0.06        yes (both ~zero)
gdansk   passive_c40                 -7.40         -5.24        yes (-)
gdansk   passive_c40_probes          -8.00         -4.35        yes (-)

manh     passive_c120                -1.50         -0.06        yes (-, shrunk to zero)
manh     passive_c120_probes         -0.10         +0.24        SIGN FLIP (noise-sized either way)
manh     passive_c120_ttl_short      +0.20         +0.89        yes (+, grew)
manh     passive_c120_ttl_long       -1.50         -1.19        yes (-)
manh     passive_c40                -12.70         -6.31        yes (-)
manh     passive_c40_probes         -11.90         -5.42        yes (-)

seapdx   passive_c120                +0.90         +1.31        yes (+, grew)
seapdx   passive_c120_probes         +0.90         +1.43        yes (+, grew)
seapdx   passive_c120_ttl_short      +0.90         +2.62        yes (+, grew)
seapdx   passive_c120_ttl_long       +1.70         +2.32        yes (+, grew)  <-- CI now excludes zero
seapdx   passive_c40                -17.60         -7.62        yes (-, much less bad)
seapdx   passive_c40_probes         -18.40         -8.57        yes (-, much less bad)
```

Direction: 17 of 18 non-baseline cells agree. The one sign flip (manh passive_c120_probes -0.10 -> +0.24) is well inside noise on both sides.

The main structural change is **magnitude and CI**:

- **passive_c120**: base-traffic deltas were +0.00/-1.50/+0.90 (all CIs include zero). Realistic deltas +0.30/-0.06/+1.31 — all three CIs still include zero, but on seapdx the upper CI is +4.11. passive_c120 remains inert on gdansk and manh and directionally positive on seapdx. Not CI-significant anywhere.

- **passive_c120_ttl_short**: on base, gdansk was +3.20 [+0.30, +6.30], seapdx +0.90 [-2.10, +3.70], manh +0.20 [-3.10, +3.30]. On realistic: gdansk drops to +1.43 [-0.89, +3.75] (lost its CI>0), seapdx grows to +2.62 [-0.60, +5.65] (still CI crosses zero), manh grows to +0.89 [-1.01, +2.92] (still CI crosses zero). Gdansk's base-sweep significance did **not** survive the traffic-mix change; seapdx and manh improved but still don't clear CI.

- **probes (passive_c120_probes)**: gdansk +1.20 -> +1.01, seapdx +0.90 -> +1.43, manh -0.10 -> +0.24. Contention did not materially rescue probes — trend slightly more positive, but 0/3 CIs exclude zero on either sweep.

- **passive_c120_ttl_long on seapdx: +1.70 [-1.10, +4.70] on base, +2.32 [+0.00, +4.64] on realistic.** The realistic CI lower bound sits exactly at +0.00 (bootstrap 2.5th percentile is 1.52e-16). That is right on the edge of CI-significance; I treat it as "not cleanly significant" but the single strongest positive signal in either sweep outside of gdansk-ttl_short-on-base.

So: **no feature becomes CI-clear across all three regions under realistic traffic.** The only cell that newly approaches CI>0 is seapdx passive_c120_ttl_long. The gdansk ttl_short finding lost its significance.

## Q2. Does TopoGraph's relative advantage grow under contention?

Paired-by-seed baseline drop from base to realistic (delivery pp, realistic minus base, CI95):

```
region   baseline drop     CI95
gdansk      -3.86        [-6.91, -0.80]
manh        -6.65       [-10.11, -3.27]
seapdx      -6.42       [-10.07, -2.53]
```

All three region baselines drop significantly (CIs exclude zero). The 2.5-3x heavier traffic (reference: 84 + 46 broadcast vs 50 + 16 broadcast) costs ~4-7pp of delivery across regions. Now compare TopoGraph variants' drops:

```
region   feature                   variant drop    vs baseline drop
gdansk   baseline                    -3.86pp        (reference)
gdansk   passive_c120                -3.56pp        +0.30pp better
gdansk   passive_c120_probes         -4.05pp        -0.19pp worse
gdansk   passive_c120_ttl_short      -5.63pp        -1.77pp worse (came from higher base)
gdansk   passive_c120_ttl_long       -3.42pp        +0.44pp better

manh     baseline                    -6.65pp        (reference)
manh     passive_c120                -5.21pp        +1.44pp better
manh     passive_c120_probes         -6.32pp        +0.33pp better
manh     passive_c120_ttl_short      -5.96pp        +0.69pp better
manh     passive_c120_ttl_long       -6.35pp        +0.30pp better

seapdx   baseline                    -6.42pp        (reference)
seapdx   passive_c120                -6.01pp        +0.41pp better
seapdx   passive_c120_probes         -5.89pp        +0.53pp better
seapdx   passive_c120_ttl_short      -4.70pp        +1.72pp better  <-- biggest resistance
seapdx   passive_c120_ttl_long       -5.80pp        +0.62pp better
```

TopoGraph variants drop less than baseline on 11 of 12 c120-* cells (gdansk_ttl_short and gdansk_probes are the exceptions — ttl_short had further to fall because its base was elevated). The effect is mild (+0.3 to +1.7pp less drop) and none of these individual differences would clear a CI test (they're 0.3-1.7pp shifts on top of 3-7pp region drops with noisy seed pairing).

There is directional support for the path-cache-thrashing hypothesis on manh (everything drops less than baseline, by +0.3 to +1.4pp) and on seapdx_ttl_short specifically (+1.72pp less drop, which is also the region where ttl_short's absolute delta grew the most under realistic). But nothing reaches CI-significance, and gdansk doesn't show the effect at all.

The c40 variants show a different story: their "drops" are much smaller (only -1.70pp gdansk, -0.26pp manh) or even positive (seapdx c40 went *up* +3.56pp under realistic traffic). That is because c40 was already catastrophically bad on base, so realistic traffic barely degrades it further — c40 has no remaining headroom to lose. This is a floor effect, not a virtue.

**Weak evidence for a contention-resistance effect on manh and seapdx_ttl_short.** Not strong enough to claim TopoGraph has a contention-specific advantage as a general property.

## Q3. Airtime story: double-wins under realistic traffic

Features with simultaneously (positive delivery delta) AND (negative delta tx/delivered):

```
region   feature                   delta_pp    delta tx/del       double win?
gdansk   passive_c120_probes        +1.01         -0.90           yes (both tiny)
gdansk   passive_c120_ttl_short     +1.43         -2.19           yes (both small)
gdansk   passive_c120               +0.30         +4.69           no
gdansk   passive_c120_ttl_long      -0.06        +13.71           no

manh     passive_c120_ttl_short     +0.89         -6.12           yes
manh     passive_c120                -0.06        +4.72           no
manh     passive_c120_probes        +0.24         +9.94           no
manh     passive_c120_ttl_long      -1.19        +24.90           no

seapdx   passive_c120               +1.31        -31.25           yes
seapdx   passive_c120_probes        +1.43        -42.37           yes
seapdx   passive_c120_ttl_short     +2.62        -62.11           yes
seapdx   passive_c120_ttl_long      +2.32        -84.94           yes  <-- best airtime
```

**Seapdx is a universal double-win region under realistic traffic** — all four c120 variants improve both delivery AND airtime efficiency. ttl_long gives the biggest airtime saving (-84.94 tx per delivered) and has the near-CI-clear delivery delta (+2.32 [+0.00, +4.64]). This replicates the base-sweep pattern on seapdx, amplified.

**Manh gets one double-win under realistic**: ttl_short (+0.89pp, -6.12 tx/del). On base sweep, manh had zero double-wins. Under contention, ttl_short becomes airtime-positive on manh while it was airtime-negative before (+1.23 tx/del on base -> -6.12 on realistic). That is a meaningful qualitative change, even if the delivery CI still crosses zero.

**Gdansk has two very small double-wins** (probes, ttl_short) — both within noise.

The c40 variants' airtime penalties shrink under realistic traffic (seapdx c40 tx/del penalty was +539, now +240) but the delivery floor is still 7-9pp below baseline — unshippable.

## Q4. Does the shipping recommendation change?

Base-sweep recommendation: ship `passive_c120` default because it's CI-safe (never significantly negative) on all regions, with gdansk ttl_short flagged as a region-specific win.

Under realistic traffic:

- `passive_c120` remains never significantly negative and never significantly positive (CIs +0.30 [-1.79, +2.56], -0.06 [-2.26, +2.20], +1.31 [-1.43, +4.11]). Safe. Same story as base. **Confirms the base recommendation.**
- `passive_c120_ttl_short` no longer has any CI-clear region (gdansk's significance on base did not replicate under realistic). Still positive trend on all three regions (+1.43, +0.89, +2.62), and on manh it became an airtime double-win, but 0/3 CIs exclude zero.
- `passive_c120_ttl_long` on seapdx is the single best candidate under realistic (+2.32 [+0.00, +4.64], best airtime of any variant at -84.94 tx/del). CI lower bound is at zero exactly. One region, borderline significance, so not a globally shippable recommendation — but a stronger regional case than anything in the base sweep.
- Probes: still inert everywhere.
- c40 variants: still unshippable.

**Bottom line: ship `passive_c120` default, unchanged from the base recommendation.** The realistic sweep does not upgrade any feature to CI-clear across regions, and the gdansk-specific ttl_short win from base did not survive the traffic-mix change. It does slightly strengthen the seapdx case for ttl_long but not enough to override default.

There is **no feature that wins everywhere under realistic traffic.** Be honest about that: TopoGraph's value under dynamic topologies is in (a) not being harmful (all c120 variants keep CIs including zero under both traffic mixes) and (b) modest airtime efficiency wins on seapdx that grow under contention.

## Q5. Sign flips and magnitude shifts between base and realistic

Sign flips (base -> realistic):
- manh passive_c120_probes: -0.10pp -> +0.24pp. Both inside noise, not a real flip.

Significance flips:
- gdansk passive_c120_ttl_short: **was +3.20 [+0.30, +6.30] on base, becomes +1.43 [-0.89, +3.75] on realistic.** The only CI-clear positive result in the base sweep lost its significance under realistic traffic. This is the biggest qualitative change between sweeps.
- seapdx passive_c120_ttl_long: **was +1.70 [-1.10, +4.70] on base, becomes +2.32 [+0.00, +4.64] on realistic.** Near-CI-clear on realistic; grew in both magnitude and tightness. Opposite direction from gdansk ttl_short.

Magnitude shifts worth noting:
- All c40 variants: their negative delta shrank substantially under realistic (gdansk c40 -7.40 -> -5.24, manh c40 -12.70 -> -6.31, seapdx c40 -17.60 -> -7.62). Floor effect from already-degraded baseline under contention; not a rehabilitation of c40.
- seapdx c120 variants: all four grew under realistic (+0.90 -> +1.31, +0.90 -> +1.43, +0.90 -> +2.62, +1.70 -> +2.32). Seapdx is the one region where contention demonstrably amplifies TopoGraph's benefit.
- manh c120 variants: three of four improved (less negative / more positive). Compatible with the path-cache-thrashing hypothesis, none CI-significant.

Seed-variance effects: realistic sd_pp is systematically lower than base sd_pp in most cells (e.g., seapdx baseline 5.52 -> 5.17, manh baseline 5.68 -> 3.75, seapdx ttl_long 5.91 -> 3.15). 84 sent messages per run gives tighter per-seed delivery-rate estimates than 50 sent, which shows up as narrower CIs on realistic despite the same n=20. This is **why several realistic CIs got narrower without the central estimate moving much.**

## Synthesis

Realistic traffic (2.5x message volume, multi-pair bursty chat, denser channel broadcasts) degrades baseline delivery by 3.9-6.6pp across regions. TopoGraph c120 variants track that drop within ~1-2pp — slight evidence they resist contention better than baseline, strongest on manh and on seapdx_ttl_short, but never CI-clearly so.

The base-sweep gdansk ttl_short CI>0 finding is **not reproduced** under realistic traffic; it drops from +3.20 [+0.30, +6.30] to +1.43 [-0.89, +3.75]. The single feature/region cell that approaches CI>0 under realistic is seapdx passive_c120_ttl_long (+2.32 [+0.00, +4.64]) with the best airtime profile of any variant on any region.

No feature is a cross-region CI-clear winner. The base recommendation (ship `passive_c120` default) stands.

If one wanted to extract additional value region-specifically, the realistic sweep supports:
- seapdx: `passive_c120_ttl_long` (near-CI-clear delivery +2.32pp, best airtime -84.94 tx/del).
- manh: `passive_c120_ttl_short` (first double-win at manh across either sweep, +0.89pp, -6.12 tx/del, CI crosses zero).
- gdansk: no clear win under realistic; ttl_short lost its gdansk-specific significance.

This further weakens the case for a global non-default setting and strengthens the case for a runtime-configurable `edge_ttl` knob (seapdx prefers long, gdansk preferred short under base but that didn't replicate, manh was fine either way).

## Methodology

- delivery_rate = delivered / sent per run. No sent==0 or rc!=0 rows were observed in either sweep.
- Paired-by-seed delta: each feature run at seed S is paired with baseline at same region, same seed S. 20 pairs per cell. Both sweeps share the identical 20-seed list (42, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1010, 1111, 1212, 1313, 1414, 1515, 1616, 1717, 1818, 1919).
- Bootstrap CI: 10,000 resamples with replacement of the 20 paired differences; report 2.5/97.5 percentiles for 95% CI. Single RNG seed 0xC0DE across all cells for reproducibility. Where CI bound printed as +0.00 it reflects the 2.5th percentile falling at ~1.5e-16 (floating-point zero); treated as "touches zero."
- tx_per_delivered computed per-run then averaged across 20 seeds within a cell (no delivered==0 rows observed).
- Cross-sweep drop analysis (Q2): within a (region, feature) cell, delta = (realistic delivery_rate at seed S) - (base delivery_rate at seed S), averaged across 20 paired seeds, with the same 10k bootstrap procedure.
- Variability-event parity: events_drift + events_shadow + events_fade sums to 71.0 per run on all three real regions in both sweeps. Event model is identical; differences in this writeup are attributable to traffic mix only.
- Urban region excluded: the realistic sweep does not include urban.
- No multiple-comparison correction applied. 7 features x 3 regions = 21 cells per sweep; with alpha=0.05 you'd expect ~1 false positive by chance per sweep, and the surviving CI-significant results (c40 variants' negative deltas, seapdx ttl_long near-zero CI) are not candidates for this concern since c40 is overwhelmingly significant and ttl_long's signal is marginal regardless.
