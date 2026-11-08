# BLIS Haswell Source Reading Notes

Source revision: `36df51a81cc732eeadbf2e6732941dd5400db47d`.

| Evidence | f32 | f64 | Source |
|---|---:|---:|---|
| GEMM kernel | `bli_sgemm_haswell_asm_6x16` | `bli_dgemm_haswell_asm_6x8` | `config/haswell/bli_cntx_init_haswell.c:54-55` |
| MR | 6 | 6 | context line 192; kernel setup lines 104/970 |
| NR | 16 | 8 | context line 193; kernel setup lines 104/970 |
| MC | 168 | 72 | context line 196 |
| KC | 256 | 256 | context line 197 |
| NC | 4080 | 4080 | context line 206 |
| Pack kernel | `bli_spackm_haswell_asm_6x16` | `bli_dpackm_haswell_asm_6x8` | context lines 74-75 |
| Row preference | true | true | context lines 149-150 |
| ISA flags | AVX2/FMA | AVX2/FMA | `config/haswell/make_defs.mk:68` |

The active `#if 1` branch is authoritative for this extraction. Alternative
`#else` kernels are retained as source alternatives but are not emitted as
active Facts. Alignment, complete packed affine layout, and M/N fringe policy
cannot be established from context registration alone and remain in
`data/ambiguities.csv`.
