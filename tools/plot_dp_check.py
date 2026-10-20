"""Plot the dp_check manipulation check beside Ronay et al. (2023).

Four figures in docs/figs/:
  dp_check_effect_sizes.png  d per scale: Ronay Studies 2 and 3 against our two conditions,
                             with 95% CIs (Ronay: normal approximation from their N; ours:
                             bootstrap over the 10 runs, so wide and only indicative).
  dp_check_runs.png          every run's P and D score, joined per run, with Ronay's
                             condition means for scale.
  dp_check_traits_runs.png   routine only: the full persona against dp_check_traits (P and
                             D reduced to traits), run by run, same tasks and neutrals.
  dp_check_agreeableness.png D's dominance rating by the agreeableness of the bank row its
                             description came from, full persona against traits only.

Ronay's prestige d as printed (0.69, 0.96) cannot be rebuilt from their own M and SD,
which give 0.78 and 1.18; both are drawn.

    python tools/plot_dp_check.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from analysis import subscale_scores  # noqa: E402
from config import RunConfig  # noqa: E402
from instrument import POST  # noqa: E402
from pipeline import load_records  # noqa: E402
from stats import mean  # noqa: E402
from study import load_study  # noqa: E402

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"   # dataviz reference palette, slots 1-3 (validated;
# aqua is under 3:1 on white, so it always carries a direct label or a distinct marker)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SCALES = {"dominance": ("D", "P"), "prestige": ("P", "D")}   # (expected higher, lower)
CONDITIONS = {"collaborative": "Routine", "threat": "Threat"}

# Ronay et al. (2023): Table 4 (Study 2, n = 204 D / 196 P) and Table 6 (Study 3, 258 / 236).
# Each scale: (mean of D, SD, mean of P, SD, d as printed).
RONAY = {
    "Ronay S2": {"n": (204, 196), "dominance": (4.66, .93, 3.48, .95, 1.26),
                 "prestige": (4.05, 1.44, 5.04, 1.09, .69)},
    "Ronay S3": {"n": (258, 236), "dominance": (5.59, .98, 3.42, 1.10, 2.08),
                 "prestige": (4.24, 1.00, 5.28, .76, .96)},
}


def run_units(name: str = "dp_check") -> dict[str, list[dict]]:
    """Per condition, one {group: {scale: mean over that target's neutral raters}} per run,
    plus the D persona's id under "Did"."""
    config = RunConfig.from_ini(ROOT / "config.ini")
    study = load_study(name)
    rating = study.candidate_rating
    out = {}
    for key in study.conditions:
        units = []
        for record in load_records(Path(config.output_dir) / study.name / key):
            by_target: dict[str, dict[str, list[float]]] = {}
            for by_rated in record.responses(POST, rating).values():
                for target, answers in by_rated.items():
                    for name, value in subscale_scores(answers, rating).items():
                        by_target.setdefault(target, {}).setdefault(name, []).append(value)
            unit = {g: {n: mean(v) for n, v in by_target[pid].items()}
                    for g in ("P", "D") for pid in record.members(g) if pid in by_target}
            unit["Did"] = record.members("D")[0]
            units.append(unit)
        out[key] = units
    return out


def d_av(a: np.ndarray, b: np.ndarray) -> float:
    return (a.mean() - b.mean()) / ((a.std(ddof=1) + b.std(ddof=1)) / 2)


def bootstrap_ci(a: np.ndarray, b: np.ndarray, reps: int = 10000) -> tuple[float, float]:
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(a), (reps, len(a)))
    draws = [d_av(a[i], b[i]) for i in idx if a[i].std() + b[i].std() > 0]
    return tuple(np.percentile(draws, [2.5, 97.5]))


def ronay_d(n: tuple[int, int], cell: tuple) -> tuple[float, float, float, float]:
    """(printed d, d rebuilt from M/SD, CI low, CI high), d in the expected direction."""
    md, sd_d, mp, sd_p, printed = cell
    (n1, n2), diff = n, abs(md - mp)
    d = diff / np.sqrt(((n1 - 1) * sd_d ** 2 + (n2 - 1) * sd_p ** 2) / (n1 + n2 - 2))
    se = np.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    return printed, d, d - 1.96 * se, d + 1.96 * se


def style(ax) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_effect_sizes(units: dict, path: Path) -> None:
    rows = list(RONAY) + [f"Ours, {CONDITIONS[k].lower()}" for k in CONDITIONS]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
    for ax, (scale, (hi, lo)) in zip(axes, SCALES.items()):
        for y, name in enumerate(rows):
            if name in RONAY:
                printed, rebuilt, lo_ci, hi_ci = ronay_d(RONAY[name]["n"], RONAY[name][scale])
                ax.plot([lo_ci, hi_ci], [y, y], color=BLUE, lw=2, solid_capstyle="round")
                ax.plot(printed, y, "o", color=BLUE, ms=8, mec="white", mew=1.5)
                label = f"{printed:.2f}"
                if abs(rebuilt - printed) > .05:
                    ax.plot(rebuilt, y, "o", mfc="white", mec=BLUE, ms=8, mew=1.5)
                    label += f"  (M/SD give {rebuilt:.2f})"
                ax.annotate(label, (hi_ci, y), xytext=(6, 0), textcoords="offset points",
                            va="center", fontsize=8, color=MUTED)
            else:
                key = [k for k in CONDITIONS if CONDITIONS[k].lower() in name][0]
                a = np.array([u[hi][scale] for u in units[key]])
                b = np.array([u[lo][scale] for u in units[key]])
                d = d_av(a, b)
                lo_ci, hi_ci = bootstrap_ci(a, b)
                ax.plot([lo_ci, hi_ci], [y, y], color=ORANGE, lw=2, solid_capstyle="round")
                ax.plot(d, y, "o", color=ORANGE, ms=8, mec="white", mew=1.5)
                ax.annotate(f"{d:.2f}", (hi_ci, y), xytext=(6, 0), textcoords="offset points",
                            va="center", fontsize=8, color=MUTED)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_xlim(-1.5, 4.2)
        ax.set_title(f"{scale.capitalize()} scale: {hi} − {lo}", fontsize=10, color=INK, loc="left")
        ax.set_xlabel("Effect size d (95% CI)", fontsize=9, color=MUTED)
        style(ax)
    axes[0].set_yticks(range(len(rows)), rows)
    axes[0].invert_yaxis()
    fig.legend(handles=[
        plt.Line2D([], [], marker="o", color=BLUE, ls="", label="Ronay et al. (2023), as printed"),
        plt.Line2D([], [], marker="o", mfc="white", mec=BLUE, ls="", label="Ronay, rebuilt from M and SD"),
        plt.Line2D([], [], marker="o", color=ORANGE, ls="", label="This check, gpt-4.1, 10 runs"),
    ], loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.15)


def plot_runs(panels: list[tuple[str, list[dict], str]], path: Path) -> None:
    """One panel per (title, units, scale): each run's P and D, joined per run."""
    fig, axes = plt.subplots(1, len(panels), figsize=(10, 3.4), sharey=True)
    for ax, (title, units, scale) in zip(axes, panels):
        p = [u["P"][scale] for u in units]
        d = [u["D"][scale] for u in units]
        for pi, di in zip(p, d):
            ax.plot([0, 1], [pi, di], color=GRID, lw=1.2, zorder=1)
        ax.scatter([0] * len(p), p, color=BLUE, s=36, edgecolor="white", lw=1, zorder=2)
        ax.scatter([1] * len(d), d, color=ORANGE, s=36, edgecolor="white", lw=1, zorder=2)
        for name, marker in (("Ronay S2", "D"), ("Ronay S3", "s")):
            md, _, mp, _, _ = RONAY[name][scale]
            ax.scatter([-0.25, 1.25], [mp, md], marker=marker, facecolor="white",
                       edgecolor=MUTED, s=30, zorder=2)
        ax.set_xticks([0, 1], ["P", "D"])
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(1, 7)
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        style(ax)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Peer rating, 1-7", fontsize=9, color=MUTED)
    fig.legend(handles=[
        plt.Line2D([], [], color=GRID, lw=1.2, label="one run (same neutrals rate P and D)"),
        plt.Line2D([], [], marker="D", mfc="white", mec=MUTED, ls="", label="Ronay S2 mean"),
        plt.Line2D([], [], marker="s", mfc="white", mec=MUTED, ls="", label="Ronay S3 mean"),
    ], loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.15)


def plot_agreeableness(full: list[dict], traits: list[dict], path: Path) -> None:
    """D's dominance rating, routine, grouped by the agreeableness of D's bank row."""
    levels = ["low", "medium", "high"]
    level = {u["Did"]: json.loads((ROOT / "studies" / "ffni_mediation" / "personas" / f"{u['Did']}.agent.json")
                                  .read_text())["persona"]["personality"]["big_five"]["agreeableness"]
             for u in full}
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for units, color, marker, dx, label in ((full, ORANGE, "o", -0.12, "Full persona (OCEAN + description)"),
                                            (traits, AQUA, "s", 0.12, "Traits only")):
        for i, lv in enumerate(levels):
            ys = [u["D"]["dominance"] for u in units if level[u["Did"]] == lv]
            xs = i + dx + np.linspace(-.05, .05, len(ys)) if len(ys) > 1 else [i + dx]   # spread ties
            ax.scatter(xs, ys, color=color, marker=marker, s=40, edgecolor="white", lw=1, zorder=2)
            ax.plot([i + dx - .08, i + dx + .08], [np.mean(ys)] * 2, color=INK, lw=2, zorder=3)
            ax.annotate(f"{np.mean(ys):.2f}", (i + dx + .1, np.mean(ys)), va="center", fontsize=8, color=MUTED)
    counts = {lv: sum(level[u["Did"]] == lv for u in full) for lv in levels}
    ax.set_xticks(range(3), [f"{lv.capitalize()}\n(n = {counts[lv]} D)" for lv in levels])
    ax.set_xlabel("Agreeableness of the bank row D was built from (traits-only D no longer carries it)",
                  fontsize=8, color=MUTED)
    ax.set_ylim(1, 7)
    ax.set_ylabel("D's dominance rating, 1-7", fontsize=9, color=MUTED)
    style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.legend(handles=[
        plt.Line2D([], [], marker="o", color=ORANGE, ls="", label="Full persona (OCEAN + description)"),
        plt.Line2D([], [], marker="s", color=AQUA, ls="", label="Traits only"),
        plt.Line2D([], [], color=INK, lw=2, label="group mean"),
    ], loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.45))
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.15)


if __name__ == "__main__":
    units = run_units()
    traits = run_units("dp_check_traits")["collaborative"]
    figs = ROOT / "docs" / "figs"
    plot_effect_sizes(units, figs / "dp_check_effect_sizes.png")
    plot_runs([(f"{CONDITIONS[k]}: {s}", units[k], s) for k in CONDITIONS for s in SCALES],
              figs / "dp_check_runs.png")
    plot_runs([("Full persona: dominance", units["collaborative"], "dominance"),
               ("Traits only: dominance", traits, "dominance"),
               ("Full persona: prestige", units["collaborative"], "prestige"),
               ("Traits only: prestige", traits, "prestige")],
              figs / "dp_check_traits_runs.png")
    plot_agreeableness(units["collaborative"], traits, figs / "dp_check_agreeableness.png")
    print(f"wrote 4 figures to {figs}")
