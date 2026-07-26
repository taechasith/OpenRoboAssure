# Changelog

All notable project changes will be documented here.

## Unreleased

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
