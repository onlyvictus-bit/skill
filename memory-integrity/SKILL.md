---
name: memory-integrity
description: Diagnose and prove memory, complete-read, and source-coverage integrity for GPT/agent work. Use when a user says GPT forgot prior work, asks whether every page/paragraph/line of a large file was processed, needs persistent cross-session memory verified, wants no silent omissions/truncation, needs source hashes/read receipts/resume coverage, or is designing Fable/Graphify/AgentMemory/Aider/Docling context-memory architecture. Separates upload, extraction, canonicalization, retrieval, active context, processing, synthesis, and durable memory; fails closed when any required layer is unverified.
---

# Memory Integrity

Treat "GPT memory" and "GPT read everything" as a **multi-layer integrity problem**, not as one feature.

The governing rule is:

```text
NEVER CLAIM MORE THAN THE EVIDENCE PROVES.
```

A healthy memory store does not prove a file was completely read. Complete chunk coverage does not prove PDF extraction was complete. A complete canonical read does not prove perfect semantic understanding.

## 1. Load the right knowledge before acting

For any non-trivial memory/complete-read task, read `references/problem-model.md` first.

Then load the relevant reference directly from this entrypoint:

- durable recall, forgotten sessions, memory persistence, scope, staleness: `references/memory-integrity-model.md`
- large files, every paragraph/line, resumable processing: `references/complete-read-protocol.md`
- PDF/DOCX/PPTX/scans/tables/images: `references/document-ingestion.md`
- repositories, Graphify/Aider/repo-map/context selection: `references/code-context.md`
- source-linked reasoning correctness: `references/semantic-audit.md`
- Fable source registry/read receipts/gates: `references/fable-source-basis.md`
- failures/recovery: `references/diagnosis-recovery.md`
- false-green/adversarial tests: `references/acceptance-tests.md`
- current AgentMemory REST details: `references/agentmemory-interface.md`
- compact source/receipt schema: `references/source-coverage-contract.md`
- component roles/build order: `references/integration-architecture.md`

Do not answer a broad memory-integrity question from only one subsystem reference.

## 2. First classify the user's actual problem

Use this model:

```text
A. SOURCE STORAGE
B. EXTRACTION
C. CANONICALIZATION
D. INDEX / RETRIEVAL
E. ACTIVE CONTEXT SELECTION
F. MODEL PROCESSING
G. SYNTHESIS
H. DURABLE MEMORY / RESUME
```

Common examples:

- "I uploaded 50 MB; did GPT read all of it?" -> A through G, not H alone.
- "It forgot what we decided yesterday" -> H, then source freshness.
- "Search found only some paragraphs" -> D/E; selective retrieval is not complete-read mode.
- "All chunks were processed but the answer is wrong" -> F/G semantic audit.
- "The PDF has a table GPT missed" -> B before coverage.
- "Use Aider so the whole repo is remembered" -> D/E; Aider is relevance ranking, not complete-read proof.

If the failing layer is not yet known, diagnose before proposing another memory framework.

## 3. Keep six evidence states separate

Always report these separately when relevant:

1. `SOURCE_IDENTITY` — exact original/current source version.
2. `EXTRACTION` — whether rich-document extraction is complete.
3. `COVERAGE` — whether every canonical primary chunk has valid current evidence.
4. `SEMANTIC_AUDIT` — whether source-linked interpretation checks passed.
5. `MEMORY` — whether current-session durable store/recall/delete works.
6. `PERSISTENCE_BRIDGE` — whether memory survived the tested session/restart boundary.

Never compress all six into `COMPLETE` or `HEALTHY`.

## 4. Authority rules

Prefer:

```text
current authoritative source
  > verified canonical representation
  > current source-linked evidence
  > Fable governed project state
  > derived Graphify / AgentMemory / retrieval indexes
  > summaries
  > model prior knowledge
```

If memory contradicts current source truth, reread the source and treat memory as stale/superseded.

Fable remains the only requirements/approval/completion authority when present. This skill produces integrity evidence for Fable; it does not create a second governor.

## 5. Durable-memory workflow

Use `scripts/memory_watchdog.py` against the current AgentMemory API.

### Liveness only

