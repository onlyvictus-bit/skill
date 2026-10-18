# Practical fence continuation checkpoint — 14 October 2026

Status: PARTIAL_NOT_RELEASE_READY. The human approval for isolated stages P1–P5 remains valid. No new milestone approval is needed for the same scope. Do not substitute the prior strict expiry-before-save contract or relabel its failed candidate as passed.

## Exact retained evidence

Source baseline: commit ad3f66e4cd885494cf5d4b10453d089288d7c517, tree003cf1770d86b684462ca6feb50060b8f9e7a280, Source-Baseline.json outside source checkout. All 401 baseline tracked blobs originally matched Git.

The test checkpoint is outside the checkout at:

`C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\checkpoints\checkpoint-bd07186ce75e475eb77fec6d5bf1f03b\Practical-Checkpoint.json`

SHA-256: `25f65176f6b598f4e90a5ab272da6fc2b8471a34738d54133e9032339219f1fd`.

The checkpoint recorded stable source bytes during testing, 395 unchanged baseline files and six intentional existing-file changes (CM ledger and canonical Fable JSON). All 46 checked old release/Semantica files remained unchanged. This document is a subsequent governance addition and is not claimed to have existed in that earlier source manifest.

Focused executed suites:

- Lease-bound contract/SQL-template/quarantine: 10 tests passed. Parsing and generated-text evidence only; no native SQL or safety qualification.
- Practical CM journal plus ledger/history/coordination regressions: 48 tests passed, including one reservation winner across two connections and UNKNOWN-to-exact-APPLIED recovery after reopening.
- Retaining native runtime policy: four tests passed. No native fence behavior was exercised.
- Predecessor/backend/consumer/unfinished CLI suite: 21 tests ran, one failure and ten errors. The reviewed-invalid predecessor is deliberately stopped; old fixtures omit the new node field; public CLI integration remains absent. Do not skip these failures or count this suite green.

All source Python files captured in the checkpoint parsed without AST errors. This is syntax evidence, not behavior evidence. No final ZIP or content manifest was generated.

## What the review changed

The initial sidecar candidate was not a real Beads lease fence. It relied on caller deadline fields, could transfer ownership through a title request, had incomplete per-action transitions, and could lose the exact receipt because of multi-table affected-row assumptions. The injected runner could also fabricate a consumer readback. No native execution of that candidate occurred in this continuation.

The predecessor's public mutation methods now raise E_PRACTICAL_LEASE_REVISION_REQUIRED before dispatch, and its consumer raises E_PRACTICAL_REVISION_STOPPED before reader registration. Code bodies remain inspectable as historical development material; they are not an active fallback. No generic native writer/acceptance/merge qualification is enabled.

LeaseGuardedTitleRequest now binds the original exact real lease holder, granting node, granted-at, expiry and heartbeat snapshot; it has no title-transfer or caller deadline-extension fields. Fixed deadline derives from the original lease expiry. Its digest binds every field. Native lease timestamps use the pinned second-precision representation and calendar/order validation.

The separate practical_lease_sql.py template reads actual leases plus stored namespace/grant state in its authorization snapshot before the harness-only pause; changes title and row_lock only; uses separate issue/grant cardinality assertions; and stores numeric conflict token plus DB authorization time with the operation receipt before COMMIT. It has no process-dispatch entry point. The v2 schema/assertion routine and actual Dolt rollback/grammar proof are still missing. Its string tests cannot prove native correctness.

## Native access and review limitations

An agent-terminal setup attempt retained:

`...\native-attempts\run-a18f8b4558624623b0a62c95181a0648\Practical-Pilot-Receipt.json`

SHA-256: `a38619d99db9b5d3bca3d2750a40e4678707eaebafe138eb1d9a64822943b179`.

It failed creating the new physical scratch root with WinError5. Zero native commands were dispatched. An earlier read-only ancestor check also observed WinError5 on Documents. These are agent-host access observations, not evidence that the user's previously successful normal-PowerShell Beads host test has regressed. Do not change ACLs, disable Beads gates or retry an uncertain mutation.

All three native helper agents stopped with `Your workspace is out of credits`. The reviewer delivered critical partial findings, not a final approval. No external Claude/Gemini consultation was made or authorized. Resume independent review when the workspace can run the reviewer; do not describe self-review as independent.

