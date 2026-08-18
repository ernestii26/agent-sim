"""Load persona specs from a study's personas/ directory."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime import ensure_tinytroupe_imports


@dataclass(frozen=True)
class Participant:
    """One agent taking part in one run. Always fully assigned — never half-built."""
    agent: Any
    persona_id: str
    name: str
    group: str


def load_personas(personas_dir: Path, groups: dict[str, str]) -> dict[str, Participant]:
    """Load every persona in `groups` (persona_id -> group key) as a ready Participant.

    Taking the group assignment as input keeps the returned objects complete: there is
    no "now set .group yourself" rule for callers to remember or get wrong.
    """
    _, TinyPerson, _, _ = ensure_tinytroupe_imports()

    loaded: dict[str, Participant] = {}
    for pid, group in groups.items():
        path = personas_dir / f"{pid}.agent.json"
        if not path.exists():
            raise SystemExit(f"Persona file not found: {path} (run tools/gen_personas.py)")
        spec = json.loads(path.read_text(encoding="utf-8"))
        agent = TinyPerson.load_specification(
            path_or_dict=spec,
            suppress_mental_faculties=False,
            suppress_memory=True,
            suppress_mental_state=True,
        )
        name = str(spec.get("persona", spec).get("name", pid))  # accepts flat or TinyPerson-wrapped specs
        loaded[pid] = Participant(agent=agent, persona_id=pid, name=name, group=group)
    return loaded
