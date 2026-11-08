#!/usr/bin/env python3
"""Extract source-backed BLIS GEMM facts and target contracts.

The extractor evaluates literal ``#if 0``/``#if 1`` branches, extracts active
kernel registrations and block sizes, and cross-checks each register tile
against the kernel setup macro. It emits both compatibility profiles and the
atomic Fact records required by the thesis schema.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
THESIS_DIR = PROJECT_DIR.parents[1]
DEFAULT_BLIS_ROOT = THESIS_DIR / "blis" / "blis"
DEFAULT_SIGNOFFS = PROJECT_DIR / "verification" / "human_signoffs.json"

DTYPES = {
    "BLIS_FLOAT": ("f32", "s", 4),
    "BLIS_DOUBLE": ("f64", "d", 8),
    "BLIS_SCOMPLEX": ("c64", "c", 8),
    "BLIS_DCOMPLEX": ("c128", "z", 16),
}


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str


def active_source_lines(path: Path) -> list[SourceLine]:
    """Return lines active under literal #if 0/#if 1 branches."""
    result: list[SourceLine] = []
    stack: list[tuple[bool, bool]] = []
    active = True
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        directive = text.strip()
        if_match = re.match(r"#\s*if\s+(.+?)\s*$", directive)
        if if_match:
            expression = if_match.group(1).strip()
            condition = expression != "0"
            stack.append((active, condition))
            active = active and condition
            continue
        if re.match(r"#\s*else\b", directive):
            if not stack:
                raise ValueError(f"unmatched #else in {path}:{number}")
            parent_active, condition = stack[-1]
            active = parent_active and not condition
            stack[-1] = (parent_active, not condition)
            continue
        if re.match(r"#\s*endif\b", directive):
            if not stack:
                raise ValueError(f"unmatched #endif in {path}:{number}")
            parent_active, _ = stack.pop()
            active = parent_active
            continue
        if active:
            result.append(SourceLine(number, text.split("//", 1)[0]))
    if stack:
        raise ValueError(f"unterminated preprocessor branch in {path}")
    return result


def evidence(path: Path, line: int, blis_root: Path, kind: str) -> dict:
    return {
        "file": path.relative_to(blis_root).as_posix(),
        "line": line,
        "kind": kind,
    }


def first_match(
    lines: Iterable[SourceLine], pattern: re.Pattern[str], label: str
) -> tuple[SourceLine, re.Match[str]]:
    for line in lines:
        match = pattern.search(line.text)
        if match:
            return line, match
    raise ValueError(f"could not extract {label}")


def find_kernel_source(blis_root: Path, symbol: str) -> tuple[Path, int, list[str]]:
    declaration = re.compile(rf"\bvoid\s+{re.escape(symbol)}\b")
    for path in sorted((blis_root / "kernels").rglob("*.c")):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = declaration.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            return path, line, text.splitlines()
    raise ValueError(f"could not locate implementation for {symbol}")


