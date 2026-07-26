# OpenRoboAssure

> **An AI-agent-driven, human-governed, fully simulation-based open-source pipeline for discovering limitations, generating scenarios, calibrating uncertainty, training policies, finding counterexamples, and producing reproducible assurance evidence for physical AI.**

**Document:** Simulation-First Master Build and Research Execution Guide  
**Project short name:** ORA  
**Repository name:** `openroboassure`  
**Guide version:** `2.0.0-plan`  
**Document date:** 2026-07-26  
**Validation target for v1.0:** Simulation only  
**Required external training data:** None  
**Required paid software or service:** None  
**Recommended code licence:** Apache License 2.0  
**Recommended original benchmark-data licence:** CC BY 4.0  

---

## 0. Status statement

This guide replaces the earlier hardware-first procedure.

OpenRoboAssure v1.0 will be validated entirely in simulation. It will not require a physical robot, paid dataset, paid simulator, proprietary cloud platform, or paid model API. All essential experiment data will be generated locally from deterministic simulation seeds.

The project may use permissively licensed open-source software and assets. Every dependency, robot model, texture, mesh, task asset, and imported dataset must pass an automated licence gate before entering the benchmark.

The v1.0 release may claim:

> OpenRoboAssure has been validated as a reproducible simulation pipeline for uncertainty modelling, scenario generation, policy robustness testing, counterexample discovery, coverage measurement, and sim-to-sim calibration across multiple robot-task configurations.

The v1.0 release must not claim:

- physical-robot validation;
- real-world safety certification;
- universal sim-to-real transfer;
- complete discovery of all possible failures;
- guaranteed policy safety;
- support for arbitrary robots without adapters;
- proof that simulation results equal real-world performance.

A future optional Phase P14 may introduce hardware validation after v1.0.

---

# 1. How to use this guide

This file is the authoritative execution plan until the repository contains a newer approved version.

The project is designed to be built primarily by an AI coding and research agent. A human project owner approves decisions that change the project’s main direction, benchmark definition, permitted public claims, licences, compute budget, or release status.

The AI agent must:

1. Work phase by phase.
2. Read the current repository state before starting any task.
3. Never skip a required human approval gate.
4. Produce evidence for every completion claim.
5. Update code, tests, documentation, experiment manifests, and the README together.
6. Push important solution milestones to GitHub only after required checks pass.
7. Record failed runs and negative results.
8. Never silently change a preregistered benchmark.
9. Never introduce paid, non-commercial, research-only, or unclear-licence data into the core benchmark.
10. Stop and request human approval when a decision changes project direction rather than implementation detail.

The human project owner must:

- approve the mission, scope, licence policy, benchmark design, compute ceiling, final claims, and releases;
- review changes to protected files;
- approve any exception to the free/open-data policy;
- decide whether results support the proposed research conclusions;
- accept negative results when the evidence does not support the original hypothesis.

---

# 2. Project identity

## 2.1 Name

# **OpenRoboAssure**

### Meaning

- **Open:** Inspectable, reproducible, freely usable, and based on permissive infrastructure.
- **Robo:** Focused on robots and embodied physical-AI systems.
- **Assure:** Produces structured evidence about limitations, uncertainty, robustness, coverage, and failure modes.

### Tagline

> **Generate. Challenge. Measure. Reproduce.**

### One-sentence description

OpenRoboAssure is an open-source orchestration and assurance layer that enables an AI agent to build simulation tasks, propose uncertainties, generate constrained scenarios, train and evaluate policies, calibrate source simulation against hidden target simulation, search for counterexamples, measure scenario coverage, and publish auditable results under explicit human governance.

## 2.2 Core research question

> Can an AI-agent-driven, human-governed, simulation-only pipeline discover important physical-AI limitations and improve robustness evaluation more efficiently and reproducibly than fixed or manually designed domain randomisation?

## 2.3 Secondary research questions

1. Can sensitivity analysis reduce the number of randomised variables without reducing failure discovery?
2. Can hidden-target sim-to-sim calibration recover useful uncertainty distributions from limited trajectories?
3. Can coverage-guided and adversarial scenario generation find failures more efficiently than uniform random sampling?
4. Can a common interface support comparable experiments across different robot embodiments and simulators?
5. Can an AI agent execute most of the pipeline while leaving directional decisions to a human?
6. Can the full benchmark be reproduced without paid data, paid APIs, or proprietary runtime dependencies?

## 2.4 Primary hypotheses

### H1: Failure-discovery hypothesis

The full OpenRoboAssure loop will discover a greater proportion of hidden failure regions per simulation episode than uniform random sampling and manually broad randomisation.

### H2: Robustness hypothesis

Policies trained using sensitivity-guided, calibration-guided, and counterexample-guided randomisation will have better worst-case performance on held-out scenario families than policies trained with no randomisation or fixed broad randomisation.

### H3: Calibration hypothesis

A distribution inferred from limited hidden-target trajectories will reduce source-target trajectory discrepancy and improve target-simulator task performance compared with an uncalibrated source simulator.

### H4: Coverage hypothesis

Coverage-guided scenario generation will reduce the number of untested scenario combinations compared with independent random sampling under the same evaluation budget.

### H5: Agentic reproducibility hypothesis

An AI agent using explicit schemas, protected files, evidence requirements, deterministic seeds, and human approval gates can execute most of the build and benchmark without silently changing the research question or evaluation protocol.

---

# 3. Version 1.0 scope

## 3.1 Included

OpenRoboAssure v1.0 will support:

- simulation-only execution;
- rigid-body robot manipulation;
- fixed-base robot arms;
- structured task definitions in YAML;
- procedural scene generation;
- procedural synthetic training and evaluation data;
- multiple robot embodiments;
- at least two simulator backends;
- a common observation and action contract;
- domain randomisation;
- uncertainty provenance tracking;
- Morris and Sobol sensitivity analysis;
- black-box range optimisation;
- hidden-target sim-to-sim calibration;
- constrained scenario generation;
- falsification and counterexample search;
- scenario coverage measurement;
- policy training and evaluation;
- fault injection;
- cross-simulator evaluation;
- reproducible experiment manifests;
- deterministic seed management;
- local experiment tracking;
- versioned benchmark datasets;
- machine-readable evidence records;
- human approval gates for project direction;
- public releases through GitHub.

## 3.2 Excluded

OpenRoboAssure v1.0 will not require or claim:

- physical robot control;
- real-world data collection;
- proprietary robot SDKs;
- paid cloud GPUs;
- paid LLM APIs;
- commercial simulation software;
- human teleoperation datasets;
- internet access during benchmark execution;
- deformable-object validation;
- fluid simulation validation;
- human-robot interaction validation;
- safety certification;
- real-time language-model control;
- universal automatic reward generation;
- formal proof of safety for arbitrary learned policies.

## 3.3 Reference robots

The core benchmark will use three embodiments:

1. **ORA-4A:** a project-owned generic four-axis tabletop arm created procedurally and released with the repository under Apache-2.0;
2. **Franka Panda:** imported only from a model package whose exact subdirectory licence is approved and recorded;
3. **Universal Robots UR5e:** imported only from a model package whose exact subdirectory licence is approved and recorded.

The benchmark must not depend on a Dobot MG400 mesh or model whose redistribution rights are unclear. ORA-4A may be kinematically inspired by compact four-axis industrial arms, but it must not copy proprietary geometry, branding, firmware, or confidential specifications.

## 3.4 Reference tasks

1. **Pick and Place**
   - detect or observe a rigid object;
   - grasp it;
   - move it into a target zone;
   - avoid collisions and drops.

2. **Precision Insertion**
   - align a peg-like object;
   - insert it into a matching opening;
   - respect force, collision, and pose-error limits.

3. **Push to Target**
   - contact an object;
   - push it into a target region;
   - avoid overshoot and workspace violations.

## 3.5 Learned policies

The benchmark should begin with state-based policies before introducing vision.

Required policy levels:

- **Level A:** deterministic scripted controller;
- **Level B:** state-based reinforcement-learning policy;
- **Level C:** optional image-based policy using fully synthetic rendered observations.

The core v1.0 claim must be achievable using Levels A and B. Level C is an extension, not a release blocker.

---

# 4. Free and open data policy

## 4.1 Definition of “free data” for this project

Core benchmark data must satisfy all of the following:

- no purchase is required;
- no paid subscription is required;
- no private account is required to reproduce the benchmark;
- no non-commercial restriction is allowed;
- no research-only restriction is allowed;
- no “evaluation only” restriction is allowed;
- no unclear or missing licence is allowed;
- no dependency on a hosted API is required after repository setup;
- data can be regenerated locally from code and fixed seeds whenever possible.

## 4.2 Default data source

