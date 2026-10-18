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
