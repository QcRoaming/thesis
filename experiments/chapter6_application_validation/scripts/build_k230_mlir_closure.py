#!/usr/bin/env python3
"""Build representative linalg/Transform-to-K230 OpenBLAS closure artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
EXTERNAL = EXPERIMENTS / "chapter6_external_validation"
THESIS = EXPERIMENTS.parent
REPO = EXPERIMENTS.parents[2]
DEFAULT_SDK = THESIS / "third_party" / "k230_sdk"
DEFAULT_OPENBLAS = THESIS / "third_party" / "OpenBLAS-k230"
BUDDY_OPT = REPO / "build" / "bin" / "buddy-opt"
MLIR_OPT = REPO / "llvm" / "build" / "bin" / "mlir-opt"
MLIR_TRANSLATE = REPO / "llvm" / "build" / "bin" / "mlir-translate"
LLC = REPO / "llvm" / "build" / "bin" / "llc"
CLANG = REPO / "llvm" / "build" / "bin" / "clang"

K230_HELPERS = EXPERIMENTS / "k230_rvv_backend" / "scripts"
import sys

sys.path.insert(0, str(K230_HELPERS))
from build_k230_elfs import output, sha256, toolchain_paths, verify_elf  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def run(command: list[str], log: Path) -> float:
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True)
    elapsed = (time.perf_counter() - started) * 1000.0
    log.write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout
        + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed; see {log}: {' '.join(command)}")
    return elapsed


def c_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def token(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not re.match(r"[A-Za-z_]", result):
        result = "case_" + result
    return result


def load_cases() -> list[dict[str, Any]]:
    declaration = read_json(PROJECT / "data" / "k230_mlir_closure_cases.json")
    workload_rows = read_json(EXTERNAL / "data" / "transformer_workloads.json")["workloads"]
    workloads = {row["id"]: row for row in workload_rows}
    matrix = read_json(EXTERNAL / "processed" / "k230_candidate_matrix.json")["rows"]
    lookup = {(row["workload_id"], row["candidate_id"]): row for row in matrix}
    cases: list[dict[str, Any]] = []
    for declared in declaration["cases"]:
        key = (declared["workload_id"], declared["candidate_id"])
        if key not in lookup:
            raise KeyError(f"closure case is absent from the frozen matrix: {key}")
        row = lookup[key]
        if not row["executable"]:
            raise ValueError(f"closure case is not executable: {key}")
        if row["predicted_path"] != declared["expected_path"]:
            raise ValueError(
                f"path changed for {key}: {row['predicted_path']} != "
                f"{declared['expected_path']}"
            )
        workload = workloads[declared["workload_id"]]
        cases.append({
            **declared,
            "token": token(declared["id"]),
            "m": int(workload["m"]),
            "k": int(workload["k"]),
            "n": int(workload["n"]),
            "tile_m": int(row["tile_m"]),
            "tile_n": int(row["tile_n"]),
            "tile_k": int(row["tile_k"]),
            "score": float(row["score"]),
        })
    if len(cases) != 3:
        raise ValueError("the representative closure protocol requires exactly three cases")
    return cases


def render_input(case: dict[str, Any]) -> str:
    mlir_symbol = f"k230_mlir_{case['token']}"
    adapter_symbol = f"k230_contract_adapter_{case['token']}"
    return f"""module @k230_payload attributes {{buddy.payload}} {{
  func.func @{mlir_symbol}(
      %A: memref<?x?xf32>,
      %B: memref<?x?xf32>,
      %C: memref<?x?xf32>) attributes {{llvm.emit_c_interface}} {{
    linalg.generic {{
        indexing_maps = [
          affine_map<(m, n, k) -> (m, k)>,
          affine_map<(m, n, k) -> (k, n)>,
          affine_map<(m, n, k) -> (m, n)>],
        iterator_types = ["parallel", "parallel", "reduction"]}}
        ins(%A, %B : memref<?x?xf32>, memref<?x?xf32>)
        outs(%C : memref<?x?xf32>) {{
      ^bb0(%a: f32, %b: f32, %c: f32):
        %product = arith.mulf %a, %b : f32
        %sum = arith.addf %c, %product : f32
        linalg.yield %sum : f32
      }}
    return
  }}
}}

