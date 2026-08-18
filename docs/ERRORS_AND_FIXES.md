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

**Guard:** `src/discussion.py:_safe_listen_and_act` wraps every agent call and returns an empty
action list on failure. The turn is recorded as silence and the run continues.

**Watch out:** a rate-limited run degrades into agents that "choose" not to speak. Speech rate is a
dependent variable here, so silent API failures silently corrupt the data. That is why
`_safe_listen_and_act` prints a warning per failure and `_check_quota` aborts the whole run after
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

**Cause:** an early version of `_safe_listen_and_act` caught only `TypeError`/`AttributeError`
(the P1 bug). `LengthFinishReasonError` subclasses `openai.OpenAIError`, so after TinyTroupe
exhausted its own retries the exception propagated and killed the run.

**Guard:** `_safe_listen_and_act` catches `(TypeError, AttributeError, openai.OpenAIError)`, plus a
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
