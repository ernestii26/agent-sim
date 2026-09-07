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
| 3 | The **interaction is the primary test**; per-condition t-tests are descriptive | Section 4, and it is what the hypothesis claims. `summarize_contrast` handles one condition at a time, so `tools/interaction_test.py` runs the test over the two saved summaries' `per_run` values; result in section 8. |
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
| H1 (collaborative: P > D votes) | NOT supported, p = 0.483 (P wins 8/20) |
| H2 (threat: D > P votes) | **supported**, p = 0.002 (D wins 15/20, mean 5.80 vs 1.65) |
| **Interaction** (threat's D-P gap > collaborative's) | **supported**, p = 0.007 (mean D-P: threat +4.15, collaborative -0.05) |

The interaction is the test that actually matches the claim in decision 3 — threat
does not merely favor D in isolation, it favors D **relative to** an otherwise-neutral
collaborative baseline (collaborative's D-P gap sits at essentially zero, not favoring
either side). H1 not holding is not a failure of the design: it means the effect in
threat isn't just an existing D advantage getting amplified, since there was no D
advantage to begin with under collaboration.

Threat's speech-rate gap (0.98 vs 0.85, p = 0.008) is real but far too small to explain
a 5.80-vs-1.65 vote gap on its own. `words_per_turn`'s p = 1.000 in both reports is a
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

## 11. The FFNI paper, checked against the PDF (2026-08-25)

