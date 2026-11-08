#!/usr/bin/env python3
"""Build, execute, and analyze the Transformer region go/no-go probe."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import random
import statistics
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[3]
CONFIG_PATH = PROJECT / "data" / "experiment_config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
RUNTIME = PROJECT / "runtime" / "region_fanout_bench.cpp"
BUILD = PROJECT / "build"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
PROVENANCE = PROJECT / "provenance"
TESTS = PROJECT / "tests"

CXX = REPO / "llvm" / "build" / "bin" / "clang++"
BLIS = REPO / "jlq" / "thesis" / "blis" / "blis"
BLIS_INCLUDE = BLIS / "include" / "haswell"
BLIS_LIBRARY = BLIS / "lib" / "haswell" / "libblis.a"
EXECUTABLE = BUILD / "region_fanout_bench"


def run(
    command: list[str], log: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            "$ " + " ".join(command) + f"\nELAPSED_MS={elapsed_ms:.6f}\n\n"
            + "STDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
            encoding="utf-8",
        )
    if check and completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stderr[-2400:]}"
        )
    return completed


def ensure_environment() -> None:
    missing = [
        path
        for path in (CXX, BLIS_INCLUDE / "blis.h", BLIS_LIBRARY)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "missing fixed toolchain inputs: " + ", ".join(map(str, missing))
        )


def compile_benchmark() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    run(
        [
            str(CXX), "-O3", "-march=native", "-std=c++17",
            "-I" + str(BLIS_INCLUDE), str(RUNTIME), str(BLIS_LIBRARY),
            "-lpthread", "-lm", "-o", str(EXECUTABLE),
        ],
        REPORTS / "compile.log",
    )
    symbols = run(["nm", "-C", str(EXECUTABLE)], REPORTS / "symbols.log").stdout
    if "bli_sgemm_haswell_asm_6x16" not in symbols:
        raise RuntimeError("compiled probe does not contain the required BLIS 6x16 symbol")


def execute_cases(cpu: int, quick: bool) -> list[dict[str, Any]]:
    measurement = dict(CONFIG["measurement"])
    if quick:
        measurement.update(
            {
                "warmups": 1,
                "repeats": 3,
                "trials": 2,
                "target_flops_per_sample": 100_000_000,
            }
        )
    all_rows: list[dict[str, Any]] = []
    for region in CONFIG["regions"]:
        ns = [int(value) for value in region["branch_n"]]
        for phase in CONFIG["phases"]:
            m = int(phase["m"])
            case_id = f"{region['id']}_{phase['id']}"
            operations = 2 * m * int(region["input_k"]) * sum(ns)
            iterations = max(
                1,
                min(
                    int(measurement["max_inner_iters"]),
                    math.ceil(int(measurement["target_flops_per_sample"]) / operations),
                ),
            )
            command = [
                "taskset", "-c", str(cpu), str(EXECUTABLE),
                region["id"], phase["id"], str(m), str(region["input_k"]),
                ",".join(map(str, ns)), str(measurement["warmups"]),
                str(measurement["repeats"]), str(iterations),
                str(measurement["trials"]),
            ]
            completed = run(command, REPORTS / "case_logs" / f"{case_id}.log")
            rows = list(csv.DictReader(io.StringIO(completed.stdout)))
            expected_rows = 4 * int(measurement["trials"])
            if len(rows) != expected_rows:
                raise RuntimeError(
                    f"{case_id}: expected {expected_rows} rows, got {len(rows)}"
                )
            for row in rows:
                row["case_id"] = case_id
                row["phase_group"] = phase["group"]
                row["cpu_affinity"] = str(cpu)
                all_rows.append(row)
    return all_rows


def write_raw(rows: list[dict[str, Any]]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    with (RAW / "region_trials.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def geomean(values: list[float]) -> float:
    if not values or any(value <= 0.0 for value in values):
        raise ValueError("geometric mean requires positive values")
    return math.exp(statistics.fmean(math.log(value) for value in values))


def bootstrap_case_ratio(
    paired: dict[str, list[float]], resamples: int, seed: int
) -> tuple[float, float]:
    rng = random.Random(seed)
    cases = sorted(paired)
    samples: list[float] = []
    for _ in range(resamples):
        ratios: list[float] = []
        for _ in cases:
            case = rng.choice(cases)
            ratios.append(rng.choice(paired[case]))
        samples.append(geomean(ratios))
    samples.sort()
    lower = samples[int(0.025 * (len(samples) - 1))]
    upper = samples[int(0.975 * (len(samples) - 1))]
    return lower, upper


def analyze(rows: list[dict[str, Any]], quick: bool) -> dict[str, Any]:
    by_case_trial: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row["status"] == "PASS":
            by_case_trial[(row["case_id"], int(row["trial"]))][row["variant"]] = row

    comparisons = {
        "shared_a_microkernel_vs_repacked_a_microkernel": (
            "repacked_a_microkernel", "shared_a_microkernel"
        ),
        "shared_a_microkernel_vs_concatenated_blis": (
            "concatenated_blis", "shared_a_microkernel"
        ),
        "shared_a_microkernel_vs_independent_blis": (
            "independent_blis", "shared_a_microkernel"
        ),
        "shared_a_microkernel_vs_best_complete_blis": (
            "best_complete_blis", "shared_a_microkernel"
        ),
        "concatenated_blis_vs_independent_blis": (
            "independent_blis", "concatenated_blis"
        ),
    }
    ratio_trials: dict[str, dict[str, list[float]]] = {
        name: defaultdict(list) for name in comparisons
    }
    for (case_id, _trial), variants in by_case_trial.items():
        if len(variants) != 4:
            raise RuntimeError(f"incomplete variant matrix for {case_id}")
        for name, (baseline, method) in comparisons.items():
            baseline_ms = (
                min(
                    float(variants["independent_blis"]["total_median_ms"]),
                    float(variants["concatenated_blis"]["total_median_ms"]),
                )
                if baseline == "best_complete_blis"
                else float(variants[baseline]["total_median_ms"])
            )
            method_ms = float(variants[method]["total_median_ms"])
            ratio_trials[name][case_id].append(baseline_ms / method_ms)

    case_rows: list[dict[str, Any]] = []
    cases = sorted({row["case_id"] for row in rows})
    for case_id in cases:
        case_source = next(row for row in rows if row["case_id"] == case_id)
        record: dict[str, Any] = {
            "case_id": case_id,
            "region": case_source["region"],
            "phase": case_source["phase"],
            "phase_group": case_source["phase_group"],
            "m": int(case_source["m"]),
            "k": int(case_source["k"]),
            "branch_n": case_source["branch_n"],
        }
        for variant in CONFIG["variants"]:
            variant_id = variant["id"]
            variant_rows = [
                row
                for row in rows
                if row["case_id"] == case_id and row["variant"] == variant_id
            ]
            record[f"{variant_id}_median_ms"] = statistics.median(
                float(row["total_median_ms"]) for row in variant_rows
            )
            record[f"{variant_id}_median_gflops"] = statistics.median(
                float(row["region_gflops"]) for row in variant_rows
            )
            trial_times = [
                float(row["total_median_ms"]) for row in variant_rows
            ]
            record[f"{variant_id}_trial_cv"] = (
                statistics.stdev(trial_times) / statistics.fmean(trial_times)
                if len(trial_times) > 1
                else 0.0
            )
            if variant_id.endswith("microkernel"):
                record[f"{variant_id}_visible_pack_ms"] = statistics.median(
                    float(row["visible_pack_median_ms"]) for row in variant_rows
                )
        for name in comparisons:
            record[name] = geomean(ratio_trials[name][case_id])

        saved_pack_ms = max(
            0.0,
            float(record["repacked_a_microkernel_visible_pack_ms"])
            - float(record["shared_a_microkernel_visible_pack_ms"]),
        )
        repacked_total_ms = float(record["repacked_a_microkernel_median_ms"])
        record["activation_pack_saved_ms"] = saved_pack_ms
        record["activation_pack_saved_fraction_of_repacked"] = (
            saved_pack_ms / repacked_total_ms
        )
        record["packing_only_ideal_speedup_vs_repacked"] = (
            repacked_total_ms / (repacked_total_ms - saved_pack_ms)
        )
        case_rows.append(record)

    comparison_summaries: dict[str, Any] = {}
    measurement = CONFIG["measurement"]
    for offset, name in enumerate(comparisons):
        case_values = {
            case: geomean(values) for case, values in ratio_trials[name].items()
        }
        lower, upper = bootstrap_case_ratio(
            ratio_trials[name],
            1000 if quick else int(measurement["bootstrap_resamples"]),
            int(measurement["bootstrap_seed"]) + offset,
        )
        by_region: dict[str, list[float]] = defaultdict(list)
        by_phase_group: dict[str, list[float]] = defaultdict(list)
        for record in case_rows:
            value = float(record[name])
            by_region[record["region"]].append(value)
            by_phase_group[record["phase_group"]].append(value)
        comparison_summaries[name] = {
            "geomean_speedup": geomean(list(case_values.values())),
            "bootstrap_95_ci": [lower, upper],
            "case_wins": sum(value > 1.0 for value in case_values.values()),
            "case_count": len(case_values),
            "case_win_fraction": sum(value > 1.0 for value in case_values.values())
            / len(case_values),
            "by_region_geomean": {
                key: geomean(values) for key, values in sorted(by_region.items())
            },
            "by_phase_group_geomean": {
                key: geomean(values)
                for key, values in sorted(by_phase_group.items())
            },
        }

    criteria = CONFIG["local_go_criteria"]
    checks: dict[str, Any] = {}
    for name in criteria["required_comparisons"]:
        result = comparison_summaries[name]
        checks[name] = {
            "geomean_at_least_threshold": result["geomean_speedup"]
            >= criteria["minimum_geomean_speedup"],
            "win_fraction_at_least_threshold": result["case_win_fraction"]
            >= criteria["minimum_case_win_fraction"],
            "bootstrap_lower_above_one": result["bootstrap_95_ci"][0] > 1.0,
            "each_region_above_one": all(
                value > 1.0 for value in result["by_region_geomean"].values()
            ),
            "each_phase_group_above_one": all(
                value > 1.0
                for value in result["by_phase_group_geomean"].values()
            ),
        }

    all_correct = bool(rows) and all(row["status"] == "PASS" for row in rows)
    local_go = all_correct and all(all(values.values()) for values in checks.values())
    decision = (
        "PROVISIONAL_GO_PENDING_SECOND_HOST"
        if local_go
        else "NO_GO_STRONG_BASELINE_NOT_BEATEN"
        if all_correct
        else "INVALID_CORRECTNESS_FAILURE"
    )

    setup_rows = [
        row for row in rows if row["variant"] == "shared_a_microkernel"
    ]
    persistent_setup_ms = statistics.median(
        float(row["persistent_weight_pack_ms"]) for row in setup_rows
    )
    concat_setup_ms = statistics.median(
        float(row["weight_concatenation_ms"]) for row in setup_rows
    )
    persistent_weight_bytes = max(
        int(row["persistent_weight_bytes"]) for row in setup_rows
    )
    packing_ideal_speedups = [
        float(record["packing_only_ideal_speedup_vs_repacked"])
        for record in case_rows
    ]
    packing_saved_fractions = [
        float(record["activation_pack_saved_fraction_of_repacked"])
        for record in case_rows
    ]
    trial_cvs = [
        float(record[f"{variant['id']}_trial_cv"])
        for record in case_rows
        for variant in CONFIG["variants"]
    ]
    break_even: dict[str, float | None] = {}
    for record in case_rows:
        saved_ms = (
            float(record["concatenated_blis_median_ms"])
            - float(record["shared_a_microkernel_median_ms"])
        )
        break_even[record["case_id"]] = (
            persistent_setup_ms / saved_ms if saved_ms > 0 else None
        )

    return {
        "experiment_id": CONFIG["experiment_id"],
        "mode": "quick" if quick else "formal_local",
        "all_correct": all_correct,
        "raw_row_count": len(rows),
        "case_count": len(case_rows),
        "variant_count": 4,
        "comparison_summaries": comparison_summaries,
        "local_go_criteria": criteria,
        "criterion_checks": checks,
        "decision": decision,
        "case_results": case_rows,
        "packing_reuse_mechanism": {
            "packing_only_ideal_geomean_speedup": geomean(
                packing_ideal_speedups
            ),
            "packing_only_ideal_maximum_speedup": max(packing_ideal_speedups),
            "maximum_saved_fraction_of_repacked_time": max(
                packing_saved_fractions
            ),
            "interpretation": (
                "Counterfactual speedup if measured activation-pack savings "
                "were removed while all microkernel compute time stayed fixed."
            ),
        },
        "measurement_quality": {
            "blis_threads": int(measurement["blis_threads"]),
            "cpu_affinity": int(rows[0]["cpu_affinity"]),
            "variant_interleaving": measurement["variant_interleaving"],
            "median_trial_cv": statistics.median(trial_cvs),
            "maximum_trial_cv": max(trial_cvs),
            "host_environment": platform.platform(),
        },
        "persistent_representation": {
            "median_weight_pack_setup_ms": persistent_setup_ms,
            "median_weight_concatenation_setup_ms": concat_setup_ms,
            "maximum_packed_weight_bytes": persistent_weight_bytes,
            "break_even_runs_vs_concatenated_blis": break_even,
        },
        "claim_boundary": CONFIG["claim_boundary"],
    }


def write_processed(summary: dict[str, Any]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "go_nogo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    cases = summary["case_results"]
    with (PROCESSED / "case_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cases[0]))
        writer.writeheader()
        writer.writerows(cases)


def write_report(summary: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    shared_repack = summary["comparison_summaries"][
        "shared_a_microkernel_vs_repacked_a_microkernel"
    ]
    shared_concat = summary["comparison_summaries"][
        "shared_a_microkernel_vs_concatenated_blis"
    ]
    shared_best_complete = summary["comparison_summaries"][
        "shared_a_microkernel_vs_best_complete_blis"
    ]
    concat_independent = summary["comparison_summaries"][
        "concatenated_blis_vs_independent_blis"
    ]
    mechanism = summary["packing_reuse_mechanism"]
    quality = summary["measurement_quality"]
    lines = [
        "# Transformer region shared-packing go/no-go",
        "",
        "## Decision",
        "",
        f"**{summary['decision']}**",
        "",
        (
            f"All {summary['raw_row_count']} measured rows passed correctness."
            if summary["all_correct"]
            else "At least one row failed correctness; no performance decision is valid."
        ),
        "",
        "## Paired results",
        "",
        "| Comparison | Geomean | 95% case-bootstrap CI | Wins |",
        "|---|---:|---:|---:|",
        f"| shared A vs repacked A microkernel | {shared_repack['geomean_speedup']:.3f}x | "
        f"[{shared_repack['bootstrap_95_ci'][0]:.3f}, {shared_repack['bootstrap_95_ci'][1]:.3f}] | "
        f"{shared_repack['case_wins']}/{shared_repack['case_count']} |",
        f"| shared A microkernel vs concatenated BLIS | {shared_concat['geomean_speedup']:.3f}x | "
        f"[{shared_concat['bootstrap_95_ci'][0]:.3f}, {shared_concat['bootstrap_95_ci'][1]:.3f}] | "
        f"{shared_concat['case_wins']}/{shared_concat['case_count']} |",
        f"| shared A microkernel vs best complete-BLIS path | {shared_best_complete['geomean_speedup']:.3f}x | "
        f"[{shared_best_complete['bootstrap_95_ci'][0]:.3f}, {shared_best_complete['bootstrap_95_ci'][1]:.3f}] | "
        f"{shared_best_complete['case_wins']}/{shared_best_complete['case_count']} |",
        f"| concatenated BLIS vs independent BLIS | {concat_independent['geomean_speedup']:.3f}x | "
        f"[{concat_independent['bootstrap_95_ci'][0]:.3f}, {concat_independent['bootstrap_95_ci'][1]:.3f}] | "
        f"{concat_independent['case_wins']}/{concat_independent['case_count']} |",
        "",
        "## Case matrix",
        "",
        "| Case | Independent BLIS ms | Concatenated BLIS ms | Repacked A ms | Shared A ms | Shared/best BLIS |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["case_results"]:
        lines.append(
            f"| {row['case_id']} | {row['independent_blis_median_ms']:.6f} | "
            f"{row['concatenated_blis_median_ms']:.6f} | "
            f"{row['repacked_a_microkernel_median_ms']:.6f} | "
            f"{row['shared_a_microkernel_median_ms']:.6f} | "
            f"{row['shared_a_microkernel_vs_best_complete_blis']:.3f}x |"
        )
    lines.extend(
        [
            "",
            "## Mechanism bound",
            "",
            (
                "Shared packing reduced the activation-pack count from the branch "
                "count to one, but the measured saved packing time was at most "
                f"{100.0 * mechanism['maximum_saved_fraction_of_repacked_time']:.2f}% "
                "of the repacked-path latency."
            ),
            "",
            (
                "Holding microkernel compute time fixed, the packing-only ideal "
                f"speedup is {mechanism['packing_only_ideal_geomean_speedup']:.3f}x "
                "geomean and at most "
                f"{mechanism['packing_only_ideal_maximum_speedup']:.3f}x. "
                "Thus activation packing reuse alone does not reach the frozen "
                f"{summary['local_go_criteria']['minimum_geomean_speedup']:.2f}x target."
            ),
            "",
            "## Measurement audit",
            "",
            f"- BLIS threads: {quality['blis_threads']}; pinned CPU: {quality['cpu_affinity']}.",
            f"- Variant schedule: `{quality['variant_interleaving']}`.",
            (
                f"- Trial CV across case/variant cells: median {quality['median_trial_cv']:.3f}, "
                f"maximum {quality['maximum_trial_cv']:.3f}. The WSL2 maximum is "
                "retained as a residual-noise limitation."
            ),
            "",
            "## Interpretation contract",
            "",
            "- `shared A vs repacked A` isolates activation-packing reuse; both use persistent B and the same real BLIS 6x16 microkernel.",
            "- `shared A vs concatenated BLIS` is the strong-baseline test; offline weight concatenation is algebraically equivalent for these fan-out linear layers.",
            "- `shared A vs best complete-BLIS path` selects the faster independent or concatenated complete-BLIS path within each paired trial; it is a stricter diagnostic and does not relax the frozen decision criteria.",
            "- A local pass remains provisional until the frozen experiment reproduces on the i9-14900.",
            "- A local failure stops expansion unless profiling identifies a separately testable implementation defect.",
            "",
            "## Boundary",
            "",
            summary["claim_boundary"],
            "",
        ]
    )
    (REPORTS / "go_nogo_results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_provenance(cpu: int, summary: dict[str, Any]) -> None:
    PROVENANCE.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": CONFIG["experiment_id"],
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {
            "platform": platform.platform(),
            "cpu_affinity": cpu,
            "lscpu": run(["lscpu"], check=False).stdout,
        },
        "toolchain": {
            "clang": run([str(CXX), "--version"], check=False).stdout.splitlines()[0],
            "blis_library": str(BLIS_LIBRARY.relative_to(REPO)),
        },
        "inputs": {
            str(CONFIG_PATH.relative_to(REPO)): sha256(CONFIG_PATH),
            str(RUNTIME.relative_to(REPO)): sha256(RUNTIME),
            str(Path(__file__).resolve().relative_to(REPO)): sha256(
                Path(__file__).resolve()
            ),
            str(BLIS_LIBRARY.relative_to(REPO)): sha256(BLIS_LIBRARY),
        },
        "measurement_protocol": CONFIG["measurement"],
        "decision": summary["decision"],
    }
    (PROVENANCE / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def write_artifact_index() -> None:
    (PROJECT / "go_nogo_artifact_index.md").write_text(
        """# Transformer region go/no-go artifact index

