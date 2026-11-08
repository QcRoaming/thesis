#!/usr/bin/env python3
"""Machine-check Chapter 6 figure exports produced by the Python backend."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
FIGURES = PROJECT / "figures"
REPORTS = PROJECT / "reports"


def main() -> None:
    checks = []
    for number in range(1, 12):
        matches = sorted(FIGURES.glob(f"fig6-{number}_*"))
        by_suffix = {path.suffix: path for path in matches}
        missing = [suffix for suffix in (".svg", ".pdf", ".tiff", ".png") if suffix not in by_suffix]
        svg_text = by_suffix[".svg"].read_text(encoding="utf-8") if ".svg" in by_suffix else ""
        tiff_dpi = None
        tiff_pixels = None
        if ".tiff" in by_suffix:
            with Image.open(by_suffix[".tiff"]) as image:
                raw_dpi = image.info.get("dpi")
                tiff_dpi = tuple(float(value) for value in raw_dpi) if raw_dpi else None
                tiff_pixels = image.size
        checks.append({
            "figure": f"6-{number}",
            "missing_formats": missing,
            "svg_has_editable_text": "<text" in svg_text,
            "svg_has_white_background": "#ffffff" in svg_text.lower() or "white" in svg_text.lower(),
            "tiff_dpi": tiff_dpi,
            "tiff_pixels": tiff_pixels,
            "files_nonempty": all(path.stat().st_size > 1000 for path in by_suffix.values()),
        })
    passed = all(
        not row["missing_formats"] and row["svg_has_editable_text"] and row["files_nonempty"]
        and row["tiff_dpi"] and min(row["tiff_dpi"]) >= 599
        for row in checks
    )
    result = {"status": "PASS" if passed else "FAIL", "backend": "Python", "checks": checks}
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "figure_qa.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Chapter 6 Figure QA", "", f"- Status: **{result['status']}**", "- Backend: Python only", "- Primary editable format: SVG", "- Raster QA format: 600 dpi TIFF", "", "| Figure | Formats | Editable text | TIFF dpi | Nonempty |", "|---|---|---|---|---|"]
    for row in checks:
        lines.append(f"| {row['figure']} | {'PASS' if not row['missing_formats'] else 'FAIL'} | {'PASS' if row['svg_has_editable_text'] else 'FAIL'} | {row['tiff_dpi']} | {'PASS' if row['files_nonempty'] else 'FAIL'} |")
    lines.extend(["", "Visual review is recorded separately after opening the PNG previews at manuscript scale.", ""])
    (REPORTS / "figure_qa.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
