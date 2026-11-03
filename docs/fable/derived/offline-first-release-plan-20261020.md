# Offline-first Memory Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> inline, as requested by the user. Steps use checkbox syntax. This plan is
> Local Tasks1-5 are now authorized by the user's review/continue instruction;
> Task6 and the named consequential actions remain separate approval gates.
> Amendment W1..W3 at the end is PROPOSED, not covered by that historical grant;
> obtain full-description approval once before building or running its observer.

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

## Gate1 completion implementation plan —2026-10-21

For agentic workers: use the user-selected superpowers:executing-plans inline,
TDD and one fresh final review. This is a continuation of the approved design,
not a second project, governor or disposable ledger. Spec: the existing
offline-first-release-design-20261020.md plus the user's six-step Gate1 table.
Goal: observe the corrected production implementation with the existing selected
Windows Python3.12 runtime from a separately sealed clean source copy, through
both workers and the public coding workflow, with refusal and preservation proof.

Authority: user requested "complete this gate fully and completely" and supplied
clean-copy/new-command/worker/workflow/refusal/preservation steps. Reuse that named
scope; do not ask the same scope again. No install, credential/security change,
live AI/learned model, Beads/Dolt, old command retry, commit/push or installation.
Old data and evidence remain immutable. Only NEW test-owned temporary cleanup is
allowed by the already approved amendment; retain copies/hashes of observed new
cache files before testing real production cleanup. Never delete a workspace as
a skill default. Existing production code/metadata/manifests stay unchanged.

### Newly verified evidence, not another completed gate

- GitHub development ref now equals923de16c91a9ef4381e7ac975e3a3780f42a4bf5.
  The three-commit push is independently confirmed. Local tree initially clean.
- Available refs/history/current campaign/private validation folders contain
  no completed clean-source Gate1 result for this corrected candidate. Earlier
  N3, host-a1 and cache startup receipts belong to earlier source or narrower
  scope; do not relabel them as this gate or repeat their consumed commands.
- Exact-commit regular CI39544827912 failed in MIv2; runtime CI39544827919 also
  failed. Windows3.12 job119040509462 exposes a NEW fixture bug: test_knowledge_
  worker_cwd.py calls relpath(D: companion,C: temp), raising before dispatch.
  Ubuntu3.12 job119040509922 passed190 knowledge tests with10 explicit skips,
  then failed historical archive/source equality. That is useful independent
  runtime evidence, NOT complete Windows/selected-local-runtime qualification.

### Decisions and additional proof inside the user's six steps

Ruling: preserve the existing architecture, fixing only the demonstrated test
fixture's cross-drive choice. An unrepresentable Windows relative companion path
must remain absolute; the report path stays relative and still exercises actual
dispatch/companion/child behavior. Add a failure-first different-mount regression;
no skip or forged runtime response. Cost if wrong: CI remains red or the relative
path regression loses coverage. Preserve the same-drive test, not just a helper.

Ruling: clean production bytes come from Git923de16. List the ONE test-only
fixture overlay separately with its old/new hashes. Do not call the whole copy
an unchanged923de16 tree. Uncommitted Gate1 drivers are externally hash-bound,
outside the clean tree; source manifests cover every copied file. Cost if wrong:
provenance refuses rather than pretending modified code was the old commit.

Options: reuse old receipts (no-build, insufficient source/scope); selected small
successor reusing existing capture/acceptance/retained runner (adequate); rewrite
the engine/build new runtime (stronger, unnecessary/out of scope). Weak link:
actual normal-account runtime and Windows cleanup. Cheapest falsifier: one real
owned-cwd startup/cleanup of each worker before the larger ladder. Any hash,
identity, containment or preservation failure stops; retain it, do not rebaseline.

Required additions to the six steps: external pre-import seals; exact source and
runtime/config/base-file pins; actual child environment/Git read before claim;
real cleanup observation separate from retention instrumentation; fixed required
test identities and exhaustive outcomes; explicit optional-mode/POSIX skip policy;
all24 literal/lexical/LSA discovery/mandatory arms and fresh replays; relevant
positive controls; refusal cause/no partial acceptance; unchanged resume; preserved
unaffected valid work; independent result review. Coverage is not comprehension,
and completing Gate1 cannot activate release/native/installation flags.

### Bounded tasks and interfaces

- [x] G1-A: repair test-only cross-drive fixture. File: memory-integrity/tests_v2/
  test_knowledge_worker_cwd.py. New different-mount control runs real dispatch and
  harmless authored child with the real companion. Expected RED then7/7 GREEN;
  all original six outcomes retained. Production hashes remain923de16.
- [ ] G1-B: implement .github/scripts/gate1_validation.py and .github/tests/
  test_gate1_validation.py. Consume Git tree, explicit overlay, selected runtime,
  old protection map. Produce a short new source root, full Source-Manifest.json,
  externally sealed Prepared.json and one fixed output path. Test changed/omitted
  inputs, wrong source/paths/runtime, existing/redirected destinations, old data
  protection and refusal BEFORE claim. No runtime start during preparation.
- [ ] G1-C: implement .github/scripts/gate1_runner.py and gate1_worker_checks.py.
  Reuse the clean copy's retained_unittest and generic owned-tree capture, not a
  native backend. Record exact case IDs/outcomes without replacing success/failure
  logic. Separately observe real single/shard cwd/cache bytes, reap and actual
  production cleanup; allow only that invocation's owned new temporary roots.
- [ ] G1-D: freeze and test the coordinator. Mandatory patterns: native_containment,
  native_paths, offline_release_profile (MI/CM), and test_knowledge*.py. Freeze all
  discovered identities, no exclusions/expected-failure acceptance. Permit ONLY
  enumerated optional-model/parser and POSIX-only cases with recorded reasons;
  no in-scope runtime skip. Reuse offline_release_acceptance for24 arms, replay,
  chunk/save/fresh-recall/resume/stale/access/budget/tamper/unaffected-work checks.
  Require real ranked positive controls and report every discovery miss separately
  from mandatory-source delivery. Preserve original and copied source/evidence.
- [x] G1-E: run focused and repository/affected regressions; obtain ONE fresh
  independent review. Correct Important findings with retained RED/GREEN and no
  silent guard reduction. Then freeze a new hash-checked normal-account launcher
  (not N3/a1/cache/push helpers). Existing venv only; no install/substitution.
- [ ] G1-F: execute the one approved successor in normal account when required
  by registered Store runtime; retain all outputs/unknown results, never repeat
  a consumed attempt. Parent verifies raw hashes, exact required outcomes and
  preservation, then reviews observed results. Gate remains PARTIAL until real
  outputs satisfy every requirement. Do not call prepared code a passed gate.

Working copy/outputs: one new short root under Documents/Codex, named
gate1-923de16-20261021 (or a newly chosen unique suffix if already present), with
source and results siblings. Original records remain in existing docs/fable;
private receipts/handoff remain ignored. No deletion or copying old caches into
the clean source. Separate final-package/CI/publish/install gates remain pending.

### Gate1 execution checkpoint after resumed review

G1-B/C/D code and fixed contracts are implemented with23 focused/104 policy
controls passing; their actual preparation/runtime outputs belong to G1-F and
remain unrun. G1-E completed through the SAME reviewer: first FIX_FIRST7,
retained RED/GREEN corrections, resumed bounded code SHIP, final handoff SHIP.
No selected3.12 validation or release result is inferred from those verdicts.

The final handoff pins the ONE fixed short root gate1-923de16-20261021. The
earlier generic suffix option is NOT authorization to choose another root after
failure; the sealed final command refuses any existing root. Parent independently
precomputed exact Prepared bytes; bootstrap must be externally hash-checked,
then checks old evidence/root absence before preparation, requires expected
Prepared match and postcopy verification before runtime. This reviewed normal-
account flow is within existing Gate1 approval, not an old-command retry.
G1-F remains OPEN until actual217 outcomes/24 arms/cleanup/preservation and
parent raw-result review. No new commit/push/install or qualification activation.

### Proposed image-identity successor after the one host stop — not implemented

Actual probe exposed the base-file/loaded-image filename conflation. See
gate1-runtime-image-diagnosis-20261021.md for raw hashes, isolated reproduction,
unknown original PATH expectation, options and acceptance criteria. Preserve the
existing sealed v1 helpers/Prepared/normal-attempt and all clean source bytes.
Recommended next diff pins exact observed loaded image as a SEPARATE role while
keeping original base/cfg/alias/venv pins; observed-frame failing test and negative
path/hash/redirect/context cases; named mismatch fields; focused/broader guards
and bounded review; independently sealed successor. No accept-any-hash fallback.
The verified567-file clean copy may be reused READ-ONLY with strict whole-source
verification; no need to rebuild already completed source recovery/preparation.
No implementation or new normal-account run is authorized by this plan record.
Seek authority for the bounded successor and ONE fresh normal attempt. Actual
cleanup/217 outcomes/24 arms/full preservation/result review still close G1-F.

### Approved image/context successor execution —2026-10-21

AUTH: user said "check if this is correct and best to run and complete the gate 1
completely and excute it" after the full bounded correction description. Covers
local correction, tests, review and ONE fresh successor run; not installs, Git
writes, native backends, deletion or release/installed qualification. No duplicate
approval required. Existing v1 helpers/seals/failed attempt remain immutable.

New primary observation: dict(os.environ) has SYSTEMDRIVE but no SystemDrive;
os.environ.get('SystemDrive') returns C: while plain dict.get returns None. The
old mixed-case environment comparison is a second reproducible harness defect.
Fix within same identity/context boundary: Windows case-insensitive lookup with
ambiguous duplicate keys REFUSED, not ignored. Retain exact safe expected fields
and PATH digest before the child runs; report named mismatches.

Selected smallest adequate design: ONE .github/scripts/gate1_image_successor.py
reuses sealed v1 validation/capture/runner/acceptance APIs, with explicit successor
output and exact loaded-image contract. It does not patch v1 globals or redirect
its existing output guard. Reuse verified567-file source READ-ONLY. Contract seals
parent Prepared, failed receipt, whole failed-attempt inventory, runtime image,
new helper and fixed output path. All old protection/history checks stay required.
No-build stays blocked; broad same-hash/path-pattern acceptance is rejected.

Tests first in .github/tests/test_gate1_image_successor.py: independently authored
Store frame, upper/mixed Windows key casing, ambiguous keys, every wrong identity/
context field, unknown schema, source/old-receipt/helper drift and existing output
refusal before runtime. Existing217 cases/24 arms/real cleanup remain mandatory.
Parent retains RED/GREEN and broader policy results; one same-seat read-only final
review checks new diff/handoff. New externally hash-checked launcher only after
review; normal SID/non-admin before any attempt. If agent account cannot launch
selected Store runtime, stop and provide normal-host command under this approval.
Stop at any failure; preserve everything. No old command, automatic runtime retry,
ACL/trust/admin workaround, baseline replacement, dependency/model/native call.

Successor execution checkpoint: two confirmed image/env faults corrected, reviewer
two Important findings closed with16-case RED/GREEN, finalpolicy120/120 and same-
seat core/final-handoff SHIP. Input-only new contract/launcher frozen; outer SHA
required before VerifyOnly and one normal invocation. Agent VerifyOnly correctly
refused before Python/output. Existing authorization covers actual normal run;
do not ask again. Current fixed output absent; G1-F is STILL OPEN until actual
cleanup/217 outcomes/24 arms/preservation and parent result review. No historical
SHIP or synthetic guard result substitutes for those missing observations.

### Actual host stop: focused cleanup diagnosis proposed, not another full run

Actual identity and standalone cleanup now observed passed. Main image-successor
attempt CLOSED:212cases completed198pass1fail13declaredskip. One required public
vector/distributed-local subcase failed in cleanup; CM5/24arms remain. See
gate1-public-cleanup-failure-20261021.md for verified receipts and the lost-error
boundary. Preserve all results; do not restart source prep/identity/suites.
Next proposed bounded diagnostic retains exception chain/notes/resource/owned
process/writer state for that single path, without retry/delay/success suppression
or old-source mutation. Fresh diagnostic normal-runtime authority still needed.
After the original cause is observed, propose minimum repair+regression+review,
then requalify affected/integrated corrected bytes and remaining Gate1 work.
Prior198 passes remain useful evidence, not automatic qualification of a future
modified candidate. No distributed-mode scope exclusion without explicit choice.

### Approved focused public cleanup diagnostic —2026-10-21

AUTH: user said "check if this is correct and best to run and complete the gate
1(suite1,2,3,4) completely and excute it" using Fable Judge. This approves the
bounded local continuation and ONE new focused normal-account diagnostic. It
does not authorize replay of the closed image attempt, install/security changes,
Git writes or automatic qualification. Existing source and all evidence remain.

Judge first: independently recheck saved receipt/case identities and error
serialization boundary; real selected-runtime reproduction is a later explicit
observation, not a claim obtained by reading logs. Numbering clarification: the
frozen source has FIVE groups, zero-based0..4 (MI containment3, paths2, profile16,
knowledge191, CM profile5),217 total, followed by24 acceptance arms. None is
dropped because the user named suites1..4. All remain required for Gate1.

INTENT: current public failure preserves BLOCKED but discards the underlying
exception. A NEW diagnostic-only source copy retains that exception while keeping
original cleanup behavior, exit2 and refusal semantics. No product repair is
selected until evidence supports it. Diagnostic outcomes cannot close Gate1.

Options: no-build retains safe BLOCKED but cannot identify the cause; recommended
smallest build copies the567 sealed files into ONE new owned output and overlays
ONLY worker.py's failure formatting (bounded traceback/causes/notes/OS fields).
A tracing/handle-monitoring hybrid adds timing effects and broadens surface, so
is held unless this minimal observation cannot identify a useful cause. No new
libraries, process termination policy, retry, sleep, skip or output suppression.
Weak link: the original failure may not reproduce. Cheapest falsifier is ONE
same-fixture public vector/distributed command; no reproduction means INCONCLUSIVE,
never fixed. Capture truncation or incomplete process containment also stops.

Milestones inside this continuation:
1. Fresh same-seat read-only judge of the diagnosis/design. Record corrections.
2. Failure-first tests of actual diagnostic worker.main exception roundtrip,
   bounded messages, causal chains and existing success/refusal behavior. Build
   .github/scripts/gate1_cleanup_diagnostic.py and its .github/tests test only;
   existing helpers/product/tests remain sealed. Retain RED/GREEN and policy run.
3. Bind exact parent Prepared/image contract/failed receipt and retained logs,
   new helper/overlay bytes/runtime and fixed new output. Preflight checks whole
   original source/protected/history and paths before creating an output. Same
   user SID/non-admin/external launcher SHA, real Git and selected-runtime probe
   before public execution. Review the helper AND final private handoff.
4. ONE actual normal-user focused diagnostic, existing runtimes only. Retain the
   new copy, authored coding fixture, stdout/stderr/exit/containment and receipt.
   Check exit and capture before JSON. No full217/24 ladder in this diagnostic.
5. Parent reviews the actual result/preservation. If a real cause is observed,
   specify the smallest repair and regression before editing. Then separately
   prepare corrected-source full Gate1 validation. If runtime/access is unavailable
   here, issue only the reviewed externally sealed normal-account command under
   this approval; no interpreter substitution or security bypass.

Done for this bounded diagnostic: meaningful RED/GREEN, clean policy regression,
cleared review, sealed handoff and either actual retained causal observation or
an explicit UNVERIFIED/INCONCLUSIVE runtime boundary. Done for Gate1 is unchanged:
all217 frozen cases under declared skip policy,24 arms, required positive/safety/
fresh replay checks and source/history preservation, plus actual result review.
Rollback is keeping the old source and attempts; no old file is removed/moved.

Judge disposition before build: four Important guardrails accepted. Diagnostic
details travel inside the legacy error STRING through unchanged WorkerClient and
public blocker, with an actual chained-child roundtrip regression. Serialization
has explicit text/depth/frame/note/byte limits and no locals/environment/payload;
any relevant truncation is INCONCLUSIVE. Child exit2/capture is retained before
JSON parsing. Separate cause-observed/not-reproduced/missing-detail/harness-failed
states ALL keep Gate1/fix/release/producer-authentication flags false.

Preservation refinement cleared by the same reviewer (architecture only): the
new external contract pins known prior receipts/streams/cases/log identities;
normal-user preflight additionally inventories the COMPLETE old image-attempt
tree before ANY new output/source creation, fail-closed on every unreadable or
redirected/linked/unstable path. Retain that exact start map in the disjoint new
output and compare immediately, after each capture and finally. No old baseline
is replaced. This proves files/bytes unchanged THROUGH THE NEW DIAGNOSTIC, not
historical producer authentication or empty-directory/metadata identity. Parent
agent cannot inventory all normal-user temp folders; no ACL workaround. The
normal host must stop if it too cannot make the complete observation.

### Diagnostic review corrections inside the approved continuation

The first finished-code review returned FIX_FIRST, not handoff clearance. Keep
that reviewed helper as a hashed private archive; preserve all prior results.
Before any host command, add failing controls and correct four Important areas:
exact Windows fixture bytes/staging and the original public timeout90; strict
public result/exit/authority-field classification; repeated helper-byte checks;
and truthful prepare-only no-repeat/saved-input drift checks. No cleanup policy,
timeout of the authoritative public test, success path or product bytes change.

The controller-only preparation must run all existing validators and full prior
attempt inventory before writing its TWO new private input/observation files.
It must refuse any existing diagnostic output, contract or preparation receipt,
validate its generated contract, and recheck saved bytes and absence of output
before success. Agent AccessDenied on an old normal-user cache observation is
not an authorization to skip it or change ACLs. A reviewed, sealed normal-user
prepare-only command may cross that observation boundary without starting3.12,
copying source or consuming the one approved diagnostic. Parent then verifies
the returned input/receipt hashes before separately freezing the Run launcher.

Current bounded code/correction and input-only handoff review: SHIP after the
four findings and additional mapping/staged-fixture finding were closed with
regressions. Focused36/36, policy156/156; exact hashes/retained failures in the
diagnostic report. Parent hash-checked agent VerifyOnly confirms normalSID
refusal before any Python/input/output. Normal preparation command may now be
issued with external launcher SHA3a58a5a417c6f3245bcef7c534a4a594a110740aab6a32d96a784361744cce9a.
This closes code/test/prepare-only review work, NOT normal preparation, runtime
diagnosis, cause, repair,217/24 qualification, package/release or installation.

### Normal preparation observed; freeze the separate diagnostic handoff

The user returned INPUT_ONLY_CONTRACT_PREPARED_DIAGNOSTIC_UNRUN. Parent directly
verified the86988-byte contract4a773e562a0b0bf0af7cea57899696febd089471750d6a7707471a2287df2924
and824-byte preparation receipt1f27b3f94bc592d8a92acd690e45520fafdd5e6f21fe5f6592aeeab0f1284526.
The exact current validator confirms567 source entries with ONLY worker.py error
formatting different,40 prior bound records, original parent authority, staged
fixture/timeout90, fixed new output and all qualification flags false. Normal
preparation reports1370 files and mapb94c45316daf100fe2c11d3d8c54ec2a2b24048bcc412df36baa085df09cda29;
do not confuse a reported digest with independently recomputing the whole map.

INTENT: finish the already-approved stage3 by freezing the separate Run launcher
against this exact helper, contract AND preparation receipt, retaining its old
unfrozen draft. No helper/product/test behavior change. Parse/check pins, request
same-seat final handoff review, verify the normal-account refusal from the agent,
and issue only the reviewed external-hash/VerifyOnly/ONE-run outer block. Do NOT
rerun preparation or old attempts. All original full normal-host preservation
checks remain required before new diagnostic creation. Gate1 remains open.

Stage3 final private handoff review now SHIP: exactRun4600bytes SHA
d34bdb9df59e7b93be1b3110aa48b481e4a4e3ed9ac65dc85e99d6777e9e9d96, all10pins and
40knownrecords independently rehashed, AST0. Parent external-hash agent VerifyOnly
refused before Python/source/attempt. ONE reviewed normal outer Run block issued;
stage4 actual observation and stage5 raw result review remain unrun. This does
not waive the complete normal-user history/inventory gates or close Gate1.

### Focused diagnostic observed and closed — ordered-context successor PROPOSED

The one approved focused normal run completed FAILURE_NOT_REPRODUCED_INCONCLUSIVE
(receiptfb8d02cc60782b7e3154c151e317caccc9e34ee198c4f69e50854e7fa2132433). Parent
readback and same-seat actual-result review confirm a valid isolated public
vector/distributed success, not a repair. Current one-shot authority CONSUMED.
No old command may be repeated. Underlying original cleanup cause still UNKNOWN.

TARGET: obtain the missing causal observation using the actual ordered public
test, not another independent vector-only probe. Consumer is Gate1's unresolved
required public advanced/replay case. Product repair and qualification are NOT
part of this proposal. All old sources, caches, receipts, packages remain intact.

Facts/observations: old full test fails fourth public command after three prior
modes/replays; focused fresh-index vector command succeeds; working/temp prefix
also changed. Original test and both retained results are primary evidence.
Assumptions: order/shared state or path context MAY matter; neither is proven.
Unknown: original OS exception, whether actual ordered method reproduces it,
and any direct shard-lifecycle cause. Only observed rich error can justify repair.

Options considered using Deep Plan within Fable (no second governor/plan store):

| Option | Mechanism and main limitation | Disposition |
| --- | --- | --- |
| No build | Preserve both results and leave Gate1 unqualified; no causal information gained | Safe default if further experiment is not approved |
| Exact ordered-method diagnostic | Execute only unchanged authoritative method, matching order/shared fixture/replay/lease checks and comparable temp layout; may still not reproduce | Recommended smallest next measurement |
| Heavy OS handle/process tracing | More runtime/handle observation, added tools/surface and timing effects; a different mechanism with broader approval | Defer unless ordered reproduction yields inadequate detail |

Constraint lens: no production/cleanup/retry change, existing runtimes only, no
old-data deletion/security workarounds. Cost lens: one method avoids repeating
already observed21case prefix/full191/217/24; direct vector-only repeat loses
the known order/context difference. Falsification lens: even exact method can
pass; that must stay inconclusive, not evidence for a guessed repair. Evidence
families: retained runtime observations (two different contexts) plus actual
test/helper implementation; parent and reviewer readings share those sources,
not extra independent runtime measurements. Confidence: Medium for selecting a
more faithful measurement, Low for any proposed cleanup cause (none selected).
Weak link: a faithful sequence/layout may not reproduce the former effect.
Cheapest test: ONE exact ordered method in a new retained diagnostic context.
Pivot: pass remains INCONCLUSIVE and stops; do not automatically add iterations.
If error details are incomplete, retain result and seek a separately bounded
instrumentation amendment; do not invent a cause or disable a required mode.

PROPOSED bounded successor, needs separate explicit approval before building:

1. Freeze the exact existing RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay
   identity and source, original community -> global -> drift -> vector ordering,
   shared fixture/index, positive fresh replays and rehashed stale-lease refusals.
   No rewriting the test or substituting fabricated receipts.
2. Prepare ONE new exclusively owned diagnostic copy with only the SAME reviewed
   worker-error formatter overlay. Use controller/selected-worker identities and
   default worker timeout unchanged; public subprocess timeout remains90seconds.
   Match relative CWD/TEMP layout plus same depth/equal-length base prefix of the
   original failed image context, and retain explicit path-length/context checks.
3. Add failure-first harness/selection/seal/staging/false-result controls and
   independently review the new helper, contract and final normal-user launcher.
   Use existing scoped test-owned temp cleanup; retain every negative result.
4. ONE new normal1001/nonadmin execution of ONLY that method. Original subtest
   aggregation remains intact, no retries or full-suite prefix/ladder. Retain
   command/error/case/pack evidence and whole old-source/history preservation
   start maps, checks after each stage/final. Preflight/read/link/seal/containment
   errors stop; no guard bypass, permission/global change or interpreter fallback.
5. Parent actual-result review preserves four result classes: complete captured
   cause pending review; nonreproduction inconclusive; missing/truncated detail
   inconclusive; harness/preservation/capture failure. All fix/Gate1/native/
   release/install/producer-authentication/retry flags false. No automatic repair.

