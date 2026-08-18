"""Run a study condition: compose runs, discuss, vote, checkpoint.

One execution path for every step. What used to be "step 1 / step 2 / step 3" is now
a condition from the study definition plus `with_votes` on or off — all aggregation
and reporting happens afterwards in reporting.py from the saved run records.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Callable

from config import RunConfig
from instrument import BASELINE, POST
from persona_store import Participant
from study import Condition, Study


class BalancedSampler:
    """Cycles through a pool in random order, ensuring each item appears once
    per cycle before any item repeats. Eliminates the over-representation bias
    that arises from repeated random.choice calls."""

    def __init__(self, pool: list[str]) -> None:
        self._pool = list(pool)
        self._queue: list[str] = []

    def take(self, n: int) -> list[str]:
        drawn: list[str] = []
        while len(drawn) < n:
            if not self._queue:
                self._queue = random.sample(self._pool, len(self._pool))
            drawn.append(self._queue.pop(0))
        return drawn


def make_samplers(study: Study) -> dict[str, BalancedSampler]:
    return {
        key: BalancedSampler(list(group.ids))
        for key, group in study.groups.items()
        if group.sample is not None
    }


def compose_run(
    study: Study,
    pool: dict[str, Participant],
    samplers: dict[str, BalancedSampler],
) -> list[Participant]:
    """Pick this run's cast: `sample` members per sampled group, all members otherwise."""
    from discussion import clone_participants

    chosen: list[str] = []
    for key, group in study.groups.items():
        if group.sample is None:
            chosen.extend(group.ids)
        else:
            chosen.extend(samplers[key].take(group.sample))
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
) -> list[dict[str, Any]]:
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
    records: list[dict[str, Any]] = []

    for run_no in range(1, runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{runs}  [checkpoint]")
            records.append(json.loads(ckpt.read_text(encoding="utf-8")))
            continue

        cast = compose_run(study, pool, samplers)
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

        record = {
            "run_no": run_no,
            "condition": condition.key,
            "members": members,
            "transcript": transcript,
            "votes": votes,
            "measures": measures,
        }
        records.append(record)
        ckpt.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return records


def load_records(output_dir: Path) -> list[dict[str, Any]]:
    """Read completed run checkpoints without running anything."""
    ckpt_dir = output_dir / "checkpoints"
    if not ckpt_dir.exists():
        raise SystemExit(f"No checkpoints found at {ckpt_dir}")
    records = [
        json.loads(p.read_text(encoding="utf-8")) for p in sorted(ckpt_dir.glob("run_*.json"))
    ]
    if not records:
        raise SystemExit(f"No checkpoint files in {ckpt_dir}")
    return records
