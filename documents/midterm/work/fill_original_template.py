import os
import socket
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue


ROOT = "/buddy-mlir/jlq/thesis"
SOURCE = f"{ROOT}/西北工业大学非全日制专业学位硕士研究生论文中期报告_原始备份_20260709.doc"
TARGET = f"{ROOT}/西北工业大学非全日制专业学位硕士研究生论文中期报告.doc"


student = "冀鲁群"
student_id = "2024214293"
college = "软件学院"
major = "软件工程"
workplace = "待填写"
fill_date = "2026年7月9日"
advisor1 = "待填写"
advisor2 = "待填写"
proposal_date = "待填写"
midterm_date = "2026.07.09"
thesis_title = "面向 MLIR Transform Dialect 的 Kernel-aware GEMM 调度搜索空间生成方法"


report_rows = [
    "一、开题以来研究进度",
    "开题后，本课题先把问题收窄到一个可操作的方向：高性能 GEMM 库里的哪些实现事实，可以整理成 MLIR Transform Dialect 调度搜索空间中的约束。研究目标没有放在重写 BLIS、OpenBLAS 或 libxsmm，也没有放在重新设计调优算法。目前主要工作是读高性能库代码，梳理 microkernel、cache blocking、packing、vectorization 和 ISA 相关事实，判断哪些内容以后可以进入搜索空间生成流程。",
    "资料学习主要围绕 Level-3 BLAS、GotoBLAS/BLIS、OpenBLAS、libxsmm、MLIR Transform Dialect、Ansor、MetaSchedule 和 BaCO 展开。通过这部分学习，已经明确 GEMM 的性能不是由单个 tile size 决定的，而是和 microkernel 形状、缓存分块、packing 布局、向量化方式、边界处理以及目标指令集一起相关。这一点也决定了后面不能只摘几个参数，需要把参数所在的库实现上下文一起记录下来。",
    "目前研究仍处在专家事实提取阶段。现阶段以 BLIS 的 Haswell 平台配置作为第一个重点对象，正在整理其中与 GEMM 有关的 microkernel 注册、packm kernel、row preference、MR/NR/MC/KC/NC blocking 参数和 gemmsup 路径等信息。例如，BLIS Haswell 配置文件中可以看到不同数据类型对应的 GEMM microkernel、packing kernel 和 blocking 参数设置。这些内容已经可以作为专家事实表的候选字段，但还需要继续核对其适用条件和调用路径，暂时还没有完成规则化建模。",
    "为了避免后面只得到一堆零散参数，目前已经开始设计专家事实记录字段。初步字段包括事实来源、库名称、平台名称、数据类型、kernel 名称、microkernel 形状、blocking 参数、packing 相关信息、row/column preference、适用条件和证据位置。这样记录的好处是每个参数都能回到源代码位置，也能保留它和数据类型、平台配置之间的关系，后面再考虑是否进入 Microkernel Contract 或搜索空间约束。",
    "除专家事实提取外，已经跑通原始 Transform Dialect 与 BaCO 结合的 GEMM 调优流程，并复现了 Transform Dialect 论文实验 4.5 的相关流程。这个流程已经能够从 Transform Dialect 暴露 GEMM 调度参数，由 BaCO 采样候选配置，再完成编译、运行和测量反馈。这里跑通的是原始调优流程，可以作为后续对比用的基线；BLIS/OpenBLAS/libxsmm 中提取的专家事实还没有接入该流程。",
    "二、阶段性进展",
    "第一，研究范围已经稳定下来。课题从比较宽泛的 GEMM 自动优化问题，收敛到“专家事实驱动的 kernel-aware 搜索空间生成”问题。这样处理后，研究重点更清楚：前端使用 Transform Dialect 表达调度，调优部分沿用 BaCO，主要新增工作放在专家事实提取和搜索空间约束上。",
    "第二，已经初步梳理出需要重点记录的 GEMM 优化事实。包括 microkernel shape、MR/NR、MC/KC/NC、packing layout、row/column preference、数据类型、目标 ISA、tail 处理以及 library/microkernel 替换条件等。后面会围绕这些字段继续整理 BLIS、OpenBLAS 和 libxsmm 的实现信息。",
    "第三，BLIS Haswell 配置的分析已经开始。当前已经定位到 GEMM microkernel、packing kernel、gemmsup kernel、row preference 和 blocking 参数等信息来源。下一步还要继续核对这些信息在不同数据类型下的差异，以及它们和实际调用路径之间的关系。这个阶段的产出应当是可追溯的专家事实表，而不是最终实验结论。",
    "第四，原始 Transform Dialect + BaCO 的 GEMM 调优流程已经跑通，并完成了 Transform Dialect 论文实验 4.5 的基本复现。这个结果说明后面已有一个可以复用的基线流程。接下来可以在这个流程上逐步加入专家事实约束，再比较 generic tuning space 和 kernel-aware tuning space 的差别。",
    "第五，后续技术路线已经初步排好。先完成 BLIS/OpenBLAS/libxsmm 中专家事实的抽取和字段统一，再设计 Microkernel Contract 的核心字段；随后研究这些字段如何约束 Transform Dialect 中的 tiling、packing、vectorization 和 library replacement 参数；最后基于已经跑通的原始调优流程开展小规模对比验证。",
    "三、存在的问题",
    "第一，专家事实在高性能库中分布比较散。以 BLIS 为例，microkernel、packing kernel、blocking 参数和偏好设置并不在一个统一表里，而是和平台配置、数据类型、宏定义以及运行时上下文初始化过程放在一起。单独抄出一个参数容易漏掉它的条件，所以还需要反复对照源代码。",
    "第二，不同库的写法差异比较大。BLIS 的平台配置相对模块化，OpenBLAS 和 libxsmm 在 kernel 组织、参数来源和调用路径上又是另一套风格。后面如果要做统一的专家事实表，必须先解决字段对齐问题，不能把某个库的实现细节直接当成通用 GEMM 规律。",
    "第三，事实和规则之间的边界还需要继续判断。现在可以提取到 MR/NR、MC/KC/NC、kernel 名称、packing kernel 等事实，但这些事实不能直接等同于调度规则。哪些是必须满足的接口约束，哪些只能作为搜索空间的经验范围，哪些只是某个平台的实现细节，还需要结合更多代码和后续实验再定。",
    "第四，虽然原始 Transform Dialect + BaCO 的 GEMM 调优流程已经跑通，但它目前只是基线复现，还没有接入专家事实约束。因此，专家规则是否能够缩小搜索空间、提高候选有效率、改善收敛效率或替换成功率，现在还不能下结论。这部分需要等专家事实表和规则设计稳定后再做实验。",
    "四、解决措施与下一步计划",
    "针对专家事实分散的问题，下一步继续从 BLIS Haswell 配置入手，按数据类型、microkernel、blocking 参数、packing kernel、偏好设置和证据位置来建立记录表。每条记录都保留源代码位置和适用条件，避免后面脱离上下文使用参数。",
    "针对不同库字段不一致的问题，后面选取 OpenBLAS 的典型 GEMM kernel 路径和 libxsmm 的小矩阵 GEMM 路径做对照。比较时先不追求覆盖所有平台，而是先把字段含义和证据位置理清楚，再逐步扩展到更多数据类型和架构。",
    "针对事实到规则的转化问题，后续先把专家事实分层处理。数据类型、microkernel shape、packing layout 和 alignment 这类内容优先作为接口约束；cache blocking 范围和 row/column preference 这类内容先作为搜索空间的经验范围；暂时无法确认通用性的库内细节先保留在事实表中，不急于写入规则库。这样可以逐步形成 Microkernel Contract 和调度规则的初步设计。",
    "后续工作按四步推进：先完成 BLIS Haswell 专家事实表；再补充 OpenBLAS 和 libxsmm 的对照事实；之后设计 Microkernel Contract 字段和 Transform Dialect 参数约束映射，并接入已经跑通的 Transform Dialect + BaCO 调优流程；最后在小规模 GEMM case 上比较原始搜索空间和专家事实约束空间。实验数据以实际运行为准，不使用估计值替代。",
]


