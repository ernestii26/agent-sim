from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from persona_store import ALL_TYPES, E_TYPES, I_TYPES


# --------------------------------------------------------------------------- #
# Step 1 reporting                                                             #
# --------------------------------------------------------------------------- #

def print_step1_report(result: dict[str, Any]) -> None:
    sr = result["speech_rate"]
    mw = result["mean_words_when_speaking"]
    names = result.get("names", {})

    print()
    print("=" * 65)
    print("MBTI BASELINE — STEP 1: SILENCE MECHANISM VALIDATION")
    print("=" * 65)
    print(f"Runs: {result['runs']}  Rounds per run: {result['rounds']}")
    print()
    print(f"{'Type':<6}  {'Name':<35}  {'Speech Rate':>12}  {'Avg Words':>10}")
    print("-" * 70)
    for t in ALL_TYPES:
        group = "E" if t in E_TYPES else "I"
        name = names.get(t, t)
        print(f"{t}({group}) {name:<35}  {sr[t]:>11.3f}  {mw[t]:>10.1f}")
    print()
    print(f"  E mean speech rate : {result['e_mean_speech_rate']:.3f}")
    print(f"  I mean speech rate : {result['i_mean_speech_rate']:.3f}")
    print(f"  E − I gap          : {result['gap']:+.3f}  (need ≥ 0.10)")
    print(f"  I-types < 0.70     : {result['i_below_70_count']} / 5  (need ≥ 3)")
    print(f"  E-types > 0.50     : {result['e_above_50_count']} / 5  (need ≥ 3)")
    print()
    verdict = "PASSED ✓ — proceed to Step 2" if result["passed"] else "FAILED ✗ — fall back to forced turns"
    print(f"  Step 1 verdict     : {verdict}")
    print("=" * 65)


def save_step1_result(result: dict[str, Any], output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"baseline_step1_{timestamp}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStep 1 result saved → {path}")
    return path


def plot_step1(result: dict[str, Any], output_dir: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping chart.")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    sr = result["speech_rate"]
    labels = [f"{t}\n({'E' if t in E_TYPES else 'I'})" for t in ALL_TYPES]
    values = [sr[t] for t in ALL_TYPES]
    colors = ["#4C72B0" if t in E_TYPES else "#DD8452" for t in ALL_TYPES]

    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(labels, values, color=colors, alpha=0.85)
    threshold_i = ax.axhline(0.70, color="red", linestyle="--", linewidth=0.9, label="I threshold (0.70)")
    threshold_e = ax.axhline(0.50, color="green", linestyle="--", linewidth=0.9, label="E threshold (0.50)")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Speech Rate (proportion of turns spoken)")
    ax.set_title("Step 1: Speech Rate by Persona\n(Blue=Extraverted, Orange=Introverted)")

    legend_elements = [
        Patch(facecolor="#4C72B0", alpha=0.85, label="E-type"),
        Patch(facecolor="#DD8452", alpha=0.85, label="I-type"),
        threshold_i,
        threshold_e,
    ]
    ax.legend(handles=legend_elements, fontsize=9)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.01,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()
    path = out / f"baseline_step1_speech_rate_{timestamp}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Chart saved → {path}")


# --------------------------------------------------------------------------- #
# Step 2 reporting                                                             #
# --------------------------------------------------------------------------- #

