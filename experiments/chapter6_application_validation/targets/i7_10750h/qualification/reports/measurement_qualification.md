# Local x86 measurement qualification

- Status: **FAIL_UNQUALIFIED**
- Scope: diagnostic only; timings are excluded from performance claims.
- Jobs: 120
- Qualifying CPUs: none
- Selected CPU: none
- Selection rule: select the lowest-numbered CPU among qualifying CPUs; never select by throughput
- Next decision: stop local WSL performance claims and retain only correctness, liveness, trace, and static-closure evidence

| CPU | Passing groups | Pass fraction | Qualified |
|---:|---:|---:|---|
| 0 | 2/4 | 50.00% | no |
| 2 | 1/4 | 25.00% | no |
| 4 | 3/4 | 75.00% | no |
| 6 | 3/4 | 75.00% | no |
| 8 | 2/4 | 50.00% | no |
| 10 | 2/4 | 50.00% | no |
