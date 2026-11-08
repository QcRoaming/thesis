#!/usr/bin/env python3
"""Generate the quantitative figures used by thesis Chapter 5.

The script reads only frozen experiment artifacts.  It does not compile
candidates, invoke BaCO, or perform hardware measurement.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


FIGURE_DIR = Path(__file__).resolve().parent
THESIS_DIR = FIGURE_DIR.parents[2]
EXPERIMENTS = THESIS_DIR / "experiments"

CONTRACT_VALIDATION = EXPERIMENTS / "chapter6_contract_space_validation" / "processed"
FORMAL_EVALUATION = EXPERIMENTS / "chapter6_evaluation" / "processed"
SAME_POOL = EXPERIMENTS / "chapter6_same_pool_prior" / "processed"
TERMINATION = EXPERIMENTS / "chapter6_termination_validation" / "processed"
EXTERNAL = EXPERIMENTS / "chapter6_external_validation" / "processed"
APPLICATION = EXPERIMENTS / "chapter6_application_validation" / "processed"
X86_CROSS_HOST = EXPERIMENTS / "x86_cross_host" / "processed"

MM = 1.0 / 25.4
COLORS = {
    "G0": "#A6A6A6",
    "G1": "#4C78A8",
    "C": "#008C95",
    "B1": "#4C78A8",
    "B2": "#008C95",
    "B3": "#7A6FA8",
    "B4": "#F28E2B",
    "library": "#1A1A1A",
    "reject": "#C44E52",
    "fallback": "#B7B7B7",
    "positive": "#2A9D8F",
}
HATCHES = {"G0": "//", "G1": "\\\\", "C": "xx", "B1": "//", "B2": "xx", "B3": "..", "B4": "++"}


def configure_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update(
        {
            "font.family": "AR PL SungtiL GB",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
            "mathtext.default": "regular",
        }
    )


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        0.0,
        1.03,
        label,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def finish(fig: plt.Figure, stem: str) -> list[str]:
    outputs: list[str] = []
    for suffix, kwargs in (
        ("svg", {}),
        ("pdf", {}),
        ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}}),
        ("png", {"dpi": 300}),
    ):
        path = FIGURE_DIR / f"{stem}.{suffix}"
        fig.savefig(path, bbox_inches="tight", **kwargs)
        outputs.append(path.name)
    plt.close(fig)
    return outputs


def write_source_data(frame: pd.DataFrame, name: str) -> str:
    path = FIGURE_DIR / f"source_data_chapter5_{name}.csv"
    frame.to_csv(path, index=False)
    return path.name


def short_package(package_id: str) -> str:
    return {
        "blis_haswell_f32_6x16": "BLIS f32\n6×16",
        "blis_haswell_f64_6x8": "BLIS f64\n6×8",
        "openblas_riscv64_zvl128b_f32_8x8": "OpenBLAS RVV\n8×8",
    }[package_id]


def figure_51() -> tuple[list[str], list[str]]:
    mutations = pd.read_csv(CONTRACT_VALIDATION / "e1_mutation_results.csv")
    faults = pd.read_csv(CONTRACT_VALIDATION / "e1_fault_injection.csv")
    dangerous = mutations[mutations["dangerous_mutation"].astype(bool)].copy()

    dangerous["field_group"] = dangerous["mutation_field"].where(
        ~dangerous["mutation_field"].str.startswith("kernel."),
        "kernel.block",
    )
    field_order = [
        "dtype",
        "target.features",
        "kernel.block",
        "layout.inner_stride",
        "packing.schema_id",
        "beta_mode",
        "abi.schema_id",
        "provenance.source_revision",
    ]
    field_labels = ["dtype", "ISA", "MR/NR", "stride", "packing", "tail / β", "ABI", "revision"]
    packages = list(dict.fromkeys(dangerous["package_id"]))
    action_code = {"fallback": 0, "reject": 1}
    matrix = np.empty((len(field_order), len(packages)))
    text = np.empty_like(matrix, dtype=object)
    for i, field in enumerate(field_order):
        for j, package in enumerate(packages):
            row = dangerous[
                (dangerous["field_group"] == field) & (dangerous["package_id"] == package)
            ].iloc[0]
            action = str(row["predicted_path"])
            matrix[i, j] = action_code[action]
            text[i, j] = "F" if action == "fallback" else "R"

    metric_frame = pd.DataFrame(
        [
            {"检查": "正例路径", "通过": int((~mutations["dangerous_mutation"].astype(bool)).sum()), "总数": 6},
            {"检查": "危险变异", "通过": int(dangerous["safely_downgraded_or_rejected"].astype(bool).sum()), "总数": len(dangerous)},
            {"检查": "故障注入", "通过": int(faults["wrong_result_detected"].astype(bool).sum()), "总数": len(faults)},
        ]
    )
    metric_frame["通过率"] = metric_frame["通过"] / metric_frame["总数"]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM, 76 * MM),
        gridspec_kw={"width_ratios": [1.65, 1.0]},
        constrained_layout=True,
    )
    cmap = mcolors.ListedColormap([COLORS["fallback"], COLORS["reject"]])
    axes[0].imshow(matrix, cmap=cmap, vmin=-0.5, vmax=1.5, aspect="auto")
    axes[0].set_xticks(range(len(packages)), [short_package(p) for p in packages])
    axes[0].set_yticks(range(len(field_order)), field_labels)
    axes[0].set_title("危险单字段变异的安全处理")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axes[0].text(
                j,
                i,
                text[i, j],
                ha="center",
                va="center",
                color="white" if matrix[i, j] == 1 else "#333333",
                fontweight="bold",
            )
    axes[0].grid(False)
    axes[0].legend(
        handles=[
            mpatches.Patch(facecolor=COLORS["fallback"], edgecolor="#555555", label="F：fallback"),
            mpatches.Patch(facecolor=COLORS["reject"], edgecolor="#555555", label="R：reject"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=2,
    )
    panel(axes[0], "a")

    bars = axes[1].bar(
        metric_frame["检查"],
        metric_frame["通过率"],
        color=[COLORS["C"], COLORS["reject"], COLORS["B4"]],
        edgecolor="#333333",
        linewidth=0.6,
        width=0.62,
    )
    for bar, (_, row) in zip(bars, metric_frame.iterrows()):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            0.51,
            f"{int(row['通过'])}/{int(row['总数'])}",
            ha="center",
            va="center",
            color="white" if bar.get_facecolor()[:3] != mcolors.to_rgb(COLORS["B4"]) else "#222222",
            fontweight="bold",
        )
    axes[1].set_ylim(0, 1.08)
    axes[1].set_ylabel("通过率")
    axes[1].set_title("路径、变异与运行时故障")
    axes[1].set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "25%", "50%", "75%", "100%"])
    panel(axes[1], "b")

    source_files = [
        write_source_data(
            dangerous[
                [
                    "package_id",
                    "mutation_field",
                    "expected_path",
                    "predicted_path",
                    "diagnostic",
                    "safely_downgraded_or_rejected",
                ]
            ],
            "fig5_1_mutations",
        ),
        write_source_data(metric_frame, "fig5_1_checks"),
    ]
    return finish(fig, "chapter5_contract_mutation_fault_matrix"), source_files


def figure_52() -> tuple[list[str], list[str]]:
    rows = pd.read_csv(CONTRACT_VALIDATION / "e2_space_classification.csv")
    first = pd.read_csv(CONTRACT_VALIDATION / "e2_first_callable.csv")
    order = ["G0", "G1", "C"]
    summary = (
        rows.groupby("space", as_index=False)
        .agg(
            mean_pre_count=("pre_normalization_retained_count", "mean"),
            mean_retained_count=("retained_count", "mean"),
            mean_reduction_ratio=("reduction_ratio", "mean"),
            mean_callable_density=("callable_density", "mean"),
            mean_pre_ir_duplicate_ratio=("pre_normalization_ir_duplicate_ratio", "mean"),
            mean_ir_duplicate_ratio=("normalized_ir_duplicate_ratio", "mean"),
        )
        .set_index("space")
        .loc[order]
        .reset_index()
    )
    first_summary = (
        first.groupby("space", as_index=False)
        .agg(
            workload_median_first_callable=("median_draws_to_first_callable", "median"),
            workload_p95_first_callable=("p95_draws_to_first_callable", "quantile"),
        )
        .set_index("space")
        .loc[order]
        .reset_index()
    )
    summary = summary.merge(first_summary[["space", "workload_median_first_callable"]], on="space")

    fig, axes = plt.subplots(1, 3, figsize=(183 * MM, 65 * MM), constrained_layout=True)
    colors = [COLORS[key] for key in order]
    x = np.arange(len(order))
    bars = axes[0].bar(
        x,
        summary["mean_retained_count"],
        color=colors,
        edgecolor="#333333",
        linewidth=0.6,
    )
    for bar, hatch in zip(bars, [HATCHES[key] for key in order]):
        bar.set_hatch(hatch)
    axes[0].set_yscale("log")
    axes[0].set_yticks([100, 1000], ["100", "1,000"])
    axes[0].set_xticks(x, order)
    axes[0].set_ylabel("平均候选数（对数坐标）")
    axes[0].set_title("规范化后保留规模")
    axes[0].bar_label(bars, labels=[f"{v:.1f}" for v in summary["mean_retained_count"]], padding=2, fontsize=7)
    panel(axes[0], "a")

    bars = axes[1].bar(
        x,
        summary["mean_callable_density"],
        color=colors,
        edgecolor="#333333",
        linewidth=0.6,
    )
    for bar, hatch in zip(bars, [HATCHES[key] for key in order]):
        bar.set_hatch(hatch)
    axes[1].set_xticks(x, order)
    axes[1].set_ylim(0, 1.08)
    axes[1].set_ylabel("可调用密度")
    axes[1].set_title("direct / adapt 密度")
    axes[1].bar_label(bars, labels=[f"{v:.3f}" for v in summary["mean_callable_density"]], padding=2, fontsize=7)
    panel(axes[1], "b")

    width = 0.34
    pre = axes[2].bar(
        x - width / 2,
        summary["mean_pre_ir_duplicate_ratio"],
        width,
        color="white",
        edgecolor=colors,
        linewidth=1.2,
        label="规范化前",
    )
    post = axes[2].bar(
        x + width / 2,
        summary["mean_ir_duplicate_ratio"],
        width,
        color=colors,
        edgecolor="#333333",
        linewidth=0.6,
        label="规范化后",
    )
    for bar, hatch in zip(post, [HATCHES[key] for key in order]):
        bar.set_hatch(hatch)
    axes[2].set_xticks(x, order)
    axes[2].set_ylim(0, 0.57)
    axes[2].set_ylabel("IR 重复率")
    axes[2].set_title("参数规范化后的语义重复")
    axes[2].legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    axes[2].bar_label(pre, labels=[f"{v:.2f}" for v in summary["mean_pre_ir_duplicate_ratio"]], padding=1, fontsize=6)
    axes[2].bar_label(post, labels=[f"{v:.2f}" for v in summary["mean_ir_duplicate_ratio"]], padding=1, fontsize=6)
    panel(axes[2], "c")

    source_files = [write_source_data(summary, "fig5_2_space_quality")]
    return finish(fig, "chapter5_space_intrinsic_quality"), source_files


def figure_53() -> tuple[list[str], list[str]]:
    summary = read_json(CONTRACT_VALIDATION / "e2_summary.json")
    c = summary["spaces"]["C"]
    comparison = pd.DataFrame(
        [
            {
                "状态": "规范化前",
                "平均候选数": c["mean_pre_normalization_retained_count"],
                "D90": c["pre_normalization_ablation"]["D90"],
                "time_to_90_median": c["pre_normalization_ablation"]["time_to_90pct_pool_best"],
            },
            {
                "状态": "规范化后",
                "平均候选数": c["mean_retained_count"],
                "D90": c["D90"],
                "time_to_90_median": c["time_to_90_pool_best"],
            },
        ]
    )

    old_runs = pd.read_csv(FORMAL_EVALUATION / "fixed_budget_results.csv")
    old_runs = old_runs[(old_runs["suite"] == "base") & (old_runs["label"] == "B2")].copy()
    old_runs["状态"] = "规范化前"
    old_runs["time_to_90"] = old_runs["time_to_90pct_iteration"]
    old_runs["right_censored"] = ~old_runs["reached_90pct_pool_best"].astype(bool)
    old_runs = old_runs[["workload_id", "seed", "状态", "time_to_90", "right_censored"]]

    new_runs = pd.read_csv(CONTRACT_VALIDATION / "e2_normalized_convergence.csv").copy()
    new_runs["状态"] = "规范化后"
    new_runs["time_to_90"] = new_runs["time_to_90pct_iteration"]
    new_runs = new_runs[["workload_id", "seed", "状态", "time_to_90", "right_censored"]]
    runs = pd.concat([old_runs, new_runs], ignore_index=True)

    fig, axes = plt.subplots(1, 3, figsize=(183 * MM, 65 * MM), constrained_layout=True)
    state_colors = [COLORS["G1"], COLORS["C"]]
    x = np.arange(2)

    bars = axes[0].bar(
        x,
        comparison["平均候选数"],
        color=state_colors,
        edgecolor="#333333",
        linewidth=0.6,
        width=0.62,
    )
    axes[0].set_xticks(x, comparison["状态"])
    axes[0].set_ylabel("C 池平均候选数")
    axes[0].set_title("不活跃参数折叠")
    axes[0].bar_label(bars, labels=[f"{v:.1f}" for v in comparison["平均候选数"]], padding=2)
    panel(axes[0], "a")

    bars = axes[1].bar(
        x,
        comparison["D90"],
        color=state_colors,
        edgecolor="#333333",
        linewidth=0.6,
        width=0.62,
    )
    axes[1].set_xticks(x, comparison["状态"])
    axes[1].set_ylim(0, 0.23)
    axes[1].set_ylabel("D90")
    axes[1].set_title("高性能候选密度")
    axes[1].bar_label(bars, labels=[f"{100*v:.2f}%" for v in comparison["D90"]], padding=2)
    panel(axes[1], "b")

    sns.boxplot(
        data=runs,
        x="状态",
        y="time_to_90",
        order=["规范化前", "规范化后"],
        hue="状态",
        hue_order=["规范化前", "规范化后"],
        palette=state_colors,
        legend=False,
        width=0.48,
        showfliers=False,
        linewidth=0.9,
        ax=axes[2],
    )
    noncensored = runs[~runs["right_censored"].astype(bool)]
    sns.stripplot(
        data=noncensored,
        x="状态",
        y="time_to_90",
        order=["规范化前", "规范化后"],
        color="#222222",
        size=2.2,
        alpha=0.42,
        jitter=0.16,
        ax=axes[2],
    )
    for xpos, state in enumerate(["规范化前", "规范化后"]):
        censored = runs[(runs["状态"] == state) & runs["right_censored"].astype(bool)]
        if not censored.empty:
            jitter = np.linspace(-0.10, 0.10, len(censored))
            axes[2].scatter(
                np.full(len(censored), xpos) + jitter,
                censored["time_to_90"],
                marker="^",
                s=20,
                color=COLORS["reject"],
                zorder=5,
                label="右删失" if xpos == 0 else None,
            )
    axes[2].set_xlabel("")
    axes[2].set_ylabel("callback 次数")
    axes[2].set_title("40 条离线 BaCO callback 轨迹")
    axes[2].set_ylim(0, 28)
    axes[2].legend(loc="upper center", bbox_to_anchor=(0.5, -0.14))
    panel(axes[2], "c")

    source_files = [
        write_source_data(comparison, "fig5_3_normalization"),
        write_source_data(runs, "fig5_3_time_to_90"),
    ]
    return finish(fig, "chapter5_normalization_offline_replay"), source_files


def figure_54() -> tuple[list[str], list[str]]:
    convergence = pd.read_csv(FORMAL_EVALUATION / "convergence_normalized.csv")
    convergence = convergence[convergence["suite"] == "base"].copy()
    order = ["B1", "B2", "B3", "B4"]
    curve_rows: list[dict] = []
    for method in order:
        method_rows = convergence[convergence["label"] == method]
        for iteration, group in method_rows.groupby("iteration"):
            values = group["normalized_best_to_blis"].astype(float)
            curve_rows.append(
                {
                    "method": method,
                    "iteration": int(iteration),
                    "median": values.median(),
                    "q25": values.quantile(0.25),
                    "q75": values.quantile(0.75),
                    "runs": len(values),
                }
            )
    curves = pd.DataFrame(curve_rows)
    fixed = pd.read_csv(FORMAL_EVALUATION / "fixed_budget_summary.csv")
    fixed = fixed[(fixed["suite"] == "base") & fixed["label"].isin(order)].copy()
    fixed["label"] = pd.Categorical(fixed["label"], categories=order, ordered=True)
    fixed = fixed.sort_values("label")

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM, 74 * MM),
        gridspec_kw={"width_ratios": [1.55, 1.0]},
        constrained_layout=True,
    )
    for method in order:
        frame = curves[curves["method"] == method]
        xs = frame["iteration"].to_numpy(dtype=float)
        median = frame["median"].to_numpy(dtype=float)
        q25 = frame["q25"].to_numpy(dtype=float)
        q75 = frame["q75"].to_numpy(dtype=float)
        axes[0].plot(
            xs,
            median,
            color=COLORS[method],
            lw=1.6,
            label=method,
            marker={"B1": "o", "B2": "s", "B3": "^", "B4": "D"}[method],
            markevery=5,
            ms=3,
        )
        axes[0].fill_between(xs, q25, q75, color=COLORS[method], alpha=0.12, linewidth=0)
    axes[0].axhline(1.0, color=COLORS["library"], lw=1.2, ls="--", label="B5 完整 BLIS")
    axes[0].set_xlim(1, 25)
    axes[0].set_ylim(0, 1.10)
    axes[0].set_xlabel("候选评价次数")
    axes[0].set_ylabel("best-so-far / B5 性能")
    axes[0].set_title("固定预算收敛轨迹（中位数与四分位带）")
    axes[0].legend(ncol=3, loc="lower right")
    panel(axes[0], "a")

    y = np.arange(len(order))[::-1]
    for yi, (_, row) in zip(y, fixed.iterrows()):
        value = float(row["normalized_gmean"])
        low = float(row["bootstrap_low"])
        high = float(row["bootstrap_high"])
        method = str(row["label"])
        axes[1].plot([low, high], [yi, yi], color=COLORS[method], lw=1.8)
        axes[1].plot(value, yi, marker="o", color=COLORS[method], ms=5)
        axes[1].text(high + 0.012, yi, f"{value:.3f}", va="center", fontsize=7)
    axes[1].axvline(1.0, color=COLORS["library"], lw=1.0, ls="--")
    axes[1].set_yticks(y, order)
    axes[1].set_xlim(0.62, 1.10)
    axes[1].set_xlabel("best-at-25 / B5 性能")
    axes[1].set_title("几何均值与 95% bootstrap CI")
    panel(axes[1], "b")

    source_files = [
        write_source_data(curves, "fig5_4_convergence"),
        write_source_data(fixed, "fig5_4_fixed_budget"),
    ]
    return finish(fig, "chapter5_fixed_budget_search"), source_files


def figure_55() -> tuple[list[str], list[str]]:
    fixed = pd.read_csv(FORMAL_EVALUATION / "fixed_budget_summary.csv")
    packing = fixed[
        (fixed["suite"] == "ablation") & fixed["label"].isin(["full", "no_packing_rule"])
    ].copy()
    packing["显示名"] = packing["label"].map({"full": "完整 B4", "no_packing_rule": "去除 packing 规则"})
    packing["显示名"] = pd.Categorical(
        packing["显示名"], categories=["完整 B4", "去除 packing 规则"], ordered=True
    )
    packing = packing.sort_values("显示名")

    paired = pd.read_csv(TERMINATION / "paired_comparisons.csv")
    paired = paired[
        (
            (paired["test_method"] == "D0_data_only_baco")
            & (paired["reference_method"] == "B2_no_prior_baco")
        )
        | (
            (paired["test_method"] == "D1_expert_plus_data_baco")
            & (paired["reference_method"] == "D0_data_only_baco")
        )
    ].copy()
    paired["比较"] = np.where(
        paired["test_method"] == "D0_data_only_baco",
        "Data-only / no-prior",
        "Expert+Data / Data-only",
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM, 70 * MM),
        gridspec_kw={"width_ratios": [0.9, 1.45]},
        constrained_layout=True,
    )
    y = np.arange(len(packing))[::-1]
    for yi, (_, row) in zip(y, packing.iterrows()):
        label = str(row["label"])
        color = COLORS["B4"] if label == "full" else COLORS["reject"]
        value = float(row["normalized_gmean"])
        low = float(row["bootstrap_low"])
        high = float(row["bootstrap_high"])
        axes[0].plot([low, high], [yi, yi], color=color, lw=2.0)
        axes[0].plot(value, yi, "o", color=color, ms=5)
        axes[0].text(high * 1.08, yi, f"{value:.3f}", va="center", fontsize=7)
    axes[0].axvline(1.0, color=COLORS["library"], ls="--", lw=1.0)
    axes[0].set_xscale("log")
    axes[0].set_xlim(0.03, 1.25)
    axes[0].set_xticks([0.05, 0.10, 0.50, 1.00], ["0.05", "0.10", "0.50", "1.00"])
    axes[0].set_yticks(y, packing["显示名"])
    axes[0].set_xlabel("best-at-25 / B5 性能（对数坐标）")
    axes[0].set_title("硬 packing 边界")
    panel(axes[0], "a")

    comparisons = ["Data-only / no-prior", "Expert+Data / Data-only"]
    ybase = np.arange(len(comparisons))[::-1]
    offsets = {5: 0.12, 10: -0.12}
    markers = {5: "o", 10: "s"}
    for comp, base in zip(comparisons, ybase):
        for budget in [5, 10]:
            row = paired[(paired["比较"] == comp) & (paired["budget"] == budget)].iloc[0]
            yval = base + offsets[budget]
            color = COLORS["C"] if comp.startswith("Data-only") else COLORS["B4"]
            axes[1].plot(
                [float(row["ci95_lower"]), float(row["ci95_upper"])],
                [yval, yval],
                color=color,
                lw=1.8,
            )
            axes[1].plot(
                float(row["gmean_speedup"]),
                yval,
                marker=markers[budget],
                color=color,
                ms=5,
                linestyle="none",
                label=f"budget {budget}" if comp == comparisons[0] else None,
            )
    axes[1].axvline(1.0, color=COLORS["library"], ls="--", lw=1.0)
    axes[1].set_yticks(ybase, comparisons)
    axes[1].set_xlim(0.97, 1.09)
    axes[1].set_xlabel("左侧方法 / 右侧方法的性能比")
    axes[1].set_title("目标数据与 BLIS 软字段的增量")
    axes[1].legend(loc="center right")
    panel(axes[1], "b")

    source_files = [
        write_source_data(packing, "fig5_5_packing"),
        write_source_data(paired, "fig5_5_soft_prior"),
    ]
    return finish(fig, "chapter5_hard_soft_ablation"), source_files


def figure_56() -> tuple[list[str], list[str]]:
    reuse = pd.read_csv(CONTRACT_VALIDATION / "e3_reuse_audit.csv")
    cross_host = read_json(X86_CROSS_HOST / "cross_host_summary.json")
    same_pool = pd.read_csv(SAME_POOL / "paired_comparisons.csv")
    same_pool = same_pool[
        same_pool["comparison"] == "B4_calibrated_prior_baco_vs_B2_no_prior_baco"
    ].copy()

    matrix_rows = [
        {"层级": "Contract Schema", "BLIS f64": 2, "OpenBLAS RVV": 2, "i9 新主机": 2},
        {"层级": "核心生成器", "BLIS f64": 2, "OpenBLAS RVV": 1, "i9 新主机": 2},
        {"层级": "合法执行", "BLIS f64": 2, "OpenBLAS RVV": 2, "i9 新主机": 2},
        {"层级": "性能排序", "BLIS f64": 1, "OpenBLAS RVV": 0, "i9 新主机": 0},
    ]
    matrix_frame = pd.DataFrame(matrix_rows)
    matrix = matrix_frame[["BLIS f64", "OpenBLAS RVV", "i9 新主机"]].to_numpy()
    labels = {
        0: "不迁移",
        1: "局部 / 目标相关",
        2: "已验证复用",
    }

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM, 74 * MM),
        gridspec_kw={"width_ratios": [1.15, 1.0]},
        constrained_layout=True,
    )
    cmap = mcolors.ListedColormap(["#D9D9D9", "#F2C078", COLORS["C"]])
    axes[0].imshow(matrix, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto")
    axes[0].set_xticks(
        range(3),
        ["BLIS f64\n同库新 dtype", "OpenBLAS RVV\n新库 / ISA", "i9\n同包新主机"],
    )
    axes[0].set_yticks(range(4), matrix_frame["层级"])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            axes[0].text(
                j,
                i,
                labels[value],
                ha="center",
                va="center",
                fontsize=6.5,
                color="white" if value == 2 else "#222222",
            )
    axes[0].grid(False)
    axes[0].set_title("迁移需要分层陈述")
    axes[0].legend(
        handles=[
            mpatches.Patch(facecolor="#D9D9D9", label="不迁移"),
            mpatches.Patch(facecolor="#F2C078", label="局部 / 目标相关"),
            mpatches.Patch(facecolor=COLORS["C"], label="已验证复用"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
    )
    panel(axes[0], "a")

    environments = ["i7_10750h_wsl2", "i9_14900_linux"]
    env_labels = {"i7_10750h_wsl2": "i7-10750H", "i9_14900_linux": "i9-14900"}
    ybase = np.arange(len(environments))[::-1]
    offsets = {5: 0.12, 10: -0.12}
    markers = {5: "o", 10: "s"}
    for environment, base in zip(environments, ybase):
        for budget in [5, 10]:
            row = same_pool[
                (same_pool["environment"] == environment) & (same_pool["budget"] == budget)
            ].iloc[0]
            yval = base + offsets[budget]
            color = COLORS["B4"] if environment.startswith("i7") else COLORS["G1"]
            axes[1].plot(
                [float(row["ci95_low"]), float(row["ci95_high"])],
                [yval, yval],
                color=color,
                lw=1.8,
            )
            axes[1].plot(
                float(row["speedup_gmean"]),
                yval,
                marker=markers[budget],
                color=color,
                ms=5,
                linestyle="none",
                label=f"budget {budget}" if environment == environments[0] else None,
            )
    axes[1].axvline(1.0, color=COLORS["library"], ls="--", lw=1.0)
    axes[1].set_yticks(ybase, [env_labels[e] for e in environments])
    axes[1].set_xlim(0.96, 1.105)
    axes[1].set_xlabel("calibrated-prior / no-prior 性能比")
    axes[1].set_title("严格同池的跨主机复制")
    axes[1].legend(loc="lower right")
    panel(axes[1], "b")

    audit_frame = pd.DataFrame(
        [
            {
                "证据": "Schema IoU",
                "数值": float(reuse["schema_intersection_over_union_ratio"].iloc[0]),
                "说明": "31/34 leaf paths",
            },
            {
                "证据": "BLIS f64 core generator modified LOC",
                "数值": float(
                    reuse.loc[
                        reuse["package_id"] == "blis_haswell_f64_6x8",
                        "core_generator_modified_loc",
                    ].iloc[0]
                ),
                "说明": "before/after hash audit",
            },
            {
                "证据": "i7 pool / BLIS",
                "数值": float(
                    cross_host["hosts"]["development_host"]["candidate_pool_relative_to_blis_gmean"]
                ),
                "说明": "36 f64 workloads",
            },
            {
                "证据": "i9 pool / BLIS",
                "数值": float(
                    cross_host["hosts"]["i9_14900"]["candidate_pool_relative_to_blis_gmean"]
                ),
                "说明": "36 f64 workloads",
            },
        ]
    )
    source_files = [
        write_source_data(matrix_frame, "fig5_6_transfer_matrix"),
        write_source_data(same_pool, "fig5_6_cross_host_prior"),
        write_source_data(audit_frame, "fig5_6_transfer_evidence"),
    ]
    return finish(fig, "chapter5_transfer_layers_cross_host"), source_files


def figure_57() -> tuple[list[str], list[str]]:
    i9 = read_json(EXTERNAL / "i9_external_summary.json")
    k230 = read_json(EXTERNAL / "k230_external_summary.json")
    closure = read_json(APPLICATION / "k230_mlir_closure_summary.json")
    economics = pd.read_csv(CONTRACT_VALIDATION / "e4_value_curves.csv")
    break_even = pd.read_csv(CONTRACT_VALIDATION / "e4_break_even_summary.csv")

    ratios = pd.DataFrame(
        [
            {
                "比较": "i9 生成池 / BLIS",
                "ratio": i9["generated_relative_to_blis_geomean"],
                "ci_low": i9["generated_relative_to_blis_ci95"][0],
                "ci_high": i9["generated_relative_to_blis_ci95"][1],
                "类型": "完整库边界",
            },
            {
                "比较": "K230 adapter / OpenBLAS",
                "ratio": k230["adapter_relative_to_openblas_geomean"],
                "ci_low": k230["adapter_relative_to_openblas_ci95"][0],
                "ci_high": k230["adapter_relative_to_openblas_ci95"][1],
                "类型": "完整库边界",
            },
            {
                "比较": "K230 C adapter / MLIR adapter",
                "ratio": closure["c_adapter_over_mlir_adapter_geomean"],
                "ci_low": closure["c_adapter_over_mlir_adapter_ci95"][0],
                "ci_high": closure["c_adapter_over_mlir_adapter_ci95"][1],
                "类型": "wrapper parity",
            },
        ]
    )

    curve = economics[economics["scenario"] == "i7_f64_posthoc_winning_shapes"].copy()
    curve["net_value_point_s"] = curve["net_value_point_ms"] / 1000.0
    curve["net_value_lcb95_s"] = curve["net_value_lcb95_ms"] / 1000.0
    be = break_even[break_even["scenario"] == "i7_f64_posthoc_winning_shapes"].iloc[0]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM, 76 * MM),
        gridspec_kw={"width_ratios": [1.0, 1.25]},
        constrained_layout=True,
    )
    y = np.arange(len(ratios))[::-1]
    for yi, (_, row) in zip(y, ratios.iterrows()):
        color = COLORS["C"] if row["类型"] == "wrapper parity" else COLORS["reject"]
        axes[0].plot([row["ci_low"], row["ci_high"]], [yi, yi], color=color, lw=1.8)
        axes[0].plot(row["ratio"], yi, "o", color=color, ms=5)
        axes[0].text(row["ci_high"] + 0.018, yi, f"{row['ratio']:.3f}", va="center", fontsize=7)
    axes[0].axvline(1.0, color=COLORS["library"], ls="--", lw=1.0)
    axes[0].set_yticks(y, ratios["比较"])
    axes[0].set_xlim(0.42, 1.08)
    axes[0].set_xlabel("几何时间或性能比")
    axes[0].set_title("完整库边界与 wrapper parity")
    panel(axes[0], "a")

    axes[1].plot(
        curve["horizon"],
        curve["net_value_point_s"],
        color=COLORS["B4"],
        lw=1.7,
        marker="o",
        ms=3,
        label="点估计 V(H)",
    )
    axes[1].plot(
        curve["horizon"],
        curve["net_value_lcb95_s"],
        color=COLORS["library"],
        lw=1.5,
        marker="s",
        ms=3,
        label="LCB95 V(H)",
    )
    axes[1].axhline(0, color="#666666", lw=0.9)
    axes[1].axvline(
        float(be["point_break_even_horizon"]),
        color=COLORS["B4"],
        ls=":",
        lw=1.0,
    )
    axes[1].axvline(
        float(be["lcb95_break_even_horizon"]),
        color=COLORS["library"],
        ls=":",
        lw=1.0,
    )
    axes[1].text(
        float(be["point_break_even_horizon"]),
        axes[1].get_ylim()[1] * 0.80,
        "点估计\n165,865",
        color=COLORS["B4"],
        ha="right",
        va="top",
        fontsize=6.5,
    )
    axes[1].text(
        float(be["lcb95_break_even_horizon"]),
        axes[1].get_ylim()[1] * 0.80,
        "LCB95\n741,587",
        color=COLORS["library"],
        ha="left",
        va="top",
        fontsize=6.5,
    )
    axes[1].set_xscale("log")
    axes[1].set_xticks(
        [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000],
        ["1", "10", "100", "1k", "10k", "100k", "1M"],
    )
    axes[1].set_xlabel("合成 deployment cycle 数（对数坐标）")
    axes[1].set_ylabel("净价值 V(H)（s）")
    axes[1].set_title("i7 事后 19-shape 描述性上界")
    axes[1].legend(loc="upper left")
    panel(axes[1], "b")

    source_files = [
        write_source_data(ratios, "fig5_7_external_ratios"),
        write_source_data(curve, "fig5_7_value_curve"),
        write_source_data(pd.DataFrame([be]), "fig5_7_break_even"),
    ]
    return finish(fig, "chapter5_library_boundary_economics"), source_files


def figure_58() -> tuple[list[str], list[str]]:
    rows = pd.read_csv(CONTRACT_VALIDATION / "e2_space_classification.csv")
    rows = rows[rows["space"] == "C"].copy()
    family_order = ["square", "m_skinny", "n_skinny", "k_small", "tail", "model_rect"]
    family_labels = {
        "square": "方阵",
        "m_skinny": "M 窄",
        "n_skinny": "N 窄",
        "k_small": "小 K",
        "tail": "边界",
        "model_rect": "模型矩形",
    }
    family_colors = {
        "square": "#4C78A8",
        "m_skinny": "#72A0C1",
        "n_skinny": "#7A6FA8",
        "k_small": "#B39BC8",
        "tail": "#F28E2B",
        "model_rect": "#008C95",
    }
    rows["family"] = pd.Categorical(rows["family"], categories=family_order, ordered=True)
    rows = rows.sort_values(["family", "pre_normalization_retained_count", "workload_id"])
    rows["workload_order"] = np.arange(1, len(rows) + 1)
    rows["removed_count"] = (
        rows["pre_normalization_retained_count"] - rows["retained_count"]
    )
    rows["retained_fraction"] = (
        rows["retained_count"] / rows["pre_normalization_retained_count"]
    )

    fig, ax = plt.subplots(figsize=(170 * MM, 68 * MM), constrained_layout=True)
    for family in family_order:
        frame = rows[rows["family"] == family]
        color = family_colors[family]
        ax.vlines(
            frame["workload_order"],
            frame["retained_count"],
            frame["pre_normalization_retained_count"],
            color=color,
            alpha=0.50,
            linewidth=1.0,
        )
        ax.scatter(
            frame["workload_order"],
            frame["pre_normalization_retained_count"],
            facecolors="white",
            edgecolors=color,
            marker="s",
            s=19,
            linewidth=0.9,
            zorder=3,
        )
        ax.scatter(
            frame["workload_order"],
            frame["retained_count"],
            color=color,
            marker="o",
            s=17,
            linewidth=0,
            label=family_labels[family],
            zorder=4,
        )

    centers = []
    labels = []
    boundaries = []
    for family in family_order:
        positions = rows.loc[rows["family"] == family, "workload_order"].to_numpy()
        centers.append(float(positions.mean()))
        labels.append(family_labels[family])
        boundaries.append(float(positions.max()) + 0.5)
    for boundary in boundaries[:-1]:
        ax.axvline(boundary, color="#D8D8D8", linewidth=0.6, zorder=0)
    ax.set_xticks(centers, labels)
    ax.set_xlim(0.3, len(rows) + 0.7)
    ax.set_ylim(0, float(rows["pre_normalization_retained_count"].max()) * 1.10)
    ax.set_ylabel("Contract 候选数")
    ax.set_xlabel("36 个冻结工作负载（按类别分组）")
    ax.set_title("不活跃 vectorize 规范化在各工作负载上的配对变化")
    ax.text(
        0.99,
        0.96,
        "均值 208.7 → 104.4；36/36 均减少 50%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.2,
        color="#333333",
    )
    marker_legend = [
        plt.Line2D([0], [0], marker="s", color="#555555", markerfacecolor="white",
                   linestyle="none", markersize=5, label="规范化前"),
        plt.Line2D([0], [0], marker="o", color="#555555", markerfacecolor="#555555",
                   linestyle="none", markersize=5, label="规范化后"),
    ]
    family_legend = ax.legend(
        loc="upper left", ncol=3, title="工作负载类别", fontsize=6.5, title_fontsize=6.5
    )
    ax.add_artist(family_legend)
    ax.legend(handles=marker_legend, loc="upper center", ncol=2, bbox_to_anchor=(0.49, 1.0))

    source = rows[
        [
            "workload_id",
            "family",
            "workload_order",
            "pre_normalization_retained_count",
            "retained_count",
            "removed_count",
            "retained_fraction",
        ]
    ].copy()
    source["family"] = source["family"].astype(str)
    return finish(fig, "chapter5_normalization_workload_distribution"), [
        write_source_data(source, "fig5_8_normalization_distribution")
    ]


def validate_outputs(manifest: dict) -> list[str]:
    notes: list[str] = []
    for figure in manifest["figures"]:
        for filename in figure["outputs"]:
            path = FIGURE_DIR / filename
            if not path.exists() or path.stat().st_size < 1000:
                raise RuntimeError(f"Missing or unexpectedly small figure output: {path}")
            if path.suffix == ".svg":
                text = path.read_text(encoding="utf-8")
                if "<text" not in text:
                    raise RuntimeError(f"SVG text was converted to paths: {path}")
        notes.append(f"{figure['id']}: four formats present; SVG contains editable text.")
    return notes


def main() -> None:
    configure_style()
    jobs = [
        ("图5-1", figure_51),
        ("图5-2", figure_52),
        ("图5-3", figure_58),
        ("图5-4", figure_53),
        ("图5-5", figure_54),
        ("图5-6", figure_55),
        ("图5-7", figure_56),
        ("图5-8", figure_57),
    ]
    figures = []
    for figure_id, function in jobs:
        outputs, sources = function()
        figures.append({"id": figure_id, "outputs": outputs, "source_data": sources})

    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "backend": "Python/Matplotlib/Seaborn",
        "measurement_boundary": (
            "Figures are reconstructed from frozen artifacts. "
            "No candidate compilation, BaCO execution, or hardware measurement is performed."
        ),
        "figures": figures,
    }
    manifest["qa_checks"] = validate_outputs(manifest)
    manifest_path = FIGURE_DIR / "chapter5_figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    qa_lines = [
        "# 第五章图形 QA",
        "",
        f"- 生成时间：{manifest['generated_at_utc']}",
        "- 后端：Python/Matplotlib/Seaborn。",
        "- 数据边界：只读取冻结结果文件，不重新编译、不运行 BaCO、不进行硬件测量。",
        "- 每幅图均导出 SVG、PDF、600 dpi TIFF 和 PNG；SVG 文字保持可编辑。",
        "- 颜色以形状、线型或填充纹理辅助区分，关键判断不只依赖颜色。",
        "- 图5-3只显示不活跃参数规范化的配对规模变化，不解释为性能收益。",
        "- 图5-4明确区分规范化前结果与冻结离线 replay。",
        "- 图5-5的区间重采样 trajectory，不代表主机间不确定性。",
        "- 图5-6的 packing 消融改变空间成员，只用于操作性边界解释。",
        "- 图5-7将表示、生成器、合法执行和性能排序分层。",
        "- 图5-8的 i7 曲线是 post-hoc descriptive upper bound，cycle 不是模型推理。",
        "",
        "## 自动检查",
        "",
    ]
    qa_lines.extend(f"- {note}" for note in manifest["qa_checks"])
    (FIGURE_DIR / "chapter5_figure_qa.md").write_text(
        "\n".join(qa_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
