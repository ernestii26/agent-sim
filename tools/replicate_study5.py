#!/usr/bin/env python3
"""Replicate Sheng et al. (2026) Study 5 on fresh bank personas, with no meeting.

    python3 tools/replicate_study5.py --smoke     3 personas per arm, to check the plumbing
    python3 tools/replicate_study5.py --arm a     Table 13: FFNI (generic) + ILT, N = 261
    python3 tools/replicate_study5.py --arm b     Table 3:  FFNI (work) + 57 descriptions, N = 367

The two arms are separate samples, as in the paper: 5a used Sample B (US, generic FFNI) and
5c used Sample E (China, work FFNI). Each arm uses its own personas, drawn from bank rows
that ffni_mediation does not use, and spread over the 243 OCEAN profiles as evenly as N
allows. Each instrument is answered on a fresh fork, as in measure-check, so no answer is
made with another one in memory. The paper's 5c had a one-week lag between FFNI and
effectiveness; here they are separate sittings with nothing in between.

The FFNI instructions are the paper's own (preprint pp. 27-28): ffni.json carries a
shortened work instruction, which is fine inside a meeting study but is not what a
replication should send.

Answers are saved per instrument under results/replication/<arm>/, and a rerun skips
whatever is already there. The comparison against the paper is printed and saved as
summary.json.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "tools"))

from analysis import prototype_by_dimension  # noqa: E402
from build_personas import profile, to_spec  # noqa: E402
from instrument import BASELINE  # noqa: E402
from run_record import RunRecord  # noqa: E402
from study import load_study  # noqa: E402

GENERIC = ("Think about the people who you consider to be the leaders in your life – those "
           "individuals who influence you and other members of groups you belong to because they "
           "help you satisfy important needs and achieve important goals. They could be influential "
           "people in your family, community, society, team, or work organization. Indicate how "
           "much you agree with each statement.")
WORK = ("Think about the people who you consider to be the leaders in your WORK ORGANIZATION "
        "(e.g., senior managers, supervisors) – those individuals who influence you and your "
        "co-workers because they help you satisfy important needs and achieve important goals. "
        "Indicate how much you agree with each statement.")

# The paper's standardised betas with the other five needs controlled, for the cells each
# table hypothesises. Table 13 (p. 790): only the significant increments, which is what
# ilt.json's `predicts` lists. Table 3, Model 2 (p. 775): every preregistered pair.
PAPER = {
    "a": {("protection", "strength"): .26,
          ("status", "tyranny"): .32, ("status", "masculinity"): .19, ("status", "well_groomed"): .30,
          ("vision", "sensitivity"): .20, ("vision", "dedication"): .30,
          ("vision", "charisma"): .19, ("vision", "creativity"): .24,
          ("expertise", "sensitivity"): .32, ("expertise", "charisma"): .22,
          ("expertise", "intelligence"): .21,
          ("fairness", "dedication"): .25, ("fairness", "intelligence"): .26,
          ("fairness", "ethics"): .29},
    "b": {("protection", "safety"): .05, ("protection", "authoritarianism"): .01,
          ("affiliation", "benevolence"): .10, ("affiliation", "team_building"): .36,
          ("status", "narcissism"): .04, ("status", "authoritarianism"): -.02,
          ("status", "dominance"): .02,
          ("vision", "vision_communication"): .18, ("vision", "high_expectation"): .10,
          ("expertise", "competence"): .08, ("expertise", "intellectual_stimulation"): .13,
          ("fairness", "moral_character"): .25, ("fairness", "virtue"): .08},
}
# Significant at .05 in the paper, so a replication is a same-sign beta at p < .05; the
# rest are nulls, replicated by p >= .05.
PAPER_SIGNIFICANT = {
    "a": set(PAPER["a"]),
    "b": {("affiliation", "benevolence"), ("affiliation", "team_building"),
          ("vision", "vision_communication"), ("expertise", "intellectual_stimulation"),
          ("fairness", "moral_character")},
}
SIZES = {"a": 261, "b": 367}


def draw_rows(bank: list[dict], exclude: set[int], n: int, rng: random.Random) -> list[int]:
    """n unused rows, one per OCEAN profile in turn, so profiles repeat only past 243."""
    by_profile: dict[tuple, list[int]] = {}
    for i, entry in enumerate(bank):
        if i not in exclude and entry["ocean_description"].get("is_valid"):
            by_profile.setdefault(profile(entry), []).append(i)
    for rows in by_profile.values():
        rng.shuffle(rows)
    order = sorted(by_profile)
    rng.shuffle(order)
    picked: list[int] = []
    while len(picked) < n:
        before = len(picked)
        for p in order:
            if by_profile[p] and len(picked) < n:
                picked.append(by_profile[p].pop())
        if len(picked) == before:
            raise SystemExit(f"bank has only {len(picked)} unused rows, {n} asked")
    return picked


def p_value(delta_r2: float, r2: float, n: int, k: int = 6) -> float:
    """The hierarchical-regression F test for one added predictor (df 1, n - k - 1)."""
    from scipy.stats import f
    df = n - k - 1
    if df <= 0 or not (r2 < 1) or delta_r2 != delta_r2:
        return float("nan")
    return float(f.sf(delta_r2 * df / (1 - r2), 1, df))


def compare(arm: str, out: dict) -> list[dict]:
    rows = []
    for (need, dim), paper_beta in PAPER[arm].items():
        cell = out["dimensions"][dim]
        c = cell["needs"][need]
        p = p_value(c["delta_r2"], cell["model_r2"], cell["n"])
        significant = (need, dim) in PAPER_SIGNIFICANT[arm]
        same = (p < .05 and (c["beta"] > 0) == (paper_beta > 0)) if significant else p >= .05
        rows.append({"need": need, "dimension": dim, "paper_beta": paper_beta,
                     "paper_significant": significant, "beta": c["beta"], "r": c["r"],
                     "delta_r2": c["delta_r2"], "p": p, "n": cell["n"], "replicated": same})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=("a", "b"), action="append")
    ap.add_argument("--n", type=int, help="personas per arm (default: the paper's N)")
    ap.add_argument("--smoke", action="store_true", help="3 personas per arm, separate folder")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    arms = args.arm or ["a", "b"]

    from config import RunConfig
    from discussion import clone_participants, run_survey
    from persona_store import load_personas

    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study("ffni_mediation")
    bank = json.loads((_PROJECT_DIR / "personas_output.json").read_text(encoding="utf-8"))
    used = {p["bank_index"] for p in json.loads(
        (study.directory / "bank_sample.json").read_text(encoding="utf-8"))["personas"]}

    root = _PROJECT_DIR / "results" / ("replication_smoke" if args.smoke else "replication")
    # Both arms are drawn together so they can never share a row, whichever is run first.
    sizes = {a: 3 if args.smoke else (args.n or SIZES[a]) for a in ("a", "b")}
    rows = draw_rows(bank, used, sizes["a"] + sizes["b"], random.Random(args.seed))
    split = {"a": rows[:sizes["a"]], "b": rows[sizes["a"]:]}

    plan = {
        "a": [replace(study.self_report, key="ffni_generic", instructions=GENERIC, targets=()),
              replace(study.prototype, targets=())],
        "b": [replace(study.self_report, instructions=WORK, targets=()),
              replace(study.descriptions, targets=())],
    }

    for arm in arms:
        folder = root / arm
        personas = folder / "personas"
        personas.mkdir(parents=True, exist_ok=True)
        ids = []
        # TinyTroupe names are global, so arm b continues arm a's numbering.
        offset = 0 if arm == "a" else sizes["a"]
        for k, row in enumerate(split[arm], start=1):
            pid = f"R{arm.upper()}{k}"
            ids.append(pid)
            path = personas / f"{pid}.agent.json"
            if not path.exists():
                path.write_text(json.dumps(to_spec(bank[row], pid, f"Participant {offset + k}", "N"),
                                           indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / "bank_sample.json").write_text(json.dumps(
            {"seed": args.seed, "rows": dict(zip(ids, split[arm]))}, indent=2), encoding="utf-8")
        pool = load_personas(personas, {pid: "N" for pid in ids})

        measures: dict = {}
        for inst in plan[arm]:
            saved = folder / f"{inst.key}.json"
            if saved.exists():
                measures[inst.key] = json.loads(saved.read_text(encoding="utf-8"))
                print(f"  {arm}/{inst.key}: {len(measures[inst.key])} saved answers, skipped")
                continue
            print(f"  {arm}/{inst.key}: {len(pool)} respondents")
            measures[inst.key] = run_survey(participants=clone_participants(list(pool.values())),
                                            instrument=inst, model=config.survey,
                                            on_progress=print)
            saved.write_text(json.dumps(measures[inst.key], indent=1), encoding="utf-8")

        needs, outcome = plan[arm]
        record = RunRecord(run_no=1, condition=f"replication_{arm}", members_by_group={},
                           transcript=[], votes=[], measures={BASELINE: measures},
                           instruments={i.key: i.fingerprint for i in plan[arm]})
        fitted = prototype_by_dimension([record], needs, outcome)
        table = compare(arm, fitted)

        title = {"a": "Table 13 (5a): FFNI generic -> ILT",
                 "b": "Table 3 Model 2 (5c): FFNI work -> effectiveness of descriptions"}[arm]
        print(f"\n{title}   n = {table[0]['n']}")
        print(f"  {'need':<12}{'dimension':<26}{'paper':>7}{'beta':>8}{'p':>8}  replicated")
        for t in table:
            star = "*" if t["paper_significant"] else " "
            print(f"  {t['need']:<12}{t['dimension']:<26}{t['paper_beta']:>6.2f}{star}"
                  f"{t['beta']:>8.2f}{t['p']:>8.3f}  {'yes' if t['replicated'] else 'NO'}")
        hits = sum(t["replicated"] for t in table)
        print(f"  {hits}/{len(table)} cells replicate  (* = significant in the paper)\n")
        (folder / "summary.json").write_text(json.dumps(
            {"arm": arm, "title": title, "cells": table, "fit": fitted}, indent=1,
            default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
