#!/usr/bin/env python3
"""Shared compiler, search-space, measurement, and artifact helpers."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
CHAPTER4 = EXPERIMENTS / "chapter4_space"
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
ONLINE_PRIOR = EXPERIMENTS / "chapter6_online_prior"

BUILD = PROJECT / "build"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
PROVENANCE = PROJECT / "provenance"

BUDDY_OPT = REPO / "build" / "bin" / "buddy-opt"
MLIR_OPT = REPO / "llvm" / "build" / "bin" / "mlir-opt"
MLIR_TRANSLATE = REPO / "llvm" / "build" / "bin" / "mlir-translate"
CXX = REPO / "llvm" / "build" / "bin" / "clang++"
BLIS = REPO / "jlq" / "thesis" / "blis" / "blis"
BLIS_INCLUDE = BLIS / "include" / "haswell"
BLIS_LIBRARY = BLIS / "lib" / "haswell" / "libblis.a"
DRIVER = PROJECT / "runtime" / "generic_matmul_bench.cpp"
ADAPTER = PROJECT / "runtime" / "blis_microkernel_adapter.cpp"
BLIS_DRIVER = PROJECT / "runtime" / "blis_frontend_bench.cpp"

sys.path.insert(0, str(CHAPTER4 / "scripts"))
sys.path.insert(0, str(CHAPTER6 / "scripts"))
from chapter4lib import (  # noqa: E402
    generate_spaces_for_task,
    load_inputs,
    raw_candidates,
    select_contract,
)
from chapter6lib import select_pool  # noqa: E402


DTYPES = {
    "f32": {
        "mlir": "f32",
        "cpp": "float",
        "mr": 6,
        "nr": 16,
        "k_step": 4,
        "wrapper": "buddy_blis_sgemm_6x16",
        "kernel": "bli_sgemm_haswell_asm_6x16",
        "frontend": "bli_sgemm",
    },
    "f64": {
        "mlir": "f64",
        "cpp": "double",
        "mr": 6,
        "nr": 8,
        "k_step": 4,
        "wrapper": "buddy_blis_dgemm_6x8",
        "kernel": "bli_dgemm_haswell_asm_6x8",
        "frontend": "bli_dgemm",
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True)
                if isinstance(value, (dict, list)) else value
                for key, value in row.items()
            })


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_key(*parts: Any) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def geometric_mean(values: Iterable[float]) -> float:
    clean = [max(float(value), 1.0e-300) for value in values]
    return math.exp(sum(math.log(value) for value in clean) / len(clean))


def logged_run(
    command: list[str], log: Path, cwd: Path = REPO,
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "$ " + " ".join(command) + f"\nELAPSED_MS={elapsed_ms:.6f}\n\n"
        + "STDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stderr[-2000:]}"
        )
    return completed, elapsed_ms


def ensure_tools(build_buddy: bool = True) -> None:
    required = [MLIR_OPT, MLIR_TRANSLATE, CXX]
    if build_buddy:
        completed = subprocess.run(
            ["cmake", "--build", str(REPO / "build"), "--target", "buddy-opt", "-j4"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        (REPORTS / "build_buddy.log").parent.mkdir(parents=True, exist_ok=True)
        (REPORTS / "build_buddy.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf-8"
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr[-2000:])
    required.append(BUDDY_OPT)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing compiler tools: " + ", ".join(missing))
    if not BLIS_LIBRARY.exists() or not (BLIS_INCLUDE / "blis.h").exists():
        raise FileNotFoundError(
            "BLIS Haswell static library is missing; run the source package configure/make first"
        )


def load_config() -> dict[str, Any]:
    config = read_json(PROJECT / "data" / "experiment_config.json")
    if "CGO_CPU" in os.environ:
        config["measurement"]["cpu_affinity"] = int(os.environ["CGO_CPU"])
    return config


def load_workloads() -> list[dict[str, Any]]:
    source = CHAPTER6 / "data" / "workloads.json"
    document = read_json(source)
    workloads = document["workloads"]
    ids = [row["id"] for row in workloads]
    if document.get("declaration_status") != "frozen_before_measurement":
        raise ValueError("source workload matrix is not frozen")
    if len(workloads) != 36 or len(ids) != len(set(ids)):
        raise ValueError("expected 36 unique frozen workloads")
    return workloads


def task_from_workload(workload: dict[str, Any], dtype: str) -> dict[str, Any]:
    if dtype not in DTYPES:
        raise KeyError(dtype)
    return {
        "id": workload["id"],
        "role": workload["family"],
        "operation": "linalg.matmul",
        "dtype": dtype,
        "shape": {"m": workload["m"], "k": workload["k"], "n": workload["n"]},
        "layout": {"a": "row_major", "b": "row_major", "c": "row_major"},
        "stride": {"a_inner": 1, "b_inner": 1, "c_inner": 1},
        "alignment_bytes": {"a": None, "b": None, "c": None},
        "target": {
            "machine": "x86_64",
            "architecture": "haswell",
            "features": ["avx2", "fma"],
            "vector_bits": 256,
            "cache_kib": {"l1d": 32, "l2": 256, "l3": 8192},
        },
        "threads": 1,
        "fallback_available": True,
        "available_adapters": {
            "packing": True,
            "mn_tail": True,
            "k_remainder": True,
            "layout_conversion": False,
            "alignment_copy": False,
        },
    }


def build_contract_state(
    dtype: str, workloads: list[dict[str, Any]], pool_size: int,
) -> dict[str, Any]:
    inputs = load_inputs(CHAPTER4)
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    state: dict[str, Any] = {}
    frequency: Counter[str] = Counter()
    for workload in workloads:
        task = task_from_workload(workload, dtype)
        spaces, rows, selection_log = generate_spaces_for_task(
            task, candidates, inputs["contracts"], inputs["space_config"]
        )
        contract, contract_selection = select_contract(task, inputs["contracts"])
        contract_rows = list(spaces["contract_only"])
        for row in contract_rows:
            frequency[row["candidate_id"]] += 1
        state[workload["id"]] = {
            "workload": workload,
            "task": task,
            "contract": contract,
            "contract_selection": contract_selection,
            "selection_log": selection_log,
            "rows": {row["candidate_id"]: row for row in rows},
            "contract_rows": contract_rows,
        }
    for workload_id, item in state.items():
        available = item["contract_rows"]
        if len(available) < pool_size:
            raise ValueError(f"{workload_id} has only {len(available)} Contract candidates")
        item["pool"] = select_pool(
            available, workload_id, "B2", pool_size, frequency
        )
    return state


def dynamic_payload(symbol: str, dtype: str) -> str:
    element = DTYPES[dtype]["mlir"]
    function = f"""func.func @{symbol}(
    %A: tensor<?x?x{element}>,
    %B: tensor<?x?x{element}>,
    %C: tensor<?x?x{element}>) -> tensor<?x?x{element}>
    attributes {{llvm.emit_c_interface}} {{
  %0 = linalg.matmul
    ins(%A, %B : tensor<?x?x{element}>, tensor<?x?x{element}>)
    outs(%C : tensor<?x?x{element}>) -> tensor<?x?x{element}>
  return %0 : tensor<?x?x{element}>
}}
"""
    indented = "\n".join("  " + line if line else line for line in function.splitlines())
    return f"module @cgo_payload attributes {{buddy.payload}} {{\n{indented}\n}}\n"


def microkernel_schedule(row: dict[str, Any], dtype: str) -> str:
    spec = DTYPES[dtype]
    options = " ".join(
        f"{name}={value}" for name, value in (
            ("tile-m", row["tile_m"]),
            ("tile-n", row["tile_n"]),
            ("tile-k", row["tile_k"]),
            ("mr", spec["mr"]),
            ("nr", spec["nr"]),
        )
    )
    wrapper = spec["wrapper"]
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(%root: !transform.any_op) {{
    %payload = transform.structured.match ops{{["builtin.module"]}}
      attributes{{buddy.payload}} in %root
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %payload
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    %prepared = transform.apply_registered_pass
      "buddy-materialize-blis-packed-matmul" to %bufferized
      {{options = "{options}"}}
      : (!transform.any_op) -> !transform.any_op
    %direct = transform.structured.match ops{{["func.call"]}}
      attributes{{callee = @buddy_microkernel_placeholder}} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %direct, "{wrapper}" : !transform.any_op
    %fringe = transform.structured.match ops{{["func.call"]}}
      attributes{{callee = @buddy_microkernel_fringe_placeholder}} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %fringe, "{wrapper}_fringe" : !transform.any_op
    transform.yield
  }}
}}
"""


