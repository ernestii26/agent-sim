#!/usr/bin/env python3
"""Self-check for the theme-free core: study loading, run composition, metrics.

    python3 test_core.py

No API calls, no TinyTroupe — everything here is pure logic on dicts.
"""
from __future__ import annotations

import json
import math
import random
import sys
import tempfile
import threading
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from analysis import (  # noqa: E402
    group_metrics, need_outcome_links, persona_metrics, straight_lining, summarize_contrast,
    summarize_mediation, summarize_needs, summarize_validation, weak_subscales,
)
from discussion import (  # noqa: E402
    APIQuotaExhausted, AgentTransport, _administer, _clone_agent, rated_by,
)
from instrument import (  # noqa: E402
    ABOUT_SELF, Instrument, load_instrument, subscale_scores,
)
from persona_store import Participant  # noqa: E402
from pipeline import BalancedSampler  # noqa: E402
from run_record import RunRecord  # noqa: E402
from stats import (  # noqa: E402
    cronbach_alpha, paired_ttest_onesided, partial_betas, slope,
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
        # A study can be seeded but not yet generated — sample_bank.py writes the design,
        # gen_personas.py fills it in later. Only demand the files once the directory is there.
        if study.personas_dir.exists():
            missing = [pid for g in study.groups.values() for pid in g.ids
                       if not (study.personas_dir / f"{pid}.agent.json").exists()]
            assert not missing, f"{name}: personas/ exists but is missing {missing}"
        if study.personas_from:
            continue  # borrows another study's personas, so it has no seeds of its own
        if not study.seeds_path.exists():
            # Personas converted straight from the bank (sample_bank.py --direct) have no
            # generation seeds; bank_sample.json records the provenance instead.
            provenance = study.directory / "bank_sample.json"
            assert provenance.exists(), f"{name}: neither seeds.json nor bank_sample.json"
            sampled = {p["persona_id"] for p in
                       json.loads(provenance.read_text(encoding="utf-8"))["personas"]}
            declared = {pid for g in study.groups.values() for pid in g.ids}
            assert sampled == declared, f"{name}: bank_sample.json and study.json disagree"
            continue
        seeds = json.loads(study.seeds_path.read_text(encoding="utf-8"))
        seeded = {s["persona_id"] for s in seeds["personas"]}
        declared = {pid for g in study.groups.values() for pid in g.ids}
        assert seeded == declared, f"{name}: seeds.json and study.json disagree on persona ids"
        for seed in seeds["personas"]:
            assert seed["prompt"] in seeds["prompts"], f"{name}: unknown prompt {seed['prompt']}"


def test_balanced_sampler_exhausts_pool_before_repeating() -> None:
    sampler = BalancedSampler(3)
    drawn = [sampler.take(1)[0] for _ in range(9)]
    for start in (0, 3, 6):
        assert sorted(drawn[start : start + 3]) == [0, 1, 2], drawn
    batch = BalancedSampler(3).take(4)
    assert sorted(batch[:3]) == [0, 1, 2] and len(batch) == 4, batch


def test_a_run_never_seats_the_same_persona_twice() -> None:
    """8 neutrals taken 3 at a time run the queue dry in the middle of run 3's draw.
    Refilling with a fresh cycle of all 8 could hand back somebody already in that
    cast, and TinyWorld rejects the duplicate name — the study died on run 3."""
    sampler = BalancedSampler(8)
    for run_no in range(1, 30):
        cast = sampler.take(3)
        assert len(set(cast)) == 3, f"run {run_no} drew {cast}"

    # Every id still appears before any repeats: 8 runs of 3 is three full cycles.
    counts: dict[int, int] = {}
    fresh = BalancedSampler(8)
    for _ in range(8):
        for i in fresh.take(3):
            counts[i] = counts.get(i, 0) + 1
    assert sorted(counts) == list(range(8))
    assert max(counts.values()) - min(counts.values()) <= 1, counts

    # A draw wider than the pool has no choice but to repeat, and still may.
    assert len(BalancedSampler(3).take(4)) == 4


def test_balanced_sampler_is_seeded_so_conditions_align() -> None:
    # Run i must draw the same positions in every condition, or the two conditions
    # are compared across different casts.
    a = [BalancedSampler(6, seed=7).take(1)[0] for _ in range(12)]
    b = [BalancedSampler(6, seed=7).take(1)[0] for _ in range(12)]
    assert a == b, (a, b)
    assert a != [BalancedSampler(6, seed=8).take(1)[0] for _ in range(12)]


def test_paired_groups_draw_the_matching_index() -> None:
    # pd_matched builds P_i and D_i from one bank row; drawing them independently
    # throws that away, which is what pair_with exists to prevent.
    from pipeline import compose_run, make_samplers
    from persona_store import Participant

    study = load_study("pd_matched")
    assert study.groups["D"].pair_with == "P", "pd_matched must pair D to P"
    pool = {
        pid: Participant(agent=None, persona_id=pid, name=pid, group=group.key)
        for group in study.groups.values()
        for pid in group.ids
    }
    samplers = make_samplers(study)
    assert "D" not in samplers, "a paired group must not carry its own sampler"
    for _ in range(20):
        cast = compose_run(study, pool, samplers)
        picked = {p.group: p.persona_id for p in cast if p.group in ("P", "D")}
        assert picked["P"][1:] == picked["D"][1:], picked


def test_compose_run_respects_group_sampling() -> None:
    from pipeline import compose_run, make_samplers
    from persona_store import Participant

    study = load_study("prestige_dominance")
    pool = {
        pid: Participant(agent=None, persona_id=pid, name=pid, group=group.key)
        for group in study.groups.values()
        for pid in group.ids
    }
    samplers = make_samplers(study)
    for _ in range(20):
        chosen = [p.persona_id for p in compose_run(study, pool, samplers)]
        assert len(chosen) == len(set(chosen)), "a persona was cast twice in one run"
        for key, group in study.groups.items():
            n = sum(1 for pid in chosen if study.group_of(pid) == key)
            assert n == (len(group.ids) if group.sample is None else group.sample)


def _record(run_no: int = 1, p_votes: int = 2, neutrals: tuple[str, ...] = ()) -> RunRecord:
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
    # `p_votes` counts NEUTRAL ballots for P; the two candidates cross-vote, the way
    # they do in the real records, so the electorate restriction has something to strip.
    votes = [
        {"voter_id": pid, "voter_group": "N",
         "voted_for_id": "P1" if i < p_votes else "D1",
         "voted_for_group": "P" if i < p_votes else "D", "reason": ""}
        for i, pid in enumerate(neutrals)
    ] + [
        {"voter_id": "P1", "voter_group": "P",
         "voted_for_id": "D1", "voted_for_group": "D", "reason": ""},
        {"voter_id": "D1", "voter_group": "D",
         "voted_for_id": "P1", "voted_for_group": "P", "reason": ""},
    ]
    return RunRecord.from_dict(
        {"run_no": run_no, "condition": "collaborative",
         "members": {"P": ["P1"], "D": ["D1"], "N": list(neutrals)},
         "transcript": tr, "votes": votes, "measures": {}}
    )


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


def test_summarize_contrast_counts_only_the_electorate() -> None:
    """The contrasted groups stand for election, so their own ballots stay out of the DV."""
    study = load_study("prestige_dominance")
    ns = ("N1", "N2", "N3")
    records = [_record(1, p_votes=2, neutrals=ns), _record(2, p_votes=3, neutrals=ns)]

    collab = summarize_contrast(study, study.condition("collaborative"), records)
    assert collab["electorate"] == ["N"]
    # Each candidate voted for the other; neither ballot reaches per_run.
    assert collab["candidate_votes"] == {"P": 2, "D": 2}, collab["candidate_votes"]
    assert collab["per_run"] == [{"run_no": 1, "P": 2.0, "D": 1.0},
                                 {"run_no": 2, "P": 3.0, "D": 0.0}]
    assert collab["wins"] == 2
    assert collab["metrics"]["votes"]["P"]["mean"] == 2.5
    assert collab["metrics"]["votes"]["D"]["mean"] == 0.5

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
    """The FFNI is a fixed, licensed instrument — 22 items in six subscales, 7-point.

    Checked in every study that carries it: the file is copied per study, so a divergent
    copy is exactly the failure this catches.
    """
    carriers = [s for s in map(load_study, list_studies())
                if any(i.key == "ffni" for i in s.instruments)]
    assert carriers, "no study carries the FFNI"
    for study in carriers:
        ffni = next(i for i in study.instruments if i.key == "ffni")
        assert ffni.scale == (1, 7), study.name
        assert len(ffni.items) == 22, (study.name, len(ffni.items))
        assert {n: len(v) for n, v in ffni.subscales.items()} == {
            "protection": 4, "affiliation": 4, "status": 4,
            "vision": 3, "expertise": 3, "fairness": 4,
        }, study.name
        assert "CC BY-NC-ND" in ffni.license, study.name  # ND: items must not be reworded
        assert "apl0001347" in ffni.citation, study.name


def test_ffni_mediation_borrows_personas_instead_of_copying_them() -> None:
    """It borrows pd_matched's, not prestige_dominance's — the mediation has to run on
    the matched pairs, or every confound pd_matched removes comes back."""
    study = load_study("ffni_mediation")
    matched = load_study("pd_matched")
    assert study.personas_from == "pd_matched"
    assert study.personas_dir == matched.personas_dir
    assert (study.personas_dir / "P1.agent.json").exists()
    assert study.groups["D"].pair_with == "P"
    assert {k: g.ids for k, g in study.groups.items()} == {k: g.ids for k, g in matched.groups.items()}
    # design-log section 13's manipulation evidence was measured on pd_matched's wording,
    # so it only transfers while the wording stays identical.
    for key, cond in study.conditions.items():
        assert cond.scenario == matched.conditions[key].scenario, key
        assert cond.friction == matched.conditions[key].friction, key


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
    record = RunRecord.from_dict(
        {"run_no": 1, "measures": {"baseline": {"ffni": {"N1": flat, "N2": flat, "N3": varied}}}}
    )
    assert straight_lining(record, "baseline", ffni) == 2 / 3


def test_cronbach_alpha_high_when_items_agree_and_nan_when_flat() -> None:
    agreeing = [[5, 5, 5], [2, 2, 2], [7, 7, 7], [3, 3, 3]]
    assert cronbach_alpha(agreeing) > 0.9
    assert math.isnan(cronbach_alpha([[4, 4], [4, 4], [4, 4]]))   # no between-person variance
    assert math.isnan(cronbach_alpha([[1, 2, 3]]))                # too few respondents


def _needs_record(run_no: int, protection: int, d_rating: int, p_rating: int = 4,
                  baseline_protection: int | None = None, d_voters: int = 0) -> RunRecord:
    """A run where every neutral reports the same protection need and rates the same way.

    `baseline_protection` defaults to `protection`, i.e. the scenario induced no change.
    `d_voters` is how many of the four neutrals endorse D; the rest endorse P.
    """
    ffni_answers = {}
    for name, count in (("protection", 4), ("affiliation", 4), ("status", 4),
                        ("vision", 3), ("expertise", 3), ("fairness", 4)):
        for i in range(1, count + 1):
            ffni_answers[f"{name}_{i}"] = protection if name == "protection" else 4
    neutrals = ["N1", "N2", "N3", "N4"]
    base_answers = dict(ffni_answers)
    if baseline_protection is not None:
        for i in range(1, 5):
            base_answers[f"protection_{i}"] = baseline_protection
    votes = [
        {"voter_id": pid, "voter_group": "N",
         "voted_for_id": "D1" if i < d_voters else "P1",
         "voted_for_group": "D" if i < d_voters else "P", "reason": ""}
        for i, pid in enumerate(neutrals)
    ]
    return RunRecord.from_dict({
        "run_no": run_no, "condition": "threat",
        "members": {"P": ["P1"], "D": ["D1"], "N": neutrals},
        "transcript": [], "votes": votes,
        "measures": {
            "baseline": {"ffni": {pid: dict(base_answers) for pid in neutrals}},
            "post": {
                "ffni": {pid: dict(ffni_answers) for pid in neutrals},
                "effectiveness": {
                    pid: {"D1": {"effectiveness_1": d_rating},
                          "P1": {"effectiveness_1": p_rating}}
                    for pid in neutrals
                },
            },
        },
    })


def test_summarize_needs_reports_the_within_persona_change() -> None:
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")
    record = _needs_record(1, protection=6, d_rating=5)
    # Post-discussion protection rises to 7 for everyone.
    for answers in record.measures["post"]["ffni"].values():
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
    """Threat induces more protection, and within a condition a bigger induced change
    goes with endorsing D."""
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")

    def runs(spec):  # (induced change, how many of 4 neutrals endorse D), x3 runs each
        spec = spec * 3
        return [_needs_record(i, protection=3 + rise, d_rating=4,
                              baseline_protection=3, d_voters=dv)
                for i, (rise, dv) in enumerate(spec, 1)]

    by_condition = {
        "collaborative": runs([(0, 0), (0, 1), (1, 1), (1, 2)]),
        "threat": runs([(2, 2), (2, 3), (3, 3), (3, 4)]),
    }
    med = summarize_mediation(
        study, by_condition, ffni, need="protection", outcome_group="D", bootstrap=300,
    )
    assert med["path_a"] > 0, med["path_a"]       # threat induces more protection
    assert med["path_b"] > 0, med["path_b"]       # within condition, more change -> more D
    assert med["indirect"] > 0
    assert med["supported"] is True


def test_mediation_is_not_fooled_by_a_condition_difference_alone() -> None:
    """The regression test for the pooled-slope bug: threat shifts BOTH the induced need
    and endorsement, but within a condition the two are unrelated. Estimating path b on
    raw pooled scores reports mediation here; centring within condition does not."""
    study = load_study("ffni_mediation")
    ffni = next(i for i in study.instruments if i.key == "ffni")

    def runs(spec):
        return [_needs_record(i, protection=3 + rise, d_rating=4,
                              baseline_protection=3, d_voters=dv)
                for i, (rise, dv) in enumerate(spec, 1)]

    by_condition = {
        "collaborative": runs([(0, 1), (0, 1), (1, 1), (1, 1)]),   # endorsement flat at 1/4
        "threat": runs([(2, 3), (2, 3), (3, 3), (3, 3)]),          # flat at 3/4
    }
    med = summarize_mediation(
        study, by_condition, ffni, need="protection", outcome_group="D", bootstrap=300,
    )
    assert med["path_a"] > 0, med["path_a"]        # the condition really did shift the need
    assert abs(med["path_b"]) < 1e-9, med["path_b"]  # but nothing within condition
    assert med["supported"] is False, med["ci95"]


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
        # protection is predicted to move the ILT strength dimension (strong, bold).
        record.measures["post"]["leader_ideal"] = {
            pid: {"strength_1": ideal, "strength_2": ideal}
            for pid in record.members("N")
        }
        records.append(record)

    links = need_outcome_links(
        study, records, ffni, ideals=ideals, effectiveness=effectiveness, contrast=("D", "P")
    )
    protection = links["needs"]["protection"]
    assert protection["cognition"]["r"] > 0.95        # need tracks the prototype
    assert math.isnan(protection["evaluation_a"]["r"])  # effectiveness held flat -> no variance
    assert links["contrast"] == ["D", "P"]


def test_run_record_round_trips_and_tolerates_pre_instrument_checkpoints() -> None:
    study = load_study("ffni_mediation")
    ffni = study.self_report

    data = _needs_record(1, protection=5, d_rating=4).to_dict()
    assert RunRecord.from_dict(data).to_dict() == data
    assert list(data) == ["run_no", "condition", "members", "transcript", "votes", "measures"]

    # A checkpoint written before instruments existed has no "measures" key at all.
    legacy = RunRecord.from_dict({"run_no": 7, "members": {"P": ["P1"]},
                                  "transcript": [], "votes": []})
    assert legacy.needs("post", ffni) == {}
    assert legacy.ratings(study.candidate_rating) == {}
    assert summarize_needs(study, [legacy], ffni)["subscales"]["protection"]["delta_n"] == 0


def test_load_study_rejects_two_instruments_of_the_same_kind() -> None:
    import study as study_module

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        directory = root / "dup"
        (directory / "instruments").mkdir(parents=True)
        for key in ("first", "second"):
            (directory / "instruments" / f"{key}.json").write_text(json.dumps({
                "instructions": "rate", "scale": [1, 7], "about": "self",
                "subscales": {"protection": ["item"]},
            }), encoding="utf-8")
        (directory / "study.json").write_text(json.dumps({
            "groups": {"N": {"ids": ["N1"]}},
            "contrast": ["N", "N"],
            "conditions": {"only": {"scenario": "x"}},
            "instruments": ["first", "second"],
        }), encoding="utf-8")

        original = study_module.STUDIES_DIR
        study_module.STUDIES_DIR = root
        try:
            load_study("dup")
        except SystemExit as exc:
            assert "first" in str(exc) and "second" in str(exc) and "dup" in str(exc), exc
        else:
            raise AssertionError("two about='self' instruments were accepted")
        finally:
            study_module.STUDIES_DIR = original

# --- survey parsing, driven through the transport seam (no API, no TinyTroupe) ---

_PROBE = Instrument(
    key="probe", title="Probe", instructions="Rate.", scale=(1, 5), anchors=("low", "high"),
    subscales={"s": ("a", "b")}, about=ABOUT_SELF, targets=(), timing=("post",),
    citation="", license="", note="",
)
_RESPONDENT = Participant(agent=None, persona_id="X1", name="Probe Person", group="N")


def _scripted(*replies: str):
    """A fake transport: hands back the next canned reply and counts the calls."""
    calls = []

    def ask(agent, prompt):
        calls.append(prompt)
        return replies[min(len(calls), len(replies)) - 1]

    return ask, calls


def test_survey_scores_a_well_formed_reply() -> None:
    ask, calls = _scripted('here you go: {"s_1": 4, "s_2": 2} thanks')
    result = _administer(_RESPONDENT, _PROBE, target=None, ask=ask)
    assert result["s_1"] == 4 and result["s_2"] == 2
    assert result["_meta"] == {"attempts": 1, "answered": 2, "complete": True}
    assert len(calls) == 1


def test_survey_nulls_a_rating_outside_the_scale() -> None:
    ask, _ = _scripted('{"s_1": 4, "s_2": 9}')
    result = _administer(_RESPONDENT, _PROBE, target=None, ask=ask)
    assert result["s_1"] == 4 and result["s_2"] is None
    assert result["_meta"]["complete"] is False and result["_meta"]["answered"] == 1


def test_survey_retries_once_then_records_nulls() -> None:
    ask, calls = _scripted('{"s_1": 3}', '{"s_1": 3}')
    result = _administer(_RESPONDENT, _PROBE, target=None, ask=ask)
    assert len(calls) == 2, "a partial answer gets exactly one retry"
    assert result["s_2"] is None and result["_meta"] == {
        "attempts": 2, "answered": 1, "complete": False,
    }


def test_survey_survives_a_non_json_reply() -> None:
    ask, calls = _scripted("I would rather not answer that.")
    result = _administer(_RESPONDENT, _PROBE, target=None, ask=ask)
    assert result["s_1"] is None and result["s_2"] is None
    assert result["_meta"]["complete"] is False and len(calls) == 2


class _FlakyAgent:
    """Stands in for a TinyPerson: raises the P1 TypeError until told otherwise."""

    def __init__(self, fail: bool = True) -> None:
        self.fail = fail

    def listen_and_act(self, prompt, return_actions=False, communication_display=True):
        if self.fail:
            raise TypeError("'NoneType' object is not subscriptable")
        return [{"action": {"type": "TALK", "content": "hi"}}]


def test_transport_counter_resets_on_success_and_aborts_after_five_failures() -> None:
    transport = AgentTransport(retries=1)  # retries=1 so the test never sleeps
    agent = _FlakyAgent()
    for _ in range(4):
        assert transport.actions(agent, "p") == []
    agent.fail = False
    transport.actions(agent, "p")
    assert transport.consecutive_failures == 0, "a success clears the counter"

    agent.fail = True
    for _ in range(4):
        transport.actions(agent, "p")
    try:
        transport.actions(agent, "p")
    except APIQuotaExhausted:
        pass
    else:
        raise AssertionError("5 consecutive exhausted-retry failures must abort the run")


def test_transports_do_not_share_a_failure_counter() -> None:
    agent = _FlakyAgent()
    first = AgentTransport(retries=1)
    for _ in range(4):
        first.actions(agent, "p")
    second = AgentTransport(retries=1)
    second.actions(agent, "p")  # would be the 5th failure if the counter were global
    assert second.consecutive_failures == 1 and first.consecutive_failures == 4


# --------------------------------------------------------------------------- #
# Persona bank sampling                                                        #
# --------------------------------------------------------------------------- #

def _sample_bank_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sample_bank", PROJECT_DIR / "tools" / "sample_bank.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_bank(profiles: int, per_profile: int = 3) -> list[dict]:
    levels = ["low", "medium", "high"]
    bank = []
    for i in range(profiles):
        ocean = {t: levels[(i + j) % 3] for j, t in enumerate(
            ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"))}
        for k in range(per_profile):
            bank.append({
                "ocean_description": {"ocean": ocean, "description_en": f"p{i}", "is_valid": True},
                "occupation": f"job{k}",
                "demographic": {"age_group": "36-50", "is_parent": k % 2 == 0},
            })
    return bank


def test_split_parsing_rejects_nonsense() -> None:
    sb = _sample_bank_module()
    assert sb.parse_split("P=6,D=6,N=24") == {"P": 6, "D": 6, "N": 24}
    for bad in ("P=0", "P=-1", "P", "P=x", "=3"):
        try:
            sb.parse_split(bad)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"accepted bad split {bad!r}")


def test_sampling_never_repeats_a_personality_and_refuses_to_overdraw() -> None:
    sb = _sample_bank_module()
    bank = _fake_bank(profiles=3, per_profile=4)   # only 3 distinct OCEAN profiles

    picked = sb.stratified_sample(bank, 3, random.Random(0))
    keys = [tuple(e["ocean_description"]["ocean"].values()) for e in picked]
    assert len(set(keys)) == 3, keys

    # Asking for more than the bank can supply without repeating must fail loudly,
    # not silently hand back duplicate personalities.
    try:
        sb.stratified_sample(bank, 4, random.Random(0))
    except SystemExit as exc:
        assert "distinct OCEAN profiles" in str(exc)
    else:
        raise AssertionError("overdrawing was allowed")


def test_assigned_style_reaches_the_generation_prompt() -> None:
    """A leadership label the prompt does not carry would leave the agent unchanged."""
    sb = _sample_bank_module()
    entry = _fake_bank(profiles=1, per_profile=1)[0]

    dominance = sb.build_user_prompt(entry, "D")
    assert "DOMINANCE" in dominance
    assert "traits, mannerisms" in dominance          # style must be woven in, not labelled
    assert entry["ocean_description"]["description_en"] in dominance

    neutral = sb.build_user_prompt(entry, "N")
    assert "NOT a natural leader" in neutral
    assert "DOMINANCE" not in neutral and "PRESTIGE" not in neutral

    # gen_personas.py substitutes this by plain replacement, so a prompt may also
    # contain unrelated braces (the rendered score dict does).
    assert "{existing_names}" in dominance
    assert dominance.replace("{existing_names}", "Ana, Bo").count("Ana, Bo") == 1


def test_a_survey_clone_never_shares_memory_with_the_agent_that_votes() -> None:
    """After a discussion the agent still holds its TinyWorld, and the world holds a
    lock deepcopy cannot follow. That failure used to be swallowed and the ORIGINAL
    agent handed back, so every post-discussion survey wrote its items into the agent
    that voted moments later. The lock here stands in for the live world."""

    class FakeAgent:
        def __init__(self) -> None:
            self.environment = threading.RLock()
            self._accessible_agents: list = []
            self.episodic_memory = ["turn 1", "turn 2"]
            self.actions_count = 7

    original = FakeAgent()
    world = original.environment
    clone = _clone_agent(original)

    assert clone is not original, "a survey must never run on the agent that votes"
    assert clone.episodic_memory == ["turn 1", "turn 2"]   # the discussion carries over
    clone.episodic_memory.append("SURVEY ITEM")
    assert "SURVEY ITEM" not in original.episodic_memory
    assert clone.environment is None and clone.actions_count == 0
    assert original.environment is world, "the original's wiring must be put back"

    # A copy that genuinely cannot be made is an error, not a silent original.
    broken = FakeAgent()
    broken.episodic_memory = threading.RLock()    # not live wiring, so not detachable
    try:
        _clone_agent(broken)
    except Exception:
        pass
    else:
        raise AssertionError("an impossible clone must raise, not return the original")


def test_alpha_gate_judges_each_read_subscale_not_the_average() -> None:
    """A mean over ten subscales waves a dead one through on the back of the long ones.
    It matters here because `protection` reaches exactly one prototype dimension."""
    summary = {
        "subscales": {
            "strength": {"alpha": 0.05},        # 2 items, and protection's only outlet
            "tyranny": {"alpha": 0.92},         # 10 items
            "sensitivity": {"alpha": 0.88},     # 8 items
            "femininity": {"alpha": float("nan")},
        },
        "gated_subscales": ["sensitivity", "strength", "tyranny"],
    }
    assert (0.05 + 0.92 + 0.88) / 3 > 0.60, "the old mean-based gate would have passed this"
    assert set(weak_subscales(summary)) == {"strength"}

    summary["subscales"]["strength"]["alpha"] = 0.71
    assert weak_subscales(summary) == {}

    # An alpha that could not be computed does not pass either.
    summary["gated_subscales"].append("femininity")
    assert set(weak_subscales(summary)) == {"femininity"}


def test_the_gate_covers_every_prototype_dimension_an_analysis_reads() -> None:
    """`gated_subscales` comes from the prediction map, so a dimension added to
    `predicts` is gated automatically and one nothing reads never blocks a study."""
    ideals = load_study("ffni_mediation").prototype
    read = {dim for dims in ideals.predicts.values() for dim in dims}
    assert read <= set(ideals.subscales)
    assert ideals.predicts["protection"] == ("strength",), \
        "protection has one outlet; if that changes, the alpha gate's stakes change too"
    assert "femininity" in ideals.subscales and "femininity" not in read
    # Sheng et al. Table 13 gives affiliation no significant increment on any of the
    # eleven dimensions — its bivariate correlations are large and its delta R2 is .00
    # or .01 throughout. An entry here would be a guess dressed as a replication.
    assert "affiliation" not in ideals.predicts


def test_each_candidate_rates_only_the_candidates() -> None:
    """Every rating is its own API call carrying the whole transcript, and
    need_outcome_links reads only the contrasted groups — so rating the neutrals is
    the most expensive way in the design to collect data nothing looks at."""
    room = [
        Participant(agent=None, persona_id=pid, name=pid, group=g)
        for pid, g in (("P4", "P"), ("D4", "D"), ("N4", "N"), ("N7", "N"), ("N8", "N"))
    ]
    rater = room[2]                                   # N4

    everyone = rated_by(room, rater)                  # no contrast: the whole room
    assert [p.persona_id for p in everyone] == ["P4", "D4", "N7", "N8"]

    candidates = rated_by(room, rater, ("D", "P"))
    assert [p.persona_id for p in candidates] == ["P4", "D4"]
    assert rater not in candidates, "nobody rates themselves"

    # At a cast of 5 that is 6 calls per run instead of 12.
    neutrals = [p for p in room if p.group == "N"]
    assert sum(len(rated_by(room, n, ("D", "P"))) for n in neutrals) == 6
    assert sum(len(rated_by(room, n)) for n in neutrals) == 12


def test_partial_betas_separate_a_real_predictor_from_its_correlate() -> None:
    """Sheng et al.'s six needs intercorrelate .60-.72, so their Table 13's bivariate
    column makes all six predict every prototype dimension at p < .001 while the
    increment over the other five picks out one. H4 is the second claim, not the first."""
    rng = random.Random(7)
    protection, tagalong, outcome = [], [], []
    for _ in range(200):
        p = rng.gauss(0, 1)
        protection.append(p)
        tagalong.append(p + rng.gauss(0, 0.5))       # rides on protection, causes nothing
        outcome.append(2 * p + rng.gauss(0, 1))      # driven by protection alone

    assert slope(tagalong, outcome)[1] > 0.6, "bivariately the tag-along looks real"

    predictors = [[a, b] for a, b in zip(protection, tagalong)]
    betas, deltas, model_r2, n = partial_betas(predictors, outcome)
    assert n == 200 and model_r2 > 0.7
    assert betas[0] > 0.7 and abs(betas[1]) < 0.20, betas
    # delta R2 is UNIQUE variance, so collinearity shrinks it: the tag-along at r ~ .89
    # leaves protection only a fraction of what it explains alone. This is why the
    # paper's headline increments are .02-.06 while the same betas are .19-.32 — a small
    # delta R2 there is not a weak result, and the gate on it must not read like one.
    assert deltas[0] > 0.10 and deltas[1] < 0.01, deltas

    # Missing values drop the whole row, not the column.
    predictors[0][1] = float("nan")
    assert partial_betas(predictors, outcome)[3] == 199
    # Too few rows to fit is n/a, never a fabricated coefficient.
    assert math.isnan(partial_betas(predictors[:2], outcome[:2])[2])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"  ok  {test.__name__}")
    print(f"\n{len(tests)} checks passed.")
