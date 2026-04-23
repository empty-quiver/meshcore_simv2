# v8 Factorial Sweep — ANOVA + Interaction Analysis

- Treatment rows used: 7830  (sent==0 dropped: 270)
- Baseline rows: 87
- Factors: conf [40, 100, 105, 120, 160], mp [1, 2, 3], pen [0, 1], h [0, 2, 5]
- Topologies (10): ['chain_10', 'chain_15', 'chain_6', 'cluster_big', 'grid_3x3', 'grid_5x5', 'grid_5x5_nodiag', 'star_5', 'star_8', 'tree_d3f2']
- Workloads (3): ['heavy', 'medium', 'sparse']

- Overall mean delivery rate (treatment): 88.51%
- Baseline mean delivery rate:           91.51%

## 1. ANOVA tables

### Overall

| term | df | sum_sq | F | p | sig(p<0.01) |
|---|---|---|---|---|---|
| C(conf) | 4 | 13.500 | 94.23 | 2.25e-78 | YES |
| C(mp) | 2 | 0.077 | 1.07 | 0.341 |  |
| C(pen) | 1 | 0.333 | 9.29 | 0.00231 | YES |
| C(h) | 2 | 0.061 | 0.85 | 0.426 |  |
| C(topology) | 9 | 75.887 | 235.41 | 0 | YES |
| C(workload) | 2 | 4.189 | 58.47 | 6.27e-26 | YES |
| C(conf):C(mp) | 8 | 0.025 | 0.09 | 1 |  |
| C(conf):C(pen) | 4 | 0.499 | 3.48 | 0.00754 | YES |
| C(conf):C(h) | 8 | 0.034 | 0.12 | 0.998 |  |
| C(mp):C(pen) | 2 | 0.000 | 0.00 | 0.999 |  |
| C(mp):C(h) | 4 | 0.012 | 0.09 | 0.987 |  |
| C(pen):C(h) | 2 | 0.001 | 0.01 | 0.992 |  |
| C(conf):C(topology) | 36 | 17.803 | 13.81 | 1.45e-79 | YES |
| C(h):C(topology) | 18 | 4.805 | 7.45 | 1.33e-19 | YES |
| C(mp):C(topology) | 18 | 0.380 | 0.59 | 0.91 |  |

### Workload = heavy

| term | df | sum_sq | F | p | sig(p<0.01) |
|---|---|---|---|---|---|
| C(conf) | 4 | 3.659 | 55.90 | 3.31e-45 | YES |
| C(mp) | 2 | 0.039 | 1.19 | 0.306 |  |
| C(pen) | 1 | 0.568 | 34.72 | 4.33e-09 | YES |
| C(h) | 2 | 0.199 | 6.07 | 0.00235 | YES |
| C(topology) | 9 | 16.741 | 113.66 | 6.32e-179 | YES |
| C(conf):C(mp) | 8 | 0.067 | 0.51 | 0.846 |  |
| C(conf):C(pen) | 4 | 0.852 | 13.02 | 1.71e-10 | YES |
| C(conf):C(h) | 8 | 0.012 | 0.09 | 0.999 |  |
| C(mp):C(pen) | 2 | 0.002 | 0.06 | 0.937 |  |
| C(mp):C(h) | 4 | 0.033 | 0.50 | 0.736 |  |
| C(pen):C(h) | 2 | 0.007 | 0.22 | 0.804 |  |
| C(conf):C(topology) | 36 | 2.970 | 5.04 | 2.09e-20 | YES |
| C(h):C(topology) | 18 | 0.941 | 3.19 | 6.15e-06 | YES |
| C(mp):C(topology) | 18 | 0.506 | 1.72 | 0.0303 |  |

### Workload = medium

| term | df | sum_sq | F | p | sig(p<0.01) |
|---|---|---|---|---|---|
| C(conf) | 4 | 4.763 | 46.49 | 9.91e-38 | YES |
| C(mp) | 2 | 0.078 | 1.52 | 0.218 |  |
| C(pen) | 1 | 0.082 | 3.20 | 0.0736 |  |
| C(h) | 2 | 0.092 | 1.79 | 0.167 |  |
| C(topology) | 9 | 16.083 | 69.78 | 5.31e-115 | YES |
| C(conf):C(mp) | 8 | 0.023 | 0.11 | 0.999 |  |
| C(conf):C(pen) | 4 | 0.123 | 1.20 | 0.308 |  |
| C(conf):C(h) | 8 | 0.108 | 0.53 | 0.838 |  |
| C(mp):C(pen) | 2 | 0.003 | 0.05 | 0.95 |  |
| C(mp):C(h) | 4 | 0.004 | 0.04 | 0.997 |  |
| C(pen):C(h) | 2 | 0.001 | 0.02 | 0.978 |  |
| C(conf):C(topology) | 36 | 5.028 | 5.45 | 7.11e-23 | YES |
| C(h):C(topology) | 18 | 11.748 | 25.48 | 1.95e-78 | YES |
| C(mp):C(topology) | 18 | 0.303 | 0.66 | 0.856 |  |

