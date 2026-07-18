# Change Artifacts

Use a tracked change when work needs a durable scope, more than one task, or
future resumption. Derive a short kebab-case name from the outcome, such as
`add-remember-me` or `fix-session-expiry`.

Create this directory in the target repository:

```text
.spec-delivery-lite/changes/<change-name>/
```

Copy the matching files from `assets/templates/` and replace all placeholders.
Create `brief.md` and `tasks.md` by default. Create `design.md` only for a
meaningful decision. Create `verification.md` when validating completion.

## Artifact Rules

- Put user-visible outcomes in **Acceptance conditions**, not technical tasks.
- Put implementation order and commands in **Tasks**, not in the brief.
- Put alternatives, chosen approach, data/API implications, and rollback notes
  in **Design** only when they materially affect the change.
- Re-read artifacts from disk before revising or implementing; do not rely on
  chat memory.
- If implementation invalidates scope or a decision, update the affected
  artifact and ask for approval if the change is material.

## Archive

Move a completed change to:

```text
.spec-delivery-lite/archive/YYYY-MM-DD-<change-name>/
```

Do not archive with incomplete tasks, missing critical acceptance evidence, or
unresolved high-severity review findings unless the user explicitly accepts the
gap.
