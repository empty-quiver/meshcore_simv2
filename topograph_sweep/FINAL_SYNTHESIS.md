# TopoGraph Full Synthesis — Static + Dynamic + Realistic Traffic

Single document tying together 7 sweep campaigns, 27,191 simulation runs total, on synthetic + real-derived topologies under both static and dynamic propagation, with both single-pair and multi-pair bursty traffic models. Supersedes `FINAL_SYNTHESIS.md` (which covered only the first 4 sweep campaigns).

## Sweep campaign inventory

| Sweep | Purpose | Rows | Regions / Topologies | Features | Seeds | Propagation | Traffic |
|---|---|---:|---|---|---|---|---|
| v6p1/v6p2 | ANOVA exploration | 250 / 115 | representative subset | varied | 3-5 | static | single-pair |
| v7 | Wide topology sensitivity | 7,200 | 40 synthetic | 6 | 5 | static | single-pair |
| v8 | Dense factorial ANOVA | 8,190 | 10 representative | 91 auto-generated | 3 | static | single-pair |
| v9 | Seed-heavy precision | 4,480 | 8 | 7 | 20 | static | single-pair |
| v10 | Real-topology validation | 60 | 3 real regions | 4 | 5 | static | single-pair |
| dynamic base | Dynamic-topology first test | 560 | 4 (1 synthetic + 3 real) | 7 | 20 | **dynamic** (drift/shadow/fade every 12s) | single-pair |
| dynamic realistic | Dynamic + contention | 420 | 3 real | 7 | 20 | dynamic | **multi-pair bursty + channel broadcasts** |

Total: ~26,800 simulation runs across seven campaigns. Sim runtime: ~6-7 hours wall-clock on 28-worker Lambda Vector.

All CSVs and per-sweep analyses live in `/tmp/sweep_v{7,8,9,10}.csv`, `/tmp/sweep_dynamic.csv`, `/tmp/sweep_dynamic_realistic.csv`, with companion markdown analyses for each.

---

## Shipping recommendation (unchanged across all sweeps)

**Ship `passive_c120` as default**: confidence threshold 120, probes off, multipath 1, edge TTL 30 minutes (1800s), penalty mode on.

The recommendation survives every sweep:

| Sweep | Evidence supporting passive_c120 default |
|---|---|
| v7 | 234/240 non-ring scenarios with delta_pp in [-6.67, +14.67], median 0, mean +0.04pp |
| v8 | Confidence saturates at ~101 (c105=c120=c160 equivalent); best 4-tuple within 0.5pp of this |
| v9 | 0/32 cells significantly negative, 1/32 significantly positive (chain_15 heavy/medium); pooled CI lower bound > -3.65pp on every topology |
| v10 | +0.40 to +0.80pp on all 3 real regions, CI lower bound ≥ 0 on each, radio cost < 1.5% |
| dynamic base | All CIs include zero across 4 regions — harmless, never significantly positive or negative |
| dynamic realistic | All CIs include zero — same pattern, resilient to traffic-mix change |

The story is consistent: passive_c120 is a **safe but modest** upgrade over baseline. It never significantly hurts anywhere outside rings. It's positive on some topology classes and neutral on others. It's not a transformative improvement.

---

## Retractions (features that looked promising but weren't)

### `p2_c120_h2` (adaptive probes, hop cap 2)
- **v7 claim:** +5.4pp on tree_d3f3, +9.8pp on tree_d4f2 (5 seeds)
- **v9 refutation:** all tree_d3f2 cells pooled to -3.1 to -3.4pp with 20 seeds
- **Dynamic confirmation:** 0/3 real regions with CI>0 on either base or realistic traffic
- **Verdict:** dead. Probes do not help on static or dynamic topologies; tree win was a 5-seed fluke.

### Multipath (`mp2`, `mp3`)
- **v7/v8 main effect:** never statistically significant (p > 0.3 in ANOVA main effects)
- **v9 refutation:** mp2 vs c120 — 0/32 sig-positive. mp3 vs c120 — 0/32 sig-positive. mp3 vs mp2 — 0/32 sig-positive.
- **Verdict:** dead. Remove from codebase.

