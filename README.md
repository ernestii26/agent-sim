# agent-sim

Multi-agent social simulation on [TinyTroupe](https://github.com/microsoft/TinyTroupe): a room of
LLM personas discusses a scenario, may stay silent, then votes. The framework measures how the
groups you define differ in votes received, speech rate, and verbosity.

**The framework knows nothing about any particular research theme.** Groups, personas, scenarios,
and hypotheses all live in `studies/<name>/`. Adding a new theme means adding a directory, never
editing `src/`.

## Setup

```bash
pip install -r requirements.txt
cp config.ini.example config.ini      # then paste your API key
python3 test_core.py                  # fast self-check, no API calls
```

## Running

```bash
python3 run.py list                                        # studies + conditions
python3 run.py validate      ffni_mediation                # do agents ever stay silent?
python3 run.py measure-check dp_check                      # gate (a): P/D self-report on every pair
python3 run.py run           dp_check collaborative --runs 20
python3 run.py run           dp_check threat --runs 20
python3 run.py style-check   dp_check                      # gate (b): must pass before ffni_mediation
python3 run.py measure-check ffni_mediation                # is the rating scale usable at all?
python3 run.py run           ffni_mediation collaborative
python3 run.py run           ffni_mediation threat --runs 20 --rounds 3
python3 run.py report        ffni_mediation threat         # re-report, no API calls
python3 run.py mediate       ffni_mediation --need protection --group D   # H6
python3 run.py layers        ffni_mediation                              # H3, H4, H5, H7
```

`mediate` and `layers` read both conditions' checkpoints, because every hypothesis they
cover is a claim about the difference between conditions. `report` renders one condition
and cannot see across them. `layers` bootstraps over runs rather than respondents — three
neutrals in a room watched one discussion between them.

Run `measure-check` before paying for a study that uses instruments. It administers the
self-report scale twice per persona (no discussion, no votes) and fails loudly if the agents
straight-line the scale, answer it differently every time, or give subscales that do not
differentiate. That costs a couple of dollars; discovering it 40 runs in does not.

Every run is checkpointed to `results/<study>/<condition>/checkpoints/run_NNN.json`. Re-running the
same command reuses them, so an interrupted study — or one stopped by an exhausted API quota —
resumes where it left off. Delete the checkpoint directory to start fresh.

Output lands in `results/<study>/<condition>/`: checkpoints and logs (gitignored, regenerable) plus
a summary JSON and chart (tracked).

## Adding a study

Create `studies/<name>/study.json` — the whole design.

```jsonc
{
  "title": "...",
  "groups": {
    "P": {"label": "Prestige",  "ids": [], "sample": 1},                     // 1 drawn per run
    "D": {"label": "Dominance", "ids": [], "sample": 1, "pair_with": "P"},  // same index as P
    "N": {"label": "Neutral",   "ids": [], "sample": 3}
  },
  "contrast": ["P", "D"],          // the two groups compared statistically
  "vote_prompt": "Based on what you observed, who should lead this team?",
  "instruments": ["ffni"],         // optional: files under instruments/
  "personas_from": "other_study",  // optional: borrow personas instead of building them
  "conditions": {
    "collaborative": {
      "label": "Collaborative",
      "hypothesis": "H1: P receives more votes than D",
      "scenario": "The situation put to the room.",
      "friction": "[Optional background tension broadcast after the scenario.]",
      "contrast": ["D", "P"]       // optional: flip the direction for this condition
    }
  }
}
```

Then build the personas from the bank:

```bash
python3 tools/build_personas.py <name> --runs 40   # personas/, bank_sample.json, fills in ids
python3 test_core.py                               # verifies study.json and personas agree
```

It builds exactly one cast per run: P_i and D_i from one bank row, three neutrals from
three more, every row a different OCEAN profile. The balanced sampler seats every id once
per cycle, so each persona appears in exactly one run, and `run` refuses a run count past
that cycle instead of quietly reusing people. What a persona carries, and where the P/D
traits come from, is in the tool's docstring.

## Layout

| Path | Role |
|---|---|
| `run.py` | CLI: `list` / `validate` / `measure-check` / `run` / `report` / `mediate` / `layers` |
| `src/study.py` | Loads and validates `study.json` |
| `src/instrument.py` | Loads a rating scale from `instruments/*.json`; subscale scoring |
| `src/config.py` | `config.ini` → `RunConfig` |
| `src/pipeline.py` | Composes each run, executes, checkpoints |
| `src/discussion.py` | One discussion, one vote, one survey administration; retries and quota detection |
| `src/persona_store.py` | Persona spec → TinyTroupe agent |
| `src/run_record.py` | One run's output; the only thing that knows the checkpoint JSON shape |
| `src/stats.py` | Numeric primitives (means, OLS slope, paired t-test, Cronbach's alpha) |
| `src/analysis.py` | Run records → summary dicts (`summarize_*`, `need_outcome_links`) |
| `src/render.py` | Summary dicts → terminal tables, JSON files, charts (`render_*`, `plot_*`) |
| `src/runtime.py` | TinyTroupe wiring and logging |
| `tools/build_personas.py` | Builds a study's personas from `personas_output.json` |
| `studies/` | One directory per research theme |
| `docs/` | Design notes, prior results, debugging log |

## Instruments

A study may administer rating scales during a run. Each one is a file under
`studies/<name>/instruments/<key>.json`:

```jsonc
{
  "scale": [1, 7],
  "anchors": ["strongly disagree", "strongly agree"],
  "about": "self",              // "self" | "prototype" | "each_candidate"
  "targets": ["N"],             // which groups answer it
  "timing": ["baseline", "post"],
  "subscales": {"protection": ["item text", "..."]}
}
```

The whole battery goes out in one call per administration, with item order shuffled per
respondent. Ratings outside the scale, or items the model skipped, are stored as `null` and
flagged — never imputed, so a parse failure reads as missing data rather than fake moderation.

**Measurement never contaminates the discussion.** The baseline administration runs on a
throwaway fork of each agent, so the agents who actually discuss have never seen the items —
a 22-item battery about what you want from a leader is a powerful prime. After the discussion,
each post measure branches from the same post-discussion state, so the survey does not prime the
vote and the vote does not prime the survey, yet all of them reflect the same conversation. This
is one thing a simulation can do that a human study cannot.

## Method notes

Agents may answer a turn with `DONE` alone, which counts as silence — speech rate is a real
dependent variable, not an artifact of everyone always talking. `run.py validate` confirms that
mechanism still works before you spend a full study on it. Invitation order is reshuffled every
round to remove position bias, and agents are deep-copied per run so no state leaks between runs.

Hypothesis tests are one-sided paired t-tests over per-run values, testing
`contrast[0] > contrast[1]`. `scipy` supplies the p-value; without it the t statistic still prints.

## Studies

### `dp_check` — the gate before `ffni_mediation`

Do the P and D traits make agents read as prestigious and dominant? Borrows
`ffni_mediation`'s personas, task pools, friction and sampler seed, so run i here is run i's
cast there. Neutrals rate the P and D they just watched on Cheng, Tracy & Henrich's (2010)
peer-rated Dominance and Prestige scales (`dp_peer`, 16 items, one omitted as in Cheng et al.
2013 for briefly acquainted groups); P and D also rate themselves (`dp_self`, 17 items) as a
sanity check. Passes when, in **each** condition, D > P on dominance **and** P > D on
prestige, paired over runs, two-sided p < .05. d_av is printed beside Ronay et al. (2023)
Study 3's pre-test (d = 2.15 / 2.06) as a benchmark, not a threshold.

### `ffni_mediation`

Adds the Fundamental Follower Needs Inventory as a **mediator** between context and endorsement,
on personas built from the bank, one fresh cast per run. Sheng, Andrews & van Vugt (2026, *JAP* 111(6),
768-801; `docs/2027-27008-001.pdf`) validated the FFNI and left open the questions this study is shaped
to answer. The full list, quoted with page numbers, is under *Research gaps* in `docs/README.md`.
Two of them:

- follower needs are *assumed* to mediate the known conflict-to-dominant-leader effect, but were
  never measured (p. 795)
- would intergroup conflict strengthen the protection–authoritarianism link (p. 789)?

The pivot is that the paper's own results split across two psychological layers. In Study 5 the
protection and status needs predicted **leadership prototypes** (Strength, Tyranny, Masculinity,
Well-Groomed — the dominance side of the dual model) but did **not** predict **perceived
effectiveness** of dominance-based leadership. Wanting to be protected is not the same as judging
an authoritarian boss effective: classification and association are one process, substantive
evaluation is another. So this study measures both layers, and H5's dominance half is expected to
possibly come back null — that is a result, not a bug.

H1 and H2 carry over unchanged. New: H3 (threat raises protection), H4 (cognition layer), H5
(evaluation layer, the observed P and D), H6 (mediation) and H7 (threat strengthens protection → D
effectiveness). All seven are in `studies/ffni_mediation/study.json`.

The FFNI is reproduced verbatim under CC BY-NC-ND 4.0 — attribution and licence travel with the
items in `instruments/ffni.json`, and NoDerivatives means they must not be reworded, abridged, or
translated.
