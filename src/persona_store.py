from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime import ensure_tinytroupe_imports

_PROJECT_DIR = Path(__file__).resolve().parent.parent

PRESTIGE_TYPES = ["P1", "P2", "P3", "P4", "P5"]
DOMINANCE_TYPES = ["D1", "D2", "D3", "D4", "D5"]
NEUTRAL_TYPES = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]
ALL_TYPES = PRESTIGE_TYPES + DOMINANCE_TYPES + NEUTRAL_TYPES


def load_personas(
    personas_dir: Path | str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Load all personas from the personas directory.

    Returns:
        agents_by_id: dict mapping persona_id → TinyPerson agent
        names_by_id:  dict mapping persona_id → persona name string
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

    for pid in manifest["all_ids"]:
        agent_path = target_dir / f"{pid}.agent.json"
        if not agent_path.exists():
            raise SystemExit(f"Agent file not found: {agent_path}")

        spec = json.loads(agent_path.read_text(encoding="utf-8"))
        agent = TinyPerson.load_specification(
            path_or_dict=spec,
            suppress_mental_faculties=False,
            suppress_memory=True,
            suppress_mental_state=True,
        )
        agents[pid] = agent
        persona = spec.get("persona", {})
        names[pid] = str(persona.get("name", pid))

    return agents, names