```text
python <skill>/scripts/memory_watchdog.py status --server http://localhost:3111
```

Expected successful verdict:

`MEMORY: UNVERIFIED`

Liveness must never become `HEALTHY`.

### Current-session roundtrip

```text
python <skill>/scripts/memory_watchdog.py roundtrip \
  --server http://localhost:3111 \
  --project <project> \
  --agent-id <agent>
```

Required path:

```text
health
-> remember unique canary
-> scoped smart-search
-> verify canary identity
-> delete by identity
-> direct-id must be absent
-> search must have no ghost
```

Only this can yield `MEMORY: HEALTHY` for the current session.

### Real recall audit

```text
python <skill>/scripts/memory_watchdog.py recall-audit \
  --server http://localhost:3111 \
  --query "<real prior fact>" \
  --expect-min 1 \
  --project <project>
```

Returned hits are `UNVERIFIED` until inspected for topical/source correctness.

### Cross-session/restart persistence

At the end of session A:

```text
python <skill>/scripts/memory_watchdog.py bridge-seed \
  --server http://localhost:3111 \
  --state-file .memory-bridge.json \
  --project <project>
```

After the intended session/service boundary, in session B:

```text
python <skill>/scripts/memory_watchdog.py bridge-verify \
  --server http://localhost:3111 \
  --state-file .memory-bridge.json
```

Only a successful second phase yields `BRIDGE: PERSISTED`.

Do not call same-session health proof a persistence proof.

## 6. Complete-source workflow

Use this when the user requires every required source unit to be processed rather than selectively retrieved.

### Step 1 — register exact sources

```text
python <skill>/scripts/source_registry.py init SOURCES.json
```

Register each required source after creating its coverage manifest:

```text
python <skill>/scripts/source_registry.py register SOURCES.json SRC-001 source.txt \
  --manifest coverage/manifest.json \
  --receipts coverage/receipts.jsonl \
  --authority AUTHORITATIVE \
  --role requirements
```

The registry produces a deterministic `source_basis_digest` over required registered identities.

### Step 2 — establish canonical coverage

For direct UTF-8 text/code:

```text
python <skill>/scripts/source_coverage.py ingest SOURCE OUTPUT_DIR --max-bytes 65536
```

For extracted rich documents, bind the original separately:

```text
python <skill>/scripts/source_coverage.py ingest canonical.json OUTPUT_DIR \
  --origin original.pdf \
  --extractor docling:<version> \
  --extraction-status COMPLETE
```

Never mark extraction complete merely because a parser returned output.

### Step 3 — create stable structural locators

For code/line-oriented material:

```text
python <skill>/scripts/structural_units.py build SOURCE units.json \
  --mode lines \
  --coverage-manifest OUTPUT_DIR/manifest.json
```

For prose:

```text
python <skill>/scripts/structural_units.py build SOURCE units.json \
  --mode paragraphs \
  --coverage-manifest OUTPUT_DIR/manifest.json
```

Use page/element/table/cell identities from the extraction adapter for complex documents.

Structural units are citation/audit handles. Byte ranges/hashes remain the preservation authority.

### Step 4 — fit processing calls to real context budget

Use `scripts/context_budget.py` when token accounting matters.

Rules:

- `tiktoken` is required for token claims but is not bundled.
- recognized model -> `encoding_for_model()`;
- unknown model -> require explicit encoding;
- context-window size must come from explicit provider/model configuration;
- reserve output, fixed prompt/tool/history overhead, and safety margin;
- record skipped candidates; never silently truncate.

Byte chunking and token-safe model-call packing are different operations.

### Step 5 — process only pending primary chunks

```text
python <skill>/scripts/source_coverage.py pending OUTPUT_DIR/manifest.json OUTPUT_DIR/receipts.jsonl
```

For each real processing attempt append one receipt:

```text
python <skill>/scripts/source_coverage.py receipt \
  OUTPUT_DIR/manifest.json OUTPUT_DIR/receipts.jsonl \
  CHUNK-000001 COMPLETE \
  --result-sha256 <result-hash>
```

Allowed statuses:

- `COMPLETE`
- `PARTIAL`
- `TRUNCATED`
- `ERROR`

Retries are new attempts. Never edit away failed history.

