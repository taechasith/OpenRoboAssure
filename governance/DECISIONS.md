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
