from __future__ import annotations

import json
import random
import textwrap
import time
from itertools import count
from typing import Any

import openai

from runtime import actions_to_text, configure_tinytroupe_runtime, ensure_tinytroupe_imports
from persona_store import PRESTIGE_TYPES, DOMINANCE_TYPES

_WORLD_COUNTER = count(1)
_consecutive_api_failures = 0
_MAX_CONSECUTIVE_FAILURES = 5


class APIQuotaExhausted(RuntimeError):
    """Raised when the API appears to have no remaining quota (billing exhausted)."""


SCENARIO = (
    "Your team has been missing key deliverables for two consecutive quarters. "
    "Leadership has granted your group full autonomy to diagnose the root cause "
    "and commit to one concrete change. You must reach a shared decision that "
    "everyone in the room can commit to implementing."
)

SCENARIO_FRICTION = (
    "[Meeting context: This group has attempted to address performance issues before. "
    "A previous initiative stalled halfway through and was quietly dropped. "
    "People in this room have different — and sometimes conflicting — views on "
    "what actually went wrong and who was responsible. Not everyone trusts the "
    "last diagnosis that was made.]"
)

SCENARIO_THREAT = (
    "Your division is under review. Senior leadership will retain only one of two "
    "competing teams — yours or the other. The decision will be made in 48 hours. "
    "Your group must agree right now on a single pitch: what you deliver, who leads it, "
    "and who is accountable. If you cannot agree among yourselves, leadership will "
    "make the decision for you — and people may lose their positions."
)

SCENARIO_THREAT_FRICTION = (
    "[Meeting context: Two months ago, the rival team landed a major client your "
    "division had been pursuing for a year. Some people here believe your group lost "
    "because of indecision and unclear ownership. Others think it was a resourcing "
    "failure. Either way, you are now in direct competition for survival. "
    "Not everyone in this room agrees on who should be leading the response — "
    "and some people are wondering whether they have a future here at all.]"
)


def _safe_listen_and_act(agent: Any, prompt: str, retries: int = 3) -> list[dict[str, Any]]:
    global _consecutive_api_failures
    for attempt in range(1, retries + 1):
        try:
            result = agent.listen_and_act(
                prompt,
                return_actions=True,
                communication_display=False,
            )
            _consecutive_api_failures = 0
            return result or []
        except (TypeError, AttributeError) as exc:
            if attempt < retries:
                delay = 2 ** attempt
                print(f"  [warn] listen_and_act failed (attempt {attempt}/{retries}, retrying in {delay}s): {exc}")
                time.sleep(delay)
            else:
                _consecutive_api_failures += 1
                print(f"  [warn] listen_and_act failed after {retries} attempts ({type(exc).__name__}: {exc}) — treating as silence")
                _check_quota()
                return []
        except openai.OpenAIError as exc:
            if attempt < retries:
                delay = 2 ** attempt
                print(f"  [warn] OpenAI error (attempt {attempt}/{retries}, retrying in {delay}s): {exc}")
                time.sleep(delay)
            else:
                _consecutive_api_failures += 1
                print(f"  [warn] OpenAI error after {retries} attempts ({type(exc).__name__}: {exc}) — treating as silence")
                _check_quota()
                return []
        except Exception as exc:
            print(f"  [warn] Unexpected error ({type(exc).__name__}: {exc}) — treating as silence")
            return []
    return []


