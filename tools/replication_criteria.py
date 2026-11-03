"""Judge the Study 5 replication cells by several replication criteria, not only significance.

Criteria, per cell:
  A  same sign and p < .05 where the paper is significant; p >= .05 where it is null
     (the rule in replicate_study5.py, Open Science Collaboration, 2015)
  C  our estimate inside the paper's 95% prediction interval (Patil, Peng & Leek, 2016):
     r on Fisher z with SE sqrt(2/(n-3)); beta as paper +/- 1.96 sqrt(SE_paper^2 + SE_ours^2)

Paper values: Table 13 (5a: r, b, SE of b, beta; SE of beta = SE_b * beta / b) and Table 3
(5c: Model 1 beta = r, Model 2 beta and p). For the two Model 2 cells reported as p < .001,
and for |beta| < .05, the paper's SE of beta is unrecoverable from p; the median of the
other cells (.054) stands in.

    python tools/replication_criteria.py
"""
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent / "results" / "replication"
TABLE13 = {  # (r, b, SE_b, beta)
    ("protection", "strength"): (.38, .35, .12, .26), ("status", "tyranny"): (.31, .44, .11, .32),
    ("status", "masculinity"): (.22, .25, .10, .19), ("status", "well_groomed"): (.37, .46, .12, .30),
    ("vision", "sensitivity"): (.43, .33, .16, .20), ("vision", "dedication"): (.57, .38, .11, .30),
    ("vision", "charisma"): (.47, .29, .15, .19), ("vision", "creativity"): (.46, .34, .14, .24),
    ("expertise", "sensitivity"): (.46, .49, .13, .32), ("expertise", "charisma"): (.48, .32, .12, .22),
    ("expertise", "intelligence"): (.35, .27, .11, .21), ("fairness", "dedication"): (.56, .39, .12, .25),
    ("fairness", "intelligence"): (.38, .44, .14, .26), ("fairness", "ethics"): (.44, .53, .15, .29),
}
TABLE3 = {  # (Model 1 beta = r, Model 2 beta, Model 2 p; None = p < .001)
    ("protection", "safety"): (.20, .05, .358), ("protection", "authoritarianism"): (-.01, .01, .904),
    ("affiliation", "benevolence"): (.31, .10, .048), ("affiliation", "team_building"): (.46, .36, None),
    ("status", "narcissism"): (.03, .04, .457), ("status", "authoritarianism"): (-.02, -.02, .672),
    ("status", "dominance"): (-.05, .02, .771), ("vision", "vision_communication"): (.32, .18, .001),
    ("vision", "high_expectation"): (.28, .10, .060), ("expertise", "competence"): (.22, .08, .161),
    ("expertise", "intellectual_stimulation"): (.31, .13, .015),
    ("fairness", "moral_character"): (.36, .25, None), ("fairness", "virtue"): (.26, .08, .136),
}
FALLBACK_SE = .054


def se_beta(beta: float, p: float, df: int) -> float:
    return abs(beta) / stats.t.isf(p / 2, df)


def judge(arm: str) -> list[dict]:
    rows = []
    for c in json.loads((ROOT / arm / "summary.json").read_text())["cells"]:
        key, n = (c["need"], c["dimension"]), c["n"]
        if arm == "a":
            r_p, b, se_b, beta_p = TABLE13[key]
            se_p = se_b * beta_p / b
        else:
            r_p, beta_p, p_p = TABLE3[key]
            se_p = FALLBACK_SE if p_p is None or abs(beta_p) < .05 else se_beta(beta_p, p_p, n - 7)
        half_r = 1.96 * np.sqrt(2 / (n - 3))
        r_pi = tuple(np.tanh(np.arctanh(r_p) + s * half_r) for s in (-1, 1))
        half_b = 1.96 * np.hypot(se_p, se_beta(c["beta"], c["p"], n - 7))
        b_pi = (beta_p - half_b, beta_p + half_b)
        rows.append({"cell": f"{key[0]} -> {key[1]}", "r_paper": r_p, "r": c["r"], "r_pi": r_pi,
                     "r_in": r_pi[0] <= c["r"] <= r_pi[1], "beta_paper": beta_p, "beta": c["beta"],
                     "beta_pi": b_pi, "beta_in": b_pi[0] <= c["beta"] <= b_pi[1], "A": c["replicated"]})
    return rows


def main() -> None:
    for arm in ("a", "b"):
        rows = judge(arm)
        print(f"== arm {arm.upper()}")
        print(f"{'cell':38s} r paper  ours  PI             | beta paper  ours  PI             | A")
        for r in rows:
            print(f"{r['cell']:38s} {r['r_paper']:5.2f} {r['r']:5.2f} [{r['r_pi'][0]:5.2f},{r['r_pi'][1]:5.2f}] "
                  f"{'in ' if r['r_in'] else 'out'} | {r['beta_paper']:5.2f} {r['beta']:5.2f} "
                  f"[{r['beta_pi'][0]:5.2f},{r['beta_pi'][1]:5.2f}] {'in ' if r['beta_in'] else 'out'} | "
                  f"{'yes' if r['A'] else 'no'}")
        n = len(rows)
        print(f"  A {sum(r['A'] for r in rows)}/{n}  C(r) {sum(r['r_in'] for r in rows)}/{n}  "
              f"C(beta) {sum(r['beta_in'] for r in rows)}/{n}  "
              f"A and C(beta) {sum(r['A'] and r['beta_in'] for r in rows)}/{n}  "
              f"r above PI {sum(r['r'] > r['r_pi'][1] for r in rows)}/{n}\n")


if __name__ == "__main__":
    main()
