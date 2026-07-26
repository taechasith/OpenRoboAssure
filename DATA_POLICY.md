# OpenRoboAssure data policy

Status: **draft for `GATE-P00-CHARTER` approval**.

## Core rule

The v1.0 benchmark uses procedurally generated synthetic data by default. No
core training or evaluation data may require payment, a private account, a paid
subscription, a hosted API after setup, or a physical robot.

## Permitted core material

Core data and assets must have an explicit, reproducible provenance and a
licence compatible with redistribution and machine-learning use. The proposed
default allow-list is Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause, Zlib, ISC,
CC0-1.0, CC-BY-4.0, and PSF-2.0. Every imported robot model, texture, mesh, and dataset
will be recorded with its exact subdirectory or source licence, retrieval
method, checksum, and review status.

## Blocked core material

The core benchmark must reject non-commercial, no-derivatives, research-only,
academic-use-only, evaluation-only, proprietary, unknown-licence, private,
personal, biometric, scraped-without-permission, or ML-prohibited material.

## Asset handling

Task objects in the core benchmark will be code-generated primitives: boxes,
cylinders, capsules, pegs, sockets, trays, target zones, planes, and simple
convex combinations. Optional visual assets may be used only when their licence
and source are recorded, their terms permit use and redistribution, and the
state-based benchmark remains runnable without them.

Imported robot models must not be assumed licensed based on their host
repository's root licence. Their precise source subdirectory licence must pass
the later automated audit and human approval where required.

## Generated outputs

Original numeric benchmark outputs generated entirely by OpenRoboAssure are
proposed to use CC BY 4.0. Third-party code, meshes, textures, and documentation
remain under their original licences and will be listed in
`THIRD_PARTY_NOTICES.md` when introduced.

## Enforcement and exceptions

Phase P02 will implement an automated licence gate that rejects blocked or
unknown licences and writes a machine-readable audit report. Automated checks
are not legal advice. Any exception to this policy requires explicit human
approval, a documented rationale, and a recorded licence review before the
material enters the benchmark.

`pathspec` is the sole approved MPL-2.0 exception. It is a development-only
transitive dependency of the required mypy tool; it must not be copied or
modified, and its notice is recorded in `THIRD_PARTY_NOTICES.md`.
