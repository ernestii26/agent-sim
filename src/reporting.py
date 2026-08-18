"""Aggregate run records into metrics, tables, charts. Group labels come from the study."""
from __future__ import annotations

import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from instrument import BASELINE, POST, Instrument, subscale_scores
from study import Condition, Study

SILENCE_THRESHOLD = 0.80  # a persona below this stayed quiet at least sometimes


# --------------------------------------------------------------------------- #
# Metrics                                                                      #
# --------------------------------------------------------------------------- #

def _mean(values: list[float]) -> float:
    valid = [v for v in values if not math.isnan(v)]
    return sum(valid) / len(valid) if valid else float("nan")


def _std(values: list[float]) -> float:
    valid = [v for v in values if not math.isnan(v)]
    if len(valid) < 2:
        return 0.0
    m = _mean(valid)
    return (sum((v - m) ** 2 for v in valid) / (len(valid) - 1)) ** 0.5


def group_metrics(record: dict[str, Any], group_key: str) -> dict[str, float]:
    """Votes received, speech rate, and words per spoken turn for one group in one run."""
    turns = [t for t in record["transcript"] if t["group"] == group_key]
    spoken = [t for t in turns if t["spoke"]]
    return {
        "votes": float(sum(1 for v in record["votes"] if v["voted_for_group"] == group_key)),
        "speech_rate": (sum(1 for t in turns if t["spoke"]) / len(turns)) if turns else float("nan"),
        "words_per_turn": _mean([float(t["word_count"]) for t in spoken]) if spoken else float("nan"),
    }


