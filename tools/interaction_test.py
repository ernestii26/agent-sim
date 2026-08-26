#!/usr/bin/env python3
"""Does threat's D-P vote gap exceed collaborative's?

    python3 tools/interaction_test.py [study]

The study used to be hardcoded to pd_matched, which meant asking about ffni_mediation
silently answered about pd_matched instead — with a different n and a different design,
and nothing in the output saying so.

design-log.md decision 3 named this as the test that actually matches the H2 claim —
per-condition t-tests (what run.py report prints) are descriptive on their own; this is
confirmatory. Reads the latest saved summary JSON for each condition, so run both
conditions through `run.py run` first.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import statistics


def latest_summary(study: str, condition: str) -> dict:
    files = sorted(glob.glob(f"results/{study}/{condition}/{condition}_*.json"))
    if not files:
        raise SystemExit(f"No summary found for {study}/{condition} — run it first.")
    return json.loads(open(files[-1]).read())


def welch_onesided_greater(a: list[float], b: list[float]) -> tuple[float, float, float]:
    """p for mean(a) > mean(b). Normal approximation to the t-tail; fine once df is
    comfortably above 30, which two n=20 groups of this variance always clear."""
    na, nb = len(a), len(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(va / na + vb / nb)
    t = (statistics.mean(a) - statistics.mean(b)) / se
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    p = 1 - 0.5 * (1 + math.erf(t / math.sqrt(2)))
    return t, df, p


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("study", nargs="?", default="pd_matched")
    args = ap.parse_args()

    threat = latest_summary(args.study, "threat")
    collab = latest_summary(args.study, "collaborative")

    # Both per_run lists are keyed by that condition's own contrast order, so normalise
    # both to (D - P) before comparing.
    t_dp = [row["D"] - row["P"] for row in threat["per_run"]]
    c_dp = [row["D"] - row["P"] for row in collab["per_run"]]

    t, df, p = welch_onesided_greater(t_dp, c_dp)

    print(f"Interaction test ({args.study}): threat's D-P vote gap exceeds "
          f"collaborative's D-P gap\n")
    print(f"  threat       mean(D-P) = {statistics.mean(t_dp):+.2f}  "
          f"sd = {statistics.stdev(t_dp):.2f}  n = {len(t_dp)}")
    print(f"  collaborative mean(D-P) = {statistics.mean(c_dp):+.2f}  "
          f"sd = {statistics.stdev(c_dp):.2f}  n = {len(c_dp)}")
    print(f"\n  Welch t = {t:.3f}, df ~ {df:.1f}, one-sided p = {p:.5f}")
    print(f"  {'SUPPORTED' if p < 0.05 else 'NOT SUPPORTED'}")


if __name__ == "__main__":
    main()
