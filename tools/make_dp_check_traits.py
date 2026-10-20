"""Build studies/dp_check_traits: dp_check's routine condition with P and D reduced to traits.

In dp_check, P_i and D_i keep their bank row's OCEAN levels and description, and half
the D personas carry a description that asks for a warm, conflict-avoiding manner
against their dominance traits. This variant drops `big_five` and `description` from
every P and D, keeping `traits`, so the traits are the whole personality. Neutrals are
copied unchanged. Same groups, ids and sampler seed as dp_check, so run i gets the same
cast and task as dp_check's run i and the two can be compared run by run.

    python tools/make_dp_check_traits.py
    python3 run.py run dp_check_traits collaborative --runs 10
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "studies" / "dp_check"
TARGET = ROOT / "studies" / "dp_check_traits"
PERSONAS = ROOT / "studies" / "ffni_mediation" / "personas"


def main() -> None:
    spec = json.loads((SOURCE / "study.json").read_text())
    spec["name"] = "dp_check_traits"
    spec["title"] = "P/D manipulation check, traits only (no OCEAN, no description for P and D)"
    spec["description"] = (
        "Diagnostic variant of dp_check, routine condition only. P and D keep their traits "
        "and lose the bank row's big_five and description; neutrals are unchanged. Built by "
        "tools/make_dp_check_traits.py. Same sampler seed as dp_check, so run i is dp_check's "
        "run i with only P's and D's persona text changed.")
    spec.pop("personas_from", None)
    spec["conditions"] = {"collaborative": spec["conditions"]["collaborative"]}

    (TARGET / "personas").mkdir(parents=True, exist_ok=True)
    for name in ("instruments", "scenarios"):
        link = TARGET / name
        if not link.exists():
            link.symlink_to(Path("..") / "dp_check" / name)
    (TARGET / "study.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")

    changed = 0
    for path in PERSONAS.glob("*.agent.json"):
        agent = json.loads(path.read_text())
        if agent.get("persona_id", path.name)[0] in "PD":
            personality = agent["persona"]["personality"]
            personality.pop("big_five", None)
            personality.pop("description", None)
            assert personality.get("traits"), path.name
            changed += 1
        (TARGET / "personas" / path.name).write_text(json.dumps(agent, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {TARGET}: {changed} P/D personas reduced to traits")


if __name__ == "__main__":
    main()
