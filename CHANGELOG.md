# Changelog

All notable project changes will be documented here.

## Unreleased

### Added

- P13 `v1.0.0` release-candidate package manifest.
- Citation metadata, benchmark card, learned-policy model card, limitations
  statement, public seed/evidence ledger, and ORA-BENCH-001 result tables.
- Final release-candidate README/status updates for `GATE-P13-RELEASE` review.

### Changed

- Project/package version prepared as `1.0.0` pending final release approval.
- Release claims are narrowed to simulation-only software and benchmark-package
  claims consistent with the P11 negative-result interpretation.

## [0.12.0] - 2026-08-02

### Added

- `ora reproduce smoke` for clean software reproduction certificates covering
  offline doctor, licence audit, deterministic baseline, scenario validity, and
  public P10 smoke benchmark execution without private seed material.
- `ora reproduce pilot` for one-command public P08 pilot reproduction.
- `reproduce-smoke` and `reproduce-pilot` Make targets.
- P12 reproduction tutorial with exact clone, sync, offline run, data checksum,
  and known-failure references.
- Passed clean-clone P12 smoke reproduction certificate.
- `GATE-P12-REPRODUCTION` approval record accepting clean software reproduction
  evidence as sufficient for the v1.0 reproduction gate.

### Changed

- CI now runs `ora reproduce smoke` with `uv run --offline` on Ubuntu after
  dependency sync.
- P10 smoke mode no longer requires the private P09 seed package; full P10 mode
  remains strict.

## [0.11.0] - 2026-08-02

### Added

- `GATE-P11-INTERPRETATION` approval record for the conservative
  negative-result interpretation of `ORA-BENCH-001`.
- P11 interpretation and limitation analysis report, including supported,
  rejected, and deferred claims plus required ablation/omission mapping.
- Paper draft evidence-boundary section that makes the simulation-only and
  all-zero learned-policy limitations prominent.

### Governance

- P11 rejects learned-policy robustness, method superiority,
  sensitivity-guided learned-policy improvement, physical-robot validation,
  real-world safety, sim-to-real reliability, and cross-simulator dynamic
  equivalence claims.
- P12 independent reproduction is the next required gate.

## [0.10.0] - 2026-08-02

### Added

- P10 `ORA-BENCH-001` full benchmark result package, execution logs, tracking
  events, 25 model artifacts, and GitHub-renderable Mermaid benchmark graph.

### Results

- `ORA-BENCH-001` completed all 25 method/seed jobs and 250,000 scheduled
  evaluation episodes with a 100% classified job rate.
- Protected-hash verification, licence audit, and training/evaluation leakage
  checks passed; leakage overlap count was 0.
- The hidden catalogue was revealed after result freeze and archived in the
  result package with 10,000 entries.
- All five preregistered methods recorded 0% mean held-out task success. This
  negative result is preserved pending `GATE-P11-INTERPRETATION`.

## [0.9.0] - 2026-08-01

### Added

- `GATE-P09-PREREGISTRATION` approval record for conservative option A:
  ORA-4A Pick-and-Place only, methods A-E, five training seeds, 10,000 hidden
  evaluation scenarios per method/seed, and a local/free-compute ceiling.
- `experiments/preregistered/ORA-BENCH-001.yaml` as the frozen full benchmark
  manifest for the validated conservative scope.
- Public SHA-256 commitments for the hidden evaluation set and hidden failure
  catalogue without committing hidden seeds, scenario hashes, parameter hashes,
  labels, or catalogue entries.
- Frozen `analysis/statistical_plan.py` helpers and P09 contract tests for
  commitment isolation, deterministic catalogue construction, Holm correction,
  bootstrap intervals, and lower-tail CVaR.

### Governance

- P09 preserves the P08 all-zero learned-policy result and prohibits claims of
  method superiority, physical validation, real-world safety, or regulatory
  compliance unless later preregistered evidence supports them.
- P10 may execute only against the frozen manifest and protected hashes.

## [0.8.0] - 2026-07-31

### Added

- `GATE-P08-PILOT` approval record for conservative option A: ORA-4A
  Pick-and-Place only, methods A-E, three seeds per method, 2,000 evaluations
  per method/seed, hidden catalogue reveal after result freeze, and local
  CPU-only compute ceiling.
- `ora benchmark pilot` and the `openroboassure.benchmark` package for
  preregistered pilot execution, protected-file hashing from committed blobs,
  frozen evaluation seeds, hidden-catalogue reveal, leakage checks,
  operational acceptance reporting, benchmark-defect reporting, and full
  benchmark change proposals.
- `ORA-PILOT-001` manifest, report, tracking events, and 15 P08 pilot model
  artifacts.

### Results

- `ORA-PILOT-001` completed 15 method/seed jobs and 30,000 scheduled evaluation
  episodes with a 100% classified job rate.
- No training/evaluation parameter-hash leakage was detected, and the frozen
  evaluation catalogue regenerated deterministically.
- The pilot passed operational criteria, but all five methods recorded 0%
  held-out task success. This negative result is retained.
