#!/usr/bin/env python3
"""Render the audience-facing architecture slide without modifying earlier figures.

Outputs a 4K PNG, embedded-font PDF, outlined SVG and a preview. Requires
PyMuPDF and the font bundled with the thesis. No compiler experiments are run.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import fitz


OUT = Path(__file__).resolve().parent
FONT = OUT.parents[1] / "nwputhesis/fonts/simhei.ttf"
WIDTH, HEIGHT = 1920, 1080
COLORS = {
    "white": "FFFFFF", "ink": "182E40", "muted": "526779",
    "teal": "087F83", "teal_dark": "086C71", "teal_bg": "EFF9F7",
    "teal_edge": "A7D7D0", "teal_light": "D7F1EC",
    "gray_bg": "F4F7FA", "gray_edge": "D9E2EA",
    "purple": "7860AC", "purple_bg": "F6F2FC",
}
ORIGINALS = [
    "draw_architecture.py", "thesis_architecture.png", "thesis_architecture.pdf",
    "thesis_architecture.svg", "thesis_architecture_preview.png",
    "architecture_layout_qa.json", "draw_overview.py", "thesis_overview.png",
    "thesis_overview.pdf", "thesis_overview.svg",
]


def hashes(names):
    return {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}


def rgb(name):
    value = COLORS.get(name, name)
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def main():
    preserved = hashes(ORIGINALS)
    doc = fitz.open()
    page = doc.new_page(width=WIDTH, height=HEIGHT)
    page.insert_font(fontname="ThesisSans", fontfile=str(FONT))
    font = fitz.Font(fontfile=str(FONT))
    checks = []

    def rect(x, y, w, h, fill="white", stroke=None, radius=.06, width=1.5):
        page.draw_rect(fitz.Rect(x, y, x + w, y + h), fill=rgb(fill),
                       color=rgb(stroke) if stroke else None,
                       width=width, radius=radius or None)

    def text(x, y, label, size=26, color="ink", max_width=None):
        length = font.text_length(label, fontsize=size)
        if max_width is not None and length > max_width + .1:
            raise ValueError(f"Text overflow {length:.1f}>{max_width}: {label}")
        if not all(font.has_glyph(ord(ch)) or ch.isspace() for ch in label):
            raise ValueError(f"Missing glyph: {label}")
        page.insert_text((x, y), label, fontsize=size, fontname="ThesisSans", color=rgb(color))
        checks.append({"text": label, "font_size": size, "x": x, "baseline_y": y, "width": length})

    def arrow(points, color="muted", dashed=False, width=3, head=10):
        pts = [fitz.Point(*point) for point in points]
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

    rect(0, 0, WIDTH, HEIGHT, radius=0)
    rect(64, 44, 58, 5, "teal", radius=0)
    text(64, 112, "面向专家微内核的 MLIR 编译与执行", 49, max_width=1792)
    text(64, 163, "将调用条件贯穿调度生成、代码变换与运行验证", 29, "muted", max_width=1792)
    page.draw_line((64, 195), (1856, 195), color=rgb("gray_edge"), width=1.3)

    text(64, 232, "约束驱动的调度生成", 23, "muted")
    rect(64, 252, 424, 142, "teal_bg", "teal_edge")
    text(88, 291, "A  调用条件建模", 30, "teal_dark", max_width=376)
    text(88, 336, "库源码 → Contract / Profile", 25, max_width=376)
    text(88, 374, "ISA · 布局 · 边界 · ABI", 25, "muted", max_width=376)

    rect(520, 252, 552, 142, "teal_bg", "teal_edge")
    text(544, 291, "B  候选空间生成", 30, "teal_dark", max_width=504)
    text(544, 336, "任务信息 + Contract → 检查与去重", 25, max_width=504)
    text(544, 374, "direct / adapt / fallback / reject", 24, "muted", max_width=504)

    rect(1104, 252, 280, 142, "gray_bg", "gray_edge")
    text(1128, 291, "BaCO 搜索器", 29, max_width=232)
    text(1128, 336, "选择候选 token", 26, max_width=232)
    text(1128, 374, "以执行耗时为目标", 24, "muted", max_width=232)

    rect(1416, 252, 440, 142, "teal_bg", "teal_edge")
    text(1440, 291, "D  验证与成本评估", 30, "teal_dark", max_width=392)
    text(1440, 336, "数值 · IR / 符号 · 运行路径", 24, max_width=392)
    text(1440, 374, "完整库对照 · 编译与调优成本", 24, "muted", max_width=392)
    arrow([(488, 323), (520, 323)], "teal", head=9)
    arrow([(1072, 323), (1104, 323)], "teal", head=9)
    arrow([(1416, 350), (1384, 350)], "purple", True, head=9)
    text(1416, 232, "验证与反馈", 23, "muted")

    # Transform is a schedule controlling the payload, not a payload IR stage.
    rect(360, 436, 640, 62, "purple_bg", "purple")
    text(382, 475, "Transform IR", 27, "purple", max_width=180)
    text(579, 475, "bufferize → packing → call", 25, "purple", max_width=399)
    arrow([(1244, 394), (1244, 417), (816, 417), (816, 436)], "purple", True, head=8)
    text(1040, 473, "候选 → 调度实例", 24, "purple", max_width=340)
    arrow([(482, 498), (482, 552)], "purple", True)
    arrow([(818, 498), (818, 552)], "purple", True)

    text(64, 527, "程序编译与执行", 23, "muted")
    xs = [64, 360, 636, 1032, 1312, 1592]
    widths = [264, 244, 364, 248, 248, 264]
    titles = ["Tensor matmul", "缓冲区化", "C  微内核接入", "标准 lowering", "编译与链接", "CPU 执行"]
    for i, (x, w, title) in enumerate(zip(xs, widths, titles)):
        own = i == 2
        rect(x, 552, w, 298, "teal_dark" if own else "gray_bg",
             None if own else "gray_edge")
        text(x + 20, 586, f"0{i + 1}", 20, "teal_light" if own else "muted")
        text(x + 20, 626, title, 28, "white" if own else "ink", max_width=w - 40)
        page.draw_line((x + 20, 646), (x + w - 20, 646),
                       color=rgb("teal" if own else "gray_edge"), width=1.2)
    for x, w, nx in zip(xs[:-1], widths[:-1], xs[1:]):
        arrow([(x + w, 724), (nx, 724)], head=9)

    text(84, 690, "%0 = linalg.matmul", 24, max_width=224)
    text(84, 732, "  ins(%A, %B : ...)", 23, max_width=224)
    text(84, 774, "  outs(%C : ...)", 23, max_width=224)
    text(84, 825, "C ← C + A × B", 25, "muted", max_width=224)

    text(380, 690, "tensor → memref", 25, max_width=204)
    text(380, 732, "linalg.matmul", 25, max_width=204)
    text(380, 774, "显式内存语义", 26, max_width=204)
    text(380, 825, "MLIR bufferization", 22, "muted", max_width=204)

    text(656, 690, "SCF 分块循环", 28, "white", max_width=324)
    text(656, 732, "A/B packing · 尾块处理", 25, "white", max_width=324)
    text(656, 774, "Transform op 绑定调用", 26, "white", max_width=324)
    text(656, 825, "func.call @BLIS_wrapper", 23, "teal_light", max_width=324)

    text(1052, 690, "SCF / MemRef / Arith", 20, max_width=208)
    text(1052, 732, "→ LLVM dialect", 26, max_width=208)
    text(1052, 774, "→ LLVM IR (.ll)", 26, max_width=208)
    text(1052, 825, "mlir-translate", 23, "muted", max_width=208)

    text(1332, 690, "LLVM IR + driver", 24, max_width=208)
    text(1332, 732, "+ ABI adapter [C]", 24, "teal_dark", max_width=208)
    text(1332, 774, "+ libblis.a", 25, max_width=208)
    text(1332, 825, "Clang → 可执行文件", 21, "muted", max_width=208)

    text(1612, 690, "生成代码 → adapter", 23, max_width=224)
    text(1612, 732, "→ BLIS 6×16 内核", 24, max_width=224)
    text(1612, 774, "输出 C · 执行耗时", 24, max_width=224)
    text(1612, 825, "微内核复用 BLIS", 23, "muted", max_width=224)
    arrow([(1724, 552), (1724, 394)], "purple", True)
    text(1740, 476, "运行证据", 24, "purple", max_width=116)

    # Fallback branches before bufferization; the BLIS route does not vectorize.
    rect(360, 901, 640, 69, "white", "gray_edge")
    text(381, 930, "Fallback：通用 tiling / 可选 vectorization", 24, "muted", max_width=598)
    text(381, 959, "tensor 调度 → bufferization", 23, "muted", max_width=598)
    arrow([(196, 850), (196, 935), (360, 935)], width=2.5)
    arrow([(1000, 935), (1156, 935), (1156, 850)], width=2.5)
    text(1312, 938, "实现路径：x86 · FP32 · BLIS 6×16", 25, "muted", max_width=544)

    page.draw_line((64, 1014), (1856, 1014), color=rgb("gray_edge"), width=1.3)
    rect(64, 1040, 17, 17, "teal_dark", radius=.15)
    text(94, 1057, "本文工作", 23, "muted")
    rect(280, 1040, 17, 17, "gray_edge", radius=.15)
    text(310, 1057, "已有工具与库", 23, "muted")
    page.draw_line((550, 1048), (600, 1048), color=rgb("purple"), width=2.8, dashes="[8 6] 0")
    text(615, 1057, "调度控制 / 测量反馈", 23, "muted")
    text(1312, 1057, "A / B / C / D  对应论文研究与实现", 23, "muted", max_width=544)

    doc.set_metadata({"title": "面向专家微内核的 MLIR 编译与执行", "subject": "Contract-driven scheduling and microkernel integration in MLIR"})
    doc.subset_fonts()
    base = OUT / "thesis_architecture_present"
    doc.save(base.with_suffix(".pdf"), garbage=4, deflate=True)
    base.with_suffix(".svg").write_text(page.get_svg_image(text_as_path=True), encoding="utf-8")
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(base.with_suffix(".png"))
    page.get_pixmap(alpha=False).save(OUT / "thesis_architecture_present_preview.png")
    spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b for line in b["lines"] for s in line["spans"]]
    assert all(page.rect.contains(fitz.Rect(s["bbox"])) for s in spans), "Text outside canvas"
    assert hashes(ORIGINALS) == preserved, "An original artifact was modified"
    (OUT / "architecture_present_qa.json").write_text(json.dumps({
        "source": Path(__file__).name,
        "page_size": [WIDTH, HEIGHT], "png_size": [WIDTH * 2, HEIGHT * 2],
        "text_width_glyph_and_page_bounds": "PASS", "text_items": checks,
        "originals_preserved": {"result": "PASS", "sha256": preserved},
        "basis": "Audience-facing simplification of thesis_architecture; same six-stage compilation chain and A/B/C/D contributions",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {base.name}.pdf/.svg/.png and preview; {len(checks)} text items checked; originals unchanged.")


if __name__ == "__main__":
    main()
