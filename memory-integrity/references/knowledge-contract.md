# Bridge v1 contracts

All JSON is strict: duplicate/unknown keys, NaN/Infinity, missing keys and messages above 8 MiB are rejected. Hashes use canonical JSON (sorted keys, compact separators, UTF-8 without ASCII escaping) and SHA-256. Bridge schema is independent of the unchanged claude-mon engine schema.

## Source map

```json
{"schema_version":1,"workspace_id":"demo","repository":"owner/repo","sources":[{"id":"policy","path":"spec/retry.txt","authority":"AUTHORITATIVE"}]}
```

Paths are relative to the explicit project root. Absolute paths, parent traversal and symlinks are rejected. Source input is UTF-8, nonempty, at most 1000 files and 8 MiB total in this initial bridge. Unit IDs/ranges/hashes come from the companion partition engine (4096-byte units), not an invented chunker. Repository branch and commit, source bytes, observed/build time and assertion validity time are separate.

## Projection

```json
{"schema_version":1,"ontology":"project-1","embedding":{"model":"reviewed-vectors-v1","dimension":2,"evidence_class":"MANUAL_REPORTED"},"nodes":[{"id":"policy:retry","type":"Assertion","text":"Never retry writes","source_units":[{"source_id":"policy","unit_id":"U000001"}],"polarity":"negative","conditions":["write operation"],"derivation":null,"valid_from":null,"valid_until":null,"review_status":"unreviewed","vector":[1,0]}],"edges":[]}
```

Types: Requirement, SourceVersion, SourceUnit, Component, Symbol, Interface, TestCase, TestRun, Decision, Assertion, AuditFinding. Predicates: DEFINED_IN, REFERENCES, DEPENDS_ON, IMPLEMENTS, TESTS, SUPPORTED_BY, CONTRADICTS, SUPERSEDES, DERIVED_FROM. Edges have exactly `id,subject,predicate,object,source_units,conditions,valid_from,valid_until`. Undefined endpoints are rejected. A TESTS edge is not a passing TestRun.

Nodes carry polarity `positive|negative|unknown`, conditions, review status `unreviewed|reviewed`, optional derivation `{"rule":"reviewed rule identifier","premises":["node-id"]}` and offset-qualified ISO timestamps or null. Cyclic derivations are rejected; permission/validity exclusions propagate through premises. The bridge retains the rule name and premises; it does not evaluate arbitrary logic rules. Explicit supplied vectors must be finite, nonzero and the exact dimension. Query model identity must match; no random-vector fallback or padding/truncation.

## Access and task contracts

```json
{"schema_version":1,"workspace_id":"demo","task_id":"review-retry","allowed_source_ids":["policy"]}
```

```json
{"schema_version":1,"task_id":"review-retry","required_units":[{"source_id":"policy","unit_id":"U000001"}],"require_graph":true,"max_bytes":100000,"execution_task_digest":null}
```

`execution_task_digest:null` permits discovery only. Before protected execution, set it to SHA-256 of canonical `{"schema_version":3,"instructions":"the exact --task string"}`. A different execution task is refused before new run state. The task owner must independently declare mandatory sources/units; retrieval never derives the expected contract from its own result. Mandatory units survive ranking; a revoked or oversized requirement blocks rather than truncates. The bridge does not prove that the human task contract is semantically adequate.

An evidence pack binds schema/workspace/task, generation, source/policy/task digests, exact embedding identity, declared required units, reopened source units, assertions, recursive premises and query/result paths/limits/provenance/SHACL. Its coverage and semantic audit are UNVERIFIED. The pack digest covers all fields except itself. A graph-required saved pack is freshly replayed with the exact selected pinned worker and current permission/validity projection; a caller-written backend label cannot qualify it.

The execution sidecar binds the real accepted ledger attempt/work-item IDs, CAS request/response hashes, task digest and exact canonical pack material from the serialized request. No companion result/ledger schema is changed. Missing or changed sidecars/packs block resume and required verification; a plain run cannot satisfy an explicit knowledge contract.

## Structured audit oracle

Supply an independent JSON list of `{"id":"C1","text":"Never retry writes","polarity":"negative","conditions":["write operation"],"source_units":[{"source_id":"policy","unit_id":"U000001"}]}`. A structured response interpretation may be JSON text `{"claims":[...same schema...]}`. Ordinary free text is PARTIAL rather than silently parsed as complete.

Source support means exact agreement with a separately supplied curated proposition oracle whose referenced current source units are present. It is not independent natural-language entailment. Prompt inclusion and ID overlap are transport measures. Answer coverage, proposition mismatch, unsupported IDs and contradictions are separate checks. Stage state OBSERVED/PARTIAL/FAILED/UNOBSERVED preserves uncertainty, empty expected denominators are null, and nonempty expected obligations cannot pass empty observed stages. Verdict `PASSED_FOR_DECLARED_STRUCTURED_CHECKS` still carries `semantic_truth:UNVERIFIED`.

## Audit integrity correction — 2026-10-08

Compare actual retrieved and serialized prompt assertions, including their text, polarity, conditions and source references, against the independent oracle. Matching IDs never replace proposition comparison. A prompt containing the referenced source unit may establish inclusion of that curated proposition as a transport measure; it cannot conceal an explicitly conflicting assertion in the same prompt. Reopen oracle references independently of the retrieval result before observing source availability. Uninstrumented source availability is UNOBSERVED. A PARTIAL stage can reveal a present contradiction, but absence from its observed subset cannot establish an observed loss.

Validate the nested retrieval receipt as well as the outer pack digest. Permit only known backend and receipt keys, typed limits/exclusions, and explicit qualification states. DIRECT_INSPECTION_DEGRADED has empty results/lineage/limits and SHACL UNVERIFIED. TEST_ONLY synthetic retrieval cannot pass protected-execution preflight. SEMANTICA_OBSERVED requires the exact pinned runtime identity and fresh replay before protected execution. A caller-written CONFORMS or lineage entry cannot qualify a degraded pack. Valid v1 source/pack/companion schemas remain unchanged; formerly accepted forged metadata is rejected.
