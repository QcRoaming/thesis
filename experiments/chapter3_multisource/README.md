# Chapter 3 Multi-source Knowledge Extraction

This package extends the Chapter 3 BLIS-only extractor with an independently
maintained implementation, OpenBLAS. It covers Haswell and 128-bit RVV SGEMM.

The package preserves two distinct knowledge classes:

- Compatibility knowledge is a hard, backend-specific contract: ISA,
  microkernel shape, packing implementation, layout and call ABI.
- Performance knowledge is a source-labelled soft prior: BLIS MC/KC/NC or
  OpenBLAS P/Q/R. It must be calibrated by measured feedback before ranking a
  compiler search space.

Run extraction and tests:

```bash
python3 scripts/extract_multisource.py
python3 -m unittest discover -s tests -v
```

Pinned source revisions and SHA-256 evidence hashes are recorded in
`provenance/manifest.json`. OpenBLAS build and runtime validation are handled by
`scripts/validate_openblas.py` so source extraction and empirical validation
remain separately auditable.
