# Multi-source Expert Knowledge Results

## Source revisions

- BLIS: `36df51a81cc732eeadbf2e6732941dd5400db47d`
- OpenBLAS: `b338322e9afc063d95e2c117e85bedf28213295a`

## Extracted SGEMM contracts

| Target | Library | MR x NR | Blocking | Knowledge treatment |
|---|---|---:|---|---|
| haswell | BLIS | 6 x 16 | `{"kc": 256, "mc": 168, "nc": 4080}` | tile/ABI hard; blocking soft |
| rv64iv_vlen128 | BLIS | 16 x 4 | `{"kc": 640, "mc": 320, "nc": 3072}` | tile/ABI hard; blocking soft |
| haswell | OpenBLAS | 8 x 4 | `{"p": 320, "q": 320, "r": "sgemm_r"}` | tile/ABI hard; blocking soft |
| riscv64_zvl128b | OpenBLAS | 8 x 8 | `{"p": 128, "q": 240, "r": 12288}` | tile/ABI hard; blocking soft |

## Conflict audit

The extractor found **4** explicit cross-source conflicts. Register-tile conflicts are not merged because each tile belongs to a different packing and call ABI. Blocking conflicts remain source-labelled soft priors for offline or online calibration.

## Claim boundary

This package proves reproducible extraction, provenance and conflict handling. It does not claim that one library's performance parameters transfer unchanged to another library, compiler pipeline or machine. Runtime library validation and K230 ELF generation are recorded by their own experiment packages.