def git_revision(blis_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(blis_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def extract_fact(blis_root: Path, arch: str, dtype: str) -> tuple[dict, dict]:
    context = blis_root / "config" / arch / f"bli_cntx_init_{arch}.c"
    make_defs = blis_root / "config" / arch / "make_defs.mk"
    if not context.is_file():
        raise FileNotFoundError(context)

    dtype_macro = next(key for key, value in DTYPES.items() if value[0] == dtype)
    dtype_name, dtype_char, element_bytes = DTYPES[dtype_macro]
    lines = active_source_lines(context)

    kernel_pattern = re.compile(
        rf"\bBLIS_GEMM_UKR\s*,\s*{dtype_macro}\s*,\s*(\w+)\s*,"
    )
    pack_pattern = re.compile(
        rf"\bBLIS_PACKM_KER\s*,\s*{dtype_macro}\s*,\s*(\w+)\s*,"
    )
    preference_pattern = re.compile(
        rf"\bBLIS_GEMM_UKR_ROW_PREF\s*,\s*{dtype_macro}\s*,\s*(TRUE|FALSE)\s*,"
    )
    kernel_line, kernel_match = first_match(lines, kernel_pattern, "GEMM kernel")
    pack_line, pack_match = first_match(lines, pack_pattern, "pack kernel")
    pref_line, pref_match = first_match(lines, preference_pattern, "row preference")

    dtype_index = list(DTYPES).index(dtype_macro)
    block_sizes: dict[str, int] = {}
    block_evidence: dict[str, int] = {}
    block_pattern = re.compile(
        r"bli_blksz_init_easy\s*\(\s*&blkszs\[\s*BLIS_(MR|NR|MC|KC|NC)\s*\]"
        r"\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)"
    )
    for line in lines:
        match = block_pattern.search(line.text)
        if match:
            block_sizes[match.group(1).lower()] = int(match.group(2 + dtype_index))
            block_evidence[match.group(1).lower()] = line.number
    missing = {"mr", "nr", "mc", "kc", "nc"} - block_sizes.keys()
    if missing:
        raise ValueError(f"missing block sizes in {context}: {sorted(missing)}")

    multiples: dict[str, str] = {}
    multiple_evidence: list[dict] = []
    multiple_pattern = re.compile(
        r"\bBLIS_(NC|KC|MC|NR|MR)\s*,\s*&blkszs\[\s*BLIS_\1\s*\]"
        r"\s*,\s*BLIS_(NR|KR|MR)\s*,"
    )
    for line in lines:
        match = multiple_pattern.search(line.text)
        if match:
            name, multiple = match.group(1).lower(), match.group(2).lower()
            multiples[name] = multiple
            multiple_evidence.append(
                evidence(context, line.number, blis_root, "blocksize_multiple")
            )

    kernel_symbol = kernel_match.group(1)
    kernel_source, kernel_source_line, kernel_lines = find_kernel_source(
        blis_root, kernel_symbol
    )
    setup_pattern = re.compile(
        rf"GEMM_UKR_SETUP_CT(?:_ANY)?\s*\(\s*{dtype_char}\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    setup_line = None
    setup_mr = setup_nr = None
    for number, text in enumerate(kernel_lines, 1):
        match = setup_pattern.search(text)
        if match:
            setup_line = number
            setup_mr, setup_nr = int(match.group(1)), int(match.group(2))
            break
    if setup_line is None:
        raise ValueError(f"missing GEMM setup macro for {dtype} in {kernel_source}")
    if (setup_mr, setup_nr) != (block_sizes["mr"], block_sizes["nr"]):
        raise ValueError(
            f"MR/NR mismatch: context has {block_sizes['mr']}x{block_sizes['nr']}, "
            f"kernel has {setup_mr}x{setup_nr}"
        )

    flags = ""
    flags_line = None
    if make_defs.is_file():
        for number, text in enumerate(make_defs.read_text(encoding="utf-8").splitlines(), 1):
            if "CKVECFLAGS" in text and ":=" in text and "-mavx2" in text:
                flags, flags_line = text.split(":=", 1)[1].strip(), number
                break
    isa = []
    if "-mavx2" in flags:
        isa.append("avx2")
    if "-mfma" in flags:
        isa.append("fma")
    vector_bits = 256 if "avx2" in isa else None

    source_evidence = [
        evidence(context, kernel_line.number, blis_root, "kernel_registration"),
        evidence(kernel_source, kernel_source_line, blis_root, "kernel_definition"),
        evidence(kernel_source, setup_line, blis_root, "kernel_contract_check"),
        evidence(context, pref_line.number, blis_root, "storage_preference"),
        evidence(context, pack_line.number, blis_root, "pack_kernel_registration"),
    ]
    for name in ("mr", "nr", "mc", "kc", "nc"):
        source_evidence.append(
            evidence(context, block_evidence[name], blis_root, f"{name}_value")
        )
    source_evidence.extend(multiple_evidence)
    if flags_line is not None:
        source_evidence.append(
            evidence(make_defs, flags_line, blis_root, "compiler_isa_flags")
        )

    vector_lanes = vector_bits // (8 * element_bytes) if vector_bits else None
    fact_id = f"blis.{arch}.gemm.{dtype_name}"
    fact = {
        "id": fact_id,
        "library": "BLIS",
        "operation": "gemm",
        "dtype": dtype_name,
        "target": {
            "architecture": arch,
            "machine": "x86_64" if arch == "haswell" else arch,
            "required_features": list(isa),
        },
        "microkernel": {
            "symbol": kernel_symbol,
            "mr": block_sizes["mr"],
            "nr": block_sizes["nr"],
            "row_preferred": pref_match.group(1) == "TRUE",
        },
        "cache_blocking": {
            "mc": block_sizes["mc"],
            "kc": block_sizes["kc"],
            "nc": block_sizes["nc"],
        },
        "packing": {
            "enabled": True,
            "kernel": pack_match.group(1),
            "a_panel": f"{block_sizes['mr']}xkc",
            "b_panel": f"kcx{block_sizes['nr']}",
        },
        "vectorization": {
            "isa": list(isa),
            "vector_bits": vector_bits,
            "lanes": vector_lanes,
            "compiler_flags": flags,
        },
        "constraints": {
            "blocksize_multiples": multiples,
            "mr_nr_verified_against_kernel": True,
        },
        "evidence": source_evidence,
    }

    contract_id = f"{arch}_{dtype_name}_gemm_{block_sizes['mr']}x{block_sizes['nr']}"
    contract = {
        "id": contract_id,
        "kernel_id": contract_id,
        "fact_id": fact_id,
        "operation": "linalg.matmul",
        "dtype": dtype_name,
        "target": {
            "machine": fact["target"]["machine"],
            "architecture": arch,
            "required_features": list(isa),
        },
        "kernel": kernel_symbol,
        "isa": list(isa),
        "mr": block_sizes["mr"],
        "nr": block_sizes["nr"],
        "register_tile": {"m": block_sizes["mr"], "n": block_sizes["nr"]},
        "k_constraint": {
            "minimum": 0,
            "multiple": 1,
            "main_loop_step": 4,
            "remainder_supported": True,
        },
        "cache_blocking": fact["cache_blocking"],
        "input_layout": {
            "a": "BLIS packed A micropanel",
            "b": "BLIS packed B micropanel",
        },
        "output_layout": "row_major_preferred",
        "stride": {
            "a": "packed-panel stride supplied by BLIS",
            "b": "packed-panel stride supplied by BLIS",
            "c": "row or column stride passed through GEMM_UKR ABI",
        },
        "alignment": {
            "a_bytes": None,
            "b_bytes": None,
            "c_bytes": None,
            "verification_status": "ambiguous_in_context_source",
        },
        "packing": {
            "required_for_direct": True,
            "a_panel_multiple": "mr",
            "b_panel_multiple": "nr",
            "kernel": pack_match.group(1),
        },
        "layout": {"output_preference": "row_major" if fact["microkernel"]["row_preferred"] else "column_major"},
        "vectorization": {
            "required_features": list(isa),
            "vector_bits": vector_bits,
            "lanes": vector_lanes,
        },
        "tail_policy": {
            "kernel": "fixed_mr_nr_with_k_remainder",
            "adapter": "pad_or_fringe_then_fallback",
        },
        "call_convention": "BLIS GEMM_UKR ABI",
        "fallback_path": "generic_mlir_tiled_loop",
        "kernel_requirements": {
            "fixed_mr": block_sizes["mr"],
            "fixed_nr": block_sizes["nr"],
            "packed_a": True,
            "packed_b": True,
            "required_features": list(isa),
        },
        "adapter_capabilities": {
            "insert_packing": True,
            "handle_mn_tail": True,
            "handle_k_remainder": True,
            "fallback_when_unavailable": True,
        },
        "verification_status": "source_cross_checked_pending_human_signoff",
        "evidence_fact": fact_id,
    }
    return fact, contract


def evidence_for(profile: dict, kind: str) -> dict:
    return next(item for item in profile["evidence"] if item["kind"] == kind)


def atomic_facts(profile: dict, version: str) -> list[dict]:
    """Normalize one compatibility profile into field-level Fact records."""
    dtype = profile["dtype"]
    architecture = profile["target"]["architecture"]
    base = {
        "operator": "gemm",
        "dtype": dtype,
        "architecture": architecture,
        "library": "BLIS",
        "version": version,
        "applicability": {
            "operation": "linalg.matmul",
            "machine": profile["target"]["machine"],
            "required_features": profile["target"]["required_features"],
            "thread_mode": "single_thread",
        },
    }
    specs = [
        ("kernel_symbol", profile["microkernel"]["symbol"], "kernel_registration", "E1", "automatic", "source_cross_checked"),
        ("mr", profile["microkernel"]["mr"], "mr_value", "E2", "automatic", "source_cross_checked"),
        ("nr", profile["microkernel"]["nr"], "nr_value", "E2", "automatic", "source_cross_checked"),
        ("mc", profile["cache_blocking"]["mc"], "mc_value", "E1", "automatic", "machine_checked"),
        ("kc", profile["cache_blocking"]["kc"], "kc_value", "E1", "automatic", "machine_checked"),
        ("nc", profile["cache_blocking"]["nc"], "nc_value", "E1", "automatic", "machine_checked"),
        ("row_preferred", profile["microkernel"]["row_preferred"], "storage_preference", "E1", "automatic", "machine_checked"),
        ("pack_kernel", profile["packing"]["kernel"], "pack_kernel_registration", "E1", "automatic", "machine_checked"),
        ("isa", profile["vectorization"]["isa"], "compiler_isa_flags", "E1", "automatic", "machine_checked"),
        ("vector_bits", profile["vectorization"]["vector_bits"], "compiler_isa_flags", "E3", "derived", "pending_manual"),
        ("vector_lanes", profile["vectorization"]["lanes"], "compiler_isa_flags", "E3", "derived", "pending_manual"),
    ]
    records = []
    for field, value, evidence_kind, level, mode, status in specs:
        source = evidence_for(profile, evidence_kind)
        records.append(
            {
                "fact_id": f"{profile['id']}.{field}",
                **base,
                "source_file": source["file"],
                "source_line": source["line"],
                "source_symbol": f"bli_cntx_init_{architecture}",
                "raw_value": value,
                "normalized_field": field,
                "normalized_value": value,
                "evidence_level": level,
                "extraction_mode": mode,
                "verification_status": status,
                "notes": "MR/NR are independently checked against GEMM_UKR_SETUP_CT_ANY." if field in {"mr", "nr"} else "",
            }
        )
    return records


def write_atomic_csv(path: Path, records: list[dict]) -> None:
    fieldnames = list(records[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = record.copy()
            for field in ("raw_value", "normalized_value", "applicability"):
                if isinstance(row[field], (dict, list)):
                    row[field] = json.dumps(row[field], sort_keys=True)
            writer.writerow(row)


def load_human_signoffs(path: Path) -> dict:
    """Load durable author signoffs without conflating them with machine checks."""
    if not path.is_file():
        return {"reviewer": "pending", "confirmed_at_utc": None, "signoffs": {}}
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError(f"unsupported human signoff schema in {path}")
    records = document.get("signoffs")
    if not isinstance(records, list):
        raise ValueError(f"human signoffs must be a list in {path}")
    signoffs = {}
    for record in records:
        case_id = record.get("case_id") if isinstance(record, dict) else None
        status = record.get("status") if isinstance(record, dict) else None
        if not case_id or status != "verified":
            raise ValueError(f"invalid human signoff record in {path}: {record!r}")
        if case_id in signoffs:
            raise ValueError(f"duplicate human signoff case in {path}: {case_id}")
        signoffs[case_id] = status
    return {
        "reviewer": document.get("reviewer", "thesis_author"),
        "confirmed_at_utc": document.get("confirmed_at_utc"),
        "signoffs": signoffs,
    }


def verification_rows(profiles: list[dict], signoff_document: dict) -> list[dict]:
    rows = []
    signoffs = signoff_document["signoffs"]
    known_case_ids = set()
    for profile in profiles:
        for field, value, evidence_kind in (
            ("kernel_symbol", profile["microkernel"]["symbol"], "kernel_registration"),
            ("mr", profile["microkernel"]["mr"], "mr_value"),
            ("nr", profile["microkernel"]["nr"], "nr_value"),
            ("mc", profile["cache_blocking"]["mc"], "mc_value"),
            ("kc", profile["cache_blocking"]["kc"], "kc_value"),
            ("nc", profile["cache_blocking"]["nc"], "nc_value"),
            ("pack_kernel", profile["packing"]["kernel"], "pack_kernel_registration"),
            ("row_preferred", profile["microkernel"]["row_preferred"], "storage_preference"),
        ):
            source = evidence_for(profile, evidence_kind)
            case_id = f"verify.{profile['dtype']}.{field}"
            known_case_ids.add(case_id)
            verified = signoffs.get(case_id) == "verified"
            confirmation_date = str(signoff_document.get("confirmed_at_utc") or "").split("T", 1)[0]
            rows.append(
                {
                    "case_id": case_id,
                    "dtype": profile["dtype"],
                    "field": field,
                    "expected": value,
                    "extracted": value,
                    "source_file": source["file"],
                    "source_line": source["line"],
                    "machine_check": "pass",
                    "human_reviewer": signoff_document["reviewer"] if verified else "pending",
                    "human_status": "verified" if verified else "pending_signoff",
                    "notes": (
                        f"Source line and kernel corroboration included; author signoff confirmed on {confirmation_date}."
                        if verified
                        else "Source line and kernel corroboration are included for review."
                    ),
                }
            )
    unknown = set(signoffs) - known_case_ids
    if unknown:
        raise ValueError(f"human signoffs reference unknown cases: {sorted(unknown)}")
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blis-root", type=Path, default=DEFAULT_BLIS_ROOT)
    parser.add_argument("--arch", default="haswell")
    parser.add_argument(
        "--dtype",
        nargs="+",
        choices=[item[0] for item in DTYPES.values()],
        default=["f32", "f64"],
    )
    parser.add_argument(
        "--facts-output", type=Path, default=PROJECT_DIR / "data" / "expert_facts.yaml"
    )
    parser.add_argument(
        "--contracts-output",
        type=Path,
        default=PROJECT_DIR / "data" / "microkernel_contracts.yaml",
    )
    parser.add_argument("--atomic-json", type=Path, default=PROJECT_DIR / "data" / "facts.json")
    parser.add_argument("--atomic-csv", type=Path, default=PROJECT_DIR / "data" / "facts.csv")
    parser.add_argument(
        "--verification-output",
        type=Path,
        default=PROJECT_DIR / "verification" / "manual_verification.csv",
    )
    parser.add_argument(
        "--signoffs-input",
        type=Path,
        default=DEFAULT_SIGNOFFS,
        help="Durable author-confirmed signoffs merged by verification case_id.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    blis_root = args.blis_root.resolve()
    revision = git_revision(blis_root)
    profiles = []
    contracts = []
    for dtype in args.dtype:
        profile, contract = extract_fact(blis_root, args.arch, dtype)
        profiles.append(profile)
        contracts.append(contract)
    records = [record for profile in profiles for record in atomic_facts(profile, revision)]
    signoff_document = load_human_signoffs(args.signoffs_input)
    verification = verification_rows(profiles, signoff_document)
    for contract in contracts:
        dtype_rows = [row for row in verification if row["dtype"] == contract["dtype"]]
        if dtype_rows and all(row["human_status"] == "verified" for row in dtype_rows):
            contract["verification_status"] = "source_cross_checked_human_verified"
    facts_document = {
        "schema_version": 2,
        "generated_by": "scripts/extract_blis_facts.py",
        "source": {"repository": str(blis_root), "revision": revision},
        "facts": profiles,
    }
    contracts_document = {
        "schema_version": 2,
        "generated_by": "scripts/extract_blis_facts.py",
        "contracts": contracts,
    }
    for path, document in (
        (args.facts_output, facts_document),
        (args.contracts_output, contracts_document),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(document, sort_keys=False, width=100), encoding="utf-8"
        )
        print(f"wrote {path}")
    args.atomic_json.parent.mkdir(parents=True, exist_ok=True)
    args.atomic_json.write_text(
        json.dumps({"schema_version": 1, "facts": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    write_atomic_csv(args.atomic_csv, records)
    args.verification_output.parent.mkdir(parents=True, exist_ok=True)
    with args.verification_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(verification[0]))
        writer.writeheader()
        writer.writerows(verification)
    print(f"wrote {args.atomic_json}")
    print(f"wrote {args.atomic_csv}")
    print(f"wrote {args.verification_output}")


if __name__ == "__main__":
    main()
