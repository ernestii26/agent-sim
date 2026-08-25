"""Survey instruments — a rating scale administered to agents during a run.

Like study.py, this module knows nothing about any particular scale. The items, the
anchors, who answers, and when all come from studies/<name>/instruments/<key>.json.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Who the rating is about. Drives prompt shape only; parsing is identical for all three.
ABOUT_SELF = "self"                      # self-report (FFNI: "I need a leader who...")
ABOUT_PROTOTYPE = "prototype"            # the generic leader concept, no target (ILT)
ABOUT_EACH_CANDIDATE = "each_candidate"  # one administration per other participant
ABOUT_KINDS = (ABOUT_SELF, ABOUT_PROTOTYPE, ABOUT_EACH_CANDIDATE)

BASELINE = "baseline"  # before the scenario is broadcast
POST = "post"          # after the discussion
TIMINGS = (BASELINE, POST)


@dataclass(frozen=True)
class Instrument:
    key: str
    title: str
    instructions: str
    scale: tuple[int, int]
    anchors: tuple[str, str]
    subscales: dict[str, tuple[str, ...]]  # dimension -> item texts
    about: str
    targets: tuple[str, ...]               # group keys that answer it
    timing: tuple[str, ...]
    citation: str
    license: str
    note: str
    # Which of THIS instrument's subscales each subscale of another instrument is
    # predicted to move. Only the prototype layer uses it: the source paper's needs map
    # many-to-many onto ILT dimensions (status reaches tyranny, masculinity AND
    # well-groomed), so a name-matching convention cannot express the hypothesis.
    predicts: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def items(self) -> list[tuple[str, str, str]]:
        """Flat (item_id, subscale, text), stable order. item_id is the JSON key agents answer with."""
        return [
            (f"{subscale}_{i}", subscale, text)
            for subscale, texts in self.subscales.items()
            for i, text in enumerate(texts, start=1)
        ]

    def is_valid_rating(self, value: object) -> bool:
        low, high = self.scale
        return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def load_instrument(path: Path) -> Instrument:
    if not path.exists():
        raise SystemExit(f"Instrument not found: {path}")
    spec = json.loads(path.read_text(encoding="utf-8"))

    subscales = {name: tuple(items) for name, items in spec["subscales"].items()}
    if not subscales:
        raise SystemExit(f"{path}: no subscales defined")
    for name, items in subscales.items():
        if not items:
            raise SystemExit(f"{path}: subscale '{name}' has no items")

    low, high = (int(x) for x in spec["scale"])
    if low >= high:
        raise SystemExit(f"{path}: scale low ({low}) must be below high ({high})")

    about = spec.get("about", ABOUT_SELF)
    if about not in ABOUT_KINDS:
        raise SystemExit(f"{path}: about must be one of {ABOUT_KINDS}, got '{about}'")

    timing = tuple(spec.get("timing", [POST]))
    unknown = set(timing) - set(TIMINGS)
    if unknown or not timing:
        raise SystemExit(f"{path}: timing must be a non-empty subset of {TIMINGS}, got {timing}")

    anchors = tuple(spec.get("anchors", ["", ""]))
    if len(anchors) != 2:
        raise SystemExit(f"{path}: anchors must be a pair [low_label, high_label]")

    predicts = {k: tuple(v) for k, v in spec.get("predicts", {}).items()}
    for source, targets in predicts.items():
        unknown_subscales = set(targets) - set(subscales)
        if unknown_subscales:
            raise SystemExit(
                f"{path}: predicts['{source}'] names subscale(s) "
                f"{sorted(unknown_subscales)} that this instrument does not have"
            )

    return Instrument(
        key=spec.get("key", path.stem),
        title=spec.get("title", path.stem),
        instructions=spec["instructions"],
        scale=(low, high),
        anchors=anchors,  # type: ignore[arg-type]
        subscales=subscales,
        about=about,
        targets=tuple(spec.get("targets", ())),
        timing=timing,
        citation=spec.get("citation", ""),
        license=spec.get("license", ""),
        note=spec.get("note", ""),
        predicts=predicts,
    )


def subscale_scores(responses: dict[str, float | None], instrument: Instrument) -> dict[str, float]:
    """Mean of each subscale's items. A subscale with no usable answer scores NaN.

    Never imputes: a missing or out-of-range rating is dropped, not replaced with a
    midpoint, so a parse failure shows up as missing data rather than fake moderation.
    """
    usable: dict[str, list[float]] = {name: [] for name in instrument.subscales}
    for item_id, subscale, _ in instrument.items:
        value = responses.get(item_id)
        if instrument.is_valid_rating(value):
            usable[subscale].append(float(value))  # type: ignore[arg-type]
    return {
        name: (sum(vals) / len(vals) if vals else float("nan"))
        for name, vals in usable.items()
    }