def _check_quota() -> None:
    if _consecutive_api_failures >= _MAX_CONSECUTIVE_FAILURES:
        raise APIQuotaExhausted(
            f"API failed {_consecutive_api_failures} times in a row — "
            "likely billing quota exhausted. Stopping simulation."
        )


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def run_discussion(
    *,
    agents: list[Any],
    names: list[str],
    persona_types: list[str],
    scenario: str,
    friction: str,
    rounds: int,
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    on_progress: Any = None,
) -> list[dict[str, Any]]:
    """Run a multi-round discussion with optional silence.

    Each round, invitation order is independently shuffled to prevent position bias.
    Agents may respond with THINK+TALK+DONE (speaking) or just DONE (silence).

    Returns a list of per-turn records:
        round, name, persona_type, spoke (bool), word_count (int), text (str)
    """
    configure_tinytroupe_runtime(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )
    _, _, TinyWorld, _ = ensure_tinytroupe_imports()

    world = TinyWorld(
        name=f"BaselineSim_{next(_WORLD_COUNTER)}",
        agents=agents,
        broadcast_if_no_target=True,
    )
    if hasattr(world, "make_everyone_accessible"):
        world.make_everyone_accessible()

    world.broadcast(f"Team meeting scenario:\n{scenario}")
    world.broadcast(friction)

    transcript: list[dict[str, Any]] = []
    n = len(agents)

    for round_no in range(1, rounds + 1):
        if on_progress:
            on_progress(f"  Round {round_no}/{rounds}")

        order = list(range(n))
        random.shuffle(order)

        for idx in order:
            agent = agents[idx]
            name = names[idx]
            persona_type = persona_types[idx]

            prompt = textwrap.dedent(
                f"""
                You are {name}, in a live team meeting.

                SPEAK LIKE A REAL PERSON TALKING, not writing a report.

                Rules for your TALK content:
                - Vary your length freely: sometimes 3-6 words ("That won't work."),
                  sometimes a full thought (20-35 words). Not every turn is a paragraph.
                - Use natural spoken rhythm. Incomplete sentences are fine.
                - Do NOT open with the same phrase you used before.
                - Do NOT use corporate filler: no "action required", "let's align",
                  "I'll volunteer to steward", "going forward", "key deliverable".
                  Say what you mean directly.
                - You are allowed to disagree, push back, or say something isn't working.
                  Real meetings have friction. A blunt challenge is fine.
                - You are also allowed to say something brief or even obvious — real
                  people repeat themselves, ask for clarification, or just confirm they heard.

                If you have something to say RIGHT NOW, respond with:
                - one THINK action (private — your honest internal reaction)
                - one TALK action (what you actually say out loud)
                - one DONE action

                If you would rather stay quiet for now, respond with JUST:
                DONE
                """
            ).strip()

            actions = _safe_listen_and_act(agent, prompt)
            time.sleep(1)

            did_speak = any(
                a.get("action", {}).get("type", "").upper() == "TALK"
                for a in (actions or [])
            )
            text = actions_to_text(actions).strip() if did_speak else ""
            word_count = len(text.split()) if did_speak and text else 0

            entry: dict[str, Any] = {
                "round": round_no,
                "name": name,
                "persona_type": persona_type,
                "spoke": did_speak,
                "word_count": word_count,
                "text": text,
            }
            transcript.append(entry)

            if on_progress:
                first = name.split()[0]
                if persona_type in PRESTIGE_TYPES:
                    group = "P"
                elif persona_type in DOMINANCE_TYPES:
                    group = "D"
                else:
                    group = "N"
                status = f"✓  {word_count:>3}w" if did_speak else "·"
                on_progress(f"    {first:<14} {persona_type} {group}   {status}")

            if did_speak and text:
                world.broadcast(text, source=agent)

    return transcript


def run_vote(
    *,
    agents: list[Any],
    names: list[str],
    persona_types: list[str],
    transcript: list[dict[str, Any]],
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> list[dict[str, Any]]:
    """Ask each agent to vote for who they trust most to lead the team.

    Returns a list of vote records:
        voter_name, voter_type, voted_for_name, voted_for_type, reason
    """
    configure_tinytroupe_runtime(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    name_to_type = dict(zip(names, persona_types))
    votes: list[dict[str, Any]] = []

    for agent, name, persona_type in zip(agents, names, persona_types):
        candidates = [n for n in names if n != name]
        name_list = ", ".join(candidates)

        prompt = textwrap.dedent(
            f"""
            The discussion has ended.

            Based on what you observed, who do you most trust to lead this team?
            You cannot vote for yourself ({name}).
            Candidates: {name_list}

            Respond with one TALK action followed by DONE.
            TALK must be strict JSON with no extra text:
            {{
              "leader": "<candidate name>",
              "reason": "<one sentence citing a specific behavior from the discussion>"
            }}
            """
        ).strip()

        actions = _safe_listen_and_act(agent, prompt)
        raw = actions_to_text(actions).strip()
        parsed = _extract_json(raw)

        leader_name = str(parsed.get("leader", "")).strip()
        reason = str(parsed.get("reason", "")).strip() or "No reason provided."

        if leader_name not in candidates:
            leader_name = _fuzzy_match_name(leader_name, candidates)

        voted_type = name_to_type.get(leader_name, "UNKNOWN")
        votes.append(
            {
                "voter_name": name,
                "voter_type": persona_type,
                "voted_for_name": leader_name,
                "voted_for_type": voted_type,
                "reason": reason,
            }
        )

    return votes


def _fuzzy_match_name(raw: str, candidates: list[str]) -> str:
    raw_lower = raw.lower()
    for candidate in candidates:
        if candidate.split()[0].lower() in raw_lower:
            return candidate
    return random.choice(candidates)
