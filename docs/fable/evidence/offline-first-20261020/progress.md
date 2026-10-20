# Offline-first local build progress

Status: PARTIAL_IMPLEMENTATION_NOT_RELEASE_READY. Basis c398be73e9e5eaa14de9e870c7787f53605afd6f.
Local Tasks1-5 continue under the user's post-design instruction. No commit,
push, install, new dependency or native Beads/Dolt/model execution. Later user
amendment permits cleanup only of new test-owned temporary files in fresh scratch;
all pre-existing files and retained evidence remain protected.

## Retained test evidence

Private output root: `.github/run-artifacts/offline-first-20261020` in the source
checkout. Existing Git ignore covers `run-artifacts/`. Windows denied the
initial sibling folder; no permission/trust change was made.

| Scope | Retained child | Result | unittest.log SHA-256 |
| --- | --- | --- | --- |
| MI profile RED after correcting test fixture | tests-1c6f35ae1c1b4760b51277f60873e576 |9methods/11failing assertions,0errors |74fabc716a1631876c6bb82c71ca3e89bcf9fc549ecd818c363bd765b1be9e56|
| CM profile RED |tests-6c9154e0581142e7a8fec4e73da7a967|4fail/0errors|58111669b21749f2b058fc39be4358a3a116a286763b3be338e7f4973e982bf8|
| MI focused profile GREEN |tests-086a375b1d2e4b438c7d735b3d67dc9d|9/9|d9e2b33b1a65c93022ec79e5e96fa39e425e29ffd851b2fa67f715e1bbe15fd0|
| CM focused profile GREEN |tests-225972dd9ebb410c9f0cb74ff638ad36|4/4|878c04e7a7f08d21977cb1ce0985ff0c6ed2ae8daa33e17677dfc1ee080bc570|
| Lifecycle RED |tests-cd1bceac593243d7b405da5d1ba309ad|3methods,1fail+2errors|da5d9faeca4fb4e7d4febbf0d34dc129dfdb86fd21fb52b41a81ff246ccdf9ee|
| Lifecycle initial GREEN |tests-400f6576b6d242fe92336b1be73871dc|3/3|2880bac8fa1a7715fb688e83b703915caceb58a0cddff667c48d58248e5acf38|

Each child retains Receipt.json, unittest.log and test-owned directories. The
runner's no-cleanup adaptation is not unchanged CI or OS-level containment; its
Python audit hooks do not propagate automatically to subprocesses. SQLite may
perform transient engine housekeeping. Initial MI fixture setup error is also
retained in tests-6cb1a3c73419466593062e16b5d53f51; it is not a product defect.

## Intent, proof and limits

The new offline-first-v1 profile must refuse supported native execution and new
native acceptance before transport/authority consumption. Historical granular
qualification and readable disk records remain factual. No runtime enable flag
is introduced. Missing/malformed profile is a refusal, not fallback authority.

Lifecycle controls reproduce leaked parent streams on failed Popen and show
why sequential session close can mask the original error and abandon a sibling.
The repair initializes owned resources before construction, stops all owned
workers before disposal, joins the writer, and retains original exceptions with
cleanup notes. First3 controlled tests pass; this is not Windows3.12 runtime proof.
The historical failed Windows log contains an output-handle WinError32 finalizer
and unclosed rb+/rb streams. It supports the resource-lifetime hypothesis but
does not by itself prove every original failure's cause.

Tasks1/2 remain in progress. Pure protocol-model compatibility review, wider
regressions, actual selected-runtime checks, portable public harness, final
instructions/version, successor manifests/ZIPs, clean extraction and fresh final
review remain. Historical manifests are intentionally unchanged at this stage.
Exact-commit CI and installed-copy use require their separate later authority.

## Resumed source correction and acceptance

- MI profile16/16 unmocked: tests-c1e6fea0fcfd4ca3869384026736b5ad,
  log SHA d9f5196fcbb9114d32aa58b98ee70634fbb57e59da9ad9af145aad285d8ab10a.
  CM profile5/5: tests-335080066c9d420495b88c3808ca5a50,
  log SHA731c1b98064b91962c1f31ef6add64bb5996217ea24cccff741702813eda85bb.
- Lifecycle6/6: tests-9bf6df9fd65945c4bf9d89252d28985e,
  log SHA476a7246e07c9e3786120301c3f4a6b49d2bba26001bfae62924f08330b37c5e.
  Controlled processes plus a real writer thread; not actual two-worker3.12 proof.
- Harness16/16: tests-e7eaa590509e474585596cd4373b411c,
  log SHA134d538245de921059ebb9282345224445a2b5d196da55c5b40b0c7c00c5d1f3.
