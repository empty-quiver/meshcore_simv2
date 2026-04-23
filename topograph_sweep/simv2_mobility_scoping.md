# meshcore_simv2 — Time-Varying Topology Scoping

**Goal:** assess feasibility of three A/B scenarios that break the
"repeaters are fixed infrastructure" assumption.

---

## How the sim currently works (relevant architecture)

The orchestrator is a discrete-event loop:
`initSimulation()` → repeating `executeStep(current_ms)` →
`emitSummary()`.

Each step does:
1. `processCommands` — fires scheduled `{at_ms, node, command}` entries
2. `deliverReceptions` — delivers PendingRx whose airtime has elapsed
3. `loop()` on every NodeContext — advances MeshCore firmware state machines
4. `registerTransmissions` / `routePackets` — routes pending TX through the link model

**Key data structures:**

| Object | Location | Description |
|---|---|---|
| `MatrixLinkModel` | `orchestrator/LinkModel.h` | N×N matrix of `(active, snr, rssi, snr_std_dev, loss)` entries. Single instance, allocated once in `configure()`. |
| `NodeContext` | `orchestrator/NodeContext.h` | Per-node struct with lat/lon, radio state, mesh instance. No runtime "enabled" flag. |
| `OrchestratorConfig::NodeDef` | `orchestrator/Orchestrator.h` | Static config parsed from JSON; no position-update slot. |
| `OrchestratorConfig::CmdDef` | same | `{at_ms, node_index, command, lua_fn}` — the only time-triggered mechanism. |

**Propagation:** SNR values come from the link table, not from a
live geometry calculation. `topology_generator/propagation.py` runs ITM
(Longley-Rice via `itmlogic`) at *topology build time* to compute per-link
SNR/RSSI, which are then baked into the JSON config. The orchestrator reads
those baked values; it never calls any propagation code at runtime.

Per-reception SNR can vary stochastically (i.i.d. Gaussian or
Ornstein-Uhlenbeck correlated fading via `snr_coherence_ms`), but
both modes sample around a fixed mean — there is no concept of a link
mean that drifts over time.

---

## Scenario 1: Moving Repeater

**Question:** can a repeater's position change during a run, with SNR
recomputed from new geometry?

### Native support: NONE

- Node lat/lon is stored in `NodeContext::lat/lon` (set in
  `Orchestrator::configure()`, line 111-113) but is only ever read by
  `EventLog::nodeReady()` at init time for the `node_ready` NDJSON event.
  It is never consumed by the link model.
- `MatrixLinkModel` has no method to zero out a link or replace a row at
  runtime. `setLink()` and `setBidirectional()` exist, but there is no
  exposure of those methods to the command or Lua layer.
- There is no `waypoint`, `move`, or position-schedule concept anywhere
  in `JsonConfig.cpp` or `Orchestrator.h`.
- Propagation (ITM) is offline/pre-computed; the orchestrator has no
  ITM call site in its hot path.

### Effort to add natively: MEDIUM (estimated 8–16 hours)

The plumbing to add native waypoint mobility:

1. **Expose link mutation to Lua** (~2h): add `sim:set_link(from, to, snr, rssi)` and `sim:clear_link(from, to)` bindings in `LuaEngine.cpp` that call
   `_orch._link_model->setLink(...)`. The `_link_model` is private but
   `Orchestrator` already exposes `nodeAt()` and `findNodeByName()`; adding a
   `setLink()` forwarder is one-line.

2. **Pre-compute waypoint SNR table offline** (~4h): write a Python
   wrapper around `topology_generator/propagation.py`'s `compute_link()` to
   produce a JSON array of `{at_ms, from, to, snr, rssi}` events. ITM is
   called at prep time, not at sim time.

3. **Wire into Lua callback** (~1h): schedule a `{"at_ms": N, "lua": "update_links"}` entry every T seconds; the Lua function reads the pre-computed table and calls `sim:set_link()`.

4. **Update node position in NDJSON** (optional, ~1h): emit a new
   `node_move` event when position changes, useful for visualization.

The hard part is that propagation is **offline only**. Moving a node at
15 m/s over a 10-minute run means re-running ITM at ~60-second intervals
gives 10 snapshots. ITM runtime is ~50ms per link pair in Python, so for
a 20-node mesh that is feasible at prep time.

### Hack alternative (zero orchestrator changes): PARTIAL

The "spawn two variants at different positions" idea does work but is
imprecise:

- Define `relay_A` at position 1 and `relay_B` at position 2, both with
  their own baked SNR tables.
- At T=switch: use a scheduled Lua callback to invoke
  `sim:set_link("relay_A", ..., snr=0, loss=1.0)` to black out relay_A's
  links, then enable relay_B's links. **This requires the link-mutation
  Lua binding above**, which doesn't exist yet.

Without Lua link mutation, the only available scheduled command is a
MeshCore CLI command (`sim:cmd(node, command)`) which has no RF
topology effect. There is no `pause`/`resume` or `disconnect` node
command in the REPL or CLI (`InteractiveRepl.cpp` help output, confirmed).

