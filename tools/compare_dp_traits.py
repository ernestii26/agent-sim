"""Compare dp_check (full persona) with dp_check_traits (P and D reduced to traits), routine.

Both studies share the sampler seed, so run i has the same task and neutrals in each;
only P's and D's persona text differs. Prints, run by run, the neutrals' mean rating of
D and P on each scale in both versions, and the paired t-test on D - P in each version.

    python tools/compare_dp_traits.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from analysis import subscale_scores  # noqa: E402
from study import load_study  # noqa: E402

RATING = load_study("dp_check").candidate_rating
VERSIONS = {"full": "dp_check", "traits": "dp_check_traits"}


def runs(study: str) -> dict[int, dict]:
    out = {}
    for path in sorted((ROOT / "results" / study / "collaborative" / "checkpoints").glob("run_*.json")):
        record = json.loads(path.read_text())
        scores = {}
        for group in ("P", "D"):
            pid = record["members"][group][0]
            rated = [subscale_scores(by[pid], RATING) for by in record["measures"]["post"]["dp_peer"].values()
                     if pid in by]
            scores[group] = {s: float(np.mean([r[s] for r in rated])) for s in ("dominance", "prestige")}
        out[record["run_no"]] = {"id": record["members"]["D"][0], "task": record["task"]["name"], **scores}
    return out


def main() -> None:
    data = {v: runs(s) for v, s in VERSIONS.items()}
    shared = sorted(set(data["full"]) & set(data["traits"]))
    print(f"{len(shared)} runs in both versions\n")
    print("run D    task                              | dominance D/P full   traits | prestige P/D full   traits")
    for n in shared:
        f, t = data["full"][n], data["traits"][n]
        print(f"{n:3d} {f['id']:4s} {f['task'][:33]:33s} | {f['D']['dominance']:4.2f}/{f['P']['dominance']:4.2f}"
              f"  {t['D']['dominance']:4.2f}/{t['P']['dominance']:4.2f} | {f['P']['prestige']:4.2f}/{f['D']['prestige']:4.2f}"
              f"  {t['P']['prestige']:4.2f}/{t['D']['prestige']:4.2f}")
    print()
    for scale, (hi, lo) in (("dominance", ("D", "P")), ("prestige", ("P", "D"))):
        for v in VERSIONS:
            a = np.array([data[v][n][hi][scale] for n in shared])
            b = np.array([data[v][n][lo][scale] for n in shared])
            t, p = stats.ttest_rel(a, b)
            d_av = (a.mean() - b.mean()) / ((a.std(ddof=1) + b.std(ddof=1)) / 2)
            print(f"{scale:9s} {v:6s} {hi} {a.mean():.2f}  {lo} {b.mean():.2f}  t {t:5.2f}  p {p:.4f}  d_av {d_av:5.2f}")
        # did the change to traits-only move the expected-direction gap?
        gap = {v: np.array([data[v][n][hi][scale] - data[v][n][lo][scale] for n in shared]) for v in VERSIONS}
        t, p = stats.ttest_rel(gap["traits"], gap["full"])
        print(f"{scale:9s} gap change traits - full: {np.mean(gap['traits'] - gap['full']):+.2f}  t {t:5.2f}  p {p:.4f}\n")


if __name__ == "__main__":
    main()
