#!/usr/bin/env python3
"""Render Figure 4-1 through Figure 4-5 with Python/matplotlib only."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


PROJECT = Path(__file__).resolve().parent.parent
FIGURES = PROJECT / "figures"
MM = 1.0 / 25.4

COLORS = {
    "ink": "#263238",
    "muted": "#607D8B",
    "neutral": "#ECEFF1",
    "blue": "#2F6B9A",
    "blue_light": "#DCEAF4",
    "teal": "#2A8C82",
    "teal_light": "#D9EEE9",
    "orange": "#D9892B",
    "orange_light": "#F7E6CF",
    "red": "#B84A4A",
    "red_light": "#F3DADA",
    "white": "#FFFFFF",
}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["AR PL SungtiL GB", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.linewidth": 0.8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def canvas(height_mm: float = 100) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(183 * MM, height_mm * MM))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    face: str = "neutral",
    edge: str = "muted",
    fontsize: float = 7,
    weight: str = "normal",
    linestyle: str = "-",
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.005,rounding_size=0.008",
        linewidth=0.9,
        facecolor=COLORS[face],
        edgecolor=COLORS[edge],
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, color=COLORS["ink"], weight=weight)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = "muted", style: str = "-") -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.9,
            color=COLORS[color],
            linestyle=style,
            shrinkA=2,
            shrinkB=2,
        )
    )


def panel_label(ax: plt.Axes, label: str, x: float, y: float) -> None:
    ax.text(
        x,
        y,
        label,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="top",
        color=COLORS["ink"],
        transform=ax.transAxes,
    )


def save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    base = FIGURES / name
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(base.with_suffix(".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def figure_4_1() -> None:
    fig, ax = canvas(96)
    panel_label(ax, "a", 0.01, 0.98)
    top = [
        (0.03, "GEMM 描述\nshape/dtype\nlayout", "neutral", "muted"),
        (0.20, "Task Context\nISA/cache/SIMD", "blue_light", "blue"),
        (0.37, "Contract 选择\n匹配度与适配代价", "blue_light", "blue"),
        (0.56, "条件参数域\n规则实例化", "teal_light", "teal"),
        (0.74, "Compatibility\nChecker", "teal_light", "teal"),
        (0.88, "四类空间\ncore + shell", "orange_light", "orange"),
    ]
    widths = [0.13, 0.13, 0.15, 0.14, 0.11, 0.10]
    for index, ((x, text, face, edge), width) in enumerate(zip(top, widths)):
        box(ax, x, 0.66, width, 0.17, text, face, edge, weight="bold" if index in {2, 3, 4} else "normal")
        if index:
            previous_x, _, _, _ = top[index - 1]
            arrow(ax, (previous_x + widths[index - 1], 0.745), (x, 0.745), "blue" if index < 5 else "orange")

    ax.text(0.5, 0.585, "候选携带 Contract、Rule、原因码与预测路径", ha="center", va="center", color=COLORS["muted"], fontsize=6.5)
    arrow(ax, (0.93, 0.66), (0.93, 0.50), "orange")

    bottom = [
        (0.75, "参数化\nnamed_sequence", "blue_light", "blue"),
        (0.57, "BaCO\n原生模型", "orange_light", "orange"),
        (0.38, "MLIR → LLVM IR\nclang AOT", "neutral", "muted"),
        (0.20, "运行与正确性\n性能测量", "teal_light", "teal"),
        (0.03, "完整日志\n结果 + provenance", "neutral", "muted"),
    ]
    widths2 = [0.15, 0.13, 0.15, 0.14, 0.13]
    for index, ((x, text, face, edge), width) in enumerate(zip(bottom, widths2)):
        box(ax, x, 0.32, width, 0.17, text, face, edge, weight="bold" if index in {0, 1} else "normal")
        if index:
            previous_x, _, _, _ = bottom[index - 1]
            arrow(ax, (previous_x, 0.405), (x + width, 0.405), "teal" if index >= 3 else "blue")
    ax.text(0.5, 0.18, "专家知识决定“搜索什么”；Transform Dialect 表达“如何变换”；BaCO 决定“按何顺序测量”", ha="center", color=COLORS["ink"], fontsize=7, weight="bold")
    ax.plot([0.03, 0.97], [0.12, 0.12], color=COLORS["neutral"], linewidth=1)
    ax.text(0.5, 0.065, "硬约束不由测量反馈修改；软先验仅调整排序与下一轮采样", ha="center", color=COLORS["muted"], fontsize=6.5)
    save(fig, "figure4_1_framework")


def figure_4_2() -> None:
    rows = read_csv(PROJECT / "processed" / "space_summary.csv")
    row = next(item for item in rows if item["task_id"] == "anchor_192x256x256_f32")
    counts = {key: int(row[key]) for key in ("raw_count", "legal_count", "direct_count", "adapt_count", "fallback_count", "reject_count", "expert_core_count", "shell_count", "expert_shell_count")}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(183 * MM, 92 * MM), gridspec_kw={"width_ratios": [1.2, 0.8]})
    for ax in (ax1, ax2):
        ax.set_facecolor("white")
    panel_label(ax1, "a", -0.03, 1.02)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.add_patch(Rectangle((0.04, 0.08), 0.91, 0.82, facecolor=COLORS["neutral"], edgecolor=COLORS["muted"], linewidth=1.0))
    ax1.text(0.06, 0.86, f"U 原始空间  {counts['raw_count']}", fontsize=7.5, weight="bold", color=COLORS["ink"])
    ax1.add_patch(Rectangle((0.10, 0.16), 0.79, 0.60, facecolor=COLORS["blue_light"], edgecolor=COLORS["blue"], linewidth=1.0))
    ax1.text(0.12, 0.71, f"S_legal = S_exec  {counts['legal_count']}", fontsize=7, weight="bold", color=COLORS["blue"])
    ax1.add_patch(Rectangle((0.17, 0.25), 0.50, 0.34, facecolor=COLORS["teal_light"], edgecolor=COLORS["teal"], linewidth=1.0))
    ax1.text(0.19, 0.54, f"S_contract  {counts['direct_count'] + counts['adapt_count']}", fontsize=7, weight="bold", color=COLORS["teal"])
    ax1.add_patch(Rectangle((0.23, 0.32), 0.26, 0.17, facecolor=COLORS["teal"], edgecolor=COLORS["teal"], linewidth=1.0))
    ax1.text(0.36, 0.405, f"S_core\n{counts['expert_core_count']}", color="white", ha="center", va="center", fontsize=7, weight="bold")
    ax1.add_patch(Rectangle((0.53, 0.32), 0.09, 0.17, facecolor=COLORS["orange"], edgecolor=COLORS["orange"], linewidth=1.0))
    ax1.text(0.575, 0.405, f"shell\n{counts['shell_count']}", color="white", ha="center", va="center", fontsize=6.3, weight="bold")
    ax1.add_patch(Rectangle((0.21, 0.29), 0.44, 0.23, fill=False, edgecolor=COLORS["orange"], linewidth=1.2, linestyle="--"))
    ax1.text(0.43, 0.265, f"S_tune = core ∪ shell = {counts['expert_shell_count']}", ha="center", va="top", fontsize=6.5, color=COLORS["orange"], weight="bold")
    ax1.text(0.70, 0.40, f"其余可执行\n{counts['legal_count'] - counts['expert_shell_count']}", ha="center", va="center", fontsize=6.5, color=COLORS["muted"])
    ax1.text(0.50, 0.025, "锚点任务：192×256×256, f32；shell 仅从 S_exec \\ S_core 采样", ha="center", fontsize=6, color=COLORS["muted"])

    panel_label(ax2, "b", -0.12, 1.02)
    labels = ["direct", "adapt", "fallback", "reject"]
    values = [counts[f"{label}_count"] for label in labels]
    colors = [COLORS["teal"], COLORS["orange"], COLORS["blue"], COLORS["red"]]
    bars = ax2.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.62)
    ax2.set_xlabel("候选数量")
    ax2.set_xlim(0, max(values) * 1.18)
    ax2.grid(axis="x", color="#D8DEE2", linewidth=0.6, alpha=0.8)
    ax2.set_axisbelow(True)
    for bar, value in zip(bars, values[::-1]):
        ax2.text(value + max(values) * 0.025, bar.get_y() + bar.get_height() / 2, f"{value}", va="center", fontsize=7, color=COLORS["ink"])
    ax2.set_title("Compatibility Checker 路径构成", fontsize=7.5, pad=8, weight="bold")
    fig.subplots_adjust(wspace=0.28, left=0.05, right=0.98, top=0.93, bottom=0.16)
    save(fig, "figure4_2_spaces_and_paths")


def figure_4_3() -> None:
    reason_data = json.loads((PROJECT / "data" / "reason_codes.json").read_text(encoding="utf-8"))["reason_codes"]
    fig, ax = canvas(104)
    panel_label(ax, "a", 0.01, 0.98)
    box(ax, 0.03, 0.39, 0.13, 0.20, "Task Context\n+ Candidate\n+ Contract", "neutral", "muted", weight="bold")
    arrow(ax, (0.16, 0.49), (0.22, 0.49), "blue")
    dimensions = ["dtype", "ISA", "MR/NR", "K 条件", "layout", "stride", "alignment", "packing", "tail", "call ABI", "Transform"]
    positions = []
    for index, dimension in enumerate(dimensions):
        col = index % 4
        row = index // 4
        x = 0.23 + col * 0.125
        y = 0.68 - row * 0.22
        positions.append((x, y))
        box(ax, x, y, 0.10, 0.11, dimension, "blue_light", "blue", fontsize=6.5)
    ax.add_patch(Rectangle((0.21, 0.20), 0.51, 0.63, fill=False, edgecolor=COLORS["blue"], linewidth=0.9, linestyle="--"))
    ax.text(0.465, 0.855, "逐维检查：硬失败、有限适配、软先验分离", ha="center", fontsize=7, color=COLORS["blue"], weight="bold")
    arrow(ax, (0.72, 0.49), (0.77, 0.49), "blue")
    terminals = [
        (0.78, 0.72, "direct", "全部条件满足", "teal_light", "teal"),
        (0.78, 0.53, "adapt", "存在已实现有限适配", "orange_light", "orange"),
        (0.78, 0.34, "fallback", "Contract/接口不匹配", "blue_light", "blue"),
        (0.78, 0.15, "reject", "语义/Transform 非法", "red_light", "red"),
    ]
    for x, y, name, description, face, edge in terminals:
        box(ax, x, y, 0.19, 0.13, f"{name}\n{description}", face, edge, weight="bold")
    ax.text(0.025, 0.11, f"原因码 {len(reason_data)} 个", fontsize=6.5, color=COLORS["muted"], weight="bold")
    ax.text(0.025, 0.065, "输出：path + reason_codes\n+ actions + checks", fontsize=6.2, color=COLORS["muted"], va="top")
    ax.text(0.50, 0.07, "软先验只产生 score/core 标记，不参与数值正确性与 reject 判定", ha="center", fontsize=6.5, color=COLORS["ink"], weight="bold")
    save(fig, "figure4_3_checker")


def figure_4_4() -> None:
    rows = read_csv(PROJECT / "raw" / "transform_paths.csv")
    fig, ax = canvas(112)
    panel_label(ax, "a", 0.01, 0.98)
    columns = [(0.03, 0.17, "实例化参数"), (0.25, 0.20, "named_sequence"), (0.50, 0.20, "变换后关键证据"), (0.75, 0.22, "路径与实测")]
    for x, width, title in columns:
        ax.text(x + width / 2, 0.91, title, ha="center", fontsize=7, weight="bold", color=COLORS["ink"])
    y_positions = [0.66, 0.39, 0.12]
    face_for = {"direct": ("teal_light", "teal"), "adapt": ("orange_light", "orange"), "fallback": ("blue_light", "blue")}
    for row, y in zip(rows, y_positions):
        path = row["predicted_path"]
        face, edge = face_for[path]
        params = f"{path}\n{row['tile_m']}×{row['tile_n']}×{row['tile_k']}\npack={row['pack_mode']}, vect={row['vectorize']}"
        sequence = "match matmul\ntile_using_for\n" + ("vectorize children\n" if row["vectorize"] == "True" else "") + "one_shot_bufferize"
        if path == "adapt":
            evidence = "scf.for + affine.min\n有限 M/N/K 边界"
        elif path == "direct":
            evidence = "tiled/vectorized IR\nContract 条件满足"
        else:
            evidence = "generic tiled loops\n无匹配 Contract"
        result = (
            f"预测 {path}\n观测 {row['observed_path']}\n"
            f"PASS, {float(row['median_ms']):.3f} ms\n"
            f"{float(row['gflops']):.3f} GFLOP/s\nBLIS call={row['microkernel_replaced']}"
        )
        box(ax, 0.03, y, 0.17, 0.18, params, face, edge, fontsize=6.4, weight="bold")
        arrow(ax, (0.20, y + 0.09), (0.25, y + 0.09), edge)
        box(ax, 0.25, y, 0.20, 0.18, sequence, "neutral", "muted", fontsize=6.2)
        arrow(ax, (0.45, y + 0.09), (0.50, y + 0.09), edge)
        box(ax, 0.50, y, 0.20, 0.18, evidence, face, edge, fontsize=6.4)
        arrow(ax, (0.70, y + 0.09), (0.75, y + 0.09), edge)
        box(ax, 0.75, y, 0.22, 0.18, result, face, edge, fontsize=5.8)
    ax.text(0.5, 0.035, "路径预测来自 Checker；观测路径来自 LLVM IR 符号检查。当前模板未物化 BLIS packing/call。", ha="center", fontsize=6.5, color=COLORS["red"], weight="bold")
    save(fig, "figure4_4_transform_instantiation")


def figure_4_5() -> None:
    registry = json.loads((PROJECT / "processed" / "contract_registry.json").read_text(encoding="utf-8"))
    hashes = registry["import_sources"]
    fig, ax = canvas(94)
    panel_label(ax, "a", 0.01, 0.98)
    sources = [
        (0.03, 0.68, "BLIS Facts\nsource path/symbol", "neutral", "muted"),
        (0.03, 0.42, "Contract Registry\n" + hashes["contracts"]["sha256"][:10] + "…", "blue_light", "blue"),
        (0.03, 0.16, "Expert Rules\n" + hashes["rules"]["sha256"][:10] + "…", "blue_light", "blue"),
    ]
    for x, y, text, face, edge in sources:
        box(ax, x, y, 0.18, 0.16, text, face, edge, fontsize=6.4, weight="bold")
        arrow(ax, (0.21, y + 0.08), (0.29, 0.50), edge)
    box(ax, 0.29, 0.39, 0.18, 0.22, "Task Context\n+ Contract 选择日志\n+ source hashes", "blue_light", "blue", fontsize=6.6, weight="bold")
    arrow(ax, (0.47, 0.50), (0.54, 0.50), "teal")
    box(ax, 0.54, 0.36, 0.18, 0.28, "Candidate provenance\n\nFact IDs\nRule IDs\nreason_codes\nconditional params", "teal_light", "teal", fontsize=6.4, weight="bold")
    arrow(ax, (0.72, 0.50), (0.79, 0.50), "orange")
    outputs = "input/transformed\nMLIR\nLLVM IR + ELF\ncompile/correctness\nlog\nBaCO trace\nbest-so-far"
    box(ax, 0.79, 0.27, 0.18, 0.46, "可复核产物\n\n" + outputs, "orange_light", "orange", fontsize=5.9, weight="bold")
    ax.plot([0.29, 0.97], [0.16, 0.16], color=COLORS["muted"], linewidth=0.8, linestyle="--")
    ax.text(0.63, 0.11, "候选 ID 同时连接规则来源、路径判定、IR、测量值与调优迭代", ha="center", fontsize=6.8, color=COLORS["ink"], weight="bold")
    ax.text(0.63, 0.055, "source_cross_checked_pending_human_signoff 状态保持不变", ha="center", fontsize=6.2, color=COLORS["red"])
    save(fig, "figure4_5_provenance")


def qa() -> None:
    results = []
    for stem in (
        "figure4_1_framework",
        "figure4_2_spaces_and_paths",
        "figure4_3_checker",
        "figure4_4_transform_instantiation",
        "figure4_5_provenance",
    ):
        png = FIGURES / f"{stem}.png"
        svg = FIGURES / f"{stem}.svg"
        pdf = FIGURES / f"{stem}.pdf"
        tiff = FIGURES / f"{stem}.tiff"
        image = plt.imread(png)
        rgb = image[..., :3]
        nonwhite = float(np.mean(np.min(rgb, axis=2) < 0.98))
        svg_text = svg.read_text(encoding="utf-8")
        result = {
            "figure": stem,
            "png_width_px": int(image.shape[1]),
            "png_height_px": int(image.shape[0]),
            "nonwhite_fraction": round(nonwhite, 6),
            "svg_has_editable_text": "<text" in svg_text,
            "pdf_bytes": pdf.stat().st_size,
            "tiff_bytes": tiff.stat().st_size,
            "pass": nonwhite > 0.02 and "<text" in svg_text and pdf.stat().st_size > 1000 and tiff.stat().st_size > 1000,
        }
        results.append(result)
    report = {"backend": "Python/matplotlib", "all_pass": all(item["pass"] for item in results), "figures": results}
    (PROJECT / "reports" / "figure_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Chapter 4 Figure QA", "", "- Backend: Python/matplotlib only", f"- Automated checks: **{'PASS' if report['all_pass'] else 'FAIL'}**", ""]
    for item in results:
        lines.append(
            f"- `{item['figure']}`: {item['png_width_px']}×{item['png_height_px']} px preview, "
            f"nonwhite={item['nonwhite_fraction']:.3f}, editable SVG text={item['svg_has_editable_text']}"
        )
    lines.extend(["", "Quantitative panels use deterministic enumeration or single-run smoke measurements; no inferential statistics are claimed.", ""])
    (PROJECT / "reports" / "figure_qa.md").write_text("\n".join(lines), encoding="utf-8")
    if not report["all_pass"]:
        raise RuntimeError("figure QA failed")


def main() -> None:
    figure_4_1()
    figure_4_2()
    figure_4_3()
    figure_4_4()
    figure_4_5()
    qa()
    print(f"wrote figures and QA to {FIGURES}")


if __name__ == "__main__":
    main()