Approval would include only that successor build/review plus one new disposable
normal-account ordered test. It would NOT include toolchain/dependency install,
download, model/API/native backend, security/ACL/trust/global change, shared-data
migration, deletion of old files, package generation, commit/push or installation.
Rollback is keeping old files and holding all qualification flags false. No new
ordered helper/launcher/runtime execution exists yet. Pending approval only;
do not reuse the consumed public-cleanup-diagnostic-20261021 output or markers.

### Ordered successor AUTHORIZED — inline execution brief and checklist

AUTH: user invoked Fable Method and Executing Plans and said "check if this is
correct and best to run and complete the gate 1(suite1,2,3,4) completely and
excute it". This approves the immediately proposed ordered successor build,
tests/review and ONE fresh normal-account method run. Existing Gate1 still has
FIVE groups0..4/217cases and24arms; naming suites1..4 does not waive the fifth.
No repair, qualification, install/security/Git/deletion expansion is inferred.

INTENT: the consumed focused run omitted original ordering/replays and did not
reproduce cleanup; execute the unchanged authoritative method with observations
and matching path context, not new cleanup logic or fabricated pass evidence.

Declared authored surfaces: .github/scripts/gate1_ordered_diagnostic.py,
.github/scripts/gate1_ordered_runner.py, focused .github/tests files, private
run-artifacts contract/launcher/logs, and these existing Fable records. Actual
new runtime roots must be exclusive and disjoint; original product, frozen
helpers, tests, source copies, receipts and caches remain read-only.

Inline checklist (record results here/progress, not in a competing plan store):
- [x] O1: meaningful RED then GREEN for exact test selection/observations; actual
  authoritative test bytes pinned; zero other cases run. Source-only observer
  calls originals exactly once, returns/raises unchanged; no worker substitution.
- [x] O2: separately sealed driver; all original/full old-history guards plus
  current consumed-result/baseline checks before ANY source/runtime output;
  recurring helper/runner/source/contract preservation, one-shot accounting.
- [x] O3: retained focused and full repository-policy controls, no hidden
  exclusions; one fresh-context final review of the complete authored slice and
  exact handoff, then one fix pass with RED/GREEN if needed.
- [ ] O4: ONE normal-account original ordered method run; actual result review.
  If this agent cannot access selected runtime/history, provide reviewed sealed
  PowerShell command, do not substitute interpreter or security context.

Ruling: keep existing development checkout/dirty baseline and use exclusive new
runtime copies for isolation; do not create/reset a Git worktree or lose any
uncommitted work. Source root alias ordsrc has the same length/depth as original
source; order-successor-20261021 has the same length/depth as image-successor-20261021.
Verify those relationships, do not merely assume them.

Ruling: Fable stays sole governor and existing progress.md is the inline ledger.
Do not run duplicate .superpowers workspace/commit/deletion automation: user
requires all old data/evidence preserved and separate authority for Git/install.
Executing Plans supplies inline implementation/TDD/one final review, not broader
authority. Retain new evidence instead of its default workspace deletion.

Ruling: a deterministic parent-sealed contract may be computed from already
readable sealed authority/result records without claiming full old-tree access.
This does not call a skipped/monkeypatched old build/preflight. BOTH original
complete normal history and full prior inventories remain mandatory in actual
execution before output/source creation; any unreadable/changed path stops.
This avoids an unnecessary new normal-account prepare-only round trip.

Ruling: run exact original method with retained unittest wrapper and observation
hooks for public subprocess results and positive/negative verifier calls. Hooks
must call originals once and preserve results/exceptions/timeouts; no test or
worker implementation is replaced. Logging has timing cost, so a pass still
remains inconclusive and cannot establish original lifecycle equivalence.

Proof obligations: exact one-case selection, four ordered subtests, public
timeout90, shared fixture/index, four fresh replays and four rehashed lease
refusals for a passing method, no partial/malformed result promoted, preserved
old trees/contract/helpers/567copy, retained cause or honest inconclusive state.
Baseline HEAD923de16, existing dirty scope retained; prior156policy/36focused and
closed actual diagnosticfb8d02cc... are evidence, not newly executed proof here.

O1..O3 closure: see gate1-ordered-final-review-20261021.md. Single final review
FIX-FIRST (one Important global-phase interleaving); parent ONE RED/GREEN fix
pass, focused19/19 and fullpolicy175/175 green,0skips/exclusions. V1 drafts/code
retained; exact V2 static seals/pins and agent refusal verified. O4 remains open:
normal1001/nonadmin runtime unavailable to agent, one approved host execution
unused. No second independent post-fix review or actual numerical run claimed.

### Authorized pin/bootstrap repair after actual ordered-v2 failure

AUTH: user said "GOT ISSUE, SOLVE IT AND GIVE ME SCRIPT TO RUN SUCCESS" and
supplied ordered-v2 actual receipt8aa9a351... . This authorizes the bounded
demonstrated harness correction, tests, review and one fresh successor handoff;
not a forced PASS, old-attempt retry or install/security/Git expansion.

Actual child stderr2cc9066b... stops at E_ORDERED_RETAINED_RUNNER_CHANGED before
test execution. Runner literal has65hexcharacters; unchanged live/frozen/copied
retained_unittest.py all match the64character pin in the existing sealed source
manifest (4aba6fe49641f86dcb548219f0c6efc8bbd2fbaa4e32f5be40703a1cee18453b).
The FileNotFoundError for Ordered-Outcomes.json is SECONDARY. Full normal
history/Git/selected-Python identity probes passed, not retrieval. Previous
19/175 unit/policy evidence missed the actual main bootstrap; it was insufficient.

INTENT: runner rejects unchanged trusted bytes because its literal is mistyped;
validate the exact manifest-proven helper through the real CLI startup, keep
tamper refusal, report original child stderr before parsing absent reports.

Compare: no build leaves known unusable handoff; changing only the literal fixes
this launch but leaves the untested entrypoint and masked error; recommended
small correction also adds no-worker bootstrap mode and missing-record primary
error handling, retaining all current observation/containment/history guards.
No redesign of retrieval/cleanup. Weak link: later actual retrieval behavior is
still unknown. Cheapest falsifier is the real controller CLI bootstrap before a
new attempt; any mismatch stops, never resets a consumed root or qualification.

- [x] P1: actual CLI bootstrap RED/GREEN, valid manifest hash accepted, modified
  helper refused before execution; no worker or test output created.
- [x] P2: original child-error regression; seal old v2 receipt/streams/full15file
  inventory and567copy, retain originals/code, use NEW equal-length ordfix and
  order-pinfix-v3-20261021 roots. No mutation of consumed old inputs.
- [x] P3: focused/full policy checks, final native read-only review and reviewed
  fixes, exact v3 external seals/PowerShell syntax/account guard. No success
  promise for unexecuted retrieval; state exact observed boundary.
- [ ] P4: ONE new normal-account original-method run via new handoff only;
  actual result review remains needed. All fix/Gate1/release/native/install
  qualification flags false. Existing old commands remain consumed/closed.

Owned edit surfaces remain only ordered runner/driver/focused tests, new private
artifacts and existing Fable records. Archive exact consumed-v2 code before
editing, preserve all prior data, allow only new test-owned temporary cleanup.

P1..P3 closure,2026-10-22: see gate1-ordered-v3-pinfix-review-20261022.md.
Same credit-interrupted configured reviewer resumed; SHIP for ONE normal-account
v3 diagnostic,0Critical/0Important/1Minor. Minor stale evidence pointers reconciled
in these records. Fresh focused23/23 p-0c4397c5 and whole-policy179/179 p-70191be0,
zero errors/skips/exclusions/expected failures. Parent verified raw log hashes,
actual no-worker bootstrap, all12launcher pins, AST0errors and absent new roots.
This does not close P4, original cleanup cause/fix,217case/24arm Gate1 or release.
Only Run-Gate1-Ordered-Context-v3.ps1 SHA9cdf019439ed457056e5421ad682bec85e2b987de7e81c6fc0c883229600a3b0
may be handed off with outer hash check,VerifyOnly,then ONE normal-account run.

### Authorized bounded subtest-accounting repair — actual V3 result

AUTH latest user: "FIND IT ROOT CAUSE VERIFY AND FIX THE ISSUE ONLY THO COMPLETE
THIS STAGE". V3 actual receipt14c350e4... is CONSUMED/CLOSED, never rerun.
Its6streams/testlog hashes match. Real method ran, with community assertion FAIL
(internal E_WORKER_TIMEOUT) and vector replay ERROR (E_DISTRIBUTED_CLEANUP,
WinError32 file-in-use). The existing validator wrongly expects failures=[parent]
and errors=[]; stdlib addSubTest records child IDs and separates FAIL/ERROR.

INTENT: report real failed subtests without masking them as accounting errors;
require exact selected parent/mode IDs, FAIL/ERROR log categories and exit code,
retain every failure and false qualification flag. Complete this accounting
stage by reviewing SAVED evidence, not repeating numerical work or forcing PASS.

Compare: no-build keeps a proven mask; accepting arbitrary errors/ID prefixes
would weaken checks; choose exact parameterized-ID reconciliation plus verified
unittest-log categories and failed-mode reporting. A new worker mechanism or
timeout/security change is outside this bounded correction. Original worker lock
holder and timeout cause remain UNKNOWN, no ACL/sleep/ignore-errors workaround.

- [x] A1: meaningful real-stdlib and retained-result RED controls; archive exact
  V3 code before edit. Freeze readable consumed V3 inventory/source identities.
- [x] A2: minimal driver-only accounting/classification correction; reject wrong
  or duplicate IDs, wrong FAIL/ERROR category, bad exit/status and tampered log.
  Earlier timeout must not hide a later complete cleanup diagnostic.
- [x] A3: focused/broader controller checks, bounded independent review, saved
  result reclassification without worker/API/model/native execution; preserve
  original receipt and mark actual runtime failures/Gate1 incomplete honestly.

Touched: ordered driver/focused tests, private NEW validation outputs and existing
Fable records only. Runner, retained helper, original tests/product/runtime and
all old sources/caches/receipts/contracts/launchers unchanged. No new normal-run
launcher, retry, install, permission change, commit/push or release in this slice.
If saved evidence cannot be checked, report partial; do not replace any baseline.

A1/A2 observed closure: RED28/5failure-records/0errors a-50510749 -> GREEN28
a-fd6a13fa, broader184 a-5b7de4fc. Additional exact hash/parse race RED29/1failure
a-17e0fe4f -> GREEN29 a-0ce101b0 after verifying/parsing SAME raw byte buffer.
Final whole-controller185/185 a-2172645b,0errors/skips/exclusions/expectedfailures.
Plain stdlib29/29 also passes without retention monkeypatch after keeping the
new log fixture alive through classification. No original worker ran again.
Saved V3 classification now retains BOTH timeout-cause-UNPROVEN and observed
WinError32 cleanup detail; original unit still1FAIL/1ERROR/exit1, never PASS.
19readable evidence records and567source-copy files rechecked unchanged. Complete
old output inventory and fixture/pack reopening remain BLOCKED_AGENT_ACCESS_DENIED;
no paths skipped or permission changes. See accounting-repair report for scope.
Final same-seat review SHIP: no Critical/Important accounting defects remain;
reviewer independently checked final29/185 receipts/logs and saved V3 records.
A1..A3 closed ONLY for bounded accounting repair, VERIFIED WITH CAVEATS. Unknown
worker timeout cause/lock holder and blocked full-history/pack readback remain;
no broader Gate1 or preservation claim. No new normal-run launcher is built.

### W1..W3 worker diagnosis — proposed, awaiting full-description approval

Spec: offline-first-release-design-20261020.md, section W. User requested
Superpowers and described the next bounded diagnosis. No explicit new milestone
approval is recorded yet; do not infer selected-runtime permission from an old
consumed command. Existing inline/native execution method and Fable ledger stay.
Planning/reconnaissance only this turn. No diagnostic code or command is built.

Global constraints: SAME selected3.12 environment and dependency/image pins;
worker30/public90/method600 deadlines; no warmup/cache reset or payload/result
changes; failed-arm data/all historical records retained; only new owned temp
cleanup allowed; native/models/install/security/Git/release/install remain off.

Review focus: wrong SID/runtime or replaced/linked input; inaccessible old data;
missing/out-of-order/overflow/exception telemetry; PID reuse/unknown holder;
observer-created handle or timing perturbation; mixed FAIL/ERROR must not PASS.

#### W1: build the minimal observer and real controls after approval

Files to CREATE (not created now):
- .github/scripts/worker_diagnostic_events.py: bounded event codec/phase parser
  and exact-source-copy overlay builder; no worker policy or authority.
- .github/scripts/worker_lock_probe.py: normal-account,exact-new-file,query-only
  Windows file-user observation with owned-session closure.
- .github/scripts/worker_timing_lifetime_diagnostic.py: fixed source/layout,
  sealing/preservation and owned-tree controller; no old-launcher dispatch.
- .github/tests/test_worker_timing_lifetime_diagnostic.py: real stdlib controls,
  malformed-input/observer-transparency/strict-result regressions.

Interfaces: emit(event:dict)->None writes one bounded exclusive NEW sidecar,
closes it, and records any failure as diagnosis-incomplete;
parse_events(records:list[bytes],expected:dict)->dict describes balanced fragments
only, never complete observations. validate_trace(records:list[name+checkedbytes],
expected:rootPID+arm+publicCount)->dict adds exact filename, role, required-phase,
parent/spawn generation and process closure; only that may report OBSERVED;
diagnostic_source(raw:bytes,expected_sha:str,role:str)->bytes refuses unknown
anchors and changes only reviewed observation sites; query_file_users(path:Path,
owned_root:Path)->dict reports OBSERVED/UNKNOWN/ERROR with PID+start identities;
prepare_inputs()->dict freezes known identities plus distinctly labelled first
observation; run(prepared:Path,external_sha:str)->int owns one fixed two-arm run.

- [ ] RED tests: preserved original return/exception and original invocation
  count/order; wrong anchors/no source change; malformed/overflow/missing phase
  must not become cause/PASS; no live stream seek/extra inherited handle.
  Bound the diagnostic-copy-only environment addition, event files and sampler;
  refuse wrong arm/PID identity, unsafe paths and telemetry failures. Baseline
  has neither helper overlay nor event environment variable.
- [ ] RED Windows known-owner control: READY/no-delete-sharing -> native failure
  and exact fixture PID+creation identity; separate RELEASE-before-cleanup ->
  success. Preserve failure files; controller can reap only its own children.
- [ ] Minimal GREEN implementation at declared sites, then focused and complete
  relevant controller suites with retained logs. No selected numerical run yet.
  Unavailable Windows control remains BLOCKED, never skipped as passed.

Named assertions to pin in that test file: original success/exception and call
counts unchanged; unknown overlay anchors leave bytes unchanged; missing,
overflowing or wrong-arm/PID events yield INCOMPLETE; no live stream seek or
inherited observer handle; wrong runtime or unreadable history creates no run
claim; observed PASS alone sets neither cause-proven nor repaired/ready flags.
Known-owner/released-owner Windows controls must bind PID+creation identity,
exact NEW filename, one cleanup call per arm and retained failed-arm contents.
Do NOT read/copy baseline internal temporary streams to satisfy evidence capture.

Future focused verification (after approval, from exact repository cwd):
`C:\Python314\python.exe -B .github\scripts\retained_unittest.py --package-root .github/tests --test-dir . --pattern test_worker_timing_lifetime_diagnostic.py --output-dir .github/run-artifacts/offline-first-20261020/<NEW-W1-RUN>`.
Use a new absent retained output name for each RED/GREEN pass; require nonzero
meaningful assertions, exact counts, zero unexpected failures/errors/skips in
GREEN and matching log hash. Broader controller verification uses the same
runner with pattern test_*.py in a different NEW output. The real Windows holder
control remains an explicit W3 normal-account gate, not a synthetic substitute.

#### W2: review and freeze exact input/normal-account handoff

- [ ] One fresh configured native read-only final review; correct accepted
  findings with real failing/passing controls. No per-step duplicate reviews.
- [ ] Seal helper/source/overlay/runtime/test identities, new ordinary equal-
  length paths, exact account/commit and dirty-content snapshot, raw command
  streams and false qualification flags. Old contracts/commands stay immutable.
- [ ] New reviewed Prepare/Run launcher under NEW private worker-diagnosis root;
  outer SHA and VerifyOnly checks before Python. Prepare only full-history
  readback and input records, no numerical worker/attempt; normal-account
  supplemental V3 map labelled FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION.
- [ ] Parent verifies/seals Prepared hash before exactly one Run. Actual selected
  child-context/loaded-image probe before consuming the workload attempt. Stop
  on ACL/trust/guard failure; no interpreter/owner/security substitution.

#### W3: execute only frozen controls and two workload arms; judge actual result

- [ ] Normal-account known-lock/released-lock controls FIRST. Failure to observe
  planted holder or required history blocks workload execution; no retry loop.
- [ ] ONE baseline + ONE observed original four-mode method, each fresh exact
  source/fixture, unchanged30/90/600deadlines. No imports warmup or history
  hashing/owner query/wait inside timed worker paths. Record observer overhead
  and any concurrent owner query; cache warmth uncontrolled.
- [ ] Correlate timing phases and process/stream/owner evidence, retain original
  real FAIL/ERROR/exit states. No marker or PID query is producer authentication.
  No reproduction -> INCONCLUSIVE, not repaired. Owner unknown -> UNKNOWN.
- [ ] Full post-preservation outside timing window; independently review saved
  result and update existing Fable checkpoint. Never promote this diagnosis to
  Gate1 completion or rewrite old receipts. No new-run automatic retry.

STOP after W3. Cause-specific product repair and regression, remaining full
five-group217case/24arm Gate1, successor packages/CI and installation are later
gates. Preserve uncommitted accounting repair; no commit/push in W1..W3.

Plan self-review2026-10-22: W1 owns observer/transparency/refusal controls; W2
owns full-history, account/runtime/seals and one-shot handoff; W3 owns planted
holder controls, exactly two original-method arms and result/preservation review.
Five Review Focus classes map to those gates. Types/names agree; existing
inline execution method retained; no unbuilt command is presented as runnable.
One fresh builder question resolved in design W, no second governor or plan.

W1..W3 AUTH2026-10-22: current user "APPROVE AND COMPLETE THE ISSUE" plus
Autonomous Operator explicitly approves this isolated diagnostic. Supersedes
W's approval-pending wording only; no new approval inside this range. Product
repair/redesign, commits/push/install remain separately bounded. Gates and
entry hashes: evidence/offline-first-20261020/worker-diagnosis-20261022/.
INTENT: previously only opaque timeout and cleanup errors; add bounded copied-
source phase/lifetime observations, never change actual worker deadlines/results.

W1 review correction2026-10-22: independent FIX-FIRST found session-close
interference, impossible coordinator quota, missing trace/schema closure and
inherited child bytecode writes. Parent corrected with retained RED/GREEN;
same configured seat is verifying this correction, not a new review campaign.
Read worker-diagnosis-20261022/Review-Corrections.md. Ordinary child128events/
16KiB unchanged; coordinator512events/64KiB after measured73/30037 fixture;
accepted total1MiB. Polling calls no longer wrapped, shard received-request
phase excludes idle readline. Historical companion handshake retained under
scoped inherited no-bytecode/no-user-site guard. Exact seal/Prepared roles are
mandatory; normalized launcher template avoids circular hashes while outer
launcher hash binds actual seal digest. These are diagnostic safety changes,
not worker repairs. W2 remains unfrozen pending same-seat delta disposition.

### W-COPY proposed next milestone — full-description approval pending

The user selects fresh BEFORE/AFTER copies rather than normal direct reads of
restricted originals. Full proposed staging and limits are in design W-COPY;
fresh native builder check returned "nothing important left". Existing sealed W
code/commands stay immutable. No new implementation/runtime is approved merely
by recording this plan direction. Before building a successor: obtain approval
of W-COPY's explicit staged sampling description, then add the detailed inline
TDD implementation tasks here (not a second project or new memory engine).

Proposed deliverable: complete, disjoint normal-readable/reader-copy content
maps; sealed BEFORE/AFTER phases; pending outcome until final preservation;
failure-first refusal controls and a reviewed fresh handoff. No ACL changes,
skips, old-data deletion, old-command reuse, native backend or Git action.

## W-COPY Implementation Plan — approved 2026-10-22

> Execute inline using superpowers:executing-plans and test-driven-development.

Goal: complete copy-based supplementary archive comparisons without ACL changes.
Architecture: immutable normal scan requests, reader-produced copies and normal
verification merge into before/after maps. A sealed successor retains the exact
W worker routine and mandatory guards; final preservation is a separate phase.
Tech: existing controller Python3.14/stdlib; existing selected3.12 for later W.
Spec: W-COPY section of offline-first-release-design-20261020.md.
AUTH: current user "aprove" to implement/test this reviewed description.
Global constraints: no old-command retry, old-data deletion, ACL/config/install,
native/model action, commit/push or production skill changes. Original30/90/600
deadlines unchanged. Every result unauthenticated/self-reported, no readiness.

Review Focus: incomplete/overlapping coverage; stale phase/copy replay; changes
to originals hidden by unchanged copies; redirected/replaced paths; premature
acceptance while AFTER is missing. Each is exercised by C1/C2 refusal tests.

### C1 — immutable snapshots and copy verification
Files: create .github/scripts/archive_copy_snapshot.py and
.github/tests/test_archive_copy_snapshot.py. API: scan(root,session,phase,
binding)->dict; copy_denied(request,output)->manifest; merge(request,copies,
copy_sha)->bundle; compare(before,after)->dict. All names map original relative
paths; only explicit denied subtrees get reader copies. No skip becomes PASS.
- [ ] Write/run missing-feature REDs for complete merge, changed/added/removed
  originals, still-denied source, tampered/incomplete/replayed copy, unsafe path,
  overlap, linked source and no-overwrite before implementing the functions.
- [ ] Implement minimum GREEN; run retained focused tests with zero hidden skips.

### C2 — sealed staged W successor and lifecycle gates
Files: create .github/scripts/worker_copy_successor.py and
.github/tests/test_worker_copy_successor.py. Consume C1 bundle/records; provide
Before/CopyBefore/VerifyBefore/Run/After/CopyAfter/Finalize modes. Bound config
root/session/output/helper/source identities; exact normal SID for normal modes.
- [ ] RED refusal tests: missing BEFORE means no claim; absent/mismatched AFTER
  means no preservation success; source/controller pin drift refuses; mandatory
  history errors still stop; pending runtime never becomes whole-W completion.
- [ ] Reuse original sealed mandatory history prefix and workload routine with
  fixed successor bindings, not a generic caller-provided runner. No mutation of
  old modules/files, fake inventory or invented original-preservation baseline.
- [ ] Bind AFTER to exact BEFORE plus retained provisional workload receipt.

### C3 — regression, review and first normal-account handoff
- [ ] Run focused C1/C2 and complete controller suite through retained_unittest;
  compare original sealed roles/launcher/source bytes; parse JSON/PS and diff.
- [ ] Fresh configured read-only whole-change review; one evidence-led correction
  pass with RED/GREEN for accepted important findings. Keep review limitations.
- [ ] Freeze successor helper/config identities outside ARTIFACTS; provide ONLY
  new Before-mode normal-account command first. It starts no numerical worker.
  Parent must inspect actual request before agent-copy; never guess coverage.
- [ ] Update checkpoint/state with observed results, exact next phase and hashes.

Ruling: reuse approved checkout/inline ledger, not a new Git worktree or second
plan store. Existing dirty changes and sealed helpers stay protected. Retain all
plan/test workspaces, overriding skill default cleanup; commits need approval.
Pre-flight: C1 produces maps/record bindings consumed by C2; C2 cannot accept
runtime until BEFORE, nor finalize until AFTER. C3 handoff freezes both modules.
Rollback: leave old sealed W untouched; stop using new successor, retain evidence.

W-COPY implementation checkpoint2026-10-22: C1/C2 and C3 local preparation DONE
with26+15focused/253controller GREEN; fresh review binding findings corrected
RED/GREEN. See Copy-Progress.md and Copy-Review-Disposition.md for rulings and
runtime gaps. New33role config sealed; external launcher checked/parser0/agent
SID refusal before Python. Actual normal Before first; no work claim, numerical
worker, cross-account full archive proof or W completion yet. Do not repeat
completed accounting/W1/C1/C2 or any consumed legacy command. No Git authority.

