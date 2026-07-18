# Evidence-Based Debugging

Follow this sequence:

```text
Reproduce → locate boundary → state one hypothesis → run a minimal experiment
→ fix the root cause → run regression verification
```

- Reproduce the observed symptom and capture the relevant command, input,
  output, and environment boundary.
- Narrow the failure to the smallest responsible component or interaction.
- State one falsifiable hypothesis before changing production code.
- Run the smallest experiment that can disprove or support that hypothesis.
- Fix the root cause, not a downstream symptom. Add or update a regression test
  when feasible.
- Re-run the reproducer and all relevant regression checks after the final edit.

If the user asks only for diagnosis, stop after reporting the evidence and
likely cause. After two failed hypotheses in the same direction, revisit the
reproduction boundary and architectural assumptions instead of stacking fixes.
