#!/usr/bin/env python3
"""Expanded parallel sweep: more topologies, workloads, feature variants.

Features can now include runtime knob-setting commands (confidence, probecool, busyrate).
"""
import argparse
import concurrent.futures as cf
import copy
import itertools
import json
import os
import re
import subprocess
import sys
import time

SIM_ROOT = "/home/eve/meshcore_simv2"
ORCHESTRATOR = f"{SIM_ROOT}/build/orchestrator/orchestrator"
OUT_DIR = "/tmp/sweep_out2"

# =================== TOPOLOGIES ===================

def topo_chain(n_repeaters, chain_snr=10, bridge=None):
    nodes = [{"name": "alice", "role": "companion"}]
    for i in range(n_repeaters):
        nodes.append({"name": f"R{i}", "role": "repeater"})
    nodes.append({"name": "frank", "role": "companion"})
    links = [{"from": "alice", "to": "R0", "snr": chain_snr, "rssi": -70}]
    for i in range(n_repeaters - 1):
        links.append({"from": f"R{i}", "to": f"R{i+1}", "snr": chain_snr, "rssi": -70})
    links.append({"from": f"R{n_repeaters-1}", "to": "frank", "snr": chain_snr, "rssi": -70})
    if bridge:
        a, b, snr = bridge
        links.append({"from": a, "to": b, "snr": snr, "rssi": -90})
    return nodes, links

def topo_grid(rows, cols, n_companions=4, neighbor_snr=8, diag_snr=4, include_diag=True):
    nodes = []
    for r in range(rows):
        for c in range(cols):
            nodes.append({"name": f"r{r}_{c}", "role": "repeater"})
    corners = [(0,0), (0, cols-1), (rows-1, cols-1), (rows-1, 0)]
    companion_names = ["alice", "bob", "carol", "dave", "eve", "frank"]
    positions = corners[:min(n_companions, 4)]
    links = []
    for r in range(rows):
        for c in range(cols):
            if c+1 < cols:
                links.append({"from": f"r{r}_{c}", "to": f"r{r}_{c+1}", "snr": neighbor_snr, "rssi": -80})
            if r+1 < rows:
                links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c}", "snr": neighbor_snr, "rssi": -80})
            if include_diag:
                if r+1 < rows and c+1 < cols:
                    links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c+1}", "snr": diag_snr, "rssi": -95})
                if r+1 < rows and c-1 >= 0:
                    links.append({"from": f"r{r}_{c}", "to": f"r{r+1}_{c-1}", "snr": diag_snr, "rssi": -95})
    for i, (r, c) in enumerate(positions):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": f"r{r}_{c}", "snr": neighbor_snr, "rssi": -80})
    return nodes, links

def topo_star(n_spokes, spoke_snr=8):
    nodes = [{"name": "hub", "role": "repeater"}]
    companion_names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo", "ivan", "jane"]
    links = []
    for i in range(n_spokes):
        nm = companion_names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hub", "snr": spoke_snr, "rssi": -80})
    return nodes, links

