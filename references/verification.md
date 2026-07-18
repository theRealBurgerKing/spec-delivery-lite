# Verification Before Completion

Before saying a change is complete, fixed, passing, ready to commit, or ready
to archive:

1. State the exact claim.
2. Identify checks that prove that claim.
3. Run those checks after the final modification.
4. Read the exit status, failure count, warnings, and actual scope of coverage.
5. Report only what the fresh evidence supports.

For a tracked change, use `assets/templates/verification.md` to map every
acceptance condition to a test, build output, code inspection, or documented
manual scenario. A green test suite alone does not prove every requirement.

If a required check cannot run, report it as an unverified gap. Do not replace
fresh evidence with confidence, prior output, or an agent report.
