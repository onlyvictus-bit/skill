# Fable Judge remediation — current evidence and open gates

**Source of truth:** `onlyvictus-bit/skill`, branch `development/victus-judge-r4-remediation`.

**Authorization:** Current user: “@Autonomous Operator fix all not fixed finding and commit to git.” This authorizes GitHub remediation commits; no deployment, merge, account secrets, or live Graphify activation.

## Test-first evidence

- RED CI: `37931932607` (commit `a3b59d8`). Adversarial trust and correctness tests failed on original source as expected, including hidden edges, false approval/witness, supply chain, timestamps, deduplication, and freshness.
- Source-remediation commit: `0d7c05f`. Exact-head CI on this intermediate commit was not green because `R4-CONTENT.json` and release package bytes were stale.
- New immutable release identity: `knowledge-bridge-v2`. Historic v1 archives remain unchanged; hosted release builder run `37932517630` passed and committed v2 artifacts.
- **Required to close:** exact-head hosted CI including safe archive check; positive+adversarial independent verification of signed grants, reviewer witness verification against trusted issuer, complete active third-party wheel hash pins, Fable plan/execute/complete gate receipts, independent source review.

## Ten findings (provisional; none is marked fully closed)

1. SPARQL: arbitrary justification refused; graph-bound signed capability required.
2. GraphRAG: self-reported approver/scope refused; signed and graph-snapshot scope binding.
3. Review witness: signed issuer receipt enforced, but institutional issuer authenticity not independently demonstrated in deployment.
4. Wheel hashes: CSV RECORD parser fixed; Semantica __init__.py wheel hash pinned from 4 matching hosted OS/Python observations (runs 37932868772); installed file bytes now separately checked; incomplete wheel RECORD coverage returns UNVERIFIED, full pin set still pending.
5. Bitemporal: explicit normalized knowledge timestamps required for retraction/correction, including deterministic event replay.
6. IR: missing-required count computed from same deduplicated top-k set as recall.
7. Freshness: unknown stale flag now excluded.
8. CI scanner: test fixture remains synthetic, with literal split to avoid scanner false-positive while retaining the same sensitive-env assertion.
9. Fable completion: requirements remain open pending exact-head and independent evidence.
10. Archive identity: v1 immutable; v2 names, version and manifest are disjoint.

**Authority boundary:** Security-sensitive operations fail closed when issuer keys, source pins or explicit timestamps are unavailable. Synthetic signed-fixture tests verify behavior, not deployment credential provenance. No production-readiness claim is made.
