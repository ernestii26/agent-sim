# Persona pilot: raw LLM, human-like OCEAN distribution, HEXACO

## Context

The Study 5 replication showed that persona needs are near-proxies of single OCEAN settings
(affiliation–agreeableness r = .89; mean |r| needs vs personality .29, people .12 in Sheng
et al. supplement S9.1) and lack the people's common factor (mean inter-need r .22 vs .54,
Table 8 Sample B). The user chose three directions to compare in one pilot, every arm
answering only the generic FFNI (the S9.1 / Sample B instrument):

| Arm | Persona | N | Temperature | Question it answers |
|---|---|---|---|---|
| `raw_t0` | name only, no personality | 10 | 0 (config) | LLM default needs; variance collapses |
| `raw_t1` | name only, no personality | 60 | 1.0 | Does sampling noise alone give variance and a common factor? |
| `b5_human` | Big Five levels drawn from people's trait intercorrelations, bank description kept | 260 | 0 | Does a human-like trait distribution restore the common factor? (differs from arm A only in distribution) |
| `hexaco` | HEXACO six levels, independent tertiles, official high/low sentences, no bank description | 260 | 0 | Cell-by-cell comparable with S9.1; does Honesty–Humility drive status/fairness? |
| arm A (existing, free) | Big Five uniform + description | 261 | 0 | Baseline: `results/replication/a/ffni_generic.json` |

Known limit, accepted by the user's choice: `hexaco` has no bank description, so a gain over
arm A cannot be split between "HEXACO" and "no description" (the Big Five no-description
control was offered and not chosen). State this in the write-up.

Cost: 10 + 60 + 260 + 260 = **590 gpt-4.1 calls**; ask before running (CLAUDE.md).

## Step 1 — sources (read-only, before code)

- Big Five intercorrelations: van der Linden, te Nijenhuis & Bakker (2010), *J Res Pers* 44,
  315–327, doi 10.1016/j.jrp.2010.03.003 (meta-analysis, K = 212). Try the Erasmus repository
  (repub.eur.nl/pub/60667); if not open, ask the user for the PDF. Save to `docs/`, transcribe
  the 5×5 matrix with page number; flip Emotional Stability to Neuroticism (sign change).
- HEXACO wording: hexaco.org/scaledescriptions, the factor-level "very high" / "very low"
  sentences, verbatim, with citation. Medium level gets no sentence.

## Step 2 — `tools/persona_pilot.py` (new)

Reuse, do not re-implement:
- `tools/build_personas.py`: `to_spec` field layout (`Participant <k>`, age/nationality/
  occupation "not specified"), `profile`, `OCEAN_ORDER`.
- `tools/replicate_study5.py`: `GENERIC` instruction, `draw_rows` exclusion pattern, the
  `replace(study.self_report, key="ffni_generic", instructions=GENERIC, targets=())` instrument.
- `src/discussion.py`: `run_survey`, `clone_participants`; `src/persona_store.py`: `load_personas`.
- `src/config.py`: `RunConfig.survey`; temperature override via `dataclasses.replace(config.survey, temperature=1.0)`.
- `src/pipeline.py`: `_claim`, `_write_atomic` for per-persona claiming and atomic writes.
- `tools/study5_tables.py`: `items()` scoring; `src/stats.py`: `cronbach_alpha`.

Subcommands:
- `build <arm>`: write personas to `results/persona_pilot/<arm>/personas/` plus `sample.json`
  (seed, bank rows or drawn levels). Excludes bank rows used by `studies/ffni_mediation/bank_sample.json`
  and `results/replication/*/bank_sample.json`.
  - `b5_human`: draw z ~ MVN(0, R_vdL2010), cut at tertiles (±0.4307) to low/medium/high, take an
    unused bank row with that profile; exit loudly if a profile runs out.
  - `hexaco`: six factors independent, each level with p = 1/3; personality = {"hexaco": levels,
    "description": the official sentences for non-medium factors}.
  - `raw_*`: personality {} (verify `load_personas`/TinyTroupe accept it; test).
- `run <arm> [--parallel N]`: each persona's FFNI saved to `answers/<pid>.json`; a persona is
  claimed with `_claim` and written with `_write_atomic`, so N worker processes (spawned like
  `run.py _run_workers`) never double-answer and a rerun resumes. Processes, not threads.
- `analyze`: offline, for every arm plus arm A: need M/SD and α; inter-need r matrix, mean and
  range vs Table 8 Sample B; need × trait r (levels 0/1/2), mean |r| and max |r| vs S9.1
  (.12 / .27); for `hexaco`, cell-by-cell vs S9.1's HEXACO rows (difference, RMSE, sign
  agreement). Prints Markdown tables. Hard-code S9.1 HEXACO rows and Table 8 values from
  `docs/study5-data.md` §4.1 and §6.1.

## Step 3 — tests (offline, in `test_core.py`)

- `b5_human` sampler: tertile marginals ≈ 1/3, sample correlations of the latent draws ≈ R,
  no bank row reused, none overlapping the excluded samples.
- `hexaco` spec: six factors, sentences only for non-medium levels.
- Claiming: two concurrent `run` workers with `run_survey` faked answer each persona once.

## Step 4 — runs (each needs the user's yes)

1. Smoke, gpt-4o-mini, 3 personas per arm (12 calls), scratch output dir.
2. Full pilot, gpt-4.1, 590 calls, `--parallel 12`.

## Step 5 — write-up

Add a short section to `docs/README.md` (criteria, counts, the tables) and the arm results to
`docs/study5-data.md`; update the README Status. Next decision for the user: which arm to
validate on Study 5a (ILT, ~260 calls).

## Verification

- `.venv/bin/python -m pytest -q test_core.py` passes, including the new tests.
- Smoke run: every arm's answers complete (`_meta.complete`), personas match `sample.json`,
  no `.lock`/`.tmp` left, `analyze` prints all tables.
- `analyze` on arm A alone reproduces the existing numbers in `docs/study5-data.md` §6.2
  (mean |r| .29, affiliation–agreeableness .89) before trusting the new arms.