module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(%root: !transform.any_op) {{
    %matmul = transform.structured.match ops{{["linalg.generic"]}} in %root
      : (!transform.any_op) -> !transform.any_op
    %callee = transform.param.constant "{adapter_symbol}"
      -> !transform.any_param
    transform.annotate %matmul "library_call" = %callee
      : !transform.any_op, !transform.any_param
    %payload = transform.structured.match ops{{["builtin.module"]}}
      attributes{{buddy.payload}} in %root
      : (!transform.any_op) -> !transform.any_op
    %library = transform.apply_registered_pass "convert-linalg-to-std"
      to %payload : (!transform.any_op) -> !transform.any_op
    transform.yield
  }}
}}
"""


def generate_config_header(cases: list[dict[str, Any]]) -> Path:
    lines = [
        "/* Generated from the frozen K230 MLIR closure cases. */",
        "#ifndef K230_MLIR_CLOSURE_CONFIG_H",
        "#define K230_MLIR_CLOSURE_CONFIG_H",
        "",
        "#define K230_MLIR_CLOSURE_CASES(X) \\",
    ]
    for index, case in enumerate(cases):
        suffix = " \\" if index + 1 < len(cases) else ""
        args = [
            case["token"], c_string(case["id"]), c_string(case["workload_id"]),
            c_string(case["candidate_id"]), c_string(case["expected_path"]),
            str(case["m"]), str(case["k"]), str(case["n"]),
            str(case["tile_m"]), str(case["tile_n"]), str(case["tile_k"]),
        ]
        lines.append("  X(" + ", ".join(args) + ")" + suffix)
    lines.extend(["", "#endif", ""])
    path = PROJECT / "build" / "generated" / "k230_mlir_closure_config.h"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def generate_host_stub(cases: list[dict[str, Any]]) -> Path:
    lines = [
        "#include <stdint.h>",
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "",
        "typedef struct {",
        "  float *allocated; float *aligned; intptr_t offset;",
        "  intptr_t sizes[2]; intptr_t strides[2];",
        "} memref2d_f32_t;",
        "static int adapter_calls;",
        "",
    ]
    for index, case in enumerate(cases, start=1):
        adapter = f"_mlir_ciface_k230_contract_adapter_{case['token']}"
        entry = f"_mlir_ciface_k230_mlir_{case['token']}"
        lines.extend([
            f"void {entry}(memref2d_f32_t *, memref2d_f32_t *, memref2d_f32_t *);",
            f"void {adapter}(memref2d_f32_t *a, memref2d_f32_t *b, memref2d_f32_t *c) {{",
            f"  if (a->sizes[0] != {case['m']} || a->sizes[1] != {case['k']} ||",
            f"      b->sizes[0] != {case['k']} || b->sizes[1] != {case['n']} ||",
            f"      c->sizes[0] != {case['m']} || c->sizes[1] != {case['n']}) exit(20);",
            f"  c->aligned[c->offset] = {1000 + index}.0f;",
            "  ++adapter_calls;",
            "}",
            "",
        ])
    lines.extend([
        "static memref2d_f32_t desc(float *data, intptr_t rows, intptr_t cols) {",
        "  memref2d_f32_t value = {data, data, 0, {rows, cols}, {cols, 1}};",
        "  return value;",
        "}",
        "int main(void) {",
        "  float a = 0.0f, b = 0.0f, c = 0.0f;",
    ])
    for index, case in enumerate(cases, start=1):
        entry = f"_mlir_ciface_k230_mlir_{case['token']}"
        lines.extend([
            f"  memref2d_f32_t a{index} = desc(&a, {case['m']}, {case['k']});",
            f"  memref2d_f32_t b{index} = desc(&b, {case['k']}, {case['n']});",
            f"  memref2d_f32_t c{index} = desc(&c, {case['m']}, {case['n']});",
            f"  {entry}(&a{index}, &b{index}, &c{index});",
            f"  if (c != {1000 + index}.0f) return {30 + index};",
        ])
    lines.extend([
        f"  if (adapter_calls != {len(cases)}) return 40;",
        f"  printf(\"PASS cases={len(cases)} adapter_calls=%d\\n\", adapter_calls);",
        "  return 0;",
        "}",
        "",
    ])
    path = PROJECT / "build" / "generated" / "k230_mlir_closure_host_stub.c"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")
    return path


def build_cases(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[Path], list[Path]]:
    for tool in (BUDDY_OPT, MLIR_OPT, MLIR_TRANSLATE, LLC, CLANG):
        if not tool.is_file():
            raise FileNotFoundError(tool)
    records: list[dict[str, Any]] = []
    host_objects: list[Path] = []
    target_objects: list[Path] = []
    for case in cases:
        case_dir = PROJECT / "build" / "k230_mlir_closure" / "cases" / case["id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        input_mlir = case_dir / "input.mlir"
        transformed = case_dir / "transformed.mlir"
        llvm_mlir = case_dir / "llvm.mlir"
        llvm_ir = case_dir / "kernel.ll"
        host_object = case_dir / "kernel_host.o"
        target_object = case_dir / "kernel_rv64gcv.o"
        input_mlir.write_text(render_input(case), encoding="ascii")
        timings = {
            "transform_ms": run(
                [str(BUDDY_OPT), str(input_mlir), "--transform-interpreter",
                 "--buddy-finalize-transform-payload", "--canonicalize", "--cse",
                 "-o", str(transformed)],
                case_dir / "01_transform.log",
            ),
            "lower_ms": run(
                [str(MLIR_OPT), str(transformed), "--test-lower-to-llvm", "-o",
                 str(llvm_mlir)],
                case_dir / "02_lower.log",
            ),
            "translate_ms": run(
                [str(MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir), "-o",
                 str(llvm_ir)],
                case_dir / "03_translate.log",
            ),
            "host_object_ms": run(
                [str(CLANG), "-O2", "-c", str(llvm_ir), "-o", str(host_object)],
                case_dir / "04_host_object.log",
            ),
            "target_object_ms": run(
                [str(LLC), "-O=3", "-mtriple=riscv64-unknown-linux-musl",
                 "-mattr=+m,+a,+f,+d,+c,+v", "-filetype=obj", str(llvm_ir),
                 "-o", str(target_object)],
                case_dir / "05_target_object.log",
            ),
        }
        adapter = f"k230_contract_adapter_{case['token']}"
        mlir_entry = f"_mlir_ciface_k230_mlir_{case['token']}"
        input_text = input_mlir.read_text(encoding="ascii")
        transformed_text = transformed.read_text(encoding="utf-8")
        llvm_text = llvm_ir.read_text(encoding="utf-8")
        checks = {
            "input_has_linalg": "linalg.generic" in input_text,
            "input_has_transform_parameter": (
                f'transform.param.constant "{adapter}"' in input_text
            ),
            "transformed_has_adapter_call": f"call @{adapter}(" in transformed_text,
            "transformed_has_no_linalg": "linalg.generic" not in transformed_text,
            "llvm_has_adapter_ciface": f"_mlir_ciface_{adapter}" in llvm_text,
            "llvm_has_mlir_entry": f"define void @{mlir_entry}(" in llvm_text,
        }
        if not all(checks.values()):
            raise RuntimeError(f"MLIR closure audit failed for {case['id']}: {checks}")
        records.append({
            **case,
            "adapter_symbol": adapter,
            "mlir_entry_symbol": mlir_entry,
            "checks": checks,
            "timings_ms": {key: round(value, 6) for key, value in timings.items()},
            "artifacts": {
                path.name: {"path": str(path), "sha256": sha256(path)}
                for path in (input_mlir, transformed, llvm_mlir, llvm_ir,
                             host_object, target_object)
            },
        })
        host_objects.append(host_object)
        target_objects.append(target_object)
    return records, host_objects, target_objects


def validate_host(cases: list[dict[str, Any]], objects: list[Path]) -> dict[str, Any]:
    stub = generate_host_stub(cases)
    executable = PROJECT / "build" / "k230_mlir_closure" / "host_closure_smoke"
    compile_ms = run(
        [str(CLANG), "-O2", str(stub), *map(str, objects), "-o", str(executable)],
        PROJECT / "build" / "k230_mlir_closure" / "host_link.log",
    )
    completed = subprocess.run([str(executable)], text=True, capture_output=True)
    log = PROJECT / "build" / "k230_mlir_closure" / "host_smoke.log"
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0 or not completed.stdout.startswith("PASS"):
        raise RuntimeError(f"host closure smoke failed; see {log}")
    return {
        "status": "PASS",
        "stdout": completed.stdout.strip(),
        "compile_ms": round(compile_ms, 6),
        "executable": str(executable),
        "sha256": sha256(executable),
        "stub_sha256": sha256(stub),
    }


def build_target(
    sdk: Path, openblas: Path, config_header: Path, target_objects: list[Path],
    cases: list[dict[str, Any]],
) -> tuple[Path, dict[str, Any]]:
    tools = toolchain_paths(sdk)
    library = openblas / "libopenblas.a"
    if not library.is_file():
        raise FileNotFoundError(library)
    external_header = EXTERNAL / "build" / "generated" / "k230_external_config.h"
    if not external_header.is_file():
        raise FileNotFoundError(external_header)
    linker_script = (
        sdk / "src" / "big" / "rt-smart" / "userapps" / "linker_scripts"
        / "riscv64" / "link.lds"
    )
    elf = PROJECT / "build" / "k230_mlir_closure" / "k230_mlir_closure.elf"
    source = PROJECT / "runtime" / "k230_mlir_closure_bench.c"
    command = [
        str(tools["gcc"]), "-std=c11", "-O3", "-march=rv64imafdcv",
        "-mabi=lp64d", "-mcmodel=medany", "-n", "-static",
        "-ffunction-sections", "-fdata-sections", "-fno-strict-aliasing",
        "-Wl,--gc-sections", "-Wl,--build-id=none", "-T", str(linker_script),
        "-I", str(PROJECT / "build" / "generated"),
        "-I", str(EXTERNAL / "build" / "generated"),
        "-I", str(EXTERNAL / "runtime"), "-I", str(openblas), str(source),
        *map(str, target_objects), str(library), "-lm", "-o", str(elf),
    ]
    link_ms = run(command, PROJECT / "build" / "k230_mlir_closure" / "target_link.log")
    required = ["main", "cblas_sgemm", "sgemm_kernel"]
    for case in cases:
        required.extend([
            f"_mlir_ciface_k230_mlir_{case['token']}",
            f"_mlir_ciface_k230_contract_adapter_{case['token']}",
        ])
    verification = verify_elf(
        tools["readelf"], tools["objdump"], tools["nm"], elf, True, required
    )
    attributes = output([str(tools["readelf"]), "-A", str(elf)])
    if "_v" not in attributes and "v1p0" not in attributes:
        raise RuntimeError("closure ELF does not advertise the RISC-V V extension")
    return elf, {
        "build_command": command,
        "link_ms": round(link_ms, 6),
        "sha256": sha256(elf),
        "size_bytes": elf.stat().st_size,
        "riscv_attributes": attributes,
        "config_header_sha256": sha256(config_header),
        **verification,
    }


def create_archive(elf: Path, records: list[dict[str, Any]], manifest: Path) -> dict[str, Any]:
    files = [
        elf,
        elf.with_suffix(".disassembly.txt"),
        PROJECT / "board" / "run_k230_mlir_closure.sh",
        PROJECT / "K230_DEPLOYMENT.md",
        PROJECT / "data" / "experiment_config.json",
        PROJECT / "data" / "k230_mlir_closure_cases.json",
        PROJECT / "scripts" / "import_k230_mlir_results.py",
        PROJECT / "scripts" / "run_k230_mlir_via_serial.py",
        manifest,
    ]
    for record in records:
        case_dir = PROJECT / "build" / "k230_mlir_closure" / "cases" / record["id"]
        files.extend(case_dir / name for name in (
            "input.mlir", "transformed.mlir", "llvm.mlir", "kernel.ll",
            "kernel_rv64gcv.o",
        ))
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("archive inputs missing: " + ", ".join(missing))
    archive = (
        PROJECT / "build" / "packages"
        / "chapter6-k230-mlir-closure-validation.tar.gz"
    )
    archive.parent.mkdir(parents=True, exist_ok=True)
    root = Path("chapter6-k230-mlir-closure-validation")
    with tarfile.open(archive, "w:gz") as bundle:
        for path in files:
            bundle.add(path, arcname=root / path.relative_to(PROJECT))
    return {
        "path": str(archive),
        "sha256": sha256(archive),
        "size_bytes": archive.stat().st_size,
        "members": [str(path.relative_to(PROJECT)) for path in files],
        "board_command": (
            "K230_MLIR_REPS=5 K230_MLIR_WARMUPS=1 "
            "sh board/run_k230_mlir_closure.sh"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--openblas", type=Path, default=DEFAULT_OPENBLAS)
    args = parser.parse_args()
    cases = load_cases()
    config_header = generate_config_header(cases)
    records, host_objects, target_objects = build_cases(cases)
    host = validate_host(cases, host_objects)
    elf, target = build_target(
        args.sdk.resolve(), args.openblas.resolve(), config_header,
        target_objects, cases,
    )
    external_adapter = EXTERNAL / "runtime" / "k230_openblas_contract_bench.c"
    generator_freeze = EXTERNAL / "provenance" / "generator_freeze.json"
    manifest_path = PROJECT / "provenance" / "k230_mlir_closure_manifest.json"
    manifest = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.k230_mlir_closure",
        "status": "elf_ready_awaiting_board_measurement",
        "protocol": read_json(PROJECT / "data" / "experiment_config.json"),
        "cases": records,
        "host_abi_smoke": host,
        "target_elf": {"path": str(elf), **target},
        "reuse_audit": {
            "chapter4_generator_freeze": read_json(generator_freeze),
            "external_adapter_source": str(external_adapter),
            "external_adapter_sha256": sha256(external_adapter),
            "core_generator_modified_for_closure": False,
            "new_compiler_pass_required": False,
            "standard_lowering": "transform.annotate + convert-linalg-to-std",
        },
        "claim_boundary": read_json(PROJECT / "data" / "experiment_config.json")
        ["claim_boundary"],
    }
    write_json(manifest_path, manifest)
    deployment = create_archive(elf, records, manifest_path)
    write_json(PROJECT / "provenance" / "k230_mlir_closure_deployment.json", deployment)
    print(json.dumps({"manifest": manifest, "deployment": deployment}, indent=2), flush=True)


if __name__ == "__main__":
    main()
