# TinyTroupe Pitfalls

Failure modes hit while building this simulation that are **properties of TinyTroupe and the
OpenAI API, not of our code**. They will bite again on a new study, a new model, or richer
personas. Each entry names the guard that currently absorbs it — if you refactor that guard away,
the failure comes back.

The original log also covered bugs in `baseline_sim.py` / the `mbti_baseline` package. Both are
gone (see git history before the 2026-08 restructure); those entries were dropped.

---

## P1 — `listen_and_act` returns `None`, caller crashes with `TypeError`

**Symptom:** `TypeError: 'NoneType' object is not subscriptable` deep inside TinyTroupe.

**Cause:** `openai_client.send_message` exhausts its retries (usually on `429 Too Many Requests`)
and returns `None`. TinyTroupe's `_generate_tentative_action` then does `next_message["role"]`
with no None guard. TinyTroupe's own `continue_on_failure=True` never helps here, because this is
a Python `TypeError`, not an LLM validation error.

**Guard:** `src/discussion.py:AgentTransport.actions` wraps every agent call and returns an empty
action list on failure. The turn is recorded as silence and the run continues.

**Watch out:** a rate-limited run degrades into agents that "choose" not to speak. Speech rate is a
dependent variable here, so silent API failures silently corrupt the data. That is why
`AgentTransport.actions` prints a warning per failure and `_check_quota` aborts the whole run after
`_MAX_CONSECUTIVE_FAILURES` (5) — better to stop with checkpoints saved than to publish a run
whose silences are really 429s.

---

## P2 — Rate limits from orphaned background processes

**Cause:** background diagnostic processes left running keep retrying with TinyTroupe's
exponential backoff (5s → 25s → 125s → 625s), eating the shared key's rate limit alongside the
real run. This was the actual origin of a P1 crash that first looked like a bad request.

**Guard:** none in code — check `ps` before blaming the API. If runs start failing in bursts, look
for your own stray processes first.

---

## P3 — `LengthFinishReasonError`: structured output truncated

**Cause:** persona system prompts are large (~4000 prompt tokens for the rich personas in
`studies/*/personas/`). TinyTroupe's structured output wraps every action in a Pydantic model with
a `reasoning` field, so the completion needs real headroom. At 300 tokens the JSON truncates
mid-response; at 800 it still truncates. 1200+ is the working floor, and the current default in
`config.ini.example` is 3000.

**Guard:** `DISCUSSION_MAX_TOKENS` / `VOTE_MAX_TOKENS` in `config.ini [Simulation]`.

**Watch out:** this scales with persona richness. A new study with longer persona specs needs the
ceiling raised again, and the symptom is a parse failure, not an obvious "too long" error.
Survey instruments are the next pressure point: a 22-item battery answered in one call needs room
for 22 ratings plus reasoning.

---

## P4 — `LengthFinishReasonError` is an `OpenAIError`, not a `TypeError`

**Cause:** an early version of the transport caught only `TypeError`/`AttributeError`
(the P1 bug). `LengthFinishReasonError` subclasses `openai.OpenAIError`, so after TinyTroupe
exhausted its own retries the exception propagated and killed the run.

**Guard:** `AgentTransport.actions` catches `(TypeError, AttributeError, openai.OpenAIError)` (the openai arm drops out only when the package is absent, e.g. in tests), plus a
bare `except Exception` fallback. Keep the `openai.OpenAIError` arm.

---

## P5 — TinyTroupe writes log files despite `loglevel_file = NONE`

**Cause:** TinyTroupe reads its config from `Path.cwd() / "config.ini"`. Run from the wrong
directory it never finds ours, falls back to its own defaults, and drops
`tinytroupe.<timestamp>.log` into the CWD.

**Guard:** `run.py` and `tools/gen_personas.py` both call `os.chdir(_PROJECT_DIR)` before any
TinyTroupe import. Any new entry point must do the same.

**Related:** `src/runtime.py:setup_file_logging` deliberately defers attaching file handlers until
after TinyTroupe's `start_logger()` has run — attaching earlier means TinyTroupe clears our
handlers. That ordering is load-bearing; see the docstring.

---

## P6 — A persona spec missing `nationality` crashes every turn it takes, silently

**Symptom:** contrasted personas (the ones `run.py` samples 1-per-run) show near-zero speech
rate, and every respondent on a self-report survey answers 0/N items after both retry attempts —
in the same run. Looks like two unrelated failures; it is one.

