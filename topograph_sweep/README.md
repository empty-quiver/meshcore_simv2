# TopoGraph sweep harness

Parallel A/B testing infrastructure for the TopoGraph companion-side
firmware feature (see `MeshCore-topo` branch at
<https://github.com/empty-quiver/MeshCore/tree/topo-graph>).

## Layout

* `sweep2.py` — main sweep driver. Builds JSON test configs on the fly
  across axes `(topology × workload × advert_schedule × feature × seed)`
  and runs them in parallel via `concurrent.futures.ProcessPoolExecutor`.
  Each run invokes `build/orchestrator/orchestrator <config>`, captures
  stdout/stderr, parses summary metrics, and writes a CSV at exit.

  Usage:
  ```
  cd meshcore_simv2   # the sim root, built via tools/firmware.py build
  python3 topograph_sweep/sweep2.py \
      --topologies chain_6,grid_5x5,star_8 \
      --workloads light,heavy \
      --features baseline,passive,probes_on,passive_c120 \
      --adverts medium \
      --seeds 42,101,202 \
      --workers 28 \
      --csv /tmp/sweep.csv
  ```

  Axes:
  - **topologies**: `chain_{3,6,10,15}`, `grid_{3x3,4x4,5x5}` with/without
    diagonal SNR links, `star_{3,5,8,10}`, `dstar_4`, `tree_d3f2`.
  - **workloads**: `light` (3 msgs), `medium` (6), `burst` (6 rapid),
    `heavy` (12), `sparse` (1 msg every 2 min).
  - **adverts**: `sparse` (2 rounds), `medium` (4 rounds), `frequent` (8).
  - **features**: `baseline` (stock MeshCore), `passive` (fw_topo probes
    off), `passive_c{60,80,95,100,105,110,120,140}` (passive + explicit
    min_confidence threshold), `probes_on`, `probes_c{110,120,140}`.

* `sweep.py` — first-generation driver, kept for reference. sweep2 supersedes.

* `analyze2.py` — consumes `sweep_v*.csv`, groups by config, averages
  across seeds, produces a grand summary table + per-topology-class
  summary + detail table. Relative deltas vs baseline.

* `analyze.py` — first-generation analyzer, simpler.

* `heatmap.py` — ANSI-colored grid `(topology × workload)` for a given
  feature, red=delivery regression, green=clean win. Intended for
  visual scanning of a CSV to spot where a variant wins or loses.

* `run_passive_ab.py` — narrow 3-way A/B (baseline / passive / probes-on)
  driver that runs a specific test trio and prints a formatted table.
  Useful for quick regression checks, not large sweeps.

* `gen_*_tests.py` — helper scripts that generate specific single-purpose
  test JSONs used during development: `hashmode1/2/mixed` (multi-byte
  path hash), `passive` (probes off), `adaptive` (adaptive probing
  chain+grid), etc.

## Requirements

The harness relies on the simv2-side CLI extensions that `fw_topo`
depends on. Specifically the orchestrator's CompanionNode dispatcher
must recognise: `probes on/off`, `confidence N`, `probecool N`,
`busyrate N`, `hashmode N`. These are guarded by feature-detection
macros (`TOPO_HAS_PROBE_SWITCH`, `HAS_PATH_HASH_MODE`) in the orchestrator
CMakeLists so older firmware plugins build cleanly without them.

Build with:
```
python3 tools/firmware.py init   # checkout all firmware sources (incl. MeshCore-topo if registered in firmware.json)
python3 tools/firmware.py build
```

## Output format

`sweep2.py` emits a CSV with columns:

```
topology, workload, advert, feature, seed,
delivered, sent,
alice_flood, alice_direct,
radio_tx, radio_rx, collisions, ackpath_tx,
total_flood_tx, total_direct_tx,
probes_fired,
wall_s, rc
```

`radio_*` fields are mesh-wide aggregates from the simulator's summary
line. `alice_*` fields are from the `sent_flood / sent_direct` per-node
stats (alice is the designated originator in all workloads).

## Result files from this repo

`sweep_v2.csv` (2,625 runs, medium adverts only) and `sweep_v3.csv`
(22,050 runs, all three advert cadences) are example outputs. Analysis
results are documented alongside the PR on the firmware fork.
