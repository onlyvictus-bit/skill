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

## 2026-10-18 - N3 plan drafted, setup not yet authorized

HEAD0584a89f11bfeec4c9ae8caa81f4492cf10c2abb, initially clean. User requested
the next step after a deep plan. The appended N3 section in the existing plan
defines isolated pinned Python3.12 runtime setup, actual lexical/LSA public
retrieval, frozen independent discovery metrics and fresh verification/safety
checks. No product/runtime/package/installed file changed; no setup/test of
the actual worker has run under N3. No commit/push approval is inferred.

New primary-source finding: worker rejects Python3.14; pinned upstream
Semantica0.7.0 requires NumPy>=2.0.2. User's existing3.12 NumPy1.26.4 is not
sufficient. Preserve existing packages; use only a new isolated environment.
Metadata/handshake alone cannot establish a working numerical retrieval path.
Installers can clean their own new transient files; the no-deletion constraint
therefore requires an explicit narrow exception before any installation.
An async N3 scope/installation/temporary-cleanup approval has been requested.
Plan review remains pending. Do not execute N3 until both scope/installation
approval and bounded plan review are recorded. Do not re-ask within that scope
after approval or repeat N1/N2/host discovery as an invented next milestone.

## Latest N3 planning checkpoint - ready, installation decision pending

The independent reviewer returned SHIP for the corrected plan only; no blocking
finding remains. The exact reviewed snapshot cdf1cd7fa28cbee40d603572929f2b2adf0d71bd7ccab6aec66ca2a35a2a5c9f
is retained privately as N3-Reviewed-Plan-cdf1cd7f.md. Corrections fixed authority
to one environment/one setup cycle, explicit private pip cache/index and
absolute/hash-bound requirements, non-installing dry-run wording, exact retained
TemporaryFile streams and the distinction between allowed repository validation
tests and forbidden execution of the copied target corpus. No product fix was
made or needed to accept this plan.

Parent preflight verifies528baselinefiles retained,525outside three planning
records unchanged, current N2 report and old receipts unchanged, clean diff
format and valid state. It establishes no runtime or retrieval-quality proof.
The pending async N3 approval is the only execution gate: installation, local
test-only worker selection and installer-owned new transient cleanup. Do not
install/create the harness until this approval is recorded. Once it is given,
execute the existing N3 plan without another planning/approval loop for the
same named scope. No commit/push or installed-skill replacement is included.

Final receipt correction: source verification detected a mistyped worker.py
digest in the first private N3 preflight receipt; actual product bytes matched
0584a89. Preserve that failed receipt. The measured successor
N3-Plan-Preflight-corrected-20261018.json SHA-256
c993e852d52a4d4933c2422c4d248279bac2e8a07de169a127b4d6ab658f8c9e
is the current preflight evidence. It changes no execution scope or readiness
claim. The independent verdict applies to the plan, not to a tested runtime.

## 2026-10-19 - N3-A through N3-D authorized, execution started

The user approved the named isolated setup/tests and the narrow cleanup of new
installer-owned temporary files only. No broader deletion, product change,
commit/push or installed-skill replacement is approved. Continue the reviewed
plan, not another planning gate. Private harness TDD comes first, then the single
setup cycle. No actual worker success is claimed at this checkpoint.

Latest:20harnesscontrols and22existinghostcontracts pass; four original coding
inputs are frozen. N3-A stopped at the first interpreter launch: py.exe exit101,
pinned Python3.12 access denied, no venv/no resolution/no install. Do not repeat
setup from the agent, change ACLs, install another Python or create another run.
Prepare/use the bounded normal-host continuation of the same empty run only.
N3-B/C real-runtime orchestration and observations remain unfinished/blocked;
N3-D fresh review had a capacity failure and one retry. Report is
docs/fable/evidence/retrieval-runtime-20261018/report.md. No product/package/
installed-copy or commit/push operation occurred; all qualification flags false.

Final checkpoint:21/21 controls pass after exact3.12.10 identity regression;
22selectedhostcontracts remain green. Both same-role execution review attempts
failed from model capacity, no substitute model used. Independent review remains
UNAVAILABLE, not passed. The normal-host N3-A entrypoint is parent-checked and
hash-bound, not independently execution-reviewed. It continues only the same
empty run; `-ValidateOnly` checks guards without installation. N3-A–D authority
already exists; obtain host evidence rather than another approval loop. No actual
N3 worker/search/embedding readiness or whole-skill completion is established.

