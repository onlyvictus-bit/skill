# Memory-integrity acceptance and trap suite

## Contents

1. Core principle
2. Memory traps
3. Source traps
4. Extraction traps
5. Token/context traps
6. Synthesis traps
7. Registry/Fable traps
8. Scale tests

## 1. Core principle

A trustworthy system must fail visibly when evidence is incomplete.

Every test below is designed to catch a false-green path.

## 2. Memory traps

### Liveness-only false green

Run only service health/status.

Expected: `UNVERIFIED`, never `HEALTHY`.

### Write-without-recall

Accept a write but make search return no canary.

Expected: `DEGRADED`.

### Delete ghost

Delete storage record but leave search hit.

Expected: `DEGRADED`.

### Wrong scope

Store in project A; search in project B.

Expected: no automatic widening of scope. Report scoped miss/investigate.

### Persistence loss

Seed bridge canary, restart/switch session, remove persistence backing.

Expected: bridge verification fails; no historical memory claims.

## 3. Source traps

### Missing receipt

Delete one required chunk receipt.

Expected: `PARTIAL` and exact chunk ID.

### Duplicate attempt identity

Duplicate an attempt number for the same chunk/source basis.

Expected: `INVALID`.

### Source byte changed

Modify one byte after coverage.

Expected: `STALE`.

### Corrupt chunk

Modify chunk content without updating manifest.

Expected: `INVALID` reassembly/hash error.

### Count-only deception

Create N receipt rows but duplicate one chunk and omit another.

Expected: not complete.

### Optional source stale

Change an optional source while all required sources remain current.

Expected: source reported stale but required basis may remain `READY`.

## 4. Extraction traps

### Canonical complete, extraction partial

All canonical chunks complete, `extraction_status=PARTIAL`.

Expected: `COVERAGE_COMPLETE` but `OVERALL: BLOCKED`.

### Image-only page with no text

Page inventory shows a page; extracted text is empty.

Expected: extraction unresolved until visual/OCR handling proves intentional blank or obtains content.

### Table flattening loss

Structured table exists in original but canonical form omits required headers/spans.

Expected: extraction cannot be marked complete for a table-dependent task.

## 5. Token/context traps

### Unknown model mapping

Call token counter with unknown model and no explicit encoding.

Expected: error; no guessed tokenizer.

### No room after reserves

Context limit minus output/overhead/safety <= 0.

Expected: error.

### Candidate overflow

Candidates exceed input budget.

Expected: deterministic selected + skipped sets; never silent truncation.

## 6. Synthesis traps

### Negated rule

One source says "must not" while summary says "may."

Expected: semantic audit rejects/reopens claim.

### Exception separated across chunks

Rule in one chunk, exception in later chunk.

Expected: synthesis preserves exception and cites both units.

### Conflicting versions

Old and new source both available.

Expected: authority/version resolution, not majority vote.

## 7. Registry/Fable traps

### Required source changed

Current hash differs from registered source basis.

Expected: registry `BLOCKED`; dependent Fable execution should reopen when integrated.

### Historical project without receipts

Migrated old project claims it previously read all files but has no evidence.

Expected: mark source basis `UNVERIFIED`; never fabricate backdated receipts.

### Graph/repo map says file exists

No direct source receipt.

Expected: cannot satisfy complete-read gate.

## 8. Scale tests

On representative 50 MB+ sources measure:

- hash throughput;
- structural-unit build time;
- chunk count;
- manifest size;
- receipt append/read time;
- resume scan time;
- tokenization rate;
- peak memory;
- source-registry audit time.

Performance optimization may change representation, but must preserve the same false-green traps.
