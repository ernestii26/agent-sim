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
from stats import cronbach_alpha, mean, paired_ttest_onesided, partial_betas, slope, std
from study import Condition, Study

SILENCE_THRESHOLD = 0.80  # a persona below this stayed quiet at least sometimes


# --------------------------------------------------------------------------- #
# Discussion metrics                                                           #
# --------------------------------------------------------------------------- #

def group_metrics(
    record: RunRecord, group_key: str, *, voters: tuple[str, ...] | None = None
) -> dict[str, float]:
    """Votes received, speech rate, and words per spoken turn for one group in one run.

    `voters` restricts which groups' ballots count towards the vote metric.
    """
    turns = record.turns(group_key)
    spoken = [t for t in turns if t["spoke"]]
    return {
        "votes": float(record.votes_for(group_key, by=voters)),
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
    # The contrasted groups are the candidates. Letting them vote in their own contest
    # puts a rival's ballot into the dependent variable: in the 10-agent runs that was
    # 2 of 10 votes and moved the gap by ~0.1, but at a cast of 5 it is 2 of 5. So the
    # electorate is everyone not standing. Falls back to the whole room if a study
    # contrasts every group it has.
    voters = tuple(k for k in study.groups if k not in (a, b)) or None
    per_run = [
        (group_metrics(r, a, voters=voters), group_metrics(r, b, voters=voters)) for r in records
    ]

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
        "electorate": list(voters) if voters else None,
        # Kept out of the test but not thrown away: how the two candidates rated each
        # other is the dominance side's own read on the prestige side, and vice versa.
        "candidate_votes": {
            a: sum(r.votes_for(a, by=(b,)) for r in records),
            b: sum(r.votes_for(b, by=(a,)) for r in records),
        },
        "metrics": metrics,
        # Sampled groups are the ones run.py validate cannot judge — it only looks at
        # always-present groups. A leader who never spoke is unratable, so the vote in
        # that run is noise, and this is the only place it shows up.
        "personas": persona_metrics(records),
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
    # Which subscales an analysis actually reads. For an instrument with a prediction
    # map that is the dimensions it points at — femininity is measured but nothing
    # reads it, so its reliability cannot sink the instrument. Without a map every
    # subscale is read.
    summary["gated_subscales"] = sorted(
        {dim for dims in instrument.predicts.values() for dim in dims}
        if instrument.predicts
        else instrument.subscales
    )
    return summary


def weak_subscales(summary: dict[str, Any], threshold: float = 0.60) -> dict[str, float]:
    """Read subscales whose alpha does not clear `threshold`.

    Judged one subscale at a time, not on the average. `protection` reaches exactly one
    prototype dimension — `strength`, two items — so a mean over ten subscales would
    wave it through on the back of `tyranny`'s ten, and H4's and H6's main line would
    rest on noise that the gate called usable. An alpha that could not be computed at
    all does not pass either.
    """
    subscales = summary["subscales"]
    gated = summary.get("gated_subscales") or list(subscales)
    weak = {}
    for name in gated:
        alpha = subscales.get(name, {}).get("alpha", float("nan"))
        if math.isnan(alpha) or alpha <= threshold:
            weak[name] = alpha
    return weak


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
    names = list(needs.subscales)
    rows: dict[str, dict[str, list[float]]] = {
        name: {"need": [], "ideal": [], "effect_a": [], "effect_b": []} for name in names
    }
    # One row per respondent, all six needs together — the bivariate columns above drop
    # a respondent per need independently, which is fine for a correlation and useless
    # as a design matrix.
    every_need: list[list[float]] = []
    composites: dict[str, list[float]] = {name: [] for name in names}
    rated: dict[str, list[float]] = {"effect_a": [], "effect_b": []}

    for record in records:
        need_scores = record.needs(POST, needs)
        ideal_scores = record.needs(POST, ideals) if ideals else {}
        ratings = record.ratings(effectiveness) if effectiveness else {}

        for pid, scores in need_scores.items():
            mine = ideal_scores.get(pid, {})

            def composite(name: str) -> float:
                # The need's predicted prototype dimensions, averaged. Many-to-many
                # because that is the shape of the source paper's result: status
                # reached tyranny, masculinity and well-groomed, not one dimension.
                predicted = ideals.predicts.get(name, ()) if ideals else ()
                return mean([mine.get(dim, float("nan")) for dim in predicted]) \
                    if predicted else float("nan")

            every_need.append([scores.get(name, float("nan")) for name in names])
            for name in names:
                composites[name].append(composite(name))
            for slot, key in (("effect_a", 0), ("effect_b", 1)):
                target_ids = record.members(contrast[key]) if contrast else []
                given = [ratings.get(pid, {}).get(t, float("nan")) for t in target_ids]
                rated[slot].append(mean(given) if given else float("nan"))

            for name, value in scores.items():
                if math.isnan(value):
                    continue
                rows[name]["need"].append(value)
                rows[name]["ideal"].append(composite(name))
                for slot in ("effect_a", "effect_b"):
                    rows[name][slot].append(rated[slot][-1])   # this respondent's, just taken

    # One regression per rated group, not one per need: the outcome is the same column
    # for every need, which is exactly the shape the paper fitted ("these relationships
    # remained significant even after controlling for all other FFNs").
    evaluation_fits = {
        slot: partial_betas(every_need, rated[slot]) for slot in ("effect_a", "effect_b")
    }

    out: dict[str, Any] = {"contrast": list(contrast) if contrast else None, "needs": {}}
    for position, name in enumerate(names):
        cols = rows[name]
        cognition = slope(cols["need"], cols["ideal"])
        evaluation = slope(cols["need"], cols["effect_a"])
        evaluation_b = slope(cols["need"], cols["effect_b"])

        # H4 is a claim about increment, not association. Reported beside the bivariate
        # r on purpose: the source paper's Table 13 shows the two columns disagreeing
        # completely, and that disagreement is itself the finding to look for here.
        betas, deltas, model_r2, partial_n = partial_betas(every_need, composites[name])

        def layer(slot: str, bivariate: tuple[float, float, int]) -> dict[str, float]:
            b, d, r2, fitted_n = evaluation_fits[slot]
            return {
                "slope": bivariate[0], "r": bivariate[1], "n": bivariate[2],
                "beta": b[position] if b else float("nan"),
                "delta_r2": d[position] if d else float("nan"),
                "model_r2": r2,
                "partial_n": fitted_n,
            }

        cognition_beta = betas[position] if betas else float("nan")
        evaluation_a = layer("effect_a", evaluation)
        out["needs"][name] = {
            "cognition": {
                "slope": cognition[0], "r": cognition[1], "n": cognition[2],
                "beta": cognition_beta,
                "delta_r2": deltas[position] if deltas else float("nan"),
                "model_r2": model_r2,
                "partial_n": partial_n,
            },
            "evaluation_a": evaluation_a,
            "evaluation_b": layer("effect_b", evaluation_b),
            # H7: how far the prototype link outruns the effectiveness link. Both sides
            # are standardised betas from a six-need fit, so the difference is between
            # comparable quantities — a bivariate r on either side would make the gap a
            # comparison of two different questions.
            "layer_gap": cognition_beta - evaluation_a["beta"],
        }
    return out


def summarize_mediation(
    study: Study,
    by_condition: dict[str, list[RunRecord]],
    needs: Instrument,
    *,
    need: str,
    outcome_group: str,
    bootstrap: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """H6: does `need` carry the condition effect onto endorsement of `outcome_group`?

    Path a  condition -> induced need   (difference in post-minus-baseline change)
    Path b  induced need -> endorsement (within-condition-centred slope, pooled)
    Indirect a*b with a percentile bootstrap CI. Deliberately a simple product-of-paths
    estimate rather than SEM: at this many runs the extra machinery would imply a
    precision the data does not have.

    The mediator is the CHANGE in the need, not its level. The source paper's null is
    about the chronic, trait-like reading of a need; the claim here is about the state
    a situation induces, and a level score mixes the two. The outcome is the respondent's
    own vote, which is the behavioural consequence the paper named as untested — and
    keeping it distinct from the effectiveness rating is what stops H6 and H5 from
    resting on the same coefficient with opposite predictions.

    ponytail: the bootstrap resamples respondents, not runs, so it still ignores that
    neutrals inside one run watched the same discussion. Simulated, that clustering moves
    the false-positive rate by about 2 points (12% -> 14% as ICC goes 0 -> .25), against
    the 8 points the centring above fixes. Switch to resampling runs if the observed ICC
    turns out high.
    """
    per_condition: dict[str, list[tuple[float, float]]] = {}
    for condition_key, records in by_condition.items():
        pairs: list[tuple[float, float]] = []
        for record in records:
            before = record.needs(BASELINE, needs)
            after = record.needs(POST, needs)
            for pid, scores in after.items():
                base = before.get(pid, {}).get(need, float("nan"))
                induced = scores.get(need, float("nan")) - base
                endorsed = record.vote_of(pid)
                if not math.isnan(induced) and endorsed is not None:
                    pairs.append((induced, 1.0 if endorsed == outcome_group else 0.0))
        per_condition[condition_key] = pairs

    keys = sorted(per_condition)
    if len(keys) != 2:
        raise SystemExit(f"Mediation needs exactly two conditions, got {keys}")
    lo_key, hi_key = keys

    def estimate(data: dict[str, list[tuple[float, float]]]) -> tuple[float, float, float]:
        a = mean([v for v, _ in data[hi_key]]) - mean([v for v, _ in data[lo_key]])
        # Path b is centred within condition. Pooling the raw scores instead makes the
        # mediator and the outcome both functions of condition — threat raises the
        # induced need AND raises endorsement directly, which is H2 — so the pooled
        # slope is positive even when the need does nothing. Simulated at this design,
        # that put the false-positive rate at 13% (5 agents, 30 runs) to 20% (10 agents,
        # 20 runs) against a nominal 5%, and the bias does not shrink with n: only the
        # CI does, so more runs made it worse. Centring returns it to ~7%.
        pooled: list[tuple[float, float]] = []
        for pairs in (data[lo_key], data[hi_key]):
            if not pairs:
                continue
            centre = mean([v for v, _ in pairs])
            pooled += [(v - centre, y) for v, y in pairs]
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


def _layer_rows(
    records: list[RunRecord],
    needs: Instrument,
    ideals: Instrument | None,
    effectiveness: Instrument | None,
    contrast: tuple[str, str] | None,
) -> list[list[dict[str, Any]]]:
    """One list per run, one row per respondent inside it.

    Runs are kept apart because the run is the sampling unit: three neutrals in a room
    watched the same discussion, so resampling respondents would count one meeting as
    three independent observations. Section 18 accepted that for H6's bootstrap; here it
    is avoided instead.
    """
    names = list(needs.subscales)
    nan = float("nan")
    runs: list[list[dict[str, Any]]] = []
    for record in records:
        before = record.needs(BASELINE, needs)
        after = record.needs(POST, needs)
        ideal_scores = record.needs(POST, ideals) if ideals else {}
        ideal_base = record.needs(BASELINE, ideals) if ideals else {}
        ratings = record.ratings(effectiveness) if effectiveness else {}
        rows: list[dict[str, Any]] = []
        for pid, scores in after.items():
            mine = ideal_scores.get(pid, {})
            was = ideal_base.get(pid, {})
            base = before.get(pid, {})

            def dimensions(name: str, source: dict[str, float]) -> float:
                predicted = ideals.predicts.get(name, ()) if ideals else ()
                return mean([source.get(d, nan) for d in predicted]) if predicted else nan
            given = {}
            for slot, key in (("a", 0), ("b", 1)):
                targets = record.members(contrast[key]) if contrast else []
                marks = [ratings.get(pid, {}).get(t, nan) for t in targets]
                given[slot] = mean(marks) if marks else nan
            rows.append({
                "level": [scores.get(n, nan) for n in names],
                "induced": [scores.get(n, nan) - base.get(n, nan) for n in names],
                "composite": {n: dimensions(n, mine) for n in names},
                # The within-person move in the prototype. Available only because the
                # prototype is administered at baseline too, which a baseline fork makes
                # nearly free — it carries no transcript.
                "induced_composite": {
                    n: dimensions(n, mine) - dimensions(n, was) for n in names
                },
                "eff_a": given["a"],
                "eff_b": given["b"],
                "vote": record.vote_of(pid),
            })
        runs.append(rows)
    return runs


def _centre(values: list[float]) -> list[float]:
    """Subtract the column's own mean, ignoring missing entries."""
    finite = [v for v in values if not math.isnan(v)]
    if not finite:
        return list(values)
    centre = mean(finite)
    return [v - centre for v in values]


def summarize_layer_moderation(
    study: Study,
    by_condition: dict[str, list[RunRecord]],
    needs: Instrument,
    *,
    ideals: Instrument | None = None,
    effectiveness: Instrument | None = None,
    contrast: tuple[str, str] | None = None,
    need: str = "protection",
    outcome_group: str = "D",
    bootstrap: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """H3, H4, H5 and H7 in one pass, with the run as the unit of resampling.

    H3  induced need, threat minus collaborative, per need.
    H4  need -> its predicted prototype dimensions, as a beta from a six-need fit.
    H5  need -> effectiveness of each contrasted group, from the same design matrix.
    H7  the same quantities per condition, and the difference between them: does threat
        strengthen the link and close the gap between the two layers?

    Every estimate is pooled with each condition centred on its own means. Threat moves
    the needs and the ratings together, so a raw pooled fit would report that shared
    shift as a need-to-rating link — the same trap section 18 found in path b.
    """
    names = list(needs.subscales)
    per_condition = {
        key: _layer_rows(records, needs, ideals, effectiveness, contrast)
        for key, records in by_condition.items()
    }
    keys = sorted(per_condition)
    if len(keys) != 2:
        raise SystemExit(f"Layer moderation needs exactly two conditions, got {keys}")
    low, high = keys

    def fit_rows(rows: list[dict[str, Any]], *, deltas: bool) -> dict[str, Any]:
        """Betas for one pool of respondents, already centred."""
        design = [r["level"] for r in rows]
        out: dict[str, Any] = {}
        for slot in ("eff_a", "eff_b"):
            betas, drops, r2, n = partial_betas(design, [r[slot] for r in rows],
                                                with_deltas=deltas)
            out[slot] = {"beta": betas, "delta_r2": drops, "model_r2": r2, "n": n}
        cognition: dict[str, Any] = {}
        for i, name in enumerate(names):
            betas, drops, r2, n = partial_betas(design, [r["composite"][name] for r in rows],
                                                with_deltas=deltas)
            cognition[name] = {
                "beta": betas[i] if betas else float("nan"),
                "delta_r2": drops[i] if drops else float("nan"),
                "model_r2": r2, "n": n,
            }
        out["cognition"] = cognition
        # The same link asked within the person: did the change in the need go with the
        # change in the prototype? Level scores cannot separate a standing disposition
        # from what the situation did; a pre-post difference on both sides can.
        moved = [r["induced"] for r in rows]
        induced: dict[str, Any] = {}
        for i, name in enumerate(names):
            betas, drops, r2, n = partial_betas(
                moved, [r["induced_composite"][name] for r in rows], with_deltas=deltas)
            induced[name] = {
                "beta": betas[i] if betas else float("nan"),
                "delta_r2": drops[i] if drops else float("nan"),
                "model_r2": r2, "n": n,
            }
        out["cognition_induced"] = induced
        return out

    def centred(runs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
        rows = [dict(r) for run in runs for r in run]
        if not rows:
            return rows
        for i in range(len(names)):
            column = _centre([r["level"][i] for r in rows])
            for r, value in zip(rows, column):
                r["level"] = list(r["level"])
                r["level"][i] = value
        for key in ("eff_a", "eff_b"):
            for r, value in zip(rows, _centre([r[key] for r in rows])):
                r[key] = value
        for i in range(len(names)):
            column = _centre([r["induced"][i] for r in rows])
            for r, value in zip(rows, column):
                r["induced"] = list(r["induced"])
                r["induced"][i] = value
        for field in ("composite", "induced_composite"):
            for name in names:
                column = _centre([r[field][name] for r in rows])
                for r, value in zip(rows, column):
                    r[field] = dict(r[field])
                    r[field][name] = value
        return rows

    def estimate(sample: dict[str, list[list[dict[str, Any]]]], *, deltas: bool) -> dict[str, Any]:
        by_key = {key: centred(sample[key]) for key in keys}
        pooled = fit_rows(by_key[low] + by_key[high], deltas=deltas)
        per_key = {key: fit_rows(by_key[key], deltas=False) for key in keys}

        result: dict[str, Any] = {"needs": {}}
        flat = {key: [r for run in sample[key] for r in run] for key in keys}
        for i, name in enumerate(names):
            def induced(key: str) -> float:
                vals = [r["induced"][i] for r in flat[key] if not math.isnan(r["induced"][i])]
                return mean(vals) if vals else float("nan")

            def gap(fit: dict[str, Any]) -> float:
                return fit["cognition"][name]["beta"] - fit["eff_a"]["beta"][i] \
                    if fit["eff_a"]["beta"] else float("nan")

            result["needs"][name] = {
                # H3
                "induced": {low: induced(low), high: induced(high),
                            "difference": induced(high) - induced(low)},
                # H4 and H5, pooled
                "cognition": pooled["cognition"][name],
                "cognition_induced": pooled["cognition_induced"][name],
                "cognition_induced_by_condition": {
                    key: per_key[key]["cognition_induced"][name]["beta"] for key in keys
                },
                "cognition_induced_difference": (
                    per_key[high]["cognition_induced"][name]["beta"]
                    - per_key[low]["cognition_induced"][name]["beta"]
                ),
                "evaluation_a": {
                    "beta": pooled["eff_a"]["beta"][i] if pooled["eff_a"]["beta"] else float("nan"),
                    "delta_r2": pooled["eff_a"]["delta_r2"][i]
                    if pooled["eff_a"]["delta_r2"] else float("nan"),
                },
                "evaluation_b": {
                    "beta": pooled["eff_b"]["beta"][i] if pooled["eff_b"]["beta"] else float("nan"),
                },
                "layer_gap": gap(pooled),
                # H7
                "layer_gap_by_condition": {key: gap(per_key[key]) for key in keys},
                "layer_gap_difference": gap(per_key[high]) - gap(per_key[low]),
            }

        # H7's other half: does the induced mediator reach the vote harder under threat?
        for key in keys:
            rows = [r for run in sample[key] for r in run]
            xs = _centre([r["induced"][names.index(need)] for r in rows])
            ys = [1.0 if r["vote"] == outcome_group else 0.0 for r in rows]
            result.setdefault("endorsement_slope", {})[key] = slope(xs, ys)[0]
        result["endorsement_slope"]["difference"] = (
            result["endorsement_slope"][high] - result["endorsement_slope"][low]
        )
        return result

    point = estimate(per_condition, deltas=True)

    rng = random.Random(seed)
    draws: list[dict[str, Any]] = []
    for _ in range(bootstrap):
        sample = {
            key: [rng.choice(runs) for _ in runs] if runs else []
            for key, runs in per_condition.items()
        }
        try:
            draws.append(estimate(sample, deltas=False))
        except (ValueError, IndexError):
            continue

    def interval(path: list[Any]) -> list[float]:
        values = []
        for draw in draws:
            node: Any = draw
            for step in path:
                node = node[step]
            if isinstance(node, float) and not math.isnan(node):
                values.append(node)
        if len(values) < 20:
            return [float("nan"), float("nan")]
        values.sort()
        return [values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]]

    for name in names:
        entry = point["needs"][name]
        entry["induced"]["ci95"] = interval(["needs", name, "induced", "difference"])
        entry["cognition"]["ci95"] = interval(["needs", name, "cognition", "beta"])
        entry["cognition_induced"]["ci95"] = interval(
            ["needs", name, "cognition_induced", "beta"])
        entry["cognition_induced_difference_ci95"] = interval(
            ["needs", name, "cognition_induced_difference"])
        entry["evaluation_a"]["ci95"] = interval(["needs", name, "evaluation_a", "beta"])
        entry["evaluation_b"]["ci95"] = interval(["needs", name, "evaluation_b", "beta"])
        entry["layer_gap_ci95"] = interval(["needs", name, "layer_gap"])
        entry["layer_gap_difference_ci95"] = interval(["needs", name, "layer_gap_difference"])
    point["endorsement_slope"]["ci95"] = interval(["endorsement_slope", "difference"])
    point["conditions"] = {"low": low, "high": high}
    point["outcome_group"] = outcome_group
    point["endorsement_need"] = need
    point["bootstrap_draws"] = len(draws)
    point["runs"] = {key: len(runs) for key, runs in per_condition.items()}
    return point
