from __future__ import annotations

import configparser
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime import clone_person
from discussion import (
    SCENARIO, SCENARIO_FRICTION,
    SCENARIO_THREAT, SCENARIO_THREAT_FRICTION,
    APIQuotaExhausted, run_discussion, run_vote,
)
from persona_store import (
    ALL_TYPES, PRESTIGE_TYPES, DOMINANCE_TYPES, NEUTRAL_TYPES, load_personas
)


@dataclass
class BaselineConfig:
    api_key: str
    discussion_model: str = "gpt-4.1"
    vote_model: str = "gpt-4.1"
    discussion_temperature: float = 0.7
    vote_temperature: float = 0.2
    discussion_max_tokens: int = 3000
    vote_max_tokens: int = 3000
    step1_runs: int = 5
    step1_rounds: int = 5
    step2_runs: int = 20
    step2_rounds: int = 3
    personas_dir: str = "personas"
    output_dir: str = "results"

    @staticmethod
    def from_ini(path: Path) -> "BaselineConfig":
        cfg = configparser.ConfigParser()
        cfg.read(path)

        api_key = cfg["OpenAI"]["API_KEY"]
        sec = cfg["Baseline"] if "Baseline" in cfg else {}

        return BaselineConfig(
            api_key=api_key,
            discussion_model=sec.get("DISCUSSION_MODEL", "gpt-4.1"),
            vote_model=sec.get("VOTE_MODEL", "gpt-4.1"),
            discussion_temperature=float(sec.get("DISCUSSION_TEMPERATURE", 0.7)),
            vote_temperature=float(sec.get("VOTE_TEMPERATURE", 0.2)),
            discussion_max_tokens=int(sec.get("DISCUSSION_MAX_TOKENS", 3000)),
            vote_max_tokens=int(sec.get("VOTE_MAX_TOKENS", 3000)),
            step1_runs=int(sec.get("STEP1_RUNS", 5)),
            step1_rounds=int(sec.get("STEP1_ROUNDS", 5)),
            step2_runs=int(sec.get("STEP2_RUNS", 20)),
            step2_rounds=int(sec.get("STEP2_ROUNDS", 3)),
            personas_dir=sec.get("PERSONAS_DIR", "personas"),
            output_dir=sec.get("OUTPUT_DIR", "results"),
        )


class _BalancedSampler:
    """Cycles through a pool in random order, ensuring each item appears once
    per cycle before any item repeats. Eliminates the over-representation bias
    that arises from repeated random.choice calls."""

    def __init__(self, pool: list[str]) -> None:
        self._pool = list(pool)
        self._queue: list[str] = []

    def next(self) -> str:
        if not self._queue:
            self._queue = random.sample(self._pool, len(self._pool))
        return self._queue.pop(0)


def _sample_run_agents(
    base_agents: dict[str, Any],
    names: dict[str, str],
    p_sampler: _BalancedSampler,
    d_sampler: _BalancedSampler,
) -> tuple[list[Any], list[str], list[str], str, str]:
    """Sample 1P + 1D + all 8N for one run using balanced samplers.

    Returns (agents, agent_names, persona_types, p_id, d_id).
    """
    p_id = p_sampler.next()
    d_id = d_sampler.next()
    run_ids = [p_id, d_id] + NEUTRAL_TYPES
    agents = [clone_person(base_agents[t]) for t in run_ids]
    agent_names = [names[t] for t in run_ids]
    return agents, agent_names, run_ids, p_id, d_id


