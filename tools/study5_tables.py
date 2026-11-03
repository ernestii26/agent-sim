"""Print the replication's numbers in the layout of Sheng et al.'s tables, as Markdown.

Arm A as Table 13 (every ILT dimension on all six needs: r, b, SE, beta, delta R2, p,
relative weight), arm B as Table 3 (Model 1 and Model 2 for the hypothesis cells), the
needs' reliabilities and intercorrelations as Table 8, the outcomes' intercorrelations as
Table S11, and the needs' correlations with the personas' OCEAN levels beside Table S9.1.
Reads results/replication only; no model calls.

    python tools/study5_tables.py > /tmp/ours.md
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from instrument import load_instrument  # noqa: E402
from stats import cronbach_alpha, partial_betas, relative_weights  # noqa: E402

DATA = ROOT / "results" / "replication"
NEEDS = ["protection", "affiliation", "status", "vision", "expertise", "fairness"]
OCEAN = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
LEVEL = {"low": 0, "medium": 1, "high": 2}
# Only effectiveness_styles has reverse-keyed items (moral_character_1, _3); FFNI and ILT have none.
STYLES = load_instrument(ROOT / "studies" / "ffni_mediation" / "instruments" / "effectiveness_styles.json")
ARMS = {"a": ("ffni_generic.json", "ilt.json"), "b": ("ffni.json", "effectiveness_styles.json")}
ILT_ORDER = ["sensitivity", "dedication", "tyranny", "charisma", "strength", "creativity",
             "well_groomed", "masculinity", "intelligence", "femininity", "ethics"]  # Table 13's order
STYLE_ORDER = ["authoritarianism", "benevolence", "moral_character", "team_building", "vision_communication",
               "high_expectation", "intellectual_stimulation", "dominance", "competence", "virtue", "safety",
               "narcissism"]  # Table S11.2's order
TABLE3_CELLS = [("protection", "safety"), ("protection", "authoritarianism"),
                ("affiliation", "benevolence"), ("affiliation", "team_building"),
                ("status", "narcissism"), ("status", "authoritarianism"), ("status", "dominance"),
                ("vision", "vision_communication"), ("vision", "high_expectation"),
                ("expertise", "competence"), ("expertise", "intellectual_stimulation"),
                ("fairness", "moral_character"), ("fairness", "virtue")]


def items(answers: dict, ids: list[str], instrument=None) -> dict[str, np.ndarray]:
    """Respondents x items per subscale, reverse-keyed items flipped; item keys are '<subscale>_<n>'."""
    score = instrument.scored if instrument else (lambda k, v: v)
    names = sorted({k.rsplit("_", 1)[0] for k, v in answers[ids[0]].items()
                    if isinstance(v, (int, float)) and not k.startswith("_")})
    out = {}
    for name in names:
        keys = sorted(k for k in answers[ids[0]] if k.rsplit("_", 1)[0] == name)
        out[name] = np.array([[score(k, answers[i][k]) for k in keys] for i in ids], dtype=float)
    return out


def load(arm: str):
    ffni = json.loads((DATA / arm / ARMS[arm][0]).read_text())
    out = json.loads((DATA / arm / ARMS[arm][1]).read_text())
    ids = [i for i in ffni if i in out]
    need_items, out_items = items(ffni, ids), items(out, ids, STYLES if arm == "b" else None)
    needs = np.column_stack([need_items[n].mean(axis=1) for n in NEEDS])
    outcomes = {d: m.mean(axis=1) for d, m in out_items.items()}
    levels = np.array([[LEVEL[json.loads((DATA / arm / "personas" / f"{i}.agent.json").read_text())
                              ["persona"]["personality"]["big_five"][t]] for t in OCEAN] for i in ids])
    return ids, need_items, needs, out_items, outcomes, levels


def ols(x: np.ndarray, y: np.ndarray):
    """Unstandardised b, SE and p with an intercept; the intercept is element 0."""
    a = np.column_stack([np.ones(len(y)), x])
    coef, *_ = np.linalg.lstsq(a, y, rcond=None)
    resid = y - a @ coef
    df = len(y) - a.shape[1]
    se = np.sqrt(resid @ resid / df * np.diag(np.linalg.inv(a.T @ a)))
    p = 2 * stats.t.sf(np.abs(coef / se), df)
    return coef, se, p


def stars(p: float) -> str:
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


def fmt_p(p: float) -> str:
    return "< .001" if p < .001 else f"{p:.3f}".lstrip("0")


def f2(v: float) -> str:
    return f"{v:.2f}".replace("0.", ".", 1) if abs(v) < 1 else f"{v:.2f}"


def table13() -> None:
    _, _, needs, _, outcomes, _ = load("a")
    for dim in ILT_ORDER:
        y = outcomes[dim]
        betas, deltas, r2, _ = partial_betas(needs.tolist(), y.tolist())
        weights, _, _ = relative_weights(needs.tolist(), y.tolist())
        b, se, p = ols(needs, y)
        print(f"\n**{dim}** (R² = {f2(r2)}, M = {y.mean():.2f}, SD = {y.std(ddof=1):.2f}; "
              f"intercept b = {b[0]:.2f}{stars(p[0])}, SE = {se[0]:.2f})\n")
        b, se, p = b[1:], se[1:], p[1:]
        print("| Need | r | b | SE | β | ΔR² | p | RW | RW% |")
        print("|---|---|---|---|---|---|---|---|---|")
        for j, need in enumerate(NEEDS):
            r = np.corrcoef(needs[:, j], y)[0, 1]
            pr = stats.pearsonr(needs[:, j], y).pvalue
            print(f"| {need} | {f2(r)}{stars(pr)} | {f2(b[j])}{stars(p[j])} | {f2(se[j])} | {f2(betas[j])} "
                  f"| {f2(deltas[j])}{stars(p[j])} | {fmt_p(p[j])} | {f2(weights[j])} | {100 * weights[j] / r2:.1f} |")


def table3() -> None:
    _, _, needs, _, outcomes, _ = load("b")
    print("| Need → effectiveness of | Model 1 β | Model 1 p | Model 2 β | Model 2 p | R² (Model 2) |")
    print("|---|---|---|---|---|---|")
    for need, dim in TABLE3_CELLS:
        y, j = outcomes[dim], NEEDS.index(need)
        r, p1 = stats.pearsonr(needs[:, j], y)
        betas, _, r2, _ = partial_betas(needs.tolist(), y.tolist())
        p2 = ols(needs, y)[2][1:]
        print(f"| {need} → {dim} | {f2(r)}{stars(p1)} | {fmt_p(p1)} | {f2(betas[j])}{stars(p2[j])} "
              f"| {fmt_p(p2[j])} | {f2(r2)} |")


def table8() -> None:
    for arm, label in (("a", "Arm A (generic, N = 261)"), ("b", "Arm B (work, N = 367)")):
        _, need_items, needs, _, _, _ = load(arm)
        corr = np.corrcoef(needs.T)
        print(f"\n**{label}**: α, M, SD, and Pearson r (lower triangle)\n")
        print("| Need | α | M | SD | 1 | 2 | 3 | 4 | 5 | 6 |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for i, need in enumerate(NEEDS):
            alpha = cronbach_alpha(need_items[need].tolist())
            cells = [f2(corr[i, j]) if j < i else ("—" if j == i else "") for j in range(6)]
            print(f"| {i + 1}. {need} | {f2(alpha)} | {needs[:, i].mean():.2f} | {needs[:, i].std(ddof=1):.2f} | "
                  + " | ".join(cells) + " |")


def table_s11() -> None:
    for arm, label in (("a", "Arm A: ILT dimensions"), ("b", "Arm B: effectiveness styles")):
        _, _, _, out_items, outcomes, _ = load(arm)
        names = ILT_ORDER if arm == "a" else STYLE_ORDER
        corr = np.corrcoef(np.array([outcomes[n] for n in names]))
        print(f"\n**{label}**: α, M, SD, and Pearson r (lower triangle)\n")
        print("| Dimension | α | M | SD | " + " | ".join(str(i + 1) for i in range(len(names))) + " |")
        print("|---|---|---|---|" + "---|" * len(names))
        for i, n in enumerate(names):
            alpha = cronbach_alpha(out_items[n].tolist())
            cells = [f2(corr[i, j]) if j < i else ("—" if j == i else "") for j in range(len(names))]
            print(f"| {i + 1}. {n} | {f2(alpha)} | {outcomes[n].mean():.2f} | {outcomes[n].std(ddof=1):.2f} | "
                  + " | ".join(cells) + " |")


def table_s9() -> None:
    for arm in ("a", "b"):
        _, _, needs, _, _, levels = load(arm)
        print(f"\n**Arm {arm.upper()}**: r between the persona's OCEAN level (0/1/2) and each need\n")
        print("| OCEAN level | " + " | ".join(NEEDS) + " |")
        print("|---|" + "---|" * 6)
        for t, trait in enumerate(OCEAN):
            print(f"| {trait} | " + " | ".join(f2(np.corrcoef(levels[:, t], needs[:, j])[0, 1]) for j in range(6)) + " |")


if __name__ == "__main__":
    for title, fn in (("Table 13 (arm A)", table13), ("Table 3 (arm B)", table3), ("Table 8", table8),
                      ("Table S11", table_s11), ("Table S9.1", table_s9)):
        print(f"\n<!-- {title} -->")
        fn()