### Step 6 — verify exact coverage

```text
python <skill>/scripts/source_coverage.py verify OUTPUT_DIR/manifest.json OUTPUT_DIR/receipts.jsonl
```

A valid verifier must detect:

- source staleness;
- origin staleness;
- chunk corruption;
- gaps/overlaps;
- missing chunks;
- duplicate attempt identities;
- foreign receipts;
- non-complete latest attempts;
- extraction incompleteness.

### Step 7 — audit the whole source basis

```text
python <skill>/scripts/source_registry.py audit SOURCES.json
```

A required stale/unready source blocks the basis. Optional stale sources remain visible but need not block required-source readiness.

### Step 8 — semantic challenge pass

Mechanical coverage is not semantic proof.

Run `references/semantic-audit.md` and reopen direct units for:

- exceptions;
- negations;
- thresholds/numbers;
- dates/times;
- units/currencies;
- definitions;
- contradictions;
- cross-chunk references;
- tables/footnotes;
- first/last/boundary material.

Final wording must distinguish mechanical coverage from semantic audit.

## 7. Rich-document workflow

For PDF/DOCX/PPTX/scans/images, read `references/document-ingestion.md` before claiming completeness.

Required order:

```text
original binary hash
-> page/slide/sheet inventory
-> structured extraction
-> extractor diagnostics
-> extraction verdict
-> canonical representation hash
-> page/element identities
-> canonical coverage
-> semantic audit
```

If any required page/element is unreadable or extraction completeness is unknown, `OVERALL` remains blocked even when canonical chunk coverage is complete.

## 8. Repository workflow

For ordinary coding tasks, use relevance mode:

```text
Fable requirements / changed files / failures
  -> Graphify relationships
  -> Aider RepoMap ranking if useful
  -> token budget
  -> OPEN REAL SOURCE
  -> execute/verify
```

For complete repository audits, use complete-audit mode instead:

```text
declare repository scope
-> immutable Git/content identities
-> enumerate required source set
-> source registry
-> coverage receipts for declared set
```

Never treat Graphify, embeddings, search excerpts, compressed Repomix, or Aider RepoMap as a complete read.

## 9. Fable integration

When asked to fix the Autonomous Operator/Fable gap, read `references/fable-source-basis.md`.

The intended architecture is:

```text
project sources
-> canonical source registry
-> source_basis_digest
-> coverage/read receipts
-> Fable gates
-> Graphify derived discovery
-> Aider task-specific relevance
-> direct source reads
-> execution evidence
-> AgentMemory continuity
```

The clean change is a versioned Fable source-basis/read-receipt contract, not another planning framework.

Do not fabricate receipts for historical projects that predate this mechanism. Mark them `UNVERIFIED` and backfill only by real rereads.

## 10. What each mechanism is allowed to prove

| Mechanism | Can prove | Cannot prove |
|---|---|---|
| SHA-256 | exact byte identity | semantic correctness |
| extraction inventory | which canonical elements were produced | universal perfect visual extraction |
| structural units | stable source locators/ranges | that model understood unit |
| chunk manifest | exact canonical partition/reassembly | processing correctness |
| receipts | processing attempt status per chunk | perfect interpretation |
| source registry | exact required source basis/current readiness | semantic truth |
| tiktoken | token count for chosen encoding | model context limit unless separately configured |
| Aider RepoMap | ranked relevant code map | complete repository read |
| Graphify | derived relationships | authoritative source truth |
| AgentMemory roundtrip | current store/recall/delete integrity | source freshness/complete-file coverage |
| persistence bridge | canary survived tested boundary | all memories are semantically correct/current |
| semantic audit | evidence-backed challenge checks | mathematical proof of perfect understanding |

## 11. Hard rules

- Never answer "yes, all 50 MB was read" from upload success.
- Never substitute MB for token/context accounting.
- Never silently replace malformed UTF-8.
- Never turn missing/unknown into false/zero/neutral/safe.
- Never count overlap/context copies as additional primary coverage.
- Never accept counts without identity/range verification.
- Never let a summary replace the original source for consequential verification.
- Never use a repo map/search result/knowledge graph as a complete-read receipt.
- Never call memory `HEALTHY` from liveness alone.
- Never call memory persistent without a boundary test.
- Never widen memory scope silently to make a recall pass.
- Never ignore a changed source hash.
- Never delete failed receipt history to get green.
- Never claim extraction is lossless for arbitrary rich documents without evidence.
- Never claim semantic perfection from hashes.
- Never create a second requirements/approval authority beside Fable.

