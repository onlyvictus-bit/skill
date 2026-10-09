# Memory Integrity R4 / m12

Memory Integrity is an evidence-focused skill for complete-read, source coverage,
durable recall, recovery and guarded task coordination. R4 is the formal successor
to the R3/m11 offline pair.

The release remains a **matching two-package system**:

- memory-integrity: user-facing workflow, evidence composition and native claim guard
- claude-mon: required companion for CM ledger, history and coordination

R4 adds verified durable native-operation recovery and a granular shared-project
claim protocol. It does **not** enable generic native Beads writes. Current native
capability truth is:

- native_shared_claim_protocol_qualified=true
- native_beads_qualified=false
- generic_native_write_qualified=false
- native_merge_qualified=false

Every real shared workspace/claim still requires an exact current authorization
bound to its selection, work item, native task, actor and operation ID. Native
create/close/delete/merge and live AI/provider calls remain separately gated.

## Release verification

The formal R4 pair is recorded under release/ as memory-integrity-r4.zip and
claude-mon-r4.zip with Memory-Integrity-R4-Release-Manifest.json and the
standard-library Verify-Memory-Integrity-R4.py verifier. Keep the two packages
together; the Memory Integrity workflow requires an explicit matching companion.

R3 artifacts are retained unchanged for rollback/history.

## Repository layout

- memory-integrity/: main skill and workflows
- claude-mon/: required companion engine
- release/: verified R3 and R4 packages/manifests/verifiers
- docs/: status, qualification evidence and operating boundaries

MIT - see LICENSE.

## Optional Semantica bridge v1

Memory Integrity now includes an opt-in isolated Semantica layer for explicit vector search, bounded local GraphRAG, source-linked relationships, recursive provenance, structural SHACL and protected offline request/audit receipts. It preserves the existing companion and Fable authority. See [integration](memory-integrity/references/semantica-integration.md), [operations](memory-integrity/references/knowledge-operations.md) and the [plan review](docs/fable/derived/plan-review.md).

Run `python -B release/Verify-Knowledge-Bridge.py` for the matching knowledge-v1 pair. The pinned optional runtime is installed separately using `semantica-runtime/requirements-lock.txt`. Set `KNOWLEDGE_WORKER_PYTHON` to its absolute interpreter to run the real runtime checks. R3/R4 release artifacts remain unchanged for rollback. Graph stays off by default; general semantic accuracy and coding benefit remain unverified.

The current pair includes the [2026-10-08 audit integrity correction](docs/fable/derived/audit-upgrade.md): actual retrieval/prompt proposition checks, independent current-source observations, and rejection of forged nested retrieval receipts before protected execution.

## Automatic coding knowledge workflow / bridge 1.1

The [project-2 workflow](memory-integrity/references/knowledge-project-2.md) adds automatic Python extraction, conservative Semantica relation DSL extraction, offline text search, typed SHACL, reverse traversal, selective invalidation, observed local tests and freshly checked task-relative admission. The [completion plan](docs/fable/derived/full-workflow-plan.md) restores the gaps in the first prototype. Existing project-1 data and R3/R4 packages remain available. Graph stays optional; offline fixture outcomes do not prove general AI coding benefit.


Semantica bridge1.2 adds optional file-pinned local MiniLM embeddings, Qwen relevance scoring and bounded per-unit processing, JavaScript/TypeScript syntax, source-bound community/global/DRIFT and local two-process sharding. Use the knowledge-v2 package pair and the explicitly prepared runtimes documented in memory-integrity/references/knowledge-models.md. Graph remains off by default. Real model coding outcomes, including failures and raw receipts, are recorded in docs/fable/derived/model-benefit.json; no production coding benefit or remote multi-host qualification is claimed.
