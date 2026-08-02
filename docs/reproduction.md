# P12 reproduction tutorial

This tutorial defines the public reproduction path for OpenRoboAssure after
`v0.11.0`. It uses only public repository contents, generated synthetic data,
and the locked Python environment. It does not require paid data, paid services,
secret credentials, physical robots, or the private P09 seed package.

## Level 1: clean software smoke reproduction

Use a fresh clone:

```text
git clone https://github.com/taechasith/OpenRoboAssure.git
cd OpenRoboAssure
uv sync --all-groups --locked
uv run --offline ora reproduce smoke
```

Equivalent Make target after dependency sync:

```text
make reproduce-smoke
```

On Windows:

```text
make.bat reproduce-smoke
```

The smoke command writes:

- `reports/reproduction/clean-software/P12-CLEAN-SOFTWARE-REPRODUCTION.json`
- `reports/reproduction/clean-software/environment/doctor.json`
- `reports/reproduction/clean-software/licence_audit/latest.json`
- `reports/reproduction/clean-software/benchmarks/EXP-SIM-BASELINE-001-smoke.json`
- `reports/reproduction/clean-software/scenarios/EXP-SCENARIO-VALIDITY-001-smoke.json`
- `reports/reproduction/clean-software/benchmarks/ORA-BENCH-001-smoke.json`
- `reports/reproduction/clean-software/benchmarks/ORA-BENCH-001-smoke.github.md`

The certificate passes only if:

- Python satisfies the declared project range;
- the strict licence audit passes;
- the deterministic scripted baseline has 100% success on the smoke seeds;
- deterministic replay is 100%;
- scenario validity is at least 99.5% on the smoke sample;
- public P10 smoke benchmark execution completes without revealing hidden P09
  values;
- P09 protected hashes verify against frozen commit
  `f9654a4f3a871401d8d1677a409337d5485ced98`;
- no private P09 seed package is present or tracked in the clean clone.

The command is intentionally run as `uv run --offline` after dependency sync.
This verifies that execution does not need network access once dependencies and
assets are cached.

## Level 2: one-command public pilot reproduction

The public P08 pilot can be regenerated with:

```text
uv sync --all-groups --locked
uv run --offline ora reproduce pilot
```

Equivalent Make target:

```text
make reproduce-pilot
```

The pilot command uses the released P08 public seed and default pilot scope:

- methods A-E;
- seeds 11, 22, and 33;
- 2,048 CPU-bounded training steps per method/seed;
- 2,000 evaluation scenarios per method/seed;
- public root seed `20260801`.

The pilot command is heavier than the smoke certificate. It regenerates the
pilot report but does not rerun the P10 full benchmark.

## Level 3: full benchmark audit boundary

The P10 full benchmark result is already released as
`reports/benchmarks/ORA-BENCH-001.json`. P12 does not rerun all 250,000 hidden
evaluation episodes by default. The full benchmark audit boundary is:

- verify P09 protected hashes;
- verify public hidden/evaluation commitments;
- verify P10 result package hash;
- rerun the public smoke benchmark;
- optionally rerun a statistically meaningful public subset;
- preserve the all-zero learned-policy result as negative evidence.

The full released P10 report hash is:

```text
98db58c72436a2d626d91f209d8a505ffcaac9fe4a019f015276ffcedc367d0d
```

Public checksum references:

- `benchmarks/hidden_catalogue/ORA-BENCH-001.commitment.yaml`
- `benchmarks/evaluation_sets/ORA-BENCH-001.commitment.yaml`
- `benchmarks/specs/ORA-BENCH-001-protected-hashes.yaml`
- `reports/benchmarks/ORA-BENCH-001.github.md`

## Known failures and non-claims

P12 reproduction does not change the scientific result:

- all P10 learned-policy methods recorded 0% mean held-out task success;
- no method-superiority claim is supported;
- no learned-policy robustness claim is supported;
- no physical-robot validation was performed;
- no real-world safety, reliability, regulatory, sim-to-real, or
  cross-simulator dynamic-equivalence claim is supported.

`GATE-P12-REPRODUCTION` approved the clean software reproduction evidence as
sufficient for the v1.0 reproduction gate. P13 still controls final public
release claims and version 1.0 packaging.
