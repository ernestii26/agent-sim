# Prestige vs Dominance Leadership Simulation

A multi-agent simulation study using [TinyTroupe](https://github.com/microsoft/TinyTroupe) + GPT-4.1 to investigate whether **prestige-based** and **dominance-based** leadership styles produce different peer-vote outcomes in group decision-making.

## Research Question

> In a group discussion where agents must reach a shared decision, do prestige-type agents (who earn influence through expertise and knowledge-sharing) receive more leadership votes than dominance-type agents (who claim influence through authority and agenda control)?

This design follows evolutionary psychology research on two evolutionarily distinct paths to social rank (Henrich & Gil-White, 2001; Cheng et al., 2013). Unlike extraversion-based studies, the prestige/dominance split is theoretically predicted to interact with environmental conditions — making it a richer target for simulation.

---

## Design

### Two-step pipeline

| Step | Purpose | Runs | Rounds |
|---|---|---|---|
| Step 1 | Validate the silence mechanism — confirm that the optional-speech design produces meaningful variation across personas | 5 | 5 |
| Step 2 | Main hypothesis test — compare peer votes between Prestige and Dominance groups | 20 | 3 |

### Personas

13 agents total, generated via GPT-4.1 using Big Five + cultural modifier profiles:

**Prestige pool (5) — tightly specified seeds:**

| ID | Name | Nationality |
|---|---|---|
| P1 | Dr. Mei-Ling Chen | Taiwanese-American |
| P2 | James Thornton | British |
| P3 | Fatima Al-Rashid | Jordanian |
| P4 | Rafael Carvalho | Brazilian |
| P5 | Anna Kovačević | Croatian |

**Dominance pool (5) — tightly specified seeds:**

| ID | Name | Nationality |
|---|---|---|
| D1 | Robert Hartmann | German |
| D2 | Natasha Volkov | Russian |
| D3 | Marcus Webb | American |
| D4 | Park Jae-Won | South Korean |
| D5 | Helena Baxter | Australian |

**Neutral group (8) — demographics only, LLM generates freely:**

N1–N8: diverse professionals (Southeast Asian, European, African, Indian, Latin American, Chinese, French/Spanish, American) generated with minimal constraints. They participate in discussions without seeking to lead.

**Per-run sampling:** each run randomly draws 1P from {P1–P5} and 1D from {D1–D5}, plus all 8N agents, for a 10-person group. Over 20 runs, different P/D combinations are tested, making the result generalizable to the prestige/dominance construct rather than any specific individual.

Each P/D persona has a full psychological profile: Big Five scores, five cultural modifiers (collectivism, hierarchy preference, shame sensitivity, conflict tolerance, uncertainty avoidance), behavioral traits, communication style, and speech examples that anchor the agent's spoken register. N personas are generated freely within the neutral constraint.

### Hypothesis (Step 2)

**H1:** Prestige-type agents receive more peer votes than Dominance-type agents.

### DVs

| Variable | Measure | Notes |
|---|---|---|
| DV1 (primary) | Peer votes per run (Prestige vs Dominance) | Main leadership emergence metric |
| DV2 (behavioral) | Speech rate per run | Validates that behavioral patterns differ |
| DV3 (behavioral) | Words per spoken turn | Secondary behavioral check |

### Statistics

20 paired observations (one per run):

```
Per run → P_votes = sum(votes for 5 Prestige agents)
          D_votes = sum(votes for 5 Dominance agents)
→ 20 pairs → one-sided paired t-test (H1: P > D)
```

---

## Setup

### Requirements

- Python 3.10+
- conda environment: `social-sim`
- TinyTroupe 0.7.0
- OpenAI API key with access to `gpt-4.1`

### Install

```bash
conda activate social-sim
pip install tinytroupe openai scipy matplotlib
```

### Config

Copy the template and add your API key:

```bash
cp config.ini.example config.ini   # if it exists, otherwise edit config.ini directly
```

`config.ini` is gitignored — never commit it. Key settings:

```ini
[OpenAI]
API_KEY = sk-...

[Baseline]
DISCUSSION_MODEL      = gpt-4.1
STEP1_RUNS            = 5
STEP1_ROUNDS          = 5
STEP2_RUNS            = 20
STEP2_ROUNDS          = 3
```

---

## Usage

### Step 0 — Generate personas (run once)

```bash
python3 gen_personas.py
```

Calls GPT-4.1 to generate 10 persona JSON files in `personas/`. Already-existing files are skipped, so re-running is safe. Takes ~5 minutes.

### Step 1 — Validate silence mechanism

```bash
python3 run.py --step1
```

Checks whether the optional-speech design produces meaningful speech rate variation. Passes if:

1. Prestige mean speech rate − Dominance mean ≥ 0.10
2. At least 3 Dominance agents have speech rate < 0.70
3. At least 3 Prestige agents have speech rate > 0.50

If Step 1 fails, the silence mechanism is not working and Step 2 results should be interpreted with caution.

### Step 2 — Main experiment

```bash
python3 run.py --step2
```

Runs 20 full discussions + post-vote rounds. Outputs:

- Console report with t-test results
- `results/baseline_step2_<timestamp>.json`
- `results/baseline_step2_<timestamp>.png`

Checkpoints are written after each run — interrupted runs can be resumed without restarting.

---

## Project Structure

```
mbti_baseline/
├── run.py                  ← CLI entry point (--step1 / --step2)
├── gen_personas.py         ← Persona generator (calls GPT-4.1)
├── config.ini              ← API key + settings (gitignored)
├── plan.md                 ← Research design notes
├── src/
│   ├── runtime.py          ← TinyTroupe utilities + file logging
│   ├── persona_store.py    ← load_personas(), PRESTIGE_TYPES, DOMINANCE_TYPES
│   ├── discussion.py       ← run_discussion() + run_vote()
│   ├── pipeline.py         ← step1_validate_silence() + step2_run_simulation()
│   └── reporting.py        ← Statistics, console reports, bar charts
├── personas/
│   ├── manifest.json       ← Generated by gen_personas.py
│   ├── P1.agent.json … P5.agent.json   ← Prestige personas
│   └── D1.agent.json … D5.agent.json   ← Dominance personas
└── results/
    ├── step1_checkpoints/  ← Per-run JSON (gitignored)
    ├── step2_checkpoints/  ← Per-run JSON (gitignored)
    ├── logs/               ← info_*.log + warnings_*.log (gitignored)
    ├── baseline_step1_*.json   ← Final Step 1 summary (kept)
    └── baseline_step2_*.json   ← Final Step 2 summary (kept)
```

---

## Design Notes

### Why Prestige vs Dominance?

The extraversion/introversion axis (the original design) produces results that are too predictable — E-types speak more, therefore get more votes. The Prestige/Dominance axis is more interesting because:

- Both types are behaviorally active and assertive in different ways
- Human research predicts Prestige wins in information-rich environments, Dominance wins under resource scarcity or threat
- The result is not obvious to human intuition

### Realism mechanisms

Three features improve conversation quality over a naïve design:

1. **Speech examples in personas** — each agent has 4–5 example sentences in their own spoken voice, anchoring register and preventing the LLM from defaulting to corporate/LinkedIn language.
2. **Friction seed** — every run begins with a broadcast informing agents that a previous initiative failed and that people disagree about why, giving agents concrete grounds for disagreement.
3. **Anti-jargon prompt** — per-turn instructions explicitly forbid corporate filler phrases and require varied sentence length and natural spoken rhythm.

### Silence mechanism

Each round, agents are invited to speak in randomized order. They may respond with THINK + TALK + DONE (speaking) or just DONE (silence). Order is reshuffled every round (not just per run) to eliminate position bias.

### Checkpoint / resume

After each run, a checkpoint JSON is written to `results/step1_checkpoints/` or `results/step2_checkpoints/`. On restart, completed runs are loaded from checkpoint and skipped. This means a 20-run Step 2 job can be safely interrupted and continued.

---

## References

- Henrich, J., & Gil-White, F. J. (2001). The evolution of prestige. *Evolution and Human Behavior*, 22(3), 165–196.
- Cheng, J. T., Tracy, J. L., Foulsham, T., Kingstone, A., & Henrich, J. (2013). Two ways to the top. *Journal of Personality and Social Psychology*, 104(1), 103–125.
- Park, G., et al. (2020). TinyTroupe: LLM-powered multi-agent persona simulation. Microsoft Research.
