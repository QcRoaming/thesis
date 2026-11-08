from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"

song = font_manager.FontProperties(fname=str(FONT_DIR / "simsun.ttc"))
hei = font_manager.FontProperties(fname=str(FONT_DIR / "simhei.ttf"))

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["axes.unicode_minus"] = False


def box(ax, x, y, w, h, title, lines, face, edge):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.014,rounding_size=0.035",
        linewidth=1.35,
        edgecolor=edge,
        facecolor=face,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h - 0.065,
        title,
        ha="center",
        va="top",
        fontproperties=hei,
        fontsize=10.6,
        color="#0f172a",
        zorder=3,
    )
    ax.text(
        x + 0.032,
        y + h - 0.145,
        "\n".join(lines),
        ha="left",
        va="top",
        fontproperties=song,
        fontsize=8.4,
        linespacing=1.35,
        color="#334155",
        zorder=3,
    )
    return patch


def arrow(ax, start, end, label=None, color="#475569"):
    arr = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.25,
        color=color,
        zorder=1,
    )
    ax.add_patch(arr)
    if label:
        ax.text(
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.025,
            label,
            ha="center",
            va="bottom",
            fontproperties=song,
            fontsize=8.2,
            color=color,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.9),
            zorder=4,
        )


fig, ax = plt.subplots(figsize=(7.2, 3.55))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.patch.set_facecolor("white")

box(
    ax,
    0.035,
    0.46,
    0.205,
    0.36,
    "专家事实",
    ["配置 / kernel 接口", "ISA 分派 / 生成器", "证据位置与适用条件"],
    "#eff6ff",
    "#2563eb",
)

box(
    ax,
    0.285,
    0.46,
    0.205,
    0.36,
    "Contract 字段",
    ["shape, dtype / ISA", "layout, memory", "tail, call, evidence"],
    "#f0fdf4",
    "#16a34a",
)

box(
    ax,
    0.535,
    0.46,
    0.205,
    0.36,
    "兼容性检查",
    ["硬约束过滤", "可适配项识别", "失败原因记录"],
    "#fff7ed",
    "#ea580c",
)

box(
    ax,
    0.785,
    0.46,
    0.18,
    0.36,
    "搜索空间",
    ["tile / pack", "vectorize / replace", "参数域与优先级"],
    "#ecfeff",
    "#0891b2",
)

arrow(ax, (0.24, 0.64), (0.285, 0.64))
arrow(ax, (0.49, 0.64), (0.535, 0.64))
arrow(ax, (0.74, 0.64), (0.785, 0.64))

action_box = FancyBboxPatch(
    (0.22, 0.19),
    0.56,
    0.14,
    boxstyle="round,pad=0.012,rounding_size=0.03",
    linewidth=1.25,
    edgecolor="#64748b",
    facecolor="#f8fafc",
    zorder=2,
)
ax.add_patch(action_box)
ax.text(
    0.5,
    0.26,
    "候选动作：direct 直接替换  |  adapt 适配  |  fallback 退化  |  reject 过滤",
    ha="center",
    va="center",
    fontproperties=song,
    fontsize=8.6,
    color="#1e293b",
    zorder=3,
)

arrow(ax, (0.637, 0.46), (0.58, 0.33), None, "#64748b")
arrow(ax, (0.62, 0.33), (0.83, 0.46), None, "#64748b")

ax.text(
    0.5,
    0.065,
    "作用：在候选进入编译与测量前，先判断其是否满足至少一个可用 microkernel 的接口条件。",
    ha="center",
    va="bottom",
    fontproperties=song,
    fontsize=8.8,
    color="#334155",
)

fig.tight_layout(pad=0.05)

for ext in ("pdf", "svg", "png"):
    fig.savefig(FIG_DIR / f"microkernel_contract_model.{ext}", bbox_inches="tight", dpi=300)