def topo_double_star(spokes_per_hub=4, hub_link_snr=8):
    """Two hubs connected, each with N companion spokes."""
    nodes = [
        {"name": "hubA", "role": "repeater"},
        {"name": "hubB", "role": "repeater"},
    ]
    names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo"]
    links = [{"from": "hubA", "to": "hubB", "snr": hub_link_snr, "rssi": -80}]
    for i in range(spokes_per_hub):
        nm = names[i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hubA", "snr": 8, "rssi": -80})
    for i in range(spokes_per_hub):
        nm = names[spokes_per_hub + i]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": "hubB", "snr": 8, "rssi": -80})
    return nodes, links

def topo_tree(depth=3, fan=2):
    """Binary (or fan-ary) tree of repeaters with companions at leaves and root."""
    nodes = []
    links = []
    def build(name, lvl, parent):
        nodes.append({"name": name, "role": "repeater"})
        if parent is not None:
            links.append({"from": parent, "to": name, "snr": 8, "rssi": -80})
        if lvl < depth:
            for k in range(fan):
                build(f"{name}_{k}", lvl+1, name)
    build("root", 0, None)
    # Alice at root, companions at leaves
    leaves = [n["name"] for n in nodes if n["name"].count("_") == depth]
    names = ["alice", "bob", "carol", "dave", "eve", "frank", "ginny", "hugo", "ivan"]
    # Alice is first companion, attached to root
    nodes.append({"name": "alice", "role": "companion"})
    links.append({"from": "alice", "to": "root", "snr": 8, "rssi": -80})
    for i, leaf in enumerate(leaves[:len(names)-1]):
        nm = names[i+1]
        nodes.append({"name": nm, "role": "companion"})
        links.append({"from": nm, "to": leaf, "snr": 8, "rssi": -80})
    return nodes, links

def topo_ring(n_repeaters, snr=8):
    nodes = [{"name": f"R{i}", "role": "repeater"} for i in range(n_repeaters)]
    nodes.insert(0, {"name": "alice", "role": "companion"})
    nodes.append({"name": "frank", "role": "companion"})
    links = [{"from": "alice", "to": "R0", "snr": snr, "rssi": -80}]
    for i in range(n_repeaters):
        links.append({"from": f"R{i}", "to": f"R{(i+1)%n_repeaters}", "snr": snr, "rssi": -80})
    links.append({"from": f"R{n_repeaters//2}", "to": "frank", "snr": snr, "rssi": -80})
    return nodes, links

def topo_cluster_bridge(cluster_size=3, bridge_snr=6):
    """Two clusters each with `cluster_size` repeaters connected by a single bridge edge."""
    nodes = []
    links = []
    for i in range(cluster_size):
        nodes.append({"name": f"A{i}", "role": "repeater"})
    for i in range(cluster_size):
        for j in range(i+1, cluster_size):
            links.append({"from": f"A{i}", "to": f"A{j}", "snr": 10, "rssi": -70})
    for i in range(cluster_size):
        nodes.append({"name": f"B{i}", "role": "repeater"})
    for i in range(cluster_size):
        for j in range(i+1, cluster_size):
            links.append({"from": f"B{i}", "to": f"B{j}", "snr": 10, "rssi": -70})
    # bridge
    links.append({"from": "A0", "to": "B0", "snr": bridge_snr, "rssi": -90})
    # companions
    nodes.append({"name": "alice", "role": "companion"})
    nodes.append({"name": "frank", "role": "companion"})
    links.append({"from": "alice", "to": f"A{cluster_size-1}", "snr": 10, "rssi": -70})
    links.append({"from": "frank", "to": f"B{cluster_size-1}", "snr": 10, "rssi": -70})
    return nodes, links

def topo_chain_with_spurs(chain_len=6, spurs_per_hub=2):
    """Chain backbone with extra repeaters dangling off each backbone node."""
    nodes = [{"name": "alice", "role": "companion"}]
    for i in range(chain_len):
        nodes.append({"name": f"R{i}", "role": "repeater"})
    nodes.append({"name": "frank", "role": "companion"})
    links = [{"from": "alice", "to": "R0", "snr": 10, "rssi": -70}]
    for i in range(chain_len - 1):
        links.append({"from": f"R{i}", "to": f"R{i+1}", "snr": 10, "rssi": -70})
    links.append({"from": f"R{chain_len-1}", "to": "frank", "snr": 10, "rssi": -70})
    # Spurs
    for i in range(chain_len):
        for s in range(spurs_per_hub):
            nodes.append({"name": f"S{i}_{s}", "role": "repeater"})
            links.append({"from": f"R{i}", "to": f"S{i}_{s}", "snr": 8, "rssi": -80})
    return nodes, links

TOPOLOGIES = {
    # Chain family — length gradient
    "chain_3":       lambda: topo_chain(2),
    "chain_4":       lambda: topo_chain(3),
    "chain_5":       lambda: topo_chain(4),
    "chain_6":       lambda: topo_chain(4, bridge=("R0", "R3", 3)),
    "chain_7":       lambda: topo_chain(5),
    "chain_8":       lambda: topo_chain(6),
    "chain_10":      lambda: topo_chain(8),
    "chain_12":      lambda: topo_chain(10),
    "chain_15":      lambda: topo_chain(13),
    "chain_20":      lambda: topo_chain(18),
    "chain_25":      lambda: topo_chain(23),

    # Grid family — with and without diagonal links
    "grid_2x2":      lambda: topo_grid(2, 2),
    "grid_3x3":      lambda: topo_grid(3, 3),
    "grid_4x4":      lambda: topo_grid(4, 4),
    "grid_5x5":      lambda: topo_grid(5, 5),
    "grid_6x6":      lambda: topo_grid(6, 6),
    "grid_3x3_nodiag": lambda: topo_grid(3, 3, include_diag=False),
    "grid_4x4_nodiag": lambda: topo_grid(4, 4, include_diag=False),
    "grid_5x5_nodiag": lambda: topo_grid(5, 5, include_diag=False),
    "grid_6x6_nodiag": lambda: topo_grid(6, 6, include_diag=False),
    "grid_2x5":      lambda: topo_grid(2, 5),
    "grid_3x7":      lambda: topo_grid(3, 7),

    # Star family
    "star_3":        lambda: topo_star(3),
    "star_4":        lambda: topo_star(4),
    "star_5":        lambda: topo_star(5),
    "star_6":        lambda: topo_star(6),
    "star_8":        lambda: topo_star(8),
    "star_10":       lambda: topo_star(10),

    # Double-star family (two hubs bridged)
    "dstar_3":       lambda: topo_double_star(3),
    "dstar_4":       lambda: topo_double_star(4),

    # Tree family
    "tree_d2f2":     lambda: topo_tree(depth=2, fan=2),
    "tree_d2f3":     lambda: topo_tree(depth=2, fan=3),
    "tree_d3f2":     lambda: topo_tree(depth=3, fan=2),
    "tree_d3f3":     lambda: topo_tree(depth=3, fan=3),
    "tree_d4f2":     lambda: topo_tree(depth=4, fan=2),

    # Ring (cycle) topologies — new
    "ring_6":        lambda: topo_ring(6),
    "ring_10":       lambda: topo_ring(10),

    # Cluster-bridge: two dense cliques joined by single link
    "cluster_small": lambda: topo_cluster_bridge(cluster_size=3),
    "cluster_big":   lambda: topo_cluster_bridge(cluster_size=5),

    # Chain with dangling spur repeaters
    "chain6_spurs":  lambda: topo_chain_with_spurs(chain_len=6, spurs_per_hub=2),
}

# =================== WORKLOADS ===================

def workload_light(peers, duration_ms=700000):
    # After advert settle (~60% of sim), send 3 messages spaced across remaining time
    t0 = duration_ms * 60 // 100
    step = duration_ms * 5 // 100
    return [
        {"at_ms": t0,           "node": "alice", "command": f"msg {peers[0]} m1"},
        {"at_ms": t0 + step,    "node": "alice", "command": f"msg {peers[1%len(peers)]} m2"} if len(peers) > 1 else None,
        {"at_ms": t0 + 2*step,  "node": "alice", "command": f"msg {peers[2%len(peers)]} m3"} if len(peers) > 2 else None,
    ]

def workload_medium(peers, duration_ms=700000):
    out = []; t = duration_ms * 50 // 100
    step = duration_ms * 4 // 100
    for i in range(6):
        out.append({"at_ms": t + step*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} med{i}"})
    return out

def workload_burst(peers, duration_ms=700000):
    peer = peers[0]
    t0 = duration_ms * 60 // 100
    step = duration_ms * 2 // 100
    return [{"at_ms": t0 + step*i, "node": "alice", "command": f"msg {peer} b{i}"} for i in range(6)]

def workload_heavy(peers, duration_ms=700000):
    out = []; t = duration_ms * 40 // 100
    step = duration_ms * 3 // 100
    for i in range(12):
        out.append({"at_ms": t + step*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} h{i}"})
    return out

def workload_sparse(peers, duration_ms=700000):
    out = []; t = duration_ms * 20 // 100
    step = duration_ms * 12 // 100
    for i in range(5):
        out.append({"at_ms": t + step*i, "node": "alice", "command": f"msg {peers[i%len(peers)]} s{i}"})
    return out

WORKLOADS = {
    "light":  workload_light,
    "medium": workload_medium,
    "burst":  workload_burst,
    "heavy":  workload_heavy,
    "sparse": workload_sparse,
}

# =================== ADVERT SCHEDULES ===================

def adverts_medium(companion_names, _repeater_names, duration_ms=700000):
    cmds = []; t = duration_ms * 4 // 100    # first round at 4%
    # 4 rounds evenly spaced across first ~50% of sim so msgs have time
    round_gap = duration_ms * 12 // 100
    for _ in range(4):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += round_gap
    return cmds

def adverts_sparse(companion_names, _repeater_names, duration_ms=700000):
    cmds = []; t = duration_ms * 4 // 100
    round_gap = duration_ms * 25 // 100
    for _ in range(2):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += round_gap
    return cmds

def adverts_frequent(companion_names, _repeater_names, duration_ms=700000):
    cmds = []; t = duration_ms * 2 // 100
    round_gap = duration_ms * 6 // 100
    for _ in range(8):
        for i, n in enumerate(companion_names):
            cmds.append({"at_ms": t + i*2000, "node": n, "command": "advert"})
        t += round_gap
    return cmds

ADVERT_SCHEDULES = {
    "medium":   adverts_medium,
    "sparse":   adverts_sparse,
    "frequent": adverts_frequent,
}

# =================== FEATURE VARIANTS ===================
# Each feature is (fw_name_or_None, list of cli commands to run at t=3000)

def feat_baseline():
    return (None, [])

def feat_passive():
    # Explicitly set confidence=40 so behavior is independent of firmware default.
    # (firmware default changed from 40 to 105 mid-way through data collection.)
    return ("fw_topo", [{"command": "confidence 40"}])

def feat_passive_strict(conf):
    return ("fw_topo", [{"command": f"confidence {conf}"}])

def feat_probes_on():
    return ("fw_topo", [{"command": "probes on"}])

def feat_probes_strict(conf):
    return ("fw_topo", [{"command": f"confidence {conf}"}, {"command": "probes on"}])

FEATURES = {
    "baseline":        feat_baseline,
    "passive":         feat_passive,
    "passive_c60":     lambda: feat_passive_strict(60),
    "passive_c80":     lambda: feat_passive_strict(80),
    "passive_c95":     lambda: feat_passive_strict(95),
    "passive_c100":    lambda: feat_passive_strict(100),
    "passive_c105":    lambda: feat_passive_strict(105),
    "passive_c110":    lambda: feat_passive_strict(110),
    "passive_c120":    lambda: feat_passive_strict(120),
    "passive_c140":    lambda: feat_passive_strict(140),
    "probes_on":       feat_probes_on,
    "probes_c110":     lambda: feat_probes_strict(110),
    "probes_c120":     lambda: feat_probes_strict(120),
    "probes_c140":     lambda: feat_probes_strict(140),
    # Multi-path redundant direct send variants (explicit confidence for robustness)
    "passive_mp2":        lambda: ("fw_topo", [{"command": "confidence 40"}, {"command": "multipath 2"}]),
    "passive_mp3":        lambda: ("fw_topo", [{"command": "confidence 40"}, {"command": "multipath 3"}]),
    "passive_mp4":        lambda: ("fw_topo", [{"command": "confidence 40"}, {"command": "multipath 4"}]),
    "passive_c120_mp2":   lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "multipath 2"}]),
    "passive_c120_mp3":   lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "multipath 3"}]),
    # Probes with varying hop caps (default is 3; explore 2/5)
    "probes_c120_h2":     lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "maxprobehops 2"}, {"command": "probes on"}]),
    "probes_c120_h3":     lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "maxprobehops 3"}, {"command": "probes on"}]),
    "probes_c120_h5":     lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "maxprobehops 5"}, {"command": "probes on"}]),
    # Auto-adjust (Agent A): small-mesh loose, large-mesh strict
    "passive_auto":       lambda: ("fw_topo", [{"command": "autoadjust on"}]),
    "passive_auto_mp2":   lambda: ("fw_topo", [{"command": "autoadjust on"}, {"command": "multipath 2"}]),
    "passive_auto_mp3":   lambda: ("fw_topo", [{"command": "autoadjust on"}, {"command": "multipath 3"}]),
    "probes_auto":        lambda: ("fw_topo", [{"command": "autoadjust on"}, {"command": "probes on"}]),
    # Combined: strict confidence + multipath + probes (everything)
    "probes_c120_mp2_h3": lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "multipath 2"}, {"command": "maxprobehops 3"}, {"command": "probes on"}]),

    # ============================================================
    # Phase 1: one-factor-at-a-time ANOVA (v6 sweep). Each feature
    # holds all OTHER knobs at their new defaults (confidence=105,
    # penalty_on, edgettl=1800s, maxprobehops=2, multipath=1) and
    # varies ONE axis.
    # ============================================================
    # Our current default (c105 is the safe threshold, others are defaults)
    "p1_default":          lambda: ("fw_topo", [{"command": "confidence 105"}]),
    # Penalty-mode axis
    "p1_penalty_off":      lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "penaltymode off"}]),
    # Edge TTL axis (confidence held at 105)
    "p1_etl_60":           lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 60"}]),
    "p1_etl_300":          lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 300"}]),
    "p1_etl_1800":         lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 1800"}]),
    "p1_etl_7200":         lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 7200"}]),
    "p1_etl_86400":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 86400"}]),
    # Confidence axis (all others default)
    "p1_c40":              lambda: ("fw_topo", [{"command": "confidence 40"}]),
    "p1_c80":              lambda: ("fw_topo", [{"command": "confidence 80"}]),
    "p1_c100":             lambda: ("fw_topo", [{"command": "confidence 100"}]),
    "p1_c120":             lambda: ("fw_topo", [{"command": "confidence 120"}]),
    # Multipath axis
    "p1_mp2":              lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "multipath 2"}]),
    "p1_mp3":              lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "multipath 3"}]),
    "p1_mp4":              lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "multipath 4"}]),
    # Probe hop-cap axis (requires probes on)
    "p1_probes_h1":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "maxprobehops 1"}, {"command": "probes on"}]),
    "p1_probes_h2":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "maxprobehops 2"}, {"command": "probes on"}]),
    "p1_probes_h3":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "maxprobehops 3"}, {"command": "probes on"}]),
    "p1_probes_h5":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "maxprobehops 5"}, {"command": "probes on"}]),
    # Auto-adjust axis
    "p1_auto":             lambda: ("fw_topo", [{"command": "autoadjust on"}]),

    # ============================================================
    # Phase 2: combined TTL/penalty/interaction sweep (700s).
    # Cross-axis: confidence × multipath × (penalty / probes / TTL)
    # ============================================================
    # Loose-confidence variants (expected to trigger penalty firings)
    "p2_c40":              lambda: ("fw_topo", [{"command": "confidence 40"}]),
    "p2_c40_mp2":          lambda: ("fw_topo", [{"command": "confidence 40"},  {"command": "multipath 2"}]),
    "p2_c40_mp3":          lambda: ("fw_topo", [{"command": "confidence 40"},  {"command": "multipath 3"}]),
    "p2_c40_penalty_off":  lambda: ("fw_topo", [{"command": "confidence 40"},  {"command": "penaltymode off"}]),
    "p2_c40_h2":           lambda: ("fw_topo", [{"command": "confidence 40"},  {"command": "maxprobehops 2"}, {"command": "probes on"}]),

    # Strict-confidence variants (baseline-like)
    "p2_c120":             lambda: ("fw_topo", [{"command": "confidence 120"}]),
    "p2_c120_mp2":         lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "multipath 2"}]),
    "p2_c120_mp3":         lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "multipath 3"}]),
    "p2_c120_h2":          lambda: ("fw_topo", [{"command": "confidence 120"}, {"command": "maxprobehops 2"}, {"command": "probes on"}]),

    # TTL extremes at 700s (would expect differentiation now)
    "p2_etl_60":           lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 60"}]),
    "p2_etl_1800":         lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 1800"}]),
    "p2_etl_86400":        lambda: ("fw_topo", [{"command": "confidence 105"}, {"command": "edgettl 86400"}]),
}