Actual post-handoff result: normal Before done; request verified. CopyBefore
STOPPED on the deliberate linked cache fixture. Current attempt is preserved,
not retryable; see CopyBefore-Hardlink-Finding.md and newest Copy-Progress.md.
COPY-H1 historical-data-only hardlink amendment proposed, NOT approved or built.
Do not reimplement accounting or existing C1/C2; the next decision concerns the
explicit no-hardlink scope contract. No old baseline/role/manifest may be edited
to disguise this actual stop as successful copying or completed preservation.

## COPY-H1 — approved bounded successor, 2026-10-22

AUTH: user's full COPY-H1 approval and three additional regression requirements.
This supersedes only the approval-pending sentence above. Preserve that failed
attempt and all old seals. No Git action, cleanup, install, ACL/trust change,
download, native operation or production skill change is authorized.

Execute inline, failure-first, in this existing checkout. Reuse the immutable
V1 snapshot and W routine through closed, separately sealed successor bindings.
Do not write another competing plan or restart accounting, C1/C2 or W1.

- H1.1: record an entry manifest; freeze exact historical scratch hardlink paths,
  IDs/link counts and origin evidence. No extension-only or directory-wide link
  exception. All other source/helper/configuration/destination inputs stay strict.
- H1.2: add RED/GREEN tests for independent copies, original identity/content/ACL,
  BEFORE/AFTER freshness, mutation/addition/missing originals, tampered/missing/
  wrong-phase/session copies, scope escapes/trusted aliases, redirects,
  non-overwrite, interruption and invalid timing/mapping/completion records.
- H1.3: implement the smallest scoped content-reader policy and staged controller.
  Originals are data only. BEFORE and AFTER are distinct, outside the archive;
  AFTER reopens originals. Explicit batch timing references avoid naming changes.
- H1.4: run focused and full controller regressions; one fresh read-only native
  review and evidence-led correction pass. Preserve every RED/GREEN receipt.
- H1.5: seal a new run/session/helper set and issue only its new normal Before
  command. Continue the approved cooperative stages, stopping on each failure.
  Keep W's original 30/90/600 deadlines and pending preservation status until
  independent fresh AFTER observation verifies the archive comparison.

Interfaces: source-policy file binds exact archive targets and role/ID whitelist;
request binds session/phase/config; Copies binds request and batch/mapping times;
Bundle is derived only from verified request and copy bytes. W Prepared binds
that BEFORE bundle; AFTER binds the same BEFORE and provisional W receipt.
Review Focus: a forged derived bundle, reused BEFORE as AFTER, authoritative
hardlink disguised as data, redirected output before first write, partial-copy
completion, unbound timing records, and permission/identity changes during read.

Ruling: retain original filenames and use exact paths plus session/phase/hash
bindings, not optional _copy renaming. No collision-renaming feature is needed.
Ruling: retained workspaces and existing Fable ledger override skill cleanup/
automatic-commit defaults. No new automatic deletion is added. Old fixtures
remain read-only; normal-account phases still require their actual account.
Completion is four separate claims: copy/preservation, W execution, runtime
causation, and Gate1. Copying alone cannot close the latter three.

## Completed-work publication checkpoint - 2026-10-23

AUTH: user "commit and push it", then "CONTINUE FROM WHERE YOU STOPED".
This separately authorizes publishing completed local source/test/Fable records
to development/r5-practical-fence-wip-20261014, not main or every local branch.
Plan: verify the saved successful normal BEFORE bundle and retained test/log
identities; update the existing checkpoint; audit the exact Git paths and scan
for credentials; commit this checkpoint; fast-forward push only that branch;
verify the exact remote SHA. Preserve every old attempt and all private data.

Before readback is now observed: bundle0def61c9...13247059bytes, exact48799-object
union and context verified. The demonstrated access/historical-hardlink BEFORE
blocker is CLOSED. No speculative worker repair or new test stage is included.
W runtime/fresh AFTER remain unrun; timeout/file-holder causes, Gate1, final
release verification and installation remain open. The containing commit is
the checkpoint identity; publication is not an installed or release qualification.

The simpler adequate route is this completed-work checkpoint. Repeating completed
copying adds no required proof for publication; expanding into W/AFTER execution
would exceed the present request. Preserve old HEAD-bound seals and require a
reviewed exact-commit continuation before a future runtime run. No guard bypass,
ACL/trust change, install, deletion, package rebuild, model/native call or PR.

## ET - user-requested extended-time, per-file diagnosis (2026-10-23)

AUTH: user asks to remove the30second limit for measurement, add per-action/file
timing and return an actual result table. This is a NEW diagnostic, not a retry
of old W/N3/Gate1. The earlier immutable30second W contract remains unchanged.
INTENT: observe completion or an honest unfinished state with120seconds selected
through the existing supported WorkerClient API for BOTH search and replay.
Production default30 and maximum120 remain unchanged. An unbounded hung process
is not required: outer child watchdog180seconds, whole diagnostic900seconds.
No per-phase budget restart. No unsupported timeout override or hidden retry.

ET1: add failure-first per-file/time-table controls; reuse the existing hash-bound
phase observer on an exclusive Git-b71b75b package copy. Add a separate small
file read/hash/path-lookup logger and retain START/END, UTC/monotonic times,
PID/thread, bytes, exact paths and unfinished spans. No protocol stdout logging.
All new helpers/tests are .github diagnostic-only; live package bytes stay fixed.

ET2: fixed community/single then vector/distributed-local cases based on the
three-source Completion fixture that exposed the failures; querywork, required
worker/U000001, original result semantics and fresh verification preserved.
Use public retrieval CLI and fresh-process verify_pack. Time fixture creation,
index build, public retrieval, selected units/unique sources, replay, shutdown
and existing cleanup. A failed case is retained as failed, not retried or called
a success; unexpected input/provenance/preservation error stops the diagnostic.

ET3: focused and relevant broader controller checks, fresh native read-only
review, exact-commit/runtime/helper seals and a single normal-host command if
the existing selected interpreter remains unavailable to the agent. Verify its
identity BEFORE consuming the workload attempt. No install/substitution/ACL or
Git write. Retain every old cache/attempt and fresh outputs; only existing
worker-owned NEW temporary housekeeping stays within prior approval.

Scope difference: this new timing experiment measures an isolated copy and its
explicit source/helper/runtime/old-receipt bindings, not the old W whole-archive
BEFORE/workload/AFTER qualification. It neither restarts COPY-H1 nor asserts a
new whole-archive preservation verdict. Check every pinned live package input
and the six existing source-cache files before/after; keep all old histories
read-only and unmodified. Record any unreadable required input as blocked.

Completion: actual table if runtime executed; otherwise a tested/sealed host
handoff with runtime result UNKNOWN, never fabricated durations. A120second
timeout means completion time >120/unknown, not exactly120. Inclusive nested
and parallel times are not summed as wall-clock total. File lookup is declared
path validation, not a fabricated whole-disk search measurement. No learned
model/provider/native backend, release/installation/commit/push or permission
changes. Any later fix or release scope decision stays separate.

ET current observation:26focused/312broader controller checks PASS;3fresh review
blockers reproduced RED and closed by same-seat native re-review. New isolated
Prepared/source copy and hash-checked normal-account launcher frozen; final
review SHIP covers one timing run only. Actual selected3.12 timing remains UNRUN.
Read ../evidence/offline-first-20261020/extended-timing-20261023.md for hashes,
retained test evidence and exact resume. Do not edit frozen helpers, rerun any
old command, restart H1, or equate timing observation with a worker fix/Gate1.

ET ACTUAL normal run now consumed: both initial/fresh replays PASS; receipt
b4bf001140ad6d4c486f4674bd7b82cf3c0ea23879e1c7bf994000c11822f569.
Cold comparable community worker41.906s, Semantica27.453/numerical12.234imports;
community replay6.189s outer, vector10.331/replay12.548s outer. Final result
review accepts bounded evidence WITH8derived startup PID-join gaps caveated,
not a complete startup trace, historic cause proof, permanent repair or Gate1.
No rerun/build to obtain already saved measurements; preserve all frozen bytes.
Next smallest budget/cold-start handling and Gate1 continuation need reviewed
scope through this existing plan, not another copying or timing-system redesign.

## TB - approved bounded default-budget correction (2026-10-23)

AUTH: "changes the30s to suitable time greater than loading package time and
close the issue". INTENT: change knowledge WorkerClient/DistributedClient and
public retrieval/offline-run/fresh verify defaults to the existing supported
120seconds, consistently including the programmatic preflight fallback.
Measured first worker41.906s and successful120s search/replay are the basis.
Keep explicit shorter overrides, positive/max120 validation, shared deadline,
kill/reap/error propagation and all source/access/evidence checks unchanged.
No-build leaves known cold calls failing. Recommend the simplest default-only
correction; lazy imports/persistent workers would be a separate unnecessary
architecture change here. No new model/runtime/install/native/Git action.
Add failure-first clock-driven delayed-worker/CLI/replay regression controls,
run the relevant source suites and review actual diff. Preserve consumed timing
source, hashes and logs unchanged: their old live-source seals become historical
after this approved change; never rebind/rerun their guards. Update source-use
instructions; historical manifests/releases stay untouched until release work.
Close the inadequate default-budget defect when code/tests/review pass. Do not
close historical intermittent WinError32, Gate1, release or installation by this
change. Any unavailable current selected-runtime execution is stated separately.

TB observed: default120 applied in4files/5literal substitutions plus usage docs;
7focused GREEN after6RED. All broader suites completed, not all green: MI700
has1containment failure/3errors/54skips/1xfail; CM213 has1missingmanifest error;
legacyMI21 has4loopbackHTTP errors under no-network wrapper. Preserve named
failures; no unrelated fixes or test weakening. Default-budget SOURCE defect
closed; remaining Gate1/release/install/WinError32 not closed. Native final
review unavailable from credits, parent diff/caller/test review recorded in
timeout-budget-correction-20261023.md. No rerun of consumed timing/oldsource seals.

TB publication AUTH2026-10-23: user "push to git with details and everythin,
so30sec error was solved". Commit/push completed17-path source/tests/evidence
checkpoint only to existing development branch; no force/main/release/install.
Exact file identities/added-line credential scan/staged scope and remote ref
must be checked. Seven timeout controls pass; broader release/host/historical
pin checks are not allgreen and must be reported, not silently weakened. Keep
private run-artifacts/caches/copies/selectedenvironment/oldpackages local. See
timeout-publication-20261023.md. After verified publication, continue separate
Gate1/release qualification; no further timeout-default rebuild is required.

## G1-CURRENT — approved sequential continuation, 2026-10-23

Authority: user "complete this 1 by 1 at a time" and the three named source,
integrated-runtime, and shutdown/preservation items. Published source basis is
a38297dd797eeecd25e41ab0af1df4e3db8fa984. Existing branch/checkout reused;
production packages stay unchanged. No commit/push/install/download/ACL/trust,
native backend, learned model, old-data deletion, or old-command retry included.
Fable remains the only plan/ledger; no new Superpowers worktree or plan store.

Recommended: a separate sealed coordinator and exclusive retained workspace.
No-build/old launchers fail their valid historical pins; rewriting those pins
would lose historical meaning. A new runtime/framework is unnecessary. Weak
link: Store Python is account-dependent; an unavailable selected interpreter
means a normal-account handoff, never substitution or an invented pass.

Scope now: new .github/scripts/gate1_current_preflight.py and corresponding
.github/tests/test_gate1_current_preflight.py; private contract/launcher/new
workspace; existing Fable plan/checkpoint/state plus a concise evidence report.
No edits to old helper/launcher/input/receipt files or production packages.

- [x] G1-C1: failure-first source-copy and runtime-validation controls; independent
  review; external hash seals; verify exact committed file/blob set, clean
  extraction with no overlays, existing controller/venv/config/loaded image and
  53 approved dependency versions. Produce Prepared.json and a retained receipt
  only after actual normal-account observations and before/after protected
  package/cache/release comparisons. No retrieval or numerical workload here.
- [ ] G1-C2: only after C1 result review, separately seal the same continuation's
  runtime phase: discover exact five group IDs (static current expectation224,
  not the old217); run all groups and24 initial/fresh-replay comparison arms.
  Preserve explicit conditional skip accounting, no exclusions/hidden failures.
  New harness must exercise omitted/default120 in both initial and fresh replay;
  old acceptance/cleanup helpers' explicit60 is not proof of that default.
- [ ] G1-C3: review actual owned-worker/tree/stream/cleanup and protected-data
  evidence; report scope and every blocked/unreadable historical path honestly.
  No claim that C1's source/env snapshot is an archive-wide preservation proof.
  All three items must be observed before Gate1 completion is considered.

Interface C1 -> C2/C3: exact Prepared path/hash, source commit, complete source
manifest, runtime records, input records, and current run ID. No newest-file
selection. Failure retains partial output and cannot create an accepted success
receipt; existing destination means stop, not automatic retry. Source/package
maps and old receipt pins are rechecked after the identity-only child commands.

Verification: retained_unittest.py with --test-dir .github/tests and the new
test pattern, then relevant existing image/source/capture tests. Fresh reviewer
must attack archive traversal/collision, overwrite/redirect/link handling,
dependency/image/context mismatch, child-error handling and false completion.
Stop on inaccessible mandatory inputs; use one exact externally hash-checked
normal-PowerShell C1 command if required. C2/C3 remain unrun until C1 passes.

Ruling: user preservation/approval boundaries override skill auto-commit,
cleanup and competing workspace defaults. Copies/logs remain retained; no Git
write. Cost: C1 alone is explicitly partial, not an installed/release verdict.

C1 actual normal result verified2026-10-23: Receipt f0a8b97b49122ad2dc86c5b7adeb4c38e84d97cc774afa80e8debba0d8e30b14,
Prepared98bfd5870d3d4032cd250dc268a99a3a791b61787081a539f9f4eb2f3818a75d.
Parent checked full627file clean copy, fixed inputs,344protected files and all
6streams; independent read-only review accepts C1 WITH CAVEATS: metadata is not
numerical retrieval or C3 handle proof. Never run C1 again.

### C2 execution detail (same approved continuation, not a new product plan)

Scope: add .github/scripts/gate1_current_runtime.py, matching
.github/tests/test_gate1_current_runtime.py and Run-Gate1-Current-Runtime.ps1;
new sealed C2 input artifacts and exclusive sibling C2 output. C1 helper,
launcher, contract, source and results remain unchanged. Existing Fable records
are updated; no production change or Git write.

Interfaces: successful externally pinned C1 Receipt AND Prepared -> fresh
source/runtime/input/preservation check -> five exact discovered ID lists ->
normal-account preclaim interpreter/context check -> one workload claim ->
five original suite groups ->24initial/fresh-replay acceptance comparisons ->
final preserved-input comparison -> result PENDING_C3_AND_REVIEW, not Gate1.

Use the original C1 suite recorder and strict per-case/aggregate accounting;
only explicit optional-parser/model/POSIX skips may be accepted. No exclusion,
new skip, expected failure, assertion or oracle change. Controller stays3.14,
numerical workers selected3.12 as before. Outer watchdogs retain1200per suite,
2400acceptance and180per acceptance child; worker default120 never restarts.

Create ONE new acceptance-helper copy outside C1, with only3exact adaptations:
omit explicit60in WorkerClient replay; omit --worker-timeout60for initial
search; bind fixture lookup to the unchanged C1 fixture directory. Preserve
all assertions/refusals, generator __file__ hash and fresh replay invocation.
Validate its receipt using that exact adapted producer helper, not the old
generator's validator. Test that both initial and replay select default120.

Failure-first controls: bad/missing/unsuccessful C1 binding; missing/reordered
or duplicate IDs; excluded/failed/errored/interrupted cases; unexpected skips;
failed/incomplete capture before JSON; altered adaptation/source; partial24arm
set; wrong default or fixture lookup. Obtain fresh final review; fix findings
with observed RED/GREEN. No selected-worker workload while preparing/testing
the coordinator. If normal account is required, freeze one hash-checked C2
command; stop and retain any failed attempt, no automatic retry.

Coverage caveat carried: original acceptance save/fresh-recall/resume uses the
first mandatory LITERAL pack;24ranked/literal initial+replay comparisons remain
separate. Do not imply ranked-pack save/resume was added. Retained suite temps
are not real cleanup proof; actual worker shutdown/handle checks remain C3.

C2 preparation observation2026-10-23:11focused tests PASS;2new tests first
reproduced failed-command record loss and setup escaping receipt handling,
then passed after the bounded correction. Input-only discovery is224tests,
exact counts3/2/16/198/5. Adapter inverse restores original pinned bytes.
Contract6cb6cb39d6b3e2a702b0e2b63cba6a97b44f250fb4c396463bc62f5cd2113c15.
Launcher69544835b9bf37acfa88d3900db332473141c90b73e01134cb1dcdc1e8d1b14d.
External input verification/VerifyOnly PASS; actual wrong-account refusal
created neither C2 output nor failure marker. Numerical runtime is still UNRUN.
Broad controller343run:0failures,16error records,0skips/exclusions/xfails.
6historical source-pin records are unchanged;10newly observed WinError5 errors
are old timing tests unable to create new retained scratch under this read-only
agent profile. No ACL/old-test change. Full details and retained logs are in
../evidence/offline-first-20261020/gate1-current-runtime-20261023.md.

C2 ACTUAL NORMAL RESULT2026-10-23: attempt consumed; do not rerun. Receipt
4424beb7298567755735500144eae66b6a43ea7192446c554ea5f559a14b0c07 verified.
3groups pass21cases; knowledge group198has184PASS/1FAIL/13allowedSKIP/0errors.
Only failure is public vector/distributed-local initial retrieval cleanup,
E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP. Community/global/DRIFT
subtests did not fail. No current worker/suite timeout is reported. The actual
underlying cleanup exception is omitted by worker.py's public error serializer;
do not relabel it as proven WinError32 or a proven remaining-handle owner.
CM group,24acceptance comparisons and C3 were not reached. Receipt and fresh
readback confirm pinned preservation; no whole archive/cleanup qualification.
Next bounded investigation must capture original cause/notes and lifetime in
a separately reviewed successor using existing diagnostic machinery, not
another blind gate run or speculative production change. All old inputs stay
immutable. Gate1 remains incomplete; no new workload was run after the failure.

### Proposed narrow cleanup repair — design approval pending2026-10-23

User now requests SOLVE THAT ERROR with Brainstorming. The full bounded repair
description is in offline-first-release-design-20261020.md, "C2 cleanup repair
description". New read-only evidence from existing timing sidecars establishes
launcher/interpreter PID differences44836->47924 and27764->8088; it does not
establish the missing original C2 cleanup exception or a permanent orphan.

- [ ] CR1, pending description approval: controlled failure-first lifetime/
  handle reproduction and original cleanup-cause capture, no old-command retry.
- [ ] CR2: only a cause-supported owned shutdown fix, default120 and bounded
  cleanup unchanged; focused/broader regressions, twin audit, fresh review.
- [ ] CR3: one reviewed sealed fresh normal-account focused comparison; honest
  result, then decide current-source Gate1 continuation. No implied full pass.

No product code, new test harness or workload was created by this proposal.
No commit/push/install/delete/ACL/trust/native/model action is included. The
description must be approved before implementation per the requested skill.

Fresh native read-only builder-check completed: "nothing important left".
No material unanswered planning question was returned. This is design clarity
review, not implementation/root-cause/runtime verification or user approval.

### Approved CR implementation checklist (same plan/ledger)

AUTH: user said "approve" to the full bounded shutdown repair and fresh
verification description. CR1–CR3 local work is approved; no commit/push,
install, original-file deletion, ACL/trust change or old-command retry.
Native inline execution is retained. Existing worktree on development branch,
existing Fable plan/ledger and retained artifacts override skill defaults for
a second worktree/plan store, auto-commit and deletion. Current source base
a38297d; old C1/C2 inputs remain immutable controls, not editable destinations.

Goal: demonstrate correct real-worker exit before resource cleanup, retain
cleanup causes and verify the repair without loosening default120 or refusals.
Tech stack: existing Python3.14 stdlib tests/controller, selected3.12 for final
normal-account numerical observation, existing Windows APIs only if needed.

CR1 Files: create tests_v2/test_knowledge_windows_shutdown.py. Its actual two-
PID stdlib relay holds the owned output until stdinEOF. Observe pinned native
process handle after _Session.stop, not a mock `_stopped` label. Cases: idle
completion and expired-deadline cancellation. Run via retained_unittest.py with
new exclusive .github/run-artifacts/cleanup-repair-20261023/red-lifetime output.
Expected RED: real descendant remains alive under old immediate-launcher kill.
Record old source/receipt hashes before implementation, preserve every fixture.

CR2 Files: distributed_retrieval.py _Session start/stop/close; a narrow Windows
owned-tree helper if cancellation reproduction requires it; matching lifecycle
tests. Preserve POSIX behavior, default120, bounded shutdown and original errors.
Owned startup must not allow a pre-assignment descendant escape; forced stop
must independently await all owned processes, not just request termination.
No live-process PID-only broad sweep. Setup/partial failures close only owned
resources and cannot turn a failed shutdown into success. Add cause-reporting
only at the necessary existing diagnostic boundary. Run focus, lifecycle/cwd,
timeout/distributed regressions and full relevant suites; record all red/skip.

CR3 Files: one new reviewed helper/launcher and exact input contract. Reuse
existing error-chain formatter, capture and original ordered public test;
new folder/new source, never old C2 command/claim. Seal baseline and corrected
source/runtime/fixtures; compare original retained C1/C2/evidence inventories.
Only fresh selected-runtime initial/replay observations may close runtime issue;
no full Gate1/24arm/packaging/install inference. Stop on failure, no auto retry.

Review focus: asynchronous launcher/child exit, blocked stdin writer, partial
startup/ownership failure, nested Windows jobs, and close errors after valid
computation. Each must have a real/control failure case or be explicitly blocked.
Pre-flight interfaces: CR1 calls actual _Session, CR2 must preserve that API;
CR3 pins exact corrected bytes rather than repinning consumed C1/C2 contracts.
Self-review: scope matches design; process primitive details are builder calls
only within the bounded owned-worker contract. Material redesign returns to user.

CR progress2026-10-23: approved CR1 lifetime reproduction DONE (2 real RED
failures, then green). CR2 implementation now has7native PASS, plus existing
6lifecycle/7cwd/7budget PASS. CR3 guard tests5PASS; actual selected3.12 remains
blocked in agent by unavailable WindowsApps base, not substituted. A fresh
native final review is running. No new runtime contract/launcher is frozen yet.
Detailed evidence/failures: ../evidence/offline-first-20261020/cleanup-repair-20261023.md.

Ruling: add a Windows-only suspended-start owned Job helper — forced cancellation
reproduction proves orderly EOF alone insufficient; old post-Popen assignment
has a pre-assignment escape race. Cost if wrong: fail-closed Windows refusal;
actual selected-runtime nested-job comparison still required before closure.
Ruling: await pinned native member handles as well as job active-count zero —
one real cancellation control caught the counter reaching zero before actual
exit signal. Reject unobserved/born-during-stop members rather than guessing.
Ruling: no blanket broad-suite green label — current fullMI706has1failure,
3errors,54skips,1xfail; controller343has7errors. Preserve all named results.
Ruling: use a NEW exact committed-source baseline control for comparison, NOT
C1's committed_source live-equality guard after intentional edits. The guard
correctly refuses changed live code; it remains unchanged. New Git archive is
validated against immutable C1tree/manifest before testing, old copy untouched.

CR continuation2026-10-24: native final reviewer returned concrete FIX-FIRST
findings. Parent reproduced three original-cause masking failures; three
negative-control false acceptances; and two post-output setup receipt-loss
subcases. Each correction now GREEN. Final focused12lifecycle/error and11helper
controls PASS; the five added native-API fault injections are not extra real
numerical observations. Same review seat is checking corrections before sealing.
Baseline700 and earlier repaired706 have identical1failure/3error/54skip/1xfail
lists with verified logs. Fresh controller353 still has7same exact pin errors;
no guards/baselines loosened. Fresh full-MI pending. Approved CR3 remains one
new sealed normal-account comparison only, not old C2 retry or Gate1 completion.

Final correction review2026-10-24: SHIP for sealing only, no Critical/Important
findings. Parent independently verified fresh712 full-MI result and log hash:
653PASS/1FAIL/3ERROR/54SKIP/1XFAIL, no exclusions/interruption. All non-pass lists
equal baseline700 exactly. Final12shutdown/error and11helper guards PASS.
Proceed to exclusive new Runtime-Inputs contract and exact launcher seals;
actual selected3.12 comparison remains UNRUN, Gate1/release/install false.