def prop(name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item


def start_office(port):
    proc = subprocess.Popen(
        [
            "soffice",
            "--headless",
            "--norestore",
            "--nofirststartwizard",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        sock = socket.socket()
        try:
            sock.connect(("127.0.0.1", port))
            sock.close()
            return proc
        except OSError:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("LibreOffice headless service did not start")


def connect_office(port):
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )
    return resolver.resolve(
        f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"
    )


def set_cell(table, name, text):
    cell = table.getCellByName(name)
    cell.setString(text)


def main():
    if not os.path.exists(SOURCE):
        raise FileNotFoundError(SOURCE)

    port = 2091
    office = start_office(port)
    try:
        ctx = connect_office(port)
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

        source_url = uno.systemPathToFileUrl(SOURCE)
        target_url = uno.systemPathToFileUrl(TARGET)
        doc = desktop.loadComponentFromURL(
            source_url,
            "_blank",
            0,
            (prop("Hidden", True),),
        )

        tables = doc.getTextTables()
        cover = tables.getByIndex(0)
        main_table = tables.getByIndex(1)
        continuation = tables.getByIndex(2)

        set_cell(cover, "B4", workplace)
        set_cell(cover, "B5", fill_date)

        set_cell(main_table, "F1", advisor1)
        set_cell(main_table, "B2", thesis_title)
        set_cell(main_table, "D2", advisor2)
        set_cell(main_table, "B3", major)
        set_cell(main_table, "D3", proposal_date)
        set_cell(main_table, "B4", "□ 工业设计    ☑ 研究论文")
        set_cell(main_table, "D4", midterm_date)

        slots = [f"A{i}" for i in range(6, 25)] + [f"A{i}" for i in range(1, 26)]
        for idx, slot in enumerate(slots):
            target_table = main_table if idx < 19 else continuation
            name = slot if idx < 19 else f"A{idx - 18}"
            set_cell(target_table, name, report_rows[idx] if idx < len(report_rows) else "")

        doc.storeAsURL(target_url, (prop("FilterName", "MS Word 97"),))
        doc.close(True)
    finally:
        office.terminate()
        try:
            office.wait(timeout=5)
        except subprocess.TimeoutExpired:
            office.kill()


if __name__ == "__main__":
    main()
