# Dynamic-Topology A/B Test Plan

Synthesis of two scoping subagents:
- `/tmp/simv2_mobility_scoping.md` — what simv2 supports
- `/tmp/stock_firmware_dynamic_topo.md` — what stock MeshCore does when a cached path breaks

## The headline: baseline has no path-repair mechanism at all

Previously we assumed baseline MeshCore had at least *some* path invalidation after timeout. It doesn't. From the firmware scoping:

- Path cache: one entry per contact, stored as `out_path[64]` + `out_path_len`.
- Cache lifetime: **infinite**. No TTL, no LRU, no heuristic aging.
- ACK timeout: ~9.4s (1-hop direct) / ~11.7s (flood) at SF10/BW250.
- Firmware retries: **zero**. Retries are entirely the app's job (typically 3 app-level retries).
- Failure handling: `onSendTimeout()` is a no-op in the companion firmware. The stale path stays cached. Every subsequent send uses the same dead route.
- Recovery: only via explicit `CMD_RESET_PATH` from the app, which triggers one flood to rediscover.

**A cached path to a dead repeater will route every future message into the void, forever, until the app manually resets it.**

Our earlier v7-v10 sweeps didn't expose this because they used **static topologies** — the cache was always correct. In a static world, baseline and TopoGraph both work fine. The moment anything changes, baseline has no recovery mechanism and TopoGraph's BGP penalty / edge decay become qualitatively different.

This reframes the TopoGraph value proposition: it's not "route better on static graphs" (tiny wins); it's "handle dynamic topologies at all" (large wins).

---

## Sim infrastructure prerequisite

All three dynamic scenarios need one ~2-hour change:

1. Expose `Orchestrator::setLink(from, to, snr, rssi)` forwarder — `_link_model` is currently private.
2. Add `sim:set_link(from, to, snr, rssi)` and `sim:clear_link(from, to)` Lua bindings in `LuaEngine.cpp`.

No other orchestrator changes needed. ITM/SRTM stays offline (static topology terrain); the link-matrix mutation is the whole story. See `simv2_mobility_scoping.md` for file:line references.

After that one-time change, all three scenarios become small Lua scripts.

---

## Scenario 1 — Bridge repeater dies mid-run (ship this first)

**Ordering:** first because it's the cleanest signal, uses the minimum infrastructure, and by itself makes the compelling argument for dynamic-topology support.

**Topology:** 8-node mesh with two redundant bridge repeaters (`R1`, `R2`) between alice-side and bob-side clusters. Both R1 and R2 are initially reachable with similar SNR.