## Required next implementation, in order

1. Finish the new ignored v2 namespace/grant/operation/token schemas and scoped assertion routine. Namespace identity must be DB-created/read back, not an echo of a caller value. Prove stale/error cardinality failures cannot leave partial effects even if the CLI's error handling differs from assumptions.
2. Implement exact protected initial claim, reassignment, expired reacquisition, heartbeat and release/reclaim semantics using real leases and DB-minted 300-second expiry. Preserve every old operation's original lease deadline. Retain history; do not add deletion or use a raw SQL grant seed as claim proof.
3. Add a sealed pinned native transport/reader, rejecting public injected runners and shadowed consumer methods. Bind all lease facts into the CM intent/receipt. Wire the actual workflow and verified no-dependency scratch policy/CAS observations; dependent/foreign/wisp/unsupported workflows must refuse. General Gate B acceptance remains separate.
4. Build and run the real scratch pilot: authorization snapshot held during Bob's committed newer grant, Alice conflict/no effect/no receipt, current-owner success, true expiry/heartbeat/ABA cases. Run only after the candidate is consistent. Do not ask the user to rerun the old host-only diagnostic or an unfinished helper.
5. Observe actual outstanding-native-client interruption and separate owned-server crash/restart, fresh-process original-op readback, and repeated recovery with no second mutation.
6. Finish independent adversarial review, baseline Windows path/containment proof gaps, source and extracted-package regressions. Only then build matching capability/instruction/companion/content/ZIP/release/report artifacts. Old package manifests remain unchanged now because the source is not final.

P1 remains partially implemented; P2 incomplete; P3 journal portion unit-tested but consumer stopped; P4 runtime policy prepared but native interruption/race proof absent; P5 not ready. No whole approved stage is declared native-complete by this checkpoint.

Publication, installs, shared databases, provider calls and deletion remain excluded. Existing installed copies were not replaced. The only eventual completion label justified by this approved range is a narrowly scoped ordinary local protected-adapter capability, not full M7/R5/native merge, strict expiry-before-save, power-loss or production qualification.

## Current continuation — 2026-10-18: original execution diagnostics

This latest entry supersedes older next-action wording above; older evidence
is retained, not rewritten. Source checkpoint before this successor is
fbabbab5e69e924ac4aae6c3a4fb6de62aae3d55 on the practical WIP branch.
The lease-v2 backend AND internal consumer already exist. Only the old unsafe
v1 consumer remains stopped; practical public commands stay preflight-only.
The unchanged original GPT handoff is now explicitly marked historical with
an appended correction. Do not revive its stale runtime or fixture advice.

The next bounded local step is diagnostic preservation, not another fence:
`practical_execution.py` captures fixed selection/SQL/command hashes, the
actual process exit or timeout class and Base64 raw-byte prefixes (64 KiB per
channel), plus original lengths/full hashes and explicit missing/truncated
state. Exception messages and environment values are not serialized. A normal
native command may itself print sensitive content; these retained diagnostics
are local evidence, not a payload approved for external sharing.

The sealed backend binds this observation into the existing protected CM
UNKNOWN reason before the consumer can swallow the exception. The controller
reads the original CM history independently and exposes diagnostics with
`causal_status=UNVERIFIED`. Worker-provided causes remain ignored. No companion
schema/API change, SQL-predicate change, new dispatch route, second ledger,
native acceptance or retry permission is introduced. A clean parsed result
with an invalid/foreign receipt retains its original transport bytes too.

Current plan and checks: see the 2026-10-18 section in the existing practical
plan and `docs/fable/evidence/execution-diagnostics-20261018/verification.md`.
Failing-before and passing-after raw receipts are retained under the existing
`build-validation` directory outside this checkout. The first wider test run
caught an incorrect new-test expectation: the existing model returns exit 1
and stderr, not a spawn exception. That expectation was corrected against the
unchanged model source; the failed receipt is retained, not counted green.

A fresh Fable reviewer was attempted but could not start because the workspace
was out of credits. Independent review remains PENDING; parent inspection is
not a substitute for it. Full unmodified CI, source/package preservation gates
and native proof are not claimed by the focused offline checks.