The default and preferred source is **procedurally generated synthetic data**.

Every training sample, scenario, trajectory, image, annotation, and evaluation record should be reproducible from:

- a simulator version;
- robot and task configuration;
- asset manifest;
- scenario specification;
- random seed;
- source-code commit;
- policy version.

No external dataset is required for the core benchmark.

## 4.3 Permitted software licences

The default allow-list is:

- `Apache-2.0`
- `MIT`
- `BSD-2-Clause`
- `BSD-3-Clause`
- `Zlib`
- `ISC`
- `CC0-1.0` for assets and data
- `CC-BY-4.0` for data and documentation assets

A human may approve another permissive licence after review.

## 4.4 Blocked licences and terms

The automated gate must reject:

- `CC-BY-NC-*`
- `CC-BY-ND-*`
- research-only licences;
- academic-use-only licences;
- evaluation-only licences;
- licences forbidding redistribution when redistribution is required;
- datasets with no explicit licence;
- assets with unknown origin;
- scraped web images without explicit permission;
- proprietary simulator assets;
- content requiring a paid account to reproduce;
- personal or biometric data;
- data whose terms prohibit machine-learning use.

## 4.5 Approved core stack

Subject to version pinning and automated checks, the intended baseline is:

| Component | Purpose | Expected licence | Core or optional |
|---|---|---:|---:|
| MuJoCo | Primary physics simulator | Apache-2.0 | Core |
| MuJoCo Playground | Optional accelerated training patterns | Apache-2.0 | Optional |
| Gymnasium | Environment API | MIT | Core |
| Bullet/PyBullet | Secondary simulator backend | Zlib, file-specific exceptions checked | Core secondary |
| Scenic | Scenario specification | BSD-3-Clause | Core |
| VerifAI | Falsification and counterexample search | BSD-3-Clause | Core |
| SALib | Sensitivity analysis | MIT | Core |
| Optuna | Black-box optimisation | MIT | Core |
| pytest | Testing | MIT | Core |
| DVC | Data and experiment lineage | Apache-2.0 | Optional but recommended |
| MLflow | Local experiment tracking | Apache-2.0 | Optional but recommended |

The agent must verify actual repository licences at the pinned commit. This table is a plan, not legal advice.

## 4.6 Robot and asset policy

MuJoCo Menagerie may be used, but each robot subdirectory has its own licence. The agent must inspect and record the licence for every selected model.

Core approved model targets:

- Panda model with a permissive subdirectory licence;
- UR5e model with a permissive subdirectory licence;
- project-owned ORA-4A model.

For task objects, the core benchmark must use procedural primitives:

- boxes;
- cylinders;
- capsules;
- pegs;
- sockets;
- trays;
- target zones;
- planes;
- simple convex combinations created by project code.

This removes dependence on external object datasets.

## 4.7 Optional visual assets

Optional textures and HDRIs may use CC0 assets, such as Poly Haven assets, only when:

- the asset licence is recorded;
- download terms are respected;
- the benchmark does not scrape the website;
- the core state-based benchmark can run without them;
- checksums and source pages are recorded;
- redistribution follows the source terms.

## 4.8 Generated-data licence

Original numeric benchmark outputs generated entirely by OpenRoboAssure should be released under `CC-BY-4.0` unless the human owner approves `CC0-1.0`.

The following must remain under their original licences:

- imported robot meshes;
- imported textures;
- third-party code;
- third-party documentation excerpts.

The project must not claim ownership over third-party materials.

## 4.9 Required licence files

The repository must contain:

```text
LICENSE
DATA_LICENSE
THIRD_PARTY_NOTICES.md
DATA_POLICY.md
assets/manifest.yaml
dependencies/approved_licenses.yaml
dependencies/blocked_licenses.yaml
reports/licence_audit/latest.json
```

## 4.10 Asset manifest schema

```yaml
asset_id: panda_mjcf
name: Franka Panda MuJoCo model
kind: robot_model
source_repository: https://github.com/google-deepmind/mujoco_menagerie
source_commit: "<pinned commit>"
source_subdirectory: franka_emika_panda
spdx_license: BSD-3-Clause
redistributed: false
retrieval_method: scripted_git_checkout
sha256: "<hash>"
review_status: approved
reviewed_by: "<human or agent reviewer>"
review_date: "YYYY-MM-DD"
notes: "Use exact subdirectory licence; do not infer from repository root."
```

## 4.11 Automated licence gate

The command:

```bash
ora licence audit
```

must:

1. scan Python dependencies;
2. scan copied source files;
3. scan asset manifests;
4. detect missing SPDX identifiers;
5. compare licences against allow-list and block-list;
6. flag conflicting notices;
7. generate a machine-readable report;
8. fail CI when a blocked or unknown licence is present.

No milestone release may proceed while the licence audit is failing.

---

# 5. Governance

## 5.1 Roles

### Human Project Owner

The human project owner approves:

- mission and name;
- licence and data policy;
- reference robots and tasks;
- benchmark hypotheses;
- permitted public claims;
- compute budget;
- preregistered evaluation design;
- major architecture changes;
- release candidates;
- final interpretation.

### AI Lead Agent

The AI lead agent performs:

- repository scaffolding;
- implementation;
- unit and integration tests;
- simulator adapters;
- scenario generation;
- policy training;
- experiment scheduling;
- analysis scripts;
- documentation;
- Git branches and commits;
- draft pull requests;
- README updates;
- issue tracking;
- evidence generation.

### AI Review Agent

A separate review process should:

- inspect changes without relying on the lead agent’s explanation;
- run tests independently;
- check licence compliance;
- check benchmark leakage;
- inspect statistical assumptions;
- verify that README claims match evidence;
- identify hidden changes to protected files.

A separate model is helpful but not mandatory. A clean-context review run is sufficient for the MVP.

### Human Research Reviewer

May be the same person as the project owner during the MVP. Reviews:

- benchmark fairness;
- hidden failure catalogue design;
- statistical plan;
- exclusions;
- final research conclusions.

## 5.2 Decision classes

### Class A: Agent-autonomous

The AI agent may decide without human approval:

- internal module layout;
- naming of local variables;
- test implementation;
- refactoring that preserves public interfaces;
- documentation formatting;
- bug fixes that do not change benchmark meaning;
- optimisation that preserves outputs within tolerance;
- issue and branch creation.

### Class B: Human review before merge

Human review is required for:

- public API changes;
- schema changes;
- new dependencies;
- new assets;
- new simulator adapters;
- metric implementation;
- scenario ontology changes;
- release-note wording;
- README benchmark tables.

### Class C: Explicit human approval before execution

Human approval is required for:

- project mission changes;
- licence-policy exceptions;
- benchmark preregistration;
- changes to frozen evaluation sets;
- compute runs above the approved ceiling;
- publication claims;
- public release tags;
- starting the full benchmark;
- accepting or rejecting the final hypotheses.

### Class D: Prohibited without a new project charter

The agent must not:

- add real-robot control to v1.0;
- introduce a paid mandatory service;
- add personal data;
- scrape copyrighted images for training;
- use non-commercial datasets in the core benchmark;
- delete failed runs to improve reported performance;
- alter hidden failure definitions after inspecting method results;
- claim safety certification.

## 5.3 Approval record

All human approvals must be machine-readable.

```yaml
approval_id: GATE-P10-FULL-BENCHMARK
project_version: 0.8.0-rc1
decision: approved
approved_by: "<name>"
approved_at: "YYYY-MM-DDTHH:MM:SS+07:00"
scope:
  experiment_manifest: experiments/preregistered/ORA-BENCH-001.yaml
  max_simulation_evaluations: 2250000
  max_training_steps: "<number>"
  allowed_compute_profile: local_or_approved_free_compute
  permitted_claims:
    - simulation_benchmark_validated
expires_when:
  - protected_manifest_changes
  - evaluation_code_changes
  - hidden_catalogue_changes
notes: "Approval is invalid after any protected benchmark change."
```

Approvals live in:

```text
governance/approvals/
```

---

# 6. AI-agent operating protocol

## 6.1 Mandatory repository state files

```text
PROJECT_STATE.yaml
ROADMAP.md
CHANGELOG.md
README.md
AGENTS.md
governance/DECISIONS.md
governance/approvals/
reports/latest_status.json
```

## 6.2 `PROJECT_STATE.yaml`

```yaml
project: OpenRoboAssure
current_phase: P00
current_version: 0.0.0
status: planning
validation_level: none
latest_commit: null
active_branch: main
protected_benchmark_frozen: false
licence_audit: not_run
last_completed_gate: null
next_required_gate: GATE-P00-CHARTER
open_blockers: []
known_limitations:
  - simulation_only
  - no_physical_robot_validation
```

## 6.3 Agent loop

For every work item, the agent must:

1. Read `PROJECT_STATE.yaml`.
2. Read the current phase in this guide.
3. Inspect relevant code, tests, manifests, and open issues.
4. Check whether a human gate is required.
5. Create or reuse a dedicated branch.
6. Implement the smallest complete change.
7. Add or update tests.
8. Run formatting, lint, type checks, unit tests, and licence audit.
9. Run a minimal smoke experiment where relevant.
10. Update documentation and README status.
11. Save evidence under `reports/` or `artifacts/`.
12. Commit using the required format.
13. Prepare a pull request summary.
14. Merge only after required review.
15. Update `PROJECT_STATE.yaml`.

## 6.4 Completion claim format

The AI agent must not say “done” without this structure:

```text
Completed:
- <specific implementation>

Evidence:
- Tests: <commands and result>
- Experiment: <run ID and result>
- Licence audit: <result>
- Documentation: <files updated>
- Git: <branch and commit>

Remaining limitations:
- <known limitation>

Human decision required:
- <none or exact gate>
```

## 6.5 Uncertainty rule

When the agent is unsure about a physical range, licence, model capability, or research claim, it must label the uncertainty rather than invent certainty.

Allowed provenance labels:

- `measured_in_simulator`
- `source_code_default`
- `official_documentation`
- `published_literature`
- `project_assumption`
- `ai_proposal_unverified`
- `human_approved_prior`
- `unknown`

## 6.6 No benchmark leakage

The AI lead agent training the methods must not read the hidden failure catalogue during method development.

Use one of these controls:

- encrypted catalogue released only to the evaluator;
- separate private branch accessible only to the evaluation process;
- generated catalogue created after methods are frozen;
- separate clean-context evaluation agent.

The method-development code may know the catalogue schema but not the hidden trigger values.

---

# 7. GitHub and version policy

## 7.1 Branches

```text
main
phase/p00-charter
phase/p01-bootstrap
feature/<short-name>
experiment/<experiment-id>
fix/<short-name>
docs/<short-name>
release/v<version>
```

## 7.2 Commit format

```text
<type>(<scope>): <imperative summary>
```

Allowed types:

- `feat`
- `fix`
- `test`
- `docs`
- `refactor`
- `exp`
- `data`
- `licence`
- `ci`
- `release`

Examples:

```text
feat(scenarios): add constrained object-pose generator
test(licence): reject non-commercial assets
exp(calibration): add hidden-target posterior benchmark
docs(readme): publish v0.7 pilot results
```

## 7.3 Protected files

Changes require human review:

```text
MASTER_BUILD_GUIDE.md
README.md
LICENSE
DATA_LICENSE
DATA_POLICY.md
PROJECT_STATE.yaml
benchmarks/specs/
experiments/preregistered/
benchmarks/hidden_catalogue_schema.yaml
governance/approvals/
dependencies/approved_licenses.yaml
dependencies/blocked_licenses.yaml
```

After preregistration, the following become frozen:

```text
experiments/preregistered/ORA-BENCH-001.yaml
benchmarks/evaluation_sets/
benchmarks/hidden_catalogue/
analysis/statistical_plan.py
```

Any change invalidates the relevant approval and requires a new benchmark ID.

## 7.4 Semantic versions

- `0.1.0`: repository and governance foundation
- `0.2.0`: schemas, data policy, and licence gate
- `0.3.0`: primary simulator and first task
- `0.4.0`: multi-simulator adapters and robot library
- `0.5.0`: scenario and uncertainty engine
- `0.6.0`: training, sensitivity, and baseline systems
- `0.7.0`: calibration, falsification, and coverage loop
- `0.8.0`: pilot benchmark
- `0.9.0`: full benchmark and independent reproduction
- `1.0.0`: simulation-validated release

## 7.5 Mandatory GitHub checkpoints

Not every internal task requires a public push. The following important solution-creation phases do.

| Checkpoint | Required push | Version | Required README update |
|---|---:|---:|---|
| Repository and governance foundation | Yes | `v0.1.0` | Scope, status, licence |
| Free-data and licence-enforcement system | Yes | `v0.2.0` | Data policy and audit result |
| First working simulator task | Yes | `v0.3.0` | Installation and baseline demo |
| Multi-simulator and multi-robot layer | Yes | `v0.4.0` | Support matrix |
| Scenario and uncertainty engine | Yes | `v0.5.0` | Scenario examples and limits |
| Training and baseline methods | Yes | `v0.6.0` | Baseline metrics |
| Closed assurance loop | Yes | `v0.7.0` | Architecture and test evidence |
| Pilot benchmark | Yes | `v0.8.0` | Pilot tables and limitations |
| Full benchmark and reproduction | Yes | `v0.9.0` | Full results and reproduction |
| Stable release | Yes | `v1.0.0` | Final claims, citation, data links |

Every checkpoint must include:

- Git tag;
- GitHub release notes;
- updated README;
- updated changelog;
- updated project state;
- licence audit report;
- test report;
- reproducible command;
- known limitations;
- checksums for released data.

## 7.6 README status block

```markdown
## Project status

- Current version: `v0.0.0`
- Current phase: `P00`
- Validation level: `Not validated`
- Physical validation: `None`
- Required paid data: `None`
- Required paid services: `None`
- Licence audit: `Not run`
- Latest benchmark: `None`
- Known limitation: `Simulation results do not establish real-world safety or performance.`
```

---

# 8. Repository structure

```text
openroboassure/
├── README.md
├── MASTER_BUILD_GUIDE.md
├── AGENTS.md
├── PROJECT_STATE.yaml
├── ROADMAP.md
├── CHANGELOG.md
├── LICENSE
├── DATA_LICENSE
├── DATA_POLICY.md
├── THIRD_PARTY_NOTICES.md
├── CITATION.cff
├── pyproject.toml
├── uv.lock
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── licence-audit.yml
│   │   ├── benchmark-smoke.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── governance/
│   ├── DECISIONS.md
│   ├── approvals/
│   └── templates/
├── dependencies/
│   ├── approved_licenses.yaml
│   ├── blocked_licenses.yaml
│   └── pinned_sources.yaml
├── assets/
│   ├── manifest.yaml
│   ├── procedural/
│   ├── robots/
│   │   ├── ora_4a/
│   │   ├── panda/
│   │   └── ur5e/
│   └── optional_cc0/
├── src/openroboassure/
│   ├── cli.py
│   ├── config/
│   ├── contracts/
│   ├── provenance/
│   ├── licensing/
│   ├── simulators/
│   │   ├── base.py
│   │   ├── mujoco_adapter.py
│   │   └── pybullet_adapter.py
│   ├── robots/
│   ├── tasks/
│   ├── observations/
│   ├── actions/
│   ├── scenarios/
│   │   ├── ontology.py
│   │   ├── compiler.py
│   │   ├── scenic_adapter.py
│   │   ├── constraints.py
│   │   └── validity.py
│   ├── uncertainties/
│   │   ├── registry.py
│   │   ├── distributions.py
│   │   ├── sensitivity.py
│   │   └── optimiser.py
│   ├── policies/
│   │   ├── scripted/
│   │   ├── rl/
│   │   └── registry.py
│   ├── calibration/
│   │   ├── hidden_target.py
│   │   ├── discrepancy.py
│   │   └── posterior.py
│   ├── falsification/
│   │   ├── search.py
│   │   ├── verifai_adapter.py
│   │   └── replay.py
│   ├── coverage/
│   │   ├── bins.py
│   │   ├── interactions.py
│   │   └── reports.py
│   ├── faults/
│   │   ├── injectors.py
│   │   └── catalogue.py
│   ├── experiments/
│   │   ├── runner.py
│   │   ├── scheduler.py
│   │   ├── seeds.py
│   │   └── tracking.py
│   ├── analysis/
│   └── reporting/
├── configs/
│   ├── robots/
│   ├── tasks/
│   ├── scenarios/
│   ├── policies/
│   ├── methods/
│   └── compute/
├── benchmarks/
│   ├── specs/
│   ├── evaluation_sets/
│   ├── hidden_catalogue/
│   ├── hidden_catalogue_schema.yaml
│   └── expected_outputs/
├── experiments/
│   ├── drafts/
│   ├── preregistered/
│   ├── pilot/
│   └── full/
├── data/
│   ├── generated/
│   ├── manifests/
│   ├── checksums/
│   └── releases/
├── reports/
│   ├── licence_audit/
│   ├── tests/
│   ├── benchmarks/
│   ├── counterexamples/
│   └── coverage/
├── notebooks/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   ├── regression/
│   └── benchmark_smoke/
└── docs/
    ├── architecture/
    ├── tutorials/
    ├── methods/
    ├── benchmark/
    ├── limitations/
    └── reproducibility/
```

