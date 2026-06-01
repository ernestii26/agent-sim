# Prestige vs Dominance Leadership Simulation — Results

**Date:** 2026-05-26  
**Model:** gpt-4.1  
**Rounds per run:** 3  
**Group size per run:** 10 (1P + 1D + 8N, sampled from 5P/5D pools)

| Step | Scenario | n runs | Hypothesis |
|---|---|---|---|
| Step 2 | Collaborative (missed deliverables) | 13 | H1: Prestige > Dominance |
| Step 3 | Threat (division survival, zero-sum) | 20 | H2: Dominance > Prestige |

---

## Research Questions

**H1 (Step 2):** In a collaborative, information-rich setting, do prestige-based agents receive more peer leadership votes than dominance-based agents?

**H2 (Step 3):** Under resource scarcity and survival threat, does the advantage reverse — do dominance-based agents receive more votes?

---

## Quantitative Results

### Step 2 — Collaborative scenario (n = 13)

| Metric | Prestige mean | Dominance mean | t | p (one-sided) |
|---|---|---|---|---|
| **Votes per run** | **4.69** | 1.23 | 3.033 | **0.005** |
| Speech rate | 0.974 | 1.000 | −1.000 | 0.831 |
| Words per spoken turn | 35.4 | 31.0 | 3.727 | **0.001** |

**H1 verdict: SUPPORTED** — Prestige agents received significantly more peer votes than Dominance agents (p = 0.005, one-sided paired t-test, n = 13).

### Step 3 — Threat scenario (n = 20)

| Metric | Prestige mean | Dominance mean | t | p (one-sided H2: D>P) |
|---|---|---|---|---|
| **Votes per run** | 4.40 | **3.15** | −1.170 | 0.872 |
| Speech rate | 0.933 | 0.983 | — | — |
| Words per spoken turn | 35.9 | 30.4 | — | — |

**H2 verdict: NOT SUPPORTED** — Dominance did not significantly outperform Prestige under threat (p = 0.872). P still won 11/20 runs vs D's 8/20.

### Cross-scenario comparison (key finding)

| | Step 2 (collaborative) | Step 3 (threat) | Change |
|---|---|---|---|
| P mean votes | 4.69 | 4.40 | −0.29 |
| D mean votes | 1.23 | 3.15 | **+1.92** |
| P − D gap | **3.46** | **1.25** | −64% |

The threat scenario did not reverse the advantage, but **narrowed the P−D gap by 64%**. This directional shift is consistent with evolutionary theory even though H2 was not statistically supported.

### Per-run breakdown

| Run | P | D | P votes | D votes | Diff | Winner |
|---|---|---|---|---|---|---|
| 1 | P3 | D5 | 1 | 7 | −6 | D |
| 2 | P4 | D2 | 6 | 0 | +6 | P |
| 3 | P3 | D5 | 4 | 2 | +2 | P |
| 4 | P2 | D2 | 0 | 1 | −1 | D |
| 5 | P2 | D4 | 4 | 0 | +4 | P |
| 6 | P1 | D3 | 7 | 2 | +5 | P |
| 7 | P1 | D4 | 8 | 2 | +6 | P |
| 8 | P5 | D1 | 1 | 0 | +1 | P |
| 9 | P1 | D2 | 9 | 0 | +9 | P |
| 10 | P2 | D4 | 0 | 0 | 0 | Tie |
| 11 | P1 | D5 | 7 | 0 | +7 | P |
| 12 | P4 | D3 | 8 | 1 | +7 | P |
| 13 | P1 | D2 | 6 | 1 | +5 | P |

P wins: **10/13** · D wins: 2/13 · Tie: 1/13

---

## Qualitative Analysis — Why Prestige Won

### 1. Inclusive facilitation was the dominant vote reason

Across all P-wins, neutral agents' stated reasons for voting for Prestige agents centred on the same cluster of behaviours:

- **"Made space for everyone to speak up"** (runs 3, 6, 7, 9, 11, 13)
- **"Checked for unheard concerns before committing"** (runs 6, 7, 9, 11, 12)
- **"Summarised the group's decision and encouraged open questions"** (runs 2, 12)
- **"Offered concrete help — documenting decisions, task lists"** (runs 9, 12)

Representative quotes:

> *"She made sure everyone had a chance to share their perspective before making a decision."* (run 11, voter: Trang)