def build_fingerprint(dtype: str) -> str:
    digest = hashlib.sha256(dtype.encode())
    for path in (
        REPO / "midend" / "lib" / "Conversion" / "MatMulOptimization"
        / "MatMulBlisMicrokernel.cpp",
        DRIVER,
        ADAPTER,
    ):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def compile_candidate(
    row: dict[str, Any], dtype: str, force: bool = False,
) -> dict[str, Any]:
    candidate_id = str(row["candidate_id"])
    case = BUILD / "binaries" / dtype / candidate_id
    manifest_path = case / "manifest.json"
    executable = case / "benchmark"
    fingerprint = build_fingerprint(dtype)
    if manifest_path.exists() and executable.exists() and not force:
        manifest = read_json(manifest_path)
        if manifest.get("build_fingerprint") == fingerprint:
            return manifest
    if row["predicted_path"] not in {"direct", "adapt"}:
        raise ValueError(f"{candidate_id} is not a microkernel-compatible candidate")
    case.mkdir(parents=True, exist_ok=True)
    symbol = "cgo_" + dtype + "_" + re.sub(r"[^A-Za-z0-9_]", "_", candidate_id)
    input_mlir = case / "input.mlir"
    transformed = case / "transformed.mlir"
    llvm_mlir = case / "llvm.mlir"
    llvm_ir = case / "kernel.ll"
    input_mlir.write_text(
        dynamic_payload(symbol, dtype) + microkernel_schedule(row, dtype),
        encoding="utf-8",
    )
    timings: dict[str, float] = {}
    _, timings["transform_ms"] = logged_run(
        [str(BUDDY_OPT), str(input_mlir), "--transform-interpreter",
         "--buddy-finalize-transform-payload", "--canonicalize", "--cse",
         "-o", str(transformed)],
        case / "01_transform.log",
    )
    _, timings["lower_ms"] = logged_run(
        [str(MLIR_OPT), str(transformed), "--convert-linalg-to-loops",
         "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case / "02_lower.log",
    )
    _, timings["translate_ms"] = logged_run(
        [str(MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir),
         "-o", str(llvm_ir)],
        case / "03_translate.log",
    )
    spec = DTYPES[dtype]
    _, timings["native_compile_ms"] = logged_run(
        [str(CXX), "-O3", "-march=native", "-std=c++17",
         f"-DKERNEL_SYMBOL={symbol}", f"-DSCALAR_TYPE={spec['cpp']}",
         "-I" + str(BLIS_INCLUDE), str(DRIVER), str(llvm_ir), str(ADAPTER),
         str(BLIS_LIBRARY), "-lpthread", "-lm", "-o", str(executable)],
        case / "04_native_compile.log",
    )
    symbols, timings["symbol_check_ms"] = logged_run(
        ["nm", "-C", str(executable)], case / "05_symbols.log"
    )
    llvm_text = llvm_ir.read_text(encoding="utf-8")
    manifest = {
        "dtype": dtype,
        "candidate_id": candidate_id,
        "predicted_path": row["predicted_path"],
        "symbol": symbol,
        "executable": str(executable),
        "executable_sha256": sha256(executable),
        "build_fingerprint": fingerprint,
        "wrapper_call_present": f"call void @{spec['wrapper']}(" in llvm_text,
        "fringe_wrapper_call_present": f"call void @{spec['wrapper']}_fringe(" in llvm_text,
        "blis_kernel_symbol_present": bool(re.search(
            rf"\bT {re.escape(str(spec['kernel']))}$", symbols.stdout, re.MULTILINE
        )),
        "pipeline_ms": round(sum(timings.values()), 6),
        **{key: round(value, 6) for key, value in timings.items()},
    }
    if not all(manifest[key] for key in (
        "wrapper_call_present", "fringe_wrapper_call_present",
        "blis_kernel_symbol_present",
    )):
        raise RuntimeError(f"incomplete microkernel linkage for {dtype} {candidate_id}")
    write_json(manifest_path, manifest)
    return manifest


def compile_blis_frontend(dtype: str, force: bool = False) -> dict[str, Any]:
    spec = DTYPES[dtype]
    case = BUILD / "binaries" / dtype / "B5_blis"
    manifest_path = case / "manifest.json"
    executable = case / "benchmark"
    fingerprint = hashlib.sha256(
        dtype.encode() + BLIS_DRIVER.read_bytes() + BLIS_LIBRARY.read_bytes()
    ).hexdigest()
    if manifest_path.exists() and executable.exists() and not force:
        manifest = read_json(manifest_path)
        if manifest.get("build_fingerprint") == fingerprint:
            return manifest
    case.mkdir(parents=True, exist_ok=True)
    _, compile_ms = logged_run(
        [str(CXX), "-O3", "-march=native", "-std=c++17",
         f"-DSCALAR_TYPE={spec['cpp']}", "-I" + str(BLIS_INCLUDE),
         str(BLIS_DRIVER), str(BLIS_LIBRARY), "-lpthread", "-lm",
         "-o", str(executable)],
        case / "01_compile.log",
    )
    symbols, symbol_ms = logged_run(
        ["nm", "-C", str(executable)], case / "02_symbols.log"
    )
    manifest = {
        "dtype": dtype,
        "candidate_id": None,
        "executable": str(executable),
        "executable_sha256": sha256(executable),
        "build_fingerprint": fingerprint,
        "blis_frontend_symbol_present": bool(re.search(
            rf"\bT {re.escape(str(spec['frontend']))}$", symbols.stdout, re.MULTILINE
        )),
        "blis_kernel_symbol_present": bool(re.search(
            rf"\bT {re.escape(str(spec['kernel']))}$", symbols.stdout, re.MULTILINE
        )),
        "pipeline_ms": round(compile_ms + symbol_ms, 6),
    }
    write_json(manifest_path, manifest)
    return manifest


def parse_benchmark(stdout: str) -> dict[str, Any]:
    rows = list(csv.DictReader(io.StringIO(stdout)))
    if not rows or rows[-1].get("status") != "PASS":
        raise RuntimeError("benchmark did not produce a passing CSV row")
    result: dict[str, Any] = {}
    for key, value in rows[-1].items():
        if key == "status":
            result[key] = value
        else:
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                result[key] = value
    return result


def expected_fringe_calls(
    workload: dict[str, Any], row: dict[str, Any], dtype: str,
    measurement: dict[str, Any], invocations: int = 1,
) -> int:
    spec = DTYPES[dtype]
    mr, nr = int(spec["mr"]), int(spec["nr"])
    m_panels = math.ceil(int(workload["m"]) / mr)
    n_panels = math.ceil(int(workload["n"]) / nr)
    full_panels = (int(workload["m"]) // mr) * (int(workload["n"]) // nr)
    k_panels = math.ceil(int(workload["k"]) / int(row["tile_k"]))
    calls_per_process = (
        int(measurement["warmups"]) + int(measurement["repeats"])
    ) * int(measurement["inner_iters"])
    return (m_panels * n_panels - full_panels) * k_panels * calls_per_process * invocations


def measure_live(
    manifest: dict[str, Any], workload: dict[str, Any], measurement: dict[str, Any],
    log: Path, row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    command = []
    cpu = measurement.get("cpu_affinity")
    if cpu is not None:
        command.extend(["taskset", "-c", str(cpu)])
    command.extend([
        str(manifest["executable"]), str(workload["m"]), str(workload["k"]),
        str(workload["n"]), str(measurement["warmups"]),
        str(measurement["repeats"]), str(measurement["inner_iters"]),
    ])
    completed, wall_ms = logged_run(command, log)
    values = parse_benchmark(completed.stdout)
    result = {
        **values,
        "benchmark_wall_ms": round(wall_ms, 6),
        "executable_sha256": manifest["executable_sha256"],
        "log": str(log),
    }
    if row is not None:
        dtype = str(manifest["dtype"])
        expected = expected_fringe_calls(workload, row, dtype, measurement)
        observed = int(float(values.get("fringe_calls", 0)))
        if observed != expected:
            raise RuntimeError(
                f"fringe mismatch for {workload['id']} {row['candidate_id']}: "
                f"expected {expected}, observed {observed}"
            )
        spec = DTYPES[dtype]
        result.update({
            "expected_fringe_calls": expected,
            "observed_path": "adapt" if (
                expected > 0 or int(workload["k"]) % int(spec["k_step"]) != 0
            ) else "direct",
        })
    return result


def aggregate_trials(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((str(row["workload_id"]), str(row["variant"])), []).append(row)
    aggregates = []
    for _, values in sorted(groups.items()):
        first = values[0]
        medians = [float(row["median_ms"]) for row in values]
        gflops = [float(row["gflops"]) for row in values]
        aggregates.append({
            **{key: first.get(key) for key in (
                "dtype", "workload_id", "family", "split", "m", "k", "n",
                "variant", "candidate_id", "predicted_path", "observed_path",
            )},
            "trial_count": len(values),
            "all_pass": all(row["status"] == "PASS" for row in values),
            "median_ms": statistics.median(medians),
            "min_trial_ms": min(medians),
            "max_trial_ms": max(medians),
            "median_gflops": statistics.median(gflops),
            "max_abs_diff": max(float(row["max_abs_diff"]) for row in values),
        })
    return aggregates
