---
doc: spec
status: draft
---

# AegisOS — Technical Spec

## How This Works, In Plain Language
AegisOS is a verification tool for AI-assisted development. Instead of trusting a coding agent’s claim that a task is “done,” the user submits a task to the app, selects a repository, and the system runs the relevant automated checks against that code. The app then shows whether the task passed, failed, or could not be verified because execution failed or evidence was incomplete.

This is a small proof of concept, not a general autonomous coding platform. The architecture deliberately keeps the workflow simple: one dashboard, one backend workflow, one execution sandbox, and a small demo repo so the system can prove its value without adding large infrastructure or broad feature scope.

## The Core Journey Through the System
The PRD’s core journey is implemented as a short, direct pipeline:

1. The user opens the AegisOS dashboard and signs in.
2. The user selects an existing demo repository or a registered repository from the local workspace.
3. The user submits a task with a clear title, issue text, and acceptance criteria.
4. The backend stores the task and begins the workflow.
5. The workflow analyzes the repository context and creates a bounded patch proposal.
6. The execution layer runs the relevant checks in the sandbox.
7. The evaluator compares the actual execution evidence to the task requirements and decides whether the result is verified, failed, or inconclusive.
8. The dashboard shows the final status and the meaningful output from the test run.
9. The user can inspect the run record, task trace, and prior history.

PRD ref: `prd.md > The Core Journey`.

## Stack
The technical plan uses the existing AegisOS stack already present in the repo:

- Python backend with FastAPI
- SQLAlchemy for data models and persistence
- SQLite for local project data and task history
- Pydantic models / schema validation
- Docker-based sandbox execution for isolated Python test runs
- React + TypeScript + Vite for the frontend
- Local workspace repository registration for demo repos

This is a deliberately minimal stack for a proof of concept. The stack already exists in the project and is sufficient for a reliable verification loop without adding extra services or deployment complexity.

Documentation links:
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Docker: https://docs.docker.com/
- React: https://react.dev/
- Vite: https://vite.dev/

## Where It Runs and How Someone Tries It
The project runs locally in the current workspace and does not require a production deployment for the hackathon proof of concept.

Runtime model:
- frontend runs in the browser on the local dev server
- backend runs as a local FastAPI process
- SQLite is used for local app data
- sandbox execution uses Docker for isolated validation

The required demo path:
1. start the backend and web app locally
2. sign in with the local demo account or register a workspace user
3. select a demo repository
4. submit a task for verification
5. review the status and execution output
6. demonstrate one pass run and one controlled failing run

Deployment is optional and not a substitute for the required demo video or repository. For this PoC, local execution is the simplest and most reliable option.

## Look and Feel
The existing dashboard already sets the right direction: technical, trustworthy, and engineering-oriented. The UI should remain concise, readable, and clearly structured around task outcomes and evidence rather than broad visual polish.

The interface should:
- emphasize status and evidence over marketing language
- keep the task and run history easy to scan
- use strong labels for PASS, FAILED, and ERROR/INCONCLUSIVE
- avoid visual clutter that could hide the key result

This matches the product direction already established in the PRD and scope documents.

## Components

### Frontend dashboard
The dashboard is the user-facing workspace for task submission, repository selection, and result review. It presents the current workspace state and task history, and it makes the execution status readable without hiding the underlying evidence.

PRD ref: `prd.md > Screens and Layout`, `prd.md > Features and Behavior`.

### Task submission and repository selection
This component captures the user’s task input and links it to a repository that is already registered in the system. It supports the main verification workflow and is the entry point for the task lifecycle.

PRD ref: `prd.md > Task Submission and Repository Selection`.

### Task workflow engine
The backend workflow handles the lifecycle of a task: accept, analyze repository context, prepare a bounded patch proposal, run tests, evaluate evidence, and record status. It does not treat an AI-generated claim as proof; it waits for execution evidence.

PRD ref: `prd.md > Execution Workflow`, `prd.md > Status Outcomes`.

### Sandbox runner
The sandbox runner is responsible for executing repository checks in a controlled container. It applies the patch to a disposable workspace, executes Python tests, captures stdout/stderr, and reports the final execution result without exposing the full source in the stored output.