## 12. Required report contract

For complete-source work, report at least:

```text
SOURCE BASIS: <digest or UNVERIFIED>
REQUIRED SOURCES: <ready>/<total>
EXTRACTION: COMPLETE | PARTIAL | ERROR | UNKNOWN | NOT_APPLICABLE
COVERAGE: COVERAGE_COMPLETE | PARTIAL | INVALID | STALE
SEMANTIC AUDIT: PASSED_FOR_DECLARED_CHECKS | PARTIAL | UNVERIFIED
OVERALL: READY | BLOCKED
```

For durable memory, report separately:

```text
MEMORY: HEALTHY | UNVERIFIED | DEGRADED | BLIND | MISSING
PERSISTENCE BRIDGE: PERSISTED | UNVERIFIED | FAILED
```

Include exact missing/stale/error IDs and next recovery action.

When a user asks whether "GPT remembered everything," answer with the evidence for each layer rather than one reassuring sentence.

## v2 normative appendix (added 2026-10-01; original above preserved byte-for-byte)

v2 adds a versioned integrity engine beside the v1 scripts. v1 commands keep
their behavior; v2 is selected explicitly by using the v2 entrypoints below.
No v1 receipt, memory verdict, or bridge file satisfies a v2 gate.

### Entry points (run from the skill root)

```text
python scripts/memory_integrity_v2.py --version
python scripts/memory_integrity_v2.py capabilities --claude-mon-root <engine-dir>
python scripts/memory_integrity_v2.py audit --claude-mon-root <engine-dir> --scope-file S --source-dir D --manifest-dir M
python scripts/memory_integrity_v2.py report --layers-file L [--reasons-file R]
python scripts/memory_integrity_v2.py watchdog --canary TEXT
```

The `watchdog` command runs the strict round-trip against an in-process
TEST_ONLY backend; a live AgentMemory backend needs a running service and is
not configured by this skill. All commands emit JSON envelopes.

The engine root is always explicit: the companion claude-mon v2 copy is
found by path, never by searching for a same-named skill. A digest mismatch
fails closed. v2 modules live in `scripts/integrity_v2/`: engine_client,
source_audit, extraction, watchdog, report. Tests live in `tests_v2/`.

### Strict v2 path (hosts that execute code: Codex, API shell, local runs)

1. `source_audit`: read-only presence, freshness, and manifest-binding audit;
   deep manifest validation runs inside the explicit engine copy.
2. `extraction`: EXACT_TEXT only on identical original/canonical digests;
   claimed inventories reconciled against produced elements.
3. `watchdog`: backend-injected strict round-trip (exact id+content, confirmed
   delete, direct-absence and no-ghost proofs); same-process probes cap at
   BOUNDARY_UNAVAILABLE-proof BOUNDARY_UNVERIFIED; restart/restore need
   observed generation change plus data identity.
4. `report`: overall READY_FOR_DECLARED_TASK only when every required layer
   is READY; counts never override a missing layer.

### ChatGPT manual mode (regular chat uploads cannot run scripts)

Work the six evidence states from section 3 as a checklist against visible
material: paste and hash the source list, enumerate required units, attach
one finding row per unit, keep failures visible, and report the section-12
contract with exact missing/stale IDs. Label the outcome MANUAL_REPORTED:
weaker than runner evidence, never a strict READY.

### Compatibility

v2 components handshake by contract digest; mixing releases fails closed.
See the upgrade workspace IMPLEMENTATION_LOG.md for the tested version.

## R2 isolated offline workflow (2.0.0-m10)

Use this appendix for R2 strict reporting; the preceding v1/v2 text is retained
as historical compatibility documentation. Caller-provided layer labels and
digests are not authoritative evidence. Only the fresh offline verifier can
report `VERIFIED_OFFLINE`; this is TEST_ONLY, not live AI or perfect semantic
understanding. It does not enlarge the GPT context window or permanent memory.