def persona_metrics(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Speech rate and mean words per persona, pooled across every run they appeared in."""
    turns: dict[str, int] = {}
    spoke: dict[str, int] = {}
    words: dict[str, int] = {}
    for record in records:
        for turn in record["transcript"]:
            pid = turn["persona_id"]
            turns[pid] = turns.get(pid, 0) + 1
            if turn["spoke"]:
                spoke[pid] = spoke.get(pid, 0) + 1
                words[pid] = words.get(pid, 0) + turn["word_count"]
    return {
        pid: {
            "turns": float(n),
            "speech_rate": spoke.get(pid, 0) / n,
            "mean_words": (words[pid] / spoke[pid]) if spoke.get(pid) else float("nan"),
        }
        for pid, n in sorted(turns.items())
    }


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


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}" if not math.isnan(value) else "n/a"


def _fmt_p(p: float) -> str:
    if math.isnan(p):
        return "n/a"
    return "< .001" if p < 0.001 else f"{p:.3f}"


# --------------------------------------------------------------------------- #
# Summaries — pure functions over run records, no printing                     #
# --------------------------------------------------------------------------- #

def summarize_validation(study: Study, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Did the silence mechanism produce real variation? Judged on groups present in
    every run — sampled groups appear too rarely to have trustworthy rates."""
    stats = persona_metrics(records)
    always_on = [g.key for g in study.groups.values() if g.sample is None] or list(study.groups)
    rates = [m["speech_rate"] for pid, m in stats.items() if study.group_of(pid) in always_on]
    quiet = sum(1 for r in rates if r < SILENCE_THRESHOLD)
    mean_rate = _mean(rates)
    return {
        "study": study.name,
        "runs": len(records),
        "personas": stats,
        "judged_groups": always_on,
        "mean_speech_rate": mean_rate,
        "quiet_personas": quiet,
        "judged_personas": len(rates),
        "passed": quiet >= 3 and mean_rate < 0.90,
    }


def summarize_contrast(
    study: Study, condition: Condition, records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare the condition's two contrasted groups over every run.

    One-sided paired t-tests of contrast[0] > contrast[1] on votes, speech rate, and
    words per spoken turn. `supported` refers to the votes metric at p < .05.
    """
    a, b = condition.contrast
    per_run = [(group_metrics(r, a), group_metrics(r, b)) for r in records]

    metrics: dict[str, Any] = {}
    for key in ("votes", "speech_rate", "words_per_turn"):
        vals_a = [ma[key] for ma, _ in per_run]
        vals_b = [mb[key] for _, mb in per_run]
        t, p = paired_ttest_onesided(vals_a, vals_b)
        metrics[key] = {
            a: {"mean": _mean(vals_a), "sd": _std(vals_a)},
            b: {"mean": _mean(vals_b), "sd": _std(vals_b)},
            "t": t,
            "p": p,
            "values": {a: vals_a, b: vals_b},
        }

    votes = metrics["votes"]
    return {
        "study": study.name,
        "condition": condition.key,
        "hypothesis": condition.hypothesis,
        "contrast": [a, b],
        "runs": len(records),
        "per_run": [
            {"run_no": r["run_no"], a: ma["votes"], b: mb["votes"]}
            for r, (ma, mb) in zip(records, per_run)
        ],
        "wins": sum(1 for ma, mb in per_run if ma["votes"] > mb["votes"]),
        "metrics": metrics,
        "supported": (
            votes[a]["mean"] > votes[b]["mean"]
            and not math.isnan(votes["p"])
            and votes["p"] < 0.05
        ),
    }


# --------------------------------------------------------------------------- #
# Rendering — everything below only formats a summary                          #
# --------------------------------------------------------------------------- #

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
    print("=" * 74)


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
        for x, (mean, sd) in enumerate(zip(means, sds)):
            ax.text(x, mean + sd + offset, f"{mean:.2f}",
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


# --------------------------------------------------------------------------- #
# Instrument summaries — needs, prototypes, effectiveness, mediation           #
# --------------------------------------------------------------------------- #

def _responses(record: dict[str, Any], timing: str, key: str) -> dict[str, Any]:
    """Instrument responses for one run, or {} for records predating instruments."""
    return record.get("measures", {}).get(timing, {}).get(key, {})


def scored(record: dict[str, Any], timing: str, instrument: Instrument) -> dict[str, dict[str, float]]:
    """{persona_id: {subscale: mean}} for a self/prototype instrument in one run."""
    return {
        pid: subscale_scores(answers, instrument)
        for pid, answers in _responses(record, timing, instrument.key).items()
    }


def candidate_ratings(record: dict[str, Any], instrument: Instrument) -> dict[str, dict[str, float]]:
    """{rater_id: {target_id: mean rating}} for an about=each_candidate instrument."""
    out: dict[str, dict[str, float]] = {}
    for rater, by_target in _responses(record, POST, instrument.key).items():
        out[rater] = {
            target: _mean(list(subscale_scores(answers, instrument).values()))
            for target, answers in by_target.items()
        }
    return out


def straight_lining(record: dict[str, Any], timing: str, instrument: Instrument) -> float:
    """Share of respondents who gave the same rating to every item. High = dead instrument."""
    flat = 0
    total = 0
    for answers in _responses(record, timing, instrument.key).values():
        values = [v for k, v in answers.items() if k != "_meta" and v is not None]
        if not values:
            continue
        total += 1
        flat += len(set(values)) == 1
    return flat / total if total else float("nan")


def cronbach_alpha(rows: list[list[float]]) -> float:
    """Alpha over respondents x items. NaN when there are too few rows or no variance."""
    rows = [r for r in rows if r and not any(math.isnan(v) for v in r)]
    k = len(rows[0]) if rows else 0
    if len(rows) < 3 or k < 2:
        return float("nan")
    item_var = sum(_std([r[i] for r in rows]) ** 2 for i in range(k))
    total_var = _std([sum(r) for r in rows]) ** 2
    if total_var == 0:
        return float("nan")
    return (k / (k - 1)) * (1 - item_var / total_var)


def summarize_needs(
    study: Study, records: list[dict[str, Any]], instrument: Instrument
) -> dict[str, Any]:
    """Per-subscale means at baseline and post, plus the within-persona change (H3)."""
    per_timing: dict[str, dict[str, list[float]]] = {}
    for timing in (BASELINE, POST):
        by_subscale: dict[str, list[float]] = {name: [] for name in instrument.subscales}
        for record in records:
            for _, scores in scored(record, timing, instrument).items():
                for name, value in scores.items():
                    if not math.isnan(value):
                        by_subscale[name].append(value)
        per_timing[timing] = by_subscale

    # Paired change: same persona, same run, baseline vs post.
    deltas: dict[str, list[float]] = {name: [] for name in instrument.subscales}
    for record in records:
        before, after = scored(record, BASELINE, instrument), scored(record, POST, instrument)
        for pid in before.keys() & after.keys():
            for name in instrument.subscales:
                b, a = before[pid].get(name, float("nan")), after[pid].get(name, float("nan"))
                if not (math.isnan(b) or math.isnan(a)):
                    deltas[name].append(a - b)

    alpha_rows: dict[str, list[list[float]]] = {name: [] for name in instrument.subscales}
    for record in records:
        for answers in _responses(record, BASELINE, instrument.key).values():
            for name, texts in instrument.subscales.items():
                row = [answers.get(f"{name}_{i}") for i in range(1, len(texts) + 1)]
                if all(v is not None for v in row):
                    alpha_rows[name].append([float(v) for v in row])  # type: ignore[arg-type]

    return {
        "study": study.name,
        "instrument": instrument.key,
        "runs": len(records),
        "subscales": {
            name: {
                "baseline_mean": _mean(per_timing[BASELINE][name]),
                "baseline_sd": _std(per_timing[BASELINE][name]),
                "post_mean": _mean(per_timing[POST][name]),
                "post_sd": _std(per_timing[POST][name]),
                "delta_mean": _mean(deltas[name]),
                "delta_sd": _std(deltas[name]),
                "delta_n": len(deltas[name]),
                "alpha": cronbach_alpha(alpha_rows[name]),
            }
            for name in instrument.subscales
        },
        "straight_lining": {
            BASELINE: straight_lining_over(records, BASELINE, instrument),
            POST: straight_lining_over(records, POST, instrument),
        },
    }


def straight_lining_over(
    records: list[dict[str, Any]], timing: str, instrument: Instrument
) -> float:
    rates = [straight_lining(r, timing, instrument) for r in records]
    return _mean([r for r in rates if not math.isnan(r)])


def _slope(xs: list[float], ys: list[float]) -> tuple[float, float, int]:
    """OLS slope of y on x, its correlation, and n. NaN pairs dropped."""
    pairs = [(x, y) for x, y in zip(xs, ys) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    if n < 3:
        return float("nan"), float("nan"), n
    mx, my = _mean([p[0] for p in pairs]), _mean([p[1] for p in pairs])
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    if sxx == 0 or syy == 0:
        return float("nan"), float("nan"), n
    return sxy / sxx, sxy / (sxx * syy) ** 0.5, n


def need_outcome_links(
    study: Study,
    records: list[dict[str, Any]],
    needs: Instrument,
    *,
    ideals: Instrument | None = None,
    effectiveness: Instrument | None = None,
    contrast: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Both layers at once, respondent by respondent (H4, H5, H7).

    Cognition layer: need score -> the matching leader-ideal prototype rating.
    Evaluation layer: need score -> effectiveness rating given to the group in `contrast[0]`.
    The paper found the first link holds for protection/status and the second does not; the
    point of reporting them side by side is to see whether threat closes that gap.
    """
    rows: dict[str, dict[str, list[float]]] = {
        name: {"need": [], "ideal": [], "effect_a": [], "effect_b": []}
        for name in needs.subscales
    }

    for record in records:
        need_scores = scored(record, POST, needs)
        ideal_scores = scored(record, POST, ideals) if ideals else {}
        ratings = candidate_ratings(record, effectiveness) if effectiveness else {}
        members = record.get("members", {})

        for pid, scores in need_scores.items():
            for name, value in scores.items():
                if math.isnan(value):
                    continue
                rows[name]["need"].append(value)

                ideal = ideal_scores.get(pid, {}).get(f"{name}_ideal", float("nan"))
                rows[name]["ideal"].append(ideal)

                for slot, key in (("effect_a", 0), ("effect_b", 1)):
                    target_ids = members.get(contrast[key], []) if contrast else []
                    given = [ratings.get(pid, {}).get(t, float("nan")) for t in target_ids]
                    rows[name][slot].append(_mean(given) if given else float("nan"))

    out: dict[str, Any] = {"contrast": list(contrast) if contrast else None, "needs": {}}
    for name, cols in rows.items():
        cognition = _slope(cols["need"], cols["ideal"])
        evaluation = _slope(cols["need"], cols["effect_a"])
        evaluation_b = _slope(cols["need"], cols["effect_b"])
        out["needs"][name] = {
            "cognition": {"slope": cognition[0], "r": cognition[1], "n": cognition[2]},
            "evaluation_a": {"slope": evaluation[0], "r": evaluation[1], "n": evaluation[2]},
            "evaluation_b": {"slope": evaluation_b[0], "r": evaluation_b[1], "n": evaluation_b[2]},
            # H7: how far the prototype link outruns the effectiveness link.
            "layer_gap": cognition[1] - evaluation[1],
        }
    return out


def summarize_mediation(
    study: Study,
    by_condition: dict[str, list[dict[str, Any]]],
    needs: Instrument,
    *,
    need: str,
    outcome_group: str,
    effectiveness: Instrument,
    bootstrap: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """H6: does `need` carry the condition effect onto endorsement of `outcome_group`?

    Path a  condition -> need        (difference in post-discussion need scores)
    Path b  need -> endorsement      (slope, pooled across conditions)
    Indirect a*b with a percentile bootstrap CI. Deliberately a simple product-of-paths
    estimate rather than SEM: with ~20 runs per condition the extra machinery would imply
    a precision the data does not have.
    """
    per_condition: dict[str, list[tuple[float, float]]] = {}
    for condition_key, records in by_condition.items():
        pairs: list[tuple[float, float]] = []
        for record in records:
            need_scores = scored(record, POST, needs)
            ratings = candidate_ratings(record, effectiveness)
            targets = record.get("members", {}).get(outcome_group, [])
            for pid, scores in need_scores.items():
                value = scores.get(need, float("nan"))
                given = _mean([ratings.get(pid, {}).get(t, float("nan")) for t in targets])
                if not (math.isnan(value) or math.isnan(given)):
                    pairs.append((value, given))
        per_condition[condition_key] = pairs

    keys = sorted(per_condition)
    if len(keys) != 2:
        raise SystemExit(f"Mediation needs exactly two conditions, got {keys}")
    lo_key, hi_key = keys

    def estimate(data: dict[str, list[tuple[float, float]]]) -> tuple[float, float, float]:
        a = _mean([v for v, _ in data[hi_key]]) - _mean([v for v, _ in data[lo_key]])
        pooled = data[lo_key] + data[hi_key]
        b, _, _ = _slope([v for v, _ in pooled], [y for _, y in pooled])
        return a, b, a * b

    a_path, b_path, indirect = estimate(per_condition)

    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(bootstrap):
        resampled = {
            k: [rng.choice(v) for _ in v] if v else []
            for k, v in per_condition.items()
        }
        if all(len(v) >= 3 for v in resampled.values()):
            _, _, product = estimate(resampled)
            if not math.isnan(product):
                draws.append(product)
    draws.sort()
    ci = (
        (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1])
        if len(draws) >= 100
        else (float("nan"), float("nan"))
    )

    return {
        "need": need,
        "outcome_group": outcome_group,
        "conditions": {"low": lo_key, "high": hi_key},
        "n": {k: len(v) for k, v in per_condition.items()},
        "path_a": a_path,
        "path_b": b_path,
        "indirect": indirect,
        "ci95": list(ci),
        "bootstrap_draws": len(draws),
        # A CI excluding zero is the evidence for mediation; with 20 runs treat it as
        # suggestive, not confirmatory.
        "supported": not math.isnan(ci[0]) and (ci[0] > 0) == (ci[1] > 0),
    }


def render_needs(study: Study, summary: dict[str, Any]) -> None:
    print()
    print("=" * 88)
    print(f"{study.title.upper()} — {summary['instrument'].upper()} ({summary['runs']} runs)")
    print("=" * 88)
    print(f"{'Subscale':<18}  {'T1 mean':>9}  {'T2 mean':>9}  {'delta':>9}  {'n_d':>5}  {'alpha':>7}")
    print("-" * 88)
    for name, s in summary["subscales"].items():
        print(
            f"{name:<18}  {_fmt(s['baseline_mean'], 2):>9}  {_fmt(s['post_mean'], 2):>9}  "
            f"{_fmt(s['delta_mean'], 2):>9}  {s['delta_n']:>5}  {_fmt(s['alpha'], 2):>7}"
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
    print(f"{'Need':<14}  {'r prototype':>12}  {'r eff ' + label_a:>14}  {'r eff ' + label_b:>14}  {'gap':>8}")
    print("-" * 88)
    for name, s in links["needs"].items():
        print(
            f"{name:<14}  {_fmt(s['cognition']['r'], 2):>12}  "
            f"{_fmt(s['evaluation_a']['r'], 2):>14}  {_fmt(s['evaluation_b']['r'], 2):>14}  "
            f"{_fmt(s['layer_gap'], 2):>8}"
        )
    print("=" * 88)


def render_mediation(study: Study, med: dict[str, Any]) -> None:
    lo, hi = med["conditions"]["low"], med["conditions"]["high"]
    print()
    print("=" * 88)
    print(f"MEDIATION — {med['need']} carrying {lo} -> {hi} onto "
          f"{study.label_of(med['outcome_group'])} endorsement")
    print("=" * 88)
    rows = [
        (f"path a   {lo} -> {hi} shift in {med['need']}", _fmt(med["path_a"], 3)),
        (f"path b   {med['need']} -> effectiveness slope", _fmt(med["path_b"], 3)),
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


def render_measure_check(study: Study, summary: dict[str, Any], retest: dict[str, float]) -> bool:
    """Is the instrument alive on these agents? Printed before any full study is paid for."""
    render_needs(study, summary)
    subscales = summary["subscales"]
    means = [s["baseline_mean"] for s in subscales.values() if not math.isnan(s["baseline_mean"])]
    spread = _std(means)
    flat = summary["straight_lining"][BASELINE]
    alphas = [s["alpha"] for s in subscales.values() if not math.isnan(s["alpha"])]
    mean_retest = _mean(list(retest.values()))

    print()
    print(f"{'Subscale':<18}  {'test-retest r':>14}")
    print("-" * 36)
    for name, r in retest.items():
        print(f"{name:<18}  {_fmt(r, 2):>14}")

    checks = {
        "differentiates subscales (SD of means > 0.30)": spread > 0.30,
        "few straight-liners (< 0.30)": not math.isnan(flat) and flat < 0.30,
        "internal consistency (mean alpha > 0.60)": bool(alphas) and _mean(alphas) > 0.60,
        "stable across administrations (mean r > 0.50)": mean_retest > 0.50,
    }
    print()
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}]  {label}")
    passed = all(checks.values())
    print()
    print(f"  Verdict: {'USABLE' if passed else 'NOT USABLE — do not spend a full study on this'}")
    print("=" * 88)
    return passed