- Corrected portable core: acceptance-core-final-source/Receipt.json,
  SHA13be156376c33d5ab8949dde9d35572e96a0d79701fa81c9a3ddba636aa8aa29.
  Eleven checks;8 literal arms/fresh replays;4 coding tests. Discovery0/8 and
  mandatory8/8 are separate. PASS_CORE_ONLY_RUNTIME_UNVERIFIED; source/evidence
  accounting is mechanical, not AI comprehension or semantic completeness.
- Prior reviewer cleared Task3 source corrections after RED->GREEN for exact
  structured safety-refusal causes, retained timeout/spawn streams and oracle/
  source/runtime binding. This is bounded source review, not whole-release approval.
- Preserved protocol-model suites: observation19, pilot9, raceharness132 and
  offline-sequence27 pass. Local policy mocking is explicitly MODEL_ONLY, with
  fake transports; no real native backend/claim/merge is qualified by these tests.
- TWINS: hard-coded sibling scratch paths existed in test_practical_cli.py and
  test_practical_execution.py only in the searched test trees. Both now select
  the test invocation's temporary root. Retained stack proved PermissionError
  retry in Python3.14 tempfile.mkdtemp; CLI10/10 passes after correction.
- A fresh isolated WindowsApps runtime probe cannot start in this agent account.
  No reinstall/substitution/security change attempted. Actual runtime checks need
  a new reviewed normal-account continuation, not an old consumed N3 command.
- Full companion v2 run213 tests:212 pass,1 historical R4 manifest drift failure,
  no errors/skips. Broad MI rerun after model-compatibility corrections underway.
  No final source/extracted/CI/installed or whole-skill completion claim.

## Current broad baseline and bounded reviewer disposition

- MI broad retained run: tests-53ae3515ec0e4ae6a27ca0a25104ddab;
  log SHA43cf3e30aeba83332b27f9a6477bb41e36b68cf916f8d5530cc2d7a0f2b00395.
  686 discovered,2 preservation methods explicitly excluded,684 ran:626 ordinary
  passes,54 skips,1 expected failure,1 failure and2 errors. Remaining failures:
  test_native_containment grandchild capture reports tree-sweep taskkill exit1;
  native_paths two tests cannot obtain Windows short form. These are recorded
  host observations, not hidden/skipped/fixed or a full-suite pass.
- Fable Sol native read-only reviewer offline_followup_review cleared the active
  profile/helper and model-compatibility scope only. Reviewer independently
  inspected exact refusal helpers, dispatch/ledger guards and fake transports,
  confirmed retained profile/model logs and no product import of model_policy.
  This bounded SHIP verdict does not cover numerical runtime or final release.
- Task4 successor consumer integrated in both packages and CI. Six RED->GREEN
  fixture contracts: tests-36627ef009cb48a2b13f181c4a7dbb3e,
  log SHAebcb560266fe9c396e61aac80bffb5b327cb399691aaa10d73078de5fad9e77f.
  Pointer is OFFLINE1-CONTENT.json; active missing/corrupt never falls back toR4.
  All previous manifests remain hashed package inputs. No OFFLINE1 list/archive
  generated yet. Missing successor is an intentional BLOCKED release gate, not
  an assertion to suppress. Engine metadata/instructions remain old candidate
  versions until finalization; no m13 release claimed.
- New offline_host_validation + retained_unittest implement a future fresh host
  check of the existing selected3.12 runtime and portable24-arm acceptance.
  Five initial host-guard regressions pass; independent host-code review pending.
  No old N3 command, selected runtime, install or host evaluation was run here.

## Host review correction checkpoint

- Reviewer required three corrections: exact non-vacuous Prepared schema/input
  set, physical rather than lexical output containment, and owned-tree timeout
  capture. Each accepted; retained RED in tests-7937506bbc5b4e13a0b5da9f50052425.
- Corrected host regressions8/8: tests-61f7d88bc39f413ba2ccb380e4a19440,
  log SHA613de84f88010e4dc44074cbca301212783a472a078234bf6bac592c4489be25.
  Alias and failed-capture controls are synthetic; they do not prove actual Windows
  aliases or descendant termination. Actual containment and short-path suites
  are mandatory first normal-host gates, before any numerical retrieval suite.
- Source package inventories and exact controller/worker/helper/fixture file sets
  are required before output creation. A correctly hashed incomplete document now
  rejects before child launch and output creation. Hash consistency is NOT producer
  authentication. Strict platform realpath resolution has no lexical fallback.
- Host controller uses existing generic Python process-tree capture, not a native
  backend. Every command must report complete, error-free, tree-contained capture;
  uncertain timeout streams and failures stay retained, never a successful receipt.