Everything `studies/ffni_mediation/study.json` claimed about Sheng, Andrews & van Vugt
(2026) had been recorded from an earlier reading and never re-verified. Checked against
`docs/ffni-paper.pdf` (90-page preprint; the article's own page N is PDF page N+2).

**Confirmed as recorded.** All 22 FFNI items are verbatim from Table 4 — only difference
is our JSON uses ASCII `'` where the paper has `’`. All six Table 1 leadership-ideal
adjective pairs match `instruments/leader_ideal.json`. The Study 5 dominance-side null is
real (p.42): protection and status "failed to predict perceived effectiveness of
dominance-based leadership styles ... while [they] may influence leadership prototypes,
they did not necessarily translate to effectiveness perceptions."

**Two corrections, both of which understated the study's contribution.**

1. **The paper names four gaps, not two.** Beyond mediation (p.45-46, "often assume yet
   do not empirically test the mediating role of follower needs") and moderation (p.42,
   "would inter-group conflict situations ... strengthen the FFN
   protection-authoritarianism link?"), the Limitations name two more this design
   already satisfies: they call for "experimental manipulations (e.g., vignettes or
   **simulations** of threat, inequality, or uncertainty)" (p.49) because their own work
   was "entirely self-report measures and correlational designs"; and they call for
   "behavioral consequences ... such as **voting in elections**, leader support,
   resistance" (p.45-46, p.49) because they measured only cognitive and perceptual
   outcomes. The vote has been the DV here since before any of this was read.

2. **Their "effectiveness" layer never involved observing a person.** Study 5 administered
   the FFNI at T1 and, one week later at T2, asked participants to rate ~50 abstract
   leadership *descriptions* for how effective those people would be as their leader.
   So the paper's layers 2 and 3 are both abstract, and the break sits between two
   abstract measures. Rating someone you just watched lead a pressured meeting is
   untested on **both** sides — not just the dominance side. That is a larger opening
   than "replicate their null", and it is why H5 was rewritten: a dominance-side effect
   appearing here would be attributable to the shift from description to observed
   behaviour, not to a failed replication.

Also worth knowing: the paper anchors "intergroup conflict raises preference for dominant
leaders" on Laustsen & Petersen (2017), Laustsen et al. (2025) and Spisak et al. (2012),
not on Kakkar & Sivanathan (2017), which is where this project's threat manipulation came
from. Both lines are legitimate; the former are the citations to engage if writing back at
this paper.

**Structural risk to name out loud:** Step 2's instruments, layer framework, hypotheses
and entire rationale come from this single 2026 paper, which is new enough to have no
independent validation yet. H4 is the mitigation — it is a positive control, so failing to
reproduce an already-supported result would indicate a problem with this environment
rather than with the new hypotheses.

## 12. Still open

Sections 13-20 are all from the 2026-08-26 session. Nothing in `results/` was produced
under any of them — the 40 runs there predate the sampling fix, the cast change, the
electorate restriction and the persona regeneration, and are kept only as the pilot that
established the effect size everything since was sized against.

### Next actions, in order

1. **`python3 run.py measure-check ffni_mediation`** — the gate before spending on Step 2.
   Judges FFNI and `leader_ideal` together (section 20). Watch four things: `leader_ideal`
   straight-lining, since 45 items in one call has never been tried; the alphas on
   strength, masculinity and femininity, which carry 2 items each and may simply fail;
   `protection`'s **delta SD**, which is the noise floor H6's induced-need mediator has to
   clear; and whether test-retest lands above 0.85, which would mean the agents are too
   stable for a situation to move them. Roughly 80 calls, a few dollars.
2. **Consider a cheaper `SURVEY_MODEL`.** Section 15 found the post-scenario instruments
   carry 77% of Step 2's transcript cost, not the discussion. Run `measure-check` on
   `gpt-4.1-mini` and `gpt-5-mini` and take the cheapest that clears every gate.
   `DISCUSSION_MODEL` stays `gpt-4.1` — the discussion is the phenomenon.
3. **Re-run Step 1 (`pd_matched`)** under the current design. Delete `checkpoints/` first.
4. **Run Step 2 (`ffni_mediation`)**, which now shares pd_matched's personas, cast and
   scenario text.

### Known and accepted

- `effectiveness` cannot be validated before a run — it rates someone from a meeting.
  Section 20 covers the other two instruments; this one needs a post-hoc check.
- No manipulation check is administered by any study. Section 13 has the items, the
  per-item results, why it was retired, and the loader change needed to bring it back.
- `summarize_mediation`'s bootstrap resamples respondents, not runs, so it ignores that
  neutrals in one run watched the same discussion. Worth about 2 points of false-positive
  rate (section 18). Marked `ponytail:` in the docstring.
- H4 rests on a reconstruction of the ILT scale, not the instrument Sheng et al. used
  (section 19). It is a much closer replication than the 12 adjectives it replaced, but
  a failure still has more than one reading.
- Pair 1 (Hugo Marchand / Xavier Dubois) is the low-extraversion matched pair, and
  section 17 removed the text that told a quiet dominant how to dominate. Watch the
  speech-rate warning on that pair specifically in the next run.
- ~~`leadership_style` reaches the system prompt~~ — removed 2026-08-26, see section 17.
- Environment: `.venv` on CPython 3.12.14 via `uv` (the system Python is 3.14.5 and
  `tinytroupe` fails to install there).

---

## 13. The manipulation check, retired (2026-08-25)

`threat_check` is removed from `pd_matched`'s instruments list. It ran on all 40 runs
and is not being re-run. `studies/pd_matched/instruments/threat_check.json` stays on
disk as the record of what was asked; nothing loads it.

### What it was

Three items, 7-point agreement, administered post-scenario to the eight Neutral agents
only. Deliberately mentions no leader and no person, so it can neither prime the vote
nor be primed by it. Post-only: the between-condition difference is the check, and a
baseline would have measured trait threat-sensitivity instead of the situation.

1. My own position here feels insecure.
2. This situation is urgent — there is very little time to get it right.
3. If this goes wrong, the consequences for me personally will be serious.

### What it found — per item, n = 160 per cell (8 N x 20 runs)

| item | threat | collaborative | gap |
|---|---|---|---|
| 1. position feels insecure | 4.31 | 1.96 | **2.35** |
| 2. urgent, little time | 6.84 | 4.83 | 2.01 |
| 3. personal consequences serious | 4.99 | 2.84 | 2.15 |
| composite | 5.38 | 3.21 | 2.17 |

Straight-lining 0.00 in both conditions — no agent gave all three items the same
score, so the scale was discriminating rather than dead.

The manipulation worked, and it worked on the intended construct: item 1, the item
closest to threat in the theoretical sense, has both the largest gap and the cleanest
separation (1.96 -> 4.31, crossing the midpoint from a real floor).

### Two things the per-item breakdown showed that the composite hid

**Item 2 measures time pressure, not threat.** It is not carrying the effect (2.01 is
the smallest of the three gaps), but it does not belong in an average with the other
two. It also sits at 6.84/7 under threat — near ceiling, so little variance is left
for any individual-level analysis — and at 4.83 under collaborative, above the midpoint
in a scenario that named no deadline at all.

**Urgency was bundled into the manipulation itself.** The threat scenario carried
"48 hours" and "right now"; the collaborative scenario carried no deadline. So the
check cannot separate threat from time pressure — time pressure is part of the
treatment, not a nuisance. This matters because "we are on a clock, someone decide"
is a competing explanation for the D advantage, and it fits the vote reasons (84%
decisive/responsible, 0% fear) better than the theory's fear channel does.

Both scenarios now carry a matched 48-hour deadline, so this is fixed for anything
run after 2026-08-25 — but the 40 runs in `results/` predate the fix.

Neither Kakkar & Sivanathan (economic uncertainty) nor Laustsen & Petersen (intergroup
conflict) manipulate deadlines. The 48 hours was ours.

### Why it is retired rather than kept

Its job was to make a null in Step 1 interpretable, and Step 1 produced no null that
needed it: H2 p = 0.002, interaction p = 0.007. It costs roughly 20% more API calls
per run, and the effect it verified (5.38 vs 3.21, matching a smaller pilot to within
0.1) is stable enough to cite rather than re-measure.

### What this costs, stated plainly

`ffni_mediation` now has no manipulation check either, and its nulls are the ones that
were expected in advance — H5's dominance side by design, and H3 possibly. A null H3
("threat did not raise protection need") is not separable from "the scenario did not
feel threatening" without one. The mitigation is that this section's numbers stand as the evidence that the
manipulation lands.

**The deadline edit does not expire that evidence — decided 2026-08-26, deliberately.**
Matching the deadlines rewrote one clause of each collaborative scenario, so the strict
reading is that the numbers above describe text that no longer exists. Judged
non-material, and the reason is item-specific rather than a general appeal to
similarity:

- The gap that carries the manipulation is **item 1, position feels insecure**: 1.96 ->
  4.31, the largest of the three and the only one that crosses the midpoint from a real
  floor. It is driven by the threat scenario's "people will lose their posts" and
  "whether they have a future here at all". **The deadline clause touches none of that**
  — a due date does not create job insecurity.
- The item the edit does move is **item 2, urgency**, and moving it is the entire point:
  the edit exists to stop urgency differentiating the conditions. Its gap narrowing is
  the fix working, not the manipulation weakening.
- So the composite will drift (collaborative rises above 3.21 as item 2 rises), but the
  composite was never the load-bearing number — §13's own reading of the per-item table
  is that item 2 does not belong in that average.

**Residual risk, accepted:** nobody has measured the new text. If the added urgency in
the collaborative condition turns out to raise felt insecurity too — plausible if agents
read a deadline as a threat to standing rather than to schedule — then item 1's gap
narrows and nothing would catch it. What would genuinely expire this evidence is a
change to the threat scenario's stakes, or to who is in the room, not a clause about
timing.

**代價要講明**

FFNI's own protection subscale cannot substitute: it measures a want, not a state; it
is the H6 mediator, so using it would assume the conclusion; and every item names a
leader.

### If it is ever brought back

There is a structural blocker. `load_study` allows at most one instrument per `about`
kind, and `threat_check` declares `about: "self"` — the same kind `ffni` declares. So
`ffni_mediation` cannot simply add it; the loader rejects the pair. A manipulation
check is not a self-report about needs, so the fix is a fourth kind:

- add `ABOUT_MANIPULATION = "manipulation"` in `instrument.py`
- retype `threat_check.json`, add a `Study.manipulation_check` property
- render it in `run.py::_report` separately, **per item** rather than as a composite

That last point is why the item-2 problem above went unnoticed until now: `render_needs`
prints subscale means only, and it took reading the raw checkpoints to see the three
items apart. While `threat_check` was typed `about: "self"` it also became
`Study.self_report`, so the needs pipeline ran on it and the report printed two blocks
of `n/a` — a T1/delta/alpha row it can never fill, and a COGNITION vs EVALUATION table
that has no meaning for a manipulation check.

---

## 14. What the 2026-08-24 session cost, and where the money goes

**Observed: about US$42** for the session that produced the 40 runs in `results/`.
That figure covers more than the 40 runs themselves — it also paid for the personas
generated twice (the `nationality` bug in §6 invalidated the first batch), the threat
runs discarded after that fix, `validate` and `measure-check` passes, and the deleted
`ffni_profiles` study.

### The config it was spent under

```ini
DISCUSSION_MODEL = gpt-4.1     DISCUSSION_TEMPERATURE = 0.7   DISCUSSION_MAX_TOKENS = 6000
VOTE_MODEL       = gpt-4.1     VOTE_TEMPERATURE       = 0.2   VOTE_MAX_TOKENS       = 3000
SURVEY_MODEL     = gpt-4.1     SURVEY_TEMPERATURE     = 0.2   SURVEY_MAX_TOKENS     = 3000
RUNS = 20   ROUNDS = 3   MAX_ATTEMPTS = 3   EXPONENTIAL_BACKOFF_FACTOR = 3
```

Cast: 10 agents (1 P + 1 D + 8 N), two conditions.

### Measured volume, from the checkpoints

| quantity | value |
|---|---|
| runs | 40 |
| speaking turns | 1200 (30 per run — every agent spoke every round) |
| transcript words | 29,215 (730 per run) |
| API calls per run | 48 = 30 discussion + 10 vote + 8 threat_check |
| API calls, total | ~1,920 for the 40 runs alone |

### Why cast size is the dominant lever

Each discussion call carries the transcript so far. Summed over a run that is a
triangular number, so the transcript the run pays for is roughly

    cumulative words  ~  turns^2 x words_per_turn / 2

and `turns = cast x rounds`. **Halving the cast quarters the transcript cost**, and it
halves the number of calls on top of that. Measured here: 30 turns -> ~10,950 cumulative
transcript words per run.

Projected at rounds = 3, ~24 words per turn, threat_check retired:

| cast | turns | cumulative transcript | calls/run | vs now |
|---|---|---|---|---|
| 10 (1P+1D+8N) | 30 | ~10,800 w | 40 | — |
| 7 (1P+1D+5N) | 21 | ~5,300 w | 28 | **-51%** transcript |
| 5 (1P+1D+3N) | 15 | ~2,700 w | 20 | **-75%** transcript |

The same scaling applies to `ROUNDS`, which also multiplies into `turns`.

### Levers, ranked by saving per unit of information lost

1. **Cast 10 -> 7.** Biggest single saving, and the vote barely notices. `power_sim.py`
   rerun at three cast sizes, 20 runs per condition, reps = 2000:

   | cast | H2 at r=2 | interaction at r=2 | H2 at r=1.5 | interaction at r=1.5 |
   |---|---|---|---|---|
   | 10 | 78% | 82% | 37% | 53% |
   | 7 | 75% | 79% | 36% | 51% |
   | 5 | 72% | 77% | 36% | 50% |

   The DV is the per-run D-P difference, so cutting voters shrinks its mean and its
   variance together and the t-statistic hardly moves. Two caveats the sim cannot see:
   it is a weighted lottery, not a model of a discussion, so it says nothing about
   whether a room of 5 can still be *dominated* the way a room of 10 can; and the real
   cost lands on Step 2, whose individual-level n is `neutrals x runs` — 160 -> 100 at
   7 agents, 60 at 5. Do not go to 3 neutrals for a mediation study: 60 pairs against
   FFNI subscales that correlate .60-.72 in the source paper will not separate anything.
   (Those 160 were never 160 independent observations either — neutrals within a run
   watched the same discussion. The bootstrap in `summarize_mediation` resamples pairs
   rather than runs and so ignores that clustering, which is its own open item.)
2. **The manipulation check, already retired** (§13): -8 calls per run, about -20%.
3. **`measure-check` before the full study.** Costs a couple of dollars, and its whole
   job is to stop a study that cannot work from being paid for 40 runs deep.
4. **Checkpoints, already in place.** A resumed condition re-pays nothing. The `compose_run`
   fix on 2026-08-26 was needed to keep that correct, not to make it cheaper.
5. **`MAX_ATTEMPTS` 5 -> 3 and backoff 5 -> 3, already done** (§7). Truncation is
   deterministic, so the extra attempts bought nothing but wall-clock.
6. **Rounds 3 -> 2** is available but is the one lever that touches the manipulation:
   3 rounds exists so that a paired P/D who are both low-extraversion still say enough
   to be judged. Cut it only while watching the speech-rate warning in the contrast
   report, which flags anyone speaking in a third of their turns or fewer.

### What not to cut

`SURVEY_MAX_TOKENS` and `DISCUSSION_MAX_TOKENS`. Both were raised to fix silent data
corruption (P3 and P7 in `ERRORS_AND_FIXES.md`, §7 here). A ceiling only bills for what
the model actually emits, so a generous one costs nothing until it is needed — unlike
cast size or rounds, which are paid on every single call.

Switching the survey model to something cheaper is also off the table for now: the
instruments are the measurement, and a model change there is a change to the instrument,
not to the budget.

---

## 15. Cast cut to 5, runs raised to 30 (2026-08-26)

Both studies now run **1 P + 1 D + 3 of 8 N**, 30 runs per condition, replacing
10 agents over 20 runs.

### Why the vote barely notices

`power_sim.py` at three cast sizes, 20 runs, reps = 1200-2000:

| cast | H2 at r=2 | interaction at r=2 |
|---|---|---|
| 10 | 78-80% | 82% |
| 7 | 75-76% | 78-79% |
| 5 | 72-73% | 77-78% |

The DV is the per-run D-P difference. Cutting voters shrinks its mean and its variance
together, so the t-statistic hardly moves. Runs, not cast, are what buy vote power:
5 agents over 30 runs reaches 90%/92%, over 40 runs 94%/96%.

### Why the mediation does notice, and why more rooms beat bigger rooms

H6's individual-level n is `neutrals x runs`. Simulating the estimator
`summarize_mediation` actually uses — path a as the between-condition difference in
induced need, path b as a linear slope of a binary endorsement, indirect = a*b with a
percentile bootstrap over pairs — at path a = 0.5 SD and path b = +10pp per SD:

| cast | runs | n/condition | ICC = .10 | ICC = .25 |
|---|---|---|---|---|
| 7 | 20 | 100 | 88% | 81% |
| 5 | 20 | 60 | 63% | 61% |
| 5 | 30 | 90 | ~88% | ~87% |
| 5 | 33 | 99 | 91% | 89% |
| 5 | 40 | 120 | 93% | 90% |

The non-obvious result: **5 agents over 33 runs beats 7 agents over 20 at nearly
identical n** (91%/89% vs 88%/81%). Neutrals inside one run watched the same
discussion, so they share a run-level component; spreading the same n over more
independent rooms shrinks that component's weight. Raising ICC from .10 to .25 costs
the 7-agent design 7 points and the 5-agent design 2.

30 runs was chosen over 40 because it is the point where cost actually falls: 41 calls
x 30 = 1,230 against 136 x 20 = 2,720, and ~81,000 cumulative transcript words against
~105,840. **Revised to 40 in section 18** — fixing path b cost real power that had to be
bought back; 40 runs still costs 1,640 calls against the old 2,720.

### Two costs the simulation cannot price

1. **The choice set shrinks from 9 to 4.** Measured on the Step 1 data, neutrals sent
   37% of their votes to other neutrals under collaboration and only 7% under threat.
   With 3 neutrals in the room there are 2 other neutrals to pick instead of 7, so that
   share must fall mechanically, inflating both P's and D's vote counts. The
   93%-vs-63% convergence contrast — threat making neutrals converge on a leadership
   candidate at all — cannot be read off the new data, because choice-set size is now
   confounded with it. That observation belongs to the 10-agent runs and stays there.
2. **P and D go from 20% to 40% of the room.** Their absolute airtime is unchanged at
   3 turns each, but the audience thins from 8 to 3. Whether dominance behaviour works
   the same way in a 5-person room is not something a weighted-lottery simulation can
   answer, in either direction.

### Neutrals rotate again, reversing section 5

Section 5 fixed the audience at 8 because rotating observers add between-run variance
that 20 runs could not absorb. At 30 runs with 3 in the room the trade flips: fixing
the audience would rest every conclusion on 3 specific personas with no averaging at
all, while rotating 3 of 8 gives each neutral about 11 appearances and keeps the
conclusion conditional on 8 observers rather than 3.

### Where Step 2's money actually goes — correcting section 14

Section 14 concluded cast size dominates because each discussion call carries the
transcript so far. That is true of Step 1, which has no instruments. Step 2 inverts it.
Transcript-weighted, per run at cast 5:

| stage | calls | transcript each | weight |
|---|---|---|---|
| discussion | 15 | 0 -> 14 turns | 105 |
| effectiveness | 12 | full 15 turns | **180** |
| vote | 5 | full 15 turns | 75 |
| FFNI post | 3 | full 15 turns | 45 |
| leader_ideal | 3 | full 15 turns | 45 |
| FFNI baseline | 3 | none | 0 |

**The post-scenario instruments carry 77% of the transcript cost; the discussion carries
23%.** Every survey call asks the agent about "the meeting you just had", so it drags
the whole discussion along with it.

That redirects the model-substitution question. `DISCUSSION_MODEL` should stay
`gpt-4.1` — the discussion is the phenomenon under study, and it is the cheap quarter
anyway. `SURVEY_MODEL` is the expensive three quarters, and unlike section 14's claim
that swapping it is off the table, it is empirically decidable: `measure-check` exists
to tell you whether an instrument survives on a given model, gating on subscale
differentiation, straight-lining, alpha and test-retest. Prices per 1M tokens at
2026-08-26: gpt-4.1 $2.00/$8.00, gpt-4.1-mini $0.40/$1.60, gpt-5-mini $0.25/$2.00,
gpt-4.1-nano $0.10/$0.40, gpt-5-nano $0.05/$0.40. Batch API is 50% off everything but
needs an async 24-hour window, and the discussion is turn-dependent, so it is not a
near-term option.

Plan: run `measure-check` on gpt-4.1-mini and gpt-5-mini and take the cheapest that
clears all four gates. A few dollars to test, against roughly four fifths of the
dominant cost line.

### The existing 40 runs

Now incomparable to new data on two counts rather than one — the sampling fixes in
section 13's header, and this cast change. They remain valid as the pilot that
established the behavioural effect and the effect size 30 runs was sized against.

---

## 16. The electorate excludes the candidates (2026-08-26)

`summarize_contrast` now counts only ballots cast by groups that are not in the
condition's contrast. `RunRecord.votes_for` takes a `by=` filter; `group_metrics` passes
it through; the summary carries `electorate` and a `candidate_votes` block, and
`render_contrast` prints both.

### Why

Everyone in the room votes and nobody may vote for themselves, so P and D were voting in
the contest they are the candidates in. They cross-vote heavily — under threat, D chose
P 11 times out of 20, more often than it chose any neutral.

At a cast of 10 that was 2 ballots in 10 and barely moved anything. At the cast of 5
adopted in section 15 it is 2 in 5, and D can receive at most 4 votes, one of them from
its direct rival. Same design detail, double the weight.

### What it changes in the existing 20-run results

| test | all voters | neutrals only |
|---|---|---|
| H1, collaborative P > D | 2.95 vs 2.75, p = 0.440 | 2.55 vs 2.50, p = 0.483 |
| H2, threat D > P | 6.25 vs 2.20, p = 0.003 | **5.80 vs 1.65, p = 0.002** |
| Interaction | +4.25, p = 0.011 | **+4.20, p = 0.007** |
| mean D-P, threat | +4.05 | +4.15 |
| mean D-P, collaborative | -0.20 | -0.05 |

Every conclusion stands and both supported tests get stronger. H1's null gets slightly
deeper, which costs nothing — it was never close.

All figures quoted in `docs/weekly-report-2026-08-25.md` were updated to the restricted
electorate. Anything citing 6.25 vs 2.20 predates this.

### Why not simply stop P and D voting

Their ballots are data. D choosing P over every neutral is the dominance side's own read
on the prestige side, and the vote reasons attached to those ballots are the only place
a candidate explains what it saw in its rival. So they are still collected, still stored,
and reported as a set-aside line rather than folded into the test.

### Alignment this buys

H6's outcome is a neutral's binary endorsement (design decisions of 2026-08-26). The
vote-level tests now run on exactly the same ballots, so the behavioural layer and the
mediation layer are no longer computed from different electorates.

---

## 17. The `leadership_style` label removed from personas (2026-08-26)

`tools/sample_bank.py` no longer writes `leadership_style` or `style.register` into a
persona spec. `studies/pd_matched/personas/` regenerated at the same seed; the diff is
those two keys and nothing else — same names, Big Five, occupations, traits, speech
examples, same six pairs.

### How bad the leak actually was

Worse than a stray field. `tinytroupe/agent/tiny_person.py:319`:

    template_variables["persona"] = json.dumps(self._persona.copy(), indent=4)

The whole persona dict goes verbatim into the system prompt, under a `## Persona`
heading, in a template that says "You interpret the persona described below. You indeed
think you ARE that person" and "the persona characteristics ALWAYS OVERRIDE ANY BUILT-IN
CHARACTERISTICS you might have". So each agent was reading `"leadership_style":
"dominance"` as a self-description it had been instructed to embody.

That is the textbook demand characteristic: the risk was never that dominance behaviour
would be absent, but that we would be measuring the model's stereotype of the word
rather than the behaviour the style block describes.

`style.register` went for the same reason. It read "This describes how they seek
influence, not their temperament..." — meta-language about the specification, which cues
the manipulation and also contradicts TinyTroupe's own instruction that the agent must
never suggest it is following a persona spec.

### It cost nothing to remove

`leadership_style` was written by `sample_bank.py` and read by nothing. Group membership
comes from `study.json`'s `groups.ids` and is passed to `load_personas` explicitly, so
no analysis path ever consulted the field.

The timing was free too: sections 13, 15 and 16 already made the existing 40 runs
incomparable, so there was no baseline to preserve and no separate comparison run to
pay for. A dedicated labelled-vs-unlabelled comparison would have measured a design
that no longer exists.

### What still carries the manipulation

`style.influence` ("Claims influence by taking control of the room..."), the six
behavioural `traits` ("treats a challenge as something to be shut down, not examined")
and four `speech_examples` ("We're doing it this way. Next."). Concrete behaviour, no
construct name.

### The accepted cost

`register` was what told a low-extraversion dominant how to dominate quietly — "flat
refusal, cold silence and ending discussions early, not by volume". Pair 1 (Hugo
Marchand / Xavier Dubois) is the low-extraversion profile and may now go quieter than
before. The speech-rate warning in the contrast report is the thing that catches it;
watch pair 1 specifically on the next run.

### A landmine found on the way

`pair_bank.py` regenerated `study.json` as well as the personas, from hardcoded
defaults — so simply re-running it to refresh personas silently reverted `pair_with`,
`N.sample`, the corrected vote prompt, the matched deadline and the note. It now writes
`study.json` only when the file is absent and says so when it declines. Regenerating
personas is a routine thing to want; losing a week of design decisions to it is not.

---

## 18. H6's estimator rebuilt: induced need, the vote, and a within-condition path b

`summarize_mediation` changed on all three of its parts. The first two implement design
decisions taken in the same session; the third fixes a bug those decisions exposed.

### Path b was measuring the condition, not the need

The old estimator pooled both conditions and regressed endorsement on the raw need:

    pooled = data[lo_key] + data[hi_key]
    b, _, _ = slope([v for v, _ in pooled], [y for _, y in pooled])

Threat raises the need (that is path a) and raises endorsement of D directly (that is
H2, a large effect). Both variables therefore move with condition, so the pooled slope
comes out positive even when the need does nothing within either condition.

Simulated against this design with path b set to exactly zero:

| design | ICC = 0 | ICC = .10 | ICC = .25 |
|---|---|---|---|
| 5 agents, 30 runs | 12% | 13% | 14% |
| 10 agents, 20 runs | 20% | 20% | 20% |

Against a nominal 5%. Two things to note. Clustering is the smaller problem — it moves
the rate about 2 points, while the confound accounts for the rest, and it is already
12% at ICC = 0. And **the bias does not shrink with n**: the estimate is systematically
positive, only the CI narrows, so adding runs raises the false-positive rate rather than
lowering it.

Centring the mediator within each condition before pooling returns it to about 7%, at
the cost of the power that was never real:

| | pooled (old) | centred (new) |
|---|---|---|
| null, b = 0 (want 5%) | 13% | **7%** |
| real effect, b = 0.10 | 85% | **73%** |

`RUNS` goes 30 -> 40 to bring honest power back to roughly 80%. That still costs less
than the original 10-agent, 20-run design: 41 calls x 40 = 1,640 against 136 x 20 =
2,720.

`test_mediation_is_not_fooled_by_a_condition_difference_alone` is the regression test —
threat shifts both the need and endorsement, nothing relates them within a condition,
and the estimator must report no mediation.

### The mediator is now the induced need, not the level

`post` minus `baseline`, per respondent. The source paper's dominance-side null is about
the **chronic** reading of a need — its Study 5 measured FFNI at T1 and effectiveness at
T2 a week later with no event in between, so all of its variance is trait-like. The
claim being tested here is about the **state** a situation induces. A level score mixes
the two and would have made H6 partly a re-run of the null it is trying to explain.

`run.py mediate` now refuses to run if the self-report instrument has no baseline timing,
rather than silently mediating through a level.

### The outcome is now the respondent's own vote

Binary: 1 if that neutral endorsed the outcome group, 0 otherwise, including when they
endorsed a fellow neutral — voting for a quiet bystander genuinely is not endorsing the
dominant candidate, and dropping those ballots would be a non-random exclusion of
exactly the low-need respondents.

This also resolves a contradiction in the hypothesis set. H5 predicts protection will
NOT predict D's effectiveness rating, replicating the paper. H6 requires the mediator to
reach D. While both ran on the effectiveness rating they were the same coefficient with
opposite predictions, so H6 was predicted to fail by construction. Now H5 uses the
chronic level against the rating, H6 uses the induced change against the vote, and they
share neither end.

### What was skipped

The bootstrap still resamples respondents rather than runs, so it ignores that neutrals
inside one run watched the same discussion. Measured above at about 2 points of
false-positive rate, against the 8 the centring fixes. Marked `ponytail:` in the
docstring; switch to resampling runs if the observed ICC comes out high.

---

## 19. `leader_ideal` replaced with a reconstructed ILT scale (2026-08-26)

The prototype layer was 12 adjectives lifted from Sheng et al.'s Table 1. That table is
theory exposition, not an administered instrument, and it gave every subscale 2 items.
It is now a 45-item, 10-dimension reconstruction of the scale they actually used.

### Why not just drop the layer instead

Because it is not only H4's positive control. Section 11 established that the paper
measured ILT in the US and UK samples and effectiveness in the Chinese one, with no
sample carrying both — so it could not test whether the layers connect, and we can,
because all four layers are measured on the same agents in one session. That question is
the strongest thing this design has, and it needs the prototype layer measured.

### What the reconstruction is, and is not

Sheng et al. used Offermann & Coats (2018): a 46-item nine-factor revision, plus a
femininity dimension and three ethics items they added, for 51 items. Neither the 2018
items nor the article are available here.

What is available is Offermann, Kennedy & Wirtz (1994), the 41-trait eight-factor
ancestor, reproduced verbatim in Appendix A of Bhatia et al. (2022, *The Leadership
Quarterly*), plus the femininity and ethics items quoted in Sheng et al.'s own footnote
13. Together that covers **10 of the 11 dimensions they administered**, missing only
creativity, which is new in 2018. The 2018 paper's own headline is that seven of the
eight 1994 factors replicated and attractiveness became well-groomed.

Two defects recorded rather than hidden: the source appendix lists 40 traits where its
own body text says 41, so one may be missing; and no wording has been checked against
the original 1994 or 2018 article.

### What it buys

All four dominance-side dimensions Sheng et al. reported are now present under their own
names — protection -> Strength, status -> Tyranny, Masculinity, Well-Groomed. H4 moves
from "does a need track two adjectives we chose" to something much closer to a direct
replication of a published result, and subscales get 2-10 items instead of 2.

### The one-to-one mapping had to go, and that is a code change

`need_outcome_links` looked the prototype up by naming convention, `f"{name}_ideal"`,
which silently assumed each need has exactly one matching dimension. The real result is
many-to-many. Instruments now carry an explicit `predicts` block, validated at load
against the instrument's own subscale names, and the analysis averages a need's
predicted dimensions. The mapping is taken from their Study 5 results, not invented; the
single theoretical entry is affiliation -> sensitivity, since their text groups
affiliation with the prestige side but reports no per-dimension increment for it.

### Costs accepted

45 items answered in one call is a real straight-lining risk, and it is larger than the
22-item FFNI that already forced the P3 ceiling up. `SURVEY_MAX_TOKENS` goes 3000 ->
4500. Item count does not change call count — `_administer` sends a whole battery in one
call — so the cost is output tokens only.

Nothing validates this instrument yet: `measure-check` runs on `study.self_report` only,
so `leader_ideal` and `effectiveness` are unchecked for differentiation, straight-lining
and reliability. `leader_ideal` could be added to it — `about: prototype` needs no rating
target, so it can be administered twice with no discussion, exactly like the FFNI.
`effectiveness` cannot: it asks about "the meeting you just had". That remains open.

---

## 20. `measure-check` extended to the prototype layer (2026-08-26)

`run.py measure-check` now administers every instrument that can be answered without a
meeting — the self-report and the prototype — twice per persona, and gates each one
separately. It fails if any instrument fails.

`effectiveness` stays out and cannot be brought in: it asks how good a person the
respondent just watched would be as a leader, and in a measure check nobody has watched
anyone. It can only be validated after the fact, from real run data.

### Why this mattered enough to do before Step 2

`leader_ideal` was rebuilt in section 19 into a 45-item battery answered in one call.
Nothing had ever checked whether an agent can answer 45 leader adjectives without
straight-lining, and its two smallest dimensions carry 2 items each. Finding that out
after 40 runs would waste the whole prototype layer; finding it out now costs a few
dollars.

### Two changes to what the gates mean

**`delta SD` is now printed.** `summarize_needs` had computed it since the beginning and
`render_needs` never showed it. In a measure check there is no scenario between the two
administrations, so this column is the instrument's **noise floor** — how far a score
moves when nothing happened. Since H6's mediator is a change score (section 18), any
change a real study wants to attribute to its scenario has to clear this number. It is
the single most decision-relevant figure the check produces and it was being discarded.

**The test-retest gate is now two-sided: 0.40 < mean r < 0.85**, replacing r > 0.50.

The old gate was written when the mediator was a need *level*, and its reasoning was
sound for that: an agent whose answers do not correlate with its own answers minutes
earlier has no measurable trait to mediate. A change-score mediator inverts half of it.
The reliability of a difference is

    reliability(X2 - X1) = (r_xx - r_12) / (1 - r_12)

so a test-retest correlation that is too high leaves no state variance for a situation
to move, and the change is noise for the opposite reason. Only one side of that was
guarded.

### Cost

Roughly doubles the check: two administrations per instrument across the whole cast of
20 personas. Still a few dollars, against a study whose per-run cost is 41 calls over
80 runs.

---

## 21. Measurement leaked into the vote, and four decisions that followed (2026-08-26)

A grilling session over section 12's handoff. The bug came out of checking one
question — does answering an instrument disturb the agent that then votes.

### The fork was never made

`run_discussion` builds a `TinyWorld` and left it attached: every agent kept
`agent.environment` pointing at it after the discussion returned. The world holds a
`_thread.RLock`, so `copy.deepcopy` of a post-discussion agent raised
`TypeError: cannot pickle '_thread.RLock' object`. `_clone_agent` caught that with a
bare `except Exception: return person` and handed back **the original agent**.

So for any study with post instruments, every survey was administered to the live
agent, and `pipeline.run_condition` votes on that same agent immediately afterwards.
The comment "Vote last, on the original cast — nothing downstream can be primed by it"
was true only while cloning worked, and cloning had never worked after a discussion.

Verified before and after against real `TinyPerson` objects with a real `TinyWorld`
attached: before, `_clone_agent` returned the original and a write to the "fork"
appeared in the agent that voted; after, it does not.

**Scope.** Baseline administrations were always clean — they run before any world
exists, so the deepcopy succeeded. `pd_matched` has no instruments, so its votes were
never touched. `ffni_mediation` had not been run. The one study affected is the
retired `threat_check` in the 40-run pilot: 3 threat-salience items, administered to
the 8 neutrals — the entire electorate — immediately before they voted. The
manipulation numbers themselves (5.38 vs 3.21) are clean, since threat_check was the
first post instrument and nothing preceded it. What was primed is the pilot's votes,
and those votes are what section 4's effect size and the choice of 30/40 runs rest on.

**The fix.** The live wiring is stripped from the original *before* the copy and
restored in a `finally`; the bare except is gone, so a fork that cannot be made raises
instead of silently becoming a measurement on the original. `run_discussion` also
detaches the world from every participant and drops it from `TinyWorld.all_environments`
at the end, which stops one world per run accumulating for the length of a study.
`CONTEXT.md` gains **Fork** as a term, since README said "throwaway fork" and the code
said "clone" for the same thing.

### Decisions

1. **Step 1 is not re-run.** `ffni_mediation` and `pd_matched` are now identical except
   for the instruments list — same personas, groups, sampling, contrast, vote prompt,
   and both conditions' scenario and friction text, with `test_core` pinning the last
   two byte-identical. The samplers share a seed, so run *N* draws the same room in
   both. With the fork fixed, a Step 2 voter has seen no instrument, so Step 2's votes
   are Step 1's votes. H1 and H2 come from Step 2's checkpoints. What is given up is an
   independent replication of the effect; what is bought is the entire Step 1 budget.

2. **A cheap calibration pilot comes first.** Section 4's `r` was measured on primed
   voters, on a cast of 10, with the candidates voting in their own contest — none of
   which is the current design. 10-15 runs of `pd_matched` threat on `gpt-4.1`
   (discussion and vote only, the cheap quarter) re-estimate `r`, then `power_sim` sizes
   Step 2. Those votes are exchangeable with Step 2's and pool into the final test, so
   the calibration is not a sunk cost. This partly reverses decision 1's scope — but as
   calibration, not as evidence.

3. **The alpha gate is judged per subscale, not on the mean.** `protection` reaches
   exactly one prototype dimension, `strength`, which has 2 items. A mean over ten
   subscales would have waved a dead `strength` through on the back of `tyranny`'s ten,
   and H4's and H6's main line would have rested on noise the gate called usable. The
   gated set is the union of `predicts`' values, so a dimension nothing reads
   (`femininity`) cannot block a study, and one added to the map is gated automatically.

4. **`each_candidate` rates only the candidates.** `need_outcome_links` reads ratings of
   the contrasted groups and nothing else, but every neutral was rating every other
   neutral — 6 of 12 `effectiveness` calls per run collecting data no analysis looks at,
   on the most transcript-heavy line in the design (section 15). Now 6 calls, about 20%
   off Step 2. The rejected alternative was to keep them as a per-rater leniency anchor
   and centre the candidate ratings on them; that would have bought variance reduction
   for H5's expected null, at the cost of `Evaluation` no longer being the absolute
   rating `CONTEXT.md` defines it as.

### Still open after this session

- Cheaper `SURVEY_MODEL` (section 12, action 2). New evidence: on `gpt-4o-mini`, both
  the 22-item FFNI and the 45-item `leader_ideal` came back complete on the first
  attempt, every item in range, for all three respondents.
- What a failed gate actually means — abort, or proceed with the affected hypothesis
  declared dead in advance.
- No threshold is written down for `protection`'s delta SD, which section 12 calls the
  noise floor H6's mediator has to clear.

---

## 22. The effect survives every fix; `gpt-4o-mini` does not carry the manipulation (2026-08-26)

Section 21's fixes needed a run to prove them, and the cheap model was the obvious
place to start. It turned into a three-cell comparison that settles two things at once.

### What was run

All in a scratch directory; nothing in `results/` was touched.

| cell | personas | discussion model | condition | runs |
|---|---|---|---|---|
| pilot (section 8) | with `leadership_style` + `style.register` | `gpt-4.1` | threat | 20, cast 10 |
| **cheap** | current (section 17) | `gpt-4o-mini` | threat + collaborative | 20 each, cast 5 |
| **real** | current | `gpt-4.1` | threat + collaborative | 10 each, cast 5 |

### The cheap model does not manipulate anything

Counting turns where a contrasted persona claims the leadership rather than asking for
it — "I'm taking point", "I've made the call", "we're done debating" against "who's
stepping up to lead?":

| cell | D claim rate | P claim rate | N speech rate |
|---|---|---|---|
| old personas + `gpt-4.1` | **0.25** | 0.00 | 0.71 |
| current personas + `gpt-4.1` | **0.17** | 0.00 | 0.83 |
| current personas + `gpt-4o-mini` | **0.00** | 0.00 | **1.00** |

On `gpt-4o-mini` the dominance personas defer 14 times and claim nothing, which their
own `speech_examples` ("We're doing it this way. Next.") directly contradict. P and D
become behaviourally indistinguishable — the independent variable is not being
manipulated at all. The silence mechanism dies with it: every agent speaks on every
turn, so `run.py validate` would fail on that model.

Its votes follow: prestige takes both conditions equally (threat D-P = -1.60,
collaborative -1.70, interaction p = 0.43), which reads as a reversal of H2 but is
really the absence of a manipulation.

**`DISCUSSION_MODEL` therefore stays `gpt-4.1`, now on evidence rather than on the
argument in section 15 that the discussion is the phenomenon.** The case for a cheaper
`SURVEY_MODEL` is untouched and if anything strengthened: on `gpt-4o-mini` both the
22-item FFNI and the 45-item `leader_ideal` came back complete on the first attempt,
every item in range, for every respondent.

### Removing `register` did not cost the manipulation

Section 17 removed `leadership_style` and `style.register` together and accepted one
risk: that a low-extraversion dominant would go quiet. The claim rate went 0.25 -> 0.17
across a change of cast size and sample size that no test at these n separates from
zero, and what still carries the style — `style.influence`, the six behavioural
`personality.traits`, the four `speech_examples` — visibly still works on `gpt-4.1`.
Pair 1 (Hugo Marchand / Xavier Dubois) did not go quiet: D1 spoke on every turn it had.

### H2 replicates under the corrected design

`gpt-4.1`, current personas, cast 5, electorate restricted to the three neutrals, no
manipulation check priming the voters, P and D paired within the run, both conditions
carrying a deadline — every fix from sections 13 through 21 in force at once:

| | D votes/run | P votes/run | t | p | D wins |
|---|---|---|---|---|---|
| threat, 10 runs | 2.10 | 0.70 | 2.201 | **0.028** | 7/10 |

This answers the worry section 21 raised about the pilot. The pilot's H2 was measured on
voters primed by a three-item threat scale; it survives the priming's removal, so it was
not an artifact of it. D taking 2.10 of 3 available votes puts `r` near 3, where section
4's power table gives 99% at 20 runs — the calibration decision 2 of section 21 called
for is effectively answered, and `RUNS = 40` is comfortable rather than marginal.

### The interaction holds too, and more cleanly than the pilot

`gpt-4.1`, current personas, 10 runs per condition:

| test | result |
|---|---|
| H1 (collaborative: P > D) | P 1.70 vs D 0.70, p = 0.064, P wins 7/10 — direction right, short of .05 at n = 10 |
| H2 (threat: D > P) | D 2.10 vs P 0.70, **p = 0.028**, D wins 7/10 |
| **Interaction** (threat's D-P gap > collaborative's) | threat +1.40, collaborative -1.00, **p = 0.003** |

Set against section 8's pilot — H1 p = 0.483, H2 p = 0.002, interaction p = 0.007, all
at 20 runs per condition — the corrected design is doing better on half the data. The
difference is in the collaborative condition. There, the pilot's D-P gap was -0.05,
essentially nothing; here it is -1.00, so prestige actually leads when the situation is
collaborative. That is the crossover the dual model predicts, and section 8 explicitly
could not show it: it had to argue that H1's failure "is not a failure of the design"
because there was no prestige advantage to amplify. There now is one.

Most likely cause is the electorate restriction of section 16. In the collaborative
condition the two candidates split their own ballots — here D gave P 10 of 10 — so
letting them vote diluted exactly the gap H1 is about. Removing them from the count
does not change the story under threat, where the effect is large, but it is what makes
the collaborative side legible.

H1 at p = 0.064 on 10 runs is not a result to lean on; it is a direction. `RUNS = 40`
resolves it or it does not.

### What this settles

- `DISCUSSION_MODEL` stays `gpt-4.1`, on evidence.
- Section 17's persona edit is vindicated: it removed the demand characteristic without
  removing the manipulation.
- Sections 13, 15, 16 and 21's fixes are collectively sound — every hypothesis points
  the right way under all of them at once, which no run before this one could show.
- Section 21's decision 2 (a calibration pilot before sizing Step 2) is discharged.
  `r` is near 3 under threat; `RUNS = 40` is comfortable.

---

## 23. H4 was testing the wrong column of the source paper's table (2026-08-26)

Read out of `docs/2027-27008-001.pdf` Table 13, the per-dimension results of Study 5,
Sample B (N = 261) that section 19 built the `predicts` map from without reading the
table's own structure.

### The two columns disagree completely

Table 13 reports, for each of the eleven ILT dimensions, both a bivariate correlation
with each need and the increment that need adds over the other five. For Strength —
protection's only outlet and the dominance side of H4:

| predictor | correlation r | delta R2 |
|---|---|---|
| **protection** | **.38*** | **.03** |
| affiliation | .29*** | .00 |
| status | .29*** | .01 |
| vision | .32*** | .00 |
| expertise | .26*** | .00 |
| fairness | .26*** | .00 |

All six needs correlate with Strength at p < .001. Only the increment picks out
protection. This is structural, not luck: the paper's Table 8 puts the needs'
intercorrelations at r = .60 to .72, so a bivariate test cannot separate a need that
reaches a dimension from five that ride along with it.

`need_outcome_links` computed `slope(need, ideal)` — the bivariate column. H4 as
implemented would have "supported" every need on every dimension and separated nothing.
It could not have failed, which means it was not a test.

### The fix

`stats.partial_betas` fits a prototype composite on all six needs at once and returns
each need's standardised beta and its delta R2, the same hierarchical regression the
paper ran. Both are reported next to the bivariate r rather than replacing it: Table 13
shows the two columns telling different stories, and whether they do so here as well is
itself worth seeing. Relative weights analysis is not reproduced — delta R2 answers the
hypothesis and Johnson's weights would be machinery for a number nothing reads.

One thing the fix makes visible, recorded because it will otherwise read as a weak
result: **delta R2 is unique variance, so collinearity shrinks it.** The paper's own
headline increments are .02 to .06 against betas of .19 to .32. A gate or a reading that
treats .03 as small would throw away the paper's result along with ours.

### `affiliation` had an invented entry, and the table says it predicts nothing

Section 19 flagged `affiliation -> sensitivity` as the map's single theoretical entry,
taken from the paper's prose grouping affiliation with the prestige side rather than
from a reported increment. Table 13 settles it: affiliation's delta R2 is .00 or .01 on
every one of the eleven dimensions and significant on none, while its bivariate
correlations run to .54. It was the exact confound the bivariate estimator could not
see. The entry is removed; affiliation stays in the regression as a control and its
cognition row now reads n/a, which is the honest answer.

The other five entries survive contact with the table unchanged — protection ->
strength; status -> tyranny, well-groomed (our `attractiveness`, the 1994 name),
masculinity; vision -> sensitivity, dedication, charisma; expertise -> sensitivity,
charisma, intelligence; fairness -> dedication, intelligence, ethics.

### H6: the paper offers no estimator, but it does underwrite the design

The mediation passage is in Directions for Future Research. It names the gap and says
the FFNI closes it; there is no method to import, so the clustering caveat in section 18
remains ours. What it does supply is provenance for three choices already made:

- the outcome. "Future research should also go beyond cognitive and perceptual outcomes
  to examine behavioral consequences of follower needs, such as **voting in elections**,
  leader support, resistance, or insubordination."
- the method. "Future studies should use experimental manipulations (e.g., vignettes or
  **simulations of threat**, inequality, or uncertainty)."
- the mediator being a change and not a level (section 18). "It remains unclear whether
  perceived threats **increase** protection needs or whether certain individuals are
  **chronically inclined** toward this need." That ambiguity is what a within-persona
  pre-post difference resolves and a level score preserves.

And one prediction close enough to quote in the write-up: "In **hospitals**, for
instance, threats from infectious diseases may heighten the need for **protection**."
The scenario is a hospital under threat and the mediator is protection.

### Also worth having: the paper's own alphas

The eleven ILT scales ran alpha .76 to .92 on humans. Section 20's gate asks for .60,
which is lenient against that benchmark — reasonable for a first look at whether agents
can answer the scale at all, but not a claim that the instrument performs as published.

---

## 24. Step 2's design, grilled (2026-08-26)

Four findings, each of which would have cost a full study to discover afterwards.

### H5 and H7 were reading the column section 23 had just condemned

Section 23 moved H4 onto the increment over the other five needs. H5 and H7 were left on
`slope(...)`. The paper's effectiveness analysis is the same hierarchical regression as
its ILT analysis — "these relationships remained significant even after controlling for
all other FFNs" — so the null H5 is built around ("the FFNs for protection and status
failed to predict perceived effectiveness of dominance-based leadership") is a null on
the incremental statistic. Reading the bivariate column there would have manufactured a
positive result on the study's headline comparison, in the one place a null is the
expected and interesting outcome. Both layers now come from the same six-need fit, and
`layer_gap` is a difference of two standardised betas rather than of two correlations.

### Eight neutrals could not identify the need regressions

H4 and H5 regress a respondent's six need scores on their ratings. A need level is
largely a property of the persona, so the count of DISTINCT neutrals caps the
between-person variance no matter how many runs are collected: eight profiles against
six predictors, repeated fifteen times each, is a saturated model wearing an n of 120.
The paper fitted the same regressions on 261 independent people.

`pair_bank.py` already defaulted to 24 neutrals and draws from the 3,645-row bank with
no API call, so the pool was free to widen. The obstacle was that names came from a pool
shuffled by the same rng that had already drawn the persona rows — asking for more
neutrals renamed every persona, P and D included. Name assignment is now taken from the
personas already on disk, with only new ids drawing from what is unused, so it is
append-only by construction. 24 also divides evenly by the draw of 3, so every neutral
appears exactly 5 times over 40 runs and the sampler's cycle boundary never falls inside
a run.

### Four of seven hypotheses could be printed but not decided

H3 and H7 are claims about the difference between conditions. `run.py report` renders one
condition at a time, so neither comparison was computed anywhere — `cmd_mediate`'s
docstring claimed H7 and `summarize_mediation` has no moderation term. H4 and H5 reported
a coefficient with no interval, which leaves an expected null indistinguishable from
having found nothing.

`run.py layers` computes all four from both conditions' checkpoints, pooled with each
condition centred on its own means (threat moves the needs and the ratings together; a
raw pooled fit reports that shared shift as a need-to-rating link — section 18's trap).
**Its bootstrap resamples runs rather than respondents**, which discharges the clustering
caveat section 18 marked `ponytail:` and accepted for H6.

### The prototype now has a baseline, so the cognition layer is within-person

`leader_ideal` was `post` only, so H4 correlated a post-discussion need with a
post-discussion prototype — the cross-sectional design the paper is limited to, in a
study whose whole advantage is that it manipulates the situation. A baseline
administration carries no transcript (section 15's weighting: it runs before the
discussion exists), so three more calls per run at 45 items is the cheapest thing in the
design, output tokens only.

The report now carries both readings: the level-to-level beta, which is the replication,
and the change-to-change beta, which asks whether the situation moved the prototype and
moved it with the need. The second is the question the source paper's correlational data
cannot ask, and it is the same logic the mediation runs on.

### Cost

Per run at cast 5: 3 baseline FFNI + 3 baseline `leader_ideal` + 15 discussion + 3 post
FFNI + 3 post `leader_ideal` + 6 effectiveness + 5 votes = **38 calls**, against 35
before this session and 41 before the `each_candidate` cut in section 21. The six
baseline calls carry no transcript.

### H6's bootstrap now resamples runs too, and that exposed a bug in its verdict

Leaving H6 on respondent resampling would have put the study's flagship hypothesis on
looser assumptions than the report next to it, and invited the obvious question about why
two intervals in the same write-up are built differently. Both now resample runs; the
`ponytail:` marker section 18 left is discharged.

Switching the unit made a mediator that does nothing produce an interval of exactly
`[0, 0]` — every draw returns the same zero, where respondent resampling had produced
scatter around it. `supported` was written as "both bounds share a sign", and `[0, 0]`
passes that test: neither bound is above zero, so they agree. The verdict is now stated
as the interval excluding zero, which is what was meant. `[-1, 0]` had the same defect.
The regression test for the pooled-slope bug is what caught it.

### What 40 runs can actually resolve in the layer hypotheses

**Superseded by section 26.** This table was computed with a single `sd_induced`
parameter standing in for both measurement noise and real individual differences,
and against a noise floor of 1.0 that only held while item order was re-randomised
per administration. Both are gone. Kept for the record of how the question was
first framed; the numbers to use are in section 26.

`tools/layer_power.py`, 100 reps, 200 bootstrap draws, 3 respondents per run, detection
defined as the estimator's own interval clearing zero. `beta_eff = 0` throughout, so the
H5 column is a **false-positive rate**, not power — the paper's null is the expected
result there.

| lift | beta proto | b vote | runs | H3 | H4 within | H5 false positive | H6 |
|---|---|---|---|---|---|---|---|
| 0.5 | 0.5 | 0.10 | 20 | 65% | 100% | **11%** | 30% |
| 0.5 | 0.5 | 0.10 | 40 | 84% | 100% | **5%** | 67% |
| 0.5 | 0.5 | 0.25 | 40 | 84% | 100% | 5% | 84% |
| 0.3 | 0.3 | 0.10 | 40 | 42% | 99% | 5% | 41% |
| 0.5 | 0.5 | 0.10 | 60 | 94% | 100% | 6% | **88%** |

**The strongest argument for 40 runs is not power, it is H5.** Its false-positive rate is
11% at 20 runs and nominal at 40, in every cell. H5's dominance side is preregistered as
an expected null, and a null read off an 11%-false-positive test is not a null. Section
4's tables sized the vote and would have accepted 20.

**H4 is over-powered**, at or near 100% even where the effect is weak. The baseline
administration added this session is cheap and decisive, and the within-person reading is
the one the source paper's data cannot give.

**H3 and H6 are the fragile pair, and both depend on the same unknown.** H3 falls from
84% to 42% when the induced shift drops from 0.5 to 0.3; H6 sits at 67% at a modest path
b and reaches 84% only at a strong one. Both are quotients of the induced shift over the
measurement noise, and `sd_induced = 1.0` here is an assumption.

**H6 is the reason to consider 60 runs.** It goes 30% -> 67% -> 88% across 20, 40 and
60 runs at the same effect, so it is the only hypothesis for which the extra 50% of
Step 2's budget buys a crossing of the conventional threshold rather than a refinement.
H3 improves too (84% -> 94%); H4 and H5 are unaffected, being saturated and nominal
already. The decision is therefore narrow: is H6 at 67% acceptable, given it is the
hypothesis the study is named after and the one the source paper names as untested?

That assumption is exactly what `measure-check` reports. Section 12 called
`protection`'s delta SD the noise floor without saying what to do with the number; this
is what to do with it: re-run `layer_power.py --sd-induced <observed>` and read H3 and H6
off the table. If they land where cell C does, the choice is more runs or a study that
cannot speak to its own flagship hypothesis — decided before the money is spent rather
than after.

---

## 25. The measure check, run twice: the prototype scale needs temperature 0 (2026-08-26)

144 calls per run (36 personas x 2 instruments x 2 administrations), `gpt-4.1`, about
eight minutes and a couple of dollars each. Section 12 estimated ~80 calls; that was 20
personas ago, before section 24 widened the neutral pool.

### The result

| | temperature 0.2 | temperature 0 |
|---|---|---|
| FFNI | **USABLE** (mean retest .64) | **USABLE** (.65) |
| `leader_ideal` | **NOT USABLE** (mean retest **.35**, gate is > .40) | **USABLE** (**.47**) |

The failure was the opposite of the one section 12 was watching for. It was not that the
agents are too stable for a situation to move them; it is that they could not reproduce
their own answers at all. Alphas were fine throughout (.73 to .99, `strength` at .80 on
two items) and nobody straight-lined a 45-item battery. Coherent within a sitting,
unrepeatable across two.

### Why, and why temperature fixes only half of it

Test-retest tracks the ratio of between-person SD to the noise floor almost exactly:

| | between SD | noise SD | ratio | retest |
|---|---|---|---|---|
| affiliation | 1.36 | 0.63 | 2.15 | .90 |
| sensitivity | 1.06 | 0.70 | 1.52 | .83 |
| **protection** | 0.79 | 1.01 | **0.78** | **.21** |
| **strength** | 0.49 | 0.67 | **0.74** | **.23** |

So it is not that the agents share one stereotype of a leader and have no individual
variation — the between-person SDs are real. The noise is simply as large as the signal.
Two distinct causes, and they respond differently:

- **Ceiling compression** on `strength` (7.39), `dedication` (8.56), `ethics` (8.80) out
  of 10. Everyone agrees a leader is strong and dedicated, so little variance survives.
- **No stable view** on `masculinity`, `femininity`, `attractiveness`: large
  between-person SD, larger noise.

Dropping temperature to 0 nearly doubles the worst prototype scales — `strength`
.23 -> .46, `dedication` .27 -> .56, `intelligence` .18 -> .41 — and moves the FFNI
almost not at all (.64 -> .65). The battery that was reading noise was the 45-item one.

**The residual is not decoding randomness.** `discussion.py:391` re-randomises item order
for every administration, so at temperature 0 the two sittings are still different
prompts. What is left is order sensitivity, which is a property of the instrument on
these agents rather than a setting to turn off — and the FFNI was validated with randomly
presented items, so removing the shuffle would depart from the published protocol to
flatter the reliability.

### What did not improve, and it is the one that matters

`protection` went .21 -> .26 and its noise floor stayed at **1.01**. It is H6's mediator
and the dominance side of H4. `strength`, its only prototype outlet, reached .46.
The attenuation on that link is sqrt(.26 x .46) = **.35**: a true correlation of .5 would
be observed at about .18.

The one piece of luck is that 1.01 is almost exactly the `sd_induced = 1.0` section 24
assumed, so that power table stands as computed rather than needing a re-run: H3 and H6
at 84% and 67% for 40 runs, 94% and 88% for 60.

### Decisions

- `SURVEY_TEMPERATURE = 0`. Note that this closes the door on the `gpt-5` family as
  `SURVEY_MODEL` — TinyTroupe strips a non-default temperature for those models
  (`clients/openai_client.py:425`), and reasoning models reject the parameter outright.
- The two runs are kept side by side in `results/ffni_mediation/measure_check/`, the
  second suffixed `_t0`. **`save_summary` records neither model nor temperature**, so a
  summary cannot say what produced it; the suffix and this section are the only record.

### Open, and it is the same flaw section 23 fixed for alpha

The retest gate is a **mean over subscales**. `masculinity` sits at .01 and
`attractiveness` at .28 even at temperature 0, and they pass because `sensitivity` (.92)
and `ethics` (.76) carry the average — exactly how a dead `strength` used to pass the
alpha gate. It matters because `status`, the other dominance-side need, has its composite
averaged over `tyranny` (.68), `masculinity` (.01) and `attractiveness` (.28): two of its
three outlets are noise. Gating retest per read subscale would fail `leader_ideal` again.

---

## 26. Item order was the noise floor, and what that does to the sample size (2026-08-26)

Three `measure-check` runs, `gpt-4.1`, 144 calls each. The question was where the noise
that failed `leader_ideal` in section 25 was coming from.

### Temperature was a third of it; item order was the rest

| | mean test-retest | | | protection noise SD |
|---|---|---|---|---|
| temperature 0.2, order re-shuffled per administration | FFNI .64 / ILT **.35** | | | 1.01 |
| temperature 0, order re-shuffled | FFNI .65 / ILT .47 | | | 1.01 |
| temperature 0, **order fixed per respondent** | FFNI **.89** / ILT **.76** | | | **0.40** |

Every noise floor roughly halves in the third row. `protection` .21 -> .26 -> **.83**;
`strength` .23 -> .46 -> **.81**; `masculinity` -.04 -> .01 -> .63.

`_administer` drew a fresh item order on every call, so the same persona met a different
order at baseline and at post and the difference between them carried order sensitivity.
That difference is H3's dependent variable and H6's mediator. The order is now drawn from
a generator keyed on the instrument and the persona: items are still randomly presented,
orders still differ between people so position bias does not accumulate, and one
respondent sees one order throughout.

The first framing of this was wrong and is worth recording as such. Removing the shuffle
looked like departing from a published protocol to flatter a reliability number. The
protocol asks for randomly presented items; it does not ask for a respondent to be
re-randomised against themselves between two waves of the same measure.

### The gate's upper bound had to go

With order fixed and temperature at 0, two administrations with nothing in between are
the same prompt. Test-retest stops measuring whether an agent holds a stable position and
starts measuring whether the same prompt returns the same answer. The FFNI promptly
"failed" at .89 for being too stable, which is not a finding about the FFNI.

The bound was there to catch agents too frozen for a situation to move them (section 12).
That question cannot be asked by administering a scale twice with nothing happening
between; H3's path a asks it, on data where something did happen. The gate is now
one-sided: a scale that cannot reproduce itself under identical conditions is broken, and
a scale that can is doing its job. Both instruments pass.

### The power simulation was parameterised wrongly, and it flattered H6

`layer_power.py` had one `sd_induced` standing in for two different things: how far the
situation really moves different respondents, and what the instrument adds on top. They
pull opposite ways — the prototype and the vote follow the true change, while every
estimator sees only the observed one — so a single parameter made a *lower* noise floor
look like *lost* power. Split into `--sd-true` and `--sd-noise`, the second being
measure-check's delta SD.

With `sd_noise = 0.40` measured and `sd_true = 0.5` assumed:

| runs | H3 | H4 within | H5 false positive | H6 (b .10) | H6 (b .25) |
|---|---|---|---|---|---|
| 20 | 92% | 65% | **13%** | 20% | — |
| 40 | 100% | 94% | 2% | 31% | **95%** |
| 60 | 100% | 97% | 4% | 44% | 100% |

### The sample size decision, settled

**40 runs per condition. Not 60.**

- H3 is now saturated. Halving the noise floor took it from 84% to 100%, which is the
  clearest return on the ordering fix.
- H5's false-positive rate is 13% at 20 runs and nominal at 40. This remains the reason
  40 is a floor, and the reason is not power.
- H4 within-person sits at 94%.
- **H6 is a cliff, not a slope.** At a small path b it is 31% at 40 runs and still only
  44% at 60; at a medium one it is 95% at 40 and 100% at 60. The extra 50% of budget
  buys nothing at either end — it cannot rescue the small case and is not needed for the
  medium one. Section 24's reading, that 60 runs was worth considering for H6, was an
  artefact of the conflated parameter.

H6's fate is therefore decided by how strongly an induced need actually reaches a vote,
not by how much is spent. Worth stating plainly in the write-up rather than discovering
afterwards: **the links of the chain are each well powered and the product of them is
not.** H2 (p = .028, measured), H3 (100%) and H4 (94%) can each carry mechanism evidence
on their own; H6 asks one coefficient to claim the whole path at once.

If H6 comes back with an interval spanning zero, the levers in order of leverage are more
respondents per run rather than more runs — path b is a respondent-level regression and
the discussion is shared — then a second post administration averaged to lift the
mediator's reliability from .61 towards .76. Switching to a continuous outcome would work
and is refused: that outcome is H5's effectiveness rating, and section 18 separated them
on purpose.

---

## 27. Step 2 ran: the behavioural effect replicates, the proposed mediator does not carry it (2026-08-26)

40 runs per condition, `gpt-4.1`, `SURVEY_TEMPERATURE 0`, three rounds, cast of 5, every
fix from sections 13 through 26 in force. About six and a half hours and roughly $27.

### The behavioural layer

| test | result |
|---|---|
| H1 collaborative: P > D | **supported**, p = .017, P 1.65 vs D 0.90, P wins 25/40 |
| H2 threat: D > P | not supported, p = .105, D 1.57 vs P 1.10, D wins 23/40 |
| **Interaction** | **supported**, p = **.0076**, threat +0.47 against collaborative -0.75 |

H2 alone missing .05 is what section 4's power table predicts: the interaction is better
powered than either condition on its own, and it is the test that matches the claim.

### The mechanism layer

**H3 holds, and for exactly one need.** The induced-need difference for `protection` is
**+0.31, CI [0.12, 0.50]**. Every other need's interval contains zero, `status` included.
Threat moved the need the source paper names and nothing else.

**H4 does not hold, on either reading.** Within-person, `protection`'s beta is .05,
CI [-.09, .19]; between-person, -.07, CI [-.19, .05]. `status` reaches the dominance-side
prototype at -.16, CI [-.28, -.05] — significant and in the wrong direction.

**H5's dominance side is null**, replicating the paper: `protection` to Dominance
effectiveness is -.00, CI [-.14, .13].

**H6 finds no mediation:**

    path a     0.310     threat did raise the induced need
    path b    -0.006     which predicted nothing about the respondent's own vote
    indirect  -0.002     CI [-0.027, 0.024]

### The null has content

The interval is narrow in absolute terms. Dividing through by path a puts path b's
interval at roughly [-.09, .08], which excludes the `b_vote = 0.10` that section 26's
simulation called the *small* case — and the same simulation detects a medium path b 95%
of the time at this n. So this is not a study that failed to look; it is a study that
looked and can rule out anything but a very small effect.

    threat ─────────────────────────────────→ endorsement shifts to Dominance   (p = .008)
       └→ protection need rises (H3)  ──✗──→ the vote (H6)
                                      ──✗──→ the prototype (H4)

Both ends are causally connected and the proposed mediator does not carry the connection.
Sheng et al. assume this mediation and say plainly that it has never been tested
(pp. 45-46) — that assumption is the reason this study exists. It has now been tested on
data where the situation was manipulated rather than observed, the need was measured
within-person before and after, and the outcome was a behaviour rather than a rating. It
does not hold.

### What could still explain it away, in order of how much they worry me

- `protection`'s own reliability. Test-retest .83 after section 26's ordering fix, which
  is the best it has been, but the measurement is still the weakest link in the chain.
- The mediator is measured after the discussion, and the vote follows it. A need that
  moved *during* the discussion and moved back is invisible here.
- Path b is estimated within condition on 120 respondents clustered in 40 rooms. The
  bootstrap resamples rooms, so the interval is honest, but a room-level common cause
  would not show up as mediation either way.

### A tool that answered the wrong question

`tools/interaction_test.py` had `results/pd_matched/` hardcoded. Asked about Step 2 it
silently reported Step 1's calibration runs instead — a different design at n = 10 — with
nothing in its output naming the study. It takes the study as an argument now and prints
it. The first reading of Step 2's interaction in this session came from that bug.

---

## 28. The positive control failed on the dominance side, and that bounds what section 27 can claim (2026-08-26)

Section 27 reported H4 as null and moved on. H4 is not a hypothesis this study invented:
it is Sheng et al.'s **positive** result (Study 5, Sample B — protection to Strength at
delta R2 = .03**, status to Tyranny, Masculinity and Well-Groomed). Section 19 built the
prototype layer in explicitly to serve as H4's positive control. A failed positive
control is not a footnote; it is the thing that says how far the rest of the results
travel.

### The paper-comparable test, which section 27 did not run

The paper measured needs and prototypes cold, at one sitting, as levels. Section 27's H4
used post-discussion scores on both sides. Since section 24 added a baseline
administration of `leader_ideal`, the closer analogue was sitting in the same
checkpoints, unanalysed: baseline need against baseline prototype, before anything
happened. Run-level bootstrap, 600 draws, 240 respondents in 80 rooms.

| need | baseline beta | 95% CI | paper | |
|---|---|---|---|---|
| expertise | **+0.23** | [0.12, 0.34] | + | replicates |
| vision | **+0.13** | [0.03, 0.23] | + | replicates |
| status | -0.03 | [-0.14, 0.10] | + | null |
| **protection** | **-0.16** | [-0.29, -0.01] | + | **significantly reversed** |
| fairness | -0.20 | [-0.31, -0.11] | + | significantly reversed |

Three of five intervals clear zero, so this is not a scale returning noise. It is a
structured failure: **the prestige-side needs reproduce the paper's individual-difference
structure and the dominance-side needs do not.** The dominance side is what the study is
about.

### What this does to section 27

H6's null has to be stated at two different scopes, and only the first survives:

- **About this simulation**: the induced protection need does not predict these agents'
  endorsements. The interval is narrow and rules out anything but a very small effect.
  That claim stands.
- **About people**: much weaker than section 27 implied. These agents fail to reproduce
  an *established* protection-to-Strength association, and reproduce it backwards. An
  untested mediation coming back null in a population that cannot reproduce the tested
  association is thin evidence about the population the paper is describing.

Section 27's "the null has content" stands as written about the simulation and should not
be read as being about human followers. The behavioural result (interaction p = .0076) is
unaffected — it does not rest on the prototype layer.

### Which explanation, in order of weight

1. **These are LLM personas, not people.** A persona's needs and its leader prototype are
   both generated from one Big Five description, so the correlation between them is the
   model's own consistency logic rather than a human individual difference. There is no
   reason it should reproduce a human structure, and the honest reading is that where it
   does (expertise, vision) it may be coincidence as much as fidelity.
2. **The reconstruction is not the instrument they used** (section 19). Offermann,
   Kennedy & Wirtz (1994) via Bhatia et al. rather than Offermann & Coats (2018), and
   `strength` carries two items.
3. **Ceiling compression on the dominance-side dimensions.** `strength` averages 7.39 of
   10 with a between-person SD of 0.49. This one explains `protection` and not `fairness`,
   whose dimensions have good reliability (dedication .84, intelligence .70, ethics .80)
   and still come out significantly reversed.

### The general lesson, recorded because it will apply to the next study too

A simulated population can reproduce a behavioural effect (the interaction replicates
twice, at n = 10 and n = 40) while failing to reproduce the individual-difference
structure that a mechanism claim needs. Behaviour and covariance structure are separate
things to validate, and this design validated the first and assumed the second. Any
future mechanism study on LLM personas should treat a published positive association as a
gate to be passed before the untested one is interpreted, not as a control to be read
afterwards.

---

## 29. The control did not fail randomly: protection is a prestige-flavoured need here (2026-08-26)

Section 28 recorded H4's dominance side as a failed positive control and offered three
explanations, leading with "these are LLM personas, not people". That is right but vague,
and two of the three were checkable. Both check out clean, and what is left is specific
enough to state as a finding rather than a caveat.

### Not a scoring bug

The obvious candidate for a significant *reversal* is a reverse-worded item that nothing
reverses. There are none. All four `protection` items are positively worded ("I wish to
have a leader who positions themselves between my group and an outside threat"), and
`leader_ideal` is trait adjectives rated for how characteristic of a leader they are —
`strong`, `bold`, `domineering`. Neither instrument declares reverse-scored items and
neither needs to.

### Not isolated noise either

`protection` against each of the ten prototype dimensions separately, baseline, six-need
fit, 240 respondents:

| dimension | beta | | dimension | beta |
|---|---|---|---|---|
| **charisma** | **+0.21** | | **strength** | **-0.16** |
| **ethics** | **+0.17** | | masculinity | -0.07 |
| **dedication** | **+0.15** | | femininity | -0.06 |
| attractiveness | +0.12 | | tyranny | -0.05 |
| sensitivity | +0.04 | | intelligence | -0.02 |

The positive side is charisma, ethics and dedication; the negative side is strength,
masculinity and tyranny. Those are the prestige-side and dominance-side dimensions
respectively, and the split is clean. A broken measure returns noise, not a coherent
inversion along the theoretical axis.

### What it actually says

**In this simulated population, wanting to be protected is a prestige-flavoured need.**
An agent that scores high on protection wants a charismatic, ethical, dedicated leader —
not a strong or domineering one. Sheng et al.'s humans go the other way, which is what
puts `protection` on the dominance side of their dual-model account in the first place.

This is mechanically why H6 came back null, and it is a better explanation than
measurement error. The chain does not break in the middle: **it routes somewhere else.**
A mediator that connects to the prestige side cannot carry a condition effect onto
dominance endorsement no matter how well it is measured or how many runs are collected.

### Consequences

- H6's null should be reported as **conditional**: conditional on a population whose
  protection need sits on the prestige side. It is not evidence that human follower needs
  fail to mediate, and it is no longer merely "weak evidence" — it is evidence about a
  different nomological network.
- This is not fixable in code. The instruments are right, the scoring is right, the
  estimators are right. It is a property of the population.
- It is worth reporting in its own right. "LLM personas reproduce the behavioural effect
  but attach the mediating need to the opposite leadership strategy" is a finding about
  the validity of persona simulations for mechanism work, and it is more useful than the
  null it explains.

### If it is to be pursued

The neutrals' personas are generated from a Big Five description and an occupation and
nothing else, so whatever maps a personality profile onto a protection need here is the
model's own prior. Testing whether that is the cause means generating neutrals some other
way — richer biographies, explicit threat histories, or personas sampled to vary on
security concerns directly — and re-measuring the baseline association before running any
meeting at all. That is a study, not a fix, and it is cheap: the association is measured
before any discussion happens, so it costs two survey calls per persona.

---

## 30. Hunting the real instruments: what is obtainable and what is not (2026-09-02)

Two of this study's three instruments are not the ones the source paper used. This
section records what was found looking for the originals, so the next attempt does not
repeat the search. **Nothing was changed** — `leader_ideal.json` and
`effectiveness.json` are untouched.

### The ILT: not obtainable

Sheng et al. used Offermann & Coats (2018), 51 items (their 46-item nine-factor scale
plus the femininity and ethics items Sheng et al. added, per their footnote 13).

| route | outcome |
|---|---|
| ScienceDirect (`S1048984317304988`) | paywalled |
| academia.edu, ResearchGate | HTTP 403, login wall |
| Sheng et al.'s own Appendix (p.801) | an **overview table of measures only** — names, item counts and sources, no items |
| Sheng et al.'s data statement (p.775) | "All data, analysis code, and survey materials are available upon request from the author team" — not deposited |
| the preregistration (`aspredicted.org/vt3x-j9vb`) | HTTP 403 |
| Bhatia et al. (2022) Appendix A | **the 1994 version**, which is what section 19 already reconstructed from |

Bhatia et al.'s Appendix A was re-read and confirmed verbatim: Sensitivity (8),
Dedication (4), Tyranny (10), Charisma (5), Attractiveness (4), Masculinity (2),
Intelligence (5), Strength (2) — **40 traits, eight factors**, matching section 19's
note that the appendix lists 40 where the body text says 41. Our `leader_ideal.json`
is exactly this plus femininity (2) and ethics (3) = 45.

**One unverified lead, recorded as a lead and not as a fact.** A search-engine summary
of the 2018 abstract and citing works described the nine-factor structure as including
**Strength = forceful, bold, powerful, strong** — four items rather than 1994's two.
If true it matters a great deal: section 29 traced H4's entire reversal to `bold`
(protection to `strong` is −0.02, to `bold` is −0.29), and three more items would
dilute exactly that. **This came from a generated summary, not from the article, and
must not be used until the article itself is read.** The obvious route is institutional
access to *The Leadership Quarterly* 29(4), 513–522.

### The effectiveness criterion: the criterion is fine, the reliability is not

**Corrected 2026-09-07.** The paragraph below originally read "our version is not an
instrument at all" and treated a 57-items-to-1 gap as the finding. That was wrong about
what the paper measures. The paper's effectiveness measure **is one question and one
1-7 scale**:

> "Please answer to what extent you perceive these leadership descriptions as effective
> if these individuals were your own leaders… (1 = not at all effective as a leader,
> 7 = extremely effective as a leader)" — p.785

Its 57 items are the **stimuli**, not the criterion: twelve published leadership-style
scales reworded as descriptions of hypothetical leaders, with each style's 4-6
descriptions averaged into one effectiveness score. Applying the same question and scale
to a different stimulus — an agent the respondent just watched — is using their measure,
not inventing one. `effectiveness.json` now carries their question and anchors verbatim.

What the substitution really costs is **reliability**. A style score built from 4-6
ratings has an alpha; one rating of one person does not, and `measure-check` cannot
produce one for this instrument. That is not fixable by adding paraphrased items: the
paper's multiple items are different stimuli for one style, and paraphrases would
measure agreement between rewordings rather than between observations.

The second cost stands as recorded below: their dominance-side null is specific to
Authoritarianism, Narcissism and Dominance as separate scales, while
`protection → Safety` is .43***/.20***, and one rating cannot separate them.

### What the paper actually administered

Sheng et al.'s Appendix (p.801) lists "Leadership Effectiveness" as **twelve published
scales, 57 items**:

| construct | items | source |
|---|---|---|
| Authoritarianism | 5 | B.-S. Cheng et al. (2004, 2014) |
| Benevolence | 5 | B.-S. Cheng et al. (2004, 2014) |
| Moral Character | 6 | B.-S. Cheng et al. (2004, 2014) |
| Team-Building | 5 | X.-H. Wang & Howell (2010) |
| Vision Communication | 4 | X.-H. Wang & Howell (2010) |
| High-Expectation | 5 | X.-H. Wang & Howell (2010) |
| Intellectual Stimulation | 4 | X.-H. Wang & Howell (2010) |
| Dominance | 4 | Bai et al. (2020) |
| Competence | 4 | Bai et al. (2020) |
| Virtue | 6 | Bai et al. (2020) |
| Safety | 3 | X. W. Hu et al. (2025) |
| Narcissism | 6 | Back et al. (2013) |

Ours applies their question to **one stimulus, rated once**. The paper's dominance side
is three separate scales (Authoritarianism, Dominance, Narcissism) and its null is
specific to them, while `protection → Safety` is **.43\*\*\*/.20\*\*\*** — strongly
supported. A single rating cannot separate "wants protection" from "rates an
authoritarian effective", so what we replicated is a null about a construct we collapsed.

**Found so far**, verbatim, from Leckelt et al.'s NARQ-S validation:

    Narcissism — Back et al. (2013), NARQ-S, 6 items, 1 (do not agree at all) to 6 (completely agree)
      1. I react annoyed if another person steals the show from me.   [Rivalry]
      2. I deserve to be seen as a great personality.                 [Admiration]
      3. I want my rivals to fail.                                    [Rivalry]
      4. Being a very special person gives me a lot of strength.      [Admiration]
      5. I manage to be the center of attention with my outstanding
         contributions.                                               [Admiration]
      6. Most people are somehow losers.                              [Rivalry]

**Not yet found**: Bai et al.'s Status Attainment Scale (15 items covering
virtue–admiration, dominance–fear, competence–respect) — the article's body gives
example items only and points to supplementary materials; Cheng et al.'s paternalistic
leadership scale; Wang & Howell's transformational scales; Hu et al.'s safety scale.

**A rewording problem that applies to all twelve.** These are self-report or
other-report trait scales in the first person ("I want my rivals to fail"). Sheng et al.
administered them as **descriptions of hypothetical leaders** to be rated for
effectiveness — "We will now present approximately 50 leadership descriptions… indicate
your perceptions of its effectiveness". Any replacement instrument here has to make the
same transformation, and our design adds a further one: the target is a specific agent
the respondent just watched, not a description. That is the study's intended
contribution (section 2 of the study note), but it means even a faithful item set is
not administered the way the paper administered it.

### To replace, when the instruments are in hand

1. **`effectiveness.json`** — highest value and lowest risk. The dominance side needs at
   minimum Authoritarianism (5), Dominance (4) and Narcissism (6); the prestige side
   Competence (4), Benevolence (5) and Intellectual Stimulation (4). That is 28 items
   against the current 1. Cost: item count does not change call count — `_administer`
   sends a whole battery per call — so this is output tokens only, and it would let H5
   be reported per construct instead of collapsed.
2. **`leader_ideal.json`** — replace the 1994 reconstruction with the 2018 items,
   which also settles whether `strength` has two items or four and therefore whether
   section 29's diagnosis survives.
3. Re-run `measure-check` after either change. Both gates are per-subscale now, so a
   weak new subscale will be caught before a study is paid for.

---

## 31. Defect register: everything found wrong on 2026-09-07

An audit of `docs/technical-report-2026-08-26.md` against the code, the saved results and
the two source articles, plus three things found while getting the instruments. Recorded
in full before any of it is fixed, so the fixes can be checked off and nothing is quietly
dropped. Severity is about how far a reader would be misled, not how hard it is to fix.

### A. Claims that are wrong

**A1 — H6's null does not rule out a small effect. SEVERE.**
Reported in technical report §6.6 and §11.1, design log §27 and §28, and the weekly
report's "The null that has content" slide: dividing the indirect CI by `a = 0.31` gives
`b ∈ [−0.087, +0.078]`, said to exclude the simulation's small case `b_vote = 0.10`.
Two errors compound.

- The simulation's `b_vote` multiplies the **true** induced change
  (`tools/layer_power.py`: `P(vote) = 0.5 + b_vote × induced`, pre-noise), while the
  estimator regresses the observed change. Running the simulator's own generator at
  `b_vote = 0.10` yields an observed path b of **+0.023** — comfortably inside the
  interval. At `b_vote = 0.25` it yields **+0.142**, which is outside.
- Dividing by `a` treats `a` as known. Its own CI is [0.125, 0.496]; at the lower bound
  the implied interval is [−0.216, +0.193], which contains even the medium case.

Correct statement: **the interval excludes a medium path b and does not exclude a small
one.** H6's null is informative about medium mediation only.

**A2 — "every paper-supported positive effect failed to replicate" is false. SEVERE.**
Technical report §11.1. `affiliation → prestige-side effectiveness` is **+0.151,
CI [+0.013, +0.303]**, excluding zero, and `→ dominance-side` is −0.190 [−0.318, −0.070].
The paper's two largest supported links are Affiliation → Benevolence .31\*\*\* and
→ Team-building .46\*\*\* (Table 3, Model 2). A paper-supported positive prediction
replicated in the right direction on both sides. The sentence is the one that bounds
every downstream inference, so its being a false universal matters more than its size.

**A3 — "the paper measured needs cross-sectionally, once" is false. MODERATE.**
Technical report §1's contrast table. Sample E administered the FFNI at two time points
a week apart (p.775: "E in two time points"; Table 5 prints T1 and T2 columns; Table 8
reports both). The real contribution — pre/post around a *manipulated* event inside one
session — stands, but as written the table understates the paper.

**A4 — §6.7's decomposition does not close arithmetically. MODERATE.**
Reported: cognition −0.305, evaluation +0.178, total gap difference −0.467. But
−0.305 − 0.178 = −0.483. Recomputed deterministically from the checkpoints: cognition
collab +0.052, threat −0.251 → −0.303; evaluation collab −0.078, threat +0.086 → +0.164;
−0.303 − 0.164 = −0.467, matching the saved summary. The two reported components came
from bootstrap means rather than point estimates. The conclusion survives; the numbers
do not.

**A5 — "the 2018 instrument is unavailable here" is now false. MODERATE.**
Technical report §4.1 and §11.5. `docs/1-s2.0-S1048984317304988-main.pdf` is in the repo
and its Figure 2 prints all 46 items with factor assignments.

**A6 — the ILT reconstruction is described too kindly. MODERATE.**
§4.1 says "41 traits, reproduced verbatim". `leader_ideal.json` holds **40**, and its own
note says no wording was ever checked against the original. Item-by-item against the
instrument the paper used, **17 of the 45 administered traits do not appear in it at
all**, and of the 28 shared, three sit on different factors: `bold` → charisma,
`attractive` → masculinity, `clever` → creativity.

**A7 — §6.5 enumerates 11 criteria where there are 12 scales. MINOR-MODERATE.**
The omitted one is **Safety**, which is the criterion where protection is strongly
supported (.43\*\*\*/.20\*\*\*) and therefore the one that makes the collapsing problem
concrete. Table 3 has 13 rows because Authoritarianism appears twice.

**A8 — §5.4's reason for using Welch contradicts §2.2. LOW-MODERATE.**
§5.4 says the two conditions' runs "have no pairing relationship"; §2.2 says run *i*
draws the same cast in both, and the checkpoints confirm it for 40/40 runs. Welch is
still defensible as the conservative choice, but not for the reason given.

**A9 — §2.1 misdescribes the pairing assertion. LOW.**
Cited as `pair_bank.py:150-158`; it is at 163-171. It compares *sorted multisets* of
OCEAN traits, occupation and age group between the P and D groups, so a permutation of
which bank row feeds which D index would pass it. Index-wise pairing is guaranteed by the
construction loop, not by the check.

**A10 — provenance strings that do not resolve. LOW, but they are citations.**
`ffni.json`'s licence says the items come from "Table 4"; in the published article they
are **Table 5, p.779** (Table 4 is the study/sample overview). Technical report L22 cites
the mediation quote to "p.45-46", which under its own page convention does not exist —
it is **p.795**, correctly cited later in §6. And the CC BY-NC-ND 4.0 licence asserted in
`ffni.json` and repeated as fact in §4.1 **appears nowhere in the article**, every page
of which carries APA's "All rights reserved"; it is to be marked unverified rather than
removed, since the preprint may carry it.

**A11 — small factual slips. LOW.**
"the paper's headline increments are .02-.06" — Table 13's significant increments run
.01-.06. The Table 8 range quoted as .21-.87 mixes two triangles and two samples; the
full table reaches .08. "(attractiveness = the 1994 name for well-groomed)" inverts the
direction: *attractiveness* is 1994, *well-groomed* is the 2018 rename. §5.7's interval
formula uses a ceiling for the upper order statistic where the code uses a floor. §5.7
quotes "12% → 14%" for clustering, but that row was measured on the *uncentred*
estimator, where 12% is the condition confound rather than a clustering floor.

**A12 — the report's own reproducibility claim is not strictly true. LOW.**
The header says every number can be reproduced at commit `0067e63`. §11.7's exploratory
behavioural mediation reproduces exactly, but no script in the repo computes it and §12
lists no command for it.

### B. Omissions

**B1 — the independent variable has never been checked. MODERATE-HIGH.**
No study administers a manipulation check of the P/D styles. `pd_matched` has
`"instruments": []`; `ffni_mediation` carries only ffni, leader_ideal and effectiveness.
The style blocks in `tools/sample_bank.py` are written for this project and carry no
citation — correctly, the report never claims one — but no measure has ever asked whether
neutrals perceive D as dominant or P as prestigious. The only evidence the manipulation
bites is behavioural: the claim-rate contrast (D 0.17-0.25, P 0.00). §11 enumerates seven
validity threats and does not include this one.

**B2 — §13's threat-check evidence predates the deadline fix. LOW.**
It was collected on `pd_matched` under the pre-fix collaborative wording, which had no
48-hour deadline. §13 argues the evidence still transfers; the technical report cites the
deadline fix without noting that the manipulation evidence sits on the other side of it.

### C. Errors in this log

**C1 — §30 called the effectiveness measure "not an instrument at all".** Corrected in
commit `ea0ed3c`: the paper's criterion *is* one question and a 1-7 scale, its 57 items
are stimuli.

**C2 — "no reliability can be computed for a single-item rating" is wrong. MODERATE.**
Stated in §30 as corrected and in `effectiveness.json`'s note. Cronbach's alpha indeed
cannot be computed, but **inter-rater reliability can**: three neutrals rate the same
target's same performance in every run, giving 160 (run x target) cells of three ratings.
Computed: **ICC(1,1) = 0.723, ICC(1,3) = 0.887** over 480 ratings, MSB 2.021 / MSW 0.229.
For a measure of an observed person that is the more appropriate coefficient than alpha —
alpha asks whether rewordings agree, ICC asks whether observers of one performance agree.
The claim that this "is not fixable by adding items" was answering the wrong question.

**C3 — §28 and §29's explanation ranking for H4 is superseded.** Both rank causes for the
failed positive control without knowing that `bold` is a *charisma* item in the
instrument the paper used. The framing "the reconstruction has too few items to dilute
one word's semantics" is wrong: the word does not belong to that factor at all.

**C4 — §30's "unverified lead" about the 2018 Strength items was wrong.** It recorded a
search summary claiming `forceful, bold, powerful, strong`. Figure 2 gives
`commanding, assertive, authoritative, tough, strong, firm` — six items, and `bold` is
not among them. Recorded as a lead rather than a fact, which is why it did no damage.

### D. Code gaps

**D1 — no inter-rater reliability anywhere in the pipeline.** `summarize_measure_check`
computes subscale differentiation, straight-lining, alpha and test-retest.
`about: each_candidate` instruments get none of these, and the ICC in C2 was computed by
hand. Nothing in `run.py report` or `run.py layers` reports it, so the one reliability
figure this study's evaluation layer *can* produce is absent from every report.

**D2 — `save_summary` records neither model nor temperature**, already noted in the
technical report §12. Three `measure-check` runs are distinguishable only by a filename
suffix added by hand.

### Fix order

A1 and A2 first: they are what a reader takes away. Then C2 and D1 together, since the
correction needs the number to exist in the pipeline. Then A3-A7 and B1, which are
report-level. Then A8-A12, C3, C4 and D2.
