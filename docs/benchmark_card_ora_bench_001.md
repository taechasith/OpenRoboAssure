# Benchmark card: ORA-BENCH-001

## Identity

- Benchmark id: `ORA-BENCH-001`
- Release package: `v1.0.0`
- Scope: simulation-only ORA-4A Pick-and-Place
- Frozen preregistration: `experiments/preregistered/ORA-BENCH-001.yaml`
- Result package: `reports/benchmarks/ORA-BENCH-001.json`
- Result hash:
  `98db58c72436a2d626d91f209d8a505ffcaac9fe4a019f015276ffcedc367d0d`

## Intended use

Use this benchmark to reproduce and audit the OpenRoboAssure software evidence
pipeline: protected preregistration, hidden-evaluation handling, deterministic
scenario generation, local policy training/evaluation, negative-result
preservation, and public smoke reproduction.

Do not use this benchmark as evidence of physical robot safety, real-world
reliability, regulatory compliance, sim-to-real performance, or learned-policy
robustness.

## Scope

| Dimension | Value |
|---|---|
| Robot | ORA-4A only |
| Task | Pick-and-Place only |
| Simulator evidence | Simulation-only; MuJoCo primary, PyBullet smoke/canonical checks |
| Methods | A-E |
| Seeds | 5 per method |
| Hidden evaluation scenarios | 10,000 per method/seed |
| Scheduled evaluations | 250,000 |
| Physical robot validation | None |

## Methods

| Method | Description |
|---|---|
| A | no randomization |
| B | broad independent uniform randomization |
| C | automatic curriculum |
| D | Morris/Sobol-guided randomization |
| E | P07 closed-loop revision |

## Result summary

All 25 method/seed jobs completed and classified. Every method recorded 0% mean
held-out task success.

| Method | Classified runs | Evaluation episodes | Mean held-out success | Bootstrap 95% interval |
|---|---:|---:|---:|---:|
| A | 5 | 50,000 | 0.0 | 0.0-0.0 |
| B | 5 | 50,000 | 0.0 | 0.0-0.0 |
| C | 5 | 50,000 | 0.0 | 0.0-0.0 |
| D | 5 | 50,000 | 0.0 | 0.0-0.0 |
| E | 5 | 50,000 | 0.0 | 0.0-0.0 |

## Integrity checks

- Protected P09 hashes: passed.
- Licence audit: passed.
- Hidden catalogue reveal: after result freeze.
- Training/evaluation parameter-hash leakage: 0 overlaps.
- Clean software reproduction: passed via
  `reports/reproduction/clean-software/P12-CLEAN-SOFTWARE-REPRODUCTION.json`.

## Limitations

- No physical robot validation.
- No learned-policy robustness evidence.
- No method superiority evidence.
- No cross-simulator dynamic equivalence claim.
- Full benchmark is limited to ORA-4A Pick-and-Place.
- P12 smoke reproduction is not a full 250,000-episode P10 rerun.
