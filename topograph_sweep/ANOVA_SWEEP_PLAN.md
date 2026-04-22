# ANOVA-style sweep plan — TopoGraph v2 knobs

After the subagent analyses (10 agents, 7 ideas cleared for pursuit), five new runtime-tunable knobs live in TopoGraph:

| CLI | Knob | Default | Range | Owner of intuition |
|---|---|---|---|---|
| `penaltymode on/off` | BGP edge penalty vs legacy suppression | `on` | on / off | BGP-agent (90% conf) |
| `edgettl <sec>` | Max edge-age considered in Dijkstra | `1800` (30min) | 60 .. 86400 | BATMAN-agent (24h → stale) |
| `confidence <0-255>` | Dijkstra accept threshold | `105` | 40 / 80 / 100 / 105 / 120 / 160 | v3 sweep (sharp boundary) |
| `maxprobehops <0-8>` | TRACE probe hop cap | `2` | 1 / 2 / 3 / 5 | v5 sweep (2 is best) |
| `multipath <1-4>` | K-path redundant send | `1` | 1 / 2 / 3 / 4 | user request |
| `autoadjust on/off` | Auto-lower confidence on small meshes | `off` | on / off | Agent A |

**Plus `obs_count` (BATMAN bonus)** is always on, no CLI. Always applied to Dijkstra cost when there's data. Could gate via CLI if we want to isolate it.

## The curse of dimensionality

Full factorial on the new knobs alone:
- 2 (penaltymode) × 6 (edgettl) × 6 (confidence) × 4 (maxprobehops) × 4 (multipath) × 2 (autoadjust) = **2,304 feature configs**
- × 15 topologies × 5 workloads × 3 adverts × 5 seeds = **2.59 million runs**
- At 2s/run with 28 workers: ~50 hours wall clock. Uneconomical.

Need **fractional factorial + targeted interaction checks**.

## Phase 1: individual effects (one-factor-at-a-time)

Hold all other knobs at their default. Vary one axis. N = 30-100 runs per cell.

**Purpose:** measure each knob's **main effect** in isolation. If a knob shows ≤1pp delivery delta across all values, pin to default and exclude from further sweeps.

```
features:
  baseline
  passive_c105_default_mp1_h2_etl1800          # our new default
  passive_c105_penalty_off                      # isolate penalty mode effect
  passive_c105_etl_60    / etl_300 / etl_3600 / etl_86400  # edge TTL sweep
  passive_c40 / c80 / c100 / c120 / c160       # confidence gradient
  passive_c105_h0 / h1 / h2 / h3 / h5 / h8      # maxprobehops (h0 = no probes)
  passive_c105_mp1 / mp2 / mp3 / mp4            # multipath
  passive_c105_auto                             # autoadjust on
```

**Expected run count**: ~22 features × 15 topos × 3 workloads × 3 adverts × 5 seeds = **14,850 runs**. ~20 min with 28 workers.

**Success metric:** effect size (Cohen's d) ≥ 0.3 for inclusion in Phase 2.

## Phase 2: two-factor interactions (Latin hypercube sample)

Some combinations are theoretically promising; others are wasteful. Use **Latin hypercube sampling** to cover the high-dimensional space efficiently:

Fix 2 knobs to their default, vary the other 4 across 3 levels each. 3^4 = 81 combos, 3 seeds, 8 topology+workload combos (strategically chosen: chain_6/light, grid_5x5/heavy, tree_d3f2/sparse, seapdx/medium, etc.).

**Purpose:** detect **interactions** (e.g., penalty + high confidence might cancel out; multipath + large edge_ttl might amplify).

**Expected runs:** 81 × 8 × 3 = ~1,944. ~3-5 min.

## Phase 3: real-topology validation

Phase 1 + 2 will identify 3-5 candidate configurations. Validate ON REAL TOPOLOGIES (Gdansk, Seattle+Portland, MA+NH) × 7 seeds:

- `baseline`
- `default` (our candidate defaults)
- `default_penalty_off` (compare A)
- `default_with_mp2` (compare B)
- `most aggressive viable config` (compare C)

~5 × 3 × 7 = 105 runs. ~15 min (real topologies are slower).

## Phase 4: ANOVA interpretation

For each response variable (`delivery_rate`, `radio_tx`, `collisions`, `ackpath_tx`), fit a **linear model with interactions**:

```python
# pseudocode
import statsmodels.formula.api as smf
model = smf.ols(
    'delivery_rate ~ C(penaltymode) + C(confidence) + C(edgettl) '
    '+ C(maxprobehops) + C(multipath) + C(topology) + C(workload) '
    '+ C(penaltymode):C(confidence)       # penalty may interact with threshold'
    '+ C(multipath):C(confidence)         # multipath payoff depends on path acceptance'
    '+ C(topology):C(penaltymode)         # penalty probably helps chains more than stars'
    '+ C(topology):C(multipath)',         # multipath probably helps chains more than stars
    data=df
).fit()
anova_lm(model, typ=3)
```

**Key interactions to probe in reporting:**

1. **penaltymode × topology**: BGP-agent hypothesis is penalty shines in redundant-path topologies (grids) more than linear ones (chains). Verify.
2. **multipath × confidence**: MPTCP-agent's "coupled subflows" argument says uncoupled multipath at loose confidence should hurt more than at strict. Verify.
3. **edgettl × advert_cadence**: stale edges should matter LESS when adverts are frequent (fresh data) and MORE when sparse. Verify.
4. **maxprobehops × mesh_density**: probes should help more in sparse meshes (where edges are underqualified) and hurt more in dense (contention). Verify.

## Phase 5: minimal-reproducer sweep for any anomaly found

When an interaction looks significant (p < 0.01, effect size > 1pp), re-run with 20 seeds on the specific cells to confirm it's not a 5-seed fluke.

## Sweep implementation

Existing harness (`topograph_sweep/sweep2.py`) supports all new features — just extend the `FEATURES` dict with new named variants. Each Phase 1-3 sweep is a separate CSV:

- `sweep_v6_p1_individual.csv` (one-factor-at-a-time)
- `sweep_v6_p2_interactions.csv` (LHS)
- `sweep_v6_p3_real.csv` (Gdansk + SEAPDX + MANH validation)

Analyzer (`analyze2.py`) + a new `anova.py` (to be written, using pandas + statsmodels) consume these.

## Budget

- Phase 1: ~20 min
- Phase 2: ~5 min
- Phase 3: ~15 min (real topologies)
- Phase 4-5: reruns depending on findings, budget ~1-2 hours
- **Total: ~2-3 hours of compute** for a thorough statistical characterization of the new knob space

## Deliverable

A **decision table** per use case:

```
topology class   workload       recommended config
-----------------------------------------------------------
star_*           any            passive_c40 + mp1 + h2 + etl_300
chain_<6         any            passive_c40 + mp1 + h2 + etl_300
chain_>=10       any            passive_c105 + penalty_on + mp2 + etl_1800
grid_small       sparse         passive_c120 + mp2 + probes_h2
grid_large       any            passive_c120 + mp1 + probes_off
tree             sparse         passive_c105 + probes_h3
real (Gdansk)    any            passive_c120 + penalty_on + mp1 + etl_1800
real (SEAPDX)    any            passive_c120 + penalty_on + mp1 + h0 (no probes)
```

From that table: pick the **single config that wins most rows** as the shipping default; the rest become documented alternate modes.
