from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


FIG_DIR = Path(__file__).resolve().parent
FONT_DIR = Path("/buddy-mlir/.agents/skills/canvas-design/canvas-fonts")

sans = font_manager.FontProperties(fname=str(FONT_DIR / "InstrumentSans-Regular.ttf"))
sans_bold = font_manager.FontProperties(fname=str(FONT_DIR / "InstrumentSans-Bold.ttf"))
mono = font_manager.FontProperties(fname=str(FONT_DIR / "JetBrainsMono-Regular.ttf"))
mono_bold = font_manager.FontProperties(fname=str(FONT_DIR / "JetBrainsMono-Bold.ttf"))

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["axes.unicode_minus"] = False


INK = "#172033"
MUTED = "#64748b"
GRID = "#d6dce7"
BLUE = "#3157d5"
CYAN = "#22a6b3"
GREEN = "#4f9f68"
ORANGE = "#d98c2b"
RED = "#c2414b"
PAPER = "#fbfaf7"


def label(ax, x, y, text, size=7.8, color=INK, prop=mono, ha="center", va="center", alpha=1.0):
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontproperties=prop,
        fontsize=size,
        color=color,
        alpha=alpha,
        zorder=10,
    )


def arrow(ax, start, end, color=MUTED, lw=1.0, rad=0.0, alpha=0.9):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=10,
        linewidth=lw,
        color=color,
        alpha=alpha,
        connectionstyle=f"arc3,rad={rad}",
        zorder=5,
    )
    ax.add_patch(patch)


def soft_box(ax, x, y, w, h, edge, face="#ffffff", lw=1.1, radius=0.018, alpha=1.0):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
        alpha=alpha,
        zorder=2,
    )
    ax.add_patch(patch)
    return patch


def matrix_grid(ax, x, y, w, h, rows, cols, accent_col=None, accent_row=None, tail=False):
    soft_box(ax, x, y, w, h, edge="#b9c2d1", face="#ffffff", lw=0.95, radius=0.012)
    for i in range(1, cols):
        xx = x + w * i / cols
        ax.add_line(Line2D([xx, xx], [y, y + h], color=GRID, linewidth=0.42, zorder=3))
    for j in range(1, rows):
        yy = y + h * j / rows
        ax.add_line(Line2D([x, x + w], [yy, yy], color=GRID, linewidth=0.42, zorder=3))
    if accent_col is not None:
        cw = w / cols
        ax.add_patch(
            Rectangle(
                (x + cw * accent_col, y),
                cw,
                h,
                facecolor="#dce7ff",
                edgecolor="none",
                alpha=0.85,
                zorder=2.8,
            )
        )
    if accent_row is not None:
        rh = h / rows
        ax.add_patch(
            Rectangle(
                (x, y + rh * accent_row),
                w,
                rh,
                facecolor="#e5f5ee",
                edgecolor="none",
                alpha=0.88,
                zorder=2.7,
            )
        )
    if tail:
        cw = w / cols
        rh = h / rows
        ax.add_patch(
            Rectangle(
                (x + w - cw, y),
                cw,
                rh * 1.05,
                facecolor="#f8d6cf",
                edgecolor="#cc6b5a",
                linewidth=0.45,
                alpha=0.95,
                zorder=4,
            )
        )


def packed_panel(ax, x, y, w, h, n_stripes, color, orientation="vertical", tail=False):
    soft_box(ax, x, y, w, h, edge="#aab5c5", face="#ffffff", lw=0.9, radius=0.012)
    gap = 0.004
    if orientation == "vertical":
        stripe_w = (w - gap * (n_stripes + 1)) / n_stripes
        for i in range(n_stripes):
            xx = x + gap + i * (stripe_w + gap)
            alpha = 0.8 if i % 2 == 0 else 0.55
            ax.add_patch(Rectangle((xx, y + gap), stripe_w, h - 2 * gap, facecolor=color, edgecolor="none", alpha=alpha, zorder=4))
        if tail:
            ax.add_patch(Rectangle((x + w - stripe_w - gap, y + gap), stripe_w, h - 2 * gap, facecolor="#f4b6ac", edgecolor="none", alpha=0.95, zorder=5))
    else:
        stripe_h = (h - gap * (n_stripes + 1)) / n_stripes
        for i in range(n_stripes):
            yy = y + gap + i * (stripe_h + gap)
            alpha = 0.8 if i % 2 == 0 else 0.55
            ax.add_patch(Rectangle((x + gap, yy), w - 2 * gap, stripe_h, facecolor=color, edgecolor="none", alpha=alpha, zorder=4))
        if tail:
            ax.add_patch(Rectangle((x + gap, y + gap), w - 2 * gap, stripe_h, facecolor="#f4b6ac", edgecolor="none", alpha=0.95, zorder=5))


def vector_lanes(ax, x, y, w, h, lanes, active, color):
    soft_box(ax, x, y, w, h, edge="#8893a4", face="#ffffff", lw=0.95, radius=0.012)
    gap = 0.006
    lane_h = (h - gap * (lanes + 1)) / lanes
    for i in range(lanes):
        yy = y + gap + i * (lane_h + gap)
        face = color if i < active else "#f2d0cc"
        alpha = 0.75 if i < active else 0.92
        ax.add_patch(Rectangle((x + gap, yy), w - 2 * gap, lane_h, facecolor=face, edgecolor="none", alpha=alpha, zorder=4))
    for i in range(1, lanes):
        yy = y + i * h / lanes
        ax.add_line(Line2D([x, x + w], [yy, yy], color="#e2e8f0", linewidth=0.35, zorder=5))


