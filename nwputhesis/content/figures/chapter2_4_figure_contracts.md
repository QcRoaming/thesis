# Chapters 1-4 figure contracts

All eleven figures target the Northwestern Polytechnical University master's
thesis layout. The plotting backend is Python only. Each figure is exported as
editable PDF/SVG, 600-dpi TIFF, and PNG preview. The manuscript uses the PDF
version.

## Figure 1-1: External-microkernel admissibility gap

- Core conclusion: a Transform schedule that is semantically legal is not yet
  admissible to a specific external microkernel; the Contract closes that gap
  and classifies the candidate as direct, adapt, fallback, or reject before
  performance evaluation.
- Archetype: schematic-led composite.
- Final size: approximately 144 mm by 78 mm at 0.90 text width.
- Panel map: schedule and payload inputs; L1 semantic gate; Contract and
  adapter-capability gate; four execution outcomes and their downstream
  actions; a lower strip separating legality, admissibility, and performance.
- Evidence hierarchy: the semantic-to-implementation gap and Contract gate are
  primary; path actions and layer separation are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; terminology follows the Chapter 1
  problem statement and the Chapter 4 execution semantics.
- Image integrity: vector primitives only.
- Reviewer risk: semantic legality must not be drawn as proof of external-call
  safety; fallback is a correct execution route rather than an error; the four
  path classes must not imply a performance ranking.

## Figure 1-2: Research content and technical route

- Core conclusion: the thesis forms a closed evidence chain from pinned source
  facts through Contract/Profile construction, candidate-space compilation,
  real execution, four research questions, and a deployment decision.
- Archetype: schematic-led workflow.
- Final size: approximately 141 mm by 82 mm at 0.88 text width.
- Panel map: source evidence; hard/soft knowledge objects; constrained space
  and path classification; Transform-to-binary execution and joint checks;
  RQ1--RQ4 evidence and deployment decision; two explicitly typed feedback
  loops for target measurement and source revision.
- Evidence hierarchy: the five-phase route is primary; the measurement and
  invalidation loops are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; phase contents follow the four
  research tasks and four research questions in Chapter 1.
- Image integrity: vector primitives only.
- Reviewer risk: target measurements may update Performance Profile but not
  hard Contract fields; source revision invalidates affected knowledge objects
  rather than rewriting historical experiments.

## Figure 2-1: GEMM layers, packing, and the microkernel interface

- Core conclusion: an external microkernel consumes fixed packed micro-panels
  and updates an MR by NR register tile, while the caller remains responsible
  for macro blocking, strides, tails, and the real call ABI.
- Archetype: schematic-led composite.
- Final size: approximately 144 mm by 78 mm at 0.90 text width.
- Panel map: original matrices and highlighted blocks; packed A/B panels;
  microkernel input/output tiles; call-boundary obligations.
- Evidence hierarchy: data-layout hierarchy is primary; the obligation strip
  is supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; terminology follows the Chapter 2
  definitions and the implemented packing/adapter interface.
- Image integrity: vector primitives only.
- Reviewer risk: the schematic must not imply that all libraries share one
  panel schema or that MC/KC/NC are correctness constraints.

## Figure 2-2: L1/L2/L3 problem boundaries

- Core conclusion: semantic legality, implementation admissibility, and
  performance economics consume different evidence, and a higher layer cannot
  repair failure at a lower layer.
- Archetype: schematic-led composite.
- Final size: approximately 128 mm by 74 mm at 0.80 text width.
- Panel map: three stacked layers with their inputs, checks, outputs, and
  one-way dependency.
- Evidence hierarchy: layer boundaries and outputs are primary; the
  non-substitution rule is supporting evidence.
- Statistics: none.
- Source data: no quantitative source data.
- Image integrity: vector primitives only.
- Reviewer risk: the diagram must not imply that successful L2 checking proves
  performance or that fallback fails L1.

## Figure 3-1: Source-to-knowledge pipeline

- Core conclusion: pinned multi-source evidence is normalized into field-level
  Facts, audited for conflicts, and split so that only verified hard facts enter
  Contract while soft performance facts enter Performance Profile.
- Archetype: schematic-led workflow.
- Final size: approximately 141 mm by 84 mm at 0.88 text width.
- Panel map: configuration, kernel/packing/call, build/object, and runtime
  sources; field-level Fact extraction; normalization, conflict handling,
  machine checks, and author signoff; Contract, Performance Profile, and
  Unresolved outputs; downstream consumers.
- Evidence hierarchy: the fixed-source-to-Fact chain is primary; audit states
  and typed outputs are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; source types and object states
  follow the Chapter 3 evidence model.
- Image integrity: vector primitives only.
- Reviewer risk: values from BLIS and OpenBLAS must not be averaged or merged;
  machine checks and author signoff are distinct states; the four object types
  do not share one confidence threshold.

## Figure 3-2: Microkernel Admissibility Contract schema

- Core conclusion: a Contract groups hard call conditions, declared execution
  capabilities, and evidence/validity metadata, then exposes field-level
  diagnostics to the checker.
