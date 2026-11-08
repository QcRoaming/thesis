#!/usr/bin/env python3
"""Verify every immutable file in the i9 external-validation delta package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path)
    args = parser.parse_args()
    root = args.package_root.resolve()
    manifest = json.loads((root / "package_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing: {record['path']}")
        elif path.stat().st_size != int(record["size_bytes"]):
            failures.append(f"size mismatch: {record['path']}")
        elif sha256(path) != record["sha256"]:
            failures.append(f"sha256 mismatch: {record['path']}")
    if failures:
        raise SystemExit("package verification failed:\n" + "\n".join(failures))
    print(f"PASS: verified {len(manifest['files'])} immutable package files")


if __name__ == "__main__":
    main()
