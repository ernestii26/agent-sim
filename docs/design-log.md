# Design log — pd_matched

Decisions and the measurements behind them, recorded so nothing here has to be
re-run. Scripts that produced these numbers are named per section; re-run one only
when the design it describes has changed.

Session: 2026-08-24. Nothing had been run through the post-restructure pipeline at
this point — `results/` held only pre-2026-08 archive charts.

---

## 1. The persona sets, audited

### `prestige_dominance` — 18 hand-written, corporate

Prestige and Dominance differ on nearly every trait, not only on influence style.
Scores are the personas' own 0-10 `cultural_profile` values.

| trait | P (n=5) | D (n=5) | gap |
|---|---|---|---|
| openness | 8.4 | 5.2 | 3.2 |
| conscientiousness | 8.2 | 8.2 | 0.0 |
| extraversion | 5.6 | 8.0 | **2.4** |
| agreeableness | 7.6 | 2.4 | **5.2** |
| neuroticism | 2.4 | 2.0 | 0.4 |
| hierarchy_preference | 4.2 | 6.6 | 2.4 |
| conflict_tolerance | 5.0 | 7.8 | 2.8 |

Mean age P 44.8 / D 48.4 / N 41.1. Gender roughly balanced in every group.

The extraversion gap is the dangerous one: the dependent variable is votes, talkative
agents get more of them, so a D win could be airtime rather than dominance. Partly
checkable for free — `summarize_contrast` already reports speech rate and words per
turn beside votes.

Occupations: D holds line authority (VP Operations, COO, Regional GM, Executive
Director Finance), P holds staff/expert authority (Principal Architect, Chief
Knowledge Officer, Director of Research). Rank is comparable; **line vs staff is not**.
That sits between confound and construct — Cheng et al.'s dominance does include
leveraging formal authority — so it is reportable as a limitation, not a defect.

### `ffni_profiles` — 36 sampled from the bank

Big Five matched to within 0.5 (seed 30, found by rerandomisation). Occupation was
not part of that search and came out badly: **three of the six D personas were
stay-at-home parents**, against zero in P, in a scenario about a division being cut.
Deleted this session; the study directory went with it (`git rm`, recoverable).

---

## 2. The bank, characterised

`personas_output.json`, 6.1 MB.

- 3645 entries = **243 OCEAN profiles x 15 occupations**, each cell exactly once. A
  perfect full factorial with no gaps or duplicates. `is_valid` true for all 3645.
- OCEAN is recorded as low/medium/high; `sample_bank.LEVEL_SCORES` maps these to 2/5/8.
- **Demographics are orthogonal to personality.** Mean trait level (0-2 coding) across
  the six age x parenthood cells stays within 1.00 +/- 0.08 for all five traits. A
  demographic-based grouping therefore carries no personality confound by construction.
- Occupations are a general population sample (prosecutor, truck driver, stay-at-home
  parent, ...), not a workforce. Only one coherent workplace subset exists:
  **ER nurse / pharmacist / hospital administrator / social worker = 972 entries,
  covering all 243 profiles.** Filtering to it costs no personality range.
- Age groups 25-35 / 36-50 / 51-65, roughly 1200 each; `is_parent` split 1828 / 1817.
  Usable later as a reproductive-timing proxy if a life-history moderator is wanted.

---

## 3. Why assignment was changed from random to paired

Simulation of the existing `sample_bank.py` scheme over **2000 seeds**, 6 personas per
group:

| quantity | value |
|---|---|
| max P/D Big Five gap, median | **2.00** |
| max gap, mean | 2.25 |
| 25% of seeds exceed | 2.50 |
| 10% of seeds exceed | 3.00 |
| worst seed | 5.00 |
| seeds reaching gap <= 0.5 | **0.9%** |
| seeds with unequal stay-at-home-parent counts across P/D | **50%** |
| seeds off by >= 2 | 8.3% |

The sampling was already uniform — `stratified_sample` takes one entry per distinct
OCEAN profile, and occupation is uniform within profile. The imbalance is n = 6 with
simple randomisation, which no amount of extra uniformity fixes. Rerandomisation only
balances the variable it searches on, and each extra criterion multiplies the seeds
needed (0.9% x 50% for two).

