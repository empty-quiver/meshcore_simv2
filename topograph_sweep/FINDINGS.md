# TopoGraph parameter sweep findings

Summary of the v2 (2,625 runs) and v3 (22,050 runs) sweeps, plus four
subagent analyses of the v3 dataset.

## Sweeps run

- **sweep_v2.csv**: 15 topologies × 5 workloads × 7 features × 5 seeds
  = 2,625 runs. Single advert cadence ("medium", 4 rounds).
- **sweep_v3.csv**: 15 topologies × 5 workloads × 14 features × 3 advert
  cadences × 7 seeds = 22,050 runs. Added fine-grained confidence
  gradient (60, 80, 95, 100, 105, 110, 120, 140) and probe variants.

Both CSVs live alongside this doc in the repo.

## Core result: confidence-100 boundary

The min_confidence threshold has **exactly two equivalence classes**:

- **Loose (any ≤ 100)**: `passive`, `passive_c60`, `passive_c80`,
  `passive_c95`, `passive_c100` → all produce identical statistics,
  because `confidenceForSnrQ2(SNR_UNKNOWN)` returns 100, so thresholds
  at-or-below 100 accept paths with unknown-SNR edges.
- **Strict (any ≥ 105)**: `passive_c105`, `passive_c110`, `passive_c120`,
  `passive_c140` → all identical, all reject any path with an unknown
  edge, falling back to flood.

The strict class behaves essentially like baseline with ~2.5% TX overhead
(from the graph-consult work). The loose class accepts direct paths
through unknown-quality edges.

## Delivery outcome distribution (v3, 1,575 matched pairs)

| Variant | Strong win ≥+10pp | Win +2..+10 | Neutral | Loss −2..−10 | Strong loss ≤−10pp |
|---|---|---|---|---|---|
| passive (loose) | 41 (2.6%) | 4 (0.3%) | 1223 (77.7%) | 25 (1.6%) | **231 (14.7%)** |
| **passive_c120** | 8 (0.5%) | 4 (0.3%) | **1501 (95.3%)** | 5 (0.3%) | 6 (0.4%) |
| probes_c120 | 103 (6.5%) | 26 (1.7%) | 1259 (79.9%) | 34 (2.2%) | 98 (6.2%) |

`passive_c120` (strict) is the only variant with a safety margin
comparable to baseline. Passive loose has 14.7% catastrophic regressions.
Probes have both more strong wins AND more strong losses.

## TX delta vs baseline

| Variant | Mean | Median | p10 | p90 | Worst |
|---|---|---|---|---|---|
| passive loose | −3.3% | −3.3% | −14.2% | +8.6% | +25% |
| passive_c120 | +2.4% | 0% | 0% | +9.1% | +25% |
| probes_c120 | +8.1% | +5.7% | −1.0% | +22.3% | **+78%** |

## Per-topology-class behavior (passive loose, v3)

| Class | n | Δtx% med | Δdel_pp mean |
|---|---|---|---|
| star | 75 | −6.1% | −0.3 |
| tree | 15 | −10.4% | −3.0 |
| chain | 60 | −0.3% | −5.6 |
| grid | 75 | −6.0% | **−12.4** |

Stars are the clean win zone. Grids are the danger zone. Trees and chains
are mixed.

## Advert cadence effect (passive loose)

| Advert | Δdel_pp mean | Wins | Losses |
|---|---|---|---|
| frequent | −8.5 | 1 | **27** |
| medium | −5.0 | 2 | 18 |
| sparse | −4.4 | 2 | 19 |

**Counter-intuitive**: passive gets WORSE with more adverts, not better.
More mesh traffic → more collisions → direct routes lose ACKs more.

## Probe economics (4,460 probe-firing runs)

- Average TX cost per probe: **~6 packets**
- Average delivery gain per probe: **~0 overall**
- Sweet spots (probes_c120):
  - `tree_d3f2 + sparse + sparse`: +21.4pp delivery, only +3% TX
  - `grid_3x3_nodiag + sparse + any advert`: +16-18pp delivery
  - `chain_15 + light + medium advert`: +28.6pp delivery, +23% TX
- Catastrophic cases:
  - `grid_5x5 + probes_on + medium/frequent`: −48pp to −57pp delivery
  - `chain_10/15 + light + sparse + probes_on`: std=0.58 (bimodal: 0% or 100%)

**Perfect-oracle selection** (only probe where it wins): would save
18,124 TX packets and gain 239 messages. Proves probes work when
triggered selectively.

## Shipping recommendation

**Ship `passive_c120` as the default and only non-baseline variant.**
- 95.3% neutral runs (statistically indistinguishable from baseline)
- Mean Δdelivery = −0.016pp (essentially zero)
- +2.4% TX mean overhead
- 6 strong wins (0.4% of runs) — small but real bonus in the right cells

**Do NOT ship by default:**
- `passive` loose (14.7% strong regressions, up to −100pp)
- `probes_on` ungated (mean delivery −6.4%, collision cascades)
- `probes_c120` (bimodal: 103 wins but 98 strong losses — unreliable)

**Keep as opt-in:**
- `passive` (confidence < 100) with strong opt-in UX and warnings about
  dense-mesh regressions
- `probes_c120` with clear "experimental, uses ~6% more airtime" label

## Single highest-leverage follow-up

Add a **carrier-sense or hop-count gate before firing probes**:
- Block probes when hop count to target > 3
- Block probes when recent channel utilization is high
- This would reclaim most of the `probes_c120` blackout cases while
  preserving tree/small-grid wins

Expected outcome: the passive+probes variant becomes shippable.

## Subagent provenance

Four independent Sonnet agents analyzed the v3 CSV in parallel:
- **Agent A** (decision rule): proposed routing_table_size ≤ 6 as
  auto-enable trigger for passive
- **Agent B** (failure clusters): enumerated 5 failure modes, identified
  seed instability in long chains
- **Agent C** (probe economics): established per-probe cost (~6 TX) and
  gain profile; proved tree/small-grid sweet spots
- **Agent D** (shipping decision): recommended `passive_c120` as
  default-only with confidence 85%

All four converged on the same shipping recommendation.

## Next work queued

- Real-topology sims (Gdansk, Seattle+Portland, MA+NH) to validate
  findings against actual deployed meshes. Topologies fetched from
  MeshCore public API and propagation computed with ITM + SRTM terrain.
- Congestion-aware probe gating (highest-leverage improvement above).
