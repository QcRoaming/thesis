#!/usr/bin/env python3
"""Run the frozen K230 OpenBLAS candidate pool through RT-Smart serial."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import select
import termios
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CSV_HEADER = (
    "variant,candidate_id,predicted_path,workload_id,m,k,n,tile_m,tile_n,"
    "tile_k,trial,time_seconds,gflops,projection_error,correct,"
    "initialize_seconds,pack_a_seconds,pack_b_seconds,kernel_seconds,"
    "scatter_seconds,counter_total_seconds,kernel_calls,fringe_calls,"
    "k_tail_calls"
)
VARIANTS = {"contract_adapter", "openblas_full"}
PROMPT = b"msh />"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def protocol(matrix_path: Path, repetitions: int) -> dict[str, Any]:
    document = read_json(matrix_path)
    workloads = {row["id"]: row for row in document["workloads"]}
    active = {
        (row["workload_id"], row["candidate_id"]): row
        for row in document["rows"]
        if row["executable"]
    }
    return {
        "workloads": workloads,
        "active": active,
        "repetitions": repetitions,
        "contract_rows": len(active) * repetitions,
        "baseline_rows": len(workloads) * repetitions,
        "total_rows": (len(active) + len(workloads)) * repetitions,
    }


def configure_serial(fd: int) -> None:
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
    attrs[3] = 0
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def read_until_prompt(fd: int, timeout_seconds: float, raw_log: Path) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    last_report = time.monotonic()
    payload = bytearray()
    raw_log.parent.mkdir(parents=True, exist_ok=True)
    with raw_log.open("wb") as stream:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.25)
            if fd not in ready:
                continue
            try:
                chunk = os.read(fd, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                continue
            payload.extend(chunk)
            stream.write(chunk)
            stream.flush()
            if time.monotonic() - last_report >= 30.0:
                adapter_markers = payload.count(b"contract_adapter,")
                library_markers = payload.count(b"openblas_full,")
                print(
                    "[k230-external] "
                    f"captured {len(payload)} bytes, approximately "
                    f"{adapter_markers + library_markers} result rows",
                    flush=True,
                )
                last_report = time.monotonic()
            if PROMPT in payload:
                return bytes(payload)
    raise TimeoutError(f"RT-Smart prompt not observed within {timeout_seconds}s")


def synchronize_prompt(fd: int, raw_log: Path) -> bytes:
    """Wake an idle shell or interrupt a stale foreground process."""
    attempts = ((b"\r", 3.0), (b"\x03\r", 10.0))
    captured = bytearray()
    for index, (sequence, timeout_seconds) in enumerate(attempts):
        attempt_log = raw_log.with_name(
            f"{raw_log.stem}.attempt{index + 1}.raw.log"
        )
        os.write(fd, sequence)
        try:
            payload = read_until_prompt(fd, timeout_seconds, attempt_log)
        except TimeoutError:
            if attempt_log.exists():
                captured.extend(attempt_log.read_bytes())
            continue
        captured.extend(payload)
        raw_log.write_bytes(captured)
        return bytes(captured)
    raw_log.write_bytes(captured)
    raise TimeoutError(
        "RT-Smart prompt not observed after wake-up and Ctrl+C recovery; "
        "use the RT-Smart channel (normally /dev/ttyACM1)"
    )


def integer(row: dict[str, str], field: str) -> int:
    try:
        return int(row[field])
    except (KeyError, ValueError) as error:
        raise RuntimeError(f"invalid integer field {field!r}: {row.get(field)!r}") from error


def validate_rows(rows: list[dict[str, str]], frozen: dict[str, Any]) -> None:
    expected_trials = set(range(frozen["repetitions"]))
    if len(rows) != frozen["total_rows"]:
        raise RuntimeError(
            f"captured {len(rows)} CSV rows; expected {frozen['total_rows']} "
            f"({frozen['contract_rows']} adapter + "
            f"{frozen['baseline_rows']} OpenBLAS)"
        )
    if {row["variant"] for row in rows} != VARIANTS:
        raise RuntimeError("captured variant set does not match the frozen protocol")
    if any(row["correct"] != "1" for row in rows):
        raise RuntimeError("board output contains a correctness failure")

    counts: Counter[tuple[str, str, str]] = Counter()
    trials: dict[tuple[str, str, str], set[int]] = {}
    for row in rows:
        workload_id = row["workload_id"]
        workload = frozen["workloads"].get(workload_id)
        if workload is None:
            raise RuntimeError(f"unexpected workload: {workload_id}")
        shape = (integer(row, "m"), integer(row, "k"), integer(row, "n"))
        expected_shape = (workload["m"], workload["k"], workload["n"])
        if shape != expected_shape:
            raise RuntimeError(
                f"shape mismatch for {workload_id}: {shape} != {expected_shape}"
            )

        key = (workload_id, row["variant"], row["candidate_id"])
        counts[key] += 1
        trials.setdefault(key, set()).add(integer(row, "trial"))
        if row["variant"] == "contract_adapter":
            candidate = frozen["active"].get(
                (workload_id, row["candidate_id"])
            )
            if candidate is None:
                raise RuntimeError(
                    f"unexpected active candidate: {workload_id}/{row['candidate_id']}"
                )
            expected_candidate = (
                int(candidate["tile_m"]),
                int(candidate["tile_n"]),
                int(candidate["tile_k"]),
                candidate["predicted_path"],
            )
            observed_candidate = (
                integer(row, "tile_m"),
                integer(row, "tile_n"),
                integer(row, "tile_k"),
                row["predicted_path"],
            )
            if observed_candidate != expected_candidate:
                raise RuntimeError(
                    f"candidate metadata mismatch for {workload_id}/"
                    f"{row['candidate_id']}: {observed_candidate} != "
                    f"{expected_candidate}"
                )
        else:
            if row["candidate_id"] != "openblas_full":
                raise RuntimeError("OpenBLAS baseline has an unexpected candidate id")
            if row["predicted_path"] != "library":
                raise RuntimeError("OpenBLAS baseline has an unexpected path")
            if any(integer(row, field) != 0 for field in ("tile_m", "tile_n", "tile_k")):
                raise RuntimeError("OpenBLAS baseline must use zero tile fields")

    expected_keys = {
        (workload_id, "contract_adapter", candidate_id)
        for workload_id, candidate_id in frozen["active"]
    }
    expected_keys.update(
        (workload_id, "openblas_full", "openblas_full")
        for workload_id in frozen["workloads"]
    )
    if set(counts) != expected_keys:
        missing = sorted(expected_keys - set(counts))
        extra = sorted(set(counts) - expected_keys)
        raise RuntimeError(f"result-group mismatch: missing={missing}, extra={extra}")
    for key in sorted(expected_keys):
        if counts[key] != frozen["repetitions"]:
            raise RuntimeError(
                f"{key} has {counts[key]} rows; expected {frozen['repetitions']}"
            )
        if trials[key] != expected_trials:
            raise RuntimeError(
                f"{key} trials are {sorted(trials[key])}; "
                f"expected {sorted(expected_trials)}"
            )


def extract_csv(
    payload: bytes,
    repetitions: int,
    matrix_path: Path,
) -> tuple[str, list[dict[str, str]], dict[str, Any]]:
    text = payload.decode("utf-8", errors="replace").replace("\r", "")
    text = ANSI_ESCAPE.sub("", text)
    prefixes = tuple(variant + "," for variant in sorted(VARIANTS))
    data_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(prefixes)
    ]
    csv_text = CSV_HEADER + "\n" + "\n".join(data_lines) + "\n"
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    frozen = protocol(matrix_path, repetitions)
    validate_rows(rows, frozen)
    return csv_text, rows, frozen


def probe_storage(port: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        synchronize_prompt(fd, output_dir / "probe_initial_prompt.raw.log")
        for label, path in (
            ("sdcard", "/sdcard"),
            (
                "external_package",
                "/sdcard/chapter6-k230-openblas-external-validation",
            ),
        ):
            termios.tcflush(fd, termios.TCIFLUSH)
            os.write(fd, f"ls {path}".encode("ascii") + b"\r")
            payload = read_until_prompt(
                fd, 10.0, output_dir / f"probe_{label}.raw.log"
            )
            decoded = ANSI_ESCAPE.sub(
                "", payload.decode("utf-8", errors="replace").replace("\r", "")
            )
            print(f"[k230-external] ls {path}:\n{decoded}", flush=True)
    finally:
        os.close(fd)


def run(
    port: Path,
    board_root: str,
    output_dir: Path,
    repetitions: int,
    timeout_seconds: float,
    matrix_path: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (output_dir / "run_timestamp_utc.txt").write_text(
        timestamp + "\n", encoding="ascii"
    )
    (output_dir / "serial_port.txt").write_text(str(port) + "\n", encoding="ascii")
    (output_dir / "board_root.txt").write_text(board_root + "\n", encoding="ascii")
    raw_log = output_dir / "k230_openblas_contract_pool.raw.log"
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        synchronize_prompt(fd, output_dir / "initial_prompt.raw.log")
        termios.tcflush(fd, termios.TCIFLUSH)
        command = (
            f"{board_root}/build/k230_external/"
            "k230_openblas_contract_pool.elf"
        )
        print(f"[k230-external] starting {command}", flush=True)
        os.write(fd, command.encode("ascii") + b"\r")
        payload = read_until_prompt(fd, timeout_seconds, raw_log)
    finally:
        os.close(fd)

    csv_text, rows, frozen = extract_csv(payload, repetitions, matrix_path)
    csv_path = output_dir / "k230_openblas_contract_pool.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "status": "PASS",
        "timestamp_utc": timestamp,
        "serial_port": str(port),
        "board_root": board_root,
        "repetitions": repetitions,
        "workloads": len(frozen["workloads"]),
        "active_candidates": len(frozen["active"]),
        "contract_rows": frozen["contract_rows"],
        "baseline_rows": frozen["baseline_rows"],
        "correctness_rows": len(rows),
        "matrix_sha256": sha256(matrix_path),
        "csv_sha256": sha256(csv_path),
    }
    (output_dir / "serial_run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    checksum_paths = sorted(output_dir.glob("*.csv")) + sorted(
        output_dir.glob("*.json")
    ) + sorted(output_dir.glob("*.raw.log"))
    with (output_dir / "sha256sums.txt").open("w", encoding="ascii") as stream:
        for path in checksum_paths:
            stream.write(f"{sha256(path)}  {path.name}\n")
    print(
        f"[k230-external] complete: {len(rows)} correct rows "
        f"({frozen['contract_rows']} adapter + {frozen['baseline_rows']} "
        f"OpenBLAS) -> {csv_path}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=Path, default=Path("/dev/ttyACM1"))
    parser.add_argument(
        "--board-root",
        default="/sdcard/chapter6-k230-openblas-external-validation",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=14400.0)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=PROJECT / "processed" / "k230_candidate_matrix.json",
    )
    parser.add_argument(
        "--probe-storage",
        action="store_true",
        help="list the RT-Smart SD-card and package roots without running the ELF",
    )
    args = parser.parse_args()
    if args.probe_storage:
        probe_storage(args.port, args.output_dir.resolve())
        return
    if args.repetitions != 3:
        raise ValueError("the frozen board ELF defaults to exactly three repetitions")
    run(
        args.port,
        args.board_root,
        args.output_dir.resolve(),
        args.repetitions,
        args.timeout,
        args.matrix.resolve(),
    )


if __name__ == "__main__":
    main()
