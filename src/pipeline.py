from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime import clone_person
from discussion import SCENARIO, run_discussion, run_vote
from persona_store import ALL_TYPES, E_TYPES, I_TYPES, load_stripped_personas


@dataclass
class BaselineConfig:
    api_key: str
    discussion_model: str = "gpt-4.1"
    vote_model: str = "gpt-4.1"
    discussion_temperature: float = 0.7
    vote_temperature: float = 0.2
    discussion_max_tokens: int = 1200
    vote_max_tokens: int = 1200
    step1_runs: int = 10
    step1_rounds: int = 5
    step2_runs: int = 40
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
            discussion_max_tokens=int(sec.get("DISCUSSION_MAX_TOKENS", 1200)),
            vote_max_tokens=int(sec.get("VOTE_MAX_TOKENS", 1200)),
            step1_runs=int(sec.get("STEP1_RUNS", 10)),
            step1_rounds=int(sec.get("STEP1_ROUNDS", 5)),
            step2_runs=int(sec.get("STEP2_RUNS", 40)),
            step2_rounds=int(sec.get("STEP2_ROUNDS", 3)),
            personas_dir=sec.get("PERSONAS_DIR", "personas"),
            output_dir=sec.get("OUTPUT_DIR", "results"),
        )


def _load_base_agents(
    config: BaselineConfig,
) -> tuple[dict[str, Any], dict[str, str]]:
    return load_stripped_personas(config.personas_dir)


def _clone_run_agents(
    base_agents: dict[str, Any],
    names: dict[str, str],
) -> tuple[list[Any], list[str], list[str]]:
    agents = [clone_person(base_agents[t]) for t in ALL_TYPES]
    agent_names = [names[t] for t in ALL_TYPES]
    mbti_types = list(ALL_TYPES)
    return agents, agent_names, mbti_types


