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
