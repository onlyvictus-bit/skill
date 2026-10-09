# Campaign mode

Use campaign mode for work that spans multiple milestones, sessions, or recovery points.

## Canonical record

`docs/fable/` remains authoritative. Keep requirement IDs stable across sessions. Preserve historical approval records; do not rewrite an old approval to match a changed plan.

## Milestone lifecycle

For each milestone:

1. Load requirements, plan, tests, approvals, state, and relevant evidence.
2. Verify the plan gate.
3. Obtain approval for the exact milestone or named range.
4. Verify the execute gate immediately before behavior-changing work.
5. Execute only approved scope.
6. Update state before any pause or handoff.
7. On resume, verify the resume gate before trusting previous next-action notes.
8. Produce fresh evidence after relevant artifact changes.
9. Verify complete gate and adversarial review.
10. Advance only after the current milestone is evidence-complete or explicitly accepted with documented caveats.

## Recovery rules

State must identify the current milestone, current task when applicable, next action, completed requirement IDs, and requirement/plan digests. A fresh session must distrust prose summaries if their digests do not match canonical files.

If state is stale, re-orient from the repository and canonical Fable files. Never resume a task solely because a previous assistant said it was next.

## Approval continuity

One user approval covers the same unchanged named scope across subordinate skills and sessions. Do not ask repeatedly inside that scope. Any material requirement/plan change creates a new approval boundary.

## Campaign reporting

At each handoff report current milestone, completed requirements, fresh evidence, blockers, stale/unverified layers, and the exact next approval boundary. Do not label the campaign complete when only one phase is complete.
