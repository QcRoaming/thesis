from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = "/buddy-mlir/jlq/thesis"
OUT_DOCX = f"{ROOT}/西北工业大学非全日制专业学位硕士研究生论文中期报告_研究进度版.docx"


student = "冀鲁群"
student_id = "2024214293"
college = "软件学院"
major = "软件工程"
workplace = "待填写"
fill_date = "2026年7月9日"
advisor1 = "待填写"
advisor2 = "待填写"
proposal_date = "待填写"
midterm_date = "2026年7月9日"
midterm_date_short = "2026.07.09"
thesis_title = "面向 MLIR Transform Dialect 的 Kernel-aware GEMM 调度搜索空间生成方法"


report_sections = [
    (
        "一、开题以来研究进度",
        [
            "开题后，本课题先把问题收窄到一个可操作的方向：高性能 GEMM 库里的哪些实现事实，可以整理成 MLIR Transform Dialect 调度搜索空间中的约束。研究目标没有放在重写 BLIS、OpenBLAS 或 libxsmm，也没有放在重新设计调优算法。目前主要工作是读高性能库代码，梳理 microkernel、cache blocking、packing、vectorization 和 ISA 相关事实，判断哪些内容以后可以进入搜索空间生成流程。",
            "资料学习主要围绕 Level-3 BLAS、GotoBLAS/BLIS、OpenBLAS、libxsmm、MLIR Transform Dialect、Ansor、MetaSchedule 和 BaCO 展开。通过这部分学习，已经明确 GEMM 的性能不是由单个 tile size 决定的，而是和 microkernel 形状、缓存分块、packing 布局、向量化方式、边界处理以及目标指令集一起相关。这一点也决定了后面不能只摘几个参数，需要把参数所在的库实现上下文一起记录下来。",
            "目前研究仍处在专家事实提取阶段。现阶段以 BLIS 的 Haswell 平台配置作为第一个重点对象，正在整理其中与 GEMM 有关的 microkernel 注册、packm kernel、row preference、MR/NR/MC/KC/NC blocking 参数和 gemmsup 路径等信息。例如，BLIS Haswell 配置文件中可以看到不同数据类型对应的 GEMM microkernel、packing kernel 和 blocking 参数设置。这些内容已经可以作为专家事实表的候选字段，但还需要继续核对其适用条件和调用路径，暂时还没有完成规则化建模。",
            "为了避免后面只得到一堆零散参数，目前已经开始设计专家事实记录字段。初步字段包括事实来源、库名称、平台名称、数据类型、kernel 名称、microkernel 形状、blocking 参数、packing 相关信息、row/column preference、适用条件和证据位置。这样记录的好处是每个参数都能回到源代码位置，也能保留它和数据类型、平台配置之间的关系，后面再考虑是否进入 Microkernel Contract 或搜索空间约束。",
            "除专家事实提取外，已经跑通原始 Transform Dialect 与 BaCO 结合的 GEMM 调优流程，并复现了 Transform Dialect 论文实验 4.5 的相关流程。这个流程已经能够从 Transform Dialect 暴露 GEMM 调度参数，由 BaCO 采样候选配置，再完成编译、运行和测量反馈。这里跑通的是原始调优流程，可以作为后续对比用的基线；BLIS/OpenBLAS/libxsmm 中提取的专家事实还没有接入该流程。",
        ],
    ),
    (
        "二、阶段性进展",
        [
            "第一，研究范围已经稳定下来。课题从比较宽泛的 GEMM 自动优化问题，收敛到“专家事实驱动的 kernel-aware 搜索空间生成”问题。这样处理后，研究重点更清楚：前端使用 Transform Dialect 表达调度，调优部分沿用 BaCO，主要新增工作放在专家事实提取和搜索空间约束上。",
            "第二，已经初步梳理出需要重点记录的 GEMM 优化事实。包括 microkernel shape、MR/NR、MC/KC/NC、packing layout、row/column preference、数据类型、目标 ISA、tail 处理以及 library/microkernel 替换条件等。后面会围绕这些字段继续整理 BLIS、OpenBLAS 和 libxsmm 的实现信息。",
            "第三，BLIS Haswell 配置的分析已经开始。当前已经定位到 GEMM microkernel、packing kernel、gemmsup kernel、row preference 和 blocking 参数等信息来源。下一步还要继续核对这些信息在不同数据类型下的差异，以及它们和实际调用路径之间的关系。这个阶段的产出应当是可追溯的专家事实表，而不是最终实验结论。",
            "第四，原始 Transform Dialect + BaCO 的 GEMM 调优流程已经跑通，并完成了 Transform Dialect 论文实验 4.5 的基本复现。这个结果说明后面已有一个可以复用的基线流程。接下来可以在这个流程上逐步加入专家事实约束，再比较 generic tuning space 和 kernel-aware tuning space 的差别。",
            "第五，后续技术路线已经初步排好。先完成 BLIS/OpenBLAS/libxsmm 中专家事实的抽取和字段统一，再设计 Microkernel Contract 的核心字段；随后研究这些字段如何约束 Transform Dialect 中的 tiling、packing、vectorization 和 library replacement 参数；最后基于已经跑通的原始调优流程开展小规模对比验证。",
        ],
    ),
    (
        "三、存在的问题",
        [
            "第一，专家事实在高性能库中分布比较散。以 BLIS 为例，microkernel、packing kernel、blocking 参数和偏好设置并不在一个统一表里，而是和平台配置、数据类型、宏定义以及运行时上下文初始化过程放在一起。单独抄出一个参数容易漏掉它的条件，所以还需要反复对照源代码。",
            "第二，不同库的写法差异比较大。BLIS 的平台配置相对模块化，OpenBLAS 和 libxsmm 在 kernel 组织、参数来源和调用路径上又是另一套风格。后面如果要做统一的专家事实表，必须先解决字段对齐问题，不能把某个库的实现细节直接当成通用 GEMM 规律。",
            "第三，事实和规则之间的边界还需要继续判断。现在可以提取到 MR/NR、MC/KC/NC、kernel 名称、packing kernel 等事实，但这些事实不能直接等同于调度规则。哪些是必须满足的接口约束，哪些只能作为搜索空间的经验范围，哪些只是某个平台的实现细节，还需要结合更多代码和后续实验再定。",
            "第四，虽然原始 Transform Dialect + BaCO 的 GEMM 调优流程已经跑通，但它目前只是基线复现，还没有接入专家事实约束。因此，专家规则是否能够缩小搜索空间、提高候选有效率、改善收敛效率或替换成功率，现在还不能下结论。这部分需要等专家事实表和规则设计稳定后再做实验。",
        ],
    ),
    (
        "四、解决措施与下一步计划",
        [
            "针对专家事实分散的问题，下一步继续从 BLIS Haswell 配置入手，按数据类型、microkernel、blocking 参数、packing kernel、偏好设置和证据位置来建立记录表。每条记录都保留源代码位置和适用条件，避免后面脱离上下文使用参数。",
            "针对不同库字段不一致的问题，后面选取 OpenBLAS 的典型 GEMM kernel 路径和 libxsmm 的小矩阵 GEMM 路径做对照。比较时先不追求覆盖所有平台，而是先把字段含义和证据位置理清楚，再逐步扩展到更多数据类型和架构。",
            "针对事实到规则的转化问题，后续先把专家事实分层处理。数据类型、microkernel shape、packing layout 和 alignment 这类内容优先作为接口约束；cache blocking 范围和 row/column preference 这类内容先作为搜索空间的经验范围；暂时无法确认通用性的库内细节先保留在事实表中，不急于写入规则库。这样可以逐步形成 Microkernel Contract 和调度规则的初步设计。",
            "后续工作按四步推进：先完成 BLIS Haswell 专家事实表；再补充 OpenBLAS 和 libxsmm 的对照事实；之后设计 Microkernel Contract 字段和 Transform Dialect 参数约束映射，并接入已经跑通的 Transform Dialect + BaCO 调优流程；最后在小规模 GEMM case 上比较原始搜索空间和专家事实约束空间。实验数据以实际运行为准，不使用估计值替代。",
        ],
    ),
]


