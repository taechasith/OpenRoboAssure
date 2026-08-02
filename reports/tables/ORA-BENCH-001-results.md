# ORA-BENCH-001 result table

Source: `reports/benchmarks/ORA-BENCH-001.json`

Report hash:
`98db58c72436a2d626d91f209d8a505ffcaac9fe4a019f015276ffcedc367d0d`

| Method | Description | Classified runs | Evaluation episodes | Mean held-out success | Bootstrap 95% interval | Interpretation |
|---|---|---:|---:|---:|---:|---|
| A | no randomization | 5 | 50,000 | 0.0 | 0.0-0.0 | negative result preserved |
| B | broad independent uniform | 5 | 50,000 | 0.0 | 0.0-0.0 | negative result preserved |
| C | automatic curriculum | 5 | 50,000 | 0.0 | 0.0-0.0 | negative result preserved |
| D | Morris/Sobol guided | 5 | 50,000 | 0.0 | 0.0-0.0 | negative result preserved |
| E | P07 closed-loop revision | 5 | 50,000 | 0.0 | 0.0-0.0 | negative result preserved |

All five methods recorded 0% mean held-out task success. This table supports
the P11 conservative interpretation and does not support learned-policy
robustness or method-superiority claims.
