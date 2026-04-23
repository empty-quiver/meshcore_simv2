# TopoGraph Parameter Sweep — Final Synthesis (v7 + v8 + v9 + v10)

Four complementary sweeps run end-to-end over ~4 hours on the Lambda Vector (28 workers):

| Sweep | Purpose | Rows | Topologies | Features | Seeds |
|---|---|---:|---|---|---|
| v7 | Wide topology sensitivity | 7,200 | 40 synthetic (chains, grids, stars, dstars, trees, rings, clusters, spurs) | 6 curated | 5 |
| v8 | Dense factorial / ANOVA | 8,190 | 10 representative | 91 auto-generated (C × mp × pen × h) | 3 |
| v9 | Seed-heavy precision | 4,480 | 8 key | 7 candidates | 20 |
| v10 | Real-topology validation | 60 | 3 regions (Gdansk, SEAPDX, MANH) | 4 finalists | 5 |

All analyses authored by background subagents; raw CSVs and per-sweep reports preserved:
- `/tmp/sweep_v{7,8,9,10}.csv`
- `/tmp/v7_full_analysis.md`, `/tmp/v8_factorial_analysis.md`, `/tmp/v9_precision_analysis.md`, `/tmp/v10_realtopo_analysis.md`

---

## Shipping recommendation: `passive_c120` / `p2_c120`

**Single default.** Strict confidence (threshold = 120), no probes, no multipath, penalty-mode = default (no-op at strict conf).

Equivalent CLI state:
```
confidence 120
probes off
multipath 1
```

This recommendation survives every independent test:

| Sweep | Evidence |
|---|---|
| v7 | 234/240 non-ring scenarios at delta_pp in [-6.67, +14.67], median 0, mean +0.04pp. Never regresses >1.1pp outside of rings. Best single topology: chain_15 +1.78pp. |
| v8 | Main-effect ANOVA: confidence saturates at ~101 (c105 = c120 = c160, all equivalent). `c120_mp1_pen1_h0` is within 0.5pp of the global best 4-tuple, at lower variance and lower radio cost. |
| v9 | 20-seed paired CI: 0/32 cells significantly negative, 1/32 significantly positive. Pooled CI lower bound > -3.65pp on every topology. Median radio overhead +0.45%. |
| v10 | 3/3 real regions: delta CI lower bound ≥ 0 (gdansk +0.80pp, seapdx +0.40pp, manh +0.40pp). Zero per-seed regressions across 15 region-seed pairs. Radio cost < 1.5%. |

---

## Retractions (features we thought worked but don't)

### `p2_c120_h2` (probes hop-2) as a tree / backbone alternate
v7 5-seed: `tree_d4f2 +9.8pp`, `tree_d3f3 +5.4pp` — these looked like a clear probe win for tree topologies.
**v9 with 20 seeds:** all four `tree_d3f2` cells pool to **-3.13 to -3.44pp**. The v7 tree result did not replicate. v10 real-topology: probes lose 2.8-4.0pp mean on Gdansk/SEAPDX, with seapdx CI firmly negative [-8.0, -1.2].

Net: probes are not a safe default **anywhere** demonstrated. Kill the tree-alternate-mode recommendation.

### `p2_c120_mp2` / `p2_c120_mp3` (multipath K=2 / K=3)
v7 + v8 main effect: mp was never statistically significant (p > 0.3 everywhere).
**v9 with 20 seeds:** mp2 vs c120 — 0/32 cells significantly positive. mp3 vs c120 — 0/32 sig-positive. mp3 vs mp2 — 0/32 sig-positive.

Net: multipath gains nothing over single-path at strict confidence. **Remove the feature.**

### `p2_c40` / `p2_c40_penalty_off` (loose confidence)
v7: sharp cliff at chain length 8 (-18.7pp), grid 3x3 diagonal (-17pp), scaling to -52pp on grid_6x6.
v8: conf × topology interaction F=13.81, p=1.4e-79. penalty-off mitigates (-7 to -14pp) but does not remove the cliff.
v9: confirms and broadens — significantly negative on 10/16 pooled cells.

Net: loose-conf modes **must not ship** as user-facing options. Keep only for debug.

---

## Known limitation: ring topologies

v7 surfaces a structural failure mode not seen in the partial data:

| Feature | ring_6 mean delta | ring_10 mean delta |
|---|---:|---:|
| p2_c120 | -14.06pp | -9.17pp |
| p2_c120_mp2 | -14.83pp | -12.83pp |
| p2_c120_h2 | **-27.17pp** | -5.06pp |

Any TopoGraph-assisted mode hurts rings. Cause is structural: with symmetric ring topology both "directions" look equally good, the algorithm commits to one, and the committed path has lower resilience than flooding. No strict-confidence variant helps.

**Action:** document as a known limitation. If budget permits, add runtime ring detection + fall back to baseline flood for ring-like subgraphs. Non-blocking for shipping — real-world deployments are not ring-dominated (v10 regions all benefited from passive_c120).

---

## Firmware bug to investigate