Read [R2 workflow](references/r2-workflow.md) when running an offline audit,
reopening a saved run, or preparing an isolated release. The one public command
is `scripts/memory_integrity_workflow.py`, with `offline-run` and `verify`.
An explicit matching `--claude-mon-root` is required; no companion search.
Reviews must be supplied for every declared primary unit. Never invent reviews
or substitute fixture success for actual model/semantic evidence.

The workflow binds exact source bytes, manifest, task/profile, scope/extraction/
review records, accepted attempts, single-use approvals and CAS files. Fresh
verification reopens and rechecks them. Missing, corrupt, stale or unresolved
evidence blocks success. Existing complete runs resume without resend; partial
run directories are retained for inspection and never overwritten blindly.
Cards are derived views; Beads is OFF/SHADOW only and never upgrades acceptance.

Installation/promotion, native Beads and any live provider/backend call remain
separate approvals. Preserve all source versions and failed evidence history.

## R3 task coordination and protected history (2.0.0-m11)

R3 is an isolated successor; all preceding R2 bytes remain preserved. When work
has task prerequisites, branch-state changes or retained-history obligations,
read [R3 coordination](references/r3-coordination.md). The single user-facing
name remains `memory-integrity`, with the explicit matching m11 `claude-mon`
companion. Do not mix the R2/m10 companion or silently search for another copy.

Use the public workflow's `coordinate-*`, `history-seal` and `branch-*` routes.
Registered coordination policy cannot be downgraded to OFF. Native task closure
never proves accepted evidence. Guards recheck the full dependency closure and
current source/basis before execution, acceptance, report, recall and resume.
Merged task state needs a new approved basis and fresh evidence; old approvals
and accepted strings cannot migrate as proof. Preserve the six evidence states
and all five card dimensions rather than collapsing them to a done flag.

Ordinary SQL event immutability, chain/projection validity and checkpoint-anchored
completeness are separate claims. Without a separately retained checkpoint,
anchored completeness remains UNVERIFIED. This is not protection against a
filesystem owner replacing both history and the trusted checkpoint.

Qualification is TEST_ONLY offline policy. Native Beads is disabled/unqualified
until the separately approved M7 runtime/database pilot; installed promotion
and live calls remain separate. In uploaded/no-runner ChatGPT mode, use only the
dependency/branch/history checklist and section-12 report as MANUAL_REPORTED,
never claim enforced dependencies, computed hashes or strict READY.

## M7 native coordination candidate (development, not yet released)

For an explicitly selected Beads workspace, read
[M7 native observation](references/m7-native-observation.md). Keep readonly
observation separate from native mutation qualification.

### Read-only observation

Use:

```text
python scripts/memory_integrity_workflow.py native-observe \
  --claude-mon-root <matching-companion> \
  --selection-file <exact-selection.json> \
  --receipt <absolute-new-receipt.json>
```

This checks the selected executable/build/project/database, the complete
issue/dependency export and repeated current head/data reads. All outcomes
remain `NATIVE_OBSERVED_UNQUALIFIED`, `active=false` and
`native_beads_qualified=false`. Observed task closure, assignment or lease
dates never create accepted evidence or an effective execution fence.

### Disposable M7 exactly-once pilot

Only after the current user has explicitly authorized an isolated disposable
pilot, run the dedicated command with a **new** workspace and receipt path:

```text
python scripts/m7_native_pilot.py \
  --bd <absolute-bd.exe> \
  --expected-executable-sha256 <64-hex-sha256> \
  --workspace <absolute-new-disposable-workspace> \
  --receipt <absolute-new-receipt.json> \
  --claude-mon-root <matching-companion>
```

The pilot verifies the executable SHA and pinned Beads v1.3.1/commit before
initialization, keeps the disposable Beads database external via explicit `BEADS_DIR`, creates a tiny
sibling launcher Git repository only to provide the pinned v1.3.1 `beads.role`
configuration, then runs `init --quiet --stealth`, creates one disposable task, and performs one claim
through the durable CM native journal. It intentionally interrupts after the
claim effect but before the terminal outcome, reopens CM, and reconciles by
readonly backend state. Success requires exactly one claim invocation and the
journal sequence `NATIVE_INTENT -> NATIVE_UNKNOWN -> NATIVE_RECONCILED`.
A second reconciliation must be idempotent.

