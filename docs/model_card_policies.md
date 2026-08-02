# Model card: OpenRoboAssure learned-policy artifacts

## Model family

OpenRoboAssure policy artifacts are small NumPy MLP policies used for local
simulation benchmarks. They are not production controllers.

## Intended use

- Reproduce the released simulation benchmark artifacts.
- Audit training/evaluation determinism and model/configuration hashes.
- Study negative-result preservation in a controlled software benchmark.

## Out-of-scope use

- Physical robot control.
- Safety-critical operation.
- Real-world deployment.
- Claims of robust manipulation performance.
- Sim-to-real transfer claims.

## Training scope

| Phase | Artifacts | Scope |
|---|---|---|
| P06 | `reports/models/p06_*.npz` | Systems A-D, ORA-4A Pick-and-Place |
| P07 | `reports/models/p07_system_e_d_77.npz` | Demonstration-scale System E revision |
| P08 | `reports/models/p08_*.npz` | Conservative pilot methods A-E |
| P10 | `reports/models/p10_*.npz` | Full benchmark methods A-E |

All learned-policy runs are simulation-only. The P10 benchmark used five seeds
per method and 100,000 training environment steps per method/seed.

## Performance

The deterministic scripted baseline succeeds in the current kinematic task, but
the learned-policy artifacts do not demonstrate task success:

- P06 learned policies: 0% held-out task success.
- P07 System E demonstration retraining: 0% -> 0% held-out task success.
- P08 pilot methods A-E: 0% held-out task success.
- P10 full benchmark methods A-E: 0% mean held-out task success.

## Safety and deployment statement

These policy artifacts are preserved benchmark evidence only. They are not
validated for real robots, safety, reliability, or regulatory use.

## Reproduction

Use the public smoke reproduction command for software audit:

```text
uv sync --all-groups --locked
uv run --offline ora reproduce smoke
```

Use `uv run --offline ora reproduce pilot` for the heavier public P08 pilot
recipe. The full P10 250,000-episode benchmark is not rerun by default.
