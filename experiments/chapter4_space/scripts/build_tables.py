#!/usr/bin/env python3
"""Build Chapter 4 source-data tables and XeLaTeX fragments."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from chapter4lib import PROJECT_DIR, write_csv


def tex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def write_latex(path: Path, caption: str, label: str, headers: list[str], rows: list[list[Any]], widths: str) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        f"  \\caption{{{caption}}}",
        f"  \\label{{{label}}}",
        f"  \\begin{{tabular}}{{{widths}}}",
        r"    \toprule",
        "    " + " & ".join(headers) + r" \\",
        r"    \midrule",
    ]
    lines.extend("    " + " & ".join(tex_escape(cell) for cell in row) + r" \\" for row in rows)
    lines.extend([r"    \bottomrule", r"  \end{tabular}", r"\end{table}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    tables = PROJECT_DIR / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    symbols = [
        {"symbol": "U", "type": "input/set", "definition": "原始笛卡尔候选集合"},
        {"symbol": "S_legal", "type": "set", "definition": "满足语义与 Transform 静态合法性的候选"},
        {"symbol": "gamma(s)", "type": "function", "definition": "候选到 direct/adapt/fallback/reject 的路径映射"},
        {"symbol": "S_contract", "type": "set", "definition": "路径为 direct 或 adapt 的 Contract 兼容候选"},
        {"symbol": "S_exec", "type": "set", "definition": "路径不是 reject 且存在可执行实现的候选"},
        {"symbol": "S_core", "type": "set", "definition": "满足硬约束并由软先验优先的专家核心"},
        {"symbol": "S_shell", "type": "set", "definition": "从 S_exec 减去 S_core 后确定性分层采样的探索外壳"},
        {"symbol": "S_tune", "type": "output/set", "definition": "S_core 与 S_shell 的并集"},
        {"symbol": "TaskContext", "type": "input", "definition": "shape、dtype、layout、ISA、cache、SIMD 与线程模式"},
        {"symbol": "Contract", "type": "input", "definition": "microkernel 接口、MR/NR、packing、tail 与 ABI 约束"},
        {"symbol": "Provenance", "type": "output", "definition": "候选到 Fact、Rule、Contract、原因码和测量文件的追溯记录"},
    ]
    write_csv(tables / "table4_1_symbols.csv", symbols)
    write_latex(
        tables / "table4_1_symbols.tex",
        "方法输入、输出与主要符号",
        "tab:chapter4-symbols",
        ["符号", "类型", "定义"],
        [[row["symbol"], row["type"], row["definition"]] for row in symbols],
        "p{0.16\\textwidth}p{0.16\\textwidth}p{0.58\\textwidth}",
    )

    reason_data = json.loads((PROJECT_DIR / "data" / "reason_codes.json").read_text(encoding="utf-8"))
    reasons = reason_data["reason_codes"]
    write_csv(tables / "table4_2_checker_rules.csv", reasons)
    write_latex(
        tables / "table4_2_checker_rules.tex",
        "兼容性判定维度、原因码与动作",
        "tab:chapter4-reasons",
        ["原因码", "维度", "判定结果", "含义"],
        [[row["code"], row["dimension"], row["action"], row["meaning"]] for row in reasons],
        "p{0.25\\textwidth}p{0.14\\textwidth}p{0.12\\textwidth}p{0.39\\textwidth}",
    )

    paths = [
        {
            "path": "direct",
            "contract_condition": "全部目标 Contract 条件满足",
            "action": "请求 packing 与目标 kernel 调用",
            "implemented_transform": "tiling + optional vectorization + bufferization",
            "observed_boundary": "当前无 BLIS call，观测为 fallback",
        },
        {
            "path": "adapt",
            "contract_condition": "仅存在已声明的有限 tail/K 余数差异",
            "action": "插入有限 fringe/cleanup 适配",
            "implemented_transform": "边界感知 tiled loops（affine.min）",
            "observed_boundary": "当前无 BLIS call，观测为 fallback",
        },
        {
            "path": "fallback",
            "contract_condition": "Contract 不匹配或目标接口条件缺失",
            "action": "执行通用 MLIR tiled-loop lowering",
            "implemented_transform": "generic tile + bufferization",
            "observed_boundary": "实际编译、运行并通过正确性",
        },
        {
            "path": "reject",
            "contract_condition": "语义/Transform 非法或不存在可执行 fallback",
            "action": "候选不进入调优空间",
            "implemented_transform": "不实例化",
            "observed_boundary": "静态原因码记录",
        },
    ]
    write_csv(tables / "table4_3_paths.csv", paths)
    write_latex(
        tables / "table4_3_paths.tex",
        "执行路径条件、动作与当前实现边界",
        "tab:chapter4-paths",
        ["路径", "Contract 条件", "动作", "当前 Transform/观测"],
        [[row["path"], row["contract_condition"], row["action"], row["implemented_transform"] + "；" + row["observed_boundary"]] for row in paths],
        "p{0.10\\textwidth}p{0.25\\textwidth}p{0.25\\textwidth}p{0.30\\textwidth}",
    )
    print(f"wrote tables to {tables}")


if __name__ == "__main__":
    main()
