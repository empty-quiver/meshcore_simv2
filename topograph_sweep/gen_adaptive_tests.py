import json, copy

# Variant 1: quiet chain with probes ON — should fire (low rx_util)
d1 = json.load(open("/home/eve/meshcore_simv2/test/t31_topo_cold.json"))
d1["_name"] = "t31_topo_cold_probes_on"
d1["_desc"] = "Quiet chain with probes explicitly ON. Adaptive gate should NOT suppress (rx_util low). Expect probes to fire as in original Phase 2."
d1["commands"].insert(0, {"at_ms": 3000, "node": "alice", "command": "probes on"})
d1["commands"].sort(key=lambda c: c["at_ms"])
with open("/home/eve/meshcore_simv2/test/t31_topo_cold_probes_on.json", "w") as f:
    json.dump(d1, f, indent=2); f.write("\n")

# Variant 2: busy grid with probes ON — adaptive gate should SUPPRESS
d2 = json.load(open("/home/eve/meshcore_simv2/test/t_grid_ab_topo.json"))
d2["_name"] = "t_grid_ab_topo_probes_on"
d2["_desc"] = "Busy 5x5 grid with probes explicitly ON. Adaptive gate should detect busy mesh (rx_util high) and suppress probes. Expect: same delivery as passive-only; no probes fired."
d2["commands"].insert(0, {"at_ms": 3000, "node": "alice", "command": "probes on"})
d2["commands"].sort(key=lambda c: c["at_ms"])
with open("/home/eve/meshcore_simv2/test/t_grid_ab_topo_probes_on.json", "w") as f:
    json.dump(d2, f, indent=2); f.write("\n")

print("wrote chain_probes_on and grid_probes_on variants")
