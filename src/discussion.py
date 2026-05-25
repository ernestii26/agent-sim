from __future__ import annotations

import json
import random
import textwrap
from itertools import count
from typing import Any

import openai

from runtime import actions_to_text, configure_tinytroupe_runtime, ensure_tinytroupe_imports

_WORLD_COUNTER = count(1)

SCENARIO = (
    "Your team has been missing key deliverables for two consecutive quarters. "
    "Leadership has granted your group full autonomy to diagnose the root cause "
    "and commit to one concrete change. You must reach a shared decision that "
    "everyone in the room can commit to implementing."
)


def _safe_listen_and_act(agent: Any, prompt: str) -> list[dict[str, Any]]:
    try:
        result = agent.listen_and_act(
            prompt,
            return_actions=True,
            communication_display=False,
        )
        return result or []
    except (TypeError, AttributeError) as exc:
        # TinyTroupe bug: send_message returned None (e.g. after 429 exhaustion)
        print(f"  [warn] listen_and_act failed ({type(exc).__name__}: {exc}) — treating as silence")
        return []
    except openai.OpenAIError as exc:
        # LengthFinishReasonError, RateLimitError, APIStatusError, etc.
        print(f"  [warn] OpenAI error ({type(exc).__name__}: {exc}) — treating as silence")
        return []
    except Exception as exc:
        print(f"  [warn] Unexpected error ({type(exc).__name__}: {exc}) — treating as silence")
        return []


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
    mbti_types: list[str],
    scenario: str,
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
        round, name, mbti_type, spoke (bool), word_count (int), text (str)
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
            mbti_type = mbti_types[idx]

            prompt = textwrap.dedent(
                f"""
                You are {name}, in a team meeting.

                If you have something meaningful to add RIGHT NOW, respond with:
                - one THINK action (private, not spoken aloud)
                - one TALK action in <= 40 words
                - one DONE action

                If you would rather listen for now, respond with JUST:
                DONE
                """
            ).strip()

            actions = _safe_listen_and_act(agent, prompt)

            did_speak = any(
                a.get("action", {}).get("type", "").upper() == "TALK"
                for a in (actions or [])
            )
            text = actions_to_text(actions).strip() if did_speak else ""
            word_count = len(text.split()) if did_speak and text else 0

            entry: dict[str, Any] = {
                "round": round_no,
                "name": name,
                "mbti_type": mbti_type,
                "spoke": did_speak,
                "word_count": word_count,
                "text": text,
            }
            transcript.append(entry)

            if on_progress:
                first = name.split()[0]
                group = "E" if mbti_type.startswith("E") else "I"
                status = f"✓  {word_count:>3}w" if did_speak else "·"
                on_progress(f"    {first:<14} {mbti_type} {group}   {status}")

            if did_speak and text:
                world.broadcast(text, source=agent)

    return transcript


def run_vote(
    *,
    agents: list[Any],
    names: list[str],
    mbti_types: list[str],
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

    name_to_type = dict(zip(names, mbti_types))
    votes: list[dict[str, Any]] = []

    for agent, name, mbti_type in zip(agents, names, mbti_types):
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
                "voter_type": mbti_type,
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
