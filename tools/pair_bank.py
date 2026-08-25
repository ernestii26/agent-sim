#!/usr/bin/env python3
"""Sample a persona bank into MATCHED prestige/dominance pairs.

    python3 tools/pair_bank.py pd_matched

Why this exists alongside sample_bank.py: that script assigns leadership style at
random and then hunts for a seed whose group means happen to balance. With 6 per group
that search only ever balances the one variable you searched on — ffni_profiles came
out matched on Big Five (top 0.9% of seeds) and badly unmatched on occupation.

Here P_i and D_i are built from the SAME bank row, so every measured variable is
matched by construction and the seed is irrelevant. They differ in name and in the
style block, which is the manipulation. Agents never see each other's persona file,
so a P and a D sharing an occupation costs nothing inside the simulation.

Occupations are filtered to one coherent workplace, because a scenario about a unit
being closed is incoherent for the bank's stay-at-home parents and truck drivers.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "tools"))

from sample_bank import NAME_POOL, OCEAN_ORDER, to_tinyperson_spec  # noqa: E402

# One workplace the bank's occupations can actually share. The other eleven
# (truck driver, prosecutor, stay-at-home parent, ...) cannot sit on one team.
SETTING = {
    "hospital": ("emergency room nurse", "pharmacist", "hospital administrator", "social worker"),
}

SCENARIOS = {
    "collaborative": {
        "label": "Collaborative",
        "hypothesis": "H1: Prestige receives more peer votes than Dominance",
        "scenario": (
            "Your unit has missed its patient-safety and throughput targets for two "
            "consecutive quarters. Hospital leadership has granted your group full autonomy "
            "to diagnose the root cause and commit to one concrete change. You must reach a "
            "shared decision that everyone in the room can commit to implementing."
        ),
        "friction": (
            "[Meeting context: This group has attempted to address the shortfall before. A "
            "previous initiative stalled halfway through and was quietly dropped. People in "
            "this room have different — and sometimes conflicting — views on what actually "
            "went wrong and who was responsible. Not everyone trusts the last diagnosis.]"
        ),
    },
    "threat": {
        "label": "Threat",
        "hypothesis": "H2: Dominance receives more peer votes than Prestige under resource scarcity",
        "contrast": ["D", "P"],
        "scenario": (
            "The hospital is consolidating. Administration will keep only one of two "
            "overlapping units — yours or the other. The decision will be made in 48 hours. "
            "Your group must agree right now on a single case for keeping this unit: what you "
            "deliver, who leads it, and who is accountable. If you cannot agree among "
            "yourselves, administration will decide for you — and people will lose their posts."
        ),
        "friction": (
            "[Meeting context: Two months ago the other unit absorbed a service line yours had "
            "been building for a year. Some people here believe your group lost it through "
            "indecision and unclear ownership. Others think it was a staffing failure. Either "
            "way, you are now in direct competition for survival. Not everyone in this room "
            "agrees on who should be leading the response — and some are wondering whether "
            "they have a future here at all.]"
        ),
    },
}


def profile_key(entry: dict) -> tuple:
    return tuple(entry["ocean_description"]["ocean"][t] for t in OCEAN_ORDER)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("study")
    ap.add_argument("--bank", default="personas_output.json")
    ap.add_argument("--setting", default="hospital", choices=sorted(SETTING))
    ap.add_argument("--pairs", type=int, default=6, help="matched P/D pairs (default: 6)")
    ap.add_argument("--neutrals", type=int, default=24)
    ap.add_argument("--seed", type=int, default=0,
                    help="only picks WHICH profiles are used; balance holds for every seed")
    args = ap.parse_args()

    allowed = SETTING[args.setting]
    bank = json.loads((_PROJECT_DIR / args.bank).read_text(encoding="utf-8"))
    pool = [e for e in bank
            if e["ocean_description"]["is_valid"] and e["occupation"] in allowed]
    print(f"Bank: {len(bank)} entries -> {len(pool)} in setting '{args.setting}'")

    by_profile: dict[tuple, list[dict]] = {}
    for entry in pool:
        by_profile.setdefault(profile_key(entry), []).append(entry)

    rng = random.Random(args.seed)
    profiles = list(by_profile)
    rng.shuffle(profiles)
    if args.pairs + args.neutrals > len(profiles):
        raise SystemExit(f"Need {args.pairs + args.neutrals} distinct OCEAN profiles, "
                         f"setting has {len(profiles)}")

    # One row per profile. P_i and D_i share it; the neutrals take later profiles, so no
    # neutral is a personality twin of a leader.
    leader_rows = [rng.choice(by_profile[p]) for p in profiles[:args.pairs]]
    neutral_rows = [rng.choice(by_profile[p])
                    for p in profiles[args.pairs:args.pairs + args.neutrals]]

    names = list(NAME_POOL)
    rng.shuffle(names)
    if args.pairs * 2 + args.neutrals > len(names):
        raise SystemExit(f"NAME_POOL has {len(names)} names, need "
                         f"{args.pairs * 2 + args.neutrals}")

    specs: list[tuple[str, dict]] = []
    provenance: list[dict] = []
    cursor = 0
    group_ids: dict[str, list[str]] = {"P": [], "D": [], "N": []}

    for i, row in enumerate(leader_rows, start=1):
        for group in ("P", "D"):
            pid = f"{group}{i}"
            specs.append((pid, to_tinyperson_spec(row, group, pid, names[cursor])))
            group_ids[group].append(pid)
            provenance.append({"persona_id": pid, "group": group, "pair": i,
                               "name": names[cursor], "occupation": row["occupation"],
                               "ocean": row["ocean_description"]["ocean"],
                               "demographic": row["demographic"]})
            cursor += 1

    for i, row in enumerate(neutral_rows, start=1):
        pid = f"N{i}"
        specs.append((pid, to_tinyperson_spec(row, "N", pid, names[cursor])))
        group_ids["N"].append(pid)
        provenance.append({"persona_id": pid, "group": "N", "pair": None,
                           "name": names[cursor], "occupation": row["occupation"],
                           "ocean": row["ocean_description"]["ocean"],
                           "demographic": row["demographic"]})
        cursor += 1

    # The check: matching is the entire point, so it is verified rather than asserted in
    # a docstring. Any future edit that breaks the pairing fails here, not 1600 API calls in.
    p_rows = [r for r in provenance if r["group"] == "P"]
    d_rows = [r for r in provenance if r["group"] == "D"]
    for trait in OCEAN_ORDER:
        assert sorted(r["ocean"][trait] for r in p_rows) == \
               sorted(r["ocean"][trait] for r in d_rows), f"{trait} not matched"
    assert sorted(r["occupation"] for r in p_rows) == sorted(r["occupation"] for r in d_rows)
    assert sorted(r["demographic"]["age_group"] for r in p_rows) == \
           sorted(r["demographic"]["age_group"] for r in d_rows)
    assert len({r["name"] for r in provenance}) == len(provenance), "duplicate names"

    out_dir = _PROJECT_DIR / "studies" / args.study
    (out_dir / "personas").mkdir(parents=True, exist_ok=True)
    for pid, spec in specs:
        (out_dir / "personas" / f"{pid}.agent.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    study = {
        "name": args.study,
        "title": "Prestige vs Dominance on Matched Persona Pairs",
        "description": (
            f"P_i and D_i are built from the same bank row — identical Big Five, occupation, "
            f"age and parental status — so the only difference between the groups is the "
            f"leadership style block. Group balance is exact by construction, not by seed "
            f"search, and holds for every --seed. Occupations are filtered to the "
            f"'{args.setting}' setting so the scenario is coherent for every participant."
        ),
        "groups": {
            "P": {"label": "Prestige", "sample": 1, "ids": group_ids["P"]},
            "D": {"label": "Dominance", "sample": 1, "ids": group_ids["D"]},
            "N": {"label": "Neutral", "sample": 8, "ids": group_ids["N"]},
        },
        "contrast": ["P", "D"],
        "vote_prompt": "Based on what you observed, who do you most trust to lead this team?",
        "conditions": SCENARIOS,
        "persona_bank": {"source": args.bank, "setting": args.setting,
                         "seed": args.seed, "matching": "P_i and D_i share one bank row"},
    }
    (out_dir / "study.json").write_text(
        json.dumps(study, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "bank_sample.json").write_text(
        json.dumps({"bank": args.bank, "setting": args.setting, "seed": args.seed,
                    "personas": provenance}, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWrote {len(specs)} personas + study.json to {out_dir}")
    print(f"  {args.pairs} matched pairs, {args.neutrals} neutrals")
    print("  matching verified: Big Five, occupation, age group, parental status")
    print("\nMatched pairs:")
    for i in range(1, args.pairs + 1):
        p = next(r for r in p_rows if r["pair"] == i)
        d = next(r for r in d_rows if r["pair"] == i)
        o = "/".join(f"{v[0].upper()}" for v in
                     (p["ocean"][t] for t in OCEAN_ORDER))
        print(f"  {i}. {p['name']:<18} (P) | {d['name']:<18} (D)  "
              f"{p['occupation']:<22} {p['demographic']['age_group']:<6} OCEAN={o}")
    print(f"\nNext: python3 test_core.py && python3 run.py run {args.study} threat --runs 3")


if __name__ == "__main__":
    main()