The closest existing primitive is `adversarial.mode = "drop"` +
`tx_fail_prob`, but both are static per-node config — they cannot be
toggled mid-run.

### Sim limitations for Scenario 1

- ITM is static SRTM terrain: no weather variation, no time-of-day
  effects, buildings are not modeled.
- Even with link-mutation, the fading state vector (`_fading_state`,
  O-U offsets) is indexed by `symmetricLinkIndex(a, b, n)` and sized
  at `n*(n-1)/2` at configure time. Adding new nodes mid-run is not
  possible without a full reconfigure (which tears down everything).
  Waypoints must reuse existing nodes with mutated link tables.

---

## Scenario 2: Mid-Run Node Kill

**Question:** can a repeater go offline at a scheduled time?

### Native support: NONE (but very close)

There is no `disconnect`, `pause`, `kill`, or node-level `enabled` flag.
The closest existing mechanisms are:

- `adversarial.mode = "drop"`: suppresses all TX from a node. Static,
  cannot be toggled.
- `tx_fail_prob = 1.0`: makes every TX attempt fail. Also static.

Neither is schedule-triggerable via the existing command system, because
`commands[].command` is passed to `node->mesh->handleCommand()`, which
is MeshCore's CLI — not an orchestrator control plane command.

### Effort to add: SMALL (estimated 2–4 hours)

The cleanest path is to add link-blackout via Lua (which also unblocks
Scenario 1):

1. **Add `sim:set_link()` and `sim:clear_link()` Lua bindings** (~1h):
   See Scenario 1 item 1 above. `clear_link(from, to)` calls
   `_link_model->setLink(from, to, 0, 0, 0, 0)` and also sets
   `_links[...].active = false`.

2. **Schedule a Lua callback to clear all links for a node** (~1h):
   ```lua
   function kill_relay()
     for _, n in ipairs(sim:nodes()) do
       sim:clear_link("relay1", n.name)
       sim:clear_link(n.name, "relay1")
     end
   end
   ```
   Add `{"at_ms": 120000, "lua": "kill_relay"}` to the config.

This silently disconnects the node from the RF graph. Its firmware
keeps running (timers fire, it tries to TX) but no packet goes
anywhere. That is a realistic "radio failed" model. If a "firmware
crash" model is needed (node stops generating traffic too), a second
option is to add an `active` flag to `NodeContext` and skip its
`loop()` call in `executeStep()` — one additional if-guard, ~30 min.

### Hack alternative (zero orchestrator changes): NONE

There is no way to kill a node mid-run without code changes. The
`adversarial.mode = "drop"` is set at configure time only.

---

## Scenario 3: Link Degradation Over Time

**Question:** can a single link's SNR drift down gradually (battery
dying, weather)?

### Native support: PARTIAL

The sim has two relevant mechanisms:

1. **`snr_std_dev` + `snr_coherence_ms`** (O-U fading): SNR varies
   around a *fixed mean* with a configurable coherence time. This models
   channel flutter, not a monotonic drift. The O-U offset can temporarily
   be far below the mean but always mean-reverts.

2. **`loss` probability** per link: can approximate a degrading link by
   using a high `snr_std_dev` so many samples fall below the demodulation
   threshold. Crude and binary.

Neither supports a deterministic or scheduled SNR mean that decreases
over time.

### Effort to add: SMALL (estimated 1–3 hours, depends on fidelity)

**With the `sim:set_link()` Lua binding already added** (from Scenarios 1/2):

Write a Lua script that calls `sim:set_link("A", "B", decreasing_snr, ...)` at regular intervals using scheduled `{"at_ms": N, "lua": "degrade_link"}` entries or a loop inside the Lua main:

```lua
sim:initialize()
local base_snr = 8.0
while not sim:finished() do
    sim:step(30000)
    local elapsed_min = sim:time() / 60000
    local snr = base_snr - elapsed_min * 0.5  -- 0.5 dB/min
    sim:set_link("relay1", "bob", snr, -80.0)
    sim:set_link("bob", "relay1", snr, -80.0)
end
sim:finalize()
```

No C++ changes needed beyond the one Lua binding.

**Without the Lua binding:** not achievable at all with zero changes.
The `snr_coherence_ms` O-U model could be stretched to simulate a
degrading trend by setting a very long coherence time and relying on
the random walk, but this is not controllable or deterministic.

### Sim limitations for Scenario 3

- Link SNR changes take effect at the next `registerTransmissions()` call
  (next sim step after the Lua callback fires). Step granularity is 1ms
  by default. Smooth per-step drift is possible but will generate many
  Lua callback events.
- The fading O-U state (`_fading_state`) offsets around the *old* mean
  until the link is updated; after `set_link()` the offset still applies,
  causing a potential jump. If the drift is gradual (>10s intervals) this
  is not material.

---

## Summary Table

