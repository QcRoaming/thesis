#!/usr/bin/env python3
"""Validate chapter 3 Facts, Contracts, Rules, evidence, and review records."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
THESIS_DIR = PROJECT_DIR.parents[1]
DEFAULT_BLIS_ROOT = THESIS_DIR / "blis" / "blis"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def matches_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }.get(expected, True)


def validate_record(record: dict, schema: dict, label: str) -> list[str]:
    errors = []
    for field in schema.get("required", []):
        if field not in record:
            errors.append(f"{label}: missing required field '{field}'")
    for field, definition in schema.get("properties", {}).items():
        if field not in record:
            continue
        if "type" in definition and not matches_type(record[field], definition["type"]):
            errors.append(f"{label}.{field}: expected {definition['type']}")
        if "enum" in definition and record[field] not in definition["enum"]:
            errors.append(f"{label}.{field}: value not in enum")
    if schema.get("additionalProperties") is False:
        unexpected = set(record) - set(schema.get("properties", {}))
        if unexpected:
            errors.append(f"{label}: unexpected fields {sorted(unexpected)}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    parser.add_argument("--blis-root", type=Path, default=DEFAULT_BLIS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    blis_root = args.blis_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    facts = load_json(project / "data" / "facts.json")["facts"]
    fact_schema = load_json(project / "schemas" / "fact.schema.json")
    fact_ids = [record["fact_id"] for record in facts]
    if len(fact_ids) != len(set(fact_ids)):
        errors.append("Fact IDs are not unique")
    for index, record in enumerate(facts):
        errors.extend(validate_record(record, fact_schema, f"fact[{index}]"))
        source = blis_root / record["source_file"]
        if not source.is_file():
            errors.append(f"{record['fact_id']}: missing source file {source}")
            continue
        line_count = len(source.read_text(encoding="utf-8", errors="replace").splitlines())
        if not 1 <= record["source_line"] <= line_count:
            errors.append(f"{record['fact_id']}: invalid source line")

    contracts = load_yaml(project / "data" / "microkernel_contracts.yaml")["contracts"]
    contract_schema = load_json(project / "schemas" / "contract.schema.json")
    if len(contracts) < 2:
        errors.append("At least two real Contracts are required")
    for index, contract in enumerate(contracts):
        errors.extend(validate_record(contract, contract_schema, f"contract[{index}]"))
        if (contract["mr"], contract["nr"]) != (
            contract["register_tile"]["m"],
            contract["register_tile"]["n"],
        ):
            errors.append(f"{contract['kernel_id']}: duplicated MR/NR fields disagree")
        if not contract["k_constraint"]["remainder_supported"]:
            warnings.append(f"{contract['kernel_id']}: K remainder support is disabled")

    rules_doc = load_yaml(project / "data" / "expert_rules.yaml")
    rules = rules_doc["rules"]
    rule_schema = load_json(project / "schemas" / "rule.schema.json")
    categories = set()
    known_facts = set(fact_ids)
    for index, rule in enumerate(rules):
        errors.extend(validate_record(rule, rule_schema, f"rule[{index}]"))
        categories.add(rule["category"])
        missing_facts = set(rule["source_fact_ids"]) - known_facts
        if missing_facts:
            errors.append(f"{rule['rule_id']}: unknown source facts {sorted(missing_facts)}")
    required_categories = {
        "register_blocking",
        "cache_blocking",
        "packing",
        "vectorization",
        "tail_and_fallback",
    }
    if categories != required_categories:
        errors.append(f"Rule categories differ from required set: {sorted(categories)}")

    with (project / "verification" / "manual_verification.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        verification = list(csv.DictReader(handle))
    if len(verification) < 16:
        errors.append("Manual verification set has fewer than 16 source-backed cases")
    machine_failures = [row for row in verification if row["machine_check"] != "pass"]
    if machine_failures:
        errors.append(f"{len(machine_failures)} verification cases failed machine checks")
    pending_human = sum(row["human_status"] != "verified" for row in verification)
    if pending_human:
        warnings.append(f"{pending_human} verification cases still require human signoff")

    with (project / "data" / "ambiguities.csv").open(encoding="utf-8", newline="") as handle:
        ambiguities = list(csv.DictReader(handle))
    if not ambiguities:
        errors.append("Ambiguity register is empty")

    report = {
        "status": "pass" if not errors else "fail",
        "fact_count": len(facts),
        "contract_count": len(contracts),
        "rule_count": len(rules),
        "fact_fields": dict(Counter(record["normalized_field"] for record in facts)),
        "evidence_levels": dict(Counter(record["evidence_level"] for record in facts)),
        "verification_cases": len(verification),
        "pending_human_signoff": pending_human,
        "ambiguity_count": len(ambiguities),
        "errors": errors,
        "warnings": warnings,
    }
    output_dir = project / "verification"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Chapter 3 Artifact Validation",
        "",
        f"- Status: **{report['status'].upper()}**",
        f"- Atomic Facts: {len(facts)}",
        f"- Contracts: {len(contracts)}",
        f"- Rules: {len(rules)}",
        f"- Verification cases: {len(verification)}",
        f"- Pending human signoff: {pending_human}",
        f"- Open ambiguities: {len(ambiguities)}",
        "",
        "## Warnings",
        "",
        *(f"- {warning}" for warning in warnings),
        "",
        "## Errors",
        "",
        *(f"- {error}" for error in errors),
        "",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
