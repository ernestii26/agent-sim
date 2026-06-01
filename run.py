"""Prestige vs Dominance Leadership Simulation — entry point.

Usage (from any directory):
    python3 /data1/ernestii26/mbti_baseline/run.py --step1
    python3 /data1/ernestii26/mbti_baseline/run.py --step2
    python3 run.py --step1   # from inside the project dir
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# CWD = project root so TinyTroupe finds config.ini and applies [Logging] settings.
# src/ on sys.path so all modules (pipeline, discussion, etc.) import by bare name.
_PROJECT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _PROJECT_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
os.chdir(_PROJECT_DIR)

_CONFIG_PATH = _PROJECT_DIR / "config.ini"


def _get_config():
    from pipeline import BaselineConfig
    if not _CONFIG_PATH.exists():
        raise SystemExit(f"config.ini not found at {_CONFIG_PATH}. Set API_KEY before running.")
    return BaselineConfig.from_ini(_CONFIG_PATH)


def run_step1() -> None:
    from pipeline import step1_validate_silence
    from reporting import plot_step1, print_step1_report, save_step1_result
    from runtime import setup_file_logging

    config = _get_config()
    setup_file_logging(Path(config.output_dir) / "logs")
    print(f"\nStep 1: silence mechanism validation")
    print(f"  Model   : {config.discussion_model}")
    print(f"  Runs    : {config.step1_runs}  Rounds: {config.step1_rounds}")
    print(f"  Personas: {config.personas_dir}\n")

    result = step1_validate_silence(config, on_progress=print)
    print_step1_report(result)
    save_step1_result(result, config.output_dir)
    plot_step1(result, config.output_dir)

    if not result["passed"]:
        print(
            "\nStep 1 FAILED — silence mechanism not reliable.\n"
            "You may still run Step 2, but DV2 (speech rate) will be less meaningful."
        )
        sys.exit(1)
    else:
        print("\nStep 1 PASSED — proceed to Step 2 when ready.")


def run_step3() -> None:
    from pipeline import step3_run_simulation
    from reporting import plot_step2, print_step2_report, save_step2_result
    from runtime import setup_file_logging

    config = _get_config()
    setup_file_logging(Path(config.output_dir) / "logs")
    print(f"\nStep 3: threat scenario — testing H2 (Dominance > Prestige under resource scarcity)")
    print(f"  Discussion model : {config.discussion_model}")
    print(f"  Runs             : {config.step2_runs}  Rounds: {config.step2_rounds}")
    print(f"  Personas         : {config.personas_dir}\n")

    result = step3_run_simulation(config, on_progress=print)
    print_step2_report(result)
    path = save_step2_result(result, config.output_dir)
    # rename saved file to reflect step3
    renamed = path.parent / path.name.replace("step2", "step3")
    path.rename(renamed)
    print(f"  (renamed → {renamed})")
    plot_step2(result, config.output_dir)


def run_step2() -> None:
    from pipeline import step2_run_simulation
    from reporting import plot_step2, print_step2_report, save_step2_result
    from runtime import setup_file_logging

    config = _get_config()
    setup_file_logging(Path(config.output_dir) / "logs")
    print(f"\nStep 2: Prestige vs Dominance leadership hypothesis test")
    print(f"  Discussion model : {config.discussion_model}")
    print(f"  Vote model       : {config.vote_model}")
    print(f"  Runs             : {config.step2_runs}  Rounds: {config.step2_rounds}")
    print(f"  Personas         : {config.personas_dir}\n")

    result = step2_run_simulation(config, on_progress=print)
    print_step2_report(result)
    save_step2_result(result, config.output_dir)
    plot_step2(result, config.output_dir)


def run_report(n: int | None = None) -> None:
    """Generate Step 2 report from completed checkpoints without running new simulations."""
    import json
    from reporting import plot_step2, print_step2_report, save_step2_result

    config = _get_config()
    ckpt_dir = Path(config.output_dir) / "step2_checkpoints"
    if not ckpt_dir.exists():
        raise SystemExit(f"No checkpoints found at {ckpt_dir}")

    all_ckpts = sorted(ckpt_dir.glob("run_*.json"))
    if n is not None:
        all_ckpts = all_ckpts[:n]

    run_results = [json.loads(ckpt.read_text(encoding="utf-8")) for ckpt in all_ckpts]

    if not run_results:
        raise SystemExit("No checkpoint files found.")

    print(f"\nLoaded {len(run_results)} completed runs from {ckpt_dir}")
    result = {"step": 2, "runs": len(run_results), "rounds": config.step2_rounds, "run_results": run_results}
    print_step2_report(result)
    save_step2_result(result, config.output_dir)
    plot_step2(result, config.output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prestige vs Dominance Leadership Simulation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--step1", action="store_true", help="Step 1: silence mechanism validation")
    group.add_argument("--step2", action="store_true", help="Step 2: collaborative scenario (H1: P > D)")
    group.add_argument("--step3", action="store_true", help="Step 3: threat scenario (H2: D > P under scarcity)")
    group.add_argument("--report", action="store_true", help="Generate Step 2 report from existing checkpoints")
    parser.add_argument("--runs", type=int, default=None, help="Limit report to first N checkpoints (default: all)")
    args = parser.parse_args()

    if args.step1:
        run_step1()
    elif args.step2:
        run_step2()
    elif args.step3:
        run_step3()
    elif args.report:
        run_report(n=args.runs)


if __name__ == "__main__":
    main()