| Scenario | Native support | Effort with existing code | Requires new code? |
|---|---|---|---|
| 1. Moving repeater | None | Medium (8–16h) | Yes: Lua link-mutation binding + offline ITM waypoint prep |
| 2. Mid-run node kill | None | Small (2–4h) | Yes: Lua link-mutation binding (same as S1) |
| 3. Link SNR degradation | Partial (O-U only, no drift) | Small (1–3h after S2 binding exists) | Lua script only, no C++ once binding exists |

---

## Highest-ROI Scenario: Scenario 2 (Node Kill)

**Reasoning:**

- Scenario 2 requires the smallest code change: ~2h to add
  `sim:set_link()` + `sim:clear_link()` Lua bindings, plus a
  ~10-line Lua script. That one binding also unblocks Scenario 3
  almost for free.
- Scenario 2 maps to a clean A/B test: run A (all repeaters up) vs B
  (repeater killed at T=N). Delivery rate, ack rate, and relay
  utilization all change measurably. The existing message fate
  tracking infrastructure handles this natively.
- Scenario 2 is also the strongest violation of the
  "repeaters are fixed" assumption: a node going down is a
  qualitative topology change. Scenarios 1 and 3 are quantitative
  variations.
- Scenario 1 (moving repeater) requires both the Lua binding AND
  offline ITM re-runs, making it a bigger prep commitment with
  higher chance of ITM edge cases in the propagation model.

**Recommended implementation order:**
1. Add `sim:set_link(from, to, snr, rssi)` and `sim:clear_link(from, to)` to `LuaEngine.cpp` (~2h). This is the single enabling primitive.
2. Write Scenario 2 test immediately (node kill at T=N, no C++ beyond the binding).
3. Add Scenario 3 as a Lua-only extension (~1h script).
4. Add Scenario 1 only if the node-kill results are interesting enough to justify the offline ITM waypoint prep work.

---

## Known Sim Limitations Relevant to All Three Scenarios

| Limitation | Impact |
|---|---|
| ITM/SRTM is static | No time-varying weather, building diffraction, foliage effects. SNR changes must come from the link table, not from geometry recalculation. |
| Propagation computed at topology build time only | Moving a node requires offline ITM re-runs for each new position; the sim has no online path-loss computation. |
| Node count fixed at configure time | Cannot add or remove nodes mid-run. The `_fading_state` vector, `_node_event_keys`, and fate-tracking vectors are all sized at configure time (`Orchestrator.cpp` line 120-133). Killing a node must zero out its links; the `NodeContext` object stays live. |
| `_link_model` is private to `Orchestrator` | The Lua engine currently has no access to it. The binding addition requires adding a one-line accessor in `Orchestrator.h` plus the binding in `LuaEngine.cpp`. |
| No sub-step timing on link changes | A link SNR update takes effect at the next simulation step (1ms default). Sub-second mobility fidelity is possible but requires many scheduled Lua callbacks. |
| Adversarial drop / tx_fail_prob are static | They cannot be toggled mid-run via any existing command. They are set in `NodeContext` at configure time. For node kill the link-blackout approach is cleaner anyway. |
| O-U fading state persists across link SNR changes | After `set_link()` changes the mean SNR, the O-U offset still applies. For large SNR steps (>5 dB) this causes a one-step artifact. Use `snr_std_dev=0` on links you intend to mutate programmatically. |

---

## File/Line Reference Summary

| Finding | File | Line / Function |
|---|---|---|
| Link model data structure | `orchestrator/LinkModel.h` | `struct LinkEntry`, `setLink()` |
| Link model built once at configure | `orchestrator/Orchestrator.cpp` | ~137-151, `configure()` |
| Link model queried every TX step | `orchestrator/Orchestrator.cpp` | ~459, `registerTransmissions()` |
| No runtime link mutation exposed | `orchestrator/LuaEngine.cpp` | — (absent) |
| Node lat/lon stored but unused at runtime | `orchestrator/NodeContext.h` | line 66-67 |
| Propagation offline only | `topology_generator/propagation.py` | `compute_link()` |
| processCommands fires CLI only | `orchestrator/Orchestrator.cpp` | ~768-824, `processCommands()` |
| No pause/kill in REPL | `orchestrator/InteractiveRepl.cpp` | `handleHelp()` |
| Adversarial drop (static) | `orchestrator/Orchestrator.cpp` | ~317, `registerTransmissions()` |
| Fixed node count at configure | `orchestrator/Orchestrator.cpp` | ~120-133 |
| Lua callback scheduling (existing) | `orchestrator/JsonConfig.cpp` | ~168-175, `{"lua": "fn_name"}` |
| sim:cmd binding (existing) | `orchestrator/LuaEngine.cpp` | `sim.set_function("cmd", ...)` |
| Planned binding attachment point | `orchestrator/LuaEngine.cpp` | after `sim.set_function("cmd", ...)` |
| Orchestrator public accessor gap | `orchestrator/Orchestrator.h` | no `setLink` forwarder exists |
