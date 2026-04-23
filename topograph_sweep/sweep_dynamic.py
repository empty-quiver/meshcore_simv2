"""Dynamic-topology A/B sweep across synthetic + real urban topologies.

Applies the same SNR-variability event model (drift/shadow/deep-fade)
to each region's topology, then measures delivery + airtime per feature
across multiple seeds.

Regions:
  urban   - synthetic 10-node 2-chain corridor (urban_variability_test.json)
  gdansk  - real gdansk topology
  seapdx  - Seattle + Portland
  manh    - Massachusetts + New Hampshire

Features:
  baseline, passive_c120, passive_c120_probes, passive_c40, passive_c40_probes,
  passive_c120_ttl_short, passive_c120_ttl_long

Per region, per feature, run N seeds and emit one CSV row each.
"""
import argparse
import concurrent.futures as cf
import copy
import csv
import json
import os
import random
import re
import subprocess
import sys
import time

SIM_ROOT = '/home/eve/meshcore_simv2'
ORCH = f'{SIM_ROOT}/build/orchestrator/orchestrator'
LUA_GENERIC = f'{SIM_ROOT}/simulation/variability_generic.lua'
LUA_URBAN = f'{SIM_ROOT}/simulation/urban_variability.lua'
OUT_DIR = '/tmp/dynamic_sweep_out'

REGION_CFG = {
    'urban':  f'{SIM_ROOT}/simulation/urban_variability_test.json',
    'gdansk': f'{SIM_ROOT}/simulation/gdansk_test.json',
    'seapdx': f'{SIM_ROOT}/simulation/seapdx_test.json',
    'manh':   f'{SIM_ROOT}/simulation/manh_test.json',
}
REGION_CFG_REALISTIC = {
    'gdansk': f'{SIM_ROOT}/simulation/gdansk_realistic_test.json',
    'seapdx': f'{SIM_ROOT}/simulation/seapdx_realistic_test.json',
    'manh':   f'{SIM_ROOT}/simulation/manh_realistic_test.json',
}

FEATURES = {
    'baseline':                 (None,      []),
    'passive_c120':             ('fw_topo', ['confidence 120']),
    'passive_c120_probes':      ('fw_topo', ['confidence 120', 'probes on']),
    'passive_c40':              ('fw_topo', ['confidence 40']),
    'passive_c40_probes':       ('fw_topo', ['confidence 40', 'probes on']),
    'passive_c120_ttl_short':   ('fw_topo', ['confidence 120', 'edgettl 300']),
    'passive_c120_ttl_long':    ('fw_topo', ['confidence 120', 'edgettl 3600']),
}

METRIC_RE = {
    'radio_tx':   re.compile(r'Radio: (\d+) TX'),
    'radio_rx':   re.compile(r'Radio: \d+ TX, (\d+) RX'),
    'collisions': re.compile(r'Radio: \d+ TX, \d+ RX, (\d+) collision'),
    'ackpath_tx': re.compile(r'ACK\+path radio: (\d+) TX'),
    'delivered':  re.compile(r'Delivery: (\d+)/(\d+) messages'),
}
EVENT_RE = re.compile(r'events fired: drift=(\d+) shadow=(\d+) fade=(\d+)')

def parse_output(out):
    m = {}
    for k, rx in METRIC_RE.items():
        hit = rx.search(out)
        if hit:
            if k == 'delivered':
                m['delivered'] = int(hit.group(1)); m['sent'] = int(hit.group(2))
            else:
                m[k] = int(hit.group(1))
    ev = EVENT_RE.search(out)
    if ev:
        m['events_drift']  = int(ev.group(1))
        m['events_shadow'] = int(ev.group(2))
        m['events_fade']   = int(ev.group(3))
    return m

def extract_mutable_links(cfg, max_links=24):
    """Pull a representative sample of bidirectional links from a region config.

    For real topologies with 200+ links we sample a subset so the variability
    doesn't swamp the network. For synthetic urban we use all links.
    """
    all_links = cfg['topology']['links']
    # Filter to bidir only (unidirectional edges are usually tiny corner cases)
    bidir = [l for l in all_links if l.get('bidir', False)]
    if len(bidir) <= max_links:
        sample = bidir
    else:
        rng = random.Random(42)  # stable sample across runs
        sample = rng.sample(bidir, max_links)
    # Emit only the fields the Lua script needs
    return [{'from': l['from'], 'to': l['to'], 'snr': float(l['snr']), 'rssi': float(l['rssi'])} for l in sample]