def step1_validate_silence(
    config: BaselineConfig,
    *,
    on_progress: Any = None,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Step 1: silence mechanism validation (1P + 1D + 8N per run)."""
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = checkpoint_dir or Path(config.output_dir) / "step1_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading personas...")
    base_agents, names_by_id = load_personas(config.personas_dir)
    p_sampler = _BalancedSampler(PRESTIGE_TYPES)
    d_sampler = _BalancedSampler(DOMINANCE_TYPES)

    # Track per-persona across runs they actually participated in
    per_persona_runs: dict[str, int] = {t: 0 for t in ALL_TYPES}
    per_persona_spoke: dict[str, int] = {t: 0 for t in ALL_TYPES}
    per_persona_words: dict[str, int] = {t: 0 for t in ALL_TYPES}
    per_persona_talk_turns: dict[str, int] = {t: 0 for t in ALL_TYPES}

    for run_no in range(1, config.step1_runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{config.step1_runs}  [checkpoint]")
            saved = json.loads(ckpt.read_text(encoding="utf-8"))
            p_id, d_id = saved["p_id"], saved["d_id"]
            for t in [p_id, d_id] + NEUTRAL_TYPES:
                per_persona_runs[t] += config.step1_rounds
            for entry in saved["transcript"]:
                t = entry["persona_type"]
                if entry["spoke"]:
                    per_persona_spoke[t] += 1
                    per_persona_words[t] += entry["word_count"]
                    per_persona_talk_turns[t] += 1
            continue

        agents, agent_names, run_ids, p_id, d_id = _sample_run_agents(base_agents, names_by_id, p_sampler, d_sampler)
        progress(f"\nRun {run_no}/{config.step1_runs}  (P={p_id}, D={d_id})")
        for t in run_ids:
            per_persona_runs[t] += config.step1_rounds

        transcript = run_discussion(
            agents=agents,
            names=agent_names,
            persona_types=run_ids,
            scenario=SCENARIO,
            friction=SCENARIO_FRICTION,
            rounds=config.step1_rounds,
            api_key=config.api_key,
            model=config.discussion_model,
            temperature=config.discussion_temperature,
            max_tokens=config.discussion_max_tokens,
            on_progress=progress,
        )

        for entry in transcript:
            t = entry["persona_type"]
            if entry["spoke"]:
                per_persona_spoke[t] += 1
                per_persona_words[t] += entry["word_count"]
                per_persona_talk_turns[t] += 1

        ckpt.write_text(
            json.dumps(
                {"run_no": run_no, "p_id": p_id, "d_id": d_id, "transcript": transcript},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    speech_rate = {
        t: (per_persona_spoke[t] / per_persona_runs[t] if per_persona_runs[t] > 0 else float("nan"))
        for t in ALL_TYPES
    }
    mean_words = {
        t: (per_persona_words[t] / per_persona_talk_turns[t] if per_persona_talk_turns[t] > 0 else float("nan"))
        for t in ALL_TYPES
    }

    # Pass criteria: N personas show silence variation (always present, enough data)
    n_rates = [speech_rate[t] for t in NEUTRAL_TYPES if not math.isnan(speech_rate[t])]
    n_mean_rate = sum(n_rates) / len(n_rates) if n_rates else 1.0
    n_some_silence = sum(1 for r in n_rates if r < 0.80)
    passed = n_some_silence >= 3 and n_mean_rate < 0.90

    return {
        "step": 1,
        "runs": config.step1_runs,
        "rounds": config.step1_rounds,
        "speech_rate": speech_rate,
        "mean_words_when_speaking": mean_words,
        "n_mean_speech_rate": n_mean_rate,
        "n_some_silence_count": n_some_silence,
        "passed": passed,
        "names": names_by_id,
    }


def step2_run_simulation(
    config: BaselineConfig,
    *,
    on_progress: Any = None,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Step 2: Prestige vs Dominance leadership hypothesis test (1P + 1D + 8N per run)."""
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = checkpoint_dir or Path(config.output_dir) / "step2_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading personas...")
    base_agents, names_by_id = load_personas(config.personas_dir)
    p_sampler = _BalancedSampler(PRESTIGE_TYPES)
    d_sampler = _BalancedSampler(DOMINANCE_TYPES)

    run_results: list[dict[str, Any]] = []

    for run_no in range(1, config.step2_runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{config.step2_runs}  [checkpoint]")
            run_results.append(json.loads(ckpt.read_text(encoding="utf-8")))
            continue

        agents, agent_names, run_ids, p_id, d_id = _sample_run_agents(base_agents, names_by_id, p_sampler, d_sampler)
        progress(f"\nRun {run_no}/{config.step2_runs}  (P={p_id}, D={d_id})")

        try:
            transcript = run_discussion(
                agents=agents,
                names=agent_names,
                persona_types=run_ids,
                scenario=SCENARIO,
                friction=SCENARIO_FRICTION,
                rounds=config.step2_rounds,
                api_key=config.api_key,
                model=config.discussion_model,
                temperature=config.discussion_temperature,
                max_tokens=config.discussion_max_tokens,
                on_progress=progress,
            )

            votes = run_vote(
                agents=agents,
                names=agent_names,
                persona_types=run_ids,
                transcript=transcript,
                api_key=config.api_key,
                model=config.vote_model,
                temperature=config.vote_temperature,
                max_tokens=config.vote_max_tokens,
            )
        except APIQuotaExhausted as exc:
            progress(f"\n[FATAL] {exc}")
            progress(f"  Stopping after {len(run_results)} completed runs. Checkpoints are saved — resume when quota is restored.")
            break

        vote_counts: dict[str, int] = {t: 0 for t in run_ids}
        for v in votes:
            vt = v["voted_for_type"]
            if vt in vote_counts:
                vote_counts[vt] += 1

        p_votes = vote_counts[p_id]
        d_votes = vote_counts[d_id]

        spoke_by_type: dict[str, list[bool]] = {t: [] for t in run_ids}
        words_by_type: dict[str, list[int]] = {t: [] for t in run_ids}
        for entry in transcript:
            t = entry["persona_type"]
            spoke_by_type[t].append(entry["spoke"])
            if entry["spoke"]:
                words_by_type[t].append(entry["word_count"])

        speech_rate_run = {
            t: (sum(spoke_by_type[t]) / len(spoke_by_type[t]) if spoke_by_type[t] else 0.0)
            for t in run_ids
        }

        p_speech_rate = speech_rate_run[p_id]
        d_speech_rate = speech_rate_run[d_id]
        p_words = (sum(words_by_type[p_id]) / len(words_by_type[p_id])
                   if words_by_type[p_id] else float("nan"))
        d_words = (sum(words_by_type[d_id]) / len(words_by_type[d_id])
                   if words_by_type[d_id] else float("nan"))

        result = {
            "run_no": run_no,
            "p_id": p_id,
            "d_id": d_id,
            "p_votes": p_votes,
            "d_votes": d_votes,
            "vote_counts": vote_counts,
            "p_speech_rate": p_speech_rate,
            "d_speech_rate": d_speech_rate,
            "p_words_per_turn": p_words,
            "d_words_per_turn": d_words,
            "speech_rate_by_type": speech_rate_run,
            "transcript": transcript,
            "votes": votes,
        }
        run_results.append(result)
        ckpt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        progress(
            f"  votes  P({p_id}) {p_votes:>2} / D({d_id}) {d_votes:>2}"
            f"   speech  P {p_speech_rate:.2f} / D {d_speech_rate:.2f}"
        )

    return {
        "step": 2,
        "runs": config.step2_runs,
        "rounds": config.step2_rounds,
        "run_results": run_results,
    }


def step3_run_simulation(
    config: BaselineConfig,
    *,
    on_progress: Any = None,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Step 3: threat scenario — tests whether Dominance > Prestige under
    resource scarcity and external survival pressure (H2: D > P)."""
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = checkpoint_dir or Path(config.output_dir) / "step3_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading personas...")
    base_agents, names_by_id = load_personas(config.personas_dir)
    p_sampler = _BalancedSampler(PRESTIGE_TYPES)
    d_sampler = _BalancedSampler(DOMINANCE_TYPES)

    run_results: list[dict[str, Any]] = []

    for run_no in range(1, config.step2_runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{config.step2_runs}  [checkpoint]")
            run_results.append(json.loads(ckpt.read_text(encoding="utf-8")))
            continue

        agents, agent_names, run_ids, p_id, d_id = _sample_run_agents(base_agents, names_by_id, p_sampler, d_sampler)
        progress(f"\nRun {run_no}/{config.step2_runs}  (P={p_id}, D={d_id})")

        try:
            transcript = run_discussion(
                agents=agents,
                names=agent_names,
                persona_types=run_ids,
                scenario=SCENARIO_THREAT,
                friction=SCENARIO_THREAT_FRICTION,
                rounds=config.step2_rounds,
                api_key=config.api_key,
                model=config.discussion_model,
                temperature=config.discussion_temperature,
                max_tokens=config.discussion_max_tokens,
                on_progress=progress,
            )

            votes = run_vote(
                agents=agents,
                names=agent_names,
                persona_types=run_ids,
                transcript=transcript,
                api_key=config.api_key,
                model=config.vote_model,
                temperature=config.vote_temperature,
                max_tokens=config.vote_max_tokens,
            )
        except APIQuotaExhausted as exc:
            progress(f"\n[FATAL] {exc}")
            progress(f"  Stopping after {len(run_results)} completed runs. Checkpoints are saved — resume when quota is restored.")
            break

        vote_counts: dict[str, int] = {t: 0 for t in run_ids}
        for v in votes:
            vt = v["voted_for_type"]
            if vt in vote_counts:
                vote_counts[vt] += 1

        p_votes = vote_counts[p_id]
        d_votes = vote_counts[d_id]

        spoke_by_type: dict[str, list[bool]] = {t: [] for t in run_ids}
        words_by_type: dict[str, list[int]] = {t: [] for t in run_ids}
        for entry in transcript:
            t = entry["persona_type"]
            spoke_by_type[t].append(entry["spoke"])
            if entry["spoke"]:
                words_by_type[t].append(entry["word_count"])

        speech_rate_run = {
            t: (sum(spoke_by_type[t]) / len(spoke_by_type[t]) if spoke_by_type[t] else 0.0)
            for t in run_ids
        }

        p_speech_rate = speech_rate_run[p_id]
        d_speech_rate = speech_rate_run[d_id]
        p_words = (sum(words_by_type[p_id]) / len(words_by_type[p_id])
                   if words_by_type[p_id] else float("nan"))
        d_words = (sum(words_by_type[d_id]) / len(words_by_type[d_id])
                   if words_by_type[d_id] else float("nan"))

        result = {
            "run_no": run_no,
            "p_id": p_id,
            "d_id": d_id,
            "p_votes": p_votes,
            "d_votes": d_votes,
            "vote_counts": vote_counts,
            "p_speech_rate": p_speech_rate,
            "d_speech_rate": d_speech_rate,
            "p_words_per_turn": p_words,
            "d_words_per_turn": d_words,
            "speech_rate_by_type": speech_rate_run,
            "transcript": transcript,
            "votes": votes,
        }
        run_results.append(result)
        ckpt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        progress(
            f"  votes  P({p_id}) {p_votes:>2} / D({d_id}) {d_votes:>2}"
            f"   speech  P {p_speech_rate:.2f} / D {d_speech_rate:.2f}"
        )

    return {
        "step": 3,
        "scenario": "threat",
        "runs": config.step2_runs,
        "rounds": config.step2_rounds,
        "run_results": run_results,
    }
