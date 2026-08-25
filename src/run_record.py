"""One simulation run's output — the thing checkpoints hold and every report reads.

The on-disk shape is fixed: {run_no, condition, members, transcript, votes, measures}.
Readers ask questions here instead of walking that dict, which is also where the
tolerance for pre-instrument checkpoints (no "measures" key) lives — see `responses`.
"""
from __future__ import annotations

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_no": self.run_no,
            "condition": self.condition,
            "members": self.members_by_group,
            "transcript": self.transcript,
            "votes": self.votes,
            "measures": self.measures,
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
        )

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
        return {
            pid: subscale_scores(answers, instrument)
            for pid, answers in self.responses(timing, instrument).items()
        }

    def ratings(self, instrument: Instrument) -> dict[str, dict[str, float]]:
        """{rater_id: {target_id: mean rating}} for an about=each_candidate instrument."""
        return {
            rater: {
                target: mean(list(subscale_scores(answers, instrument).values()))
                for target, answers in by_target.items()
            }
            for rater, by_target in self.responses(POST, instrument).items()
        }
