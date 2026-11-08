"""Shared schema and compatibility logic for the chapter 3 MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ACTIONS = ("direct", "adapt", "fallback", "reject")


@dataclass(frozen=True)
class GemmTask:
    id: str
    operation: str
    dtype: str
    target: str
    features: frozenset[str]
    m: int
    k: int
    n: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GemmTask":
        shape = data["shape"]
        task = cls(
            id=data["id"],
            operation=data["operation"],
            dtype=data["dtype"],
            target=data["target"]["machine"],
            features=frozenset(data["target"].get("features", [])),
            m=int(shape["m"]),
            k=int(shape["k"]),
            n=int(shape["n"]),
        )
        if min(task.m, task.k, task.n) <= 0:
            raise ValueError(f"task {task.id} has a non-positive shape")
        return task


@dataclass(frozen=True)
class MicroKernelDesc:
    id: str
    operation: str
    dtype: str
    machine: str
    architecture: str
    required_features: frozenset[str]
    kernel: str
    mr: int
    nr: int
    mc: int
    kc: int
    nc: int
    packing_required: bool
    vector_lanes: int
    tail_policy: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MicroKernelDesc":
        return cls(
            id=data["id"],
            operation=data["operation"],
            dtype=data["dtype"],
            machine=data["target"]["machine"],
            architecture=data["target"]["architecture"],
            required_features=frozenset(data["target"].get("required_features", [])),
            kernel=data["kernel"],
            mr=int(data["register_tile"]["m"]),
            nr=int(data["register_tile"]["n"]),
            mc=int(data["cache_blocking"]["mc"]),
            kc=int(data["cache_blocking"]["kc"]),
            nc=int(data["cache_blocking"]["nc"]),
            packing_required=bool(data["packing"]["required_for_direct"]),
            vector_lanes=int(data["vectorization"]["lanes"]),
            tail_policy=data["tail_policy"],
        )


@dataclass(frozen=True)
class Candidate:
    id: str
    task_id: str
    space: str
    tile_m: int
    tile_n: int
    tile_k: int
    micro_m: int
    micro_n: int
    pack_a: bool
    pack_b: bool
    vectorize: bool
    kernel: str
    action: str
    reason: str
    tuner_eligible: bool

    def to_row(self) -> dict[str, Any]:
        row = self.__dict__.copy()
        for name in ("pack_a", "pack_b", "vectorize", "tuner_eligible"):
            row[name] = str(row[name]).lower()
        return row


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"expected a YAML mapping in {path}")
    return document


def load_tasks(path: Path) -> list[GemmTask]:
    document = load_yaml(path)
    return [GemmTask.from_dict(item) for item in document.get("tasks", [])]


def load_contracts(path: Path) -> list[MicroKernelDesc]:
    document = load_yaml(path)
    return [MicroKernelDesc.from_dict(item) for item in document.get("contracts", [])]


def compatible_contract(
    task: GemmTask, contracts: list[MicroKernelDesc]
) -> MicroKernelDesc:
    for contract in contracts:
        if (
            contract.operation == task.operation
            and contract.dtype == task.dtype
            and contract.machine == task.target
            and contract.required_features <= task.features
        ):
            return contract
    raise ValueError(f"no microkernel contract matches task {task.id}")


def assess_candidate(
    task: GemmTask,
    contract: MicroKernelDesc,
    *,
    tile_m: int,
    tile_n: int,
    tile_k: int,
    pack_a: bool,
    pack_b: bool,
    vectorize: bool,
    enforce_cache: bool = True,
    packing_adapter: bool = True,
) -> tuple[str, str]:
    if min(tile_m, tile_n, tile_k) <= 0:
        return "reject", "tile sizes must be positive"
    if contract.operation != task.operation or contract.dtype != task.dtype:
        return "reject", "operation or dtype does not match the contract"
    if contract.machine != task.target or not contract.required_features <= task.features:
        return "reject", "target features do not satisfy the contract"
    effective_m = min(tile_m, task.m)
    effective_n = min(tile_n, task.n)
    effective_k = min(tile_k, task.k)
    if enforce_cache and (
        effective_m > contract.mc
        or effective_n > contract.nc
        or effective_k > contract.kc
    ):
        return "reject", "outer tile exceeds BLIS cache-blocking bound"
    if vectorize and tile_n % contract.vector_lanes != 0:
        return "reject", "N tile is not a whole SIMD-vector multiple"
    if tile_m % contract.mr != 0 or tile_n % contract.nr != 0:
        return "fallback", "tile does not contain an integral MRxNR microtile"
    if contract.packing_required and not (pack_a and pack_b):
        if packing_adapter:
            return "adapt", "insert A/B packing before direct kernel use"
        return "fallback", "packing rule is disabled"
    tails = []
    if tile_m < task.m and task.m % tile_m:
        tails.append("M")
    if tile_n < task.n and task.n % tile_n:
        tails.append("N")
    if tile_k < task.k and task.k % tile_k:
        tails.append("K")
    if task.m % contract.mr or task.n % contract.nr:
        tails.append("microkernel")
    if tails:
        return "adapt", "tail handling required for " + "/".join(dict.fromkeys(tails))
    return "direct", "candidate satisfies the microkernel contract"


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")
