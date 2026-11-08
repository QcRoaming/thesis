# Chapter 3 Figure QA Report

## Export and backend

- Backend: R 4.3.3 with ggplot2 3.5.2, patchwork 1.3.2, svglite 2.2.1 and
  ragg 1.5.0, used exclusively for drawing, preview exports and pixel QA.
- Width contract: 183 mm double-column figure width.
- Exports: editable SVG, PDF with TrueType text, 300 dpi PNG, and 600 dpi TIFF.
- SVG files contain live `<text>` elements; text was not converted to paths.
- `figure_qa.json` confirms all four PNG previews are nonblank with stable
  dimensions and nonwhite pixel content.
- Visual review checked all four PNG previews after regeneration for clipping,
  overlapping labels, arrow obstruction, and legibility at the intended aspect
  ratio. The first revision exposed two clipped labels in Figure 3-2; both were
  shortened and the complete export bundle was regenerated before acceptance.

## Figure 3-1 quantitative contract

- Source data: `raw/preliminary_aot.csv` and
  `processed/preliminary_best_so_far.csv`.
- Workloads: 8 static f32 shapes.
- Outcome panel n: 64 non-baseline sampled candidates.
- Performance panel n: 6 actually compiled/measured candidates per shape,
  48 measurements total.
- Convergence panel: median and interquartile range across 8 shape-level
  best-so-far curves.
- Seed: 17.
- Metric: candidate GFLOP/s divided by the best sampled GFLOP/s for the same
  shape; this is sample-relative normalization, not normalization to BLIS.
- Baseline definition for the reported speedup field: untiled default MLIR
  lowering for the same shape.
- Statistical inference: none. No p-values or confidence intervals are claimed
  because this is a small preliminary motivation experiment with one seed.

## Concept figures

Figures 3-2 and 3-3 are schema/process diagrams derived from the implemented
artifacts and are not presented as quantitative effect evidence. Figure 3-4 combines
`provenance/anchor_192x256x256.json` with the integrated path-matrix record.
Solid and dashed line styles preserve the hard/soft distinction in grayscale;
no conclusion depends on color alone. Clean source-data extracts for the
quantitative and provenance panels are stored as `source_data_fig3-1.csv` and
`source_data_fig3-4.csv`.

## Final publication-layout check

- Completed against `nwputhesis/build/graduate.pdf` on 20 July 2026 after the
  final Chapter 3 rewrite and figure regeneration.
- Inspected physical PDF pages 49-63 at 180 dpi and at print scale. Chapter 3
  closes on page 61 without an orphan line, the template-generated verso page
  62 has no body content, and Chapter 4 begins on page 63.
- All four figures and their captions were checked in the university template
  for clipping, overlap, grayscale distinction and readable text. Figure 3-4
  is placed at 0.94 times the text width; its labels remain legible within the
  intended 5-7 pt print range.
- No layout defect requiring figure regeneration remains.
