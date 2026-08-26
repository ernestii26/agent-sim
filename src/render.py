"""Turn summary dicts into terminal tables, JSON files and charts.

Nothing here recomputes anything — if a number is not in the summary it does not
get printed, so the saved JSON and the printed table can never disagree.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from analysis import SILENCE_THRESHOLD, weak_subscales
from instrument import BASELINE, POST
from stats import mean, std
from study import Condition, Study


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}" if not math.isnan(value) else "n/a"


def _fmt_p(p: float) -> str:
    if math.isnan(p):
        return "n/a"
    return "< .001" if p < 0.001 else f"{p:.3f}"


def render_validation(study: Study, summary: dict[str, Any]) -> None:
    print()
    print("=" * 74)
    print(f"{study.title.upper()} — SILENCE MECHANISM VALIDATION")
    print("=" * 74)
    print(f"Runs: {summary['runs']}")
    print()
    print(f"{'ID':<5}  {'Group':<12}  {'Turns':>6}  {'Speech Rate':>12}  {'Avg Words':>10}")
    print("-" * 74)
    for pid, m in summary["personas"].items():
        print(
            f"{pid:<5}  {study.label_of(study.group_of(pid)):<12}  {int(m['turns']):>6}  "
            f"{_fmt(m['speech_rate']):>12}  {_fmt(m['mean_words'], 1):>10}"
        )
    print()
    print(f"  Mean speech rate (always-present groups) : {_fmt(summary['mean_speech_rate'])}")
    print(
        f"  Personas below {SILENCE_THRESHOLD:.2f}                     : "
        f"{summary['quiet_personas']} / {summary['judged_personas']}  (need >= 3)"
    )
    print()
    verdict = "PASSED — silence mechanism works" if summary["passed"] else "FAILED — agents never stay quiet"
    print(f"  Verdict : {verdict}")
    print("=" * 74)


def render_contrast(study: Study, condition: Condition, summary: dict[str, Any]) -> None:
    a, b = summary["contrast"]
    label_a, label_b = study.label_of(a), study.label_of(b)

    print()
    print("=" * 74)
    print(f"{study.title.upper()} — {condition.label.upper()} CONDITION")
    print("=" * 74)
    print(f"Runs: {summary['runs']}")
    if summary["hypothesis"]:
        print(f"Hypothesis: {summary['hypothesis']}")
    print()

    if summary.get("electorate"):
        voting = ", ".join(study.label_of(g) for g in summary["electorate"])
        cv = summary["candidate_votes"]
        print(f"Electorate: {voting} only — the two contrasted groups stand, so they do not vote.")
        print(f"  (set aside: {label_b} gave {label_a} {cv[a]} votes, "
              f"{label_a} gave {label_b} {cv[b]})")
        print()

    print(f"  {'Run':>3}  {label_a + ' votes':>16}  {label_b + ' votes':>16}  {'Diff':>6}")
    print("  " + "-" * 48)
    for row in summary["per_run"]:
        print(
            f"  {row['run_no']:>3}  {int(row[a]):>16}  {int(row[b]):>16}  {row[a] - row[b]:>+6.0f}"
        )
    print()

    print(f"{'Metric':<24}  {label_a:>10}  {label_b:>10}  {'t':>8}  {'p':>8}")
    print("-" * 68)
    for key, title in (
        ("votes", "Votes per run"),
        ("speech_rate", "Speech rate"),
        ("words_per_turn", "Words per spoken turn"),
    ):
        m = summary["metrics"][key]
        print(
            f"{title:<24}  {_fmt(m[a]['mean'], 2):>10}  {_fmt(m[b]['mean'], 2):>10}"
            f"  {_fmt(m['t']):>8}  {_fmt_p(m['p']):>8}"
        )

    print()
    print(f"  {label_a} wins in {summary['wins']}/{summary['runs']} runs")
    print(
        f"  Verdict: {'SUPPORTED' if summary['supported'] else 'NOT SUPPORTED'} "
        f"({label_a} vs {label_b} votes, p = {_fmt_p(summary['metrics']['votes']['p'])})"
    )
    _render_sampled_speech(study, summary)
    print("=" * 74)


def _render_sampled_speech(study: Study, summary: dict[str, Any]) -> None:
    """Did the contrasted personas actually speak? run.py validate skips them."""
    sampled = {g.key for g in study.groups.values() if g.sample is not None}
    rows = [(pid, m) for pid, m in summary.get("personas", {}).items()
            if study.group_of(pid) in sampled]
    if not rows:
        return
    print()
    print(f"{'ID':<5}  {'Group':<12}  {'Runs in':>7}  {'Speech Rate':>12}  {'Avg Words':>10}")
    print("-" * 68)
    mute = 0
    for pid, m in rows:
        rate = m["speech_rate"]
        flag = "  <- barely spoke" if rate <= 1 / 3 else ""
        mute += rate <= 1 / 3
        print(f"{pid:<5}  {study.label_of(study.group_of(pid)):<12}  "
              f"{int(m['turns']):>7}  {_fmt(rate):>12}  {_fmt(m['mean_words'], 1):>10}{flag}")
    if mute:
        print(f"\n  {mute} contrasted persona(s) spoke in a third of their turns or less — "
              f"raise --rounds, or those runs carry no impression to vote on.")


def render_needs(study: Study, summary: dict[str, Any]) -> None:
    print()
    print("=" * 88)
    print(f"{study.title.upper()} — {summary['instrument'].upper()} ({summary['runs']} runs)")
    print("=" * 88)
    print(f"{'Subscale':<18}  {'T1 mean':>9}  {'T2 mean':>9}  {'delta':>9}  "
          f"{'delta SD':>9}  {'n_d':>5}  {'alpha':>7}")
    print("-" * 88)
    for name, s in summary["subscales"].items():
        print(
            f"{name:<18}  {_fmt(s['baseline_mean'], 2):>9}  {_fmt(s['post_mean'], 2):>9}  "
            f"{_fmt(s['delta_mean'], 2):>9}  {_fmt(s['delta_sd'], 2):>9}  "
            f"{s['delta_n']:>5}  {_fmt(s['alpha'], 2):>7}"
        )
    sl = summary["straight_lining"]
    print()
    print(f"  Straight-lining  T1 {_fmt(sl[BASELINE], 2)}   T2 {_fmt(sl[POST], 2)}"
          "   (share answering every item identically; high means the scale is dead)")
    print("=" * 88)


def render_layers(study: Study, links: dict[str, Any]) -> None:
    contrast = links.get("contrast")
    label_a = study.label_of(contrast[0]) if contrast else "A"
    label_b = study.label_of(contrast[1]) if contrast else "B"
    print()
    print("=" * 88)
    print("COGNITION vs EVALUATION — need score as predictor")
    print("=" * 88)
    print("Cognition = matching leader-ideal prototype rating.  Evaluation = effectiveness rating.")
    print("The source paper found protection/status predict the prototype but NOT effectiveness.")
    print()
    print("Bivariate r is reported for contrast only. The needs intercorrelate, so every need")
    print("tracks every dimension; beta and delta R2 hold the other five constant, which is")
    print("the increment H4 is actually about (Sheng et al., Table 13).")
    print()
    print(f"{'Need':<13}  {'PROTOTYPE':>21}  {'EFF ' + label_a:>15}  {'EFF ' + label_b:>15}  {'gap':>6}")
    print(f"{'':<13}  {'r':>6} {'beta':>6} {'dR2':>7}  {'r':>6} {'beta':>7}  {'r':>6} {'beta':>7}")
    print("-" * 88)
    for name, s in links["needs"].items():
        c, ea, eb = s["cognition"], s["evaluation_a"], s["evaluation_b"]
        print(
            f"{name:<13}  {_fmt(c['r'], 2):>6} {_fmt(c['beta'], 2):>6} {_fmt(c['delta_r2'], 3):>7}  "
            f"{_fmt(ea['r'], 2):>6} {_fmt(ea['beta'], 2):>7}  "
            f"{_fmt(eb['r'], 2):>6} {_fmt(eb['beta'], 2):>7}  {_fmt(s['layer_gap'], 2):>6}"
        )
    print()
    print("  gap = prototype beta - effectiveness beta, both from a six-need fit. The paper")
    print("  found protection and status reach the prototype and NOT effectiveness, so a")
    print("  positive gap there is the result being replicated, not a failure.")
    print("=" * 88)


def render_layer_moderation(study: Study, out: dict[str, Any]) -> None:
    """H3, H4, H5 and H7 with intervals, so each one can be decided rather than admired."""
    low, high = out["conditions"]["low"], out["conditions"]["high"]
    runs = out["runs"]

    def ci(bounds: list[float]) -> str:
        return f"[{_fmt(bounds[0], 2)}, {_fmt(bounds[1], 2)}]"

    print()
    print("=" * 100)
    print(f"LAYERS ACROSS CONDITIONS — {low} ({runs.get(low, 0)} runs) vs "
          f"{high} ({runs.get(high, 0)} runs)")
    print("=" * 100)
    print(f"Intervals are percentile bootstrap over RUNS ({out['bootstrap_draws']} draws), not")
    print("over respondents: three neutrals in a room saw one discussion between them.")
    print()
    print("H3  did the situation move the need?")
    print(f"  {'Need':<14}  {'induced ' + low:>16}  {'induced ' + high:>16}  "
          f"{'difference':>11}  {'95% CI':>16}")
    print("  " + "-" * 82)
    for name, s in out["needs"].items():
        ind = s["induced"]
        print(f"  {name:<14}  {_fmt(ind[low], 2):>16}  {_fmt(ind[high], 2):>16}  "
              f"{_fmt(ind['difference'], 2):>11}  {ci(ind['ci95']):>16}")

    label_a = study.label_of(out.get("outcome_group", "D"))
    print()
    print("H4 / H5 / H7  which layer does the need reach, and does threat change that?")
    print(f"  {'Need':<14}  {'proto b':>8} {'95% CI':>14}  {'eff ' + label_a:>8} {'95% CI':>14}  "
          f"{'gap':>6}  {'gap diff':>8} {'95% CI':>14}")
    print("  " + "-" * 96)
    for name, s in out["needs"].items():
        c, e = s["cognition"], s["evaluation_a"]
        print(f"  {name:<14}  {_fmt(c['beta'], 2):>8} {ci(c['ci95']):>14}  "
              f"{_fmt(e['beta'], 2):>8} {ci(e['ci95']):>14}  {_fmt(s['layer_gap'], 2):>6}  "
              f"{_fmt(s['layer_gap_difference'], 2):>8} {ci(s['layer_gap_difference_ci95']):>14}")

    es = out["endorsement_slope"]
    print()
    print(f"H7  induced {out['endorsement_need']} -> endorsing {label_a}, within condition:")
    print(f"  {low} {_fmt(es[low], 3)}   {high} {_fmt(es[high], 3)}   "
          f"difference {_fmt(es['difference'], 3)}  {ci(es['ci95'])}")
    print()
    print("  A gap above zero with an interval clear of it is the paper's own result: the")
    print("  need reaches the prototype and not the person. An effectiveness interval that")
    print("  contains zero is the null being replicated, not a failure to find anything.")
    print("=" * 100)


def render_mediation(study: Study, med: dict[str, Any]) -> None:
    lo, hi = med["conditions"]["low"], med["conditions"]["high"]
    print()
    print("=" * 88)
    print(f"MEDIATION — {med['need']} carrying {lo} -> {hi} onto "
          f"{study.label_of(med['outcome_group'])} endorsement")
    print("=" * 88)
    rows = [
        (f"path a   {lo} -> {hi} shift in induced {med['need']}", _fmt(med["path_a"], 3)),
        (f"path b   induced {med['need']} -> endorsement (centred within condition)",
         _fmt(med["path_b"], 3)),
        ("indirect a*b", _fmt(med["indirect"], 3)),
        (f"95% CI   percentile bootstrap, {med['bootstrap_draws']} draws",
         f"[{_fmt(med['ci95'][0], 3)}, {_fmt(med['ci95'][1], 3)}]"),
        ("n per condition", str(med["n"])),
    ]
    width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"  {label:<{width}}  :  {value}")
    print()
    verdict = "CI excludes zero — mediation supported" if med["supported"] else "CI includes zero — no mediation evidence"
    print(f"  Verdict: {verdict}")
    print("  (~20 runs per condition: treat as suggestive, not confirmatory.)")
    print("=" * 88)


def render_measure_check(study: Study, summary: dict[str, Any]) -> bool:
    """Is the instrument alive on these agents? Printed before any full study is paid for."""
    render_needs(study, summary)
    subscales = summary["subscales"]
    means = [s["baseline_mean"] for s in subscales.values() if not math.isnan(s["baseline_mean"])]
    spread = std(means)
    flat = summary["straight_lining"][BASELINE]
    weak = weak_subscales(summary)
    retest = summary["test_retest"]
    mean_retest = mean(list(retest.values()))

    print()
    print(f"{'Subscale':<18}  {'test-retest r':>14}")
    print("-" * 36)
    for name, r in retest.items():
        print(f"{name:<18}  {_fmt(r, 2):>14}")
    print()
    print("  The delta SD column above is this instrument's noise floor: how far a score")
    print("  moves when nothing happened between the two administrations. Any change a")
    print("  real study attributes to its scenario has to clear it.")

    checks = {
        "differentiates subscales (SD of means > 0.30)": spread > 0.30,
        "few straight-liners (< 0.30)": not math.isnan(flat) and flat < 0.30,
        "internal consistency (every subscale read by an analysis > 0.60)": not weak,
        # Two-sided on purpose. A mediator that is a CHANGE score inverts the usual
        # logic: too low and the scale is noise, but too high and there is no state
        # variance left for a situation to move, so the change is noise too.
        "stable but not frozen (0.40 < mean r < 0.85)": 0.40 < mean_retest < 0.85,
    }
    print()
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}]  {label}")
    if weak:
        print("          " + ", ".join(f"{n} alpha={_fmt(a, 2)}" for n, a in weak.items()))
    passed = all(checks.values())
    print()
    print(f"  Verdict: {'USABLE' if passed else 'NOT USABLE — do not spend a full study on this'}")
    print("=" * 88)
    return passed


# --------------------------------------------------------------------------- #
# Output files                                                                 #
# --------------------------------------------------------------------------- #

def save_summary(summary: dict[str, Any], output_dir: Path, prefix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary saved -> {path}")
    return path


def plot_contrast(
    study: Study, condition: Condition, summary: dict[str, Any], output_dir: Path
) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping chart.")
        return None

    a, b = condition.contrast
    label_a, label_b = study.label_of(a), study.label_of(b)
    output_dir.mkdir(parents=True, exist_ok=True)

    titles = {
        "votes": "Votes per run",
        "speech_rate": "Speech rate",
        "words_per_turn": "Words per spoken turn",
    }
    fig, axes = plt.subplots(1, len(titles), figsize=(5 * len(titles), 5))
    for ax, (key, title) in zip(axes, titles.items()):
        m = summary["metrics"][key]
        means = [m[a]["mean"], m[b]["mean"]]
        sds = [m[a]["sd"], m[b]["sd"]]
        ax.bar([label_a, label_b], means, yerr=sds, color=["#4C72B0", "#DD8452"],
               alpha=0.85, capsize=6, width=0.5)
        ax.set_ylim(bottom=0)
        ax.set_title(title, fontsize=11)
        offset = max(sds) * 0.1 + 0.05 * max(*means, 1)
        for x, (m_val, sd) in enumerate(zip(means, sds)):
            ax.text(x, m_val + sd + offset, f"{m_val:.2f}",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.suptitle(
        f"{study.title} — {condition.label}\n"
        f"(n={summary['runs']} runs, error bars = ±1 SD)",
        fontsize=11,
    )
    plt.tight_layout()
    path = output_dir / f"{condition.key}_{datetime.now():%Y%m%d_%H%M%S}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Chart saved -> {path}")
    return path