`tools/pair_bank.py` replaces it: P_i and D_i are built from **the same bank row**, so
Big Five, occupation, age group and parental status are identical by construction.
Verified gap = **0 at seeds 0, 7, 42, 99** — and necessarily at every other seed. The
same equalities are `assert`ed at the end of every run of the script.

Agents never see each other's persona file, so a P and a D sharing an occupation has
no effect inside the simulation.

---

## 4. Detectable effect size

`tools/power_sim.py`, 3000 reps per cell (the script now defaults to 1000, which
reproduces these to within ~2 points and finishes in about 45 seconds).

Effect size `r` = D's relative attractiveness as a vote target; r = 1 is the null.

### Each condition on its own (paired t-test, D > P)

| r | mean D votes | mean P votes | 20 runs | 40 | 60 |
|---|---|---|---|---|---|
| 1.0 | 1.03 | 1.00 | 4% | 5% | 5% |
| 1.5 | 1.38 | 0.97 | **36%** | 60% | 75% |
| 2.0 | 1.83 | 0.90 | **78%** | 96% | 99% |
| 3.0 | 2.44 | 0.83 | 99% | 100% | 100% |
| 4.0 | 2.99 | 0.78 | 100% | 100% | 100% |

### The interaction (threat gap > collaborative gap), collaborative fixed at r = 0.7

| r under threat | 20 runs/condition | 40 | 60 |
|---|---|---|---|
| 0.7 | 5% | 5% | 6% |
| 1.5 | **54%** | 78% | 91% |
| 2.0 | **83%** | 98% | 100% |
| 3.0 | 99% | 100% | 100% |
| 4.0 | 100% | 100% | 100% |

**The interaction is better powered than either condition alone** (54% vs 36% at
r = 1.5), because the collaborative condition anchors in the opposite direction and
widens the gap being tested. It is also the only test that matches the claim
"threat causes a shift". Two separately significant one-sided tests are not evidence
of a difference between them.

At 20 runs the design resolves only a large effect — D taking roughly twice P's votes.

---

## 5. Decisions

| # | Decision | Reason |
|---|---|---|
| 1 | Vote prompt changed to *"Based on what you observed, who should lead this team?"* | The previous wording asked who you most **trust**, and trust is prestige's defining currency in the dual model (Henrich & Gil-White 2001; Cheng et al. 2013). It loaded the dependent variable against H2. Applied to all three studies; no data existed yet, so the change was free. |
| 2 | 20 runs per condition, declared a **pilot for estimating effect size**, not a confirmatory test | Section 4: 20 runs only resolves r >= 2. Reporting a p-value from it and extending if borderline would be optional stopping. Confirmatory n gets chosen from the observed r. |
| 3 | The **interaction is the primary test**; per-condition t-tests are descriptive | Section 4, and it is what the hypothesis claims. Not yet implemented — `summarize_contrast` handles one condition at a time. |
| 4 | Added `instruments/threat_check.json` — 3 items, `about: self`, `post` only, N respondents | Without it a null is uninterpretable: no way to separate "threat does not shift preference" from "the scenario did not feel threatening". Costs 8 calls per run (+20%). Mentions no leader or person, so it cannot prime the vote. Post-only because the between-condition difference is the check; a pre-scenario baseline would measure trait threat-sensitivity instead. FFNI's protection subscale was not borrowed for it, for three reasons in order of weight: it measures a *need* for a protective leader, not felt threat; that need is exactly H6's mediator, so checking the manipulation with it would be circular; and every item names a leader, which the check must not do. (Licensing is a distant fourth — the full 22 items are reproduced verbatim under CC BY-NC-ND, which is permitted, but carving 4 of them out as a standalone short scale would be abridging.) |
| 5 | Rounds stays at 3; verify on the 3-run smoke test before committing | `P1` and `D1` are both low-extraversion (necessarily — they are a matched pair). Each appears in roughly 3.3 of 20 runs, so about 30% of runs could carry a near-silent leader with no impression to vote on. `run.py validate` cannot catch this: `summarize_validation` judges only groups with `sample is None`, i.e. N alone. |
| 6 | Contrast report now prints per-persona speech rate for the **sampled** groups | Closes the gap in decision 5. Flags any contrasted persona speaking in a third of their turns or less. `analysis.summarize_contrast` gained a `personas` key; `render._render_sampled_speech` prints it. |
| 7 | Neutral pool cut 24 -> 8, fixed every run | Only 8 were drawn per run anyway. A rotating audience adds between-run variance and costs power at 20 runs; a fixed panel makes the finding conditional on those 8, which is the right trade for a pilot. Also makes `pd_matched` and `prestige_dominance` structurally identical (10 agents per run) so the two can be compared. |
| 8 | Deleted `studies/ffni_profiles/` and the stale `prestige_dominance/personas/manifest.json` | Section 1. The manifest used an older schema and nothing reads it — `gen_personas.py` writes it, no reader anywhere. Instruments were byte-identical to `ffni_mediation`'s, so no measure was lost. |

