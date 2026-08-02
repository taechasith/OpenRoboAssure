# Governance decisions

Decision records preserve project-direction choices and their approval status.
Directional changes require the project owner's approval; implementation details
remain agent-autonomous as defined in the master build guide.

## Recorded — P12 clean reproduction implementation

- **Status:** implemented pending `GATE-P12-REPRODUCTION`
- **Scope:** public clean-software smoke reproduction, one-command pilot
  reproduction, offline-after-sync execution, Linux CI smoke reproduction, and
  machine-readable reproduction certificates.
- **Evidence path:** `ora reproduce smoke` runs an offline doctor check, strict
  licence audit, deterministic scripted baseline, scenario validity sample, and
  public P10 smoke benchmark without requiring the private P09 seed package.
- **Tutorial:** [docs/reproduction.md](../docs/reproduction.md)
- **Pending gate:** the owner must still approve whether the reproduction
  evidence is sufficient for v1.0 under `GATE-P12-REPRODUCTION`.
- **Boundary:** P12 smoke reproduction is not a full 250,000-episode P10 rerun
  and does not change the P11 negative-result interpretation.

## Approved — GATE-P11-INTERPRETATION

- **Status:** approved on 2026-08-02
- **Selected option:** A, conservative negative-result interpretation.
- **Decision record:**
  [GATE-P11-INTERPRETATION.yaml](approvals/GATE-P11-INTERPRETATION.yaml)
- **Evidence basis:** `ORA-BENCH-001` completed all 25 method/seed jobs and
  250,000 scheduled evaluation episodes with a 100% classified job rate. The
  protected-hash preflight passed, the licence audit passed, the hidden
  catalogue was revealed only after result freeze, and no training/evaluation
  parameter-hash leakage was detected.
- **Interpretation:** all methods A-E recorded 0% mean held-out task success.
  This is a valid negative result for the approved simulation-only ORA-4A
  Pick-and-Place scope, not evidence of learned-policy robustness or method
  superiority.
- **Claims supported:** operational completion of the full benchmark package,
  preservation of a negative result, and no detected train/evaluation
  parameter-hash leakage under the implemented check.
- **Claims rejected:** learned-policy robustness, System E superiority, System D
  or E worst-case superiority, sensitivity-guided learned-policy improvement,
  physical-robot validation, real-world safety or reliability, regulatory
  compliance, sim-to-real reliability, and cross-simulator dynamic equivalence.
- **Consequence:** P12 independent reproduction may proceed. Public v1.0 claims
  must remain conservative unless later approved evidence changes the evidence
  boundary.

## Approved — GATE-P09-PREREGISTRATION

- **Status:** approved on 2026-08-01
- **Scope:** conservative option A preregistration for `ORA-BENCH-001`: ORA-4A
  Pick-and-Place only; methods A-E; five training seeds; 100,000 training
  environment steps per method/seed; 10,000 hidden evaluation scenarios per
  method/seed for 250,000 scheduled evaluations; hidden seed and failure
  catalogue values committed by digest only until result freeze; local or
  approved free-compute ceiling.
- **Decision record:**
  [GATE-P09-PREREGISTRATION.yaml](approvals/GATE-P09-PREREGISTRATION.yaml)
- **Manifest:**
  [ORA-BENCH-001.yaml](../experiments/preregistered/ORA-BENCH-001.yaml)
- **Consequence:** P10 full benchmark execution may proceed only if protected
  hashes verify and no frozen benchmark file changes. Panda, UR5e,
  Push-to-Target, insertion, physical validation, and cross-simulator dynamic
  equivalence claims remain outside the preregistered benchmark.
- **Evidence basis:** P08 completed operationally but all five methods had 0%
  held-out success. The preregistration therefore prioritizes a rigorous,
  hidden, simulation-only quantification of the validated ORA-4A scope over
  unsupported breadth.

## Approved — GATE-P08-PILOT

- **Status:** approved on 2026-07-31
- **Scope:** conservative pilot option A: ORA-4A Pick-and-Place only; methods
  A-E; three training seeds per method; 2,000 evaluation scenarios per
  method/seed for 30,000 scheduled evaluations; hidden catalogue labels revealed
  only after result freeze; local CPU-only compute ceiling.
- **Decision record:**
  [GATE-P08-PILOT.yaml](approvals/GATE-P08-PILOT.yaml)
- **Consequence:** P08 pilot implementation may proceed. Panda task execution
  and Push-to-Target remain outside the approved pilot scope. The pilot success
  criterion is operational reproducibility and benchmark-defect discovery, not
  support for the research hypotheses.
- **Evidence:** `ORA-PILOT-001` completed 30,000 scheduled evaluation episodes
  with a 100% classified job rate, deterministic catalogue regeneration, and
  zero detected training/evaluation parameter-hash leakage. All five methods
  recorded 0% held-out task success; the negative result and benchmark defects
  are preserved for P09 preregistration.

## Recorded — P07 closed-loop implementation