- Benchmark defects recorded: zero learned-policy success for methods A-E, plus
  the deliberately conservative scope excluding Panda and Push-to-Target.

## [0.7.0] - 2026-07-30

### Added

- P07 hidden-target calibration with fixed excitation policies, observable
  trajectory discrepancy metrics, Gaussian-error posterior fitting, prediction
  freeze hashing, reveal-stage posterior coverage, and `ora calibrate
  hidden-target`.
- P07 constrained falsification search using an internal VerifAI-compatible
  black-box API, preserved counterexample JSON files, replay across seeds, and
  `ora falsify search` / `ora falsify replay`.
- P07 one-way parameter-bin coverage, pairwise interaction coverage,
  scenario-family coverage, prioritized coverage-gap queue, gap-targeted
  scenario generation, and `ora coverage report`.
- P07 System E closed-loop runner that combines sensitivity, calibration,
  counterexample, and coverage evidence into a revised randomization plan, then
  retrains and compares a CPU-sized demonstration policy.

### Results

- `EXP-CALIBRATION-001` improved observable trajectory RMSE from `0.036349` to
  `0.004901`, while preserving the hidden-target reveal order.
- `EXP-FALSIFICATION-001` found 10 preserved counterexamples in 96 trials;
  `EXP-FALSIFICATION-REPLAY-001` replayed failures at 93.3% across three seeds.
- `EXP-COVERAGE-001` reported a 92.4% combined coverage score and 24 prioritized
  coverage gaps.
- `EXP-LOOP-001` completed System E and retained the negative learned-policy
  result: held-out task success stayed `0.0% -> 0.0%` after P07 demonstration
  retraining.

## [0.6.0] - 2026-07-26

### Added

- P06 Gymnasium-compatible ORA-4A Pick-and-Place wrapper, shared 64x64
  state-only NumPy policy-gradient learner, Systems A-D, local tracking,
  model/configuration hashing, fixed evaluation scenarios, and `ora policy`
  and `ora sensitivity` commands.
- SALib Morris/Sobol evidence with 1,000-resample confidence intervals and
  Optuna verification that gate-fixed sensitivity thresholds were not tuned.

### Results

- `EXP-POLICY-BASELINES-001` ran 20 exact 100,000-step jobs and 4,000 common
  held-out evaluation episodes. The equal-budget check passed; all systems had
  0% held-out task success across five seeds. This negative result is retained.
- `EXP-SENS-001` ran 340 Morris and 4,096 Sobol reference evaluations and
  selected six variables for System D; this is scripted-reference sensitivity,
  not learned-policy robustness evidence.

### Approved

- `GATE-P06-BASELINES` for the CPU-standard ORA-4A Pick-and-Place baseline
  campaign: Systems A-D, a fixed state-only 64x64 MLP, five 100,000-step
  seeds per system, held-out evaluation, and Morris/Sobol selection rules.
- Narrow runtime-only P02 licence exceptions for transitive `Pillow` under
  MIT-CMU and `tqdm` under MPL-2.0 AND MIT; their notices must be preserved,
  and MPL-2.0 remains outside the general allow-list.

## [0.5.0] - 2026-07-26

### Added

- P05 constrained Pick-and-Place uncertainty registry, deterministic Latin
  hypercube and Halton sampling, hard/soft scenario validation, deduplication,
  serializable scenario hashes, and train/evaluation split protection.
- `EXP-SCENARIO-VALIDITY-001`: one million generated scenarios, 100% valid,
  zero duplicates, deterministic regeneration, and 256 accepted scenarios
  exercised through both current simulator adapters.

### Approved

- `GATE-P05-SCENARIO-ONTOLOGY` for the core constrained Pick-and-Place
  ontology, its global validity bounds and exclusions, and one million
  deterministic scenarios for `EXP-SCENARIO-VALIDITY-001`.

## [0.4.0] - 2026-07-26

### Added

- P00 charter draft, project state, governance decision record, roadmap, and
  proposed code/data licence declarations.
- P01 CPU-first Python 3.12 bootstrap with a locked `uv` environment, linting,
  typing, tests, pre-commit hooks, Docker/Compose recipes, CI, `ora doctor`,
  and deterministic seed utilities.
- A network-isolated CPU container smoke path using the already-built,
  lockfile-pinned environment.
- P02 asset schema, policy allow/block lists, dependency and source-header
  licence audit, asset registration command, CI enforcement, and audit report.
- P03 procedural ORA-4A MuJoCo adapter, scripted Pick-and-Place baseline,
  deterministic replay tests, and the 1,000-seed baseline evidence record.
- P04 PyBullet ORA-4A adapter, shared canonical task-space action conversion,
  pinned Panda and UR5e MuJoCo model imports, kinematic model probes, and
  `EXP-SIM-DISCREPANCY-001` cross-simulator evidence.
- Strict asset entrypoint checksum verification and missing-package-metadata
  protection in the licence audit.

### Approved

- `GATE-P00-CHARTER` for the project charter and P00 foundation.
- `GATE-P04-ROBOT-SET` for MuJoCo/PyBullet, ORA-4A/Panda/UR5e, the declared
  equivalence tolerances, and the reviewed model sources.
