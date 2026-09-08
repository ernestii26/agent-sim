#!/usr/bin/env python3
"""Build the scenario pools from HiddenBench, and record exactly how they were built.

HiddenBench (Li, Naito & Shirado, arXiv:2505.11556; github.com/jonradoff/hiddenbench,
MIT) is 65 hidden-profile tasks: facts are split so no single agent can reach the right
answer alone. We use it for two things this study could not do with a hand-written
vignette:

  * The threat manipulation stops being ours. The corpus already contains both
    life-threatening and routine decisions, so the contrast is drawn from someone
    else's stimuli instead of written to fit the hypothesis.
  * Every task has a correct answer, so endorsement can be scored against whether the
    group actually decided well.

Run it again and you get the same file; the classification below is data, not judgment
applied at run time.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=YuxuanLi1225%2FHiddenBench&config=default&split=train&offset=0&length=100"
)
OUT = Path(__file__).resolve().parent.parent / "studies/ffni_mediation/scenarios/hiddenbench.json"

# Classified once, by hand, against one rule applied to the task text:
#
#   threat  — human lives or bodily safety are at immediate risk AND the decision is
#             time-critical (evacuations, casualties, life-saving transport).
#   routine — a wrong answer costs money, convenience, or a research result. Nobody is
#             in danger.
#
# Tasks where only property or data is at stake (ransomware, a datacenter, a stolen
# painting) sit between the poles and are in NEITHER pool: including them would blunt
# the manipulation, and deciding case by case which way they lean is the experimenter
# degree of freedom this whole exercise is meant to remove.
THREAT = {1, 2, 3, 9, 10, 12, 19, 20, 21, 22, 25, 26, 28, 29, 32, 33, 34, 35, 37, 38,
          39, 40, 41, 42, 45, 46, 51, 52, 55, 65}
ROUTINE = {4, 5, 6, 7, 8, 13, 14, 17, 18, 23, 27, 30, 31, 44, 47, 49, 54, 57, 59, 60,
           61, 62, 63}

# The tasks were written for four agents; this study runs five (1 P + 1 D + 3 N). A
# description that names the wrong headcount invites the agents to hunt for a missing
# person, so the count is rewritten. Nothing else about the prose changes.
HEADCOUNT = [
    (r"\bthe other three\b", "the other four"),
    (r"\bthree other\b", "four other"),
    (r"\bthree colleagues\b", "four colleagues"),
    (r"\bfour[- ]person\b", "five-person"),
    (r"\bfour scientists\b", "five scientists"),
    (r"\bfour council members\b", "five council members"),
    (r"\bfour of you\b", "five of you"),
]

# Payment and clock promises we cannot keep: these agents earn nothing and the chat has
# a fixed number of rounds. Left in, they are an incentive manipulation nobody asked for.
DROP_SENTENCE = re.compile(
    r"[^.\n]*(?:\$\d|you will earn|maximize your rewards|15 minutes"
    r"|the exact time when the chat)[^.\n]*\.?",
    re.I,
)


def normalise(text: str) -> str:
    text = DROP_SENTENCE.sub("", text)
    for pattern, replacement in HEADCOUNT:
        text = re.sub(pattern, replacement, text, flags=re.I)
    text = re.sub(r"You are participating in a study, acting as", "You are", text)
    text = re.sub(r"You are participating in a study and are", "You are", text)
    # Removing whole sentences leaves ragged spacing behind.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"After the discussion:\s*\n?", "", text)
    return text.strip()


def main() -> int:
    with urllib.request.urlopen(URL, timeout=60) as response:
        rows = [row["row"] for row in json.load(response)["rows"]]
    if len(rows) != 65:
        return _fail(f"expected 65 tasks, got {len(rows)}")

    by_id = {row["id"]: row for row in rows}
    unknown = (THREAT | ROUTINE) - set(by_id)
    if unknown:
        return _fail(f"classified ids not present upstream: {sorted(unknown)}")
    if THREAT & ROUTINE:
        return _fail(f"ids in both pools: {sorted(THREAT & ROUTINE)}")

    pools = {
        name: [
            {
                "id": by_id[i]["id"],
                "name": by_id[i]["name"],
                "description": normalise(by_id[i]["description"]),
                "shared": list(by_id[i]["shared_information"]),
                "hidden": list(by_id[i]["hidden_information"]),
                "options": list(by_id[i]["possible_answers"]),
                "correct": by_id[i]["correct_answer"],
            }
            for i in sorted(ids)
        ]
        for name, ids in (("threat", THREAT), ("routine", ROUTINE))
    }

    for name, tasks in pools.items():
        for task in tasks:
            if task["correct"] not in task["options"]:
                return _fail(f"{name}/{task['name']}: correct answer is not an option")
            if not task["hidden"]:
                return _fail(f"{name}/{task['name']}: no hidden information to distribute")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": "HiddenBench (Li, Naito & Shirado, arXiv:2505.11556), MIT licence",
                "dataset": "YuxuanLi1225/HiddenBench",
                "built_by": "tools/fetch_hiddenbench.py",
                "excluded": sorted(set(by_id) - THREAT - ROUTINE),
                "pools": pools,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"{OUT}: threat={len(pools['threat'])} routine={len(pools['routine'])} "
          f"excluded={len(by_id) - len(THREAT) - len(ROUTINE)}")
    return 0


def _fail(message: str) -> int:
    print(f"[error] {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
