# Blueprint: complete, scoped design

Read the preserved [Blueprint source](specialists/blueprint/SKILL.md) after this adapter.

## Input and scope

Use accepted user stories, existing architecture/contracts, the chosen approach and rejected alternatives, constraints, primary evidence, and observable acceptance criteria. Inferred requirements are proposals until Fable classifies and accepts them. Six hats mean six review viewpoints, not six agents or independent witnesses.

## Procedure

1. Restate each spoken requirement as a user story and measurable acceptance condition. Sweep hidden needs and anti-requirements. Keep unsupported numeric targets marked proposed or unknown, never measured.
2. Architect: document components/data flow, data model, trade-offs, latency/throughput/cost/recovery targets and how to measure them. Estimate capacity at 1x/10x/100x only with explicit inputs; list material failure modes with detection and mitigation. Mark irrelevant scaling work not applicable with a reason.
3. Designer: trace first use through the intended outcome. For every relevant screen or endpoint enumerate loading, empty, partial, network/validation/permission error, success, stale and offline states. Review keyboard/screen-reader access, contrast, responsiveness, language/timezone needs and existing design tokens.
4. Developer: specify real request/response/error contracts, authorization, validation, idempotency, concurrent writes, retry/backoff, config validation, structured logs, compatibility, migrations and flags. Confirm consumers exist. Avoid invented APIs.
5. Tester: map acceptance IDs to meaningful unit/integration/end-to-end or manual observations. Generate applicable null/empty/huge/Unicode/duplicate/out-of-order/expired/revoked/concurrent/interrupted-write cases. Include performance/security checks where required; justify exclusions.
6. Operations: define relevant logs, metrics, traces, thresholds, SLO/error-budget proposals, runbook, rollout/bake criteria, backup/restore and rollback. A written rollback procedure is a design artifact; it is not a successful rollback rehearsal.
7. Security: examine trust boundaries, role-resource-action authorization, validation, secrets, rate limits, dependencies and licenses against the actual system. Keep findings specific to reachable behavior.
8. Run gap radar per capability: needed by which requirement; why selected over an alternative; strongest failure; supported user journey; measured/proposed cost/latency; next dependency; missing condition. Rank P0 blockers and P1 follow-ups by consequence and effort with rationale.
9. Produce a walking skeleton milestone that proves the thin end-to-end path. Prepare deployment where relevant, but execute external release only under separate authorization. Never build proposed backlog features silently.
10. Cross-check hats for contradictions, resolve against accepted requirements and evidence, then import accepted changes into Fable. Reopen approval only when the authorized scope actually changes.

## Output

Use a planned design report with nine parts: requirement matrix, NFR/measurement table, component/data-flow map, surface state matrix, tests/edge cases, observability/runbook/rollback, security findings, ranked gaps with cheapest closing check, and milestone exit criteria. For an inapplicable part state why; never omit it silently.

## Verification

Trace every requirement to at least one design decision, consumer and test/observation. Review a scratch design missing an error state and rollback: both must remain unresolved gaps, not readiness claims. A design is complete when its scoped parts and gaps are accounted for; production readiness requires the actual implementation/runtime evidence. Register the output and corresponding typed verification in Fable.
