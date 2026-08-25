#!/usr/bin/env python3
"""Keyword-scan the free-text vote reasons for dominance's defining feature: coercion/fear.

    python3 tools/vote_reason_scan.py pd_matched threat
    python3 tools/vote_reason_scan.py pd_matched collaborative

Cheng et al. (2013) / Henrich & Gil-White (2001) define dominance as influence via fear
and coercion, prestige as influence via freely conferred respect. run_vote asks every
agent for a one-sentence reason (src/discussion.py); this has never been read by any
analysis function — summarize_contrast only counts the vote, not the reason. This script
closes that gap: it checks what vocabulary voters actually use to justify a D or P vote,
against the theory's own defining vocabulary rather than an arbitrary word list.
"""
from __future__ import annotations

import glob
import json
import sys

DECISIVE = ["decisive", "clarity", "responsib", "stepped up", "clear",
           "accountab", "focused"]
COERCIVE = ["forced", "afraid", "fear", "shut down", "refused to listen",
           "dismiss", "intimidat", "threat", "silenc"]
REASONING = ["explain", "evidence", "reasoning", "credit", "data", "logic"]


def hits(reasons: list[str], words: list[str]) -> int:
    return sum(1 for r in reasons if any(w in r for w in words))


def main() -> None:
    study, condition = sys.argv[1], sys.argv[2]
    files = glob.glob(f"results/{study}/{condition}/checkpoints/*.json")
    if not files:
        raise SystemExit(f"No checkpoints at results/{study}/{condition}/checkpoints/")

    by_group: dict[str, list[str]] = {"D": [], "P": []}
    for f in files:
        record = json.loads(open(f).read())
        for vote in record["votes"]:
            group = vote["voted_for_group"]
            if group in by_group:
                by_group[group].append(vote["reason"].lower())

    print(f"{study}/{condition} — vote reasons by group voted for\n")
    for group, reasons in by_group.items():
        n = len(reasons)
        print(f"  {group}  n={n}")
        for label, words in (("decisive/responsible framing", DECISIVE),
                              ("coercion/fear (dominance's defining feature)", COERCIVE),
                              ("reasoning/evidence (prestige's defining feature)", REASONING)):
            h = hits(reasons, words)
            print(f"    {label:<50} {h:>4}/{n} ({h / max(1, n):.0%})")
        print()


if __name__ == "__main__":
    main()
