"""Run a study condition: compose runs, discuss, vote, checkpoint.

One execution path for every step. What used to be "step 1 / step 2 / step 3" is now
a condition from the study definition plus `with_votes` on or off — all aggregation
and reporting happens afterwards in analysis.py from the saved run records.
"""
from __future__ import annotations

import json
import random
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from config import RunConfig
from instrument import BASELINE, POST, Instrument
from persona_store import Participant
from run_record import RunRecord
from study import Condition, Study


class BalancedSampler:
    """Cycles through positions 0..size-1 in random order, ensuring each appears once
    per cycle before any repeats. Eliminates the over-representation bias that arises
    from repeated random.choice calls.

    Yields positions rather than ids so that paired groups can draw the same index,
    and carries its own seeded RNG so run i draws the same cast in every condition.
    """

    def __init__(self, size: int, seed: int = 0) -> None:
        self._size = size
        self._queue: list[int] = []
        self._rng = random.Random(seed)

    def take(self, n: int) -> list[int]:
        drawn: list[int] = []
        while len(drawn) < n:
            if not self._queue:
                self._queue = self._rng.sample(range(self._size), self._size)
            index = self._queue.pop(0)
            # A cycle boundary inside one draw must not seat the same persona twice in
            # one room: 8 neutrals taken 3 at a time run the queue dry mid-draw on run
            # 3, and the fresh cycle can hand back somebody already in this cast. Send
            # the repeat to the back of the new cycle instead. A draw wider than the
            # pool still repeats — it has no other option.
            if index in drawn and len(drawn) < self._size:
                self._queue.append(index)
                continue
            drawn.append(index)
        return drawn


def make_samplers(study: Study) -> dict[str, BalancedSampler]:
    """One sampler per sampled group. A paired group has none — it reuses its source's
    draw, which is the whole point of pairing."""
    return {
        key: BalancedSampler(len(group.ids), study.sampler_seed)
        for key, group in study.groups.items()
        if group.sample is not None and group.pair_with is None
    }


def compose_run(
    study: Study,
    pool: dict[str, Participant],
    samplers: dict[str, BalancedSampler],
) -> list[Participant]:
    """Pick this run's cast: `sample` members per sampled group, all members otherwise.

    A group declaring `pair_with` takes the positions drawn for that group, so bank-paired
    personas (P_i and D_i from one row) appear together instead of being drawn independently.
    """
    from discussion import clone_participants

    picks: dict[str, list[int]] = {}
    chosen: list[str] = []
    for key, group in study.groups.items():
        if group.sample is None:
            chosen.extend(group.ids)
            continue
        source = group.pair_with or key
        if source not in picks:
            picks[source] = samplers[source].take(study.groups[source].sample)
        chosen.extend(group.ids[i] for i in picks[source])
    return clone_participants([pool[pid] for pid in chosen])


