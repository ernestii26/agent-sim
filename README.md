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
python3 run.py validate      prestige_dominance            # do agents ever stay silent?
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

Create `studies/<name>/` with two files:

**`study.json`** — the whole design.

```jsonc
{
  "title": "...",
  "groups": {
    "A": {"label": "Prestige",  "ids": ["A1", "A2"], "sample": 1},   // 1 drawn per run
    "N": {"label": "Neutral",   "ids": ["N1", "N2"], "sample": null} // all, every run
  },
  "contrast": ["A", "B"],          // the two groups compared statistically
  "vote_prompt": "Who do you most trust to lead this team?",
  "instruments": ["ffni"],         // optional: files under instruments/
  "personas_from": "other_study",  // optional: borrow personas instead of copying them
  "conditions": {
    "collaborative": {
      "label": "Collaborative",
      "hypothesis": "H1: A receives more votes than B",
      "scenario": "The situation put to the room.",
      "friction": "[Optional background tension broadcast after the scenario.]",
      "contrast": ["B", "A"]       // optional: flip the direction for this condition
    }
  }
}
```

Sampled groups draw from a balanced sampler — every id appears once per cycle before any repeats,
so no persona is over-represented. `sample: null` means the whole group is in every run.

**`seeds.json`** — the persona generation prompts.

```jsonc
{
  "prompts": {"leader": "<system prompt>", "neutral": "<system prompt>"},
  "personas": [
    {"persona_id": "A1", "group": "A", "prompt": "leader", "temperature": 0.8,
     "user": "Generate a persona for: ...  {existing_names}"}
  ]
}
```

`{existing_names}` is replaced with the names generated so far — useful for telling the model to
avoid near-duplicates. Then:

```bash
python3 tools/gen_personas.py <name>     # writes studies/<name>/personas/*.agent.json
python3 test_core.py                     # verifies study.json and seeds.json agree
```

`test_core.py` checks every study in `studies/` — a persona id declared in `study.json` but missing
from `seeds.json` or from disk fails the check.

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
| `tools/gen_personas.py` | Generates a study's personas from `seeds.json` |
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

### `prestige_dominance`

Do prestige-type agents (influence earned through expertise) receive more peer leadership votes
than dominance-type agents (influence claimed through authority)? Follows Henrich & Gil-White
(2001) and Cheng et al. (2013). H1: Prestige wins in the collaborative condition. H2: Dominance
wins under threat. Charts from the original pipeline are in `results/archive_prestige_dominance/`
and the write-up is `docs/result.md`; those predate the 2026-08 restructure and use the old record
format, so `run.py report` cannot read them.

### `ffni_mediation`

Adds the Fundamental Follower Needs Inventory as a **mediator** between context and endorsement,
reusing the same 18 personas (`personas_from`). Sheng, Andrews & van Vugt (2026, *JAP* 111(6),
768-801; `docs/2027-27008-001.pdf`) validated the FFNI and left two questions open, both of which this
study is shaped to answer:

- follower needs are *assumed* to mediate the known conflict-to-dominant-leader effect, but were
  never measured (p.45-46)
- would intergroup conflict strengthen the protection-to-dominance link (p.42)?

The pivot is that the paper's own results split across two psychological layers. In Study 5 the
protection and status needs predicted **leadership prototypes** (Strength, Tyranny, Masculinity,
Well-Groomed — the dominance side of the dual model) but did **not** predict **perceived
effectiveness** of dominance-based leadership. Wanting to be protected is not the same as judging
an authoritarian boss effective: classification and association are one process, substantive
evaluation is another. So this study measures both layers, and H5's dominance half is expected to
possibly come back null — that is a result, not a bug.

H1 and H2 carry over unchanged; H3 (threat raises protection/status), H4 (cognition layer), H5
(evaluation layer), H6 (mediation) and H7 (threat moderates, narrowing the layer gap) are new.
All seven are listed in `studies/ffni_mediation/study.json`.

The FFNI is reproduced verbatim under CC BY-NC-ND 4.0 — attribution and licence travel with the
items in `instruments/ffni.json`, and NoDerivatives means they must not be reworded, abridged, or
translated.
