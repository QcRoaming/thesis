#!/usr/bin/env python3
"""Extract source-backed SGEMM knowledge from BLIS and OpenBLAS.

The output deliberately separates backend compatibility contracts from
performance hints.  Conflicting microkernel ABIs remain independent contracts;
cache blocking values are retained as soft, source-specific observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
THESIS_DIR = PROJECT_DIR.parents[1]
DEFAULT_BLIS = THESIS_DIR / "blis" / "blis"
DEFAULT_OPENBLAS = THESIS_DIR / "third_party" / "OpenBLAS"
CHAPTER3_FACTS = THESIS_DIR / "experiments" / "chapter3_rules" / "data" / "expert_facts.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def source_line(path: Path, pattern: str) -> int:
    regex = re.compile(pattern)
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if regex.search(text):
            return number
    raise ValueError(f"missing source evidence {pattern!r} in {path}")


def evidence(root: Path, path: Path, pattern: str, kind: str) -> dict[str, Any]:
    return {
        "file": path.relative_to(root).as_posix(),
        "line": source_line(path, pattern),
        "kind": kind,
        "sha256": sha256(path),
    }


def cpp_macros(openblas: Path, target_macro: str, extra: list[str] | None = None) -> dict[str, str]:
    command = ["gcc", "-E", "-dM", "-x", "c", f"-D{target_macro}"]
    command.extend(f"-D{name}" for name in (extra or []))
    command.append(str(openblas / "param.h"))
    output = subprocess.check_output(command, text=True)
    macros: dict[str, str] = {}
    for line in output.splitlines():
        match = re.match(r"#define\s+(\w+)\s+(.+)$", line)
        if match:
            macros[match.group(1)] = match.group(2).strip()
    return macros


def make_variables(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Z0-9_]+)\s*(?::|\?)?=\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def expand_make(value: str, variables: dict[str, str]) -> str:
    for _ in range(8):
        updated = re.sub(
            r"\$\((\w+)\)", lambda match: variables.get(match.group(1), match.group(0)), value
        )
        if updated == value:
            return value
        value = updated
    return value


def int_macro(macros: dict[str, str], name: str) -> int:
    value = macros[name]
    if not re.fullmatch(r"\d+", value):
        raise ValueError(f"{name} is not an integer literal: {value}")
    return int(value)


def openblas_fact(openblas: Path, arch: str) -> dict[str, Any]:
    if arch == "haswell":
        macro = "HASWELL"
        kernel_map = openblas / "kernel" / "x86_64" / "KERNEL.HASWELL"
        required_features = ["avx2", "fma"]
        machine = "x86_64"
        compiler_flags = "-march=haswell"
        target_id = "haswell"
        extra: list[str] = []
    elif arch == "riscv64_zvl128b":
        macro = "RISCV64_ZVL128B"
        kernel_map = openblas / "kernel" / "riscv64" / "KERNEL.RISCV64_ZVL128B"
        required_features = ["rv64gc", "rvv", "zvl128b"]
        machine = "riscv64"
        compiler_flags = "-march=rv64imafdcv -mabi=lp64d"
        target_id = "riscv64_zvl128b"
        extra = []
    else:
        raise ValueError(arch)

    macros = cpp_macros(openblas, macro, extra)
    variables = make_variables(kernel_map)
    variables.update(
        {
            "SGEMM_UNROLL_M": macros["SGEMM_DEFAULT_UNROLL_M"],
            "SGEMM_UNROLL_N": macros["SGEMM_DEFAULT_UNROLL_N"],
        }
    )
    kernel_file = expand_make(variables["SGEMMKERNEL"], variables)
    packing = {
        name.lower(): expand_make(value, variables)
        for name, value in variables.items()
        if name in {"SGEMMINCOPY", "SGEMMITCOPY", "SGEMMONCOPY", "SGEMMOTCOPY"}
    }
    param = openblas / "param.h"
    block_values: dict[str, int | str] = {}
    for short in ("P", "Q", "R"):
        raw = macros[f"SGEMM_DEFAULT_{short}"]
        block_values[short.lower()] = int(raw) if raw.isdigit() else raw

    fact_id = f"openblas.{target_id}.gemm.f32"
    return {
        "id": fact_id,
        "library": "OpenBLAS",
        "operation": "gemm",
        "dtype": "f32",
        "target": {
            "architecture": target_id,
            "machine": machine,
            "required_features": required_features,
        },
        "compatibility_knowledge": {
            "microkernel": {
                "source": kernel_file,
                "mr": int_macro(macros, "SGEMM_DEFAULT_UNROLL_M"),
                "nr": int_macro(macros, "SGEMM_DEFAULT_UNROLL_N"),
            },
            "packing": {"required": True, "kernels": packing},
            "call_convention": "OpenBLAS internal GEMM kernel ABI",
            "public_entry": "cblas_sgemm",
            "compiler_flags": compiler_flags,
        },
        "performance_knowledge": {
            "kind": "soft_prior",
            "native_parameter_names": "OpenBLAS P/Q/R",
            "blocking": block_values,
            "runtime_derived": [name for name, value in block_values.items() if isinstance(value, str)],
        },
        "evidence": [
            evidence(openblas, param, rf"^#define SGEMM_DEFAULT_UNROLL_M {macros['SGEMM_DEFAULT_UNROLL_M']}$", "mr_value"),
            evidence(openblas, param, rf"^#define SGEMM_DEFAULT_UNROLL_N {macros['SGEMM_DEFAULT_UNROLL_N']}$", "nr_value"),
            evidence(openblas, param, rf"^#define SGEMM_DEFAULT_P {macros['SGEMM_DEFAULT_P']}$", "p_value"),
            evidence(openblas, param, rf"^#define SGEMM_DEFAULT_Q {macros['SGEMM_DEFAULT_Q']}$", "q_value"),
            evidence(openblas, param, rf"^#define SGEMM_DEFAULT_R {macros['SGEMM_DEFAULT_R']}$", "r_value"),
            evidence(openblas, kernel_map, r"^SGEMMKERNEL\s*=", "kernel_mapping"),
            evidence(openblas, kernel_map, r"^SGEMMONCOPY\s*=", "packing_mapping"),
        ],
    }


def blis_haswell_fact(blis: Path) -> dict[str, Any]:
    document = yaml.safe_load(CHAPTER3_FACTS.read_text(encoding="utf-8"))
    source = next(item for item in document["facts"] if item["id"] == "blis.haswell.gemm.f32")
    return {
        "id": source["id"],
        "library": "BLIS",
        "operation": "gemm",
        "dtype": "f32",
        "target": source["target"],
        "compatibility_knowledge": {
            "microkernel": source["microkernel"],
            "packing": {
                "required": True,
                "kernel": source["packing"]["kernel"],
                "a_panel": source["packing"]["a_panel"],
                "b_panel": source["packing"]["b_panel"],
            },
            "call_convention": "BLIS GEMM_UKR ABI",
            "public_entry": "bli_sgemm",
            "compiler_flags": source["vectorization"]["compiler_flags"],
        },
        "performance_knowledge": {
            "kind": "soft_prior",
            "native_parameter_names": "BLIS MC/KC/NC",
            "blocking": source["cache_blocking"],
            "runtime_derived": [],
        },
        "evidence": [
            {**entry, "sha256": sha256(blis / entry["file"])} for entry in source["evidence"]
        ],
    }


def blis_rvv_fact(blis: Path) -> dict[str, Any]:
    context = blis / "config" / "rv64iv" / "bli_cntx_init_rv64iv.c"
    wrapper = blis / "kernels" / "rviv" / "3" / "bli_sgemm_rviv_4vx4.c"
    assembly = blis / "kernels" / "rviv" / "3" / "bli_sgemm_rviv_asm_4vx4.S"
    text = context.read_text(encoding="utf-8")
    required = [
        r"const uint32_t v = get_vlenb\(\) / sizeof\(float\)",
        r"const uint32_t mr_s = 4 \* v",
        r"BLIS_GEMM_UKR, BLIS_FLOAT,\s+bli_sgemm_rviv_4vx4",
        r"BLIS_GEMM_UKR_ROW_PREF, BLIS_FLOAT,\s+FALSE",
        r"BLIS_NR \],\s+4,",
        r"BLIS_MC \],\s+20\*mr_s",
        r"BLIS_KC \],\s+640,",
        r"BLIS_NC \],\s+3072,",
    ]
    for pattern in required:
        if not re.search(pattern, text):
            raise ValueError(f"BLIS rv64iv source no longer matches {pattern}")
    vlen_bits = 128
    lanes = vlen_bits // 32
    mr, nr = 4 * lanes, 4
    return {
        "id": "blis.rv64iv_vlen128.gemm.f32",
        "library": "BLIS",
        "operation": "gemm",
        "dtype": "f32",
        "target": {
            "architecture": "rv64iv_vlen128",
            "machine": "riscv64",
            "required_features": ["rv64gc", "rvv", "zvl128b"],
            "deployment_target": "K230 C908 big core",
            "assumed_vlen_bits": vlen_bits,
        },
        "compatibility_knowledge": {
            "microkernel": {"symbol": "bli_sgemm_rviv_4vx4", "mr": mr, "nr": nr},
            "packing": {"required": True, "a_panel": f"{mr}xkc", "b_panel": f"kcx{nr}"},
            "output_layout": "column_major_required_by_kernel_wrapper",
            "output_stride_constraint": "rs_c == 1",
            "call_convention": "BLIS GEMM_UKR ABI",
            "public_entry": "bli_sgemm",
            "compiler_flags": "-march=rv64gcv_zvl128b -mabi=lp64d",
        },
        "performance_knowledge": {
            "kind": "soft_prior",
            "native_parameter_names": "BLIS MC/KC/NC",
            "blocking": {"mc": 20 * mr, "kc": 640, "nc": 3072},
            "runtime_derived": ["mr=4*(VLEN/32)"],
        },
        "evidence": [
            evidence(blis, context, r"const uint32_t v = get_vlenb", "vlen_query"),
            evidence(blis, context, r"const uint32_t mr_s = 4 \* v", "mr_formula"),
            evidence(blis, context, r"BLIS_GEMM_UKR, BLIS_FLOAT", "kernel_registration"),
            evidence(blis, context, r"BLIS_GEMM_UKR_ROW_PREF, BLIS_FLOAT", "storage_preference"),
            evidence(blis, context, r"BLIS_NR \],\s+4,", "nr_value"),
            evidence(blis, context, r"BLIS_MC \],\s+20\*mr_s", "mc_formula"),
            evidence(blis, context, r"BLIS_KC \],\s+640,", "kc_value"),
            evidence(blis, context, r"BLIS_NC \],\s+3072,", "nc_value"),
            evidence(blis, wrapper, r"GEMM_UKR_SETUP_CT\( s, mr, nr, false \)", "kernel_contract"),
            evidence(blis, wrapper, r"assert\( rs_c == 1 \)", "output_stride_contract"),
            evidence(blis, assembly, r"REALNAME bli_sgemm_rviv_asm_4vx4", "assembly_definition"),
        ],
    }


def contract(fact: dict[str, Any]) -> dict[str, Any]:
    compatibility = fact["compatibility_knowledge"]
    kernel = compatibility["microkernel"]
    return {
        "id": fact["id"].replace(".", "_") + "_contract",
        "fact_id": fact["id"],
        "library": fact["library"],
        "operation": "linalg.matmul",
        "dtype": fact["dtype"],
        "target": fact["target"],
        "kernel": kernel,
        "packing": compatibility["packing"],
        "layout": {
            key: compatibility[key]
            for key in ("output_layout", "output_stride_constraint")
            if key in compatibility
        },
        "call_convention": compatibility["call_convention"],
        "public_entry": compatibility["public_entry"],
        "fallback_path": "generic_mlir_tiled_vectorized_loop",
        "compatibility_policy": "hard_backend_specific",
        "performance_hint_policy": "soft_online_calibrated",
    }


def conflicts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {fact["id"]: fact for fact in facts}

    def tile(fact_id: str) -> str:
        kernel = by_id[fact_id]["compatibility_knowledge"]["microkernel"]
        return f"{kernel['mr']}x{kernel['nr']}"

    return [
        {
            "id": "haswell_sgemm_register_tile",
            "scope": "same ISA family and dtype",
            "knowledge_class": "compatibility",
            "observations": {
                "blis.haswell.gemm.f32": tile("blis.haswell.gemm.f32"),
                "openblas.haswell.gemm.f32": tile("openblas.haswell.gemm.f32"),
            },
            "resolution": "retain two backend-specific hard contracts",
        },
        {
            "id": "haswell_sgemm_cache_blocking",
            "scope": "same ISA family and dtype",
            "knowledge_class": "performance",
            "observations": {
                fact_id: by_id[fact_id]["performance_knowledge"]["blocking"]
                for fact_id in ("blis.haswell.gemm.f32", "openblas.haswell.gemm.f32")
            },
            "resolution": "retain as source-labelled soft priors and calibrate online",
        },
        {
            "id": "rvv128_sgemm_register_tile",
            "scope": "RVV with VLEN=128 and f32",
            "knowledge_class": "compatibility",
            "observations": {
                "blis.rv64iv_vlen128.gemm.f32": tile("blis.rv64iv_vlen128.gemm.f32"),
                "openblas.riscv64_zvl128b.gemm.f32": tile("openblas.riscv64_zvl128b.gemm.f32"),
            },
            "resolution": "retain two backend-specific hard contracts",
        },
        {
            "id": "rvv128_sgemm_cache_blocking",
            "scope": "RVV with VLEN=128 and f32",
            "knowledge_class": "performance",
            "observations": {
                fact_id: by_id[fact_id]["performance_knowledge"]["blocking"]
                for fact_id in (
                    "blis.rv64iv_vlen128.gemm.f32",
                    "openblas.riscv64_zvl128b.gemm.f32",
                )
            },
            "resolution": "retain as source-labelled soft priors and calibrate on K230",
        },
    ]


def write_report(facts: list[dict[str, Any]], conflict_rows: list[dict[str, Any]], revisions: dict[str, str]) -> None:
    lines = [
        "# Multi-source Expert Knowledge Results",
        "",
        "## Source revisions",
        "",
        f"- BLIS: `{revisions['BLIS']}`",
        f"- OpenBLAS: `{revisions['OpenBLAS']}`",
        "",
        "## Extracted SGEMM contracts",
        "",
        "| Target | Library | MR x NR | Blocking | Knowledge treatment |",
        "|---|---|---:|---|---|",
    ]
    for fact in facts:
        kernel = fact["compatibility_knowledge"]["microkernel"]
        blocking = fact["performance_knowledge"]["blocking"]
        lines.append(
            f"| {fact['target']['architecture']} | {fact['library']} | "
            f"{kernel['mr']} x {kernel['nr']} | `{json.dumps(blocking, sort_keys=True)}` | "
            "tile/ABI hard; blocking soft |"
        )
    lines.extend(
        [
            "",
            "## Conflict audit",
            "",
            f"The extractor found **{len(conflict_rows)}** explicit cross-source conflicts. "
            "Register-tile conflicts are not merged because each tile belongs to a different "
            "packing and call ABI. Blocking conflicts remain source-labelled soft priors for "
            "offline or online calibration.",
            "",
            "## Claim boundary",
            "",
            "This package proves reproducible extraction, provenance and conflict handling. "
            "It does not claim that one library's performance parameters transfer unchanged "
            "to another library, compiler pipeline or machine. Runtime library validation and "
            "K230 ELF generation are recorded by their own experiment packages.",
        ]
    )
    report = PROJECT_DIR / "reports" / "multisource_results.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blis-root", type=Path, default=DEFAULT_BLIS)
    parser.add_argument("--openblas-root", type=Path, default=DEFAULT_OPENBLAS)
    args = parser.parse_args()

    facts = [
        blis_haswell_fact(args.blis_root),
        blis_rvv_fact(args.blis_root),
        openblas_fact(args.openblas_root, "haswell"),
        openblas_fact(args.openblas_root, "riscv64_zvl128b"),
    ]
    contract_rows = [contract(fact) for fact in facts]
    conflict_rows = conflicts(facts)
    revisions = {
        "BLIS": git_revision(args.blis_root),
        "OpenBLAS": git_revision(args.openblas_root),
    }
    source_roots = {
        "BLIS": {"path": str(args.blis_root), "revision": revisions["BLIS"]},
        "OpenBLAS": {"path": str(args.openblas_root), "revision": revisions["OpenBLAS"]},
    }

    data_dir = PROJECT_DIR / "data"
    processed_dir = PROJECT_DIR / "processed"
    provenance_dir = PROJECT_DIR / "provenance"
    for directory in (data_dir, processed_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=True)

    fact_doc = {"schema_version": 1, "sources": source_roots, "facts": facts}
    contract_doc = {"schema_version": 1, "contracts": contract_rows}
    conflict_doc = {"schema_version": 1, "conflicts": conflict_rows}
    (data_dir / "multisource_facts.yaml").write_text(
        yaml.safe_dump(fact_doc, sort_keys=False), encoding="utf-8"
    )
    (data_dir / "multisource_contracts.yaml").write_text(
        yaml.safe_dump(contract_doc, sort_keys=False), encoding="utf-8"
    )
    (data_dir / "conflicts.yaml").write_text(
        yaml.safe_dump(conflict_doc, sort_keys=False), encoding="utf-8"
    )
    summary = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter3_multisource",
        "source_count": len(revisions),
        "fact_count": len(facts),
        "contract_count": len(contract_rows),
        "conflict_count": len(conflict_rows),
        "targets": sorted({fact["target"]["architecture"] for fact in facts}),
        "compatibility_policy": "hard_backend_specific",
        "performance_policy": "soft_online_calibrated",
        "sources": source_roots,
    }
    (processed_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_report(facts, conflict_rows, revisions)

    input_paths = sorted(
        {str(root / item["file"]): item["sha256"] for fact, root in [
            (fact, args.blis_root if fact["library"] == "BLIS" else args.openblas_root)
            for fact in facts
        ] for item in fact["evidence"]}.items()
    )
    outputs = [
        data_dir / "multisource_facts.yaml",
        data_dir / "multisource_contracts.yaml",
        data_dir / "conflicts.yaml",
        processed_dir / "summary.json",
        PROJECT_DIR / "reports" / "multisource_results.md",
    ]
    manifest = {
        "schema_version": 1,
        "experiment_id": summary["experiment_id"],
        "sources": source_roots,
        "inputs": dict(input_paths),
        "outputs": {str(path): sha256(path) for path in outputs},
    }
    (provenance_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
