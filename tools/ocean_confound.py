"""How much of the Study 5 replication runs through the persona's OCEAN settings.

Each instrument in tools/replicate_study5.py is answered on a fresh fork, so a need and
an outcome can only correlate through what both forks share: the persona's OCEAN levels
and description. This prints, per arm, the R2 of each need and each outcome on OCEAN
(each trait as medium/high dummies, low as reference), and for each paper cell: r, r
after OCEAN is regressed out of both sides, and r between the two OCEAN-predicted parts
(whether the need and the outcome draw on the same traits). The description text is not
modelled.

    python tools/ocean_confound.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "results" / "replication"
OCEAN = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
LEVEL = {"low": 0, "medium": 1, "high": 2}
NEEDS = ["protection", "affiliation", "status", "vision", "expertise", "fairness"]
ARMS = {
    "a": ("ffni_generic.json", "ilt.json"),
    "b": ("ffni.json", "effectiveness_styles.json"),
}


def scores(answers: dict, names: list[str], ids: list[str]) -> np.ndarray:
    """Mean of each subscale's items; item keys are '<subscale>_<n>'."""
    return np.array([[np.mean([v for k, v in answers[i].items()
                               if k.rsplit("_", 1)[0] == n and isinstance(v, (int, float))])
                      for n in names] for i in ids])


def fit(x: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """R2, residual, and fitted part of y regressed on x."""
    x = np.column_stack([np.ones(len(y)), x])
    fitted = x @ np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - fitted
    return 1 - resid.var() / y.var(), resid, fitted


def arm(key: str) -> None:
    ffni_file, out_file = ARMS[key]
    ffni = json.loads((ROOT / key / ffni_file).read_text())
    out = json.loads((ROOT / key / out_file).read_text())
    ids = [i for i in ffni if i in out]
    levels = np.array([[LEVEL[json.loads((ROOT / key / "personas" / f"{i}.agent.json").read_text())
                              ["persona"]["personality"]["big_five"][t]] for t in OCEAN] for i in ids])
    dummies = np.column_stack([(levels[:, j] == v).astype(float) for j in range(5) for v in (1, 2)])
    dims = sorted({k.rsplit("_", 1)[0] for v in out.values() for k in v if not k.startswith("_")})
    needs, outcomes = scores(ffni, NEEDS, ids), scores(out, dims, ids)

    print(f"== arm {key.upper()}, n = {len(ids)}")
    for i, n in enumerate(NEEDS):
        print(f"  need {n:26s} R2(OCEAN) {fit(dummies, needs[:, i])[0]:.2f}")
    for j, d in enumerate(dims):
        y = outcomes[:, j]
        print(f"  outcome {d:23s} M {y.mean():.2f}  SD {y.std(ddof=1):.2f}  R2(OCEAN) {fit(dummies, y)[0]:.2f}")
    for c in json.loads((ROOT / key / "summary.json").read_text())["cells"]:
        x, y = needs[:, NEEDS.index(c["need"])], outcomes[:, dims.index(c["dimension"])]
        r_raw = np.corrcoef(x, y)[0, 1]
        _, rx, fx = fit(dummies, x)
        _, ry, fy = fit(dummies, y)
        # r of the OCEAN-predicted parts: do the need and the outcome draw on the same traits?
        print(f"  {c['need']} -> {c['dimension']:24s} r {r_raw:+.2f}  r|OCEAN {np.corrcoef(rx, ry)[0, 1]:+.2f}"
              f"  r(OCEAN parts) {np.corrcoef(fx, fy)[0, 1]:+.2f}  replicated {c['replicated']}")


if __name__ == "__main__":
    for key in ARMS:
        arm(key)
