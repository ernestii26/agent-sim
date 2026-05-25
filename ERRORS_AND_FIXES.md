# mbti_baseline — Errors & Fixes Log

---

## E1 — `ModuleNotFoundError: No module named 'mbti_baseline'`

**File:** `baseline_sim.py`  
**When:** Running `python baseline_sim.py --step1` from inside `mbti_baseline/`  
**Root cause:** The script was invoked from inside the package directory. Python's module resolver looks for `mbti_baseline` as a sibling of `sys.path[0]`, but `sys.path[0]` was `mbti_baseline/` itself, so the package couldn't be found.  
**Fix:** Added a path bootstrap at the top of `baseline_sim.py` that resolves `__file__` to the repo root and prepends it to `sys.path`. Also fixed `_get_config` to find `config.ini` via `_repo_root` rather than `Path("config.ini")` (which is CWD-relative). Script can now be run from any directory.

---

## E2 — `TypeError: 'NoneType' object is not subscriptable`

**File:** `discussion.py` → TinyTroupe `action_generator.py:423`  
**When:** First invocation of `agent.listen_and_act(...)` during `run_discussion`  
**Stack trace (abbreviated):**
```
mbti_baseline/pipeline.py, step1_validate_silence
  → mbti_baseline/discussion.py:100, run_discussion
    → tinytroupe/control.py:747, wrapper
      → tinytroupe/agent/tiny_person.py:904, act
        → tinytroupe/agent/action_generator.py:423, _generate_tentative_action
TypeError: 'NoneType' object is not subscriptable
```
**Root cause (confirmed by E3 below):** `openai_client.py:send_message` exhausted all retries on a `429 Too Many Requests` rate limit error and returned `None`. TinyTroupe's `_generate_tentative_action` does `next_message["role"]` without a None guard, raising the `TypeError`. TinyTroupe's own `continue_on_failure=True` config is never reached because the crash is a Python TypeError, not an LLM validation error.  
**Fix:** Replaced all direct `agent.listen_and_act()` calls with `_safe_listen_and_act()`, which wraps the call in `try/except (TypeError, AttributeError)` and returns an empty action list on failure. The caller treats the failed turn as silence (no TALK action emitted), records a warning, and continues the run.

```python
def _safe_listen_and_act(agent, prompt):
    try:
        return agent.listen_and_act(prompt, return_actions=True, communication_display=False) or []
    except (TypeError, AttributeError) as exc:
        print(f"  [warn] listen_and_act failed ({type(exc).__name__}: {exc}) — treating as silence")
        return []
```

---

## E3 — `429 Too Many Requests` + Orphaned diagnostic processes consuming quota

**When:** Step 1 first run (2026-05-11 ~12:42)  
**Root cause (confirmed):** During debugging of E2, 5 background Python processes were launched for diagnostics but never killed. All 5 were silently retrying their own API calls with TinyTroupe's exponential backoff (5s → 25s → 125s → 625s), consuming the shared API key's rate limit alongside the real Step 1 process. The rate limit exhaustion was what actually caused the `None` return in E2 — not a BadRequestError.

**TinyTroupe log:**
```
[3] Rate limit error, waiting 25.0s
[4] Rate limit error, waiting 125.0s
[5] Rate limit error, waiting 625.0s  ← max_attempts=5 exhausted → returns None → TypeError in E2
```

**Orphaned PIDs:** 1128477, 1128494, 1129001, 1129019, 1129879, 1129885  
**Fix:** Killed all orphaned processes with `kill <pids>`. Also killed the crashed Step 1 process (1131800) and restarted with new code (`_safe_listen_and_act`) that handles None gracefully so future rate-limit exhaustion degrades to silence instead of crashing.  
**Prevention:** Never leave background diagnostic processes running against a shared API key. Use `ps aux | grep python` to verify before starting experiments.

---

## E4 — `LengthFinishReasonError`: completion truncated at 300 tokens

**When:** Step 1 first successful API call (2026-05-11 ~15:47), model `gpt-4.1`  
**Log:**
```
[3] LengthFinishReasonError: Could not parse response content as the length limit was reached
completion_tokens=300, prompt_tokens=3963
```
**Root cause:** `DISCUSSION_MAX_TOKENS=300` is too small. The persona system prompts are ~3963 prompt tokens (rich mbti_sim personas with beliefs, skills, behaviors, etc.). TinyTroupe's structured output response format (Pydantic model with `reasoning` field + action JSON) cannot be completed within 300 tokens, so the JSON is truncated mid-response and fails to parse.  
**Fix:** Increased `DISCUSSION_MAX_TOKENS` and `VOTE_MAX_TOKENS` from 300/600 → 800/800 in `config.ini [Baseline]`. 800 tokens gives sufficient headroom for the structured JSON completion without excessive cost.

---

## E5 — `LengthFinishReasonError`: discussion still truncated at 800 tokens

**When:** Step 1 second run (2026-05-11 ~16:06), model `gpt-4.1`  
**Log:**
```
[3] LengthFinishReasonError: Could not parse response content as the length limit was reached
completion_tokens=800, prompt_tokens=3993
```
**Root cause:** 800 tokens still insufficient. `prompt_tokens=3993` is slightly larger than the 3963 estimated in E4 (likely due to small context differences). TinyTroupe's structured output requires more than 800 tokens for `reasoning` + JSON action.  
**Fix:** Raised `DISCUSSION_MAX_TOKENS` and `VOTE_MAX_TOKENS` from 800 → **1200** in `config.ini [Baseline]`.

---

## E6 — `LengthFinishReasonError` not caught → process crash

**When:** 2026-05-11 after E5 fix  
**Root cause:** `_safe_listen_and_act` only caught `TypeError`/`AttributeError` (TinyTroupe None-return bug). `LengthFinishReasonError` is an `openai.OpenAIError` subclass — after TinyTroupe exhausts its 3 retries, the exception propagates up and crashes the entire run.  
**Fix:** Added two more except clauses to `_safe_listen_and_act`:
```python
except openai.OpenAIError as exc:          # LengthFinishReasonError, RateLimitError, etc.
    print(f"  [warn] OpenAI error ...")
    return []
except Exception as exc:                   # any other unexpected error
    print(f"  [warn] Unexpected error ...")
    return []
```
All API errors now degrade to silence rather than crashing the run.

---

## E7 — TinyTroupe log files appear despite `loglevel_file = NONE`

**When:** 2026-05-11, after adding `[Logging] loglevel_file = NONE` to sim2/config.ini  
**Root cause:** TinyTroupe reads its config via `Path.cwd() / "config.ini"`. When `baseline_sim.py` is run from inside `mbti_baseline/`, CWD = `mbti_baseline/`, so TinyTroupe cannot find sim2/config.ini → falls back to its own defaults → file logging is enabled → creates `tinytroupe.<timestamp>.log` in CWD.  
**Fix (sim2 version):** Added `os.chdir(_repo_root)` at the top of `baseline_sim.py`, before any TinyTroupe import.  
**Fix (standalone version):** `run.py` calls `os.chdir(_PROJECT_DIR)` where `_PROJECT_DIR` contains its own `config.ini` with `loglevel_file = NONE`.
