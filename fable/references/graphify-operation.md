# Graphify: native derived graph workflow

Read [the full Graphify source](specialists/graphify/SKILL.md) after this adapter and the existing graphify-integration contract. Preserve its modes: full/deep extraction, incremental update, cluster-only, query/path/explain, HTML/Obsidian/Canvas/SVG/GraphML/Cypher exports, optional Neo4j push/MCP/watch/hooks, URL ingestion, cache/cost reporting and provenance.

## Preflight and input

Run `python <fable>/scripts/specialist_tools.py status` with the intended Python interpreter. `graphify_importable: false` means `GRAPHIFY_UNAVAILABLE`. Do not execute the source's automatic pip install, `--break-system-packages`, or POSIX cleanup snippets. Obtain install authorization for a named isolated environment if required. Inspect that installed runtime's real modules/signatures before adapting examples; the supplied skill is not the Python package.

Define approved corpus, exclusions/privacy rules, output directory, repository/source identities, desired modes and expected known relationship. Treat empty/unsupported corpora as an explicit result, not evidence of coverage. Respect the source's large-corpus choice boundary. Native semantic extraction may involve external models: disclose provider, purpose, payload, sensitivity and approximate size, then obtain the required per-call authorization.

## Actual workflow

1. Load prior graph and manifest if present. Validate repository identity, file hashes, exclusions and extractor version; mark drift before using old relationships.
2. Use native detection to inventory supported code/docs/papers/images and sensitive exclusions. Count supported versus excluded and failed sources. Never expose secret contents in logs.
3. Extract code with native structural APIs. For semantic sources use permitted native agents or an authorized provider and the full source's node/edge/hyperedge schema. If agents/providers are unavailable, mark the semantic portion UNVERIFIED. Initialize an empty semantic fragment for a genuinely code-only run so the subsequent merge never reads a nonexistent file.
4. Use semantic caches only when their source/extractor basis matches. Keep EXTRACTED/INFERRED/AMBIGUOUS classes and source locations. Model confidence scores are uncalibrated metadata, not measured probabilities or approval evidence. Keep failed chunks visible; a partial graph cannot prove a complete corpus read.
5. Merge structural/semantic nodes and edges, preserving source provenance and hyperedges. Use native build/cluster/analyze/export functions. Reject an empty graph when a known positive relationship was expected. Produce persistent graph JSON, audit report, source manifest, and requested visual outputs.
6. For updates, compute added/changed/deleted sources. Remove or explicitly invalidate all affected old entities/edges before merging replacements. Preserve unchanged extraction; persist the actual merged graph before rebuilding projections. Do not follow the original example's in-memory-only update and then rebuild from a different extraction file. If native incremental support cannot satisfy deletion/rename semantics, rebuild the scoped graph and label it a full refresh.
7. Query a known symbol/concept, shortest path and explain operations. Confirm cited relationships in their actual sources. Report missing matches honestly. Generated Q&A/wiki memory remains derived and must be excluded from independent primary-source evidence; otherwise the feedback loop counts its own answer as proof.
8. Save output/source hashes and extractor identity. Import only selected graph candidates and observations into Fable. Graphs never replace source reading, requirement authority or completion evidence.

## Operational modes and boundaries

Use source procedures for requested exports and query modes after runtime validation. Do not fabricate benchmark/cost numbers (the original cluster-only example's word count is a placeholder). Report unavailable token telemetry as unknown. `graphify-out` is an ordinary directory name, not inherently hidden. Avoid generating huge interactive views beyond documented limits.

Neo4j push is an external write requiring exact destination approval; don't put credentials in generated source or logged command lines. Hooks, CLAUDE.md integration, dependency installs and background watchers are separate operations, not implicit consequences of a read-only graph request. Use native Windows filesystem operations when on Windows.

## Behavior tests

In scratch data, create two code files with a known import/reference. Run native detect/extract/build, save graph, query the relationship, add a source, modify the dependency, then delete a source. Verify new edges appear and obsolete edges disappear or are explicitly stale. Verify a second unchanged run reuses the intended state. Inspect exported JSON/report and any requested rendered output. No hand-built substitute may be called a successful Graphify run.

If native runtime cannot run, deliver the bundled source/adapter with `GRAPHIFY_UNAVAILABLE` and exact unverified tests. Fable's direct discovery fallback remains usable for other tasks, but does not satisfy an explicit native Graphify demonstration.
