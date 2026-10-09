---
name: blueprint
description: >
  Production-readiness design layer that thinks like a full product team.
  Maximizes requirements from a bare ask (user stories, acceptance criteria,
  hidden assumptions), then convenes six engineering hats — architect (NFR
  targets, ADR trade-offs, FMEA failure modes, capacity math), designer (journey
  map, full UI state matrix, accessibility, i18n), developer (contracts, error
  taxonomy, idempotency, migrations), tester (test pyramid per feature, edge/
  negative generators, executable acceptance checks), SRE (metrics/traces/
  alerts, SLOs, runbook, rollout+rollback), security (STRIDE/OWASP sweep) —
  and runs the gap-radar loop: what is needed, what makes it BEST vs
  alternatives, robust under failure, useful to users, efficient in time/cost,
  what ships NEXT, what is MISSING before launch — every gap ranked by
  risk x effort into P0 blockers vs P1 backlog. Use for "design X completely",
  "make it production ready", "what are we missing", "full feature plan",
  or after deep-plan picks an approach.
---

# blueprint — From Idea to Production-Complete Design

deep-plan decides WHICH idea wins. blueprint makes that idea WHOLE: every
requirement surfaced, every hat's artifacts written, every gap named and
ranked — so implementation never discovers a missing pillar mid-build.

Run after deep-plan's verdict (or standalone when the approach is already
fixed). Grade final confidence with triangulate.

## Phase A — Requirement maximization

Expand the ask into the complete requirement set BEFORE designing anything:

1. **Spoken requirements**: restate each as a user story with an EXECUTABLE
   acceptance criterion ("import completes <30s for 10k rows", not "fast").
2. **Hidden requirements** users assume but never say: auth, pagination,
   empty/error states, undo, concurrency (two users, same row), data export,
   audit trail, timezone/locale, mobile, offline, upgrade path. Sweep this
   list explicitly; each item becomes Blocking / Required / Recommended /
   Future / Rejected-with-reason (same vocabulary as fable).
3. **Anti-requirements**: what this deliberately will NOT do. One line each;
   prevents silent scope creep later.

## Phase B — Six hats, six artifacts

Each hat writes its artifact from Phase A evidence; hats sharing a data origin
get merged by triangulate's independence rules before weighting conclusions.

### Architect — non-negotiable numbers
| NFR | Target | Measured how |
|---|---|---|
p95 latency, throughput/RPS, availability %, max cost/unit, recovery time
(RTO/RPO), max payload. Every target needs a measurement method or it is
decoration. Plus: ADR-style trade-off notes (chosen vs rejected, one line of
why), data model sketch, capacity math at 1x/10x/100x load, top-10 failure
modes table (mode → detection → mitigation).

### Designer — the state matrix
Journey map (first-run → habit). For EVERY screen/endpoint enumerate all
states: loading, empty, partial, error (network/validation/permission),
success, stale/offline. Accessibility pass (contrast, keyboard-only, screen-
reader labels), responsive breakpoints, i18n/pluralization hooks, consistency
against existing design tokens. A flow missing any state is a support ticket
factory.

### Developer — contracts and hygiene
API contracts (request/response schema, status codes, error envelope),
idempotency keys for writes, migration strategy (expand-contract), config via
env with validation, structured logging points named, retry/backoff policy,
feature-flag plan, tech-debt register seeded.

### Tester — break it on paper
Map the test pyramid onto features (unit/integration/e2e counts per story).
Generate edge/negative cases mechanically: null, empty, huge, unicode, duplicate,
out-of-order, expired, revoked, concurrent, interrupted-mid-write. Convert every
Phase-A acceptance criterion into an executable check. Add property-based/fuzz
candidates and the perf/security test plan. Anything untestable goes back to
the architect as a design smell.

### SRE — run it at 3am
Metrics/logs/traces list with alert thresholds, SLO + error budget, dashboard
sketch, runbook outline (symptom → check → fix), deploy strategy (flags,
canary %, bake time), ROLLBACK procedure tested-in-writing, data-backup/restore
drill schedule. No rollback = not shippable.

### Security — assume hostility
STRIDE-lite per trust boundary, OWASP Top-10 sweep against the actual design,
authz matrix (role x resource x action), input validation inventory, secrets
handling, rate limits, dependency/license risks.

## Phase C — Gap radar (the reasoning loop)

For each capability in the design, answer in writing:

1. **What is NEEDED?** — traceable to a Phase-A requirement or drop it.
2. **What makes it BEST?** — name the alternative compared and why it lost.
3. **Is it ROBUST?** — inject its top failure mode; does the design survive?
4. **Is it USEFUL?** — which user journey step does it serve; orphan = cut.
5. **Is it EFFICIENT?** — time/cost/latency number vs its NFR target.
6. **What comes NEXT?** — the capability this unlocks; feeds the roadmap.
7. **What is MISSING?** — anything whose absence blocks ship or embarrasses
   post-launch. Check across ALL hats' artifacts, not just your favorite.

Rank every gap: P0 blocker (ship dies without it) vs P1 next-iteration, sorted
by risk x effort. Never silently drop: cuts go to backlog with a reason.

## Output — the Blueprint document

```
1. Requirement matrix (story | criterion | MoSCoW | owner-hat)
2. NFR table with measurement methods
3. Component/data-flow map
4. State matrix per surface
5. Test matrix + edge-case list
6. Observability + runbook + rollback summary
7. Security posture summary
8. GAP LIST: P0 blockers first, each with cheapest-closing-test
9. Roadmap M0..Mn, exit criteria per milestone (M0 = walking skeleton)
```

## Hard rules

- A feature without an owner hat, a test, telemetry, and a rollback path is
  NOT production-ready — mark it prototype.
- Efficiency claims carry numbers; "fast" and "scalable" are banned words.
- The walking-skeleton milestone (thinnest end-to-end path incl. deploy +
  observability) always exists and always ships first.
- If any hat finds a contradiction (architect target vs tester reality),
  surface it as a finding — do not average targets to make peace.
