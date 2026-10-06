# The memory and complete-read problem model

## Contents

1. The actual problem
2. The eight layers that can fail
3. Why file size in MB is the wrong guarantee
4. What can and cannot be proven
5. Authority hierarchy
6. Failure taxonomy
7. Required response pattern

## 1. The actual problem

When a user says "GPT forgot," "GPT skipped part of my file," or "make sure it remembers everything," do not treat that as one problem.

At least eight different mechanisms may be involved:

```text
SOURCE STORAGE
    -> EXTRACTION
    -> CANONICALIZATION
    -> INDEX / RETRIEVAL
    -> CONTEXT SELECTION
    -> MODEL PROCESSING
    -> SYNTHESIS
    -> DURABLE MEMORY / RESUME
```

A failure in any layer can look like forgetting.

The system must therefore answer separate questions:

1. What exact source existed?
2. Was all required source content converted into a canonical representation?
3. Was that canonical content preserved exactly after conversion?
4. Which parts were selected or processed?
5. Did every required primary unit receive a processing attempt?
6. Were any requests or responses truncated or errored?
7. Can important facts be recalled in a later session?
8. Are recalled facts still current relative to authoritative sources?
9. Are final conclusions traceable to source evidence?

Never reduce all of these to "memory works."

## 2. The eight layers that can fail

### Layer A — source storage

The uploaded file or repository exists somewhere accessible.

This proves only storage/availability. It does not prove extraction, reading, or understanding.

Evidence:

- immutable source identity;
- byte size;
- SHA-256 or Git blob/tree identity;
- acquisition time and provenance when relevant.

### Layer B — extraction

PDF, DOCX, PPTX, scans, images, tables, or other rich content are converted into something the processing engine can inspect.

Possible failures:

- scanned text omitted;
- table cell order flattened incorrectly;
- headers/footers dropped;
- image labels lost;
- reading order wrong;
- encrypted or damaged pages skipped;
- unsupported embedded objects ignored.

Extraction correctness is independent from later chunk coverage.

### Layer C — canonicalization

The extracted or direct text becomes a stable canonical representation.

For direct UTF-8 text/code this can often be the exact bytes. For rich documents it should be a structured representation with provenance, not a lossy summary.

Evidence:

- canonical hash;
- encoding;
- parser/extractor version;
- source-to-canonical provenance;
- page/element inventory when applicable.

### Layer D — indexing and retrieval

Search, embeddings, graphs, repo maps, or memory indexes nominate relevant candidates.

Retrieval is selective by design.

A successful search result means "this material was retrieved," not "everything else was reviewed."

### Layer E — active context selection

Only a bounded amount of material is placed into the model's active context for a particular call.

Context budgeting must account for:

- system/developer instructions;
- chat history;
- tools and schemas;
- retrieved material;
- model output reserve;
- safety margin.

A file may exist in storage yet never enter a model call.

### Layer F — model processing

The model receives input and produces a result.

Even if all text is present in context, no mechanism can prove perfect human-like attention to every sentence or guarantee perfect interpretation.

Reduce risk with smaller proof units, explicit tasks, source IDs, challenge passes, and independent checks.

### Layer G — synthesis

Results from many chunks are combined.

Common failures:

- exceptions dropped;
- conflicting sections flattened;
- duplicate evidence over-weighted;
- later chunks override earlier rules incorrectly;
- numbers or negations lost;
- summaries replace source truth.

Synthesis requires its own verification.

### Layer H — durable memory and resume

Facts, decisions, progress, and relationships survive beyond one active context/session.

Possible failures:

- write never persisted;
- index not updated;
- wrong user/project/agent scope;
- memory survived storage but not search;
- service restart lost state;
- stale facts remain retrievable;
- superseded facts appear current;
- session progress was never checkpointed.

## 3. Why file size in MB is the wrong guarantee

There is no useful universal rule such as "a 50 MB file will be read completely."

Fifty megabytes can be:

- mostly images;
- compressed XML inside an Office document;
- millions of UTF-8 characters;
- source code with very different token density;
- a scanned PDF with little directly extractable text.

The active model limit is measured in tokens and includes much more than the user file.

Therefore:

```text
UPLOAD LIMIT != ACTIVE CONTEXT LIMIT != COMPLETE-READ GUARANTEE
```

Do not answer a completeness question with only an upload limit.

## 4. What can and cannot be proven

Mechanically strong claims:

- exact original byte identity;
- exact canonical byte identity;
- exact source/chunk/unit hashes;
- deterministic ordered unit/chunk manifests;
- exact reassembly of canonical text/code;
- every required chunk has a current receipt;
- missing, duplicate, stale, truncated, or error states;
- durable-memory canary write/read/delete behavior;
- persisted canary surviving a session/service boundary when explicitly tested.

Claims that are not absolute mathematical proofs:

- extractor captured every visual fact from an arbitrary document;
- model attended to every sentence equally;
- model understood every sentence correctly;
- final synthesis has no semantic mistake.

For these, report audit evidence and uncertainty rather than pretending the hash proves semantics.

## 5. Authority hierarchy

Use this default ordering unless the governed project defines something stricter:

```text
original authoritative source
    > canonical verified representation
    > current source-linked evidence
    > governed project state
    > derived graphs / indexes / memories
    > summaries
    > model prior knowledge
```

If durable memory contradicts a current authoritative source, the source wins and the memory must be treated as stale or superseded.

## 6. Failure taxonomy

| Symptom | Likely layer | First proof to run |
|---|---|---|
| "GPT skipped pages" | extraction or coverage | page/extraction inventory + source coverage |
| "Search found only one section" | retrieval | distinguish selective retrieval from complete-read mode |
| "GPT forgot last session" | durable memory | liveness + roundtrip + session bridge |
| "Memory exists but recall is empty" | index/scope | direct-id read + scoped search |
| "It remembered an old decision" | staleness | compare source/current project hashes and supersession |
| "All chunks processed but answer wrong" | model/synthesis | source-linked semantic audit |
| "Context overflow/truncation" | budgeting | exact tokenizer + reserved output/overhead |
| "999/1000 chunks done" | coverage | list exact missing IDs; do not synthesize final completion |
| "1000/1000 count but still missing content" | duplicate identity error | verify identities/ranges, not counts |
| "Repository map looks complete" | retrieval misconception | open real source; repo map cannot satisfy complete-read receipt |

## 7. Required response pattern

When diagnosing a memory/complete-read problem, report:

1. **Observed layer** — which layer is actually failing or unverified.
2. **Evidence** — hashes, receipt IDs, scope, hit counts, page/chunk IDs, direct reads.
3. **What that evidence proves.**
4. **What it does not prove.**
5. **Next falsifier** — cheapest test that could disprove the current hypothesis.
6. **Recovery action** — reread, re-extract, reindex, retry chunk, correct scope, or reopen synthesis.

Never say "I read everything" merely because the source was uploaded or searchable.
