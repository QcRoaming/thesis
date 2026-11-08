#!/usr/bin/env python3
"""Build K230 RT-Smart static ELF benchmarks with the official SDK toolchain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tarfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent
THESIS = PROJECT.parents[1]
DEFAULT_SDK = THESIS / "third_party" / "k230_sdk"
DEFAULT_OPENBLAS = THESIS / "third_party" / "OpenBLAS"
WORKSPACE = THESIS.parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()


def run(command: list[str], cwd: Path | None = None, log: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    if log is None:
        subprocess.run(command, cwd=cwd, check=True)
    else:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w", encoding="utf-8") as stream:
            subprocess.run(command, cwd=cwd, check=True, stdout=stream, stderr=subprocess.STDOUT)


def toolchain_paths(sdk: Path) -> dict[str, Path]:
    binary = sdk / "toolchain" / "riscv64-linux-musleabi_for_x86_64-pc-linux-gnu" / "bin"
    prefix = binary / "riscv64-unknown-linux-musl-"
    paths = {
        name: Path(str(prefix) + name)
        for name in ("gcc", "ar", "ranlib", "readelf", "objdump", "nm")
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("official K230 RT-Smart toolchain missing: " + ", ".join(missing))
    return paths


def ensure_openblas_worktree(source: Path, destination: Path) -> str:
    revision = output(["git", "-C", str(source), "rev-parse", "HEAD"])
    if not destination.exists():
        run(["git", "-C", str(source), "worktree", "add", "--detach", str(destination), revision])
    actual = output(["git", "-C", str(destination), "rev-parse", "HEAD"])
    if actual != revision:
        raise RuntimeError(f"OpenBLAS K230 worktree revision mismatch: {actual} != {revision}")
    return revision


def generate_rvv_compatibility(worktree: Path, build_dir: Path, gcc: Path) -> dict[str, object]:
    """Bridge ratified intrinsic names to the API shipped by K230's GCC."""
    token_pattern = re.compile(r"\b__riscv_[A-Za-z0-9_]+\b")
    predefined = {
        "__riscv_v", "__riscv_vector", "__riscv_v_elen", "__riscv_v_min_vlen",
        "__riscv_xtheadc",
    }
    tokens: set[str] = set()
    source_files = sorted((worktree / "kernel" / "riscv64").glob("**/*.[ch]"))
    for path in source_files:
        tokens.update(token_pattern.findall(path.read_text(encoding="utf-8", errors="ignore")))
    intrinsics = sorted(token for token in tokens if token.startswith("__riscv_v") and token not in predefined)
    if not intrinsics:
        raise RuntimeError("no prefixed RVV intrinsics found in OpenBLAS sources")

    compatibility_dir = build_dir / "rvv_intrinsic_compat"
    compatibility_dir.mkdir(parents=True, exist_ok=True)
    header = compatibility_dir / "k230_rvv_intrinsic_compat.h"
    header_lines = [
        "/* Generated: map ratified RVV intrinsic names to the K230 GCC API. */",
        "#ifndef K230_RVV_INTRINSIC_COMPAT_H",
        "#define K230_RVV_INTRINSIC_COMPAT_H",
    ]

    def flatten_tuple_type(intrinsic: str) -> str:
        lmul_exponents = {"mf8": -3, "mf4": -2, "mf2": -1, "m1": 0, "m2": 1, "m4": 2, "m8": 3}
        exponent_lmuls = {value: key for key, value in lmul_exponents.items()}

        def replace(match: re.Match[str]) -> str:
            element, lmul, count_text = match.groups()
            count = int(count_text)
            count_exponent = {2: 1, 4: 2, 8: 3}.get(count)
            if count_exponent is None:
                return match.group(0)
            combined = lmul_exponents[lmul] + count_exponent
            if combined not in exponent_lmuls:
                return match.group(0)
            return element + exponent_lmuls[combined]

        return re.sub(r"(bf16|f16|f32|f64)(mf[248]|m[1248])x([2348])", replace, intrinsic)

    tuple_type_pattern = re.compile(r"\bv(float|bfloat|int|uint)(16|32|64)(mf[248]|m[1248])x([248])_t\b")
    tuple_type_mappings: dict[str, str] = {}
    for path in source_files:
        for kind, width, lmul, count_text in tuple_type_pattern.findall(
            path.read_text(encoding="utf-8", errors="ignore")
        ):
            source_type = f"v{kind}{width}{lmul}x{count_text}_t"
            flattened = flatten_tuple_type(f"f32{lmul}x{count_text}").removeprefix("f32")
            if "x" not in flattened:
                tuple_type_mappings[source_type] = f"v{kind}{width}{flattened}_t"
    header_lines.extend(
        f"#define {source_type} {target_type}"
        for source_type, target_type in sorted(tuple_type_mappings.items())
    )

    for name in intrinsics:
        old_name = flatten_tuple_type(name.removeprefix("__riscv_"))
        if re.match(r"__riscv_vfred(?:max|min|usum)_vs_", name):
            if old_name.endswith("_tu"):
                base_name = old_name.removesuffix("_tu")
                header_lines.append(
                    f"#define {name}(maskedoff, vs2, vs1, vl) "
                    f"{base_name}(maskedoff, vs2, vs1, vl)"
                )
            else:
                header_lines.append(
                    f"#define {name}(vs2, vs1, vl) {old_name}(vs1, vs2, vs1, vl)"
                )
        elif re.match(r"__riscv_vslidedown_vx_", name):
            header_lines.append(
                f"#define {name}(src, offset, vl) {old_name}(src, src, offset, vl)"
            )
        elif match := re.fullmatch(
            r"__riscv_vsseg([248])e(16|32|64)_v_((?:bf16|f16|f32|f64)(?:mf[248]|m[1248]))x\1",
            name,
        ):
            count = int(match.group(1))
            width = match.group(2)
            component_type = match.group(3)
            flat_type = flatten_tuple_type(f"{component_type}x{count}")
            extracts = ", ".join(
                f"vget_v_{flat_type}_{component_type}(group, {index})"
                for index in range(count)
            )
            header_lines.append(
                f"#define {name}(base, group, vl) "
                f"vsseg{count}e{width}_v_{component_type}(base, {extracts}, vl)"
            )
        elif match := re.fullmatch(
            r"__riscv_vlseg([2348])e(16|32|64)_v_((?:bf16|f16|f32|f64)(?:mf[248]|m[1248]))x\1",
            name,
        ):
            count = int(match.group(1))
            width = match.group(2)
            component_type = match.group(3)
            flat_type = flatten_tuple_type(f"{component_type}x{count}")
            c_prefix = "vbfloat" if component_type.startswith("bf16") else "vfloat"
            c_width_lmul = component_type.removeprefix("bf16").removeprefix("f16").removeprefix("f32").removeprefix("f64")
            element_width = re.match(r"(?:bf16|f16|f32|f64)", component_type).group(0).removeprefix("bf").removeprefix("f")
            component_c_type = f"{c_prefix}{element_width}{c_width_lmul}_t"
            flat_lmul = flat_type.removeprefix("bf16").removeprefix("f16").removeprefix("f32").removeprefix("f64")
            flat_c_type = f"{c_prefix}{element_width}{flat_lmul}_t"
            zero_intrinsic = f"vfmv_v_f_{flat_type}"
            parts = [f"_k230_part_{index}" for index in range(count)]
            declarations = f"{component_c_type} " + ", ".join(parts) + ";"
            load_call = (
                f"vlseg{count}e{width}_v_{component_type}("
                + ", ".join(f"&{part}" for part in parts)
                + ", base, vl);"
            )
            sets = " ".join(
                f"_k230_group = vset_v_{component_type}_{flat_type}(_k230_group, {index}, {part});"
                for index, part in enumerate(parts)
            )
            header_lines.append(
                f"#define {name}(base, vl) ({{ {declarations} "
                f"{flat_c_type} _k230_group = {zero_intrinsic}(0, (vl) * {count}); "
                f"{load_call} {sets} _k230_group; }})"
            )
        elif match := re.fullmatch(
            r"__riscv_vlsseg([2348])e(16|32|64)_v_((?:bf16|f16|f32|f64)(?:mf[248]|m[1248]))x\1",
            name,
        ):
            count = int(match.group(1))
            width = match.group(2)
            component_type = match.group(3)
            flat_type = flatten_tuple_type(f"{component_type}x{count}")
            element_match = re.match(r"(bf16|f16|f32|f64)(mf[248]|m[1248])", component_type)
            element, component_lmul = element_match.groups()
            c_prefix = "vbfloat" if element == "bf16" else "vfloat"
            element_width = element.removeprefix("bf").removeprefix("f")
            component_c_type = f"{c_prefix}{element_width}{component_lmul}_t"
            flat_lmul = flat_type.removeprefix(element)
            flat_c_type = f"{c_prefix}{element_width}{flat_lmul}_t"
            zero_intrinsic = f"vfmv_v_f_{flat_type}"
            parts = [f"_k230_part_{index}" for index in range(count)]
            declarations = f"{component_c_type} " + ", ".join(parts) + ";"
            load_call = (
                f"vlsseg{count}e{width}_v_{component_type}("
                + ", ".join(f"&{part}" for part in parts)
                + ", base, stride, vl);"
            )
            sets = " ".join(
                f"_k230_group = vset_v_{component_type}_{flat_type}(_k230_group, {index}, {part});"
                for index, part in enumerate(parts)
            )
            header_lines.append(
                f"#define {name}(base, stride, vl) ({{ {declarations} "
                f"{flat_c_type} _k230_group = {zero_intrinsic}(0, (vl) * {count}); "
                f"{load_call} {sets} _k230_group; }})"
            )
        elif match := re.fullmatch(
            r"__riscv_vssseg([2348])e(16|32|64)_v_((?:bf16|f16|f32|f64)(?:mf[248]|m[1248]))x\1",
            name,
        ):
            count = int(match.group(1))
            width = match.group(2)
            component_type = match.group(3)
            flat_type = flatten_tuple_type(f"{component_type}x{count}")
            extracts = ", ".join(
                f"vget_v_{flat_type}_{component_type}(group, {index})"
                for index in range(count)
            )
            header_lines.append(
                f"#define {name}(base, stride, group, vl) "
                f"vssseg{count}e{width}_v_{component_type}(base, stride, {extracts}, vl)"
            )
        else:
            header_lines.append(f"#define {name} {old_name}")
    header_lines.extend(["#endif", ""])
    header.write_text("\n".join(header_lines), encoding="ascii")

    wrapper = compatibility_dir / "k230-openblas-gcc"
    wrapper.write_text(
        "#!/bin/sh\nexec " + shlex.quote(str(gcc)) + " -include "
        + shlex.quote(str(header)) + " \"$@\"\n",
        encoding="ascii",
    )
    wrapper.chmod(0o755)
    return {
        "strategy": "forced-include prefix mapping; OpenBLAS source worktree remains unmodified",
        "header": str(header),
        "header_sha256": sha256(header),
        "compiler_wrapper": str(wrapper),
        "compiler_wrapper_sha256": sha256(wrapper),
        "mapped_intrinsic_count": len(intrinsics),
        "mapped_intrinsics": intrinsics,
        "mapped_tuple_type_count": len(tuple_type_mappings),
        "mapped_tuple_types": tuple_type_mappings,
    }


