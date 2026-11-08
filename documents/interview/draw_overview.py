#!/usr/bin/env python3
"""Render the interview overview as a font-embedded PDF, vector SVG and 4K PNG.

Uses PyMuPDF and the thesis' bundled fonts. No hardware measurements are run.
Run from any directory: python documents/interview/draw_overview.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import fitz


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
FONT = ROOT / "nwputhesis/fonts/simhei.ttf"
WIDTH, HEIGHT = 1920, 1080
C = {
    "bg": "F4F7FA", "ink": "172B3A", "muted": "536777",
    "teal": "007E83", "teal_bg": "E8F5F3", "teal_edge": "A3D4CE",
    "purple": "7661AA", "purple_bg": "F0ECF8",
    "gray_bg": "EDF1F5", "gray_edge": "CDD6DF",
    "red": "A94850", "red_bg": "FAECEC", "white": "FFFFFF",
}


def rgb(name):
    h = C.get(name, name)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def main():
    doc = fitz.open()
    page = doc.new_page(width=WIDTH, height=HEIGHT)
    page.insert_font(fontname="ThesisSans", fontfile=str(FONT))
    font = fitz.Font(fontfile=str(FONT))
    text_checks = []

    def rect(x, y, w, h, fill="white", stroke=None, radius=0.08, width=1.4):
        page.draw_rect(fitz.Rect(x, y, x + w, y + h), fill=rgb(fill),
                       color=rgb(stroke) if stroke else None,
                       width=width, radius=radius or None)

    def text(x, y, s, size=25, color="ink", max_width=None, center=False):
        length = font.text_length(s, fontsize=size)
        if max_width is not None and length > max_width + 0.1:
            raise ValueError(f"Text overflow {length:.1f}>{max_width}: {s}")
        if center:
            x -= length / 2
        if not all(font.has_glyph(ord(ch)) or ch.isspace() for ch in s):
            raise ValueError(f"Missing glyph: {s}")
        page.insert_text((x, y), s, fontsize=size, fontname="ThesisSans", color=rgb(color))
        text_checks.append({"text": s, "font_size": size, "x": x, "baseline_y": y, "width": length})

    def arrow(points, color="teal", dashed=False, width=2.8, head=10):
        pts = [fitz.Point(*p) for p in points]
        page.draw_polyline(pts, color=rgb(color), width=width,
                           dashes="[8 6] 0" if dashed else None,
                           lineJoin=1, lineCap=1, closePath=False)
        dx, dy = pts[-1].x - pts[-2].x, pts[-1].y - pts[-2].y
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        end = pts[-1]
        left = fitz.Point(end.x - head * ux + head * .45 * uy,
                          end.y - head * uy - head * .45 * ux)
        right = fitz.Point(end.x - head * ux - head * .45 * uy,
                           end.y - head * uy + head * .45 * ux)
        page.draw_polyline([left, end, right], color=rgb(color), fill=rgb(color),
                           width=1, closePath=True)

    rect(0, 0, WIDTH, HEIGHT, "bg", radius=0)
    text(56, 52, "硕士论文  /  AI 编译器岗位面试", 22, "teal")
    text(56, 112, "让 MLIR 自动调优理解微内核的调用条件", 46, max_width=1750)
    text(56, 160, "核心问题：调度语义正确之后，怎样接入专家微内核，并生成值得搜索的候选？", 27, "muted")
    rect(56, 189, 18, 18, "teal", radius=.2)
    text(84, 205, "论文实现", 22, "muted")
    rect(230, 189, 18, 18, "gray_edge", radius=.2)
    text(258, 205, "输入 / 复用组件", 22, "muted")
    page.draw_line((460, 199), (506, 199), color=rgb("purple"), width=2.6, dashes="[7 5] 0")
    text(518, 205, "软先验与性能反馈", 22, "muted")
    text(1450, 205, "单线程 / 行主序 / rank-2 GEMM", 22, "muted", max_width=410)

    titles = ["提炼调用知识", "生成候选空间", "选择并物化调度", "执行验证与性能取舍"]
    subtitles = ["哪些条件必须满足？", "哪些候选可以进入搜索？", "如何变成真实调用？", "结果是否正确、收益能否覆盖成本？"]
    xs = [56, 514, 972, 1430]
    for i, x in enumerate(xs):
        page.draw_circle((x + 17, 249), 17, color=None, fill=rgb("teal"))
        text(x + 17, 258, str(i + 1), 25, "white", center=True)
        text(x + 45, 260, titles[i], 30, max_width=385)
        text(x + 4, 292, subtitles[i], 21, "muted", max_width=426)
        rect(x, 310, 430, 448, "white", "gray_edge", radius=.045)

    # 1. Source facts feed separate hard and soft knowledge objects.
    rect(76, 330, 390, 78, "teal_bg", "teal_edge")
    text(94, 360, "固定源码 → 可追溯 Fact", 27, "teal", max_width=354)
    text(94, 391, "BLIS / OpenBLAS · 版本核验", 22, "muted", max_width=354)
    rect(96, 444, 370, 156, "teal_bg", "teal_edge")
    text(115, 481, "硬契约 Contract", 28, "teal", max_width=332)
    text(115, 518, "dtype / ISA / MR×NR", 25, max_width=332)
    text(115, 552, "panel / stride / tail / ABI", 23, max_width=332)
    text(115, 584, "约束调用前提，生成适配义务", 23, "muted", max_width=332)
    rect(96, 638, 370, 100, "purple_bg", "purple")
    text(115, 672, "软性能 Profile", 27, "purple", max_width=332)
    text(115, 708, "分块偏好与排序；用目标数据校准", 21, "muted", max_width=332)
    arrow([(271, 408), (271, 423), (82, 423), (82, 518), (96, 518)])
    arrow([(82, 518), (82, 688), (96, 688)], "purple", True, 2)

    # 2. Task and Contract compile to executable candidates and diagnostics.
    rect(534, 330, 390, 78, "gray_bg", "gray_edge")
    text(552, 360, "GEMM IR + 目标任务", 27, max_width=354)
    text(552, 391, "M/N/K · dtype · layout · ISA", 22, "muted", max_width=354)
    rect(534, 444, 390, 156, "teal_bg", "teal_edge")
    text(552, 481, "Contract 编译器", 29, "teal", max_width=354)
    text(552, 518, "任务匹配 / 约束检查 / 路径分类", 23, max_width=354)
    text(552, 552, "参数活性分析 / 规范化去重", 23, max_width=354)
    text(552, 584, "输出：token + 生成义务 + 诊断", 22, "muted", max_width=354)
    arrow([(729, 408), (729, 444)])
    arrow([(466, 518), (534, 518)])
    paths = [
        (534, 624, "Direct  直接调用", "teal_bg", "teal"),
        (735, 624, "Adapt  边界适配", "teal_bg", "teal"),
        (534, 685, "Fallback  回退", "teal_bg", "teal"),
        (735, 685, "Reject  提前拒绝", "red_bg", "red"),
    ]
    for x, y, label, fill, color in paths:
        rect(x, y, 189, 51, fill, radius=.10)
        text(x + 94.5, y + 33, label, 21, color, center=True, max_width=180)

    # 3. The tuner is reused. Custom materialization realizes Contract obligations.
    rect(992, 330, 390, 78, "gray_bg", "gray_edge")
    text(1010, 360, "BaCO 选择候选（复用）", 27, max_width=354)
    text(1010, 391, "仅非 reject 候选进入调优", 22, "muted", max_width=354)
    arrow([(924, 491), (948, 491), (948, 359), (992, 359)])
    rect(992, 453, 390, 285, "teal_bg", "teal_edge")
    text(1010, 493, "Transform 调度物化", 28, "teal", max_width=354)
    text(1010, 535, "分块循环 + A/B packing", 25, max_width=354)
    text(1010, 577, "动态边界：padding / fringe", 23, max_width=354)
    text(1010, 619, "占位调用 → 真实微内核 wrapper", 22, max_width=354)
    page.draw_line((1010, 644), (1364, 644), color=rgb("teal_edge"), width=1)
    text(1010, 678, "pass + Transform op + adapter", 22, "muted", max_width=354)
    text(1010, 714, "linalg / memref / scf → LLVM IR", 22, "teal", max_width=354)
    arrow([(1187, 408), (1187, 453)])

    # 4. Package-specific adapters retain their backend implementation boundaries.
    rect(1450, 330, 390, 78, "gray_bg", "gray_edge")
    text(1468, 360, "复用专家库微内核", 27, max_width=354)
    text(1468, 391, "BLIS x86 f32/f64 · OpenBLAS RVV", 21, "muted", max_width=354)
    rect(1450, 453, 390, 110, "gray_bg", "gray_edge")
    text(1468, 493, "LLVM / Clang → 目标二进制", 25, max_width=354)
    text(1468, 537, "x86 主机 / 物理 K230 执行", 24, "muted", max_width=354)
    arrow([(1382, 510), (1450, 510)])
    arrow([(1645, 408), (1645, 453)], "muted", width=2)
    rect(1450, 610, 390, 128, "teal_bg", "teal_edge")
    text(1468, 646, "联合验证与成本评价", 28, "teal", max_width=354)
    text(1468, 684, "数值 / IR / 符号 / 运行路径", 23, max_width=354)
    text(1468, 719, "目标计时 + 完整库对照 + 全成本", 22, "muted", max_width=354)
    arrow([(1645, 563), (1645, 610)])

    # Soft preferences and measured objectives share a return path to selection.
    arrow([(466, 688), (496, 688), (496, 787), (974, 787)], "purple", True, 2.5, head=8)
    text(520, 777, "软先验只影响候选选择", 22, "purple")
    arrow([(1645, 738), (1645, 835), (281, 835), (281, 738)], "purple", True, 2.5)
    arrow([(974, 835), (974, 392), (992, 392)], "purple", True, 2.5, head=8)
    rect(1024, 799, 557, 49, "bg", radius=0)
    text(1035, 829, "性能反馈：目标值回传 / 软先验校准", 24, "purple", max_width=544)

    # Bottom evidence is deliberately limited to three easy-to-explain findings.
    metric_xs = [56, 668, 1280]
    metric_titles = ["2,600 → 平均 104.4", "1,256 / 1,256 路径一致", "以完整库为部署基线"]
    metric_lines = [
        ["36 个 workload：静态候选空间压缩", "排除不可调用项，折叠等价参数"],
        ["预测与实测对应；24 个危险变异", "均被拒绝或安全降级"],
        ["i9 / K230 精确形状各 0/10 胜出", "据性能与成本决定是否采用生成路径"],
    ]
    for x, title, lines in zip(metric_xs, metric_titles, metric_lines):
        rect(x, 878, 580, 144, "white", "gray_edge")
        rect(x, 878, 6, 144, "teal", radius=0)
        text(x + 24, 922, title, 31, "teal", max_width=532)
        text(x + 24, 965, lines[0], 24, "muted", max_width=532)
        text(x + 24, 1000, lines[1], 24, "muted", max_width=532)
    text(56, 1056, "实现边界：BLIS f32/f64 复用核心生成逻辑；OpenBLAS RVV 共享契约语义，保留包内生成与适配。", 21, "muted", max_width=1810)

    doc.set_metadata({"title": "论文整体架构：AI 编译器面试讲解", "subject": "Microkernel Contract-driven MLIR schedule-space generation"})
    doc.subset_fonts()
    base = OUT / "thesis_overview"
    doc.save(base.with_suffix(".pdf"), garbage=4, deflate=True)
    # Outlined SVG is portable: the receiving computer need not have Chinese fonts.
    base.with_suffix(".svg").write_text(page.get_svg_image(text_as_path=True), encoding="utf-8")
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(base.with_suffix(".png"))
    page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(OUT / "thesis_overview_preview.png")
    (OUT / "overview_layout_qa.json").write_text(json.dumps({
        "page_size": [WIDTH, HEIGHT], "png_size": [WIDTH * 2, HEIGHT * 2],
        "text_width_and_glyph_checks": "PASS", "text_items": text_checks,
        "source": "draw_overview.py", "evidence": [
            "nwputhesis/content/thesis/graduate/chapter3.tex",
            "nwputhesis/content/thesis/graduate/chapter4.tex",
            "nwputhesis/content/thesis/graduate/chapter5.tex",
            "experiments/chapter6_contract_space_validation/processed/e1_summary.json",
            "experiments/chapter6_contract_space_validation/processed/e2_summary.json",
            "experiments/chapter6_contract_space_validation/processed/e3_summary.json",
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {base}.pdf/.svg/.png and preview; {len(text_checks)} text items checked.")


if __name__ == "__main__":
    main()
