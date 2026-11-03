# Working in agent-sim

Rules for any agent working in this repo. What the project is: `README.md`. Where it stands:
the Status section of `README.md` (update it when a stage finishes). Research write-up:
`docs/README.md`. Vocabulary: `CONTEXT.md`.

## Talking to the user

- Reply in Traditional Chinese. Keep code identifiers, paper titles and quoted scale items in English.
- Back every design or research claim with evidence: a paper page, a results file, a commit,
  or a `docs/` section. If nothing backs it, say so first. The user checks ("有證據嗎").
- Persona attributes and manipulations need literature support (e.g. traits from Ronay et al.
  2023 Table 2; checks from Cheng et al. 2010). Read original PDFs; put them in `docs/`.
- Separate the paper's stated rule from our inference (Sheng et al. never state theirs).
- Lead with the conclusion; keep explanations to the data asked about.

## Money: API calls

- **Never call the API without telling the user first and getting a yes.** "要浪費API的話要讓我知道".
  Give the estimated number of calls and the model. Smallest run that answers the question.
- Calls happen in: `run.py validate | run | measure-check`, `tools/replicate_study5.py`
  (only for instruments without saved answers), `tools/score_pooling.py`.
- Offline (free): `run.py report | mediate | layers | style-check`, `tools/study5_tables.py`,
  `tools/replication_criteria.py`, `tools/ocean_confound.py`, tests.
- For offline checks of API code paths, use a temporary `config.ini` with an invalid key and an
  `OUTPUT_DIR` outside `results/`, so a stray call fails instead of costing money.
- Never print, copy or commit `config.ini` (it holds the key). Run logs echo it: `*.log` and
  `*.out` under `results/` are gitignored for that reason.

## Git

- Commit messages: the change description only. **No `Co-Authored-By:`, `Claude-Session:` or
  "Generated with" lines**, whatever a default workflow suggests.
- Commit or push only when asked. Work branch: `fix/paired-sampling`.

## Data

- Never delete experiment data: `results/**` (checkpoints, answers, summaries), `studies/**`
  definitions, `personas_output.json`, paper PDFs. Archives under `results/archive_*` stay.
- Regenerable and gitignored: `studies/dp_check_traits/personas/`, `results/replication/*/personas/`.
- Every run checkpoints to `results/<study>/<condition>/checkpoints/`; re-running resumes.
- Parallel runs are processes (`run.py run --parallel N`), never threads: TinyTroupe state is
  global. Workers coordinate only through per-run lock files and atomic checkpoint writes.

## Code

- Match the surrounding style. Comments explain *why* (design decisions, measured costs,
  traps found), not what. No docstring sweeps, no new abstraction layers, no new dependencies.
- Unmatched answers are missing data, never guessed: rating scales store `null`; votes and task
  answers go through `discussion._resolve_option` (whole-word match, one hit or None).
- Reverse-keyed items: score through `Instrument.scored`. Only `effectiveness_styles`
  (`moral_character_1`, `_3`) has any.
- Tests: `test_core.py` at the top level, `.venv/bin/python -m pytest -q test_core.py`
  (or `python3 test_core.py`). Add one small test with each behaviour change.
- A refactor must not change outputs. Prove it: diff the tools' output, `run.py layers` on
  simulated checkpoints (`tools/layer_power.make_run`), loaded studies, and survey prompts
  before and after (`PYTHONHASHSEED=0` when output contains sets).

## Decks (pptx)

Content:
- Few slides. Data first, conclusion second: each slide is mainly a table, with at most a
  one-line takeaway. Conclusion and next-step slides last.
- Only the metrics the analysis actually decides on (5c: Model 2 β and p; 5a: ΔR², p, RW%,
  RW rank). Add another metric only when it must be read together with these (e.g. the
  prediction interval beside β). Full tables go in `docs/study5-data.md`, not on slides.
- State criteria concretely: the exact rule and threshold (e.g. "β > 0, p < .05, Model 2, no
  correction"), its source, and whether it is the paper's stated rule or our inference.
- Order for a replication: goal and criterion → paper's data → ours, same columns → cell by
  cell under each criterion → cause → conclusion → directions.
- Slide text English unless asked (conclusion/direction slides have been Chinese). Notes in
  Chinese, teaching from scratch: what each column is, how computed, how to read, caveats.

Build:
- Source is `docs/<name>.md` (`# ` per slide). While discussing page by page, edit only the
  `.md`; build once at the end with `tools/build_deck.sh <name> [render_dir]`.
- Then read every rendered slide; fix overflow, two-line titles, wrapped headers. Tables on the
  slide, never in `::: notes`. 13 data rows fit at 12pt, 14 at 11pt. A pipe-table separator
  longer than 72 chars sets column widths by dash count.
- `/tmp2/b12902056/ppt/` (the build copy) also holds unrelated credential files
  (`creds.json`, `席位帳號密碼.md`): touch only the deck you are building.
- `cp` and `rm` are aliased to interactive: use `\cp -f`, `\rm`.

## Study 5 replication conventions

- Paper: `docs/2027-27008-001.pdf`; preregistration (5c only):
  `docs/aspredicted-223181-sheng-criterion-validity.pdf`; supplement (S9, S11):
  https://supp.apa.org/psycarticles/supplemental/apl0001347/apl0001347_Supplemental_Materials.pdf
- Judge cells by two criteria, reported separately: A, same sign and significance status as the
  paper (Open Science Collaboration, 2015); C, inside the paper's 95% prediction interval
  (Patil, Peng & Leek, 2016). Significance alone counts "too large" as success.
- "Holding OCEAN fixed" means OCEAN dummies added to Model 2 on saved data, not re-running
  personas without OCEAN. Say so whenever it is shown.
- Calibration target for persona needs vs personality: supplement Table S9.1 (human |r| ≤ .27).
  Calibrate on S9, validate on Study 5; never tune personas on Study 5 results.
