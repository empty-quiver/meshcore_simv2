import subprocess, re, json

def gather(cfg):
    r = subprocess.run(["./build/orchestrator/orchestrator", cfg], capture_output=True, text=True, timeout=1200)
    out = r.stdout + r.stderr
    tfx=tdx=0; alice_flood=0; alice_direct=0
    probe_count=0
    for line in out.splitlines():
        if "[TOPO-probe" in line and "fired trace" in line: probe_count += 1
        if "node_stats" not in line: continue
        try:
            j = json.loads(line)
            if "flood_tx" in line and j.get("stats_type") == "packets":
                d = j["data"]; tfx += d.get("flood_tx",0); tdx += d.get("direct_tx",0)
            elif j.get("node") == "alice" and "sent_flood" in line:
                alice_flood = j.get("sent_flood", 0); alice_direct = j.get("sent_direct", 0)
        except: pass
    m  = re.search(r"Radio: (\d+) TX, (\d+) RX, (\d+) collision", out)
    m2 = re.search(r"ACK\+path radio: (\d+) TX, (\d+) RX, (\d+) collision", out)
    m3 = re.search(r"Delivery: (\d+)/(\d+)", out)
    return dict(total_flood_tx=tfx, total_direct_tx=tdx,
                alice_flood=alice_flood, alice_direct=alice_direct,
                radio=(int(m.group(1)),int(m.group(2)),int(m.group(3))) if m else None,
                ackpath=(int(m2.group(1)),int(m2.group(2)),int(m2.group(3))) if m2 else None,
                delivery=(int(m3.group(1)),int(m3.group(2))) if m3 else None,
                probes_fired=probe_count)

print("Running baseline (no TopoGraph)..."); b = gather("test/t_grid_ab_base.json")
print("Running fw_topo passive (no probes)..."); p = gather("test/t_grid_ab_topo_passive.json")
print("Running fw_topo full (probes on, adaptive)..."); t = gather("test/t_grid_ab_topo_probes_on.json")

def row(lbl, vb, vp, vt, lower_better=True):
    def sgn(d):
        s = "+" if d >= 0 else ""
        return s + str(d)
    dp = vp - vb; dt = vt - vb
    pp = ""; pt = ""
    if isinstance(vb, int) and vb > 0:
        pp = "({:+.1f}%)".format(100.0 * dp / vb)
        pt = "({:+.1f}%)".format(100.0 * dt / vb)
    print("{:<28} {:>10} {:>10} {:>10}   passive: {:>8} {:>9}   probes: {:>8} {:>9}".format(
        lbl, vb, vp, vt, sgn(dp), pp, sgn(dt), pt))

print()
print("{:<28} {:>10} {:>10} {:>10}".format("metric", "BASELINE", "PASSIVE", "+PROBES"))
print("-"*95)
row("alice sent_flood",           b["alice_flood"],  p["alice_flood"],  t["alice_flood"])
row("alice sent_direct",          b["alice_direct"], p["alice_direct"], t["alice_direct"], False)
row("Total flood_tx",             b["total_flood_tx"], p["total_flood_tx"], t["total_flood_tx"])
row("Total direct_tx",            b["total_direct_tx"], p["total_direct_tx"], t["total_direct_tx"], False)
row("Radio TX overall",           b["radio"][0], p["radio"][0], t["radio"][0])
row("Radio collisions",           b["radio"][2], p["radio"][2], t["radio"][2])
row("ACK+path TX (msg subset)",   b["ackpath"][0], p["ackpath"][0], t["ackpath"][0])
print()
print("Probes fired:  baseline={}  passive={}  full={}".format(0, p["probes_fired"], t["probes_fired"]))
print("Delivery: baseline {}/{}  passive {}/{}  full {}/{}".format(
    b["delivery"][0], b["delivery"][1],
    p["delivery"][0], p["delivery"][1],
    t["delivery"][0], t["delivery"][1]))