# Auto-generate v8 full-factorial feature combos across key axes.
# Axes: confidence (40, 100, 105, 120, 160) × multipath (1, 2, 3)
#     × penalty (on, off) × probe_hops (0=off, 2, 5)
# = 5 × 3 × 2 × 3 = 90 combos. Named p3_cX_mY_pZ_hW.
for _c in (40, 100, 105, 120, 160):
    for _mp in (1, 2, 3):
        for _pen in ("on", "off"):
            for _h in (0, 2, 5):
                name = f"p3_c{_c}_mp{_mp}_pen{'1' if _pen=='on' else '0'}_h{_h}"
                def _f(c=_c, mp=_mp, pen=_pen, h=_h):
                    cmds = [{"command": f"confidence {c}"},
                            {"command": f"multipath {mp}"},
                            {"command": f"penaltymode {pen}"}]
                    if h == 0:
                        cmds.append({"command": "probes off"})
                    else:
                        cmds.append({"command": f"maxprobehops {h}"})
                        cmds.append({"command": "probes on"})
                    return ("fw_topo", cmds)
                FEATURES[name] = _f

# =================== CONFIG ASSEMBLY ===================

def build_config(topo_name, workload_name, feature_name, advert_name="medium",
                 duration_ms=700000, seed=42):
    nodes, links = TOPOLOGIES[topo_name]()
    comp_names = [n["name"] for n in nodes if n["role"] == "companion"]
    rep_names  = [n["name"] for n in nodes if n["role"] == "repeater"]
    peers = [n for n in comp_names if n != "alice"]
    if not peers:
        raise ValueError(f"{topo_name}: no non-alice companions")

    fw, pre_cmds = FEATURES[feature_name]()
    nodes2 = copy.deepcopy(nodes)
    for n in nodes2:
        if fw and n["name"] == "alice":
            n["firmware"] = fw

    cmds = []
    if fw:
        for c in pre_cmds:
            cmds.append({"at_ms": 3000, "node": "alice", "command": c["command"]})
    cmds.extend(ADVERT_SCHEDULES[advert_name](comp_names, rep_names, duration_ms=duration_ms))
    wl = [c for c in WORKLOADS[workload_name](peers, duration_ms=duration_ms) if c is not None]
    cmds.extend(wl)
    cmds.sort(key=lambda c: c["at_ms"])

    cfg = {
        "_name": f"sw_{topo_name}_{workload_name}_{advert_name}_{feature_name}_s{seed}",
        "simulation": {
            "duration_ms": duration_ms, "step_ms": 4, "warmup_ms": 10000,
            "hot_start": False, "seed": seed,
        },
        "nodes": nodes2,
        "topology": {"links": links},
        "commands": cmds,
        "expect": [],
    }
    if fw:
        cfg["_requires_plugins"] = [fw]
    return cfg

