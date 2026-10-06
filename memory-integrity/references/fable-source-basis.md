# Fable source-basis integration

## Contents

1. Goal
2. Authority boundary
3. Canonical registry
4. Read-receipt binding
5. `source_basis_digest`
6. Gate behavior
7. Dependency invalidation
8. Storage layout
9. Migration plan
10. Non-goals

## 1. Goal

Close the gap between a governor that says "read authoritative sources completely" and mechanics that can prove which exact source versions were actually covered.

## 2. Authority boundary

Fable remains the single canonical control plane for:

- requirements;
- plan;
- approvals;
- execution state;
- evidence;
- completion.

GPT Monitor supplies source-integrity evidence. It must not create a second project governor.

AgentMemory and Graphify remain derived continuity/discovery systems.

## 3. Canonical registry

Recommended canonical record under Fable:

```text
docs/fable/sources.json
```

Each entry should bind at least:

```json
{
  "source_id": "SRC-0007",
  "authority": "AUTHORITATIVE",
  "required": true,
  "role": "canonical-build-plan",
  "identity": {
    "kind": "sha256",
    "value": "..."
  },
  "provenance": {
    "path_or_uri": "...",
    "provider": "git/filesystem/upload",
    "ref": "optional immutable ref"
  },
  "canonical_representation": {
    "hash": "...",
    "extractor": null,
    "extraction_status": "NOT_APPLICABLE"
  },
  "read_basis": {
    "manifest_sha256": "...",
    "receipt_set": "..."
  }
}
```

Do not store huge extracted bodies inside `docs/fable/` merely to make them canonical. Fable should bind identities and evidence. Large hash-addressed representations can live in a replaceable cache/artifact store.

## 4. Read-receipt binding

A required source is not considered read merely because:

- it was mentioned in a plan;
- Graphify indexed it;
- a repo map listed symbols;
- search returned excerpts;
- a summary exists.

The read basis must point to current coverage evidence.

Suggested receipt states:

- `COMPLETE`;
- `PARTIAL`;
- `TRUNCATED`;
- `ERROR`;
- derived aggregate `STALE` when source identity changed.

## 5. `source_basis_digest`

Compute a deterministic digest over the sorted required-source basis, for example:

```text
source_id
registered immutable identity
manifest digest
required flag
source authority
semantic role
```

Do not include volatile timestamps in the digest.

The digest should change when the required authoritative basis changes, but not merely because the same check ran at a new time.

Bind this digest beside existing requirements/plan/tests digests.

Conceptually:

```text
approval = H(requirements, plan, tests, source_basis)
state    = H(approved scope, source_basis, execution evidence)
```

## 6. Gate behavior

### Plan gate

Identify required authoritative sources and unresolved source gaps.

### Execute gate

Block source-dependent implementation when a required source is:

- absent;
- stale;
- extraction-incomplete;
- coverage-partial;
- invalid/truncated/error;
- not bound to the approved source basis.

### Resume gate

Recompute/verify current source identities before trusting previous next-action notes.

### Completion gate

Require source-dependent evidence to bind to the current source basis.

## 7. Dependency invalidation

Ideal dependency graph:

```text
SOURCE VERSION
   -> READ RECEIPT SET
   -> REQUIREMENT / DECISION
   -> IMPLEMENTATION / TEST EVIDENCE
   -> COMPLETION CLAIM
```

When a source changes:

1. old read receipt becomes stale;
2. affected requirement/decision is reopened;
3. dependent implementation evidence is rechecked where semantics may have changed;
4. execution/completion remains blocked until reconciliation.

Do not reopen unrelated work merely because an optional source changed.

## 8. Storage layout

Recommended shape:

```text
docs/fable/
  sources.json
  reads/
    index.json
    runs/
      <receipt-set>.json
  ... existing Fable state ...

.fable-cache/
  sources/<sha256>/...
  units/<sha256>/...
  chunks/<sha256>/...
```

The cache is replaceable because canonical Fable state binds hashes.

## 9. Migration plan

Do not silently add unknown fields to a schema that rejects them.

Use an explicit versioned migration:

1. add source-basis schema;
2. migrate existing projects with `UNVERIFIED` source basis rather than fake receipts;
3. make plan/execute/resume/complete gates understand the new basis;
4. add fault-injection tests;
5. only then require the gate for new governed projects;
6. gradually backfill old projects from direct sources.

## 10. Non-goals

This integration must not:

- replace Fable planning;
- make AgentMemory authoritative;
- make Graphify edges proof;
- require Aider for correctness;
- claim semantic perfection;
- fabricate historical read receipts for work that predates the mechanism.
