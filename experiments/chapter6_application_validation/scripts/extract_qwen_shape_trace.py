#!/usr/bin/env python3
"""Execute the Qwen2 model control flow with shape-only modules and record GEMMs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch
from accelerate import init_empty_weights
from torch import nn
from transformers import Qwen2Config, Qwen2ForCausalLM
import transformers


PROJECT = Path(__file__).resolve().parents[1]
EXTERNAL = PROJECT.parent / "chapter6_external_validation"
CONFIG_PATH = PROJECT / "data" / "experiment_config.json"
MODEL_CONFIG_PATH = PROJECT / "data" / "qwen2_5_0_5b_instruct_config.json"
MODEL_CONFIG_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/raw/main/config.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(name: str) -> tuple[str, bool]:
    suffixes = {
        "q_proj": "q_projection",
        "k_proj": "k_projection",
        "v_proj": "v_projection",
        "o_proj": "attention_output",
        "gate_proj": "gate_projection",
        "up_proj": "up_projection",
        "down_proj": "down_projection",
        "lm_head": "lm_head",
    }
    for suffix, region in suffixes.items():
        if name.endswith(suffix):
            return region, suffix != "lm_head"
    raise ValueError(f"unclassified Linear module: {name}")


class ShapeLinear(nn.Module):
    def __init__(
        self,
        name: str,
        source: nn.Linear,
        records: list[dict[str, Any]],
        scenario: dict[str, Any],
    ) -> None:
        super().__init__()
        self.name = name
        self.in_features = source.in_features
        self.out_features = source.out_features
        self.records = records
        self.scenario = scenario

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        if value.ndim < 2:
            raise ValueError(f"Linear input must have at least two dimensions: {self.name}")
        m = 1
        for extent in value.shape[:-1]:
            m *= int(extent)
        if int(value.shape[-1]) != self.in_features:
            raise ValueError(f"Linear K mismatch for {self.name}")
        match = re.search(r"\.layers\.(\d+)\.", self.name)
        layer = int(match.group(1)) if match else -1
        region, in_scope = classify(self.name)
        self.records.append({
            "scenario_id": self.scenario["id"],
            "batch": self.scenario["batch"],
            "sequence": self.scenario["sequence"],
            "call_index": len(self.records),
            "module_name": self.name,
            "layer": layer,
            "region": region,
            "m": m,
            "k": self.in_features,
            "n": self.out_features,
            "flops": 2 * m * self.in_features * self.out_features,
            "core_projection_scope": in_scope,
        })
        return torch.zeros(
            (*value.shape[:-1], self.out_features),
            dtype=value.dtype,
            device=value.device,
        )


class ShapeEmbedding(nn.Module):
    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.hidden_size = hidden_size

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        return torch.zeros(
            (*token_ids.shape, self.hidden_size),
            dtype=torch.float32,
            device=token_ids.device,
        )


class ShapeRotaryEmbedding(nn.Module):
    def __init__(self, head_dim: int) -> None:
        super().__init__()
        self.head_dim = head_dim

    def forward(
        self, value: torch.Tensor, position_ids: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        shape = (*position_ids.shape, self.head_dim)
        cosine = torch.ones(shape, dtype=value.dtype, device=value.device)
        sine = torch.zeros(shape, dtype=value.dtype, device=value.device)
        return cosine, sine


def replace_linears(
    module: nn.Module,
    records: list[dict[str, Any]],
    scenario: dict[str, Any],
    prefix: str = "",
) -> None:
    for name, child in list(module.named_children()):
        full_name = f"{prefix}.{name}" if prefix else name
        if isinstance(child, nn.Linear):
            setattr(module, name, ShapeLinear(full_name, child, records, scenario))
        else:
            replace_linears(child, records, scenario, full_name)


def execute_scenario(
    model_config: dict[str, Any], scenario: dict[str, Any]
) -> list[dict[str, Any]]:
    config_values = dict(model_config)
    config_values["use_cache"] = False
    config = Qwen2Config.from_dict(config_values)
    with init_empty_weights():
        model = Qwen2ForCausalLM(config)
    records: list[dict[str, Any]] = []
    replace_linears(model, records, scenario)
    model.model.embed_tokens = ShapeEmbedding(config.hidden_size)
    for layer in model.model.layers:
        layer.input_layernorm = nn.Identity()
        layer.post_attention_layernorm = nn.Identity()
    model.model.norm = nn.Identity()
    model.model.rotary_emb = ShapeRotaryEmbedding(
        config.hidden_size // config.num_attention_heads
    )
    input_ids = torch.zeros(
        (int(scenario["batch"]), int(scenario["sequence"])), dtype=torch.long
    )
    with torch.no_grad():
        output = model(input_ids=input_ids, use_cache=False)
    expected = (
        int(scenario["batch"]), int(scenario["sequence"]), config.vocab_size
    )
    if tuple(output.logits.shape) != expected:
        raise RuntimeError(f"unexpected logits shape: {tuple(output.logits.shape)} != {expected}")
    return records


def canonicalize(
    raw_rows: list[dict[str, Any]], workloads: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    lm_head: list[dict[str, Any]] = []
    for row in raw_rows:
        if row["region"] == "lm_head":
            lm_head.append(row)
        else:
            groups[(row["scenario_id"], int(row["layer"]))].append(row)

    scenario_workloads = {
        "decode_batch8": {
            "qkv": "qkv_decode_m8",
            "gate_up": "gate_up_decode_m8",
            "down_projection": "down_decode_m8",
            "attention_output": "out_decode_m8",
        },
        "prefill_batch1_seq32": {
            "qkv": "qkv_prefill_m32",
            "gate_up": "gate_up_prefill_m32",
            "down_projection": "down_prefill_m32",
            "attention_output": "out_prefill_m32",
        },
    }
    canonical: list[dict[str, Any]] = []
    for (scenario_id, layer), rows in sorted(groups.items()):
        by_region = {row["region"]: row for row in rows}
        required = {
            "q_projection", "k_projection", "v_projection", "attention_output",
            "gate_projection", "up_projection", "down_projection",
        }
        if set(by_region) != required:
            raise RuntimeError(
                f"unexpected projection set for {scenario_id} layer {layer}: {sorted(by_region)}"
            )
        combinations = [
            ("qkv", ["q_projection", "k_projection", "v_projection"]),
            ("attention_output", ["attention_output"]),
            ("gate_up", ["gate_projection", "up_projection"]),
            ("down_projection", ["down_projection"]),
        ]
        for region, source_regions in combinations:
            source = [by_region[name] for name in source_regions]
            if len({(row["m"], row["k"]) for row in source}) != 1:
                raise RuntimeError(f"cannot canonicalize {scenario_id} {region}")
            workload_id = scenario_workloads[scenario_id][region]
            m = int(source[0]["m"])
            k = int(source[0]["k"])
            n = sum(int(row["n"]) for row in source)
            workload = workloads[workload_id]
            matched = (m, k, n) == (
                int(workload["m"]), int(workload["k"]), int(workload["n"])
            )
            canonical.append({
                "scenario_id": scenario_id,
                "layer": layer,
                "canonical_region": region,
                "source_regions": "+".join(source_regions),
                "workload_id": workload_id,
                "m": m,
                "k": k,
                "n": n,
                "flops": sum(int(row["flops"]) for row in source),
                "frozen_workload_match": matched,
            })

    aggregates: list[dict[str, Any]] = []
    aggregate_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in canonical:
        aggregate_groups[(row["scenario_id"], row["workload_id"])].append(row)
    for (scenario_id, workload_id), rows in sorted(aggregate_groups.items()):
        first = rows[0]
        aggregates.append({
            "scenario_id": scenario_id,
            "workload_id": workload_id,
            "canonical_region": first["canonical_region"],
            "m": first["m"],
            "k": first["k"],
            "n": first["n"],
            "call_count": len(rows),
            "total_flops": sum(int(row["flops"]) for row in rows),
            "all_frozen_workload_matches": all(row["frozen_workload_match"] for row in rows),
        })
    if len(lm_head) != len({row["scenario_id"] for row in lm_head}):
        raise RuntimeError("expected one lm_head call per scenario")
    return canonical, aggregates


def write_report(summary: dict[str, Any], aggregates: list[dict[str, Any]]) -> None:
    lines = [
        "# Qwen2.5-0.5B GEMM shape-trace coverage",
        "",
        f"- Status: **{summary['status']}**",
        f"- Raw Linear calls: {summary['raw_linear_calls']}",
        f"- Raw Transformer projection calls: {summary['raw_core_projection_calls']}",
        f"- Canonical fused projection calls: {summary['canonical_core_calls']}",
        f"- Core projection call coverage: {summary['core_call_coverage']:.2%}",
        f"- Core projection FLOP coverage: {summary['core_flop_coverage']:.2%}",
        f"- Coverage including lm_head FLOPs: {summary['all_linear_flop_coverage']:.2%}",
        "",
        "| Scenario | Workload | Shape MxKxN | Calls | FLOPs | Covered |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in aggregates:
        lines.append(
            f"| {row['scenario_id']} | {row['workload_id']} | "
            f"{row['m']}x{row['k']}x{row['n']} | {row['call_count']} | "
            f"{row['total_flops']} | {'yes' if row['all_frozen_workload_matches'] else 'no'} |"
        )
    lines.extend([
        "",
        "The trace executes Hugging Face Qwen2 model control flow with stateless shape-preserving modules. It is evidence for operator shapes and multiplicities, not model accuracy or end-to-end latency. Q/K/V and Gate/Up calls are retained in the raw trace and fused only in the canonical view used to map the existing measurement pool.",
        "",
    ])
    path = PROJECT / "reports" / "qwen_trace_coverage.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    experiment = read_json(CONFIG_PATH)
    model_config = read_json(MODEL_CONFIG_PATH)
    workload_rows = read_json(EXTERNAL / "data" / "transformer_workloads.json")["workloads"]
    workloads = {row["id"]: row for row in workload_rows}
    raw_rows: list[dict[str, Any]] = []
    for scenario in experiment["qwen_trace"]["scenarios"]:
        raw_rows.extend(execute_scenario(model_config, scenario))
    canonical, aggregates = canonicalize(raw_rows, workloads)

    raw_core = [row for row in raw_rows if row["core_projection_scope"]]
    covered = [row for row in canonical if row["frozen_workload_match"]]
    core_flops = sum(int(row["flops"]) for row in canonical)
    covered_flops = sum(int(row["flops"]) for row in covered)
    raw_total_flops = sum(int(row["flops"]) for row in raw_rows)
    summary = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.qwen_trace",
        "status": "PASS" if len(covered) == len(canonical) else "FAIL",
        "model": experiment["qwen_trace"]["model"],
        "model_config_url": MODEL_CONFIG_URL,
        "model_config_sha256": sha256(MODEL_CONFIG_PATH),
        "scenarios": len(experiment["qwen_trace"]["scenarios"]),
        "raw_linear_calls": len(raw_rows),
        "raw_core_projection_calls": len(raw_core),
        "canonical_core_calls": len(canonical),
        "covered_canonical_calls": len(covered),
        "core_call_coverage": len(covered) / len(canonical),
        "core_flop_coverage": covered_flops / core_flops,
        "all_linear_flop_coverage": covered_flops / raw_total_flops,
        "lm_head_calls": sum(row["region"] == "lm_head" for row in raw_rows),
        "canonical_workload_rows": len(aggregates),
        "transformer_layers": int(model_config["num_hidden_layers"]),
        "provenance": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "script_sha256": sha256(Path(__file__)),
        },
        "claim_boundary": experiment["claim_boundary"],
    }
    if summary["status"] != "PASS":
        raise RuntimeError("the frozen workload pool does not cover the canonical core trace")
    write_csv(PROJECT / "raw" / "qwen_linear_trace.csv", raw_rows)
    write_csv(PROJECT / "processed" / "qwen_canonical_trace.csv", canonical)
    write_csv(PROJECT / "processed" / "qwen_trace_workloads.csv", aggregates)
    write_json(PROJECT / "processed" / "qwen_trace_summary.json", summary)
    write_report(summary, aggregates)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