fig, ax = plt.subplots(figsize=(7.25, 3.95))
fig.patch.set_facecolor(PAPER)
ax.set_facecolor(PAPER)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Very light construction grid, intentionally visible only as a sense of craft.
for xx in [0.06, 0.22, 0.38, 0.54, 0.70, 0.86]:
    ax.add_line(Line2D([xx, xx], [0.08, 0.92], color="#edf1f5", linewidth=0.5, zorder=0))
for yy in [0.18, 0.34, 0.50, 0.66, 0.82]:
    ax.add_line(Line2D([0.04, 0.96], [yy, yy], color="#f0f3f6", linewidth=0.45, zorder=0))

label(ax, 0.104, 0.88, "source", size=7.0, color=MUTED, prop=mono_bold)
matrix_grid(ax, 0.045, 0.55, 0.16, 0.24, rows=5, cols=7, accent_col=1, tail=True)
matrix_grid(ax, 0.055, 0.23, 0.14, 0.21, rows=6, cols=4, accent_row=2)
label(ax, 0.125, 0.515, "A / B", size=7.0, color=INK, prop=mono_bold)
label(ax, 0.125, 0.195, "stride", size=6.6, color=MUTED, prop=mono)

arrow(ax, (0.215, 0.67), (0.295, 0.67), BLUE, lw=1.1)
arrow(ax, (0.208, 0.34), (0.295, 0.34), GREEN, lw=1.1)

label(ax, 0.337, 0.88, "pack", size=7.0, color=MUTED, prop=mono_bold)
packed_panel(ax, 0.292, 0.56, 0.105, 0.24, 6, "#8fb3ff", orientation="vertical", tail=True)
packed_panel(ax, 0.412, 0.56, 0.105, 0.24, 5, "#83d1bf", orientation="vertical")
packed_panel(ax, 0.314, 0.245, 0.18, 0.105, 6, "#83d1bf", orientation="horizontal")
label(ax, 0.344, 0.515, "A-panel", size=6.5, color=INK, prop=mono)
label(ax, 0.464, 0.515, "B-panel", size=6.5, color=INK, prop=mono)
label(ax, 0.405, 0.205, "aligned buffer", size=6.5, color=MUTED, prop=mono)

for x in [0.318, 0.338, 0.358, 0.438, 0.458, 0.478]:
    ax.add_line(Line2D([x, x + 0.008], [0.825, 0.835], color="#aab5c5", linewidth=0.8, zorder=6))

arrow(ax, (0.528, 0.66), (0.607, 0.66), CYAN, lw=1.1)
arrow(ax, (0.502, 0.30), (0.606, 0.43), CYAN, lw=0.95, rad=-0.12)

label(ax, 0.662, 0.88, "lanes", size=7.0, color=MUTED, prop=mono_bold)
vector_lanes(ax, 0.61, 0.53, 0.125, 0.28, lanes=8, active=7, color="#9ae2dc")
vector_lanes(ax, 0.755, 0.53, 0.125, 0.28, lanes=8, active=8, color="#a7c4ff")
label(ax, 0.672, 0.49, "mask tail", size=6.4, color=RED, prop=mono)
label(ax, 0.818, 0.49, "full lanes", size=6.4, color=INK, prop=mono)

for x0, y0, col in [(0.642, 0.395, CYAN), (0.787, 0.395, BLUE)]:
    soft_box(ax, x0, y0, 0.065, 0.045, edge=col, face="#ffffff", lw=0.75, radius=0.01)
    label(ax, x0 + 0.0325, y0 + 0.022, "fma", size=5.8, color=col, prop=mono_bold)

arrow(ax, (0.885, 0.66), (0.93, 0.66), ORANGE, lw=1.1)

soft_box(ax, 0.915, 0.51, 0.055, 0.30, edge="#8f99aa", face="#ffffff", lw=0.9, radius=0.012)
for yy, txt, col in [
    (0.755, "shape", BLUE),
    (0.707, "layout", GREEN),
    (0.659, "isa", CYAN),
    (0.611, "tail", RED),
    (0.563, "cost", ORANGE),
]:
    ax.add_line(Line2D([0.925, 0.958], [yy - 0.019, yy - 0.019], color=col, linewidth=1.25, zorder=5))
    label(ax, 0.942, yy, txt, size=5.6, color=INK, prop=mono, alpha=0.9)

label(ax, 0.942, 0.475, "rule capsule", size=6.3, color=MUTED, prop=mono)

# Bottom grammar: very sparse, useful when the figure is read apart from the caption.
soft_box(ax, 0.065, 0.085, 0.85, 0.065, edge="#c8d0dc", face="#ffffff", lw=0.65, radius=0.012, alpha=0.72)
label(
    ax,
    0.49,
    0.118,
    "packing fixes locality and layout  ·  vectorization consumes aligned panels through ISA-width lanes",
    size=6.9,
    color="#334155",
    prop=sans,
)

fig.tight_layout(pad=0.08)

for ext in ("pdf", "png", "svg"):
    fig.savefig(FIG_DIR / f"packing_vectorization_rule_map.{ext}", bbox_inches="tight", dpi=450)
