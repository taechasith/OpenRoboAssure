# ORA-BENCH-001 P11 interpretation and limitation analysis

Status: approved by `GATE-P11-INTERPRETATION` on 2026-08-02 under option A,
the conservative negative-result interpretation.

Primary evidence:

- Result package: `reports/benchmarks/ORA-BENCH-001.json`
- GitHub graph: `reports/benchmarks/ORA-BENCH-001.github.md`
- Result hash:
  `98db58c72436a2d626d91f209d8a505ffcaac9fe4a019f015276ffcedc367d0d`
- Benchmark scope: ORA-4A Pick-and-Place only; methods A-E; five seeds per
  method; 10,000 hidden evaluation scenarios per method/seed.

## Final interpretation

`ORA-BENCH-001` is a valid conservative negative benchmark result for the
approved simulation-only ORA-4A Pick-and-Place scope. The full benchmark
completed operationally and preserved the failed learned-policy outcome. It does
not establish learned-policy robustness, physical-robot performance, real-world
safety, sim-to-real reliability, or method superiority.

The result supports a narrow operational claim: the project can run the frozen
full benchmark package, preserve hidden evaluation integrity, classify all
method/seed jobs, and publish a reproducible evidence package for the approved
simulation-only scope. Independent reproduction remains a P12 requirement.

## Confirmatory results

These results are confirmatory because they were covered by the P09 frozen
benchmark scope, commitments, protected hashes, and statistical plan.

| Evidence item | Result | Interpretation |
|---|---:|---|
| Method/seed jobs completed and classified | 25 / 25 | Operational full-benchmark execution succeeded. |
| Scheduled evaluation episodes | 250,000 | The planned hidden evaluation budget was executed. |
| Classified job rate | 1.0 | Meets the 0.95 operational acceptance threshold. |
| Training/evaluation parameter-hash leakage | 0 overlaps | No detected leakage under the implemented hash check. |
| Protected P09 hashes | passed | Frozen preregistration material matched at execution time. |
| Hidden catalogue reveal | after result freeze | Hidden failure labels were unavailable before result freeze. |

Primary held-out task success was zero for every method:

| Method | Classified runs | Evaluation episodes | Mean held-out task success | Bootstrap 95% interval |
|---|---:|---:|---:|---:|
| A - no randomization | 5 | 50,000 | 0.0 | 0.0-0.0 |
| B - broad independent uniform | 5 | 50,000 | 0.0 | 0.0-0.0 |
| C - automatic curriculum | 5 | 50,000 | 0.0 | 0.0-0.0 |
| D - Morris/Sobol guided | 5 | 50,000 | 0.0 | 0.0-0.0 |
| E - P07 closed-loop revision | 5 | 50,000 | 0.0 | 0.0-0.0 |

The preregistered superiority hypotheses are not supported. Because all methods
have zero primary success, there is no positive primary-success effect for
System E against A-D and no supported worst-case improvement claim for D or E.

## Exploratory results

These observations are useful for diagnosis but are not confirmatory method
claims because they were interpreted after the frozen result was known.

- Hidden catalogue labels after result freeze show repeated exposure to
  difficult families and condition labels, including long transfers, high
  delay, high observation dropout, and heavy low-friction cases.
- The all-zero learned-policy outcome prevents reliable component attribution:
  removing or adding a component cannot be credited with benefit when no method
  reaches non-zero task success.
- The deterministic scripted controller remains a useful smoke and scenario
  validity reference, but it is not evidence that the learned-policy training
  stack is robust.

## Required ablations and documented omissions

P11 requires each major component to have an ablation or a documented reason for
omission. The table below distinguishes actual comparative evidence from
omitted clean ablations.

