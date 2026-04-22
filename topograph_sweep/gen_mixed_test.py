import json
d = json.load(open("/home/eve/meshcore_simv2/test/t31_topo_cold.json"))
d["_name"] = "t_hashmode_mixed"
d["_desc"] = "Mixed-mode test: frank on mode=2 (3-byte), alice on default mode=0 (1-byte). Verifies graph handles mixed-hash-size observations without corruption."
d["_requires_plugins"] = ["fw_topo"]
d["simulation"]["duration_ms"] = 300000
d["commands"] = [c for c in d["commands"] if not c["command"].startswith("set path.hash.mode")]
# Only frank flips modes
d["commands"].append({"at_ms": 2000, "node": "frank", "command": "hashmode 2"})
d["commands"].sort(key=lambda c: c["at_ms"])
for n in d["nodes"]:
    if n["name"] == "alice":
        n["firmware"] = "fw_topo"
with open("/home/eve/meshcore_simv2/test/t_hashmode_mixed.json", "w") as f:
    json.dump(d, f, indent=2); f.write("\n")
print("wrote mixed test")
