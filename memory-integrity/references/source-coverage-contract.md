# Verifiable Source Coverage contract

## Purpose

Answer a narrower, mechanically testable question:

> Did the canonical source representation remain intact, and did every required primary chunk receive valid processing evidence?

Do not turn that into the stronger claim “the model understood every word.”

## Proof layers

| Layer | Mechanically provable? | Evidence |
|---|---:|---|
| Original binary identity | Yes | SHA-256 + size |
| Canonical text/code identity | Yes | SHA-256 + strict encoding |
| Chunk preservation | Yes | byte ranges + per-chunk SHA-256 + exact reassembly |
| Every primary chunk has processing evidence | Yes | hash-bound receipt ledger |
| Extraction captured every visual/document fact | Not universally | extractor/page diagnostics + independent inspection |
| Model understood every sentence | No absolute proof | source-linked semantic audits, challenge checks, independent review |

## Canonical source

For direct UTF-8 text/code, canonical bytes equal the source bytes and extraction is `NOT_APPLICABLE`.

For PDF/DOCX/PPTX/images/scans:

1. Hash the original binary.
2. Extract to a structured canonical representation.
3. Preserve extractor identity/version and extraction status.
4. Run coverage over that canonical representation.
5. Keep extraction state separate from coverage state.

For Docling, prefer a structured representation such as `DoclingDocument` JSON over lossy flattened prose when hierarchy/table/layout provenance matters.

## Primary coverage

The bundled core uses contiguous UTF-8-safe primary byte ranges. Ranges must cover `[0, source_size)` exactly once. Context overlap, if added by a higher-level processor, must never count as additional primary coverage.

A manifest binds:

- source path, size, SHA-256;
- original path/hash when extraction is involved;
- extractor identity and extraction status;
- ordered chunk ids;
- start/end byte ranges;
- chunk sizes and SHA-256 hashes;
- a deterministic manifest SHA-256.

The verifier reconstructs bytes from chunk files and requires the resulting hash to equal the canonical source hash.

## Receipts

A receipt binds to the current source hash, manifest hash, chunk id, chunk hash, attempt number, status, timestamp, and optional result hash.

Statuses:

- `COMPLETE`: this processing attempt finished for the primary chunk.
- `PARTIAL`: some required work is incomplete.
- `TRUNCATED`: input/output was cut and must not count complete.
- `ERROR`: processing failed.

Retries are append-only attempts. The highest valid attempt number controls the current chunk state. Reusing the same attempt number is invalid evidence.

Counts alone are insufficient. `726/726` can still hide a duplicate plus a missing chunk; identities and hashes are required.

## State separation

- `EXTRACTION: NOT_APPLICABLE | COMPLETE | PARTIAL | ERROR | UNKNOWN`
- `COVERAGE: COVERAGE_COMPLETE | PARTIAL | INVALID | STALE`
- `OVERALL: READY | BLOCKED`

`READY` requires current source/origin hashes, valid exact reassembly, complete latest receipts for every primary chunk, and extraction `COMPLETE` or `NOT_APPLICABLE`.

## Resume and staleness

The ledger is restartable because finished chunks remain evidenced. `pending` lists only missing or latest-noncomplete chunks.

If canonical source or original-source hash changes, old evidence is `STALE`; do not silently reuse it.

## Security and privacy

The manifest stores source paths and hashes; chunk files contain source content. Put the output directory somewhere appropriate for the source's sensitivity. Do not upload or persist secrets merely to obtain a coverage proof.

## Scale path

The current JSON manifest is intentionally simple and auditable. If manifests become too large, preserve the same invariants while replacing verbose per-unit state with compact interval sets and/or Merkle-rooted chunk manifests. Do not trade away exact gap/duplicate/staleness detection merely to reduce storage.

## Multi-source basis

Per-source coverage is necessary but not sufficient for a task that depends on several authoritative files.

Use `scripts/source_registry.py` to bind all required sources into one deterministic source basis. The registry records exact registered hashes, required/optional status, authority/role, and coverage evidence references. Its `source_basis_digest` is computed from sorted required source identities and is stable across repeated audits of unchanged sources.

A required source that becomes stale or whose coverage is not ready blocks the registry. Optional sources remain visible but do not automatically block the required basis.

The source-basis digest proves which exact registered versions were declared required. It does not prove semantic understanding.

## Structural source identities

Use `scripts/structural_units.py` when claims need stable human/audit locators beyond chunk IDs.

Supported direct UTF-8 modes:

- `lines` -> `L000001`, `L000002`, ...
- `paragraphs` -> `P000001`, `P000002`, ...

Each unit binds exact byte ranges/hashes and may be mapped to overlapping coverage chunk IDs. Unit inventories cover canonical bytes exactly once and become stale when the source hash changes.

For PDFs/Office documents, page/element/table identities should come from the extraction adapter and preserve original-document provenance.

Structural units do not replace byte-level coverage; they make source-linked semantic auditing traceable.
