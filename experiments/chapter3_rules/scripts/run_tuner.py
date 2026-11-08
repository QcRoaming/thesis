#!/usr/bin/env python3
"""Run equal-budget random search over generated GEMM candidate spaces."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from jlq.thesis.experiments.chapter3_rules.scripts.rulelib import load_tasks, parse_bool


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=OUTPUT_DIR / "candidates.csv")
    parser.add_argument("--tasks", type=Path, default=DATA_DIR / "gemm_tasks.yaml")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "tuning_trace.csv")
    parser.add_argument("--summary", type=Path, default=OUTPUT_DIR / "tuning_summary.md")
    parser.add_argument("--plot-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--backend", choices=("proxy", "native"), default="proxy")
    parser.add_argument("--budget", type=int, default=16)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--spaces", nargs="+", help="default: every space in the CSV")
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--cxx", default=os.environ.get("CXX"))
    return parser.parse_args()


def load_candidates(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def proxy_score(candidate: dict[str, str], task) -> float:
    tm, tn, tk = (int(candidate[name]) for name in ("tile_m", "tile_n", "tile_k"))
    mr, nr = int(candidate["micro_m"]), int(candidate["micro_n"])
    score = 1.0
    score *= 1.65 if tm % mr == 0 and tn % nr == 0 else 0.72
    score *= 1.28 if parse_bool(candidate["pack_a"]) else 0.88
    score *= 1.35 if parse_bool(candidate["vectorize"]) else 0.76
    score *= math.exp(-0.18 * abs(math.log2(max(tm, 1) / min(task.m, 96))))
    score *= math.exp(-0.14 * abs(math.log2(max(tn, 1) / min(task.n, 128))))
    score *= math.exp(-0.12 * abs(math.log2(max(tk, 1) / min(task.k, 256))))
    if tm > 168 or tk > 256:
        score *= 0.58
    if task.m % tm or task.n % tn or task.k % tk:
        score *= 0.9
    digest = hashlib.sha256(candidate["id"].encode()).digest()
    noise = 0.96 + digest[0] / 255.0 * 0.08
    return score * noise


def choose_cxx(requested: str | None) -> str:
    if requested:
        return requested
    for ancestor in (PROJECT_DIR, *PROJECT_DIR.parents):
        repo_clang = ancestor / "llvm" / "build" / "bin" / "clang++"
        if repo_clang.exists():
            return str(repo_clang)
    compiler = shutil.which("clang++") or shutil.which("c++")
    if compiler is None:
        raise RuntimeError("no C++ compiler found")
    return compiler


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return "unknown"
    for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return "unknown"


def build_native_runner(cxx: str) -> Path:
    output = OUTPUT_DIR / "native_gemm_bench"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            cxx,
            "-O3",
            "-march=native",
            "-std=c++17",
            str(SCRIPT_DIR / "native_gemm_bench.cpp"),
            "-o",
            str(output),
        ],
        check=True,
    )
    return output


def native_score(
    runner: Path, candidate: dict[str, str], task, warmups: int, repeats: int
) -> tuple[float, dict]:
    command = [
        str(runner),
        str(task.m),
        str(task.k),
        str(task.n),
        candidate["tile_m"],
        candidate["tile_n"],
        candidate["tile_k"],
        candidate["micro_m"],
        candidate["micro_n"],
        "1" if parse_bool(candidate["pack_a"]) else "0",
        "1" if parse_bool(candidate["vectorize"]) else "0",
        str(warmups),
        str(repeats),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    output = completed.stdout.strip().splitlines()
    if not output:
        raise RuntimeError(completed.stderr.strip() or "native benchmark produced no output")
    measurement = json.loads(output[-1])
    if completed.returncode or measurement["status"] != "PASS":
        raise RuntimeError(f"native benchmark failed: {measurement}")
    return float(measurement["gflops"]), measurement


def color_for(index: int) -> str:
    palette = ("#006D77", "#D1495B", "#3A7D44", "#7B2CBF", "#E07A1F", "#2563A6")
    return palette[index % len(palette)]


def write_svg(trace_rows: list[dict], task_id: str, output: Path, metric: str) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in trace_rows:
        if row["task_id"] == task_id:
            groups[row["space"]].append(row)
    width, height = 920, 520
    left, right, top, bottom = 78, 24, 54, 66
    plot_w, plot_h = width - left - right, height - top - bottom
    all_scores = [float(row["best_so_far"]) for rows in groups.values() for row in rows]
    max_x = max((len(rows) for rows in groups.values()), default=1)
    min_y, max_y = min(all_scores), max(all_scores)
    if math.isclose(min_y, max_y):
        min_y, max_y = min_y * 0.9, max_y * 1.1 + 1e-9

    svg = ET.Element(
        "svg",
        {"xmlns": "http://www.w3.org/2000/svg", "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}"},
    )
    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "fill": "#ffffff"})
    title = ET.SubElement(svg, "text", {"x": str(left), "y": "30", "font-family": "sans-serif", "font-size": "18", "fill": "#1f2933"})
    title.text = f"Best-so-far: {task_id}"
    for tick in range(6):
        y = top + plot_h * tick / 5
        value = max_y - (max_y - min_y) * tick / 5
        ET.SubElement(svg, "line", {"x1": str(left), "x2": str(left + plot_w), "y1": f"{y:.2f}", "y2": f"{y:.2f}", "stroke": "#d9dee5", "stroke-width": "1"})
        label = ET.SubElement(svg, "text", {"x": str(left - 10), "y": f"{y + 4:.2f}", "text-anchor": "end", "font-family": "sans-serif", "font-size": "11", "fill": "#4b5563"})
        label.text = f"{value:.3g}"
    ET.SubElement(svg, "line", {"x1": str(left), "x2": str(left), "y1": str(top), "y2": str(top + plot_h), "stroke": "#374151"})
    ET.SubElement(svg, "line", {"x1": str(left), "x2": str(left + plot_w), "y1": str(top + plot_h), "y2": str(top + plot_h), "stroke": "#374151"})

    def x_pos(iteration: int) -> float:
        return left + (iteration - 1) / max(max_x - 1, 1) * plot_w

    def y_pos(value: float) -> float:
        return top + (max_y - value) / (max_y - min_y) * plot_h

    legend_y = height - 24
    for index, (space, rows) in enumerate(sorted(groups.items())):
        points = " ".join(f"{x_pos(int(row['iteration'])):.2f},{y_pos(float(row['best_so_far'])):.2f}" for row in rows)
        color = color_for(index)
        ET.SubElement(svg, "polyline", {"points": points, "fill": "none", "stroke": color, "stroke-width": "2.5"})
        legend_x = left + (index % 3) * 270
        legend_row_y = legend_y - (1 - index // 3) * 18
        ET.SubElement(svg, "line", {"x1": str(legend_x), "x2": str(legend_x + 22), "y1": str(legend_row_y), "y2": str(legend_row_y), "stroke": color, "stroke-width": "3"})
        label = ET.SubElement(svg, "text", {"x": str(legend_x + 28), "y": str(legend_row_y + 4), "font-family": "sans-serif", "font-size": "11", "fill": "#1f2933"})
        label.text = space
    x_label = ET.SubElement(svg, "text", {"x": str(left + plot_w / 2), "y": str(top + plot_h + 38), "text-anchor": "middle", "font-family": "sans-serif", "font-size": "13", "fill": "#374151"})
    x_label.text = "Measurement budget"
    y_label = ET.SubElement(svg, "text", {"x": "18", "y": str(top + plot_h / 2), "transform": f"rotate(-90 18 {top + plot_h / 2})", "text-anchor": "middle", "font-family": "sans-serif", "font-size": "13", "fill": "#374151"})
    y_label.text = metric
    output.write_text(ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.budget <= 0 or args.warmups <= 0 or args.repeats <= 0:
        raise SystemExit("budget, warmups, and repeats must be positive")
    candidates = load_candidates(args.candidates)
    tasks = {task.id: task for task in load_tasks(args.tasks)}
    spaces = args.spaces or sorted({row["space"] for row in candidates})
    selected = [row for row in candidates if row["space"] in spaces and parse_bool(row["tuner_eligible"])]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        grouped[(row["task_id"], row["space"])].append(row)
    cxx = choose_cxx(args.cxx) if args.backend == "native" else None
    runner = build_native_runner(cxx) if cxx else None
    metric = "gflops" if args.backend == "native" else "proxy_score"
    trace_rows: list[dict] = []
    for (task_id, space), rows in sorted(grouped.items()):
        task = tasks[task_id]
        rng = random.Random(f"{args.seed}:{task_id}:{space}")
        sampled = rng.sample(rows, min(args.budget, len(rows)))
        best = -math.inf
        for iteration, candidate in enumerate(sampled, 1):
            if runner is None:
                score = proxy_score(candidate, task)
                measurement = {"median_ms": "", "max_abs_diff": "", "status": "PROXY"}
            else:
                score, measurement = native_score(
                    runner, candidate, task, args.warmups, args.repeats
                )
            best = max(best, score)
            trace_rows.append(
                {
                    "task_id": task_id,
                    "space": space,
                    "iteration": iteration,
                    "candidate_id": candidate["id"],
                    "action": candidate["action"],
                    "tile_m": candidate["tile_m"],
                    "tile_n": candidate["tile_n"],
                    "tile_k": candidate["tile_k"],
                    "packing": "ab" if parse_bool(candidate["pack_a"]) else "none",
                    "vectorize": candidate["vectorize"],
                    "metric": metric,
                    "score": f"{score:.8f}",
                    "best_so_far": f"{best:.8f}",
                    "median_ms": measurement["median_ms"],
                    "max_abs_diff": measurement["max_abs_diff"],
                    "status": measurement["status"],
                }
            )

    if not trace_rows:
        raise SystemExit("no tuner-eligible candidates matched the requested spaces")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trace_rows[0]))
        writer.writeheader()
        writer.writerows(trace_rows)

    args.plot_dir.mkdir(parents=True, exist_ok=True)
    for task_id in sorted({row["task_id"] for row in trace_rows}):
        write_svg(
            trace_rows,
            task_id,
            args.plot_dir / f"best_so_far_{task_id}_{args.backend}.svg",
            metric,
        )

    final = {}
    for row in trace_rows:
        final[(row["task_id"], row["space"])] = row["best_so_far"]
    lines = [
        "# Equal-budget Random Search",
        "",
        f"- Backend: `{args.backend}`",
        f"- Metric: `{metric}` (higher is better)",
        f"- Budget per task and space: `{args.budget}`",
        f"- Seed: `{args.seed}`",
        "",
    ]
    if args.backend == "proxy":
        lines.extend(
            [
                "> Proxy scores are deterministic pipeline smoke-test data, not measured performance.",
                "",
            ]
        )
    else:
        compiler_version = subprocess.check_output(
            [cxx, "--version"], text=True
        ).splitlines()[0]
        lines[6:6] = [
            f"- Native host: `{cpu_model()}`",
            f"- Compiler: `{compiler_version}`",
            f"- Warmups/repeats: `{args.warmups}/{args.repeats}`",
        ]
        lines.extend(
            [
                "> Native GFLOP/s measures the bundled tiled C++ proxy kernel. It validates the",
                "> tuning/measurement loop but is not a BLIS or final MLIR AOT performance claim.",
                "",
            ]
        )
    lines.extend(["| Task | Space | Final best |", "|---|---|---:|"])
    for (task_id, space), score in sorted(final.items()):
        lines.append(f"| {task_id} | {space} | {float(score):.4f} |")
    lines.append("")
    args.summary.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(trace_rows)} measurements to {args.output}")
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
