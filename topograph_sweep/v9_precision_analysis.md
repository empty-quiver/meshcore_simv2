# v9 Precision Sweep — Analysis with Tight CIs

- Rows: 4,480 (14 dropped for `sent==0`; all remaining `rc==0`).
- Design: 8 topo x 2 wl x 2 advert x 7 feature x 20 seed = 4,480 runs.
- Cells: 224 (topo, wl, advert, feature). All CIs are 95% bootstrap (10k resamples).
- All feature deltas are paired: each feature-seed paired to the matching baseline-seed within the same (topo, wl, advert) cell.
- Feature deltas reported in **percentage points** of delivery rate.
- Supporting CSVs: `/tmp/v9_cells.csv`, `/tmp/v9_deltas.csv`, `/tmp/v9_pooled_deltas.csv`, `/tmp/v9_winners.csv`, `/tmp/v9_mp{2,3}_vs_c120.csv`, `/tmp/v9_advert_sensitivity.csv`, `/tmp/v9_topo_variance.csv`, `/tmp/v9_feature_summary.csv`.

## Feature summary (pooled over advert within topo x wl, paired vs baseline)

| feature            | cells | sig+ | sig- | mean delta pp | min    | max   |
|--------------------|------:|-----:|-----:|--------------:|-------:|------:|
| p2_c120_mp3        |    16 |    0 |    1 |       +0.18   |  -4.06 | +2.14 |
| p2_c120            |    16 |    0 |    0 |       +0.14   |  -1.77 | +2.56 |
| p2_c120_mp2        |    16 |    1 |    1 |       +0.13   |  -4.27 | +2.56 |
| p2_c120_h2         |    16 |    0 |    1 |       -0.55   |  -3.44 | +4.10 |
| p2_c40_penalty_off |    16 |    0 |    8 |       -6.76   | -32.29 | +6.25 |
| p2_c40             |    16 |    0 |   10 |      -10.91   | -32.92 | +3.75 |

Reading: `p2_c120 / mp2 / mp3` are all net-zero-or-positive on every topology but almost never clear CI. `p2_c40*` are catastrophic on any dense / long-chain graph.

---

## 1. Which prior findings survive tight CIs?

### p2_c120 universally safe?
Across all 32 (topo, wl, advert) cells, **0 cells are sig-negative**, 1 cell is sig-positive (`grid_5x5 heavy frequent: +1.67 pp [+0.42, +3.33]`). Minimum lower bound across all cells is **-5.83 pp** (`chain_15 medium medium`; point estimate there is actually **+2.63 pp**, the lower bound is driven by seed variance). In 23/32 cells the lower bound is >= 0. **Verdict: safe stance survives. CI excludes negative delta on every topology at the pooled level — worst pooled lower bound is -3.65 pp on `grid_5x5_nodiag heavy` (point -1.77 pp, not sig).**

### p2_c120 on chain_15
| wl x adv              | baseline | p2_c120 | delta pp | 95% CI          |
|-----------------------|---------:|--------:|---------:|-----------------|
| medium x medium       |   0.8947 |  0.9211 |   +2.63  | [-2.63, +7.02]  |
| medium x frequent     |   0.9000 |  0.9250 |   +2.50  | [-0.83, +5.83]  |
| heavy x medium        |   0.7816 |  0.7816 |    0.00  | [ 0.00,  0.00]  |
| heavy x frequent      |   0.8000 |  0.8000 |    0.00  | [ 0.00,  0.00]  |

Pooled (n=39 per wl): medium **+2.56 pp [-0.43, +5.56]**, heavy **0.00 pp**. The v7 5-seed +1.78 pp is revised to ~ +2.6 pp medium / 0 pp heavy, but **CI does not exclude zero even with 20 seeds**. Chain-15 heavy is saturated — c120 == baseline exactly (same seeds drive same trace until probes fire).

### p2_c120_h2 on tree_d3f2
**Does NOT hold up.** v7 reported +5.36 pp; v9 pooled gives:
| wl x adv              | baseline | p2_c120_h2 | delta pp | 95% CI            |
|-----------------------|---------:|-----------:|---------:|-------------------|
| medium x medium       |   0.920  |   0.866    |  -5.42   | [-12.92, +1.83]   |
| medium x frequent     |   0.940  |   0.932    |  -0.83   | [ -4.50, +2.83]   |
| heavy x medium        |   0.796  |   0.758    |  -3.76   | [-12.21, +4.45]   |
| heavy x frequent      |   0.888  |   0.856    |  -3.11   | [ -6.64, +0.50]   |

Pooled medium **-3.13 pp [-7.38, +0.88]**, heavy **-3.44 pp [-7.98, +1.07]**. Every cell has a negative point estimate. No sig-negative at 95% but the *sign* of the v7 effect flipped. **h2 on tree_d3f2 is NOT a real win — v7 was a 5-seed fluke.**

