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
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))
os.chdir(_PROJECT_DIR)  # TinyTroupe reads config.ini from the CWD

from analysis import (  # noqa: E402
    need_outcome_links, summarize_contrast, summarize_measure_check, summarize_mediation,
    summarize_needs, summarize_validation,
)
from config import RunConfig  # noqa: E402
from instrument import BASELINE  # noqa: E402
from pipeline import load_records, run_condition, run_measure_check  # noqa: E402
from render import (  # noqa: E402
    plot_contrast, render_contrast, render_layers, render_mediation, render_measure_check,
    render_needs, render_validation, save_summary,
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

    needs = study.self_report
    if needs and any(r.measures for r in records):
        need_summary = summarize_needs(study, records, needs)
        render_needs(study, need_summary)
        summary["needs"] = need_summary

        links = need_outcome_links(
            study, records, needs,
            ideals=study.prototype,
            effectiveness=study.candidate_rating,
            contrast=condition.contrast,
        )
        render_layers(study, links)
        summary["layers"] = links

    save_summary(summary, out, condition.key)
    plot_contrast(study, condition, summary, out)


def cmd_measure_check(args: argparse.Namespace) -> None:
    """Is the self-report instrument usable on these agents, before a full study is paid for?"""
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    needs = study.self_report
    if needs is None:
        raise SystemExit(f"Study '{study.name}' has no self-report instrument to check.")

    out = _output_dir(config, study, "measure_check")
    setup_file_logging(out / "logs")
    print(f"\nMeasure check — {study.title} / {needs.title}")
    print(f"  Model: {config.survey_model}   Personas: {study.personas_dir}\n")

    record = run_measure_check(study, config, on_progress=print)
    summary = summarize_measure_check(study, record, needs)
    passed = render_measure_check(study, summary)
    save_summary(summary, out, "measure_check")
    if not passed:
        sys.exit(1)


def cmd_mediate(args: argparse.Namespace) -> None:
    """H6/H7: pool both conditions' checkpoints and test the indirect path."""
    config = RunConfig.from_ini(_PROJECT_DIR / "config.ini")
    study = load_study(args.study)
    needs = study.self_report
    if needs is None:
        raise SystemExit(f"Study '{study.name}' has no self-report instrument to mediate through.")
    if BASELINE not in needs.timing:
        raise SystemExit(
            f"'{needs.key}' is not administered at baseline, so there is no induced change "
            f"to mediate through — H6's mediator is post minus baseline, not the level."
        )

    by_condition = {
        key: load_records(_output_dir(config, study, key)) for key in study.conditions
    }
    for key, records in by_condition.items():
        print(f"  {key}: {len(records)} runs")

    med = summarize_mediation(
        study, by_condition, needs, need=args.need, outcome_group=args.group,
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