CR3 handoff frozen2026-10-24 after correction clearance. Input-only contract
211348bytes SHA18b1d93425f0f52965b94ed7349acf11042065348aafc26b8152ce7c6b595838;
launcher SHAc9fb41897545625f3b152315fcef276b5afe343a75ac478183d7d8cf11086c59.
Parent actual VerifyOnly and complete input verification PASS. One new normal-
account focused comparison remains UNRUN; do not rerun preparation/old C2 or
replace this input contract. Read current checkpoint and report for exact seals.
Only raw-result/preservation review can close CR3; wholeGate1 stays incomplete.

## CR3 root-cause continuation — Deep Plan2026-10-24

AUTH: user requests Deep Plan "TO FIND ROOT CAUSE AND FIX THIS ISSUE TO MAKE
THIS STAGE COMPLETE" after the consumed CR3 failure. This authorizes bounded
local diagnosis, cause-supported correction and verification of this same stage;
not an old-command retry, broader Gate1/release/install or an outward Git action.
Fable remains the only plan/ledger. Inline implementation and one native read-
only review are retained; no new worktree, competing plan or external AI call.

TARGET: complete CR3 with observed selected3.12 all12 lifecycle cases plus the
repaired ordered public initial/replay/lease-refusal cases and pinned protection.
Surrounding system must remain healthy against recorded baseline; existing full
MI712/controller353 non-pass evidence must remain visible. Historical C2 cause
is not automatically established by a new corrected pass. Gate1 stays separate.

EVIDENCE: failed normal Receipt168066bytes SHAd214498c4e7ff2b613ebb933c4174e7c19a3125dc60350c34c1c5491d456c9d7;
outer repaired-lifetime TIMEOUT,60second watchdog, complete contained capture;
internal log first casePASS, blocked-real-pipe case started with no completion.
No unit receipt/Case-Outcomes was finalized. All4control modesPASS, historical
cleanup failure not reproduced; repaired-ordered UNRUN. Parent verified8streams,
both627/629source copies and current pinned inputs. Those command/log/receipt
signals are ONE runtime evidence family, not three independent witnesses.

OPTIONS: no-build retains failed state but cannot close CR3; simplest adequate
route reuses existing retained_unittest --stack-after10 and owned capture with
unchanged60watchdog in a separately sealed output; stronger hybrid adds broader
process/handle tracing only if the stack witness is inconclusive. Reject timeout
increase, skip, suppressed cleanup or speculative production rewrite. Prefer
existing mechanisms; new glue must not become another process framework.

RECOMMENDATION: obtain main/writer stacks in the selected runtime before fixing.
Constraints lens: frozen source/history stay read-only; no selected3.12 substitute.
Cost/outside-view lens: C314 real-process controls passed while selected3.12
stalled, so another C314-only pass cannot close the gap. Pre-mortem: teardown
may obscure the active exception; stack capture must precede the same watchdog
and survive timeout. Source inspection is a second evidence family for candidate
mechanisms, not runtime proof. Weak link is still the unobserved blocked frame.
CHEAPEST TEST: existing stack-after10, same12 unmodified cases and watchdog60,
new exclusive output, no retrieval/control repeat. PIVOT: no useful stack ->
review one bounded stronger observation; fixture frame -> reproduce/fix fixture;
production shutdown frame -> reproduce/fix only that path. Stop on unreadable
required pins, preservation mismatch or3evidence-changing failed diagnostic cycles.
CONFIDENCE: medium in diagnostic choice, low in a particular root-cause claim.

- [ ] RC1: new .github diagnostic helper, matching guard tests, new sealed input
  and normal-account launcher. Reuse current CR3 pins, old complete failure
  inventory, existing selected identity/capture/runner; add only --stack-after10.
  Retain timeout/failed test honestly; never label a captured stack a fixed stage.
  Fresh native review, then one new normal-account diagnostic if agent cannot
  start the already-known unavailable selected runtime. No old workload retry.
- [ ] RC2: after observed cause, failing regression then minimal correction in
  the evidenced test-fixture or shutdown surface. Preserve error visibility,
  process ownership, deadlines, no skip and unrelated changes. Material redesign
  returns to the user. Run focused/broader regression, twin search and review.
- [ ] RC3: reviewed separate exact corrected-source proof of all12 selected-runtime
  lifecycle tests and ordered initial/replay/refusal, compare raw results and
  all pinned inputs before marking this stage complete. Do not reuse consumed
  CR3 or diagnostic claims. Report any unreproduced historical cause explicitly.

INTENT RC1: current watchdog loses the blocked operation; requested diagnostic
retains timed thread stacks without changing the tested source or budgets.
Rollback: leave new retained diagnostics unused and preserve old source/attempts;
no automatic delete/rebaseline. Completion of RC1 alone is partial, not CR3 done.

RC1 observation:13new diagnostic guardsPASS including actual C314 existing-
runner stack dump; broad controller367has same7exact source-pin errors,0fail/
skip/exclusion. No MI source/test bytes changed. Parent full old-attempt walk
BLOCKED WinError5 at control-tests/retained-temp/mi-worker-9rtyb1xz. This reopens
the preparation placement decision, not the observed lifecycle cause: do NOT
waive full inventory or change permissions. Add only a separate sealed normal-
account INPUT-ONLY preparation launcher. It invokes controller --prepare, never
selected3.12/tests/workload claim. Old full inventory must be read successfully
there before new Inputs are created; then review/hash that exact Inputs before
freezing any runtime launcher. Current ROOT/Inputs/normal-stack remain absent.
Independent review requested; final preparation seal pending. Rootcause/fix and
stage closure remain unobserved, not inferred from13guards or preserved receipt.

RC1 input-only handoff2026-10-24: fresh independent review NARROW CLEARANCE for
preparation only. Frozen prepare launcher SHAb0eabad1fe626c76c47c9d2bb9d1d73940657c11accbaf0a4a4986fc4d563931;
helper SHAb03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031.
Parent actual VerifyOnly PASS and0PS parse errors. ROOT absent; runtime remains
FREEZE. Next normal input-only preparation, then exact returned Inputs review;
neither that code clearance nor preparation can close RC1/RC2/RC3 runtime gates.

RC1 host preparation observed and diagnostic frozen2026-10-24: Inputs189744bytes
SHAead95373d25ee2750a10c52e4e2bbf7cf3cabb087166b00df2533458bec27075,
1339entries. Parent verified exact16key schema/roles/cases/budgets/falseflags,
C1/runtime/protection,627/629source copies and8streams. Private scratch remains
host-verified only; full normal-context guard is unchanged before/after workload.
Fresh independent final seal review SHIP for ONE stack-only normal diagnostic.
Only2launcher literals changed. Final runtime launcher SHA
ffabc697263406c7598d1f59d2f718bfa65b6486d82f631fe096c67bf2e6df86;
parent actual VerifyOnly PASS,0PS parser errors. No normal-stack/diagnostic claim
exists. Next new normal-account command, no reprepare/old retry. RC1 actual stack,
RC2 cause-supported repair andRC3 stage proof remain incomplete, not inferred.

### TC1 approved — process/stage timing after captured wait2026-10-24

User asks timing of each process/stage as in previous issue and whether package
installation is involved. Actual stack attempt is consumed: Receiptc803e2fa...
and stack6fcc6477... show writerwrite/mainfixtureclose blocked at10seconds,
outer60watchdog; original exception still hidden. Coordinator receipt interval
74.648245seconds is aggregate including checks/capture, not per-stage timing.
Prior27.453Semantica/12.234numerical seconds are imports, NOT installs. Current
blocked fixture is stdlib-only and deliberately not readingstdin; no install
invocation appears. Do not confuse a metadata probe with installing packages.

No-build uses current stack only, cannot supply missing durations. Recommend
smallest timing-only adapter around existing bounded per-process logger in a NEW
diagnostic copy, with reversible/exact observation delta, rather than new logger
or whole-call profiler. Stronger whole-call profiling is a fallback only if the
targeted witness cannot identify the blocker; it perturbs timing more heavily.