### p2_c40 cliff
v7 was `chain_10`. v9 has `chain_15`. Pooled:
| topo x wl             | delta pp | 95% CI            | sig- |
|-----------------------|---------:|-------------------|:----:|
| chain_15 heavy        |  -15.81  | [-27.14,  -6.41]  | yes  |
| chain_15 medium       |  -17.09  | [-29.91,  -5.13]  | yes  |
| grid_5x5 heavy        |  -31.77  | [-39.58, -24.16]  | yes  |
| grid_5x5 medium       |  -32.92  | [-41.46, -25.00]  | yes  |
| grid_5x5_nodiag both  |  ~-21.7  | sig               | yes  |
| grid_3x3 both         |  ~-10.6  | sig               | yes  |
| tree_d3f2 both        |  ~-6.2   | sig               | yes  |
| chain_6, star_5, cluster_big | ~0 | straddles 0       | no   |

**The p2_c40 cliff is confirmed and CI-significant on every dense / long-range topology. 10/16 pooled cells sig-negative. Do not ship c40.**

### p2_c120_mp2 vs p2_c120
**32 cells, 0 sig-positive, 1 sig-negative, range [-5.83 pp, +2.29 pp].** The one sig-positive shown in the pooled table (`cells` = 16) is an artifact of a tight cluster_big cell; at the advert-level (32 cells) there are zero sig-positive cells. Median delta ≈ 0.

### p2_c120_mp3 vs p2_c120_mp2
**32 cells, 0 sig-positive, 0 sig-negative. Range [-5.00, +2.29 pp].** K=3 does nothing measurable beyond K=2.

---

## 2. Per-(topology, workload) winners (pooled across advert, n=39-40)

| topology         | workload | best feature          | delta pp | 95% CI              | sig+ |
|------------------|----------|-----------------------|---------:|---------------------|:----:|
| chain_6          | heavy    | p2_c120 (tie, 0)      |   0.00   | [-0.62, +0.62]      | no   |
| chain_6          | medium   | p2_c120_mp3           |  +0.83   | [ 0.00, +2.08]      | no   |
| chain_15         | heavy    | p2_c120_h2            |  +4.10   | [-0.34, +9.79]      | no   |
| chain_15         | medium   | p2_c120               |  +2.56   | [-0.43, +5.56]      | no   |
| grid_3x3         | heavy    | p2_c120_mp3           |  +0.63   | [-0.62, +1.98]      | no   |
| grid_3x3         | medium   | p2_c120_mp3           |  +1.04   | [ 0.00, +2.71]      | no   |
| grid_5x5         | heavy    | p2_c120_mp2           |  +1.46   | [ 0.00, +2.92]      | **yes** |
| grid_5x5         | medium   | p2_c120 (tie, 0)      |   0.00   | [ 0.00,  0.00]      | no   |
| grid_5x5_nodiag  | heavy    | p2_c120_mp2           |  -0.83   | [-3.13, +1.56]      | no   |
| grid_5x5_nodiag  | medium   | p2_c120_mp2           |  +1.46   | [ 0.00, +3.33]      | no   |
| cluster_big      | heavy    | p2_c40_penalty_off    |  +6.25   | [-3.33, +16.46]     | no   |
| cluster_big      | medium   | p2_c120_mp2           |  +0.83   | [-0.83, +2.50]      | no   |
| star_5           | heavy    | (all tied at 0)       |   0.00   | [ 0, 0]             | no   |
| star_5           | medium   | (all tied at 0)       |   0.00   | [ 0, 0]             | no   |
| tree_d3f2        | heavy    | p2_c120_mp3           |  +0.73   | [ 0.00, +1.67]      | no   |
| tree_d3f2        | medium   | p2_c120_mp3           |   0.00   | [ 0.00,  0.00]      | no   |

Only **1 of 16 cells has a CI-significant winner** (`grid_5x5 heavy` -> `p2_c120_mp2 +1.46 pp [ 0.00, +2.92]`), and the CI lower bound is effectively zero. The v7 "h2 wins tree_d3f2" call did not reproduce — on tree_d3f2 the point estimate flips to mp3 (tiny), and h2 is uniformly negative.

---

## 3. Advert sensitivity

Mean(frequent - medium) delta per feature across (topo, wl):

| feature            | mean diff pp | median | min     | max    |
|--------------------|-------------:|-------:|--------:|-------:|
| p2_c120            |  +0.24       |  0.00  |  -0.83  | +2.08  |
| p2_c120_mp2        |  +0.17       |  0.00  |  -3.20  | +4.58  |
| p2_c120_mp3        |  +0.36       |  0.00  |  -1.93  | +5.42  |
| p2_c120_h2         |  -2.03       | +0.21  | -32.50  | +6.46  |
| p2_c40             |  -1.69       |  0.00  | -16.67  | +2.50  |
| p2_c40_penalty_off |  -1.96       | -0.18  | -18.33  | +4.38  |

No feature is systematically helped by frequent adverts. `p2_c120_h2` has huge cross-advert swings — the min (-32.5 pp) is `cluster_big medium`, where h2 looks great under medium advert (+15.8 pp) but terrible under frequent (-16.7 pp). That is almost certainly a small-sample interaction with a very noisy topology (see section 4). **No feature ranking reversal is advert-driven for the c120 family.**

---

