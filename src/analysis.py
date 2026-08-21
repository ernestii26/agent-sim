"""Aggregate run records into summary dicts. No printing, no files.

Everything here is a pure function of RunRecords plus the study definition, so a
report can be recomputed from checkpoints without touching the API.
"""
from __future__ import annotations

import math
import random
from typing import Any

from instrument import BASELINE, POST, Instrument
from run_record import RunRecord
from stats import cronbach_alpha, mean, paired_ttest_onesided, slope, std
from study import Condition, Study

SILENCE_THRESHOLD = 0.80  # a persona below this stayed quiet at least sometimes


# --------------------------------------------------------------------------- #
# Discussion metrics                                                           #
# --------------------------------------------------------------------------- #

def group_metrics(record: RunRecord, group_key: str) -> dict[str, float]:
    """Votes received, speech rate, and words per spoken turn for one group in one run."""
    turns = record.turns(group_key)
    spoken = [t for t in turns if t["spoke"]]
    return {
        "votes": float(record.votes_for(group_key)),
        "speech_rate": (len(spoken) / len(turns)) if turns else float("nan"),
        "words_per_turn": mean([float(t["word_count"]) for t in spoken]) if spoken else float("nan"),
    }


def persona_metrics(records: list[RunRecord]) -> dict[str, dict[str, float]]:
    """Speech rate and mean words per persona, pooled across every run they appeared in."""
    turns: dict[str, int] = {}
    spoke: dict[str, int] = {}
    words: dict[str, int] = {}
    for record in records:
        for turn in record.turns():
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


def summarize_validation(study: Study, records: list[RunRecord]) -> dict[str, Any]:
    """Did the silence mechanism produce real variation? Judged on groups present in
    every run — sampled groups appear too rarely to have trustworthy rates."""
    stats = persona_metrics(records)
    always_on = [g.key for g in study.groups.values() if g.sample is None] or list(study.groups)
    rates = [m["speech_rate"] for pid, m in stats.items() if study.group_of(pid) in always_on]
    quiet = sum(1 for r in rates if r < SILENCE_THRESHOLD)
    mean_rate = mean(rates)
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
    study: Study, condition: Condition, records: list[RunRecord]
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
            a: {"mean": mean(vals_a), "sd": std(vals_a)},
            b: {"mean": mean(vals_b), "sd": std(vals_b)},
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
            {"run_no": r.run_no, a: ma["votes"], b: mb["votes"]}
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
# Instrument summaries — needs, prototypes, effectiveness, mediation           #
# --------------------------------------------------------------------------- #

def straight_lining(record: RunRecord, timing: str, instrument: Instrument) -> float:
    """Share of respondents who gave the same rating to every item. High = dead instrument."""
    flat = 0
    total = 0
    for answers in record.responses(timing, instrument).values():
        values = [v for k, v in answers.items() if k != "_meta" and v is not None]
        if not values:
            continue
        total += 1
        flat += len(set(values)) == 1
    return flat / total if total else float("nan")


def straight_lining_over(
    records: list[RunRecord], timing: str, instrument: Instrument
) -> float:
    rates = [straight_lining(r, timing, instrument) for r in records]
    return mean([r for r in rates if not math.isnan(r)])


