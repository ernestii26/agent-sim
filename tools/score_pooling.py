#!/usr/bin/env python3
"""Score how much of the split information actually reached the group.

Run over saved checkpoints, so it costs nothing during a study and can be redone when
the judging prompt changes. For each private fact a participant was given, one call
asks whether that fact was communicated to the others -- in substance, not in wording.

Wording is the whole reason this is not a regex. Agents paraphrase: a run where one
agent said "we also need to consider the dam release" and another said "it's just washed
out" contains at least two of its four private facts and scores zero on verbatim
matching. Judging in substance is the only version of this number worth reporting.

    tools/score_pooling.py ffni_mediation [--model gpt-4o-mini] [--dry-run]

Writes {"raised": {fact: bool}} into each checkpoint's task block.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import RunConfig  # noqa: E402

PROMPT = """You are checking whether one piece of information reached a group.

Below is a transcript of a team meeting. Before it started, one participant was told
this fact privately. Nobody else was told it.

FACT: {fact}

TRANSCRIPT:
{transcript}

Did anyone communicate the substance of that fact to the group? Judge in substance:

- Paraphrase counts. Wording, length and detail do not have to match, and the speaker
  need not be the person who was told it.
- Naming the topic without the claim does not count. "Someone should check the roof"
  does not convey "the roof collapsed last night".
- A partial statement of the claim DOES count. "The roof is down" conveys it.

Answer with one word, YES or NO."""


def judge(client, model: str, fact: str, transcript: str) -> bool:
    reply = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=5,
        messages=[{"role": "user", "content": PROMPT.format(fact=fact, transcript=transcript)}],
    )
    return (reply.choices[0].message.content or "").strip().upper().startswith("Y")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study")
    # gpt-4.1, not a cheap model. On the first two runs the two judges agreed on the
    # total but not on which fact: gpt-4o-mini called "it's just washed out" a miss and
    # counted a bare mention of "the dam release" as a hit, which is both rules backwards.
    # 4 facts x 80 runs is ~320 short calls, so the cheap judge saves almost nothing.
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--results", help="results root (default: OUTPUT_DIR from config.ini)")
    parser.add_argument("--rescore", action="store_true", help="redo already-scored runs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    config = RunConfig.from_ini(root / "config.ini")
    results = Path(args.results) if args.results else root / config.output_dir
    paths = sorted((results / args.study).glob("*/checkpoints/run_*.json"))
    if not paths:
        print(f"no checkpoints under {results}/{args.study}", file=sys.stderr)
        return 1

    client = None
    if not args.dry_run:
        from openai import OpenAI
        client = OpenAI(api_key=config.api_key)

    calls = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data.get("task") or {}
        facts = [f for held in (task.get("shares") or {}).values() for f in held]
        if not facts:
            continue
        if task.get("raised") and not args.rescore:
            print(f"{path.parent.parent.name}/{path.name}: already scored, skipping")
            continue

        transcript = "\n".join(
            f"{t['name']}: {t['text']}" for t in data["transcript"] if t.get("spoke")
        )
        if args.dry_run:
            print(f"{path.parent.parent.name}/{path.name}: would judge {len(facts)} facts")
            calls += len(facts)
            continue

        raised = {fact: judge(client, args.model, fact, transcript) for fact in facts}
        calls += len(facts)
        task["raised"] = raised
        data["task"] = task
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        hit = sum(raised.values())
        print(f"{path.parent.parent.name}/{path.name}: {hit}/{len(facts)} facts reached the group")

    print(f"\n{calls} judgements{' (dry run, nothing called or written)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
