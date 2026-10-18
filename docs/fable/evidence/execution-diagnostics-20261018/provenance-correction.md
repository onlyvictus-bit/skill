# Offline provenance correction and memory-use smoke - 2026-10-18

Bounded result: OFFLINE_PROVENANCE_CORRECTION_VERIFIED_NATIVE_UNQUALIFIED.
This is a saved, uncommitted successor to 0f1fe58, not a new release or install.
The initial independent review remains FIX-FIRST for that published commit;
its finding is not retroactively erased by this successor. Final saved-diff
review is recorded separately below.

## Authority and decision

After the explicit offline-provenance approval question, the user answered
"do whichis best" and clarified the goal: large/complex task and coding work,
memory, chunks and embeddings, without removing important hybrid behavior or
files. The existing practical plan retains the complete quote and design.

Chosen correction: report unauthenticated diagnostics explicitly. Do not add a
new producer authority, journal, fence, service or schema. Do not claim that
this implements authenticated native provenance. Fable remains the governor;
Deep Plan compared alternatives; Superpowers supplied review, root-cause,
failing-before tests and observation-based completion. Existing Fable records
are the execution ledger; generic cleanup/automatic-commit steps do not apply.

## What changed

- practical_execution.py emits DECLARED_DOLT_CLIENT for new packets. Existing
  SEALED_DOLT_CLIENT packets remain readable without rewriting stored bytes.
- Every diagnostics-reader result, including unavailable/error results,
  explicitly carries provenance_status=UNAUTHENTICATED,
  producer_authenticated=false and invocation_identity_verified=false.
- The controller's no-journal/unreadable fallback has the same explicit limits.
- capture_complete continues to describe retained byte/status completeness,
  not who produced it. A canonical caller-built reason may remain available,
  but cannot become authenticated output, APPLIED, replay permission or a
  fence verdict. Rehashed invocation claims remain self-reported, not verified.
- Five new regressions exercise actual supported reserve/consume/mark-unknown
  APIs, rehashed identity claims, historical packets, current capture labels
  and the controller fallback. Existing sixteen diagnostic tests are intact.

INTENT: remove a misleading provenance implication while retaining diagnostic
bytes, history compatibility and all existing no-authority/no-replay behavior.
No companion ledger/schema, SQL predicates, protected consumer, public CLI
activation, memory/chunk/embedding module, SKILL, capability or ZIP changed.

## Red/green and exact-source verification

Evidence root is the sibling build-validation directory of this source-git.
All receipts retain exact commands, logs and hashes; nothing was deleted.

| Check | Observed result |
| --- | --- |
| Before source fix: diagnostic regressions | 21 run; five new tests FAIL for missing provenance/declared label; sixteen existing pass |
| After source fix: diagnostic regressions | 21/21 pass |
| Connected practical MI groups | 280 run; 279 pass; one existing live-dolt-ignore expected-failure placeholder |
| CM practical journal/dispatch | 18/18 pass |
| Practical public CLI preflight | 9/9 pass |
| Preservation | 524 baseline files retained; 518 outside six intentional edit targets byte-identical; no prior class/function removed |

Red receipt execution-provenance-red-3007eddc5e3e4500a12f9a06d5f40a7a/Receipt.json
SHA-256 ef4a2cb6e6d5acc170ee422cdf002966342faf8802f548c301363569db0c931c.
Green receipt execution-provenance-green-9ad8b068488f40ce8f82a40443795773/Receipt.json
SHA-256 b45be9d2f7f814ac54a942b9bf4dc71073dfced224c3dd45f941450e462bf855.

Final focused receipts:
- execution-provenance-final-mi-bd5ab2cd49d2499aaf24dc77006b1c31/Receipt.json
  SHA-256 33b2137e4b1cb84a033b479b7ba85ef9124a22a77a679900844202abe8a7915f.
- execution-provenance-final-cm-c26a095eda1c40e98cfad0656fd8ab27/Receipt.json
  SHA-256 585e89badce9761b8acde8afcb26ad2a5eb6b1763fe69fc3d9b81058fb07d22c.
- execution-provenance-final-cli-fd8e8fcf0338444d9704a84f28585e14/Receipt.json
  SHA-256 18ee9a6d01db91e52655ecb501a16dc332f189fd997af3f83a6ec1c38bf62570.

Verify-Provenance-Correction-20261018.py verifies exact source bytes, prior
definitions/files, logs, red/green results, false qualification flags and
broader before/after outcome sets. Proof:
Provenance-Correction-Verified-a67d42c62bd8475085c16f8e5cc468a0.json,
SHA-256 dbbeea953c22756816ffdd620a8d11bae2c9330ab96ccd045be3ab42c42ed4c8.

## Broader regression evidence - not full green CI

The same strict retained-fixture adapter ran each group before and after the
production correction. It prohibits deletion, network and all subprocesses;
tests requiring those operations are therefore blocked, not silently skipped.
All failures/errors and traces remain in the exact receipts indexed by the
proof above. Comparing outcome IDs does not prove blocked behavior works.

| Group | Run each phase | Failures before -> after | Errors before/after | Skips | Expected failures |
| --- | --- | --- | --- | --- | --- |
| MI v2 | 663 | 15 -> 10 | 119 | 54 | 1 |
| MI legacy | 21 | 0 -> 0 | 4 | 0 | 0 |
| CM v2 | 208 | 2 -> 2 | 13 | 0 | 0 |
| CM legacy | 21 | 0 -> 0 | 17 | 0 | 0 |
| Repository | 19 | 0 -> 0 | 0 | 0 | 0 |
| Evals | 10 | 0 -> 0 | 0 | 0 | 0 |