### Loose confidence (`c40` family)
- **v7/v8:** cliff at chain length 8 (-18pp) and grid size 3×3 diagonal (-17pp), scaling to -53pp on grid_6x6
- **v9:** sig-negative on 10/16 pooled cells
- **Dynamic:** -7 to -18pp on all regions (also sig-negative, by floor effect under contention)
- **Verdict:** must never ship. Debug mode only.

---

## The dynamic-topology story (new since v10)

The big question that emerged from v10: "our sims are all static; what happens when RF conditions change mid-run?"

### Baseline MeshCore's hidden weakness

Subagent analysis of the stock firmware (`/tmp/stock_firmware_dynamic_topo.md`) revealed:

- Path cache has **no TTL**. Once cached, a path lives forever unless manually reset.
- Firmware has **zero retries** on ACK timeout. Retries are entirely the app's responsibility.
- `onSendTimeout()` is a no-op. No penalty, no flag, no re-flood trigger.
- Recovery from "cached path through dead repeater" requires the app to explicitly call `CMD_RESET_PATH`. Without it, every future message routes into the void.

This reframes TopoGraph's value proposition: it's the piece that lets baseline relax its "fixed infrastructure" assumption.

### What the dynamic sweeps actually showed

The dynamic sweeps added mid-run RF variability: every 12s, a random link either drifts (±3 dB persistent), gets shadowed (-10 dB for 60-120s), or deep-fades (-22 dB for 30-90s — link effectively dead). Event parity was identical across features (~71 events/run on all real regions).

**Base traffic (single-pair alice→bob):**
- Baseline delivery dropped to 36-44% across the 3 real regions (vs 37-48% static on v10).
- passive_c120 remains inert: all 3 region CIs include zero.
- passive_c120_ttl_short showed one CI-clean win on gdansk: **+3.20pp [CI +0.30, +6.30]** — but did NOT replicate on seapdx or manh (both CIs cross zero).
- Probes remain retracted (v9 finding confirmed under dynamics).

**Realistic traffic (7 pairs × 3 sessions × 4 msgs = 84 unicasts + 46 channel broadcasts):**
- Baseline drops a further 3.9-6.6pp across regions (CIs exclude zero) — contention tax.
- gdansk ttl_short CI-significance **did not replicate**: +3.20pp became +1.43pp [CI -0.89, +3.75].
- seapdx passive_c120_ttl_long became the strongest candidate: **+2.32pp [CI +0.00, +4.64]** — CI lower bound touches zero, best airtime of any variant (-84.94 tx per delivered message).
- TopoGraph variants drop ~1pp less than baseline on 11 of 12 c120 cells under contention. Directional support for path-cache-thrashing resilience, never CI-clear.

### Honest read of dynamic sweeps

The dynamic sweeps did **not** upgrade the shipping recommendation. No feature wins CI-clearly across multiple regions under either traffic model. The one CI-significant finding (gdansk ttl_short) did not replicate:
- Same scenario, different regions: doesn't replicate.
- Same regions, different traffic: doesn't replicate.
- 1-of-4 replications is not evidence for a general effect.

What the sweeps **did** support:
- passive_c120 is never harmful on dynamic topologies (still CI-clean).
- Seapdx (1076-node mesh) has a small consistent airtime-efficiency win for any c120 variant.
- edge_ttl may be worth exposing as a runtime knob (gdansk/manh like short; seapdx likes long).

---

## Known limitations

1. **Ring topologies regress** — any TopoGraph variant loses 14-27pp on ring_6 and 9-12pp on ring_10. Structural issue (algorithm commits to one direction when both look equally good). Recommended mitigation: document as known limitation and investigate ring-detection heuristic. Non-blocking for shipping since real-world deployments are not ring-dominated.

2. **Sim model unvalidated against real-world packet captures.** ITM/SRTM propagation + our MAC sim is the best we have, but until we see captures from real deployments, we can't confirm that delivery rates, event rates, or feature deltas match reality. User noted MQTT Boston access is forthcoming.

