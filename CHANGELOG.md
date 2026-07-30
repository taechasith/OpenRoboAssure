# Changelog

All notable project changes will be documented here.

## Unreleased

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
