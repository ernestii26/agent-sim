"""Run a study condition: compose runs, discuss, vote, checkpoint.

One execution path for every step. What used to be "step 1 / step 2 / step 3" is now
a condition from the study definition plus `with_votes` on or off — all aggregation
and reporting happens afterwards in analysis.py from the saved run records.
"""
from __future__ import annotations

import json
import os
import random
import socket
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from config import RunConfig
from instrument import BASELINE, POST, Instrument
from persona_store import Participant
from run_record import RunRecord
from study import Condition, Study, Task


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
        """n pool indices, cycling through a fresh shuffle of the whole pool before any repeats."""
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


def check_no_reuse(study: Study, runs: int) -> None:
    """Refuse a run count that would seat a sampled persona twice.

    Personas are built as exactly one cycle (tools/build_personas.py), so every run is a
    fresh draw from the bank. Past the cycle the sampler starts over and the same people
    come back, which is a different design, and nothing downstream would say so.
    """
    for key, group in study.groups.items():
        if group.sample is not None and group.pair_with is None and runs * group.sample > len(group.ids):
            raise SystemExit(
                f"{runs} runs need {runs * group.sample} '{key}' personas, the study has "
                f"{len(group.ids)}; rebuild with tools/build_personas.py --runs {runs}"
            )


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
    from persona_store import load_personas

    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    check_no_reuse(study, runs)
    ckpt_dir = output_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress(f"Loading personas from {study.personas_dir} ...")
    pool = load_personas(
        study.personas_dir,
        {pid: group.key for group in study.groups.values() for pid in group.ids},
    )

    samplers = make_samplers(study)
    # Tasks cycle the same way casts do, so 40 runs spread evenly over the pool instead
    # of landing on whichever vignette repeated draws happened to favour.
    task_sampler = (
        BalancedSampler(len(condition.pool), study.sampler_seed) if condition.pool else None
    )
    records: list[RunRecord] = []

    for run_no in range(1, runs + 1):
        # Drawn before the checkpoint check: the sampler must advance once per run
        # number either way, or a resumed condition re-draws run 1's cast and loses
        # both the balanced cycle and the alignment with the other condition.
        cast = compose_run(study, pool, samplers)
        # Same reason as the cast: advance once per run number whether or not the run is
        # replayed from a checkpoint.
        task = condition.pool[task_sampler.take(1)[0]] if task_sampler else None
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            records.append(_replay(ckpt, condition, run_no, runs, progress))
            continue
        # Several processes may work one condition (run.py run --parallel). Each draws
        # every cast in order, so run i's cast never depends on who executes it; the lock
        # decides who does. Re-checked after claiming: a peer may have finished the run
        # and released its lock between the check above and the claim.
        lock = _claim(ckpt)
        if lock is None:
            progress(f"\nRun {run_no}/{runs}  [taken by another worker]")
            continue
        try:
            if ckpt.exists():
                records.append(_replay(ckpt, condition, run_no, runs, progress))
                continue
            record = _execute_run(
                study, condition, config, cast, task, run_no, runs,
                rounds=rounds, with_votes=with_votes, progress=progress,
            )
            if record is None:
                progress(
                    f"  Stopping after {len(records)} completed runs. "
                    "Checkpoints are saved — resume with the same command when quota is restored."
                )
                break
            records.append(record)
            _write_atomic(ckpt, json.dumps(record.to_dict(), ensure_ascii=False, indent=2))
        finally:
            lock.unlink(missing_ok=True)

    return records


def _replay(
    ckpt: Path, condition: Condition, run_no: int, runs: int, progress: Callable[[str], None]
) -> RunRecord:
    """A finished run read back from its checkpoint."""
    progress(f"\nRun {run_no}/{runs}  [checkpoint]")
    replayed = RunRecord.from_dict(json.loads(ckpt.read_text(encoding="utf-8")))
    _reject_foreign_scenario(replayed, condition, ckpt)
    return replayed


def _execute_run(
    study: Study,
    condition: Condition,
    config: RunConfig,
    cast: list[Participant],
    task: Task | None,
    run_no: int,
    runs: int,
    *,
    rounds: int,
    with_votes: bool,
    progress: Callable[[str], None],
) -> RunRecord | None:
    """Simulate one run and return its record, or None if the API quota ran out."""
    from discussion import APIQuotaExhausted

    members: dict[str, list[str]] = {}
    for participant in cast:
        members.setdefault(participant.group, []).append(participant.persona_id)
    progress(f"\nRun {run_no}/{runs}  ({members})")

    scenario, shares = _deal_task(study, condition, run_no, task, cast, progress)
    try:
        measures, transcript, votes, answers = _simulate_run(
            study, condition, config, cast, scenario, shares, task,
            rounds=rounds, with_votes=with_votes, progress=progress,
        )
    except APIQuotaExhausted as exc:
        progress(f"\n[FATAL] {exc}")
        return None

    return RunRecord(
        run_no=run_no,
        condition=condition.key,
        members_by_group=members,
        transcript=transcript,
        votes=votes,
        measures=measures,
        # The exact wording each battery was answered against. Item ids are
        # positional, so two versions of a scale can share them while asking
        # different questions; this is what lets a later report refuse to mix them.
        instruments={i.key: i.fingerprint for i in study.instruments},
        task=_task_summary(task, shares),
        answers=answers,
    )