Next: review this exact diff, then separately authorize and run the pinned
native grammar/forced-rollback preflight before the three-arm synchronized
race. Native diagnostic interpretation still needs actual pinned-runtime
observations; no error-string guess may replace that proof. Enabled stale
effect stops the candidate; missing/transport/syntax/permission cause stays
INCONCLUSIVE. Prior manifests/ZIPs/installed copies remain unchanged and
publication or promotion requires separate approval. No files/data are to be
deleted, no native activation is allowed, and no API/LLM key is needed.

## Latest continuation - 2026-10-18: independent review completed, FIX-FIRST

Published source remains 0f1fe58b66a03e34244b1f2ac56e5588d2489eee;
the current turn began with a clean tree. Fresh native Fable Sol review of
fbabbab5..0f1fe58 completed successfully; the old workspace-credit blockage
is not the current review result. Verdict: FIX-FIRST, P2/moderate provenance
finding, not an unauthorized-write or native-acceptance finding.

Normal CM reserve/consume/mark-unknown APIs can retain a caller-built packet
which the diagnostics reader labels available/complete/SEALED_DOLT_CLIENT.
Rehashed changed port/command digest are accepted too. Both reviewer and
parent reproduced this without a native process or database tampering.
History hashes and completeness do not authenticate a producer. Causal status
remains UNVERIFIED; no APPLIED, replay or fence verdict was created.

Review/evidence: docs/fable/evidence/execution-diagnostics-20261018/review.md.
The existing practical plan now sequences a bounded provenance correction
before pinned grammar/forced-rollback preflight, paired race and later
heartbeat/ABA/interruption tests. The recommended correction explicitly
labels unauthenticated diagnostics; it does not introduce a new fence or
another authority store. Human approval is pending before that behavior/
evidence-contract change. No native helper is claimed ready to execute.

Fresh focused runs reproduced 301 passes plus one existing expected failure
across 302 MI/CM/CLI checks, zero unexpected failures/errors. Adapted retained
offline checks only. The existing pinned binaries were hashed, not executed.
No source/SQL/CM change, native test, deletion, install, package regeneration,
commit or push was performed in this review turn. All qualification flags
remain false. Current task and unmet parent P1-P5 gates remain unchanged.

## Latest execution - 2026-10-18: approved provenance correction saved

The human approved the recommended offline direction with "do whichis best"
and clarified that useful memory/chunk/embedding support is the priority.
The bounded correction is now implemented, not awaiting design approval:
new captures say DECLARED_DOLT_CLIENT, old packet bytes remain compatible,
and every available/unavailable result explicitly reports unauthenticated
producer and unverified invocation identity. No new authority store or fence.

Five new regression failures were observed before the source fix; all 21
diagnostic checks pass now. Connected practical groups: 280 MI (279 pass plus
one known expected failure), 18 CM and nine CLI checks. Same-policy broader
before/after discovery ran 942 cases each; only those five failures closed,
with no new failing/error IDs. Existing guard blocks and frozen-manifest/
other failures are retained; this is not full green CI or a release verdict.

Existing public offline workflow also passed four fresh-process fixture tests
for recall, no-duplicate resume and invalid/unresolved-input refusal. Pure
50 MiB mechanical partition/reassembly and missing-primary detection passed.
No embedding/model quality, semantic perfection or live memory-service
persistence was inferred from those observations.

Evidence: docs/fable/evidence/execution-diagnostics-20261018/provenance-correction.md.
All 524 original files remain, 518 unrelated originals byte-identical. No prior
class/function removed, packages/installed copies/native flags unchanged.
HEAD remains published 0f1fe58; this successor is uncommitted/unpushed.
Fresh saved-diff review is the current gate. After acceptance, prioritize
task-relative core usability/retrieval/embedding and packaging acceptance;
the optional native ladder remains separate and unqualified, not deleted.

Final saved-diff review is now completed: SHIP for this bounded explicit-
unauthenticated correction, no blocking/moderate finding. Parent acceptance:
VERIFIED WITH CAVEATS; nine selected reviewer checks passed, with parent
independently reproducing the load-bearing source/test/preservation claims.
One minor short-docstring phrase is deferred and recorded in the report.
R1 is closed, not the whole native/product campaign. Next priority is core
memory/chunk/retrieval/embedding task acceptance and source/package usability;
the native ladder, publication and installed replacement remain separate gates.

