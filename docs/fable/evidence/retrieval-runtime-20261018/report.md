# Current N3 checkpoint - ACL partial4/57; local commit authorized, 2026-10-19

**Current status: ACL_PARTIAL_4_OF_57_STOP_FOR_ARCHITECTURE_REVIEW.** N3-A's
previous host installation/import/positive control is observed; N3-B/C evaluation,
29runtime tests and final N3-D review are not complete. No release/install claim.

User authorized a local commit of all pending repository changes and specifically
approved normal-account read access to19folders/38files while keeping all checks.
No file/data deletion, push, code hiding/disabling or evidence exclusion is allowed.
This current section supersedes the historical statuses/commands retained below.
Do not run any historical one-shot command from this report.

Host receipt b7b0b4e39282a7b998fb168e3cd0f1aa333e2d5674f322a8ef38cca401bd4d5c
records19AccessDenied directories/38unobservedpaths. All38 are present and hash-match
in the owning agent account. Owner-restricted tempfile ACLs and suppressed rglob
scan errors explain current visibility mismatch; the original preflight inventory
was not retained, so exclusive historical causation is not claimed.

Observed ACL execution, with every attempt retained:

| Attempt | Result | Permission effects |
| --- | --- | --- |
| PowerShell Set-Acl | Audit-security privilege refused |0|
| Access-only .NET persistence | First folder written; raw descriptor check stopped on Windows AI metadata |1folder|
| Reviewed metadata-aware post-check |3more grants; raw pre-write child check stopped after parent normalization |4total:2folders/2files|

**53grants remain:17folders and36files.** Current state matches the retained partial
receipt exactly; old access entries/owners/protection and all38filehashes are intact.
Normal-user readback is still UNVERIFIED. Three stopped write cycles require an
architecture discussion; no fourth attempt occurred. Native review approved the
bounded plans, not successful execution; parent observations overrule any success
inference from those reviews.17prior validator controls passed; not N3/runtime CI.

Private evidence directory (retained outside Git):
`build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/permission-read-grant-20261019/`.
Original Before.json SHA4894b3826f7107b1de83e1ae6efd21b5044bd68316e3b0f04278729f94f3327a;
After-Normalized.json SHAffc984df4a75234c1d12b5872b9a75ad73fc1274b7958135cad58da7e0a341c0;
Checkpoint-Partial-20261019.json SHA4febc0bfd6978abcaf7ee4cd10cb5f3869b5ff9eab85128f84afe299a84aea6f.
The latter records4granted/53pending and38unchangedhashes. Old helpers/receipts/
claims, temporary audit contents and original evaluation baselines are preserved.

Recommended next design for approval/review: pending files first, parents last,
with a parent-normalization regression and exact old-permission invariants. It is
not implemented or executed. Local commit authorization covers only the four
pending Fable records, not private environments/raw receipts or a public push.
Committing changesHEAD while the original N3 runner pins0584a89; no stale runner,
guard bypass, baseline replacement or retry is authorized. Source/installed skill,
capabilities and release packages remain unchanged; no new qualification flag is
activated. Native Beads/merge/generic-write qualifications remain false. The
pre-existing narrowly qualified shared-claim protocol remains true and unchanged;
it is not qualification of this N3 run, the practical fence or a finished release.

Fresh precommit content verification: all458protected project/N1/N2 files and
1,015pre-existing non-venv N3 files match the original inventories. All529repository
paths remain;525outside the four authorized Fable records hash-match. The original
plan/resume prefixes and entire earlier report suffix remain byte-for-byte intact.
State JSON retains the previous checkpoint values alongside corrected current status.
Private Verification-Final-Precommit.json records these read-only observations;
no skill suite, worker/model, native database or new ACL write ran in this check.

## Historical checkpoint log - preserved; commands below are not current instructions

# N3 isolated retrieval setup — partial execution, 2026-10-19

Current status: **N3_A3_PREPARED_OFFLINE_VERIFIED_HOST_CONTINUATION_READY_NOT_INSTALLED**.
The approved inputs and full environment baseline are prepared. Agent identity
stopped at the venv launcher (exit103, base alias not visible), before any install.
The exact guarded normal-host continuation passes validation;75selectedoffline
checks pass. Independent finalcode review is unavailable, not passed. Earlier
checkpoints below remain historical; see the latest N3-A3 update at the end.
Previously, the normal host created
and verified the one isolated Python3.12.10 environment, then its one permitted
dependency-resolution command failed during Git clone. Installation, numerical
imports and real retrieval remain unobserved. See the latest host update below.
This is not
installation, real retrieval, search-quality, native-fence or release proof.

## Authority and unchanged basis

The user approved N3-A through N3-D and then explicitly allowed removal of
**new installer-owned temporary installation files only**. All pre-existing
source/data, evidence, environments and installed skills remain protected.
No product repair, dependency-pin change, package rebuild, commit/push or
installed-copy replacement is included.

HEAD remains `0584a89f11bfeec4c9ae8caa81f4492cf10c2abb` on the development
branch. The approved plan is the N3 section of the existing practical-fence
plan; its previously reviewed immutable snapshot is retained privately with
SHA-256 `cdf1cd7fa28cbee40d603572929f2b2adf0d71bd7ccab6aec66ca2a35a2a5c9f`.

Private artifacts below are relative to the sibling `build-validation/` directory,
not Git deliverables. They are retained local observations, not authenticated
producer attestations or a portable skill release.

## Observed work

The table below records the initial agent checkpoint. The latest host update
supersedes its no-environment/zero-resolution state; the old receipt remains
unaltered as history, not a current instruction to retry.

| Check | Observed result | Boundary |
| --- | --- | --- |
| New private harness controls | 21 tests passed, zero failures/errors/skips; prior failing controls retained | Synthetic validator controls plus one actual stdlib child I/O test; not Semantica retrieval |
| Existing selected host contracts | 22 tests passed, zero failures/errors/skips | Same bounded selection as N2; not full discovery/CI or the seven real-worker tests |
| Source freeze | Four source files match the original N2 oracle; same four questions/required-source obligations; canary excluded; fixed bounds retained | Input preparation only, no question retuning or query execution |
| One setup attempt | `py.exe -3.12 -B -m venv <new-run>/venv` returned 101 | Launcher started; pinned Python child could not start: Access is denied |
| Environment / dependencies | No environment exists; zero resolution/install commands started | No installation success, numerical import, handshake or worker control claimed |
| Preservation | All 528 original repository files retained; 525 outside the three authorized existing Fable records hash-match the before inventory; six prior evidence identities unchanged | Repo/source and named prior seals; not an OS-wide third-party filesystem attestation |

Original blocked run:
`n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/`.

Its immutable `Setup-Receipt.json` has SHA-256
`0b1e5fde9b8899474c21d46796b72e6dd2184676baa20abdb1a23f74df061dfd`.
The exact launch diagnostic and process status are preserved under
`01-create-venv/`. This is not a Python/NumPy/Semantica defect diagnosis: the
selected interpreter did not execute. No ACL/security change, alternate
interpreter, second environment or install retry was attempted.