TC1 scope after approval: existing timing logger reused unchanged where adequate;
new diagnostic glue/test/contract/launcher and existing Fable records only. Any
needed source overlays apply ONLY to new copies, exact original/hash/inverse
checked. Never repin an old observer or run old timing/stack/CR3/C2 commands.
Capture UTC/monotonic START/END, process CPU (not exclusive thread CPU), PID plus
creation identity, PPID/actual launcher-child links, thread, outcome/error/notes,
bytes when measured. No payload-content logging, protocol stdout or held loghandle.
Measure startup/module readiness; declared imports; fixture creation/child ready;
serialization; pipe write and flush separately; request/deadline; job membership,
terminate/wait; writer join; stream close/fixture finally. Capture sys.exception
BEFORE close to retain the actual original cause. No poll-event flood or inferred
direct launcherPID=interpreterPID join (the previous renderer's known limitation).

Done: actual table with durations or explicit unfinished/unknown/lower-bound
spans, correct process lineage, preserved original exception, no clock-overlap
double counting, no observer-error promotion to pass, and full named protection.
Unchanged0.1fixture deadline/5shutdown allowance/60outerwatchdog/120production
default. No package reinstall, dependency/environment change or test skip. Native
review and focused/regression guards precede one separately sealed host run.
Any readable-evidence limit is retained; no whole-private-archive claim or ACL
workaround. TC1 does not qualify a fix or complete CR3; RC2/RC3 remain separate.
TC1 APPROVED2026-10-24: user said "aprove, add timing show code in all part
and stage and segment". Execute TC1 inline, with a fresh native read-only review
before host handoff. No second approval inside this timing-only scope.
INTENT: add observation-only AST wrappers to a NEW diagnostic source copy;
preserve the original AST after removing wrappers, assertion values, all12cases
and0.1/5/60/120 budgets. Reuse the existing logger and process-creation probe.
Record original exceptions before fixture close, separately time write/flush,
and render exact code locations with completed/unfinished spans. Baseline HEAD
a38297d, dirty CR/Fable work retained; logger0b234e49 unchanged. Existing parent
stack Inputs/receipt/source and all consumed attempts remain immutable.

TC1 implementation observation2026-10-24:23focusedPASS (includes actual C314
12case instrumented copy);390broader0fail7exact historical pin errors, no skips,
not green. Retained REDs close new observer ownership/lineage/alias/coverage gaps;
fresh native final review and exact final preparation seal both SHIP. Observer
00ee0acf/helper883ec3cd/tests ef7b71f7 frozen; no MI source/test changes.
New Run-Cleanup-Timing-Prepare.ps1 SHA
9101c4d21730687d416a93f4b727cf2d05773e11067713a39b60268c819ac6d0;
parent0PS parse errors/VerifyOnlyPASS. ROOT/Inputs/normal-timing absent. NEXT ONLY
normal non-admin INPUT-ONLY preparation, then exact returned Inputs review and
new runtime freeze/review; not another approval request inside approved TC1.
No selected3.12/timing workload yet. Process-category MAX values are not totals;
unfinished spans unknown, original error may remain NOT_REPRODUCED. Report latest
cleanup-repair-20261023.md contains hashes/raw paths/caveats. TC1 actual observation,
RC2 cause-supported fix andRC3 proof still incomplete; no stage/Gate1 qualification.

TC1 host preparation observed2026-10-24: user returned Inputs85251bytes SHA
cf45dfde1fae5d2bb5f601a8d54c4fa68e62d5db35e3248ffe9bdfecf9476d62.
Parent independently verified exact15key schema, helper/3support records,629file
frozen source,12case IDs,0.1/5/60/120budgets, prior stack Inputs/Receipt records,
HEAD and unchanged CR verification of C1/runtime/protected/history. Full old CR3
walk still WinError5 at mi-worker-9rtyb1xz; full stack walk also denied at
owned-shutdown-proof-112v6tbq. These two private inventories remain HOST-PREPARED,
not independently agent-compared; normal-context full checks stay mandatory.
Inputs now EXISTS; preparation is consumed and MUST NOT be rerun. Normal-timing
remains absent. INTENT next: add only a new Run-Cleanup-Timing.ps1 sealed to exact
returned Inputs/reviewed helper/support/controller; retain normal non-admin SID,
no existing output, no retries and unchanged coordinator guards. No new runtime
logic/source overlay/budget/test change; parser, VerifyOnly, wrong-seal refusal
and fresh native exact-handoff review before issuing one timed host command.

TC1 runtime handoff observation2026-10-24: new launcher3472bytes SHA
3b049895ebd0af70cd1e1c25811bea4a63d7d35db92766a84532304a0b2b1aa2;
parent parser0errors/VerifyOnly/wrong-contract seal/actual wrong-account refusal
PASS, all before Python/output. First review credit-interrupted, not clearance;
same-seat retry after user continuation returned SHIP for exact launcher +ONE
normal-account diagnostic. Final source/helper/observer/Inputs hashes unchanged.
NEXT only new external-hash-checked runtime command, no reprepare. Normal-timing
absent; actual TC1 measurement/rootcause/fix/stage proof still incomplete. Read
latest report/checkpoint for normal-context private-inventory caveats and resume.

### MP1 — approved FIX-FIRST review continuation2026-10-25

Authority: user pasted shutdown cause review and said CONTINUE FROM WHERE YOU
LEFT. MP1 is its smallest next step, not conditional production redesign.
INTENT: one focused stdlib fixture records actual returned job membership and
creation-bound handle states before changing live MI behavior. Old TC1 is consumed.
No-build cannot answer membership; another full12-case timing run repeats the
known failure. Choose focused witness; stronger direct-image/overlapped transport
redesign stays conditional. Weakest link is selected-runtime reproduction.
Cheapest falsifier: IsProcessInJob of final blocked child BEFORE writing. If inside
yet survives termination, stop incremental ownership fixes and return to design.

Files: NEW .github/scripts/cleanup_membership_probe.py (native fixture/witness),
cleanup_membership_diagnostic.py (existing sealed-guard composition), matching
.github/tests/test_cleanup_membership.py, Run-Cleanup-Membership-Prepare.ps1.
Existing design/checkpoint/report/state/this plan remain the sole plan store.
New private root .github/run-artifacts/cleanup-membership-20261025. Same selected
venv, oversized request/.1deadline/5shutdown/60outer watchdog; no install/Git/ACL,
old-command retry, timeout increase, deletion or broad PID kill. Baseline HEAD
a38297d and dirty CR/TC1 work retained; expected new files absent before editing.

- [x] MP1-A tests first: complete four-role/creation-bound chain; current member
  count vs ActiveProcesses; lifetime TotalProcesses not treated as live count;
  outside/inside-survivor/pipe-only/inconclusive classification; emergency cleanup
  preserves original failure. Retain RED then GREEN.
- [x] MP1-B implement pinning of exact root/relay/nested-launcher/final-child native handles before
  oversized write; validate markers/parent/creation links. Record job PID list,
  total/active, per-role IsProcessInJob/signalled state before/after actual job
  termination and after stop. Record exact writer native identity and stop time.
  Observation failures cannot become usable classification or product success.
- [x] MP1-C implement emergency fixture cleanup AFTER measurement terminating only already
  pinned creation-bound fixture handles, cancels exact local dedicated writer
  using CancelSynchronousIo, then bounded join. Separate emergency5s budget is NOT
  extra product shutdown time. Never close buffered stdin while writer lives;
  preserve original stop error and retain files. No emergency success promotion.
- [x] MP1-D reuse unchanged TC1/CR/C1/runtime/history guards plus exact new helper
  pins and full consumed TC1 inventory. Normal-account INPUT-ONLY preparation if
  private history unreadable; no waiver. Runtime stays UNFROZEN until actual Inputs
  review. No source overlay, numerical retrieval, or current-source qualification.
- [x] MP1-E focused controller/native controls, related broader regression, fresh
  independent read-only review, seals/PS parse/VerifyOnly/wrong-seal-account guards.
  Local completion is tested/reviewed witness + input-only handoff, NOT actual
  membership proof, RC2 fix, RC3 lifecycle/ordered proof, Gate1/release/install.

After actual witness: outside child -> exact-runtime ownership repair and bounded
writer cancellation; all inside but survivor -> stronger design decision; all dead
writer alive -> pipe cancellation/handle ownership; no failure -> inconclusive.
Rollback leaves new unused artifacts retained; never revert user edits or repin
old contracts. Three evidence-changing failed cycles stop for reassessment.

MP1 corrective verification2026-10-25: initial25focusedPASS/415broader with7same
historical pin errors did NOT clear final review. Seven native safety findings
required correction, plus omitted resource-proof acceptance fields. Parent RED
9finalization and6resource-proof subtests precede their23/23GREEN. Native fault
controls now cover borrowed-root identity failure, local single-close, rejected
thread close error preservation, partial request losing the real blocked writer,
and close failure becoming an error receipt. Parent final33/33PASS with ResourceWarning
as error (23contracts+10native/fault cases), log12815af19929f2a52a9e00ff69b99d8eaf96b4196372450585c6cd3dcf9d63b2.
This checks MP1 implementation only: selected topology has NOT run; B/C actual
normal-runtime observations remain pending. Final broader/review/seals pending;
preparation still FREEZE and MP1 root absent. No host attempt has been consumed.

Superseding stable MP1 observation2026-10-26: final probe7598e119/native tests
1fa1db1f, parent34/34focusedPASS including11native/fault cases;424broader0fail,
7exact historical pin errors, no skips/exclusions/interruption, NOT green. Same
reviewer CODE SHIP at exact bytes, no Critical/Important code findings. New
input-only launcher5272ae81...2673bytes freezes helper2c87/probe7598/oldTC helper/
controller only. PS7 parse0/VerifyOnly/wronghash/accountrefusalPASS; PS5parse0 but
Fileload denied by agent script policy, no bypass. Separate exact input-only seal
and PS7-route review SHIP_WITH_CAVEATS, no Critical/Important handoff finding.
Use existing shell362a356c via absolute path, hash shell+launcher before VerifyOnly
and rehash both immediately before ONE actualrun; stop on child nonzero. Exact
PS5 command -> sealedPS7 File route observed VerifyOnlyPASS/wrongSID refusal,
no Python/output. This is input-only preparation, not selected-runtime clearance.
MP1 root/Inputs/runtime command absent. Local A/B/C implementation is complete,
actual normal-runtime B/C observations and D preparation remain pending. Local E
acceptance is complete WITH CAVEATS, not an actual membership result. Old TC1/
stack/CR3/C2 commands stay consumed; no old command retry or runtime launcher yet.

MP1 host preparation returned2026-10-26: Inputs175926bytes SHA
457fc256b81f52572695b787344cd5778f3bd06bdc14939b5416508ceeacf5a4.
Preparation is consumed; NEVER rerun it. Parent verified exact18key contract,
all7false flags, source629/629, helper/probe/TC1input/TC1receipt/HEAD and budgets.
Full666entry TC1 inventory walk is denied at normal-timing/tests/retained-temp/
owned-shutdown-proof-470z594_; full old private guard also denied. Both remain
HOST-PREPARED, not independently agent-compared, with mandatory normal-context
before/after verification unchanged. No inaccessible-file waiver or ACL workaround.

INTENT next within approved MP1: add only Run-Cleanup-Membership.ps1, sealed to
these actual Inputs, reviewed helper2c87/probe7598/TChelper883e/controllercce2.
Reuse existing launcher ancestry/hash/SID1001/nonadmin/exclusive-output pattern,
invoke only existing coordinator --sha256; no source/budget/test/helper change.
Observe PS parse/VerifyOnly, wrong-contract seal and actual wrong-account refusal
before Python/output; fresh read-only exact-handoff review. Then issue ONE new
normal-account native membership witness using sealed existing PS7 outer route.
Runtime remains UNRUN until actual receipt. Rootcause/fix/stage/Gate1 stay false;
no numerical retrieval, package install, Git/security change, deletion or retry.

MP1 runtime handoff cleared2026-10-26: new launcher3154bytes SHA
0738e9510cb114ae7617d296bd06794e018ac280c61d420a2c58f768e9eb5562;
parent PS7 parse0/VerifyOnly/wrong-contract seal/actualwrongSID/sealedPS7 File
route checks PASS before Python/output. Fresh native read-only final handoff
review SHIP_WITH_CAVEATS, no Critical/Important finding; independently629/629source
and retained34focused/424broader log/receipt hashes confirmed, seven historical
errors unchanged. D preparation/input review complete WITH private-read caveats;
full normal-context inventory checks remain mandatory before/after actual witness.
NEXT ONE normal non-admin MP1 witness via shell362a356c+launcher0738e951 rehashed
before VerifyOnly AND before actualcall, each child exit checked. Actual runtime,
membership result, RC2/RC3/stage/Gate1/release/install still unobserved/incomplete.

### SR — authorized shutdown repair continuation2026-10-26

AUTH: user said "start fixing , i will give some more idea for this fix" after
the three-reply assessment. This approves the bounded local repair sequence,
not old-command retries, selected-runtime execution from the agent, installs,
security/ACL changes, deletion, Git writes or qualification claims. Existing
Fable artifacts remain the only plan store. Additional user ideas are evaluated
against evidence, not blindly applied.

Actual MP1 is CONSUMED. Receipt9846bytes SHA
0a61222897b210c2500a5c461b7bacc5f00e296b4d2f5678a51f82b256c488d7
and all6 bound streams were verified. Membership child EXITED1, not a watchdog
timeout: capture_complete=true, timed_out=false. Incremental events pin the
root44532->relay43800->launcher35012->child19464 chain. Launcher and child remain
unsignalled after stop, writer remains alive, and primary stop error is
E_DISTRIBUTED_WRITER_STILL_ALIVE. Emergency kill+cancel succeeds jointly; it does
not prove cancel alone. Original historical C2 exception/pipe holder/escape
mechanism remain unproven. Probe-error omits observation_errors; pre-terminate
validation rejects a later historical-membership transition and prevents final
classification. Lifetime TotalProcesses is not current live ownership.

INTENT: replace timeout-as-cancellation assumptions with independent cancellation
and ownership evidence, preserve failure visibility and existing0.1/5/60/120/90
budgets. First correct interpretation without touching any sealed consumed file.
No-build preserves failure; cancel-only leaves leaked children; stop-time parent
PID scanning cannot prove complete lifetime ownership. Recommend a narrow
two-axis repair, with startup ownership verified before work and dedicated writer
cancellation. Overlapped transport remains a conditional redesign if synchronous
cancellation cannot pass the independent reader-alive test.

- [x] SR1: NEW .github/scripts/cleanup_shutdown_evidence.py and matching controller
  tests: read saved MP1 JSON/streams only, reproduce the current validator's bad
  transition, phase-aware reporting, distinguish complete nonzero capture from
  incomplete capture, retain raw records/errors and all readiness flags false.
  No overwrite/repin/re-execution of MP1 helper/launcher/Inputs/output.
- [x] SR2 (isolated controller-native candidate only): NEW knowledge_bridge/windows_writer.py and matching native tests:
  actual blocked synchronous writer, reader kept alive throughout cancellation;
  thread-owned native handle, closing/done state, bounded cancel/join, partial
  write/error handling, cancel races/1168, no stream close while writer lives.
  Candidate is not wired into retrieval until this axis passes; controller3.14
  evidence remains distinct from selected3.12. No extra shutdown budget.
- [ ] SR3: cause-supported exact-runtime ownership mechanism, then integrate
  cancellation and process exit separately; no stop-time ancestry sweep as full
  ownership proof. Any mechanism that cannot cover startup/deep-descendant gaps
  returns to design. New selected-runtime handoff only after focused/broader tests
  and independent review; never retry consumed attempts. Public initial/replay
  verification follows lifecycle proof; Gate1/release/install stay separate.

Immediate declared writes: SR1/SR2 new modules/tests, one exclusive retained
.github/run-artifacts/cleanup-shutdown-repair-20261026 root, and existing
design/plan/checkpoint/report/state. Before.json records18 target/control hashes,
HEADa38297d and dirty status; re-check each target before writing. Existing live
distributed/job modules, all historical helpers/contracts/source copies and
attempts remain unchanged during SR1/SR2. Existing broad baseline is424run with
0failures/7historical error records, not green. Retained runner scopes any allowed
test-owned temporary housekeeping; no old evidence deletion. Rollback means leave
new candidates unused and retained, never revert unrelated user changes.

Completion: meaningful RED->GREEN per axis; real reader-alive cancel and native
handle exit observations; regression compared against recorded baseline; fresh
read-only judge; explicit selected3.12 gap if unrun. Weak link: coverage of actual
Store/venv ownership. Cheapest falsifier: expected actual interpreter has verified
identity+membership before first request, then every required native handle exits.
Three evidence-changing failed cycles on one problem require reassessment.

SR1 observation2026-10-26: actual old-validator regression reproduced from saved
JSON only; RED15run14fail ->GREEN15/15, then fresh FIX-FIRST2 found incomplete
transition grammar and parent JS numeric round-trip in the first derived export.
Additional meaningful RED19run10failure records ->GREEN19/19 with unchanged test
expectations. Exact consumed-event grammar now rejects each deleted transition,
ordering/result/error/emergency mismatches; malformed input never yields a gap.
New Saved-Evidence-exact.json preserves all raw integer values; Python compared
it byte-for-byte to CLI after CRLF->LF only and structurally to the actual
function. Old rounded export is retained, marked faulty/superseded in report,
state and Artifact-Status.json. No original MP1 bytes changed. Same fresh reviewer
rechecked corrections and returned SHIP for SR1 only, no Critical/Important.

Final focused19/19 log477b2578a78904a28276001169b4c3336de79deb0040fa10a53bda8c345c5c56.
Final broader443run0fail/7exact historical errors/0skip/exclusions/interruption,
logc0c83772e9a2ea30daafd8e315549c318a62eb1a70cb95703af3b8be79a1bf0a;
not green. Existing lifecycle6/cwd7/budget7 controls PASS. SR1 is a read-only
interpretation/reporting repair, not historical producer authentication, actual
shutdown fix, native selected3.12 or stage completion. SR2 isolated tests first
retain5RED failures for absent writer candidate; implementation/reader-alive
native cancellation observation pending. All old commands remain consumed.

### SR2 superseding observation — isolated writer axis verified2026-10-26

INTENT: cancel the one synchronous stdin writer independently of reader death;
never turn a cancellation request, readiness notification or cleanup debt into
successful completion. New windows_writer.py remains UNWIRED to retrieval.
Its real duplicated thread handle has one owner: startup acceptance and worker
self-retirement compete atomically under the same lock. Late/unaccepted starts
cannot write or expose a worker-owned handle to cancellation/native waiting.
Unaccepted cleanup Python-joins first; no-handle pre-I/O outcomes explicitly say
native_thread_exited=false. Accepted I/O requires actual native wait plus join
before close. Raw unbuffered stdin is mandatory; buffered close cannot reflush.
Only cancellation requests may repeat within ONE absolute deadline, never bytes.

Observed RED->GREEN progression: initial5absent failures;8edge cases; Boolean
write-count RED12/1 ->GREEN12; review startup RED15/4 ->GREEN15; failed retirement
RED16/1 ->GREEN16; final ownership-handoff RED18/2 ->GREEN18/18, no errors, skips,
exclusions, expected failures or interruption, ResourceWarning-as-error. These
are different missing invariants, not repeated speculative production repairs.
Final native read-only judge: SHIP_CANDIDATE_WITH_CAVEATS, no remaining blocker,
exact writer72dde9c3a495f0326bf95a1eef25e2eb81ac1333921889a8e48656840f475d29,
testsf3f89b80864a909abb704007db24503d475575365a79f02e64fef006cd969b62.

Retained root remains cleanup-shutdown-repair-20261026. writer-handoff-green
Receiptcb47fea0b22f6e39ffbd01b0abe19c124302af58a731a233e20e53e04e9e3fe8,
logbf85c3f96b243e51ac663932c883d38218f9a0507e1f68f1228615ef1e6cddf2.
Run-Inputs.json binds parent-observed exact controller/source/tests/runner hashes,
receipts/logs and9unchanged Before controls; not producer authentication.
Final broader knowledge228run174PASS/54SKIP/0fail/error, log
e1615634bf25343859f19b51a5b978abe72e62686669b68b3cacd3b0a3d5855d.
Final controller443run0fail/7exact baseline pin errors, log
f86d6332d9ea4b3b6bb18439ba2805dea2025548df4a6105fc9ab2e19da854e2;
NOT green CI. First broad443/23errors retained:16fresh-fixture access refusals
were resolved using scoped tool grants, not code/check/ACL edits; no outputs
were removed. Existing lifecycle6/cwd7/budget7 also freshly PASS.

Single controlled real-pipe observation, reader ALIVE through native/Python join:
blocked setup0.109043600s (includes deliberate0.1s test blockage), cancel request
0.000198000s, exit/join check0.000181000s, reader-alive check0.000004700s.
Separate forced1168/WriteFile-gap cancel+join0.012150400s. Inclusive values are not
summed; these are controller3.14 observations, not selected3.12 or historical C2.

SR3 remains incomplete. Actual process ownership, selected-runtime lifecycle and
public initial/replay have not been repaired or qualified by the writer primitive.
No selected3.12, old command, package install, evidence deletion or Git action ran.

### SR3 launch-mechanism decision — design gate, not implementation authority

No-build retains leaked workers; stop-time ancestry scans or source-only
self-enrollment leave pre-bootstrap/deep-descendant gaps. Recommended next
feasibility design: launch the EXACT already-pinned loaded interpreter image
directly, preserve/re-prove the existing venv context and dependency identities,
and assign it suspended to the owned Job before resume. This changes the launch
contract, so obtain approval of this description before new launch code/handoff;
the earlier SR sequence does not silently authorize a different runtime identity.
It is NOT a new Python install, arbitrary same-hash executable or pin waiver.

Primary-source support is explanatory only: CPython3.12.10 PC/launcher.c redirects
venv launches; Modules/getpath.py consumes __PYVENV_LAUNCHER__ for executable/venv
discovery. Windows nested jobs describe inherited restrictive Job chains.
https://raw.githubusercontent.com/python/cpython/v3.12.10/PC/launcher.c
https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/getpath.py
https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs

Weak link: actual Store activation and exact venv equivalence are UNVERIFIED;
source semantics are one evidence family, not installed-binary proof. Cheapest
falsifier is one NEW reviewed normal-account identity/ownership-only witness,
no writer/numerical workload: exact loaded image/file identity, version/prefix/
base/venv, dependency metadata, nested child membership and independently pinned
native exits. If any identity drifts or a required process is outside the Job,
stop/re-plan; do not rebaseline, reinstall, add time or integrate the candidate.
Only after that proof can combined shutdown and public initial/replay qualify
the stage. Old private before/after preservation checks remain mandatory.

### SR3 approved implementation detail2026-10-26

AUTH: user said "WE ALREDY DISCUSSED ABOUT SOLUTION FOR THIS, USE ALL REQUIRED
SKILL AND SOLVE THE ISSUE" in direct response to the SR3 design gate. This clears
that launch-design gate and authorizes bounded local implementation/tests/review
and a fresh sealed normal-account verification handoff. Do not ask again within
this scope. It does not authorize selected3.12 agent execution, installs, old
attempt retries, security/ACL edits, evidence deletion or Git writes.

Code evidence: worker.py:153 creates DistributedClient(sys.executable) inside the
already-selected worker. Therefore use its CURRENT native loaded image plus
explicit original sys.executable/venv context; never guess another installation
from PATH/registry or accept a different selected executable. A stdlib pre-work
bootstrap must attest Popen-root PID/image/prefix/venv and Job membership before
the authored worker script runs. Assignment precedes resume. If activation or
identity differs, fail closed before request work, retain the failed observation.

Declared surfaces: NEW windows_owned_process.py, windows_owned_bootstrap.py and
test_knowledge_windows_owned_process.py; bounded distributed_retrieval.py wiring
and matching lifecycle tests; NEW shutdown_repair_verification.py, its controller
tests and Run-Shutdown-Repair.ps1; this existing Fable plan/design/checkpoint/state/
report, and exclusive new SR3 evidence under cleanup-shutdown-repair-20261026.
SR3-Before.json records current hashes/absent targets/dirty status before writes.
Existing windows_job.py and all consumed helpers/launchers/contracts/copies remain
immutable controls. SR2 writer bytes remain fixed unless a reproduced integration
defect requires a separately recorded correction. Do not change POSIX behavior.

- [ ] SR3a: failure-first current-image/direct Job ownership primitive; real root/
  child/grandchild exits and unrelated-process survival without any writer;
  actual-image/venv/selected-path mismatch refusals, partial startup and API-fault
  cleanup, nested Jobs and membership churn. Pin native handles and observe exit;
  do not mistake live lists/lifetime totals or Job-empty for all native exits.
- [ ] SR3b: combine owned process stop and SR2 cancellation using raw stdin and
  ONE existing5s cleanup deadline; preserve120default, original errors, no resend,
  no close/delete while ownership or writer shutdown is incomplete. Focused tests,
  relevant broader suites, exact nonpass comparison and fresh native final review.
- [ ] SR3c: one NEW sealed normal-account verification; mandatory old/private
  histories/source/runtime/preservation guards before/after. Identity first,
  ownership-only/combined lifecycle controls before unchanged public ordered
  initial+replay/lease refusals. Stop on failure and retain output, no automatic
  retry. This may close focused cleanup stage only; Gate1/release/install stay false.

Rollback: keep new candidates unused on failed feasibility, preserve failed output,
and re-plan on actual outside-Job process/identity drift. No blind process sweep,
timeout increase, package reinstall or silent check removal. An inaccessible
required old input still needs the normal account; it is never skipped.

### SR3 implementation/review observation2026-10-27 — same approved scope

SR3a/b implementation is complete and independently exact-hash reviewed under
controller Python3.14. Keep the acceptance boxes open until selected3.12 proves
the same behavior. No repeated design approval is needed. Current-image owner,
identity/venv bootstrap gate and SR2 writer cancellation are integrated. All
owned exits need pinned native-handle proof in addition to final Job/list/ledger
agreement; asynchronous accounting snapshots are not assumed atomic. Actual
worker script sibling imports and SystemExit behavior are preserved. Ownership,
cancellation and stream/constructor cleanup failures retain original errors,
all-close debt and unresolved resources; no deferred auto-delete hides failure.

Meaningful final reviews found and parent RED/GREEN closed assignment-failure
root survival, proof-gap termination bypass, bootstrap exit-code/venv-env false
refusals, close-error masking/debt loss, expired/unbounded gating/drain, failed
startup/stream-retention debt, script sibling-import loss and non-atomic snapshot
false refusal. No historical control, skip or larger timeout made these green.

Final current-byte observations: owner17PASS, session7PASS, combined12PASS,
handoff16PASS (real627file copy included); knowledge252run198PASS54existingSKIP,
0fail/error. Final controller459run0fail11errors0skip/exclusion:7historical pins
plus4old frozen membership diagnostic/private-API errors. Preserve all11 errors;
neither broad-green nor full-native/release/install qualification is claimed.
Independent final native/code clearance and exact helper/launcher seal review
allow ONE fresh normal-account SR3 verification, not an old attempt retry.

New verifier shutdown_repair_verification.py SHA
f224d215d0eb8ac898ac6a185cb388d1aa45b627765a006ae266455b800aff69;
Run-Shutdown-Repair.ps1 SHA
010305e3a8e75ad62c4b6fe4ef527203e31dabea16ca88f87f2c476c9944109b.
Literal10source/7support/6oldcontract pins plus mandatory old/private inventories
are checked before preparation/workload and afterward. Old private traversal is
still a normal-account obligation; no inaccessible input is skipped. Selected
runtime identity/53dependency checks occur before and after workload. All7groups
use selected worker:17owner+18writer+12shutdown+7session+6lifecycle+7cwd+7budget
=74controls; then original public ordered4modes, replay and negative leases.
No numerical success/source overlay or producer-authentication claim is added.

Actual existing sealed PS7 parse/VerifyOnly and wrong-SID refusal pass before
Python; SR3Inputs/preparation/normal output absent at handoff. Normal account
will create SR3-Inputs.json and exclusive sr3-prepare/sr3-normal once. Stop and
retain any failure; share Failure.json or Receipt.json, no retry. Only observed
allpass/preservation may close focused cleanup stage; Gate1/release/install stay
false. Existing public90/lifecycle60/default120/shared-cleanup5 unchanged.

### SR3 actual preparation stop2026-10-27 — access decision required

Normal account consumed the new preparation once at08:39:25Z. Mandatory full
history traversal refused old audit-emwso553 WinError5; no selected3.12 identity,
74controls, ordered public workload, SR3-Inputs or sr3-normal output was reached.
Claim/Failure are retained. Old helper/launcher exact hashes still match. Do not
reuse this consumed preparation or delete/rename its marker to force a retry.

Read-only descriptor diagnosis establishes cross-account evidence ownership:
fixture owner CodexSandboxOffline, protected DACL with only OWNER RIGHTS/SYSTEM/
Administrators. Parent grants to normal user do not inherit. All330direct sibling
fixture directories share this pattern; no complete recursive/history census.
This contradicts the assumption that normal account can read every sandbox-
created retained fixture. It does NOT refute shutdown code or establish a package
problem. Existing runner/mkdtemp0700 behavior explains why test fixtures persist
with a different access boundary from the parent evidence folder.

Options now: no-build keeps stage blocked; recommended smallest route is an
explicitly authorized read-only grant for normal account on exact affected old
test-evidence targets, with saved before/after ACL/content/identity evidence and
no owner/existing-ACE removal, write grant or global reset. Stronger alternative
is a separately designed two-account read/verification workflow without changing
old ACLs; that changes provenance/coordination and needs design approval. Simply
skipping unreadable history would weaken the approved guard and is not accepted.
Weak link: other protected descendants may also block normal traversal. Cheapest
next check is read-only exact-scope ACL/access inventory before authoring any
permission change. On any target/provenance uncertainty stop for scope decision.

No permission repair or successor launcher is authorized merely by this failure.
Ask separately before ACL changes; preserve consumed files and all runtime/code
seals. A later authorized recovery needs a NEW reviewed/sealed preparation,
never a rewritten old baseline, admin retry or broad permission command.

### SR3-COPY correction2026-10-27 — selected no-ACL route; adaptation planned

User identifies the already implemented/verified cooperating-account copy path.
This supersedes the ACL-repair recommendation above. Freshly hashed old H1
Copies.json39851134bytes956f2c50.../BEFOREBundle13247059bytes0def61c9... agree;
46010copied objects/27208file mappings merged into48799objects. Both maps lack
cleanup-repair-20261023/audit-emwso553; no old AFTER success is inferred. Current
SR3 history() lacks the corresponding data-copy transport for its newer roots.
Known failure remains normal preparation only, not a shutdown/package regression.

INTENT: replace direct-only access to restricted HISTORICAL EVIDENCE DATA with
complete, phase-bound fresh-original BEFORE/AFTER cooperation; preserve direct
authoritative source/runtime/helper/protected checks and known history baselines.
The existing design now contains full SR3-COPY description/acceptance. New helper
implementation waits for approval of this precise preservation-boundary change;
the user already selected no-ACL route, so do not ask them to choose ACL repair.
Do not repeat approval of the existing worker-shutdown solution or old W copying.

Compare: no-build/direct-only remains blocked; adapt existing staged exact-denied
copy/readback (recommended) uses current tested primitives and read permissions;
a persistent cross-account broker adds long-lived trust/lifecycle burden and is
not needed for finite BEFORE/AFTER sampling. Reusing old map as current evidence,
skipping denied paths and changing ACLs contradict coverage/user constraints.
Weak link is actual fresh two-account access/readable destination for new roots,
not package installation. Cheapest falsifier is one new exact denied fixture
capture plus normal byte readback after input-only approval. If both readers
cannot open it or normal cannot read the copy, STOP; no ACL/elevation fallback.

Approved-range candidate, ONE requested approval for all local steps below:

- [ ] SC1: new input-only copy adapter/tests, exact four history roots and old
  positive-baseline comparison, consumed SR3 failure pins, fixed source/helper/
  runtime identities. Preserve archive_copy_snapshot/archive_copy_h1/worker_copy_
  h1 and consumed SR3 code unchanged. New closed coordinator/tests/launchers only;
  no shutdown code changes. Reuse data-only primitive contracts, not old root/
  session/workload or old56hardlink whitelist. Failure-first stale/phase/coverage/
  source-drift/access/link/ACL-preservation tests and relevant regression check.
  Record exact source baseline before editing; independent review before command.
- [ ] SC2: separately sealed fresh BEFORE scan, existing-access data-reader copy,
  normal-account full content/mapping readback. Exact inherited-access destination
  outside all sampled roots; no ACL changes/deletes/overwrites. Direct source,
  runtime and authoritative guards remain live. All requested coverage resolves
  before any selected-runtime workload. Stop if either required reader fails.
- [ ] SC3: new reviewed runtime phase, unchanged74controls+ordered4mode method,
  original budgets and actual selected3.12. Result stays provisional and stage
  false. Fresh ORIGINAL AFTER scan/copy/readback, same-run/BEFORE/workload binding,
  complete maps/known-baseline checks and final independent raw-result review.
  Final sampled preservation plus runtime observations may close focused stage
  only; Gate1/release/install/producer/historical-C2-cause flags remain false.

Required falsification: changed/removed/added ORIGINAL after BEFORE even if copy
unchanged; tampered/missing/extra/partial copy; stale old-map/wrong-root/phase;
denied both sides; no-BEFORE workload and no-AFTER finalization; direct source/
runtime guards not routed through evidence reader; unexpected linked fixture;
changed readable/unresolved partition; byte/identity/permission mutation; phase
reuse and overwrite. Old9/8controls and actual historical baselines stay intact.
Runtime capture uses fresh selected interpreter, no source execution from data
copies. Completion is sampled agreement, not continuous/atomic/authenticated data.

Rollback: retain new inactive candidate/failed outputs, preserve consumed attempt
and old successful H1 copies unchanged. No deletion or reverting unrelated edits.
No new copy, worker command, source edit or ACL operation ran during this plan.

SC approval2026-10-27: user "start" approves SC1-SC3 as the named bounded range
in the immediately preceding answer. No repeated approval for this adaptation.
Execution uses Fable native Terra-high for new shutdown_copy_data.py/test data
layer; parent owns shutdown_copy_verification.py/test coordinator, new launcher,
verification and records. These NEW files were absent at baseline; old snapshot
77c98066...,H1reader8e66fa51...,SR3helperf224d215... remain immutable. Current
dirty source/HEADa38297d and prior459/11controller baseline are retained. New
test output only sr3-copy-development; new normal session proposed fixed root
Documents/Codex/sr3-copy-20261027-4a52cd8d (absent), session
4a52cd8d336b40c29587dfb5ece35522. Record exact self/dependency seals before issuing
any staged command. No selected3.12 from agent; actual cross-account BEFORE and
AFTER remain human/reader cooperation gates, not synthetic-test claims.

SC direct-authority amendment2026-10-27: current checkout independently observed
f63f62496f82fb479e352bdd9c90accf9f869e8b, immediate child of pinned evaluated source
a38297dd797eeecd25e41ab0af1df4e3db8fa984. Four A-only changes are existing C1
launcher/preflight/test/report. Old SR3 source_basis correctly refuses E_SR3_HEAD;
no actor/cause of this Git change is inferred. User explicitly answered
"Approve the exact transition" to the precise async question retaining a382+
approved repairs. NEW helper may verify ONLY that checkout SHA, single parent,
exact four additions/modes/blob SHA256s and live byte agreement; then reconstruct
the original627-file a382 tree with original10named deltas. Record both checkout
and evaluated-source heads. Unknown SHA/parent/extra/missing/mode/blob refuses.
No old constant/guard/contract or Git state changes. RED17run/2fail captured at
coordinator-checkout-red-07 before implementation. This is the only new authority
predicate; all other direct mandatory checks remain executable.

SC1 execution2026-10-27: DATA layer12PASS; coordinator20PASS; broader copy106PASS,
0nonpass. Retained RED20/3fail policy gaps then GREEN20 at sr3-copy-development/
coordinator-policy-{red-08,green-06}; GREEN log4ba25cdae5493c014ced4c229ea21c3c9e5584449ca4b8187814ff9c2e7efee5.
Copy-regression02 log9666e18493d17532d4a1c6e2f1ae15299097bfa06e1279029636e6f563affdb7.
Review additionally requires complete authority-derived protected identity list
and immutable strictRequest->unapprovedProposal->externally sealed normal
PolicyInputs/PolicyRequest lineage before copy. Implemented with blocked base
copy and direct-authority/readable-partition rechecks, no old56path reuse.
New source-reader inspection does not copy, bind approval or start a worker.

Current normal session remains absent. Finish full regression/final exact-hash
review and launcher negative checks before issuing BEFORE-only normal command.
SC2 requires actual complete original coverage/copied-byte readback; SC3 requires
actual selected3.12 runtime plus fresh ORIGINAL AFTER and independent final
raw-result review. Synthetic full phase fixture explicitly mocks workload and
positive-history gates; it is NOT actual runtime/history qualification.

SC1 boundary2026-10-27: final coordinator21PASS (real denied hardlink pair
proposal/bind/copy/readback/ACL-preservation + protected-ID rejection); DATA12,
copy106PASS. Full shorter controller492run0FAIL12ERROR0SKIP, log
270736b1864cd23a2bf6a227517cafe700c5d8f578e11786d965937612442ce2.
The12 are4old membership probe CurrentImageOwner.handle errors+8historical
source/HEAD pin records. Initial491run2FAIL24ERROR retained; unchanged timing23
and gate23 PASS from shorter test output remove long-cwd/scratch contaminants.
No old test/source guard changed, skipped or relabelled green. Fresh parent
21fixed source/control/old-input seals match, and new normal root remains absent.

- [x] SC1 implementation/focused controls/final input-only native read-only review.
- [ ] SC2 actual normal BEFORE request, reviewed policy/copy/byte-readback.
- [ ] SC3 selected312 observation, fresh ORIGINAL AFTER and final result review.

Independent final exact-hash SHIP: one normal non-admin BEFORE input action ONLY.
Coordinator234dd24e90a33feeee9fbacd5e75f03b2099c8393b7be86d3d9f994d99946cd3,
DATA4fa0afdaa1219b243421717eca9a8d2939c4f653a8d9b27110e2b63c80e27299,
launcher5554f4b3d45514262f2e497636642e435f2c535f9249957fdede7073c45ea7e1.
PS7parse0/VerifyOnly/actualSID1003-refusal and wronghelperseal-refusal observed
before Python. Outer command must hash existing PS7and launcher beforeVerifyOnly
and again beforeone invocation; no automatic retry. Review actual Inputs and
Request before separately sealed source-reader inspection. User range approval
remains valid; next observation is human-account cooperation, not new design
approval. Final stage/Gate1/release/install and all oldconsumed flags unchanged.

SC2 actual BEFORE2026-10-27: user executed exact frozen normal command once.
Inputs596109bytes49f19acc752bb0b97594db194873c1f3f994212edca3dc7ba1af50021094b21a;
Request1227544bytesc81c2d9b095c108893dee9fe0b10ce625462d3b736e2a41c3782eca5aac70e42.
Parent/independent actual validations pass;1379complete protectedIDs;1240denied
directories retained. Independent read-only metadata traversal of exact denied
coverage found1800directories/4396files,0errors/redirects/protectedhits/hardlinks;
this is feasibility metadata only, NOT completed content inspection or copies.
Narrow review SHIP one source-reader InspectBefore; parent started frozen exact
helper with both external seals. Existing-access inspection Claim consumed;
wait/review actual unapproved proposal, never repeat it. SC2 copy/readback and
SC3 selected312/AFTER/final review remain incomplete. No old command or ACL edit.

SC2 reader inspection completed once exit0. Proposal225555bytes SHA
dce8bda736214950bc69e63d585027a750982789ae4ca69e9062f66bbd78b1c5;
all4exact allowlistsEMPTY, each1379protectedIDs. Actual request/protected-policy
validators pass and baseInputs/Request exacthashes unchanged. No evidence copy
or worker ran. Approx claim-to-proposalmtime97.865s, not CPU/import profiling.
Exact source-reader content inspection is now observed, not inferred from old
H1 copies. Intended normal BindPolicy unused: wrongSID refuses beforeclaim;
outer wrongproposalhash refuses beforePython. Inert exact handoff text retained
SC2-Bind-Command.txt SHA4cc4e3c7f96744647d32d5d0b19e2646ee14ebbd3fc7dd6c382f24bf6dcc85ae,
parse0/singlePythoncall. Await actualproposal/exactcommand narrow review before
issuing. No implementation changes; historical/Before/Inspect consumed outputs
fixed. Only after reviewed normal childbind output may source-reader copy start.

SC2 binding handoff reviewed2026-10-27: actual proposal canonical/schema/session/
root/request/protectedIDs validated,4EMPTYallowlists; fresh original direct
authority equals sealedInputs. Independent substantive audit SHIP preceded a
workspace-credit FINAL error. New user "continue from you left" resumed SAME
reviewer, which finalized narrow SHIP for exact4cc4e3...block. No new code or
repeated operational phase. Clearance ONLY ONE normal non-admin BindPolicy,
not copy or runtime. Command pins6roleSHA256s, refusesexistingoutputs, calls
one frozen Python314 mode. It rechecks normal context/directauthority/visibility
and fresh scan, writes exclusive childRequest/Inputs. Confirm resulting actual
childhashes and complete base/proposal/empty-policy lineage before copy review.
Residual same-root hostile-concurrent-writer race is not atomic-proof; nothing
may be called continuous/producerauthenticated. Existing before/inspection
outputs remain fixed. Parent final unchanged rolehashes/HEAD and absent next
phase outputs verified; normal action awaits human-account cooperation.

SC2 normalBind observation2026-10-27: user ran reviewed block once successfully.
ChildInputs822007bytesc91235f95b135a1e170893513d3105095fb5dd39feef268eb3b2fec3c4cd3180;
childRequest1227544bytescd5ce65e48f7a604fb577279e9dea3ab8e8c30bfbddf907c1ab222f5c6b476ff.
Parent actual frozen session/lineage/request/policy validators pass. Original
Inputs/Request/proposal hashes unchanged, readable/unresolved partition stable,
1240denied dirs/1379protectedIDs/0exceptions. CopyClaim/output/Bundle/run absent.
Baseline in SC2-Copy-Before.json; native read-only actual-child/CopyBefore review
requested before real source-reader copy. Next normal full-copy readback must
execute old positive history guards before Bundle publication. No source or
helper changes, ACL/install/Git/delete/retry or selected312 action.

SC2 copyexecution boundary2026-10-27: SAME native read-only reviewer validated
actual child canonical/config/lineage/root/policies/partition/directauthority
and absent nextoutputs, returned FINAL SHIP ONE SID1003 nonadmin CopyBefore.
Parent rechecked exact controller/helper/DATA/base/proposal/child8role hashes,
SID/nonadmin and absent CopyClaim/Failure/reader-copy/Bundle, then started only
CopyBefore once. ExclusiveClaim and new destination now exist; original data
read/copy/readback/source-stability validation is running. No normal VerifyBefore
or workload chained. Await actual result and separately review raw aggregate/
perroot copies and unchanged inputs before handoff. On failure retain partial
output/Claim/Failure, never delete/retry or change ACLs. SC2 is not complete until
actual normal copiedbyte readback and historical positive guards publish Bundle.

SC2 actual copycompletion2026-10-27: exact reviewed CopyBefore completed ONCE
exit0. Outer1283bytes SHA f9a38306ee2e4bf351e5d824932e92d486e736668de596cf8bcf223cf78d3b7b.
All4root manifests bind the sealed childRequest/policies/session/phase. Parent
actual session/outer/H1manifest/mapping/coverage validators pass; directauthority
unchanged.1240deniedtargets ->4396filecopies/33362733bytes; no linked exception.
Three roots have0deniedtargets; normal-readable originals remain mandatory.
Normal byte-readback and old positive history guards NOTYET observed; Bundle
absent. No selected runtime. Inert VerifyBefore-only outerblock45a860e33fff4e6670a470ce87014e61a30a50c282519e6dd7b58961849c8089
has13pins/exactnormalSID/nonadmin/absentoutputs, parse0/onePythoncall, realwrongSID
refusal and inmemorywrongcopyseal refusal. SAME independent FINAL review SHIP
ONE exact normal VerifyBefore block:4manifests valid, no merged overlap and
manifest-only timing/stack/1339CR3 positive baselines satisfy. Actual normal
bytes/readablepartition/directguards/positivegates remain required. Review the
returned Bundle before separately sealing Run. No implementation/test/oldhistory
changes; keep all consumed outputs. Runtime+freshORIGINAL AFTER/finalreview
remain later gates; focusedstage/Gate1/release/install false.

SC2 actual normalreadback2026-10-27: user consumed exact VerifyBefore once,
status SC_BEFORE_VERIFIED_NO_WORKLOAD. Bundle3092807bytes
29fba89ef123eb5c4e9df957f0bbfacad58328301787658dfc42a95356a81019 and
VerifyClaim161bytesb7b9a11ed7a30c4e3f5f07f28034db63cb650521ae19b70e439e0bd567d372b4
matched locally. Exact allfields derivation from sealedrequests+copyrecords
passes;7345files/94513658bytes/nooverlap, directauthority unchanged. Normalbyte/
visibility/oldpositivehistory gates precede exclusiveBundlepublication. NoACL
BEFOREaccessblocker closed. SC2BeforeBundle observed, no qualification inferred.

SC3 next candidate Run-only block8f64b8490972e048fe6e0b649d71f8b40f5a9a40004ee7d6e175d2d734c22bf0:
14pins/exactnormalSID/nonadmin/absentRunoutputs; parse0/oneRunPythoncall,
actualwrongSID beforePython and inmemorywrongBundle/consumedclaim refusal.
Same read-only reviewer auditing actualBundle and runtime adaptation/finalblock.
Selected312 remains unrun; noRunClaim/contract/run/AFTER/Final. Approved74controls
and retainedpublicorderedmethod only; no oldcommandretry. SuccessfulRun must
remain provisionalstage/preservationfalse until freshORIGINAL AFTER/copy/
normalreadback/comparison/rawreview. No source/helper/test changes thisturn,
no repeated suites or oldhistory mutations. Broader492/12knownerrors NOTGREEN.

SC3 exact handoff FINAL read-only review2026-10-27: SHIP ONE full8f64b849...block
normal1001/nonadmin Run-only. Actual canonicalBundle/disjointexact4root unions,
all14seals/exclusiveoutput guards and source/runtime/history adaptation verified.
Only exact4root DATAinventory+CR3DATAsubmanifest substituted; originalsource/
runtime/dependency/protected/positivehistory guards remain. Executedsource627a382
+10deltas, exactf63transition only. Runtime74noskip/noexclusion controls then
unchanged4modepublicinitial/replay/lease, identity/deps pre+post; provisional
receipt forcedfalse pending ORIGINAL AFTER. No realphase/selected312 inreview.
Issue ONCE; rawcontract/receipt/counts/streams/discovery/publicresult review
before anyAftercommand. No retry/permission/package/Git/Gate1/release/install
clearance. Detailed SC3-Handoff-Review.json retains observedchecks and caveats.

### SC3 consumed failure and bounded SR4 proposal2026-10-27

Actual SC3Receipt10011bytesbeab04ef2dde95a01cc25ed21eedf6ff79c3e50c2aceacaf2cd2f74dc4fc76d2
is FAILED, not pendingAFTERsuccess.17ownership tests3.424s/9errorrecords; all
maintraces bootstrapBASE_EXECUTABLE; no timeout/capturegap/skips/exclusions.
Identity+53metadata dependencychecks passed. Remaining6groups/public/AFTER
unreached. Parent verified all4rows/8streams/receipt/log/source/contract bindings.
Consumedroot remains immutable; existing snapshot cannot be relabelled AFTER.

TARGET: strict valid currentStore-image startup AND bounded proved shutdown on
startupfailure, preserving budgets/ownership/identity and all old evidence.
FACT: launch_current expectedbase=image. OBSERVED: basecheckrejects child;
parent basealias and loadedStoreimage are different exactroles in passed probe.
UNKNOWN: child's actualbasevalue absent from shortfailure output and private
fixture unreadable1003; WinError31/5 cleanup exactnativefailure cause unknown.
INFERENCE: roleconflation is likely blocker; rootpin-after-ready creates a
potential earlyexit ledger gap. Neither inference is a completed repair.

Options: no-build retains honestfailedstage; simple role-aware bootstrap and
existing nativeledger correction is recommended AFTER causal controls; stronger
persistent supervisor/broker redesign changesarchitecture and remains outside
defaultscope. A one-lineblindbase substitution/removedidentitycheck is rejected:
would assume missingchildvalue and leave failed-startcleanup proof unresolved.
Reinstall/ACLchange/budgetincrease/sleeps/suppression do not address the evidence.
Evidencefamilies: actualonehostrun (all9traces correlated), implementation+old
roleawareprimary code, retainedtestcoverage. No independent runtime repetition.

Approved SR4 scope: AUTH user said "aprove" to SR4-D1–D3 on2026-10-27.
Approval supersedes earlier pending text; execute sequentially without another
same-scope approval gate. No consequential outward operations included.
- [ ] SR4-D1: controller-side deterministic/fault/native-stdlib RED/GREEN before
  newselected312 observation. Separate expectedbase from actualimage using
  attestedparent sys._base_executable, keep exact loadedimage/venv/prefix checks;
  exclusively record bounded tokenbound expected/observed identity on failure,
  and keep authoredwork gated. After suspendedprocess assignment but BEFORE
  resume, pin root membership/creation/image through existing Popenhandle or
  ownedduplicate. NEWrootnotifications idempotent; trulyunknownexit stillerror.
  Track suspended-unassigned/assigned-not-resumed/resumed startupstates; native
  stop/wait state-specific, same5s, no broadPIDkill. Fastidentityfailure must
  preserve primaryerror plus named nativecleanupoperation evidence, and may not
  claim success without signallednativehandles+emptyownedjob. RequiredREDs:
  distinctvalidroles/wrongrole, earlyEXITwithoutNEW for pre-pinnedroot,
  assigned-not-resumed failure/noauthoredwork, immediatebootstrapfailure,
  unknownnonrootexit, releasebeforeproof and unrelatedprocesssurvival. Existing
  SystemExit/import/deadline/membership/writer/session/lifecycle controls retained.
  Expected surfaces windows_owned_process.py/windows_owned_bootstrap.py and
  corresponding tests, newsuccessorhelper only as needed; no oldfrozen edits.
- [ ] SR4-D2: independent exactsource/test/seal/output review, then ONE NEW
  normal selected312 ownership/startup observation only (no retrieval), with
  fullchildidentityframe and cleanupstate. All17originalownership IDs PLUS new
  regression IDs must pass, zero failure/error/skip/exclusion. Discover/freeze
  updated exactIDs/counts instead of deleting newcases or pretending total17.
  Stop on failure; no retry or unknownrole allowance. Actualchildbase unequal
  to attestedparent expectedbase reopens model before more changes.
- [ ] SR4-D3: only after D2 resultreview, freshreviewed newsealedfull successor,
  exactnewdelta contract/sourcecopy and new runtime session. Preserve ALL74
  original controls PLUS addedregressions; new exactcounts/IDs explicitly bound,
  unchanged retainedpublicmethod, originalBEFORE/AFTER content/identity/permission
  samples, noACL copycooperation as needed, rawreview before focusedstage.
  One new fullrun, no oldmarker/input/root retry or replacement. Gate1/release/
  installation still separate; normalhost cooperation remains necessary.

SAME independent read-only cause/design review FINAL FIX-FIRST endorses this
smallestcomplete option, not identity-only patch. Primarycontract roleconflation
confirmed; earlyexit ledger weakness visible, exactWinError31/5 call unknown.
No code/probe/selectedruntime/copy/ACL operation in review. Review is design
evidence, not approval or runtimeclearance. SC3-Cause-Design-Review.json retained.

WEAKLINK: actual failingchildidentity value is unknown and cleanupcause not
captured with nativecall context. CHEAPESTFALSIFIER: exactchildidentity evidence
plus stdlib fast-exit ownership regression, no package reinstall. PIVOT: if
these refute rolemismatch/latepin hypotheses, stop and use observedcause; no
speculative repair. CONFIDENCE: high in failingpredicate and no-timeout result;
medium in proposed mechanism until controls run. STOP: inaccessible mandatory
evidence or unownedprocess requirement. No sourcecode edits/newtest/workload,
runtime retry, install/Git/ACL/delete action authorized by writing this proposal.

SR4 execution baseline2026-10-27: userapproval now authorizes the named local
range, not oldRunretry. Before edits parent verified currentHEAD f63, dirtytree,
live module/test hashes and exact matching failedrun/source old module copies.
Baseline .github/run-artifacts/sr4/Baseline.json. D1 live two modules + newowned
startup test are exclusive implementation surfaces; old17casefile/helpers/
attempts untouched. Controller314 RED/GREEN/native stdlib controls precede D2
helper freeze and fresh independentreview. No selected312 invocation from agent
account. D2 ownership-only success before D3 fullrun. No OS ACL edits.

SR4 controller observation2026-10-28: the interrupted native draft was retained
and parent completed D1 corrections. Original17ownership source remains exact
00c837f55f8527cefe361c5421155b2b8a4e51b177296506b9f249613eb223c4.
Required new fault/native controls are21cases:38total focus PASS, no skips or
exclusions, parent-d1-green-08. New D2 verifier22guard tests PASS. Relevant
knowledge273run/0failure/0error/54runtime skips; fullcontroller514run/0failure/
12old diagnostic/API/source-HEAD pin errors/0skips NOTGREEN. No old guards were
edited to turn those errors green. Red and intermediate failed candidates are
retained; their directory names are not success claims.

D1 candidate exact three hashes are ownerd9f8cf4a2f72db3f320252617982f160e9646b8254860498e2e288eaed2c94e4,
bootstrapa7fa933c35d919e6c730ff58b4634315b5afc05b2917d5c520ab5d5a990e086e,
newtest1cf10aa195798ed4e10792a8bdbb4cb3b449c216524bbfa9858220abb91d8978.
D2 candidate .github/scripts/shutdown_startup_successor.py binds all38IDs and
627a382files+11revieweddeltas. Read-only contract and real636file extraction
verification passed. Normal destination sr4-owned-20261027 remains ABSENT.
No selected312/Prepare/Run. Exact outer block is a review candidate in
.github/run-artifacts/sr4/SR4-D2-Command.txt; NOT ISSUED until native final review.
D2 intentionally observes ownership/startup only; it verifies original source,
runtime/protected inputs and consumed SC3 critical records directly, without
reusing unreadable private archive data as a preservation verdict. D3 retains
fresh ORIGINAL BEFORE/AFTER plus existing-access no-ACL copy cooperation for
all required newer history. D1/D2 final independent acceptance is pending;
checkboxes above stay open until that evidence arrives. User approval persists.

SR4 final review2026-10-28: independent read-only native Sol SHIP exactD1andONE
D2ownership/startup hostblock, noCritical/Important. D1checked above based on
38focusPASS/original17bytes/21newcontrols/broader evidence and actualdiff review;
it is not selected312runtime or completeworker-stage proof. D2 remains unchecked
until the host observation is received and reviewed. D3 remains separate/full.
Final helper self-description corrected only; final22guard PASS. Exact outer
block SHA476e012fe1a923d8309dab15e75c1e5966f9889916c75405d9fee36f842dc3e5;
helperd845e107...; expectedInputs319d71ed...281611bytes. Reviewer independently
recomputed contract and all38loggedIDs/order/pins; normalroot absent, noactual
phase/selected312 inreview. Low test-quality caveat: ctypesobject/int inequality
does not prove numericdifference; realDuplicateHandle source is verified, so
not a blocker for exactD2. No mid-handoff reseal for that cosmetic strengthening.
Read finalcheckpoint for command/result gate. All fullqualification flags false.

### SR4 actual D2 failure — reopened ownership design, approval pending2026-10-28

User executed the ONE authorized exact D2 block. It is now consumed/failed;
never retry it or proceed to D3. Actual38cases10.874s:36PASS/1FAIL/1ERROR,
0skips/exclusions/interruption/timeout/captureloss. All21new regressions pass;
actual selectedchild identity roles match. Original nested-fixture PID read is
empty; original tree assertion independently observes WAIT_TIMEOUT258 after
owner.stop/native_exit_proved=true. Child ORgrandchild is affected; the generic
loop does not identify which. Main raw/source/stream checks and independent
judge agree FIX-FIRST. D1 checkbox reopened: controller work remains observed,
but its promised complete-descendant boundary is contradicted under selected312.
There is no production-code change or test edit in this result review.

TARGET: identify the precise descendant ownership/exit discontinuity and repair
the independently confirmed readiness publication race without weakening native
exit assertions or changing old evidence. A diagnostic's completion criterion
is complete per-role evidence, NOT a passing stage label or an automatic retry.

EVIDENCE: one normal-host runtime family (receipt/unitlog/4commands/8streams and
its copies), implementation+fixture source, and independent Microsoft API
contracts. The independent review shares the first two families, not a third
runtime witness. Source/636files/38IDs/order/current protected guards verified;
one-root positive frame does not prove descendants. Failingcase ledger and
per-role membership/image/creation/wait data are UNKNOWN, not fabricated.

| Option | Mechanism / main failure mode | Assessment |
| --- | --- | --- |
| No build | Preserve failed state and keep D3 disabled; exact cause remains unknown | Safe baseline, does not solve issue |
| Bounded causal diagnostic plus atomic fixture publication | Observe exact role handles, membership and launch paths; repair only complete-marker publication with all assertions retained | Recommended smallest next milestone; may still return an inconclusive mechanism |
| Controlled descendant supervisor plus explicit unsupported-profile fence | Route every supported descendant creation through a pre-assignment owner and refuse unproven paths | Potential later architecture; larger contract/maintenance cost and speculative before evidence |

RECOMMENDATION: the bounded diagnostic. A larger supervisor or silently treating
the independent wait failure as an allowed environment error is rejected now.
Generic nested-job omission is not an explanation: Microsoft's nested Jobs/PID
list/accounting contracts include child jobs. The current leading inference is
a Store/venv alias/broker boundary outside the inner Job, not a confirmed fact.
No package reinstall is supported by the passed identity/dependency/startup
observations, and 10.874s was not a watchdog timeout.

NEW proposed scope requiring approval (not a repeated D1–D3 approval request):

- DR1: controller-only failure-first publication controls and a strictly test-
  fixture-only atomic temporary-file/rename publisher correction. All original
  17 test IDs/native assertions survive; old consumed copies/hash00c837f5... stay
  immutable controls. Changing the LIVE previously frozen17file requires this
  explicit authority and a new hash, not an in-place old guard/contract edit.
- DR2: one NEW reviewed/sealed normal-account diagnostic session, not old D2.
  Use a fresh source/output and stdlib-only root/child/grandchild fixtures. Keep
  the original selected executable/Store image/venv bindings; compare the
  sys.executable alias path and a same-pinned-image controlled launch where
  identity can be preserved. No alternative interpreter or environment install.
  Retain each role's PID, creation time, actual native image, executable/base
  identity, exact inner IsProcessInJob, completion events, ledger, PID list and
  accounting before/after stop. Record EVERY per-role native wait instead of
  ending at the first failed loop assertion. Preserve 5s shutdown and60s watchdog;
  no arbitrary sleeps, larger budgets or automatic retry. Exact-handle bounded
  emergency cleanup is limited to proven freshly diagnostic-owned processes;
  uncertain provenance/access is an error, never authority for a broad PID kill.
  Record outer containment separately where safely observable; don't claim it
  substitutes for inner ownership. No retrieval/model/native DB operation.
- DR3: raw result review and causal recommendation. If a role is outside the
  inner Job, return with evidence for an explicitly controlled launch/fence
  architecture decision. If all roles are inside but native exit remains false
  after owner success, repair only the demonstrated observation algorithm under
  a separately reviewed implementation. Inconclusive means inconclusive, not
  ownership passed. D3 full qualification is held until a new full ownership
  successor actually passes every original assertion plus added controls.

WEAK LINK: no failingcase per-role owner snapshot survives from this D2 run;
the original proof artifact was written only after the failed assertion. The
private marker read is SID-denied1003; no ACL/account workaround was attempted.
CHEAPEST FALSIFIER: exact same-run per-role IsProcessInJob/creation/image and
native waits, with a controlled same-image launch comparison. PIVOT: inner-
member=true versus false selects observation-algorithm versus launch-boundary
work; no reproduction does not select either. Feasibility must preserve exact
handles and avoid unrelated processes. Outside-view evidence: controller314
green did not predict this Store312 shape, so another opaque full suite has low
information value. Pre-mortem: diagnostic-only all-pass labels or omitted roles
would repeat the same false proof; require complete raw role records instead.
CONFIDENCE: high in measured failure/race/proof contradiction; medium in the
Store/alias mechanism hypothesis. No calibrated probabilities invented.

STOP: no new diagnostic helper, fixture/source edit or selected runtime until
this changed scope is approved. No oldattempt/baseline/input overwrite, reinstall,
ACL/security/Git action, old-data deletion or unsupported blanket kill. Existing
no-ACL cooperating-copy preservation remains the later full-stage requirement.

### DR1–DR3 approved execution baseline2026-10-28

AUTH: user said CONTINUE directly after the explicit narrow diagnostic plus
atomic-fixture correction approval question. This approves DR1–DR3 described
above, not an oldD2retry or a speculative production/supervisor redesign. Do
not repeat approval inside this range. Separate exact-checkpoint question was
answered "Approve this exact checkpoint transition": fee69861e1f94c54721e5eb773633f9b1d6f9fd3,
direct child of f63. Read-only Git evidence shows saved repair/helpers/tests/
failed-result campaign checkpoint, not an unreviewed new runtime. New verifier
may pin ONLY that exact checkout; evaluated source remains627a382 plus sealed
repair bytes and the explicitly approved fixture-only change. Old guards stay
unchanged and may continue refusing newer HEADs legitimately.

INTENT: replace only the incomplete nested-PID marker publication boundary with
temporary-file/rename atomic publication; every original17ID/native assertion
remains. Keep original00c837... bytes in immutable D2source as control. No
production windows_owned_process/bootstrap changes are approved by this step.
Build only a new bounded witness that reports per-role inner membership and
native exit for alias versus same-pinned-image descendant launch paths, preserving
all identities/budgets and fail-closed cleanup/provenance. No oldflow gets rerun.

Baseline hashes/mtimes/currentdirty inventory were inspected before writes;
record .github/run-artifacts/shutdown-descendant-20261028/Baseline.json. Parent
owns live fixture publisher/new fixture tests/new coordinator and Fable context.
Native Terra owns only new shutdown_descendant_probe.py/test counterpart and
fresh retained probe outputs. Native Sol performs read-only architecture/final
review. All actors preserve concurrent user changes and consumed attempts.

DR observed checkpoint2026-10-28: parent now owns final probe/test sources after
Terra's partial candidate. Atomic2/original17/startup21 PASS; knowledge275run
221PASS54existingSKIP0fail/error; real637filecopy verified. New focused combined
26/26 PASS (probe15 + coordinator11), including real controller314 alias/image
fixtures and separate outer captures/PID binding. Original selected312 remains
UNRUN; source owner/bootstrap unchanged d9f8/a7fa. All consumed history retained.

Final independent probe/seal review NOT_PASSED: native reviewer returned workspace
out of credits after clearing atomic correction and coordinator structure.
Parent closed remaining bounded evidence/schema/cleanup issues with observed
RED/GREEN; final new bytes still need native review. Candidate read-only authority
build361923bytes SHA0cabf116954056619fb3ebdb6fa0a2ddc5d1fa8f579cb2d0fd77f5d6d7c283fd
passed source/runtime/protected/oldD2 critical guards. Launcher stays deliberately
FREEZE_AFTER_REVIEW; no command issued, no normalroot/claim/selected312 created.
Next is final review then exactsealed ONE already-approved normal diagnostic;
no repeat scope approval, no oldD2 retry, no D3 qualification or speculative
production ownership edit. See shutdown-descendant-20261028.md report.

DR final reviewed handoff2026-10-28 supersedes the unavailable-review statement:
same native reviewer resumed, required and cleared bounded PEP678 note capture.
Observed note RED then combined27/27 GREEN,16probe+11coordinator. Final candidate
361923bytes SHA965ad98ef311051c052ee87262bb6e35e580c8baec4a81a6ce9f7fabd267be8e
was independently rebuilt; six external seals and both actual PowerShell files
verified,0parseerrors, normalroot absent. Verdict SHIP EXACT ONE new normal
descendant diagnostic only. Issued DR-Diagnostic-Command.ps1
SHAbdb9322f0357fd4073eb4400153349dd135b417ad3cb556c640cb2484d575fe8;
launcher d6a3eea98ba8fabb1dfe427cfb72cc085deac1bdef315799a4210f150abed6be.
Agent1003 VerifyOnly correctly refused before Python/output; normal VerifyOnly,
Prepare/Run/selected312 remain UNRUN. Preserve actual output and then judge raw
receipt/roles/source/protected/runtime before any new repair conclusion. No
same-scope approval repeats, old retries, production edit or D3/fullstage claim.

## DR actual result and proposed RP1–RP3 recursive launch repair2026-10-28

DR1–DR3 evidence gathering is complete. Normal attempt consumed; NEVER rerun
DR-Diagnostic-Command.ps1. Receipt136045bytes SHA
54782c5c8e81dc751b4a4630272b2c067ede4720a4123993d7ca27f379aa3e21.
Parent and independent native judge verified6command records/12streams, both
Probe/stdout/main-report bindings,637source files,53dependency versions and
matching before/after runtime identity except per-command cwd. Fresh read-only
direct source/runtime/protected/old critical guards PASS. No workload rerun.

Alias route: root32528 inside the exact inner Job; child23492 (launcher32148)
and grandchild4908 (launcher16216) outside it. All four descendant interpreter/
launcher handles were alive immediately after owner.stop. Job accounting and
owner proof covered exactly1root. Diagnostic emergency cleanup reaped those
four proven handles, and closed all resources without debt.
Image route: root2356/child20564/grandchild45100 all inside the Job, accounting3,
proof records3; every independent native wait signalled immediately after stop.
No emergency termination. Both arms used the same native3.12.10/venv/deps.
Native actual-result verdict FIX-FIRST: the selected venv-launch route crosses
the inner ownership boundary. Exact internal Windows activation/broker cause,
historical C2 exception and production repair remain UNPROVEN. One paired run
is one runtime evidence family, not repeated or universal platform proof.

TARGET: contain supported recursive Python descendants while preserving the
existing venv-facing sys.executable, prefix, public protocol and process API
semantics. A root-only change cannot meet this: launch_current already starts
the native image, while unchanged original17 authored scripts call
subprocess.Popen([sys.executable,...]) recursively.

| Option | Mechanism and main failure mode | Decision |
| --- | --- | --- |
| No build | Keep the observed failure fenced and stage false | Honest fallback; does not complete shutdown repair |
| Exact-native executable override plus explicit sealed recursive bootstrap | Owned-process guard routes supported Python creates to attested native image; every generation loads exact policy/config before dispatching authored code | Recommended bounded RP prototype; argv/env compatibility and bypass refusal must be demonstrated before integration |
| General native launcher/broker or process-creation supervisor | Covers a broader native creation contract | Deferred; larger architecture and operational cost, not silently included |

RECOMMENDATION: the second option, conditional on RP1 falsifiers. Preserve
sys.executable as the selected venv path. Keep caller Python argv intact at the
public API; use Popen.executable (or an equivalent proved owned-process creation
boundary) to choose the exact attested native image, with existing venv selector
restored per child. Bind the recursive request/policy/loader by exact path/hash,
nonce and expected image/venv frame. An explicit trusted descendant bootstrap
must install the same guard before dispatching script/-c/-m authored work.
No reliance on a bare sitecustomize hook: missing, shadowed or disabled hooks
cannot attest their own absence, and a late marker cannot undo authored work.

This is an application-controlled Python launch contract, not an OS sandbox.
Audit current worker, indexing/Git, test-evidence, benchmark, multiprocessing
and pinned adapter creation paths before selecting the guard boundary. Existing
legitimate native/Git behavior must remain supported and contained; do not
silently replace it with a new refusal. Raw native creation outside a proved
guard must be explicitly excluded/audited or trigger a stronger design decision.

PROPOSED range requiring new approval (DR explicitly excluded production and
supervisor redesign; no RP implementation is authorized just by this record):

- RP1: implement only a new source-local scratch prototype and failure-first
  tests for exact native routing plus explicit recursive pre-authored bootstrap.
  Inventory actual command grammar first: script/-c/-m, existing flags/argv,
  stdin/stdout/stderr, cwd, environment, exit codes and exceptions. Include
  original17 unchanged native assertions against the prototype. Prove absence,
  tamper, shadow, disabled startup and stripped/foreign environment cases cannot
  produce their child must-not-run marker. Reject unsupported/breakaway launch
  forms before CreateProcess. Do not patch the selected venv, .pth/site-packages,
  registry, global environment, ACLs or an old frozen artifact.
  Execution authority requested for this milestone is explicit: controller314
  unit/failure checks first, then AT MOST ONE fresh normal non-admin SID1001
  selected3.12 scratch-prototype observation under a NEW reviewed/sealed root
  and command. No selected312 agent execution, old command or automatic retry.
  Stop/preserve on failure. Controller-only GREEN cannot clear RP2 because it
  did not reproduce the selected Store topology. The selected prototype result
  must pass and receive raw-result review before live-source integration.
- RP2: integrate only if RP1 and fresh native design/code review clear the same
  contract. Expected source surfaces: windows_owned_process.py,
  windows_owned_bootstrap.py, narrow new policy/descendant-bootstrap modules,
  and only necessary environment propagation at distributed_retrieval.py or
  worker_client.py. Keep public schemas, selected venv identity, original17
  IDs/assertions and source controls. Run focused ownership/writer/lifecycle,
  recursive grammar/refusal and broader relevant suites; retain all failures.
- RP3: independently review and seal one fresh selected3.12 normal-account
  qualification successor. Require all original ownership/writer/lifecycle and
  startup assertions, unchanged ordered public initial/replay/lease controls,
  actual inner Job membership/count3 and all independent root/child/grandchild
  native waits, with no emergency process termination needed for success.
  Use existing cooperating-account copy method for mandatory fresh ORIGINAL
  BEFORE/AFTER preservation. Judge raw receipts before stage closure. No old
  D2/DR command retry; stop on failure, preserve output, no automatic retry.

Done requires launch/authored image identities and creations to agree with the
approved native route in every supported generation, same selected venv and53
dependency identities, nested-Job coverage, all original assertions intact and
unsupported forms refused before child authored work. Default120/public90/
lifecycle60/sharedshutdown5 stay fixed. No install/reinstall, runtime/cfg change,
ACL/security/global mutation, Git write, old-data deletion or release inference.

Mandatory RP1/RP2 compatibility matrix: compare guarded dispatch against an
unguarded native CPython control with the SAME pinned image and existing venv
selector, separately for script/-c/-m and each supported flag/argument form.
Observe child-visible sys.argv (including argv0), sys.path[0], __main__ identity,
__file__ presence/value, __package__/__spec__ where relevant, cwd, stdio bytes,
return code and exception type/message/root-cause visibility. Do not infer
compatibility from only loaded-image or prefix equality. Any additional trusted
bootstrap traceback frame must be documented; no protocol/stdout pollution.
Approval of RP1–RP3 requests two distinct normal selected-runtime attempts at
most: ONE scratch proof in RP1, then ONE integrated qualification in RP3 after
successful integration/review. Neither is a retry of a failed attempt. A failed
prototype cannot be followed by integration or an automatic successor attempt.

WEAK LINK: the native route works in one paired witness; recursive propagation
and full argv/environment compatibility are not implemented or proved. CHEAPEST
FALSIFIER: RP1 must-not-run markers for every missing/tampered/bypassed gate plus
the unchanged original17 child/grandchild wait assertions. PIVOT: if any authored
child runs without exact policy attestation, or a required existing creation API
cannot be contained by the bounded guard, reject this prototype and return for
the stronger native-boundary architecture rather than weakening tests.
Confidence: supported repair direction, implementation feasibility unverified.

Primary API sources: Python documents Popen.executable separately from argv at
https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen and site
startup/disable behavior at https://docs.python.org/3.12/library/site.html.
Windows Job child inheritance semantics:
https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects.
These explain candidate mechanics; they are not binary-level Windows cause
proof or a substitute for selected-runtime qualification.

### RP1–RP3 approval and RP1 execution2026-10-29

AUTH: user answered "Approve RP1–RP3 (Recommended)" to the explicit range.
The proposed range above is now approved with its conditional ordering and
one RP1 / one RP3 maximum normal-account attempts. No re-approval inside it.
RP1 live production/old histories remain immutable controls. Baseline saved
exclusively under .github/run-artifacts/recursive-launch-20261028/Baseline.json.

Required native review correction: normal CPython startup precedes a -c loader;
so the loader alone is not the trust boundary. Compare (a) audited/sealed normal
startup with a clean startup environment and sanitized loader imports, against
(b) internal no-site startup followed by explicit site reconstruction. Prefer
(a) only if startup-surface and must-not-run evidence prove its boundary; (b)
changes sys.flags.no_site and3.12 prefix semantics and needs an equivalence proof.
Do not pretend manually restored prefix alone preserves interpreter behavior.
Before any authored dispatch, exact request/source/frame binding, recursive
guard installation and supported command grammar must pass. Tests include cwd
sitecustomize/usercustomize/hashlib/json shadows, startup path drift and .pth
injection in synthetic test-owned directories, duplicate-case environment,
missing/tampered requests, breakaway and unsupported flag refusal.

Inventory observed in application sources: persistent distributed roots route
through launch_current; WorkerClient has raw script+args Popen; benchmarks use
-c; test_evidence uses script+args; worker/indexing conditionally require Git.
No application multiprocessing/joblib/direct_winapi/os.spawn calls found.
Installed adapter creation paths still require read-only inventory before
integration; absence in application source does not prove absence in vendors.

### RP1 implementation observation and input-only handoff2026-10-29

Scratch only: recursive_policy.py, recursive_bootstrap.py, controller-copy
helper, selected verifier/probe drafts and focused controls are local under
.github/run-artifacts/recursive-launch-20261028/prototype. Production unchanged.
Exact strict f6500cd3 module passed77Windows controls in controller-final-11;
original17 assertions and source seals stay unchanged. Retain all earlier REDs,
including the access-denial discovery and controller count6 baseline witness.

Closed production profile: only _Session's distributed_worker.py roots receive
the guard; current WorkerClient/taskkill executes outside it. Do not broaden
installation without re-auditing native creation. RP1 stdlib fixtures are explicit
test roots, not a generic OS sandbox claim.

Agent Candidate mandatory Store alias metadata was denied. Normal input-only
preparation is authorized within RP1, independently of the one runtime attempt.
Same-seat native final review SHIP for the externally sealed INPUT-ONLY block
after isolated-controller/env-shadow controls. No old/current runtime command
may be inferred from it. Launcher97a4f2b0, outerb6ed010a are frozen; see latest
recursive-launch-rp1-20261029.md. Normal root is absent and attempt unused.
Observe Inputs.json from normal1001, parent review exact contents/hash, then
finish the full runtime successor review/seals and issue one RP1 command.
No new approval gate inside approved RP1–RP3; no auto retry, missing-input skip,
installation, permission change, Git write, old-data deletion or qualification.

### RP1 actual normal Inputs and final runtime review2026-10-29

Input preparation is now observed, superseding root-absent statements above.
Inputs369408bytes SHA60b392e49bd7a0de42847b92150dcb590c89806e4d4836a506f38072cbae6bfd
verified directly by parent against current readable authority/14bound rows.
No RP1 selected attempt; normal root contains only Inputs.json.

Full handoff review found runtime evidence defects excluded from input-only
clearance. Keep consumed preparation bytes immutable; use a separately sealed
recursive_runtime_verification.py within the same approved RP1 milestone.
Required corrections now implemented and controller tested: closed initial
child environment before claim, retained postclaim mkdir/publication errors,
exact original17 IDs/logs, six-method matrix/36rawstreams, Command/stream/Probe/
marker/claim bindings and full evidence recheck AFTER. No weakened assertions,
new selected attempt, expanded production guard or deadline increase.

Focused fault RED/GREEN and combined58run57PASS1known link-fixture skip retained;
last partial-publication regression GREEN11/11. Existing unchanged-core77Windows
controller proof remains separate. Final runtime source ef59eee3; launcher
c52a50d2; outer b8e97698. Exact final native review pending before issuance.
On clearance issue this one normal-account scratch proof, then inspect actual
raw results before conditional RP2 integration. RP3 fresh ORIGINAL BEFORE/AFTER
cooperating-copy preservation remains mandatory and is not closed by RP1.

Final exact native review SHIP2026-10-29: successor ef59eee3, launcher c52a50d2,
outer b8e97698, prepared Inputs60b392e4. One normal-account RP1 scratch handoff
is now issued; selected attempt remains unrun. Final59controller checks:
58PASS,1known real-symlink fixture skip; focused11/11. Native VerifyOnly11pins,
wronghash/foreignselector/wrongaccount controls observed beforePython. Review
excludes RP2/RP3/Gate1 readiness; their already-approved conditional scope stays
unchanged. Stop/preserve on failure and never retry a consumed command.

### ACTUAL RP1 failure and existing-data readback2026-10-29

User executed the reviewed command once. It is now consumed. Exact95881byte
Run-Failure/runReceipt SHA63c315d3d8a6846642f7c2783d5329239e247897866987eb365293929ddf78f8
matches parent raw readback.4complete captures; identity/dependency/startupPASS,
original17 ran15PASS2FAIL in14.763s, no timeout/errors/skips/postcheck failure.
Both failing cases lack a descendant-ready marker before shutdown assertions;
remaining matrix/descendant/AFTER phases did not execute. Central requests empty.
All17recorded artifacts and639copied source hashes verified. RP2 precondition
is false; approved RP1 one-shot authority is not automatically renewed.

Decision: report-only preserves an honest failure but cannot learn the cause.
Smallest next observation is normal-account read-only access to the exact two
already identified private fixture leaves; no recursive copy or permission
change is needed to report their existing contracts/ready/go/marker metadata.
Stronger alternative is a distinct exception-capturing selected diagnostic,
requiring new explicit one-shot authority if the old data cannot distinguish
the pre-request failure. Never rerun old command or change test assertions.

Recommend existing-data readback first. Weak link: stderr=DEVNULL already lost
the exact exception; marker timing may narrow phase but cannot recreate it.
Cheapest falsifier: compare existing contract deadlines and marker/go metadata.
Pivot: if that is inconclusive, prepare bounded atomic root-install/pre-request
exception sidecars in a new scratch diagnostic, controller RED/GREEN and native
review before requesting new selected-execution authority. Deadline narrowing
is a hypothesis only; no production repair or package reinstall is justified.

New PowerShell-only helper RP1-Read-Failed-Fixtures.ps1 d0383891 and outer
RP1-Readback-Command.ps1 a49a7dca read exactly sr3-nested-job-w8m4fynk and
sr3-owned-tree-3mm1_fl1 under the consumed run. No Python, test, output file,
workload claim, old-file mutation, security/Git/install operation. Four consumed
artifact pins, normal1001/non-admin, name/count/byte/link/UTF8/read-stability
guards; numeric link count explicitly UNOBSERVED.3controller checks PASS;
parse/VerifyOnlyPASS. Final read-only review pending before handoff.

Final read-only review SHIP for exact d0383891 helper/a49a7dca outer. Native
wrongagentSID refusal observed before private reads; consumed result hash stays
63c315d3. This read-only handoff is issued without renewing runtime authority.
Review its existing data first. It does not authorize Python, another selected
process, a workload, RP2/source integration or any old command retry.

### Corrected RP1 continuation — controller verified2026-10-29

User MAKE THIS RP1 SUCCESS/CONTINUE authorizes local corrective implementation.
Old selected proof63c315d3 remains consumed. Readback completed and refutes
immediate startup expiry for the tree root; discarded original error unknown.
Do not spend another selected attempt without a concrete reviewed fresh proof.

Selected mechanism: smallest corrected scratch successor with calibrated shared
clock deadline, independently bounded root installation and pre-authored failure
retention. No-build leaves RP1 failed. A persistent worker/service or new Python
environment is larger scope without evidence and is rejected. Weakest link:
selected3.12 behavior remains unobserved. Cheapest falsifier: captured strict
root-child-grandchild smoke first; stop on any failure before17/matrix. Pivot
to its retained exact stage/cause if it fails; do not force clock hypothesis.

- [x] Correct clock-domain and startup/lifetime split in NEW scratch only.
- [x] Preserve exact loader/install/dispatch failures even before bootstrap entry.
- [x] Bind original17/command partial logs, cumulative strict sidecars and both
  descendant proofs' five raw markers. Retain original error if capture fails.
- [x] Parent40/40 focused+unchanged compatibility and77/77 full Windows controls
  pass. Exact original17 and original25 assertions unchanged; no skips/widening.
- [x] External15pinVerifyOnly,0parse errors, wronghash/wrongSID refusal observed.
- [ ] Final exact native review and separately approved concrete one-shot normal
  corrected proof. No selected operation from agent1003; no old retry.
- [ ] Parent raw receipt/result/stream/profile/source/native-wait review before
  RP1 acceptance and conditional RP2 integration. RP3 remains separate.

See recursive-launch-rp1-20261029.md latest corrective section for exact seals,
receipts and retained REDs. Newnormal recursive-launch-rp1-corrected-20261029
must remain absent until deliberate approved execution. Every qualification flag
false. Original source/runtime/history permissions and bytes unchanged.

Final exact native review completed SHIP: bootstrap1d6c87fc, coordinator22f59ce5,
launcher d7f2e99e, outerdb7cd1f2. FINAL40/40+77/77 controller checks PASS and
all15external seals/refusals verified. Review checkbox above is closed; only
deliberate new one-shot user approval/execution and subsequent raw review remain
before RP1 acceptance. Normal destination absent; selected3.12 remains UNRUN.

### Corrected RP1 actual environment refusal and bounded successor2026-10-29

User ran the reviewed corrected proof. It is now CONSUMED/FAILED, not UNRUN.
Actual Run-Failure109583bytes SHA9f4b2ce33ea624386a64b3b85dafedd549051f4fc53b9a632d80871f8bdc175b.
Five identity/dependency/startup/clock captures passed. Captured exact3 smoke
failed before first child creation: retained stderr and dispatch sidecar agree
stage environment/E_RP1_ENV_STARTUP, authored_child_startedFalse, about109.475s
recursive budget left. Sole unexpected recorded Python key is PYTHONUSERBASE.
Tagged CPython3.12.10 PC/python_uwp.cpp220-223 inserts this key when absent.
Initial closed controller env forbids it, so this runtime-added key explains the
current boundary failure. Its actual value and historical lost-stderr cause
remain unobserved; do not invent either. Original17/matrix/finalproof unrun.

Recommendation: fresh scratch successor, bind selected Store-generated USERBASE
from the existing pre-workload startup metadata frame, validate its package-
family normal LocalCache location, require no-user-site1/siteFalse/exactpaths,
then preserve only that exact value through guarded descendants. Extend profile
with optional controllerNone/selectedexact binding; ordinary clean_env remains
strict by default. Reject changed value, duplicate casing, enabled user-site,
missing no-user-site1 and every other unsupported Python key. Attest binding
at every child entry. Preserve public env values and immutable original tests.

No-build preserves a now-explained refusal. Blanket allowance or arbitrary
stripping loses the refusal/value contract. Reinstall/newruntime/ACL changes
cannot solve this policy mismatch. Weakest link: actual new selected value and
recursive proof still need observation. Cheapest falsifier remains the early
captured exact3 smoke; stop on failure and retain exact cause, no automatic retry.

- [ ] New recursive-launch-store-env-20261029 prototype only; preserve consumed
  source/helpers/contracts/receipts. No production integration in this step.
- [ ] Failure-first policy/profile/startup metadata controls, unchanged contracts,
  relevant ownership regression; exact reviewed fresh normal-account one-shot.
- [ ] Parent actual raw review before RP1 acceptance and conditional RP2.

One new selected proof requires concrete deliberate approval/execution after
local correction/review; neither consumed command may be rerun. Default120,
public90/watchdog60/shutdown5 and all full-stage/Gate1/release/install flags stay.

Store-env final local observation: policy5RED→5PASS, metadata4RED→4PASS, final
combined60run59PASS0fail/error1knownsymlinkpermissionSKIP. Two new positivewiring
testfixture defects retainedRED and corrected; implementation unchanged to close
them. Broader77run76PASS1accessERROR, unchangedstartupbaseline21/21PASS; keep
access/I/Ocauseunknown and broadsuiteNOTgreen. No broad rerun/skip/ACL workaround.
Exact native final review SHIP bootstrap035a8226/policyea17b5e/coordinator4e2be144,
launcher48a2e281/outer4b10636d. VerifyOnly16sealsPASS, parse0, wronghash/wrongSID
refusebeforePython, newnormalrootABSENT. Localbuild/reviewcheckboxes closed;
deliberate one-shot userexecution and actualrawreview still pending beforeRP1.

### Store-env actual result and collector follow-up, 2026-10-29

Issued Store-env attempt consumed. Actual selected3.12 captured exact3 smoke
and unchanged17tests PASS; Run-Failure6017f134 retains a subsequent collector
stop. Parent639source/49evidencehashes matched;1private sidecar unreadable.
Collector's broad *.failure.* scan misclassifies an owned-bootstrap temporary
publication in intentional expired-gate test as recursive enter failure.
Do not call the inaccessible payload verified or blanket-ignore those records.

- [x] Verify actual receipt, available raw hashes, native3role shutdown/cleanup,
  unchanged17PASS and exact failing collector branch; preserve consumed run.
- [ ] DATA-ONLY normal-account hash-checked readback of sidecar7c92170e,
  matching contract/ready, and go/authored-marker absence/presence.
- [ ] Use actual payload to reproduce and narrowly repair classification in
  new scratch only, with strict expected-negative provenance and unexpected/
  incomplete/changed-record controls. Preserve old helpers and test assertions.
- [ ] Review bounded continuation of remaining RP1 proof; no automatic old
  workload retry. Matrix/finalproof/AFTERmetadata remain unrun; RP2 conditional.

Cheapest falsifier is existing sidecar readback, not another selected run.
No-build remains partial; blanket ignoring .tmp/owned failure records rejected;
larger failure framework unnecessary. If the readback reveals an unexpected
cause, address that evidence before proposing a collector acceptance exception.

### Approved collector correction and complete failure reporting, 2026-10-29

User supplied normal readback:1706byte sidecar7c92170e is exact TimeoutError /
E_OWNED_BOOTSTRAP_GO_DEADLINE; expected and observed identity match. Contract
45384434 and ready60f28631 bind same token,PID27140 and script. Final failure/go/
authored marker absent; go.tmp present. This closes unknown payload, not exact
instruction at termination. User now requires comprehensive segment/cause logs
in one handoff, not a PowerShell command for every small test.

Within approved RP1 scope create NEW recursive-launch-audit-20261029 scratch;
reuse Store-env bootstrap/policy/probe bytes unchanged. Parent owns runtime
orchestration/reporting; native worker owns a bounded failure-audit module and
its tests. Preserve every consumed artifact. No production/Git/ACL/install edit.

1. Reproduce collector false refusal, then accept only the expected expired-gate
   negative control with exact body/token/identity/contract/ready/script/marker,
   source/test outcome and count binding. A final publication or its PID-bound
   temporary predecessor can both represent this expected error; reject both
   together, wrong schema and any unbound/malformed record. Retain each state.
2. Capture candidate raw text/hash and related bounded records BEFORE validation.
   Retain errors independently; never let later validation erase primary cause.
   Unexpected recursive and matrix failures keep their strict rejection rules.
3. Add bounded structured phase/substage timelines, original exception chains
   and notes, command exit/containment, relevant stdout/stderr/log excerpts,
   PID/cleanup/identity summaries, unreadable paths and capture incompleteness.
   Whole receipt plus a concise diagnostic summary must carry enough accessible
   evidence to avoid another manual private-file read. No credentials/env dump.
4. Controller-only focused negative controls and unchanged compatibility tests,
   fresh native review, exact external seals, one normal-account full RP1 run.
   Same120/90/60/5 budgets. No retry, success fabrication or skip. Actual raw
   review required before RP2. Prior broad76PASS/1accessERROR remains caveated.

No-build leaves a now-explained verifier defect. Chosen smallest adequate fix
is strict expected-negative classification plus evidence-first reporting.
Blanket ignoring .tmp or replacing the test is rejected; a general telemetry
framework is unnecessary. Weakest link is unseen selected-path behavior in
the remaining matrix/final phases; cheapest falsifier is complete local fault
coverage followed by the single fully logged selected qualification.

2026-10-31 review clarification: repository scratch is
.github/run-artifacts/recursive-launch-audit-20261029/prototype; the separate
normal-account execution root is C:/Users/sakth/Documents/Codex/recursive-launch-rp1-audit-20261029.
Retained dates in these fixed names are identities, not a claim of execution.
Classifier requires selected-clock deadline between conservative upper-start
and lower-end bounds of the completed original17 command, using existing clock
calibration; no timeouts/deadlines are enlarged. Reviewer found missing expiry
and independent top-folder retention checks; both corrected and tested locally.
All qualification flags must remain false at aggregate validation. Missing
required artifacts fail; optional Intent.json absence alone is permitted.

Final2026-10-31: local93run92PASS1knownskip0errors/failures; reporting-only final
coordinator delta9/9PASS. Exact native SHIP for coordinator9b650a93,
launcher8caba29b, outerc09a5999. Final parse/VerifyOnlyPASS; normal root ABSENT.
Next is ONE full selected normal-account observation then raw review. RP1 actual
completion/RP2 integration remain pending; no renewed scope approval is needed.


### RP1 actual acceptance and approved RP2 continuation, 2026-10-31

RP1 complete after actual parent raw review and fresh native reviewer SHIP.
Evidence: rp1-actual-acceptance-20261031.md. Receipt20800625...; all11commands
exit0,17/17ownership,6/6matrix/36streams, two fresh3role native waits/cleanup.
639source and116direct+5embedded private evidence hashes independently checked.
Five private originals remain agent-unreadable; full normal-captured bytes are
verified, not falsely described as fresh agent reads. No new workload/retry.

Next approved RP2: inspect concrete profile/startup integration seams, record
minimal mapping, then integrate proved recursive guard in owned startup while
keeping selected identity, budgets, public API and original17 assertions. Retain
failure-first tests, focused ownership/writer/lifecycle and broader regressions;
fresh review before one new RP3 integrated qualification. Existing authorization
covers RP2; no ceremony approval. Full shutdown/Gate1/release/install stay false.


### RP2 concrete integration mapping, 2026-10-31

INTENT: make every launch_current-owned root install the proved recursive guard
by default after its existing identity/Job/ready-go/deadline gate and before any
authored worker code. Parent processes retain their own unmodified Popen. An
optional/off guard limited to _Session was rejected: it would leave unchanged
original17 direct-owner calls exercising the old Store descendant escape.

Scope: new knowledge_bridge/recursive_bootstrap.py and recursive_policy.py,
windows_owned_process.py contract/source seals, windows_owned_bootstrap.py
post-go installer, and only necessary shared deadline propagation in Windows
_Session. Existing call shapes remain valid; an optional recursive_deadline
keyword defaults to an independent120-second budget. _Session supplies its
existing shared request deadline unchanged, so two sessions cannot reset it.
The existing startup deadline bounds startup/install only. No extra interpreter
probe is used: construct runtime profile in the attested child from actualimage,
venv/startup paths excluding bootstrap path0, exact Store USERBASE observation
and sealed adjacent source. All normal startup/audit/refusal checks still apply.

No-build leaves live source unfixed. Chosen route promotes the observed bounded
owned-root guard; a new generic process service/global interception would enlarge
scope and is rejected. Weak link is profile construction outside the scratch
harness. Cheapest falsifier is a real unchanged direct owner call that can still
create an unsupported/unattested child or changes argv/stdio/exception behavior.
Refuse integration if it requires weakening identity/startup or original tests.

TDD: add new integration controls, retain observed RED on current production
behavior, implement, then original17 plus Windows writer/lifecycle/startup,
recursive compatibility/refusal and broader knowledge tests. Existing tests and
all consumed prototypes/normal outputs remain immutable. Baseline is retained
in .github/run-artifacts/recursive-integration-rp2-20261031/Before.json.
Fresh design/code review and parent observations precede RP2 completion/RP3.


### RP2 review corrections, 2026-11-01

Fresh native review found Store binding and conditional editable-Git gaps.
Store roots must require USERBASE/no-site and bind its exact observed value
to Local/AppData/Packages/<attested alias family>/LocalCache/local-packages.
Derive Local from the already-attested base alias, without a probe or env change.
Normal non-Store roots retain absence; generic USERBASE allowance is rejected.

Preserve worker.runtime_identity's existing editable Semantica branch using the
accepted native_spec/route_native, with one necessary worker.py hook before its
existing rev-parse/status calls. Bind only the exact existing PATH git.exe and
resolved Semantica root; binding is idempotent for that pair and rejects rebinding.
Only those two read-only vectors are available to OWNED_RUNTIME. Check the shared
recursive clock/deadline before/after binding/routing and immediately before create.
Ordinary parent Popen has no binder and keeps its existing behavior. The source
package is trusted application code; this is not an OS sandbox.

No-build would regress an inventoried conditional path. Chosen bounded binding
reuses proved controls; a general native command allowlist is rejected. RED
controls precede fixes, then final relevant regressions and independent re-review.
Native-Git-Before.json pins worker.py before this required integration seam.


### RP2 acceptance, 2026-11-01

Native final review SHIP after Store missing/location and editable Git findings
were reproduced RED and closed. Final292knowledge:238PASS54knownSKIP0FAIL/ERROR;
45immutable compatibility:44PASS1knownsymlinkSKIP0FAIL/ERROR. Original17 and
WorkerClient baseline bytes unchanged. RP2-Accepted.json SHA feb82bdbecfa8fef0c37ba72f7d4601b4fb0febea05e6cb101adc5aa1f078369
pins all9 code/test records and final receipts. See rp2-integration-acceptance-20261101.md.
RP2 complete; RP3 selected integrated qualification and fresh ORIGINAL BEFORE/AFTER
remain unrun. Existing RP1-RP3 approval continues; no duplicate approval needed.


### RP3 bounded preparation mapping, 2026-11-01

RP2 native SHIP closes the conditional gate; existing RP1-RP3 approval applies.
First prepare new normal-account Inputs and fresh ORIGINAL BEFORE data request,
without selected Python3.12, test execution, source extraction or workload claim.
New helper lives under recursive-integration-rp3-20261101/prototype; old helpers
and every consumed command/input remain immutable. Reuse checked C1 and existing
shutdown_copy_data SnapshotSet; keep inaccessible evidence explicit for the
cooperating existing-access reader, while authoritative code/runtime must remain
directly readable and exact. No permission/security change or inaccessible skip.

Source-Recipe.json 236879bytes SHA644a540b86083f244acb3f29a596f8030c393e80e7aaf73c572f97a8fead3fec
binds exact fee69861 HEAD tree675 records plus10 approved overlays (9 RP2 records
and the previously approved original17 atomic-marker fixture),680 evaluated files.
Parent observed zero live-authority mismatches. This is a recipe, not a copied
source/normal preparation or selected-runtime observation. Original17/WorkerClient
are not being repaired again. All retained sources remain unchanged.

Preparation seals RP2 acceptance/source recipe, original runtime/lock metadata,
current protected packages/caches and declared consumed receipt/history coverage;
records phase/root timing and full bounded original exception chains. Fresh data
coverage includes the4 cleanup roots and4 consumed RP1 normal roots. Any further
required history must be explicit; no archive-wide claim. Prepare in one unique
normal destination; existing claim/output means consumed, retain and stop.

Review/test input guard/source/digest/overwrite and denied-data handling in the
controller, then issue one sealed input-only handoff if normal account is required.
After current ORIGINAL BEFORE copies/readback, freeze one full RP3 selected run
with identity/dependencies, complete ownership/lifecycle/public initial+replay,
segments/causes/raw bytes and actual tree exit. Then fresh ORIGINAL AFTER copies
and parent raw comparison. Runtime command is not frozen by input preparation.
No old retry, install, ACL/global/Git write, original deletion or budget increase.


RP3 prep final2026-11-01:9/9controller controls PASS, source680+6olderpins
observed, actual wrong-agent refusal leaves ROOTabsent. Fresh nativeSHIP for
helper017a4072/outer569137d4,0PowerShell parseerrors. One normal input-only
preparation issued; actual Inputs/BEFORERequest and cooperating copy/readback
remain pending. No selected runtime command frozen or issued. Existing approval
continues; no repeated milestone scope question. See rp3-input-preparation-20261101.md.


### RP3 actual preparation and authorized local checkpoint, 2026-11-01

Normal input preparation SUCCEEDED and is CONSUMED. Parent verified3output
hashes/sizes/bindings, source680,53versions,8roots and0failure marker. Cleanup-
repair retains1240unresolved paths; cooperating BEFORE copy/readback remains.
Runtime/sourcecopy/test/workload unrun; fullRP3/AFTER/stage remain incomplete.
AUTH: user asks "can we comit to git to save successfull details to reuse?"
Save approved source/tests and curated status/hash/archive evidence using an
isolated Git index and separate local checkpoint/rp2-rp3-inputs-20261101 ref.
Preserve active development HEADfee69861 and its index; a normal active-branch
commit would invalidate prepared exactHEAD guards. No raw private request/data/
caches/binaries, unrelated dirty files or push. Verify each committed blob and
ref, unchanged activeHEAD/index and prepared-file seals. This is checkpoint
storage, not RP3/runtime qualification or a baseline change.


### Approved RP3 completion continuation, 2026-11-01

AUTH: user says "complete it, make it complete rp2 and rp3". RP2 remains
accepted; no repeat of its controller campaign. INTENT: new rp3_copy.py reuses
sealed SnapshotSet DATA policy/copy/readback, new rp3_runtime.py validates one
actual integrated selected3.12 observation, rp3_finish.py coordinates and
requires fresh ORIGINAL AFTER before completion. Existing reader access only;
no ACL/install/Git/source edits or consumed-command retry. All new code stays
in the current RP3 phase; old preparation/Inputs/Request and authority remain
sealed. Focused failure-first coordinator controls plus fresh native review
precede normal execution. Every segment/cause/command is retained.
No-build leaves RP3 incomplete; reuse of strict existing copy/capture primitives
is recommended. A new environment or relaxed guards would not prove this stage.
Done requires complete BEFORE coverage, exact680-file evaluated source, actual
selected identity/dependency/group/public initial+replay/native-exit evidence,
and fresh original AFTER content/identity/ACL comparison plus raw review.


### RP3 cooperating BEFORE copies and one-shot completion handoff, 2026-11-01

Existing-access inspection/copy SUCCEEDED:1240directorytargets,4396files,
7436objects,33362733bytes;0hardlinkexceptions. CopyInputs7c18bb40... and
Copiesfdeacbb0... frozen; original Inputs77769.../Request15086... unchanged.
New controller35/35 PASS after review fixes: separate external DATApolicy seal,
workload-bound BEFOREbaseline, every later CopyInputs reopen pinned using new
private sealedadapter, child cause retained in correct runtime segment. Native
explicit SHIP received; later reviewer final credits error is retained honestly.
New outer29pins a9c8a92b...,0parseerrors,VerifyOnlyPASS,wronghashrefusalPASS;
locale-sensitive date reparse caught beforePython and corrected via typedcast.
Reader session29980 waiting through20:58:24IST; one normalaccount command
performs BEFOREreadback,actualselected3.12 groups91authoredcases+publicordered
initial/replay,then fresh ORIGINALAFTERcopy/readback/comparison. All stages/
causes timed and retained. No normalclaim/runtime started at issuance. RP3
completion remains conditional on actualobserved result and parent raw review.
No duplicate approval required inside approved RP1-RP3. Preserve activeHEADfee
and allolddata. No Gitwrite,install,ACL change,timeoutincrease,originaldelete
or oldretry. See rp3-completion-handoff-20261101.md for exact resume/seals.


### Approved READY read-only/copy repair with 3-day managed-copy retention

AUTH: user requests strictly read-only READY access, copy fallback into a specific
folder based on existing copy code, and explicitly selects "3 நாட்கள்". This is
a narrow exception to no-deletion for NEW managed READY copies only. No deletion
of originals, failed attempts, source, caches, receipts or old evidence is allowed.
RP3 original attempt is consumed: BEFORE readback passed, selected3.12 ownership
17/17 and writer18/18 passed, shutdown11PASS/1startupERROR opening .ready.json.
Runtime Receipt5dc1bea4... preserves the cause; no old command is rerun.

INTENT: explicit GENERIC_READ source handles, read-sharing without write access,
exact native error codes; on access/sharing failure only, a current-token copy
pre-created by the parent and read using its already-open read-only handle. Child
publishes only into that exact empty single-link file; framed size/hash/token and
actual native PID/image/Job checks remain mandatory. Bad JSON/identity/link/data
never falls back. Permission errors are not relabelled a proven ACL/lock cause.

Reuse archive_copy_h1/read_file principles: source preserved, independent copy,
file identity/link/type/size/hash checks, explicit source-to-copy mapping. Existing
offline SnapshotSet is inert evidence machinery, not live-worker authority; do
not execute copied data or bypass native attestation. Parent resolves one user
cache root via Windows known folders and sends exact path to child. Proposed
normal root is C:/Users/sakth/AppData/Local/MemoryIntegrity/ready-copies-v1.

Deletion eligibility requires an accepted read, successful startup, and actual
native worker-tree exit; expires3days after both read/exit complete. Cleanup on
subsequent application starts deletes only the exact managed single-link payload
by verified file handle inside that root; metadata/audit stays, failed/unaccepted
copies stay. No global scheduler/service or permission/attribute change. If app
is not running, expiry cleanup occurs at the next startup after3days.

No-build leaves RP3 failed; another chmod/read-only attribute does not grant read
access. Recommend parent-owned copy with existing read-only first path. A pipe
transport is a stronger redesign held outside this focused repair. Weak link:
selectedStore3.12 access behavior remains unobserved until one separately sealed
new source/runtime proof. Cheapest falsifier is real native exclusive-sharing
denial plus read-only fallback, token/hash/reparse drift, and expiry guards in
controller tests. Keep120/90/60/5 and existing ordered600 bounds.

Files: new windows_ready_copy.py and test_knowledge_windows_ready_copy.py; bounded
changes windows_owned_process.py/bootstrap.py; existing Fable plan/design/state
and evidence. First failing focused tests, minimal integration, Windows/lifecycle
and knowledge regressions, read-only review, then a fresh sealed successor. Any
source/runtime recipe is NEW; old680recipe/launcher/receipts remain immutable.


### READY-copy implementation observation and native final review

Final exact-source32focusedPASS; broader324run270PASS54unchanged runtime-dependent
SKIP,0FAIL/ERROR in108.667s. Native Fable reviewer first FIX-FIRST for expiry
bound/scan/audit/error propagation, then explicit SHIP after retained RED/GREEN
corrections. All32 focused cases are included in broader total. Controller uses
isolated managed cache and PYTHONNOUSERSITE=1 because agent1003 cannot create
normal user's LocalAppData path. Three-day time arithmetic is simulated; actual
Store3.12/default-cache access/fullRP3/ORIGINAL AFTER remain UNVERIFIED.

Expiry implementation: due-date queue bounded to128 scanned entries and64
reserved deletion attempts, cooperative0.1s check (not native-I/O preemption).
Permanent receipts never scanned; interrupted/invalid queue data preserved in
retained quarantine; unsafe active-queue traversal fails explicitly. Verified
exclusive payload handle plus durable DELETE_INTENT precede removal; outcome/
error envelope precedes metadata archival. Only new empty queue-day directories
are removed as housekeeping. Locked/unsafe payloads stay retained with causes.
No global scheduler; cleanup waits for a later app start after3days.

Candidate source hashes: ready_copy755df303..., owner0ff54944..., bootstrap
7f85872a..., testsba742402.... Source-Candidate/Controller-Accepted and read-only
Independent-Review are under existing RP3 ready-copy-repair evidence phase. Read
rp3-ready-copy-repair-20261101.md for actual failing selected run and exact proofs.
Old680recipe/runtime/RP2Acceptance/failedreceipt remain unchanged; HEADfee69861,
indexempty. No selected runtime/oldcommand retry, install, ACL/Gitwrite or olddata
removal. A NEW sealed normal-account combined BEFORE/run/ORIGINAL AFTER successor
is still required before any full RP3 success statement; no successor issued here.


### Approved RP3 READY-copy successor continuation2026-11-02

User asks COMPLETED? OR CONTINUE; prepare one NEW normal integrated workflow.
Code/controller acceptance frozen, no production edits. New private phase
rp3-ready-20261102, absent normal root Codex/rp3-ready-20261102. Reuse five
predecessor helpers BYTE-FOR-BYTE through one exact-name/path/SHA factory; every
copy.modules/runtime.load_module/finish.modules reopen must stay configured.
New validator binds exactfee69861 base+historical RP2 overlay+ONLY four newly
accepted READY-copy deltas; exact682manifest, no arbitrary dirty source.

Test/implement/review: preparation publishes immutable Preparation-Ready only
after prepare returns success (binds Inputs/Request/success Diagnostics and no
Failure). Existing-access reader waits for this, then existing structural policy
validation PLUS exact8roots/allowed{} allroots and durable Zero-Exception-
Accepted; exceptions stop, no discretion or policy_approved rewrite. New outer
Reader/Workload/AFTER/Stage envelopes bind factory/config/helpers, recipe, source
acceptance and exact inner artifacts. Original JSON never edited after publish.

One normal command: fresh prep, cooperating BEFORE copies/readback, selected3.12
old10groups+READY32+owned-startup in fixed12group order, original public initial/
replay, fresh ORIGINAL AFTER, comparison and raw review. Original120/90/60/5/600
budgets and ONE absolute3600s reader coordination deadline remain fixed. Every
stage prints elapsed time and retains original errors/commands/native waits.
No old-command retry, selected runtime in agent, ACL/install/global/Gitwrite or
original deletion. Existing8root sample coverage; prior failed RP3 receipt/log
additionally pinned before/after with ordinary type/link/size/hash/fileidentity,
not a whole failed-temp-root/archive qualification. Failing controls before
implementation, same controller tests GREEN then fresh read-only handoff review.


RP3 successor finalhandoff2026-11-02:37controllerPASS; strictsamePID/claim, exact
actualruntimebudgets, atomicpublication, normalAFTER-before-inner-read, direct
hookFSM faulttests, sealed in-memory entry bootstrap cleared by nativeSHIP.
Live Reader37260/session58287 expires13:56:30IST; outer210eeacf... final exact
review SHIP, VerifyOnly/parsepass. One normalworkflow issued; root/selectedruntime
unrun. Fullstage completion pendingactualresult+parentrawreview, no oldretry.

### Approved RP3 fresh reader-session reissue, 2026-11-02

AUTH: user "I NEED TO TEST THIS NOW" within approved RP1-RP3 continuation.
Old reader expired at08:26:30UTC before normal preparation. Normal output absent;
no selected runtime or workload claim. Preserve expired service/claim/failure and
old outer. Do not reset deadlines or edit old guards. Use fresh sibling phase
rp3-ready-20261102-b, fresh normal root/session; copy exactly the reviewed helpers
with only factory root/contract and source contract literal bindings updated.
Keep 682-source recipe, accepted bytes, 12groups, budgets and history fixed.
Verify new family/source bindings and normal refusal, then fresh native read-only
handoff review. Launch one existing-access DATA reader; freeze one new normal
command inside original3600second window. No product tests rerun just for expiry,
no install/ACL/Git/original deletion. Full RP3 pending real run and raw AFTER review.
No-build leaves test blocked. Chosen fresh sealed session avoids old-output reuse;
changing expiry logic/longer window is outside this bounded reissue.

Fresh -b finalnativeSHIP;37metadata controlsPASS; actualPS7VerifyOnlyPASS.
Reader21032/session24359 expires14:17:24UTC. One new outer59ad944c issued;
actualselectedruntime/Stage/AFTERpending. No new scope approval required.

### Approved RP3 explicit actor output routing repair, 2026-11-02

AUTH: user invokes fable-method to SOLVE THE ISSUE after confirmed reader write
refusal. Current -b normalprep129.374s completed; reader failed InspectBefore-Claim
create, no CopyInputs/RunClaim/selected3.12. Preserve all -b files/claims/failures.
INTENT: code sends reader writes into normal ROOT; required handoff lets each
account write only its own outputs; approved no-ACL copy design uses separate
readable copies and exact source-to-copy/hash/BEFORE-AFTER verification.

Decision: explicit NORMAL_ROOT(short) and READER_ROOT(privatephase/outbox/session),
normal-only channel for preflight. Existing SnapshotSet accepts output path and
remains unchanged. No-build stays blocked. Shared-parent crosswrites still depend
on inherited token permissions and add path-length risk; generic path wrappers or
normal import rewrite records and obscure authority. Choose explicit two-root
routing with exact sealedpath/session/hash/PID/readiness validation.

Scope NEW .github/run-artifacts/rp3-routed-20261102/prototype9helpers, focused
controller tests/config/manifest/outer; existing Fable ledger/evidence. Product
source682recipe/default120/public90/lifecycle60/shutdown5/ordered600 unchanged.
Native design review FIX-FIRST endorsed architecture, required these gates:
- [ ] Failure-first reader-only output tests; route copy/bound/runtime/finish
      record references explicitly, no reader ROOT writes or normal outbox writes.
- [ ] Bind distinct canonical normal/outbox/channel paths and new session. Reuse
      copy primitives unchanged; independently require zero exception policy.
- [ ] Cheap two-account ping/ack preflight before expensive preparation; atomic
      publication, exactrecords, no new timeout/reset or native worker workload.
- [ ] Verify source/recipe/helper/history seals and focused/broader controllers;
      wrongactor/root/session/PID/link/hash/afterworkload/stalebefore/fault controls.
- [ ] Native read-only finalreview and externally sealed ONE normal command with
      sameabsolute3600sec reader lifetime; preserve all partial/failure outputs.
- [ ] Observe actualnormal preflight then full selected3.12 integration and fresh
      original AFTER. Parent rawreadback before fullRP3 complete, all broader gates
      separate. No auto retry/ACL/installation/global/Git/deletion/oldcommand.

### Approved continuation: fresh unused reader session, 2026-11-03

User CONTINUE resumes approved RP3 dual-root repair. Yesterday's reviewed routed
session expired before normal channel/root/preparation/selected runtime existed.
Keep its claim/service/failure/outer immutable. Reuse exact two-root workflow and
six unchanged helpers; fresh phase/root/channel/session and three literal contract
bindings only. Same682source/12groups/51controller proof and budget120/90/60/5/
600/3600 retained. Verify today's registry/source/config bindings, native exact
reissue/outer review; launch existing-access DATA reader only at freeze. One new
normal-account command runs cheap ping/ack before expensiveprep and original
integrated3.12 plus freshoriginalAFTER. No product reimplementation, old selected
attempt retry, new runtime/install/ACL/Git/original deletion. FullRP3 stillfalse.

Nov3 reissue12registryPASS; nativeSHIP; live43132/tool47343 until17:59:19IST;
oneouter15a4feec issued. Actualnormalpreflight/fullRP3pending, notcomplete.

### Authorized reusable Git checkpoint, 2026-11-03

AUTH: user said "IF NOT COMMIT IT TO LATER USE, VERIFY IF ITS ALREDY COMMITED OR NOT".
Read-only Git comparison confirms RP2 localcheckpointe801c358 already saves8of12
current evaluated overlay files. READYrepair4files differ/are absent. Save a new
local checkpoint child ofe801 on checkpoint/rp3-verified-progress-20261103,
using isolatedindex/commit-tree/CASnewref so activefeeHEAD/index and sealedattempts
retainmeaning. Scope: exact4READYsource/tests, currentFableledger+selectedreports,
curated byte-exact snapshots of sourceacceptance/testreceipts/logs, routed9helpers/
7controls, preparation+realpreflight records and currentfailedpolicycause. Raw
privatehistory/venv/cache/datacopies/binaries/unrelateddirtyfiles remainlocal.
No-build losesunsavedprogress; activebranchcommit changes frozenHEADguards;
choose existing separatecheckpoint pattern. No source behavior change or fix of
consumedschemahelper. Preserve actualpolicy4fields versusverifier3 mismatch as
UNRESOLVED, fullRP3false. Verify candidate12overlayhashes, receipts/loghashes,
exactisolatedindex/tree/blobscope andref; commit only after concrete review.
No push, runtime workload, ACL/security change, reset, deletion or old retry.
