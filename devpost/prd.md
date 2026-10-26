---
doc: prd
status: approved
---

# AegisOS — Product Requirements

AegisOS is a developer-facing verification tool that turns an AI coding agent’s claim of completion into evidence-backed execution results. The product is a small proof of concept focused on one core workflow: a user submits a task, the system executes relevant automated checks against a registered repository, and the dashboard shows whether the task passed, failed, or was inconclusive due to execution error or missing evidence.

Source: `scope.md > The Unique Kernel`, `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`, and `scope.md > The POC Boundary`.

## The Core Journey
1. A developer opens the AegisOS dashboard and sees a workspace with tasks, recent runs, and repository status.
2. The developer selects a registered demo repository and enters a coding task that needs verification.
3. The system records the task and begins the verification workflow, showing a task status while execution is running.
4. The backend runs real automated checks against the repository in a controlled execution environment.
5. The dashboard updates with pass/fail status, evidence, and execution output.
6. The user can inspect the result and understand whether the task is genuinely verified or whether the system failed to obtain sufficient evidence.
7. The task remains visible in a run history so earlier results can be compared and explained.

This is the product’s central value: trust is tied to evidence, not to the AI’s claim that a task is complete.

## Screens and Layout
The project is a small dashboard with a developer-focused layout. The interface contains:
- a primary workspace or overview screen
- a task creation and submission area
- a recent task / run history panel
- a selected task detail or trace view that exposes execution evidence
- a minimal repository selection view for demo repositories

The layout should feel technical and clear, not promotional. It should prioritize reading output, understanding status, and scanning evidence quickly.

## Look and Feel
The interface should feel calm, trustworthy, and engineering-oriented. The experience should emphasize clarity and evidence over visual excess. The product should avoid gimmicky styling and instead favor functional readability, strong contrast, useful labels, and direct status messaging.

The design direction is practical rather than polished: it is a proof of concept for verification confidence, not a consumer-facing app.

## Features and Behavior

### Task Submission and Repository Selection
The user can open the dashboard and submit a task associated with a selected repository. The interface should make it clear which repository is being checked and what task is under evaluation.

- As a developer, I want to select a repository for verification so that the checks run against the right project.
  - [ ] Acceptance criterion — the user can choose a registered repository from the UI.
  - [ ] Acceptance criterion — the task is linked to the selected repository and records the repository choice.

- As a developer, I want to submit a coding task so that the system can run relevant checks.
  - [ ] Acceptance criterion — the task is created with a title, issue description, and acceptance criteria.
  - [ ] Acceptance criterion — the system records the submitted task and shows it in active or recent runs.

### Execution Workflow
The system runs actual validation checks based on the selected repo and task. The workflow is separate from any salesperson or agent claim about completion.

- As a developer, I want the selected checks to run against a repository so that I can verify the result with evidence.
  - [ ] Acceptance criterion — the task enters an execution workflow after submission.
  - [ ] Acceptance criterion — execution evidence is collected in the task record or trace.

### Status Outcomes
The dashboard shows a clear result for each task based on observed execution results.

- As a developer, I want a PASS or VERIFIED status only when the checks actually succeed.
  - [ ] Acceptance criterion — a task is shown as verified only when the execution result and checks indicate success.
  - [ ] Acceptance criterion — the interface distinguishes verified status from a simple “done” or “accepted” claim.

- As a developer, I want a FAILED status when the checks or tests fail.
  - [ ] Acceptance criterion — failing execution records the failure and relevant output.
  - [ ] Acceptance criterion — the user can see the failing test or command result without ambiguity.

- As a developer, I want an ERROR or INCONCLUSIVE status when execution does not complete or evidence is insufficient.
  - [ ] Acceptance criterion — the system does not label the task as verified when execution was unavailable, failed, or incomplete.
  - [ ] Acceptance criterion — the reason is surfaced to the user in the task or run details.

### Evidence Display
The user must be able to understand the result without guessing what happened.

