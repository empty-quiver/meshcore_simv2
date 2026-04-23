# OPUS Adversarial Review — TopoGraph Shipping Evidence

Reviewer: Opus, pulling punches disabled. 27,910 sim runs, 6 sweeps, 6 analysis docs, +1 firmware audit.

---

## Verdict (one paragraph)

**Ship with narrow caveats, or — cleaner — don't ship yet.** The evidence does not support the framing that "TopoGraph passive_c120 measurably improves delivery." Pooled across all 1,918 paired (non-ring) comparisons from v7/v9/v10/dyn/dyn-realistic, the passive_c120 delivery effect is **+0.06 pp, 95% CI [-0.12, +0.25], p = 0.51** — statistically indistinguishable from zero. There are exactly **zero positive cells that survive a Bonferroni or BH-FDR correction in any sweep**. The one CI-clear positive result in the dynamic sweep (gdansk_ttl_short +3.20 pp) is **p = 0.056 uncorrected** and did not replicate under a traffic-mix change on the same topology. The evidence *does* solidly show that (a) c40 is catastrophic and must not ship — this survives all corrections, and (b) passive_c120 is not *harmful* outside rings. That is a much narrower claim than "TopoGraph works." The honest shipping question then becomes: do we bless a 0-pp-effect mechanism as default because it is not harmful? I think no, not until the baseline-path-TTL counterfactual is tested and the sim is validated against at least one real-world capture. Ship the c40 *prohibition* as a finding. Keep TopoGraph on a flag. Get MQTT Boston data before flipping the default.

---

## Q1. Multiple comparisons — how many findings survive?

I recomputed paired t-tests for every (feature, cell) combination in every sweep and ran both Bonferroni and BH-FDR at alpha = 0.05.

| Sweep | Cells | Raw CI ≠ 0 | Expected by chance | Bonferroni sig+ | Bonferroni sig− | BH-FDR sig+ | BH-FDR sig− |
|---|---:|---:|---:|---:|---:|---:|---:|
| v7  | 1,200 | 106 (8.8%) | 60 | 0 | 0 | 0 | 0 |
| v9  | 192 | 35 (18.2%) | 9.6 | 0 | 8 | 0 | 19 |
| v10 | 9   | 0 | 0.5 | 0 | 0 | 0 | 0 |
| dyn | 24  | 9 (37.5%) | 1.2 | 0 | 6 | 0 | 8 |
| dyn-realistic | 18 | 6 (33.3%) | 0.9 | 0 | 6 | 0 | 6 |

The per-feature breakdown for passive_c120 / p2_c120 specifically:

- **v7 p2_c120:** 1/240 raw-CI-positive, 6/240 raw-CI-negative, **0 survive BH-FDR either direction**.
- **v9 p2_c120:** 1/32 raw-CI-positive (grid_5x5 heavy +1.46 pp), **0 survive BH-FDR**.
- **v10 passive_c120:** 0/3 raw-CI-positive. Best was gdansk +0.80 pp [0.00, +1.60]; t-test p = 0.178.
- **dyn passive_c120:** 0/4 raw-CI-positive.
- **dyn-realistic passive_c120:** 0/3 raw-CI-positive.

What *does* survive BH-FDR: **only the negative findings about c40 and multipath/probes on rings.** Every single "passive_c120 wins" claim is a raw-CI assertion, often on cells with near-saturation (192/640 v9 cells have paired delta ≡ 0 exactly because the baseline is at 100% delivery — 94.2% of v7 non-ring cells have exactly-zero paired deltas; the claim "never regresses" is mostly stating "both endpoints deliver 100% of the time").

**The team is not correcting for multiple comparisons and is repeatedly reading raw-95%-CI-excludes-zero as meaningful.** It isn't. You don't get to run 1,200 tests and report the 8 that came up positive.

**But fairness cuts both ways:** the c40 cliff is a real, robust, survives-anything finding. If you showed me just "c40 is a 10–30 pp regression on non-trivial topologies, 16/16 v9 cells sig-neg under BH-FDR" I would call that rock-solid.

---

## Q2. Retraction pattern — healthy self-correction or fishing expedition?

The retraction pattern is *partially* a sign of good methodology. Points in the team's favor:

- They did walk back the v7 probes-on-trees +5.4 pp claim when v9 showed −3.1 pp with more seeds.
- They did walk back mp2/mp3 when v9 showed 0/32 sig-positive cells.
- They documented these retractions prominently in FINAL_SYNTHESIS rather than burying them.

But there are structural concerns:

- The v7 effects that got retracted were at **n = 5 seeds per cell**. Anyone running a 6-feature × 40-topology sweep knows n = 5 is too few for stable small-effect-size estimates. The team *knew* this was going to need revisiting (that's what v9 was for). The honest version is "we ran a fishing expedition at n = 5 and then verified the hits at n = 20, most of the hits died." That's less terrible than "we cherry-picked n = 5 wins and shipped them" but it's still wildly inefficient science, and the fact that **most of the v7 hits died** should make you suspicious that the v9 hits will die at n = 50 too.
- The gdansk_ttl_short finding in dyn (p = 0.056 uncorrected, p_adj = 0.15 BH-FDR across 24 cells, p_adj = 0.90 if you restrict to the 16 "interesting" non-c40 cells) **already failed replication once** on dyn-realistic (dropped to +1.43 [−0.89, +3.75]). If the team hadn't already retracted their v7 h2 result via v9, I would predict this as the next retraction.
- **Most damningly:** there is no pre-registration. No pre-stated "we will ship iff condition X holds on sweep Y at effect size Z." Each sweep redefines what "success" means after the fact. v8 declared victory via "saturation at c101" (a sim-implementation artifact, see Q3). v9 declared victory via "0/32 sig-negative" (i.e., not-harmful re-framed as winning). v10 declared victory via "CI lower bound ≥ 0 on all 3 regions" (but at n = 5, CI lower bound ≥ 0 just means the median of 5 paired deltas is non-negative — not meaningfully restrictive).

**Will passive_c120 get retracted by the next sweep?** Probably not, because the effect is so close to zero that more seeds will just tighten the CI around zero. The retraction you should worry about is someone running the baseline with a 30-minute path-TTL + one retry and finding passive_c120 gives +0.0 pp over *that* stronger baseline (see Q4).

---

## Q3. Effect-size sanity check — is +0.40 to +0.80 pp meaningful?

v10 reports:

| Region | passive_c120 delta | Per-seed deltas (pp) |
|---|---:|---|
| gdansk | +0.80 | [0, 0, 0, +2, +2] |
| seapdx | +0.40 | [0, 0, 0, 0, +2] |
| manh   | +0.40 | [0, 0, 0, 0, +2] |

That is not "+0.40 pp improvement." That is: **on 1 of 5 seeds, the feature delivered one additional packet out of 50 sent.** The other 4 seeds are a literal tie. The reported CI lower bound ≥ 0 is a tautology (the 2.5th percentile of [0,0,0,0,2] is 0). This is a 1-packet-per-50-sent signal in 1/5 runs.

For real users on a real mesh, at typical LoRa airtimes and user message rates, nobody will ever feel a 0.4 pp delivery-rate change. Users feel categorical things: "my messages always get through on this repeater, they never get through on that one." A 0.4 pp improvement is well below the noise floor of what users can perceive — and well below the seed-to-seed noise of the sim itself (v9 shows cluster_big with 26 pp CI width at n = 20).

**Is it a sim artifact?** Plausibly. The sim uses deterministic MAC-level modeling with injected RF variability, and 40% of v7 cells (84/240) have *every* baseline seed at 100% delivery — implying that the only cells that can show a positive delta are the ones where baseline is already degraded. On the topologies where baseline is not saturated, passive_c120 being +0.06 pp globally is not distinguishable from small implementation-level numerical differences (e.g., a packet arriving 1 ms earlier/later because its path was direct-routed and happened to dodge a collision). The sim has not been validated against real-world captures (see Q8), so a 0.06 pp pooled effect is exactly in the zone where "could be an artifact of the sim model" is the null hypothesis I would preregister.

The v8 "confidence saturation at 101" finding is *definitionally* a sim artifact: SNR_UNKNOWN = 100 is an encoding convention in the sim, and the "saturation" effect is just "threshold crosses the sentinel." Presenting that as a product insight ("there's no point exposing a slider") is using a sim implementation detail to simplify product decisions. That's not wrong exactly, but if the firmware implementation uses a different sentinel or encoding you'd have to rerun the whole confidence sweep.

---

## Q4. Scenario design bias — is baseline set up to fail?

**Yes, in a specific and correctable way.** The firmware audit at `/tmp/stock_firmware_dynamic_topo.md` says:

> Cache entry implicit TTL: **None — never expires**
> Firmware retry count: 0
> Self-healing after bridge failure: None — path never cleared automatically
> Time to recover WITHOUT `CMD_RESET_PATH`: **INFINITE**

So baseline in the sim is running with a *pathologically broken* path cache by design. Any time a repeater drops, baseline sits on the stale path forever (until the app layer sends `CMD_RESET_PATH`). The sim's "baseline" is not stock firmware — it is stock firmware **minus the app-layer recovery mechanism that the team's own audit says recovers in ~30-45 s**.

The dynamic sweep tests variability every 12 s. In 12 s, the app-layer retry policy fires maybe once. After 28 s (3 retries × 9.4 s) the app gives up and would issue `CMD_RESET_PATH` on the real handset. The sim presumably does not do this. If the sim baseline had even a *single* implemented retry + `CMD_RESET_PATH` call, my prior is that most of the ttl_short / ttl_long "wins" would evaporate, because what TopoGraph_ttl_short is really simulating is "dump the stale path faster than the app would force-dump it anyway."

**I am not saying the sim is rigged maliciously.** I am saying the baseline in the sim represents a strictly weaker thing than MeshCore-in-the-field, and the feature under test (passive_c120) is partially a workaround for a limitation that already has a better fix in stock firmware. A credible evaluation would compare:

1. sim-baseline (no TTL, no retries) — current sim baseline
2. sim-baseline + CMD_RESET_PATH after N failures + path TTL (= realistic stock behavior)
3. sim-baseline + TopoGraph passive_c120

The team has not run (2). Until they do, the shipping recommendation is being compared against a strawman.

---

## Q5. Cherry-picking lenses — the "double-win" framing

The dynamic analysis reports "double wins" (delivery up AND tx-per-delivered down). These are not independent metrics. If delivery goes up by X and radio_tx stays constant, tx-per-delivered *mechanically* goes down. The lens is not revealing a second independent effect; it's restating the same delivery delta with a ratio.

Concrete: seapdx passive_c120 on dyn-realistic has delivery delta +1.31 pp (CI [−1.43, +4.11], not sig) and tx-per-delivered delta −31.25. If you ask "is the airtime-per-delivered improvement CI-significant?" the analysis does not report that test. The "double-win" framing lets a non-significant delivery result be re-described as a win because the ratio improved "too."

Similarly, v10 reports passive_c120 has "radio cost < 1.5%" — which is true but also a consequence of the delivery delta being ≈ 0. Where delivery is unchanged, total radio_tx is largely unchanged. It is not an independent win.

**The number of lenses applied (delivery pp, paired CI, pooled CI, tx-per-delivered, tx-per-delivered delta, double-wins, max-topo-gap, max regression) is large.** Even without p-hacking across seeds, picking the right lens per finding is its own multiplicity problem.

---

## Q6. The gdansk ttl_short surprise

Dynamic base gdansk_ttl_short: +3.20 pp, **95% CI [+0.30, +6.30]**, per-seed deltas [−6, −6, −4, −4, −2, −2, −2, 0, 0, 0, +4, +4, +4, +8, +8, +8, +10, +12, +12, +20]. Uncorrected paired t-test **p = 0.056**.

If I ran one BH-FDR correction across the 24 (region × non-baseline-feature) cells in the dynamic sweep, **this result does not survive (p_adj = 0.15).** If I restrict to the 16 non-c40 cells (still plausible: c40's catastrophic regressions are pre-understood, you wouldn't include them in a "did any subtle feature help?" family), **p_adj = 0.90.**

And then on dyn-realistic — same gdansk topology, same 20 seeds, same RF events — the delta dropped to **+1.43 pp [−0.89, +3.75]**. In other words: change the traffic mix, on the same topology, with the same seeds, and the effect loses significance. That is a classic "single-study finding that doesn't replicate under a small perturbation" — i.e., exactly what a p-hacked result looks like. It is right at the p = 0.05 boundary and failed a replication.

The team's own analysis calls this out honestly ("Under a pre-registered multi-region success criterion, ttl_short fails") and recommends *against* shipping ttl_short — so the honesty is there. But the *existence* of this finding, prominently in the dynamic analysis, is evidence that the team is willing to CI-lower-bound-at-zero a feature that they know does not generalize. It is the precise pattern that would produce a passive_c120 default by the same process: "here's a feature with mean > 0 on some slice and a CI touching zero; ship as default because it is not sig-negative."

**It is not that ttl_short's finding hides a deeper methodological issue. It is that it perfectly exemplifies the methodological issue.**

---

## Q7. Engineering merit — is TopoGraph a defensible design?

**Probably yes, in isolation.** Graph + SNR weighting + BGP penalty + edge aging is a reasonable companion-side design for a passive path-quality store. The BGP-style dampening is standard art. The code is concentrated on the companion side (per the team's framing), which is the correct layer for path policy — the firmware should stay dumb and fast.

**But "is it the simplest thing that works?" — no.** Looking at the firmware audit:

- Baseline's path cache has **no TTL**. Adding a 30-minute TTL is ~10 lines of code.
- Baseline has **no firmware-level retry**. Adding "retry-after-timeout, then reset-path-on-retry-exhaustion" is a straightforward modification.
- Baseline has **no path-penalty on ACK timeout**. Adding "on timeout, clear cached path" is ~3 lines.

If you made those three changes to baseline, how much of TopoGraph's (tiny) measured benefit would remain? The team doesn't know because they haven't run that experiment. I would bet significantly more than zero of the "dynamic contention resistance" pattern observed on manh/seapdx is attributable to TTL expiry, not to BGP-style penalty or SNR weighting.

The question isn't "is TopoGraph defensible?" It is "is TopoGraph the right marginal investment given there are three simpler changes that likely capture most of the benefit at a fraction of the code-size and mechanism-maintenance cost?" I don't see that comparison anywhere in the evidence.

---

## Q8. Sim model validity

The team admits it: "MQTT Boston data is future work." The entire evidence base rests on a sim that has not been validated against a single real packet capture. Given that:

- v8's confidence-saturation finding is a sim encoding artifact (SNR_UNKNOWN = 100).
- v7's 192/640 (30%) exactly-zero paired-delta cells are a sim saturation artifact (ceilinged delivery rate).
- Urban (10-node toy) has sd = 13 pp at n = 20 — the noise floor of a tiny sim topology dominates any signal there.
- The v10 "real topology" regions are RF-propagation-simulated on SRTM/ITM, not real packet captures. The topology is real; the mesh behavior is not.
- The sim baseline is a strawman (Q4).

Should any conclusion be trusted without real-world validation? The c40 cliff conclusion — yes, because it is so large (10-30 pp) that it would survive any modest sim-vs-reality gap. The passive_c120 benefit conclusion — **no**, because the claimed effect size (0-1 pp, median zero) is comfortably inside any plausible sim-model error bar.

"Future work" is not a valid place to put the validation step for a feature you are recommending for default-on shipping. Validation needs to happen *before* default-on, not *before the next paper*.

---

## Q9. The honest shipping question

Pooled across all 1,918 non-ring paired comparisons in v7 + v9 + v10 + dyn + dyn-realistic:

```
passive_c120 delivery delta: +0.0625 pp
95% CI: [-0.1223, +0.2474]
t-test p = 0.5075
median = 0.000
  exactly zero:  1,686 / 1,918 (87.9%)
  positive:        124 / 1,918  (6.5%)
  negative:        108 / 1,918  (5.6%)
```

The feature produces an exactly-zero paired delta in **88% of the runs it was tested on.** On the 12% where it moves the number at all, it is roughly as likely to go up as down. The aggregate effect is +0.06 pp, p = 0.51, CI comfortably contains zero.

Against that headline: the team is shipping a default that adds:
- A new graph data structure (SNR-weighted directed graph).
- BGP-style penalty bookkeeping (non-trivial; dampening semantics are famously where routing bugs hide).
- An edge TTL timer (reasonable, but a new periodic task).
- A confidence threshold that will inevitably have to be re-tuned per firmware version as sim-vs-real discrepancies surface.

The code-size, complexity, and maintenance cost of this is bounded but non-zero. The baseline has **known unfixed issues** (no path TTL, no retries) that would be cheaper to fix and might capture most of the claimed benefit.

So the honest question — "does shipping passive_c120 as a default actually make the firmware better?" — resolves to: **probably 0-1 pp real delivery improvement, at nontrivial code-size + new-mechanism cost, with a cheaper alternative untested.**

That is not a ship-as-default profile. That is a ship-as-optional-flag profile, if at all, until (a) the baseline-with-TTL comparison is run, and (b) the sim is validated against any real packet capture.

---

## Q10. Bottom line — would I sign off?

**No. Not as default.** My confidence in "this is a small, unreliable, sim-specific effect that has not cleared multiple-testing or validation thresholds" is high (>80%). My confidence in "TopoGraph is harmful" is low — the feature clearly does not regress on non-ring topologies. So the shippable version is:

**Ship as a non-default opt-in flag with the retraction list already in release notes. Do not flip the default.**

The single most important thing to do before recommending default-on to real users is:

> **Validate the sim baseline against one real MQTT capture, and re-run passive_c120 against a baseline that includes firmware path-TTL + one retry + CMD_RESET_PATH-on-timeout.**

If passive_c120 still shows a measurable (not just CI-lower-bound-at-zero) delivery improvement on real capture data over an equivalently-tuned baseline, ship it. If it doesn't, the feature is a 20-line TTL in baseline plus some modest retry logic away from redundant.

Ship the *findings* from this work unambiguously:

- c40 / loose-confidence variants must not ship. (Rock-solid, survives all corrections.)
- Rings are a structural failure mode. (Well-documented, correct.)
- Probes and multipath don't pay. (Correctly retracted.)
- Baseline's no-TTL path cache is a real firmware issue. (The audit makes this clear and the sim supports it indirectly.)

These are valuable, independently of whether the positive default-on case for passive_c120 holds up.

---

## What I'd demand before recommending this to real users (5 bullets)

1. **Real-world validation.** One MeshCore MQTT packet capture (or any real-hardware 4-hour capture) compared seed-for-seed against the sim's predictions for the same topology. If the sim's baseline delivery rate is off from reality by more than 5 pp, the 0.06 pp default-on case is indefensible until the sim is fixed.
2. **Counterfactual baseline.** Rerun the full dyn + dyn-realistic sweep against a *fixed* baseline that adds (a) 30-minute path-TTL and (b) app-layer CMD_RESET_PATH after 3 retries. If passive_c120 still shows even +0.3 pp over *that* baseline pooled across regions with CI excluding zero under BH-FDR, ship it. Otherwise, ship the baseline fix and put TopoGraph behind a flag.
3. **Pre-registration for the decisive sweep.** Before running the sweep above, write down: the feature under test, the effect size to detect, the topologies, the seeds, the analysis plan, and the pass/fail criterion (including the MC correction). File it as an issue, timestamp it. Report the pre-registered outcome.
4. **Power analysis for cluster_big and any dynamic-traffic cell.** v9 shows 26-pp CI widths at n = 20 on cluster_big. The current evidence is underpowered to detect sub-5-pp effects in realistic-density topologies. Either 50+ seeds or longer sim runs per seed, and state the power target up front.
5. **A "null-case" check.** Ship the passive_c120 code but gate it to no-op on boot (e.g., same binary, flag off). Run the same sweep suite. If you still find 5-8% of cells with raw-CI-excludes-zero deltas against true-baseline, the entire CI machinery in these sweeps has a systemic bias (likely seed-pairing or sim-nondeterminism) and all conclusions need to be revisited. If instead all cells come back with deltas ≈ 0, the CI machinery is honest. You have not run this sanity check.

---

## Fairness footer

To be explicit about what I think the team did well:

- Retracting v7 h2-probes after v9 showed the opposite sign is not trivial self-correction. Many teams would have pushed the v7 finding to release.
- Identifying the ring topology as a structural limitation, honestly, is a real finding.
- The c40 cliff characterization is thorough and credible.
- The v8 factorial design is a well-structured ANOVA attempt; the analysis is decent.
- The probes_on == probes_c120 identical-output flag is a genuine bug catch that the team correctly escalated.
- The dyn-realistic sweep was a good instinct — test the traffic assumption — and it was correctly allowed to retract the gdansk_ttl_short finding rather than being buried.

These are all signs of a team that wants to be right. But wanting to be right is not the same as being right, and the pattern of reading raw-95%-CI-excludes-zero as "finding" on 1,200-cell sweeps is the exact mechanism by which serious, honest teams end up shipping nothing-burgers. Please run the counterfactual baseline before you flip the default.
