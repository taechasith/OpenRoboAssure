# OpenRoboAssure v1.0.0 limitations statement

OpenRoboAssure v1.0.0 is a simulation-only software and benchmark package. Its
results do not establish physical-robot safety, real-world reliability,
regulatory compliance, guaranteed robustness, complete failure discovery, or
proven sim-to-real transfer.

## Core limitations

- No physical robot validation was performed.
- The full benchmark covers ORA-4A Pick-and-Place only.
- Panda and UR5e are included as imported model assets and kinematic probes, not
  as successful full-task benchmark executions.
- MuJoCo/PyBullet canonical-state checks do not prove contact-physics fidelity
  or dynamic equivalence.
- All P10 learned-policy methods recorded 0% mean held-out task success.
- No method superiority claim is supported.
- Sensitivity-guided and closed-loop revisions did not improve learned-policy
  held-out success under the released budgets.
- P12 clean software reproduction is a public smoke reproduction, not a full
  250,000-episode rerun.

## Permitted v1.0.0 claims

- Open-source, local, simulation-only software package.
- No paid training dataset, paid API, proprietary simulator, secret credential,
  or physical robot is required for public smoke reproduction.
- Procedural synthetic benchmark data and deterministic evidence files are
  released under the stated repository licences.
- Counterexample search, coverage measurement, and hidden-target sim-to-sim
  calibration evidence are included as simulation evidence.
- The P10 benchmark is a valid preserved negative result for the approved
  simulation-only ORA-4A Pick-and-Place scope.

## Prohibited v1.0.0 claims

- Real-world validated.
- Physically safe.
- Certified or compliant with a safety standard.
- Universal robot/task support.
- Complete failure coverage.
- Proven sim-to-real performance.
- Guaranteed robust learned policies.
- Cross-simulator dynamic equivalence.