### Workload = sparse

| term | df | sum_sq | F | p | sig(p<0.01) |
|---|---|---|---|---|---|
| C(conf) | 4 | 5.147 | 26.99 | 5.96e-22 | YES |
| C(mp) | 2 | 0.253 | 2.66 | 0.0703 |  |
| C(pen) | 1 | 0.002 | 0.04 | 0.851 |  |
| C(h) | 2 | 0.018 | 0.19 | 0.83 |  |
| C(topology) | 9 | 77.333 | 180.21 | 1.31e-263 | YES |
| C(conf):C(mp) | 8 | 0.420 | 1.10 | 0.359 |  |
| C(conf):C(pen) | 4 | 0.003 | 0.01 | 1 |  |
| C(conf):C(h) | 8 | 0.014 | 0.04 | 1 |  |
| C(mp):C(pen) | 2 | 0.001 | 0.01 | 0.991 |  |
| C(mp):C(h) | 4 | 0.031 | 0.16 | 0.958 |  |
| C(pen):C(h) | 2 | 0.001 | 0.01 | 0.994 |  |
| C(conf):C(topology) | 36 | 13.729 | 8.00 | 1.86e-38 | YES |
| C(h):C(topology) | 18 | 3.564 | 4.15 | 9.87e-09 | YES |
| C(mp):C(topology) | 18 | 0.661 | 0.77 | 0.737 |  |

## 2. Main-effect-per-knob

### Factor: conf

| level | mean_delivery | delta_vs_grand_pp | cohens_d | n |
|---|---|---|---|---|
| 105.0 | 91.90% | +3.39 | +0.151 | 1566.0 |
| 120.0 | 91.90% | +3.39 | +0.151 | 1566.0 |
| 160.0 | 91.90% | +3.39 | +0.151 | 1566.0 |
| 40.0 | 83.42% | -5.09 | -0.227 | 1566.0 |
| 100.0 | 83.42% | -5.09 | -0.227 | 1566.0 |

### Factor: mp

| level | mean_delivery | delta_vs_grand_pp | cohens_d | n |
|---|---|---|---|---|
| 1.0 | 88.85% | +0.34 | +0.015 | 2610.0 |
| 2.0 | 88.58% | +0.08 | +0.003 | 2610.0 |
| 3.0 | 88.09% | -0.42 | -0.019 | 2610.0 |

### Factor: pen

| level | mean_delivery | delta_vs_grand_pp | cohens_d | n |
|---|---|---|---|---|
| 0.0 | 89.16% | +0.65 | +0.029 | 3915.0 |
| 1.0 | 87.86% | -0.65 | -0.029 | 3915.0 |

### Factor: h

| level | mean_delivery | delta_vs_grand_pp | cohens_d | n |
|---|---|---|---|---|
| 2.0 | 88.90% | +0.39 | +0.018 | 2610.0 |
| 5.0 | 88.34% | -0.17 | -0.007 | 2610.0 |
| 0.0 | 88.28% | -0.23 | -0.010 | 2610.0 |

## 3. Top interaction patterns (by max range pp)

| factors | mean_range_pp | max_range_pp |
|---|---|---|
| conf x topology | 33.27 | 40.51 |
| h x topology | 29.74 | 38.10 |
| mp x topology | 29.74 | 30.62 |
| conf x pen | 1.30 | 3.26 |
| mp x pen | 1.30 | 1.33 |
| conf x mp | 0.76 | 1.29 |
| conf x h | 0.74 | 1.24 |
| mp x h | 0.68 | 0.77 |
| pen x h | 0.62 | 0.68 |

### conf x topology (delivery %)

