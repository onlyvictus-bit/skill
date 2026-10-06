# Claude Mon architecture

## Target

Prove what source version existed, how it was partitioned, what exact chunk payloads were processed for a specific task, what failed or truncated, and whether that proof is still current.

This is a coverage engine, not a memory database and not a semantic-correctness oracle.

## Data flow

```text
original source bytes
  -> project-relative source identity + SHA-256
  -> deterministic UTF-8 unit manifest
  -> verified contiguous byte coverage
  -> chunk manifest
       primary units = coverage responsibility
       context units = repeated coherence only
  -> exact chunk payload + payload SHA-256
  -> processor outcome per expected chunk
  -> immutable task-bound receipt
  -> current-basis verification
  -> Claude Mon gate
  -> Fable continues only when its own gate also passes
```

For complex documents:

```text
original binary hash
  -> extractor result/status/errors
  -> structured extracted representation hash
  -> Claude Mon text coverage on the extracted representation
```

Do not collapse the two proof layers. Processing all extracted JSON does not prove the extractor captured every fact in the original visual document.

## Authority

- **Underlying source**: authoritative content.
- **Fable `docs/fable/`**: project requirements, approvals, tests, state, evidence, and completion authority when Fable is active.
- **`docs/fable/claude-mon/`**: canonical source-coverage extension inside the Fable control plane.
- **`.claude-mon/cache/`**: reproducible/hash-bound unit and chunk manifests; not project truth by itself.
- **Aider/Graphify/Repomix**: derived navigation/export helpers only.

Claude Mon deliberately avoids adding fields to Fable schema-v2 JSON documents, because Fable rejects unknown fields. The bridge composes gates instead of patching Fable's canonical schemas.

## Why the source ID and source version are separate

`source_id` is deterministic from the normalized project-relative path. It names the logical source slot. `source_sha256` identifies the current byte version. A content change can therefore keep the logical source ID while making old receipts stale.

A rename intentionally creates a different source ID in M1. If rename lineage becomes necessary, add an explicit alias/move record; do not guess identity from similar content.

## Unit model

M1 uses strict UTF-8 byte segments instead of paragraph semantics as the mechanical truth. This avoids normalization loss and works for code, Markdown, logs, JSON, and prose.

Each unit records:

- deterministic ordinal ID for one source version/config;
- contiguous `[start_byte, end_byte)` range;
- SHA-256 of those source bytes;
- byte size;
- line-start/end metadata.

Every unit is independently valid UTF-8. A source containing malformed UTF-8 fails the text route instead of silently inserting replacement characters.

Units are stable for the same source bytes and `max_unit_bytes`. They are not promised to retain IDs across source edits; source-version staleness is the safer contract.

## Chunk model

Chunks own an ordered set of `primary_units`. Across a valid complete manifest, every unit must appear exactly once as primary. Neighbor units can appear as `context_before`/`context_after` repeatedly.

The payload SHA-256 covers the exact concatenation:

`context_before + primary_units + context_after`

The `payload` operation recomputes that hash before returning text. Every `ok` or `truncated` processing outcome must carry that exact `input_sha256`; a missing or different hash is converted to an error, and verification rechecks the saved receipt.

## Receipt model

A receipt binds:

- source ID and source SHA-256;
- unit-manifest digest;
- chunk-manifest digest;
- exact task-spec SHA-256;
- processor metadata;
- chunk outcomes;
- derived coverage status.

Receipt files are create-once. Staleness is derived during verification; historical files are not rewritten.

## Status precedence

1. `STALE` — current source/manifests differ from the receipt basis.
2. `ERROR` — integrity error, unknown/duplicate chunk, explicit processing error, or malformed outcome.
3. `TRUNCATED` — at least one expected chunk is known to have been truncated.
4. `PARTIAL` — expected chunks remain absent.
5. `COMPLETE` — all expected chunks occur exactly once with `ok`.

This precedence prevents a partially successful run from hiding a stronger failure signal.

## What COMPLETE does not prove

It does not prove:

- a PDF/OCR/layout extractor captured the original perfectly;
- a model understood every statement;
- a model result is factually correct;
- synthesis preserved every finding;
- an Aider/Graphify/retrieval result discovered every authoritative source.

Those claims require their own evidence.

## Scale and storage

Original source bytes are never duplicated into the registry. Unit/chunk manifests store metadata only. Source hashing and unitization stream file bytes; current M1 verification/chunk planning materializes manifest metadata in memory, so memory scales with **unit count**, not source byte size.

The supplied 50 MiB check is a representative floor, not a universal upper bound. If manifest metadata becomes the measured bottleneck at much larger scales, move to streaming/SQLite interval verification or a Merkle index. Do not add a Merkle tree before that bottleneck is observed.

## Concurrency and recovery

Use a single writer for registry mutation. Mutable registry/manifests use atomic replacement; immutable receipt files use exclusive creation. This prevents torn writes and receipt overwrite but does not merge simultaneous registry edits.

After interruption, re-run current-source verification. Deterministic manifests can be regenerated. Receipt history stays immutable.

## Security/privacy

Core scripts are local, perform no network calls, and do not execute source content. Optional dependency installation and external AI calls remain separate authorization boundaries. Routine status output contains hashes/paths/IDs, not source content.