Controls: `Test-N3-Retrieval-Harness-20261018.py`.
Latest green run: `n3-harness-controls-27af338214f744f39846846bb6c28dd6/`.
Harness implementation: `N3-Retrieval-Runtime-20261018.py`.
Existing contract run: `retrieval-contracts-c27b793ddfd442bb9dce8d8b12c1e0c1/`,
receipt SHA-256 `729c5ededa2ec79bab56be30f5193a90a19b4bfbbb656e35c25b69e78f292197`.
Measured preservation: blocked run's `Checkpoint-Preservation.json`.

The first new PowerShell preservation view encountered ConstrainedLanguage's
`GetEnumerator` restriction. Its zero unchanged count was invalid, discarded,
and replaced by a fail-on-error Keys-based comparison. One early new control
also errored on its not-yet-defined pin before being corrected to an explicit
missing-feature assertion and observed RED-to-GREEN. All such runs remain.

## Initial pending work at the agent checkpoint (historical)

1. N3-A normal-host continuation of the **same empty run**: create the one
   environment, resolve/install the unchanged 50-package snapshot once, check
   numerical imports/identity, public status and actual retrieval control.
   A started resolution/install or partial existing environment forbids this
   continuation. No automatic fallback or silent unpinning is permitted.
2. N3-B actual public lexical/LSA ranking and independent source/byte metrics.
   No returned-source scores or quality measurements exist yet.
3. N3-C fresh actual-worker replay, refusal/forgery cases and the seven required
   actual-runtime tests in addition to the 22 host contracts. These are blocked,
   not skipped successes. Full B/C orchestration is not yet implemented or run.
4. N3-D fresh independent review, final preservation recheck and observed-result
   handoff after real execution. Both fresh-review attempts hit model capacity.
   No alternate model was substituted. This is unavailable review, not a pass;
   `Independent-Review.json` retains it. Prior plan review is not execution review.

The hash-bound `Run-N3-Retrieval-20261018.ps1` host entrypoint is limited to N3-A
setup/positive control. Its `-ValidateOnly` file guards pass without setup. It does
not automatically claim N3-B/C/D or whole-skill completion. Retain its printed
receipt even on failure and do not rerun a failed setup. The scope approval is
already recorded; no repeated milestone approval is required for N3-A–D.

## Decisions and safety limits

- Reuse the existing Fable ledger, private retention pattern and development
  checkout; no additional governor/worktree, automatic commit or scratch deletion.
  Cost: explicit receipts rather than Superpowers' automatic workspace bookkeeping.
- Treat the launcher's process and the Python child's launch separately. The
  retained exact, hash-bound access-denial diagnostic plus absent environment,
  absent resolver/install and current identities allow one normal-host handoff
  into the same empty run. Any other failure stops rather than enabling a retry.
- Preserve selected-test scope. Full discovery, model/RealBenefit fixtures and
  native tests are not authorized merely by a general skill testing guideline.
- No provider/model inference, Beads/Dolt run, packaging, promotion or Git write
  occurred. Capability flags remain unchanged. Semantic truth, learned embedding
  quality, real-project coding benefit and installed readiness remain unverified.

Parent final inspection found that a generic Python3.12 check could accept a
different patch from the observed3.12.10 selection. A new falsifier was observed
RED then GREEN; the helper now validates exact3.12.10 and isolated prefix/user-site
**before dependency resolution**, then checks it again with the numeric imports.
That setup path remains unexecuted because the interpreter child was blocked.
Helper final SHA-256:
`062b298db5800b84477d15fa36a7f37814e250d44e0073600a6c3227aeac040e`.
The original blocked setup receipt correctly binds the earlier helper bytes;
it is retained as historical evidence, not rewritten to claim the new code ran.

## Latest host update and root cause — 2026-10-19

The user's host command was correct. Its saved Host-Setup-Receipt.json exactly
matches the supplied SHA-256
`f556ab5071892b5ae1d4daf0765fd5b74433aa76496b0998da871808f471571e`.
All six retained stdout/stderr artifacts match that receipt.

- Environment creation passed. Identity passed: Python3.12.10, isolated prefix,
  different base prefix, user site disabled; pyvenv.cfg excludes system packages.
- Dependency resolution started and failed before completing a resolution report.
  Pip invoked Git to clone the unchanged pinned Semantica source; Git exited128
  with `fatal: '$GIT_DIR' too big`. The pip resolver exited1.
- The actual install command never started. The venv currently contains only
  `pip-25.0.1.dist-info` among distribution metadata; no Semantica/numeric imports,
  worker handshake, positive retrieval or N3-B/C run occurred.
- The helper put installer TEMP too deeply under the long private run path.
  The resulting Git directory is224ASCIIcharacters. This is a setup-layout
  defect, not a user command, missing credential or observed package-version
  incompatibility. The preflight should have caught it before invoking pip.

Read-only probes on installed Git2.53.0.windows.1 reproduced the boundary without
creating a repository, changing configuration or using network:

| Git directory argument | Observation |
| --- | --- |
| 220 characters | Passes the length gate, then correctly refuses the nonexistent repository |
| 221 characters | `fatal: '$GIT_DIR' too big` |
| Original224characters | Same length refusal |
| Original224with process-local core.longpaths=true | Same length refusal; no global config was changed |

