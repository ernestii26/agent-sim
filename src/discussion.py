"""Run one discussion + one vote round. Theme-free: scenario text comes from the study."""
from __future__ import annotations

import copy
import json
import random
import textwrap
import time
from itertools import count
from typing import Any

from config import ModelSettings
from instrument import ABOUT_EACH_CANDIDATE, ABOUT_PROTOTYPE, ABOUT_SELF, Instrument
from persona_store import Participant
from study import Task
from runtime import actions_to_text, configure_tinytroupe_runtime, ensure_tinytroupe_imports

_WORLD_COUNTER = count(1)
_MAX_CONSECUTIVE_FAILURES = 5


class APIQuotaExhausted(RuntimeError):
    """Raised when the API appears to have no remaining quota (billing exhausted)."""


def _api_error_types() -> tuple[type[BaseException], ...]:
    """P1 + P4 (docs/ERRORS_AND_FIXES.md): TinyTroupe returns None on exhausted retries
    (TypeError/AttributeError) and LengthFinishReasonError arrives as an OpenAIError.
    Imported lazily so this module stays importable where openai is not installed."""
    try:
        import openai
    except ImportError:
        return (TypeError, AttributeError)
    return (TypeError, AttributeError, openai.OpenAIError)


class AgentTransport:
    """The one real adapter: turn a prompt into agent actions, absorbing API failure.

    The consecutive-failure counter lives here rather than on the module so its lifetime
    is one run: scattered failures across two conditions in the same process must not add
    up into a spurious APIQuotaExhausted abort.
    """

    def __init__(self, retries: int = 3) -> None:
        self.retries = retries
        self.consecutive_failures = 0

    def actions(self, agent: Any, prompt: str) -> list[dict[str, Any]]:
        errors = _api_error_types()
        for attempt in range(1, self.retries + 1):
            try:
                result = agent.listen_and_act(
                    prompt,
                    return_actions=True,
                    communication_display=False,
                )
                self.consecutive_failures = 0
                return result or []
            except errors as exc:
                if attempt < self.retries:
                    delay = 2 ** attempt
                    print(f"  [warn] {type(exc).__name__} (attempt {attempt}/{self.retries}, retrying in {delay}s): {exc}")
                    time.sleep(delay)
                else:
                    self.consecutive_failures += 1
                    print(f"  [warn] {type(exc).__name__} after {self.retries} attempts ({exc}) — treating as silence")
                    self._check_quota()
                    return []
            except Exception as exc:
                print(f"  [warn] Unexpected error ({type(exc).__name__}: {exc}) — treating as silence")
                return []
        return []

    def __call__(self, agent: Any, prompt: str) -> str:
        """Ask the agent and give back plain text — the seam the survey parser talks to."""
        return actions_to_text(self.actions(agent, prompt))

    def _check_quota(self) -> None:
        # A rate-limited run degrades into fake silence, and speech rate is a dependent
        # variable — stop with checkpoints saved rather than publish 429s as data.
        if self.consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            raise APIQuotaExhausted(
                f"API failed {self.consecutive_failures} times in a row — "
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


def clone_participants(participants: list[Participant]) -> list[Participant]:
    """Fresh copies for one run, so state never leaks between runs."""
    return [
        Participant(
            agent=_clone_agent(p.agent), persona_id=p.persona_id, name=p.name, group=p.group
        )
        for p in participants
    ]


# Live wiring: references to the world and to peers. Stripped from the original
# *before* deepcopy, not from the copy afterwards — a TinyWorld reaches a
# _thread.RLock, and an agent still attached to one cannot be deep-copied at all.
_LIVE_WIRING = (
    "environment",
    "current_messages",
    "_actions_buffer",
    "_accessible_agents",
    "_displayed_communications_buffer",
)


def _clone_agent(person: Any) -> Any:
    """A copy carrying the agent's memory but none of its live wiring.

    This used to deep-copy first and strip afterwards, with a bare `except: return
    person`. After a discussion that combination always fired — the agent still held
    its TinyWorld, deepcopy hit the world's RLock, and the caller was silently handed
    the *original* agent. Post-discussion surveys then wrote their items into the very
    agent that voted next. A copy that cannot be made is now an error, never a
    contaminated measurement.
    """
    saved = {attr: getattr(person, attr) for attr in _LIVE_WIRING if hasattr(person, attr)}
    for attr in saved:
        setattr(person, attr, None if attr == "environment" else [])
    try:
        cloned = copy.deepcopy(person)
    finally:
        for attr, value in saved.items():
            setattr(person, attr, value)

    for counter in ("actions_count", "stimuli_count", "_current_episode_event_count"):
        if hasattr(cloned, counter):
            setattr(cloned, counter, 0)
    return cloned


TURN_PROMPT = """
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


def run_discussion(
    *,
    participants: list[Participant],
    scenario: str,
    friction: str,
    rounds: int,
    model: ModelSettings,
    private: dict[str, list[str]] | None = None,
    on_progress: Any = None,
) -> list[dict[str, Any]]:
    """Run a multi-round discussion with optional silence.

    Each round, invitation order is independently shuffled to prevent position bias.
    Agents may respond with THINK+TALK+DONE (speaking) or just DONE (silence).

    `private` maps persona id to facts only that agent knows. They are delivered before
    the first round and never broadcast, which is what makes the room a hidden profile:
    the answer exists in the union of what the group holds and in no single member.

    Returns a list of per-turn records:
        round, name, persona_id, group, spoke (bool), word_count (int), text (str)
    """
    configure_tinytroupe_runtime(model)
    _, _, TinyWorld, _ = ensure_tinytroupe_imports()

    world = TinyWorld(
        name=f"Sim_{next(_WORLD_COUNTER)}",
        agents=[p.agent for p in participants],
        broadcast_if_no_target=True,
    )
    if hasattr(world, "make_everyone_accessible"):
        world.make_everyone_accessible()

    world.broadcast(f"Team meeting scenario:\n{scenario}")
    if friction:
        world.broadcast(friction)

    for participant in participants:
        facts = (private or {}).get(participant.persona_id)
        if not facts:
            continue
        listing = "\n".join(f"- {fact}" for fact in facts)
        # Said to one agent only. The instruction to share is deliberate: without it a
        # null would be ambiguous between "leadership did not help pooling" and "nobody
        # realised the facts were theirs alone to contribute".
        participant.agent.listen(
            "Only you know the following. No one else in the meeting has been told:\n"
            f"{listing}\n\n"
            "Others hold different pieces. Decide for yourself what to raise and when.",
            communication_display=False,
        )

    transcript: list[dict[str, Any]] = []
    transport = AgentTransport()

    for round_no in range(1, rounds + 1):
        if on_progress:
            on_progress(f"  Round {round_no}/{rounds}")

        for participant in random.sample(participants, len(participants)):
            actions = transport.actions(
                participant.agent, TURN_PROMPT.format(name=participant.name).strip()
            )
            time.sleep(1)

            did_speak = any(
                a.get("action", {}).get("type", "").upper() == "TALK"
                for a in (actions or [])
            )
            text = actions_to_text(actions).strip() if did_speak else ""
            word_count = len(text.split()) if text else 0

            transcript.append(
                {
                    "round": round_no,
                    "name": participant.name,
                    "persona_id": participant.persona_id,
                    "group": participant.group,
                    "spoke": did_speak,
                    "word_count": word_count,
                    "text": text,
                }
            )

            if on_progress:
                status = f"✓  {word_count:>3}w" if did_speak else "·"
                first = participant.name.split()[0]
                on_progress(
                    f"    {first:<14} {participant.persona_id:<4} {participant.group:<3} {status}"
                )

            if did_speak and text:
                world.broadcast(text, source=participant.agent)

    # Tear the world down. Every agent holds a reference to it and it holds every
    # agent, so leaving it attached both defeats cloning (see _clone_agent) and keeps
    # one world per run alive in TinyWorld's registry for the length of a study.
    for participant in participants:
        if hasattr(participant.agent, "environment"):
            participant.agent.environment = None
    TinyWorld.all_environments.pop(world.name, None)

    return transcript


def run_vote(
    *,
    participants: list[Participant],
    question: str,
    model: ModelSettings,
) -> list[dict[str, Any]]:
    """Ask each agent the study's vote question about the others.

    Returns a list of vote records:
        voter_id, voter_group, voted_for_name, voted_for_id, voted_for_group, reason
    """
    configure_tinytroupe_runtime(model)

    by_name = {p.name: p for p in participants}
    votes: list[dict[str, Any]] = []
    ask = AgentTransport()

    for participant in participants:
        candidates = [p.name for p in participants if p.name != participant.name]

        prompt = textwrap.dedent(
            f"""
            The discussion has ended.

            {question}
            You cannot vote for yourself ({participant.name}).
            Candidates: {", ".join(candidates)}

            Respond with one TALK action followed by DONE.
            TALK must be strict JSON with no extra text:
            {{
              "choice": "<candidate name>",
              "reason": "<one sentence citing a specific behavior from the discussion>"
            }}
            """
        ).strip()

        parsed = _extract_json(ask(participant.agent, prompt))
        choice = str(parsed.get("choice") or parsed.get("leader") or "").strip()
        reason = str(parsed.get("reason", "")).strip() or "No reason provided."

        if choice not in candidates:
            choice = _fuzzy_match_name(choice, candidates)
        chosen = by_name[choice]

        votes.append(
            {
                "voter_id": participant.persona_id,
                "voter_group": participant.group,
                "voted_for_name": chosen.name,
                "voted_for_id": chosen.persona_id,
                "voted_for_group": chosen.group,
                "reason": reason,
            }
        )

    return votes


def run_poll(
    *,
    participants: list[Participant],
    task: Task,
    model: ModelSettings,
) -> list[dict[str, Any]]:
    """Ask each agent which option the group should take, and score it.

    Separate from the leadership vote on purpose: this measures whether the discussion
    reached the right answer, which is the one thing the endorsement result cannot say
    on its own. A group can back a leader confidently and still decide wrongly.

    Returns: persona_id, group, choice, correct (bool), reason
    """
    configure_tinytroupe_runtime(model)

    answers: list[dict[str, Any]] = []
    ask = AgentTransport()
    options = list(task.options)

    for participant in participants:
        prompt = textwrap.dedent(
            f"""
            The discussion has ended. You must now commit to an answer.

            Which option should the group take? Answer for yourself, even if
            the group did not converge.
            Options: {", ".join(options)}

            Respond with one TALK action followed by DONE.
            TALK must be strict JSON with no extra text:
            {{
              "choice": "<one option, copied exactly>",
              "reason": "<one sentence saying what decided it>"
            }}
            """
        ).strip()

        parsed = _extract_json(ask(participant.agent, prompt))
        choice = str(parsed.get("choice") or "").strip()
        if choice not in options:
            choice = _fuzzy_match_name(choice, options)
        answers.append(
            {
                "persona_id": participant.persona_id,
                "group": participant.group,
                "choice": choice,
                "correct": choice == task.correct,
                "reason": str(parsed.get("reason", "")).strip() or "No reason provided.",
            }
        )

    return answers


def rated_by(
    participants: list[Participant], rater: Participant, rate_groups: tuple[str, ...] = ()
) -> list[Participant]:
    """Who a rater rates on an about=each_candidate instrument.

    `rate_groups` narrows it to the candidates — the groups being contrasted. Everyone
    else in the room is someone no analysis asks about, and each rating is its own API
    call carrying the whole transcript, so rating them is the most expensive way in the
    design to collect data nothing reads. Empty means everyone, which is what a study
    with no contrast gets.
    """
    return [
        p for p in participants
        if p.persona_id != rater.persona_id and (not rate_groups or p.group in rate_groups)
    ]


def run_survey(
    *,
    participants: list[Participant],
    instrument: Instrument,
    model: ModelSettings,
    rate_groups: tuple[str, ...] = (),
    on_progress: Any = None,
) -> dict[str, Any]:
    """Administer `instrument` to every participant whose group it targets.

    The whole battery goes out in ONE call per administration, with item order shuffled
    per respondent (the FFNI was validated with "randomly presented items"). Ratings
    outside the scale, or missing items, are recorded as null and flagged — never
    imputed, so a parse failure reads as missing data instead of fake moderation.

    Returns {persona_id: {item_id: rating|None, "_meta": {...}}}, or for
    about="each_candidate", {persona_id: {candidate_id: {...}}}.
    """
    configure_tinytroupe_runtime(model)

    respondents = [
        p for p in participants if not instrument.targets or p.group in instrument.targets
    ]
    results: dict[str, Any] = {}
    ask = AgentTransport()

    for participant in respondents:
        if instrument.about == ABOUT_EACH_CANDIDATE:
            results[participant.persona_id] = {
                other.persona_id: _administer(participant, instrument, target=other, ask=ask)
                for other in rated_by(participants, participant, rate_groups)
            }
        else:
            results[participant.persona_id] = _administer(
                participant, instrument, target=None, ask=ask
            )

        if on_progress:
            on_progress(f"    {participant.persona_id:<4} {instrument.key} done")

    return results


def _administer(
    participant: Participant,
    instrument: Instrument,
    *,
    target: Participant | None,
    ask: Any,
) -> dict[str, Any]:
    """One administration = one API call, with a single retry on an unusable response.

    `ask(agent, prompt) -> str` is the transport seam, so this parser can be driven from a
    test with scripted replies instead of a live agent.
    """
    items = instrument.items
    # Shuffled per respondent, not per administration. Items must be randomly presented
    # (the FFNI was validated that way) and position bias must not accumulate across the
    # sample, but re-ordering the SAME person between baseline and post puts order
    # sensitivity straight into the pre-post difference — which is H3's dependent
    # variable and H6's mediator. Keyed on the persona and the instrument, so one
    # respondent sees one order throughout and the orders still differ between people.
    order = random.Random(f"{instrument.key}:{participant.persona_id}").sample(
        items, len(items)
    )
    low, high = instrument.scale
    low_label, high_label = instrument.anchors

    if instrument.about == ABOUT_SELF:
        frame = f"You are {participant.name}. Answer about yourself, honestly."
    elif instrument.about == ABOUT_PROTOTYPE:
        frame = (
            f"You are {participant.name}. Answer about leaders in general — not about any "
            "specific person in this meeting."
        )
    else:
        frame = f"You are {participant.name}. Answer about {target.name}."  # type: ignore[union-attr]

    listing = "\n".join(f'  "{item_id}": {text}' for item_id, _, text in order)
    prompt = textwrap.dedent(
        f"""
        {frame}

        {instrument.instructions}

        Rate each statement from {low} to {high}, where {low} = {low_label} and
        {high} = {high_label}. Use the full range — not every statement deserves the
        same number.

        {listing}

        Respond with one TALK action followed by DONE.
        TALK must be strict JSON with no extra text: an object mapping every id above
        to its integer rating, and nothing else.
        """
    ).strip()

    for attempt in (1, 2):
        # The retry must not repeat the prompt verbatim. TinyTroupe suppresses an action
        # too similar to the agent's previous one, replacing it with DONE -- and rating a
        # second candidate right after the first is exactly that case, so the identical
        # re-ask was guaranteed to be suppressed again. Seen on gpt-4o-mini, where five of
        # six second ratings came back empty; gpt-4.1 answered 480/480, which is why it
        # never surfaced before.
        retry_note = (
            ""
            if attempt == 1
            else "\n\nYour previous reply could not be read. Send the JSON object again, "
                 "on its own, even if your ratings are the same as before."
        )
        parsed = _extract_json(ask(participant.agent, prompt + retry_note))
        responses: dict[str, Any] = {}
        for item_id, _, _ in items:
            value = parsed.get(item_id)
            responses[item_id] = value if instrument.is_valid_rating(value) else None
        answered = sum(1 for v in responses.values() if v is not None)
        if answered == len(items):
            responses["_meta"] = {"attempts": attempt, "answered": answered, "complete": True}
            return responses
        if attempt == 2:
            print(
                f"  [warn] {participant.persona_id} answered {answered}/{len(items)} items of "
                f"{instrument.key} after 2 attempts — missing items recorded as null"
            )
            responses["_meta"] = {"attempts": attempt, "answered": answered, "complete": False}
            return responses
    return {}


def _fuzzy_match_name(raw: str, candidates: list[str]) -> str:
    raw_lower = raw.lower()
    for candidate in candidates:
        if candidate.split()[0].lower() in raw_lower:
            return candidate
    return random.choice(candidates)