def _paired_ttest_onesided(a: list[float], b: list[float]) -> tuple[float, float]:
    """One-sided paired t-test for H1: mean(a) > mean(b). NaN pairs are skipped."""
    import math

    pairs = [(x, y) for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    if n < 2:
        return float("nan"), float("nan")
    diffs = [x - y for x, y in pairs]
    mean_d = sum(diffs) / n
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    if var_d == 0:
        return float("nan"), float("nan")
    se = math.sqrt(var_d / n)
    t = mean_d / se

    try:
        from scipy import stats
        p = float(stats.t.sf(t, df=n - 1))
    except ImportError:
        p = float("nan")
    return t, p


def print_step2_report(result: dict[str, Any]) -> None:
    runs = result["run_results"]

    e_votes_per_run = [r["e_votes"] for r in runs]
    i_votes_per_run = [r["i_votes"] for r in runs]
    e_sr_per_run = [r["e_speech_rate"] for r in runs]
    i_sr_per_run = [r["i_speech_rate"] for r in runs]
    e_wpt_per_run = [r["e_words_per_turn"] for r in runs]
    i_wpt_per_run = [r["i_words_per_turn"] for r in runs]

    n = len(runs)

    def mean(lst: list[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    t_votes, p_votes = _paired_ttest_onesided(e_votes_per_run, i_votes_per_run)
    t_sr, p_sr = _paired_ttest_onesided(e_sr_per_run, i_sr_per_run)
    t_wpt, p_wpt = _paired_ttest_onesided(e_wpt_per_run, i_wpt_per_run)

    print()
    print("=" * 65)
    print("MBTI BASELINE — STEP 2: E vs I LEADERSHIP HYPOTHESIS TEST")
    print("=" * 65)
    print(f"Runs: {n}  Rounds per run: {result['rounds']}")
    print(f"H1: E-types receive more peer votes than I-types")
    print()
    print(f"{'Metric':<30}  {'E mean':>8}  {'I mean':>8}  {'t':>7}  {'p':>8}")
    print("-" * 65)
    print(
        f"{'Votes per run':<30}  {mean(e_votes_per_run):>8.2f}  {mean(i_votes_per_run):>8.2f}"
        f"  {t_votes:>7.3f}  {_fmt_p(p_votes):>8}"
    )
    print(
        f"{'Speech rate':<30}  {mean(e_sr_per_run):>8.3f}  {mean(i_sr_per_run):>8.3f}"
        f"  {t_sr:>7.3f}  {_fmt_p(p_sr):>8}"
    )
    print(
        f"{'Words per spoken turn':<30}  {mean(e_wpt_per_run):>8.1f}  {mean(i_wpt_per_run):>8.1f}"
        f"  {t_wpt:>7.3f}  {_fmt_p(p_wpt):>8}"
    )
    print()
    h1_supported = mean(e_votes_per_run) > mean(i_votes_per_run) and (not _is_nan(p_votes)) and p_votes < 0.05
    print(f"  H1 verdict: {'SUPPORTED' if h1_supported else 'NOT SUPPORTED'} "
          f"(E votes {'>' if mean(e_votes_per_run) > mean(i_votes_per_run) else '≤'} I votes, "
          f"p = {_fmt_p(p_votes)})")
    print("=" * 65)


def save_step2_result(result: dict[str, Any], output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"baseline_step2_{timestamp}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStep 2 result saved → {path}")
    return path


def plot_step2(result: dict[str, Any], output_dir: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping chart.")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs = result["run_results"]

    def mean(lst: list[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    def std(lst: list[float]) -> float:
        m = mean(lst)
        return (sum((x - m) ** 2 for x in lst) / max(len(lst) - 1, 1)) ** 0.5

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    metrics = [
        ("Votes per run", [r["e_votes"] for r in runs], [r["i_votes"] for r in runs]),
        ("Speech rate", [r["e_speech_rate"] for r in runs], [r["i_speech_rate"] for r in runs]),
        ("Words per spoken turn", [r["e_words_per_turn"] for r in runs], [r["i_words_per_turn"] for r in runs]),
    ]

    for ax, (title, e_vals, i_vals) in zip(axes, metrics):
        e_m, e_s = mean(e_vals), std(e_vals)
        i_m, i_s = mean(i_vals), std(i_vals)
        ax.bar(["E-types", "I-types"], [e_m, i_m], yerr=[e_s, i_s],
               color=["#4C72B0", "#DD8452"], alpha=0.85, capsize=6, width=0.5)
        ax.set_ylim(bottom=0)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(title)
        label_offset = max(e_s, i_s) * 0.1 + 0.05 * max(e_m, i_m, 1)
        for x, (m, s) in enumerate([(e_m, e_s), (i_m, i_s)]):
            ax.text(x, m + s + label_offset, f"{m:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.suptitle(
        f"MBTI Baseline Step 2: E vs I Leadership\n(n={len(runs)} runs, error bars = ±1 SD)",
        fontsize=12,
    )
    plt.tight_layout()
    path = out / f"baseline_step2_{timestamp}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Chart saved → {path}")


def _fmt_p(p: float) -> str:
    if _is_nan(p):
        return "n/a"
    if p < 0.001:
        return "< .001"
    return f"{p:.3f}"


def _is_nan(x: float) -> bool:
    import math
    return math.isnan(x)