| conf \\ topology | chain_10 | chain_15 | chain_6 | cluster_big | grid_3x3 | grid_5x5 | grid_5x5_nodiag | star_5 | star_8 | tree_d3f2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 40 | 59.5 | 68.5 | 98.3 | 68.3 | 95.8 | 76.5 | 74.5 | 100.0 | 97.2 | 87.6 |
| 100 | 59.5 | 68.5 | 98.3 | 68.3 | 95.8 | 76.5 | 74.5 | 100.0 | 97.2 | 87.6 |
| 105 | 95.7 | 88.5 | 98.8 | 71.6 | 98.6 | 90.3 | 84.5 | 100.0 | 100.0 | 92.4 |
| 120 | 95.7 | 88.5 | 98.8 | 71.6 | 98.6 | 90.3 | 84.5 | 100.0 | 100.0 | 92.4 |
| 160 | 95.7 | 88.5 | 98.8 | 71.6 | 98.6 | 90.3 | 84.5 | 100.0 | 100.0 | 92.4 |

### h x topology (delivery %)

| h \\ topology | chain_10 | chain_15 | chain_6 | cluster_big | grid_3x3 | grid_5x5 | grid_5x5_nodiag | star_5 | star_8 | tree_d3f2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 82.7 | 83.8 | 99.0 | 61.9 | 97.1 | 89.3 | 76.9 | 100.0 | 98.9 | 91.3 |
| 2 | 81.2 | 78.7 | 98.4 | 75.1 | 97.7 | 82.5 | 82.8 | 100.0 | 98.9 | 91.1 |
| 5 | 79.7 | 78.9 | 98.4 | 73.8 | 97.7 | 82.5 | 81.7 | 100.0 | 98.9 | 88.9 |

### mp x conf (delivery %)

| mp \\ conf | 40 | 100 | 105 | 120 | 160 |
|---|---|---|---|---|---|
| 1 | 84.0 | 84.0 | 92.0 | 92.0 | 92.0 |
| 2 | 83.5 | 83.5 | 92.0 | 92.0 | 92.0 |
| 3 | 82.8 | 82.8 | 91.6 | 91.6 | 91.6 |

### pen x conf (delivery %)

| pen \\ conf | 40 | 100 | 105 | 120 | 160 |
|---|---|---|---|---|---|
| 0 | 85.1 | 85.1 | 91.9 | 91.9 | 91.9 |
| 1 | 81.8 | 81.8 | 91.9 | 91.9 | 91.9 |

## 4. Best 4-tuple globally

Top 10 tuples by mean delivery rate (across all topologies/workloads/seeds):

| conf | mp | pen | h | delivery | radio_tx | probes_fired | n |
|---|---|---|---|---|---|---|---|
| 160 | 1 | 0 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 105 | 1 | 1 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 105 | 1 | 0 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 120 | 1 | 0 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 120 | 1 | 1 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 160 | 1 | 1 | 2 | 92.39% | 332.7 | 3.02 | 87 |
| 105 | 2 | 1 | 0 | 92.02% | 316.6 | 0.00 | 87 |
| 105 | 2 | 0 | 0 | 92.02% | 316.6 | 0.00 | 87 |
| 160 | 2 | 1 | 0 | 92.02% | 316.6 | 0.00 | 87 |
| 160 | 2 | 0 | 0 | 92.02% | 316.6 | 0.00 | 87 |

**v7 shipping tuple** (c120_mp1_pen1_h0): delivery 91.89%, radio_tx 314.1, probes 0.00
**v8 global best**    (c160_mp1_pen0_h2): delivery 92.39%, radio_tx 332.7, probes 3.02
**Delta**: +0.50 pp delivery, +18.6 radio_tx, +3.02 probes

## 5. Per-topology winners

| topology | winner | winner_delivery | global_best_here | gap_pp |
|---|---|---|---|---|
| chain_10 | c105_mp1_pen0_h0 | 98.61% | 95.83% | +2.78 |
| chain_15 | c105_mp2_pen0_h0 | 94.26% | 87.59% | +6.67 |
| chain_6 | c105_mp3_pen0_h0 | 100.00% | 98.15% | +1.85 |
| cluster_big | c40_mp1_pen1_h2 | 88.70% | 72.22% | +16.48 |
| grid_3x3 | c105_mp1_pen0_h0 | 98.61% | 98.61% | +0.00 |
| grid_5x5 | c105_mp1_pen0_h0 | 94.07% | 90.37% | +3.70 |
| grid_5x5_nodiag | c105_mp2_pen0_h2 | 89.44% | 87.59% | +1.85 |
| star_5 | c40_mp1_pen0_h0 | 100.00% | 100.00% | +0.00 |
| star_8 | c105_mp1_pen0_h0 | 100.00% | 100.00% | +0.00 |
| tree_d3f2 | c105_mp1_pen0_h2 | 94.65% | 94.65% | +0.00 |

### Universal-candidate search (min worst-case gap across topologies)

Top 10 tuples with smallest max topology gap:

| conf | mp | pen | h | mean_rate | max_topo_gap_pp |
|---|---|---|---|---|---|
| 105 | 2 | 0 | 5 | 91.97% | 14.63 |
| 160 | 3 | 0 | 5 | 91.26% | 14.63 |
| 160 | 2 | 1 | 5 | 91.97% | 14.63 |
| 160 | 2 | 0 | 5 | 91.97% | 14.63 |
| 120 | 3 | 1 | 5 | 91.26% | 14.63 |
| 120 | 3 | 0 | 5 | 91.26% | 14.63 |
| 120 | 2 | 1 | 5 | 91.97% | 14.63 |
| 105 | 3 | 1 | 5 | 91.26% | 14.63 |
| 105 | 3 | 0 | 5 | 91.26% | 14.63 |
| 105 | 2 | 1 | 5 | 91.97% | 14.63 |

Tuples with max topology gap <= 1pp: **0**

## 6. Radio-cost Pareto frontier

Delta vs baseline, mean across all scenarios. Frontier = non-dominated tuples.

| conf | mp | pen | h | dr_delta_pp | radio_delta |
|---|---|---|---|---|---|
| 100 | 1 | 1 | 0 | -9.804 | -21.41 |
| 100 | 1 | 0 | 0 | -5.877 | -13.66 |
| 100 | 1 | 0 | 2 | -5.184 | +5.25 |
| 120 | 1 | 0 | 0 | +0.374 | +6.63 |
| 120 | 1 | 1 | 0 | +0.374 | +6.63 |
| 160 | 2 | 1 | 0 | +0.508 | +9.07 |
| 105 | 1 | 0 | 2 | +0.875 | +25.23 |

### Top tuples per radio-cost decile

| decile | best_conf_mp_pen_h | delivery | radio_tx |
|---|---|---|---|
| 0 | c40_mp1_pen0_h0 | 85.63% | 293.8 |
| 1 | c40_mp3_pen0_h0 | 83.56% | 298.9 |
| 2 | c105_mp1_pen0_h0 | 91.89% | 314.1 |
| 3 | c105_mp2_pen0_h0 | 92.02% | 316.6 |
| 4 | c105_mp3_pen0_h0 | 91.78% | 317.7 |
| 5 | c40_mp3_pen0_h2 | 85.26% | 319.5 |
| 6 | c105_mp1_pen0_h2 | 92.39% | 332.7 |
| 7 | c105_mp2_pen0_h2 | 92.00% | 334.0 |
| 8 | c105_mp2_pen0_h5 | 91.97% | 340.2 |
| 9 | c105_mp2_pen1_h5 | 91.97% | 340.2 |

## 6b. Probe-hop cost summary

| h | mean_delivery | mean_probes_fired | mean_radio_tx |
|---|---|---|---|
| 0 | 88.28% | 0.00 | 307.0 |
| 2 | 88.90% | 3.01 | 325.3 |
| 5 | 88.34% | 3.81 | 331.1 |

### h cost per workload

| workload | h | delivery | probes | radio_tx |
|---|---|---|---|---|
| heavy | 0 | 87.87% | 0.00 | 366.1 |
| heavy | 2 | 88.98% | 3.13 | 392.0 |
| heavy | 5 | 86.84% | 3.92 | 393.3 |
| medium | 0 | 91.03% | 0.00 | 288.6 |
| medium | 2 | 91.34% | 3.00 | 301.4 |
| medium | 5 | 92.41% | 3.79 | 310.5 |
| sparse | 0 | 85.94% | 0.00 | 266.3 |
| sparse | 2 | 86.38% | 2.91 | 282.4 |
| sparse | 5 | 85.76% | 3.73 | 289.5 |

## Hypothesis verdicts (A-D)

| hypothesis | term | p_overall | p_heavy | p_medium | p_sparse | verdict |
|---|---|---|---|---|---|---|
| A: conf x topology (c40 cliff) | C(conf):C(topology) | 1.45e-79 | 2.09e-20 | 7.11e-23 | 1.86e-38 | SUPPORTED |
| B: h x topology (probes help sparse, hurt dense) | C(h):C(topology) | 1.33e-19 | 6.15e-06 | 1.95e-78 | 9.87e-09 | SUPPORTED |
| C: mp x conf (loose conf + multipath compounds loss) | C(conf):C(mp) | 1 | 0.846 | 0.999 | 0.359 | NOT SUPPORTED |
| D: pen x conf (penalty matters less at strict conf) | C(conf):C(pen) | 0.00754 | 1.71e-10 | 0.308 | 1 | SUPPORTED |

## Top 5 interaction patterns — narrative