def summarize_needs(
    study: Study, records: list[RunRecord], instrument: Instrument
) -> dict[str, Any]:
    """Per-subscale means at baseline and post, plus the within-persona change (H3)."""
    per_timing: dict[str, dict[str, list[float]]] = {}
    for timing in (BASELINE, POST):
        by_subscale: dict[str, list[float]] = {name: [] for name in instrument.subscales}
        for record in records:
            for scores in record.needs(timing, instrument).values():
                for name, value in scores.items():
                    if not math.isnan(value):
                        by_subscale[name].append(value)
        per_timing[timing] = by_subscale

    # Paired change: same persona, same run, baseline vs post.
    deltas: dict[str, list[float]] = {name: [] for name in instrument.subscales}
    for record in records:
        before = record.needs(BASELINE, instrument)
        after = record.needs(POST, instrument)
        for pid in before.keys() & after.keys():
            for name in instrument.subscales:
                b, a = before[pid].get(name, float("nan")), after[pid].get(name, float("nan"))
                if not (math.isnan(b) or math.isnan(a)):
                    deltas[name].append(a - b)

    alpha_rows: dict[str, list[list[float]]] = {name: [] for name in instrument.subscales}
    for record in records:
        for answers in record.responses(BASELINE, instrument).values():
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
                "baseline_mean": mean(per_timing[BASELINE][name]),
                "baseline_sd": std(per_timing[BASELINE][name]),
                "post_mean": mean(per_timing[POST][name]),
                "post_sd": std(per_timing[POST][name]),
                "delta_mean": mean(deltas[name]),
                "delta_sd": std(deltas[name]),
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


def summarize_measure_check(
    study: Study, record: RunRecord, instrument: Instrument
) -> dict[str, Any]:
    """Two administrations of the same scale, scored as if they were baseline and post.

    The extra column over summarize_needs is test-retest: an agent whose answers do not
    correlate with its own answers minutes earlier has no measurable trait to mediate.
    """
    summary = summarize_needs(study, [record], instrument)
    first, second = record.needs(BASELINE, instrument), record.needs(POST, instrument)
    shared = sorted(first.keys() & second.keys())
    summary["test_retest"] = {
        name: slope(
            [first[pid].get(name, float("nan")) for pid in shared],
            [second[pid].get(name, float("nan")) for pid in shared],
        )[1]
        for name in instrument.subscales
    }
    return summary


def need_outcome_links(
    study: Study,
    records: list[RunRecord],
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
        need_scores = record.needs(POST, needs)
        ideal_scores = record.needs(POST, ideals) if ideals else {}
        ratings = record.ratings(effectiveness) if effectiveness else {}

        for pid, scores in need_scores.items():
            for name, value in scores.items():
                if math.isnan(value):
                    continue
                rows[name]["need"].append(value)

                ideal = ideal_scores.get(pid, {}).get(f"{name}_ideal", float("nan"))
                rows[name]["ideal"].append(ideal)

                for slot, key in (("effect_a", 0), ("effect_b", 1)):
                    target_ids = record.members(contrast[key]) if contrast else []
                    given = [ratings.get(pid, {}).get(t, float("nan")) for t in target_ids]
                    rows[name][slot].append(mean(given) if given else float("nan"))

    out: dict[str, Any] = {"contrast": list(contrast) if contrast else None, "needs": {}}
    for name, cols in rows.items():
        cognition = slope(cols["need"], cols["ideal"])
        evaluation = slope(cols["need"], cols["effect_a"])
        evaluation_b = slope(cols["need"], cols["effect_b"])
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
    by_condition: dict[str, list[RunRecord]],
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
            ratings = record.ratings(effectiveness)
            targets = record.members(outcome_group)
            for pid, scores in record.needs(POST, needs).items():
                value = scores.get(need, float("nan"))
                given = mean([ratings.get(pid, {}).get(t, float("nan")) for t in targets])
                if not (math.isnan(value) or math.isnan(given)):
                    pairs.append((value, given))
        per_condition[condition_key] = pairs

    keys = sorted(per_condition)
    if len(keys) != 2:
        raise SystemExit(f"Mediation needs exactly two conditions, got {keys}")
    lo_key, hi_key = keys

    def estimate(data: dict[str, list[tuple[float, float]]]) -> tuple[float, float, float]:
        a = mean([v for v, _ in data[hi_key]]) - mean([v for v, _ in data[lo_key]])
        pooled = data[lo_key] + data[hi_key]
        b, _, _ = slope([v for v, _ in pooled], [y for _, y in pooled])
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
