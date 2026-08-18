"""Runtime settings, read from config.ini (see config.ini.example)."""
from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelSettings:
    """Everything one LLM call site needs. These four always travel together —
    passing them separately let call sites mix the discussion and vote settings."""
    api_key: str
    model: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class RunConfig:
    api_key: str
    discussion_model: str = "gpt-4.1"
    vote_model: str = "gpt-4.1"
    discussion_temperature: float = 0.7
    vote_temperature: float = 0.2
    discussion_max_tokens: int = 3000
    vote_max_tokens: int = 3000
    survey_model: str = "gpt-4.1"
    survey_temperature: float = 0.2
    survey_max_tokens: int = 3000
    runs: int = 20
    rounds: int = 3
    validate_runs: int = 5
    validate_rounds: int = 5
    output_dir: str = "results"

    @property
    def discussion(self) -> ModelSettings:
        return ModelSettings(
            self.api_key, self.discussion_model,
            self.discussion_temperature, self.discussion_max_tokens,
        )

    @property
    def vote(self) -> ModelSettings:
        return ModelSettings(
            self.api_key, self.vote_model, self.vote_temperature, self.vote_max_tokens,
        )

    @property
    def survey(self) -> ModelSettings:
        # Low temperature on purpose: a rating scale should be a measurement, not a
        # creative act. Same reasoning as the vote settings.
        return ModelSettings(
            self.api_key, self.survey_model, self.survey_temperature, self.survey_max_tokens,
        )

    @staticmethod
    def from_ini(path: Path) -> "RunConfig":
        if not path.exists():
            raise SystemExit(
                f"config.ini not found at {path}. Copy config.ini.example and set API_KEY."
            )
        cfg = configparser.ConfigParser()
        cfg.read(path)
        try:
            api_key = cfg["OpenAI"]["API_KEY"]
        except KeyError:
            raise SystemExit(f"{path}: missing [OpenAI] API_KEY") from None

        sec = cfg["Simulation"] if "Simulation" in cfg else {}
        return RunConfig(
            api_key=api_key,
            discussion_model=sec.get("DISCUSSION_MODEL", "gpt-4.1"),
            vote_model=sec.get("VOTE_MODEL", "gpt-4.1"),
            discussion_temperature=float(sec.get("DISCUSSION_TEMPERATURE", 0.7)),
            vote_temperature=float(sec.get("VOTE_TEMPERATURE", 0.2)),
            discussion_max_tokens=int(sec.get("DISCUSSION_MAX_TOKENS", 3000)),
            vote_max_tokens=int(sec.get("VOTE_MAX_TOKENS", 3000)),
            survey_model=sec.get("SURVEY_MODEL", "gpt-4.1"),
            survey_temperature=float(sec.get("SURVEY_TEMPERATURE", 0.2)),
            survey_max_tokens=int(sec.get("SURVEY_MAX_TOKENS", 3000)),
            runs=int(sec.get("RUNS", 20)),
            rounds=int(sec.get("ROUNDS", 3)),
            validate_runs=int(sec.get("VALIDATE_RUNS", 5)),
            validate_rounds=int(sec.get("VALIDATE_ROUNDS", 5)),
            output_dir=sec.get("OUTPUT_DIR", "results"),
        )
