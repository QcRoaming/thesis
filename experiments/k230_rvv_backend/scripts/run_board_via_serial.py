#!/usr/bin/env python3
"""Run the K230 RT-Smart benchmark suite through a serial console."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import select
import sys
import termios
import time
from datetime import datetime, timezone
from pathlib import Path


CSV_HEADER = (
    "binary,candidate,implementation,source_prior,workload,m,n,k,tile_m,"
    "tile_n,tile_k,trial,time_seconds,gflops,projection_error,correct"
)
RUNS = (
    ("k230_gemm_scalar", "scalar", 40),
    ("k230_gemm_rvv", "rvv", 240),
    ("k230_gemm_openblas", "openblas", 280),
)
PROMPT = b"msh />"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
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
                    f"[serial-runner] {raw_log.name}: "
                    f"captured {len(payload)} bytes",
                    flush=True,
                )
                last_report = time.monotonic()
            if PROMPT in payload:
                return bytes(payload)
    raise TimeoutError(f"RT-Smart prompt not observed within {timeout_seconds} seconds")


def extract_csv(payload: bytes, binary_id: str) -> tuple[str, int]:
    text = payload.decode("utf-8", errors="replace").replace("\r", "")
    text = ANSI_ESCAPE.sub("", text)
    lines = [line.strip() for line in text.splitlines()]
    data_lines = [line for line in lines if line.startswith(binary_id + ",")]
    csv_text = CSV_HEADER + "\n" + "\n".join(data_lines) + "\n"
    rows = list(csv.DictReader(csv_text.splitlines()))
    if not rows:
        raise RuntimeError(f"no CSV rows captured for {binary_id}")
    if any(row.get("binary") != binary_id for row in rows):
        raise RuntimeError(f"binary identity mismatch in captured {binary_id} rows")
    if any(row.get("correct") != "1" for row in rows):
        raise RuntimeError(f"correctness failure reported by {binary_id}")
    return csv_text, len(rows)


def run_suite(
    port: Path,
    board_root: str,
    output_dir: Path,
    timeout_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (output_dir / "run_timestamp_utc.txt").write_text(timestamp + "\n", encoding="ascii")
    (output_dir / "serial_port.txt").write_text(str(port) + "\n", encoding="ascii")

    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd)
        termios.tcflush(fd, termios.TCIFLUSH)
        os.write(fd, b"\r")
        read_until_prompt(fd, 10.0, output_dir / "initial_prompt.raw.log")

        for stem, binary_id, expected_rows in RUNS:
            termios.tcflush(fd, termios.TCIFLUSH)
            command = f"{board_root}/build/elf/{stem}.elf"
            print(f"\n[serial-runner] starting {stem}", flush=True)
            os.write(fd, command.encode("ascii") + b"\r")
            payload = read_until_prompt(
                fd,
                timeout_seconds,
                output_dir / f"{stem}.raw.log",
            )
            csv_text, row_count = extract_csv(payload, binary_id)
            if row_count != expected_rows:
                raise RuntimeError(
                    f"{stem} produced {row_count} rows; expected {expected_rows}"
                )
            csv_path = output_dir / f"{stem}.csv"
            csv_path.write_text(csv_text, encoding="utf-8")
            print(
                f"\n[serial-runner] completed {stem}: "
                f"{row_count} correct rows -> {csv_path}",
                flush=True,
            )
    finally:
        os.close(fd)

    checksum_paths = sorted(output_dir.glob("*.csv")) + sorted(output_dir.glob("*.raw.log"))
    with (output_dir / "sha256sums.txt").open("w", encoding="ascii") as stream:
        for path in checksum_paths:
            stream.write(f"{sha256(path)}  {path.name}\n")
    print(f"[serial-runner] suite complete: {output_dir}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=Path, default=Path("/dev/ttyACM1"))
    parser.add_argument(
        "--board-root",
        default="/sharefs/k230_rvv_backend",
        help="RT-Smart path containing build/elf",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-per-binary", type=float, default=7200.0)
    args = parser.parse_args()
    run_suite(
        args.port,
        args.board_root,
        args.output_dir.resolve(),
        args.timeout_per_binary,
    )


if __name__ == "__main__":
    main()
