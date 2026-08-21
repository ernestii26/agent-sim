#!/usr/bin/env python3
"""Sample a persona bank into a study's seeds.json, assigning leadership styles.

    python3 tools/sample_bank.py <study> --split P=6,D=6,N=24

Reads a bank of raw persona profiles (personas_output.json: an OCEAN profile with a
prose description, plus occupation and demographics) and turns a sample of them into
seeds for tools/gen_personas.py, which does the actual generation.

Two things this deliberately does NOT do:

* It does not write persona specs. Generation costs API calls, so it stays a separate
  step you trigger. gen_personas.py skips personas that already exist, so the bank on
  disk grows incrementally and nothing is ever regenerated.
* It does not put the leadership style in a field and call it done. The bank's prose
  describes OCEAN only — it never mentions how a person acquires influence. A label the
  text does not carry changes nothing about how the agent behaves, so the assigned style
  is written into the generation prompt and has to come back woven through traits,
  mannerisms and speech.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))

# The bank records OCEAN as low/medium/high; the generation prompt wants 0-10 scores.
LEVEL_SCORES = {"low": 2, "medium": 5, "high": 8}
OCEAN_ORDER = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")

STYLE_PROMPT = {"P": "leader", "D": "leader", "N": "neutral"}
STYLE_NAME = {"P": "prestige", "D": "dominance", "N": "neutral"}


def parse_split(text: str) -> dict[str, int]:
    """"P=6,D=6,N=24" -> {"P": 6, "D": 6, "N": 24}"""
    split: dict[str, int] = {}
    for part in text.split(","):
        key, _, count = part.partition("=")
        key, count = key.strip(), count.strip()
        if not key or not count.isdigit() or int(count) < 1:
            raise SystemExit(f"--split: bad entry {part!r}, expected like 'P=6'")
        split[key] = int(count)
    return split


def stratified_sample(bank: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Take n entries spread across distinct OCEAN profiles.

    The bank is a full factorial (3^5 profiles x occupations), so drawing uniformly at
    random would happily return two entries with identical personalities. Picking one
    entry per profile keeps the personality range as wide as the sample size allows.
    """
    by_profile: dict[tuple, list[dict]] = {}
    for entry in bank:
        key = tuple(entry["ocean_description"]["ocean"][trait] for trait in OCEAN_ORDER)
        by_profile.setdefault(key, []).append(entry)

    profiles = list(by_profile)
    rng.shuffle(profiles)
    if n > len(profiles):
        raise SystemExit(
            f"--split totals {n}, above the {len(profiles)} distinct OCEAN profiles in the bank; "
            "sampling more would repeat personalities"
        )
    return [rng.choice(by_profile[p]) for p in profiles[:n]]


def build_user_prompt(entry: dict, group: str) -> str:
    ocean = entry["ocean_description"]["ocean"]
    scores = {trait: LEVEL_SCORES[ocean[trait]] for trait in OCEAN_ORDER}
    demo = entry["demographic"]
    style = STYLE_NAME[group]
    description = entry["ocean_description"]["description_en"]

    lines = [
        "Generate a full persona for a person with this profile:",
        f"- Occupation: {entry['occupation']}",
        f"- Age group: {demo['age_group']}   Parent: {'yes' if demo['is_parent'] else 'no'}",
        f"- Big Five (0-10): {scores}",
        "",
        "Established behavioural profile — the persona must stay consistent with it:",
        description,
        "",
    ]
    if group == "N":
        lines += [
            "This person is NOT a natural leader — neither prestige nor dominance oriented.",
            "Choose a name and cultural texture freely.",
            "Names already in this simulation (avoid similarity): {existing_names}",
        ]
    else:
        lines += [
            f"- Leadership style: {style.upper()}",
            "",
            f"Choose a name, nationality and cultural modifiers freely, but keep them "
            f"plausible for the occupation and age above.",
            f"The {style} style must show up concretely in traits, mannerisms, "
            f"decision-making and speech_examples — not as a label. Where the style and "
            f"the behavioural profile pull in different directions, the profile wins: a "
            f"low-extraversion {style} leader is quiet and still {style}, not loud.",
            "Names already in this simulation (avoid similarity): {existing_names}",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("study")
    parser.add_argument("--bank", default="personas_output.json")
    parser.add_argument("--split", default="P=6,D=6,N=24",
                        help="personas per group key (default: P=6,D=6,N=24)")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed, so a sample is reproducible")
    parser.add_argument("--prompts-from", default="prestige_dominance",
                        help="study whose seeds.json supplies the system prompts")
    args = parser.parse_args()

    split = parse_split(args.split)
    total = sum(split.values())
    rng = random.Random(args.seed)

    bank_path = _PROJECT_DIR / args.bank
    if not bank_path.exists():
        raise SystemExit(f"Bank not found: {bank_path}")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    usable = [e for e in bank if e.get("ocean_description", {}).get("is_valid")]
    print(f"Bank: {len(bank)} entries, {len(usable)} valid")

    sample = stratified_sample(usable, total, rng)
    rng.shuffle(sample)  # style assignment is random, independent of personality

    prompts = json.loads(
        (_PROJECT_DIR / "studies" / args.prompts_from / "seeds.json").read_text(encoding="utf-8")
    )["prompts"]

    personas, cursor = [], 0
    group_ids: dict[str, list[str]] = {}
    for group, count in split.items():
        ids = []
        for i in range(1, count + 1):
            entry = sample[cursor]
            cursor += 1
            pid = f"{group}{i}"
            ids.append(pid)
            personas.append({
                "persona_id": pid,
                "group": group,
                "label": f"{entry['occupation']}, {entry['demographic']['age_group']}",
                "prompt": STYLE_PROMPT[group],
                "temperature": 0.8 if group != "N" else 1.0,
                "user": build_user_prompt(entry, group),
                "source": {
                    "occupation": entry["occupation"],
                    "ocean": entry["ocean_description"]["ocean"],
                    "demographic": entry["demographic"],
                },
            })
        group_ids[group] = ids

    out_dir = _PROJECT_DIR / "studies" / args.study
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "seeds.json").write_text(
        json.dumps({"prompts": prompts, "bank": args.bank, "seed": args.seed,
                    "personas": personas}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nSampled {total} personas across {len(split)} groups (seed {args.seed}):")
    for group, ids in group_ids.items():
        print(f"  {group}: {len(ids)}  {ids[0]}..{ids[-1]}")
    print(f"\nWrote {out_dir / 'seeds.json'}")
    print("\nGroup ids for study.json:")
    print(json.dumps({g: ids for g, ids in group_ids.items()}, indent=2))
    print(f"\nNext: python3 tools/gen_personas.py {args.study}   (this is the step that costs API calls)")


if __name__ == "__main__":
    main()
