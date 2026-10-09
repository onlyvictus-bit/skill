# Operating the optional knowledge layer

All commands use `scripts/memory_integrity_workflow.py` and an explicit `--claude-mon-root`. Existing commands and historical releases remain valid. No automatic background index or worker installation occurs.

1. Create an isolated Python 3.12 environment outside the skill. From this repository install `python -m pip install -r semantica-runtime/requirements-lock.txt`. If needed create it with `python3.12 -m venv /absolute/runtime`; use that environment's absolute Python path below. The lock pins Semantica to an immutable Git revision and pyshacl. It is deliberately substantial; Semantica core imports require its core dependencies.
2. Write a source map, explicit reviewed projection, current policy and independent task contract using [bridge contracts](knowledge-contract.md).
3. Check the selected environment: `python scripts/memory_integrity_workflow.py knowledge-status --claude-mon-root /absolute/claude-mon --worker-python /absolute/runtime/bin/python` (Windows: `Scripts/python.exe`). Without a worker, readiness is DEGRADED/BLOCKED for graph-required tasks.
4. Build: `python scripts/memory_integrity_workflow.py knowledge-index --claude-mon-root /absolute/claude-mon --project-root /absolute/project --index-dir /absolute/project-index --source-map sources.json --projection-file projection.json`.
5. Retrieve: `python scripts/memory_integrity_workflow.py knowledge-retrieve --claude-mon-root /absolute/claude-mon --project-root /absolute/project --index-dir /absolute/project-index --policy-file access.json --task-file obligations.json --query-vector '[1,0]' --query-model reviewed-vectors-v1 --worker-python /absolute/runtime/bin/python --max-hops 2 --seeds 1 --max-visits 100 --max-results 50 --evidence-pack /absolute/new-pack.json`.
6. For the existing offline workflow, pass `--knowledge-pack /absolute/new-pack.json --knowledge-index /absolute/project-index --knowledge-root /absolute/project --knowledge-policy access.json --knowledge-task obligations.json --knowledge-worker-python /absolute/runtime/bin/python` to `offline-run` alongside the ordinary source/task/responses/run-dir options. Bind the execution digest first. The pack goes through existing context measurement before approval and dispatch. This is an offline fake-provider fixture, not live model qualification.
7. Verify with the same knowledge index/root/policy/task/worker options and optionally `--require-knowledge`. An explicit knowledge basis already requires verification. Use `knowledge-audit` with project/index/policy/task/worker, `--source`, verified `--run-map` and separate `--expected-claims oracle.json` to inspect structured gaps. Unknown semantic stages remain blocked/unverified.

Never delete uncertain execution history or blindly resend. CURRENT exposes a single immutable generation. A writer lock blocks parallel publication; after a crashed writer, inspect process state and retained generation/pointer files before explicitly removing a confirmed stale lock. A failed prepublication build leaves the previous CURRENT usable. Do not remove or overwrite historical generations to repair freshness. Rebuild after source/branch/commit changes; all referenced source hashes and current ACLs are checked again. Any changed current pack, task or policy requires a fresh isolated run rather than resuming a different basis.

This v1 supports atomic pointer replacement, not full power-loss durability on all filesystems; it fsyncs files but does not claim distributed transactions or OS directory-fsync guarantees. It rebuilds whole generations; dependency-based incremental optimization is future work. Raw index files are not an ACL boundary.

Portable release: keep `memory-integrity-knowledge-v1.zip` with `claude-mon-knowledge-v1.zip`. Run `python -B release/Verify-Knowledge-Bridge.py`; select the real runtime through `KNOWLEDGE_WORKER_PYTHON` to also exercise actual Semantica tests. Default host checks explicitly skip the optional runtime tests. The paired bridge ZIPs contain the skill/companion; the separately pinned runtime installer remains in the repository. Run the fixture comparison from memory-integrity/scripts: `python -B -m knowledge_bridge.benchmark --claude-mon-root /absolute/claude-mon --worker-python /absolute/runtime/bin/python`.

Rollback: use the retained R4 pair and its verifier or revert the bridge commit in Git. Preserve run histories; graph-required v1 runs still require their bridge for verification. No active ChatGPT skill replacement or generic native qualification is part of this release. Full coding/model quality and representative workload benefit remain UNVERIFIED; default graph behavior stays off.

Integrity repair: if preflight rejects a nested receipt, preserve the old run and rebuild a current pack through knowledge-retrieve. Do not edit or rehash a receipt to invent a backend, lineage or SHACL result. knowledge-audit now reports conflicting actual retrieval/prompt assertions even when IDs match. It independently reopens the oracle's permitted source references, so an unretrieved source unit is a retrieval/context gap rather than a fabricated source failure. Partial observations remain limitations.

Automatic coding workflow: use [project-2](knowledge-project-2.md) for knowledge-project/refresh/impact, text queries and reverse traversal, observed local tests, admission and Fable consumption. The explicit projection/vector instructions above remain the project-1 compatibility route.


### Remediation release v2 (security patch)

The immutable original `knowledge-bridge-v1` archive pair stays in place for history.
The new version is `knowledge-bridge-v2`, with archives `memory-integrity-knowledge-v2.zip`
and `claude-mon-knowledge-v2.zip`, and its own matching
`release/Knowledge-Bridge-Manifest-v2.json`. Regenerate only the v2 archives
using `python -B release/Build-Knowledge-Bridge.py` on an authorized
checkout, then run `python -B release/Verify-Knowledge-Bridge.py`.
Do not rewrite v1 artifacts or claim a verified active release when the
current-tree manifests diverge. Runtime third-party wheel hashes remain
UNVERIFIED until fully pinned to measured distribution contents.
