#!/usr/bin/env python3
"""How big an effect can this design actually detect?

    python3 tools/power_sim.py

Recorded output (at reps=3000) lives in docs/design-log.md — read that first, and only re-run this
when the design changes (cast size, number of voters, runs per condition).

The vote is a forced choice, so a run yields two small counts. That is a coarse
dependent variable and the question is what it can resolve at the runs config.ini asks
for. Only the electorate counts: the two candidates stand, so they do not vote
(design-log section 16), which at a cast of 5 leaves three ballots per run. Agents are modelled as picking a candidate with
probability proportional to a weight; D's weight r is the effect size, r = 1 the null.

# ponytail: weighted random choice, not a model of deliberation. It gives the null
# distribution and the mapping from "D is r times as attractive" to power, which is
# all a sample-size decision needs. Replace with resampling from real run records
# once there are 20+ of them and the observed variance is known.
"""
from __future__ import annotations

import math
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stats import paired_ttest_onesided  # noqa: E402

N_NEUTRAL = 3  # cast is 1 P + 1 D + 3 N, and only the neutrals' ballots count


def one_run(r: float, rng: random.Random) -> tuple[int, int]:
    """Votes received by D and by P in a single run, given D's relative weight r."""
    ids = ["D", "P"] + [f"N{i}" for i in range(N_NEUTRAL)]
    weight = {"D": r, "P": 1.0, **{f"N{i}": 1.0 for i in range(N_NEUTRAL)}}
    votes_d = votes_p = 0
    for voter in ids:
        pool = [c for c in ids if c != voter]
        pick = rng.choices(pool, weights=[weight[c] for c in pool])[0]
        votes_d += pick == "D"
        votes_p += pick == "P"
    return votes_d, votes_p


def welch_onesided(a: list[float], b: list[float]) -> float:
    """p for mean(a) > mean(b), independent samples. Normal approximation: the df here
    are always well above 30, where the t and normal tails agree to three decimals."""
    na, nb = len(a), len(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return 1.0
    t = (statistics.mean(a) - statistics.mean(b)) / se
    return 1 - 0.5 * (1 + math.erf(t / math.sqrt(2)))


def power_within(r: float, runs: int, reps: int = 1000, alpha: float = 0.05) -> float:
    """One condition on its own: paired t-test of D > P across runs."""
    rng = random.Random(0)
    hits = 0
    for _ in range(reps):
        a, b = zip(*(one_run(r, rng) for _ in range(runs)))
        _, p = paired_ttest_onesided([float(x) for x in a], [float(x) for x in b])
        hits += p == p and p < alpha
    return hits / reps


def power_interaction(r_threat: float, r_collab: float, runs: int,
                      reps: int = 1000, alpha: float = 0.05) -> float:
    """The actual claim: the D-P gap is wider under threat than under collaboration.
    Runs are not paired across conditions — each draws its own cast."""
    rng = random.Random(0)
    hits = 0
    for _ in range(reps):
        t = [float(d - p) for d, p in (one_run(r_threat, rng) for _ in range(runs))]
        c = [float(d - p) for d, p in (one_run(r_collab, rng) for _ in range(runs))]
        hits += welch_onesided(t, c) < alpha
    return hits / reps


def main() -> None:
    rng = random.Random(1)
    print("Single condition — H2 as its own one-sided test (D > P)\n")
    print(f"{'r':>5} {'D votes':>8} {'P votes':>8} | {'20':>6} {'40':>6} {'60':>6}   runs")
    for r in (1.0, 1.5, 2.0, 3.0, 4.0):
        sample = [one_run(r, rng) for _ in range(4000)]
        md = statistics.mean(x[0] for x in sample)
        mp = statistics.mean(x[1] for x in sample)
        cells = "  ".join(f"{power_within(r, n):>5.0%}" for n in (20, 40, 60))
        print(f"{r:>5.1f} {md:>8.2f} {mp:>8.2f} |  {cells}")
    print("\n  r = 1.0 is the null; that row is the false positive rate and should sit near 5%.")

    print("\n\nInteraction — the D-P gap under threat exceeds the gap under collaboration")
    print("Collaborative held at r = 0.7 (prestige slightly ahead, i.e. H1 holds)\n")
    print(f"{'r_threat':>9} | {'20':>6} {'40':>6} {'60':>6}   runs per condition")
    for rt in (0.7, 1.5, 2.0, 3.0, 4.0):
        cells = "  ".join(f"{power_interaction(rt, 0.7, n):>5.0%}" for n in (20, 40, 60))
        print(f"{rt:>9.1f} |  {cells}")
    print("\n  r_threat = 0.7 equals the collaborative rate; that row is the false positive rate.")


if __name__ == "__main__":
    main()