def verify_elf(
    readelf: Path,
    objdump: Path,
    nm: Path,
    elf: Path,
    require_rvv: bool,
    required_symbols: list[str],
) -> dict[str, object]:
    header = output([str(readelf), "-h", str(elf)])
    program = output([str(readelf), "-l", str(elf)])
    if "RISC-V" not in header:
        raise RuntimeError(f"not a RISC-V ELF: {elf}")
    if "INTERP" in program:
        raise RuntimeError(f"ELF is dynamically linked: {elf}")
    entry_match = re.search(r"Entry point address:\s*(0x[0-9a-fA-F]+)", header)
    if entry_match is None:
        raise RuntimeError(f"ELF entry point missing: {elf}")
    entry_point = int(entry_match.group(1), 16)
    if entry_point != 0x200000000:
        raise RuntimeError(
            f"ELF entry does not match RT-Smart USER_LOAD_VADDR: "
            f"{entry_match.group(1)}"
        )
    disassembly = output([str(objdump), "-d", str(elf)])
    disassembly_path = elf.with_suffix(".disassembly.txt")
    disassembly_path.write_text(disassembly + "\n", encoding="utf-8")
    vector_matches = re.findall(r"\b(?:vsetvli|vsetivli|vle32\.v|vse32\.v|vfmacc\.vf)\b", disassembly)
    if require_rvv and not vector_matches:
        raise RuntimeError(f"no RVV instructions found in {elf}")
    symbol_table = output([str(nm), "-C", str(elf)])
    missing_symbols = [
        symbol for symbol in required_symbols
        if not re.search(rf"\b{re.escape(symbol)}$", symbol_table, re.MULTILINE)
    ]
    if missing_symbols:
        raise RuntimeError(f"required symbols missing from {elf}: {', '.join(missing_symbols)}")
    return {
        "elf_header": header,
        "entry_point": entry_match.group(1),
        "static": True,
        "rvv_instruction_matches": len(vector_matches),
        "disassembly": str(disassembly_path),
        "disassembly_sha256": sha256(disassembly_path),
        "required_symbols": required_symbols,
    }