## 2026-10-18 - local correction committed; N1 acceptance approved

User authorized "COMMIT IT AND THAN". The reviewed eight-path correction is
locally committed as 6c5ba969feecabcdb1c05be12de41512aec01220, with no file
deletions and nothing pushed. Fresh precommit practical MI evidence:
execution-provenance-precommit-24db89fb96f64abda6feff54de00d63b/Receipt.json,
280 cases, 279 pass and one prior expected failure; source stayed stable.
The final preservation verifier passed before commit. This supersedes older
uncommitted status text without rewriting that historical evidence.

The user separately approved "N1 acceptance harness and local tests". Follow
the latest N1 section of the existing practical plan: real public offline CLI,
retained coding-source bundle, exact coverage/fresh recall, no-write resume,
copied stale/missing/corrupt/rehashed-proof variants, and non-vacuous oracles.
No production code, model/runtime activation, native operation, install,
package change, push or additional commit is included. Existing parent native
requirements remain unmet. Next: implement the external retained test harness
under build-validation, observe N1-A through N1-H, review and report honestly.

## Latest N1 checkpoint - 2026-10-18: complete with explicit caveats

N1 is now executed, not awaiting harness implementation. The initial fresh
independent review returned FIX-FIRST for a missing rehashed-response-content
control. Parent observed the new control-checker fail on that initial receipt,
added only a retained copied-response/ledger/map test arm, and observed it pass.
All previous harness/receipt/proof bytes remain; no product change was needed.
The final entire N1 run passes eight groups across 13 actual public CLI calls
(eight success controls, five correctly caused refusals), including inner
E_RESULT_CONTENT after outer file/CAS hashes were valid. The original 24 saved
run files stay byte-identical, and 60,704 source bytes/965 units/four chunks
reassemble exactly. All 527 final-run baseline files are retained; product
trees remain exactly the bytes committed as 6c5ba96.

Final receipt core-memory-acceptance-84d3b1f1dbd14de49676e64ea381053b/Receipt.json,
SHA-256 5102e7159d7a0b968e3fe9f6739ebb95b28dee5eb06154581318355a07ac557f.
Details, red/green hashes, focused regressions and reviewer scope are in
docs/fable/evidence/core-memory-acceptance-20261018/report.md.

Parent verdict: VERIFIED WITH CAVEATS for N1 only, after the one review-driven
fix pass and direct observation. No second independent review of corrected
bytes was performed or claimed. Fresh MI279+1xfail, CM18, CLI9 checks pass;
the earlier broad non-green regression state is not cleared by them.

Exact next resume: N1 is closed. Define task-relative retrieval/model quality
acceptance, or a scoped offline-core release with broad and clean-package
checks. Model/native execution, new commits/pushes, packages and installed
replacement remain separate approvals. No live AI, model download, native
Beads/Dolt test, deletion of existing files or installed change occurred.
N1 plan/state/report and private test helpers are not committed; the earlier
eight-path correction commit is complete and still unpushed by this agent.

## 2026-10-18 - N1 records committed; N2 offline baseline approved

N1's four repository records are committed locally as
0905d0e6ca12bfac16ee28794e63e25dd2a846f6; no push. Private helpers/raw runs
remain retained outside Git. N1 artifact verifier and rehashed-response checker
passed again before commit. Do not call the private helpers a portable release.

The user explicitly approved N2 offline baseline/readiness checks. Follow the
latest N2 section of the existing practical plan. No worker interpreter is
selected; the current Python3.14.3 has no numpy/sklearn/semantica. N2 measures
actual no-worker behavior, source delivery, literal discovery and refusal
boundaries, not a fake embedding/model comparison. Four independent coding-task
file obligations and query strings are frozen before retrieval. Preserve all
source/index/pack/oracle/failed artifacts. Any new writer.lock cleanup is a
test-only archive of this child's own newly created scratch lock, never removal
of foreign or historical locks. No model/native run, install, production change,
push or package/installed change is approved. Next: implement/run the bounded
private harness, verify sources and review its measured result.

