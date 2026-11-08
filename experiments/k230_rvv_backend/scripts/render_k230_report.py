#!/usr/bin/env python3
"""Render the K230 build and deployment evidence as a thesis-facing report."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent


def main() -> None:
    manifest = json.loads((PROJECT / "provenance/elf_manifest.json").read_text(encoding="utf-8"))
    deployment = json.loads((PROJECT / "provenance/deployment_manifest.json").read_text(encoding="utf-8"))
    compatibility = manifest["openblas"]["rvv_intrinsic_compatibility"]
    if manifest["status"] == "board_results_imported":
        boundary = [
            "The official-toolchain ELF evidence and returned physical-board CSV files "
            "have been imported. Runtime claims must use the board summary below and "
            "remain limited to the recorded K230 configuration.",
        ]
    else:
        boundary = [
            "This host-side result proves that the official K230 SDK toolchain can produce "
            "static RT-Smart RISC-V ELF binaries for the scalar, explicit-RVV and full "
            "OpenBLAS SGEMM paths. It does not contain K230 runtime performance data; "
            "performance claims remain blocked until the board CSV files are imported.",
        ]
    lines = [
        "# K230 RVV Backend Build Results",
        "",
        "## Evidence boundary",
        "",
        f"Current status: `{manifest['status']}`.",
        "",
        *boundary,
        "",
        "## Pinned toolchain and library",
        "",
        f"- K230 SDK revision: `{manifest['sdk']['revision']}`",
        f"- Compiler: `{manifest['toolchain']['version']}`",
        f"- OpenBLAS revision: `{manifest['openblas']['revision']}`",
        f"- OpenBLAS target: `{manifest['openblas']['target']}`",
        f"- OpenBLAS static library SHA-256: `{manifest['openblas']['library_sha256']}`",
        f"- RVV compatibility mappings: {compatibility['mapped_intrinsic_count']} intrinsics "
        f"and {compatibility['mapped_tuple_type_count']} tuple types",
        "",
        "The compatibility layer is force-included by a compiler wrapper and leaves the "
        "detached OpenBLAS source worktree unmodified. It maps the ratified `__riscv_` "
        "intrinsic spelling and tuple API to the older spelling implemented by the "
        "official K230 GCC 12 prerelease.",
        "",
        "## ELF artifacts",
        "",
        "| ELF | Bytes | RVV opcode matches | SHA-256 |",
        "|---|---:|---:|---|",
    ]
    for artifact in manifest["artifacts"]:
        lines.append(
            f"| `{artifact['name']}` | {artifact['size_bytes']} | "
            f"{artifact['rvv_instruction_matches']} | `{artifact['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "All three files are ELF64 RISC-V, statically linked, and have no `INTERP` "
            "program header. The RVV and OpenBLAS variants contain substantially more "
            "vector opcode matches than the scalar control.",
            "",
            "## Board deployment",
            "",
            f"Deployment archive: `{deployment['path']}`  ",
            f"Archive SHA-256: `{deployment['sha256']}`",
            "",
            "After extracting the archive on the K230 big-core filesystem:",
            "",
            "```sh",
            "cd k230_rvv_backend",
            deployment["board_command"],
            "```",
            "",
            "Return the generated `board_results/` directory and import it on the host:",
            "",
            "```bash",
            "python3 scripts/import_board_results.py /path/to/board_results",
            "```",
            "",
        ]
    )
    if manifest["status"] == "board_results_imported":
        summary_path = Path(manifest["board_results"]["summary"])
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        lines.extend(
            [
                "## Imported board results",
                "",
                f"Rows: {summary['row_count']}; aggregates: {summary['aggregate_count']}; "
                f"all correct: `{str(summary['all_correct']).lower()}`.",
                "",
                "| Binary | Workload | Best candidate | Median GFLOP/s | Trials |",
                "|---|---|---|---:|---:|",
            ]
        )
        for row in summary["best_by_binary_workload"]:
            lines.append(
                f"| `{row['binary']}` | `{row['workload']}` | `{row['candidate']}` | "
                f"{row['median_gflops']:.6g} | {row['trials']} |"
            )
        comparisons = summary["comparisons"]
        rvv_comparison = comparisons["rvv_best_vs_scalar"]
        openblas_comparison = comparisons["openblas_full_vs_scalar"]
        lines.extend(
            [
                "",
                "## Cross-workload comparisons",
                "",
                f"- Best measured explicit-RVV schedule per workload versus the in-process "
                f"scalar control: `{rvv_comparison['geomean_speedup']:.2f}x` geometric mean.",
                f"- Complete OpenBLAS SGEMM versus the in-process scalar control: "
                f"`{openblas_comparison['geomean_speedup']:.2f}x` geometric mean.",
                "",
                "| Workload | Best RVV candidate | RVV / scalar | OpenBLAS / scalar |",
                "|---|---|---:|---:|",
            ]
        )
        openblas_by_workload = {
            row["workload"]: row for row in openblas_comparison["by_workload"]
        }
        for row in rvv_comparison["by_workload"]:
            openblas_row = openblas_by_workload[row["workload"]]
            lines.append(
                f"| `{row['workload']}` | `{row['candidate']}` | "
                f"{row['speedup_vs_scalar']:.2f}x | "
                f"{openblas_row['speedup_vs_scalar']:.2f}x |"
            )
        lines.extend(
            [
                "",
                "## Schedule-transfer evidence",
                "",
                "| RVV candidate | Geomean / scalar | Workloads above scalar |",
                "|---|---:|---:|",
            ]
        )
        for row in comparisons["rvv_candidate_transfer"]:
            lines.append(
                f"| `{row['candidate']}` | {row['geomean_speedup_vs_scalar']:.2f}x | "
                f"{row['wins_over_scalar']} / {row['workloads']} |"
            )
        lines.extend(
            [
                "",
                "The winning explicit-RVV schedule changes with shape: generic candidates "
                "win six of eight workloads, while OpenBLAS-derived and cross-source "
                "candidates each win one. The fixed BLIS-derived candidate reaches only "
                f"`{next(row['geomean_speedup_vs_scalar'] for row in comparisons['rvv_candidate_transfer'] if row['candidate'] == 'rvv_blis_16x4x640'):.2f}x` "
                "geometric mean relative to scalar. These measurements support transferring "
                "compatibility constraints and candidate seeds, but not treating a source "
                "library's fixed parameters as a target-independent performance ranking.",
                "",
                "The complete OpenBLAS result is an optimized library reference with its own "
                "microkernel and packing path. It is not interchangeable with the explicit-RVV "
                "schedule candidates.",
                "",
            ]
        )
    reports = PROJECT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "k230_elf_results.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