**Cause:** `TinyPerson.minibio()` (tinytroupe/agent/tiny_person.py:1867) builds the agent's
biography with `self._persona['nationality']` — a direct dict index, no `.get()`, no default.
`minibio()` is called on effectively every `listen_and_act`, discussion turns and survey
administrations alike. A persona spec that never set that key raises `KeyError: 'nationality'` on
its very first action. `AgentTransport.actions` (P1's guard) catches it with the bare
`except Exception` fallback and records the turn as silence — so the crash never surfaces as an
error, it just looks like the agent chose not to speak, or the survey parser got a blank reply.

Hit this via `tools/pair_bank.py`, which reuses `sample_bank.to_tinyperson_spec()` to build
personas straight from `personas_output.json` (no LLM generation step). That bank carries
occupation and Big Five, nothing else — `to_tinyperson_spec` never wrote `nationality`,
`gender`, `residence` or `country_of_residence`. The hand-written personas in
`studies/prestige_dominance/personas/` all have `nationality` (an LLM filled it in during
generation), so they never hit this — the bug is specific to the direct-from-bank path.

**Guard:** `to_tinyperson_spec` now sets `"nationality": "not specified"` on every persona it
builds. That is the only field `minibio()` indexes without a fallback; `gender` and
`country_of_residence`/`residence` are read with `.get()`/`self.get()` elsewhere and don't crash
when absent, so they were left out rather than fabricated.

**Watch out:** any future direct-from-data persona builder (bypassing LLM generation, which tends
to fill in demographic-sounding fields on its own) needs to check this by hand. The failure mode
gives no error message and no stack trace — the only symptoms are implausibly low speech rates
and a self-report instrument that fails 100% of respondents. If both show up together in the same
run, suspect a missing required field before suspecting the model or the prompt.

---

## P7 — P3 recurs mid-run as conversation context grows, and gets worse in longer discussions

**Symptom:** a discussion call starts failing with the same `LengthFinishReasonError` as P3
(`completion_tokens` pinned at the `DISCUSSION_MAX_TOKENS` ceiling), but this time as a **retry
loop that cannot succeed**: TinyTroupe's own client retries the identical prompt up to
`max_attempts` (5) with exponential backoff (2s -> 10s -> 50s -> 250s -> ~1250s), and every retry
truncates at the same ceiling because the prompt is deterministic — nothing about a retry shortens
it. A run can stall for 20+ minutes on one turn before TinyTroupe gives up and P4's guard
(`openai.OpenAIError` caught by `AgentTransport`) finally records it as silence.

**Cause:** P3 sized `DISCUSSION_MAX_TOKENS = 3000` against a single persona's system prompt. It
does not scale with **transcript length**: `prompt_tokens` grows round over round as the
discussion accumulates, and the model's reasoning + response has to fit in what's left of the
ceiling regardless. Observed on `pd_matched` collaborative, run.py's `--runs 20` background job,
2026-08-24: 12 distinct calls truncated across a ~16-run stretch, `prompt_tokens` ranging
6318-8648; two of those (8381 and 8648) exhausted all 5 internal attempts before giving up.

**Why collaborative and not threat:** in the same session, `threat` (20/20 runs, ~3h41m) logged
far fewer of these than `collaborative` (still at 16/20 after a comparable wall-clock stretch).
Read transcripts back this up — threat's dominant persona repeatedly cuts discussion short
("We've spent long enough on this... Decision's made"), while collaborative's neutrals build
consensus over several back-and-forth turns before converging, which is exactly what grows
`prompt_tokens`. **This means the truncation rate is not independent of condition** — a design
where the very thing being measured (talkative consensus-building vs. curt unilateral decisions)
also drives how often turns get silently dropped by a token ceiling is a confound worth watching,
not just an inconvenience. Turns lost this way are indistinguishable in the checkpoint from turns
where the agent had nothing to say.

**Guard:** none yet — `DISCUSSION_MAX_TOKENS` was not raised for this run. `config.ini`
`[Simulation] DISCUSSION_MAX_TOKENS` is the lever; raising it (e.g. to 4500-6000) should be
revisited before the next full run of any condition prone to long consensus-building discussions.

**Watch out:** because the retry is deterministic, do not expect a fixed `--retries` count to help
here the way it does for rate limits (P1/P2) — the fix is headroom, not persistence. If a study's
discussions run long (many participants, many rounds, verbose personas), check `prompt_tokens` in
the logs before trusting speech-rate comparisons across conditions that differ in how much
back-and-forth they naturally produce.