## Latest host receipt — resolver path failure, 2026-10-19

The user correctly ran the host command. Receiptf556ab5071892b5ae1d4daf0765fd5b74433aa76496b0998da871808f471571e
is verified with6matchinglogs. Venv creation and exactPython3.12.10 isolation
passed; resolver started and failed at Git clone ('$GIT_DIR' too big), no install
started. The env now exists and must be retained, not recreated/cleared/moved.
Existing one-shot entrypoint is NOT a current retry instruction.

224-character .git path exceeds installed Git's observed220-character gate.
Read-only220/221/224 controls reproduce this; core.longpaths=true does not fix
this guard. Root cause is the helper's overly deep installer TEMP layout.
Host-Resolution-Diagnosis.json retains measurements. Existing helper/pins,
receipts, source/package/installed skills and Git are unchanged by diagnosis.

Current gate: user approval for the explicitly proposed N3-A2 short-temp plus
one-extra-resolution amendment in the same existing Fable plan. Preserve the
one existing venv; propose a separate short owned installer workspace and one
successor helper, same requirements, one new resolver then at most the original
unused install. No new env, pin fallback, credential/model/native call, deletion
of old data, commit/push or promotion. Await approval before recovery build/run.
Do not repeat normal-host metadata discovery or the consumed setup attempt.

## N3-A2 approved and prepared — 2026-10-19

User approved the bounded recovery. Existing venv retained; one short path is
reserved in the plan: C:\Users\sakth\Documents\Codex\n3-install-ef149e14\tmp.
New successor/test/PS entrypoint live inside the same N3 run.16newcontrols plus
21oldharnesscontrols and22selectedcontracts pass. Prediction123bytes vs220gate;
no actual new clone/install/worker observation. Agent short-root creation denied;
no resolver allowance spent. No more agent directory retries or ACL changes.

Initial successor lost its first pre-workspace exception/receipt; exact initial
code11cc57df retained. Later real New-Item denial is separately recorded. Current
successoreba239e5 fixes early error retention and missing/aliased tmp rejection,
with RED-to-GREEN tests. Native reviewer unavailable at capacity again, no pass.

Next use the existing already-approved one-time host continuation
<same N3 run>\Run-N3A2-20261019.ps1 in normalPowerShell. It creates the same owned
short root, reuses current venv and permits only one new resolver/original unused
install after validation. Retain recovery-a2/Receipt-host.json; never rerun failure.
No new approval for N3-A2 required. No commit/push/install-skill/model/native action.

## Latest N3-A2 host result — UTF-8 audit and Windows scope gate, 2026-10-19

User ran the host command once. Receipte857e729 confirms identity and the one
additional resolver exited0; install never started. Git short-path clone fix is
observed. Recovery stopped reading the914300-byte UTF-8 pip report with default
cp1252. Private read-only auditor corrects decoding without changing old helpers,
receipts, environment or dependencies;7newcontrols RED7toGREEN7 pass.

Report92fca79b contains all50approved exact versions plus3Windows dependencies:
colorama0.4.6, tzdata2026.5, win32-setctime1.2.0. Strict original scope rejects,
correctly. All53pass source/pin checks only in an unapproved in-memory proposal.
No resolver/install/model/native command was run by this diagnostic turn.
Retain resolution-diagnosis-a12e37b4818148c3b47f80fd8bfd7195/Diagnosis.json,
SHAebc12741, and resolution-controls-c7d531a9cea74482afee2c14d7cf4f92/Receipt.json.

Next approval is N3-A3's private Windows overlay and guarded install-only
continuation: preserve50existingpins/source revision; add only3exactversions;
reuse existing saved53report, venv and owned shortworkspace; no third resolver;
at most originalunusedinstall then original N3-A checks. Do not rerun any old
script or silently accept extra dependencies. Actualretrieval/N3-B/C/D remain
unverified. Fresh read-only review requested; no review pass assumed.

## Current N3-A3 resume — host continuation ready, 2026-10-19

User approved exact3Windows overlay additions and originalunusedinstall.
Preparedff0dbb79 seals originale719eda7installer,53savedinputentries (52wheel
hashURLrefs+VCScommit), original50pins and fullvenv inventory. Preparation and
actual offline preflight passed. Agent identity attempt started only the venv
launcher and exited103 with exact "No Python at" originalWindowsApps alias,
emptystdout. Receipt ee02b50e retained; installclaim/install are absent and
full861files107dirs plus repository remain unchanged. NotWinError5; old handoff
guard correctly refused. CPythonv3.12.10 PC/launcher.c places103diagnostic before
childlaunch. Alias is invisible here; normalhost availability needs observation.

