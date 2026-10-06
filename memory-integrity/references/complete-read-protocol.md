# Verifiable complete-read protocol

## Contents

1. Goal
2. Required artifacts
3. End-to-end pipeline
4. Source registry
5. Extraction
6. Canonical representation
7. Structural units
8. Chunking and context
9. Processing receipts
10. Resume and retries
11. Synthesis
12. Semantic audit
13. Repository mode
14. Rich-document mode
15. Completion gate
16. 50 MB example

## 1. Goal

The protocol does not claim that a model can hold an arbitrarily large source in one context window.

It creates a verifiable process in which every required source version is identified, every canonical primary range is accounted for, every processing attempt is recorded, and final synthesis is blocked when coverage or extraction is incomplete.

The core invariant is:

```text
NO COMPLETE-READ CLAIM WITHOUT COMPLETE CURRENT EVIDENCE
```

## 2. Required artifacts

For serious work, preserve:

1. original-source identity;
2. source registry;
3. canonical representation identity;
4. extraction diagnostics where relevant;
5. structural unit inventory;
6. chunk manifest;
7. token/context configuration;
8. append-only processing receipts;
9. source-linked findings/results;
10. coverage report;
11. semantic-audit result;
12. final `source_basis_digest`.

## 3. End-to-end pipeline

```text
ORIGINAL SOURCE(S)
      |
      v
SHA-256 / Git identity
      |
      v
SOURCE REGISTRY
      |
      v
EXTRACTION (if needed)
      |
      v
CANONICAL REPRESENTATION
      |
      +--> STRUCTURAL UNIT INVENTORY
      |
      v
EXACT PRIMARY CHUNKS
      |
      v
TOKEN-AWARE PROCESSING BATCHES
      |
      v
MODEL / PROCESSOR
      |
      v
APPEND-ONLY RECEIPTS
      |
      v
COVERAGE VERIFY
      |
      v
SOURCE-LINKED SYNTHESIS
      |
      v
SEMANTIC CHALLENGE PASS
```

## 4. Source registry

Every required source must have a stable `source_id` and exact registered identity.

Minimum fields:

- `source_id`;
- path/URI or provider identity;
- content hash or Git identity;
- size;
- required vs optional;
- authority class;
- semantic role;
- canonical manifest reference;
- receipts reference;
- parser/extractor identity where relevant.

Use `scripts/source_registry.py` for file-backed sources in this skill.

The registry produces `source_basis_digest` from the required registered identities. This is the compact statement of "these exact source versions were the basis of the work."

Do not include timestamps in the digest; otherwise identical source bases would hash differently across runs.

## 5. Extraction

Direct UTF-8 text/code can use source bytes as canonical bytes.

For PDF, DOCX, PPTX, image/scans, and complex HTML:

1. hash the original binary;
2. inventory pages/slides/sheets/elements as appropriate;
3. extract into a structured canonical representation;
4. record extractor/version/options;
5. record failures/warnings/unreadable elements;
6. preserve page/element provenance;
7. hash the canonical representation;
8. do not mark extraction `COMPLETE` if required content classes failed.

A perfect downstream ledger cannot repair an incomplete extraction.

## 6. Canonical representation

Canonicalization must be deterministic enough to identify the processed representation.

For direct text/code:

- strict UTF-8;
- no silent replacement characters;
- exact bytes preserved;
- line endings remain part of the canonical bytes unless a declared normalization is intentionally applied.

For document extraction:

- prefer structured JSON with hierarchy/provenance;
- avoid making flattened Markdown authoritative when it discards required table/layout semantics;
- keep original binary identity next to canonical identity.

## 7. Structural units

Chunk IDs are useful operationally but poor citation handles.

Create stable units for human/source-linked reasoning:

- source code: file + line units;
- prose: paragraph units;
- complex documents: page/element/table/cell units;
- sentence units only where the task actually needs sentence-level traceability.

This skill provides `scripts/structural_units.py` for UTF-8 line and paragraph inventories.

Each unit records:

- unit id;
- exact byte range;
- size;
- hash;
- overlapping processing chunk IDs.

The unit inventory must cover canonical bytes without gaps or overlap.

Do not tokenize into sentences merely because sentences sound precise. Sentence segmentation can be language- and abbreviation-dependent and is not always stable. Use it only when required.

## 8. Chunking and context

Separate two concepts:

```text
PRIMARY RANGE / UNIT
  = this processing job owns responsibility for it

CONTEXT RANGE / UNIT
  = neighboring material duplicated only to improve interpretation
```

