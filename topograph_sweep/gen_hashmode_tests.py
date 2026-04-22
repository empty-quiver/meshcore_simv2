import json
import copy

for hash_mode in (1, 2):
    d = json.load(open("/home/eve/meshcore_simv2/test/t31_topo_cold.json"))
    d["_name"] = f"t_hashmode{hash_mode}_topo"
    d["_desc"] = f"Live multi-byte hash test: companions set hashmode={hash_mode} ({hash_mode+1}-byte hashes). Alice on fw_topo."
    d["simulation"]["duration_ms"] = 300000
    d["_requires_plugins"] = ["fw_topo"]
    # Remove existing path.hash.mode sets (for repeaters)
    d["commands"] = [c for c in d["commands"] if not c["command"].startswith("set path.hash.mode")]
    # Set hashmode on all companions BEFORE adverts fire (at t=2s)
    for node in d["nodes"]:
        if node["role"] == "companion":
            d["commands"].append({"at_ms": 2000, "node": node["name"], "command": f"hashmode {hash_mode}"})
    # Alice on fw_topo
    for n in d["nodes"]:
        if n["name"] == "alice":
            n["firmware"] = "fw_topo"
    d["commands"].sort(key=lambda c: c["at_ms"])
    with open(f"/home/eve/meshcore_simv2/test/t_hashmode{hash_mode}_topo.json", "w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")
    print(f"wrote hashmode{hash_mode}")
