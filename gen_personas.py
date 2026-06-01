#!/usr/bin/env python3
"""
Generate personas for Prestige vs Dominance simulation via TinyTroupe client.
Creates 13 flat persona spec JSONs in personas/ (5P + 5D + 8N) and a manifest.json.

Usage:
    python3 gen_personas.py
"""
from __future__ import annotations

import configparser
import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
PERSONAS_DIR = PROJECT_DIR / "personas"
sys.path.insert(0, str(PROJECT_DIR / "src"))

# ── Prestige / Dominance seeds ────────────────────────────────────────────────

PD_SEEDS = [
    {
        "persona_id": "P1",
        "leadership_style": "prestige",
        "name": "Dr. Mei-Ling Chen",
        "age": 45, "gender": "Female", "nationality": "Taiwanese-American",
        "residence": "Seattle, USA",
        "occupation_title": "Director of Research Analytics",
        "occupation_org": "Pacific Analytics Institute",
        "big_five": {"openness": 8, "conscientiousness": 9, "extraversion": 5,
                     "agreeableness": 8, "neuroticism": 2},
        "cultural": {"collectivism": 8, "hierarchy_preference": 5, "shame_sensitivity": 7,
                     "conflict_tolerance": 3, "uncertainty_avoidance": 6},
        "key_behavior": (
            "Earns trust through precise, openly-shared analysis. Patient listener who "
            "synthesizes before speaking. Avoids self-promotion; lets data and outcomes speak."
        ),
    },
    {
        "persona_id": "P2",
        "leadership_style": "prestige",
        "name": "James Thornton",
        "age": 52, "gender": "Male", "nationality": "British",
        "residence": "Edinburgh, UK",
        "occupation_title": "Principal Systems Architect",
        "occupation_org": "Thornton & Partners Consulting",
        "big_five": {"openness": 9, "conscientiousness": 8, "extraversion": 6,
                     "agreeableness": 7, "neuroticism": 2},
        "cultural": {"collectivism": 3, "hierarchy_preference": 2, "shame_sensitivity": 2,
                     "conflict_tolerance": 7, "uncertainty_avoidance": 2},
        "key_behavior": (
            "Shares deep technical expertise openly and generously. Comfortable challenging "
            "or being challenged on substance. Builds credibility through demonstrated accuracy."
        ),
    },
    {
        "persona_id": "P3",
        "leadership_style": "prestige",
        "name": "Fatima Al-Rashid",
        "age": 41, "gender": "Female", "nationality": "Jordanian",
        "residence": "Dubai, UAE",
        "occupation_title": "Senior Strategy Consultant",
        "occupation_org": "Meridian Strategy Group",
        "big_five": {"openness": 8, "conscientiousness": 8, "extraversion": 6,
                     "agreeableness": 8, "neuroticism": 3},
        "cultural": {"collectivism": 7, "hierarchy_preference": 6, "shame_sensitivity": 6,
                     "conflict_tolerance": 4, "uncertainty_avoidance": 5},
        "key_behavior": (
            "Synthesizes competing perspectives into workable frameworks. Builds consensus "
            "by demonstrating she has understood everyone's position before proposing a path."
        ),
    },
    {
        "persona_id": "P4",
        "leadership_style": "prestige",
        "name": "Rafael Carvalho",
        "age": 39, "gender": "Male", "nationality": "Brazilian",
        "residence": "São Paulo, Brazil",
        "occupation_title": "Head of Product Innovation",
        "occupation_org": "Votorantim Digital Ventures",
        "big_five": {"openness": 9, "conscientiousness": 7, "extraversion": 7,
                     "agreeableness": 8, "neuroticism": 3},
        "cultural": {"collectivism": 6, "hierarchy_preference": 4, "shame_sensitivity": 4,
                     "conflict_tolerance": 6, "uncertainty_avoidance": 5},
        "key_behavior": (
            "Earns followership through contagious enthusiasm and inclusive vision. Quick to "
            "credit others, translates abstract strategy into tangible possibilities."
        ),
    },
    {
        "persona_id": "P5",
        "leadership_style": "prestige",
        "name": "Anna Kovačević",
        "age": 47, "gender": "Female", "nationality": "Croatian",
        "residence": "Zagreb, Croatia",
        "occupation_title": "Chief Knowledge Officer",
        "occupation_org": "Adriatic Technology Group",
        "big_five": {"openness": 8, "conscientiousness": 9, "extraversion": 4,
                     "agreeableness": 7, "neuroticism": 2},
        "cultural": {"collectivism": 5, "hierarchy_preference": 4, "shame_sensitivity": 5,
                     "conflict_tolerance": 5, "uncertainty_avoidance": 7},
        "key_behavior": (
            "Speaks rarely but with high precision. Earns trust by having thought through "
            "issues more deeply than others. Methodical and consistent."
        ),
    },
    {
        "persona_id": "D1",
        "leadership_style": "dominance",
        "name": "Robert Hartmann",
        "age": 54, "gender": "Male", "nationality": "German",
        "residence": "Munich, Germany",
        "occupation_title": "Vice President of Operations",
        "occupation_org": "KronbergTech AG",
        "big_five": {"openness": 4, "conscientiousness": 9, "extraversion": 8,
                     "agreeableness": 2, "neuroticism": 1},
        "cultural": {"collectivism": 2, "hierarchy_preference": 9, "shame_sensitivity": 1,
                     "conflict_tolerance": 9, "uncertainty_avoidance": 1},
        "key_behavior": (
            "Commands through structural authority and procedure. Sets the agenda, controls "
            "the pace, dismisses tangents. Uses impersonal procedural language "
            "('the correct process', 'per standard') rather than personal authority claims."
        ),
    },
    {
        "persona_id": "D2",
        "leadership_style": "dominance",
        "name": "Natasha Volkov",
        "age": 48, "gender": "Female", "nationality": "Russian",
        "residence": "London, UK",
        "occupation_title": "Director of Corporate Strategy",
        "occupation_org": "Albion Capital Partners",
        "big_five": {"openness": 6, "conscientiousness": 8, "extraversion": 8,
                     "agreeableness": 2, "neuroticism": 2},
        "cultural": {"collectivism": 3, "hierarchy_preference": 8, "shame_sensitivity": 2,
                     "conflict_tolerance": 8, "uncertainty_avoidance": 2},
        "key_behavior": (
            "Seizes conversational control through confident framing and rapid restatement. "
            "Redefines problems to position herself as indispensable. Intellectual dominance, "
            "not bluster — outpaces challengers before they can respond."
        ),
    },
    {
        "persona_id": "D3",
        "leadership_style": "dominance",
        "name": "Marcus Webb",
        "age": 44, "gender": "Male", "nationality": "American",
        "residence": "Chicago, USA",
        "occupation_title": "Regional General Manager",
        "occupation_org": "Webb Industrial Solutions",
        "big_five": {"openness": 6, "conscientiousness": 7, "extraversion": 9,
                     "agreeableness": 3, "neuroticism": 2},
        "cultural": {"collectivism": 2, "hierarchy_preference": 4, "shame_sensitivity": 1,
                     "conflict_tolerance": 9, "uncertainty_avoidance": 2},
        "key_behavior": (
            "Claims leadership through high-energy assertiveness and bravado. No formal "
            "authority needed — pure social aggression and volume. Challenges weak arguments "
            "loudly. Frames decisions as obvious once he has weighed in."
        ),
    },
    {
        "persona_id": "D4",
        "leadership_style": "dominance",
        "name": "Park Jae-Won",
        "age": 50, "gender": "Male", "nationality": "South Korean",
        "residence": "Seoul, South Korea",
        "occupation_title": "Executive Director of Finance",
        "occupation_org": "Hyeonsung Holdings",
        "big_five": {"openness": 4, "conscientiousness": 9, "extraversion": 7,
                     "agreeableness": 2, "neuroticism": 2},
        "cultural": {"collectivism": 6, "hierarchy_preference": 9, "shame_sensitivity": 7,
                     "conflict_tolerance": 4, "uncertainty_avoidance": 8},
        "key_behavior": (
            "Dominates through positional authority and shame/loss framing. Uses phrases "
            "like 'this reflects poorly on the team', 'if we fail to meet standards'. "
            "Controls through implicit threat of social consequence, not open confrontation."
        ),
    },
    {
        "persona_id": "D5",
        "leadership_style": "dominance",
        "name": "Helena Baxter",
        "age": 46, "gender": "Female", "nationality": "Australian",
        "residence": "Sydney, Australia",
        "occupation_title": "Chief Operations Officer",
        "occupation_org": "Southern Cross Infrastructure Group",
        "big_five": {"openness": 6, "conscientiousness": 8, "extraversion": 8,
                     "agreeableness": 3, "neuroticism": 3},
        "cultural": {"collectivism": 2, "hierarchy_preference": 3, "shame_sensitivity": 1,
                     "conflict_tolerance": 9, "uncertainty_avoidance": 2},
        "key_behavior": (
            "Controls the agenda through speed and blunt directness. No formal authority "
            "needed — uses impatience as a social signal that hesitation implies incompetence."
        ),
    },
]

