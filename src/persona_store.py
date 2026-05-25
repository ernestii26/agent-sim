from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from runtime import ensure_tinytroupe_imports

_PROJECT_DIR = Path(__file__).resolve().parent.parent

FIELDS_TO_STRIP = frozenset([
    "mbti_type",
    "mbti_dimensions",
    "cognitive_functions",
    "enriched_bio",
    "discussion_constraints",
])

_MBTI_TYPE_RE = re.compile(
    r"\b(ENTJ|ESTJ|INTJ|ENFJ|ISTJ|ENTP|INFJ|ESFJ|ISFP|INFP|MBTI)\b"
)

E_TYPES = ["ENTJ", "ESTJ", "ENFJ", "ENTP", "ESFJ"]
I_TYPES = ["INTJ", "ISTJ", "INFJ", "ISFP", "INFP"]
ALL_TYPES = E_TYPES + I_TYPES


def _check_no_mbti_leak(spec: dict[str, Any], mbti_type: str) -> None:
    spec_str = json.dumps(spec)
    m = _MBTI_TYPE_RE.search(spec_str)
    if m:
        raise ValueError(
            f"MBTI type label '{m.group()}' still present in {mbti_type} spec after strip"
        )


def load_stripped_personas(
    personas_dir: Path | str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Load all MBTI personas, strip MBTI-identifying fields.

    Returns:
        agents_by_type: dict mapping MBTI type code → TinyPerson agent
        names_by_type:  dict mapping MBTI type code → persona name string
    """
    if personas_dir is None:
        target_dir = _PROJECT_DIR / "personas"
    else:
        p = Path(personas_dir)
        target_dir = p if p.is_absolute() else (_PROJECT_DIR / p)

    manifest_path = target_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Persona manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _, TinyPerson, _, _ = ensure_tinytroupe_imports()

    agents: dict[str, Any] = {}
    names: dict[str, str] = {}

    for mbti_type in manifest["types"]:
        agent_path = target_dir / f"{mbti_type}.agent.json"
        if not agent_path.exists():
            raise SystemExit(f"Agent file not found: {agent_path}")

        spec = json.loads(agent_path.read_text(encoding="utf-8"))
        persona = spec.get("persona", {})
        for field in FIELDS_TO_STRIP:
            persona.pop(field, None)

        _check_no_mbti_leak(spec, mbti_type)

        agent = TinyPerson.load_specification(
            path_or_dict=spec,
            suppress_mental_faculties=False,
            suppress_memory=True,
            suppress_mental_state=True,
        )
        agents[mbti_type] = agent
        names[mbti_type] = str(persona.get("name", mbti_type))

    return agents, names