Only primary coverage counts toward completion.

This prevents overlap from creating fake 100%+ coverage.

For processing calls:

1. calculate fixed prompt/tool/history overhead;
2. reserve output tokens;
3. reserve safety margin;
4. compute remaining input budget with the configured tokenizer;
5. group primary chunks/units deterministically;
6. optionally add context without changing primary ownership;
7. reject batches that cannot fit rather than silently truncate.

Byte-level source chunking and token-level call packing are separate jobs.

## 9. Processing receipts

A receipt must bind to exact input identity, not just a counter.

Minimum receipt fields:

- source hash;
- manifest hash;
- chunk id;
- chunk hash;
- attempt number;
- status;
- timestamp;
- processor/model/config identity when available;
- optional result hash;
- optional error/truncation note.

Statuses:

- `COMPLETE`;
- `PARTIAL`;
- `TRUNCATED`;
- `ERROR`.

`726/726` is insufficient. A duplicate can hide a missing identity. Verify exact IDs and hashes.

## 10. Resume and retries

Receipts are append-only attempts.

Rules:

- never overwrite a failed attempt as if it never happened;
- latest valid attempt controls current status for that chunk;
- same attempt number twice is invalid evidence;
- resume only missing/non-complete chunks;
- if source/manifest hash changed, old receipts become stale;
- do not mix receipts from different source versions.

For concurrent processors, use atomic writes/locking or per-attempt files. A shared JSONL append is not enough under uncontrolled multi-process concurrency.

## 11. Synthesis

Do not synthesize a final "complete" result while any required primary coverage is missing.

Recommended synthesis order:

1. per-chunk findings preserve source unit references;
2. group by topic without deleting contradictions;
3. extract exact rules/numbers/exceptions separately;
4. reconcile duplicates by provenance, not by majority count;
5. reopen source units for conflicts;
6. run a contradiction/exception sweep;
7. produce final synthesis with traceable support.

## 12. Semantic audit

Coverage says a processing attempt completed. It does not prove the result was semantically correct.

Run `references/semantic-audit.md` for consequential tasks.

At minimum, challenge:

- negations;
- exceptions;
- thresholds;
- dates/time semantics;
- units/currencies;
- definitions;
- cross-references;
- contradictions;
- repeated but differently scoped rules;
- tables and footnotes;
- first/last sections where truncation mistakes often hide.

## 13. Repository mode

For repositories, registry identity should distinguish:

- Git commit/tree/blob state;
- dirty worktree changes;
- untracked files included in scope;
- generated/vendor files intentionally excluded or included;
- submodules;
- branch/ref only as navigation, never as immutable identity.

Use Graphify/Aider RepoMap to nominate likely relevant code for ordinary tasks.

For a user-required complete repository audit, relevance ranking is insufficient; enumerate the governed source set and create coverage evidence over that set.

## 14. Rich-document mode

Recommended path:

```text
original.pdf
  -> original hash
  -> page inventory
  -> extractor/Docling
  -> structured canonical JSON
  -> extraction diagnostics
  -> canonical hash
  -> structural page/element ids
  -> coverage chunks
  -> receipts
```

If a page is image-only and OCR/vision is required, record that explicitly. Do not silently treat an empty extracted page as an empty source page.

## 15. Completion gate

A complete-read workflow may report `READY` only if all required conditions pass:

- every required source in registry is current;
- source-basis digest is known;
- extraction is `COMPLETE` or `NOT_APPLICABLE` for every required source;
- canonical reassembly passes;
- structural inventory is current when required by the task;
- every required primary chunk has a latest `COMPLETE` receipt;
- no invalid/foreign/duplicate receipts;
- no stale hashes;
- no unresolved truncation/error;
- semantic audit completed to the task's declared standard.

If the semantic audit is not run, report mechanical coverage separately and label semantic completeness unverified.

## 16. 50 MB example

Suppose a 50 MB UTF-8 file becomes 800 deterministic primary chunks.

The safe process is not:

```text
upload -> ask model "did you read it all?"
```

It is:

```text
hash source
-> register source
-> build line/paragraph inventory
-> create exact chunks
-> pack chunks into token-safe calls
-> append 800 receipts
-> verify exact source/chunk identities
-> synthesize only after 800 current COMPLETE receipts
-> run semantic challenge pass
```

If 799 are complete, the answer is `PARTIAL`, and the missing chunk ID must be named.
