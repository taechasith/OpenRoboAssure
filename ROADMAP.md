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
| P05 | Scenario and uncertainty engine | Completed — v0.5.0 released | `GATE-P05-SCENARIO-ONTOLOGY` |
| P06 | Policies, baselines, and sensitivity | Completed — v0.6.0; preliminary learned-policy result is negative | `GATE-P06-BASELINES` |
| P07 | Calibration, falsification, and coverage | Completed - v0.7.0; closed-loop learned-policy result remains negative | None |
| P08 | Pilot benchmark | Completed - v0.8.0; operational pilot passed and learned-policy result remains negative | `GATE-P08-PILOT` |
| P09 | Full benchmark preregistration | Completed — v0.9.0 released; preregistration approved | `GATE-P09-PREREGISTRATION` |
| P10 | Full benchmark execution | Completed — v0.10.0 released; full benchmark operational with preserved negative result | `GATE-P10-FULL-BENCHMARK` |
| P11 | Ablation and interpretation | Completed — v0.11.0 released; conservative interpretation approved | `GATE-P11-INTERPRETATION` |
| P12 | Independent reproduction | Completed — v0.12.0 released; clean software reproduction approved | `GATE-P12-REPRODUCTION` |
| P13 | v1.0 release | Completed — v1.0.0 released; simulation scope validation approved | `GATE-P13-RELEASE` |

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
