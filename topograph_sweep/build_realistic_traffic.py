"""Generate realistic multi-user chat workload variants of the real region configs.

Modifications vs stock region configs:
  1. Bursty sessions instead of evenly-spaced msgs.
     Each of 7 chat pairs does 3 "chat sessions" spread across the sim.
     Each session = 4 messages alternating direction over 60-90s.
  2. Fuller use of the sim duration. Current configs concentrate traffic in
     the first ~400s; these spread across ~850s of a 900s run.
  3. Denser channel traffic: 1 broadcast every ~18s from a rotating sender,
     for ~45 total per run (vs 16 stock). Represents a moderately busy
     regional channel.
  4. Bidirectional. Each session alternates speaker every message, so both
     sides of each pair see inbound and outbound traffic.

Not modeled yet (future work): app-layer retries, bursts of >1 message/s,
rich payload variation.

Output: simulation/{region}_realistic_test.json for each of gdansk, seapdx, manh.
"""
import copy
import json
import os
import random

SIM_ROOT = '/home/eve/meshcore_simv2'
REGIONS = ['gdansk', 'seapdx', 'manh']

PAIRS = [
    ('alice', 'bob'), ('alice', 'carol'), ('alice', 'dave'),
    ('bob', 'carol'), ('bob', 'dave'),
    ('carol', 'dave'),
    ('dave', 'alice'),  # back-link to keep it asymmetric
]

# Each pair does 3 sessions during the sim
SESSIONS_PER_PAIR = 3
MSGS_PER_SESSION = 4
MSG_GAP_MS_MIN = 15000
MSG_GAP_MS_MAX = 25000
SESSION_SPAN_MS_MIN = 60000
SESSION_SPAN_MS_MAX = 90000

CHANNEL_USERS = ['alice', 'bob', 'carol', 'dave']
CHANNEL_PERIOD_MS = 18000  # one broadcast every ~18s
CHANNEL_JITTER_MS = 8000   # +/- jitter

def build_traffic(duration_ms: int, seed_base: int = 42):
    rng = random.Random(seed_base)  # stable topology-level workload; sim seed varies separately
    unicasts = []
    channel = []

    # Allocate session start times per pair across the sim window [30s .. duration-60s]
    usable_start_min = 30_000
    usable_start_max = duration_ms - 90_000
    seq_counter = {}

    for pair_idx, (a, b) in enumerate(PAIRS):
        # Spread sessions roughly-evenly with jitter
        session_starts = []
        for s in range(SESSIONS_PER_PAIR):
            target = usable_start_min + int((usable_start_max - usable_start_min) * (s + 0.5) / SESSIONS_PER_PAIR)
            jitter = rng.randint(-60_000, 60_000)
            session_starts.append(max(usable_start_min, min(usable_start_max, target + jitter)))

        for sess_idx, start in enumerate(session_starts):
            t = start
            for m in range(MSGS_PER_SESSION):
                # Alternate direction within session
                if m % 2 == 0:
                    sender, receiver = a, b
                else:
                    sender, receiver = b, a
                key = (sender, receiver)
                seq_counter[key] = seq_counter.get(key, 0) + 1
                seq = seq_counter[key]
                unicasts.append({
                    'from': sender, 'to': receiver,
                    'start_ms': t, 'interval_ms': 1, 'count': 1,
                    'message': f'1to1 {sender}->{receiver} s{sess_idx+1}m{m+1} seq={seq}',
                    'ack': True,
                })
                t += rng.randint(MSG_GAP_MS_MIN, MSG_GAP_MS_MAX)

    # Channel broadcasts: round-robin senders + jitter
    t = 10_000
    ch_seq = {u: 0 for u in CHANNEL_USERS}
    while t < duration_ms - 20_000:
        sender = CHANNEL_USERS[rng.randint(0, len(CHANNEL_USERS) - 1)]
        ch_seq[sender] += 1
        channel.append({
            'from': sender, 'channel': 0,
            'start_ms': t, 'interval_ms': 1, 'count': 1,
            'message': f'chan {sender} seq={ch_seq[sender]}',
        })
        t += CHANNEL_PERIOD_MS + rng.randint(-CHANNEL_JITTER_MS, CHANNEL_JITTER_MS)

    unicasts.sort(key=lambda m: m['start_ms'])
    channel.sort(key=lambda m: m['start_ms'])
    return unicasts, channel

def build_region(region: str):
    src = f'{SIM_ROOT}/simulation/{region}_test.json'
    dst = f'{SIM_ROOT}/simulation/{region}_realistic_test.json'
    with open(src) as f:
        cfg = json.load(f)
    cfg = copy.deepcopy(cfg)
    dur = cfg['simulation']['duration_ms']
    unicasts, channel = build_traffic(dur)
    cfg['_source'] = f'{region} realistic traffic variant (bursty multi-pair + dense channel)'
    cfg['message_schedule'] = unicasts
    cfg['channel_schedule'] = channel
    # Remove any pre-existing 'commands' that reference alice fw; the sweep
    # script re-adds its own feature pre-commands on top of the base config.
    # But keep any that aren't alice-feature related.
    # (Simpler: let the sweep re-add them; start from empty commands.)
    cfg['commands'] = []
    with open(dst, 'w') as f:
        json.dump(cfg, f, indent=2)
        f.write('\n')
    print(f'wrote {dst}: {len(unicasts)} unicasts, {len(channel)} channel msgs, {dur/1000:.0f}s')

if __name__ == '__main__':
    for r in REGIONS:
        build_region(r)
