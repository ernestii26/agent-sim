#!/usr/bin/env python3
"""Sample a persona bank into a study's seeds.json, assigning leadership styles.

    python3 tools/sample_bank.py <study> --split P=6,D=6,N=24

Reads a bank of raw persona profiles (personas_output.json: an OCEAN profile with a
prose description, plus occupation and demographics) and turns a sample of them into
seeds for tools/gen_personas.py, which does the actual generation.

Two things this deliberately does NOT do:

* It does not write persona specs. Generation costs API calls, so it stays a separate
  step you trigger. gen_personas.py skips personas that already exist, so the bank on
  disk grows incrementally and nothing is ever regenerated.
* It does not put the leadership style in a field and call it done. The bank's prose
  describes OCEAN only — it never mentions how a person acquires influence. A label the
  text does not carry changes nothing about how the agent behaves, so the assigned style
  is written into the generation prompt and has to come back woven through traits,
  mannerisms and speech.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))

# The bank records OCEAN as low/medium/high; the generation prompt wants 0-10 scores.
LEVEL_SCORES = {"low": 2, "medium": 5, "high": 8}
OCEAN_ORDER = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")

STYLE_PROMPT = {"P": "leader", "D": "leader", "N": "neutral"}
STYLE_NAME = {"P": "prestige", "D": "dominance", "N": "neutral"}


def parse_split(text: str) -> dict[str, int]:
    """"P=6,D=6,N=24" -> {"P": 6, "D": 6, "N": 24}"""
    split: dict[str, int] = {}
    for part in text.split(","):
        key, _, count = part.partition("=")
        key, count = key.strip(), count.strip()
        if not key or not count.isdigit() or int(count) < 1:
            raise SystemExit(f"--split: bad entry {part!r}, expected like 'P=6'")
        split[key] = int(count)
    return split


def stratified_sample(bank: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Take n entries spread across distinct OCEAN profiles.

    The bank is a full factorial (3^5 profiles x occupations), so drawing uniformly at
    random would happily return two entries with identical personalities. Picking one
    entry per profile keeps the personality range as wide as the sample size allows.
    """
    by_profile: dict[tuple, list[dict]] = {}
    for entry in bank:
        key = tuple(entry["ocean_description"]["ocean"][trait] for trait in OCEAN_ORDER)
        by_profile.setdefault(key, []).append(entry)

    profiles = list(by_profile)
    rng.shuffle(profiles)
    if n > len(profiles):
        raise SystemExit(
            f"--split totals {n}, above the {len(profiles)} distinct OCEAN profiles in the bank; "
            "sampling more would repeat personalities"
        )
    return [rng.choice(by_profile[p]) for p in profiles[:n]]


