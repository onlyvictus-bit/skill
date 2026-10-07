# Semantica integration decision and complete intake review

Recommendation: implement an opt-in isolated local vector-plus-graph adapter, preserve Fable/Memory Integrity/claude-mon boundaries, and keep graph default off. The original thin-layer recommendation is sound. Its unstated qualification gaps would permit false completion if implemented literally as capability flags or ID overlap.

Intake: all 575 lines are preserved byte-for-byte in `../intake-plan.txt`, including all fourteen sections and final recommendation. Target baseline is `onlyvictus-bit/skill@81a25fa8de16391c05dc4236a5c1b6681d6a5048`. Upstream installed and tested is `semantica-agi/semantica@320761de5d040a54a3220acc563223b4a7ffdc51` (0.7.0). The earlier upstream reference in the supplied plan is not substituted for the actual runtime revision.

Source gap: the cited local `semantica-knowledge-gap-audit.patch` was not supplied and is unavailable. Its reported behavior was treated as an unverified prior assessment. This implementation supplies a new narrow structured auditor; it does not claim to have reviewed or applied that patch.

| Plan section | Resolution and concrete scope |
|---|---|
| 1 Starting point | Freeze target/upstream, reproduce baseline, disclose missing patch and unmeasured coding benefit |
| 2 Mechanism | Isolated Python worker selected over host import or separate manager |
| 3 Architecture | One front door/authority/protected history; disposable knowledge projection |
| 4 Downward execution | Independent task/mandatory units, source freeze, ACL-filtered vectors/hops, reopening, existing request context/measurement |
| 5 Upward evidence | Recursive real provenance and exact request/response receipts; whole-generation staleness blocks. Incremental dependent invalidation is future |
| 6 Nine capabilities | Mechanisms and limits mapped individually in semantica-integration.md; no automatic extraction/model answering |
| 7 Discovery vs qualification | Unreviewed discovery retained explicitly; current source identity never self-promotes semantic truth |
| 8 Contracts | Independent bridge v1; canonical task/pack/query/permission bindings; companion schema unchanged |
| 9 Audit | Independent curated propositions, exact conditions/polarity/source checks, transport separated, empty/unknown refused; general entailment future |
| 10 Lifecycle/security | Atomic CURRENT, writer lock, drift/branch corruption, revoked ACL, worker timeout, protected resume, explicit degradation. Whole rebuild and OS ACL limitations disclosed |
| 11 Packaging | New paired knowledge-v1 ZIPs plus exact manifest/verifier; original R3/R4 ZIPs unchanged, separate optional runtime |
| 12 Usage | Public knowledge-status/index/retrieve/audit plus existing offline workflow optional flags; ordinary no-knowledge use preserved |
| 13 M0–M7 | Small local walking skeleton and lifecycle faults complete; portable isolated-copy verification. Real installed-copy replacement and broad semantic/model qualification are not implied |
| 14 Measurement | Three held-out synthetic fixtures, three repeats, four configurations, latency/source recall/omission detection. No coding/model superiority; graph default off |

## Mechanisms compared

| Mechanism | Consequence | Decision |
|---|---|---|
| Import Semantica into host | Python <3.14 requirement and broad core dependency imports conflict with dependency-light host/3.14 support | Rejected |
| Independent Semantica manager/history | Competing task/source/completion authority and duplicate state | Rejected |
| Isolated bounded optional adapter | Explicit pin/interpreter, unchanged authority/history, observable local mechanisms and failure boundary | Selected |
| Direct inspection only | Lowest setup/latency on small corpora, no linked discovery API | Keep as baseline/default; graph only opt-in |

## Root causes found in actual code

Upstream ContextGraph auto-creates undefined endpoint nodes; its neighbor traversal does not apply bridge ACL/time policy and limits after breadth-first expansion. ContextGraph.query is a keyword mechanism, not measured semantic retrieval. VectorStore may initialize an embedding generator; fallback embedding can be random. VectorRetriever pads/truncates dimensions. Cosine scores can be negative. ContextRetriever may mask failures with empty results. The generic ontology validate route is a placeholder, while run_shacl_validation actually runs SHACL. track_relationship does not establish a premise chain; track_entity with used_entities does.

Bridge remedies: reject undefined endpoints before Semantica; filter the entire permitted graph and recursive premises before worker calls; issue one-hop neighbor calls with bridge BFS budgets; use explicit exact-dimension finite vectors and exact embedding identity; use actual VectorRetriever directly; report errors; run actual SHACL and real recursive lineage; preserve no-truth boundary. Upstream files inspected: context/context_graph.py, context/context_retriever.py, vector_store/vector_store.py, embeddings/embedding_generator.py, ontology/ontology_validator.py, provenance/manager.py and provenance/storage.py at the pinned revision.

Adversarial review found empty observed audit could pass, a caller backend label could fake readiness, path receipts could include unauthorized/expired edges, premise metadata could claim untracked ancestry, protected audit could bypass the canonical map, copied map directory resolution could use the wrong folder, explicit verification basis could be ignored without a flag, and execution task binding could be skipped by audit. All routes now fail closed using real history/worker replay and a shared exact task binder. A valid non-axis vector revealed non-idempotent floating normalization; bindings retain original finite vectors and normalize once for worker scoring. Optional packs now also compare embedding provenance to the actual projection.

## Weakest link and cheapest falsifier

The weakest link is semantic adequacy: explicit vectors, graph assertions and the independently supplied structured proposition oracle may be wrong. The bridge observes identity, structure and declared proposition agreement; it cannot establish natural-language truth. Cheapest meaningful falsifier is a held-out real project task with independently reviewed source propositions, fixed model/tool budgets and direct-inspection baseline. If graph adds misleading dependencies or no measurable outcome improvement, keep it opt-in or disable expansion. No invented confidence probabilities or readiness-to-quality promotion.

Future: live embedding/extraction/reranking, global/DRIFT/distributed graph, incremental invalidation, real model/coding comparisons and active skill installation. These require new qualified execution/consent routes where applicable; they are explicit backlog, not hidden completion claims.
