# Offline-first Memory Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> inline, as requested by the user. Steps use checkbox syntax. This plan is
> Local Tasks1-5 are now authorized by the user's review/continue instruction;
> Task6 and the named consequential actions remain separate approval gates.

**Goal:** Deliver the existing memory/retrieval core as a matching, verified
offline-first pair, then separately approve and observe installation.

**Architecture:** Reuse the current public workflow, integrity and companion
engines and pinned numerical worker. Repair lifecycle defects at their owning
boundary, enforce an active restrictive release profile, and create successor
artifacts without rewriting historical releases. Existing docs/fable remains
the sole governing ledger; no second Superpowers authority/workspace is created.

**Tech Stack:** Existing Python stdlib core and SQLite ledger; existing optional
Python 3.12/3.13 numerical environment; existing pinned Semantica dependencies.

**Spec:** [offline-first-release-design-20261020.md](offline-first-release-design-20261020.md)

## Global Constraints

- Basis c398be73e9e5eaa14de9e870c7787f53605afd6f; branch
  development/r5-practical-fence-wip-20261014; inspect dirty/concurrent work first.
- Preserve all existing source, important detail, historical SKILL prefix bytes,
  release ZIPs/manifests, failed receipts, experiments and consumed N3 markers.
- No deletion, new dependency/runtime install, model/API call, native database
  operation, permission/trust/global-config change or installed-copy replacement.
- Existing development checkout may be reused only after isolation/ownership
  check. No automatic worktree creation, setup/install or gitignore commit.
- User review gates override implementation-skill automatic execution. Separate
  approval gates override skill default commits and cleanup instructions.
- New profile is offline-first-v1; matching engine version 2.0.0-m13. Existing
  dependency pins and historical granular qualification facts stay unchanged.
- Intended runtime matrix Windows/Linux 3.12/3.13; core matrix 3.11-3.14.
- All JSON/text contracts are explicit UTF-8. Never hide failures with skips,
  errors=ignore, replaced evidence, changed oracle or broadened trust.
- New local test outputs are retained. A retention wrapper is reported as such,
  not unchanged CI; exact clean CI is a later separately authorized gate.
- No local deletion includes new ephemeral files/finalizers. Retain verifier
  extraction, use nondeleting handle-access probes, and report unavailable checks.
  Clean hosted ephemeral cleanup requires explicit later authorization.
- Both single and opt-in distributed-local lexical/LSA execution are included;
  their existing runtime regressions are hard gates. No silent mode reduction.
- No auto-commit/push. No unlimited memory, semantic truth, LSA superiority,
  arbitrary-project coding improvement or whole-skill qualification claims.

## Review Focus

1. Partial worker construction/timeout or a sibling-held handle cannot strand a
   process, hide the original failure or require deleting preserved evidence.
2. Direct supported native APIs and low-level pilots cannot bypass the active
   profile or consume approval before refusal; diagnostics do not grant authority.
3. A package with a missing/tampered active manifest or companion must refuse,
   not silently fall back to an old manifest or import development resources.
4. A large UTF-8 line and dependency edit must not truncate source units or
   invalidate unrelated current work; required evidence beats ranking.
5. Relocation, missing optional runtime, offline context and fresh AI-session
   behavior must be distinguished from private developer-environment success.

## Completion and dependency map

| Work package | Tasks | Exit | Separate authority |
| --- | --- | --- | --- |
| 1: release blockers/use | 1-3 | Profile refusal, lifecycle regressions, portable public workflow | Local build/test approval after design review |
| 2: deliver pair | 4-5 | New manifests/ZIPs, extracted verification, fresh review | Exact commit, push/CI and public upload approved separately |
| 3: installed use | 6 | Target smoke, rollback identity and user-led session | App/paths and replacement approval after package success |

