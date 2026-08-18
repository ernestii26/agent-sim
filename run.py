#!/usr/bin/env python3
"""Multi-agent simulation runner.

    python3 run.py list
    python3 run.py validate      <study>
    python3 run.py measure-check <study>
    python3 run.py run      <study> <condition> [--runs N] [--rounds N]
    python3 run.py report   <study> <condition>

Every theme-specific detail (groups, personas, scenarios) lives in studies/<study>/.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))
os.chdir(_PROJECT_DIR)  # TinyTroupe reads config.ini from the CWD

from config import RunConfig  # noqa: E402
from instrument import BASELINE, POST  # noqa: E402
from pipeline import load_records, run_condition  # noqa: E402
from reporting import (  # noqa: E402
    need_outcome_links, plot_contrast, render_contrast, render_layers, render_mediation,
    render_measure_check, render_needs, render_validation, save_summary, summarize_contrast,
    summarize_mediation, summarize_needs, summarize_validation,
)
from runtime import setup_file_logging  # noqa: E402
from study import Study, list_studies, load_study  # noqa: E402


def _output_dir(config: RunConfig, study: Study, condition_key: str) -> Path:
    return Path(config.output_dir) / study.name / condition_key


def cmd_list(_: argparse.Namespace) -> None:
    studies = list_studies()
    if not studies:
        raise SystemExit("No studies found in studies/")
    for name in studies:
        study = load_study(name)
        print(f"\n{name} — {study.title}")
        groups = ", ".join(
            f"{g.label}({len(g.ids)}, sample={g.sample or 'all'})" for g in study.groups.values()
        )
        print(f"  groups     : {groups}")
        for condition in study.conditions.values():
            print(f"  condition  : {condition.key:<16} {condition.hypothesis}")
    print()


def cmd_validate(args: argparse.Namespace) -> None:
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    condition = study.condition(args.condition or next(iter(study.conditions)))
    out = _output_dir(config, study, f"validate_{condition.key}")
    setup_file_logging(out / "logs")

    runs = args.runs or config.validate_runs
    rounds = args.rounds or config.validate_rounds
    print(f"\nValidating silence mechanism — {study.title} / {condition.label}")
    print(f"  Model: {config.discussion_model}   Runs: {runs}   Rounds: {rounds}\n")

    records = run_condition(
        study, condition, config,
        runs=runs, rounds=rounds, with_votes=False, output_dir=out, on_progress=print,
    )
    summary = summarize_validation(study, records)
    render_validation(study, summary)
    save_summary(summary, out, "validation")
    if not summary["passed"]:
        print("\nAgents speak on nearly every turn — speech-rate metrics will be uninformative.")
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> None:
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    condition = study.condition(args.condition)
    out = _output_dir(config, study, condition.key)
    setup_file_logging(out / "logs")

    runs = args.runs or config.runs
    rounds = args.rounds or config.rounds
    print(f"\n{study.title} — {condition.label}")
    print(f"  {condition.hypothesis}")
    print(f"  Discussion: {config.discussion_model}   Vote: {config.vote_model}")
    print(f"  Runs: {runs}   Rounds: {rounds}   Personas: {study.personas_dir}\n")

    records = run_condition(
        study, condition, config, runs=runs, rounds=rounds, output_dir=out, on_progress=print,
    )
    _report(study, condition, records, out)


def cmd_report(args: argparse.Namespace) -> None:
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    condition = study.condition(args.condition)
    out = _output_dir(config, study, condition.key)

    records = load_records(out)
    if args.runs:
        records = records[: args.runs]
    print(f"\nLoaded {len(records)} completed runs from {out / 'checkpoints'}")
    _report(study, condition, records, out)


def _report(study: Study, condition, records: list, out: Path) -> None:
    if not records:
        raise SystemExit("No completed runs to report.")
    summary = summarize_contrast(study, condition, records)
    render_contrast(study, condition, summary)

    needs = next((i for i in study.instruments if i.about == "self"), None)
    if needs and any(r.get("measures") for r in records):
        need_summary = summarize_needs(study, records, needs)
        render_needs(study, need_summary)
        summary["needs"] = need_summary

        links = need_outcome_links(
            study, records, needs,
            ideals=next((i for i in study.instruments if i.about == "prototype"), None),
            effectiveness=next((i for i in study.instruments if i.about == "each_candidate"), None),
            contrast=condition.contrast,
        )
        render_layers(study, links)
        summary["layers"] = links

    save_summary(summary, out, condition.key)
    plot_contrast(study, condition, summary, out)


def cmd_measure_check(args: argparse.Namespace) -> None:
    """Administer the self-report instrument twice per persona and judge whether it works.

    Cheap by design: no discussion, no votes. If the agents straight-line the scale or
    answer it differently every time, the whole mediation design is dead and this is the
    place to find out — before paying for a full study.
    """
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    needs = next((i for i in study.instruments if i.about == "self"), None)
    if needs is None:
        raise SystemExit(f"Study '{study.name}' has no self-report instrument to check.")

    out = _output_dir(config, study, "measure_check")
    setup_file_logging(out / "logs")
    print(f"\nMeasure check — {study.title} / {needs.title}")
    print(f"  Model: {config.survey_model}   Personas: {study.personas_dir}\n")

    from discussion import clone_participants, run_survey
    from persona_store import load_personas
    from reporting import _slope

    pool = load_personas(
        study.personas_dir,
        {pid: g.key for g in study.groups.values() for pid in g.ids},
    )
    everyone = list(pool.values())
    # Every persona answers, not just the instrument's usual targets — a check of the
    # scale itself should cover the whole cast.
    wide = replace(needs, targets=())

    administrations = []
    for pass_no in (1, 2):
        print(f"  Administration {pass_no}/2")
        administrations.append(
            run_survey(
                participants=clone_participants(everyone),
                instrument=wide,
                model=config.survey,
                on_progress=print,
            )
        )

    fake_records = [
        {"run_no": 1, "members": {}, "transcript": [], "votes": [],
         "measures": {"baseline": {needs.key: administrations[0]},
                      "post": {needs.key: administrations[1]}}}
    ]
    summary = summarize_needs(study, fake_records, needs)

    from reporting import scored
    first, second = scored(fake_records[0], BASELINE, needs), scored(fake_records[0], POST, needs)
    shared = sorted(first.keys() & second.keys())
    retest = {}
    for name in needs.subscales:
        _, r, _ = _slope(
            [first[pid].get(name, float("nan")) for pid in shared],
            [second[pid].get(name, float("nan")) for pid in shared],
        )
        retest[name] = r

    summary["test_retest"] = retest
    passed = render_measure_check(study, summary, retest)
    save_summary(summary, out, "measure_check")
    if not passed:
        sys.exit(1)


def cmd_mediate(args: argparse.Namespace) -> None:
    """H6/H7: pool both conditions' checkpoints and test the indirect path."""
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    needs = next((i for i in study.instruments if i.about == "self"), None)
    effectiveness = next((i for i in study.instruments if i.about == "each_candidate"), None)
    if needs is None or effectiveness is None:
        raise SystemExit(
            f"Study '{study.name}' needs both a self-report and an each_candidate instrument."
        )

    by_condition = {
        key: load_records(_output_dir(config, study, key)) for key in study.conditions
    }
    for key, records in by_condition.items():
        print(f"  {key}: {len(records)} runs")

    med = summarize_mediation(
        study, by_condition, needs,
        need=args.need, outcome_group=args.group, effectiveness=effectiveness,
    )
    render_mediation(study, med)
    save_summary(med, Path(config.output_dir) / study.name, f"mediation_{args.need}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show available studies and conditions").set_defaults(func=cmd_list)

    check = sub.add_parser("measure-check", help="is the survey instrument usable on these agents?")
    check.add_argument("study")
    check.set_defaults(func=cmd_measure_check)

    med = sub.add_parser("mediate", help="test the indirect path across both conditions")
    med.add_argument("study")
    med.add_argument("--need", default="protection", help="mediator subscale (default: protection)")
    med.add_argument("--group", default="D", help="endorsed group key (default: D)")
    med.set_defaults(func=cmd_mediate)

    for name, func, help_text in (
        ("validate", cmd_validate, "check the silence mechanism produces variation"),
        ("run", cmd_run, "run a condition and report"),
        ("report", cmd_report, "re-report from saved checkpoints, no API calls"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("study")
        p.add_argument("condition", nargs="?" if name == "validate" else None)
        p.add_argument("--runs", type=int, default=None, help="override number of runs")
        if name != "report":
            p.add_argument("--rounds", type=int, default=None, help="override rounds per run")
        p.set_defaults(func=func)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