# =================== RUNNER ===================

METRIC_RE = {
    "radio_tx":     re.compile(r"Radio: (\d+) TX"),
    "radio_rx":     re.compile(r"Radio: \d+ TX, (\d+) RX"),
    "collisions":   re.compile(r"Radio: \d+ TX, \d+ RX, (\d+) collision"),
    "ackpath_tx":   re.compile(r"ACK\+path radio: (\d+) TX"),
    "delivered":    re.compile(r"Delivery: (\d+)/(\d+) messages"),
}

def parse_metrics(out):
    m = {}
    for k, rx in METRIC_RE.items():
        mm = rx.search(out)
        if mm:
            if k == "delivered":
                m["delivered"] = int(mm.group(1))
                m["sent"] = int(mm.group(2))
            else:
                m[k] = int(mm.group(1))
    tfx = tdx = 0; alice_flood = alice_direct = 0; probes_fired = 0
    for line in out.splitlines():
        if "[TOPO-probe" in line and "fired trace" in line:
            probes_fired += 1
        if "node_stats" not in line: continue
        try:
            j = json.loads(line)
            if "flood_tx" in line and j.get("stats_type") == "packets":
                d = j["data"]
                tfx += d.get("flood_tx", 0); tdx += d.get("direct_tx", 0)
            elif j.get("node") == "alice" and "sent_flood" in line:
                alice_flood = j.get("sent_flood", 0)
                alice_direct = j.get("sent_direct", 0)
        except Exception:
            pass
    m["total_flood_tx"] = tfx
    m["total_direct_tx"] = tdx
    m["alice_flood"] = alice_flood
    m["alice_direct"] = alice_direct
    m["probes_fired"] = probes_fired
    return m

