# Chapter 4 Figure Contracts

## Figure 4-1

- Core conclusion: Kernel facts constrain the schedule domain before unmodified BaCO evaluates real Transform/AOT candidates.
- Figure archetype: schematic-led workflow.
- Target/output: thesis double-column width; SVG/PDF editable and TIFF 600 dpi.
- Evidence: configuration files, generated spaces, Transform logs, and tuning trace.
- Reviewer risk: predicted kernel path must remain separate from observed LLVM-IR path.

## Figure 4-2

- Core conclusion: Contract filtering and expert ranking reduce the anchor space while the shell remains inside the executable set.
- Figure archetype: quantitative grid with set schematic and path counts.
- Source data: `processed/space_summary.csv`.
- Statistics: deterministic enumeration, one frozen anchor task, no confidence interval.
- Reviewer risk: `S_contract` and `S_exec` are not presented as a simple universal nesting claim.

## Figure 4-3

- Core conclusion: Compatibility classification depends on eleven interface and legality dimensions, not only tile divisibility.
- Figure archetype: decision schematic.
- Source data: `data/reason_codes.json` and checker implementation.
- Reviewer risk: every terminal class needs an explicit reason code and executable action.

## Figure 4-4

- Core conclusion: All three predicted paths instantiate real Transform programs, but the current backend produces fallback LLVM IR for each.
- Figure archetype: asymmetric mixed workflow and quantitative annotation.
- Source data: `raw/transform_paths.csv` and per-case IR/logs.
- Measurement definition: one case per predicted path; median of two repeats, two inner iterations; no inferential statistics.
- Reviewer risk: do not report predicted direct/adapt as observed BLIS replacement.

## Figure 4-5

- Core conclusion: Every tuning candidate retains traceable links to Task Context, Contract, Facts, Rules, reason codes, IR, and measurements.
- Figure archetype: provenance flow schematic.
- Source data: `provenance/candidate_provenance.csv` and source hashes in `processed/contract_registry.json`.
- Reviewer risk: distinguish machine source cross-checks from the separately recorded, completed thesis-author signoff.

## Shared Style And Integrity

- Backend: Python (`matplotlib`) only.
- Final width: 183 mm; heights 92-112 mm depending on figure.
- Font: AR PL SungtiL GB/DejaVu Sans; one installed family covers Chinese, Latin, digits, and arrows; SVG text remains editable and PDF uses TrueType text.
- Palette: neutral gray, blue method signal, teal valid path, orange adaptation, red rejection.
- No microscopy or manipulated raster imagery is used. TIFF files are direct 600 dpi renders of vector-origin figures.
