| Rule ID | Category | Strength | Priority | Evidence | Action |
|---|---|---|---|---|---|
| register_blocking_matches_contract | register_blocking | hard_for_direct | 100 | E2 | constrain tile_m to multiples of MR and tile_n to multiples of NR |
| cache_blocking_bounded_by_shape | cache_blocking | soft_prior | 70 | E1 | prioritize min(shape_extent, MC/KC/NC) and nearby divisors |
| packing_required_for_direct_kernel_path | packing | conditional_hard | 95 | E1 | insert A/B panel packing or downgrade to fallback |
| vectorization_matches_target_isa | vectorization | soft_prior | 60 | E3 | prioritize N tiles compatible with the dtype-specific vector lane count |
| explicit_tail_or_fallback | tail_and_fallback | hard | 110 | E2 | select adapt when the adapter can compensate; otherwise select fallback or reject with a reason code |
