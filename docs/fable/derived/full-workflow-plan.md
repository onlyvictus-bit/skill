# Full workflow completion plan

The earlier implementation translated the design into an offline prototype and left extraction, per-predicate ontology, text embeddings, selective invalidation, test ingestion and task-relative admission unfinished. This milestone restores those requirements. The original intake remains unchanged. Existing project-1 records stay readable; automatically constructed project-2 adds stronger contracts.

## Decision and alternatives

Manual projections are the compatibility baseline but cannot close the coding workflow. A local source-linked adapter is selected because it reuses the pinned worker, protected CAS history, exact request binding, and external Fable governor. A distributed platform adds unsupported permissions/deployment obligations and remains the original deferred scope. Local Python AST extraction is chosen for code; precise affirmative Semantica regex extraction is used for prose. Dynamic calls, unresolved imports, other languages, and conditional/negated prose receive diagnostics rather than fabricated facts.

Semantica's default text embedder can silently produce seeded random vectors when dependencies/model weights are missing. Therefore local TF-IDF is the default automatic text search; optional deterministic LSA measures distributional similarity on the authorized candidate corpus. No downloaded weights or provider calls. OOV queries must be explicit. Meaning-level quality remains a measured task-class property, not a truth claim.

## Proof units and coverage

| Requirement | Original gap | Observable exit |
|---|---|---|
| REQ-15 | Structural and semantic extraction | AST declarations/imports/calls and affirmative real Semantica regex relations carry exact UTF-8 byte spans and original unit references; uncertainty diagnostics remain visible |
| REQ-16 | Automatic embeddings/search | Authorized text-only lexical and latent/hybrid search, no random fallback, deterministic replay and OOV negative controls |
| REQ-17 | Ontology | project-2 canonical per-predicate domain/range rules enforced locally and by actual SHACL; legacy project-1 preserved |
| REQ-18 | Selective invalidation | Relevant source/dependency closure blocks stale mandatory evidence; unrelated same-branch commit succeeds; unchanged extraction reused in atomic refresh |
| REQ-19 | Reverse graph and exclusions | outgoing/incoming/both direction bound to query and replay; authorized per-candidate reason codes; denied information aggregate only |
| REQ-20 | Upward tests/code chain | Real local unittest subprocess records pass/fail/error/skipped/empty/timeout and exact observed code snapshot; linked TestCase/TestRun cannot fabricate success |
| REQ-21 | Qualified evidence and Fable consumption | Separate task-relative admission rechecks protected CAS, pack, independent oracle and required local tests; public check is a declared Fable automated test; unsupported assurance classes block |
| REQ-22 | Benefit evaluation | Held-out equal-budget direct/lexical/graph/audit comparison with actual code outcomes and fault detection; no model-quality superiority assertion; default off unless benefit demonstrated |
| REQ-23 | Release and publication | Full existing/new suites, real pinned runtime, paired portable archives, hostile review, CI and leased GitHub publication |

## Mechanisms and failure controls

Generation-v2 adds a construction manifest while keeping old generation-v1 exact. A source edit invalidates owned facts and recursive premises/dependents. Access filtering precedes embeddings and every hop. Branch changes block. Historical generation identities remain immutable; current relevant bytes are reopened before retrieval, request use, and admission. Refresh caches are observations of unchanged extraction, never semantic review.

A separate admission artifact binds task criteria, purpose, required check classes, oracle/reviewer identity, access policy, pack, actual protected run/CAS and local test snapshot. Discovery packs retain coverage UNVERIFIED. Fable schema-2 stays exact: it consumes admission through its ordinary declared automated-test route. The bridge does not modify the external governor or claim that a caller-supplied READY flag is evidence.

Weakest link: extracted edges may cost more and mislead more than they help. Cheapest falsifier: cross-file code dependency retrieval followed by edits, branch/access changes and actual test failures. Promotion depends on measured held-out results; failure keeps graph optional. Independently curated oracles do not derive expected claims from retrieval output. Matching IDs alone are insufficient.

## Execution and ownership

Root owns existing files, impact/retrieval-v2/test/admission integration, publication and canonical Fable records. Extraction agent owns only extraction.py and its tests. Offline-engine agent owns only offline_engine.py and its tests. Both prove RED then GREEN. Independent adversarial agents inspect finished work. Native Unlazy gates derive from these canonical requirements and do not create a second authority. Cortex routes source/privacy decisions, Blueprint records mechanisms, Triangulate tests hostile failure cases, Release Helper binds packaged/published bytes.

Paid/live model services, global/community/DRIFT, distributed deployment, installed ChatGPT replacement and complete-corpus semantic understanding remain the original explicitly deferred external layers. The referenced historical audit patch is absent; do not claim to have reproduced it. This milestone completes the offline coding workflow and measures offline outcomes; it cannot manufacture a live model benefit.
