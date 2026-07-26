# OpenRoboAssure roadmap

This roadmap mirrors the authoritative [master build guide](MASTER_BUILD_GUIDE.md).
Phases proceed in order; a later phase may not begin before its required human
gate has been satisfied.

| Phase | Scope | State | Required gate |
|---|---|---|---|
| P00 | Charter and direction | Completed — charter approved | `GATE-P00-CHARTER` |
| P01 | Reproducible repository bootstrap | Completed — v0.1.0 released | None unless a paid/proprietary dependency is proposed |
| P02 | Free-data and licence enforcement | Completed — v0.2.0 released | `GATE-P02-DATA-POLICY` |
| P03 | MuJoCo and first ORA-4A task | Completed — v0.3.0 released | None |
| P04 | Second simulator and robot library | Completed — v0.4.0 released | `GATE-P04-ROBOT-SET` |
| P05 | Scenario and uncertainty engine | Completed — pending human review before v0.5.0 | `GATE-P05-SCENARIO-ONTOLOGY` |
| P06 | Policies, baselines, and sensitivity | Not started | `GATE-P06-BASELINES` |
| P07 | Calibration, falsification, and coverage | Not started | None |
| P08 | Pilot benchmark | Not started | `GATE-P08-PILOT` |
| P09 | Full benchmark preregistration | Not started | `GATE-P09-PREREGISTRATION` |
| P10 | Full benchmark execution | Not started | `GATE-P10-FULL-BENCHMARK` |
| P11 | Ablation and interpretation | Not started | `GATE-P11-INTERPRETATION` |
| P12 | Independent reproduction | Not started | `GATE-P12-REPRODUCTION` |
| P13 | v1.0 release | Not started | `GATE-P13-RELEASE` |

## P00 exit criteria

- Charter approval exists as a machine-readable record in `governance/approvals/`.
- Protected files are identified in `PROJECT_STATE.yaml`.
- README describes the simulation-only status and non-goals accurately.
- The repository is public or ready to be made public.

## Version milestones

- `v0.1.0`: repository and governance foundation
- `v0.2.0`: data policy and licence enforcement
- `v0.3.0`: primary simulator and first procedural task
- `v0.4.0`: multi-simulator and robot layer
- `v0.5.0`: scenarios and uncertainty engine
- `v0.6.0`: training, baselines, and sensitivity
- `v0.7.0`: calibration, falsification, and coverage
- `v0.8.0`: pilot benchmark
- `v0.9.0`: full benchmark and reproduction
- `v1.0.0`: simulation-validated release
