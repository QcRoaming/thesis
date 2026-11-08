#!/usr/bin/env python3
"""Generate the eleven figures used in thesis Chapters 1-4."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import pandas as pd
from PIL import Image
import seaborn as sns


HERE = Path(__file__).resolve().parent
THESIS_ROOT = HERE.parents[1]
FONT_PATH = THESIS_ROOT / "fonts" / "simhei.ttf"
NORMALIZATION_DATA = HERE / "source_data_chapter4_parameter_normalization.csv"

if not FONT_PATH.is_file():
    raise FileNotFoundError(f"Chinese font not found: {FONT_PATH}")

font_manager.fontManager.addfont(FONT_PATH)
FONT_NAME = font_manager.FontProperties(fname=FONT_PATH).get_name()

sns.set_theme(context="paper", style="white", font=FONT_NAME)
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [FONT_NAME, "Arial", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


INK = "#1F2937"
MUTED = "#64748B"
BORDER = "#8A99A8"
GRID = "#D7DEE7"
NEUTRAL = "#F3F5F7"
NEUTRAL_2 = "#E7EBF0"
BLUE = "#4C78A8"
BLUE_DARK = "#315D86"
BLUE_LIGHT = "#DCE8F5"
TEAL = "#2A9D8F"
TEAL_DARK = "#1F776D"
TEAL_LIGHT = "#DDF3EF"
ORANGE = "#D8872D"
ORANGE_LIGHT = "#F8E8D4"
PURPLE = "#7566AE"
PURPLE_LIGHT = "#ECE8F6"
RED = "#C8555A"
RED_LIGHT = "#F6DDDF"
GREEN = "#5B936A"
GREEN_LIGHT = "#E1F0E5"


def canvas(width: float, height: float):
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def rounded_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    face: str = "white",
    edge: str = BORDER,
    linewidth: float = 1.0,
    radius: float = 0.018,
    linestyle: str = "-",
    zorder: int = 1,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def label(
    ax,
    x: float,
    y: float,
    value: str,
    *,
    size: float = 8.5,
    color: str = INK,
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    family: str | None = None,
    rotation: float = 0,
    zorder: int = 5,
):
    return ax.text(
        x,
        y,
        value,
        fontsize=size,
        color=color,
        fontweight=weight,
        ha=ha,
        va=va,
        fontfamily=family,
        rotation=rotation,
        zorder=zorder,
    )


def arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = MUTED,
    linewidth: float = 1.15,
    style: str = "-|>",
    mutation_scale: float = 10,
    connectionstyle: str = "arc3,rad=0",
    zorder: int = 3,
):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=mutation_scale,
        linewidth=linewidth,
        color=color,
        connectionstyle=connectionstyle,
        shrinkA=0,
        shrinkB=0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def chip(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    face: str,
    edge: str,
    color: str = INK,
    size: float = 7.2,
    weight: str = "normal",
):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        face=face,
        edge=edge,
        linewidth=0.9,
        radius=min(h * 0.24, 0.018),
    )
    label(ax, x + w / 2, y + h / 2, text, size=size, color=color, weight=weight)


def panel_label(ax, x: float, y: float, value: str):
    label(ax, x, y, value, size=10.5, weight="bold", ha="left", va="top")


def matrix_grid(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    rows: int,
    cols: int,
    *,
    base_face: str = "white",
    edge: str = GRID,
    highlight: Callable[[int, int], str | None] | None = None,
    hatch: Callable[[int, int], str | None] | None = None,
    linewidth: float = 0.55,
):
    cell_w = w / cols
    cell_h = h / rows
    for row in range(rows):
        for col in range(cols):
            color = highlight(row, col) if highlight else None
            hatch_value = hatch(row, col) if hatch else None
            rect = Rectangle(
                (x + col * cell_w, y + (rows - 1 - row) * cell_h),
                cell_w,
                cell_h,
                facecolor=color or base_face,
                edgecolor=edge,
                linewidth=linewidth,
                hatch=hatch_value,
                zorder=2,
            )
            ax.add_patch(rect)
    ax.add_patch(
        Rectangle(
            (x, y),
            w,
            h,
            facecolor="none",
            edgecolor=BORDER,
            linewidth=0.9,
            zorder=3,
        )
    )


def section_header(ax, x: float, y: float, w: float, title: str, color: str):
    ax.plot([x, x + w], [y, y], color=color, linewidth=2.1, solid_capstyle="round")
    label(ax, x, y + 0.028, title, size=8.8, color=color, weight="bold", ha="left")


def save_figure(fig, stem: str):
    base = HERE / stem
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        base.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.03,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    fig.savefig(
        base.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def decision_diamond(
    ax,
    cx: float,
    cy: float,
    w: float,
    h: float,
    text: str,
    *,
    face: str = "white",
    edge: str = BORDER,
    color: str = INK,
    size: float = 7.0,
):
    patch = Polygon(
        [
            (cx, cy + h / 2),
            (cx + w / 2, cy),
            (cx, cy - h / 2),
            (cx - w / 2, cy),
        ],
        closed=True,
        facecolor=face,
        edgecolor=edge,
        linewidth=1.0,
        zorder=2,
    )
    ax.add_patch(patch)
    label(ax, cx, cy, text, size=size, color=color, weight="bold", zorder=4)
    return patch


def figure_1_1():
    fig, ax = canvas(7.2, 3.9)

    section_header(ax, 0.03, 0.92, 0.22, "调度语义", BLUE_DARK)
    section_header(ax, 0.305, 0.92, 0.31, "外部实现可接纳性", PURPLE)
    section_header(ax, 0.675, 0.92, 0.295, "生成路径", TEAL_DARK)

    rounded_box(ax, 0.035, 0.67, 0.205, 0.15, face=BLUE_LIGHT, edge=BLUE, radius=0.014)
    label(ax, 0.1375, 0.775, "Transform schedule", size=8.0, color=BLUE_DARK, weight="bold")
    label(ax, 0.1375, 0.715, "tile · pack · vectorize", size=6.7, family="DejaVu Sans Mono")
    rounded_box(ax, 0.035, 0.48, 0.205, 0.13, face=NEUTRAL, edge=BORDER, radius=0.014)
    label(ax, 0.1375, 0.565, "payload IR", size=7.8, weight="bold")
    label(ax, 0.1375, 0.515, "GEMM task · dtype · shape", size=6.5, family="DejaVu Sans")

    rounded_box(ax, 0.065, 0.275, 0.145, 0.12, face="white", edge=BLUE, radius=0.014)
    label(ax, 0.1375, 0.355, "L1 语义检查", size=7.6, color=BLUE_DARK, weight="bold")
    label(ax, 0.1375, 0.31, "verifier · compile", size=6.5, family="DejaVu Sans")
    arrow(ax, (0.1375, 0.48), (0.1375, 0.395), color=BLUE)
    arrow(ax, (0.21, 0.335), (0.305, 0.52), color=BLUE, connectionstyle="arc3,rad=-0.12")
    label(ax, 0.255, 0.445, "合法", size=6.3, color=BLUE_DARK, weight="bold")

    rounded_box(ax, 0.305, 0.33, 0.31, 0.49, face=PURPLE_LIGHT, edge=PURPLE, radius=0.018)
    label(ax, 0.46, 0.77, "Microkernel Admissibility Contract", size=8.2, color=PURPLE, weight="bold")
    label(ax, 0.46, 0.725, "特定微内核、目标与版本", size=6.6, color=MUTED)
    chip(ax, 0.33, 0.625, 0.12, 0.062, "dtype · ISA", face="white", edge=BLUE, size=6.4)
    chip(ax, 0.465, 0.625, 0.125, 0.062, "MR/NR · K", face="white", edge=BLUE, size=6.4)
    chip(ax, 0.33, 0.545, 0.12, 0.062, "layout · stride", face="white", edge=BLUE, size=6.2)
    chip(ax, 0.465, 0.545, 0.125, 0.062, "packing · ABI", face="white", edge=BLUE, size=6.2)
    rounded_box(ax, 0.33, 0.445, 0.26, 0.07, face=TEAL_LIGHT, edge=TEAL, radius=0.011)
    label(ax, 0.46, 0.48, "declared adapter capabilities", size=6.4, color=TEAL_DARK, weight="bold")
    rounded_box(ax, 0.33, 0.355, 0.26, 0.06, face=ORANGE_LIGHT, edge=ORANGE, radius=0.011)
    label(ax, 0.46, 0.385, "safe fallback availability", size=6.3, color=ORANGE, weight="bold")

    route_cards = [
        (0.68, 0.63, "direct", "常规 packing / wrapper\n调用目标微内核", GREEN_LIGHT, GREEN),
        (0.835, 0.63, "adapt", "有限补齐或 fringe\n再调用目标微内核", TEAL_LIGHT, TEAL),
        (0.68, 0.43, "fallback", "通用 lowering 或\n完整库安全路径", ORANGE_LIGHT, ORANGE),
        (0.835, 0.43, "reject", "执行前停止\n保留字段级诊断", RED_LIGHT, RED),
    ]
    for x, y, title, body, face, edge in route_cards:
        rounded_box(ax, x, y, 0.135, 0.155, face=face, edge=edge, radius=0.013)
        label(ax, x + 0.0675, y + 0.113, title, size=7.5, color=edge, weight="bold", family="DejaVu Sans")
        label(ax, x + 0.0675, y + 0.052, body, size=6.0, color=INK)

    arrow(ax, (0.615, 0.58), (0.68, 0.707), color=GREEN, connectionstyle="arc3,rad=0.10")
    arrow(ax, (0.615, 0.58), (0.835, 0.707), color=TEAL, connectionstyle="arc3,rad=-0.14")
    arrow(ax, (0.615, 0.53), (0.68, 0.507), color=ORANGE, connectionstyle="arc3,rad=0.08")
    arrow(ax, (0.615, 0.48), (0.835, 0.507), color=RED, connectionstyle="arc3,rad=0.10")

    ax.plot([0.1375, 0.1375, 0.815], [0.275, 0.235, 0.235], color=RED, linewidth=0.9, linestyle=(0, (3, 3)))
    arrow(ax, (0.815, 0.235), (0.9025, 0.43), color=RED, linewidth=0.9, connectionstyle="arc3,rad=-0.08")
    label(ax, 0.225, 0.245, "L1 非法", size=6.1, color=RED, weight="bold")

    rounded_box(ax, 0.035, 0.055, 0.93, 0.12, face=NEUTRAL, edge=GRID, radius=0.014)
    label(ax, 0.065, 0.115, "L1", size=7.0, color=BLUE_DARK, weight="bold")
    label(ax, 0.105, 0.115, "结果是否保持语义", size=6.6, ha="left")
    arrow(ax, (0.285, 0.115), (0.335, 0.115), color=MUTED, mutation_scale=8)
    label(ax, 0.36, 0.115, "L2", size=7.0, color=PURPLE, weight="bold")
    label(ax, 0.40, 0.115, "指定实现能否安全接入", size=6.6, ha="left")
    arrow(ax, (0.61, 0.115), (0.66, 0.115), color=MUTED, mutation_scale=8)
    label(ax, 0.685, 0.115, "L3", size=7.0, color=ORANGE, weight="bold")
    label(ax, 0.725, 0.115, "只在可运行路径中测量排序", size=6.5, ha="left")

    save_figure(fig, "chapter1_microkernel_admissibility_problem")


def figure_1_2():
    fig, ax = canvas(7.2, 4.2)

    phases = [
        (0.025, "01", "固定来源证据", "配置与源码\npacking / call / ABI\nrevision · hash", BLUE_LIGHT, BLUE),
        (0.22, "02", "构造知识对象", "Fact\nContract / Profile\nUnresolved", PURPLE_LIGHT, PURPLE),
        (0.415, "03", "编译候选空间", "约束传播与分类\n参数活性分析\n规范化 / 去重", TEAL_LIGHT, TEAL),
        (0.61, "04", "物化真实执行", "Transform 调度\npacking / adapter\nLLVM · binary · checks", ORANGE_LIGHT, ORANGE),
        (0.805, "05", "评价与决策", "RQ1 接纳安全\nRQ2 空间质量\nRQ3 迁移 · RQ4 经济性", NEUTRAL, BORDER),
    ]
    for x, code, title, body, face, edge in phases:
        rounded_box(ax, x, 0.385, 0.17, 0.47, face=face, edge=edge, radius=0.017)
        rounded_box(ax, x + 0.012, 0.785, 0.045, 0.05, face=edge, edge=edge, radius=0.01)
        label(ax, x + 0.0345, 0.81, code, size=6.8, color="white", weight="bold", family="DejaVu Sans")
        label(ax, x + 0.085, 0.735, title, size=8.0, color=edge, weight="bold")
        ax.plot([x + 0.025, x + 0.145], [0.685, 0.685], color=edge, linewidth=0.8, alpha=0.7)
        label(ax, x + 0.085, 0.555, body, size=6.5, color=INK)
        if code == "05":
            rounded_box(ax, x + 0.025, 0.415, 0.12, 0.065, face=GREEN_LIGHT, edge=GREEN, radius=0.01)
            label(ax, x + 0.085, 0.4475, "部署：完整库或搜索", size=5.9, color=GREEN, weight="bold")

    for x0, x1, color in [(0.195, 0.22, BLUE), (0.39, 0.415, PURPLE), (0.585, 0.61, TEAL), (0.78, 0.805, ORANGE)]:
        arrow(ax, (x0, 0.62), (x1, 0.62), color=color, mutation_scale=8)

    rounded_box(ax, 0.21, 0.205, 0.745, 0.105, face=PURPLE_LIGHT, edge=PURPLE, radius=0.014)
    label(ax, 0.235, 0.258, "目标测量反馈", size=6.7, color=PURPLE, weight="bold", ha="left")
    label(ax, 0.39, 0.258, "校准排序与成本", size=6.5, ha="left")
    arrow(ax, (0.57, 0.258), (0.635, 0.258), color=PURPLE, mutation_scale=8)
    label(ax, 0.66, 0.258, "只更新 Performance Profile", size=6.5, color=PURPLE, weight="bold", ha="left")
    ax.plot([0.89, 0.89, 0.305], [0.385, 0.325, 0.325], color=PURPLE, linewidth=1.0)
    arrow(ax, (0.305, 0.325), (0.305, 0.385), color=PURPLE, mutation_scale=8)

    rounded_box(ax, 0.025, 0.055, 0.93, 0.095, face=ORANGE_LIGHT, edge=ORANGE, radius=0.014)
    label(ax, 0.05, 0.1025, "来源版本变化", size=6.7, color=ORANGE, weight="bold", ha="left")
    arrow(ax, (0.20, 0.1025), (0.265, 0.1025), color=ORANGE, mutation_scale=8)
    label(ax, 0.29, 0.1025, "相关对象 stale", size=6.5, ha="left")
    arrow(ax, (0.43, 0.1025), (0.495, 0.1025), color=ORANGE, mutation_scale=8)
    label(ax, 0.52, 0.1025, "重新提取、字段检查与签核；历史实验保持原 revision", size=6.4, ha="left")

    label(ax, 0.025, 0.925, "证据 → 知识 → 空间 → 执行 → 评价", size=9.0, color=INK, weight="bold", ha="left")
    label(ax, 0.975, 0.925, "两类反馈分别受硬/软边界约束", size=6.7, color=MUTED, ha="right")

    save_figure(fig, "chapter1_research_route")


def figure_2_1():
    fig, ax = canvas(7.2, 3.9)

    section_header(ax, 0.035, 0.91, 0.205, "原始矩阵与宏观块", BLUE_DARK)
    section_header(ax, 0.295, 0.91, 0.31, "缓存分块与 packing", TEAL_DARK)
    section_header(ax, 0.665, 0.91, 0.30, "微内核调用边界", PURPLE)

    label(ax, 0.075, 0.83, "A", size=9.0, weight="bold")
    matrix_grid(
        ax,
        0.035,
        0.58,
        0.095,
        0.21,
        5,
        4,
        highlight=lambda r, c: BLUE_LIGHT if (1 <= r <= 3 and 1 <= c <= 2) else None,
    )
    label(ax, 0.187, 0.83, "B", size=9.0, weight="bold")
    matrix_grid(
        ax,
        0.145,
        0.58,
        0.095,
        0.21,
        4,
        5,
        highlight=lambda r, c: TEAL_LIGHT if (1 <= r <= 2 and 1 <= c <= 3) else None,
    )
    label(ax, 0.055, 0.50, "C", size=9.0, weight="bold")
    matrix_grid(
        ax,
        0.078,
        0.28,
        0.12,
        0.20,
        5,
        5,
        highlight=lambda r, c: PURPLE_LIGHT if (1 <= r <= 3 and 1 <= c <= 3) else None,
    )
    label(ax, 0.0825, 0.515, "M × K", size=6.9, color=MUTED)
    label(ax, 0.1925, 0.515, "K × N", size=6.9, color=MUTED)
    label(ax, 0.138, 0.245, "M × N", size=6.9, color=MUTED)

    rounded_box(ax, 0.295, 0.64, 0.135, 0.16, face=BLUE_LIGHT, edge=BLUE)
    label(ax, 0.3625, 0.74, "A 宏观块", size=8.0, weight="bold", color=BLUE_DARK)
    label(ax, 0.3625, 0.685, "MC × KC", size=7.5, family="DejaVu Sans Mono")
    rounded_box(ax, 0.455, 0.64, 0.15, 0.16, face=TEAL_LIGHT, edge=TEAL)
    label(ax, 0.53, 0.74, "B 宏观面板", size=8.0, weight="bold", color=TEAL_DARK)
    label(ax, 0.53, 0.685, "KC × NC", size=7.5, family="DejaVu Sans Mono")

    label(ax, 0.4425, 0.72, "×", size=9.0, color=MUTED, weight="bold")

    label(ax, 0.38, 0.565, "packed A panel", size=7.2, color=BLUE_DARK)
    for i in range(4):
        ax.add_patch(
            Rectangle(
                (0.30 + i * 0.035, 0.34),
                0.029,
                0.18,
                facecolor=BLUE_LIGHT if i % 2 == 0 else "#C7D9EE",
                edgecolor="white",
                linewidth=0.5,
            )
        )
    rounded_box(ax, 0.292, 0.325, 0.153, 0.21, face="none", edge=BLUE, radius=0.01)
    label(ax, 0.368, 0.30, "micro-panels：MR × KC", size=6.8, color=MUTED)

    label(ax, 0.53, 0.565, "packed B panel", size=7.2, color=TEAL_DARK)
    for i in range(5):
        ax.add_patch(
            Rectangle(
                (0.468, 0.34 + i * 0.035),
                0.124,
                0.029,
                facecolor=TEAL_LIGHT if i % 2 == 0 else "#C5E8E2",
                edgecolor="white",
                linewidth=0.5,
            )
        )
    rounded_box(ax, 0.46, 0.325, 0.145, 0.21, face="none", edge=TEAL, radius=0.01)
    label(ax, 0.532, 0.30, "micro-panels：KC × NR", size=6.8, color=MUTED)

    ax.plot(
        [0.0825, 0.0825, 0.26],
        [0.58, 0.555, 0.555],
        color=BLUE,
        linewidth=1.1,
        solid_capstyle="round",
    )
    arrow(ax, (0.26, 0.555), (0.315, 0.64), color=BLUE)
    ax.plot(
        [0.24, 0.24, 0.43],
        [0.76, 0.845, 0.845],
        color=TEAL,
        linewidth=1.1,
        solid_capstyle="round",
    )
    arrow(ax, (0.43, 0.845), (0.48, 0.80), color=TEAL)

    rounded_box(ax, 0.665, 0.58, 0.09, 0.16, face=BLUE_LIGHT, edge=BLUE)
    label(ax, 0.71, 0.69, "Aμ", size=8.1, weight="bold", color=BLUE_DARK)
    label(ax, 0.71, 0.63, "MR × Kc", size=6.8, family="DejaVu Sans Mono")
    rounded_box(ax, 0.775, 0.58, 0.09, 0.16, face=TEAL_LIGHT, edge=TEAL)
    label(ax, 0.82, 0.69, "Bμ", size=8.1, weight="bold", color=TEAL_DARK)
    label(ax, 0.82, 0.63, "Kc × NR", size=6.8, family="DejaVu Sans Mono")
    rounded_box(ax, 0.705, 0.36, 0.12, 0.13, face=PURPLE_LIGHT, edge=PURPLE)
    label(ax, 0.765, 0.445, "microkernel", size=7.8, weight="bold", color=PURPLE)
    label(ax, 0.765, 0.395, "K-step / actual K", size=6.6, color=MUTED)
    arrow(ax, (0.71, 0.58), (0.738, 0.49), color=BLUE)
    arrow(ax, (0.82, 0.58), (0.792, 0.49), color=TEAL)

    matrix_grid(
        ax,
        0.855,
        0.32,
        0.10,
        0.21,
        4,
        5,
        highlight=lambda r, c: PURPLE_LIGHT,
    )
    label(ax, 0.905, 0.56, "C tile", size=7.8, weight="bold", color=PURPLE)
    label(ax, 0.905, 0.275, "MR × NR", size=6.8, family="DejaVu Sans Mono")
    arrow(ax, (0.825, 0.425), (0.855, 0.425), color=PURPLE)

    arrow(ax, (0.445, 0.49), (0.665, 0.66), color=BLUE, connectionstyle="arc3,rad=-0.12")
    arrow(ax, (0.605, 0.49), (0.775, 0.66), color=TEAL, connectionstyle="arc3,rad=-0.12")
    label(ax, 0.61, 0.575, "panel order / stride", size=6.1, color=MUTED)

    rounded_box(ax, 0.055, 0.055, 0.89, 0.125, face=NEUTRAL, edge=GRID, radius=0.015)
    label(ax, 0.075, 0.117, "调用方义务", size=7.7, weight="bold", ha="left", color=INK)
    chip(ax, 0.185, 0.083, 0.175, 0.065, "panel order · stride · alignment", face=BLUE_LIGHT, edge=BLUE, size=6.5)
    chip(ax, 0.375, 0.083, 0.13, 0.065, "M/N tail", face=ORANGE_LIGHT, edge=ORANGE, size=6.8)
    chip(ax, 0.52, 0.083, 0.17, 0.065, "K remainder · actual K", face=TEAL_LIGHT, edge=TEAL, size=6.5)
    chip(ax, 0.705, 0.083, 0.205, 0.065, "α/β · aux · callee ABI", face=PURPLE_LIGHT, edge=PURPLE, size=6.5)

    save_figure(fig, "chapter2_gemm_layers_microkernel_interface")


def figure_2_2():
    fig, ax = canvas(6.4, 3.7)

    layers = [
        {
            "y": 0.67,
            "code": "L3",
            "title": "性能与经济性",
            "face": PURPLE_LIGHT,
            "edge": PURPLE,
            "inputs": "C 空间 · 目标测量\n完整库 · 搜索成本 · H",
            "checks": "排序、搜索与摊销",
            "outputs": "D90 / T90 / Rlib\nV 的 95% 单侧下界",
        },
        {
            "y": 0.39,
            "code": "L2",
            "title": "实现可接纳性",
            "face": BLUE_LIGHT,
            "edge": BLUE,
            "inputs": "Contract · target · candidate\npacking · tail · ABI",
            "checks": "Compatibility Checker\n与 adapter 能力",
            "outputs": "direct / adapt\nfallback / reject",
        },
        {
            "y": 0.11,
            "code": "L1",
            "title": "语义合法性",
            "face": NEUTRAL,
            "edge": BORDER,
            "inputs": "payload IR · Transform IR",
            "checks": "verifier · compile\n数值 reference",
            "outputs": "语义保持\n或程序非法",
        },
    ]

    for layer in layers:
        y = layer["y"]
        rounded_box(ax, 0.095, y, 0.85, 0.215, face=layer["face"], edge=layer["edge"], radius=0.018)
        rounded_box(ax, 0.025, y + 0.044, 0.075, 0.13, face=layer["edge"], edge=layer["edge"], radius=0.014)
        label(ax, 0.0625, y + 0.109, layer["code"], size=10.2, color="white", weight="bold")
        label(ax, 0.125, y + 0.169, layer["title"], size=8.7, weight="bold", color=layer["edge"], ha="left")

        cards = [
            (0.125, 0.235, "输入", layer["inputs"]),
            (0.40, 0.225, "判定", layer["checks"]),
            (0.665, 0.245, "输出", layer["outputs"]),
        ]
        for x, w, head, body in cards:
            rounded_box(ax, x, y + 0.028, w, 0.118, face="white", edge=GRID, linewidth=0.8, radius=0.012)
            label(ax, x + 0.012, y + 0.126, head, size=6.6, color=MUTED, weight="bold", ha="left")
            label(ax, x + w / 2, y + 0.072, body, size=6.8, color=INK)
        arrow(ax, (0.36, y + 0.087), (0.395, y + 0.087), color=layer["edge"], mutation_scale=8)
        arrow(ax, (0.63, y + 0.087), (0.66, y + 0.087), color=layer["edge"], mutation_scale=8)

    rounded_box(ax, 0.16, 0.015, 0.72, 0.07, face=RED_LIGHT, edge=RED, radius=0.012)
    label(
        ax,
        0.52,
        0.05,
        "上层只消费下层已通过的对象，不能修改或替代下层判定",
        size=7.0,
        color=RED,
        weight="bold",
    )

    save_figure(fig, "chapter2_three_layer_boundary")


def figure_3_1():
    fig, ax = canvas(7.2, 4.2)

    section_header(ax, 0.025, 0.92, 0.17, "固定来源", BLUE_DARK)
    section_header(ax, 0.235, 0.92, 0.18, "字段级 Fact", PURPLE)
    section_header(ax, 0.455, 0.92, 0.205, "规范化与核验", TEAL_DARK)
    section_header(ax, 0.705, 0.92, 0.27, "分流后的知识对象", ORANGE)

    sources = [
        (0.72, "配置与上下文", "dtype · ISA · MR/NR"),
        (0.56, "内核、packing 与调用", "panel · stride · tail · ABI"),
        (0.40, "构建与目标文件", "flags · symbol · object hash"),
        (0.24, "运行探针与文档", "observed path · counters"),
    ]
    for y, title, body in sources:
        rounded_box(ax, 0.025, y, 0.17, 0.12, face=BLUE_LIGHT, edge=BLUE, radius=0.012)
        label(ax, 0.11, y + 0.082, title, size=6.8, color=BLUE_DARK, weight="bold")
        label(ax, 0.11, y + 0.036, body, size=5.8, family="DejaVu Sans")
        arrow(ax, (0.195, y + 0.06), (0.235, 0.55), color=BLUE, mutation_scale=7, connectionstyle="arc3,rad=0.05")

    rounded_box(ax, 0.235, 0.24, 0.18, 0.60, face=PURPLE_LIGHT, edge=PURPLE, radius=0.016)
    label(ax, 0.325, 0.79, "Fact record", size=8.0, color=PURPLE, weight="bold", family="DejaVu Sans")
    fact_fields = ["raw / normalized value", "scope · backend · dtype", "source location · revision", "file / object hash", "evidence type · status"]
    for index, value in enumerate(fact_fields):
        rounded_box(ax, 0.257, 0.685 - index * 0.084, 0.136, 0.058, face="white", edge=GRID, radius=0.009)
        label(ax, 0.325, 0.714 - index * 0.084, value, size=5.8, family="DejaVu Sans")
    label(ax, 0.325, 0.275, "Fact 不直接作接纳判断", size=6.1, color=MUTED, weight="bold")

    rounded_box(ax, 0.455, 0.24, 0.205, 0.60, face=TEAL_LIGHT, edge=TEAL, radius=0.016)
    audit_steps = [
        (0.70, "① 归一化", "单位、枚举、适用范围"),
        (0.57, "② 冲突处理", "并列来源，不求跨库平均值"),
        (0.44, "③ 机器检查", "schema · path · type · hash"),
        (0.31, "④ 作者签核", "复核证据与消费边界"),
    ]
    for y, title, body in audit_steps:
        rounded_box(ax, 0.478, y, 0.159, 0.10, face="white", edge=TEAL, radius=0.01)
        label(ax, 0.5575, y + 0.067, title, size=6.7, color=TEAL_DARK, weight="bold")
        label(ax, 0.5575, y + 0.027, body, size=5.7)
    for y0, y1 in [(0.70, 0.67), (0.57, 0.54), (0.44, 0.41)]:
        arrow(ax, (0.5575, y0), (0.5575, y1), color=TEAL, mutation_scale=7)
    arrow(ax, (0.415, 0.55), (0.455, 0.55), color=PURPLE, mutation_scale=8)

    outputs = [
        (0.66, "Contract", "核验后的硬调用条件\n+ adapter / fallback 能力", BLUE_LIGHT, BLUE),
        (0.46, "Performance Profile", "带来源、可校准、可撤销\n只影响候选排序", PURPLE_LIGHT, PURPLE),
        (0.26, "Unresolved", "冲突、歧义或证据不足\n阻止字段自动消费", NEUTRAL, BORDER),
    ]
    for y, title, body, face, edge in outputs:
        rounded_box(ax, 0.705, y, 0.27, 0.15, face=face, edge=edge, radius=0.014)
        label(ax, 0.84, y + 0.105, title, size=7.2, color=edge, weight="bold", family="DejaVu Sans")
        label(ax, 0.84, y + 0.047, body, size=6.0)
        arrow(ax, (0.66, 0.55), (0.705, y + 0.075), color=edge, mutation_scale=8, connectionstyle="arc3,rad=0.05")

    rounded_box(ax, 0.235, 0.055, 0.74, 0.105, face=NEUTRAL, edge=GRID, radius=0.013)
    label(ax, 0.255, 0.1075, "消费边界", size=6.7, color=INK, weight="bold", ha="left")
    chip(ax, 0.35, 0.077, 0.17, 0.06, "Contract → checker", face=BLUE_LIGHT, edge=BLUE, size=6.1)
    chip(ax, 0.535, 0.077, 0.20, 0.06, "Profile → rank / sample", face=PURPLE_LIGHT, edge=PURPLE, size=6.0)
    chip(ax, 0.75, 0.077, 0.20, 0.06, "Unresolved → block", face="white", edge=BORDER, size=6.1)

    save_figure(fig, "chapter3_source_fact_contract_pipeline")


def figure_3_2():
    fig, ax = canvas(7.0, 4.3)

    rounded_box(ax, 0.035, 0.86, 0.93, 0.10, face=NEUTRAL, edge=BORDER, radius=0.014)
    label(ax, 0.065, 0.91, "Contract identity", size=7.0, color=MUTED, weight="bold", ha="left")
    label(
        ax,
        0.215,
        0.91,
        "Ck = ⟨id, semantics, target, tile, memory, boundary, ABI, adapter, fallback, validity, provenance⟩",
        size=7.1,
        family="DejaVu Sans",
        ha="left",
    )

    cards = [
        ("语义", "operation · dtype\nα / β · C 初值", BLUE_LIGHT, BLUE),
        ("目标", "machine · ISA\nfeatures · target ABI", BLUE_LIGHT, BLUE),
        ("寄存器块", "MR / NR · K-step\nremainder 行为", BLUE_LIGHT, BLUE),
        ("布局与内存", "layout · stride\nalignment · C order", BLUE_LIGHT, BLUE),
        ("Packing", "required · schema\npanel order/stride · packer", BLUE_LIGHT, BLUE),
        ("边界", "M/N/K tail · β mode\ntemporary C · scatter", BLUE_LIGHT, BLUE),
        ("调用 ABI", "callee · 参数次序\nauxiliary · C update", BLUE_LIGHT, BLUE),
        ("适配与退化", "capabilities · actions\nfallback · safe guard", TEAL_LIGHT, TEAL),
        ("版本有效性", "revision · source hash\nschema / adapter version\nstale rule", NEUTRAL, BORDER),
        ("证据与诊断", "source · check phase\nfield · reason\nprovenance", PURPLE_LIGHT, PURPLE),
    ]

    xs = [0.03, 0.222, 0.414, 0.606, 0.798]
    ys = [0.57, 0.31]
    for index, (title, body, face, edge) in enumerate(cards):
        row = index // 5
        col = index % 5
        x = xs[col]
        y = ys[row]
        rounded_box(ax, x, y, 0.172, 0.205, face=face, edge=edge, radius=0.014)
        label(ax, x + 0.086, y + 0.158, title, size=8.1, color=edge, weight="bold")
        ax.plot([x + 0.025, x + 0.147], [y + 0.128, y + 0.128], color=edge, linewidth=0.8, alpha=0.7)
        label(ax, x + 0.086, y + 0.071, body, size=5.9 if index >= 8 else 6.4, color=INK)

    label(ax, 0.05, 0.815, "字段类型", size=6.8, color=MUTED, weight="bold", ha="left")
    chip(ax, 0.13, 0.79, 0.13, 0.05, "硬调用条件", face=BLUE_LIGHT, edge=BLUE, size=6.5)
    chip(ax, 0.275, 0.79, 0.15, 0.05, "执行能力", face=TEAL_LIGHT, edge=TEAL, size=6.5)
    chip(ax, 0.44, 0.79, 0.16, 0.05, "证据与有效性", face=PURPLE_LIGHT, edge=PURPLE, size=6.5)

    rounded_box(ax, 0.045, 0.075, 0.91, 0.145, face="white", edge=GRID, radius=0.014)
    label(ax, 0.065, 0.175, "字段级消费接口", size=7.4, weight="bold", ha="left", color=INK)
    label(
        ax,
        0.065,
        0.118,
        "Check(T, q, Ck) → ⟨decision, phase, first_field, reason, obligations, provenance⟩",
        size=6.8,
        ha="left",
        family="DejaVu Sans",
    )
    chip(ax, 0.615, 0.105, 0.075, 0.065, "direct", face=GREEN_LIGHT, edge=GREEN, size=6.7, weight="bold")
    chip(ax, 0.702, 0.105, 0.075, 0.065, "adapt", face=TEAL_LIGHT, edge=TEAL, size=6.7, weight="bold")
    chip(ax, 0.789, 0.105, 0.085, 0.065, "fallback", face=ORANGE_LIGHT, edge=ORANGE, size=6.5, weight="bold")
    chip(ax, 0.886, 0.105, 0.055, 0.065, "reject", face=RED_LIGHT, edge=RED, size=6.3, weight="bold")
    arrow(ax, (0.884, 0.31), (0.884, 0.22), color=PURPLE, mutation_scale=8)

    label(
        ax,
        0.5,
        0.025,
        "结构分组可复用；具体字段值、packing schema 与二进制 ABI 仍由微内核包分别给出",
        size=6.8,
        color=MUTED,
    )

    save_figure(fig, "chapter3_microkernel_contract_schema")


def figure_3_3():
    fig, ax = canvas(7.0, 3.8)

    label(ax, 0.03, 0.95, "依赖指纹驱动的版本生命周期", size=8.8, weight="bold", ha="left")
    label(ax, 0.97, 0.95, "状态转换可自动触发；Contract 签核不可自动完成", size=6.5, color=MUTED, ha="right")

    top_cards = [
        (0.03, "① verified revision", "Contract + Facts\n当前可被消费", GREEN_LIGHT, GREEN),
        (0.27, "② dependency fingerprint", "source revision / hash\nschema · generator · adapter", BLUE_LIGHT, BLUE),
        (0.51, "③ change detected", "任一依赖值变化\n记录 affected fields", ORANGE_LIGHT, ORANGE),
        (0.75, "④ stale / quarantine", "保留审计读取\n禁用 direct / adapt 生成", RED_LIGHT, RED),
    ]
    for x, title, body, face, edge in top_cards:
        rounded_box(ax, x, 0.645, 0.20, 0.21, face=face, edge=edge, radius=0.014)
        label(ax, x + 0.10, 0.805, title, size=6.8, color=edge, weight="bold", family="DejaVu Sans")
        label(ax, x + 0.10, 0.715, body, size=6.0)
    for x0, x1, color in [(0.23, 0.27, GREEN), (0.47, 0.51, BLUE), (0.71, 0.75, ORANGE)]:
        arrow(ax, (x0, 0.75), (x1, 0.75), color=color, mutation_scale=8)

    bottom_cards = [
        (0.75, "⑤ 影响分析与重提取", "定位依赖字段\n从新 revision 恢复 Fact", NEUTRAL, BORDER),
        (0.51, "⑥ 重新核验", "字段检查 · 冲突复核\nadapter / fallback 验证", PURPLE_LIGHT, PURPLE),
        (0.27, "⑦ 作者签核", "确认来源、适用范围\n与消费动作", BLUE_LIGHT, BLUE),
        (0.03, "⑧ new verified revision", "生成新对象版本\n旧版本保持可追溯", GREEN_LIGHT, GREEN),
    ]
    for x, title, body, face, edge in bottom_cards:
        rounded_box(ax, x, 0.325, 0.20, 0.21, face=face, edge=edge, radius=0.014)
        label(ax, x + 0.10, 0.485, title, size=6.7, color=edge, weight="bold")
        label(ax, x + 0.10, 0.395, body, size=5.9)
    arrow(ax, (0.85, 0.645), (0.85, 0.535), color=RED, mutation_scale=8)
    for x0, x1, color in [(0.75, 0.71, BORDER), (0.51, 0.47, PURPLE), (0.27, 0.23, BLUE)]:
        arrow(ax, (x0, 0.43), (x1, 0.43), color=color, mutation_scale=8)

    rounded_box(ax, 0.03, 0.075, 0.92, 0.145, face=NEUTRAL, edge=GRID, radius=0.014)
    label(ax, 0.055, 0.17, "不可变历史分支", size=6.8, color=INK, weight="bold", ha="left")
    label(
        ax,
        0.19,
        0.17,
        "experiment = original revision + Contract id + manifest + binary + measurement",
        size=6.1,
        family="DejaVu Sans",
        ha="left",
    )
    label(ax, 0.055, 0.115, "旧结果继续引用原 revision，不回写或冒充新版本结果", size=6.3, color=PURPLE, weight="bold", ha="left")
    label(ax, 0.95, 0.115, "冲突优先级只消除消费歧义，不制造跨库平均配置", size=6.1, color=MUTED, ha="right")
    ax.plot(
        [0.03, 0.012, 0.012, 0.035],
        [0.75, 0.75, 0.245, 0.245],
        color=PURPLE,
        linewidth=0.9,
        linestyle=(0, (3, 3)),
    )
    arrow(ax, (0.035, 0.245), (0.13, 0.22), color=PURPLE, linewidth=0.9, mutation_scale=7)

    save_figure(fig, "chapter3_provenance_conflict_invalidation")


def figure_4_1():
    fig, ax = canvas(7.5, 4.5)

    label(ax, 0.19, 0.965, "共享核心", size=8.4, color=BLUE_DARK, weight="bold")
    label(ax, 0.785, 0.965, "微内核包内实现", size=8.4, color=ORANGE, weight="bold")
    ax.plot([0.695, 0.695], [0.07, 0.925], color=ORANGE, linewidth=1.0, linestyle=(0, (4, 3)))

    rows = [
        (0.785, "知识层", BLUE_LIGHT, BLUE),
        (0.615, "空间层", TEAL_LIGHT, TEAL),
        (0.445, "调度层", PURPLE_LIGHT, PURPLE),
        (0.275, "后端层", ORANGE_LIGHT, ORANGE),
        (0.105, "证据层", NEUTRAL, BORDER),
    ]
    for y, title, face, edge in rows:
        rounded_box(ax, 0.025, y, 0.12, 0.13, face=edge, edge=edge, radius=0.014)
        label(ax, 0.085, y + 0.065, title, size=8.1, color="white", weight="bold")
        rounded_box(ax, 0.16, y, 0.515, 0.13, face=face, edge=edge, radius=0.014)
        rounded_box(
            ax,
            0.72,
            y,
            0.255,
            0.13,
            face="white",
            edge=ORANGE if title in {"知识层", "后端层"} else BORDER,
            radius=0.014,
            linestyle="--" if title in {"知识层", "后端层"} else "-",
        )

    label(ax, 0.185, 0.865, "Fact", size=7.4, weight="bold", color=BLUE_DARK)
    label(ax, 0.295, 0.865, "Contract", size=7.4, weight="bold", color=BLUE_DARK)
    label(ax, 0.455, 0.865, "Performance Profile", size=7.2, weight="bold", color=PURPLE)
    label(ax, 0.595, 0.865, "Unresolved", size=7.0, weight="bold", color=MUTED)
    label(ax, 0.847, 0.865, "BLIS f32/f64 · OpenBLAS RVV\n包内字段值与 provenance", size=6.8)

    label(ax, 0.205, 0.695, "任务匹配", size=7.2, weight="bold", color=TEAL_DARK)
    label(ax, 0.32, 0.695, "约束传播", size=7.2, weight="bold", color=TEAL_DARK)
    label(ax, 0.44, 0.695, "路径分类", size=7.2, weight="bold", color=TEAL_DARK)
    label(ax, 0.575, 0.695, "规范化 / 去重", size=7.2, weight="bold", color=TEAL_DARK)
    label(ax, 0.847, 0.695, "capability · package config\n统一候选记录接口", size=6.8)

    label(ax, 0.23, 0.525, "schedule token registry", size=7.1, weight="bold", color=PURPLE)
    label(ax, 0.43, 0.525, "BaCO / 其他调优器", size=7.1, weight="bold", color=PURPLE)
    label(ax, 0.59, 0.525, "objective callback", size=7.1, weight="bold", color=PURPLE)
    label(ax, 0.847, 0.525, "调优器不读取 ABI\n也不修改 Contract", size=6.8, color=MUTED)

    label(ax, 0.225, 0.355, "参数化 Transform", size=7.2, weight="bold", color=ORANGE)
    label(ax, 0.405, 0.355, "candidate record", size=7.2, weight="bold", color=ORANGE)
    label(ax, 0.585, 0.355, "generic fallback", size=7.2, weight="bold", color=ORANGE)
    rounded_box(ax, 0.735, 0.302, 0.105, 0.077, face=BLUE_LIGHT, edge=BLUE, radius=0.01)
    label(ax, 0.7875, 0.341, "BLIS\nshared core", size=6.5, color=BLUE_DARK, weight="bold")
    rounded_box(ax, 0.852, 0.302, 0.105, 0.077, face=TEAL_LIGHT, edge=TEAL, radius=0.01)
    label(ax, 0.9045, 0.341, "OpenBLAS RVV\nlocal generator", size=6.2, color=TEAL_DARK, weight="bold")

    label(ax, 0.205, 0.185, "数值 reference", size=6.9, weight="bold")
    label(ax, 0.325, 0.185, "Transform / LLVM IR", size=6.9, weight="bold")
    label(ax, 0.475, 0.185, "链接符号", size=6.9, weight="bold")
    label(ax, 0.585, 0.185, "observed path", size=6.9, weight="bold")
    label(ax, 0.847, 0.185, "wrapper · fringe counter\nbinary · manifest", size=6.7)

    for y0, y1, color in [
        (0.785, 0.745, BLUE),
        (0.615, 0.575, TEAL),
        (0.445, 0.405, PURPLE),
        (0.275, 0.235, ORANGE),
    ]:
        arrow(ax, (0.415, y0), (0.415, y1), color=color, mutation_scale=8)

    ax.plot(
        [0.685, 0.685, 0.54],
        [0.17, 0.82, 0.82],
        color=PURPLE,
        linewidth=1.1,
        solid_capstyle="round",
    )
    arrow(ax, (0.54, 0.82), (0.48, 0.82), color=PURPLE, linewidth=1.1)
    label(ax, 0.605, 0.80, "目标测量 → Profile", size=5.9, color=PURPLE)
    ax.plot([0.72, 0.975], [0.075, 0.075], color=ORANGE, linewidth=1.0, linestyle=(0, (4, 3)))
    label(ax, 0.847, 0.04, "虚线边界：包内字段、adapter 与生成器", size=6.4, color=ORANGE)

    save_figure(fig, "chapter4_contract_space_execution_architecture")


def figure_4_2():
    fig, ax = canvas(6.7, 4.6)

    rounded_box(ax, 0.20, 0.89, 0.56, 0.075, face=NEUTRAL, edge=BORDER, radius=0.012)
    label(
        ax,
        0.48,
        0.9275,
        "输入：task T · candidate q · Contract Ck · adapter · fallback",
        size=6.8,
        weight="bold",
    )

    decision_diamond(ax, 0.48, 0.79, 0.36, 0.115, "L1：payload / Transform 可执行？", face=NEUTRAL, edge=BORDER, size=6.8)
    decision_diamond(ax, 0.48, 0.635, 0.36, 0.115, "目标 Contract 存在且硬条件原样满足？", face=BLUE_LIGHT, edge=BLUE, color=BLUE_DARK, size=6.5)
    decision_diamond(ax, 0.48, 0.48, 0.36, 0.115, "适用 Contract 已声明有限适配可修复？", face=TEAL_LIGHT, edge=TEAL, color=TEAL_DARK, size=6.4)
    decision_diamond(ax, 0.48, 0.325, 0.36, 0.115, "存在安全的通用 / 完整库 fallback？", face=ORANGE_LIGHT, edge=ORANGE, color=ORANGE, size=6.4)

    arrow(ax, (0.48, 0.89), (0.48, 0.8475), color=MUTED, mutation_scale=8)
    for y0, y1, branch, color in [
        (0.7325, 0.6925, "是", BORDER),
        (0.5775, 0.5375, "否", BLUE),
        (0.4225, 0.3825, "否", TEAL),
    ]:
        arrow(ax, (0.48, y0), (0.48, y1), color=color, mutation_scale=8)
        label(ax, 0.495, (y0 + y1) / 2, branch, size=5.9, color=MUTED, ha="left")

    terminals = [
        (0.035, 0.58, "direct", "常规 packing / wrapper\n调用目标微内核", GREEN_LIGHT, GREEN),
        (0.035, 0.425, "adapt", "执行已声明的补偿动作\n再调用目标微内核", TEAL_LIGHT, TEAL),
        (0.035, 0.27, "fallback", "生成正确的通用 lowering\n或调用完整库路径", ORANGE_LIGHT, ORANGE),
    ]
    for x, y, title, body, face, edge in terminals:
        rounded_box(ax, x, y, 0.25, 0.115, face=face, edge=edge, radius=0.012)
        label(ax, x + 0.06, y + 0.077, title, size=7.1, color=edge, weight="bold", family="DejaVu Sans")
        label(ax, x + 0.155, y + 0.057, body, size=5.7)

    arrow(ax, (0.30, 0.635), (0.285, 0.6375), color=GREEN, mutation_scale=8)
    label(ax, 0.305, 0.655, "是", size=5.9, color=GREEN, weight="bold")
    arrow(ax, (0.30, 0.48), (0.285, 0.4825), color=TEAL, mutation_scale=8)
    label(ax, 0.305, 0.50, "是", size=5.9, color=TEAL_DARK, weight="bold")
    arrow(ax, (0.30, 0.325), (0.285, 0.3275), color=ORANGE, mutation_scale=8)
    label(ax, 0.305, 0.345, "是", size=5.9, color=ORANGE, weight="bold")

    rounded_box(ax, 0.72, 0.27, 0.245, 0.575, face=RED_LIGHT, edge=RED, radius=0.016)
    label(ax, 0.8425, 0.79, "reject", size=8.2, color=RED, weight="bold", family="DejaVu Sans")
    rounded_box(ax, 0.745, 0.665, 0.195, 0.075, face="white", edge=RED, radius=0.01)
    label(ax, 0.8425, 0.7025, "L1 非法", size=6.5, color=RED, weight="bold")
    rounded_box(ax, 0.745, 0.525, 0.195, 0.09, face="white", edge=RED, radius=0.01)
    label(ax, 0.8425, 0.57, "无已声明修复\n且无安全 fallback", size=6.1, color=RED, weight="bold")
    ax.plot([0.8425, 0.8425], [0.49, 0.42], color=RED, linewidth=0.8)
    label(ax, 0.8425, 0.375, "编译或执行前停止", size=6.4, color=RED, weight="bold")
    label(ax, 0.8425, 0.325, "不进入调优空间", size=6.1, color=INK)

    arrow(ax, (0.66, 0.79), (0.72, 0.705), color=RED, mutation_scale=8, connectionstyle="arc3,rad=-0.08")
    label(ax, 0.69, 0.78, "否", size=5.9, color=RED, weight="bold")
    arrow(ax, (0.66, 0.325), (0.72, 0.57), color=RED, mutation_scale=8, connectionstyle="arc3,rad=-0.10")
    label(ax, 0.69, 0.36, "否", size=5.9, color=RED, weight="bold")

    rounded_box(ax, 0.035, 0.065, 0.93, 0.105, face=NEUTRAL, edge=GRID, radius=0.014)
    label(ax, 0.06, 0.1175, "统一决策记录", size=6.6, color=INK, weight="bold", ha="left")
    label(
        ax,
        0.215,
        0.1175,
        "path · phase · first_field · reasons · actions · checks · provenance",
        size=6.1,
        family="DejaVu Sans",
        ha="left",
    )
    label(ax, 0.94, 0.1175, "路径类别决定生成动作，不表示速度排序", size=6.1, color=PURPLE, weight="bold", ha="right")

    save_figure(fig, "chapter4_four_path_decision")


def figure_4_3():
    data = pd.read_csv(NORMALIZATION_DATA)
    if len(data) != 2:
        raise ValueError("Figure 4-3 expects exactly one two-alias example")
    if data["canonical_schedule_id"].nunique() != 1:
        raise ValueError("Figure 4-3 aliases do not share a canonical schedule")
    if not data["canonical_ir_alias_match"].astype(bool).all():
        raise ValueError("Figure 4-3 aliases lack normalized-IR agreement")

    fig, ax = canvas(7.0, 3.6)
    rounded_box(ax, 0.02, 0.06, 0.46, 0.88, face="white", edge=GRID, radius=0.014)
    rounded_box(ax, 0.52, 0.06, 0.46, 0.88, face="white", edge=GRID, radius=0.014)
    panel_label(ax, 0.035, 0.925, "a")
    panel_label(ax, 0.535, 0.925, "b")
    label(ax, 0.08, 0.90, "路径相关参数活性", size=8.4, weight="bold", ha="left")
    label(ax, 0.58, 0.90, "canonical key 与归一化 IR 复核", size=8.4, weight="bold", ha="left")

    for row_index, (_, row) in enumerate(data.iterrows()):
        y = 0.55 - row_index * 0.29
        rounded_box(ax, 0.055, y, 0.255, 0.225, face=NEUTRAL, edge=BORDER, radius=0.012)
        label(ax, 0.072, y + 0.188, f"q{row_index}: {row['candidate_id']}", size=6.7, weight="bold", ha="left", family="DejaVu Sans Mono")
        label(
            ax,
            0.072,
            y + 0.132,
            f"tile=({int(row['tile_m'])},{int(row['tile_n'])},{int(row['tile_k'])})   pack={row['pack_mode']}",
            size=6.4,
            ha="left",
            family="DejaVu Sans Mono",
        )
        label(ax, 0.072, y + 0.085, f"path={row['path']}", size=6.4, ha="left", family="DejaVu Sans Mono")
        vector_face = ORANGE_LIGHT if bool(row["vectorize"]) else BLUE_LIGHT
        vector_edge = ORANGE if bool(row["vectorize"]) else BLUE
        chip(
            ax,
            0.182,
            y + 0.047,
            0.11,
            0.055,
            f"vectorize={str(bool(row['vectorize'])).lower()}",
            face=vector_face,
            edge=vector_edge,
            size=5.9,
        )

    rounded_box(ax, 0.345, 0.315, 0.105, 0.35, face=TEAL_LIGHT, edge=TEAL, radius=0.014)
    label(ax, 0.3975, 0.61, "Normpath", size=7.2, color=TEAL_DARK, weight="bold")
    label(ax, 0.3975, 0.53, "active", size=6.4, color=MUTED, weight="bold")
    label(ax, 0.3975, 0.465, "tile\npack\npath\nobligations", size=6.5)
    ax.plot([0.365, 0.43], [0.385, 0.385], color=TEAL, linewidth=0.8)
    label(ax, 0.3975, 0.34, "inactive\nvectorize → false", size=6.2, color=ORANGE)
    arrow(ax, (0.31, 0.665), (0.345, 0.56), color=BLUE, mutation_scale=8)
    arrow(ax, (0.31, 0.375), (0.345, 0.44), color=ORANGE, mutation_scale=8)
    label(ax, 0.25, 0.125, "同一路径中只有实际改变代码或运行行为的参数进入 key", size=6.4, color=MUTED)

    rounded_box(ax, 0.56, 0.61, 0.38, 0.18, face=BLUE_LIGHT, edge=BLUE, radius=0.014)
    label(ax, 0.75, 0.75, "canonical key", size=7.2, color=BLUE_DARK, weight="bold")
    label(
        ax,
        0.75,
        0.68,
        "H(contract, path, tile, pack, obligations)",
        size=6.4,
        family="DejaVu Sans",
    )

    for x, index in [(0.56, 0), (0.775, 1)]:
        rounded_box(ax, x, 0.31, 0.165, 0.19, face=PURPLE_LIGHT, edge=PURPLE, radius=0.012)
        label(ax, x + 0.0825, 0.45, f"IRnorm(q{index})", size=7.0, color=PURPLE, weight="bold")
        label(ax, x + 0.0825, 0.38, "stable hash = hIR", size=6.2, family="DejaVu Sans Mono")
        arrow(ax, (0.75, 0.61), (x + 0.0825, 0.50), color=PURPLE, mutation_scale=8)
    label(ax, 0.75, 0.405, "=", size=11.0, weight="bold", color=PURPLE)
    rounded_box(ax, 0.60, 0.125, 0.30, 0.09, face=GREEN_LIGHT, edge=GREEN, radius=0.012)
    label(ax, 0.75, 0.17, "2 个路径内别名 → 1 个唯一 schedule", size=6.9, color=GREEN, weight="bold")
    label(ax, 0.75, 0.085, "sq_096 的一个已审计示例，不表示总体缩减比例", size=6.2, color=MUTED)

    save_figure(fig, "chapter4_parameter_activity_normalization")


def figure_4_4():
    fig, ax = canvas(7.35, 4.1)
    rounded_box(ax, 0.02, 0.06, 0.46, 0.88, face="white", edge=GRID, radius=0.014)
    rounded_box(ax, 0.52, 0.06, 0.46, 0.88, face="white", edge=GRID, radius=0.014)
    panel_label(ax, 0.035, 0.925, "a")
    panel_label(ax, 0.535, 0.925, "b")
    label(ax, 0.085, 0.90, "Direct：完整输出 tile", size=8.4, weight="bold", ha="left")
    label(ax, 0.585, 0.90, "Adapt：M/N/K fringe", size=8.4, weight="bold", ha="left")

    label(ax, 0.105, 0.80, "packed Aμ", size=6.8, color=BLUE_DARK, weight="bold")
    matrix_grid(ax, 0.055, 0.64, 0.10, 0.12, 4, 5, highlight=lambda r, c: BLUE_LIGHT)
    label(ax, 0.245, 0.80, "packed Bμ", size=6.8, color=TEAL_DARK, weight="bold")
    matrix_grid(ax, 0.195, 0.64, 0.10, 0.12, 5, 4, highlight=lambda r, c: TEAL_LIGHT)
    chip(ax, 0.325, 0.665, 0.115, 0.07, "actual K", face=NEUTRAL, edge=BORDER, size=6.5)

    rounded_box(ax, 0.155, 0.45, 0.17, 0.12, face=PURPLE_LIGHT, edge=PURPLE, radius=0.012)
    label(ax, 0.24, 0.525, "direct wrapper", size=7.1, color=PURPLE, weight="bold")
    label(ax, 0.24, 0.48, "microkernel · β=1", size=6.3)
    arrow(ax, (0.105, 0.64), (0.19, 0.57), color=BLUE, mutation_scale=8)
    arrow(ax, (0.245, 0.64), (0.275, 0.57), color=TEAL, mutation_scale=8)
    arrow(ax, (0.382, 0.665), (0.325, 0.535), color=MUTED, mutation_scale=8)

    label(ax, 0.24, 0.395, "原 C 中的 MR × NR 完整 tile", size=6.8, color=PURPLE)
    matrix_grid(ax, 0.15, 0.17, 0.18, 0.18, 5, 6, highlight=lambda r, c: PURPLE_LIGHT)
    arrow(ax, (0.24, 0.45), (0.24, 0.35), color=PURPLE, mutation_scale=8)
    label(ax, 0.24, 0.12, "微内核直接累加并写回", size=6.5, color=MUTED)

    rounded_box(ax, 0.06, 0.075, 0.36, 0.055, face=GREEN_LIGHT, edge=GREEN, radius=0.01)
    label(ax, 0.24, 0.1025, "wrapper call · linked symbol · observed direct · reference", size=5.8, color=GREEN)

    label(ax, 0.595, 0.80, "Aμ：K tail", size=6.7, color=BLUE_DARK, weight="bold")
    matrix_grid(
        ax,
        0.55,
        0.66,
        0.09,
        0.105,
        4,
        5,
        highlight=lambda r, c: RED_LIGHT if c >= 3 else BLUE_LIGHT,
        hatch=lambda r, c: "///" if c >= 3 else None,
    )
    label(ax, 0.70, 0.80, "Bμ：K tail", size=6.7, color=TEAL_DARK, weight="bold")
    matrix_grid(
        ax,
        0.66,
        0.66,
        0.09,
        0.105,
        5,
        4,
        highlight=lambda r, c: RED_LIGHT if r >= 3 else TEAL_LIGHT,
        hatch=lambda r, c: "///" if r >= 3 else None,
    )
    chip(ax, 0.785, 0.685, 0.15, 0.06, "zero pad · actual K", face=RED_LIGHT, edge=RED, size=6.1)

    rounded_box(ax, 0.665, 0.485, 0.17, 0.105, face=PURPLE_LIGHT, edge=PURPLE, radius=0.012)
    label(ax, 0.75, 0.55, "fringe wrapper", size=7.0, color=PURPLE, weight="bold")
    label(ax, 0.75, 0.51, "microkernel · β=1", size=6.2)
    arrow(ax, (0.595, 0.66), (0.70, 0.59), color=BLUE, mutation_scale=8)
    arrow(ax, (0.705, 0.66), (0.78, 0.59), color=TEAL, mutation_scale=8)
    arrow(ax, (0.86, 0.685), (0.82, 0.59), color=RED, mutation_scale=8)

    label(ax, 0.61, 0.43, "临时 C：MR × NR", size=6.5, color=PURPLE)
    matrix_grid(
        ax,
        0.55,
        0.20,
        0.16,
        0.19,
        5,
        6,
        highlight=lambda r, c: TEAL_LIGHT if (r < 3 and c < 4) else NEUTRAL_2,
        hatch=lambda r, c: None if (r < 3 and c < 4) else "..",
    )
    label(ax, 0.63, 0.165, "有效区 + 临时填充", size=6.1, color=MUTED)
    arrow(ax, (0.71, 0.295), (0.79, 0.295), color=ORANGE, mutation_scale=9)
    label(ax, 0.75, 0.335, "scatter", size=6.4, color=ORANGE, weight="bold")
    label(ax, 0.875, 0.43, "原 C：valid M × N", size=6.5, color=GREEN)
    matrix_grid(
        ax,
        0.81,
        0.20,
        0.13,
        0.19,
        5,
        6,
        highlight=lambda r, c: GREEN_LIGHT if (r < 3 and c < 4) else "white",
    )
    arrow(ax, (0.75, 0.485), (0.63, 0.39), color=PURPLE, mutation_scale=8)

    rounded_box(ax, 0.56, 0.075, 0.38, 0.055, face=GREEN_LIGHT, edge=GREEN, radius=0.01)
    label(ax, 0.75, 0.1025, "fringe counter · observed adapt · actual K · reference", size=5.9, color=GREEN)

    save_figure(fig, "chapter4_transform_packing_microkernel_fringe")


FIGURES = {
    "chapter1_microkernel_admissibility_problem": {
        "width_mm": 144,
        "role": "problem_schematic",
        "source_data": None,
    },
    "chapter1_research_route": {
        "width_mm": 141,
        "role": "research_workflow",
        "source_data": None,
    },
    "chapter2_gemm_layers_microkernel_interface": {
        "width_mm": 144,
        "role": "schematic",
        "source_data": None,
    },
    "chapter2_three_layer_boundary": {
        "width_mm": 128,
        "role": "schematic",
        "source_data": None,
    },
    "chapter3_source_fact_contract_pipeline": {
        "width_mm": 141,
        "role": "knowledge_workflow",
        "source_data": None,
    },
    "chapter3_microkernel_contract_schema": {
        "width_mm": 141,
        "role": "schematic",
        "source_data": None,
    },
    "chapter3_provenance_conflict_invalidation": {
        "width_mm": 138,
        "role": "provenance_lifecycle",
        "source_data": None,
    },
    "chapter4_contract_space_execution_architecture": {
        "width_mm": 150,
        "role": "architecture",
        "source_data": None,
    },
    "chapter4_four_path_decision": {
        "width_mm": 134,
        "role": "decision_workflow",
        "source_data": None,
    },
    "chapter4_parameter_activity_normalization": {
        "width_mm": 141,
        "role": "audited_example",
        "source_data": NORMALIZATION_DATA.name,
    },
    "chapter4_transform_packing_microkernel_fringe": {
        "width_mm": 147,
        "role": "data_layout_schematic",
        "source_data": None,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest():
    records = []
    for stem, contract in FIGURES.items():
        files = {}
        for suffix in (".pdf", ".svg", ".tiff", ".png"):
            path = HERE / f"{stem}{suffix}"
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"Missing or empty export: {path}")
            files[suffix[1:]] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }

        svg_text = (HERE / f"{stem}.svg").read_text(encoding="utf-8")
        editable_text = "<text" in svg_text
        if not editable_text:
            raise RuntimeError(f"SVG text is not editable for {stem}")

        with Image.open(HERE / f"{stem}.png") as image:
            png_size = list(image.size)
        with Image.open(HERE / f"{stem}.tiff") as image:
            tiff_size = list(image.size)
            tiff_dpi = [round(float(value), 2) for value in image.info.get("dpi", (0, 0))]

        records.append(
            {
                "figure": stem,
                **contract,
                "backend": "python",
                "matplotlib": matplotlib.__version__,
                "seaborn": sns.__version__,
                "font": FONT_NAME,
                "editable_svg_text": editable_text,
                "png_pixels": png_size,
                "tiff_pixels": tiff_size,
                "tiff_dpi": tiff_dpi,
                "files": files,
            }
        )

    manifest = {
        "status": "PASS",
        "backend": "python",
        "figure_count": len(records),
        "statistics_present": False,
        "workflow_figures_modified": True,
        "records": records,
    }
    (HERE / "chapter2_4_figure_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    figure_1_1()
    figure_1_2()
    figure_2_1()
    figure_2_2()
    figure_3_1()
    figure_3_2()
    figure_3_3()
    figure_4_1()
    figure_4_2()
    figure_4_3()
    figure_4_4()
    build_manifest()
    print(f"Generated {len(FIGURES)} figures in {HERE}")


if __name__ == "__main__":
    main()