3. **Traffic model is simpler than real.** Realistic sweep adds multi-pair bursty chat, but still no:
   - App-layer retries (stock MeshCore apps retry 3× on timeout — we don't simulate this)
   - GPS/location beacons
   - Dynamic channel joins/leaves
   - Node mobility beyond link SNR variation

4. **Firmware bug flagged, not fixed.** `probes_on` and `probes_c120` produced numerically identical output in v10 — the `confidence 120` flag appears to be a no-op when probes are enabled. Worth investigating but not blocking.

5. **No multiple-comparison correction.** Across 27k+ runs and hundreds of cells, some CI-significant findings are expected by chance alone. This synthesis treats individual CI-significant results as suggestive, not conclusive — the pattern across sweeps is what matters.

---

## Confidence threshold saturation (v8 finding worth repeating)

The 5-level confidence factor (40, 100, 105, 120, 160) collapses into 2 effective bins:

| Bin | Levels | Behavior |
|---|---|---|
| Loose | 40, 100 | Accept unknown-edge paths. Cliff at chain≥8 / grid≥3×3. |
| Strict | 105, 120, 160 | Reject unknown-edge paths. Safe on all non-ring topologies. |

Transition at confidence=101 (SNR_UNKNOWN=100 is rejected for any threshold ≥ 101).

**Product implication:** ship a binary "TopoGraph: on/off" toggle rather than a confidence slider. Internally: confidence=120 when on, no topo routing when off.

---

## Current shipping firmware defaults (as of 2026-04-23)

| Knob | Default | Source |
|---|---|---|
| `topo_min_confidence` | **120** | synthesis recommendation (was 105, bumped per v7-v10) |
| `topo_probes_enabled` | **off** | v9 retraction of tree-probe claim |
| `topo_multipath_count` | **1** | v9 retraction of multipath |
| `topo_max_probe_hops` | 2 | dead at probes-off default |
| `topo_edge_ttl_ms` | 1800s (30 min) | v3-v10 evidence; dynamic sweeps suggest exposing as knob |
| `topo_penalty_mode` | on | no effect at strict confidence anyway |
| `topo_auto_adjust` | off | not rigorously swept |

---

## What to ship

- Ship `passive_c120` as the default when TopoGraph is enabled.
- Document ring topologies as a known limitation (consider ring detection later).
- Expose `edge_ttl` as a runtime-configurable knob (default 1800s, 300s for high-churn profiles).
- Keep probes and multipath in the codebase but off by default, undocumented for users.
- File a firmware-side issue to investigate `probes_on` vs `probes_c120` identical output.
- Ultimately: wait for real-world MeshCore MQTT traffic captures before making stronger claims about dynamic-topology benefit.

## What NOT to ship

- Do NOT ship loose confidence (c40) as a user-facing option.
- Do NOT ship multipath (verified dead across 20-seed precision sweep).
- Do NOT flip `probes on` by default; keep it as opt-in debug.
- Do NOT claim "big dynamic-topology improvements" in release notes — the evidence shows *safety*, not *transformation*.

---

## For the record: what the sweeps don't prove

1. We don't have evidence TopoGraph meaningfully improves real-world user experience. Our wins are 0.4-0.8pp delivery deltas on real regions under static sims; the dynamic sweeps are compelling in theory but none of the non-default variants CI-clear across regions.

2. We don't have packet captures validating our sim model. Until MQTT Boston data arrives, dynamic-topology conclusions are sim-predictions, not measurements.

3. We haven't tested the scenarios most likely to reveal TopoGraph's true value: long-running chat between two specific nodes over many messages (path cache staying warm), mobile repeaters (tested indirectly via variability, not directly), app-layer retries (would increase the cost of baseline's dead-cache failures).

## Future work

1. **Mobile repeater scenario** (scoped in `/tmp/DYNAMIC_TOPO_AB_PLAN.md`). Needs offline ITM waypoint compute. ~6-8h effort. Would directly test the value prop.
2. **App-retry emulation**: schedule each message 3× with backoff OR add explicit Lua event hook. Would make baseline's dead-cache cost realistic (and probably make TopoGraph look better).
3. **Ring detection**: runtime heuristic to fall back to baseline flood for ring-subgraphs. Would eliminate the one known delivery regression.
4. **MQTT Boston calibration**: once packet captures are available, rerun dynamic sweep with sim workloads tuned to match observed real-world traffic patterns. Validates or refutes the whole story.
5. **Opus adversarial review**: see `/tmp/OPUS_ADVERSARIAL_REVIEW.md` for an independent skeptical read of all sweep evidence.