def set_run_font(run, size=10.5, bold=False, font="宋体"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


def set_cell_shading(cell, fill="F2F2F2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_width(cell, width_cm):
    cell.width = Cm(width_cm)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:type"), "dxa")
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))


def set_fixed_table(table, width_cm=None):
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_layout = tbl_pr.first_child_found_in("w:tblLayout")
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")
    if width_cm is not None:
        tbl_w = tbl_pr.first_child_found_in("w:tblW")
        if tbl_w is None:
            tbl_w = OxmlElement("w:tblW")
            tbl_pr.append(tbl_w)
        tbl_w.set(qn("w:type"), "dxa")
        tbl_w.set(qn("w:w"), str(int(width_cm * 567)))


def set_row_widths(row, widths):
    for cell, width in zip(row.cells, widths):
        set_cell_width(cell, width)


def set_cell_text(cell, text, size=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, font="宋体"):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, font=font)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def add_para(doc, text="", size=10.5, bold=False, align=None, first_line=False, space_after=0):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.2
    if first_line:
        pf.first_line_indent = Pt(21)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)
    return p


def add_cell_para(cell, text, size=10.5, bold=False, first_line=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = cell.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(2)
    pf.line_spacing = 1.18
    if first_line:
        pf.first_line_indent = Pt(21)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)
    return p


def set_table_borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")


doc = Document()
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.2)
section.left_margin = Cm(2.8)
section.right_margin = Cm(2.5)

