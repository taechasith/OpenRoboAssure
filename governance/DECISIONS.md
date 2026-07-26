# Governance decisions

Decision records preserve project-direction choices and their approval status.
Directional changes require the project owner's approval; implementation details
remain agent-autonomous as defined in the master build guide.

## Pending — GATE-P00-CHARTER

- **Status:** awaiting human decision
- **Scope:** name, mission, simulation-only v1.0 scope, free-data requirement,
  code and generated-data licences, research questions, candidate robots and
  tasks, and prohibited public claims.
- **Decision record:** must be created in `governance/approvals/` using the
  machine-readable approval schema in the master build guide.
- **Consequence:** no implementation beyond repository bootstrap may begin
  until approved.

## DRAFT-0001 — Initial charter proposal

- **Date:** 2026-07-26
- **Status:** proposed; not approved
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
- **Required action:** owner approval or requested amendments through
  `GATE-P00-CHARTER`.