def _claim(ckpt: Path) -> Path | None:
    """Take the run's lock file, or None if another process holds it.

    O_CREAT | O_EXCL is atomic, so when several workers reach the same run at once
    exactly one creates the file. It records host and pid so a stale lock can be told
    from a live one (clear_stale_locks).
    """
    lock = ckpt.with_suffix(".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w") as f:
        f.write(f"{socket.gethostname()} {os.getpid()}\n")
    return lock


def clear_stale_locks(ckpt_dir: Path) -> list[Path]:
    """Remove run locks left by processes on this host that no longer exist.

    Call only before any worker starts: a worker clearing locks while its peers claim
    them could read a stale lock, lose the race to a peer's fresh one, and delete it.
    """
    removed = []
    for lock in ckpt_dir.glob("run_*.lock"):
        try:
            host, pid = lock.read_text(encoding="utf-8").split()
            os.kill(int(pid), 0)
        except ProcessLookupError:
            if host == socket.gethostname():
                lock.unlink(missing_ok=True)
                removed.append(lock)
        except (OSError, ValueError):
            continue  # unreadable, or alive but not ours to signal: leave it
    return removed


def _write_atomic(path: Path, text: str) -> None:
    """Write via a temporary file and rename, so a reader never sees half a checkpoint."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _deal_task(
    study: Study,
    condition: Condition,
    run_no: int,
    task: Task | None,
    cast: list[Participant],
    progress: Callable[[str], None],
) -> tuple[str, dict[str, list[str]]]:
    """The run's scenario text, and which agent holds which private fact of its task."""
    if not task:
        return condition.scenario, {}
    progress(f"  task {task.name}")
    # Shuffled before dealing: which agent holds which private fact must not
    # track whether they are the Prestige or the Dominance persona, or the
    # endorsement result would partly be measuring who was handed the answer.
    holders = [p.persona_id for p in cast]
    random.Random(f"{study.sampler_seed}:{condition.key}:{run_no}").shuffle(holders)
    return task.briefing(), task.shares(holders)


def _simulate_run(
    study: Study,
    condition: Condition,
    config: RunConfig,
    cast: list[Participant],
    scenario: str,
    shares: dict[str, list[str]],
    task: Task | None,
    *,
    rounds: int,
    with_votes: bool,
    progress: Callable[[str], None],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """One run's model calls, in order: baseline surveys, discussion, post surveys, vote, poll."""
    from discussion import clone_participants, run_discussion, run_poll, run_survey, run_vote

    # Baseline goes to a throwaway fork: the agents who actually discuss must never
    # have seen the items, or the battery primes the very needs we then measure.
    measures: dict[str, dict[str, Any]] = {BASELINE: {}, POST: {}}
    for inst in study.instruments_at(BASELINE):
        progress(f"  baseline {inst.key}")
        measures[BASELINE][inst.key] = run_survey(
            participants=clone_participants(cast),
            instrument=inst,
            model=config.survey,
            on_progress=progress,
        )

    transcript = run_discussion(
        participants=cast,
        scenario=scenario,
        friction=condition.friction,
        rounds=rounds,
        model=config.discussion,
        private=shares,
        on_progress=progress,
    )

    # Each post measure branches from the same post-discussion state, so none of
    # them primes another, yet all of them reflect the discussion that happened.
    for inst in study.instruments_at(POST):
        progress(f"  post {inst.key}")
        measures[POST][inst.key] = run_survey(
            participants=clone_participants(cast),
            instrument=inst,
            model=config.survey,
            rate_groups=tuple(condition.contrast),
            on_progress=progress,
        )

    # Vote last, on the original cast — nothing downstream can be primed by it.
    votes = (
        run_vote(participants=cast, question=study.vote_prompt, model=config.vote)
        if with_votes
        else []
    )

    # After the vote, so committing to an answer cannot colour the endorsement.
    # Skipped with the vote: a study that endorses nobody (validate, dp_check) has
    # no use for task accuracy either, and it is another call per agent per run.
    answers = (
        run_poll(participants=cast, task=task, model=config.vote)
        if task and with_votes else []
    )
    return measures, transcript, votes, answers


def _task_summary(task: Task | None, shares: dict[str, list[str]]) -> dict[str, Any]:
    """What a checkpoint records about the run's task, so accuracy can be scored later."""
    if not task:
        return {}
    return {
        "id": task.id,
        "name": task.name,
        "options": list(task.options),
        "correct": task.correct,
        "shares": shares,
    }


def _reject_foreign_scenario(record: RunRecord, condition: Condition, path: Path) -> None:
    """Refuse to resume a run collected under a different scenario.

    Checkpoints are replayed silently so an interrupted study can continue, which is the
    right behaviour until the stimulus changes underneath them. A condition that now
    draws hidden-profile tasks cannot be topped up with runs whose discussion was seeded
    by a hand-written vignette: the two are different experiments sharing a directory,
    and averaging them would hide that.
    """
    if not condition.pool:
        return
    known = {task.name for task in condition.pool}
    name = record.task.get("name")
    if name in known:
        return
    raise SystemExit(
        f"{path}: this run was collected "
        + (f"on task '{name}', which is not in condition '{condition.key}'s pool"
           if name else "before scenarios were drawn from a task pool")
        + ".\nIt cannot be mixed with runs from the current design. Move the old results "
          "aside (results/<study>/ -> results/archive_<date>/) and start a fresh run."
    )


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