The retained pilot receipt reports
`overall=M7_DISPOSABLE_PILOT_VERIFIED`,
`pilot_native_write_observed=true`, and still
`native_beads_qualified=false`. That distinction is mandatory: disposable
qualification does **not** authorize shared/project writes, installation,
promotion, source-code merges, task closure, or live provider calls.

The protected native-operation seam derives its dispatch decision from the
matching companion's coordination guard; public callers do not supply a
pre-approved guard result. Once a durable native intent exists without a proven
terminal result, the coordinator never blindly repeats the write. Recovery is
readback-only; absent or ambiguous readback stays UNKNOWN.

A failed read or pilot is BLOCKED. Never treat it as permission to initialize a
different database, retry an uncertain native write, relax stderr diagnostics,
or broaden the selected environment. An approval from another project or a
pasted historical receipt grants no authority in the current environment.

Native compatible/conflicting merge qualification, shared-database execution
qualification, successor packaging/promotion and installed replacement remain
separate gates. Without a runner, use only the manual checklist/report profile
and never invent a successful native command or receipt.

Reference index: read references/INDEX.md first and load only matching rows.

## R4 / m12 formal successor

R4 (2.0.0-m12) promotes the verified M7 journal/recovery work and adds one
granular native capability: the **shared-project claim protocol**. This does not
turn on generic native Beads execution.

For a shared/project claim, require all of the following before mutation:

1. an exact NativeSelection for the pinned executable/project/database;
2. a fresh complete native observation of that selected workspace;
3. current CM coordination eligibility derived through the matching m12
   companion, not a caller-provided pass flag;
4. an explicit authorization record with scope=SHARED_PROJECT_CLAIM bound to
   the exact selection digest, operation ID, CM work item ID, native task ID and actor;
5. retained qualification evidence references;
6. durable CM NATIVE_INTENT before the one permitted bd update <id> --claim;
7. native readonly show readback before terminal success.

Use hybrid_bridge.native.SharedNativeClaimAdapter only through the guarded
native-operation seam. The same operation identity is idempotent. An uncertain
delivery is never blindly resent; reconcile by backend readback.

R4 capability truth is deliberately granular:

- native_shared_claim_protocol_qualified=true
- native_beads_qualified=false
- generic_native_write_qualified=false
- native_merge_qualified=false

A protocol qualification is not standing permission for any database. Every
real shared workspace and claim still needs its own exact current authorization.
Create, close, delete, merge, arbitrary update flags, live AI/provider calls,
and installed-copy replacement remain outside this qualification unless
separately approved and verified.

The matching claude-mon m12 companion remains the CM ledger/history and
coordination authority. Keep the explicit companion path and pinned schema
digest; do not mix m11/m12 packages when using the formal R4 pair.


## Optional Semantica knowledge bridge v1

Use this when a task needs source-linked semantic/vector search, bounded relationship discovery, or structured pipeline-gap diagnosis. Fable remains the approval and completion authority. Memory Integrity is the front door; an explicit matching claude-mon companion remains required. Graph behavior is opt-in and never implies source coverage or semantic truth.

Read [Semantica integration](references/semantica-integration.md), then [contracts](references/knowledge-contract.md) and [operations](references/knowledge-operations.md) before using `knowledge-status`, `knowledge-index`, `knowledge-retrieve`, or `knowledge-audit` through `scripts/memory_integrity_workflow.py`. Keep the worker interpreter isolated and pinned; do not replace canonical histories, auto-install the runtime, create a second manager, or generate answers through Semantica. Mandatory units and current access come from independent task contracts. Unavailable runtime, stale bytes, changed task, missing request binding, or unknown required audit stages block graph-required qualification.

This initial release observes real graph/vector/provenance/SHACL operations and exact protected offline requests. Meaning-bearing embeddings, general semantic entailment, live model outcomes, incremental invalidation and representative coding benefit remain separately unverified. See `knowledge-capabilities-v1.json` for granular truth.