- Fresh public no-worker acceptance after physical-path correction:
  acceptance-core-physical-guard/Receipt.json,
  SHA69cd535b60060351c5bf93cdd20ab87e47e134eede11ec1eca72014032a5c18e,
  11 checks/8 literal arms, PASS_CORE_ONLY_RUNTIME_UNVERIFIED.
- Current fixture contracts6/6: tests-18f0de5f3f5f4cccaee74a0ac4b66418,
  log SHA2e715ac546aeb8801a4c2a7b0dce0c688850eef9d2f01c735c38d00771b7bd53.
- Current harness16/16: tests-15fa577dcb9d4452b692d176371ef8ca,
  log SHA158918259cfc00f4d102a302d0a4b315609c2dd42dc176c14448587715563dc9.
- Companion legacy21/21 (cm-legacy, logc674ae3cc20305d34d986b0effc580cfa00efdf7ed44bdb09afca3e72a3923a9).
  Companion v2 213:212 pass/1 missing OFFLINE1 error (cm-v2-after-content,
  log96b44707ac88c0f697197c22be350d0dc3253c4a117b42941c1ec47f4b5eb40e).
  MI legacy21:17 pass/4 socket.bind errors (mi-legacy,
  log7a5bb08a1757e361691d2f6ac05911531190617a8084e86793e82f25888ea1f5).
  The MI legacy errors are the runner's explicit no-network guard refusing their
  local fake HTTP fixture; not observed product faults. No guard bypass was used.
- All source/historical SKILL prefixes and old release directory/R4 lists remain
  unchanged at the preservation check. OFFLINE1 exact-content test blocks honestly
  on absent successor, not an early regenerated packing list. Final runtime,
  packaging, broad clean-source/extraction, CI and installed use remain unqualified.

## Frozen host gate (not executed)

Re-review closed the additional prepare-output and optional external-consumer
gaps. Host controls10/10, then whole repository contracts65/65 in
tests-3499e2d0e9b1418a85081e271ba1d2d2,
log SHA0a24953f7c8e41ce90d2b161bbcd6e0ec8cde872983c5adf9acaa675892b844d.
The independent reviewer returned bounded SHIP for issuing the normal-host gate,
not actual host behavior or final release. See review-disposition.md.

Private evidence root remains .github/run-artifacts/offline-first-20261020.
Prepared: Host-Prepared-20261020-a1.json,
SHA7ce4922f4879a0e258f23c65ef8239dd30f2173a216acd30476bf093780ea4c4.
Launcher: Run-Offline-Host-20261020.ps1,
SHAf57a03a8ba028495301705509723a6c284fa3d550d70e025f0bfad4fc66fd0f7.
Launcher VerifyOnly passed external hashes without Python/worker/evaluation.
Output host-validation-20261020-a1 must be new. No host run/attempt occurred here.
Fresh scalar-only interpreter probe in this agent session exited1: No Python at
the existing environment's WindowsApps Python3.12 base. It performed no numerical
imports, retrieval or host attempt. Normal-account execution is still required;
no interpreter substitution or reinstall is authorized or attempted.
Source basis remains c398be7 plus current uncommitted changes. Packages, helper
bytes and fixtures are frozen for this gate; docs updates do not alter its inputs.

No new commit/push, installed-copy replacement, final archives, native qualification
or whole-skill readiness. Important remaining gates: normal host results; resolve
full regression environment limits; finalize source and paired release; clean
extraction/full source/exact-commit CI/fresh final review; separately approved use.

## SUPERSEDING host-a1 outcome and continuity commit

User ran host-a1 once. Parent verified receipt01934889c0a87314f14fcc8971b503d92f7d535ad52911c964bc389d2569f79d,
all5suite receipt/log hashes and10 command streams. Actual3.12, Python containment,
short-path, profile, lifecycle and distributed suites passed36run35pass1POSIXskip.
The next preservation check stopped BEFORE advanced/completion/24arm acceptance.
Current inventory: MI6added .db files under literal %SystemDrive%/ProgramData/
Microsoft/Windows/Caches, no baseline modified/missing; CM unchanged. Caches intact.
Both worker env builders omit SystemDrive/ProgramData/ALLUSERSPROFILE; causal
writer/environment mechanism remains a hypothesis, not a controlled reproduction.
Read derived/offline-first-checkpoint-20261020.md and host-a1-findings.json for
exact paths, hashes, scope, retained artifacts and ordered resume instructions.
Old host-a1 and N3 commands must not rerun. No baseline/guard weakening or deletion.
User authorized LOCAL checkpoint commit only to preserve work before token limit;
no push, code-fix/new host attempt, package rebuild or installed-copy action here.