def build_user_prompt(entry: dict, group: str) -> str:
    ocean = entry["ocean_description"]["ocean"]
    scores = {trait: LEVEL_SCORES[ocean[trait]] for trait in OCEAN_ORDER}
    demo = entry["demographic"]
    style = STYLE_NAME[group]
    description = entry["ocean_description"]["description_en"]

    lines = [
        "Generate a full persona for a person with this profile:",
        f"- Occupation: {entry['occupation']}",
        f"- Age group: {demo['age_group']}   Parent: {'yes' if demo['is_parent'] else 'no'}",
        f"- Big Five (0-10): {scores}",
        "",
        "Established behavioural profile — the persona must stay consistent with it:",
        description,
        "",
    ]
    if group == "N":
        lines += [
            "This person is NOT a natural leader — neither prestige nor dominance oriented.",
            "Choose a name and cultural texture freely.",
            "Names already in this simulation (avoid similarity): {existing_names}",
        ]
    else:
        lines += [
            f"- Leadership style: {style.upper()}",
            "",
            f"Choose a name, nationality and cultural modifiers freely, but keep them "
            f"plausible for the occupation and age above.",
            f"The {style} style must show up concretely in traits, mannerisms, "
            f"decision-making and speech_examples — not as a label. Where the style and "
            f"the behavioural profile pull in different directions, the profile wins: a "
            f"low-extraversion {style} leader is quiet and still {style}, not loud.",
            "Names already in this simulation (avoid similarity): {existing_names}",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("study")
    parser.add_argument("--bank", default="personas_output.json")
    parser.add_argument("--split", default="P=6,D=6,N=24",
                        help="personas per group key (default: P=6,D=6,N=24)")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed, so a sample is reproducible")
    parser.add_argument("--prompts-from", default="prestige_dominance",
                        help="study whose seeds.json supplies the system prompts")
    parser.add_argument("--direct", action="store_true",
                        help="write persona specs straight from the bank (no API calls) "
                             "instead of seeds for tools/gen_personas.py")
    args = parser.parse_args()

    split = parse_split(args.split)
    total = sum(split.values())
    rng = random.Random(args.seed)

    bank_path = _PROJECT_DIR / args.bank
    if not bank_path.exists():
        raise SystemExit(f"Bank not found: {bank_path}")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    usable = [e for e in bank if e.get("ocean_description", {}).get("is_valid")]
    print(f"Bank: {len(bank)} entries, {len(usable)} valid")

    sample = stratified_sample(usable, total, rng)
    rng.shuffle(sample)  # style assignment is random, independent of personality

    prompts = {} if args.direct else json.loads(
        (_PROJECT_DIR / "studies" / args.prompts_from / "seeds.json").read_text(encoding="utf-8")
    )["prompts"]

    if args.direct and total > len(NAME_POOL):
        raise SystemExit(f"--direct needs {total} distinct names but NAME_POOL has {len(NAME_POOL)}")
    names = list(NAME_POOL)
    rng.shuffle(names)

    personas, specs, cursor = [], [], 0
    group_ids: dict[str, list[str]] = {}
    for group, count in split.items():
        ids = []
        for i in range(1, count + 1):
            entry = sample[cursor]
            cursor += 1
            pid = f"{group}{i}"
            ids.append(pid)
            if args.direct:
                specs.append((pid, to_tinyperson_spec(entry, group, pid, names[cursor - 1])))
            personas.append({
                "persona_id": pid,
                "group": group,
                "label": f"{entry['occupation']}, {entry['demographic']['age_group']}",
                "prompt": STYLE_PROMPT[group],
                "temperature": 0.8 if group != "N" else 1.0,
                "user": build_user_prompt(entry, group),
                "source": {
                    "occupation": entry["occupation"],
                    "ocean": entry["ocean_description"]["ocean"],
                    "demographic": entry["demographic"],
                },
            })
        group_ids[group] = ids

    out_dir = _PROJECT_DIR / "studies" / args.study
    out_dir.mkdir(parents=True, exist_ok=True)

    provenance = {"bank": args.bank, "seed": args.seed, "direct": args.direct,
                  "personas": [{k: v for k, v in p.items() if k != "user"} for p in personas]}
    if args.direct:
        personas_dir = out_dir / "personas"
        personas_dir.mkdir(exist_ok=True)
        for pid, spec in specs:
            (personas_dir / f"{pid}.agent.json").write_text(
                json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "bank_sample.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        (out_dir / "seeds.json").write_text(
            json.dumps({"prompts": prompts, "bank": args.bank, "seed": args.seed,
                        "personas": personas}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"\nSampled {total} personas across {len(split)} groups (seed {args.seed}):")
    for group, ids in group_ids.items():
        print(f"  {group}: {len(ids)}  {ids[0]}..{ids[-1]}")
    written = f"{len(specs)} persona specs in {out_dir / 'personas'}" if args.direct \
        else str(out_dir / "seeds.json")
    print(f"\nWrote {written}")
    print("\nGroup ids for study.json:")
    print(json.dumps({g: ids for g, ids in group_ids.items()}, indent=2))
    if args.direct:
        print("\nNo API calls needed — the personas are ready to run.")
    else:
        print(f"\nNext: python3 tools/gen_personas.py {args.study}   (this step costs API calls)")



# --------------------------------------------------------------------------- #
# Direct conversion — bank entry to TinyPerson spec, no API call               #
# --------------------------------------------------------------------------- #

# The bank's prose covers personality only. These blocks are the leadership-style
# manipulation, and they are deliberately IDENTICAL for every persona of a style:
# the manipulation is then a constant while personality varies, instead of six
# idiosyncratic LLM inventions that differ in ways nobody measured.
#
# Style is assigned at random, so it lands on personalities it appears to contradict —
# a low-extraversion, agreeable person drawing Dominance. Without a reconciliation the
# agent gets two texts that argue with each other. `register` resolves it in one
# direction: the style says WHAT they do about influence, the personality says HOW it
# comes out. A quiet dominant person is still dominant, just not loud.
STYLE_BLOCKS = {
    "P": {
        "summary": (
            "Earns influence by being worth listening to. Shares what they know freely, "
            "shows the reasoning behind a claim, and gives way to better evidence without "
            "treating it as a loss."
        ),
        "register": (
            "This describes how they seek influence, not their temperament. Where it seems "
            "to conflict with their disposition, the disposition sets the register and the "
            "influence style still holds: a reserved version of this person earns standing "
            "in few words and in writing rather than by holding the floor."
        ),
        "traits": [
            "explains the reasoning behind a claim instead of asserting it",
            "shares what they know without being asked, including things that weaken their case",
            "changes position openly when someone presents better evidence",
            "credits the person whose idea it was, by name",
            "asks a clarifying question before disagreeing",
            "does not invoke seniority or position to settle a disagreement",
        ],
        "speech": [
            "Here's why I think that — tell me where it breaks.",
            "You're right, I had that backwards.",
            "That was Dana's point, not mine.",
            "I've seen this fail before. Want the details?",
        ],
    },
    "D": {
        "summary": (
            "Claims influence by taking control of the room. Sets the agenda, closes "
            "questions down, and makes disagreeing feel costly rather than welcome."
        ),
        "register": (
            "This describes how they seek influence, not their temperament. Where it seems "
            "to conflict with their disposition, the disposition sets the register and the "
            "influence style still holds: a quiet version of this person dominates by flat "
            "refusal, cold silence and ending discussions early — not by volume."
        ),
        "traits": [
            "states conclusions as settled rather than opening them for discussion",
            "interrupts to redirect the conversation back to their own framing",
            "uses impatience as a signal that hesitation looks like incompetence",
            "assigns work to others without asking whether it fits",
            "treats a challenge as something to be shut down, not examined",
            "invokes position or precedent when pressed for justification",
        ],
        "speech": [
            "We're doing it this way. Next.",
            "That's not the question. The question is who owns it.",
            "We've spent long enough on this.",
            "I've made the call. Someone write it up.",
        ],
    },
    "N": {
        "summary": (
            "Participates without trying to run the room. Contributes when they have "
            "something to add and is content to let others set direction."
        ),
        "register": "Their temperament shows through as-is; they are not seeking influence.",
        "traits": [
            "asks for clarification rather than assuming",
            "gives an opinion when asked, briefly",
            "goes along with a decision they did not personally push for",
        ],
        "speech": [
            "Can you say more about that?",
            "Yeah, that tracks for me.",
            "I'm not sure we've ruled out the other option.",
        ],
    },
}

# Names only need to be distinct and pronounceable — the bank supplies no identity, and
# agents address and vote for each other by name.
NAME_POOL = [
    "Alma Reyes", "Ben Osei", "Cara Lindqvist", "Dev Raman", "Elena Petrova", "Farid Haddad",
    "Grace Mbeki", "Hugo Marchand", "Ines Duarte", "Jonas Weber", "Kiran Shah", "Lena Novak",
    "Marco Bianchi", "Nadia Aziz", "Oscar Lindgren", "Pia Kowalski", "Quinn Doherty",
    "Rosa Iglesias", "Samir Chaudhry", "Tomas Varga", "Uma Krishnan", "Viktor Sokolov",
    "Wendy Chao", "Xavier Dubois", "Yara Halabi", "Zoe Andersen", "Adam Kovac", "Bianca Rossi",
    "Caleb Nwosu", "Dalia Moreno", "Erik Solberg", "Fatima Sow", "Gabriel Costa", "Hana Sato",
    "Ivan Petrenko", "Julia Berg", "Kofi Mensah", "Liwei Zhang", "Mira Halonen", "Noah Feldman",
    "Olga Ivanova", "Pedro Alves", "Rania Khoury", "Stefan Novotny", "Tara Lindholm",
    "Umar Farooq", "Vera Jankovic", "Will Harding", "Xiomara Vega", "Yusuf Demir",
]

AGE_MIDPOINT = {"25-35": 30, "36-50": 43, "51-65": 58}


def to_tinyperson_spec(entry: dict, group: str, persona_id: str, name: str) -> dict:
    """Build a persona spec from a bank entry — same shape as the hand-written ones.

    src/ only reads persona.name; every other field is what TinyTroupe turns into the
    agent's system prompt, so this mirrors the schema of the existing personas rather
    than inventing a leaner one.
    """
    ocean = entry["ocean_description"]["ocean"]
    demo = entry["demographic"]
    block = STYLE_BLOCKS[group]

    return {
        "type": "TinyPerson",
        "persona": {
            "name": name,
            "age": AGE_MIDPOINT.get(demo["age_group"], 40),
            # tiny_person.py's minibio() does self._persona["nationality"] with no
            # fallback, called on nearly every turn — an absent key is a hard crash
            # that AgentTransport's catch-all then reports as silence. The bank
            # carries no nationality data, so this stays a neutral placeholder
            # rather than fabricating one from the name.
            "nationality": "not specified",
            "occupation": {"title": entry["occupation"]},
            # No `leadership_style` key. tiny_person.py json.dumps()es the whole persona
            # into the system prompt, under a template that says the persona overrides
            # the model's own tendencies — so a "dominance" label there tells the agent
            # which construct it is supposed to embody. Nothing in the codebase read it
            # (group membership comes from study.json), so it was pure leakage.
            "personality": {
                "description": entry["ocean_description"]["description_en"],
                "big_five": {t: ocean[t] for t in OCEAN_ORDER},
                "traits": list(block["traits"]),
            },
            # `register` is dropped for the same reason: it was meta-language about the
            # specification itself ("This describes how they seek influence, not their
            # temperament"), which both cues the manipulation and contradicts TinyTroupe's
            # own instruction never to reveal that a persona spec is being followed.
            # The cost is real — register was what told a low-extraversion dominant how to
            # dominate quietly — so watch the speech-rate warning on the matched pair whose
            # profile is low on extraversion.
            "style": {"influence": block["summary"]},
            "relationships": [] if not demo["is_parent"] else [
                {"name": "family", "description": "Has children; family commitments sit "
                                                  "outside work and occasionally cut into it."}
            ],
            "speech_examples": list(block["speech"]),
        },
        "persona_id": persona_id,
    }


if __name__ == "__main__":
    main()
