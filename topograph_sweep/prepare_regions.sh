#!/bin/bash
# Generate real-topology test configs for three regions using the
# topology_generator / ITM propagation pipeline.
set -euo pipefail
cd /home/eve/meshcore_simv2

gen_region() {
    local name=$1 bbox=$2 freq=$3
    local topo="simulation/${name}_topology.json"
    local test="simulation/${name}_test.json"

    echo "=== ${name}: bbox=${bbox} freq=${freq}MHz ==="

    ~/meshcore_simv2/.venv/bin/python3 -m topology_generator \
        --region "${bbox}" \
        --api-cache "/tmp/meshcore_nodes_${name}.json" \
        --freq-mhz "${freq}" \
        --tx-power-dbm 20.0 \
        --antenna-height 5.0 \
        --sf 8 --bw 62500 --cr 4 \
        --max-distance-km 40 \
        --min-snr -10.0 \
        --max-edges-per-node 12 \
        --link-survival 0.4 \
        --clutter-db 6.0 \
        -v -o "${topo}"

    # Inject alice as the focal companion + 3 distant peers (bob, carol, dave)
    # Use 900s simulation, 5 messages at 70s intervals from alice, 4 channel msgs
    ~/meshcore_simv2/.venv/bin/python3 tools/inject_test.py "${topo}" \
        --companions 4 \
        --companion-names alice,bob,carol,dave \
        --min-neighbors 2 \
        --auto-schedule --channel \
        --msg-interval 70 --msg-count 5 \
        --chan-interval 80 --chan-count 4 \
        --duration 900000 \
        -v -o "${test}"

    echo ""
    echo "=== ${name} topology stats ==="
    ~/meshcore_simv2/.venv/bin/python3 tools/topology_stats.py "${topo}" 2>/dev/null | head -20 || true
    echo ""
}

# Gdansk, Poland (EU 869.618 MHz)
gen_region gdansk   "53.7,17.3,54.8,19.5"    869.618

# Seattle + Portland PNW corridor (US 915 MHz)
# Latitude 45.0N..48.0N, Longitude 123.5W..121.0W
gen_region seapdx   "45.0,-123.5,48.0,-121.0" 915.0

# Massachusetts + New Hampshire (US 915 MHz)
# Latitude 42.0N..45.5N, Longitude 73.5W..70.5W
gen_region manh     "42.0,-73.5,45.5,-70.5"   915.0

echo "=== ALL DONE ==="
ls -la simulation/*_topology.json simulation/*_test.json 2>/dev/null