- Archetype: schematic-led composite.
- Final size: approximately 141 mm by 86 mm at 0.88 text width.
- Panel map: identity header; ten grouped field cards; diagnostic record footer;
  direct/adapt/fallback/reject output strip.
- Evidence hierarchy: grouped schema fields are primary; diagnostic
  consumption is supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; field groups follow the Contract
  schema and package records.
- Image integrity: vector primitives only.
- Reviewer risk: grouped fields must not suggest that BLIS and OpenBLAS use
  identical values or binary ABIs.

## Figure 3-3: Provenance, conflicts, and invalidation lifecycle

- Core conclusion: field-level provenance makes dependency changes explicit:
  a changed revision, source hash, schema, generator, or adapter version marks
  the affected Contract stale, triggers re-extraction and re-verification, and
  keeps historical experiments pinned to their original revision.
- Archetype: schematic-led lifecycle.
- Final size: approximately 138 mm by 76 mm at 0.86 text width.
- Panel map: verified knowledge revision and dependency fingerprint; change
  detection; stale quarantine; impact analysis and Fact re-extraction; field
  checks, conflict review, adapter validation, and author signoff; new verified
  revision; immutable historical-evidence branch.
- Evidence hierarchy: the verified-to-stale-to-reverified state transition is
  primary; the history branch and conflict priority are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; lifecycle states follow the Chapter
  3 provenance and version-validity rules.
- Image integrity: vector primitives only.
- Reviewer risk: re-extraction must not automatically sign a new Contract;
  stale objects cannot generate direct/adapt candidates; historical results
  must not be relabelled as results of the new revision.

## Figure 4-1: Contract-space generation and execution architecture

- Core conclusion: a shared candidate-record interface connects knowledge,
  space compilation, tuning, backend materialization, and evidence collection,
  while backend-specific generators remain package local.
- Archetype: schematic-led composite.
- Final size: approximately 150 mm by 90 mm at 0.94 text width.
- Panel map: five horizontal layers; shared-core lane; BLIS and OpenBLAS
  package-local backend cards; evidence-to-Profile feedback.
- Evidence hierarchy: shared layers and candidate record are primary;
  package-local boundaries and feedback direction are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; modules follow the implemented
  Contract/checker/token/materialization interfaces.
- Image integrity: vector primitives only.
- Reviewer risk: feedback must update Performance Profile only, not Contract;
  the OpenBLAS package-local generator must not be drawn as shared core.

## Figure 4-2: Four-path decision and generation semantics

- Core conclusion: a fixed decision order selects direct, adapt, fallback, or
  reject from generic executability, hard Contract conditions, declared adapter
  capability, and safe-fallback availability; the selected path determines
  generation actions rather than a performance rank.
- Archetype: schematic-led decision tree.
- Final size: approximately 134 mm by 92 mm at 0.84 text width.
- Panel map: candidate/context inputs; generic legality decision; applicable
  Contract and hard-condition decisions; declared-adapter decision; safe
  fallback decision; four terminal action cards and a diagnostic-record footer.
- Evidence hierarchy: the decision order and mutually exclusive terminals are
  primary; action cards and diagnostics are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; predicates and actions follow the
  Chapter 4 path table and Compatibility Checker interface.
- Image integrity: vector primitives only.
- Reviewer risk: routine packing remains part of direct; adapt is limited to
  declared finite capabilities; fallback is correct execution; no path class
  should be visually interpreted as a speed hierarchy.

## Figure 4-3: Parameter activity and candidate normalization

- Core conclusion: two direct-path aliases that differ only in inactive
  `vectorize` collapse to one canonical schedule, and normalized IR provides an
  independent equivalence audit.
- Archetype: schematic-led composite with two panels.
- Final size: approximately 141 mm by 72 mm at 0.88 text width.
- Panel map: a, paired candidate records and active/inactive fields; b,
  canonical key and normalized-IR equality.
- Evidence hierarchy: the paired real alias is primary; key/hash agreement is
  validation evidence.
- Statistics: none; the displayed pair is one audited example, not an
  aggregate result.
- Source data: `source_data_chapter4_parameter_normalization.csv`.
- Image integrity: vector primitives only.
- Reviewer risk: the example must not claim that `vectorize` is globally
  inactive or report Chapter 5 aggregate reductions early.

## Figure 4-4: Direct and adapt data paths

- Core conclusion: direct and adapt reuse the same packed-panel and
  microkernel core, but adapt adds zero padding, a temporary C tile, actual-K
  propagation, and valid-region scatter for fringe blocks.
- Archetype: schematic-led composite with two panels.
- Final size: approximately 147 mm by 82 mm at 0.92 text width.
- Panel map: a, direct full-tile update; b, M/N/K fringe preparation and
  scatter.
- Evidence hierarchy: data layouts and write-back behavior are primary;
  runtime counters and validation gates are supporting evidence.
- Statistics: none.
- Source data: no quantitative source data; the layout follows the implemented
  BLIS f32/f64 packing pass and fringe wrapper.
- Image integrity: vector primitives only.
- Reviewer risk: the figure must not imply arbitrary-layout support, omit
  beta=1 accumulation, or suggest a speed ordering between direct and adapt.