def step1_validate_silence(
    config: BaselineConfig,
    *,
    on_progress: Any = None,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Step 1: silence mechanism validation."""
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = checkpoint_dir or Path(config.output_dir) / "step1_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading stripped personas...")
    base_agents, names_by_type = _load_base_agents(config)

    per_persona_spoke: dict[str, int] = {t: 0 for t in ALL_TYPES}
    per_persona_words: dict[str, int] = {t: 0 for t in ALL_TYPES}
    per_persona_talk_turns: dict[str, int] = {t: 0 for t in ALL_TYPES}
    total_turns = config.step1_runs * config.step1_rounds

    for run_no in range(1, config.step1_runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{config.step1_runs}  [checkpoint]")
            saved = json.loads(ckpt.read_text(encoding="utf-8"))
            for entry in saved["transcript"]:
                t = entry["mbti_type"]
                if entry["spoke"]:
                    per_persona_spoke[t] += 1
                    per_persona_words[t] += entry["word_count"]
                    per_persona_talk_turns[t] += 1
            continue

        progress(f"\nRun {run_no}/{config.step1_runs}")
        agents, agent_names, mbti_types = _clone_run_agents(base_agents, names_by_type)

        transcript = run_discussion(
            agents=agents,
            names=agent_names,
            mbti_types=mbti_types,
            scenario=SCENARIO,
            rounds=config.step1_rounds,
            api_key=config.api_key,
            model=config.discussion_model,
            temperature=config.discussion_temperature,
            max_tokens=config.discussion_max_tokens,
            on_progress=progress,
        )

        for entry in transcript:
            t = entry["mbti_type"]
            if entry["spoke"]:
                per_persona_spoke[t] += 1
                per_persona_words[t] += entry["word_count"]
                per_persona_talk_turns[t] += 1

        ckpt.write_text(
            json.dumps({"run_no": run_no, "transcript": transcript}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    speech_rate = {t: per_persona_spoke[t] / total_turns for t in ALL_TYPES}
    mean_words = {
        t: (per_persona_words[t] / per_persona_talk_turns[t] if per_persona_talk_turns[t] > 0 else 0.0)
        for t in ALL_TYPES
    }

    e_mean_rate = sum(speech_rate[t] for t in E_TYPES) / len(E_TYPES)
    i_mean_rate = sum(speech_rate[t] for t in I_TYPES) / len(I_TYPES)
    gap = e_mean_rate - i_mean_rate

    i_below_70 = sum(1 for t in I_TYPES if speech_rate[t] < 0.70)
    e_above_50 = sum(1 for t in E_TYPES if speech_rate[t] > 0.50)
    passed = gap >= 0.10 and i_below_70 >= 3 and e_above_50 >= 3

    return {
        "step": 1,
        "runs": config.step1_runs,
        "rounds": config.step1_rounds,
        "speech_rate": speech_rate,
        "mean_words_when_speaking": mean_words,
        "e_mean_speech_rate": e_mean_rate,
        "i_mean_speech_rate": i_mean_rate,
        "gap": gap,
        "i_below_70_count": i_below_70,
        "e_above_50_count": e_above_50,
        "passed": passed,
        "names": names_by_type,
    }


def step2_run_simulation(
    config: BaselineConfig,
    *,
    on_progress: Any = None,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Step 2: main E vs I leadership hypothesis test."""
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ckpt_dir = checkpoint_dir or Path(config.output_dir) / "step2_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    progress("Loading stripped personas...")
    base_agents, names_by_type = _load_base_agents(config)

    run_results: list[dict[str, Any]] = []

    for run_no in range(1, config.step2_runs + 1):
        ckpt = ckpt_dir / f"run_{run_no:03d}.json"
        if ckpt.exists():
            progress(f"\nRun {run_no}/{config.step2_runs}  [checkpoint]")
            saved = json.loads(ckpt.read_text(encoding="utf-8"))
            run_results.append(saved)
            continue

        progress(f"\nRun {run_no}/{config.step2_runs}")
        agents, agent_names, mbti_types = _clone_run_agents(base_agents, names_by_type)

        transcript = run_discussion(
            agents=agents,
            names=agent_names,
            mbti_types=mbti_types,
            scenario=SCENARIO,
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
            mbti_types=mbti_types,
            transcript=transcript,
            api_key=config.api_key,
            model=config.vote_model,
            temperature=config.vote_temperature,
            max_tokens=config.vote_max_tokens,
        )

        vote_counts: dict[str, int] = {t: 0 for t in ALL_TYPES}
        for v in votes:
            vt = v["voted_for_type"]
            if vt in vote_counts:
                vote_counts[vt] += 1

        e_votes = sum(vote_counts[t] for t in E_TYPES)
        i_votes = sum(vote_counts[t] for t in I_TYPES)

        spoke_by_type: dict[str, list[bool]] = {t: [] for t in ALL_TYPES}
        words_by_type: dict[str, list[int]] = {t: [] for t in ALL_TYPES}
        for entry in transcript:
            t = entry["mbti_type"]
            spoke_by_type[t].append(entry["spoke"])
            if entry["spoke"]:
                words_by_type[t].append(entry["word_count"])

        speech_rate_run = {
            t: (sum(spoke_by_type[t]) / len(spoke_by_type[t]) if spoke_by_type[t] else 0.0)
            for t in ALL_TYPES
        }
        mean_words_run = {
            t: (sum(words_by_type[t]) / len(words_by_type[t]) if words_by_type[t] else 0.0)
            for t in ALL_TYPES
        }

        e_speech_rate = sum(speech_rate_run[t] for t in E_TYPES) / len(E_TYPES)
        i_speech_rate = sum(speech_rate_run[t] for t in I_TYPES) / len(I_TYPES)
        e_words_vals = [mean_words_run[t] for t in E_TYPES if words_by_type[t]]
        i_words_vals = [mean_words_run[t] for t in I_TYPES if words_by_type[t]]
        e_words = sum(e_words_vals) / len(e_words_vals) if e_words_vals else float("nan")
        i_words = sum(i_words_vals) / len(i_words_vals) if i_words_vals else float("nan")

        result = {
            "run_no": run_no,
            "e_votes": e_votes,
            "i_votes": i_votes,
            "vote_counts": vote_counts,
            "e_speech_rate": e_speech_rate,
            "i_speech_rate": i_speech_rate,
            "e_words_per_turn": e_words,
            "i_words_per_turn": i_words,
            "speech_rate_by_type": speech_rate_run,
            "mean_words_by_type": mean_words_run,
            "transcript": transcript,
            "votes": votes,
        }
        run_results.append(result)
        ckpt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        progress(
            f"  votes  E {e_votes:>2} / I {i_votes:>2}"
            f"   speech  E {e_speech_rate:.2f} / I {i_speech_rate:.2f}"
        )

    return {"step": 2, "runs": config.step2_runs, "rounds": config.step2_rounds, "run_results": run_results}