## 6. Bugs hit while running this design

- **Missing `nationality` crashed every persona turn, silently.** The first
  `pd_matched` smoke test showed near-zero speech for the contrasted P/D personas
  *and* a 100% failure on the threat_check survey in the same run — looked like two
  problems, was one. `tools/pair_bank.py` builds personas via
  `sample_bank.to_tinyperson_spec()`, which never set `nationality`; tinytroupe's
  `minibio()` indexes that key directly on nearly every turn with no fallback, and
  `AgentTransport`'s catch-all logs the `KeyError` as a plain silent turn. Fixed by
  setting `"nationality": "not specified"` in `to_tinyperson_spec`. Full writeup:
  `docs/ERRORS_AND_FIXES.md` P6. Personas were regenerated after the fix (same
  seed); the pre-fix `pd_matched/threat` checkpoint was discarded, not analysed.

## 7. Second bug: DISCUSSION_MAX_TOKENS ceiling hit mid-run, condition-correlated

While running `pd_matched` to 20 runs/condition (2026-08-24), `collaborative` ran
visibly slower than `threat` and its log showed repeated `LengthFinishReasonError`
retries — same root cause as the pre-existing P3 in `docs/ERRORS_AND_FIXES.md`, but
recurring as an unwinnable retry loop (P7 in that file has the full writeup and the
token counts). Left running rather than interrupted; not yet fixed.

The finding worth keeping regardless of the bugfix: **threat's dominant persona cuts
discussion short, collaborative's neutrals build consensus over more turns**, and
longer discussions are exactly what pushes `prompt_tokens` toward the ceiling. So the
truncation rate is plausibly condition-correlated, not uniform noise — worth checking
before trusting a speech-rate comparison across these two conditions at the current
`DISCUSSION_MAX_TOKENS = 3000`. Applied to `config.ini` (gitignored, so not in version control):
`DISCUSSION_MAX_TOKENS` 3000 -> 6000, and separately `MAX_ATTEMPTS` 5 -> 3 /
`EXPONENTIAL_BACKOFF_FACTOR` 5 -> 3 so a call that still truncates gives up in
~8s instead of 300+s. Retries are not fully deterministic (discussion runs at
temperature 0.7, so a retry resamples rather than repeating identically) — of 13
truncated calls logged, 11 succeeded within 1-3 retries and only 2 (at
prompt_tokens 8381 and 8648) exhausted all 5 and gave up. 4500 was tried first and
raised to 6000 instead of guessing whether the margin covered the worst tail case:
the ceiling costs nothing unless the model actually needs it, so there is no
downside to generous headroom, unlike trimming cast size or rounds — both already
calibrated (section 4's power simulation assumes the 10-person cast, section 5
decision 5 fixed rounds at 3 specifically so the low-extraversion matched P1/D1
pair gets a chance to speak). Takes effect on the next process started — the
in-flight `collaborative` run already had the old config in memory and was left
running rather than restarted. Re-run collaborative under the new ceiling once it
finishes, if the truncation-rate asymmetry in section 7 looks large enough to matter.