# ── Neutral seeds (demographics only) ─────────────────────────────────────────

N_SEEDS = [
    {"persona_id": "N1", "hint": "Female, early 30s, Vietnamese or Thai, mid-level data analyst or engineer"},
    {"persona_id": "N2", "hint": "Male, mid 40s, Dutch or Swedish, project manager or operations coordinator"},
    {"persona_id": "N3", "hint": "Female, late 40s, Nigerian or Kenyan, senior individual contributor in a business function"},
    {"persona_id": "N4", "hint": "Male, late 20s, Indian, software developer or backend engineer"},
    {"persona_id": "N5", "hint": "Female, mid 40s, Mexican, HR, communications, or people operations"},
    {"persona_id": "N6", "hint": "Male, early 50s, Chinese, finance, accounting, or compliance"},
    {"persona_id": "N7", "hint": "Female, early 30s, French or Spanish, product manager or UX designer"},
    {"persona_id": "N8", "hint": "Male, mid 40s, American (Midwest), engineering or technical team lead"},
]

# ── System prompts ─────────────────────────────────────────────────────────────

PD_SYSTEM_PROMPT = """\
You generate realistic persona specifications for multi-agent leadership simulations.

Return ONLY a valid JSON object with exactly these keys (no markdown, no extra keys):
{
  "name": "...",
  "age": <integer>,
  "nationality": "...",
  "country_of_residence": "...",
  "gender": "...",
  "residence": "...",
  "occupation": {
    "title": "...",
    "organization": "...",
    "description": "2-3 sentence role description"
  },
  "education": "2 sentence education background",
  "leadership_style": "prestige" | "dominance",
  "cultural_profile": {
    "big_five": {
      "openness":          {"score": <0-10>, "description": "one behavioral sentence"},
      "conscientiousness": {"score": <0-10>, "description": "one behavioral sentence"},
      "extraversion":      {"score": <0-10>, "description": "one behavioral sentence"},
      "agreeableness":     {"score": <0-10>, "description": "one behavioral sentence"},
      "neuroticism":       {"score": <0-10>, "description": "one behavioral sentence"}
    },
    "cultural_modifiers": {
      "collectivism":          {"score": <0-10>, "description": "one behavioral sentence"},
      "hierarchy_preference":  {"score": <0-10>, "description": "one behavioral sentence"},
      "shame_sensitivity":     {"score": <0-10>, "description": "one behavioral sentence"},
      "conflict_tolerance":    {"score": <0-10>, "description": "one behavioral sentence"},
      "uncertainty_avoidance": {"score": <0-10>, "description": "one behavioral sentence"}
    }
  },
  "personality": {
    "traits": ["10-12 specific behavioral trait strings"],
    "big_five": {
      "openness": "one sentence", "conscientiousness": "one sentence",
      "extraversion": "one sentence", "agreeableness": "one sentence",
      "neuroticism": "one sentence"
    }
  },
  "style": {
    "communication": "how they speak in meetings",
    "mannerisms": "2-3 behavioral habits",
    "decision-making": "how they decide and announce"
  },
  "beliefs": ["4-6 core professional beliefs as strings"],
  "skills": ["4-6 relevant skills"],
  "behaviors": {
    "meeting": ["3-4 specific observable meeting behaviors"]
  },
  "preferences": {
    "likes": ["3-4 things"],
    "dislikes": ["3-4 things"]
  },
  "long_term_goals": ["4-6 goals"],
  "speech_examples": [
    "4-5 verbatim sentences this person says in meetings.",
    "Real spoken language only — NOT written reports or LinkedIn prose.",
    "Vary length: some 3-8 words, some 15-25 words.",
    "At least one showing friction, doubt, or direct disagreement.",
    "Reflect leadership style and cultural profile concretely."
  ]
}

RULES:
- No MBTI labels (ENTJ etc.) or cognitive function codes (Te, Fi etc.) anywhere.
- Prestige: earns influence through expertise/knowledge-sharing, not authority or fear.
- Dominance: claims influence through authority, agenda control, making dissent costly.
- Cultural modifiers shape HOW the style expresses (high-hierarchy dominance uses formal
  status; low-hierarchy dominance uses raw assertiveness).
- speech_examples must sound spoken. Bad: "I'll volunteer to steward this."
  Good: "I can take that — two days." or "That's not going to work. We tried it in Q2."
"""

