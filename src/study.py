"""Study definition — everything theme-specific lives in studies/<name>/study.json.

No module in src/ may hardcode a group name, persona id, or scenario. Swapping the
research theme means writing a new studies/<name>/ directory, not editing code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from instrument import (
    ABOUT_EACH_CANDIDATE, ABOUT_KINDS, ABOUT_PROTOTYPE, ABOUT_SELF, Instrument, load_instrument,
)

STUDIES_DIR = Path(__file__).resolve().parent.parent / "studies"


@dataclass(frozen=True)
class Group:
    key: str
    label: str
    ids: tuple[str, ...]
    sample: int | None  # None = every member participates in every run
    # Draw the same positions as another sampled group, so ids line up by index.
    # For bank-paired personas (P_i and D_i built from one row) this keeps the
    # matched pair together in the same run instead of drawing them independently.
    pair_with: str | None = None


@dataclass(frozen=True)
class Task:
    """One hidden-profile task: the group can only answer it by pooling what it knows.

    `shared` reaches everyone, `hidden` is split across the room, and `correct` is
    reachable from the union but from no single share — which is what makes the answer
    a measure of the discussion rather than of any one agent.
    """
    id: int
    name: str
    description: str
    shared: tuple[str, ...]
    hidden: tuple[str, ...]
    options: tuple[str, ...]
    correct: str

    def briefing(self) -> str:
        facts = "\n".join(f"- {fact}" for fact in self.shared)
        return f"{self.description}\n\nWhat everyone here already knows:\n{facts}"

    def shares(self, participant_ids: list[str]) -> dict[str, list[str]]:
        """Deal the hidden facts round-robin over `participant_ids` in the order given.

        The caller shuffles, so which agent holds which fact — and who holds none when
        the facts run out — is independent of whether they are the Prestige or the
        Dominance persona. Deal them by role and the endorsement result would just be
        measuring who was handed the answer.
        """
        shares: dict[str, list[str]] = {pid: [] for pid in participant_ids}
        for index, fact in enumerate(self.hidden):
            shares[participant_ids[index % len(participant_ids)]].append(fact)
        return shares


@dataclass(frozen=True)
class Condition:
    key: str
    label: str
    hypothesis: str
    scenario: str
    friction: str
    contrast: tuple[str, str]
    # Drawn per run instead of `scenario`, so the condition effect is an average over
    # tasks rather than a property of one vignette we wrote.
    pool: tuple[Task, ...] = ()


@dataclass(frozen=True)
class Study:
    name: str
    title: str
    description: str
    directory: Path
    groups: dict[str, Group]
    conditions: dict[str, Condition]
    vote_prompt: str
    # Seeds the cast samplers, so run i draws the same positions in every condition.
    sampler_seed: int = 0
    instruments: tuple["Instrument", ...] = ()
    personas_from: str | None = None  # borrow another study's personas instead of copying them

    @property
    def personas_dir(self) -> Path:
        if self.personas_from:
            return STUDIES_DIR / self.personas_from / "personas"
        return self.directory / "personas"

    def instruments_at(self, timing: str) -> tuple["Instrument", ...]:
        return tuple(i for i in self.instruments if timing in i.timing)

    def _about(self, kind: str) -> "Instrument | None":
        # load_study guarantees at most one per kind, so "the" is well defined here.
        return next((i for i in self.instruments if i.about == kind), None)

    @property
    def self_report(self) -> "Instrument | None":
        return self._about(ABOUT_SELF)

    @property
    def prototype(self) -> "Instrument | None":
        return self._about(ABOUT_PROTOTYPE)

    @property
    def candidate_rating(self) -> "Instrument | None":
        return self._about(ABOUT_EACH_CANDIDATE)

    @property
    def seeds_path(self) -> Path:
        return self.directory / "seeds.json"

    def group_of(self, persona_id: str) -> str:
        for group in self.groups.values():
            if persona_id in group.ids:
                return group.key
        return "?"

    def label_of(self, group_key: str) -> str:
        group = self.groups.get(group_key)
        return group.label if group else group_key

    def condition(self, key: str) -> Condition:
        try:
            return self.conditions[key]
        except KeyError:
            raise SystemExit(
                f"Unknown condition '{key}' for study '{self.name}'. "
                f"Available: {', '.join(self.conditions)}"
            ) from None


def list_studies() -> list[str]:
    if not STUDIES_DIR.exists():
        return []
    return sorted(d.name for d in STUDIES_DIR.iterdir() if (d / "study.json").exists())


def _load_pools(directory: Path, filename: str | None) -> dict[str, tuple[Task, ...]]:
    """Read the scenario pools a study draws its tasks from, if it declares any."""
    if not filename:
        return {}
    path = directory / "scenarios" / filename
    if not path.exists():
        raise SystemExit(f"{path}: scenario file not found")
    spec = json.loads(path.read_text(encoding="utf-8"))
    pools: dict[str, tuple[Task, ...]] = {}
    for key, raw_tasks in spec.get("pools", {}).items():
        if not raw_tasks:
            raise SystemExit(f"{path}: pool '{key}' is empty")
        tasks = []
        for raw in raw_tasks:
            if raw["correct"] not in raw["options"]:
                raise SystemExit(
                    f"{path}: task '{raw['name']}' has a correct answer that is not an option"
                )
            if not raw["hidden"]:
                raise SystemExit(f"{path}: task '{raw['name']}' has no hidden information")
            tasks.append(
                Task(
                    id=raw["id"],
                    name=raw["name"],
                    description=raw["description"],
                    shared=tuple(raw["shared"]),
                    hidden=tuple(raw["hidden"]),
                    options=tuple(raw["options"]),
                    correct=raw["correct"],
                )
            )
        pools[key] = tuple(tasks)
    return pools


def load_study(name: str) -> Study:
    directory = STUDIES_DIR / name
    path = directory / "study.json"
    if not path.exists():
        raise SystemExit(
            f"Study '{name}' not found at {path}. Available: {', '.join(list_studies()) or 'none'}"
        )
    spec = json.loads(path.read_text(encoding="utf-8"))

    groups: dict[str, Group] = {}
    for key, raw in spec["groups"].items():
        ids = tuple(raw["ids"])
        sample = raw.get("sample")
        if not ids:
            raise SystemExit(f"{path}: group '{key}' has no ids")
        if sample is not None and not 1 <= sample <= len(ids):
            raise SystemExit(f"{path}: group '{key}' samples {sample} of {len(ids)} ids")
        groups[key] = Group(
            key=key,
            label=raw.get("label", key),
            ids=ids,
            sample=sample,
            pair_with=raw.get("pair_with"),
        )

    for group in groups.values():
        if group.pair_with is None:
            continue
        source = groups.get(group.pair_with)
        if source is None:
            raise SystemExit(f"{path}: group '{group.key}' pairs with unknown group '{group.pair_with}'")
        if source.pair_with is not None:
            raise SystemExit(f"{path}: group '{group.key}' pairs with '{source.key}', which is itself paired")
        if len(source.ids) != len(group.ids) or source.sample != group.sample:
            raise SystemExit(
                f"{path}: paired groups '{group.key}' and '{source.key}' must have the same "
                f"number of ids and the same sample size"
            )

    seen: set[str] = set()
    for group in groups.values():
        clash = seen & set(group.ids)
        if clash:
            raise SystemExit(f"{path}: persona id(s) {sorted(clash)} appear in more than one group")
        seen |= set(group.ids)

    default_contrast = tuple(spec["contrast"])
    pools = _load_pools(directory, spec.get("scenarios"))

    conditions: dict[str, Condition] = {}
    for key, raw in spec["conditions"].items():
        contrast = tuple(raw.get("contrast", default_contrast))
        for group_key in contrast:
            if group_key not in groups:
                raise SystemExit(f"{path}: condition '{key}' contrasts unknown group '{group_key}'")
        pool_key = raw.get("pool")
        if pool_key is not None and pool_key not in pools:
            raise SystemExit(
                f"{path}: condition '{key}' draws from unknown pool '{pool_key}' "
                f"(have: {sorted(pools) or 'none — no \"scenarios\" file declared'})"
            )
        if pool_key is None and "scenario" not in raw:
            raise SystemExit(f"{path}: condition '{key}' has neither 'scenario' nor 'pool'")
        conditions[key] = Condition(
            key=key,
            label=raw.get("label", key),
            hypothesis=raw.get("hypothesis", ""),
            scenario=raw.get("scenario", ""),
            friction=raw.get("friction", ""),
            contrast=contrast,  # type: ignore[arg-type]
            pool=pools.get(pool_key, ()) if pool_key else (),
        )
    if not conditions:
        raise SystemExit(f"{path}: no conditions defined")

    instruments = []
    for key in spec.get("instruments", []):
        inst = load_instrument(directory / "instruments" / f"{key}.json")
        unknown_targets = set(inst.targets) - set(groups)
        if unknown_targets:
            raise SystemExit(
                f"{path}: instrument '{key}' targets unknown group(s) {sorted(unknown_targets)}"
            )
        instruments.append(inst)

    # One instrument per `about` kind: Study.self_report and friends would otherwise
    # have to guess which of two self-reports the analysis meant.
    for kind in ABOUT_KINDS:
        clash = [i.key for i in instruments if i.about == kind]
        if len(clash) > 1:
            raise SystemExit(
                f"{path}: study '{name}' declares {len(clash)} instruments with "
                f"about='{kind}' ({', '.join(clash)}); at most one is allowed"
            )

    personas_from = spec.get("personas_from")
    if personas_from and not (STUDIES_DIR / personas_from / "personas").exists():
        raise SystemExit(f"{path}: personas_from '{personas_from}' has no personas/ directory")

    return Study(
        name=spec.get("name", name),
        title=spec.get("title", name),
        description=spec.get("description", ""),
        directory=directory,
        groups=groups,
        conditions=conditions,
        vote_prompt=spec.get(
            "vote_prompt", "Based on what you observed, who should lead this team?"
        ),
        sampler_seed=spec.get("sampler_seed", 0),
        instruments=tuple(instruments),
        personas_from=personas_from,
    )
