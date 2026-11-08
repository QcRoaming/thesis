#!/usr/bin/env python3
"""Build a GitHub-safe snapshot of the thesis experiment evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve()
EXPERIMENTS = SCRIPT.parent.parent
WORKSPACE = EXPERIMENTS.parents[2]
DEFAULT_REGISTRY = Path("/root/personal-os/PersonalOS/registries/experiments.json")
MAX_GIT_FILE_BYTES = 95 * 1024 * 1024

SYNC_DIRS = {
    "4.5",
    "board",
    "config",
    "data",
    "figures",
    "mlir",
    "processed",
    "provenance",
    "reports",
    "results",
    "runtime",
    "scripts",
    "tests",
    "verification",
}
SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "outputs",
}
TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".csv",
    ".h",
    ".hpp",
    ".json",
    ".jsonl",
    ".ll",
    ".log",
    ".md",
    ".mlir",
    ".py",
    ".sh",
    ".td",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}
FIGURE_SUFFIXES = {".pdf", ".png", ".svg"}
EXTRA_IMPLEMENTATION_FILES = (
    "midend/include/Dialect/Microkernel/TransformOps.td",
    "midend/lib/Dialect/Microkernel/TransformOps.cpp",
    "midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if len(document.get("entries", [])) != 21:
        raise ValueError(f"expected 21 registry entries: {path}")
    return document


def source_git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=EXPERIMENTS.parents[1],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def registry_files(registry: dict) -> set[Path]:
    output: set[Path] = set()
    for entry in registry["entries"]:
        candidates = [entry.get("artifact_index", "")]
        candidates.extend(entry.get("evidence_files", []))
        for value in candidates:
            if not value:
                continue
            path = (WORKSPACE / value).resolve()
            if path.is_file() and WORKSPACE.resolve() in path.parents:
                output.add(path)
    return output


def is_selected_experiment_file(path: Path) -> bool:
    relative = path.relative_to(EXPERIMENTS)
    parts = relative.parts
    if any(part in SKIP_DIRS for part in parts):
        return False
    if "board_results" in parts or any(part.startswith("board_results_") for part in parts):
        return False
    if parts[:2] == ("chapter6_external_validation", "raw"):
        return False
    if "returned" in parts:
        return path.name.startswith("chapter6-i9-result-") and (
            path.name.endswith(".tar.gz") or path.name.endswith(".sha256")
        )
    if "raw" in parts:
        return False
    if len(parts) == 1:
        return path.suffix.lower() in TEXT_SUFFIXES
    if any(part in SYNC_DIRS for part in parts):
        suffix = path.suffix.lower()
        if "figures" in parts:
            return suffix in FIGURE_SUFFIXES
        return suffix in TEXT_SUFFIXES or suffix in FIGURE_SUFFIXES
    return path.suffix.lower() in TEXT_SUFFIXES and len(parts) <= 3


def canonical_board_files() -> set[Path]:
    output: set[Path] = set()
    summary_paths = (
        EXPERIMENTS / "chapter6_application_validation/processed/k230_mlir_closure_summary.json",
        EXPERIMENTS / "chapter6_external_validation/processed/k230_external_summary.json",
    )
    for summary_path in summary_paths:
        if not summary_path.is_file():
            continue
        document = json.loads(summary_path.read_text(encoding="utf-8"))
        root = Path(document["archived_result_dir"])
        if root.is_dir() and WORKSPACE.resolve() in root.resolve().parents:
            output.update(path for path in root.rglob("*") if path.is_file())
    k230_summary = EXPERIMENTS / "k230_rvv_backend/processed/k230_board_summary.json"
    if k230_summary.is_file():
        document = json.loads(k230_summary.read_text(encoding="utf-8"))
        for row in document.get("input_files", []) + document.get("metadata_files", []):
            path = Path(row["path"])
            if path.is_file() and WORKSPACE.resolve() in path.resolve().parents:
                output.add(path)
    return output


def copy_file(source: Path, destination_root: Path) -> dict:
    relative = source.relative_to(WORKSPACE)
    destination = destination_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": relative.as_posix(),
        "size_bytes": source.stat().st_size,
        "sha256": sha256(source),
    }


def build(destination: Path, registry_path: Path) -> None:
    registry = load_registry(registry_path)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    selected = {
        path
        for path in EXPERIMENTS.rglob("*")
        if path.is_file() and is_selected_experiment_file(path)
    }
    selected.update(registry_files(registry))
    selected.update(canonical_board_files())
    selected.update(
        WORKSPACE / relative
        for relative in EXTRA_IMPLEMENTATION_FILES
        if (WORKSPACE / relative).is_file()
    )

    copied: list[dict] = []
    excluded_large: list[dict] = []
    excluded_infrastructure: list[str] = []
    for source in sorted(selected):
        relative = source.relative_to(WORKSPACE)
        if any(part in {"build", "dist", "outputs"} for part in relative.parts):
            excluded_infrastructure.append(relative.as_posix())
            continue
        size = source.stat().st_size
        if size > MAX_GIT_FILE_BYTES:
            excluded_large.append({
                "path": relative.as_posix(),
                "size_bytes": size,
                "sha256": sha256(source),
            })
            continue
        copied.append(copy_file(source, destination))

    registry_destination = (
        destination
        / "jlq/thesis/experiments/data/experiment_registry_snapshot.json"
    )
    registry_destination.parent.mkdir(parents=True, exist_ok=True)
    registry_destination.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    copied.append({
        "path": registry_destination.relative_to(destination).as_posix(),
        "size_bytes": registry_destination.stat().st_size,
        "sha256": sha256(registry_destination),
    })

    readme = destination / "README.md"
    readme.write_text(
        "# Buddy-MLIR Thesis Experiment Evidence\n\n"
        "This repository is a GitHub-safe evidence snapshot for the GEMM thesis "
        "experiments. Start with "
        "`jlq/thesis/experiments/EXPERIMENTS_DETAILED_GUIDE.md`, then use "
        "`FINAL_EXPERIMENT_AUDIT.md` and `PAPER_EVIDENCE_CATALOG.md` for the "
        "consolidated conclusions and paper-use boundaries.\n\n"
        "Build caches, toolchains, duplicate extracted return trees, executables, "
        "and large deployment bundles are intentionally excluded. Their hashes and "
        "local provenance remain in the experiment packages.\n",
        encoding="utf-8",
    )
    copied.append({
        "path": "README.md",
        "size_bytes": readme.stat().st_size,
        "sha256": sha256(readme),
    })
    gitignore = destination / ".gitignore"
    gitignore.write_text(
        "__pycache__/\n*.pyc\n.pytest_cache/\nbuild/\ndist/\noutputs/\n",
        encoding="ascii",
    )
    copied.append({
        "path": ".gitignore",
        "size_bytes": gitignore.stat().st_size,
        "sha256": sha256(gitignore),
    })

    manifest = {
        "schema_version": 1,
        "snapshot_id": "buddy-mlir-thesis-experiments",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_workspace": str(WORKSPACE),
        "source_git_commit": source_git_revision(),
        "registry_entries": len(registry["entries"]),
        "file_count": len(copied),
        "total_bytes": sum(row["size_bytes"] for row in copied),
        "storage_boundary": (
            "GitHub-safe reproducibility evidence; local build caches, toolchains, "
            "duplicate extracted trees, binaries and oversized artifacts are excluded"
        ),
        "excluded_infrastructure_paths": sorted(excluded_infrastructure),
        "excluded_large_files": excluded_large,
        "files": sorted(copied, key=lambda row: row["path"]),
    }
    (destination / "SNAPSHOT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "destination": str(destination),
        "files": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "excluded_infrastructure": len(excluded_infrastructure),
        "excluded_large": len(excluded_large),
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    build(args.destination.resolve(), args.registry.resolve())


if __name__ == "__main__":
    main()
