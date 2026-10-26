---
doc: checklist
status: draft
---

# Build Checklist

Build mode: [learn]

## Slices

- [ ] **1. Verification verdicts are strict and evidence-based**
  Becomes usable: The app can distinguish verified, failed, and inconclusive outcomes from real evidence instead of trusting a patch or a claim alone.
  Why now: The unique kernel of AegisOS is evidence-backed verification; proving that contract early makes every later workflow decision safer.
  PRD ref: `prd.md > The Core Journey`, `prd.md > Status Outcomes`
  Spec ref: `spec.md > Components`, `spec.md > Important Failure Modes`
  Build: Reconfirm the evaluator rejects unsafe patches, treats missing sandbox evidence as inconclusive, and only marks a task verified when independent checks pass.
  Verify (mechanical): Run the backend evaluator and patch-validation tests; confirm the verdict logic matches the expected PASS/FAIL/INCONCLUSIVE cases.
  Learner check: review one pass case, one fail case, and one no-evidence case, then say which status is trustworthy and why.
  Commit: `Verify evidence-based verdicts`

- [ ] **2. Task execution produces real execution evidence**
  Becomes usable: A queued task can run through repository indexing, patch validation, sandbox execution, and final evaluation with explicit evidence recorded.
  Why now: The product depends on the workflow loop, and real execution evidence is the point of the proof of concept.
  PRD ref: `prd.md > Execution Workflow`, `prd.md > Evidence Display`
  Spec ref: `spec.md > Components`, `spec.md > Data Model`, `spec.md > Failure Modes`
  Build: wire the demo repository path, patch creation, sandbox runner, and evaluation output into the task lifecycle without broadening scope beyond the PoC.
  Verify (mechanical): execute the demo task flow and inspect the stored task trace, test result, and evaluation output for a real verdict.
  Learner check: open the task record and explain where the evidence came from and which part of the app makes that claim credible.
  Commit: `Run the task workflow with evidence`

- [ ] **3. The dashboard shows status and evidence clearly**
  Becomes usable: The user can see tasks, verdicts, and output history in a way that surfaces what actually happened without hiding the failure reason.
  Why now: Even a correct backend is not trustworthy if the dashboard makes the result hard to interpret.
  PRD ref: `prd.md > Screens and Layout`, `prd.md > Evidence Display`
  Spec ref: `spec.md > Look and Feel`, `spec.md > Components`
  Build: ensure task state, verdict, and evidence are visible in the app and readable by a developer trying the core journey.
  Verify (mechanical): load the app, start a task, and confirm the status and output update as expected.
  Learner check: tell which result is easiest to trust from the dashboard and what is missing from the current view.
  Commit: `Display evidence in the dashboard`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — the verification contract and task/workflow experience reviewed in context
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [real verification path, task flow, and relevant code references]
Route and stops: [actual code paths and symbols for the verification path]
Edit outcome: [retried/kept/reverted/declined/not applicable]
Reflection: [offered/answered/declined/already covered]
Activity mode: [live app and editor / focused alternative]

## Revisions
