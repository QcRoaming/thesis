#!/usr/bin/env python3
"""Render the end-to-end compiler pipeline as a font-embedded PDF, vector SVG and 4K PNG.

Uses PyMuPDF and the thesis' bundled fonts. No hardware measurements are run.
Run from any directory: python documents/interview/draw_architecture.py
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
    text(56, 48, "硕士论文 / AI 编译器面试", 22, "teal")
    text(56, 105, "从一段 matmul MLIR，到真实微内核执行", 46, max_width=1808)
    text(56, 151, "沿代码的变化讲论文：主线展示编译与执行，上方标出调度控制和研究落点。", 27, "muted")
    rect(56, 177, 17, 17, "teal", radius=.2)
    text(83, 193, "A—D：论文研究 / 实现", 21, "muted")
    rect(370, 177, 17, 17, "gray_edge", radius=.2)
    text(397, 193, "灰色：复用的编译基础设施", 21, "muted")
    page.draw_line((730, 185), (775, 185), color=rgb("purple"), width=2.6, dashes="[7 5] 0")
    text(788, 193, "紫色虚线：调度控制 / 测量反馈", 21, "muted")
    text(1510, 193, "主例：BLIS f32 6×16", 23, "teal", max_width=354)

    # Research objects belong to the control plane, not to the payload IR chain.
    rect(56, 220, 448, 154, "teal_bg", "teal_edge")
    text(76, 256, "A  调用知识建模", 29, "teal", max_width=408)
    text(76, 294, "库源码 → Fact → Contract / Profile", 22, max_width=408)
    text(76, 327, "硬条件：ISA / 布局 / tail / ABI", 23, max_width=408)
    text(76, 359, "软偏好：分块与排序；保留来源和版本", 22, "muted", max_width=408)

    rect(532, 220, 580, 154, "teal_bg", "teal_edge")
    text(552, 256, "B  Contract 驱动的候选空间", 29, "teal", max_width=540)
    text(552, 294, "Task + Contract → 约束检查 / 活性分析 / 去重", 23, max_width=540)
    text(552, 327, "direct / adapt / fallback / reject", 23, max_width=540)
    text(552, 359, "输出：候选 token、分块参数、生成义务与诊断", 22, "muted", max_width=540)

    rect(1140, 220, 258, 154, "gray_bg", "gray_edge")
    text(1158, 256, "BaCO 选择候选", 27, max_width=222)
    text(1158, 296, "复用搜索器", 24, "muted", max_width=222)
    text(1158, 332, "选中有效 token", 23, max_width=222)
    text(1158, 362, "按目标耗时搜索", 22, "muted", max_width=222)

    rect(1426, 220, 438, 154, "teal_bg", "teal_edge")
    text(1446, 256, "D  联合验证与成本评价", 28, "teal", max_width=398)
    text(1446, 294, "数值 / IR / 符号 / 实际运行路径", 22, max_width=398)
    text(1446, 327, "目标计时回传；完整库与全成本对照", 22, max_width=398)
    text(1446, 359, "回答：调用是否成立，搜索是否值得", 22, "muted", max_width=398)
    arrow([(504, 298), (532, 298)], head=8)
    arrow([(1112, 298), (1140, 298)], head=8)
    arrow([(1426, 330), (1398, 330)], "purple", True, 2.5, head=8)

    # The Transform program drives bufferization and custom materialization.
    rect(350, 419, 648, 68, "purple_bg", "purple")
    text(370, 446, "Transform IR：描述“如何变换”的调度程序", 24, "purple", max_width=608)
    text(370, 474, "bufferize → packing pass → 绑定微内核调用", 22, "purple", max_width=608)
    arrow([(1269, 374), (1269, 405), (822, 405), (822, 419)], "purple", True, 2.5, head=8)
    text(1052, 441, "选中 token → 填入参数", 21, "purple", max_width=320)
    text(1052, 474, "调度程序控制下方 IR 变换", 21, "muted", max_width=320)
    arrow([(471, 487), (471, 535)], "purple", True, 2.5)
    arrow([(810, 487), (810, 535)], "purple", True, 2.5)

    text(56, 515, "程序编译与执行主链", 24, "ink")
    # Six consecutive program/build stages; only stage 3 is a new compiler pass.
    xs = [56, 350, 622, 1028, 1314, 1600]
    widths = [264, 242, 376, 256, 256, 264]
    titles = ["1  Tensor matmul", "2  缓冲区化", "3  微内核接入 [C]", "4  标准 lowering", "5  编译与链接", "6  CPU 运行"]
    for i, (x, w, title) in enumerate(zip(xs, widths, titles)):
        fill, edge = ("teal_bg", "teal_edge") if i == 2 else ("gray_bg", "gray_edge")
        rect(x, 535, w, 300, fill, edge, radius=.05)
        text(x + 16, 575, title, 26, "teal" if i == 2 else "ink", max_width=w - 32)
        page.draw_line((x + 16, 592), (x + w - 16, 592), color=rgb(edge), width=1)
    for x, w, nx in zip(xs[:-1], widths[:-1], xs[1:]):
        arrow([(x + w, 681), (nx, 681)], "muted", width=3, head=9)

    # Types are shortened on the slide; the full valid MLIR is in the talk track.
    text(72, 628, "%0 = linalg.matmul", 23, max_width=232)
    text(72, 664, "  ins(%A, %B : ...)", 22, max_width=232)
    text(72, 700, "  outs(%C : ...)", 22, max_width=232)
    text(72, 736, "  -> tensor<?x?xf32>", 22, max_width=232)
    text(72, 788, "输入：矩阵乘加的计算语义", 19, "muted", max_width=232)
    text(72, 816, "尚未指定 packing 与微内核", 18, "muted", max_width=232)

    text(366, 628, "tensor → memref", 24, max_width=210)
    text(366, 666, "linalg.matmul", 23, max_width=210)
    text(366, 702, "操作内存中的 A/B/C", 22, max_width=210)
    text(366, 738, "memref<?x?xf32>", 23, max_width=210)
    text(366, 788, "one_shot_bufferize", 21, "muted", max_width=210)
    text(366, 816, "复用 MLIR 缓冲区化", 20, "muted", max_width=210)

    text(638, 626, "(a) packing / fringe pass", 24, "teal", max_width=344)
    text(638, 659, "SCF 循环 + A/B panel packing", 22, max_width=344)
    text(638, 692, "生成 direct / fringe 占位调用", 22, max_width=344)
    text(638, 735, "(b) Transform op 绑定 callee", 22, "teal", max_width=344)
    text(638, 770, "func.call @BLIS_wrapper(...)", 22, max_width=344)
    text(638, 815, "产物：SCF / MemRef / Arith / func.call", 18, "muted", max_width=344)

    text(1044, 626, "SCF → CF", 25, max_width=224)
    text(1044, 662, "MemRef / func / arith", 20, max_width=224)
    text(1044, 698, "→ LLVM dialect", 25, max_width=224)
    text(1044, 734, "    ↓ mlir-translate", 20, "muted", max_width=224)
    text(1044, 770, "LLVM IR (.ll)", 25, max_width=224)
    text(1044, 816, "复用标准转换与翻译工具", 19, "muted", max_width=224)

    text(1330, 626, "clang++ -O3", 25, max_width=224)
    text(1330, 664, "LLVM IR + driver", 23, max_width=224)
    text(1330, 702, "+ ABI adapter [C]", 23, "teal", max_width=224)
    text(1330, 740, "+ libblis.a", 25, max_width=224)
    text(1330, 778, "→ 可执行文件", 25, max_width=224)
    text(1330, 816, "adapter 对接 BLIS ABI", 20, "muted", max_width=224)

    text(1616, 626, "driver 调用 GEMM", 23, max_width=232)
    text(1616, 664, "→ ABI adapter [C]", 23, "teal", max_width=232)
    text(1616, 702, "→ BLIS 6×16 微内核", 23, max_width=232)
    text(1616, 740, "输出 C + 执行耗时", 23, max_width=232)
    text(1616, 778, "记录真实调用与边界路径", 21, max_width=232)
    text(1616, 816, "微内核本体由 BLIS 提供", 20, "muted", max_width=232)
    arrow([(1732, 535), (1732, 374)], "purple", True, 2.5)
    text(1747, 454, "运行证据", 22, "purple", max_width=115)

    # An alternative route, controlled by the path decision, bypasses BLIS materialization.
    rect(310, 867, 688, 80, "white", "gray_edge")
    text(330, 900, "Fallback：通用 tiling / 可选 vectorization", 23, "muted", max_width=648)
    text(330, 931, "先在 tensor 上调度，再 bufferization；接回标准 lowering", 21, "muted", max_width=648)
    arrow([(188, 835), (188, 907), (310, 907)], "muted", width=2.2)
    arrow([(998, 907), (1156, 907), (1156, 835)], "muted", width=2.2)
    text(57, 968, "路径由 B 判定；reject 在候选阶段停止，不进入编译执行。", 20, "muted", max_width=1110)
    text(1240, 883, "真实被调用的库内符号：", 21, "teal", max_width=624)
    text(1240, 918, "bli_sgemm_haswell_asm_6x16", 27, "ink", max_width=624)
    text(1240, 946, "尾块由生成代码处理；wrapper 对接 ABI", 21, "muted", max_width=624)

    rect(56, 978, 1808, 64, "teal_bg", "teal_edge")
    text(78, 1018, "论文落点：在通用 lowering 前生成可调用的候选并物化微内核接入；在执行后验证路径、性能与搜索成本。", 27, "teal", max_width=1764)
    text(56, 1070, "图中 IR 为节选示意。BLIS f64 复用核心生成逻辑；OpenBLAS RVV 保留包内生成与适配，不能套用此 BLIS pass。", 20, "muted", max_width=1808)

    doc.set_metadata({"title": "从 matmul MLIR 到真实微内核执行：论文研究落点", "subject": "Payload compilation pipeline and Contract-driven Transform control"})
    doc.subset_fonts()
    base = OUT / "thesis_architecture"
    doc.save(base.with_suffix(".pdf"), garbage=4, deflate=True)
    base.with_suffix(".svg").write_text(page.get_svg_image(text_as_path=True), encoding="utf-8")
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(base.with_suffix(".png"))
    page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(OUT / "thesis_architecture_preview.png")
    (OUT / "architecture_layout_qa.json").write_text(json.dumps({
        "page_size": [WIDTH, HEIGHT], "png_size": [WIDTH * 2, HEIGHT * 2],
        "text_width_and_glyph_checks": "PASS", "text_items": text_checks,
        "source": "draw_architecture.py", "diagram_model": "tensor matmul to executable with separate Transform control",
        "evidence": [
            "experiments/chapter4_5_integrated/scripts/run_integrated_pipeline.py",
            "experiments/chapter5_blis_adapter/scripts/run_chapter5.py",
            "compiler_snapshot/buddy-mlir/midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp",
            "compiler_snapshot/buddy-mlir/midend/lib/Dialect/Microkernel/TransformOps.cpp",
            "experiments/chapter5_blis_adapter/runtime/blis_microkernel_adapter.cpp",
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {base}.pdf/.svg/.png and preview; {len(text_checks)} text items checked.")


if __name__ == "__main__":
    main()