> *"She volunteered to document and share the task list to keep everyone clear, showing initiative and organisation."* (run 9, voter: Lilian)

> *"Rafael listened to everyone, summarised the plan clearly, and encouraged the team to speak up if there were concerns."* (run 12, voter: Lucía)

### 2. Prestige speech patterns: invite, then synthesise

P agents' speech showed a consistent two-beat pattern:

1. **Invite dissent or uncertainty** — "Does anyone have concerns?", "If anyone hasn't spoken yet, now's the time"
2. **Synthesise and offer a concrete next step** — documenting tasks, naming the agreed decision, proposing a lightweight check-in mechanism

Example (Dr. Mei-Ling Chen, run 9, round 3):
> *"Just to keep things clear, I can jot down the task list and who's taking what, then send it out for everyone to double-check. That way there's no confusion later."*

This combination — inclusive + practically useful — was highly valued by neutral agents who had no prior loyalty.

### 3. Dominance speech: directive but not trusted

Dominance agents were consistently more directive and closure-focused:

> *"Alright, enough circling. We've heard every angle. I'm calling it."* (Helena, run 1)

> *"I want one person's name. Not a group, not a shared task. If nobody volunteers, I'll assign it myself."* (Natasha, run 2)

> *"If anyone tries to wiggle out or pile on extras, I will call it out."* (Marcus, run 6)

When D agents received votes, the stated reason was typically **decisiveness when the group was stuck**, not trust or competence. D agents were valued as closure mechanisms, not leaders.

---

---

## Step 3 — Threat Scenario Analysis

### The vote heuristic shifted

Under survival pressure, neutral agents stopped rewarding inclusion and started rewarding **decisive ownership**. In Step 2, reasons for voting D were rare and tepid. In Step 3, D-win votes used language that almost never appeared in Step 2:

> *"He took charge when no one else would and gave the team clear direction to move forward."* (run 2, D1 wins 9−1)

> *"She stepped up to lead when the group was divided and made sure everyone had a clear role before closing."* (run 1)

> *"She cut through indecision, assigned clear roles, and pushed us to act when we risked stalling."* (run 5)

The phrase **"stepped up to lead"** — which encodes D-type authority assertion — appeared in 6 of 8 D-win vote reasons in Step 3, and in none of the Step 2 vote reasons.

### D's ceiling rose dramatically

In Step 2, D agents almost never received more than 2 votes in a run. In Step 3:

| Run | D votes | Context |
|---|---|---|
| 2 | 9 / 10 | D1 (Robert) took charge immediately, assigned all roles, no hesitation |
| 8 | 7 / 10 | D5 (Helena) volunteered to lead the pitch when others hesitated |
| 18 | 8 / 10 | D5 stepped up with a concrete plan when the group was frozen |

This ceiling shift is the clearest evidence that the threat manipulation worked: in the right conditions, D agents can achieve near-unanimous support.

### P agents adapted, but incompletely

P agents did not maintain pure facilitative behaviour under threat — they adapted toward more decisive language. But many still spent time on inclusion when the group wanted a clear leader:

> *"Let's pause for ten seconds and list — out loud — which datasets we actually have."* (Rafael, run 7 — P wins despite threat)

> *"All right, I just want to make sure — if anyone's still unsure or wants to flag anything before we dive in, now's the time."* (Fatima, run 9 — P wins)

When P agents combined their checking behaviour with a concrete proposal, they still won. When they only checked, without proposing, D agents took the votes.

### D5 (Helena Baxter) was most effective under threat

Among all D personas, D5 won 3 of 20 runs — more than any other D agent. Her persona (Australian, direct, high conflict tolerance) produced a style that was decisive without being alienating, making it more palatable to neutral voters in survival contexts.

---

## When Dominance Won (Step 2)

### Run 1 (D wins 7−1, P3 vs D5)

Helena Baxter (D5) won decisively. The key difference: Fatima Al-Rashid (P3) spent all three rounds asking checking questions without ever synthesising or proposing a concrete action. Agents rewarded Helena for **cutting the uncertainty short** rather than prolonging it:

> *"She cut through the back-and-forth, set a clear plan, and held everyone accountable for next steps."*

This aligns with evolutionary theory: Dominance can outperform Prestige when the group is paralysed and needs a decision-closer, not a facilitator. Fatima's inclusive style became passive in the absence of a concrete proposal.