- Configuration and frozen criteria: `data/experiment_config.json`
- Real BLIS mechanism probe: `runtime/region_fanout_bench.cpp`
- One-command runner: `scripts/run_go_nogo.py`
- Raw paired trials: `raw/region_trials.csv`
- Per-case aggregates: `processed/case_summary.csv`
- Machine-readable decision: `processed/go_nogo_summary.json`
- Human-readable report: `reports/go_nogo_results.md`
- Build and symbol logs: `reports/compile.log`, `reports/symbols.log`
- Host and input hashes: `provenance/manifest.json`
- Artifact tests: `tests/test_go_nogo.py`

The probe intentionally includes concatenated-weight complete BLIS as a strong
baseline. The C++ microkernel paths are mechanism evidence for deciding whether
to implement a later MLIR region planner; they are not presented as that
planner.
""",
        encoding="utf-8",
    )


def run_tests() -> None:
    run(
        ["python3", "-m", "unittest", "discover", "-s", str(TESTS), "-v"],
        REPORTS / "tests.log",
    )


def refresh_registry() -> None:
    root = Path("/root/personal-os/PersonalOS")
    script = root / "scripts" / "experiment_registry.py"
    if not script.exists():
        return
    run(
        [
            "python3", str(script), "refresh", "--workspace-root", str(REPO),
            "--completed-id", CONFIG["experiment_id"],
        ],
        REPORTS / "registry_refresh.log",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cpu", type=int, default=int(CONFIG["measurement"]["cpu_affinity"])
    )
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="regenerate summaries and reports from the existing raw CSV",
    )
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()

    for directory in (BUILD, RAW, PROCESSED, REPORTS, PROVENANCE):
        directory.mkdir(parents=True, exist_ok=True)
    ensure_environment()
    analysis_quick = args.quick
    if args.analyze_only:
        with (RAW / "region_trials.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        formal_rows = (
            len(CONFIG["regions"])
            * len(CONFIG["phases"])
            * len(CONFIG["variants"])
            * int(CONFIG["measurement"]["trials"])
        )
        if len(rows) == formal_rows:
            analysis_quick = False
        elif len(rows) == len(CONFIG["regions"]) * len(CONFIG["phases"]) * 4 * 2:
            analysis_quick = True
        else:
            raise RuntimeError(
                f"existing raw CSV has unexpected row count: {len(rows)}"
            )
    else:
        compile_benchmark()
        rows = execute_cases(args.cpu, args.quick)
        write_raw(rows)
    summary = analyze(rows, analysis_quick)
    write_processed(summary)
    write_report(summary)
    write_provenance(args.cpu, summary)
    write_artifact_index()
    run_tests()
    if not args.skip_registry:
        refresh_registry()
    print(
        json.dumps(
            {
                "decision": summary["decision"],
                "rows": summary["raw_row_count"],
                "shared_vs_repacked": summary["comparison_summaries"][
                    "shared_a_microkernel_vs_repacked_a_microkernel"
                ],
                "shared_vs_concat": summary["comparison_summaries"][
                    "shared_a_microkernel_vs_concatenated_blis"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
