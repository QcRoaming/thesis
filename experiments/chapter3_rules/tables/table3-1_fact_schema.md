| Field | Type | Definition |
|---|---|---|
| fact_id | required | Globally unique field-level fact identifier |
| operator | required | Source operator semantic category |
| dtype | required | Element data type |
| architecture | required | Knowledge-source architecture |
| library | required | Source library |
| version | required | Immutable source revision |
| source_file | required | Source path relative to the library root |
| source_line | required | One-based source line |
| source_symbol | required | Owning source symbol |
| raw_value | required | Value as extracted or deterministically decoded |
| normalized_field | required | Canonical field name |
| normalized_value | required | Canonical typed value |
| applicability | required | Operation, machine, feature, and thread scope |
| evidence_level | required | E1-E5 evidence grade |
| extraction_mode | required | Automatic, derived, manual, or empirical |
| verification_status | required | Machine/human verification state |
| notes | required | Ambiguity or derivation note |