---

# 9. Technical architecture

## 9.1 Component flow

```text
Task specification
        ↓
Robot and simulator adapters
        ↓
Uncertainty registry
        ↓
Scenario compiler and validity checks
        ↓
Training distribution
        ↓
Policy training
        ↓
Held-out evaluation
        ↓
Sensitivity analysis
        ↓
Hidden-target calibration
        ↓
Falsification and counterexample search
        ↓
Coverage analysis
        ↓
Distribution revision
        ↓
Retraining
        ↓
Reproducible assurance report
```

## 9.2 Simulator adapter contract

```python
from typing import Protocol

class SimulatorAdapter(Protocol):
    def reset(self, scenario: "ScenarioSpec", seed: int) -> "Observation": ...
    def step(self, action: "Action") -> "StepResult": ...
    def get_state(self) -> "CanonicalState": ...
    def set_parameters(self, parameters: dict[str, float]) -> None: ...
    def render(self, camera: str | None = None) -> "Frame": ...
    def snapshot(self) -> bytes: ...
    def restore(self, snapshot: bytes) -> None: ...
    def close(self) -> None: ...
```

## 9.3 Canonical robot contract

```python
class RobotAdapter(Protocol):
    robot_id: str
    dof: int

    def action_space(self) -> "SpaceSpec": ...
    def observation_space(self) -> "SpaceSpec": ...
    def joint_limits(self) -> list[tuple[float, float]]: ...
    def default_pose(self) -> list[float]: ...
    def end_effector_pose(self, state: "CanonicalState") -> "Pose": ...
    def convert_action(self, action: "CanonicalAction") -> object: ...
```

## 9.4 Canonical action modes

Required:

- joint position delta;
- absolute joint target;
- end-effector pose delta;
- end-effector absolute pose;
- gripper open/close scalar.

Each task must declare which action modes are valid.

## 9.5 Canonical observation

```yaml
joint_position: [float]
joint_velocity: [float]
end_effector_pose:
  position: [x, y, z]
  quaternion: [w, x, y, z]
object_states:
  - id: object_0
    position: [x, y, z]
    quaternion: [w, x, y, z]
target_state: {}
contact_summary: {}
time: float
optional_images: {}
```

## 9.6 Scenario validity layers

A scenario passes only if it satisfies:

1. **Schema validity**
2. **Licence validity**
3. **Geometry validity**
4. **Kinematic reachability**
5. **Initial non-penetration**
6. **Task feasibility**
7. **Parameter bounds**
8. **No train-test leakage**
9. **Simulator compatibility**
10. **Deterministic regeneration**

## 9.7 Evidence record

```yaml
evidence_id: ORA-EVID-000001
claim: "Scenario generator produces valid pick-and-place scenes."
claim_type: software
source_commit: "<git sha>"
run_id: "<run id>"
configuration: configs/scenarios/pick_place_v1.yaml
seeds: [1, 2, 3, 4, 5]
metrics:
  generated: 10000
  valid: 9950
  validity_rate: 0.995
artifacts:
  - reports/scenarios/validity.json
  - reports/scenarios/examples/
limitations:
  - rigid_objects_only
review_status: pending
```

---

# 10. Data contracts

## 10.1 Task specification

```yaml
task_id: pick_place_v1
family: pick_place
version: 1
observation_mode: state
action_mode: ee_delta
horizon_steps: 300
control_hz: 20
success:
  all:
    - object_inside_target: true
    - object_height_final_m: "< 0.05"
    - collision_count: "<= 0"
termination:
  success: true
  time_limit: true
  invalid_state: true
metrics:
  - success
  - completion_steps
  - collision_count
  - object_drop
  - trajectory_length
  - minimum_clearance
```

## 10.2 Uncertainty specification

```yaml
uncertainty_id: pick_place_core_v1
parameters:
  - name: object_mass_kg
    category: physics
    distribution: uniform
    low: 0.05
    high: 0.50
    provenance: project_assumption
    trainable_range: true

  - name: surface_friction
    category: contact
    distribution: uniform
    low: 0.20
    high: 1.00
    provenance: project_assumption
    trainable_range: true

  - name: action_latency_steps
    category: control
    distribution: discrete_uniform
    low: 0
    high: 4
    provenance: project_assumption
    trainable_range: true

  - name: joint_encoder_bias_rad
    category: sensor
    distribution: normal
    mean: 0.0
    std: 0.01
    clip: [-0.03, 0.03]
    provenance: project_assumption
    trainable_range: true

constraints:
  - expression: "object_mass_kg > 0"
  - expression: "surface_friction >= 0"
```

## 10.3 Experiment manifest

```yaml
experiment_id: ORA-BENCH-001
status: draft
code_commit: "<git sha>"
container_digest: "<digest>"
robots:
  - ora_4a
  - panda
  - ur5e
tasks:
  - pick_place_v1
  - insertion_v1
  - push_v1
methods:
  - no_randomisation
  - manual_uniform
  - automatic_curriculum
  - sensitivity_guided
  - openroboassure_full
training_seeds: [11, 22, 33, 44, 55]
evaluation_seeds_file: benchmarks/evaluation_sets/ora_bench_001_seeds.txt
simulators:
  source: mujoco
  target:
    - pybullet
scenario_sets:
  - S0_nominal
  - S1_in_distribution
  - S2_boundary
  - S3_unseen_combinations
  - S4_out_of_distribution
  - S5_adversarial
  - S6_fault_injection
  - S7_cross_simulator
free_data_only: true
network_required_during_run: false
metrics_file: benchmarks/specs/metrics_v1.yaml
statistical_plan: analysis/statistical_plan.py
```

## 10.4 Counterexample record

```yaml
counterexample_id: CE-000042
method: openroboassure_full
robot: panda
task: insertion_v1
source_simulator: mujoco
seed: 883244
scenario_parameters:
  insertion_clearance_mm: 2.4
  action_latency_steps: 3
  joint_encoder_bias_rad: 0.018
failure:
  type: collision
  severity: critical
  reproducible_runs: 10
  reproduced_failures: 9
artifacts:
  trajectory: reports/counterexamples/CE-000042.parquet
  video: reports/counterexamples/CE-000042.mp4
  scenario: reports/counterexamples/CE-000042.yaml
```

---

# 11. Benchmark design

## 11.1 Compared systems

### System A: No randomisation

- default simulator parameters;
- fixed object pose distribution;
- no sensor or control noise beyond simulator defaults.

### System B: Manual broad uniform randomisation

- human-authored parameter list;
- broad independent uniform ranges;
- no sensitivity filtering;
- no calibration;
- no counterexample feedback.

### System C: Automatic curriculum randomisation

- begins with narrow ranges;
- expands boundaries when performance exceeds threshold;
- no hidden-target calibration;
- no explicit coverage objective.

### System D: Sensitivity-guided randomisation

- candidate variables screened using Morris analysis;
- high-impact variables analysed with Sobol indices;
- low-impact variables narrowed or removed;
- no counterexample feedback.

### System E: OpenRoboAssure full loop

- AI-proposed candidate uncertainty registry;
- validity checking;
- sensitivity screening;
- initial policy training;
- hidden-target calibration;
- falsification search;
- coverage gap analysis;
- randomisation revision;
- retraining;
- final held-out evaluation.

## 11.2 Scenario sets

### S0: Nominal

Default parameter values and ordinary starting configurations.

### S1: In-distribution

Samples drawn from the method’s declared training distribution.

### S2: Boundary

Samples near approved lower and upper limits.

Use quantile bands such as:

- bottom 5%;
- top 5%;
- exact declared boundaries where numerically stable.

### S3: Unseen combinations

Individual parameter values may have appeared during training, but selected combinations are held out.

Example:

```text
high object mass
+ low friction
+ action delay
+ workspace-edge placement
```

### S4: Out-of-distribution

Samples just beyond the training range but inside the benchmark’s global validity bounds.

### S5: Adversarial

Scenarios found using:

- VerifAI search;
- Optuna objective search;
- evolutionary search;
- Bayesian optimisation;
- coverage-directed search.

### S6: Fault injection

Required fault families:

- delayed observations;
- dropped observations;
- frozen observations;
- biased joint sensing;
- action latency;
- reduced actuator effectiveness;
- gripper command failure;
- object-state corruption;
- camera blackout for optional vision policy;
- simulation clock jitter;
- reset inconsistency detection.

### S7: Cross-simulator

Train in MuJoCo and evaluate an equivalent task in PyBullet without policy retraining.

Cross-simulator evaluation must acknowledge imperfect model equivalence. Report both:

- raw transfer performance;
- performance after canonical-state alignment only;
- no hidden task-specific tuning after evaluation begins.

## 11.3 Hidden-target calibration experiment

