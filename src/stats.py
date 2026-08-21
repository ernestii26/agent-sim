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
