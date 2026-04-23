# v10 Real-Topology Validation Sweep

Source: `/tmp/sweep_v10.csv`, 60 rows, 3 regions x 4 features x 5 seeds.
All 60 rows have `rc=0` and `sent=50`. No failed runs.

## Headline numbers

| region | feature       | mean_dr  | std    | mean_radio_tx | mean_probes |
|--------|---------------|---------:|-------:|--------------:|------------:|
| gdansk | baseline      | 38.80%   | 0.0179 |        4915.2 |  0.0        |
| gdansk | passive_c120  | **39.60%** | 0.0167 |        4981.6 |  0.0        |
| gdansk | probes_on     | 36.00%   | 0.0566 |        4856.4 |  8.0        |
| gdansk | probes_c120   | 36.00%   | 0.0566 |        4856.4 |  8.0        |
| seapdx | baseline      | 48.40%   | 0.0518 |       33264.8 |  0.0        |
| seapdx | passive_c120  | **48.80%** | 0.0540 |       33256.8 |  0.0        |
| seapdx | probes_on     | 44.40%   | 0.0456 |       32802.0 |  8.0        |
| seapdx | probes_c120   | 44.40%   | 0.0456 |       32802.0 |  8.0        |
| manh   | baseline      | 36.80%   | 0.0228 |        9236.8 |  0.0        |
| manh   | passive_c120  | 37.20%   | 0.0228 |        9308.0 |  0.0        |
| manh   | probes_on     | **38.40%** | 0.0297 |        9246.4 |  8.0        |
| manh   | probes_c120   | **38.40%** | 0.0297 |        9246.4 |  8.0        |

Bold = region winner.

## Delta vs baseline (paired by seed, pp, 95% bootstrap CI)

| region | feature       | mean d_pp | range         | 95% CI           |
|--------|---------------|----------:|---------------|------------------|
| gdansk | passive_c120  |    +0.80  | [+0.0, +2.0]  | [+0.00, +1.60]   |
| gdansk | probes_on     |    -2.80  | [-10.0, +2.0] | [-7.60, +2.00]   |
| gdansk | probes_c120   |    -2.80  | [-10.0, +2.0] | [-7.60, +2.00]   |
| seapdx | passive_c120  |    +0.40  | [+0.0, +2.0]  | [+0.00, +1.20]   |
| seapdx | probes_on     |    -4.00  | [-12.0, +0.0] | [-8.00, -1.20]   |
| seapdx | probes_c120   |    -4.00  | [-12.0, +0.0] | [-8.00, -1.20]   |
| manh   | passive_c120  |    +0.40  | [+0.0, +2.0]  | [+0.00, +1.20]   |
| manh   | probes_on     |    +1.60  | [-6.0, +4.0]  | [-2.40, +4.00]   |
| manh   | probes_c120   |    +1.60  | [-6.0, +4.0]  | [-2.40, +4.00]   |

`passive_c120` CI lower bound is >=0 on all three regions (never hurts at 95%).
`probes_*` CI crosses zero on gdansk/manh and is firmly negative on seapdx.

## Important data anomaly

`probes_on` and `probes_c120` are numerically **identical** in every cell (same delivered, radio_tx, collisions, wall_s). The c120 flag has no effect when probes are on, i.e. the probe-on code path overrides the confidence setting. Flag this for the firmware team.

## probes_c120 vs passive_c120 (paired)

| region | mean d_pp | 95% CI          |
|--------|----------:|-----------------|
| gdansk |   -3.60   | [-8.00, +0.80]  |
| seapdx |   -4.40   | [-8.40, -1.20]  |
| manh   |   +1.20   | [-2.80, +4.00]  |

Probes-c120 does not beat passive_c120 on any region at 95%; it's significantly worse on seapdx.

## Radio cost deltas vs baseline

| region | feature       | d_radio_tx | % chg   | probes |
|--------|---------------|-----------:|--------:|-------:|
| gdansk | passive_c120  |      +66.4 | +1.35%  |    0   |
| gdansk | probes_on     |      -58.8 | -1.20%  |    8   |
| seapdx | passive_c120  |       -8.0 | -0.02%  |    0   |
| seapdx | probes_on     |     -462.8 | -1.39%  |    8   |
| manh   | passive_c120  |      +71.2 | +0.77%  |    0   |
| manh   | probes_on     |       +9.6 | +0.10%  |    8   |

Radio cost is noise-level for all three variants on real topos (<1.5%). Radio cost is not the blocker; delivery variance is.

## Per-seed regressions (>5pp drop vs same-seed baseline)

| region | feature     | seed | baseline -> feat | delta    |
|--------|-------------|-----:|------------------|---------:|
| gdansk | probes_on   |   42 | 38.0% -> 28.0%   | -10.0pp  |
| gdansk | probes_on   |  202 | 42.0% -> 32.0%   | -10.0pp  |
| gdansk | probes_c120 |   42 | 38.0% -> 28.0%   | -10.0pp  |
| gdansk | probes_c120 |  202 | 42.0% -> 32.0%   | -10.0pp  |
| seapdx | probes_on   |  303 | 54.0% -> 42.0%   | -12.0pp  |
| seapdx | probes_c120 |  303 | 54.0% -> 42.0%   | -12.0pp  |
| manh   | probes_on   |   42 | 40.0% -> 34.0%   |  -6.0pp  |
| manh   | probes_c120 |   42 | 40.0% -> 34.0%   |  -6.0pp  |

Zero regressions for `passive_c120` on any (region, seed) pair. All 8 regressions are probe-variant (and duplicated across the two probe cells, per the anomaly above).

## Per-region picks

- **gdansk**: `passive_c120` (+0.8pp, CI>=0). probes lose 2.8pp mean.
- **seapdx**: `passive_c120` (+0.4pp, CI>=0). probes lose 4.0pp mean, CI excludes zero.
- **manh**: `probes_on` nominal winner (+1.6pp) but CI crosses zero; `passive_c120` is +0.4pp with CI>=0 and only 1.2pp behind the probes mean.

No single feature is within 0.5pp of the region-best on all three regions:
- `passive_c120` gaps: gdansk 0.0, seapdx 0.0, manh 1.2pp.
- `probes_on` gaps: gdansk 3.6, seapdx 4.4, manh 0.0pp.

`passive_c120` misses the universal-best bar only on manh, and only by 1.2pp with overlapping CIs. Probes miss by 3.6+pp on two regions with one of those being significant.

## Shipping verdict

**Ship `passive_c120`. Confirms prior synthetic recommendation (v7/v8/v9).**

Rationale:
1. `passive_c120` never regresses on real topos: delta CI lower bound is >=0 on all three regions, zero per-seed regressions in 15 (region, seed) pairs, radio cost <1.5%.
2. `probes_*` has high variance on real topos just like on synthetic: six individual 10-12pp drops, seapdx CI firmly negative (-8.0 to -1.2). Matches the v9 retraction — probes are not a safe default.
3. `probes_*` only nominally wins on manh, and the gap vs `passive_c120` (+1.2pp) has a 95% CI of [-2.8, +4.0] — not distinguishable at 5 seeds.
4. `probes_c120 == probes_on` in the data: the c120 flag has no effect when probes are on. The combination feature adds nothing beyond `probes_on`. **Flag this to the firmware team as a likely bug or dead code path.**

Suggested follow-ups (non-blocking): (a) investigate the probes-override-c120 behavior; (b) if manh genuinely benefits from probes, consider a per-topology opt-in flag rather than a default flip; (c) a 20-seed re-run on manh would resolve whether the +1.6pp probes effect there is real or another 5-seed fluke.
