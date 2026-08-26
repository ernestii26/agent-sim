"""Numeric primitives. Knows nothing about studies, records or instruments.

NaN means "missing", never "zero" — every function here drops NaNs rather than
imputing, so a parse failure upstream stays visible as missing data.
"""
from __future__ import annotations

import math


def mean(values: list[float]) -> float:
    valid = [v for v in values if not math.isnan(v)]
    return sum(valid) / len(valid) if valid else float("nan")


def std(values: list[float]) -> float:
    valid = [v for v in values if not math.isnan(v)]
    if len(valid) < 2:
        return 0.0
    m = mean(valid)
    return (sum((v - m) ** 2 for v in valid) / (len(valid) - 1)) ** 0.5


def slope(xs: list[float], ys: list[float]) -> tuple[float, float, int]:
    """OLS slope of y on x, its correlation, and n. NaN pairs dropped."""
    pairs = [(x, y) for x, y in zip(xs, ys) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    if n < 3:
        return float("nan"), float("nan"), n
    mx, my = mean([p[0] for p in pairs]), mean([p[1] for p in pairs])
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    if sxx == 0 or syy == 0:
        return float("nan"), float("nan"), n
    return sxy / sxx, sxy / (sxx * syy) ** 0.5, n


def paired_ttest_onesided(a: list[float], b: list[float]) -> tuple[float, float]:
    """One-sided paired t-test for mean(a) > mean(b). NaN pairs are skipped."""
    pairs = [(x, y) for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    if n < 2:
        return float("nan"), float("nan")
    diffs = [x - y for x, y in pairs]
    mean_d = sum(diffs) / n
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    if var_d == 0:
        return float("nan"), float("nan")
    t = mean_d / (var_d / n) ** 0.5
    try:
        from scipy import stats
        p = float(stats.t.sf(t, df=n - 1))
    except ImportError:
        p = float("nan")
    return t, p


def cronbach_alpha(rows: list[list[float]]) -> float:
    """Alpha over respondents x items. NaN when there are too few rows or no variance."""
    rows = [r for r in rows if r and not any(math.isnan(v) for v in r)]
    k = len(rows[0]) if rows else 0
    if len(rows) < 3 or k < 2:
        return float("nan")
    item_var = sum(std([r[i] for r in rows]) ** 2 for i in range(k))
    total_var = std([sum(r) for r in rows]) ** 2
    if total_var == 0:
        return float("nan")
    return (k / (k - 1)) * (1 - item_var / total_var)


def partial_betas(
    predictors: list[list[float]], outcome: list[float]
) -> tuple[list[float], list[float], float, int]:
    """Standardised betas, each predictor's delta R2, the model R2, and n.

    Fits `outcome` on every column of `predictors` at once. A bivariate correlation
    cannot test what the source paper tested: its six needs intercorrelate .60-.72, so
    every need correlates with every prototype dimension at p < .001 (Sheng et al.,
    Table 13, "Correlation r" column). Only the increment over the other five separates
    them — protection reaches Strength at delta R2 = .03**, while the same table's
    bivariate column gives all six needs .26 to .38.

    delta R2 for a predictor is the full model's R2 minus the R2 of the same model
    without it, which is the hierarchical regression the paper reports. Rows with any
    missing value are dropped listwise.
    """
    import numpy as np

    x = np.asarray(predictors, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if x.ndim != 2 or x.shape[0] != y.shape[0] or x.size == 0:
        return [], [], float("nan"), 0

    keep = np.isfinite(x).all(axis=1) & np.isfinite(y)
    x, y = x[keep], y[keep]
    n, k = x.shape
    nan_k = [float("nan")] * k
    if n <= k + 1:
        return nan_k, nan_k, float("nan"), int(n)

    # Standardised, so the fit needs no intercept and the coefficients are betas. A
    # predictor with no variance becomes a zero column: it contributes nothing and
    # cannot divide by zero.
    sd = x.std(axis=0)
    xs = np.divide(x - x.mean(axis=0), np.where(sd == 0, 1.0, sd))
    xs[:, sd == 0] = 0.0
    sd_y = y.std()
    if sd_y == 0:
        return nan_k, nan_k, float("nan"), int(n)
    ys = (y - y.mean()) / sd_y

    def fit(columns: list[int]) -> tuple[np.ndarray, float]:
        if not columns:
            return np.zeros(0), 0.0
        a = xs[:, columns]
        beta = np.linalg.lstsq(a, ys, rcond=None)[0]
        resid = ys - a @ beta
        return beta, float(1.0 - resid @ resid / (ys @ ys))

    every = list(range(k))
    beta, r2 = fit(every)
    deltas = [r2 - fit([c for c in every if c != i])[1] for i in every]
    return [float(b) for b in beta], deltas, r2, int(n)
