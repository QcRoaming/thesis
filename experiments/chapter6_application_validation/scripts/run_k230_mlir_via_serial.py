#!/usr/bin/env python3
"""Run the frozen K230 MLIR closure ELF through an RT-Smart serial shell."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import re
import select
import termios
import time
from datetime import datetime, timezone
from pathlib import Path


CSV_HEADER = (
    "variant,case_id,workload_id,candidate_id,expected_path,m,k,n,tile_m,"
    "tile_n,tile_k,trial,time_seconds,gflops,projection_error,correct,"
    "observed_path,path_match,initialize_seconds,pack_a_seconds,"
    "pack_b_seconds,kernel_seconds,scatter_seconds,kernel_calls,"
    "fringe_calls,k_tail_calls,adapter_calls"
)
VARIANTS = {"c_adapter_direct", "mlir_transform_adapter", "openblas_full"}
CASES = {
    "direct_qkv_prefill_m32",
    "adapt_qkv_fringe_m17",
    "adapt_down_fringe_m33",
}
PROMPT = b"msh />"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
                print(
                    f"[k230-mlir] {raw_log.name}: captured {len(payload)} bytes",
                    flush=True,
                )
                last_report = time.monotonic()
            if PROMPT in payload:
                return bytes(payload)
    raise TimeoutError(f"RT-Smart prompt not observed within {timeout_seconds}s")


def synchronize_prompt(fd: int, raw_log: Path) -> bytes:
    """Wake an idle shell or interrupt a stale foreground process."""
    attempts = (
        (b"\r", 3.0),
        (b"\x03\r", 10.0),
    )
    captured = bytearray()
    for index, (sequence, timeout_seconds) in enumerate(attempts):
        attempt_log = raw_log.with_name(f"{raw_log.stem}.attempt{index + 1}.raw.log")
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
        "try the other USB serial channel (for example --port /dev/ttyACM0)"
    )


def extract_csv(payload: bytes, repetitions: int) -> tuple[str, list[dict[str, str]]]:
    text = payload.decode("utf-8", errors="replace").replace("\r", "")
    text = ANSI_ESCAPE.sub("", text)
    prefixes = tuple(variant + "," for variant in sorted(VARIANTS))
    data_lines = [
        line.strip() for line in text.splitlines()
        if line.strip().startswith(prefixes)
    ]
    csv_text = CSV_HEADER + "\n" + "\n".join(data_lines) + "\n"
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    expected_rows = len(VARIANTS) * len(CASES) * repetitions
    if len(rows) != expected_rows:
        raise RuntimeError(f"captured {len(rows)} CSV rows; expected {expected_rows}")
    if {row["variant"] for row in rows} != VARIANTS:
        raise RuntimeError("captured variant set does not match the frozen protocol")
    if {row["case_id"] for row in rows} != CASES:
        raise RuntimeError("captured case set does not match the frozen protocol")
    if any(row["correct"] != "1" for row in rows):
        raise RuntimeError("board output contains a correctness failure")
    adapter_rows = [row for row in rows if row["variant"] != "openblas_full"]
    if any(row["path_match"] != "1" for row in adapter_rows):
        raise RuntimeError("board output contains an adapter path mismatch")
    for variant in VARIANTS:
        if sum(row["variant"] == variant for row in rows) != len(CASES) * repetitions:
            raise RuntimeError(f"incomplete rows for {variant}")
    return csv_text, rows


def probe_sharefs(port: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        synchronize_prompt(fd, output_dir / "probe_initial_prompt.raw.log")
        for label, path in (
            ("sharefs", "/sharefs"),
            ("experiment", "/sharefs/experiment"),
            ("sdcard", "/sdcard"),
            ("sdcard_experiment", "/sdcard/experiment"),
            (
                "sdcard_closure",
                "/sdcard/chapter6-k230-mlir-closure-validation",
            ),
            (
                "sdcard_experiment_closure",
                "/sdcard/experiment/chapter6-k230-mlir-closure-validation",
            ),
        ):
            termios.tcflush(fd, termios.TCIFLUSH)
            os.write(fd, f"ls {path}".encode("ascii") + b"\r")
            payload = read_until_prompt(fd, 10.0, output_dir / f"probe_{label}.raw.log")
            decoded = ANSI_ESCAPE.sub(
                "", payload.decode("utf-8", errors="replace").replace("\r", "")
            )
            print(f"[k230-mlir] ls {path}:\n{decoded}", flush=True)
    finally:
        os.close(fd)


def run(
    port: Path,
    board_root: str,
    output_dir: Path,
    repetitions: int,
    timeout_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (output_dir / "run_timestamp_utc.txt").write_text(timestamp + "\n", encoding="ascii")
    (output_dir / "serial_port.txt").write_text(str(port) + "\n", encoding="ascii")
    (output_dir / "board_root.txt").write_text(board_root + "\n", encoding="ascii")
    raw_log = output_dir / "k230_mlir_closure.raw.log"
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        synchronize_prompt(fd, output_dir / "initial_prompt.raw.log")
        termios.tcflush(fd, termios.TCIFLUSH)
        command = f"{board_root}/build/k230_mlir_closure/k230_mlir_closure.elf"
        print(f"[k230-mlir] starting {command}", flush=True)
        os.write(fd, command.encode("ascii") + b"\r")
        payload = read_until_prompt(fd, timeout_seconds, raw_log)
    finally:
        os.close(fd)
    csv_text, rows = extract_csv(payload, repetitions)
    csv_path = output_dir / "k230_mlir_closure.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    checksum_paths = sorted(output_dir.glob("*.csv")) + sorted(output_dir.glob("*.raw.log"))
    with (output_dir / "sha256sums.txt").open("w", encoding="ascii") as stream:
        for path in checksum_paths:
            stream.write(f"{sha256(path)}  {path.name}\n")
    print(
        f"[k230-mlir] complete: {len(rows)} correct rows -> {csv_path}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=Path, default=Path("/dev/ttyACM1"))
    parser.add_argument(
        "--board-root",
        default="/sdcard/chapter6-k230-mlir-closure-validation",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument(
        "--probe-sharefs",
        action="store_true",
        help="list common RT-Smart shared-storage roots without running the ELF",
    )
    args = parser.parse_args()
    if args.probe_sharefs:
        probe_sharefs(args.port, args.output_dir.resolve())
        return
    if args.repetitions != 5:
        raise ValueError("the frozen board ELF defaults to exactly five repetitions")
    run(
        args.port,
        args.board_root,
        args.output_dir.resolve(),
        args.repetitions,
        args.timeout,
    )


if __name__ == "__main__":
    main()
