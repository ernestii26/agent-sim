"""MBTI Baseline Simulation — entry point.

Usage (from any directory):
    conda run -n social-sim python /data1/ernestii26/mbti_baseline/run.py --step1
    conda run -n social-sim python /data1/ernestii26/mbti_baseline/run.py --step2
    conda run -n social-sim python run.py --step1   # from inside the project dir
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


def run_step2() -> None:
    from pipeline import step2_run_simulation
    from reporting import plot_step2, print_step2_report, save_step2_result
    from runtime import setup_file_logging

    config = _get_config()
    setup_file_logging(Path(config.output_dir) / "logs")
    print(f"\nStep 2: E vs I leadership hypothesis test")
    print(f"  Discussion model : {config.discussion_model}")
    print(f"  Vote model       : {config.vote_model}")
    print(f"  Runs             : {config.step2_runs}  Rounds: {config.step2_rounds}")
    print(f"  Personas         : {config.personas_dir}\n")

    result = step2_run_simulation(config, on_progress=print)
    print_step2_report(result)
    save_step2_result(result, config.output_dir)
    plot_step2(result, config.output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="MBTI Baseline Simulation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--step1", action="store_true", help="Step 1: silence mechanism validation")
    group.add_argument("--step2", action="store_true", help="Step 2: E vs I leadership test")
    args = parser.parse_args()

    if args.step1:
        run_step1()
    elif args.step2:
        run_step2()


if __name__ == "__main__":
    main()
