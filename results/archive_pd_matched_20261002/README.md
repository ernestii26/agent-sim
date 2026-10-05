# pd_matched — 10 runs per condition, 2026-08-26

The data behind design-log section 22 ("H2 replicates under the corrected design":
threat, D 2.10 vs P 0.70 votes/run, p = 0.028). Archived on 2026-10-02 when the
`pd_matched` study was deleted and `ffni_mediation` became the only study.

Not comparable to anything built after it:

- 6 matched P/D pairs and 24 neutrals reused across every run; the current design draws a
  fresh cast from the bank per run and never reuses a persona (`tools/build_personas.py`)
- personas carried an occupation, age and parental status from the bank, and a name from
  a hand-written pool of culturally marked full names; current personas carry none of these
- the style manipulation was the project's own block (`style.influence`, six behavioural
  `personality.traits`, four `speech_examples`), written for this project and uncited;
  current P/D traits are adapted from Ronay et al. (2023) Table 2, Study 3
- the scenario was a hand-written hospital vignette, not a HiddenBench task

The study definition is recoverable from git history (`studies/pd_matched/`, last present
in commit 69b89c5).
