#!/bin/bash
# Sequential sweep pipeline. Runs v8, v9, v10 after v7 finishes.
# Assumes v7 already running; this script waits for it then chains.
set -u
cd /home/eve/meshcore_simv2

# Wait for any existing sweep to finish
while pgrep -f sweep2.py > /dev/null; do
    sleep 10
done

mkdir -p /tmp/pipeline_logs

# ============================================================
# v8: dense feature factorial (90 combos × 10 topos × 3 wl × 3 seeds)
# ============================================================
echo "[pipeline] $(date -u +%T) — starting v8 (dense feature factorial)"
rm -rf /tmp/sweep_out2 /tmp/sweep_v8.csv
# Representative topology subset: chain (short+long), grid (small+large), star, tree, edge-cases
TOPOLOGIES_V8="chain_6,chain_10,chain_15,grid_3x3,grid_5x5,grid_5x5_nodiag,star_5,star_8,tree_d3f2,cluster_big"
# All 90 auto-generated p3_* features + baseline
FEAT_V8=$(python3 -c "
import sys
sys.path.insert(0, '/tmp')
# Regenerate the same naming as sweep2.py
names = ['baseline']
for c in (40, 100, 105, 120, 160):
    for mp in (1, 2, 3):
        for pen in ('on', 'off'):
            for h in (0, 2, 5):
                names.append(f'p3_c{c}_mp{mp}_pen{1 if pen==\"on\" else 0}_h{h}')
print(','.join(names))
")
python3 /tmp/sweep2.py \
    --topologies "$TOPOLOGIES_V8" \
    --workloads medium,heavy,sparse \
    --features "$FEAT_V8" \
    --adverts medium \
    --seeds 42,101,202 \
    --workers 28 \
    --duration 700000 \
    --csv /tmp/sweep_v8.csv > /tmp/pipeline_logs/v8.log 2>&1
echo "[pipeline] $(date -u +%T) — v8 done: $(wc -l < /tmp/sweep_v8.csv) lines"

# ============================================================
# v9: seed-heavy precision sweep (narrow features × 20 seeds)
# ============================================================
echo "[pipeline] $(date -u +%T) — starting v9 (seed-heavy precision)"
rm -rf /tmp/sweep_out2 /tmp/sweep_v9.csv
# Top candidate features from cumulative learning — narrow list for tight CIs
SEEDS_V9="42,101,202,303,404,505,606,707,808,909,1010,1111,1212,1313,1414,1515,1616,1717,1818,1919"
python3 /tmp/sweep2.py \
    --topologies chain_6,chain_15,grid_3x3,grid_5x5,grid_5x5_nodiag,star_5,tree_d3f2,cluster_big \
    --workloads medium,heavy \
    --features baseline,p2_c120,p2_c120_mp2,p2_c120_mp3,p2_c120_h2,p2_c40,p2_c40_penalty_off \
    --adverts medium,frequent \
    --seeds "$SEEDS_V9" \
    --workers 28 \
    --duration 700000 \
    --csv /tmp/sweep_v9.csv > /tmp/pipeline_logs/v9.log 2>&1
echo "[pipeline] $(date -u +%T) — v9 done: $(wc -l < /tmp/sweep_v9.csv) lines"

# ============================================================
# v10: real-topology validation (Gdansk / SEAPDX / MANH)
# ============================================================
echo "[pipeline] $(date -u +%T) — starting v10 (real-topology)"
rm -rf /tmp/region_sweep_out /tmp/sweep_v10.csv
# Use the existing region_sweep.py but extend its FEATURES dict first
python3 -c "
import json, copy
# Build variant configs for 3 regions × 6 features × 5 seeds
import sys; sys.path.insert(0, '/tmp')
"
# Just re-run region_sweep.py with the same feature set
python3 /tmp/region_sweep.py --workers 12 --csv /tmp/sweep_v10.csv \
    --regions gdansk,seapdx,manh \
    --features baseline,passive_c120,probes_on,probes_c120 \
    --seeds 42,101,202,303,404 > /tmp/pipeline_logs/v10.log 2>&1
echo "[pipeline] $(date -u +%T) — v10 done"

echo "[pipeline] $(date -u +%T) — ALL PIPELINE SWEEPS COMPLETE"
