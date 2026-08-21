#!/usr/bin/env python3
"""Generate a study's personas from studies/<study>/seeds.json.

    python3 tools/gen_personas.py <study> [--force]

seeds.json holds every theme-specific word:
    {
      "prompts":  {"<key>": "<system prompt>"},
      "personas": [{"persona_id", "group", "prompt", "temperature", "user"}]
    }
The `user` string may contain the literal {existing_names}, substituted with the names
generated so far — useful for asking the model to avoid near-duplicate names. Plain
replacement, not str.format: prompts legitimately contain braces (a rendered score dict,
a JSON example) and format() would treat every one of them as a field.
Existing persona files are kept unless --force is given, so a failed run resumes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))
os.chdir(_PROJECT_DIR)

from config import ModelSettings, RunConfig  # noqa: E402
from runtime import configure_tinytroupe_runtime  # noqa: E402
from study import load_study  # noqa: E402


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _generate(system: str, user: str, temperature: float) -> dict:
    from tinytroupe.clients import client

    msg = client().send_message(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    if msg is None:
        raise RuntimeError("TinyTroupe client returned None")
    return _extract_json(str(msg.get("content", "")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate personas for a study")
    parser.add_argument("study")
    parser.add_argument("--force", action="store_true", help="regenerate personas that already exist")
    args = parser.parse_args()

    study = load_study(args.study)
    seeds = json.loads(study.seeds_path.read_text(encoding="utf-8"))
    prompts, personas = seeds["prompts"], seeds["personas"]

    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    configure_tinytroupe_runtime(
        ModelSettings(config.api_key, config.discussion_model, temperature=0.8, max_tokens=2000)
    )

    study.personas_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    manifest: dict[str, dict] = {}

    for i, seed in enumerate(personas, start=1):
        pid = seed["persona_id"]
        path = study.personas_dir / f"{pid}.agent.json"

        if path.exists() and not args.force:
            spec = json.loads(path.read_text(encoding="utf-8"))
            print(f"  [{i}/{len(personas)}] {pid} — exists, skipping")
        else:
            print(f"  [{i}/{len(personas)}] Generating {pid} ({seed.get('label', '')})...", flush=True)
            spec = _generate(
                prompts[seed["prompt"]],
                seed["user"].replace("{existing_names}", ", ".join(names) or "none yet"),
                float(seed.get("temperature", 0.8)),
            )
            if not spec.get("name"):
                raise SystemExit(f"Model returned an empty spec for {pid}")
            spec["persona_id"] = pid
            path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"          Saved -> {path.name}  ({spec['name']})")

        name = spec.get("persona", spec).get("name", pid)
        names.append(name)
        manifest[pid] = {"persona_id": pid, "name": name, "group": seed["group"]}

    (study.personas_dir / "manifest.json").write_text(
        json.dumps({"study": study.name, "personas": manifest}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nDone. {len(manifest)} personas in {study.personas_dir}")


if __name__ == "__main__":
    main()