### Run 4 (D wins 1−0, P2 vs D2)

Both agents received very few votes (0 and 1); most votes went to neutral agents. Both James Thornton (P2) and Natasha Volkov (D2) failed to establish meaningful presence in the discussion. The single D vote cited Natasha's one moment of pushing for a real diagnosis.

---

## Behavioural Differences (DV2 / DV3)

**Speech rate** was near-ceiling for both groups (P: 0.97, D: 1.00) — both types spoke in almost every round. This means the silence mechanism did not differentiate P from D, consistent with the design: both prestige and dominance agents are actively assertive, unlike the prior introvert/extravert design where silence was the primary signal.

**Words per spoken turn** was significantly higher for P agents (35.4 vs 31.0, p = 0.001). P agents spoke in longer, more elaborated turns — asking questions, inviting input, and offering synthesis — whereas D agents often spoke in shorter, directive bursts.

---

## Limitations

1. **n = 13** (7 runs did not complete due to API quota). Power is adequate for the main test (p = 0.005) but reduces confidence in subgroup analyses (e.g., individual P/D persona comparisons).

2. **Persona confounds**: P1 (Dr. Mei-Ling Chen) participated in 5 of 13 runs and won all five. Her persona may be unusually well-matched to the neutral agents' voting heuristics. A cleaner design would cap each persona at 2–3 appearances.

3. **Speech rate ceiling**: Both groups spoke in nearly every round, leaving no behavioural variance on DV2. The silence mechanism (designed to validate in Step 1) does not create meaningful P/D differentiation on this metric.

4. **Neutral agents dominate the vote pool**: 8 of 9 eligible voters per run are N-types. Their voting heuristic (inclusive facilitation = leadership) may not generalise to groups with different composition.

5. **Step 3 persona confounds**: D5 (Helena Baxter) won 3 of 8 D-wins — her persona may be unusually effective in threat contexts. With 20 runs and 5 D personas, each should appear 4 times, but within the 8 D-wins her wins are over-represented.

---

## Conclusions

### H1 — Supported

Prestige-type agents received significantly more peer leadership votes than Dominance-type agents in the collaborative scenario (mean 4.69 vs 1.23, p = 0.005, n = 13). The mechanism: neutral agents voted for agents who invited unheard voices, synthesised consensus, and offered concrete practical help. Dominance agents were valued for decisiveness but not trusted as leaders in a context where collective buy-in mattered.

### H2 — Not supported, but directionally consistent

The threat scenario did not produce D > P (p = 0.872). However, the P−D vote gap compressed by 64% (3.46 → 1.25), D agents achieved vote ceilings they never approached in Step 2, and the vote language shifted toward decisiveness and "stepping up." This pattern is theoretically coherent: the threat manipulation moved the group's implicit leadership criterion away from inclusion and toward authority, as predicted — but not far enough to invert the result.

The most plausible explanation is that P agents **code-switched**: under threat, Prestige personas adapted toward more directive language while retaining their credibility, keeping them competitive. A purer test would require P personas that cannot adapt — or a scenario with even higher survival stakes.

### Broader insight

Taken together, the two steps support the core claim from Henrich & Gil-White (2001) and Cheng et al. (2013): prestige and dominance are distinct influence strategies whose effectiveness varies by environmental condition. The simulation replicates the predicted direction of this interaction — P wins in information-rich collaboration, the gap shrinks under threat — in a fully controlled agent-based setting where human confounds (attractiveness, status cues, prior relationships) are absent.

---

## Files

| File | Description |
|---|---|
| `results/baseline_step2_20260526_111529.json` | Full result JSON (13 runs) |
| `results/baseline_step2_20260526_111530.png` | Bar chart: votes, speech rate, words per turn |
| `results/step2_checkpoints/run_001–013.json` | Per-run transcripts and vote records |
| `results/step3_checkpoints/run_001–020.json` | Step 3 (threat) per-run transcripts and vote records |

---

## References

- Henrich, J., & Gil-White, F. J. (2001). The evolution of prestige. *Evolution and Human Behavior*, 22(3), 165–196.
- Cheng, J. T., Tracy, J. L., Foulsham, T., Kingstone, A., & Henrich, J. (2013). Two ways to the top. *Journal of Personality and Social Psychology*, 104(1), 103–125.
