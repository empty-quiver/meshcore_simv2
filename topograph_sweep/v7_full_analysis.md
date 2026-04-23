# v7 Topology-Sensitivity Sweep — Full Analysis

Data: `/tmp/sweep_v7.csv`, 7,200 rows = 40 topologies x 6 features x 3 workloads x 2 adverts x 5 seeds. All 7,200 runs returned `rc=0`. Note: advert values in the data are `frequent, medium` (not `medium, sparse` as the prompt described — analysis uses the actual values).

All per-scenario metrics below are means over 5 seeds. `delta_pp` = delivery percentage-point delta vs. baseline for the matching (topology, workload, advert). `radio_delta_pct` = percent change in radio transmissions vs. baseline.

---

## 1. Prior findings — confirm / refute

### Finding 1: "p2_c120 safe everywhere (worst chain_20 -1.1pp, best chain_15 +1.78pp)"
**Partially refuted.** The old "safe everywhere" claim collapses once rings are in the mix.

- Non-ring universe (234 scenarios): range [-6.67pp, +14.67pp], median 0, p10 0.0, mean +0.04pp. So for non-ring topologies p2_c120 is indeed essentially harmless.
- Rings break it: `ring_6` mean -14.06pp (worst -26.67pp), `ring_10` mean -9.17pp (worst -16.67pp). Both are reproducible across multiple workloads.
- Worst non-ring: `grid_4x4_nodiag` mean -1.11pp (worst scenario -6.67pp), `chain_20` -1.11pp (worst -6.67pp), `chain_12` worst scenario -6.67pp.
- Best: `chain_15` mean +1.78pp (specific scenario +14.67pp on sparse/medium), confirming the old "+1.78pp" number exactly.

Net: p2_c120 is safe on everything except rings (see failure-modes section).

### Finding 2: "p2_c120_h2 high variance (chain_7 +3.22pp, grid_4x4_nodiag -11.4pp)"
**Confirmed and extended.** p2_c120_h2 has by far the widest spread of any feature: [-48.0pp, +27.0pp].

- chain_7 mean +3.22pp (matches); grid_4x4_nodiag mean -11.39pp (matches).
- New lows on ring topologies now that they exist: `ring_6` mean -27.17pp (worst -48.0pp) — the single worst cell in the whole sweep for a c120-class feature.
- New highs on tree family: `tree_d4f2` mean +9.80pp (best scenario +25.67pp), `tree_d3f3` mean +5.36pp (best +12.92pp). Probes clearly help poorly-covered tree backbones.
- Radio overhead: +6.25% on average, +19% worst-case, up to +103 tx absolute in a scenario. Probes fire 3.1 on average, max 6.

### Finding 3: "p2_c40 cliff: safe on chain_3..7, catastrophic at chain_8+ (-18pp) and grid_3x3+ (-17 to -53pp)"
**Confirmed precisely.** The cliff is sharp in chain length: chain_3 0.0pp, chain_4 +1.6pp, chain_5 -1.2pp, chain_6 -0.3pp, chain_7 +1.1pp, then chain_8 -18.7pp, chain_10 -21.7pp, chain_12 -16.8pp, chain_15 -15.5pp, chain_20 -14.0pp, chain_25 -25.4pp.

Grids: cliff at 3x3 (9 cells) diagonal variant, -17.1pp; then monotone worse with size — grid_4x4 -30.3pp, grid_5x5 -38.7pp, grid_3x7 -35.1pp, grid_6x6 -52.6pp (worst-case scenario -64pp). Nodiag variants have the same shape but softer magnitude (3x3 -6.5pp, 6x6 -36.7pp).

### Finding 4: "p2_c40_penalty_off 2-14pp better than p2_c40 on large topologies"
**Confirmed.** Across grids/chains where p2_c40 catastrophically regresses, penalty_off is consistently less bad: grid_6x6 -43.9 vs -52.6 (+8.6pp), grid_5x5 -33.2 vs -38.7 (+5.5pp), grid_4x4 -25.0 vs -30.3 (+5.3pp), chain_25 -11.8 vs -25.4 (+13.6pp), chain_8 -7.0 vs -18.7 (+11.7pp). However penalty_off is still a substantial regression everywhere p2_c40 is bad — it mitigates the cliff but does not eliminate it.