New sealed Continue-N3A3-Host-20261019.py (bef35cb4) accepts ONLY this exactbound
receipt/command/error/emptyoutput and unchanged fullbaseline. Import/validation
does not patch anything. Its explicit --run adapts only the old process-local
host predicate for that same attempt; all originalfull53/identity/claim/runtime
checks remain. No extra install authority, source/Prepared/receipt overwrite,
Pythonpath or ACL change.8handoffcontrols RED8toGREEN8;17installer+7report+
21harness+22contracts also pass fresh=75selectedchecks, notfullCI/runtimeproof.
Both new finalcode-review attempts failed (credits then modelcapacity), no
substitute/pass. Parentchecked only; preserve Independent-Code-Review.json.

Next: run ONCE in normalPowerShell the existing same-run
Run-N3A3-20261019.ps1 (SHA7ca9ccfd). It validates hashes/unchangedenvironment,
allows at most originalunusedinstall with sameenv/ownedshortroot/no extra dryrun,
then pipcheck/imports/actualstatus/positive retrieval. Retain recovery-a3/
Receipt-host.json. Do not rerun failure or any oldA2/agent script. This is not
another scopeapproval. No installedskill/global/Git/model/native/deletion action.
N3-B/C evaluation and N3-D finalindependentreview remain open after success.

## Current resume — N3-A observed; N3-B/C host evaluation next, 2026-10-19

Host installation, pipcheck, numericalimports, publicstatus and realretrieval
positive passed. Receipt SHA7e3a4605c2892e1aaad5082ab52e11a2ea6b644ffb13d2790e6006b0d8e8598e
independently checked against all12logs/Result records, exact53approvedpackages,
both realWorkerClient streams and posthost17,273fileinventory. NotfullN3,
semanticquality or release qualification. Install allowance used: never rerun
setup/oldA2/A3helpers or change interpreter/security/globalpackages.

Private Evaluate-N3-Retrieval-20261019.py and contracts/tests are implemented.
14oracle+7coordinator+21originalharness+22hostcontracts=64freshselectedchecks
pass without selectedworker execution; notfullCI/actual29runtime suite. Actual
publicindex4sources52nodes170edges, no constructionworker. Naturallanguage
literal finds0requiredfiles on4questions; assistederrorprobes2/2,1/1,1/2,1/2.
Keep both, no superiorityclaim. Eight public no-workerpacks plus8freshAPI
verifications pass independent completeordered mandatorydelivery/sourcechecks.

Same-run evaluation-bc-20261019/Prepared.json SHAae96299c169076491dd238898e512448bdf6aaea0cd26daf6160cb146573d992
binds runnerf935c051/contracts1970c7e0, frozenquestions/caps/corpus/index and
olddata. Hostclaim absent. Fresh read-onlyreview requested; no pass assumed.
Prior A3review unavailable. Hostentrypoint -ValidateOnly passed without worker.

Next run ONCE in normalPowerShell, under existingN3approval, same-run
Run-N3-Evaluation-20261019.ps1. No setup/download/model/native/Git/product/
installedskill change, same approvedruntime, allfiles retained. Collect
evaluation-bc-20261019/Receipt-host.json. Never rerunfailure/tunequeries/weaken
namedrefusal checks/overwrite output. Review rankedmisses and29runtime result
beforeN3-D closes. No commit/push.

## Latest review correction — old host handoff superseded

Native reviewcompleted FIX-FIRST: bind literalpublicpack to frozenquery/caps,
enforceexact29IDs, handlefirstcaseOOV without losingindependentsafetychecks,
forgecoverage/semanticflagsseparately. Oldsource/Prepared/root/launcher/results
retained; DO NOTRUN old Run-N3-Evaluation-20261019.ps1. No hostclaim spent.
Newcontracts-v2 SHA515bd5e3 and evaluator-v2 SHA259e569d use newprivate
evaluation-bc-v2-20261019 root, sameinstalledenv/frozen4sourceexam.20v2oracle
and7v2coordinatorcontrols pass; actualself-consistent wrongquery/cap/direction
packcounterexamples reproduced oldverifieraccept/newexternalvalidatorreject.
Three actualpreworkerstale/access/no-worker refusals observed, nooutputpack.
Freshv2review/preparation/hostseals pending. Remain withinexistingN3approval;
no install/resolver/runtimeenv/product/model/native/Git/installedskillchanges.

