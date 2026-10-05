#!/usr/bin/env python3
"""Build a study's personas from the bank: one fresh cast per run, never reused.

    python3 tools/build_personas.py ffni_mediation --runs 40

Each run seats 1 Prestige, 1 Dominance and 3 Neutral agents drawn from four bank rows:
P_i and D_i share a row (a matched pair), the three neutrals take one row each. Every
row has a different OCEAN profile, so no two personas in the whole study share a
personality. Exactly one cycle is built — `runs` pairs and 3 x `runs` neutrals — so the
balanced sampler in src/pipeline.py seats each persona exactly once, and run_condition
refuses a run count that would make it start over.

What a persona carries, and why nothing else:

* `personality.description` and `big_five` — the bank row, verbatim.
* `personality.traits` — P and D only. Adapted from Ronay et al. (2023) Table 2, Study 3
  (docs/ronay-et-al-2023-*.pdf, p.84), the source paper's own pre-tested manipulation,
  itself built on Cheng et al. (2010)'s items. Two kinds of sentence were dropped: the
  label ("He is a dominant leader"), because TinyTroupe puts the whole persona into the
  system prompt (design-log section 17); and what followers do in response ("they know
  it is usually better to let Anton have his way", "for that reason they follow his
  advice"), because following is the outcome the study measures.
* Name `Participant <k>`, k a shuffled 1..5*runs, so a name carries no group, gender or
  ethnicity. Unique across the study because neutrals are drawn independently of pairs,
  so who will share a room is unknown here.
* `age`, `nationality`, `occupation` = "not specified". minibio() reads all three with
  no fallback, so the keys must exist; HiddenBench gives every agent its role, and an
  occupation that matched a task would read as expertise, which is a prestige cue.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent

OCEAN_ORDER = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
UNSPECIFIED = "not specified"

TRAITS = {
    "D": [
        "has assertively moved up the ranks into positions of leadership",
        "prioritizes having control and authority over others",
        "makes quick and definitive decisions, and once a decision is made it is usually final",
        "has their own views of how tasks should be accomplished",
        "uses reward and punishment to get people to follow their ideas",
    ],
    "P": [
        "has achieved positions of leadership through exceptional performance and abilities",
        "is intelligent and skilled",
        "focuses on fostering positive relationships and teamwork",
        "cares a lot about what others think of them",
        "takes input from others on how tasks should be accomplished",
        "is quick to find common ground between other people's ideas and their own",
    ],
}


def profile(entry: dict) -> tuple:
    return tuple(entry["ocean_description"]["ocean"][t] for t in OCEAN_ORDER)


def sample_rows(bank: list[dict], n: int, rng: random.Random) -> list[int]:
    """Indices of n valid rows, each from a different OCEAN profile."""
    by_profile: dict[tuple, list[int]] = {}
    for i, entry in enumerate(bank):
        if entry["ocean_description"].get("is_valid"):
            by_profile.setdefault(profile(entry), []).append(i)
    profiles = sorted(by_profile)
    if n > len(profiles):
        raise SystemExit(f"need {n} distinct OCEAN profiles, the bank has {len(profiles)}")
    return [rng.choice(by_profile[p]) for p in rng.sample(profiles, n)]


def to_spec(entry: dict, pid: str, name: str, group: str) -> dict:
    personality = {
        "description": entry["ocean_description"]["description_en"],
        "big_five": {t: entry["ocean_description"]["ocean"][t] for t in OCEAN_ORDER},
    }
    if group in TRAITS:
        personality["traits"] = list(TRAITS[group])
    return {
        "type": "TinyPerson",
        "persona": {
            "name": name,
            "age": UNSPECIFIED,
            "nationality": UNSPECIFIED,
            "occupation": UNSPECIFIED,
            "personality": personality,
        },
        "persona_id": pid,
    }


def build(bank: list[dict], runs: int, seed: int) -> list[tuple[str, str, int, dict]]:
    """(persona_id, group, bank_index, spec) for one full cycle of `runs` casts."""
    rng = random.Random(seed)
    rows = sample_rows(bank, 4 * runs, rng)
    names = rng.sample(range(1, 5 * runs + 1), 5 * runs)
    plan = [(f"P{i}", "P", rows[i - 1]) for i in range(1, runs + 1)]
    plan += [(f"D{i}", "D", rows[i - 1]) for i in range(1, runs + 1)]
    plan += [(f"N{i}", "N", rows[runs + i - 1]) for i in range(1, 3 * runs + 1)]
    return [(pid, group, row, to_spec(bank[row], pid, f"Participant {k}", group))
            for (pid, group, row), k in zip(plan, names)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("study")
    ap.add_argument("--runs", type=int, default=40, help="casts to build (default: 40)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bank", default="personas_output.json")
    args = ap.parse_args()

    bank = json.loads((_PROJECT_DIR / args.bank).read_text(encoding="utf-8"))
    personas = build(bank, args.runs, args.seed)

    study_dir = _PROJECT_DIR / "studies" / args.study
    out = study_dir / "personas"
    out.mkdir(exist_ok=True)
    for stale in out.glob("*.agent.json"):  # ponytail: rebuilt from the seed, nothing to keep
        stale.unlink()
    for pid, _, _, spec in personas:
        (out / f"{pid}.agent.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    (study_dir / "bank_sample.json").write_text(json.dumps({
        "bank": args.bank, "seed": args.seed, "runs": args.runs,
        "personas": [{"persona_id": pid, "group": group, "bank_index": row}
                     for pid, group, row, _ in personas],
    }, indent=2), encoding="utf-8")

    study_path = study_dir / "study.json"
    study = json.loads(study_path.read_text(encoding="utf-8"))
    study.pop("personas_from", None)
    for key in ("P", "D", "N"):
        study["groups"][key]["ids"] = [pid for pid, group, _, _ in personas if group == key]
    study_path.write_text(json.dumps(study, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print(f"Wrote {len(personas)} personas ({args.runs} casts, seed {args.seed}) to {out}")


if __name__ == "__main__":
    main()