### Finding 5: "Only struggling topology found so far was chain_25 (69% baseline)"
**Refuted.** Full sweep reveals many more struggling topologies. See section 3.

---

## 2. Best feature per topology class

| Class | Topologies | Baseline mean delivery | Best feature (mean delta_pp) | Worst-case scenario for best feature |
|---|---|---|---|---|
| chain_short (3-7) | chain_3..7 | 0.95-1.00 | p2_c120 (+0.0pp) — everything ties near zero; p2_c40 safe too | p2_c120 worst scenario -4pp on chain_5 |
| chain_long (8-25) | chain_8..25 | 0.69-0.94 | **p2_c120** (+0.19pp, p10 0, max +14.67pp on chain_15). p2_c120_h2 close +0.41pp but higher variance (p10 -5.08pp) | p2_c120 -6.67pp on chain_12/chain_20 sparse/medium |
| grid_diag | grid_2x2, 2x5, 3x3, 3x7, 4x4, 5x5, 6x6 | 0.89-0.99 | **p2_c120** (+0.34pp mean). p2_c120_h2 slightly higher mean (+0.74pp) but negative tail | p2_c120 -1.67pp on grid_6x6 |
| grid_nodiag | grid_3x3..6x6_nodiag | 0.77-0.82 | **p2_c120** (-0.52pp mean, worst -6.67pp). p2_c120_mp2 close. p2_c120_h2 is toxic here (-2.28pp mean, worst -13.33pp) | - |
| star (3, 4, 5, 6, 8, 10) | all stars | 0.97-1.00 | all features tie at 0 | - |
| dstar (3, 4) | dstar_3, dstar_4 | 0.98-0.99 | all features ~0 | - |
| tree (d2f2, d2f3, d3f2, d3f3, d4f2) | trees | 0.75-0.95 | **p2_c120_h2** dominant (+9.80pp on d4f2, +5.36pp on d3f3). p2_c120 = 0 (no probes, no new paths found) | p2_c120_h2 -4.0pp on tree_d3f3 scenario |
| ring (6, 10) | both | 0.73-0.82 | **all features hurt.** Least bad: p2_c40 on ring_6 (-3.4pp mean, but min -28pp); p2_c120_h2 on ring_10 (-5.1pp) | Rings are the one class where TopoGraph of any kind is a net loss |
| cluster | cluster_big, cluster_small | 0.77-0.88 | **p2_c120_h2** (+1.22pp). p2_c120 +0.14pp safer. c40 variants catastrophic (-18pp / -13pp) | p2_c120_h2 -24pp on cluster_big worst scenario |
| spurs (chain6_spurs) | 1 topology | 0.38 (very low baseline) | **p2_c120_h2** (+1.04pp). p2_c120_mp2 = 0. c40 regressions (-8.6pp / -4.1pp) | p2_c120_h2 -4.17pp worst scenario |

Summary: **p2_c120 wins or ties for chains (long/short), grids (diag/nodiag), clusters, stars, dstars**. **p2_c120_h2 wins cleanly only for trees and — marginally — spurs**. **No feature helps rings**; all strict-confidence variants actively hurt them.

---

## 3. Struggling topologies (baseline < 70%)

Only two topologies have mean baseline delivery < 70%:

| Topology | Baseline mean | Range | What helps / hurts |
|---|---|---|---|
| chain6_spurs | 0.381 | 0.00 - 0.96 | Helps: **p2_c120_h2 +1.04pp**, p2_c120_mp2 0pp. Hurts: p2_c40 -8.6pp, penalty_off -4.1pp. Baseline itself is near-zero on some workloads (delivery floor dominates). |
| chain_25 | 0.692 | 0.63 - 0.78 | Helps: **p2_c120 +0.83pp** (max +5.0pp), p2_c120_mp2 -0.56pp. Hurts: p2_c40 -25.4pp (reaches 0.33 delivery), penalty_off -11.8pp, p2_c120_h2 -1.5pp (worst -9pp). |

A second tier of "borderline-struggling" topologies (mean baseline 0.70-0.82) where feature choice still matters: `ring_6` (0.73), `chain_20` (0.74), `tree_d4f2` (0.75), `tree_d3f3` (0.77), `grid_5x5_nodiag` (0.77), `cluster_big` (0.77), `grid_3x3_nodiag` (0.80), `grid_6x6_nodiag` (0.81), `grid_4x4_nodiag` (0.82), `ring_10` (0.82).

