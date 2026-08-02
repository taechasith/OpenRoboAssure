# OpenRoboAssure simulation benchmark draft

This draft records the current evidence boundary for OpenRoboAssure after
`GATE-P11-INTERPRETATION`. It is not a physical-robot validation paper and does
not claim real-world safety.

## Abstract draft

OpenRoboAssure is a local, open-source, simulation-only assurance pipeline for
procedural robot-manipulation experiments. In the preregistered
`ORA-BENCH-001` benchmark, five learned-policy methods were evaluated on the
approved ORA-4A Pick-and-Place scope with 250,000 scheduled hidden evaluation
episodes. The benchmark completed operationally, preserved hidden-catalogue
integrity, and detected no training/evaluation parameter-hash leakage. All five
methods recorded 0% mean held-out task success. The result is therefore a valid
negative benchmark result for this limited simulation scope, not evidence of
learned-policy robustness or physical safety.

## Evidence boundary

The current evidence supports claims about deterministic local execution,
scenario generation, protected benchmark packaging, hidden-evaluation handling,
and preservation of negative results. It does not support claims about physical
robot performance, real-world reliability, regulatory compliance, sim-to-real
transfer, cross-simulator dynamic equivalence, or method superiority.

## Limitations

- Simulation-only evidence; no physical-robot validation.
- ORA-4A Pick-and-Place only for the full benchmark.
- Learned policies failed completely under the approved training budget.
- Component value cannot be attributed because all methods recorded zero task
  success.
- P04 canonical mapping does not establish contact-physics or dynamic
  equivalence.
- Independent reproduction remains pending `GATE-P12-REPRODUCTION`.

## Result interpretation

The correct interpretation is conservative: OpenRoboAssure currently
demonstrates a rigorous local evidence pipeline and a preserved negative result,
not a successful robust learned controller. Future work should either improve
the learned-policy baseline enough to produce non-zero task success or narrow
public claims to the reproducibility and benchmark-governance machinery.
