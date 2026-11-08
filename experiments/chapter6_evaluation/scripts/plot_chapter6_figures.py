#!/usr/bin/env python3
"""Generate the complete Chapter 6 manuscript figure set with Python."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["legend.frameon"] = False
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"


PROJECT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT / "processed"
FIGURES = PROJECT / "figures"
CHAPTER3 = PROJECT.parent / "chapter3_rules"
MM = 1 / 25.4

COLORS = {
    "B0": "#A7A7A7",
    "B1": "#6F6F6F",
    "B2": "#2A8C82",
    "B3": "#2767A8",
    "B4": "#B7473E",
    "B5": "#252525",
    "accent": "#D39B2A",
    "light": "#D9D9D9",
}
PATH_COLORS = {"direct": "#2767A8", "adapt": "#D39B2A", "fallback": "#7A7A7A"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def panel(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.04, label, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")


def finish(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.svg")
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.tiff", dpi=600)
    fig.savefig(FIGURES / f"{name}.png", dpi=300)
    plt.close(fig)


def figure_61() -> None:
    coverage = json.loads((CHAPTER3 / "verification" / "extraction_coverage.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(183 * MM, 78 * MM), constrained_layout=True)
    counts = [coverage["fact_count"], coverage["evidence_levels"]["E1"], coverage["evidence_levels"]["E2"], coverage["evidence_levels"]["E3"], coverage["open_ambiguities"]]
    labels = ["Facts", "E1", "E2", "E3", "Open\nambiguities"]
    bars = axes[0].bar(labels, counts, color=[COLORS["B3"], COLORS["B2"], COLORS["accent"], "#C7A4C8", COLORS["B4"]], width=0.68)
    axes[0].bar_label(bars, fontsize=7, padding=2)
    axes[0].set_ylabel("Count")
    axes[0].set_title("Extracted evidence")
    panel(axes[0], "a")
    ratios = [coverage["field_coverage_ratio"], coverage["source_traceability_ratio"], coverage["machine_check_pass_ratio"], coverage["human_signoff_ratio"]]
    labels = ["Field\ncoverage", "Source\ntraceability", "Machine\nchecks", "Human\nsignoff"]
    bars = axes[1].bar(labels, ratios, color=[COLORS["B3"], COLORS["B2"], COLORS["accent"], COLORS["B4"]], width=0.68)
    axes[1].set_ylim(0, 1.08)
    axes[1].set_ylabel("Proportion")
    axes[1].bar_label(bars, labels=[f"{value:.0%}" for value in ratios], fontsize=7, padding=2)
    axes[1].set_title("Coverage and review state")
    panel(axes[1], "b")
    finish(fig, "fig6-1_fact_quality")


def figure_62() -> None:
    rows = read_csv(PROCESSED / "checker_confusion.csv")
    classes = ["direct", "adapt", "fallback"]
    matrix = np.zeros((3, 3), dtype=int)
    for row in rows:
        if row["predicted"] in classes and row["observed"] in classes:
            matrix[classes.index(row["predicted"]), classes.index(row["observed"])] = int(row["count"])
    fig, ax = plt.subplots(figsize=(112 * MM, 82 * MM), constrained_layout=True)
    image = ax.imshow(matrix, cmap=mcolors.LinearSegmentedColormap.from_list("agreement", ["#F3F3F3", COLORS["B3"]]))
    for i in range(3):
        for j in range(3):
            color = "white" if matrix[i, j] > matrix.max() * 0.55 else "#222222"
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color=color, fontsize=9, fontweight="bold")
    ax.set_xticks(range(3), classes)
    ax.set_yticks(range(3), classes)
    ax.set_xlabel("Observed path")
    ax.set_ylabel("Predicted path")
    ax.set_title("Compatibility Checker agreement")
    fig.colorbar(image, ax=ax, label="Candidate/workload cases", fraction=0.045)
    finish(fig, "fig6-2_checker_confusion")


def figure_63() -> None:
    rows = read_csv(PROCESSED / "space_summary.csv")
    stages = ["Raw", "Executable\n(B1)", "Contract\n(B2)", "Core\n(B3)", "Core+shell\n(B4)", "Tuning\npool"]
    values = [
        sum(int(row["raw_count"]) for row in rows),
        sum(int(row["B1_full_size"]) for row in rows),
        sum(int(row["B2_full_size"]) for row in rows),
        sum(int(row["B3_full_size"]) for row in rows),
        sum(int(row["B4_full_size"]) for row in rows),
        sum(int(row["B4_pool_size"]) for row in rows),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(183 * MM, 84 * MM), constrained_layout=True)
    bars = axes[0].bar(range(len(stages)), values, color=[COLORS["light"], COLORS["B1"], COLORS["B2"], COLORS["B3"], COLORS["B4"], COLORS["accent"]])
    axes[0].set_yscale("log")
    axes[0].set_xticks(range(len(stages)), stages, rotation=20, ha="right")
    axes[0].set_ylabel("Candidates across 36 shapes (log scale)")
    axes[0].bar_label(bars, labels=[f"{value:,}" for value in values], fontsize=6, padding=2)
    axes[0].set_title("Filtering funnel")
    panel(axes[0], "a")
    families = sorted({row["family"] for row in rows})
    x = np.arange(len(families))
    for method, color in (("B2", COLORS["B2"]), ("B3", COLORS["B3"]), ("B4", COLORS["B4"])):
        medians = []
        for family in families:
            family_rows = [row for row in rows if row["family"] == family]
            medians.append(np.median([int(row[f"{method}_full_size"]) / int(row["raw_count"]) for row in family_rows]))
        axes[1].plot(x, medians, marker="o", lw=1.5, color=color, label=method)
    axes[1].set_xticks(x, [name.replace("_", "\n") for name in families])
    axes[1].set_ylabel("Median retained fraction")
    axes[1].set_title("Retention by shape family")
    axes[1].legend(ncols=3, loc="upper right")
    panel(axes[1], "b")
    finish(fig, "fig6-3_space_funnel")


def figure_64() -> None:
    rows = read_csv(PROCESSED / "candidate_space_quality.csv")
    fig, ax = plt.subplots(figsize=(118 * MM, 82 * MM), constrained_layout=True)
    for method in ("B1", "B2", "B3", "B4"):
        values = np.sort([float(row["normalized_to_blis"]) for row in rows if row["method"] == method])
        y = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, y, lw=1.7, color=COLORS[method], label=method)
    for threshold in (0.8, 0.9, 0.95):
        ax.axvline(threshold, color="#B0B0B0", lw=0.7, ls="--")
    ax.set_xlabel("Candidate performance / B5 performance")
    ax.set_ylabel("Empirical CDF")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.01)
    ax.legend(ncols=2)
    ax.set_title("Measured candidate-space quality")
    finish(fig, "fig6-4_performance_cdf")


def figure_65() -> None:
    rows = [row for row in read_csv(PROCESSED / "convergence_normalized.csv") if row["suite"] == "base"]
    fig, axes = plt.subplots(1, 2, figsize=(183 * MM, 84 * MM), constrained_layout=True)
    for method in ("B1", "B2", "B3", "B4"):
        method_rows = [row for row in rows if row["label"] == method]
        by_iteration = defaultdict(list)
        wall_by_iteration = defaultdict(list)
        for row in method_rows:
            iteration = int(row["iteration"])
            by_iteration[iteration].append(float(row["normalized_best_to_blis"]))
            wall_by_iteration[iteration].append(float(row["equivalent_wall_s"]))
        xs = sorted(by_iteration)
        median = np.array([np.median(by_iteration[x]) for x in xs])
        low = np.array([np.quantile(by_iteration[x], 0.25) for x in xs])
        high = np.array([np.quantile(by_iteration[x], 0.75) for x in xs])
        wall = np.array([np.median(wall_by_iteration[x]) for x in xs])
        axes[0].plot(xs, median, color=COLORS[method], lw=1.7, label=method)
        axes[0].fill_between(xs, low, high, color=COLORS[method], alpha=0.12, linewidth=0)
        axes[1].plot(wall, median, color=COLORS[method], lw=1.7, label=method)
        axes[1].fill_between(wall, low, high, color=COLORS[method], alpha=0.12, linewidth=0)
    axes[0].set_xlabel("Evaluations")
    axes[0].set_ylabel("Best-so-far / B5 performance")
    axes[0].set_title("Candidate budget")
    axes[0].legend(ncols=2)
    panel(axes[0], "a")
    axes[1].set_xlabel("Evaluator-equivalent time (s)")
    axes[1].set_ylabel("Best-so-far / B5 performance")
    axes[1].set_title("Compile-and-measure cost axis")
    panel(axes[1], "b")
    finish(fig, "fig6-5_convergence")


def figure_66() -> None:
    summary = [row for row in read_csv(PROCESSED / "fixed_budget_summary.csv") if row["suite"] == "base"]
    runs = [row for row in read_csv(PROCESSED / "fixed_budget_results.csv") if row["suite"] == "base"]
    methods = ["B1", "B2", "B3", "B4"]
    values = [float(next(row for row in summary if row["label"] == method)["normalized_gmean"]) for method in methods]
    low = [float(next(row for row in summary if row["label"] == method)["bootstrap_low"]) for method in methods]
    high = [float(next(row for row in summary if row["label"] == method)["bootstrap_high"]) for method in methods]
    fig, ax = plt.subplots(figsize=(116 * MM, 82 * MM), constrained_layout=True)
    x = np.arange(4)
    for index, method in enumerate(methods):
        points = [float(row["normalized_best_to_blis"]) for row in runs if row["label"] == method]
        jitter = np.linspace(-0.12, 0.12, len(points))
        ax.scatter(np.full(len(points), index) + jitter, points, s=5, color=COLORS[method], alpha=0.25, linewidth=0)
    ax.bar(x, values, color=[COLORS[m] for m in methods], width=0.62, alpha=0.88)
    ax.errorbar(x, values, yerr=[np.array(values) - np.array(low), np.array(high) - np.array(values)], fmt="none", ecolor="#222222", capsize=3, lw=0.9)
    ax.set_xticks(x, methods)
    ax.set_ylabel("Best-at-25 / B5 performance")
    ax.set_title("Equal-budget tuning outcome")
    finish(fig, "fig6-6_fixed_budget")


def figure_67() -> None:
    rows = [row for row in read_csv(PROCESSED / "fixed_budget_summary.csv") if row["suite"] == "ablation"]
    preferred = ["full", "no_mr_nr", "no_cache_prior", "no_packing_rule", "no_checker", "no_soft_prior", "no_shell", "misleading_prior"]
    lookup = {row["label"]: row for row in rows}
    labels = [label for label in preferred if label in lookup]
    values = [float(lookup[label]["normalized_gmean"]) for label in labels]
    low = [float(lookup[label]["bootstrap_low"]) for label in labels]
    high = [float(lookup[label]["bootstrap_high"]) for label in labels]
    fig, ax = plt.subplots(figsize=(178 * MM, 82 * MM), constrained_layout=True)
    y = np.arange(len(labels))[::-1]
    for yi, value, lo, hi, label in zip(y, values, low, high, labels):
        color = COLORS["B4"] if label == "full" else COLORS["B2"] if value >= values[0] else COLORS["B1"]
        ax.plot([lo, hi], [yi, yi], color=color, lw=1.6)
        ax.plot(value, yi, "o", color=color, ms=5)
    ax.axvline(values[0], color=COLORS["B4"], ls="--", lw=0.8)
    ax.set_yticks(y, [label.replace("_", " ") for label in labels])
    ax.set_xlabel("Best-at-25 / B5 performance")
    ax.set_title("Operational component ablations")
    finish(fig, "fig6-7_ablation")


def figure_68() -> None:
    rows = [row for row in read_csv(PROCESSED / "fixed_budget_summary.csv") if row["suite"] == "shell"]
    rows.sort(key=lambda row: float(row["label"]))
    ratio = np.array([float(row["label"]) * 100 for row in rows])
    perf = np.array([float(row["normalized_gmean"]) for row in rows])
    time_to = np.array([float(row["median_time_to_90pct_iteration"]) for row in rows])
    fig, ax = plt.subplots(figsize=(116 * MM, 82 * MM), constrained_layout=True)
    line1 = ax.plot(ratio, perf, marker="o", color=COLORS["B4"], lw=1.7, label="Performance")[0]
    ax.set_xlabel("Exploration-shell share (%)")
    ax.set_ylabel("Best-at-25 / B5 performance", color=COLORS["B4"])
    ax.tick_params(axis="y", labelcolor=COLORS["B4"])
    second = ax.twinx()
    second.spines["right"].set_visible(True)
    line2 = second.plot(ratio, time_to, marker="s", color=COLORS["B3"], lw=1.4, label="Time-to-90%")[0]
    second.set_ylabel("Median evaluations to 90% pool best", color=COLORS["B3"])
    second.tick_params(axis="y", labelcolor=COLORS["B3"])
    ax.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")
    ax.set_title("Exploration-shell sensitivity")
    finish(fig, "fig6-8_shell_sensitivity")


def figure_69() -> None:
    rows = read_csv(PROCESSED / "holdout_zero_shot.csv")
    methods = ["B1", "B2", "B3", "B4"]
    workloads = sorted({row["workload_id"] for row in rows})
    matrix = np.array([[float(next(row for row in rows if row["method"] == method and row["workload_id"] == workload)["normalized_to_blis"]) for workload in workloads] for method in methods])
    fig, ax = plt.subplots(figsize=(183 * MM, 94 * MM), constrained_layout=True)
    image = ax.imshow(matrix, cmap=mcolors.LinearSegmentedColormap.from_list("holdout", ["#F2F2F2", "#8BC8BF", COLORS["B3"]]), aspect="auto")
    ax.set_xticks(range(len(workloads)), [name.replace("_", "\n") for name in workloads], rotation=45, ha="right", fontsize=6)
    ax.set_yticks(range(4), methods)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=5.5, color="white" if matrix[i, j] > matrix.max() * 0.58 else "#222222")
    ax.set_title("Zero-shot holdout performance relative to B5")
    fig.colorbar(image, ax=ax, label="Performance / B5", fraction=0.025, pad=0.02)
    finish(fig, "fig6-9_holdout")


def figure_610() -> None:
    rows = read_csv(PROCESSED / "overhead_profile.csv")
    rows = [row for row in rows if row["mean_ms"] != "pending_profile"]
    labels = [row["stage"].replace("_", "\n") for row in rows]
    values = [float(row["mean_ms"]) for row in rows]
    fig, ax = plt.subplots(figsize=(118 * MM, 82 * MM), constrained_layout=True)
    bars = ax.bar(range(len(rows)), values, color=[COLORS["B2"], COLORS["B3"], COLORS["accent"], COLORS["B4"], COLORS["B1"], "#8F72A7"][:len(rows)])
    ax.set_yscale("log")
    ax.set_xticks(range(len(rows)), labels, rotation=24, ha="right")
    ax.set_ylabel("Measured time (ms, log scale)")
    ax.bar_label(bars, labels=[f"{value:.1f}" for value in values], fontsize=5.5, padding=2)
    ax.set_title("System-stage overhead (units declared in source table)")
    finish(fig, "fig6-10_overhead")


def figure_611() -> None:
    quality = read_csv(PROCESSED / "candidate_space_quality.csv")
    aggregates = read_csv(PROCESSED / "measurement_aggregates.csv")
    baselines = read_csv(PROCESSED / "baseline_comparison.csv")
    index = {(row["workload_id"], row["candidate_id"]): row for row in quality}
    points = []
    for row in aggregates:
        if not row["variant"].startswith("candidate:"):
            continue
        key = (row["workload_id"], row["candidate_id"])
        if key not in index:
            continue
        points.append((float(row["compile_pipeline_ms"]), float(index[key]["normalized_to_blis"]), row["observed_path"], row["candidate_id"]))
    fig, axes = plt.subplots(1, 2, figsize=(183 * MM, 84 * MM), constrained_layout=True)
    baseline_values = [
        [float(row["scalar_relative_to_blis"]) for row in baselines],
        [float(row["optimized_relative_to_blis"]) for row in baselines],
    ]
    positions = np.arange(2)
    box = axes[0].boxplot(
        baseline_values, positions=positions, widths=0.48, patch_artist=True,
        showfliers=False, medianprops={"color": "#222222", "linewidth": 1.0},
    )
    for patch, color in zip(box["boxes"], (COLORS["B1"], COLORS["B3"])):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)
    for index_value, (values, color) in enumerate(zip(baseline_values, (COLORS["B1"], COLORS["B3"]))):
        jitter = np.linspace(-0.14, 0.14, len(values))
        axes[0].scatter(
            np.full(len(values), index_value) + jitter, values, s=7,
            color=color, alpha=0.42, linewidth=0,
        )
        geometric_mean = math.exp(np.mean(np.log(values)))
        axes[0].plot(index_value, geometric_mean, marker="D", ms=5, color=color)
    axes[0].axhline(1.0, color="#9A9A9A", lw=0.8, ls="--")
    axes[0].set_yscale("log")
    axes[0].set_xticks(positions, ["Scalar dynamic", "Vectorized dynamic"])
    axes[0].set_ylabel("Performance / complete BLIS")
    axes[0].set_title("Dynamic MLIR references (36 shapes)")
    panel(axes[0], "a")

    ax = axes[1]
    for path in ("fallback", "adapt", "direct"):
        selected = [row for row in points if row[2] == path]
        ax.scatter([row[0] for row in selected], [row[1] for row in selected], s=9, alpha=0.38, color=PATH_COLORS[path], label=path, linewidth=0)
    ax.set_xscale("log")
    ax.set_xlabel("Candidate construction time (ms, log scale)")
    ax.set_ylabel("Candidate performance / B5")
    ax.set_title("Representative success and fallback cost")
    ax.legend(ncols=3)
    if points:
        fastest = max(points, key=lambda row: row[1])
        slowest = min(points, key=lambda row: row[1])
        for point, label in ((fastest, "best observed"), (slowest, "slowest correct")):
            ax.annotate(label, (point[0], point[1]), xytext=(5, 5), textcoords="offset points", fontsize=6)
    panel(ax, "b")
    finish(fig, "fig6-11_cases")


def main() -> None:
    figure_61()
    figure_62()
    figure_63()
    figure_64()
    figure_65()
    figure_66()
    figure_67()
    figure_68()
    figure_69()
    figure_610()
    figure_611()
    print(json.dumps({"status": "PASS", "figures": 11, "formats": ["svg", "pdf", "tiff", "png"]}, indent=2))


if __name__ == "__main__":
    main()