| Required P11 item | Status | Evidence or omission rationale |
|---|---|---|
| Remove sensitivity analysis | Post-hoc comparative evidence only | Methods A-C do not use the P06 Morris/Sobol-guided System D path, and all methods still recorded 0% success. This prevents any sensitivity-benefit claim, but it is not a clean isolated ablation. |
| Remove hidden-target calibration | Documented omission | P10 compares A-E, where E includes P07 closed-loop evidence. It does not isolate hidden-target calibration from falsification, coverage, and randomization revision. A clean calibration-only ablation would change the frozen method set. |
| Remove falsification search | Documented omission | P10 does not isolate falsification search from the rest of System E. Counterexamples remain preserved evidence, but they cannot be credited with learned-policy improvement. |
| Remove coverage guidance | Documented omission | P10 does not isolate coverage guidance. Coverage remains diagnostic evidence, not a demonstrated cause of success. |
| Remove AI-generated uncertainty proposals | Not used for confirmatory claims | No confirmatory P10 method claim depends on AI-generated uncertainty proposals. The approved uncertainty space is the P05 procedural ontology and P09 frozen manifest. |
| Replace correlated distributions with independent distributions | Post-hoc comparative evidence only | Method B is the broad independent-uniform comparator. It also recorded 0% success, so independent distributions did not rescue learned-policy performance under the frozen budget. |
| Reduce target trajectories | Documented omission | Reducing target trajectories would alter the P07 calibration evidence and was not part of the frozen P09 method set. Any trajectory-budget study must be explicitly exploratory or preregistered later. |
| Reduce evaluation budget | Post-hoc comparative evidence only | P08 ran a smaller 30,000-episode pilot and P10 ran 250,000 scheduled episodes. Both produced all-zero learned-policy success. This supports the robustness of the negative finding, not a budget-efficiency claim. |
| Use only one simulator | Documented limitation | P10 is not a multi-simulator dynamic-equivalence benchmark. P04 measured canonical mapping, but P10 does not establish MuJoCo/PyBullet dynamic equivalence or physical fidelity. |
| Remove counterexample replay | Documented omission | Counterexample replay was validated in P07 but was not isolated in P10. Replay remains a diagnostic mechanism, not a demonstrated source of learned-policy improvement. |

## Limitation taxonomy

### Method-performance limitations

- All learned-policy methods failed under the approved training budget.
- No method superiority, sensitivity-guided improvement, curriculum benefit, or
  closed-loop improvement is supported.
- Odds ratios and positive effect sizes are not informative when all primary
  success rates are zero.

### Scope limitations

- The full benchmark covers only ORA-4A Pick-and-Place.
- Panda task execution, UR5e task execution, Push-to-Target, precision
  insertion, and physical robots are outside the approved P10 scope.
- The result is simulation-only and cannot be used as a safety, reliability, or
  regulatory-compliance claim.

### Simulator and dynamics limitations

- P04 canonical-state mapping does not prove contact-physics fidelity.
- Cross-simulator dynamic equivalence is not established.
- Scenario validity checks prove constrained scenario construction, not
  physical-world validity.

### Component-attribution limitations

- Because every learned method has zero success, P11 cannot identify which
  OpenRoboAssure component creates performance value.
- Sensitivity, calibration, falsification, coverage, and counterexample replay
  remain valuable diagnostic components, but P10 does not show that they improve
  learned-policy success.

### Reproduction limitations

- The P10 package includes hashes, logs, model artifacts, and result files, but
  independent reproduction is not complete until `GATE-P12-REPRODUCTION`.
- The Docker/container definition was hashed, but no immutable external Docker
  image digest was recorded in the P10 preflight.

## Supported, rejected, and deferred claims

Supported:

- `ORA-BENCH-001` completed the approved full benchmark scope operationally.
- The result is a preserved negative learned-policy benchmark result for the
  approved simulation-only ORA-4A Pick-and-Place setting.
- No training/evaluation parameter-hash leakage was detected by the implemented
  check.

Rejected:

- Learned-policy robustness.
- Method E superiority over A-D.
- Method D or E worst-case superiority over A or B.
- Sensitivity-guided learned-policy improvement.
- Physical-robot validation, real-world safety, sim-to-real reliability, or
  regulatory compliance.

Deferred:

- Independent reproduction sufficiency: `GATE-P12-REPRODUCTION`.
- Final public v1.0 claim packaging: later public-release gate.
