#!/usr/bin/env python3
"""What can the layer hypotheses resolve at the runs config.ini asks for?

    python3 tools/layer_power.py --reps 100

power_sim.py sizes the VOTE. H3 to H7 are different estimands on a different n: the
vote gets one paired observation per run, while the layer regressions get three
clustered respondent rows per run and the mediation multiplies two noisy paths. "40
runs is comfortable" was established for H1 and H2 and was simply unknown for
everything Step 2 exists to measure.

Detection here means the estimator's own bootstrap interval excludes zero — the same
rule the reports use, run on the real `summarize_layer_moderation` and
`summarize_mediation` rather than on a formula for them.

# ponytail: respondents are drawn independently around a per-run offset, which gives
# the clustering the bootstrap has to survive but not the way a real discussion moves a
# room. Effect sizes are assumptions until measure-check reports the noise floor; re-run
# with --sd-induced set to the observed delta SD once it does.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analysis import summarize_layer_moderation, summarize_mediation  # noqa: E402
from run_record import RunRecord  # noqa: E402
from study import load_study  # noqa: E402

NEEDS = (("protection", 4), ("affiliation", 4), ("status", 4),
         ("vision", 3), ("expertise", 3), ("fairness", 4))


def make_run(run_no: int, condition: str, rng: random.Random, *, lift: float,
             beta_proto: float, beta_eff: float, b_vote: float,
             sd_induced: float, respondents: int) -> RunRecord:
    """One room. `lift` is path a; the betas are how far the induced need reaches."""
    room = rng.gauss(0, 0.3)          # what this discussion did to everyone in it
    neutrals = [f"N{i}" for i in range(1, respondents + 1)]
    baseline, post, proto_base, proto_post, effect, votes = {}, {}, {}, {}, {}, []
    for pid in neutrals:
        level = rng.uniform(2.0, 6.0)
        induced = lift + room + rng.gauss(0, sd_induced)
        after = level + induced
        baseline[pid] = {}
        post[pid] = {}
        for name, count in NEEDS:
            base = level if name == "protection" else rng.uniform(2.0, 6.0)
            end = after if name == "protection" else base
            for i in range(1, count + 1):
                baseline[pid][f"{name}_{i}"] = base
                post[pid][f"{name}_{i}"] = end
        moved = beta_proto * induced + rng.gauss(0, 1.0)
        proto_base[pid] = {"strength_1": level, "strength_2": level}
        proto_post[pid] = {"strength_1": level + moved, "strength_2": level + moved}
        rating = 4.0 + beta_eff * induced + rng.gauss(0, 1.0)
        effect[pid] = {"D1": {"effectiveness_1": rating},
                       "P1": {"effectiveness_1": rng.gauss(4.0, 1.0)}}
        endorsed = "D" if rng.random() < min(max(0.5 + b_vote * induced, 0.0), 1.0) else "P"
        votes.append({"voter_id": pid, "voter_group": "N", "voted_for_id": endorsed + "1",
                      "voted_for_group": endorsed, "reason": ""})
    return RunRecord.from_dict({
        "run_no": run_no, "condition": condition,
        "members": {"P": ["P1"], "D": ["D1"], "N": neutrals},
        "transcript": [], "votes": votes,
        "measures": {"baseline": {"ffni": baseline, "leader_ideal": proto_base},
                     "post": {"ffni": post, "leader_ideal": proto_post,
                              "effectiveness": effect}},
    })


def one_rep(study, rng: random.Random, runs: int, draws: int, **kw) -> dict[str, bool]:
    flat = dict(kw, lift=0.0)          # the collaborative arm is the no-shift baseline
    by_condition = {
        "collaborative": [make_run(i, "collaborative", rng, **flat)
                          for i in range(1, runs + 1)],
        "threat": [make_run(i, "threat", rng, **kw) for i in range(1, runs + 1)],
    }
    layers = summarize_layer_moderation(
        study, by_condition, study.self_report, ideals=study.prototype,
        effectiveness=study.candidate_rating, contrast=("D", "P"),
        bootstrap=draws, seed=rng.randrange(10**6),
    )
    med = summarize_mediation(
        study, by_condition, study.self_report, need="protection", outcome_group="D",
        bootstrap=draws, seed=rng.randrange(10**6),
    )
    p = layers["needs"]["protection"]

    def clear(bounds) -> bool:
        return bool(bounds) and (bounds[0] > 0 or bounds[1] < 0)

    return {
        "H3 induced need moved": clear(p["induced"]["ci95"]),
        "H4 need -> prototype (within)": clear(p["cognition_induced"]["ci95"]),
        "H5 need -> effectiveness": clear(p["evaluation_a"]["ci95"]),
        "H6 indirect a*b": bool(med["supported"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--study", default="ffni_mediation")
    ap.add_argument("--runs", type=int, nargs="+", default=[20, 40])
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--draws", type=int, default=200, help="bootstrap draws per rep")
    ap.add_argument("--respondents", type=int, default=3)
    ap.add_argument("--lift", type=float, default=0.5, help="path a: induced-need shift")
    ap.add_argument("--beta-proto", type=float, default=0.5)
    ap.add_argument("--beta-eff", type=float, default=0.0, help="0 = H5's expected null")
    ap.add_argument("--b-vote", type=float, default=0.10)
    ap.add_argument("--sd-induced", type=float, default=1.0,
                    help="measurement noise on the induced need; measure-check reports it")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    study = load_study(args.study)
    print(f"\nlift={args.lift}  beta_proto={args.beta_proto}  beta_eff={args.beta_eff}  "
          f"b_vote={args.b_vote}  sd_induced={args.sd_induced}")
    print(f"{args.reps} reps, {args.draws} bootstrap draws, "
          f"{args.respondents} respondents per run\n")

    labels = ["H3 induced need moved", "H4 need -> prototype (within)",
              "H5 need -> effectiveness", "H6 indirect a*b"]
    print(f"{'runs/condition':<16}" + "".join(f"{k:>32}" for k in labels))
    print("-" * (16 + 32 * len(labels)))
    for runs in args.runs:
        rng = random.Random(args.seed)
        hits = {k: 0 for k in labels}
        for _ in range(args.reps):
            for key, ok in one_rep(study, rng, runs, args.draws,
                                   respondents=args.respondents, lift=args.lift,
                                   beta_proto=args.beta_proto, beta_eff=args.beta_eff,
                                   b_vote=args.b_vote, sd_induced=args.sd_induced).items():
                hits[key] += ok
        print(f"{runs:<16}" + "".join(f"{hits[k] / args.reps:>31.0%} " for k in labels))
    print("\nH5's column is a FALSE-positive rate when --beta-eff is 0: the paper's null is")
    print("the expected result there, so what matters is that it stays near 5%.\n")


if __name__ == "__main__":
    main()
