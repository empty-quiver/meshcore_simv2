"""Build a synthetic urban-corridor test config for the SNR-variability A/B scenario.

10-node mesh with alice <-> bob separated by 3-5 hops via redundant paths.
Multiple routes mean the topology remains deliverable when a single link
degrades - TopoGraph's SNR-aware Dijkstra and BGP penalty should pick
around the affected links faster than baseline's fixed path cache.

Links have moderate base SNR (6-10 dB) with small O-U fading (std_dev=1.5)
to simulate channel flutter before any Lua-driven shadow/fade events.
"""
import json
import sys

OUT = '/home/eve/meshcore_simv2/simulation/urban_variability_test.json'

# 10 nodes: alice, bob, 8 repeaters R1..R8 in a 2-lane corridor.
#
# Row A:   R1 -- R3 -- R5 -- R7
#          /                     \
# alice ---                       --- bob
#          \                     /
# Row B:   R2 -- R4 -- R6 -- R8
#
# Cross-links between rows (R1<->R2, R3<->R4, R5<->R6, R7<->R8) provide
# redundancy: if a link in Row A degrades, traffic can cross over and
# continue on Row B.

NODES = [
    {'name': 'alice', 'role': 'companion', 'lat': 54.3000, 'lon': 18.6000},
    {'name': 'R1',    'role': 'repeater',  'lat': 54.3002, 'lon': 18.6020},
    {'name': 'R2',    'role': 'repeater',  'lat': 54.2998, 'lon': 18.6020},
    {'name': 'R3',    'role': 'repeater',  'lat': 54.3002, 'lon': 18.6040},
    {'name': 'R4',    'role': 'repeater',  'lat': 54.2998, 'lon': 18.6040},
    {'name': 'R5',    'role': 'repeater',  'lat': 54.3002, 'lon': 18.6060},
    {'name': 'R6',    'role': 'repeater',  'lat': 54.2998, 'lon': 18.6060},
    {'name': 'R7',    'role': 'repeater',  'lat': 54.3002, 'lon': 18.6080},
    {'name': 'R8',    'role': 'repeater',  'lat': 54.2998, 'lon': 18.6080},
    {'name': 'bob',   'role': 'companion', 'lat': 54.3000, 'lon': 18.6100},
]

# Edges: alice-R1, alice-R2; R7-bob, R8-bob; row-A chain; row-B chain;
# row-A<->row-B cross links. All bidirectional.
# Base SNR 6-10 dB simulates "moderate urban" conditions.
BASE_SNR = 4.0        # moderate-weak urban link; closer to SF10 margin (-15 dB)
BASE_RSSI = -115.0
FADING_STD = 1.5

# Less-redundant mesh: two parallel chains with just two cross-links at the
# midpoint. Resembles a sparse suburban deployment where each route matters.
EDGES = [
    ('alice', 'R1'), ('alice', 'R2'),
    ('R1', 'R3'), ('R3', 'R5'), ('R5', 'R7'),       # Row A chain
    ('R2', 'R4'), ('R4', 'R6'), ('R6', 'R8'),       # Row B chain
    ('R3', 'R4'), ('R5', 'R6'),                      # two mid-mesh cross-links
    ('R7', 'bob'), ('R8', 'bob'),
]

def build_links():
    links = []
    for a, b in EDGES:
        links.append({
            'from': a, 'to': b,
            'snr': BASE_SNR,
            'rssi': BASE_RSSI,
            'snr_std_dev': FADING_STD,
            'bidir': True,
        })
    return links

# Message schedule: alice -> bob every 15s from t=30s to t=580s.
# 37 messages - meaningful sample size; 600s run leaves room for final ACKs.
def build_messages():
    msgs = []
    seq = 0
    for t in range(30000, 580001, 15000):
        seq += 1
        msgs.append({
            'from': 'alice', 'to': 'bob',
            'start_ms': t, 'interval_ms': 1, 'count': 1,
            'message': f'1to1 alice->bob seq={seq}',
            'ack': True,
        })
    return msgs

# Lua commands: load the variability script at t=0, then fire apply_variability
# every 20s from t=60000 to t=580000 (24 mutation windows).
def build_commands():
    cmds = [
        {'at_ms': 0, 'lua': 'init_variability'},
    ]
    # Faster cadence (every 12s instead of 20s) so multiple events can overlap
    # during the 10-min run - mimics the steady drum of micro-events in a
    # real urban RF environment rather than a clean single-event-at-a-time world.
    for t in range(30000, 580001, 12000):
        cmds.append({'at_ms': t, 'lua': 'apply_variability'})
    return cmds

cfg = {
    '_source': 'urban_variability synthetic - SNR-variability dynamic A/B',
    'simulation': {
        'duration_ms': 600000,
        'step_ms': 4,
        'warmup_ms': 5000,
        'hot_start': True,
        'seed': 42,
        'radio': {'sf': 10, 'bw': 250000, 'cr': 4},
    },
    'nodes': NODES,
    'topology': {'links': build_links()},
    'commands': build_commands(),
    'message_schedule': build_messages(),
    'channel_schedule': [],
}

with open(OUT, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
print(f'wrote {OUT}: {len(NODES)} nodes, {len(EDGES)} edges, {len(cfg["message_schedule"])} msgs, {len(cfg["commands"])} cmds')