## Latest v3 candidate — final review/preflight

Secondreview confirmed priorfourfixes but foundemptyrankedresultmisclassification.
Fixed in separatev3contracts d0bc0e9d/evaluator0f0c37e5; v2source/Prepared/root/
launcher/8literalpacks preserved. Do notrun v1/v2entrypoints. Emptyranked stays
CASE_FAILED_NO_RANKED_RESULTS, freshverified/retained but neversafetybasis;
literalempty is labelledbaseline, notranking. Onlynonemptylexicalmandatory after
freshverify suppliesbasis. Ifbotheligiblecases fail,29runs andsafetyispartial.

25v3oracle+7coordinator+21existingharness+22hostcontracts=75selectedoffline
checks pass, notfullCI/actual29runtime. Newv3publicindex4sources52nodes170edges,
0constructionworker. Prepared0d7a883a1106e68da6d753138827c9cf248877c4b2ce64e05bad93bebeadb9b5
seals samefrozenexam/newindex/originalevidence/installedruntime. Currententrypoint
Run-N3-Evaluation-v3-20261019.ps1, noinstall/download/model/native/Git/product/
installedskill change. Finalreview/preflight beingchecked; hostclaim absent.
Read finalreport/state before dispatch. ActualB/C and N3-D remainunrun.

## Current approved handoff — final v3 code review SHIP

Nativeindependentv3review SHIP_FOR_HOST_HANDOFF_ONLY, nocritical/importantfinding.
25oracle+7coordinator+21harness+22hostcontracts=75selectedofflinechecks green.
V3configuredhost -ValidateOnly exit0;2literalpublicpacks+2freshverifiers pass,
receiptf5767b4d. Source/seals unchanged; minorcopiedtarget-code wording clarified
inreport, notsealedcode. Normalhostranked/safety/29runtime stillunrun.

Extra WindowsPowerShell5.1compatibilitydiagnostic hitagentscriptsdisabledpolicy
beforepreflight, retained494bytestderr35c17a19/exit1/nooutput. No policychange/
retry/weakershell. Earlierconfiguredhostpreflightalready passed; independent
Pythoncontroller --inspect finalevidence separate. This is notnormalhostfailure.

Next ONCE in normalPowerShell, sameN3run Run-N3-Evaluation-v3-20261019.ps1,
SHAd11a168a6d3866c78a9fa3c9c92291a4d264143050e331a18a37e58fd8a5ee36.
CurrentPrepared0d7a883a; evaluator0f0c37e5/contracts d0bc0e9d. Collect
evaluation-bc-v3-20261019/Receipt-host.json; neverrerunfailure/deleteclaim/change
policy/tuneexam. No setup/download/global/product/installedskill/model/native/
Gitaction. V1/v2scripts obsolete, allolddata retained. Afteractualresult inspect
discoveryscores/misses and safety/runtime receipts, then independentN3-Dreview.

Final existingcontrollercontext preflight PASSED_NO_WORKER, receipt16f0a4ebc38a6634b8fed6789f85c74ccf31dd1e8f9b284f717f58552666af9b.
Rechecked529repofiles/1,015oldN3/454priorN1N2/fullinstalledruntime and allseals;
preservationpassed/claimabsent. Extra scrubbedchild preflight lostexistingGit
trustcontext and refusedownership; failedlogsretained/noGitexception added.
Gitdiffcheckexit0. Currentv3normalhostcommand readyundertheexistingapproval;
actualranked/safety/29runtime/N3-D stillpending, notwhole-skillcompletion.

## STOP currentevaluation — normalhost preservation mismatch

User currentv3normalhostcommand failed --inspect at E_EVAL_ORIGINAL_EVIDENCE_CHANGED,
beforeclaim/--run. Do notrerun/rebaseline/ignore paths. Agent current4project+
454N1/N2files allmatch, noaccess/reparseerrors. Cause remainsUNCONFIRMED; current
agentread doesnotprove pastnormalhoststate. N3-A stillobserved, B/C29stillunrun.