def create_deployment_archive(project: Path, files: list[Path]) -> dict[str, object]:
    archive = project / "build" / "k230_rvv_backend_deployment.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for path in files:
            bundle.add(path, arcname=Path("k230_rvv_backend") / path.relative_to(project))
    return {
        "path": str(archive),
        "sha256": sha256(archive),
        "size_bytes": archive.stat().st_size,
        "members": [str(path.relative_to(project)) for path in files],
        "board_command": "K230_REPS=5 K230_WARMUPS=1 sh board/run_k230_suite.sh",
    }


def refresh_experiment_registry() -> None:
    personal_os = Path(os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    run(
        [
            "python3", str(registry), "refresh", "--workspace-root", str(WORKSPACE),
            "--completed-id", "thesis.k230_rvv_backend",
        ],
        cwd=personal_os,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--openblas", type=Path, default=DEFAULT_OPENBLAS)
    parser.add_argument("--skip-openblas-build", action="store_true")
    args = parser.parse_args()
    sdk, openblas_source = args.sdk.resolve(), args.openblas.resolve()
    tools = toolchain_paths(sdk)
    sdk_revision = output(["git", "-C", str(sdk), "rev-parse", "HEAD"])
    toolchain_version = output([str(tools["gcc"]), "--version"]).splitlines()[0]
    archive = sdk / "toolchain" / "riscv64-unknown-linux-musl-rv64imafdcv-lp64d-20230420.tar.bz2"
    if hashlib.md5(archive.read_bytes()).hexdigest() != "e6c0ce95844595eb0153db8dfaa74bcb":
        raise RuntimeError("K230 RT-Smart toolchain archive MD5 mismatch")

    worktree = THESIS / "third_party" / "OpenBLAS-k230"
    openblas_revision = ensure_openblas_worktree(openblas_source, worktree)
    build_dir = PROJECT / "build"
    elf_dir = build_dir / "elf"
    elf_dir.mkdir(parents=True, exist_ok=True)
    compatibility = generate_rvv_compatibility(worktree, build_dir, tools["gcc"])
    openblas_library = worktree / "libopenblas.a"
    openblas_command = [
        "make", "TARGET=RISCV64_ZVL128B", "DYNAMIC_ARCH=0", "NOFORTRAN=1",
        "NO_LAPACK=1", "ONLY_CBLAS=1", "BUILD_SINGLE=1", "NO_SHARED=1", "USE_THREAD=0",
        "NUM_THREADS=1", f"CC={compatibility['compiler_wrapper']}", "HOSTCC=gcc", f"AR={tools['ar']}",
        f"RANLIB={tools['ranlib']}", "-j8",
    ]
    if not args.skip_openblas_build:
        run(["make", "clean"], cwd=worktree, log=build_dir / "openblas_k230_clean.log")
        run(openblas_command, cwd=worktree, log=build_dir / "openblas_k230_build.log")
    if not openblas_library.is_file():
        raise FileNotFoundError(openblas_library)

    source = PROJECT / "runtime" / "k230_gemm_bench.c"
    linker_script = (
        sdk / "src" / "big" / "rt-smart" / "userapps"
        / "linker_scripts" / "riscv64" / "link.lds"
    )
    if not linker_script.is_file():
        raise FileNotFoundError(f"RT-Smart user linker script missing: {linker_script}")
    common = [
        str(tools["gcc"]), "-std=c11", "-O3", "-mcmodel=medany", "-mabi=lp64d",
        "-n", "-static", "-ffunction-sections", "-fdata-sections",
        "-Wl,--gc-sections", "-Wl,--build-id=none", "-T",
        str(linker_script), str(source), "-lm",
    ]
    builds = [
        {
            "name": "k230_gemm_scalar.elf", "rvv": False,
            "required_symbols": [],
            "command": common[:1] + ["-march=rv64imafdc", "-fno-tree-vectorize", "-DK230_BINARY_ID=\"scalar\""] + common[1:],
        },
        {
            "name": "k230_gemm_rvv.elf", "rvv": True,
            "required_symbols": [],
            "command": common[:1] + ["-march=rv64imafdcv", "-DK230_ENABLE_RVV=1", "-DK230_BINARY_ID=\"rvv\""] + common[1:],
        },
        {
            "name": "k230_gemm_openblas.elf", "rvv": True,
            "required_symbols": ["cblas_sgemm", "sgemm_kernel", "sgemm_oncopy", "sgemm_otcopy"],
            "command": common[:1] + [
                "-march=rv64imafdcv", "-DK230_ENABLE_RVV=1", "-DK230_ENABLE_OPENBLAS=1",
                "-DK230_BINARY_ID=\"openblas\"", "-I", str(worktree),
            ] + common[1:-1] + [str(openblas_library), "-lm"],
        },
    ]
    artifacts: list[dict[str, object]] = []
    for build in builds:
        elf = elf_dir / str(build["name"])
        command = [*build["command"], "-o", str(elf)]
        run(command)
        verification = verify_elf(
            tools["readelf"], tools["objdump"], tools["nm"], elf, bool(build["rvv"]),
            list(build["required_symbols"]),
        )
        artifacts.append({
            "name": build["name"], "path": str(elf), "sha256": sha256(elf),
            "size_bytes": elf.stat().st_size, "build_command": command, **verification,
        })

    manifest = {
        "schema_version": 1,
        "experiment_id": "thesis.k230_rvv_backend",
        "status": "elf_ready_awaiting_board_results",
        "target": "K230 C908 big core / RT-Smart",
        "sdk": {"path": str(sdk), "revision": sdk_revision},
        "toolchain": {
            "version": toolchain_version, "gcc": str(tools["gcc"]),
            "archive": str(archive), "archive_md5": "e6c0ce95844595eb0153db8dfaa74bcb",
        },
        "openblas": {
            "path": str(worktree), "revision": openblas_revision,
            "target": "RISCV64_ZVL128B", "library": str(openblas_library),
            "library_sha256": sha256(openblas_library), "build_command": openblas_command,
            "rvv_intrinsic_compatibility": compatibility,
        },
        "inputs": {
            str(source): sha256(source),
            str(linker_script): sha256(linker_script),
            str(PROJECT / "data/workloads.json"): sha256(PROJECT / "data/workloads.json"),
            str(PROJECT / "data/candidates.json"): sha256(PROJECT / "data/candidates.json"),
        },
        "artifacts": artifacts,
        "board_results": None,
    }
    provenance = PROJECT / "provenance"
    provenance.mkdir(parents=True, exist_ok=True)
    elf_manifest = provenance / "elf_manifest.json"
    elf_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    deployment = create_deployment_archive(
        PROJECT,
        [
            *(Path(row["path"]) for row in artifacts),
            PROJECT / "board" / "run_k230_suite.sh",
            PROJECT / "data" / "workloads.json",
            PROJECT / "data" / "candidates.json",
            elf_manifest,
            PROJECT / "README.md",
        ],
    )
    (provenance / "deployment_manifest.json").write_text(
        json.dumps(deployment, indent=2) + "\n", encoding="utf-8"
    )
    run(["python3", str(SCRIPT_DIR / "render_k230_report.py")], cwd=PROJECT)
    refresh_experiment_registry()
    print(json.dumps({
        "status": manifest["status"],
        "sdk_revision": sdk_revision,
        "toolchain": toolchain_version,
        "elfs": [{"path": row["path"], "sha256": row["sha256"], "rvv_matches": row["rvv_instruction_matches"]} for row in artifacts],
        "deployment": deployment,
    }, indent=2))


if __name__ == "__main__":
    main()
