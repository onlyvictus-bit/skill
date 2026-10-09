# Unlazy integration contract

Use `unlazy` only as a subordinate completion-depth specialist for substantial, exhaustive, previously half-done, or explicitly "do not stop until complete" work. Fable remains the governor and `docs/fable/` remains the single canonical project authority.

## What to reuse

Reuse these mechanisms when the `unlazy` skill is actually available:

- the **Depth Tree** idea: split a substantial approved outcome until every leaf is one coherent, independently verifiable deliverable;
- contract inventory before fan-out so independently omittable outcomes and acceptance-changing constraints cannot disappear;
- exact leaf ownership and dependency ordering before parallel work;
- branch-level integration checks in addition to leaf checks;
- parent **reverify** of returned work instead of trusting leaf self-report;
- the **four passes** on each meaningful leaf: complete the deliverable, reread as a domain expert and replace cheap/partial work, hunt correctness/integration/portability/performance/evidence defects, then apply low-cost polish until another pass finds nothing;
- bounded retry/abandonment semantics: impossible or blocked work becomes an explicit handoff, never fake success;
- measured completion reporting rather than a confident done claim.

## Authority boundary

Unlazy is advisory/subordinate inside Fable. Its `PLAN.md`, `GATES.md`, `.unlazy/` state, checkboxes, leases, dispatch waves, and approval records are **never authoritative** for Fable project truth. Do not let them replace or silently mutate Fable requirements, plan, approvals, state, tests, read receipts, proof-unit status, or evidence.

If an Unlazy ledger is useful, generate or use it only as a **derived** execution/review projection from the current Fable proof units. Import surviving findings and observations back into `docs/fable/`, then rerun the applicable Fable gate. A checked Unlazy box never promotes a Fable requirement to VERIFIED by itself.

Unlazy command approval is a separate security boundary. Fable approval does not authorize arbitrary Unlazy `CHECK:` shell code. Before any inherited command is executed, inspect the exact command and its called scripts under the normal Fable authorization policy. Never use an Unlazy success marker to bypass Fable's test/evidence requirements.

## Routing

Prefer Unlazy when at least one is true:

- the task has many independently omittable outcomes;
- earlier work returned partially complete;
- the user explicitly asks for exhaustive completion, a depth tree, gates, or a "do not stop early" workflow;
- a milestone benefits from leaf/branch decomposition and independent parent re-verification;
- Fable's Work Compiler has many ready proof units and premature completion is a material risk.

Do not invoke it for trivial edits or factual replies.

When available, give Unlazy a compact Fable task capsule: proof-unit IDs, exact requirements/constraints, dependencies, allowed write set, acceptance conditions, and approved verification commands. Do not dump the whole project when the capsule is enough.

## Availability and install boundary

Do not auto-install Unlazy. Detect whether the skill/runtime is available. If it is not callable, record `UNLAZY_UNAVAILABLE` and continue with Fable's internal proof-unit decomposition, four-pass leaf review, parent re-verification, bounded retries, and `fable-judge` completion attack. Lack of Unlazy must not weaken the canonical Fable gates.


## Bundled operational implementation

Read [unlazy-operation.md](unlazy-operation.md) for executable entry points, exact inputs/outputs, dependency checks, verification, and failure handling. The full original source is preserved under `specialists/unlazy/`; it is consumed through that adapter and the six-specialist operating contract. This supplements every rule above.
