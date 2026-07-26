# Governance decisions

Decision records preserve project-direction choices and their approval status.
Directional changes require the project owner's approval; implementation details
remain agent-autonomous as defined in the master build guide.

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
