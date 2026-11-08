# Chapter 3 Figure Contracts

All figures use the R/ggplot2 backend exclusively and are exported as editable
SVG/PDF plus high-resolution raster previews.

## Figure 3-1: preliminary generic-space evidence

- Core conclusion: the bounded generic space contains policy-incompatible
  candidates, while every successfully compiled candidate remains on the
  generic fallback path and the sampled candidates show substantial
  performance dispersion.
- Evidence chain: panel a reports observed candidate outcomes; panel b reports
  per-shape normalized performance for every measured candidate; panel c
  reports best-so-far convergence across eight shapes.
- Archetype: quantitative grid with panel b as the visual emphasis.
- Export: 183 mm wide, editable SVG/PDF, 600 dpi TIFF, 300 dpi PNG.
- Review risks: 64 is the number of non-baseline records, comprising 48 measured
  candidates and 16 pre-check rejects; only six candidates are measured per
  shape; the single-seed result is descriptive and carries no inferential
  claim; replacement is zero because the frozen adapter was not implemented.

## Figure 3-2: hard/soft knowledge boundary

- Core conclusion: compatibility knowledge stays in the execution-validated
  BLIS Contracts, while OpenBLAS remains an isolated source profile and
  performance ordering depends on target measurements.
- Evidence chain: panel a maps BLIS facts to two same-backend callable Contracts
  and records OpenBLAS structural conflicts without claiming an implemented
  OpenBLAS ABI; panel b separates the BLIS-derived static soft score and its
  six workload-family interactions from the shared f64 target measurements.
- Archetype: two-panel schematic-led composite.
- Review risks: this is a model-boundary schematic, not effect-size evidence;
  do not imply that different packing/call ABIs can be merged, that an OpenBLAS
  internal ABI was integrated, or that Expert+Data outperformed Data-only.
  The frozen comparison covers one i7-10750H host, 12 holdout workloads and
  five seeds.

## Figure 3-3: evidence and normalization flow

- Core conclusion: every normalized field and downstream decision remains
  traceable to source, derivation, review state, and evidence level, while
  target measurements update ordering without changing hard execution paths.
- Evidence chain: source/build/measurement evidence flows through extraction,
  verification, schemas, and provenance.
- Archetype: schematic-led process flow.
- Review risks: machine verification must remain distinct from human signoff.

## Figure 3-4: end-to-end provenance case

- Core conclusion: the same provenance chain separates Contract eligibility
  from end-to-end execution: the frozen prototype is eligible at the interface
  level but is predicted and observed to fall back, while the integrated
  `pack_mode=ab` path reaches the predicted direct BLIS call.
- Evidence chain: source line to Fact to Contract to Transform candidate, then
  a fork into preliminary and integrated runtime observations.
- Archetype: asymmetric evidence chain.
- Review risks: preserve the frozen fallback result, require wrapper, kernel
  symbol and numerical evidence for the later direct result, and avoid using
  one anchor timing as a general performance claim.