The target simulator behaves as an unknown world.

Procedure:

1. Select hidden target parameters in PyBullet or a modified MuJoCo target environment.
2. Keep exact target values inaccessible to the calibration method.
3. Generate a limited trajectory set from fixed excitation policies.
4. Provide only observations, actions, timestamps, and task outcomes.
5. Infer a distribution over source-simulator parameters.
6. Measure trajectory discrepancy before and after calibration.
7. Train policies in the calibrated source distribution.
8. Evaluate policies in the hidden target simulator.
9. Reveal true hidden parameters only after all predictions and results are frozen.

Metrics:

- normalised parameter estimation error;
- posterior coverage of hidden values;
- trajectory root-mean-square error;
- task-success improvement;
- number of target trajectories required;
- calibration runtime;
- robustness to observation noise.

## 11.4 Hidden failure catalogue

The benchmark evaluator creates failure regions unknown to the methods.

Example schema:

```yaml
catalogue_id: HFC-ORA-BENCH-001
failures:
  - id: HF-001
    task: pick_place_v1
    trigger:
      all:
        - surface_friction: "< 0.24"
        - object_mass_kg: "> 0.34"
    expected_failure: grasp_slip
    severity: major

  - id: HF-002
    task: insertion_v1
    trigger:
      all:
        - insertion_clearance_mm: "< 3.0"
        - action_latency_steps: ">= 3"
    expected_failure: collision
    severity: critical
```

Catalogue requirements:

- include single-variable, interaction, boundary, and fault-triggered failures;
- include decoy regions that should not fail;
- include multiple severities;
- remain hidden from method development;
- be generated before final evaluation;
- be cryptographically hashed;
- be revealed with the final result package.

## 11.5 Primary metrics

### Failure discovery

```text
hidden failure discovery rate
critical failure discovery rate
episodes per discovered failure
time to first critical failure
false-positive region rate
counterexample reproducibility
```

### Policy robustness

```text
mean success
median success
worst 10% success
conditional value at risk
collision rate
object-drop rate
completion steps
minimum clearance
```

### Scenario quality

```text
valid scenario rate
constraint satisfaction rate
duplicate rate
scenario diversity
coverage score
interaction coverage
invalid simulation rate
```

### Calibration

```text
trajectory discrepancy
parameter error
posterior coverage
target-simulator success
sample efficiency
```

### Reproducibility

```text
successful rerun rate
metric deviation across clean reruns
artifact checksum match
container build success
seed determinism rate
```

### Agentic execution

```text
percentage of phases completed without implementation intervention
number of required human gates
number of reverted agent changes
number of licence violations caught before merge
number of benchmark-protection violations caught
```

## 11.6 Pilot scale

```text
2 robots
2 tasks
5 methods
3 training seeds
2,000 evaluation scenarios per configuration
```

Nominal evaluation count:

```text
2 × 2 × 5 × 3 × 2,000 = 120,000 scenario evaluations
```

Recommended pilot robots:

- ORA-4A;
- Panda.

Recommended pilot tasks:

- Pick and Place;
- Push to Target.

## 11.7 Full scale

```text
3 robots
3 tasks
5 methods
5 training seeds
10,000 evaluation scenarios per configuration
```

Nominal evaluation count:

```text
3 × 3 × 5 × 5 × 10,000 = 2,250,000 scenario evaluations
```

Training episodes are counted separately and must be reported.

## 11.8 Statistical plan

Before the full run, preregister:

- primary outcomes;
- secondary outcomes;
- exclusion rules;
- seed counts;
- confidence intervals;
- multiple-comparison correction;
- effect-size reporting;
- handling of failed jobs;
- missing-data policy.

Recommended analysis:

- bootstrap 95% confidence intervals for success rates;
- paired comparisons using identical evaluation seeds;
- mixed-effects logistic regression for binary success;
- robot and task as grouping factors;
- Holm correction for planned pairwise comparisons;
- effect sizes in percentage points and odds ratios;
- worst-case and CVaR comparisons;
- survival-style analysis for episodes to first failure.

Do not rely only on p-values.

## 11.9 Software success versus research success

### Software success

The pipeline succeeds as software when:

- all required phases execute end to end;
- data can be generated from seeds;
- licences pass audit;
- methods run under one command;
- outputs are reproducible;
- failures are preserved;
- clean installation works.

### Research success

The hypotheses are supported only if the preregistered statistical comparisons support them.

A negative research result does not make the open-source software a failure. Negative results must be reported honestly.

---

# 12. Phase-by-phase execution plan

# Phase P00: Charter and direction

## Goal

Freeze the project mission, name, scope, governance, validation level, and permitted claims.

## AI agent tasks

1. Create the repository.
2. Add this guide as `MASTER_BUILD_GUIDE.md`.
3. Draft `README.md`.
4. Draft `PROJECT_STATE.yaml`.
5. Draft `ROADMAP.md`.
6. Draft `governance/DECISIONS.md`.
7. Draft Apache-2.0 code licence.
8. Draft CC BY 4.0 data licence.
9. Add initial risk and limitation statements.
10. Create GitHub issue labels and milestones.

## Human gate: `GATE-P00-CHARTER`

Approve:

- project name;
- simulation-only v1.0;
- no paid data requirement;
- licences;
- research questions;
- reference robots;
- reference tasks;
- prohibited claims.

## Deliverables

```text
README.md
MASTER_BUILD_GUIDE.md
PROJECT_STATE.yaml
ROADMAP.md
LICENSE
DATA_LICENSE
DATA_POLICY.md
governance/DECISIONS.md
```

## Completion criteria

- human approval file exists;
- protected files identified;
- README accurately states simulation-only status;
- repository is public or ready to be made public.

## Required GitHub push

**Yes**

Tag:

```text
v0.1.0
```

README update:

- project description;
- scope;
- licences;
- status;
- non-goals.

---

# Phase P01: Reproducible repository bootstrap

## Goal

Create a clean local development environment that can run without paid services.

## AI agent tasks

1. Configure Python 3.12.
2. Create `pyproject.toml`.
3. Pin dependencies with `uv.lock` or equivalent.
4. Add Ruff, mypy, pytest, and pre-commit.
5. Add Dockerfile with CPU-compatible mode.
6. Add optional GPU profile without making it mandatory.
7. Add GitHub Actions for lint, type check, tests, and package build.
8. Add deterministic random-seed utilities.
9. Add `ora doctor` command.
10. Add `make setup`, `make test`, and `make smoke`.

## Required tests

```bash
make setup
make lint
make typecheck
make test
make smoke
ora doctor
```

## Human gate

No direction gate unless the agent proposes a mandatory paid or proprietary dependency.

## Completion criteria

- clean CPU installation succeeds;
- no cloud account is required;
- smoke test runs offline after dependencies are installed;
- environment report is generated.

## Git handling

Push through normal pull request. No release tag required unless combined with P00.

---

# Phase P02: Free-data and licence enforcement

## Goal

Make it technically difficult to introduce restricted data or assets.

## AI agent tasks

1. Implement asset manifest schema.
2. Implement dependency licence scanner.
3. Add allow-list and block-list.
4. Scan Python package metadata.
5. Scan repository file headers where practical.
6. Require SPDX identifiers for every imported asset.
7. Add CI failure on unknown licence.
8. Create `ora licence audit`.
9. Create `ora asset add` to register source, commit, hash, and licence.
10. Add tests with known allowed and blocked examples.
11. Document that automated scanning is not legal advice.

## Human gate: `GATE-P02-DATA-POLICY`

Approve:

- licence allow-list;
- licence block-list;
- generated-data licence;
- third-party asset handling;
- exception procedure.

## Completion criteria

- non-commercial asset fixture is rejected;
- unknown licence fixture is rejected;
- permissive asset fixture is accepted;
- audit report is saved;
- README includes free-data statement.

## Required GitHub push

**Yes**

Tag:

```text
v0.2.0
```

README update:

- no paid data required;
- permitted licences;
- licence audit command;
- current audit status.

---

# Phase P03: Primary simulator and first working task

## Goal

Run one complete procedural task in MuJoCo using ORA-4A.

## AI agent tasks

1. Implement the simulator adapter interface.
2. Implement MuJoCo adapter.
3. Build ORA-4A procedurally.
4. Build procedural table, object, and target assets.
5. Implement Pick and Place v1.
6. Implement scripted controller.
7. Implement canonical observations and actions.
8. Add deterministic reset.
9. Add trajectory logging.
10. Add video rendering as optional output.
11. Add 1,000-seed baseline test.

## Experiment: `EXP-SIM-BASELINE-001`

Run:

- 1 robot;
- 1 task;
- scripted controller;
- 1,000 seeds;
- nominal and small perturbations.

Report:

- success rate;
- invalid reset rate;
- collision rate;
- deterministic replay rate;
- runtime.

## Human gate

Approve only if task success definition changes the project direction.

## Completion criteria

- same seed reproduces equivalent initial state;
- scripted policy succeeds in nominal conditions;
- every failure has a saved reason;
- no external dataset is used;
- licence audit passes.

## Required GitHub push

**Yes**

Tag:

```text
v0.3.0
```

README update:

- installation;
- first demo command;
- screenshot or generated video;
- baseline results;
- current limitations.

---

# Phase P04: Multi-simulator and multi-robot layer

## Goal

Support equivalent canonical tasks across MuJoCo and PyBullet and across three robot embodiments.

## AI agent tasks

1. Implement PyBullet adapter.
2. Import Panda model through asset manifest.
3. Import UR5e model through asset manifest.
4. Validate each model’s exact licence.
5. Implement robot-specific kinematic adapters.
6. Implement canonical task-space action conversion.
7. Add shared object and target geometry.
8. Build task-equivalence tests.
9. Measure simulator discrepancies under scripted excitation.
10. Document non-equivalence and known mismatches.

## Required tests

- reset validity across both simulators;
- joint-limit consistency;
- end-effector pose consistency within declared tolerance;
- object geometry consistency;
- action conversion tests;
- scripted task smoke tests;
- licence manifest completeness.

## Human gate: `GATE-P04-ROBOT-SET`

Approve:

- final robot set;
- simulator set;
- acceptable equivalence tolerances;
- any model licence exceptions.

## Completion criteria

- ORA-4A runs in both simulators;
- Panda and UR5e run at least in the primary simulator;
- cross-simulator evaluation interface exists;
- discrepancies are reported rather than hidden.

## Required GitHub push

**Yes**

Tag:

```text
v0.4.0
```

README update:

- robot support matrix;
- simulator support matrix;
- licence table;
- cross-simulator caveats.

---

# Phase P05: Scenario and uncertainty engine

## Goal

Generate valid, reproducible, constrained scenarios and uncertainty distributions.

## AI agent tasks

1. Implement uncertainty registry.
2. Implement distributions and correlations.
3. Implement scenario ontology.
4. Integrate Scenic or provide a compatible internal compiler.
5. Add hard and soft constraints.
6. Add reachability pre-check.
7. Add collision-free initialisation.
8. Add Latin hypercube and quasi-random sampling.
9. Add scenario deduplication.
10. Add scenario hash.
11. Add train/evaluation split protection.
12. Add scenario family labels S0-S7.
13. Generate procedural task-object variants.

## Required uncertainty categories

### Physics

- mass;
- inertia multiplier;
- friction;
- restitution;
- damping;
- actuator effectiveness.

### Geometry

- object size;
- object pose;
- target size;
- insertion clearance;
- centre-of-mass offset.

### Control

- latency;
- action noise;
- control rate;
- clipping;
- missed action.

### Sensors

- joint bias;
- joint noise;
- object-state noise;
- frame delay;
- missing observation.

### Environment

- workspace placement;
- surface orientation;
- gravity perturbation within declared benchmark bounds;
- external impulse.

## Experiment: `EXP-SCENARIO-VALIDITY-001`

Generate at least 100,000 scenarios.

Measure:

- valid rate;
- duplicate rate;
- constraint violation rate;
- deterministic regeneration;
- simulator execution rate;
- category coverage.

## Human gate: `GATE-P05-ONTOLOGY`

Approve:

- major uncertainty categories;
- global validity bounds;
- scenario-family definitions;
- variables excluded from v1.0.

## Completion criteria

- validity rate meets preregistered target;
- invalid scenarios are categorised;
- duplicate rate is reported;
- all scenario definitions are serialisable;
- no external data is needed.

## Required GitHub push

**Yes**

Tag:

```text
v0.5.0
```

README update:

- scenario examples;
- ontology summary;
- free synthetic-data generation command;
- validity results.

---

# Phase P06: Policy training, sensitivity, and baselines

## Goal

Train all baseline systems and identify influential uncertainty variables.

## AI agent tasks

1. Implement common policy interface.
2. Implement deterministic scripted baseline.
3. Implement state-based RL training.
4. Implement System A: no randomisation.
5. Implement System B: manual broad uniform.
6. Implement System C: automatic curriculum.
7. Integrate SALib.
8. Implement Morris screening.
9. Implement Sobol analysis.
10. Implement System D: sensitivity-guided randomisation.
11. Integrate Optuna for range and threshold searches.
12. Add local experiment tracking.
13. Add model registry and configuration hashes.
14. Enforce equal training budgets.

## Experiment: `EXP-SENS-001`

### Stage A: Morris screening

- use candidate parameter set;
- measure elementary effects on success and risk metrics;
- rank variables;
- identify variables with interaction or nonlinear effects.

### Stage B: Sobol analysis

- run on reduced parameter set;
- calculate first-order and total-order indices;
- include confidence intervals;
- compare across robots and tasks.

## Fairness rules

- identical training-step budgets;
- identical policy architectures where applicable;
- identical evaluation seeds;
- identical stopping rules;
- no method-specific evaluation tuning;
- all failed training seeds retained.

## Human gate: `GATE-P06-BASELINES`

Approve:

- baseline definitions;
- training budget;
- policy architecture constraints;
- sensitivity thresholds;
- primary metrics.

## Completion criteria

- Systems A-D train end to end;
- sensitivity reports generated;
- equal-budget check passes;
- model and data provenance recorded;
- README results are clearly labelled preliminary.

## Required GitHub push

**Yes**

Tag:

```text
v0.6.0
```

README update:

- baseline methods;
- preliminary metrics;
- sensitivity examples;
- exact reproduction commands.

---

# Phase P07: Calibration, falsification, coverage, and full loop

## Goal

Implement System E, the complete OpenRoboAssure loop.

## AI agent tasks

### Calibration

1. Create hidden target generator.
2. Create excitation policies.
3. Generate limited target trajectories.
4. Implement discrepancy metrics.
5. Implement posterior or approximate distribution fitting.
6. Evaluate parameter recovery.
7. Evaluate target-simulator policy transfer.

### Falsification

8. Integrate VerifAI or compatible search API.
9. Define failure predicates.
10. Implement adversarial parameter search.
11. Save reproducible counterexamples.
12. Replay counterexamples across seeds.

### Coverage

13. Implement one-way parameter-bin coverage.
14. Implement pairwise interaction coverage.
15. Implement scenario-family coverage.
16. Implement coverage-gap queue.
17. Generate scenarios targeting gaps.

### Closed loop

18. Revise randomisation based on sensitivity, calibration, failures, and gaps.
19. Retrain policy.
20. Compare before and after.
21. Generate an assurance report.

## Required closed-loop record

```yaml
iteration: 2
input_policy: policy_001
sensitivity_findings: reports/sensitivity/run_001.json
calibration_findings: reports/calibration/run_001.json
counterexamples:
  - CE-000001
  - CE-000002
coverage_gaps:
  - low_friction__high_mass
  - latency__small_clearance
changes:
  - parameter: surface_friction
    old_range: [0.4, 0.9]
    new_range: [0.2, 0.9]
    reason: counterexample_and_hidden_target_support
  - parameter: object_colour
    action: removed
    reason: low_sensitivity_state_based_task
output_policy: policy_002
```

## Human gate

No direction gate for ordinary loop iterations. Human review required if the agent adds a new uncertainty category, changes task success, or changes protected metrics.

## Completion criteria

- System E executes end to end;
- every distribution change has evidence;
- counterexamples replay successfully;
- coverage gaps are measurable;
- calibration improves at least one declared discrepancy metric or reports a negative result;
- failed iterations remain visible.

## Required GitHub push

**Yes**

Tag:

```text
v0.7.0
```

README update:

- closed-loop architecture;
- calibration demo;
- counterexample examples;
- coverage report;
- limitations.

---

# Phase P08: Pilot benchmark

## Goal

Run a smaller preregistered benchmark to detect implementation and design problems before the full experiment.

## AI agent tasks

1. Draft `ORA-PILOT-001.yaml`.
2. Freeze pilot evaluation seeds.
3. Create pilot hidden failure catalogue.
4. Hash protected files.
5. Estimate compute and storage.
6. Run all five systems.
7. Preserve failed runs.
8. Generate statistical summary.
9. Identify benchmark defects.
10. Propose changes for the full benchmark.

## Human gate: `GATE-P08-PILOT`

Approve:

- pilot robot and task set;
- method definitions;
- seed count;
- evaluation count;
- hidden-catalogue procedure;
- compute ceiling.

## Pilot acceptance criteria

The pilot is operationally successful when:

- all methods run for all approved configurations;
- at least 95% of scheduled jobs terminate with a classified outcome;
- licence audit passes;
- no evaluation leakage is detected;
- generated data can be regenerated;
- result package can be reproduced on a clean environment;
- benchmark flaws are documented.

The pilot does not need to support the research hypotheses.

## Required GitHub push

**Yes**

Tag:

```text
v0.8.0
```

README update:

- pilot protocol;
- result tables;
- failed-run count;
- benchmark changes planned;
- clear “pilot only” label.

---

# Phase P09: Full benchmark preregistration

## Goal

Freeze the final research design before full evaluation.

## AI agent tasks

1. Draft `experiments/preregistered/ORA-BENCH-001.yaml`.
2. Freeze robot, task, method, seed, and metric definitions.
3. Freeze statistical plan.
4. Generate hidden evaluation seeds.
5. Generate hidden failure catalogue through isolated evaluator.
6. Hash all protected benchmark files.
7. Create compute plan.
8. Create storage plan.
9. Create failure-recovery plan.
10. Create analysis validation tests.

## Human gate: `GATE-P09-PREREGISTRATION`

Approve:

- final hypotheses;
- primary and secondary outcomes;
- method definitions;
- robots and tasks;
- training budgets;
- evaluation budgets;
- statistical plan;
- exclusion policy;
- compute ceiling;
- final permitted claims.

## Completion criteria

- approval file committed;
- protected-file hashes committed;
- evaluator isolation verified;
- no results from the full evaluation exist before approval;
- benchmark ID is fixed.

## Git handling

Push protected preregistration commit to GitHub. A release tag is optional; do not publish hidden trigger values before evaluation.

---

# Phase P10: Full benchmark execution

## Goal

Execute the complete benchmark without changing the frozen design.

## AI agent tasks

1. Verify protected-file hashes.
2. Verify container digest.
3. Verify licence audit.
4. Run training jobs.
5. Run evaluation jobs.
6. Retry infrastructure failures according to preregistered policy.
7. Never retry legitimate poor-performance results merely to improve scores.
8. Save all logs and manifests.
9. Generate interim integrity reports without inspecting hidden results for tuning.
10. Run final statistical analysis.
11. Reveal hidden catalogue.
12. Calculate failure-discovery metrics.
13. Generate benchmark tables.
14. Generate machine-readable result package.

## Human involvement during execution

The human does not need to supervise each run. Human action is needed only when:

- compute exceeds the approved ceiling;
- a protected file mismatch occurs;
- data corruption threatens benchmark integrity;
- an unplanned methodological decision is required;
- the agent proposes excluding results outside the preregistered rules.

## Stop rules

Stop the benchmark when:

- protected hashes do not match;
- licence audit fails;
- evaluation leakage is detected;
- more than the preregistered infrastructure-failure threshold occurs;
- generated scenarios violate global validity bounds;
- storage corruption prevents provenance recovery;
- the agent changes a protected benchmark file.

## Completion criteria

- all scheduled jobs have completed or classified failures;
- every result maps to code, configuration, seed, and environment;
- hidden catalogue has been revealed and archived;
- statistical analysis is reproducible;
- no unapproved exclusion is applied.

## Git handling

Do not merge final claims until review. Save results on `experiment/ORA-BENCH-001` and create a release candidate branch.

---

# Phase P11: Ablation and limitation analysis

## Goal

Determine which parts of OpenRoboAssure create value and where it fails.

## Required ablations

1. Remove sensitivity analysis.
2. Remove hidden-target calibration.
3. Remove falsification search.
4. Remove coverage guidance.
5. Remove AI-generated uncertainty proposals.
6. Replace correlated distributions with independent distributions.
7. Reduce target trajectories.
8. Reduce evaluation budget.
9. Use only one simulator.
10. Remove counterexample replay.

## AI agent tasks

- run preregistered or clearly post-hoc ablations;
- label exploratory analyses as exploratory;
- compare compute cost and benefit;
- identify failure modes of the pipeline itself;
- produce a limitation taxonomy.

## Human gate: `GATE-P11-INTERPRETATION`

Approve:

- distinction between confirmatory and exploratory results;
- final interpretation;
- claims supported by evidence;
- claims rejected by evidence.

## Completion criteria

- each major component has an ablation or documented reason for omission;
- negative findings are included;
- limitations are prominent in README and paper draft.

---

# Phase P12: Independent reproduction

## Goal

Show that a clean agent or external contributor can reproduce the pipeline without hidden local state or paid resources.

## Reproduction levels

### Level 1: Clean software reproduction

- new environment;
- fresh repository clone;
- CPU smoke test;
- no private files;
- no paid services.

### Level 2: Independent pilot reproduction

- separate agent or contributor;
- regenerated pilot data;
- same public seeds;
- independent analysis run;
- metric comparison within tolerance.

### Level 3: Full benchmark audit

- verify hashes;
- verify manifests;
- rerun a statistically meaningful subset;
- check released data;
- check licence notices;
- verify result tables from raw records.

## AI agent tasks

1. Create reproduction tutorial.
2. Create one-command smoke reproduction.
3. Create one-command pilot reproduction.
4. Export exact environment lock.
5. Test on clean Linux environment.
6. Test without internet after dependencies and assets are cached.
7. Generate reproduction certificate.

## Human gate: `GATE-P12-REPRODUCTION`

Approve whether reproduction evidence is sufficient for v1.0.

## Completion criteria

- independent run succeeds;
- no paid data is requested;
- no secret credentials are required;
- public scripts retrieve or generate all required assets;
- reported metrics regenerate within declared tolerance.

## Required GitHub push

**Yes**

Tag:

```text
v0.9.0
```

README update:

- full benchmark results;
- reproduction status;
- exact commands;
- data and checksum references;
- known failures.

---

# Phase P13: Version 1.0 release

## Goal

Publish a stable, reproducible, simulation-validated open-source release.

## Required release package

```text
source code
licence files
third-party notices
asset manifests
container recipe
locked dependencies
benchmark specifications
public evaluation seeds
revealed hidden catalogue
raw or minimally processed numeric results
analysis scripts
result tables
counterexample records
coverage reports
reproduction guide
model cards
benchmark card
limitations statement
CITATION.cff
```

## Allowed release claims

- simulation-validated;
- open-source;
- no paid training dataset required;
- procedurally generated benchmark data;
- multi-robot simulation benchmark;
- multi-simulator evaluation;
- reproducible counterexample search;
- scenario coverage measurement;
- hidden-target sim-to-sim calibration.

## Prohibited release claims

- real-world validated;
- physically safe;
- certified;
- universal;
- complete failure coverage;
- proven sim-to-real performance;
- guaranteed robust.

## Human gate: `GATE-P13-RELEASE`

Approve:

- final version;
- final README;
- final benchmark tables;
- permitted claims;
- licences and notices;
- public release of data;
- publication or preprint submission.

## Required GitHub push

**Yes**

Tag:

```text
v1.0.0
```

README update:

- final status badge;
- benchmark summary;
- installation;
- reproduction;
- citation;
- licence and data policy;
- prominent simulation-only limitation.

---

# Optional Phase P14: Post-v1.0 physical validation

This phase is outside the v1.0 definition of done.

It may introduce:

- one physical robot;
- one bounded task;
- read-only calibration first;
- deterministic safety supervisor;
- human approval for every hardware stage;
- comparison between simulation predictions and real outcomes.

Starting P14 requires a new safety charter, new governance approvals, and a separate guide.

---

# 13. Command-line interface

Minimum required commands:

```bash
ora doctor
ora licence audit
ora asset add
ora robot list
ora task list
ora scenario validate
ora scenario generate
ora policy train
ora policy evaluate
ora sensitivity morris
ora sensitivity sobol
ora calibrate hidden-target
ora falsify search
ora falsify replay
ora coverage report
ora benchmark pilot
ora benchmark full
ora report build
ora reproduce smoke
ora reproduce pilot
```

Example end-to-end pilot:

```bash
ora licence audit
ora scenario validate --config configs/scenarios/pilot.yaml
ora benchmark pilot --manifest experiments/preregistered/ORA-PILOT-001.yaml
ora report build --run ORA-PILOT-001
```

Example full benchmark:

```bash
ora benchmark full \
  --manifest experiments/preregistered/ORA-BENCH-001.yaml \
  --require-approval GATE-P09-PREREGISTRATION \
  --verify-protected-hashes
```

---

# 14. Testing requirements

## 14.1 Unit tests

Cover:

- schemas;
- distributions;
- constraints;
- hashes;
- licence parsing;
- action conversion;
- metric calculations;
- seed generation;
- coverage bins;
- discrepancy functions.

## 14.2 Property tests

Examples:

- generated mass is always positive;
- joint targets remain inside declared limits;
- scenario serialisation round-trips;
- identical seed produces identical scenario hash;
- blocked licences always fail;
- evaluation seeds never appear in training manifests.

## 14.3 Integration tests

- MuJoCo complete episode;
- PyBullet complete episode;
- scenario generation to execution;
- training to evaluation;
- calibration to target evaluation;
- falsification to replay;
- coverage report generation;
- licence audit in CI.

## 14.4 Regression tests

Maintain fixed small scenarios with expected tolerances.

Do not require bitwise-identical floating-point trajectories across all hardware. Declare numeric tolerances.

## 14.5 Benchmark smoke tests

Every pull request must run a small configuration:

```text
1 robot
1 task
2 methods
2 seeds
20 scenarios
```

The smoke test verifies orchestration, not research performance.

---

# 15. Compute and storage policy

## 15.1 No paid-compute requirement

The project must support a CPU smoke path and a reduced pilot path that can run on a normal workstation.

GPU acceleration may be supported but not mandatory for installation or basic reproduction.

## 15.2 Compute profiles

```yaml
profiles:
  cpu_smoke:
    required_gpu: false
    max_parallel_jobs: 2

  local_single_gpu:
    required_gpu: true
    max_parallel_jobs: 8

  approved_cluster:
    required_gpu: optional
    human_gate_required: true
```

## 15.3 Pre-run estimate

Before a large run, the agent must estimate:

- total episodes;
- total environment steps;
- wall-clock range;
- peak memory;
- expected storage;
- video-storage cost;
- retry allowance.

The agent must not start a run above the approved ceiling.

## 15.4 Storage controls

Save for every run:

- manifest;
- metrics;
- logs;
- policy checksum;
- environment checksum;
- selected trajectories;
- all counterexamples;
- all failures.

Do not save video for every ordinary successful episode. Use deterministic regeneration plus sampled videos to control storage.

---

# 16. README structure

The README should follow this order:

1. Project name and one-sentence description
2. Simulation-only warning
3. Current status
4. What problem it solves
5. What it does not prove
6. Quick start
7. Free-data and licence policy
8. Architecture
9. Supported simulators, robots, and tasks
10. Benchmark methods
11. Latest results
12. Reproduction commands
13. Repository structure
14. Governance and human gates
15. Known limitations
16. Roadmap
17. Citation
18. Licences

Required warning near the top:

```markdown
> OpenRoboAssure v1.0 is validated only in simulation. Its results do not establish physical-robot safety, real-world reliability, or regulatory compliance.
```

---

# 17. `AGENTS.md` minimum content

```markdown
# Agent rules

1. Read `PROJECT_STATE.yaml` before acting.
2. Work only in the current approved phase.
3. Do not modify protected files without required review.
4. Do not use paid, non-commercial, research-only, or unknown-licence data.
5. Run `ora licence audit` before every milestone merge.
6. Never expose hidden failure values to method-development code.
7. Preserve failed runs and negative results.
8. Update README for every milestone release.
9. Do not claim real-world validation.
10. Stop when a human directional decision is required.
```

---

# 18. Initial GitHub issues

## Milestone v0.1.0

1. Create repository charter.
2. Add governance model.
3. Add licence and data licence.
4. Add project-state schema.
5. Add README status block.

## Milestone v0.2.0

6. Add asset manifest schema.
7. Implement licence allow-list.
8. Implement blocked-licence tests.
9. Implement `ora licence audit`.
10. Add third-party notice generator.

## Milestone v0.3.0

11. Implement MuJoCo adapter.
12. Create ORA-4A model.
13. Create procedural pick-and-place task.
14. Add scripted policy.
15. Add deterministic replay.

## Milestone v0.4.0

16. Implement PyBullet adapter.
17. Add Panda asset manifest.
18. Add UR5e asset manifest.
19. Add canonical action mapping.
20. Add simulator discrepancy report.

## Milestone v0.5.0

21. Implement uncertainty registry.
22. Implement scenario ontology.
23. Integrate Scenic.
24. Add validity checks.
25. Add train-test split protection.

## Milestone v0.6.0

26. Implement policy registry.
27. Implement Systems A-C.
28. Integrate SALib.
29. Implement System D.
30. Add equal-budget checker.

## Milestone v0.7.0

31. Implement hidden-target calibration.
32. Integrate VerifAI.
33. Implement counterexample replay.
34. Implement coverage report.
35. Implement System E closed loop.

## Milestone v0.8.0

36. Preregister pilot.
37. Generate pilot hidden catalogue.
38. Run pilot.
39. Publish pilot report.
40. Fix benchmark defects.

## Milestone v0.9.0

41. Preregister full benchmark.
42. Run full benchmark.
43. Run ablations.
44. Complete independent reproduction.
45. Publish raw numeric results.

## Milestone v1.0.0

46. Finalise benchmark card.
47. Finalise model cards.
48. Finalise limitations.
49. Final licence audit.
50. Publish stable release.

---

# 19. Definition of done

OpenRoboAssure v1.0 is complete only when all conditions below are true.

## Governance

- human approvals exist for all directional gates;
- protected benchmark files are hashed;
- public claims match approved wording.

## Open and free operation

- no paid dataset is required;
- no paid API is required;
- no proprietary simulator is required;
- CPU smoke test works;
- all third-party licences are recorded;
- blocked and unknown licences fail CI.

## Software

- at least two simulators are supported;
- at least three robot embodiments are represented;
- at least three tasks are represented;
- Systems A-E run through one interface;
- scenario generation is deterministic from seeds;
- failures are reproducible;
- full reports are machine-readable.

## Experiments

- pilot benchmark completed;
- full benchmark completed or transparently terminated under stop rules;
- hidden catalogue revealed after evaluation;
- statistical plan executed;
- ablations completed;
- failed runs included;
- negative findings included.

## Reproducibility

- clean installation succeeds;
- smoke reproduction succeeds;
- pilot reproduction succeeds independently;
- released data has checksums;
- tables regenerate from raw results.

## Documentation

- README is current;
- changelog is current;
- limitations are prominent;
- citation file exists;
- data and code licences are clear;
- no real-world safety claim appears.

## Release

- `v1.0.0` tag exists;
- GitHub release exists;
- release package is archived;
- benchmark data is publicly accessible under the declared licence;
- third-party notices are included.

---

# 20. Final human responsibilities

The human does not need to operate a robot or supervise simulation episodes.

The human must approve:

1. **P00:** project direction and licences;
2. **P02:** free-data and asset policy;
3. **P04:** robot and simulator set;
4. **P05:** scenario ontology and validity bounds;
5. **P06:** baseline definitions and compute budget;
6. **P08:** pilot design;
7. **P09:** final preregistration;
8. **P11:** interpretation of results;
9. **P12:** reproduction sufficiency;
10. **P13:** public release and claims.

The human should not intervene in individual technical choices unless they affect project direction, benchmark fairness, licence compliance, or public interpretation.

The human’s final decision must be one of:

```text
A. Simulation benchmark validated for the documented scope.
B. Pipeline operational, but research conclusions remain preliminary.
C. Not validated because reproducibility, integrity, or evidence requirements were not met.
```

---

# 21. Source and licence references for implementation review

The agent must re-check these sources at the pinned commit before implementation.

- MuJoCo repository and licence: `https://github.com/google-deepmind/mujoco`
- MuJoCo Playground: `https://github.com/google-deepmind/mujoco_playground`
- MuJoCo Menagerie: `https://github.com/google-deepmind/mujoco_menagerie`
- Bullet Physics: `https://github.com/bulletphysics/bullet3`
- Gymnasium: `https://github.com/Farama-Foundation/Gymnasium`
- Scenic documentation: `https://docs.scenic-lang.org/`
- VerifAI: `https://github.com/BerkeleyLearnVerify/VerifAI`
- SALib: `https://salib.readthedocs.io/`
- Optuna: `https://github.com/optuna/optuna`
- DVC: `https://github.com/iterative/dvc`
- MLflow: `https://github.com/mlflow/mlflow`
- Optional CC0 visual assets: `https://polyhaven.com/license`

These references do not replace the repository’s own licence files. The exact licence of every pinned version and asset must be recorded in the project manifest.

---

# 22. Immediate next action

The AI agent should begin with:

```text
Phase P00: Charter and direction
```

First branch:

```bash
git checkout -b phase/p00-charter
```

First deliverable set:

```text
README.md
MASTER_BUILD_GUIDE.md
PROJECT_STATE.yaml
ROADMAP.md
LICENSE
DATA_LICENSE
DATA_POLICY.md
governance/DECISIONS.md
```

The first human approval requested must be:

```text
GATE-P00-CHARTER
```

No implementation beyond repository bootstrap should begin until that gate is approved.