def run_single(cfg_path):
    t0 = time.time()
    try:
        r = subprocess.run([ORCHESTRATOR, cfg_path], capture_output=True,
                           text=True, timeout=600, cwd=SIM_ROOT)
        out = r.stdout + r.stderr
        m = parse_metrics(out)
        m["wall_s"] = time.time() - t0
        m["rc"] = r.returncode
        return m
    except subprocess.TimeoutExpired:
        return {"rc": -1, "error": "timeout", "wall_s": time.time() - t0}
    except Exception as e:
        return {"rc": -2, "error": str(e), "wall_s": time.time() - t0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--duration", type=int, default=300000,
                    help="Sim duration ms (default 300s for screening; use 700000 for validation)")
    ap.add_argument("--topologies", default=",".join(TOPOLOGIES.keys()))
    ap.add_argument("--workloads",  default=",".join(WORKLOADS.keys()))
    ap.add_argument("--features",   default=",".join(FEATURES.keys()))
    ap.add_argument("--adverts",    default="medium")
    ap.add_argument("--seeds",      default="42,101,202")
    ap.add_argument("--csv",        default="/tmp/sweep_results.csv")
    ap.add_argument("--no-run", action="store_true", help="generate configs but do not run")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    combos = []
    for topo in args.topologies.split(","):
        for wl in args.workloads.split(","):
            for adv in args.adverts.split(","):
                for feat in args.features.split(","):
                    for seed in args.seeds.split(","):
                        combos.append((topo, wl, adv, feat, int(seed)))
    print(f"{len(combos)} configs, {args.workers} workers")
    t_start = time.time()

    config_paths = []
    for topo, wl, adv, feat, seed in combos:
        cfg = build_config(topo, wl, feat, advert_name=adv, duration_ms=args.duration, seed=seed)
        path = f"{OUT_DIR}/{cfg['_name']}_{adv}.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2); f.write("\n")
        config_paths.append((topo, wl, adv, feat, seed, path))
    if args.no_run:
        print("configs generated, --no-run specified, exiting")
        return

    # Streaming CSV: open once, write header, append each row as it completes.
    # Sweep can be interrupted and we still have all completed runs.
    cols = ["topology", "workload", "advert", "feature", "seed",
            "delivered", "sent", "alice_flood", "alice_direct",
            "radio_tx", "radio_rx", "collisions", "ackpath_tx",
            "total_flood_tx", "total_direct_tx", "probes_fired",
            "wall_s", "rc"]
    csv_f = open(args.csv, "w", buffering=1)   # line-buffered
    csv_f.write(",".join(cols) + "\n")

    results = []
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_single, p[5]): p for p in config_paths}
        done = 0
        for fut in cf.as_completed(futures):
            topo, wl, adv, feat, seed, path = futures[fut]
            m = fut.result()
            m.update({"topology": topo, "workload": wl, "advert": adv, "feature": feat, "seed": seed})
            results.append(m)
            csv_f.write(",".join(str(m.get(c, "")) for c in cols) + "\n")
            done += 1
            if done % 50 == 0 or done == len(combos):
                print(f"[{done}/{len(combos)}] elapsed={time.time()-t_start:.1f}s")

    csv_f.close()
    print(f"wrote {args.csv}  total_wall={time.time()-t_start:.1f}s")

if __name__ == "__main__":
    main()
