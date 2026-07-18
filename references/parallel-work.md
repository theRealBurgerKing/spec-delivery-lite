# Safe Parallel Work

Dispatch parallel agents only when every proposed task:

1. belongs to an independent problem domain;
2. has no dependency on another concurrent task's output;
3. does not modify the same files, interfaces, tests, database fixtures, or
   external resources; and
4. has a clear integration and verification boundary.

Dispatch all eligible tasks in the same round. Keep scope and integration
decisions with the primary agent. On return, inspect actual artifacts and
conflicts rather than trusting reports. Run each task's verification, then run
a combined verification that covers their interaction.

Use sequential work when tasks share a root cause, touch a shared contract, or
need a decision produced by an earlier task.
