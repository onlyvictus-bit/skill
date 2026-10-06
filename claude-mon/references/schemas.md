# Claude Mon schemas

These are M1 contracts. Unknown fields should be treated cautiously; do not infer weakened semantics from misspellings.

## Source registry

Path: `docs/fable/claude-mon/sources.json`

```json
{
  "schema": 1,
  "sources": [
    {
      "source_id": "SRC-...",
      "path": "relative/path.md",
      "kind": "text",
      "required": true,
      "provenance": ["user-request"],
      "current_version": {"sha256": "...", "byte_size": 1234},
      "versions": [
        {"sha256": "...", "byte_size": 1234}
      ]
    }
  ]
}
```

Kinds: `text`, `binary`, `document`, `extracted-document`.

Only `text` and `extracted-document` enter the built-in strict UTF-8 unitizer.

## Unit manifest

Summary file: `.claude-mon/cache/<source-id>/<source-sha>/unit_manifest.json`

```json
{
  "schema": 1,
  "source_id": "SRC-...",
  "source_sha256": "...",
  "byte_size": 1234,
  "max_unit_bytes": 65536,
  "unit_count": 3,
  "units_path": ".claude-mon/cache/.../units.jsonl",
  "units_sha256": "..."
}
```

Each JSONL row:

```json
{
  "unit_id": "U00000001",
  "ordinal": 1,
  "start_byte": 0,
  "end_byte": 512,
  "byte_size": 512,
  "sha256": "...",
  "line_start": 1,
  "line_end": 18
}
```

Ranges are half-open. Exact complete unit coverage requires contiguous ranges from byte 0 to source byte size, correct hashes, correct order, and strict UTF-8 decode.

## Chunk manifest

Summary file: `.claude-mon/cache/<source-id>/<source-sha>/chunk_manifest.json`

```json
{
  "schema": 1,
  "source_id": "SRC-...",
  "source_sha256": "...",
  "unit_manifest_sha256": "...",
  "max_primary_bytes": 262144,
  "context_units": 1,
  "chunk_count": 10,
  "chunks_path": ".claude-mon/cache/.../chunks.jsonl",
  "chunks_sha256": "..."
}
```

Each JSONL row:

```json
{
  "chunk_id": "C00000001",
  "ordinal": 1,
  "primary_units": ["U00000001", "U00000002"],
  "context_before": [],
  "context_after": ["U00000003"],
  "primary_bytes": 1000,
  "payload_sha256": "..."
}
```

Only `primary_units` count toward coverage.

## Processor outcomes

Input to `receipt` is a JSON array:

```json
[
  {
    "chunk_id": "C00000001",
    "status": "ok",
    "input_sha256": "...",
    "result_sha256": "..."
  }
]
```

`result_sha256` is optional metadata. It proves result identity only, not correctness.

For every `ok` or `truncated` outcome, `input_sha256` is mandatory and must equal the current chunk payload hash. A missing or mismatched value is converted to an error. An `error` outcome may omit it when processing failed before a payload was accepted.

## Receipt

Path: `docs/fable/claude-mon/receipts/runs/<receipt-id>.json`

```json
{
  "schema": 1,
  "receipt_id": "READ-...",
  "created_at": "...Z",
  "source_id": "SRC-...",
  "source_sha256": "...",
  "unit_manifest_sha256": "...",
  "chunk_manifest_sha256": "...",
  "task_spec_sha256": "...",
  "processor": {"kind": "model", "name": "..."},
  "chunk_outcomes": [],
  "status": "COMPLETE",
  "coverage_only": true,
  "semantic_correctness_proven": false
}
```

Receipt status is re-derived during verification. Do not trust the stored status when the current basis has changed.

## Extraction receipt for complex documents

M1 does not mint this automatically because Docling/OCR is optional and unavailable in some runtimes. When implementing a document adapter, keep an independent extraction record with at least:

```json
{
  "original_source_id": "SRC-...",
  "original_sha256": "...",
  "extractor": "docling",
  "extractor_version": "...",
  "conversion_status": "SUCCESS|PARTIAL_SUCCESS|FAILURE|...",
  "errors": [],
  "extracted_source_id": "SRC-...",
  "extracted_sha256": "..."
}
```

Only an explicitly accepted extraction basis may feed a claim about the original document. A Claude Mon `COMPLETE` receipt on the extracted representation alone is insufficient.