- **Status:** implemented on 2026-07-30 without a new directional gate.
- **Scope:** hidden-target calibration, counterexample search and replay,
  coverage measurement, coverage-gap scenario generation, randomization
  revision, and CPU-sized System E retraining for ORA-4A Pick-and-Place.
- **Consequence:** P07 may be reviewed for the v0.7.0 milestone. The next
  required human gate remains `GATE-P08-PILOT` before pilot benchmark
  implementation. P07 does not add a new uncertainty category, does not change
  protected success metrics, and does not claim real-world validation.

## Approved — GATE-P06-BASELINES

- **Status:** approved on 2026-07-26
- **Scope:** the CPU-standard ORA-4A Pick-and-Place campaign: Systems A-D; a
  state-only 64x64 MLP with fixed reward, action limits, and stopping rule;
  five 100,000-step seeds per system; 200 held-out scenarios per policy/seed;
  and the declared Morris/Sobol sensitivity thresholds and selection rule.
- **Decision record:**
  [GATE-P06-BASELINES.yaml](approvals/GATE-P06-BASELINES.yaml)
- **Consequence:** P06 implementation may proceed. Panda and UR5e remain
  model probes, failed seeds remain evidence, and each added dependency must
  pass the P02 licence audit before it is used. The owner additionally approved
  only package-specific runtime exceptions for transitive `Pillow` (MIT-CMU)
  and `tqdm` (MPL-2.0 AND MIT), with their notices preserved; MPL-2.0 remains
  absent from the general allow-list.
- **Evidence:** `EXP-POLICY-BASELINES-001` completed its exact four-system,
  five-seed, two-million-step campaign with 4,000 common held-out episodes.
  All learned-policy systems recorded 0% held-out success; the negative result,
  all model hashes, and all seed records are preserved. `EXP-SENS-001` retains
  its scripted-reference Morris/Sobol selection evidence separately.

## Approved — GATE-P05-SCENARIO-ONTOLOGY

- **Status:** approved on 2026-07-26
- **Scope:** the core constrained Pick-and-Place scenario ontology; its physics,
  geometry, control, sensor, and environment variables; global validity bounds;
  the S0–S7 family definitions; declared exclusions; and one million
  deterministic scenarios for `EXP-SCENARIO-VALIDITY-001`.
- **Decision record:**
  [GATE-P05-SCENARIO-ONTOLOGY.yaml](approvals/GATE-P05-SCENARIO-ONTOLOGY.yaml)
- **Consequence:** P05 implementation and its one-million-scenario validity
  evidence are complete pending review. Dynamic/contact uncertainty variables
  remain excluded until separately approved with supporting simulator semantics
  and evidence.

## Approved — GATE-P00-CHARTER

- **Status:** approved on 2026-07-26
- **Scope:** name, mission, simulation-only v1.0 scope, free-data requirement,
  code and generated-data licences, research questions, candidate robots and
  tasks, and prohibited public claims.
- **Decision record:** [GATE-P00-CHARTER.yaml](approvals/GATE-P00-CHARTER.yaml)
- **Consequence:** P01 repository bootstrap may begin. Future direction gates
remain mandatory.

## Approved — GATE-P04-ROBOT-SET

- **Status:** approved on 2026-07-26
- **Scope:** MuJoCo as primary and PyBullet as secondary simulator; ORA-4A,
  Panda, and UR5e as the reference robot set; 5 mm static end-effector and
  1 mm shared-geometry equivalence tolerances; no licence exception.
- **Model sources:** MuJoCo Menagerie commit
  `71f066ad0be9cd271f7ed58c030243ef157af9f4`: `franka_emika_panda`
  (Apache-2.0) and `universal_robots_ur5e` (BSD-3-Clause).
- **Decision record:** [GATE-P04-ROBOT-SET.yaml](approvals/GATE-P04-ROBOT-SET.yaml)
- **Consequence:** P04 implementation may proceed. Dynamic equivalence remains
  a measurement and reporting obligation, not an assumed property.

## DRAFT-0001 — Initial charter proposal

- **Date:** 2026-07-26
- **Status:** approved by `GATE-P00-CHARTER`
- **Decision:** Define OpenRoboAssure as a human-governed, simulation-only,
  open-source pipeline for reproducible physical-AI assurance experiments.
- **Proposed scope:** rigid-body, fixed-base robot manipulation; procedural
  synthetic data; MuJoCo and PyBullet; ORA-4A, Panda, and UR5e candidates;
  pick-and-place, insertion, and pushing candidates.
- **Proposed licences:** Apache-2.0 for project code and CC BY 4.0 for original
  generated numeric benchmark outputs.
- **Risks and limitations:** simulation results do not establish physical safety
  or real-world reliability; third-party robot assets require file-specific
  licence review; research hypotheses may have negative results; reproducibility
  requires deterministic seeds, recorded environments, and preserved failures.
- **Outcome:** approved; this decision remains in force until a protected
  charter file changes.
