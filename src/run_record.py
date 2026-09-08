"""One simulation run's output — the thing checkpoints hold and every report reads.

The on-disk shape is fixed: {run_no, condition, members, transcript, votes, measures,
instruments}.
Readers ask questions here instead of walking that dict, which is also where the
tolerance for pre-instrument checkpoints (no "measures" key) lives — see `responses`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from instrument import POST, Instrument, subscale_scores
from stats import mean


@dataclass
class RunRecord:
    run_no: int
    condition: str
    members_by_group: dict[str, list[str]]
    transcript: list[dict[str, Any]]
    votes: list[dict[str, Any]]
    measures: dict[str, dict[str, Any]] = field(default_factory=dict)
    # {instrument key: fingerprint} for the wording this run was collected with. Absent
    # in checkpoints written before 2026-09-07; the item-id check below covers those.
    instruments: dict[str, str] = field(default_factory=dict)
    # The hidden-profile task this run drew, and who held which private fact. Empty for
    # runs from a study whose conditions carry a fixed `scenario` instead of a pool.
    task: dict[str, Any] = field(default_factory=dict)
    # One committed answer per participant: persona_id, group, choice, correct, reason.
    answers: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_no": self.run_no,
            "condition": self.condition,
            "members": self.members_by_group,
            "transcript": self.transcript,
            "votes": self.votes,
            "measures": self.measures,
            "instruments": self.instruments,
            "task": self.task,
            "answers": self.answers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunRecord":
        return cls(
            run_no=data["run_no"],
            condition=data.get("condition", ""),
            members_by_group=data.get("members", {}),
            transcript=data.get("transcript", []),
            votes=data.get("votes", []),
            measures=data.get("measures", {}),
            instruments=data.get("instruments", {}),
            task=data.get("task", {}),
            answers=data.get("answers", []),
        )

    def correct_rate(self, group: str | None = None) -> float | None:
        """Share of participants who committed to the task's correct answer.

        None when the run carries no task, which is every run collected before scenarios
        were drawn — callers must skip those rather than score them as zero.
        """
        rows = [a for a in self.answers if group is None or a["group"] == group]
        if not rows:
            return None
        return sum(1 for a in rows if a["correct"]) / len(rows)

    def hidden_facts_raised(self) -> tuple[int, int]:
        """(facts that surfaced in the transcript, facts dealt out).

        A fact counts as raised when a substantial run of its words appears in something
        someone said. Deliberately crude: it is a floor on pooling, not a transcript
        parser, and the comparison across conditions is what carries the meaning.
        """
        shares = self.task.get("shares") or {}
        facts = [fact for held in shares.values() for fact in held]
        if not facts:
            return (0, 0)
        spoken = " ".join(t["text"] for t in self.transcript if t.get("spoke")).lower()
        raised = sum(1 for fact in facts if _echoes(fact, spoken))
        return (raised, len(facts))

    # -- discussion -------------------------------------------------------- #

    def turns(self, group: str | None = None) -> list[dict[str, Any]]:
        if group is None:
            return self.transcript
        return [t for t in self.transcript if t["group"] == group]

    def votes_for(self, group: str, *, by: tuple[str, ...] | None = None) -> int:
        """Votes received by `group`, optionally counting only voters in `by`.

        The contrasted groups are candidates in their own contest, so restricting the
        electorate to everyone else is what keeps a rival's ballot out of the DV.
        """
        return sum(
            1 for v in self.votes
            if v["voted_for_group"] == group and (by is None or v["voter_group"] in by)
        )

    def vote_of(self, voter_id: str) -> str | None:
        """The group this persona endorsed, or None if it cast no usable vote."""
        return next((v["voted_for_group"] for v in self.votes if v["voter_id"] == voter_id), None)

    def members(self, group: str) -> list[str]:
        return self.members_by_group.get(group, [])

    # -- instruments ------------------------------------------------------- #

    def responses(self, timing: str, instrument: Instrument) -> dict[str, Any]:
        """Raw answers, or {} for checkpoints written before instruments existed."""
        return self.measures.get(timing, {}).get(instrument.key, {})

    def needs(self, timing: str, instrument: Instrument) -> dict[str, dict[str, float]]:
        """{persona_id: {subscale: mean}} for a self/prototype instrument."""
        answered = self.responses(timing, instrument)
        self._reject_foreign_answers(answered, instrument, timing)
        return {pid: subscale_scores(a, instrument) for pid, a in answered.items()}

    def _reject_foreign_answers(
        self, answered: dict[str, Any], instrument: Instrument, timing: str
    ) -> None:
        """Refuse to score answers that were given to a different version of a scale.

        A stored fingerprint that disagrees is decisive. Without one, an item id the
        instrument does not define is the same signal: these answers came from a scale
        that had questions this one does not. Either way the overlap would be scored
        against the wrong wording, which is worse than missing data because it looks
        like data.
        """
        stored = self.instruments.get(instrument.key)
        if stored and stored != instrument.fingerprint:
            raise SystemExit(
                f"{timing}/{instrument.key}: run {self.run_no} was collected with "
                f"instrument {stored}, and {instrument.fingerprint} is loaded. The item "
                f"ids overlap but the wording differs, so scoring these together would "
                f"be silently wrong. Re-run the condition, or load the instrument the "
                f"data was collected with."
            )
        known = {item_id for item_id, _, _ in instrument.items}
        for pid, a in answered.items():
            unknown = {k for k in a if k != "_meta"} - known
            if unknown:
                raise SystemExit(
                    f"{timing}/{instrument.key}: run {self.run_no}, persona {pid} answered "
                    f"{len(unknown)} item(s) this instrument does not define "
                    f"({', '.join(sorted(unknown)[:4])}...). These answers belong to a "
                    f"different version of the scale; scoring the overlap would be "
                    f"silently wrong."
                )

    def ratings(self, instrument: Instrument) -> dict[str, dict[str, float]]:
        """{rater_id: {target_id: mean rating}} for an about=each_candidate instrument."""
        return {
            rater: {
                target: mean(list(subscale_scores(answers, instrument).values()))
                for target, answers in by_target.items()
            }
            for rater, by_target in self.responses(POST, instrument).items()
        }


def _echoes(fact: str, spoken: str) -> bool:
    """True when any 5-word run of `fact` reappears in `spoken`.

    Five is long enough that ordinary shared vocabulary ("the supply truck") does not
    trigger it, and short enough to survive an agent paraphrasing the rest of the
    sentence around the part that matters.
    """
    words = [w for w in re.findall(r"[a-z0-9]+", fact.lower()) if w]
    if len(words) < 5:
        return " ".join(words) in spoken
    return any(
        " ".join(words[i:i + 5]) in spoken for i in range(len(words) - 4)
    )