## 8. Results — 20 runs/condition, 2026-08-24

Both conditions complete (threat under the old 3000-token ceiling before the P7 fix
landed mid-run; collaborative straddled the fix — see section 7). `run.py report` for
each, plus `tools/interaction_test.py` for the primary test.

| test | result |
|---|---|
| H1 (collaborative: P > D votes) | NOT supported, p = 0.440 (P wins 8/20) |
| H2 (threat: D > P votes) | **supported**, p = 0.003 (D wins 15/20, mean 6.25 vs 2.20) |
| **Interaction** (threat's D-P gap > collaborative's) | **supported**, p = 0.011 (mean D-P: threat +4.05, collaborative -0.20) |

The interaction is the test that actually matches the claim in decision 3 — threat
does not merely favor D in isolation, it favors D **relative to** an otherwise-neutral
collaborative baseline (collaborative's D-P gap sits at essentially zero, not favoring
either side). H1 not holding is not a failure of the design: it means the effect in
threat isn't just an existing D advantage getting amplified, since there was no D
advantage to begin with under collaboration.

Threat's speech-rate gap (0.98 vs 0.85, p = 0.008) is real but far too small to explain
a 6.25-vs-2.20 vote gap on its own. `words_per_turn`'s p = 1.000 in both reports is a
reporting artifact, not a finding — `summarize_contrast` always tests contrast[0] >
contrast[1] one-sided, and P consistently talks *more* per turn than D in both
conditions, so that metric's one-sided test is checking the wrong direction; read the
raw means, not the p, for that row.

Threat_check landed within 0.1 of its pilot value in both conditions across 20 runs
(threat 5.38 vs pilot 5.29; collaborative 3.21 vs the single collaborative pilot's
implicit range) — the manipulation is stable, not a fluke of small samples.

## 9. Vote reasons were never read until now — and they complicate H2's mechanism

`run_vote` (src/discussion.py) has always asked every agent for a one-sentence reason
alongside their vote, and it has always been stored in every checkpoint. No analysis
function has ever read it — `summarize_contrast` only counts the vote. `tools/vote_reason_scan.py`
closes that gap by keyword-scanning the reasons against the dual-strategies model's own
defining vocabulary (Cheng et al. 2013 / Henrich & Gil-White 2001): dominance is influence
via **fear and coercion**, prestige is influence via **freely conferred respect** grounded
in demonstrated competence.

| | threat, D votes (n=125) | threat, P votes (n=44) | collab, D votes (n=55) | collab, P votes (n=59) |
|---|---|---|---|---|
| decisive/responsible framing | 84% | 52% | 82% | 36% |
| coercion/fear language | **0%** | 2% | **0%** | 0% |
| reasoning/evidence language | 0% | 7% | 0% | 0% |

Coercion/fear language is essentially absent from vote justifications **in both
conditions**, even for D votes, even though D's own transcript behavior is explicitly
coercive by design (`STYLE_BLOCKS["D"]` in `tools/sample_bank.py`: "states conclusions
as settled," "treats a challenge as something to be shut down"; observed in transcripts,
e.g. "We're doing it this way. Next," "Decision's made"). Instead, voters overwhelmingly
justify a D vote with competence/decisiveness language ("stepped up," "took
responsibility," "made sure we reached a decision") — and this framing rate is nearly
identical across conditions (84% threat vs 82% collaborative), so it is not something
threat specifically switches on.

**This does not undercut section 8's result** — the vote counts and the interaction
test are unaffected; H2 and the interaction are behavioral findings about who gets
votes, not about why. What it complicates is the **theoretical attribution**: the
result is consistent with the dual-strategies account only if "dominance" is read
loosely as decisive/authoritative behavior. Read strictly — influence via fear and
coercion — the voters' own stated reasoning never once describes it that way, in
either condition. Two explanations, not distinguishable from this data alone:

1. In a threat scenario, D's behavior (interrupt, foreclose discussion, decide
   unilaterally) *functions* as decisiveness, and that's what gets rewarded — the
   fear/coercion channel the theory names may just not be what's operating here.
