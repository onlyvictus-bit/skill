# Automatic project-2 workflow

## Scope and contracts

Keep the existing source map, access policy, task obligations and outer evidence-pack-v1 contracts. Automatic projection schema2 uses ontology project-2 and source-qualified IDs. Generation schema2 adds a construction manifest; project-1/generation1 remain exact and retain their stricter whole-repository freshness behavior. Existing immutable histories are retained. Bridge1.0 protected receipts remain historical; use their matching package from the prior Git commit to replay them, or create a new authorized current run. Do not rewrite old receipts.

Python AST extraction reads exact source bytes without importing project code. The manifest records parser identity, frozen hashes, exact UTF-8 byte spans, source units, local imports/static references, unresolved diagnostics and cached fragments. Cache reuse requires sealed matching manifest, source/unit/path/parser identity; global import resolution is recomputed. Other languages remain source navigation. Static edges are candidates, not runtime call coverage.

The pinned Semantica regex extractor accepts a narrow relation DSL: each nonblank line must contain one standalone affirmative identifier relationship, such as `Client depends on Worker.` Any other prose/context refuses extraction for the whole document. Mixed prose, negations, conditions, examples and fenced code remain source navigation requiring review. Relations are unreviewed and carry checked byte spans and heuristic scores. This does not provide free-text semantic entailment.

Text retrieval fits only the current authorized candidate text. Lexical uses local sklearn TF-IDF; LSA uses deterministic corpus SVD; hybrid combines lexical and latent similarity. Fitted corpus/configuration/version digests bind the receipt and replay. OOV, empty-token and zero latent vectors fail explicitly. No model weights/downloads/random embedding fallback or provider calls. LSA quality depends on the corpus; lexical is default.

Same-branch unrelated commits are allowed when the declared source/dependency basis remains current. Branch changes block. Source edits exclude stale owned facts and recursive premises/dependents before fitting/hops; stale mandatory evidence blocks. Refresh parses changed sources, reuses valid unchanged fragments, and publishes an immutable generation atomically. Per-query corpus fitting depends on all authorized candidates, so a change to that fit scope invalidates its old text receipt even when a retained unit did not change. Undeclared/dynamic dependencies remain explicit uncertainty.

Incoming traversal uses original authored edges in reverse; it does not assert an inverse predicate. Receipt direction is bound and replayed. Each fully authorized excluded candidate receives stale/expired/notyetvalid/premise_unavailable/not_selected/limit reasons. Denied nodes have aggregate counts only, and premise identifiers are not exposed. Over-budget packs fail; mandatory units are never truncated.

## Commands

All commands use `python scripts/memory_integrity_workflow.py` and an explicit `--claude-mon-root`. Use an isolated absolute `--worker-python` when graph/extraction operations are required. Project/index arguments are `--project-root` and `--index-dir`. Current obligations are `--policy-file` and `--task-file`.

1. `knowledge-project --source-map sources.json` builds the automatic projection. Add the worker to observe relation DSL extraction.
2. `knowledge-refresh --source-map sources.json` publishes a refreshed generation and reports actual cache reuse. Optionally add `--test-receipt tests.json` to ingest freshly replayed observed tests into the projection.
3. `knowledge-impact` plus current policy/task reports visible stale sources and affected nodes.
4. `knowledge-retrieve --query-text "Python function api.dispatch" --direction outgoing --embedding-mode lexical --evidence-pack /absolute/new-pack.json` reopens candidate and mandatory units. Graph bounds remain seeds/hops/visits/results and task max_bytes. Vector/query-model mode remains available for imported project-1 only.
5. `knowledge-test --test-path test_worker.py --test-timeout 60 --output /absolute/new-tests.json` explicitly executes local unittest source declared in the map. The policy must permit the entire declared execution scope. The observer distinguishes pass/fail/error/skipped/expected_failure/unexpected_success/empty/timeout. Snapshot covers all project Python and declared non-Python bytes; undeclared data/dependencies and execution coverage are not qualified. Verification reruns the same tests and reopens the same snapshot. Tests may execute project code; Python socket blocking is best effort, not an OS sandbox.
6. Pass the pack through the existing protected `offline-run` with exact execution_task_digest and knowledge basis. Keep a separately authored structured claim oracle; a free-text answer remains a partial semantic observation.
7. `knowledge-admit --source policy.md --run-map /absolute/run/run-map.json --expected-claims oracle.json --admission-spec admission-spec.json --test-receipt tests.json --admission-file /absolute/new-admission.json` creates task-relative qualification after fresh protected-run/CAS/pack/oracle/test checks.
8. `knowledge-check-admission` with the same inputs and saved admission file repeats verification. Use this exact command as an ordinary Fable schema2 automated test with expect exit=0, mapped to the applicable requirement/criteria. List the spec, source/index/run/admission artifacts in its approved artifact set. Existing Fable consumes the actual subprocess observation; the bridge neither alters its schema nor completes Fable recursively.
9. `knowledge-benchmark --output /absolute/new-benchmark.json` with the pinned worker runs equal-budget held-out deterministic patcher experiments. These are offline coding fixtures, not model coding superiority.

## Admission specification

```json
{"schema_version":1,"task_id":"coding","purpose":"verify retry change","criteria":{"REQ-CODE-1":["test_worker.Check.test_retry"]},"required_checks":["source_identity","protected_request","structured_oracle","local_tests"],"oracle_review":{"reviewer":"independent reviewer","oracle_digest":"<SHA256 of canonical oracle JSON>"}}
```

The first three checks are mandatory. `local_tests` requires every criterion to name nonempty actually passed case IDs. Optional `python_syntax_extraction` freshly re-extracts independent required/oracle source syntax and refuses unsupported/failed parsing or cache disagreement; it does not prove all runtime calls. `resolved_static_dependencies` additionally refuses required-source unresolved/dynamic dependencies. `reviewed_propositions` requires reviewed graph propositions for the independent oracle and remains manual review evidence. Requested unsupported assurance classes, including universal semantic truth, block.

Admission binds exact task instructions, criteria/purpose/spec, policy, pack/generation, reviewed oracle, actual protected check/audit and observed test receipt. Any relevant drift, access change, false structured proposition, missing stage, failed/missing test, or changed admission bytes blocks. Verdict is ADMITTED_FOR_DECLARED_OFFLINE_CHECKS; semantic_truth remains UNVERIFIED. Tests cannot independently establish oracle truth, arbitrary free-text fidelity, complete corpus understanding, or every possible runtime behavior.

## Ontology

Use the canonical TYPE_RULES in offline_engine.py for project-2 domain/range eligibility. Local host checks and genuine SHACL render the same matrix. Code/interface implements requirements; TestCase/TestRun tests code/interface/requirements/assertions; fact contradictions/supersession have fact domains; sources, static references, supports and derivations retain explicit typed ranges. Old project-1 relationship conventions are not retroactively changed. Type conformance proves structure only.

## Recovery and release

Preserve previous generation and protected history on a failed build/test/admission. Reconcile retained writer locks before retrying; no automatic source repair or uncertain provider retry. After source edits refresh, retrieve a new pack and create a new protected run as needed. A historical generation never silently qualifies stale current evidence.

Keep the matching knowledge-v1 ZIP family at bridge1.1 with its separately pinned runtime; R3/R4 archives remain unchanged. Roll back to the prior GitHub commit for bridge1.0 bytes. Publication does not replace the user's installed ChatGPT skill. Live providers, learned embedding services, global/community/DRIFT and distributed operation retain separate qualification boundaries.