1. **conf x topology** — Largest interaction (40.5 pp max range). c40/c100 collapses hardest on chain_10 (59.5% vs 95.7% at c>=105), chain_15 (68.5% vs 88.5%), grid_5x5 (76.5% vs 90.3%), grid_5x5_nodiag (74.5% vs 84.5%). Star topos unaffected. Confirms v7 c40-cliff and shows it extends to grid_5x5.

2. **h x topology** — Second-largest interaction (38.1 pp max range). Probes help cluster_big (+13.2 pp going h0->h2) and grid_5x5_nodiag (+5.9 pp), but hurt chain_15 (-5.1 pp) and grid_5x5 (-6.8 pp). Dense-with-alt-paths benefits; long-chain/grid-diag is hurt. Supports v7 finding that probes are topology-specialized.

3. **mp x topology** — mp main-effect is tiny (+/- 0.4 pp) but the mp:topology interaction row shows ~30 pp range across cells - this is almost entirely driven by topology main-effect leakage (Type II SS attributes cross-cell variance). mp:topology is NOT significant (p=0.91 overall). Conclusion: multipath does not differentially help any topology.

4. **conf x pen** — Significant (p=0.00754). At c40/c100, pen=0 beats pen=1 by 3.3 pp (85.1% vs 81.8%) - legacy 60s suppression hurts when confidence is loose. At c>=105, pen has zero effect (both 91.9%). Supports Hypothesis D: penalty stops mattering once paths are trustworthy.

5. **pen main effect (heavy workload)** — In heavy workload, pen and conf:pen are highly significant (p=4.3e-9 and 1.7e-10). But this is fully driven by c40/c100 (pen=0: 87.0%, pen=1: 79.6%); at c>=105 pen has zero effect in every workload. **Implication**: at the shipping conf=120, pen is a no-op. No reason to flip pen unless we drop conf.

## 7. Shipping recommendation refinement

| tuple | mean_delivery | radio_tx | probes | max_topo_gap_pp |
|---|---|---|---|---|
| c120_mp1_pen1_h0 (v7 shipping) | 91.89% | 314.1 | 0.00 | 20.00 |
| c120_mp1_pen0_h0 | 91.89% | 314.1 | 0.00 | 20.00 |
| c160_mp1_pen0_h2 | 92.39% | 332.7 | 3.02 | 16.48 |
| c105_mp2_pen0_h0 | 92.02% | 316.6 | 0.00 | 20.00 |
| c105_mp1_pen0_h2 | 92.39% | 332.7 | 3.02 | 16.48 |

### Verdict

v8 does **not** change the v7 recommendation. Key reasons:

1. **conf levels bin into 2 groups**: c40==c100 (loose) and c105==c120==c160 (strict). Once conf>=105 the threshold saturates and raising it further changes nothing. c120 stays a safe pick; c160 buys nothing.
2. **pen only matters in the loose-conf regime**. At c120, pen=0 and pen=1 are identical in every workload (confirmed: heavy c120_mp1_pen1_h0 = heavy c120_mp1_pen0_h0 = 91.29%). The significant conf:pen ANOVA term is entirely driven by c40/c100, where pen=0 recovers ~3 pp. Since we ship at c120, there is no reason to flip pen.
3. **h=2 gives +0.5 pp delivery globally at +18 radio_tx**, but hurts chain_15 (-5 pp) and grid_5x5 (-7 pp). Not a universal default. Keep h=0 shipped.
4. **mp has no significant main or interaction effect** (p=0.34 overall, worst cell-level loss 0.4 pp). Stay at mp=1.

**Recommendation: keep `c120_mp1_pen1_h0` (v7 default) as the shipping tuple.** All v8 alternatives that beat it do so by <=0.5 pp and come with topology risk (h=2 cliffs on chain_15/grid_5x5) or zero benefit (pen=0 at c120).

**Optional topology-specific presets** for sites known to be chain-heavy or cluster_big-heavy:
- cluster_big: `c40_mp1_pen1_h2` -> 88.7% (vs 71.6% at global-best tuple here, +16.5 pp) - but this is the c40 regime that is toxic on chains/grids, so only deploy if the topology is stable.
- tree_d3f2, grid_5x5_nodiag: `c120_mp1_pen1_h2` gains a few pp with manageable risk.

**No universal tuple exists within 1 pp of per-topology optima** (worst-case gap 14.6 pp). Universal-deployment guidance: stay at `c120_mp1_pen1_h0`. If topology detection is available at runtime, switch to h=2 only for sparse-with-alt-paths (cluster_big, grid_5x5_nodiag) and never for long chains or dense diag grids.
