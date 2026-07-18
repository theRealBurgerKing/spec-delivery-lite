# Review Feedback

Evaluate each review item against the current code, tests, and approved change.
Classify it before editing:

| Classification | Meaning | Action |
|---|---|---|
| Accept | The finding is correct | Fix it and verify the relevant behavior. |
| Adapt | The problem is real but the proposed fix does not fit | Explain the alternative, implement it, and verify it. |
| Disagree | The finding conflicts with code facts, compatibility, or approved requirements | State concise evidence; do not make an unnecessary change. |
| Decision needed | The finding changes product scope, architecture, or an approved trade-off | Present the choice to the user. |

Do not close a security, data-loss, or correctness finding merely by disagreeing.
Provide equivalent safety evidence or escalate it as a decision.
