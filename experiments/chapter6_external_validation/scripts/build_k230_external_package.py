#!/usr/bin/env python3
"""Generate the OpenBLAS Contract matrix and build the K230 RT-Smart ELF."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent
EXPERIMENTS = PROJECT.parent
THESIS = EXPERIMENTS.parent
GENERATOR = EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py"
K230_HELPERS = EXPERIMENTS / "k230_rvv_backend" / "scripts"
DEFAULT_SDK = THESIS / "third_party" / "k230_sdk"
DEFAULT_OPENBLAS = THESIS / "third_party" / "OpenBLAS-k230"

sys.path.insert(0, str(GENERATOR.parent))
sys.path.insert(0, str(K230_HELPERS))

from chapter4lib import Candidate, generate_spaces_for_task  # noqa: E402
from build_k230_elfs import output, sha256, toolchain_paths, verify_elf  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def c_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def generator_freeze(refresh: bool) -> dict[str, Any]:
    path = PROJECT / "provenance" / "generator_freeze.json"
    current = sha256(GENERATOR)
    if path.exists() and not refresh:
        record = read_json(path)
        if record["sha256"] != current:
            raise RuntimeError(
                "Chapter 4 generator changed after the external-backend freeze: "
                f"{record['sha256']} != {current}"
            )
        return record
    record = {
        "schema_version": 1,
        "status": "frozen_before_k230_backend_generation",
        "path": str(GENERATOR),
        "sha256": current,
        "prefreeze_generalization": (
            "conditional_parameters now reads packing.layout and call_convention "
            "from the selected Contract; selection, compatibility, scoring, and "
            "space-membership algorithms are unchanged"
        ),
        "postfreeze_allowed_additions": [
            "Contract descriptor",
            "package-local candidate data",
            "packing/call adapter",
            "deployment and result-import code",
        ],
    }
    write_json(path, record)
    return record


def task_for(workload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": workload["id"],
        "role": workload["family"],
        "operation": "linalg.matmul",
        "dtype": "f32",
        "shape": {"m": workload["m"], "k": workload["k"], "n": workload["n"]},
        "target": {
            "machine": "riscv64",
            "architecture": "riscv64_zvl128b",
            "features": ["rv64gc", "rvv", "zvl128b"],
        },
        "layout": {"a": "row_major", "b": "row_major", "c": "row_major"},
        "stride": {"a_inner": 1, "b_inner": 1, "c_inner": 1},
        "available_adapters": {"mn_tail": True, "k_remainder": True},
        "fallback_available": True,
    }


def build_matrix() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    workloads = read_json(PROJECT / "data" / "transformer_workloads.json")["workloads"]
    contract = read_json(PROJECT / "data" / "k230_openblas_contract.json")["contract"]
    raw_candidates = read_json(PROJECT / "data" / "k230_candidates.json")["candidates"]
    candidates = [
        Candidate(
            tile_m=int(row["tile_m"]),
            tile_n=int(row["tile_n"]),
            tile_k=int(row["tile_k"]),
            pack_mode="ab",
            vectorize=True,
        )
        for row in raw_candidates
    ]
    config = {
        "seed": 20260719,
        "configs": [
            {"id": "generic", "initial_design_size": 16, "exploration_ratio": 0.0},
            {"id": "contract_only", "initial_design_size": 16, "exploration_ratio": 0.0},
            {"id": "expert_core", "initial_design_size": 16, "exploration_ratio": 0.0},
            {"id": "expert_shell", "initial_design_size": 16, "exploration_ratio": 0.25},
        ],
    }
    matrix: list[dict[str, Any]] = []
    for workload in workloads:
        spaces, rows, selection = generate_spaces_for_task(
            task_for(workload), candidates, [contract], config
        )
        selected_contracts = [row for row in selection if row.get("selected")]
        if len(selected_contracts) != 1 or selected_contracts[0]["contract_id"] != contract["id"]:
            raise RuntimeError(f"Contract selection failed for {workload['id']}")
        executable = {row["candidate_id"] for row in spaces["generic"]}
        for row in rows:
            matrix.append({
                "workload_id": workload["id"],
                "candidate_id": row["candidate_id"],
                "tile_m": row["tile_m"],
                "tile_n": row["tile_n"],
                "tile_k": row["tile_k"],
                "predicted_path": row["predicted_path"],
                "reason_codes": ";".join(row["reason_codes"]),
                "score": row["score"],
                "executable": row["candidate_id"] in executable,
                "pack_layout": row["conditional_parameters"].get("pack_layout", ""),
                "call_convention": row["conditional_parameters"].get("call_convention", ""),
            })
    return workloads, [
        {
            "id": candidate.id,
            "tile_m": candidate.tile_m,
            "tile_n": candidate.tile_n,
            "tile_k": candidate.tile_k,
        }
        for candidate in candidates
    ], matrix


def generate_header(
    workloads: list[dict[str, Any]], candidates: list[dict[str, Any]], matrix: list[dict[str, Any]]
) -> Path:
    lookup = {(row["workload_id"], row["candidate_id"]): row for row in matrix}
    lines = [
        "/* Generated from the frozen external-validation JSON inputs. */",
        "#ifndef K230_EXTERNAL_CONFIG_H",
        "#define K230_EXTERNAL_CONFIG_H",
        "",
        "#define K230_CONTRACT_MR 8",
        "#define K230_CONTRACT_NR 8",
        f"#define K230_WORKLOAD_COUNT {len(workloads)}",
        f"#define K230_CANDIDATE_COUNT {len(candidates)}",
        "",
        "typedef struct { const char *id; int m; int k; int n; } k230_workload_t;",
        "typedef struct { const char *id; int tile_m; int tile_n; int tile_k; } k230_candidate_t;",
        "",
        "static const k230_workload_t k230_workloads[K230_WORKLOAD_COUNT] = {",
    ]
    for row in workloads:
        lines.append(
            f"  {{{c_string(row['id'])}, {row['m']}, {row['k']}, {row['n']}}},"
        )
    lines.extend(["};", "", "static const k230_candidate_t k230_candidates[K230_CANDIDATE_COUNT] = {"])
    for row in candidates:
        lines.append(
            f"  {{{c_string(row['id'])}, {row['tile_m']}, {row['tile_n']}, {row['tile_k']}}},"
        )
    lines.extend(["};", "", "static const char *k230_predicted_paths[K230_WORKLOAD_COUNT][K230_CANDIDATE_COUNT] = {"])
    for workload in workloads:
        values = [
            c_string(lookup[(workload["id"], candidate["id"])]["predicted_path"])
            for candidate in candidates
        ]
        lines.append("  {" + ", ".join(values) + "},")
    lines.extend(["};", "", "static const unsigned char k230_candidate_active[K230_WORKLOAD_COUNT][K230_CANDIDATE_COUNT] = {"])
    for workload in workloads:
        values = [
            "1" if lookup[(workload["id"], candidate["id"])]["executable"] else "0"
            for candidate in candidates
        ]
        lines.append("  {" + ", ".join(values) + "},")
    lines.extend(["};", "", "#endif", ""])
    header = PROJECT / "build" / "generated" / "k230_external_config.h"
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text("\n".join(lines), encoding="ascii")
    return header


def build_elf(sdk: Path, openblas: Path, header: Path) -> tuple[Path, dict[str, Any]]:
    tools = toolchain_paths(sdk)
    library = openblas / "libopenblas.a"
    if not library.is_file():
        raise FileNotFoundError(f"prebuilt K230 OpenBLAS archive missing: {library}")
    source = PROJECT / "runtime" / "k230_openblas_contract_bench.c"
    linker_script = (
        sdk / "src" / "big" / "rt-smart" / "userapps" / "linker_scripts"
        / "riscv64" / "link.lds"
    )
    elf = PROJECT / "build" / "k230_external" / "k230_openblas_contract_pool.elf"
    elf.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(tools["gcc"]), "-std=c11", "-O3", "-march=rv64imafdcv", "-mabi=lp64d",
        "-mcmodel=medany", "-n", "-static", "-ffunction-sections",
        "-fdata-sections", "-fno-strict-aliasing", "-Wl,--gc-sections",
        "-Wl,--build-id=none", "-T", str(linker_script), "-I", str(header.parent),
        "-I", str(openblas), str(source), str(library), "-lm", "-o", str(elf),
    ]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)
    verification = verify_elf(
        tools["readelf"], tools["objdump"], tools["nm"], elf, True,
        ["main", "cblas_sgemm", "sgemm_kernel"],
    )
    attributes = output([str(tools["readelf"]), "-A", str(elf)])
    if "_v" not in attributes and "v1p0" not in attributes:
        raise RuntimeError("RISC-V ELF attributes do not advertise the V extension")
    return elf, {
        "build_command": command,
        "sha256": sha256(elf),
        "size_bytes": elf.stat().st_size,
        "riscv_attributes": attributes,
        **verification,
    }


def create_archive(files: list[Path]) -> dict[str, Any]:
    package_dir = PROJECT / "build" / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    archive = package_dir / "chapter6-k230-openblas-external-validation.tar.gz"
    root = Path("chapter6-k230-openblas-external-validation")
    with tarfile.open(archive, "w:gz") as bundle:
        for path in files:
            bundle.add(path, arcname=root / path.relative_to(PROJECT))
    return {
        "path": str(archive),
        "sha256": sha256(archive),
        "size_bytes": archive.stat().st_size,
        "members": [str(path.relative_to(PROJECT)) for path in files],
        "board_command": (
            "python3 scripts/run_k230_external_via_serial.py --port /dev/ttyACM1 "
            "--board-root /sdcard/chapter6-k230-openblas-external-validation "
            "--output-dir board_results"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--openblas", type=Path, default=DEFAULT_OPENBLAS)
    parser.add_argument("--refresh-generator-freeze", action="store_true")
    args = parser.parse_args()

    freeze = generator_freeze(args.refresh_generator_freeze)
    workloads, candidates, matrix = build_matrix()
    matrix_json = PROJECT / "processed" / "k230_candidate_matrix.json"
    matrix_csv = PROJECT / "processed" / "k230_candidate_matrix.csv"
    write_json(matrix_json, {"workloads": workloads, "candidates": candidates, "rows": matrix})
    write_csv(matrix_csv, matrix)
    header = generate_header(workloads, candidates, matrix)
    elf, verification = build_elf(args.sdk.resolve(), args.openblas.resolve(), header)

    manifest_path = PROJECT / "provenance" / "k230_external_manifest.json"
    manifest = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_external_validation.k230_openblas",
        "status": "elf_ready_awaiting_board_measurement",
        "target": "K230 C908 RT-Smart RV64GCV",
        "generator_freeze": freeze,
        "contract": {
            "path": str(PROJECT / "data" / "k230_openblas_contract.json"),
            "sha256": sha256(PROJECT / "data" / "k230_openblas_contract.json"),
        },
        "inputs": {
            "workloads": sha256(PROJECT / "data" / "transformer_workloads.json"),
            "candidates": sha256(PROJECT / "data" / "k230_candidates.json"),
            "runtime": sha256(PROJECT / "runtime" / "k230_openblas_contract_bench.c"),
            "openblas_library": sha256(args.openblas.resolve() / "libopenblas.a"),
        },
        "matrix": {
            "rows": len(matrix),
            "executable_rows": sum(bool(row["executable"]) for row in matrix),
            "direct_rows": sum(row["predicted_path"] == "direct" for row in matrix),
            "adapt_rows": sum(row["predicted_path"] == "adapt" for row in matrix),
            "reject_rows": sum(row["predicted_path"] == "reject" for row in matrix),
            "json_sha256": sha256(matrix_json),
            "csv_sha256": sha256(matrix_csv),
            "header_sha256": sha256(header),
        },
        "elf": {"path": str(elf), **verification},
        "claim_boundary": read_json(PROJECT / "data" / "experiment_config.json")["claim_boundary"],
    }
    write_json(manifest_path, manifest)
    files = [
        elf,
        PROJECT / "board" / "run_k230_external_validation.sh",
        PROJECT / "README_K230.md",
        PROJECT / "data" / "experiment_config.json",
        PROJECT / "data" / "transformer_workloads.json",
        PROJECT / "data" / "k230_openblas_contract.json",
        PROJECT / "data" / "k230_candidates.json",
        matrix_json,
        matrix_csv,
        header,
        PROJECT / "runtime" / "k230_openblas_contract_bench.c",
        PROJECT / "scripts" / "import_k230_external_results.py",
        PROJECT / "scripts" / "run_k230_external_via_serial.py",
        PROJECT / "provenance" / "generator_freeze.json",
        manifest_path,
    ]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("package inputs missing: " + ", ".join(missing))
    deployment = create_archive(files)
    write_json(PROJECT / "provenance" / "k230_deployment_manifest.json", deployment)
    print(json.dumps({"manifest": manifest, "deployment": deployment}, indent=2), flush=True)


if __name__ == "__main__":
    main()