PRD ref: `prd.md > Execution Workflow`, `prd.md > Evidence Display`.

### Evaluator
The evaluator interprets the real execution result, rejects unsafe or empty patch structures, and determines whether the task is VERIFIED, FAILED, or INCONCLUSIVE. Its logic is intentionally conservative and blocks false positives.

PRD ref: `prd.md > Status Outcomes`, `prd.md > Evidence Display`.

### Task history and trace
Task detail and event history provide transparency for the end user. This is the mechanism that exposes why a task passed, failed, or lacked sufficient evidence.

PRD ref: `prd.md > Historical Context`.

## Data Model
The existing data model already contains the relevant entities for the PoC:

- User
- Repository
- Task
- WorkflowEvent
- AgentStep
- TestResult
- Evaluation

These are sufficient for the minimal working flow. In particular:

- Task stores the submitted issue, acceptance criteria, repo choice, status, verdict, and timing metadata.
- WorkflowEvent tracks the task lifecycle and user-visible progress states.
- AgentStep records the steps taken by the workflow and any role-specific reasoning summaries.
- TestResult records the actual command execution, exit code, and raw output.
- Evaluation stores the final verdict and reasoning based on the evidence.

This model is appropriate for a small PoC because it preserves the evidence trail without adding a large, separate analytics pipeline.

## File Structure
The project already has the necessary file layout for the planned workflow:

```text
project/
├── apps/
│   └── web/
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
├── backend/
│   ├── app/
│   ├── tests/
│   └── alembic/
├── devpost/
│   ├── learner-profile.md
│   ├── scope.md
│   ├── prd.md
│   └── spec.md
├── scripts/
│   └── seed.py
├── workspaces/
│   └── demo-repository/
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── Makefile
└── .gitignore
```

This structure is sufficient for the required PoC and aligns with the existing architecture. It does not add unnecessary services or broad project scaffolding.

## External Services and Dependencies
The PoC relies on a small set of local dependencies and one major execution dependency:

- Local FastAPI backend
- SQLite database
- Browser-based frontend
- Docker for isolated code execution
- Demo repository under the workspace directory

Required environment assumptions:
- Docker must be available and working for sandbox execution
- the local Python environment must include the project dependencies
- the local dev server must be running for the dashboard to reach the API

No external hosted service is required for the required proof of concept. That keeps the architecture small and reproducible.

## Important Failure Modes
The main points where this system can fail are the places that matter most for trust:

- **Sandbox unavailable or Docker missing** → the task should not be marked as verified; the system should return an inconclusive or error status with the reason.
- **Tests fail** → the task should show FAILED with the actual output and relevant counts.
- **Execution output is missing or incomplete** → the task should not be marked verified; the system should show the evidence gap clearly.
- **Patch or repo data is unsafe or invalid** → the system should reject it before execution or show a failure reason.

## What Was Simplified and Why
- **One demo repo and one minimal pass/fail flow** instead of a broad repository manager or general-purpose language runner — because the PoC only needs to prove the verification idea.
- **Local execution** instead of hosted deployment — because the hackathon demo requires a reliable, reproducible local run with visible evidence.
- **One verification model** instead of multi-agent orchestration — because the required value is evidence, not autonomous code generation.
- **Python-only demo checks** instead of wider language support — because the project already contains a Python-based repo and the demo can stay narrow and reliable.

## Decisions and Open Issues
Decisions made:
- The project stays focused on task submission, automated checks, and evidence-backed verification.
- The architecture reuses the existing AegisOS app structure rather than creating a parallel system.
- The proof of concept will remain local and small, with optional deployment deferred.
- The app will keep the pass/fail and error/inconclusive distinction explicit in the UI and task records.

The one genuine unresolved point from the PRD is the exact demo setup for pass/fail evidence. The implementation will use the simplest workable option: one Python demo repository with a controlled failing variant if that remains the least disruptive path. Alternative two-fixture setups are acceptable but not required.

This was the relevant, consequential open issue captured from the PRD review, and it is the only remaining decision before build execution.