Across this struggling + borderline set, **p2_c120_h2 is best for trees, spurs, cluster_big, grid_5x5_nodiag**; **p2_c120 is best for long chains and grid_nodiag**; **nothing helps rings**.

---

## 4. Radio overhead

Overall scenario-mean radio_tx delta vs. baseline (mean / max):

| Feature | pct mean | pct max | abs tx mean | abs tx max |
|---|---|---|---|---|
| p2_c120 | +2.70% | +14.46% | +6.5 | +52.8 |
| p2_c120_mp2 | +3.55% | +19.60% | +8.4 | +63.0 |
| p2_c120_h2 | +6.25% | +19.31% | +15.5 | +103.4 |
| p2_c40 | -6.39% | +8.42% | -29.1 | +28.2 |
| p2_c40_penalty_off | -3.15% | +15.05% | -17.8 | +49.4 |

Per class (pct mean radio_delta):

| Class | c120 | c120_mp2 | c120_h2 | c40 | c40_penalty_off |
|---|---|---|---|---|---|
| chain_short | +8.8 | +8.0 | +11.1 | -2.1 | +5.6 |
| chain_long | +5.0 | +5.8 | +8.8 | -5.5 | +1.3 |
| grid_diag | +0.8 | +2.4 | +4.4 | -6.1 | -4.0 |
| grid_nodiag | +1.1 | +2.8 | +4.1 | -10.1 | -7.1 |
| star | +1.9 | +1.9 | +3.8 | -6.9 | -5.2 |
| dstar | +0.0 | +0.0 | +5.6 | -5.9 | -5.9 |
| tree | +0.5 | +0.3 | +7.8 | -11.0 | -11.0 |
| ring | +2.2 | +3.2 | +5.8 | -3.5 | -0.6 |
| cluster | +3.2 | +2.9 | +5.7 | -2.6 | -0.8 |
| spurs | -0.5 | -0.2 | +0.3 | -9.2 | -4.2 |

p2_c40's "radio savings" (-6% mean) are the suppress-flood mechanism kicking in before the route is confirmed — they are proportional to the delivery loss, not a win. The c120 family pays 2-9% more radio, peaks ~20%, with p2_c120 at the low end.

---

## 5. Failure modes (mean delta_pp < -5pp at topology-level aggregation)

49 (feature, topology) combos with mean loss > 5pp. 0 for p2_c120 except rings; 2 for p2_c120_mp2 (both rings); 3 for p2_c120_h2 (ring_6 -27.2, ring_10 -5.1, grid_4x4_nodiag -11.4); **21 for p2_c40; 23 for p2_c40_penalty_off**.

Strict-confidence family regression list (the only ones shipping candidates care about):

| Feature | Topology | Mean delta_pp | Worst scenario |
|---|---|---|---|
| p2_c120 | ring_6 | -14.06 | -26.67 |
| p2_c120 | ring_10 | -9.17 | -16.67 |
| p2_c120_mp2 | ring_6 | -14.83 | -23.33 |
| p2_c120_mp2 | ring_10 | -12.83 | -23.33 |
| p2_c120_h2 | ring_6 | -27.17 | -48.00 |
| p2_c120_h2 | ring_10 | -5.06 | -18.33 |
| p2_c120_h2 | grid_4x4_nodiag | -11.39 | -22.67 |

Worst scenario-level regressions in the full sweep (any feature): all in p2_c40 / p2_c40_penalty_off on large grids — grid_6x6 medium/frequent -66.67pp (delivery 0.27 vs 0.93), grid_6x6 sparse -64pp, grid_5x5 sparse -60pp, ring_6 sparse p2_c120_h2 -48pp.

---

## 6. Cliff analysis for p2_c40

**Chain cliff: exactly at length 8.** Means by length:

```
length:  3    4    5    6    7    8     10    12    15    20    25
c40:    +0  +1.6 -1.2 -0.3 +1.1 -18.7 -21.7 -16.8 -15.5 -14.0 -25.4
pen_off:+0  +1.6 -1.8 -0.3 +1.1  -7.0 -11.1  -5.9  -5.8  -6.5 -11.8
```