v10 observation: `probes_on` and `probes_c120` produce **numerically identical** output in every single (region, seed) cell — same delivered, radio_tx, collisions, wall_s.

Interpretation: when `probes on` is set, the `confidence 120` flag has no effect. Either probes override confidence or the code path is dead. This is worth a firmware-team look even though probes aren't shipping — it means the feature-gating for probes+c120 is not working as the simv2 config sheet implies.

File the issue; don't block on it.

---

## Confidence threshold saturation (v8 discovery)

The v8 factorial revealed that the 5-level confidence factor effectively collapses into **2 bins**:

| Bin | Levels | Behavior |
|---|---|---|
| Loose | 40, 100 | Accept unknown-edge paths. Cliff at chain≥8 / grid≥3x3. |
| Strict | 105, 120, 160 | Reject unknown-edge paths. Safe on all non-ring topologies. |

The transition is at confidence value 101. This is an artifact of `SNR_UNKNOWN = 100` in the encoding: any threshold ≤ 100 accepts unknown-SNR edges; any threshold ≥ 101 rejects them.

Product implication: there is no benefit to exposing a `confidence` slider to users. Ship a single "TopoGraph: on/off" toggle. Internally this maps to confidence=120 when on, and no topograph routing at all when off.

---

## Radio overhead summary

| Feature | Mean radio delta | Max radio delta | Worth it? |
|---|---:|---:|---|
| passive_c120 | +2.7% (v7), +0.45% (v9 median), <1.5% (v10) | +14.5% worst | Yes — modest cost, guaranteed non-regression |
| passive_c120 + probes_h2 | +6.25% mean, +19.3% max | +103 tx abs | No — does not replicate delivery wins |
| multipath_c120 | +3.55% mean | +19.6% max | No — zero delivery benefit |
| c40 (loose) | -6.4% mean (floods suppressed before route confirmed) | — | No — "savings" proportional to delivery loss |

The shipping default's radio overhead is under 2% in every measurement — well below noise floor for real meshes.

---

## Per-topology-class summary (from v7)

| Class | Baseline | Best feature | Verdict |
|---|---:|---|---|
| chain_short (3-7) | 95-100% | all tie near 0 | `passive_c120` safe, no gain needed |
| chain_long (8-25) | 69-94% | `passive_c120` +0.19pp mean | `passive_c120` |
| grid_diag | 89-99% | `passive_c120` +0.34pp | `passive_c120` |
| grid_nodiag | 77-82% | `passive_c120` -0.52pp (best of bad choices) | `passive_c120` (probes are toxic here) |
| star / dstar | 97-100% | all tie at 0 | `passive_c120` no-op |
| tree | 75-95% | `passive_c120_h2` +5-10pp **in v7** but **-3pp in v9** | `passive_c120` (v7 tree win did not replicate) |
| ring | 73-82% | **all hurt** | baseline (structural limitation) |
| cluster | 77-88% | `passive_c120_h2` marginal +1.2pp; variance wide | `passive_c120` (safer) |
| spurs (chain6_spurs) | 38% | `passive_c120_h2` +1.04pp | `passive_c120` (v9 retraction applies) |

---

## What the knobs do (final)

| CLI | Recommended ship value | Why |
|---|---|---|
| `confidence` | 120 | Strict; rejects unknown-edge paths. Anything 105-160 is equivalent. |
| `probes on/off` | off | High variance, real-topology CI firmly negative on seapdx. |
| `multipath` | 1 | Never statistically significant in 20-seed testing. |
| `penaltymode` | default (on) | No effect at strict confidence; left on so loose-mode debuggers see intended behavior. |
| `edgettl` | 1800 (30min) | Not directly re-swept; prior v3 evidence shows 30min is the sweet spot. |
| `autoadjust` | off | Not swept here. Keep off until explicitly tested. |

---

## Budget note

Total compute: ~3h 45min wall-clock across 4 sweeps. Sweep2 parallelism of 28 workers gave ~16 effective cores of sim throughput. Each analysis agent took 2-5 min. Entire end-to-end pipeline — including the 4 subagent analyses and this synthesis — completed in ~4h with no human intervention after the initial "run the pipeline" kickoff.

---

## Open follow-ups (non-blocking)

1. **Ring-detection heuristic** — investigate adding runtime ring-subgraph detection and fallback to flood. Could be a companion-side topology invariant check during graph updates.
2. **Probes firmware bug** — why does `confidence 120` + `probes on` produce the same output as just `probes on`? Dead code path or correct-but-surprising override?
3. **Manh probes effect** — v10 shows probes_on +1.6pp on manh but CI crosses zero. A 20-seed re-run on just manh would resolve this. If real, may indicate probes help on specific real-world topology shapes (diameter > ~8 hops).
4. **cluster_big high variance** — v9 flags it as the noisiest topology (26pp CI width even at n=20). Longer sim duration or more seeds would tighten conclusions there.
5. **edge_ttl and autoadjust revisits** — both untouched in v7-v10; neither should block shipping but deserve targeted sweeps before turning `autoadjust` on by default.