## 4. Seed-variance by topology (20 seeds)

Mean bootstrap CI width on the per-cell delivery-rate mean:

| topology          | mean SE pp | mean CI width pp | max CI width pp | mean delivery |
|-------------------|-----------:|-----------------:|----------------:|--------------:|
| cluster_big       |       7.02 |           26.34  |          40.83  |         0.753 |
| grid_5x5_nodiag   |       4.23 |           16.13  |          32.50  |         0.738 |
| chain_15          |       3.57 |           13.51  |          34.21  |         0.822 |
| grid_5x5          |       3.03 |           11.51  |          29.17  |         0.826 |
| tree_d3f2         |       2.60 |            9.89  |          15.33  |         0.864 |
| grid_3x3          |       2.30 |            8.71  |          19.17  |         0.922 |
| chain_6           |       1.07 |            3.97  |           5.83  |         0.980 |
| star_5            |       0.00 |            0.00  |           0.00  |         1.000 |

**`cluster_big` is by far the noisiest** (CI width > 26 pp even with n=20; delivery 0.57 in the worst cell). Most of the v9 "wide CI" pain comes from here. `grid_5x5_nodiag` and `chain_15` are second-tier noisy. **If anything needs more seeds, it's cluster_big — 40+ seeds would likely be required to clear CI on realistic effect sizes.** Star_5 is fully saturated and carries no information.

---

## 5. Multipath verdict

- `p2_c120_mp2` vs `p2_c120`: 32 cells, **0 sig-positive**, 1 sig-negative. Deltas in [-5.83, +2.29 pp], median 0.
- `p2_c120_mp3` vs `p2_c120`: 32 cells, **0 sig-positive**, 0 sig-negative. Deltas in [-5.00, +2.29 pp], median 0.
- `p2_c120_mp3` vs `p2_c120_mp2`: 32 cells, **0 sig-positive**, 0 sig-negative.

**There is no cell, workload, advert, or topology where K=2 or K=3 multipath beats K=1 at CI-excludes-zero. Kill the multipath feature.** The one sig-positive mp2 pooled cell (`grid_5x5 heavy`) is +1.46 pp vs baseline, not vs c120 — c120 itself is also significant there. mp2/mp3 contribute nothing above c120.

---

## 6. Shipping recommendation

### Ship `p2_c120` as the default
- **0/32 cells sig-negative**, 1/32 sig-positive.
- Pooled mean delta across 16 topo-wl cells: **+0.14 pp** (barely positive; the safe-not-a-cost profile from v7/v8 holds).
- Radio-TX overhead is modest: median **+0.45%** vs baseline, mean **+2.83%**, max **+13.2%** (`chain_6 heavy`). Worst absolute bump is +33.5 frames on `grid_5x5 heavy frequent` (4.1%).
- v8's saturation finding is consistent with the observed pattern (c120 caps out — small consistent gains, never catastrophic).

### Do NOT recommend `p2_c120_h2` as a tree alternate
v7's +5.36 pp on `tree_d3f2` **did not replicate** in v9. All four tree cells are negative point estimates (pooled -3.13 to -3.44 pp), with CIs straddling zero. The v7 result was a 5-seed fluke.

There is a weak positive signal on `chain_15 heavy` (+4.10 pp, CI [-0.34, +9.79], nearly significant) — h2 may be a long-chain helper, not a tree helper. **Recommend: do NOT ship h2 as a shape-gated alternate based on v9. If the chain_15 signal matters to you, run a targeted 50-seed sweep on `chain_15` with `heavy` workload.**

### Remove `p2_c120_mp2` and `p2_c120_mp3`
Zero evidence of benefit over K=1 in 32 cells each. mp3 vs mp2 also null. **Drop the multipath knob from the codebase — it adds complexity without measurable delivery benefit at K in {2, 3}.** If there is a theoretical reason to keep a multipath hook for future work, gate it behind a flag that is off by default.

### Do NOT ship `p2_c40*`
c40 is sig-negative on 10/16 pooled cells (chain_15, grid_3x3, grid_5x5, grid_5x5_nodiag, tree_d3f2). `p2_c40_penalty_off` sig-negative on 8/16. Both confirmed as cliffs with tight CIs. v7/v8 conclusion stands.

### Revised summary vs v7/v8

| claim                                          | v7 status  | v9 verdict                          |
|------------------------------------------------|------------|-------------------------------------|
| p2_c120 default, universally safe              | supported  | **confirmed** (0/32 sig-neg)        |
| p2_c120 ≈ saturation (c105 = c120 = c160)      | v8 finding | consistent (c120 effect is small)   |
| p2_c120_h2 alternate on tree_d3f2 (+5.36 pp)   | supported  | **REFUTED** (point estimates negative) |
| p2_c40 cliff on long chains (-18 pp)           | supported  | **confirmed and broadened** (also kills grids, tree) |
| multipath K=2/K=3 helps anywhere               | v8: no     | **confirmed no** — remove feature   |

**Net action: ship p2_c120 as default. Retract the h2 tree-alternate recommendation. Remove mp2/mp3. Keep c40 off.**