Transition is unambiguous: chain_7 is still fine (+1.1pp), chain_8 is already catastrophic (-18.7pp). penalty_off shrinks the cliff to -7pp but does not remove it. chain_25 is worse than intermediate lengths because the flood-overhead problem and the stale-edge problem compound.

**Grid cliff: at 9 cells (3x3) for diagonal grids, at 16 cells (4x4) for nodiag.** Diagonal grids:

```
cells:   4    9    10   16    21    25    36
c40:    +0  -17.1 -8.4 -30.3 -35.1 -38.7 -52.6
pen_off:+0  -14.8 -7.4 -25.0 -31.3 -33.2 -43.9
```

grid_2x2 (4 cells, diag) and grid_2x5 (10 cells) are mild; grid_3x3 (9 cells) already loses 17pp. Nodiag grids tolerate up to 3x3 (-6.5pp) before collapsing at 4x4 (-14.6pp). Magnitude is monotone in cell count above the threshold.

**Root cause fits the pattern:** c40 accepts unknown-edge paths and the flood-suppression penalty prevents the backup flood from recovering. Shorter chains and smaller grids complete before the stale-path window matters; longer/larger ones don't.

---

## 7. Shipping recommendation

### Default (ship this): `p2_c120` — strict confidence, no probes, no multipath

Rationale from the full sweep:
- Harmless on every non-ring topology: 234/240 non-ring scenarios at delta_pp in [-6.67, +14.67], median 0, p10 0, mean +0.04pp.
- Positive on the topologies where users actually feel pain (long chains, large grids): chain_15 +1.78pp, chain_25 +0.83pp, grid_3x7 +1.11pp, grid_6x6_nodiag +0.56pp, cluster_small +1.22pp.
- Radio overhead modest: +2.7% mean, +14% worst-case, +6.5 tx per scenario on average.
- Never hits a cliff.
- The only regression class is rings (mean -14pp on ring_6, -9pp on ring_10). Rings are structurally hostile to any strict-confidence routing because both "directions" look equally good and p2_c120 commits to one. **Document this as a known limitation and consider runtime ring detection**, but do not let it block shipping.

### Alternate mode 1 (for tree-heavy / backbone-sparse deployments): `p2_c120_h2`

- Best feature for trees (+9.8pp on tree_d4f2, +5.4pp on tree_d3f3), cluster_big (+0.3pp, max +16.7pp), chain_7 (+3.2pp), chain6_spurs (+1.0pp).
- Cost: higher variance (p10 -5.9pp non-ring, worst-case single scenarios -24pp), and +6% radio average (peak +19%, +103 tx absolute).
- Strictly worse than p2_c120 on grid_nodiag (mean -2.3pp, worst -13.3pp on grid_4x4_nodiag) and on rings (catastrophic on ring_6 -27pp). Do not flip this on globally; gate it on tree-shape heuristics or expose as a power-user toggle.

### Alternate mode 2 (experimental / disabled by default): `p2_c120_mp2`

- Multipath K=2. Mean and distribution near-identical to p2_c120 on non-ring topologies (mean -0.03pp, p10 -1.67pp, p90 +0.50pp). Slightly better than p2_c120 on chain_8 (+1.6pp) and cluster_small (+1.9pp).
- Pays small radio tax (+3.55% avg vs +2.70% for p2_c120) with negligible delivery upside in the common case.
- Worse than p2_c120 on rings (ring_10 -12.8pp vs -9.2pp).
- Keep behind a flag for environments with bursty radio availability where duplicate path insurance is worth the tx cost.

### Not shipped: `p2_c40` / `p2_c40_penalty_off`

The cliff at chain_8 / grid_3x3 is reproducible and severe (-18 to -66pp scenario losses). penalty_off reduces but does not remove the cliff. Neither variant should be exposed to users as a supported mode. They can remain as debug/experimental features only.

### Known limitation to document in release notes

Ring topologies regress with any TopoGraph-assisted feature (p2_c120 ring_6 -14pp / ring_10 -9pp). Cause is structural, not a bug. Recommended mitigation: detect ring-like subgraphs at runtime and fall back to flood for those nodes, or document that ring-deployed networks should stay on `baseline` until ring-aware handling lands.