**Timeline:**
- t=0..60s: mesh warm-up, baseline adverts propagate, first flood to bob establishes initial path (assume it goes via R1 with 50% probability — we'll average over seeds).
- t=30s onward: alice sends unicast to bob every 15s (18 messages over 300s).
- **t=120s: kill R1** via `sim:clear_link()` to/from every node — R1 is now a radio-dead node.
- t=120..300s: observation window. What fraction of messages to bob are delivered?

**Expected baseline behavior:**
- Messages sent t=30..120s that cached R1 as the path: delivered normally.
- First message after t=120s sent via cached-R1 path: app times out at ~28-35s (3 retries × ~9.4s), declares failure.
- Subsequent messages: same dead cache, same 28-35s timeout per send.
- If the app calls `CMD_RESET_PATH` after the first failure: one flood re-establishes path via R2, delivery resumes at ~t=155s.
- If the app doesn't: delivery stays at 0 for the rest of the run.
- We'll simulate both app behaviors (`reset_on_timeout=on/off`) since different clients make different choices.

**Expected TopoGraph behavior:**
- First timeout at ~t=129s triggers BGP penalty (penalty=80, half-life=150s) on every edge through R1.
- Dijkstra on next send picks the path via R2 (penalty-free).
- Delivery resumes on the immediate retry (~t=138s).
- No explicit flood needed — the graph already knew R2 was an option.

**Expected A/B delta:** +50-80pp delivery in the post-death window *if app does not reset path*; +10-20pp if it does (TopoGraph saves one flood cycle, ~15s).

**Variants to sweep:**
- Death time: 60s / 120s / 180s (tests whether cache-warmup duration matters)
- App reset policy: on / off
- R1 failure mode: hard kill / half-power degradation / restore-after-60s (tests recovery behavior)
- Mesh size: 8-node / 16-node (tests whether extra nodes absorb recovery cost)

**Effort:** 2h C++ binding + 30min Lua + 30min test config. ~3h total.
**Expected runtime:** ~15 min for 10 seeds × 8 variants × 2 features = 160 runs.

---

## Scenario 2 — Mobile bridge (walks in, walks out)

Realistic: a hiker or delivery rider carries a repeater through a sparse mesh.

**Topology:** two 4-node clusters separated by a 2km RF gap. `Mallory` (a repeater) walks from cluster-A's vicinity, through the gap, into cluster-B, and keeps going. The only viable bridge during the in-range window is Mallory.

**Trajectory:** Mallory traverses a 3km path at 1.5 m/s (walking pace). In-range of cluster-A for t=60..200s, in-range of cluster-B for t=240..380s, in-range of both (the actual bridge window) only for t=200..240s. 10-min total run.

**Pre-computed SNR schedule:** offline Python script calls `compute_link()` at 15s intervals along the walk, produces a `(time, from, to, snr)` table baked into the test config. Lua step function applies the current interval's SNRs via `sim:set_link()`.

**Workload:** alice messages bob every 20s from t=0 onward. 30 messages total.

**Expected baseline behavior:**
- t=0..60s: floods fail (no bridge). Zero delivery.
- t=60..200s: first flood during Mallory's A-side window succeeds, path cached (alice→Mallory→bob). Delivery OK for messages that reach Mallory.
- t=200..240s: brief window where both sides reach Mallory — cache valid.
- t=240s onward: Mallory leaves A-side range. Cached path now routes into void. Every subsequent message fails per above timeline.
- t=240..600s: 0% delivery unless app resets path, in which case re-flood also fails (Mallory no longer reachable from A-side).

**Expected TopoGraph behavior:**
- Same initial pattern (must flood to bootstrap since nothing else connects).
- Once Mallory's SNR on the A-side drops below threshold, edge's confidence drops (passive update via advert observations + obs_count).
- BGP penalty on timeout accelerates it.
- Eventually graph marks that alice has no reachable path to bob → attempts flood → fails → waits for a new bridge.
- This is *worse than baseline in absolute terms* (neither can deliver after Mallory leaves), but TopoGraph's state is *correct* (knows no path exists) vs baseline's cache is *wrong* (thinks path exists). If Mallory returns, TopoGraph finds the path faster.

**Variants:**
- Mallory's speed: 1 m/s / 5 m/s / 15 m/s (pedestrian / cyclist / vehicle)
- Mallory's pattern: one-pass / oscillating (back-and-forth 4 times in 10 min)
- TopoGraph `edge_ttl`: 300s / 1800s default / 3600s — does shorter TTL help here?
- Number of oscillation periods (tests penalty half-life memory)

**Effort:** 2h C++ binding (shared with Scenario 1) + 4-6h Python for offline ITM waypoint compute + 1h Lua/config. ~8h incremental after Scenario 1 lands.

**This is the *edge_ttl* sweep we've been missing** — the only scenario where TTL actually matters, because only here do edges become genuinely invalid over time.

---

## Scenario 3 — Gradual link degradation (weather / battery)

Least physical but shortest implementation.

**Topology:** simple chain. Alice → R1 → bob, with a fallback via R2. R1's link to bob slowly degrades over 10 min (simulating battery dying or increasing weather attenuation).

**Timeline:** SNR on R1↔bob link drifts from 10dB down to -5dB over 600s (1.5dB/min). Lua step function applies the new SNR every 30s.

**Expected baseline:** sticks with R1-path until it completely breaks (timeout storm), then app resets and floods.

**Expected TopoGraph:** graph's SNR-weighted Dijkstra shifts preference to R2 continuously as R1's link degrades. No explicit failure event.

**A/B delta:** TopoGraph should show flatter delivery curve, baseline shows cliff-edge failure.

**Effort:** 1h pure Lua after binding exists.

---

## Recommended ordering and total budget

| Phase | Work | Effort | Unblocks |
|---|---|---|---|
| 0 | Add `sim:set_link()` / `sim:clear_link()` Lua binding | 2h C++ | all of 1, 2, 3 |
| 1 | Scenario 1 (bridge-kill) sweep | 3h setup + 15min run | |
| 2 | Scenario 3 (SNR drift) sweep | 1h setup + 15min run | |
| 3 | Scenario 2 (mobile bridge) — offline ITM compute + sweep | 6h setup + 30min run | |
| 4 | Cross-scenario analysis + write-up | 2h subagent | |

**Total: ~14h effort, 1 hour of compute, should produce 20-80pp deltas on the bridge-kill scenario alone.**

If the binding ships cleanly, phases 1-3 can be run as a single pipeline similar to v7-v10, with subagent analysis per scenario.

---

## Expected story at the end

The v7-v10 sweep already showed TopoGraph is a *safe free upgrade on static topologies* (+0.4-0.8pp delivery, <1.5% radio cost). The dynamic sweep should show TopoGraph is *qualitatively different on moving topologies* — expected 20-80pp delivery wins when repeaters move or fail, because baseline literally has no mechanism to recover.

That reframes the pitch. Instead of "TopoGraph is a marginal improvement on MeshCore's existing routing," it becomes "**MeshCore currently assumes fixed infrastructure; TopoGraph is what's needed to relax that assumption.**" That's a much more publishable and shippable story.

---

## Open questions before committing

1. Should we ship the Lua binding as a standalone sim-infra PR even if we don't pursue dynamic sims immediately? It's a generally-useful primitive.
2. Scenario 2's offline ITM compute — can we re-use existing `propagation.py compute_link()` or does it need a waypoint-aware wrapper?
3. Does the stock app's `CMD_RESET_PATH` behavior need to be modeled in the simv2 companion? Currently our companion implementation may or may not emit that command on app-retry-exhausted. Worth verifying in the simv2 CompanionNode code.
4. Does TopoGraph's BGP penalty actually fire on stock MeshCore timeouts, or only on our own sendMessage path? Need to verify the timeout hook is wired up correctly.
