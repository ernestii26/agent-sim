#!/usr/bin/env python3
"""Self-check for the theme-free core: study loading, run composition, metrics.

    python3 test_core.py

No API calls, no TinyTroupe — everything here is pure logic on dicts.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from pipeline import BalancedSampler  # noqa: E402
from instrument import load_instrument, subscale_scores  # noqa: E402
from reporting import (  # noqa: E402
    cronbach_alpha, group_metrics, need_outcome_links, paired_ttest_onesided, persona_metrics,
    straight_lining, summarize_contrast, summarize_mediation, summarize_needs,
    summarize_validation,
)
from study import list_studies, load_study  # noqa: E402


def test_every_study_loads() -> None:
    studies = list_studies()
    assert studies, "no studies found in studies/"
    for name in studies:
        study = load_study(name)
        assert study.conditions, f"{name}: no conditions"
        for condition in study.conditions.values():
            assert condition.scenario.strip(), f"{name}/{condition.key}: empty scenario"
            for key in condition.contrast:
                assert key in study.groups
        for group in study.groups.values():
            for pid in group.ids:
                assert study.group_of(pid) == group.key
                assert (study.personas_dir / f"{pid}.agent.json").exists(), \
                    f"{name}: missing persona file for {pid}"
        if study.personas_from:
            continue  # borrows another study's personas, so it has no seeds of its own
        seeds = json.loads(study.seeds_path.read_text(encoding="utf-8"))
        seeded = {s["persona_id"] for s in seeds["personas"]}
        declared = {pid for g in study.groups.values() for pid in g.ids}
        assert seeded == declared, f"{name}: seeds.json and study.json disagree on persona ids"
        for seed in seeds["personas"]:
            assert seed["prompt"] in seeds["prompts"], f"{name}: unknown prompt {seed['prompt']}"


def test_balanced_sampler_exhausts_pool_before_repeating() -> None:
    sampler = BalancedSampler(["a", "b", "c"])
    drawn = [sampler.take(1)[0] for _ in range(9)]
    for start in (0, 3, 6):
        assert sorted(drawn[start : start + 3]) == ["a", "b", "c"], drawn
    batch = BalancedSampler(["a", "b", "c"]).take(4)
    assert sorted(batch[:3]) == ["a", "b", "c"] and len(batch) == 4, batch


def test_compose_run_respects_group_sampling() -> None:
    study = load_study("prestige_dominance")
    from pipeline import make_samplers

    samplers = make_samplers(study)
    for _ in range(20):
        chosen: list[str] = []
        for key, group in study.groups.items():
            chosen.extend(group.ids if group.sample is None else samplers[key].take(group.sample))
        assert len(chosen) == len(set(chosen)), "a persona was cast twice in one run"
        for key, group in study.groups.items():
            n = sum(1 for pid in chosen if study.group_of(pid) == key)
            assert n == (len(group.ids) if group.sample is None else group.sample)


def _record(run_no: int = 1, p_votes: int = 2, neutrals: tuple[str, ...] = ()) -> dict:
    """A synthetic run: P1 speaks 1 of 2 turns, D1 speaks both, plus optional neutrals."""
    tr = [
        {"round": 1, "persona_id": "P1", "group": "P", "spoke": True, "word_count": 10},
        {"round": 2, "persona_id": "P1", "group": "P", "spoke": False, "word_count": 0},
        {"round": 1, "persona_id": "D1", "group": "D", "spoke": True, "word_count": 4},
        {"round": 2, "persona_id": "D1", "group": "D", "spoke": True, "word_count": 6},
    ]
    for i, pid in enumerate(neutrals):
        for r in (1, 2):
            spoke = (i + r) % 2 == 0  # each neutral is quiet exactly half the time
            tr.append({"round": r, "persona_id": pid, "group": "N",
                       "spoke": spoke, "word_count": 12 if spoke else 0})
    voters = ["P1", "D1"] + list(neutrals)
    votes = [
        {"voter_id": v, "voted_for_id": "P1" if i < p_votes else "D1",
         "voted_for_group": "P" if i < p_votes else "D", "reason": ""}
        for i, v in enumerate(voters)
    ]
    return {"run_no": run_no, "members": {"P": ["P1"], "D": ["D1"], "N": list(neutrals)},
            "transcript": tr, "votes": votes}


def test_group_metrics() -> None:
    record = _record(p_votes=1)  # one vote for P, one for D
    p = group_metrics(record, "P")
    assert p == {"votes": 1.0, "speech_rate": 0.5, "words_per_turn": 10.0}, p
    d = group_metrics(record, "D")
    assert d == {"votes": 1.0, "speech_rate": 1.0, "words_per_turn": 5.0}, d
    absent = group_metrics(record, "N")
    assert absent["votes"] == 0.0 and absent["speech_rate"] != absent["speech_rate"]  # NaN


def test_persona_metrics_pool_across_runs() -> None:
    stats = persona_metrics([_record(), _record(run_no=2)])
    assert stats["P1"]["turns"] == 4 and stats["P1"]["speech_rate"] == 0.5
    assert stats["D1"]["mean_words"] == 5.0


def test_ttest_direction_and_degenerate_input() -> None:
    t, _ = paired_ttest_onesided([3.0, 4.0, 5.0], [1.0, 2.0, 1.0])
    assert t > 0
    t_rev, _ = paired_ttest_onesided([1.0, 2.0, 1.0], [3.0, 4.0, 5.0])
    assert t_rev < 0
    t_nan, p_nan = paired_ttest_onesided([1.0], [2.0])  # too few pairs
    assert t_nan != t_nan and p_nan != p_nan
    t_flat, _ = paired_ttest_onesided([2.0, 3.0], [1.0, 2.0])  # zero variance in the diffs
    assert t_flat != t_flat


def test_summarize_contrast_follows_the_conditions_direction() -> None:
    study = load_study("prestige_dominance")
    records = [_record(1, p_votes=2), _record(2, p_votes=1)]  # P gets 2 then 1 vote

    collab = summarize_contrast(study, study.condition("collaborative"), records)
    assert collab["contrast"] == ["P", "D"]
    assert collab["per_run"] == [{"run_no": 1, "P": 2.0, "D": 0.0},
                                 {"run_no": 2, "P": 1.0, "D": 1.0}]
    assert collab["wins"] == 1
    assert collab["metrics"]["votes"]["P"]["mean"] == 1.5

    # The threat condition flips the contrast, so the same records must reverse.
    threat = summarize_contrast(study, study.condition("threat"), records)
    assert threat["contrast"] == ["D", "P"]
    assert threat["wins"] == 0
    assert threat["metrics"]["votes"]["t"] == -collab["metrics"]["votes"]["t"]
    assert threat["supported"] is False


def test_summarize_validation_judges_only_always_present_groups() -> None:
    study = load_study("prestige_dominance")
    neutrals = ("N1", "N2", "N3", "N4")
    summary = summarize_validation(study, [_record(neutrals=neutrals)])

    # P and D are sampled 1-per-run, so their sparse rates must not drive the verdict.
    assert summary["judged_groups"] == ["N"], summary["judged_groups"]
    assert summary["judged_personas"] == len(neutrals)
    assert summary["mean_speech_rate"] == 0.5
    assert summary["passed"] is True
    assert summary["personas"]["D1"]["speech_rate"] == 1.0  # still reported, just not judged


# --------------------------------------------------------------------------- #
# Instruments                                                                  #
# --------------------------------------------------------------------------- #

def test_every_instrument_loads_and_is_consistent() -> None:
    for name in list_studies():
        study = load_study(name)
        for inst in study.instruments:
            assert inst.scale[0] < inst.scale[1]
            assert set(inst.targets) <= set(study.groups)
            ids = [item_id for item_id, _, _ in inst.items]
            assert len(ids) == len(set(ids)), f"{name}/{inst.key}: duplicate item ids"
            assert len(ids) == sum(len(v) for v in inst.subscales.values())


def test_ffni_matches_the_published_instrument() -> None:
    """The FFNI is a fixed, licensed instrument — 22 items in six subscales, 7-point."""
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    assert ffni.scale == (1, 7)
    assert len(ffni.items) == 22, len(ffni.items)
    assert {n: len(v) for n, v in ffni.subscales.items()} == {
        "protection": 4, "affiliation": 4, "status": 4,
        "vision": 3, "expertise": 3, "fairness": 4,
    }
    assert "CC BY-NC-ND" in ffni.license  # ND: items must not be reworded
    assert "apl0001347" in ffni.citation


def test_ffni_mediation_borrows_personas_instead_of_copying_them() -> None:
    study = load_study("ffni_mediation")
    assert study.personas_from == "prestige_dominance"
    assert study.personas_dir == load_study("prestige_dominance").personas_dir
    assert (study.personas_dir / "P1.agent.json").exists()


def test_subscale_scores_drop_bad_ratings_rather_than_impute() -> None:
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    answers = {"protection_1": 6, "protection_2": 7, "protection_3": None, "protection_4": 99}
    scores = subscale_scores(answers, ffni)
    assert scores["protection"] == 6.5, scores["protection"]   # 99 out of range, None missing
    assert math.isnan(scores["status"])                        # nothing answered at all


def test_straight_lining_detects_a_dead_scale() -> None:
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    flat = {item_id: 7 for item_id, _, _ in ffni.items}
    varied = {item_id: (i % 5) + 1 for i, (item_id, _, _) in enumerate(ffni.items)}
    record = {"measures": {"baseline": {"ffni": {"N1": flat, "N2": flat, "N3": varied}}}}
    assert straight_lining(record, "baseline", ffni) == 2 / 3


def test_cronbach_alpha_high_when_items_agree_and_nan_when_flat() -> None:
    agreeing = [[5, 5, 5], [2, 2, 2], [7, 7, 7], [3, 3, 3]]
    assert cronbach_alpha(agreeing) > 0.9
    assert math.isnan(cronbach_alpha([[4, 4], [4, 4], [4, 4]]))   # no between-person variance
    assert math.isnan(cronbach_alpha([[1, 2, 3]]))                # too few respondents


def _needs_record(run_no: int, protection: int, d_rating: int, p_rating: int = 4) -> dict:
    """A run where every neutral reports the same protection need and rates the same way."""
    ffni_answers = {}
    for name, count in (("protection", 4), ("affiliation", 4), ("status", 4),
                        ("vision", 3), ("expertise", 3), ("fairness", 4)):
        for i in range(1, count + 1):
            ffni_answers[f"{name}_{i}"] = protection if name == "protection" else 4
    neutrals = ["N1", "N2", "N3", "N4"]
    return {
        "run_no": run_no, "members": {"P": ["P1"], "D": ["D1"], "N": neutrals},
        "transcript": [], "votes": [],
        "measures": {
            "baseline": {"ffni": {pid: dict(ffni_answers) for pid in neutrals}},
            "post": {
                "ffni": {pid: dict(ffni_answers) for pid in neutrals},
                "effectiveness": {
                    pid: {"D1": {"effectiveness_1": d_rating},
                          "P1": {"effectiveness_1": p_rating}}
                    for pid in neutrals
                },
            },
        },
    }


def test_summarize_needs_reports_the_within_persona_change() -> None:
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    record = _needs_record(1, protection=6, d_rating=5)
    # Post-discussion protection rises to 7 for everyone.
    for answers in record["measures"]["post"]["ffni"].values():
        for i in range(1, 5):
            answers[f"protection_{i}"] = 7

    summary = summarize_needs(study, [record], ffni)
    protection = summary["subscales"]["protection"]
    assert protection["baseline_mean"] == 6.0
    assert protection["post_mean"] == 7.0
    assert protection["delta_mean"] == 1.0
    assert protection["delta_n"] == 4
    assert summary["subscales"]["status"]["delta_mean"] == 0.0


def test_mediation_finds_the_indirect_path_when_it_is_there() -> None:
    """Threat raises protection, and higher protection goes with rating D as effective."""
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    effectiveness = next(i for i in study.instruments if i.key == "effectiveness")

    by_condition = {
        "collaborative": [_needs_record(i, protection=p, d_rating=d)
                          for i, (p, d) in enumerate([(3, 2), (4, 3), (3, 3), (4, 2)], 1)],
        "threat": [_needs_record(i, protection=p, d_rating=d)
                   for i, (p, d) in enumerate([(6, 6), (7, 7), (6, 5), (7, 6)], 1)],
    }
    med = summarize_mediation(
        study, by_condition, ffni,
        need="protection", outcome_group="D", effectiveness=effectiveness, bootstrap=300,
    )
    assert med["path_a"] > 0, med["path_a"]       # threat raises protection
    assert med["path_b"] > 0, med["path_b"]       # protection tracks D effectiveness
    assert med["indirect"] > 0
    assert med["supported"] is True

    # A design with no condition difference must not produce mediation.
    flat = {"collaborative": by_condition["collaborative"],
            "threat": [_needs_record(i, protection=3, d_rating=2) for i in range(1, 5)]}
    null = summarize_mediation(
        study, flat, ffni,
        need="protection", outcome_group="D", effectiveness=effectiveness, bootstrap=300,
    )
    assert abs(null["path_a"]) < 1.0


def test_need_outcome_links_separates_cognition_from_evaluation() -> None:
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    ideals = next(i for i in study.instruments if i.key == "leader_ideal")
    effectiveness = next(i for i in study.instruments if i.key == "effectiveness")

    records = []
    for run_no, (protection, ideal, d_rating) in enumerate(
        [(2, 2, 5), (4, 5, 5), (6, 8, 5), (7, 9, 5)], 1
    ):
        record = _needs_record(run_no, protection=protection, d_rating=d_rating)
        record["measures"]["post"]["leader_ideal"] = {
            pid: {"protection_ideal_1": ideal, "protection_ideal_2": ideal}
            for pid in record["members"]["N"]
        }
        records.append(record)

    links = need_outcome_links(
        study, records, ffni, ideals=ideals, effectiveness=effectiveness, contrast=("D", "P")
    )
    protection = links["needs"]["protection"]
    assert protection["cognition"]["r"] > 0.95        # need tracks the prototype
    assert math.isnan(protection["evaluation_a"]["r"])  # effectiveness held flat -> no variance
    assert links["contrast"] == ["D", "P"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"  ok  {test.__name__}")
    print(f"\n{len(tests)} checks passed.")
