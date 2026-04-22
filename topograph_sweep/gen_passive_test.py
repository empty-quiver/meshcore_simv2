import json, copy
d = json.load(open("/home/eve/meshcore_simv2/test/t_grid_ab_topo.json"))
d["_name"] = "t_grid_ab_topo_passive"
d["_desc"] = "Same as t_grid_ab_topo but TRACE probes disabled at t=5s. Isolates the passive-only (advert-learned graph) value from the probe contribution."
# Insert "probes off" right after warmup, before adverts fire
d["commands"].insert(0, {"at_ms": 5000, "node": "alice", "command": "probes off"})
d["commands"].sort(key=lambda c: c["at_ms"])
d["expect"].append({"type": "cmd_reply_contains", "node": "alice", "command": "probes off", "value": "disabled"})
with open("/home/eve/meshcore_simv2/test/t_grid_ab_topo_passive.json", "w") as f:
    json.dump(d, f, indent=2); f.write("\n")
print("wrote passive variant")