def build_variant(region, feature, seed, traffic='base'):
    if traffic == 'realistic' and region in REGION_CFG_REALISTIC:
        cfg_path = REGION_CFG_REALISTIC[region]
    else:
        cfg_path = REGION_CFG[region]
    with open(cfg_path) as f:
        cfg = json.load(f)
    cfg = copy.deepcopy(cfg)

    fw, pre_cmds = FEATURES[feature]
    cfg['simulation']['seed'] = seed
    if fw:
        for n in cfg['nodes']:
            if n['name'] == 'alice':
                n['firmware'] = fw
        cfg['_requires_plugins'] = [fw]
    pre = [{'at_ms': 3000, 'node': 'alice', 'command': c} for c in pre_cmds]
    cfg['commands'] = pre + cfg.get('commands', [])
    # For real regions, inject our init_variability + apply_variability schedule
    # (synthetic urban config already has these entries).
    if region != 'urban':
        cfg['commands'].append({'at_ms': 0, 'lua': 'init_variability'})
        dur = cfg['simulation'].get('duration_ms', 600000)
        for t in range(30000, dur - 20000, 12000):
            cfg['commands'].append({'at_ms': t, 'lua': 'apply_variability'})
    cfg['commands'].sort(key=lambda c: c['at_ms'])

    mutable = extract_mutable_links(cfg)

    out_path = f'{OUT_DIR}/cfg_{region}_{traffic}_{feature}_s{seed}.json'
    with open(out_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    return out_path, mutable

def run_one(region, feature, seed, traffic='base'):
    t0 = time.time()
    cfg_path, mutable_links = build_variant(region, feature, seed, traffic)
    # urban scenario uses its own specific Lua file (hardcoded links)
    # other regions use the generic one + --lua-var
    if region == 'urban':
        lua_path = LUA_URBAN
        extra = []
    else:
        lua_path = LUA_GENERIC
        extra = ['--lua-var', f'links_json={json.dumps(mutable_links)}']
    try:
        r = subprocess.run(
            [ORCH, '--lua', lua_path] + extra + [cfg_path],
            capture_output=True, text=True, timeout=900, cwd=SIM_ROOT
        )
        m = parse_output(r.stdout + r.stderr)
        m['wall_s'] = time.time() - t0
        m['rc'] = r.returncode
        m['region'] = region
        m['feature'] = feature
        m['seed'] = seed
        m['traffic'] = traffic
        m['n_mutable_links'] = len(mutable_links)
        return m
    except subprocess.TimeoutExpired:
        return {'region': region, 'feature': feature, 'seed': seed, 'traffic': traffic, 'rc': -1, 'wall_s': time.time() - t0}
    except Exception as e:
        return {'region': region, 'feature': feature, 'seed': seed, 'traffic': traffic, 'rc': -2, 'error': str(e), 'wall_s': time.time() - t0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regions', default=','.join(REGION_CFG.keys()))
    ap.add_argument('--features', default=','.join(FEATURES.keys()))
    ap.add_argument('--seeds', default='42,101,202,303,404,505,606,707,808,909')
    ap.add_argument('--traffic', default='base', choices=['base', 'realistic'])
    ap.add_argument('--workers', type=int, default=14)
    ap.add_argument('--csv', default='/tmp/sweep_dynamic.csv')
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    regions = args.regions.split(',')
    features = args.features.split(',')
    seeds = [int(s) for s in args.seeds.split(',')]
    combos = [(r, f, s) for r in regions for f in features for s in seeds]
    print(f'[sweep] {len(combos)} runs: {len(regions)} regions x {len(features)} features x {len(seeds)} seeds, traffic={args.traffic}')

    cols = ['region', 'traffic', 'feature', 'seed', 'delivered', 'sent', 'radio_tx',
            'radio_rx', 'collisions', 'ackpath_tx', 'events_drift',
            'events_shadow', 'events_fade', 'n_mutable_links', 'wall_s', 'rc']
    out_f = open(args.csv, 'w', buffering=1)
    w = csv.DictWriter(out_f, fieldnames=cols, extrasaction='ignore')
    w.writeheader()

    done = 0
    t_start = time.time()
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, r, f, s, args.traffic): (r, f, s) for r, f, s in combos}
        for fut in cf.as_completed(futs):
            r, f, s = futs[fut]
            try:
                m = fut.result()
            except Exception as e:
                m = {'region': r, 'feature': f, 'seed': s, 'rc': -3, 'error': str(e)}
            w.writerow(m)
            out_f.flush()
            done += 1
            delivered = m.get('delivered', '?')
            sent = m.get('sent', '?')
            print(f'[{done}/{len(combos)}] {r}/{f}/s{s} del={delivered}/{sent} '
                  f'tx={m.get("radio_tx","?")} rc={m.get("rc")} '
                  f'wall={m.get("wall_s",0):.1f}s elapsed={time.time()-t_start:.0f}s')
    out_f.close()
    print(f'[sweep] done: {done} runs, CSV: {args.csv}')

if __name__ == '__main__':
    main()