N2 execution checkpoint: all ten bounded groups passed through 13 actual public
CLI calls, with four specifically caused refusals. Manual required-file packs
reopened every declared unit, but no-worker ranked results were empty; ordinary
natural-language substring queries found no units. Literal required-file hits
were 2/2,1/1,1/2,1/2. Do not present mandatory inclusion as discovery quality.
No optional runtime/model was selected, activated or installed. Fresh selected
host contracts passed22/22 (not full discovery or ranked runtime tests).
Report: docs/fable/evidence/retrieval-baseline-20261018/report.md.
Primary receipt SHA-256 a5bbe45fc7b26f76b9baf9dcd6215a5f6bc3de40eba867bb08c23384f0dd24f2.
Source/project/index/oracle inventories are retained and unchanged. Fresh
read-only review is now the gate, not another unimplemented harness.

N2 review/fix checkpoint: initial independent verdict FIX-FIRST identified two
missing retained-evidence obligations (exact locator IDs/bytes and exercised
reorder rejection). Initial run remains unchanged. Parent observed the coverage
checker fail before correction and pass after a new complete harness run.
Corrected receipt873e696aa2754c7aa0d142c08c03a14a SHA-256
0667b4c80874ae52d2d6ee5dcabf4796894905dd8649d94671e685ddf29bf93b.
Ten groups/13publiccalls, eight retained locator payloads, four rejection probes,
fresh verifier and selected22hostcontracts pass. Repeat read-only review gates
final acceptance. No product code changed and no model/native execution ran.

The user correctly ran the host-only metadata helper. Its receipt
Retrieval-Runtime-Discovery-b5b2744dbe0c439788aad9108252a48e.json SHA-256
3b3d0cb032777eeb313efc39367f78c39b930c429f67d9b18250c71784501a1b
was read and verified. Python3.12.10 has NumPy1.26.4, but sklearn/semantica
absent there. This resolves package-discovery UNKNOWN for that interpreter,
not worker readiness; do not repeat that host check or auto-install anything.
After N2 review closes, next unmet gate is a supported pinned runtime setup
decision/approval, not another N2 harness rebuild or native Beads diversion.

## Latest N2 checkpoint - 2026-10-18: complete offline baseline, quality blocked

Repeat independent read-only acceptance review returned SHIP for N2 only,
closing both Important evidence gaps after correction. Parent accepts
VERIFIED_WITH_CAVEATS based on its own full rerun and source/artifact verifier.
Ten groups/13publiccalls, eight original locator payloads and recorded reorder
rejection,22selectedcontracts, unchanged product trees and retained528baseline
files are verified. Initial FIX-FIRST/red/old helper/run artifacts remain.
Ranked/embedding quality is BLOCKED_NO_SELECTED_RUNTIME, scores null. Native,
fullCI, model/real-project benefit, releases and installed readiness stay unmet.

User's host metadata command was correct; receipt already read/hash-verified.
Do not ask them to rerun it. Python3.12.10 has NumPy1.26.4 but lacks sklearn/
semantica; current Python3.14.3 lacks all three. No worker is selected. Next:
show a supported isolated runtime setup/evaluation plan and ask separately
before any installation or activation. Prefer existing lexical/LSA route
without learned weights initially. Never alter global/current Python packages,
install, download weights, run native Beads or promote flags under N2 authority.
N1 commit0905d0e is local; N2 docs/helpers are uncommitted, nothing pushed.

## N2 local commit authorization - 2026-10-18

AUTH: user said "COMMIT AND WHAT NEXT STEP?". The containing Git commit records
the four reviewed N2 Fable documents plus this publication-status annotation.
Earlier uncommitted wording is historical, not the current resume instruction.
The private harnesses, original/failed runs and raw receipts remain retained
outside Git; this is not a portable release. No push or installation is approved.
Fresh precommit artifact/coverage checks and22selectedcontracts pass; protected
product trees remain unchanged. Next show the bounded supported-worker setup
and lexical/LSA evaluation plan, then ask separately before installing or
activating it. N2 is closed; ranked/embedding quality and full release remain
unqualified. Do not repeat N2, the host metadata command or native feasibility.
