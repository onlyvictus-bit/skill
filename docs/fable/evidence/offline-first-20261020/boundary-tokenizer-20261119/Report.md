# Boundary qualification, 2026-11-19

Partial. Earlier F01/F02 processing failure is resolved for the tested installed pair. No code, installed bytes, checkpoint or Git state changed.

{'discovered': 114, 'executed': 114, 'passed': 97, 'failure_records': 0, 'error_records': 0, 'skipped': 17, 'expected_failures': 0, 'unexpected_successes': 0, 'incomplete': 0}

| Boundary | Verdict | Observed scope | Evidence |
|---|---|---|---|
| INSTALLATION_INTEGRITY | PASS | 279 installed files unchanged; exact source inventories agree. | Identity-Before.json; Identity-After.json |
| COMPANION_COMPATIBILITY | PASS | Installed explicit companion handshake succeeds; matching pinned content identities verified; retained installed negative regressions remain on this unchanged pair. | mi-capabilities/stdout.log; retained cm-cli-repair-20261119 evidence |
| SOURCE_COVERAGE | PASS | Real current checkpoint original identities and eight exhaustive records verified; scope is declared sources, not entire repository comprehension. | Project-Recovery.json |
| PROCESSING_AND_LEDGER | PASS | 11 F01/F02 regression tests pass. Fresh public offline workflow accepts all8 current checkpoint records with saved author reviews (TEST_ONLY). Default global Temp attempt blocked; explicit process-local owned Temp succeeds. | cm-cli-cases/Receipt.json; public-project-owned-temp.stdout.log |
| CONTEXT_BUDGETING | BLOCKED | 3 legacy+14 v2 budget tests pass; reserve arithmetic passes. Exact installed token counting raises missing-tiktoken error. | cm-budget-cases/Receipt.json; cm-budget-v2-cases/Receipt.json; practical-v2/Practical-Checks.json |
| EXTRACTION | BLOCKED | Supported inventory/refusal tests pass. OOXML tracked changes and embedding cause PARTIAL. Complete conversion/OCR unsupported by active profile and Docling absent. | mi-extraction-cases/Receipt.json; mi-pdf-cases/Receipt.json; practical-v2/Practical-Checks.json |
| SEMANTIC_AUDIT | UNVERIFIED | 6 declared semantic-obligation tests pass. General source proposition truth, independent interpretation and arbitrary-document correctness not established. | mi-semantic-cases/Receipt.json |
| COORDINATION_AND_HISTORY | PASS | Retained isolated policy/history tests and fresh protected checkpoint verification support the offline scope only; native live DB remains disabled. | Project-Recovery.json; retained installed-functional-audit-20261119 evidence |
| KNOWLEDGE_AND_WORKER_RUNTIME | BLOCKED | 4 offline-engine tests and10 model-contract tests pass;17 optional tests skipped. Selected3.12 identity probe exits103 because Store base executable unavailable in this account. Controller3.14 has no numerical/model packages and is outside declared knowledge runtime range. | mi-offline-knowledge-cases/Receipt.json; mi-model-contract-cases/Receipt.json; selected312-identity/stderr.log |
| CURRENT_SESSION_MEMORY | BLOCKED | 21 legacy loopback TEST_ONLY tests+6 watchdog contract+5 boundary tests pass. Real loopback health refuses connection (WinError10061); no live roundtrip attempted. | mi-memory-http-cases/Receipt.json; memory-live-health/stdout.log |
| CODEX_PROJECT_CONTINUITY | PASS | Current v8 file recovery succeeds with893 bound project/evidence files and8 exhaustive records. No new independent model or user chat boundary was executed in this turn. | Project-Recovery.json |
| MEMORY_SERVICE_PERSISTENCE | BLOCKED | No reachable real service, stable datastore restart observation or qualified independent boundary observer. Same-process/caller-supplied claims remain UNVERIFIED. | memory-live-health/stdout.log; mi-memory-boundary-cases/Receipt.json |
| OVERALL_FOR_DECLARED_OFFLINE_USE | UNVERIFIED | Bounded public8-unit offline processing/recovery passes; broad all-function acceptance remains partial. Prior216-row inventory still contains public-route coverage gaps; missing/disabled/live boundaries cannot be upgraded from tests. | Summary.json; retained installed-functional-audit-20261119/Function-Matrix.json |

## Limits and retained failures

The practical-check harness initially loaded a same-named budgeting module from the wrong installed skill. A new script with an exact module path passed; both scripts and the harness finding are retained. The public offline workflow initially could not use global Temp; a new isolated owned-Temp control passed, with the initial failure retained. Optional/model skips are not integrations. Fresh workflow review accounting reused actual saved author reviews and does not prove independent semantic truth. Earlier review/model-context evidence remains historical; no new independent model context or user chat was created. No real memory writes, service restart, package/model download, install, native database or remote AI call occurred.