Task 1 profile feeds Task 2/3 supported behavior. Task 2 lifecycle proof feeds
Task 3/5 runtime proof. Task 3's exact receipt schema feeds Task 5 extraction
verification. Task 4 active-manifest selection feeds both current preservation
suites and CI; adding a manifest without updating consumers is NOT completion.
Task 6 consumes only the final reviewed package hashes, never development files.

### Task 1: Enforce the offline-first supported-operation boundary

**Files:** both capabilities-v2.json and scripts/*/__init__.py version owners;
new memory-integrity/scripts/hybrid_bridge/release_profile.py and
claude-mon/scripts/complete_read_v2/release_profile.py; native.py,
native_observation.py, native_pilot.py, shared_native_pilot.py,
practical_backend.py, practical_lease_backend.py, practical_lease_consumer.py,
practical_lease_issuer.py; companion ledger.py native dispatch/acceptance only.
Tests: new test_offline_release_profile.py in each package's tests_v2.
Read all changed definitions before editing; add another owning boundary only
with an explicit scoped ruling, never by changing SQL/fencing semantics.

**Interfaces:** package-local require_native_execution_enabled() -> None,
raising ValueError('E_RELEASE_PROFILE_NATIVE_DISABLED') for the active profile;
load_active_profile() -> validated dict from the owning capabilities-v2.json.
Reject every Beads/Dolt subprocess, including readonly readback, plus new native
authority consumption/acceptance. Disk-only historical records remain readable;
UNKNOWN operations remain frozen. No caller/environment enable override.
Historical booleans stay factual.

- [ ] Inventory actual mutation/reservation/approval/acceptance and pilot entry
  points, distinguishing SQL transport from local SQLite bookkeeping.
- [ ] RED: authored profile tests expect zero native subprocess calls, zero
  reservation/approval consumption, no new native-success event; valid fake
  diagnostic cannot enable work. Include missing/malformed profile and direct
  SharedNativeClaimAdapter.execute and LeaseScratchBackend dispatch attempts.
  Expected: current code reaches the instrumented sentinel or lacks the profile.
- [ ] Add minimal profile checks at the actual mutation and acceptance boundary,
  before side effects. Preserve read-only historical journal/fixture functions.
  Guard whole native pilot start before initialization, not after creating DBs.
- [ ] Reconcile positive legacy native fixtures explicitly against the new
  disabled profile without removing substantive historical protocol assertions,
  adding blanket skips or using a runtime enable bypass solely to green tests.
- [ ] GREEN: from each package run `python -B -m unittest discover -s tests_v2
  -p test_offline_release_profile.py -v` through the reviewed retained-output
  runner. Expected: all declared cases pass, no native binary/provider executed.
- [ ] Broader companion/core fixture checks retain existing failure/skip reasons;
  pending content mismatch is reported, not repaired here. Commit: PENDING
  separate user authorization, not an automatic task step.

### Task 2: Repair owned-worker lifecycle, not just suppress cleanup errors

**Files:** memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py;
new tests_v2/test_knowledge_process_lifecycle.py; existing
test_knowledge_distributed.py and test_knowledge_completion.py.

**Interfaces:** preserve DistributedClient(python, timeout=30).__call__(payload)
and reply bindings. _Session remains internal. Lifecycle owns all sessions,
writer threads, processes and stream handles even on partial construction.
Task 3 receives unchanged successful retrieval schema and truthful refusals.

- [ ] Read retained Windows 3.12 job 118539872559 and its complete first error;
  inspect handle inheritance and finalization. Write the causal hypothesis and
  predicted observation. Do not call the hypothesis a confirmed root cause.
- [ ] RED: tests for two-session shutdown before resource release, partial
  creation failure, pipe-write timeout and exception in one finalizer. Assert
  every owned worker is reaped and writer activity ended, original error remains
  visible, unrelated processes untouched. Use retained directories and Windows
  handle-access probes, not deletion as a test assertion.
- [ ] Implement the smallest demonstrated lifecycle repair. Do not add a new
  worker framework, ignore_errors, blind retries, larger limits or test skips.
- [ ] GREEN: `python -B -m unittest discover -s tests_v2 -p
  test_knowledge_process_lifecycle.py -v`; then existing distributed/killed-owner
  and advanced public replay cases with the exact selected existing worker.
  Expected: lifecycle controls plus real success/refusal cases pass and no live
  owned child remains. Record every original/final output and source identity.
- [ ] Agent inability to launch WindowsApps Python means HOST_REQUIRED, not a
  substituted interpreter or new installation. Any host helper is a new reviewed
  continuation, not a consumed N3 command. If the mechanism fails three changed
  attempts, stop for an explicitly approved supported-mode reduction.

### Task 3: Portable representative coding/source acceptance

**Files:** new .github/scripts/offline_release_acceptance.py,
.github/tests/test_offline_release_acceptance.py and
.github/fixtures/offline-first/ authored fixtures/oracle. Existing public
memory_integrity_workflow.py and knowledge_bridge workflow/index/retrieval code
change only if a new non-vacuous test proves a release requirement gap.

**Interfaces:** script CLI --package-root PATH --claude-mon-root PATH
[--worker-python ABS_PATH] --output-dir UNUSED_PATH. No installation/retry.
Output Receipt.json schema_version=1, with source/package/runtime hashes,
commands and raw stream hashes, checks, discovery_metrics, required_delivery,
preservation, tests, limitations, and status PASS/PARTIAL/BLOCKED/REFUTED.
The script returns 0 only if all selected required checks ran and passed.
No worker means a named no-worker scope, never ranked-runtime qualification.

- [ ] RED: receipt/oracle tests reject empty measurements, omitted required
  source, false coverage/readiness, altered stream binding and a failed child
  hidden by JSON parsing. Refuse an existing/redirected output directory before
  writes. Expected: new implementation absent; then meaningful malformed inputs
  fail at their intended assertion, not an unrelated import.
- [ ] Create the eight-file authored dependency/distractor/Unicode fixture and
  deterministic 256 KiB source; freeze expected sources/units before retrieval.
  Keep discovery metrics separate from mandatory-source delivery.
- [ ] Implement the stdlib harness using actual public offline-run/verify,
  knowledge-project/retrieve and knowledge-test routes. Do not invent an
  offline-verify command or use an internal call as public-workflow proof.
- [ ] Execute save -> exit -> fresh recall -> unchanged resume. In new retained
  copies, edit a dependency, revoke access, reduce budget and fabricate a
  rehashed pack. Require correct refusals and unaffected-source preservation.
  Source-accounting assertion is exact reconstructed UTF-8 bytes/IDs/order.
- [ ] Run the independently authored local unittest, retaining code/test hashes,
  pass/fail/error/skip outcomes. This is a mechanical coding-task fixture, not
  proof that an AI wrote correct code or understood all units.
- [ ] GREEN: repository unit tests for the harness; invoke the script with the
  selected existing runtime and new retained output path. Expected: every frozen
  mandatory obligation reopened or correctly refused, all safety cases pass,
  all authored coding tests pass; discovery misses are reported, never hidden.
- [ ] Record observed time/bytes/limits without extrapolation to arbitrary large
  projects. Carry N3's original 6/7 discovery result unchanged as history.

### Task 4: Successor manifests and paired build contracts

**Files:** new release/Build-Offline-First.py, release/Verify-Offline-First.py,
.github/tests/test_offline_release_contract.py; both package test_preservation.py
and new tests_v2/OFFLINE1-CONTENT.json; current .github/workflows/ci.yml and
knowledge-runtime.yml. Append both SKILL.md instructions and relevant existing
knowledge-operations documentation; do not replace baseline instructions.
Artifacts: new *-offline-v1.zip and Offline-First-Release-Manifest.json only.

**Interfaces:** `Build-Offline-First.py --output-dir UNUSED_PATH`; verifier
`--release-dir PATH --output-dir UNUSED_PATH [--worker-python ABS_PATH]`.
Build returns inventory/hash data, not readiness. Verifier returns nonzero on
any wrong hash/member/contract/test/required-runtime or preserved-file mismatch.
Its report separates core source, extracted packages, runtime and installed use.

- [ ] RED: contract tests require OFFLINE1 active selection, no fallback when
  active metadata is corrupt/missing, historical manifests included unchanged,
  active manifest alone excluded from self-hash. Tampered archive/wrong companion
  and an existing output path must be rejected. No overwrite allowed.
- [ ] Implement successor selection in both preservation consumers and current
  CI. Preserve R3/R4/knowledge-v2 archives, builders and manifests byte-for-byte.
  Reuse safe-member validation with stricter traversal/symlink checks if needed.
- [ ] Finalize instructions/profile/version and companion contract together.
  Keep schema digest if schema is unchanged; otherwise update all paired digest
  consumers and test wrong-companion refusal. Do not bump a lock to hide drift.
- [ ] Build OFFLINE1 content lists from final intended source, including declared
  original-file additions/changes. Verify current list and historic SKILL prefix
  bytes before producing deterministic new archives and new release manifest.
- [ ] GREEN: `python -B -m unittest discover -s .github/tests -p
  test_offline_release_contract.py -v`; builder refuses unsafe/overwrite cases,
  produces two safe archives whose exact bytes match the successor manifest.
  Prior artifact inventory unchanged. Package creation is not a release claim.

### Task 5: Clean extraction, full review and exact delivery identity

**Files:** Task 4 verifier plus Fable acceptance/traceability, report/resume/state.
No product correction without a failing test and owning-task ruling.

**Consumes:** Task 3 receipt schema and public harness; Task 4 archive/manifest
identity. **Produces:** final source/extracted suite and preservation reports,
review disposition and exact commit/package attestation after approval.

- [ ] Before final generation, run each source legacy/v2 package suite, repository
  contract suite and eval self-tests under the inspected no-deletion constraints.
  Inventory every discovered test, skip and expected failure. Content manifest
  closure occurs after source is final, not early to camouflage drift.
- [ ] Inspect retained runner ownership/finalizer behavior before execution;
  cleanup is limited to new test-owned temporary files in fresh retained workspaces
  under the user's later explicit amendment; prior data and receipts are protected.
  Extraction uses new
  retained unique directories. Test cleanup-boundary lifetime with nondeleting
  Windows handle probes, and label physical-delete behavior unobserved locally.
- [ ] Extract into new retained directories; run all applicable legacy/v2 suites
  and relocated Task 3 public smoke using only extracted package roots. Verify
  no development-root import, no omitted runtime resource, wrong companion
  refusal and native profile denial. No-runtime tests remain clearly separate.
- [ ] Use superpowers:verification-before-completion and one fresh Fable Sol
  whole-change reviewer with design, plan, actual diff, test outputs, manifests,
  historical inventories and explicit review-focus list. No external provider
  consultation. Reviewer unavailable is UNAVAILABLE, never approval.
- [ ] Re-grade findings by user effect. One parent fix pass for accepted Important/
  Critical issues, each RED -> GREEN plus full relevant suite. Record rulings and
  minors; do not replace a fresh reviewer with author self-review silently.
- [ ] Ask separately before the exact local commit and before push. Then verify
  remote SHA and all required Windows/Linux source/runtime/extracted CI results
  on that final commit. No skip-ci, manual dispatch, merge to main, release tag
  or public upload without its own authority. Old N3 proof is not exact-release CI.
  Before that hosted run, explicitly authorize only its new test-owned ephemeral
  cleanup if existing unmodified suites need it; otherwise report CI BLOCKED.

### Task 6: Separately approved target installation and fresh-session use

**Files:** only the app/paths explicitly approved at this later gate; no target
is selected by this plan. Default recommendation is Codex because this chat is
in Codex; historical OpenCode m11 remains preserved, not silently replaced.

**Consumes:** final reviewed pair/manifest, passing required exact-commit CI.
**Produces:** target inventory, preserved rollback identity, installed smoke and
user-led fresh-session observations, separately labelled from runtime tests.

- [ ] Ask app/location and replacement/selection authority once after packages
  pass. Read the applicable installer skill and inventory existing files.
- [ ] Preserve prior pair and install the exact new matching pair side-by-side
  where supported. No global hooks, environment/model installs or broad ACL change.
- [ ] Run installed save/reopen/retrieve and stale/tamper/budget/profile-negative
  smoke. Hash installed files against the release; prove no development-path use.
- [ ] User-led new AI session loads actual instructions and saved checkpoint,
  reconstructs completed/pending/stale state with source cites. Mechanical
  process success is not automatic AI-session memory or comprehension proof.
- [ ] Demonstrate rollback selection without deleting/overwriting user work.
  Only then label installed behavior observed for the tested workflow.

## Current plan ledger

- Planning baseline: clean c398be7; no implementation/test/runtime was started.
- Existing plan/resume/state hashes before planning documentation:
  05cbcd06537941a8bad7b0fbb6e5604b1d8995ee8a6fcb3beff6be04dd425508;
  8948ea06d0326a99996de8a37ada877e6f94a47af4e9cb536776373d5ab130d2;
  d2f4d84ba5c9e6c9d8dd852e5b88176187b28352168fd287293aad4977933224.
- User requested executing-plans inline; no need to ask the execution method.
- Brainstorming builder check: one fresh read-only fable_sol_reviewer returned
  FIX_FIRST with three important questions: ephemeral cleanup scope, read-only
  native subprocess authority and distributed support. Parent proposed decisions
  are now explicit: no local deletion/retain everything; ALL Beads/Dolt subprocesses
  denied and UNKNOWN frozen; distributed-local included with mandatory regression
  gate. No second independent approval of corrected bytes is claimed.
- Human go-ahead after the full-design presentation: observed. User requested
  Fable Judge/receiving-code-review, "DO THE BEST TO COMPLETE THE SKILL USEFULL
  AND WORKING", and then "CONTINUE FROM WHERE YOU STOPED". Local Tasks1-5
  proceed; installation, dependency changes, commits, pushes, manual CI dispatch
  and release upload remain separate gates.
- No task is marked complete merely because this document names its future test.

### Execution checkpoint (2026-10-20, uncommitted)

- HEAD remains c398be73e9e5eaa14de9e870c7787f53605afd6f. Historical archives,
  content lists, N3 inputs/attempts, Semantica pins and installed skills unchanged.
- The originally proposed sibling output folder was denied by Windows. No ACL
  change/retry was used. New retained output is instead in the existing ignored
  `.github/run-artifacts/offline-first-20261020` inside this checkout. This is
  test evidence only, not another authority store or a portable release.
- Task1: restrictive profile helpers and initial native/companion boundaries
  implemented. Retained RED then focused GREEN: MI9 and CM4 methods. Native
  protocol-fixture compatibility and remaining public acceptance paths are under
  read-only review; Task1 is not complete from those13 methods alone.
- Task2: retained RED reproduced constructor stream leakage and sequential
  cleanup masking the original fit error/abandoning a sibling. Minimal lifecycle
  repair now passes all3 controls. Additional timeout/cleanup regressions and
  actual selected-runtime tests remain; no Windows runtime repair is qualified.
- Read-only twin inventory: `worker_client._process` already uses context-managed
  streams and a finally reaper; benchmarks/test_evidence own temporary folders.
  The constructor leak/two-session disposal order is specific to `_Session` and
  `DistributedClient`. Further shared-worker error handling is not changed
  without a failing regression and explicit owning-task ruling.
- Exact retained evidence and limits: `../evidence/offline-first-20261020/progress.md`.

### Resumed compatibility checkpoint (2026-10-20)

- Cleanup authority amended explicitly by the user: "Allow only new test-owned
  temporary cleanup; preserve all existing and retained evidence". This supersedes
  only the no-ephemeral-cleanup restriction above, not preservation or side-effect
  boundaries. Old data, source, receipts and packages may not be deleted.
- Profile now has MI16 and CM5 unmocked refusal controls. Lifecycle has6 controls,
  including a real writer thread; these are not selected Windows runtime proof.
- Legacy protocol tests are labelled LEGACY_MODEL_ONLY/POLICY_CHECK_TEST-MOCKED.
  Their fake transports exercise preserved protocol logic, never active native
  authority. Active profile negative tests are not patched. No tests are skipped
  or substantive assertions removed merely to accommodate the new profile.
- Public portable core acceptance observed11 checks,8 literal arms plus fresh
  replays,4 authored coding tests. Receipt SHA-256:
  13be156376c33d5ab8949dde9d35572e96a0d79701fa81c9a3ddba636aa8aa29.
  Status PASS_CORE_ONLY_RUNTIME_UNVERIFIED. Literal discovery0/8; mandatory8/8.
- Windows test stall traced to two fixture-only hard-coded sibling scratch paths;
  both now use selected tempfile.gettempdir(). Practical CLI10/10 passes. No ACL
  changes or product safety weakening. Broader test rerun and final package/runtime
  work remain. Historical R4 content lists remain unchanged; their drift is not
  concealed by an early refresh.

### Current gate and preserved scope

- Source-only profile/model/lifecycle corrections have bounded independent SHIP
  review. The host helper received FIX_FIRST findings; all accepted corrections
  now have regressions and bounded SHIP re-review. Neither verdict is final-release
  acceptance. Full dispositions are in offline-first evidence/review-disposition.md.
- Active content selection, preservation consumers and CI are integrated and6
  fixture contracts pass. OFFLINE1 files are deliberately absent until final
  source/runtime gates. Task4 builder/verifier/version/instructions/ZIPs and
  Task5 final clean/extracted/CI review remain open; do not describe them as built.
- Current repository contracts65/65 pass. Broad retained MI684 is partial with
  three Windows host problems/54skips/1expectedfailure and2 explicitly excluded
  preservation methods; CMv2 blocks on absent OFFLINE1. Four legacyMI loopback
  tests are blocked by the wrapper. These facts cannot be replaced by65/65.
- New normal-account host gate frozen under ignored run-artifacts. Prepared
  source/package/runtime/helper inventories are externally hash-bound, with
  optional external governor absence explicitly NOT_EXERCISED. First real
  containment/path failure stops before numerical suites. Existing runtime only,
  no old N3, install, security change, native backend, Git write or prior deletion.
  A source/package/helper edit invalidates this handoff; never change its seal
  merely to force a run. Generate a separate reviewed successor if needed.

### Superseding observation: host-a1 is consumed/partial

Read offline-first-checkpoint-20261020.md first. Normal host passed5suites,
36run35pass1POSIXskip, including real two-worker checks. Preservation then detected
6 added cache DBs under literal %SystemDrive% inside MI; original files unchanged,
CM unchanged. No advanced/completion/24arm acceptance ran. Cache attribution and
minimum env/cwd correction require a controlled scratch regression; no deletion,
old command retry or changed baseline. User approved saving this local WIP commit,
not pushing or another host attempt. Final release/installation remain pending.

### Cache-cause investigation, continued from6361868 (approved local Tasks1-5)

Current request explicitly asks for a controlled scratch regression BEFORE a
production correction. No consumed host/N3 run will be repeated. Six existing
cache files/receipts remain immutable. This is investigation, not qualification.

Plan: (1) revalidate the six-file difference and receipt identities; (2) compare
both actual env/cwd builders, including transitive single/model/parser launches;
(3) create one small retained diagnostic with fixed startup/handshake/shard arms
in separate NEW owned cwd directories; compare filtered3.14 control and selected
3.12 startup in two distinct cwd locations; (4) record exact streams/file hashes
and source preservation after each arm; (5) infer only what reproduced, then
write the regression and minimum owning-boundary correction if justified.

Alternatives: no-build would preserve the known failure but not explain it;
restoring a broad inherited environment could leak credentials or change global
cache destinations and is rejected; the selected approach keeps the existing
filter unchanged and varies only controlled launch context, so all newly created
relative cache output stays in retained scratch. No global variable, ACL, trust,
dependency, cache removal or old baseline change. Do not redirect SystemDrive to
a fabricated drive or mutate system-wide ProgramData as a control.

Done for investigation: independently review the bounded diagnostic; at least
one actually observed source of cache creation OR a truthful non-reproduction/
host-blocked result, with both launch boundaries covered and all previous files
unchanged. Existing-source probe execution is not a repaired-product acceptance
run. A new full successor host evaluation still needs separate authority.

Ruling: reuse the current checkout and docs/fable as sole authority, executing
inline. Do not create a second skill workspace or follow automatic cleanup/commit
defaults; they conflict with the user's explicit preservation/approval rules.

Investigation checkpoint:10 focused/75 repository harness controls pass. Real
scratch echo children confirm inherited cwd/filter on both boundaries, but actual
selected3.12 startup is agent-blocked (exit103); no cache-cause RED observed.
All source/cache/old host evidence preserved. Independent review could not start
(workspace credits), NOT_PASSED. Hold new normal-host diagnostic handoff for fresh
review; no production correction/full-host retry. Resume/evidence (docs/fable-relative):
evidence/offline-first-20261020/cache-cause-investigation.md.

### Approved continuation froma9ae630: finish existing four work groups

User requested "finish this above required, if needed, give file path to run in
power shell" and selected Brainstorming/Writing Plans/Executing Plans. Reuse this
approved design/plan, existing checkout and progress ledger; no second governor,
workspace deletion or ceremonial redesign. Execute inline. No new commit/push,
dependency/permission change or installed-copy replacement is inferred. Task6's
target-app/paths and replacement approval remain explicit later gates.

- [x] A: Fresh bounded read-only review of cache_cause_probe.py + test. Preserve
  review findings; fix Important/Critical harness defects with observed RED/GREEN
  and all repository harness controls. Unavailable review stays NOT_PASSED.
- [ ] B: If cleared, prepare one NEW externally sealed normal-account scratch
  launcher and output root, not old N3/host-a1/agent attempts. Validate helper,
  controller, runtime and package identities before launch. Keep original pins,
  filters, caches, receipts and false qualification flags. Command runs startup
  controls and the existing single/shard startup boundaries; no full retrieval,
  install, learned-model/API/native operation, global configuration or cleanup.
- [ ] C: Inspect the actual scratch receipt. Only observed causal evidence may
  drive the smallest shared env/cwd correction; first add the symptom RED and
  both launch-boundary regressions. Non-reproduction reopens investigation, not
  silent promotion of a hypothesis or a broad environment inheritance change.
- [ ] D: Prepare separate clean-source successor/full-host inputs after correction
  and review; observe advanced/completion/24-arm/preservation gates. Do not weaken
  exclusions, erase discovery misses or recycle consumed seals/markers.
- [ ] E: Finish existing Tasks4–5 on final source bytes: paired m13 instructions/
  capabilities/contract, new OFFLINE1 lists, builder/verifier, ZIPs and full clean
  source/extracted checks/review. Publishing/exact-commit CI needs separate push
  approval. Keep all historical releases/experiments and native profile disabled.
- [ ] F: After package success, separately settle app/installed target and approve
  replacement; observe save/fresh-session reopening/retrieval/stale refusal.

Immediate deliverable for this turn is A/B. B requires the user's normal account
because the agent cannot start the existing WindowsApps base Python. Do not
repeat that same failed agent probe. Continue C–F after the necessary receipts,
not by claiming a multi-stage release from green harness controls.

A completed with FIX_FIRST review and parent RED/GREEN corrections, repository
harness81/81. Choose the reviewer's cache-cause-only identity boundary: exact cfg,
expected prefix and matched in-arm3.12 identities, no exact-base/numerical claim.
B inputs/launcher prepared; agent -File VerifyOnly blocked by script policy, no
bypass. Normal-account block runs VerifyOnly before new scratch, stopping any
error. No normal-attempt directory yet. Exact hashes, limitations and rulings:
evidence/offline-first-20261020/cache-cause-review-correction-20261020.md.

### C: actual normal-account observation; bounded cwd correction

User ran the new sealed scratch diagnostic once, then requested "after complete
check commit it". Its consumed receipt SHAa1a37f4a1128bc2d5be42bd2a11ac758e844e3a4746630e32f2add2e1141f6dc
reports five arms and no failure. Direct parent readback recomputes the status:
RELATIVE_CACHE_WRITE_REPEATED_IN_DISTINCT_STARTUP_CWDS. All319 protected file
hashes and12 named historical artifacts still match. Three generation1 database
contents match original caches; cversions differs; generation2 files did not
reproduce. This does NOT identify the Windows writer or prove SystemDrive omission
causality. Runtime base authentication remains UNVERIFIED_CACHE_CAUSE_ONLY.

INTENT: contain relative startup side effects by explicit, process-owned cwd at
both real launch boundaries. Keep the existing environment whitelist unchanged.
The no-build option retains known package contamination. Broad environment
restoration changes trust/cache destinations and is rejected. Use one new owned
temporary directory in worker_client._process; reuse the existing owned session
directory in distributed_retrieval._Session. Preserve absolute script/executable
selection without resolving a venv symlink. Do not change source selection,
evidence guards, native profile, old manifests/packages or any original cache.

Verification before commit: retain actual command/stream/arm hashes; add real
stdlib subprocess regressions for BOTH boundaries and observe pre-fix RED;
verify relative fixture writes leave caller source unchanged, distinct owned cwd
per launch, unchanged environment restrictions, payload/path continuity and
existing lifecycle/error behavior. These authored controls are NOT numerical
3.12 retrieval proof. Run focused/lifecycle/repository and broad retained suites,
report all remaining failures/skips explicitly, obtain bounded source-diff review,
and verify preservation excluding only declared source edits/new tests. Commit
only completed source/tests/Fable records locally. No push/install or full-host
success is inferred; new selected-runtime acceptance needs its separate reviewed
successor, not a retry of the now-consumed cache/N3/host command.

Required compatibility correction discovered in the recurrence search and
independently confirmed by review: the benchmark is the only _process arguments
caller. Its companion/output CLI values may be relative; resolve those against
the caller before changing child cwd. Manifest is already absolute; preserve the
explicit worker requirement. A real dispatch/companion handshake plus authored
argv/report child must reproduce the regression before this two-path correction.
This runs no learned model and adds no capability or new authority.

C source correction completed through independent bounded SHIP review on2026-10-21.
The final six controls cover cwd isolation, caller-relative path continuity and
cleanup failure precedence; each missing behavior has retained pre-fix RED.
The real3.12 corrected-candidate cleanup and integrated acceptance are NOT done.
B is now consumed/observed, not a runnable instruction. Continue at D after the
local source checkpoint and separate new-host authority. Do not repeat B/N3/a1,
replace old seals or interpret a source-only SHIP as release readiness. Exact
evidence/current broad outcomes: evidence/offline-first-20261020/cache-cwd-correction-20261020.md.