def run_condition(
    study: Study,
    condition: Condition,
    config: RunConfig,
    *,
    runs: int,
    rounds: int,
    with_votes: bool = True,
    output_dir: Path,
    on_progress: Callable[[str], None] | None = None,
) -> list[RunRecord]:
    """Execute `runs` independent runs, checkpointing each one.

    Existing checkpoints are reused, so an interrupted study resumes where it stopped.
    Returns one record per run: run_no, members (by group), transcript, votes.
    """
    # Imported here, not at module scope: openai/tinytroupe are only needed to actually
    # run a simulation, so tools and tests can import this module without them installed.
    from discussion import (
        APIQuotaExhausted, clone_participants, run_discussion, run_survey, run_vote,
    )
    from persona_store import load_personas

    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = output_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress(f"Loading personas from {study.personas_dir} ...")
    pool = load_personas(
        study.personas_dir,
        {pid: group.key for group in study.groups.values() for pid in group.ids},
    )

    samplers = make_samplers(study)
    records: list[RunRecord] = []

    for run_no in range(1, runs + 1):
        # Drawn before the checkpoint check: the sampler must advance once per run
        # number either way, or a resumed condition re-draws run 1's cast and loses
        # both the balanced cycle and the alignment with the other condition.
        cast = compose_run(study, pool, samplers)
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{runs}  [checkpoint]")
            records.append(RunRecord.from_dict(json.loads(ckpt.read_text(encoding="utf-8"))))
            continue

        members: dict[str, list[str]] = {}
        for p in cast:
            members.setdefault(p.group, []).append(p.persona_id)
        progress(f"\nRun {run_no}/{runs}  ({members})")

        try:
            # Baseline goes to a throwaway fork: the agents who actually discuss must never
            # have seen the items, or the battery primes the very needs we then measure.
            measures: dict[str, dict[str, Any]] = {"baseline": {}, "post": {}}
            for inst in study.instruments_at(BASELINE):
                progress(f"  baseline {inst.key}")
                measures["baseline"][inst.key] = run_survey(
                    participants=clone_participants(cast),
                    instrument=inst,
                    model=config.survey,
                    on_progress=progress,
                )

            transcript = run_discussion(
                participants=cast,
                scenario=condition.scenario,
                friction=condition.friction,
                rounds=rounds,
                model=config.discussion,
                on_progress=progress,
            )

            # Each post measure branches from the same post-discussion state, so none of
            # them primes another, yet all of them reflect the discussion that happened.
            for inst in study.instruments_at(POST):
                progress(f"  post {inst.key}")
                measures["post"][inst.key] = run_survey(
                    participants=clone_participants(cast),
                    instrument=inst,
                    model=config.survey,
                    rate_groups=tuple(condition.contrast),
                    on_progress=progress,
                )

            # Vote last, on the original cast — nothing downstream can be primed by it.
            votes = (
                run_vote(
                    participants=cast,
                    question=study.vote_prompt,
                    model=config.vote,
                )
                if with_votes
                else []
            )
        except APIQuotaExhausted as exc:
            progress(f"\n[FATAL] {exc}")
            progress(
                f"  Stopping after {len(records)} completed runs. "
                "Checkpoints are saved — resume with the same command when quota is restored."
            )
            break

        record = RunRecord(
            run_no=run_no,
            condition=condition.key,
            members_by_group=members,
            transcript=transcript,
            votes=votes,
            measures=measures,
        )
        records.append(record)
        ckpt.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return records


def load_records(output_dir: Path) -> list[RunRecord]:
    """Read completed run checkpoints without running anything."""
    ckpt_dir = output_dir / "checkpoints"
    if not ckpt_dir.exists():
        raise SystemExit(f"No checkpoints found at {ckpt_dir}")
    records = [
        RunRecord.from_dict(json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(ckpt_dir.glob("run_*.json"))
    ]
    if not records:
        raise SystemExit(f"No checkpoint files in {ckpt_dir}")
    return records


def run_measure_check(
    study: Study,
    config: RunConfig,
    instruments: tuple[Instrument, ...],
    *,
    on_progress: Callable[[str], None] | None = None,
) -> RunRecord:
    """Administer each instrument twice per persona, nothing else.

    Cheap by design: no discussion, no votes. The two administrations are stored as
    baseline and post of a single run record so the ordinary needs analysis applies —
    with no discussion between them, the "change" is measurement noise, which is
    exactly the test-retest reliability we want to see before paying for a study.

    Only instruments that ask about the respondent or about the leader category can be
    checked this way. One that rates a specific person cannot: with no meeting, there is
    nobody to rate.
    """
    from discussion import clone_participants, run_survey
    from persona_store import load_personas

    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    if not instruments:
        raise SystemExit(f"Study '{study.name}' has no instrument that can be checked.")

    pool = load_personas(
        study.personas_dir,
        {pid: g.key for g in study.groups.values() for pid in g.ids},
    )

    measures: dict[str, dict[str, Any]] = {BASELINE: {}, POST: {}}
    for instrument in instruments:
        # Every persona answers, not just the instrument's usual targets — a check of the
        # scale itself should cover the whole cast.
        wide = replace(instrument, targets=())
        for pass_no, timing in ((1, BASELINE), (2, POST)):
            progress(f"  {instrument.key}: administration {pass_no}/2")
            measures[timing][instrument.key] = run_survey(
                participants=clone_participants(list(pool.values())),
                instrument=wide,
                model=config.survey,
                on_progress=progress,
            )

    return RunRecord(
        run_no=1,
        condition="measure_check",
        members_by_group={},
        transcript=[],
        votes=[],
        measures=measures,
    )