The exact-version upstream [setup.c guard](https://github.com/git-for-windows/git/blob/v2.53.0.windows.1/setup.c#L1021-L1022)
checks Git-directory length against PATH_MAX minus40 before repository validation.
The source and installed-binary controls agree on the immediate cause. This does
not prove the remaining dependencies will resolve after a path correction.

Evidence: same run's `Host-Resolution-Diagnosis.json`. The first diagnostic probe
mistakenly batched arguments and produced Git usage; that was not accepted as a
path test. The corrected separated-argument probes above are the observation.
All528originalrepo files remain;525outside the three existing Fable records
match the original inventory. No source, dependency pin, runtime helper, old
entrypoint, package, installed skill or Git state was changed during diagnosis.

### Next: bounded N3-A recovery amendment, approval pending

The previous one-shot resolution allowance has been consumed. **Do not rerun the
old host script**, recreate/clear the venv, change permissions, enable global
long-path settings, replace VCS provenance with an archive, or silently unpin.

Recommended amendment: preserve/reuse the existing venv and all old artifacts;
create one exclusive short installer workspace at
`C:\Users\sakth\Documents\Codex\n3-install-<new8hex>`; record its owner/run identity;
add a UTF-8 Git-path-length preflight with headroom; retain the original helpers
and add a separately named recovery helper. Allow exactly **one additional
non-installing resolution command** using that short TEMP/TMP, the same private
cache and unchanged absolute/hash-bound requirements. Only if its report passes
the existing identity/origin/scope checks may the **one still-unused install**
proceed in the same venv, followed by the original N3-A imports/positive checks.
No second environment, package fallback, provider/model or installed-skill work.

Alternatives: remain blocked (safest no-build rollback, no retrieval progress);
use a one-letter temp child inside the current run (reduces this Git path to211,
but leaves only9characters below the observed gate); use the short owned workspace
(recommended headroom without changing security/system Git settings). Do not use
an archive/local-path install that would discard the worker's required VCS
commit provenance. This is a layout repair, not a new retrieval mechanism.

Weak link: dependency availability/ABI and longer installed-package paths remain
untested. Cheapest falsifier: reject overlong predicted paths offline first,
then inspect the one new resolution report. Any failure stops without another
retry or pin change. Cleanup remains limited to newly created installer-owned
transients in the explicitly owned new workspace. All pre-existing data and
every prior failure are retained. No recovery helper/retry was executed or
authorized by merely receiving the user's failure receipt.

N3-B/C actual evaluation/orchestration remains unfinished. N3-D independent
execution review remains unavailable from the prior two capacity failures.

## N3-A2 approved build and current handoff — 2026-10-19

AUTH: user approved "Approve bounded N3-A2 recovery (Recommended)". This is now
the execution authority for the named amendment, not a pending approval. It
does not authorize another environment, deletion of old data, pin/global-Git/
ACL changes, provider/model/native calls, publication or installed-skill changes.

Built privately under the existing N3 run:

- `Recover-N3A2-20261019.py`: unchanged original helper and host receipt are
  hash-bound inputs; existing Python environment is revalidated; short TEMP
  ownership/ordinary-directory and UTF-8 path-budget checks precede one new
  resolver; exactly one attempt reservation and one host claim prevent repeats.
  The original pin/origin/version checks, numeric imports and actual worker
  positive control remain required before a bounded N3-A2 success result.
- `Test-N3A2-20261019.py`:16/16 retained controls passed, no failures/errors/skips.
  Initial13missing-feature controls were observed RED then GREEN; additional
  early-error/handoff controls RED2toGREEN, and missing-temp refusal RED1toGREEN.
  These synthetic guard/fixture checks are not actual pip/worker qualification.
- `Run-N3A2-20261019.ps1`: one normal-PowerShell host continuation, pinned to
  the exact successor and observed agent-denial evidence. Its `-ValidateOnly`
  guards passed without creating the workspace or running setup.

The predicted VCS .git path is123UTF-8bytes,97below the installedGit220gate;
the helper refuses a prediction above160bytes. This is verified calculation,
not a successful new clone observation. Original21harnesscontrols and22selected
offline contracts also passed fresh, with no failures/errors/skips.

### Actual attempted work and disclosed harness repair

The agent start reserved `recovery-a2/` but could not create the approved short
workspace `C:\Users\sakth\Documents\Codex\n3-install-ef149e14`. The new directory
is still absent. An adjusted PowerShell New-Item diagnostic explicitly reported
`CreateDirectoryUnauthorizedAccessError` / Access is denied. No Python identity
child, additional resolver or install started. Stop agent-side directory retries;
do not change permissions or switch to another unapproved folder.

The first successor had a real early-error-recording defect: it assigned its
receipt path after workspace creation, so the initial console output had
receipt=null and lost that first exception. The exact initial source is retained
as `recovery-a2/Initial-Successor-11cc57df.source.txt`, SHA-256
`11cc57df9f41b04e06e766cbcfa84708934b8b48fbb5aac5a35d266eb4f8e768`.
Do not pretend the later directory diagnostic reconstructs the lost exception.
The current successor records its source/receipt location before creation and
retains preparation errors in finally; a real existing-directory failure control
proved RED-to-GREEN without changing that foreign directory's data.

The first PowerShell diagnostic's error formatter itself hit ConstrainedLanguage
on GetType. Its output was discarded; the adjusted formatter captured the actual
directory denial. All retained first attempts remain; no package operation was
spent by these local controls. A matching owner record without an ordinary
non-aliased tmp directory is also rejected; the owner fixture was corrected to
mirror this real workspace structure, not to weaken the expected refusal.

The exact observed boundary and first-error limitation are retained in
`recovery-a2/Agent-Workspace-Denial.json`. It permits the one normal-host creation
continuation only before any child/resolver/install/host claim, into the same
reserved recovery and exact short path. It grants no producer authentication
or runtime qualification. The host command creates the approved short workspace
itself; the user need not separately seed/adopt a directory.

### Verification and remaining boundaries

- New controls: `a2-controls-1f4293a7b94b4bd795f9739ff4ec1a26/Receipt.json`,16passed.
- Original harness: sibling `n3-harness-controls-87e62db4120345b49541d2ca972072f7/`,21passed.
- Existing contracts: sibling `retrieval-contracts-80123014060d461e8200bdf1fdab8cb8/`,22passed;
  receipt SHA-256`cdffd32fddefc27841eca01dbaaa9eab528faa3b13b3a3a37f5e20fa353e1f70`.
- One native read-only Fable review was requested for this amendment; the selected
  model again failed at capacity. No model substitution or independent pass is
  claimed. `recovery-a2/Independent-Review.json` records the unavailable review.
- Parent checks validate the original sources/receipt/executable, one-shot guards
  and named regressions. Full CI, real clone/install/numerical imports/retrieval
  and N3-B/C/D remain unverified. No third-party OS-wide sandbox is claimed.

Current successor SHA-256:
`eba239e52a1be5386b6040f10225892d7b85d3e2a827cfb176060b5a99b86e5d`.
The old helper062b298d, original host receiptf556ab50, original dependency pins,
old script and prior evidence remain unchanged. Native/release/install-skill
flags remain false. All existing data and every failed artifact are retained.

Next: run the already-approved `Run-N3A2-20261019.ps1` once in normal PowerShell,
then inspect its retained `recovery-a2/Receipt-host.json`. Do not rerun a failure.
This is a host-execution requirement, not another approval gate for N3-A2.

## Latest N3-A2 normal-host result — 2026-10-19

The user ran the command correctly, once. The saved `recovery-a2/Receipt-host.json`
SHA-256 matches the console:
`e857e7299fbd8279d2abf832bc57d79a34aa58e200ab8ccc85b8d8140b1340b5`.
Both identity-host and02-resolve started and exited0; their Result.json records
and all4stdout/stderr byte counts and hashes match the receipt. The short path
therefore worked for this actual clone/resolution; it is no longer prediction
alone. Existing isolatedPython3.12.10 and owned short workspace remain intact.

The resolver wrote `recovery-a2/Resolution.json` (914300bytes), SHA-256
`92fca79b1e94d05cd4ad97295a1cd61bf1596a6cd464c983dae45f5280973462`.
The private successor then used `read_text()` without an explicit encoding.
The controller's cp1252 codec rejected byte0x81 at29148. This defect is in our
helper, not the user's command, credentials or dependency download. The local
pinned pip25.0.1 code explicitly writes --report with encoding='utf-8' and
ensure_ascii=False. Reading the retained exact bytes as strictUTF-8 succeeds.

### Independent dependency-scope blocker behind the encoding failure

All50approved dependencies are present with exact expected versions and none
are missing or duplicated. The saved resolver output contains53packages:

| Addition not in approved snapshot | Resolved version | Dependency marker in saved metadata |
|---|---|---|
| colorama | 0.4.6 | loguru sys_platform=='win32'; tqdm platform_system=='Windows' |
| tzdata | 2026.5 | pandas sys_platform=='win32' |
| win32-setctime | 1.2.0 | loguru sys_platform=='win32' |

The unchanged scope validator correctly raises E_N3_RESOLUTION_SCOPE_OR_PIN.
Do not call this an approved/validated install merely because pip exited0.
No original or recovery03-install directory exists; site-packages still has
only pip25.0.1 metadata. The original additional-resolver allowance is consumed.
No automatic retry, third resolver, lock change or pin substitution is allowed.

### Bounded offline correction and tests

Added private `Inspect-N3A2-Resolution-20261019.py`, leaving both original setup
helpers and every receipt/report unchanged. It reads JSON explicitly asUTF-8,
binds the actual saved report/receipt/helper hashes, rechecks command logs,
executable/empty-venv/owner state and reruns the original strict scope validator.
It contains no resolver/install/worker invocation and only adds a diagnostic
folder when --save is requested. Local hash checks are not authentication.

`Test-N3A2-Resolution-20261019.py`:7controls observed RED7failures/0errors before
implementation, then GREEN7/0/0/0. Controls prove cp1252-breaking UTF-8 content
reads unchanged; malformedUTF-8/hash drift are refused; valid exact pins pass;
extra/missing/wrong-version/duplicate packages remain refused; the real saved
host report stays blocked for the3additions and no install is falsely claimed.
These are offline diagnostic controls, not runtime/import/retrieval proof.
Broader CI and earlier21/22harness/contract suites were not rerun for this
private auditor-only change; their prior retained results remain historical.

Retained GREEN receipt:
`<same N3 run>/resolution-controls-c7d531a9cea74482afee2c14d7cf4f92/Receipt.json`.
Retained diagnosis:
`<same N3 run>/resolution-diagnosis-a12e37b4818148c3b47f80fd8bfd7195/Diagnosis.json`,
SHA-256`ebc12741b52caf585c658ebfbf1938d480e7bd174a76998b37248d8a94658019`.

Read-only proposal check: adding exactly those3versions to an in-memory copy of
the expected50passes all53existing URL/origin/archive-hash-format/version and
Semantica commit checks. This is not file modification, user approval, fresh
download/hash verification or installed-byte proof. Existing50snapshot and
Semantica revision remain unchanged. The report metadata includes additional
optional/dev marker declarations; these are retained separately, not presented
as active requirements observed through new execution.

TWINS: the preserved original helper also defaults JSON decoding at resolution,
installation and streams reads; the recovery helper repeats those locations.
Do not rerun either helper. Any subsequently approved installation continuation
must use explicitUTF-8 for all external JSON inputs, not only Resolution.json.
No production source or dependency file has been edited to hide these twins.

### Proposed next bounded amendment — approval required

N3-A3: create a private Windows dependency overlay containing only
colorama==0.4.6, tzdata==2026.5, win32-setctime==1.2.0. Retain all50existing pins,
the exact Semantica revision, same venv, same short workspace and every prior
artifact. Build/test a successor install-only continuation with explicitUTF-8,
saved-resolution/hash/provenance checks and one exclusive unused-install claim.
Revalidate the saved53-package report; do not issue another dry-run resolver.
Use at most the original still-unused actual install, then pip check, numerical
imports, worker status and the existing real retrieval positive control. Stop
without resend on failure. No global Git/ACL/package/skill changes, model calls,
native Beads, commit/push, release or deletion of old data. Existing installer-
owned NEW transient cleanup exception remains confined to its owned workspace.

No-build alternative: hold setup, preserve the already available offline value.
Recommended overlay is the simplest sufficient Windows closure; ignoring
dependencies or widening acceptance to arbitrary extras is rejected. Weak link:
download/build/ABI and actual retrieval remain unobserved. Cheapest next checks
are exact saved53scope and no-repeat/UTF-8 regression tests before installation.
If any additional package/version is needed, stop and return to the user.
This amendment changes dependency scope, so N3-A2 approval alone is insufficient.

## N3-A3 approved build checkpoint — 2026-10-19

AUTH: user replied "Approve N3-A3 private Windows overlay and guarded
continuation (Recommended)". The50originalpins and Semantica revision remain
unchanged. Exact3additions exist only in recovery-a3/windows-overlay.txt.
Zero extra dry-run resolvers; at most originalunusedinstall in same venv.

The prior fresh native read-only reviewer returned SHIP for the N3-A2 diagnosis
and N3-A3 approval proposal only, not install/runtime/qualification. Its53-row
independent observations agree with the parent. Five preinstall gates are
adopted: full53scope validation before install claim, explicitUTF-8 at allJSON
inputs, savedStart.json command bindings, fullvenvinventory, and unambiguous
consumed-resolver fields. Summary: private recovery-a3/Prior-Diagnosis-Review.json.
A separate final review of the newly built installer code is pending.

Built privately: Install-N3A3-20261019.py, Test-N3A3-20261019.py and Approval.json.
Sixteen new controls observed RED16/0 then GREEN16/0/0/0. Parent also found an
early-preflight status-masking defect before any actual execution: lack of a
beforeinventory was reported as failed preservation instead of UNKNOWN. A17th
control reproduced RED1/0, then the minimal correction yielded GREEN17/0/0/0.
The refusal/failure is retained accurately without implying data damage or
permitting an install; all failed/control fixtures are retained.

Fresh regression: previous7saved-report controls,21originalharnesscontrols and
22selectedofflinecontracts all passed,0failures/errors/skips. Receipts:

- Same run a3-controls-94fc1d4c2fce4fe29bbffd4bce204005/Receipt.json:17.
- Same run resolution-controls-95e74681e64f46e6a7052626ab6418f4/Receipt.json:7.
- Sibling n3-harness-controls-d25b02f4be1542869423b034b7d36692/Receipt.json:21.
- Sibling retrieval-contracts-f4e77fa87ae54fdabf37104d077b8b2a/Receipt.json:22,
  SHA1fa02dd7b2aeb9b5a5f05d2ef626afea574ea6952fb542897150bafdf0a86b5f.

These are retained offline controls/contracts, not fullCI or worker/runtime
proof; the22contract suite explicitly excludes3separate-process/runtime cases.
One git diff command accidentally ran in the non-repo private run directory;
it only printed usage. It is rechecked at the actual repo before handoff; it
does not imply repository loss or a test failure. No source was mutated by it.

Installer design: validate saved53report and exactrecordedStart hashes, build
private53entry install input using52saved wheel URLs with SHA-256 fragments and
the exact VCS commit; preserve original50file and overlay. No --no-deps bypass;
no writes to existing pip-cache (--no-cache-dir). Fresh fullvenv files+directories
inventory and allrepo source hashes precede execution; exactprivateinput and
source/venv drift stop the command. Identity in selectedPython3.12.10 must pass
before exclusiveinstallclaim. Install failures/unknown delivery are never resent.
All olddata remain; cleanup is limited to already-approved new installer-owned
transients in the same shortworkspace. No actual install or worker has started.

## Latest N3-A3 execution and host handoff — 2026-10-19

The initial final-code review failed during remotecompaction with workspace
credits exhausted. After the user explicitly said CONTINUE, a same-role retry
failed selected-model capacity. No substitution or independent pass. Parent
verified code, primaryprotocol shapes, adversarialcontrols and actualoffline
preflight; preparation/identity proceed within existing approval with that
review gap explicit. Private Independent-Code-Review.json records both failures.
A resumed-turn filesystem grant initially blocked one patch before writing;
normal scoped permissions were requested/granted, no ACL/security bypass.

### Prepared inputs and actual agent boundary

Prepared.json SHAff0dbb7951ade69fc0c0310142f09fc033178279c73c6c9cdb7c79cd7146def1
binds oldinstalle719eda733aeefa94c08326b0bf16b3b171acdeb7eb4690c4712549eac655e7f,
privateoverlay5370d4e6, full53rowinput0c34e51a, Approval339bb283 and full861file/
107directory venvbaseline0f0fe363. Originalrequirements hash892900d3 unchanged.
Both --prepare and --inspect succeeded without starting any installer/worker.

One actual --start identity attempt started the venvlauncher(pid44544), exit103,
stderr130bytes exact "No Python at" its original configured WindowsApps base
alias, stdout0bytes. No 03-install or install-claim exists. Entire venvbaseline
matches byte-for-byte and repository before/after hashes match. Saved agent
receipt SHAee02b50e94cd7995a8cbef83d6ad23940efa3395f9c21c4f02a8ab73abc6d841;
stderr SHAa03fd5bce6a250abe3d2062bd544f81669721c8971286ce6c6f8f4dac2e474f4.
The old guard correctly refused because this is not process-startWinError5.

Read-only Path.is_file on the original alias is false in this agent session;
do not infer that the user's normalhost interpreter was removed. The original
host identity succeeded earlier, but currenthost accessibility is unobserved.
Primary CPythonv3.12.10 [PC/launcher.c](https://github.com/python/cpython/blob/v3.12.10/PC/launcher.c#L1850)
defines103as RC_NO_PYTHON and emits this diagnostic when GetFileAttributesW
cannot see the baseexe, before invoke_child. This supports interpreting the
recorded event as a launcher failure, not successful identity-code execution.
No basepath/pyvenv.cfg/ACL/toolchain change or agentlaunch retry was attempted.

### Exact host adapter, not a blanket retry

Continue-N3A3-Host-20261019.py SHAbef35cb458b1949e5b73222b070ead06e04362270195ce78ad691d80fc68152e
binds original source, Prepared, failedreceipt, Start/Result, both logs and full
unchangedvenv/input/source baseline. It accepts only the exact103event, expected
command, no stdout and no priorhost/installclaim. Ordinaryexit, differenterror,
anyidentityoutput, changedfiles or recorddisagreement remain refused. No input
selection/runner flag can skip these checks. Localhashes are not authentication.

The adapter leaves original installer, Prepared and failed receipt unchanged.
Import/validation does not alter the old predicate. Its sole --run invocation
temporarily adapts ONLY the process-local host predicate for this same bound
event, delegates to the unchanged original execute(host=True), and restores the
predicate finally. All original full53scope/identity/exclusiveclaim/hash/import/
runtime checks still execute. No additional resolver or install is authorized.
The host must demonstrate exact3.12.10/sameprefix identity before the one claim;
failure stops and retains data. This is a necessary bounded N3-A3 correction,
not a new native-fence mechanism or relaxation of package/identity validation.

8newhostcontrols observed RED8/0 then GREEN8/0/0/0. Fresh final results:

| Selected check | Passed | Retained receipt (same run unless sibling) |
|---|---|---|
| Installer controls | 17 | a3-controls-a1fd33b42c1f47648af3173b988be35c/Receipt.json |
| Exact103 host controls | 8 | a3-host-controls-9485efefdff84ae29fdb3832d5021fd2/Receipt.json |
| UTF-8/report controls | 7 | resolution-controls-ad5bb7903e90440e989c16b65da12ed7/Receipt.json |
| Original harness | 21 | sibling n3-harness-controls-e878e58f1b10473ba1e8792178a45970/Receipt.json |
| Selected host contracts | 22 | sibling retrieval-contracts-8de80d217fea441f98c41fb2171454da/Receipt.json |

Total75selectedofflinechecks,0failures/errors/skips. The22suite's3explicit
exclusions remain; no fullCI, numericalimports/realretrieval or learnedembedding
quality proof. Failed/redfixtures and earlier greenruns remain intact.

Run-N3A3-20261019.ps1 SHA7ca9ccfda810066b435b8b97f5d0cdcac24daf4bc31362b8a0a361901b41beac
seals source/adapter/Prepared/agentreceipt, refuses any existing host/install
attempt, validates first and then runs only the one approved continuation.
Its -ValidateOnly check passed here with no install or worker run. Expected
receipt is recovery-a3/Receipt-host.json. Run ONCE in normalPowerShell, not this
agent session. Do not rerun a failure, edit seals or use old A2/agent scripts.

Next host step is already approved; no new approval loop. It may download/install
only the approved53runtime packages into the same environment, then run pipcheck,
numericimports, publicknowledge-status and actualretrievalpositive. It changes
no installed skill, globalpackages/settings, originalpins/revision, APIcredential,
model/nativeBeads/Git state. Olddata remain; only alreadyapproved new installer
transients may be cleaned in ownedshortworkspace. N3-B/C and final N3-D remain.

## Observed N3-A success and N3-B/C preparation — 2026-10-19

The requested normal-PowerShell continuation succeeded. I independently checked
the retained evidence, not only the pasted summary. Same private N3 run:
`build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/`.

| Observed evidence | Result and boundary |
|---|---|
| recovery-a3/Receipt-host.json | SHA256 `7e3a4605c2892e1aaad5082ab52e11a2ea6b644ffb13d2790e6006b0d8e8598e`; all six commands started and exited0, no recorded error |
| Saved Result records and stdout/stderr | All12 byte lengths and hashes match; both WorkerClient stream triples match command outputs |
| Installation.json and installed versions | All53 packages match approved scope, saved origins/archive hashes and pinned Semantica revision; no original pin relaxed |
| Interpreter/numerical imports | Isolated Python3.12.10, no user site; numpy/scipy/sklearn/semantica/rdflib/pyshacl imports and finite vectors observed |
| Public knowledge-status and actual retrieval positive | Retry ranks first, score0.5773502691318908; other two score0; SHACL CONFORMS; lineage verified |
| Preservation during install | Repository unchanged; no pre-existing environment file changed/disappeared; old receipts retained |
| Installed runtime inventory | 17,273files/1,756directories/530,969,535bytes; Venv-After-host.json SHA256 `b7e12e360a434ffc39ecbc053483fa1efec7baae4f84b10010608ea44b660aff` |

This closes observed N3-A setup/positive-control requirements, not search quality,
semantic completeness, learned embeddings, native fencing or whole-skill release/
install readiness. The install allowance is consumed: never rerun setup. All
packets remain locally observed/self-reported, not authenticated attestations.

### Private N3-B/C harness and observed offline behavior

Only private harness/tests/evidence and the four already-open Fable records
changed. Product source, requirements/revision, SKILL/capabilities, release ZIPs
and installed skills remain unchanged; HEAD remains0584a89f.

Evaluate-N3-Retrieval-20261019.py uses unchanged public CLI, fresh-process
verify_pack API and unchanged29selectedtests. Discovery preinserts no required
units; mandatory delivery is separate. Four frozen questions/sourcebytes/unitIDs/
access/searchcaps remain unchanged. No copied target is imported or executed.
Raw WorkerClient descriptors are retained using the existing adapter; numerical
fixture pipes use existing tests, not separately captured WorkerClient streams.

14oraclecontrols observed RED-before/GREEN-after. Seven coordinator controls
observed RED for missing label/API-job checks then GREEN after harness-only
validation. Fresh14+7+21originalharness+22hostcontracts=64selectedofflinechecks,
0failures/errors/skips; not the29runtime tests or fullCI. Retained receipts:

- evaluation-controls-8b18c6e6c8b44aae9898afafea87012a/Receipt.json (14)
- evaluation-runner-controls-8ef37e6e249f4a2daae50688ee6fe5b4/Receipt.json (7)
- sibling n3-harness-controls-f64e7a29d8be48cbafb5629cb7248130/Receipt.json (21)
- sibling retrieval-contracts-11e041cf29f842f4a292217555a5e2d4/Receipt.json (22)

Actual public knowledge-project built4source/52node/170edge index, generation
`811de2debd37f875f3e2b2edb691cc75fbf1692bd01db7b8873b6c2a4019caab`.
No constructionworker was invoked, as expected for this Python-only corpus.
Its own writer lock was retained; no source or old evidence was removed.

| Frozen case | Natural-language literal required-file hits | Assisted error-phrase hits | Assisted logical bytes reopened |
|---|---:|---:|---:|
| freshness | 0/2 | 2/2 | 193 |
| unicode | 0/1 | 1/1 | 100 |
| approval | 0/2 | 1/2 | 98 |
| resume | 0/2 | 1/2 | 185 |

Literal substring is a weak baseline, not tuned lexical search. Assisted probes
are separate, never natural-language discovery scores. Logical byte counts are
not all physical disk IO. No ranked superiority follows from these zeros.

Eight actual public no-worker pack calls and eight fresh-process verifier calls
passed. Mandatory arms delivered all authored units in order with independent
range/hash checks; discovery inserted none. Parent-Literal-CLI.json SHA256
`738bffe32831f71e1d10ae903c07bd507776418e830c24edec921ef6db6ad670`.

Prepared.json SHA256 `ae96299c169076491dd238898e512448bdf6aaea0cd26daf6160cb146573d992`
seals runner `f935c0510aa9de44df4fe6838e1ec9aef3e8ce0f7537b28102da4fb4459a47c5`,
contracts `1970c7e0df83ea9bb5bb4b8cb1970ac48ff564f1990c32b8a8713e2b69d32161`,
frozen inputs, original-data inventories and new index. No ranked/safety run
has started. Fresh independent review requested, not assumed passed; prior A3
final-code review remains unavailable/not passed.

### Remaining host action, within existing N3 approval

The selected environment's original WindowsApps base alias was unavailable to
the agent in the retained prior attempt. No agent3.12 retry/security workaround.
Same-run Run-N3-Evaluation-20261019.ps1 -ValidateOnly passed without launching
the worker. Use it ONCE without that flag in normalPowerShell after finalreview.
It installs/downloads nothing, creates no environment, has zeroresolverauthority
and refuses repeatclaims. It runs frozen24arms, freshreplay, exactreason safety
negatives, unaffected-source control and29selectedruntime tests. Preserve every
result; stop on failure; never remove markers/tune the exam. Productdefects
reopen planning. Expected receipt: evaluation-bc-20261019/Receipt-host.json.

N3-D must assess actual host results, including discovery misses, before any
readiness recommendation. No model/provider/native/Git/release/installedskill action.

### Fresh review: FIX-FIRST; retained successor correction

The native reviewer completed read-only evaluation review. Three important
findings: degraded-literal publicpacks lacked external frozenquery/cap checks;
29test count was not exactID enforcement; firstcase OOV could raiseKeyError and
abort safety checks. Minor: false semantic_audit needed its own forgedcopy.
These are evaluator defects, not evidence that production retrieval is broken.
N3-Evaluation-Review-1-20261019.md retains findings/boundaries. No retroactive
independent pass for the interrupted earlier A3review.

Oldcontracts1970c7e0, runnerf935c051, Preparedae96299c, launcher6401a9e5 and all
literal/index/faileddiagnostic evidence remain unchanged. Oldevaluationroot is
superseded preparation-only; do not run Run-N3-Evaluation-20261019.ps1. No old
hostclaim or hostreceipt exists. Superseded-Preparation-Only.json explains this.

Within approved N3scope, newv2contracts515bd5e3 and runnerv2 259e569d use new
evaluation-bc-v2-20261019 root, not another environment/install. Reuse same
installedruntime and frozenexam. New20controls RED20before/GREEN20after;
7v2coordinatorcontrols pass. Fixes: everypublicpack gets externalfrozenbinding;
comparisonmode/publicmode/backend/locator are distinct; exactordered29testIDs
construct and validate suite; deterministic successfulreport-required safety
basis, or explicitNOT_EXECUTABLE/partial without unrelatedKeyError; separate
falsecoverage/falsesemantic-audit actualverifier probes. Freshreview requested.

Actualcounterexamples: fresh old no-worker verifier accepts internallycoherent
wrongquery/direction/cap; newexternalexperimentvalidator rejects allthree. Old
suitevalidator accepts29unapprovedIDs; v2refuses. Binding-Falsifier-v2-20261019.json
SHAc0df42f91f0589962b41ab7087b471fefe1df050c6f8b482557149e7379a4b9c.
Initial diagnostic stopped on incoherentdirectioncopy (only one of twofields
changed), correctly refusedE_RETRIEVAL_DIRECTION; allcode/logs retained and
corrected in a newhelper, no productchange. No workerexecuted in theseprobes.

Also observed three preworker public safetyrefusals: E_REQUIRED_STALE,
E_REQUIRED_ACCESS_REVOKED, E_GRAPH_RUNTIME_UNAVAILABLE; eachBLOCKED/nonzero,
nooutputpack/noWorkerClient invocation. Parent-Preworker-Refusals.json
SHA7fa8bbeacc6fa3257d8a00134d4eabbcb9b069dd9ca0238be5dd891fa1217de1.
These are not the remaining worker-dependent budget/OOV/metadata/replay tests.

### Second review correction and final v3 candidate

Second native read-only review confirmed the four fixes, but required explicit
handling of empty observed ranked results. Earlier code would record empty
lexical/LSA as CASE_QUALITY_MEASURED and admit it to safetyproofs. Accepted as a
harness-truthfulness correction, not a productiondefect/newmechanism. Preserve
N3-Evaluation-Review-2-20261019.md and allv2source/Prepared/8literalpacks/replays.
Do notrun v1/v2hostentrypoints; neither has consumed a rankedhostclaim.

Finalv3contracts `d0bc0e9d2ee5b3bfda25067a079dcead5fcd0d72923548482f2792a0fad46a1a`
add classifier: emptyranked=CASE_FAILED_NO_RANKED_RESULTS, retained/freshverified
but never eligible; literalempty=CASE_BASELINE_DELIVERY_MEASURED, separately
located, never eligible; only nonemptylexicalmandatory after freshverification
can supply safetybasis. Finite scoretype/bounds checked independently. Explicit
quality_failed_arms retained, and safetynotexecutable still runs29thenpartial.

Evaluator `0f0c37e5bf50bb4a2c88d4b640ae14460c4e21fee603254b86eae7cf58b0e8cb`;
newroot evaluation-bc-v3-20261019, sameenv/53pins/fourquestion/caps/oracle/source.
25v3oraclecontrols RED25before/GREEN25after;7v3coordinatorchecks green. Latest
existing21harness and22hostcontracts green too:75selectedofflinechecks total,
no failures/errors/skips, not the29actualruntime tests/fullCI. Latest receipts:

- evaluation-controls-60f9560103a749ec90c11e88581081f8/Receipt.json (25)
- evaluation-runner-controls-9361fcc769bc4d9da670ff2abf586563/Receipt.json (7)
- sibling n3-harness-controls-63d8219c063e4b27b5a4f75c743834b6/Receipt.json (21)
- sibling retrieval-contracts-c1d90316acb74df1b7e92ddb5a20a315/Receipt.json (22)

V3publicproject preparation passed with4sources52nodes170edges/no construction
worker. Prepared SHA`0d7a883a1106e68da6d753138827c9cf248877c4b2ce64e05bad93bebeadb9b5`,
generation `aa1ce2d242420804bda94ee6e5607de0242079581166f0941aee7abf1eca82ca`.
It independently seals originalevidence/source/runtime inventories, questions,
policy/task files, code andindex. New Run-N3-Evaluation-v3-20261019.ps1 uses
these exactseals, one permanentclaim, sameexistingruntime and noinstall route.
Fresh v3review requested; no pass inferred from earlierfixes. N3-D actualresults
review remains after hostevaluation. Only currentv3entrypoint may be handed off.

## Current handoff — v3 code review SHIP, actual ranked evaluation pending

Fresh native independent review returned SHIP for the approved normal-host
handoff only, with no critical/important findings. Finalreview primaryrecord:
same-run N3-Evaluation-Review-3-20261019.md. It verified correctedclassifications,
exact29IDs/controlflow/binding/one-shot/provenance/preservation/launcher seals.
It did not execute tests/worker/preflight/runtime or judge searchquality.
Earlier A3 interrupted preinstallreview remains unavailable, not retroactively
passed. Minor docstring wording is clarified here: the copied frozen target
corpus is not imported/executed; intended productCLI and selected29producttests
do execute. No sealedsource edit was made for this nonblocking clarification.

Parent actualfinalchecks: configuredPowerShell launcher -ValidateOnly exited0,
no worker; two v3literalpublicpacks plus twofreshAPIverifications passed (both
discovery/mandatory for freshness), with newfrozenbinding and baselineclassifier
explicitly checked. Parent-Literal-CLI.json SHAf5767b4d857973faeb6d684534a236f9a5af15cb0a05f8f4fcefe1804a889301.
Older8v1+8v2literalchecks/results remain as earlierobservations, not freshv3runs.
Three earlierpublic preworkerrefusals stay separatelyevidenced, not substituted
for laterworker-dependent budget/OOV/metadata/optional-source/replay cases.

One extra compatibilitycheck explicitly launching WindowsPowerShell5.1 -File
was refused beforepreflight by agentpolicy: scriptsdisabled, exit1,stdout0,
stderr494bytes SHA35c17a19000d27e4d3d9d833a091ba26f9c5f1c6cec83de6ca6ec91e094d4dff.
Retained parent-entrypoint-validate/Start/Result/logs and failedparenthelper.
No executionpolicychange, retry or weaker-shell workaround. This is not the
normaluserhostresult; earlierconfiguredhostvalidation had alreadypassed.
Separate finalparent evidence uses the alreadyapproved controller Python
--inspect directly, not executionoftheblockedPSscript. Normalhost v3 remains
unobserved. If normalhostpolicy refuses too, stop/shareerror; do not changepolicy.

Onlycurrentcommand, once in normalPowerShell under existingN3approval:

```powershell
& "C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\build-validation\n3-retrieval-9ec6fb1db36444acba2945896e8b8d17\Run-N3-Evaluation-v3-20261019.ps1"
```

Launcher SHAd11a168a6d3866c78a9fa3c9c92291a4d264143050e331a18a37e58fd8a5ee36.
Expected receipt evaluation-bc-v3-20261019/Receipt-host.json. No hostclaim or
rankedreceipt exists yet; noinstall, resolver, model/provider/native, deletion,
product, installedskill, release or Gitwrite this turn. Allv1/v2source/results
and interrupteddiagnostics retained. Never run oldsetup or superseded v1/v2
evaluationentrypoints. No new approval needed inside N3; no permission to push.

Remaining: actual24arms/worker-dependent safety/freshreplay/exact29runtime and
postrunpreservation, then independent N3-D resultreview. Evaluate discovery
misses separately from complete authoredmandatorydelivery. Technicalsuccess is
not semanticcompleteness, usefulcodingbenefit, fullN3 or wholereleasereadiness.

Finaldiagnostic detail: the extra parenthelper's child Python preflight used
the worker-style scrubbed environment. Its Git HEAD check refused ownership
(CodexSandboxOnline-owned repo vs CodexSandboxOffline process) because that
scrubbed environment omitted the alreadyconfigured workspace trustcontext.
Both stdout0/stderr1184bytes/exit1 and source remain in parent-python-preflight/;
stderr SHA4c83e0405716125cf114a167691b4b7f6305cd21cc1e0d6c2c457ca188df1f8b.
Read-only comparison reproduces scrubbedexit128 and normal existingcontext
exit0/HEAD0584a89f. No safe.directory/global/repository/securitysetting was added
or changed. Finalcheck uses the same normalcontrollercontext in which prior
preflight succeeded, not a relaxed/forged Git exception or executionpolicy.
This extra diagnostic is not the normalhostactualworker run. Retain failure;
if normalhost refuses trust/policy too, stop/report rather than add exceptions.

Final normal-existing-controller-context preflight actually passed, no worker:
Final-Existing-Context-Preflight.json SHA256
`16f0a4ebc38a6634b8fed6789f85c74ccf31dd1e8f9b284f717f58552666af9b`.
It reverified setup/source/input/index/code seals and fullinstalledruntime;
529repository files (onlyfourFabledocs allowedchanges),1,015oldN3files and454
priorN1/N2files preserved. Hostclaim absent; prepared/launcherhashes unchanged.
Git diff --check exit0. Both extra diagnosticfailures remain, no Git/ACL/policy
change or weakerexception. No commit/push/installskill/native/model operation.

## Latest host result — PRESERVATION PREFLIGHT BLOCKED, do not rerun

User pasted the current v3 normal-PowerShell failure at --inspect, line85:
E_EVAL_ORIGINAL_EVIDENCE_CHANGED. It compares the copied project and three old
N1/N2 roots with Before.json, not retrieval rankings. Launcher stopped atline25
before --run. Current agent observes no hostclaim/rankedreceipt. The original
failure is a user-pasted console report, not independently retainedrawstdout;
private User-Reported-Host-Preflight-Failure.json labels that distinction.
N3-A installed/import/positive evidence is unchanged. B/C and29runtime remain
unrun. Previous code-review SHIP does not override this observedpreflightfailure.

Current agent comparison: all4projectfiles and all454oldN1/N2files match their
savedSHA256 inventories. Strictscans report no accesserrors or reparselinks.
This does not prove equality during the failed normalhostrun or acrosscontexts.
Changedvisibility/transientchanges are hypotheses, not establishedrootcauses.
Do not replaceBefore, ignore changedpaths, resetdata or retryevaluation.

INTENT: additive diagnostic only within approvedN3scope, not a newmechanism.
preservation-diagnostics-20261019/Diagnose-N3-Preservation.py seals evaluator
0f0c37e5/Prepared0d7a883a/Beforehash, scans only4fixedprotectedroots, retains
exactadded/missing/modifiedpaths andhashfacts plus strictaccess/reparse/errors.
Only newobservation directories/receipt are written. No project/runtime/source/
baseline/security/Git/network/subprocess/worker/evaluation function is invoked
or changed. Contextlabels and selfhashes are not authenticatedattestations.

The diagnostic's own firstninecontrols failed beforeimplementation; the first
implementation then had8passes/1failure. Rootcause verified on actualWindows:
DirEntry.stat returnedst_ino0/st_dev0 while Path.stat/os.fstat returned the real
nonzerofileID/device, with equal9bytes/mtime/ctime. Comparing those different
metadataforms falsely reported mutation. One-lineconsistentPath.stat before/
after fixes the diagnosticcheck without dropping identity/time/size checks.
This is NOT a rootcause/fix for the originalnormalhostpreflight mismatch.

Initialdiagnostic retained byte-for-byte, SHA519a3928d738fc6b300c6f229ff7b23bfd0bd3dbf097fc8c1b475c3a5a4f678d;
corrected SHA40662777509442915e45c1aea318c89d426fcac7202dde1f14bf580c367c289b.
Fresh9/9controls pass, nofailures/errors/skips, receiptcontrols-1fdc241ad3da4c08a19046c3d181fbad/Receipt.json.
Failed/redfixtures/logs retained. A narrower initialdirectorygrant could not
createparent; correctedscopedpermission requested. Laterresumedwrite was blocked
read-only before editing; explicitcorrectgrant restored. One request briefly
resolved lostsessionvariables to unusedundefinedpaths; nocommand/fileedit ran,
then exactabsolutepaths were granted. No ACL/securitychange or bypass.

Actual --agent observation:0added/missing/modified,0errors, receiptSHA
bb9cd40285cb3669170b3b1bf4c66aac374ae21f686b997d821844de1c72df78.
Status explicitly NO_VISIBLE_MISMATCH_IN_THIS_CONTEXT_NOT_CROSS_CONTEXT_PROOF.
Sealedv3evaluator/contracts/Prepared stillmatch; no evaluationclaim exists.
Freshread-only diagnostic review requested, not assumedpassed. Need one
normalhost --host diagnostic result before choosing any repair. Noevaluation
retry is authorized by the diagnostic, including a no-difference result.

### Diagnostic review correction — successor v2, not original N3 repair

Native read-only review returned FIX-FIRST: unsafe second rglob/is_file pass
could enumerate/follow host-only reparse metadata; selfhash alone did not bind
reviewedcode before launch. Also clarify who did not delete data and use nonzero
for visiblemismatch. All accepted; originalreview/source/receipts retained in
Diagnostic-Review-1.md. Do notrun original direct--host helper.

Successor Diagnose-N3-Preservation-v2.py SHA7399be3968ae5b1f0f2979016f485526765e72e55972672a7f944adf19dd5245
has only strict non-following scan, no legacysecondtraversal. Newordinaryoutput
observation-v2-agent/host, no predecessoroverwrite. Schema2 labels
diagnostic_deleted_old_data=false, missing-original causeundetermined,
context_label_authentication=false. Exit2visiblemismatch,1incomplete/error,
0onlycompletednovisiblemismatch (neveroriginalcauseor preservationacceptance).

11controls RED11before/GREEN11after, receiptcontrols-12cefa95f1e746db902e79ccfd59adb3/Receipt.json.
ActualWindowsjunctionfixture was created only between newprivatefixturefolders;
auditcontrol confirms0targetopen/scandir, REPARSE_NOT_FOLLOWED error and
INCOMPLETE status. Allfixturedata/junction/source retained, no systemsettings/
shareddata/oldfile altered. Actualv2agentobservation still0diff/errors,
receipt2671297601a57b09eb2cf8035cba6f6e77c8bbdd2127c4472007d3c8c5a74bc2.
No conclusion about the earliernormalhoststate follows.

External Run-N3-Preservation-Diagnostic.ps1 SHA
d9c26b8da26f6fe78a334ecdae0029b5c0e2a3bae5a86d5d585b4f6e585aa813
checks revieweddiagnostic7399/evaluator0f0/Prepared0d7/Before20a94e1cc805b8c582c78fe837d2ffc8be520b96cd89542c093be17014040543,
ordinaryinputfiles andhostobservationabsence. Only fixedC:\Python314\python.exe
-B newdiagnostic--host maylaunch. Noevalinspect/run, network, worker, nativeBeads,
installation, download, global/security/Git edit. Everyresult retryfalse.

Actual Test-Diagnostic-Hash-Gates.ps1 passed4controls: fixedinputgates, wronghash
refusal, reparseinputrefusal beforehash, nohostobservation duringValidateOnly.
These are parentobserved tests, not authentication or wholeproductCI. Newfinal
read-only review requested; no passassumed. Both normalhostdiagnostic and
originalmismatchcause remainunobserved/unconfirmed; no N3retry authorized.

### Current read-only host diagnostic handoff — final code review SHIP

Fresh native read-only review accepted v2diagnostic7399be39 and external
launcherd9c26b8d for ONE hostobservation only, no critical/importantfinding.
Diagnostic-Review-2.md records exactscope; reviewer didnotexecute tests/host.
Parent latest11Pythoncontrols+4actualPowerShellgatechecks pass, nofailures/
errors/skips in Python11; latestcontrols-177d9819efb0401bb239b4b10dffab1e/Receipt.json.
Agentread-onlyobservation-v2-agent/Receipt.json SHA26712976 still0diff/errors;
all458protectedfiles inthiscontext match, notproof of pastnormalhoststate.
Hostobservation/evaluationclaim/rankedreceipt absent at handoff.

ActualWindowsstatregression is retained separately: initialscanner falsely
rejects same9bytefixture from DirEntryst_ino0 while directPath.stat/fstat agrees;
correctedscanner accepts. Windows-Stat-Regression.json SHA
960abf84380e35abeab077127a84de853a34d44584856ae9568ef2d77d5f3ded.
Recurrencesearch across MI/CMscripts found no similarinodecomparison; preserved
initialdiagnostic is the onlycached/directcomparison in newdiagnosticfolder.
Originalevaluationuseshashmaps, not inodecomparison: these are distinctissues.

User should hashcheck the launcher and run it ONCE in normalPowerShell:

```powershell
$n3DiagnosticLauncher = "C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\build-validation\n3-retrieval-9ec6fb1db36444acba2945896e8b8d17\preservation-diagnostics-20261019\Run-N3-Preservation-Diagnostic.ps1"
$n3ExpectedLauncherHash = "d9c26b8da26f6fe78a334ecdae0029b5c0e2a3bae5a86d5d585b4f6e585aa813"
if ((Get-FileHash -LiteralPath $n3DiagnosticLauncher -Algorithm SHA256).Hash.ToLowerInvariant() -ne $n3ExpectedLauncherHash) { throw "Diagnostic launcher changed; stop." }
& $n3DiagnosticLauncher
```

Expectednewreceipt preservation-diagnostics-20261019/observation-v2-host/Receipt.json.
Mismatch/error mayend withredPowerShelltext intentionally; retain/shareconsole
andreceipt, neverrerun/deleteoutput/changepolicy orignoreobservedpaths. A zero
exit is only completedcurrentobservation, NOT acceptedpreservation/solvedcause/
retrypermission. Allresults keep N3stopped. No baselinerewrite, evaluation,
worker/model/provider/nativeBeads/install/download/product/installedskill/Git
change. SourceHEAD0584a89f and N3evaluator/contract/Prepared pinsunchanged;
Gitdiffcheckexit0. No originalfiles/data deleted.
