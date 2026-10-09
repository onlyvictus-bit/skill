# Graphify integration contract

Use `graphify` only as a subordinate discovery and knowledge-graph specialist. Fable remains the governor; `docs/fable/` remains the single canonical project authority. A Graphify graph is a **derived** navigation/projection artifact and is **never authoritative**: it is not requirements truth, approval, proof of a complete read set, or completion evidence by itself.

## What to reuse

When the `graphify` skill/runtime is available, use it to improve open-world discovery and context efficiency:

- structural code extraction and call/reference relationships;
- semantic relationships across Markdown, text, papers, diagrams, and images when those sources are in approved scope;
- persistent graph navigation across sessions;
- SHA256-based incremental cache/update behavior so unchanged files do not need semantic reprocessing;
- community detection and high-connectivity concepts for orientation;
- path/query/explain operations for finding likely related material;
- Obsidian and wiki projections for human navigation;
- explicit edge provenance classes such as `EXTRACTED`, `INFERRED`, and `AMBIGUOUS`.

## Truth boundary

Treat Graphify results as **candidate discovery evidence**:

- `EXTRACTED` edges may seed the Fable candidate-document or candidate-symbol set, but the underlying source must still receive the normal Fable read receipt or structural verification before it can support a requirement or decision.
- `INFERRED` edges are hypotheses. They require source confirmation before use.
- `AMBIGUOUS` edges are review prompts, never facts.
- community labels, "god nodes", surprising connections, suggested questions, token-reduction figures, and generated wiki prose are navigation aids, not project authority.

Never allow generated Graphify reports, wiki pages, or Obsidian notes to feed back into requirement discovery as if they were independent primary sources. Tag them as derived and exclude them from authoritative-source discovery unless the task is explicitly auditing the projection itself.

## Safe execution pattern

Prefer a scratch working directory so Graphify's own output does not pollute the project write set. Point it at the approved project corpus, then import only the selected outputs under `docs/fable/derived/graphify/`, for example `graph.json`, a report, and an Obsidian projection. Bind every imported projection to the repository identity, HEAD/working-tree basis, Graphify version when known, and source-file SHA256 identities.

Graphify may identify a relevant file; that does not prove it was read. Fable still builds the required read set and requires a current **read receipt** for every required source. Graphify also cannot prove that no relevant file exists outside its graph, so combine it with the Topic Registry, explicit links/backlinks, Git history, lexical search, requirement IDs, and structural symbol references.

Respect source exclusions and privacy. Do not send secrets, credentials, `.env` files, private keys, dumps, or excluded sensitive material to a semantic extractor. Treat Graphify's sensitive-file skips as a signal to report coverage gaps without naming secret paths in user-facing output.

## Obsidian

Graphify's Obsidian output is useful as a human navigation view. Keep it derived from Fable/project sources. Obsidian may display links, communities, requirements, symbols, and traceability, but an edited local note is not canonical until Fable deliberately ingests it through the normal intake/authority process.

## Availability and install boundary

Do not auto-install Graphify or its Python package. Detect whether the skill/runtime is callable. If unavailable, record `GRAPHIFY_UNAVAILABLE` and continue with Fable's deterministic/standard discovery mechanisms. Lack of Graphify must not reduce the required source coverage or read-receipt gates.


# Graphify Memory Integrity Backbone

For large or complex projects, reuse the existing Graphify data before rebuilding it. Treat the imported Graphify graph/cache plus its repository/source/version metadata as a **persistent derived memory index** that Fable can reopen on every continuation session.

When the previous graph basis is still valid, preserve unchanged nodes/edges and **incrementally update only changed or newly discovered sources**. When source hashes, repository/branch/HEAD, aliases/renames, exclusions, or the Graphify runtime basis change, mark affected graph-derived relationships stale and refresh those portions before using them.

Reuse Graphify data to strengthen memory integrity in these ways:

- seed and expand the **required-read candidate set** from document/topic/link/community relationships;
- maintain candidate **requirement-to-document and requirement-to-symbol relationships** without re-discovering unchanged structure from scratch;
- recover code definition/reference/call/consumer relationships for integration and reverse-audit candidates;
- retain stable aliases/rename lineage so moved documents or symbols do not look like forgotten/new facts merely because paths changed;
- drive **staleness and excluded-source reconsideration** when a previously read, excluded, or linked source changes;
- identify connected but previously unreviewed sources that may contain requirements, constraints, decisions, or integration dependencies;
- reuse graph paths/communities to prioritize which sources must be inspected next while still requiring normal Fable read receipts;
- generate/update the human-facing **Obsidian projection** from the same derived relationships rather than creating another memory database.

Graphify memory is reusable **derived evidence**, not project truth. It may remember that two sources/symbols are related and help Fable find them again; it does not prove the semantics of the relation, prove that a file was completely read, authorize a requirement, satisfy a test, or mark work complete. It **never becomes the canonical requirement, approval, completion, or evidence store**. `docs/fable/` plus the underlying project sources remain authoritative.

On continuation, prefer this sequence when Graphify is available:

`load prior Graphify data -> validate basis -> incrementally refresh changed/new sources -> recover candidate relationships -> union with direct Git/lexical/link/symbol discovery -> build/revalidate required read set -> perform Fable read receipts -> continue governed work`.

If Graphify is unavailable, record `GRAPHIFY_UNAVAILABLE` and use the existing Fable fallback. Do not silently substitute model memory for the missing graph.


## Bundled operational implementation

Read [graphify-operation.md](graphify-operation.md) for executable entry points, exact inputs/outputs, dependency checks, verification, and failure handling. The full original source is preserved under `specialists/graphify/`; it is consumed through that adapter and the six-specialist operating contract. This supplements every rule above.
