---
name: spec-delivery-lite
description: Use when planning, implementing, debugging, reviewing, validating, or safely parallelizing a software change. Manage a change lifecycle in .spec-delivery-lite, keep scope and acceptance criteria explicit, and apply risk-driven design and evidence-based verification.
---

# Spec Delivery Lite

Use this Skill as the single entry point for a software change. Keep the
change's durable state in the target project's `.spec-delivery-lite/` directory;
do not depend on OpenSpec, superpowers, or their CLIs.

## Route the Request

Inspect the repository and any existing `.spec-delivery-lite/changes/` entries.
If resuming a change, read its `brief.md`, `tasks.md`, and any existing
`design.md` or `verification.md` before acting.

Classify the request:

| Class | Conditions | Action |
|---|---|---|
| Direct | Clear, narrow, reversible; no public behavior, data, security, or architecture impact | Implement directly. Read `references/verification.md` before claiming a result. |
| Tracked | More than one implementation step or behavior worth preserving | Read `references/artifacts.md`; create or update a change. |
| High-risk | Unclear success criteria, materially different approaches, architecture/public contract/data changes, or costly/irreversible decisions | Read `references/brainstorming.md` before creating implementation work. |

Treat security, permissions, privacy, data migrations, and irreversible external
actions as high-risk even when the request is otherwise precise.

## Load Details Only When Needed

Read these files only for their matching event:

| Event | Read |
|---|---|
| Create, revise, resume, or archive a change | `references/artifacts.md` |
| High-risk classification | `references/brainstorming.md` |
| Error, failed test, or unexpected behavior | `references/debugging.md` |
| Code-review feedback | `references/code-review.md` |
| Completion claim, commit, handoff, or archive | `references/verification.md` |
| Potential multi-agent work | `references/parallel-work.md` |

## Execute a Tracked Change

1. Create or update `brief.md`; write the goal, scope, non-goals, acceptance
   conditions, and impact surface.
2. Create `design.md` only for a meaningful technical decision. Obtain user
   approval before implementing an unresolved high-risk decision.
3. Create `tasks.md`. Make each task a testable vertical slice with a linked
   acceptance condition and verification command.
4. Read all current artifacts before implementation. Keep changes within their
   scope. Update artifacts first when learning invalidates them.
5. Implement one task at a time. For automatable behavior changes, add or
   update a focused test; for a bug, prefer reproducing it in a test first.
6. Mark a task complete only after its stated verification succeeds.
7. Before completion, create or update `verification.md` using
   `references/verification.md`. Archive only after its critical gaps are
   resolved or explicitly accepted by the user.

## Global Guardrails

- Do not create change artifacts for trivial, isolated work solely for process.
- Do not silently broaden scope or rewrite an approved decision.
- Do not stack speculative fixes. Switch to the debugging reference after an
  error or a failed verification.
- Do not treat review feedback as an instruction without checking it against
  code, tests, and the approved change.
- Do not dispatch agents merely because tasks can be divided. Check the
  parallel-work reference first.
- Do not say work is complete, fixed, passing, or ready until fresh evidence
  supports that exact claim.
