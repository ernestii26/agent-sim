"""One simulation run's output — the thing checkpoints hold and every report reads.

The on-disk shape is fixed: {run_no, condition, members, transcript, votes, measures,
instruments}.
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
    # {instrument key: fingerprint} for the wording this run was collected with. Absent
    # in checkpoints written before 2026-09-07; the item-id check below covers those.
    instruments: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_no": self.run_no,
            "condition": self.condition,
            "members": self.members_by_group,
            "transcript": self.transcript,
            "votes": self.votes,
            "measures": self.measures,
            "instruments": self.instruments,
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