N_SYSTEM_PROMPT = """\
You generate realistic persona specifications for multi-agent workplace simulations.

This persona is NEUTRAL — competent but not leadership-seeking. Neither prestige-type
(expertise-based influence) nor dominance-type (authority-based influence). They
participate naturally in group discussions without driving the agenda.

Return ONLY a valid JSON object with exactly these keys (no markdown, no extra keys):
{
  "name": "...",
  "age": <integer>,
  "nationality": "...",
  "country_of_residence": "...",
  "gender": "...",
  "residence": "...",
  "occupation": {
    "title": "...",
    "organization": "...",
    "description": "2 sentence role description"
  },
  "education": "1-2 sentence education background",
  "leadership_style": "neutral",
  "personality": {
    "traits": ["6-8 specific behavioral traits"],
    "big_five": {
      "openness": "one sentence", "conscientiousness": "one sentence",
      "extraversion": "one sentence", "agreeableness": "one sentence",
      "neuroticism": "one sentence"
    }
  },
  "style": {
    "communication": "how they speak in meetings — ordinary, not commanding",
    "mannerisms": "1-2 habits",
    "decision-making": "how they approach group decisions"
  },
  "beliefs": ["3-4 professional beliefs"],
  "skills": ["3-4 skills"],
  "behaviors": {
    "meeting": ["2-3 observable meeting behaviors"]
  },
  "preferences": {
    "likes": ["2-3 things"],
    "dislikes": ["2-3 things"]
  },
  "long_term_goals": ["3-4 goals"],
  "speech_examples": [
    "4 verbatim sentences this person says in meetings.",
    "Ordinary participation: questions, confirmations, brief opinions.",
    "One mild disagreement or uncertainty is fine.",
    "Sound like a real person talking, not writing."
  ]
}

RULES:
- No MBTI labels or cognitive function codes anywhere.
- Big Five scores should be MODERATE (extraversion 3-6, others avoid extremes).
- Not passive or incompetent — just not spotlight-seeking.
- speech_examples: "Can you say more about that?", "I'm not sure we've ruled out X.",
  "Yeah that tracks for me." — ordinary meeting language.
- Make this a distinct individual with real cultural texture, not a generic 'average'.
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_api_key() -> str:
    cfg = configparser.ConfigParser()
    cfg.read(PROJECT_DIR / "config.ini")
    try:
        return cfg["OpenAI"]["API_KEY"]
    except KeyError:
        raise SystemExit("API_KEY not found in config.ini")


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start: end + 1])
    except json.JSONDecodeError:
        return {}


def _call(messages: list[dict], *, temperature: float) -> dict:
    from tinytroupe.clients import client
    msg = client().send_message(
        messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    if msg is None:
        raise RuntimeError("TinyTroupe client returned None")
    return _extract_json(str(msg.get("content", "")))


def _generate_pd(seed: dict) -> dict:
    user_msg = (
        f"Generate a full persona for:\n"
        f"- Name: {seed['name']}, Age: {seed['age']}, "
        f"Gender: {seed['gender']}, Nationality: {seed['nationality']}\n"
        f"- Residence: {seed['residence']}\n"
        f"- Occupation: {seed['occupation_title']} at {seed['occupation_org']}\n"
        f"- Leadership style: {seed['leadership_style'].upper()}\n"
        f"- Big Five (0-10): {seed['big_five']}\n"
        f"- Cultural modifiers (0-10): {seed['cultural']}\n"
        f"- Key behavioral pattern: {seed['key_behavior']}\n\n"
        f"Use the exact scores. All traits, style, and speech examples must "
        f"reflect BOTH the leadership style AND the cultural scores."
    )
    spec = _call(
        [{"role": "system", "content": PD_SYSTEM_PROMPT},
         {"role": "user", "content": user_msg}],
        temperature=0.8,
    )
    spec["persona_id"] = seed["persona_id"]
    return spec


def _generate_n(seed: dict, existing_names: list[str]) -> dict:
    names_str = ", ".join(existing_names) if existing_names else "none yet"
    user_msg = (
        f"Generate a neutral persona with these demographics:\n"
        f"  {seed['hint']}\n\n"
        f"Names already in this simulation (avoid similarity): {names_str}\n\n"
        f"Choose name, occupation, personality, and cultural texture freely. "
        f"This person is NOT a natural leader — neither prestige nor dominance oriented."
    )
    spec = _call(
        [{"role": "system", "content": N_SYSTEM_PROMPT},
         {"role": "user", "content": user_msg}],
        temperature=1.0,
    )
    spec["persona_id"] = seed["persona_id"]
    return spec


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from runtime import configure_tinytroupe_runtime

    api_key = _load_api_key()
    os.chdir(PROJECT_DIR)

    configure_tinytroupe_runtime(
        api_key=api_key,
        model="gpt-4.1",
        temperature=0.8,
        max_completion_tokens=2000,
    )

    PERSONAS_DIR.mkdir(exist_ok=True)
    all_names: list[str] = []
    generated: dict[str, dict] = {}
    total = len(PD_SEEDS) + len(N_SEEDS)
    idx = 0

    for seed in PD_SEEDS:
        idx += 1
        pid = seed["persona_id"]
        path = PERSONAS_DIR / f"{pid}.agent.json"
        if path.exists():
            print(f"  [{idx}/{total}] {pid} ({seed['name']}) — exists, skipping")
            spec = json.loads(path.read_text(encoding="utf-8"))
        else:
            print(f"  [{idx}/{total}] Generating {pid} ({seed['name']}) ...", flush=True)
            spec = _generate_pd(seed)
            if not spec.get("name"):
                raise SystemExit(f"Empty spec for {pid}")
            path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"         Saved → {path.name}")
        all_names.append(spec.get("name", seed["name"]))
        generated[pid] = {"persona_id": pid, "name": spec.get("name", seed["name"]),
                          "leadership_style": seed["leadership_style"]}

    for seed in N_SEEDS:
        idx += 1
        pid = seed["persona_id"]
        path = PERSONAS_DIR / f"{pid}.agent.json"
        if path.exists():
            print(f"  [{idx}/{total}] {pid} — exists, skipping")
            spec = json.loads(path.read_text(encoding="utf-8"))
        else:
            print(f"  [{idx}/{total}] Generating {pid} ({seed['hint'][:45]}...) ...", flush=True)
            spec = _generate_n(seed, all_names)
            if not spec.get("name"):
                raise SystemExit(f"Empty spec for {pid}")
            path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"         Saved → {path.name}  ({spec.get('name', pid)})")
        all_names.append(spec.get("name", pid))
        generated[pid] = {"persona_id": pid, "name": spec.get("name", pid),
                          "leadership_style": "neutral"}

    prestige_ids = [s["persona_id"] for s in PD_SEEDS if s["leadership_style"] == "prestige"]
    dominance_ids = [s["persona_id"] for s in PD_SEEDS if s["leadership_style"] == "dominance"]
    neutral_ids = [s["persona_id"] for s in N_SEEDS]

    manifest = {
        "study": "Prestige vs Dominance Leadership Emergence",
        "prestige_ids": prestige_ids,
        "dominance_ids": dominance_ids,
        "neutral_ids": neutral_ids,
        "all_ids": prestige_ids + dominance_ids + neutral_ids,
        "personas": generated,
    }
    (PERSONAS_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nDone. {len(generated)} personas ({len(prestige_ids)}P + {len(dominance_ids)}D + {len(neutral_ids)}N).")


if __name__ == "__main__":
    main()