942 cases per phase. Only the five intended provenance failures closed;
no new failure/error IDs appeared and existing skip/expected-failure sets
were unchanged. Many broad errors are deliberate retention/process guard
refusals: for example atomic writers attempt unlink of an already-renamed
temporary path, or a companion-handshake test requires a Python subprocess.
Historical content manifests still describe old releases and fail on WIP
source. These gates are not waived or repaired by a baseline comparison.

## User-goal smoke: memory, exact chunking and fresh-process recall

Public-Memory-Smoke-20261018.py exercised the existing offline-run/verify CLI
with real matching companion Python children, not mocked CLI responses:

1. Fresh-process recall reopens all three declared fixture unit records and
   retains zero-write shadow views.
2. Unchanged resume does not duplicate work or overwrite the saved ledger;
   a changed task refuses reuse.
3. Empty source is rejected.
4. Unresolved review input refuses before creating mutable run state.

All four passed. Reviews are explicit TEST_ONLY fixtures, not model-generated
semantic evidence. An additional pure mechanical synthetic source had exactly
52,428,800 bytes (50 MiB), including Unicode: 801 primary units and 200 chunks,
exact byte reassembly, no duplicated primary accounting, and a deliberately
missing primary was detected. This is not a 50 MiB LLM read/understanding claim.

Receipt public-memory-smoke-c614b74c0d26448aa28c7cf046aec88f/Receipt.json,
SHA-256 87eced43c5cc2a155e4ccdfd8744e9191097c839837ec6f140b37080dd9f43bf.
The first retained smoke attempt failed in the new test helper's Windows
audit-argv handling; the next hit inaccessible default TEMP in a child.
The helper was corrected to match exact Windows Python CLI prefixes and use
its retained private temp directory. Neither failure was a product repair or
counted as a pass. Both failed receipts remain alongside the final one.

The loaded project SKILL and R2/complete-read/memory references explicitly say
this workflow does not increase context size, generate reviews, configure a
memory service, or prove semantic correctness. Those boundaries remain intact.
Embedding quality/model benefit, real project coding benefit and live-memory
restart persistence were not tested. No provider/model call was made.

## Rulings, deferred scope and next priority

Ruling: preserve the offline skill and prove its useful public path now;
do not make optional Beads qualification a false prerequisite for mechanical
chunking or fixture-based persisted recall. Native stages remain tracked, not
removed or mislabeled complete. Preserve all hybrid features and original
packages/instructions. Larger task-specific retrieval/embedding evaluation
and core release/install qualification need their own measured acceptance.

Deferred minor: capture_transport's short docstring says "fixed identity".
The module/validator/reader contract now explicitly limits every such field
to a claim, with false authenticity/identity flags. The phrase does not add
authentication; no extra source change is made merely for wording polish.

Current source is saved locally, not committed/pushed. Exact-commit CI was not
dispatched. Packages and installed skills remain unchanged. No native binary,
shared database, live memory service or external AI was invoked. All baseline
files and prior evidence are retained. This is not full M7/R5/release readiness.

## Final saved-diff review

Fresh reviewer /root/provenance_successor_review is checking the saved successor
against the approved explicit unauthenticated contract. Its final verdict and
parent acceptance are recorded here when observed, not inferred from tests.

Observed final result: SHIP for the bounded correction only; parent Fable
acceptance is VERIFIED WITH CAVEATS. The reviewer found no blocking or moderate
defect remaining in this scope. It independently ran nine selected in-memory/
mocked-boundary tests successfully and separately forced the unreadable-journal
controller branch. All outputs retained unverified/unauthenticated status and
false producer/identity flags. It checked the exact source hashes against the
saved green/final receipts, the broader outcome comparison, preserved files,
updated authorization/state and public memory-smoke limits.

Its one P3 minor is the "fixed identity" short docstring wording already
recorded above; the explicit result contract and module/validator documentation
control its interpretation. That polish is deferred, not an authentication
claim. The reviewer explicitly declined native execution, authenticated origin,
actual argv proof, model/embedding quality, full CI, packages and installation.
The parent reproduced the load-bearing public-API forgery, red/green changes,
connected regressions, preservation and public workflow rather than accepting
the review report alone. R1 is complete for the approved offline contract;
the parent P1-P5 and broader product/release gates are not marked complete.

## Provider-free knowledge-contract check

After that review, the parent directly reran three existing
TypesAndIsolation tests in test_knowledge_offline_engine.py:
test_coding_and_test_evidence_type_rules,
test_wrong_domain_range_and_foreign_predicate_rejected, and
test_malformed_type_records_are_explicit_value_errors. All three passed.
The Python process denied subprocess, deletion and network-connect/bind audit
events; numpy, sklearn and semantica were absent from sys.modules afterward.
No product source changed for this check. These are type/input-contract checks,
not an observed vector search, embedding inference or semantic-quality test.

The parent also inspected offline_engine.search_vectors and the existing
knowledge-models reference. Lexical TF-IDF/LSA and learned embeddings are
different paths; neither fixture recall nor successful graph type validation
establishes learned retrieval quality. The reference records a prior 12-trial
coding experiment with no demonstrated coding benefit; that experiment was
not rerun in this correction. Optional model/runtime installation, evaluation
and activation remain outside this completed offline provenance repair.