Only additivepreservation-diagnostics-20261019 helper/tests/receipts built.
Firstimplementation8passes/1failure dueWindowscachedDirEntryinode0 vsPath.stat
realID, verifiedsamebytes/times. FixedconsistentPath.stat before/after; all9now
pass. Initialsource519a3928 retained byteexact, corrected40662777; this is a
diagnosticfix, notoriginalhostcause. Agentreceiptbb9cd402 says0differences and
0errors with explicitNOT_CROSS_CONTEXT_PROOF. Originalv3source/contracts/Prepared
unchanged, hostclaim/rankedreceipt absent. Freshread-onlydiagnosticreview pending.
Next one normalhost --host diagnostic only afterreview; it writes onlynewreceipt,
neverlaunchesworker/eval/installs/Git and grants noretryauthority. Do notrunN3eval.

LatestdiagnosticreviewFIX-FIRST required safetraversal/externalhashgate and
minortruthfulstatusfixes; accepted in newv2, oldsource/evidence intact. New
Diagnose-N3-Preservation-v2.py SHA7399be39, Run-N3-Preservation-Diagnostic.ps1
SHAd9c26b8d.11controls(includingactualnewprivatejunction) and4actualexternal
gatecontrols pass. V2agentreceipt26712976:0diff/errors, nothost/paststateproof.
Finalread-onlyreview pending. Onlyhashedlauncher may be handedoff, notoldhelper.
No normalhostdiagnostic/evaluationretry occurred. OriginalcauseUNCONFIRMED.

## Current nextaction — ONE read-only host diagnostic, not an N3 retry

V2diagnostic7399be39 and externalhashlauncherd9c26b8d passed finalnativecode
review SHIP_FOR_HOST_DIAGNOSTIC_ONLY; parent11controls+4gatechecks pass fresh.
Existingsource519a/4066/allolddata preserved. Agent26712976receipt0diff/errors
over458fixedfiles, originalnormalhostcause stillUNCONFIRMED. Currentdiagnostic
hostfolder/evalclaim/receipt absent. Use only reviewedlauncherhash/command in
report, notoldhelpers orN3evaluator. It hashesdiagnostic/eval/Prepared/Before,
records observation-v2-host/Receipt.json, launches no eval/worker/API/native/
installer/Git. Anyresult keeps retryfalse; redmismatch/erroroutput is expected
failcloseddiagnosis. Shareconsole/receipt once; do not rerun/delete/changepolicy.
Afterreceiptcompareexactpaths/bytes/context then choose reviewedrepair. No
baseline rewrite/retry/qualification is authorized justby observation.

## Current checkpoint - local commit authorized; ACL partial4/57, 2026-10-19

AUTH: "COMMIT EVERYTHING" and "Grant normal-account read access to the 19
folders/38 files; keep all checks (Recommended)". No deletion/push/N3 retry.
Host diagnostic b7b0b4e is now observed:19AccessDenied errors,38unobservedpaths,
project4/N2-82match. Agent verifies38files exist/hash-match; protected owner-only
temp ACLs explain current cross-account visibility, not exclusive past causation.

Three ACL write cycles stopped: Set-Acl requested SeSecurityPrivilege (0effects);
Access-only changed first folder then exact-text guard stopped on Windows AI
normalization (1grant); semantic successor added3grants then a raw pre-write child
guard stopped after its own parent normalization (4total). Latest outcome is
After-Normalized.json SHAffc984df4a75234c1d12b5872b9a75ad73fc1274b7958135cad58da7e0a341c0.
Current Checkpoint-Partial-20261019.json SHA4febc0bfd6978abcaf7ee4cd10cb5f3869b5ff9eab85128f84afe299a84aea6f
verifies4/57granted,53pending, all38hashes/oldpermissions/owners/protection intact.
No fourth write attempted. Normal-host readability has not been observed.

Do not rerun any old diagnostic/setup/evaluation/grant command or delete claims.
No code has been hidden, commented out or made unreadable; no preservation path
is ignored.17semantic validator controls passed in prior turn, not whole-skill
tests; failed predecessors remain. Final N3-B/C/29runtime/N3-D remain unrun.

Next discuss/review a files-first successor (36files then17directories) with
parent-induced metadata controls; this is proposed, not implemented/approved
as a fourth attempt. Existing4grants are skipped, all original baselines retained.
Local checkpoint contains only the four pending Fable records. Private receipts,
helpers and installed runtime remain outside Git. Commit changesHEAD, so original
N3's0584a89 basis guard must still refuse; a reviewed exact-commit continuation
plus separate retry approval is needed. No push, release/package/install change.