2. LLM voters may systematically reframe a vote for coercive behavior in
   socially-palatable competence language regardless of the actual driver — a known
   risk in LLM-simulated self-report, and if true it means the stated reason is not a
   reliable window into the mechanism even though it's the only mechanism data we have.

Worth citing as a limitation on any claim that this replicates the dual-strategies
mechanism specifically, not just its top-line prediction (threat -> D preferred).

**Caveat on the caveat**, raised and left unresolved rather than tested: comparing the
scan's 0% to the theory's literal "fear and coercion" is too strict a bar, because
neither this simulation nor the source literature's own vignette manipulations involve
real stakes — no human participant in a hypothetical-leader study is actually afraid of
losing their job either. A fairer comparison is to what those studies' own manipulation
checks find: participants given a coercive-leader vignette typically still rate that
leader as intimidating on a *direct* item, even knowing the scenario is hypothetical.
The scan here measured something narrower — whether voters **spontaneously volunteer**
coercion language in a one-sentence justification — not whether the perception exists
at all. Zero volunteered mentions is consistent with either "the perception isn't there"
or "the perception is there but doesn't make it into a self-justifying sentence," and
free-text mining can't tell those apart. The clean test would be a direct per-candidate
item ("how much would it cost you to oppose this person?"), matching how human studies
run this manipulation check, rather than inferring it from unprompted text. Not run —
current findings (section 8) were judged sufficient without it; revisit if the
mechanism question becomes central rather than a noted limitation.

## 10. Candidate next study — life history as a moderator

Not yet designed or run. Theory backing the idea that a fast/slow life-history proxy
(age, `is_parent`) would moderate the threat -> dominance-preference effect:

- Safra, L., Algan, Y., Tecu, T., Grèzes, J., Baumard, N., & Chevallier, C. (2017).
  Childhood harshness predicts long-lasting leader preferences. *Evolution and Human
  Behavior*, 38(5), 645-651. Childhood environmental harshness (a fast-life-history
  cue) predicts adult preference for authoritarian/dominant leaders, independent of
  current circumstances — the direct precedent for treating life-history calibration
  as a moderator of dominance-leader preference rather than just threat itself.
- Maner, J. K., & Hasty, C. R. (2023). Life history strategies, prestige, and
  dominance: An evolutionary developmental view of social hierarchy. *Personality
  and Social Psychology Bulletin*, 49(4), 627-641.
  https://doi.org/10.1177/01461672221078667. Theoretical integration: predicts a
  slow-life-history orientation favors prestige (long time horizon, cooperative
  investment) and a fast orientation favors dominance (short horizon, immediate
  resource competition) — the mechanism this study would test isn't only "threat
  activates dominance preference" but "the threat effect should be larger for
  fast-life-history individuals."
- Kakkar, H., & Sivanathan, N. (2017). When the appeal of a dominant leader is
  greater than a prestige leader. *PNAS*, 114(26), 6734-6739. Source of the
  threat/collaborative manipulation already used in `pd_matched` (economic-threat
  framing increases dominant-leader support, mediated by felt lack of control) —
  cited here because a life-history moderator study extends this design directly,
  not a new manipulation.

Age (25-35/36-50/51-65) and `is_parent` are already recorded as orthogonal to Big
Five in the bank (section 2), which is what makes this affordable: a life-history
grouping costs no personality-matching precision. Design and power sim not yet done —
see section 4's caveat, a 3-way design (life-history x condition x P/D) needs
re-running the power simulation before committing to a run count.

## 11. Still open

- The interaction test itself (decision 3) has no implementation. Both conditions'
  summaries save `per_run` values, so it is a small script over two saved summaries.
- `leadership_style: "prestige" | "dominance"` remains in the persona and reaches the
  system prompt, so agents are told their own style. That is a demand characteristic.
  Cheap to test later: drop the field, keep traits/influence/speech, re-run.
- Environment: `.venv` on CPython 3.12.14 via `uv` (the system Python is 3.14.5 and
  `tinytroupe` fails to install there).