- As a developer, I want to see actual output from the checks so that I can understand the result.
  - [ ] Acceptance criterion — the dashboard shows command or test output relevant to the task result.
  - [ ] Acceptance criterion — the task includes the status, timing, and any failure details visible in the output.

- As a developer, I want summary counts so I can understand whether the task passed or failed at a glance.
  - [ ] Acceptance criterion — the task summary includes counts such as tests run, passed, and failed where available.
  - [ ] Acceptance criterion — the interface shows a clear breakdown for successful and failing runs.

### Historical Context
The dashboard should keep recent runs understandable and comparable.

- As a developer, I want recent task runs to remain visible so that I can compare outcomes over time.
  - [ ] Acceptance criterion — tasks or executions remain in a recent history.
  - [ ] Acceptance criterion — result states are understandable without reading unrelated workflow details.

## States and Boundaries
- **Queued** — the task has been accepted and is waiting to run.
- **Running / In Progress** — the verification workflow is active and the task has not yet reached a final status.
- **PASS / VERIFIED** — the execution evidence supports success.
- **FAILED** — the checks or tests reported a negative result.
- **ERROR / INCONCLUSIVE** — execution failed, timed out, or did not provide enough evidence to verify success.
- **Cancelled** — a task was intentionally stopped before final evaluation.

The system should avoid treating a task as verified when execution is unavailable or incomplete. The design requirement is evidence-first, not optimistic completion.

## Product Decisions
- Keep the project focused on a narrow verification loop rather than autonomous software generation.
- Demonstrate the workflow using a small, reproducible demo repository and a limited set of checks.
- Reuse the existing dashboard and backend wherever they support the required workflow rather than rebuilding everything.
- Treat all unverified functionality as planned or experimental, never as confirmed product behavior.
- Show both a passing and failing test outcome in the demo to prove the system can detect and explain failure.

## Verified vs. Planned Functionality

### Already implemented in the codebase
The repository already contains a dashboard shell, backend API, task and repository models, the workflow engine, sandbox runner, evaluator rules, and a demo Python repository. These are existing project artifacts and should be treated as prior work, not as new work created during this hackathon.

### Verified for this PRD
No functionality in the current implementation is considered fully verified for the PoC until a live execution path is demonstrated with actual output. The PRD therefore distinguishes between what exists in the repo and what is actually confirmed by evidence.

### Planned for the PoC
- real end-to-end task submission through the dashboard or API
- pass/fail execution against a demo repository
- evidence-backed status transitions for PASS, FAILED, and ERROR/INCONCLUSIVE
- historical task visibility and readable execution output
- controlled failing-case demonstration without touching the existing project codebase

## What We're Building
The proof of concept must include:
- a developer dashboard that accepts task submission and repository selection
- a task workflow that executes real checks against a demo repository
- clear PASS, FAILED, and ERROR/INCONCLUSIVE states based on execution results
- evidence display including output, counts, and failure details
- both successful and failing demonstration runs using the same task execution model
- a small, understandable reproduction path for future learners and project reviewers

## Deferred From the POC
- autonomous code generation
- multi-agent orchestration
- support for many programming languages
- broad cloud deployment or advanced infrastructure
- large-scale collaboration or multi-user workflows
- advanced analytics and reporting

These remain relevant later, but they are not needed to prove the core AegisOS value in this hackathon.

## Possible Later Enhancements
- richer repository support and more robust task selection
- better scheduling and historical trend reporting
- deeper integration with code review and CI checks
- richer task metadata and explanation for engineers
- broader verification support beyond a single demo workflow

## Non-Goals
- turning the product into a general autonomous coding platform
- presenting AI opinion as proof of correctness
- claiming verification success without real execution evidence
- adding broad language support before the core workflow is proven

## Open Question
- Which demo setup should be used for the required pass/fail proof: one Python repository with a controlled failing variant, or two separate demo fixtures for pass and fail?

This is the only essential decision still needed to lock the final PoC boundary before the technical plan.
