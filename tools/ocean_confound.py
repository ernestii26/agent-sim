"""How much of the Study 5 replication runs through the persona's OCEAN settings.

Each instrument in tools/replicate_study5.py is answered on a fresh fork, so a need and
an outcome can only correlate through what both forks share: the persona's OCEAN levels
and description. This prints, per arm, the R2 of each need and each outcome on OCEAN
(each trait as medium/high dummies, low as reference), and for each paper cell: r, r
after OCEAN is regressed out of both sides, and r between the two OCEAN-predicted parts
(whether the need and the outcome draw on the same traits), and the Model 2 beta of the
need with the OCEAN dummies added as controls. The description text is not
modelled.

    python tools/ocean_confound.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study5_tables import ARMS, DATA, NEEDS, load  # noqa: E402


def fit(x: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """R2, residual, and fitted part of y regressed on x."""
    x = np.column_stack([np.ones(len(y)), x])
    fitted = x @ np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - fitted
    return 1 - resid.var() / y.var(), resid, fitted


def beta_given(z_needs: np.ndarray, z_y: np.ndarray, controls: np.ndarray, j: int) -> tuple[float, float]:
    """Standardised beta and p of need j in Model 2 with the controls added."""
    x = np.column_stack([np.ones(len(z_y)), z_needs, controls])
    coef = np.linalg.lstsq(x, z_y, rcond=None)[0]
    resid = z_y - x @ coef
    df = len(z_y) - np.linalg.matrix_rank(x)
    se = np.sqrt(resid @ resid / df * np.linalg.pinv(x.T @ x)[1 + j, 1 + j])
    return coef[1 + j], 2 * stats.t.sf(abs(coef[1 + j] / se), df)


def arm(key: str) -> None:
    ids, _, needs, _, by_dim, levels = load(key)
    dummies = np.column_stack([(levels[:, j] == v).astype(float) for j in range(5) for v in (1, 2)])
    dims = sorted(by_dim)
    outcomes = np.column_stack([by_dim[d] for d in dims])

    print(f"== arm {key.upper()}, n = {len(ids)}")
    for i, n in enumerate(NEEDS):
        print(f"  need {n:26s} R2(OCEAN) {fit(dummies, needs[:, i])[0]:.2f}")
    for j, d in enumerate(dims):
        y = outcomes[:, j]
        print(f"  outcome {d:23s} M {y.mean():.2f}  SD {y.std(ddof=1):.2f}  R2(OCEAN) {fit(dummies, y)[0]:.2f}")
    for c in json.loads((DATA / key / "summary.json").read_text())["cells"]:
        x, y = needs[:, NEEDS.index(c["need"])], outcomes[:, dims.index(c["dimension"])]
        r_raw = np.corrcoef(x, y)[0, 1]
        _, rx, fx = fit(dummies, x)
        _, ry, fy = fit(dummies, y)
        z = lambda a: (a - a.mean(axis=0)) / a.std(axis=0)
        b, p = beta_given(z(needs), z(y), dummies, NEEDS.index(c["need"]))
        # r of the OCEAN-predicted parts: do the need and the outcome draw on the same traits?
        print(f"  {c['need']} -> {c['dimension']:24s} r {r_raw:+.2f}  r|OCEAN {np.corrcoef(rx, ry)[0, 1]:+.2f}"
              f"  r(OCEAN parts) {np.corrcoef(fx, fy)[0, 1]:+.2f}  beta {c['beta']:+.2f}"
              f"  beta|OCEAN {b:+.2f} (p {p:.3f})  replicated {c['replicated']}")


if __name__ == "__main__":
    for key in ARMS:
        arm(key)
