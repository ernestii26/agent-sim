from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from persona_store import ALL_TYPES, PRESTIGE_TYPES, DOMINANCE_TYPES, NEUTRAL_TYPES


# --------------------------------------------------------------------------- #
# Step 1 reporting                                                             #
# --------------------------------------------------------------------------- #

def print_step1_report(result: dict[str, Any]) -> None:
    sr = result["speech_rate"]
    mw = result["mean_words_when_speaking"]
    names = result.get("names", {})

    print()
    print("=" * 70)
    print("PRESTIGE vs DOMINANCE — STEP 1: SILENCE MECHANISM VALIDATION")
    print("=" * 70)
    print(f"Runs: {result['runs']}  Rounds per run: {result['rounds']}")
    print(f"Design: 1P + 1D sampled per run, 8N fixed")
    print()
    print(f"{'ID':<4}  {'Group':<10}  {'Name':<32}  {'Speech Rate':>12}  {'Avg Words':>10}")
    print("-" * 74)

    def _fmt(v: float) -> str:
        return f"{v:.3f}" if not math.isnan(v) else "  n/a"

    for t in ALL_TYPES:
        if t in PRESTIGE_TYPES:
            group = "Prestige"
        elif t in DOMINANCE_TYPES:
            group = "Dominance"
        else:
            group = "Neutral"
        name = names.get(t, t)
        print(f"{t:<4}  {group:<10}  {name:<32}  {_fmt(sr[t]):>12}  {_fmt(mw[t]):>10}")

    print()
    print(f"  Neutral mean speech rate  : {result['n_mean_speech_rate']:.3f}")
    print(f"  Neutral-types < 0.80      : {result['n_some_silence_count']} / {len(NEUTRAL_TYPES)}  (need ≥ 3)")
    print(f"  (P/D shown above; sparse data because sampled 1-per-run)")
    print()
    verdict = "PASSED ✓ — silence mechanism works" if result["passed"] else "FAILED ✗ — all agents speak every turn"
    print(f"  Step 1 verdict : {verdict}")
    print("=" * 70)


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
    names = result.get("names", {})

    # Only show N types (have full data); P/D are sparse
    labels_n = [f"{t}\n{names.get(t,'').split()[0]}" for t in NEUTRAL_TYPES]
    values_n = [sr[t] if not math.isnan(sr[t]) else 0 for t in NEUTRAL_TYPES]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels_n, values_n, color="#888888", alpha=0.75)
    ax.axhline(0.80, color="red", linestyle="--", linewidth=0.9, label="Silence threshold (0.80)")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Speech Rate (proportion of turns spoken)")
    ax.set_title("Step 1: Neutral Agents Speech Rate\n(P/D omitted — sparse because sampled 1-per-run)")
    ax.legend(fontsize=9)

    for i, (val, bar) in enumerate(zip(values_n, ax.patches)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.01,
            f"{val:.2f}",
            ha="center", va="bottom", fontsize=8,
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
    pairs = [(x, y) for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    if n < 2:
        return float("nan"), float("nan")
    diffs = [x - y for x, y in pairs]
    mean_d = sum(diffs) / n
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    if var_d == 0:
        return float("nan"), float("nan")
    se = (var_d / n) ** 0.5
    t = mean_d / se

    try:
        from scipy import stats
        p = float(stats.t.sf(t, df=n - 1))
    except ImportError:
        p = float("nan")
    return t, p


def print_step2_report(result: dict[str, Any]) -> None:
    runs = result["run_results"]
    n = len(runs)

    def mean(lst: list[float]) -> float:
        valid = [x for x in lst if not math.isnan(x)]
        return sum(valid) / len(valid) if valid else float("nan")

    p_votes_per_run = [r["p_votes"] for r in runs]
    d_votes_per_run = [r["d_votes"] for r in runs]
    p_sr_per_run = [r["p_speech_rate"] for r in runs]
    d_sr_per_run = [r["d_speech_rate"] for r in runs]
    p_wpt_per_run = [r["p_words_per_turn"] for r in runs]
    d_wpt_per_run = [r["d_words_per_turn"] for r in runs]

    t_votes, p_votes_stat = _paired_ttest_onesided(p_votes_per_run, d_votes_per_run)
    t_sr, p_sr_stat = _paired_ttest_onesided(p_sr_per_run, d_sr_per_run)
    t_wpt, p_wpt_stat = _paired_ttest_onesided(p_wpt_per_run, d_wpt_per_run)

    print()
    print("=" * 70)
    print("PRESTIGE vs DOMINANCE — STEP 2: LEADERSHIP HYPOTHESIS TEST")
    print("=" * 70)
    print(f"Runs: {n}  Rounds per run: {result['rounds']}")
    print(f"Design: per run, 1P sampled from {{P1–P5}}, 1D from {{D1–D5}}, 8N fixed")
    print(f"H1: Prestige-type receives more peer votes than Dominance-type")
    print()

    # Per-run table
    print(f"  {'Run':>3}  {'P':>3}  {'D':>3}  {'P votes':>8}  {'D votes':>8}  {'Diff':>6}")
    print("  " + "-" * 42)
    for r in runs:
        diff = r["p_votes"] - r["d_votes"]
        sign = "+" if diff >= 0 else ""
        print(f"  {r['run_no']:>3}  {r['p_id']:>3}  {r['d_id']:>3}  "
              f"{r['p_votes']:>8}  {r['d_votes']:>8}  {sign}{diff:>5}")
    print()

    # Summary stats
    print(f"{'Metric':<30}  {'P mean':>8}  {'D mean':>8}  {'t':>7}  {'p':>8}")
    print("-" * 65)
    print(
        f"{'Votes per run':<30}  {mean(p_votes_per_run):>8.2f}  {mean(d_votes_per_run):>8.2f}"
        f"  {t_votes:>7.3f}  {_fmt_p(p_votes_stat):>8}"
    )
    print(
        f"{'Speech rate':<30}  {mean(p_sr_per_run):>8.3f}  {mean(d_sr_per_run):>8.3f}"
        f"  {t_sr:>7.3f}  {_fmt_p(p_sr_stat):>8}"
    )
    print(
        f"{'Words per spoken turn':<30}  {mean(p_wpt_per_run):>8.1f}  {mean(d_wpt_per_run):>8.1f}"
        f"  {t_wpt:>7.3f}  {_fmt_p(p_wpt_stat):>8}"
    )
    print()

    p_wins = sum(1 for r in runs if r["p_votes"] > r["d_votes"])
    h1_supported = (
        mean(p_votes_per_run) > mean(d_votes_per_run)
        and not math.isnan(p_votes_stat)
        and p_votes_stat < 0.05
    )
    direction = ">" if mean(p_votes_per_run) > mean(d_votes_per_run) else "≤"
    print(f"  P wins in {p_wins}/{n} runs")
    print(
        f"  H1 verdict: {'SUPPORTED' if h1_supported else 'NOT SUPPORTED'} "
        f"(Prestige {direction} Dominance in votes, p = {_fmt_p(p_votes_stat)})"
    )
    print("=" * 70)


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
        valid = [x for x in lst if not math.isnan(x)]
        return sum(valid) / len(valid) if valid else 0.0

    def std(lst: list[float]) -> float:
        valid = [x for x in lst if not math.isnan(x)]
        if len(valid) < 2:
            return 0.0
        m = mean(valid)
        return (sum((x - m) ** 2 for x in valid) / (len(valid) - 1)) ** 0.5

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    metrics = [
        ("Votes per run", [r["p_votes"] for r in runs], [r["d_votes"] for r in runs]),
        ("Speech rate", [r["p_speech_rate"] for r in runs], [r["d_speech_rate"] for r in runs]),
        ("Words per spoken turn", [r["p_words_per_turn"] for r in runs], [r["d_words_per_turn"] for r in runs]),
    ]

    for ax, (title, p_vals, d_vals) in zip(axes, metrics):
        p_m, p_s = mean(p_vals), std(p_vals)
        d_m, d_s = mean(d_vals), std(d_vals)
        ax.bar(["Prestige", "Dominance"], [p_m, d_m], yerr=[p_s, d_s],
               color=["#4C72B0", "#DD8452"], alpha=0.85, capsize=6, width=0.5)
        ax.set_ylim(bottom=0)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(title)
        label_offset = max(p_s, d_s) * 0.1 + 0.05 * max(p_m, d_m, 1)
        for x, (m, s) in enumerate([(p_m, p_s), (d_m, d_s)]):
            ax.text(x, m + s + label_offset, f"{m:.2f}",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.suptitle(
        f"Prestige vs Dominance: Leadership Emergence\n"
        f"(n={len(runs)} runs, 1P+1D sampled per run + 8N fixed, error bars = ±1 SD)",
        fontsize=11,
    )
    plt.tight_layout()
    path = out / f"baseline_step2_{timestamp}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Chart saved → {path}")


def _fmt_p(p: float) -> str:
    if math.isnan(p):
        return "n/a"
    if p < 0.001:
        return "< .001"
    return f"{p:.3f}"
