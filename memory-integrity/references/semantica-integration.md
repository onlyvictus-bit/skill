# Optional Semantica knowledge bridge v1

Use this layer to discover source-linked relationships or diagnose a structured evidence gap. Fable owns requirements, approvals, edits and completion. Memory Integrity remains the entrypoint. The explicit matching claude-mon companion owns partition units, execution ledger, request measurement and protected history. A knowledge generation is a disposable projection, never an authority or a replacement memory system.

The initial bridge runs Semantica 0.7.0 at commit `320761de5d040a54a3220acc563223b4a7ffdc51` in a separately selected Python 3.10–3.13 interpreter. The host remains standard-library-only Python 3.11+. Do not install `semantica[all]` in the host. The repository runtime lock is a Python 3.12 qualification snapshot, not a promise for every OS/version; the isolated runtime CI checks selected supported environments.

| Selected capability | Implemented mechanism | Qualification boundary |
|---|---|---|
| Semantic search | Real Semantica VectorRetriever using explicit finite normalized vectors with exact model/dimension identity | Vector similarity observed; embedding meaning/quality requires independently qualified vectors |
| GraphRAG | Vector seeds plus authorized ContextGraph neighbors | Local directed traversal only; no global/hybrid/DRIFT summary |
| Multi-hop discovery | Bounded depth, visits, seeds and results with edge paths | Traversal is not logical inference |
| Entity relationships | Fully scoped explicit node IDs and typed directed edges | No automatic entity extraction or name merging |
| Provenance graph | Real ProvenanceManager lineage through source units and recursive derivation premises | Checks structured links/checksums; never proves source truth |
| Ontology / SHACL | Strict project-1 contract and actual optional SHACL node/edge shapes | Structural validation only; absent pyshacl is UNAVAILABLE |
| Knowledge graph | Immutable persisted generations and atomic CURRENT pointer | Rebuildable; whole generation invalidation, single writer |
| Answer/evaluation tooling | Independent structured oracle checks and four-configuration fixture benchmark | No Semantica answer generation or universal semantic accuracy claim |
| Pipeline-gap diagnosis | Actual request/response CAS receipt plus observed/partial/unknown stages | Extraction/reasoning steps not observed are unknown |

Discovery accepts unreviewed assertions while retaining their review state. Evidence packs reopen current source bytes and preserve declared mandatory units independently of ranking. Source identity is not proof that an interpretation is correct, or that all relevant corpus material was read. The canonical complete-read verifier still owns that judgment. Source authority (`AUTHORITATIVE`, `SUPPORTING`, `DERIVED`, `EPHEMERAL`) and assertion review state survive in each pack; this bridge does not automatically promote a discovery assertion to semantically qualified evidence.

The access policy is an explicit current, trusted operator input bound to workspace/task. This is not a multi-user authorization service. The local index contains the frozen source text; keep it in the same protected workspace and protect files/backups with OS permissions. Candidate sources, recursive premises and every retained edge are filtered before any bytes reach the worker. Denied IDs/text are omitted from output; only an aggregate exclusion count is disclosed.

The worker has no answer-generation/provider operation. Credentials and user configuration are not forwarded. Python socket connections are blocked and offline library flags set; this is best-effort application isolation, not an OS network sandbox or measured zero-network telemetry. Use an OS/container network boundary if a stricter threat model requires one.

See [contracts](knowledge-contract.md) for exact JSON and [operations](knowledge-operations.md) for commands and recovery. Repository review/evidence lives in `docs/fable/derived/`. Graph behavior stays off by default until representative workload evaluation demonstrates benefit.