styles = doc.styles
styles["Normal"].font.name = "宋体"
styles["Normal"].font.size = Pt(10.5)
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

add_para(doc, "表4.", size=10.5, align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, f"学号：{student_id}", size=10.5, align=WD_ALIGN_PARAGRAPH.RIGHT)
for _ in range(3):
    add_para(doc, "")
add_para(doc, "西 北 工 业 大 学", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
add_para(doc, "非全日制专业学位硕士研究生论文中期报告", size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
for _ in range(5):
    add_para(doc, "")

cover = doc.add_table(rows=5, cols=2)
cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_fixed_table(cover, width_cm=10)
set_table_borders(cover)
cover_data = [
    ("学       院", college),
    ("专业或领域", major),
    ("姓       名", student),
    ("所 在 单 位", workplace),
    ("填 表 日 期", fill_date),
]
for r, (k, v) in enumerate(cover_data):
    set_row_widths(cover.rows[r], [3.0, 7.0])
    set_cell_text(cover.cell(r, 0), k, bold=True)
    set_cell_text(cover.cell(r, 1), v)

for _ in range(8):
    add_para(doc, "")
add_para(doc, "研  究  生  院", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_page_break()

info = doc.add_table(rows=6, cols=6)
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info_widths = [2.2, 2.3, 1.7, 3.0, 2.8, 2.5]
set_fixed_table(info, width_cm=sum(info_widths))
set_table_borders(info)

for row in info.rows:
    set_row_widths(row, info_widths)
    for cell in row.cells:
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

row0 = info.rows[0].cells
row0_values = [
    ("姓    名", 9.5, True),
    (student, 9.5, False),
    ("学 号", 9.5, True),
    (student_id, 8.0, False),
    ("第一指导教师", 9.0, True),
    (advisor1, 9.5, False),
]
for idx, (text, size, bold) in enumerate(row0_values):
    set_cell_text(row0[idx], text, size=size, bold=bold)

row1 = info.rows[1].cells
set_cell_text(row1[0], "论文题目", size=9.5, bold=True)
title_cell = row1[1].merge(row1[3])
set_cell_text(title_cell, thesis_title, size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT)
set_cell_text(row1[4], "第二指导教师", size=9.5, bold=True)
set_cell_text(row1[5], advisor2, size=9.5)

row2 = info.rows[2].cells
set_cell_text(row2[0], "工程领域", size=9.5, bold=True)
field_cell = row2[1].merge(row2[3])
set_cell_text(field_cell, major, size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT)
set_cell_text(row2[4], "论文开题时间", size=9.5, bold=True)
set_cell_text(row2[5], proposal_date, size=9.5)

row3 = info.rows[3].cells
set_cell_text(row3[0], "论文形式", size=9.5, bold=True)
form_cell = row3[1].merge(row3[3])
set_cell_text(form_cell, "□ 工业设计    ☑ 研究论文", size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT)
set_cell_text(row3[4], "中期报告时间", size=9.5, bold=True)
set_cell_text(row3[5], midterm_date_short, size=8.0)

heading = info.rows[4].cells[0].merge(info.rows[4].cells[5])
set_cell_text(
    heading,
    "论文（报告）开题以来情况报告：（包括论文的进度、存在的问题、解决问题的措施）",
    size=9.5,
    bold=True,
    align=WD_ALIGN_PARAGRAPH.LEFT,
)
set_cell_shading(heading)

body = info.rows[5].cells[0].merge(info.rows[5].cells[5])
body.text = ""
for title, paragraphs in report_sections:
    add_cell_para(body, title, bold=True, first_line=False)
    for para in paragraphs:
        add_cell_para(body, para, first_line=True)

doc.add_paragraph()

opinion = doc.add_table(rows=2, cols=2)
opinion.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_fixed_table(opinion, width_cm=sum(info_widths))
set_table_borders(opinion)
for row in opinion.rows:
    set_row_widths(row, [2.2, sum(info_widths) - 2.2])
set_cell_text(opinion.cell(0, 0), "第二导师意见", bold=True)
opinion.cell(0, 0).width = Cm(2.2)
opinion.cell(0, 1).text = ""
add_cell_para(opinion.cell(0, 1), "综合评价意见：", bold=True)
for _ in range(5):
    add_cell_para(opinion.cell(0, 1), "")
add_cell_para(opinion.cell(0, 1), "指导教师（签字）：")
add_cell_para(opinion.cell(0, 1), "年    月    日")
set_cell_text(opinion.cell(1, 0), "备注", bold=True)
set_cell_text(opinion.cell(1, 1), "")

for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    set_run_font(run, size=run.font.size.pt if run.font.size else 10.5, bold=run.bold)

doc.core_properties.title = "西北工业大学非全日制专业学位硕士研究生论文中期报告"
doc.core_properties.author = student
doc.save(OUT_DOCX)
print(OUT_DOCX)
