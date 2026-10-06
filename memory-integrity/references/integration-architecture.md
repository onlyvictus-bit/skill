# Integration architecture and build plan

## Authority split

```text
project/original sources
        |
        v
source hashes + extraction evidence
        |
        v
verifiable source coverage manifests/receipts
        |
        +------------------------+
        |                        |
        v                        v
Fable canonical governance   Graphify derived relationships
(requirements/approval/      (candidate navigation, never proof)
evidence/completion)
        |                        |
        +------------+-----------+
                     v
             task-specific retrieval
          Aider RepoMap where useful
                     |
                     v
             tiktoken budget fit
                     |
                     v
            direct source reads
                     |
                     v
            processing receipts
                     |
                     v
             governed execution
                     |
                     v
       AgentMemory durable continuity
       (facts/lessons, not authority)
```

One component, one job. Do not add another planning/governance framework.

## Components

### Fable

Owns canonical requirements, plan, approvals, state, completion evidence, and authorization boundaries. GPT Monitor produces evidence Fable may bind; it must not become a second control plane.

### Graphify

Persistent derived relationship/discovery memory. Useful for recovering linked code/docs and identifying candidate reads. A graph edge is not a complete-read receipt.

### AgentMemory

Durable episodic/fact continuity across sessions. GPT Monitor verifies live remember/recall/delete behavior. A healthy memory service does not prove source coverage or source freshness.

### Aider RepoMap

Use as an **ephemeral code relevance ranker**, not a completeness engine.

Current Aider `RepoMap` source verified on 2026-09-29 shows Tree-sitter-based tag extraction, NetworkX PageRank, mentioned-file/identifier weighting, bounded repo-map construction, and a Pygments-related fallback path. It also checks its tag cache against file mtime.

Two important consequences:

1. Wrap cache trust with content/Git blob hashes if Fable integrity depends on it; mtime is not a sufficient authority identity.
2. Do not use Aider's internal token estimate as canonical accounting. Current `RepoMap.token_count()` samples lines and estimates token count for longer text. Use explicit `tiktoken` accounting for governed budgets.

Aider is Apache-2.0 in the currently inspected repository.

### tiktoken

Use for deterministic token counts when available. Current upstream `encoding_for_model()` raises `KeyError` when a model is not recognized and instructs callers to select an encoding explicitly. Preserve that fail-closed behavior.

Do not derive the model's context limit from tiktoken. Store the context limit as explicit provider/model configuration and reserve output + fixed prompt/tool/history overhead + safety margin.

### Docling

Use only on the document-ingestion route. Current Docling materials expose `DocumentConverter` and `HybridChunker`; the canonical coverage ledger should still be ours so extraction/chunking library behavior cannot silently redefine completeness.

Recommended document path:

```text
original binary hash
  -> DocumentConverter
  -> DoclingDocument structured representation
  -> extraction diagnostics/page inventory
  -> canonical JSON hash
  -> GPT Monitor coverage chunks/receipts
```

### Repomix

Keep as an export/interoperability tool, not memory authority. A compressed/signature-only package cannot satisfy a requirement to process implementation details that it omitted.

## Stronger build plan

### M0 — Semantics and threat model

Define exactly what `MEMORY`, `EXTRACTION`, `COVERAGE`, `UNDERSTANDING`, `STALE`, `TRUNCATED`, and `READY` mean. Define what each mechanism cannot prove.

### M1 — Deterministic source core

Implemented in this skill for canonical UTF-8 text/code:

- SHA-256 source identity;
- strict UTF-8, no replacement decoding;
- deterministic primary byte ranges;
- per-chunk hashes;
- exact reassembly;
- manifest digest;
- gap/duplicate/hash verification.

### M2 — Processing ledger and resume

Implemented in this skill:

- append-only attempts;
- `COMPLETE/PARTIAL/TRUNCATED/ERROR`;
- result-hash slot;
- missing/noncomplete listing;
- source/manifest/chunk binding;
- retry state via monotonic attempt numbers.

Next hardening for high-concurrency runners: serialize receipt appends or move to atomic per-attempt files plus an index; then adversarially test crash-between-write/fsync/rename cases.

### M3 — Fable binding

Add a versioned Fable contract migration only in the Fable project itself. Bind approval/state to a `source_basis_digest` derived from authoritative source identities and required read receipts. Source changes should reopen dependent proof obligations.

Do not modify `docs/fable/` from this standalone monitor without that governed migration.

### M4 — Token budgeting

Implemented as a fail-closed optional script. When `tiktoken` is installed, bind the chosen encoding/version and explicit context configuration to the execution evidence.

### M5 — Aider adapter

Add only after M1-M4 are proven. Inputs: user-mentioned files/symbols, changed files, failing tests, Graphify candidates, Fable requirement links. Output: ranked candidate source paths/symbols. Then open the real source; RepoMap output never creates a complete receipt.

Cache candidate maps under a git tree/source-hash identity rather than trusting timestamps alone.

### M6 — Document extraction

Add Docling behind the extraction contract. Persist page/element/table provenance and explicit extraction failures. `COVERAGE_COMPLETE` over Docling JSON must remain `OVERALL: BLOCKED` if extraction is partial/unknown.

### M7 — Semantic audit

Add source-linked result schemas and independent challenge checks:

- each consequential finding cites source units/ranges;
- verify cited ranges exist and hashes match;
- sample cross-chunk rules/exceptions/numbers;
- test contradictions and boundary conditions;
- reopen source text for disputes.

This increases confidence but must never be advertised as a mathematical proof of understanding.

### M8 — Scale and concurrency

Benchmark representative 50 MB+ sources. Measure manifest size, chunk count, receipt write rate, resume time, hash throughput, tokenization throughput, and peak memory. If verbose manifests dominate, move to interval/Merkle representations while preserving exact verification.

## Cheapest falsifiers

Before deeper integration, deliberately:

1. remove one receipt — verifier must name the missing chunk;
2. duplicate one attempt number — verifier must reject evidence;
3. modify one source byte — old evidence must become stale;
4. corrupt one chunk file — exact reassembly must fail;
5. mark document extraction `PARTIAL` while all chunks are complete — overall must remain blocked;
6. use an unknown model without an explicit tokenizer — token accounting must fail, not guess;
7. make AgentMemory reachable but skip roundtrip — memory must remain unverified.

If any one of these falsely goes green, stop and repair the proof model before adding retrieval sophistication.

## Implemented source-basis additions

The standalone skill now includes two pieces that the earlier plan treated only as future architecture:

### `scripts/source_registry.py`

Provides a first-class multi-source registry for file-backed required/optional sources and produces a deterministic `source_basis_digest`. It audits every registered required source against current hashes and its linked source-coverage manifest/receipts.

This is **evidence machinery**, not Fable authority. Fable may import/bind the digest in a future schema migration.

### `scripts/structural_units.py`

Provides stable line/paragraph unit identities with exact byte ranges/hashes and optional mapping to source-coverage chunks. It exists for source-linked claims and semantic auditing; byte-range chunk coverage remains the preservation authority.

### Session bridge

`memory_watchdog.py` now distinguishes current-session roundtrip health from cross-session/restart persistence using `bridge-seed` and `bridge-verify`.

The architecture therefore has three distinct continuity proofs:

```text
source identity/coverage -> did we process the declared source basis?
semantic audit          -> did the conclusions survive source-linked challenge checks?
AgentMemory bridge      -> did durable memory survive the tested boundary?
```

None substitutes for another.
