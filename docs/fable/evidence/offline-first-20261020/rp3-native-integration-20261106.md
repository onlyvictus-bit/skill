# RP3 native product integration — 2026-11-06

Status: partial. The actual selected diagnostic supports the native enrollment
repair. Product code and controller regressions pass. The new selected integrated
batch has not run; full RP3 still needs that result and historical ORIGINAL AFTER.
This record supersedes the Nov5 diagnostic's UNRUN/product-unchanged statements.

## Observed cause and chosen repair

The selected Python3.12 inherited arm had owned root7484 in INNER and OUTER,
but native Git34928 outside BOTH. OUTER cumulative/ledger remained1. This directly
refutes the assumption that ordinary native Popen inherits the required Job in
this selected Store configuration. Exact Windows/Store broker internals remain
unknown; no package-installation, data-preparation or slow-query cause was shown.

The explicit arm had root16688 and suspended Git648. Git initially belonged to
neither Job. Actual AssignProcessToJobObject(INNER) succeeded; INNER and OUTER
membership became true before resume, native wait258 proved the suspended child
had not exited, and all3 members were pinned/reaped: root,cmdGit,mingwGit. Exact
HEAD and fixture hashes passed. Identity-before/after and69 original pins passed.
assignment_exercised=true is actual selected evidence, not a controller inference.

Actual immutable receipts under C:/Users/sakth/Documents/Codex/rp3-native-dispatch-proof-20261105:

| Receipt | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt.json | 8449 | 262e2d2d16696157327d883db11d67afd3c3d1f48c9d97c79c0961efca71fa02 |
| probe/Receipt.json | 24494 | 31ff1c8392114a38154a88123b5b0612a394966f27c554a6a124b593ccc637c0 |
| probe/inherit/Receipt.json | 9945 | 7a82290238fe6d8bfec160e833920580c778ff28250e71dd4a892e36043123d3 |
| probe/explicit/Receipt.json | 11843 | def5fd60300dcc6c3b7c329757d2283f603eca0799b474ddde77bf68cacc8c8e |

No-build leaves the demonstrated failure. The smallest adequate choice is explicit
native enrollment before execution, reusing the retained INNER Job. A general
controller launch service/OUTER numeric-handle transport adds unrelated authority
and is not needed while INNER nesting plus independent OUTER proof pass. Microsoft
documents the nested subset/parent constraints in [Nested Jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)
and [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject).
The selected proof remains the environment-specific evidence. Pivot only if actual
product OUTER proof contradicts this mechanism; never lower ledger assertions.

## Product changes and reviewed failure boundaries

recursive_bootstrap.py only changes the approved OWNED_RUNTIME native route:
validate existing command/options, require current root's retained INNER Job,
create native child suspended, pin PID/creation/image, query/assign/re-query
INNER membership, check absolute work deadline immediately before resume, require
previous suspend count1. The gate runs inside CPython's constructor cleanup scope.
Captured base methods are per-subclass; there is no global native dispatch patch,
unsealed import, new native command, breakaway, or change to POSIX/controller routes.

Construction failure attempts direct-child kill/native wait/Popen wait within ONE
5second allowance. Only pinned direct-child resources are touched. OUTER remains
full-tree cleanup authority; the INNER Job includes the running root and is never
terminated as a cleanup shortcut. Original operation/WinError remains primary;
independent close failures and handle debt stay visible. Failure before CPython
publishes a child handle remains UNKNOWN, not fake no-child or successful cleanup.
Per-launch identity/source/vector/flags/deadline/membership/resume proof is retained;
legacy failure schema points to a complete native sidecar by filename/size/SHA256.

The real Git test's former direct install fixture bypassed the legitimate owned
root boundary. It now runs guarded Git inside a real owned child while retaining
direct-versus-guarded returncode/stdout/stderr, exact HEAD/status and fixture hashes.
Only the NEW fixture Git config gets longpaths=true. Original >=2 assertion stays.

A separate broader-run failure exposed CRT read sharing at pre-installer startup
error receipt reading. The historical holder is not identified. A controlled
NEW file with live DELETE-access/share7 holder deterministically reproduces CRT
PermissionError13 while existing NativeFiles read-only/share7 reads the bytes.
windows_owned_process._bootstrap_json reuses that reader with size4096, stable
identity/type/no-redirect/single-link checks and unchanged strict JSON validation.
No DELETE action, permission change, retry or permissive parse is introduced.

TWINS: recursive Python launch has its own sealed startup gate; Git's negative
evidence does not prove a Python twin defect. Product Python behavior is retained
and independently exercised by a root-child-grandchild ledger proof. Both remaining
Windows startup JSON reads use the same shared read-only boundary. Native/Python
ownership and handle finalization fault paths were inspected and covered directly.

## Retained verification

All paths below are in .github/run-artifacts/rp3-native-integration-20261105.
Verification.json binds receipt/log/file SHA256 records. Failed attempts remain.

| Check | Observation |
| --- | --- |
| red-native-wiring | 5run/3expected failures before native wiring |
| red-review-deadline-proof | 21run/2failures expose final deadline and partial identity gaps |
| recursive-review-green | 47PASS; no errors/skips; log fda99487a9e522e4815cbe0676b8041fce81f6d0ea65a33f00876f3437fad14f |
| knowledge-final-green | retained354run/1startup-read error/54skips; never reported green |
| red-startup-read-sharing | 22run/1controlled CRT sharing failure |
| green-startup-read-sharing | 22PASS; log a37e9661fe7816b3412b5ee337f5beae3230dea5eb963d68fb1d83c31dfb8b2d |
| knowledge-read-final-green | final355run/301PASS/54existing runtime/POSIX SKIP;0fail/error/exclusion/interruption;117.905seconds |
| controller-frozen-product-03 | real frozen product, Git OUTER ledger6 and Python ledger4; all native exits/fixture preserved |
| frozen-ready-real-resolver | 32PASS, including real known-folder resolver |
| frozen-startup-cache-isolation | 22PASS with current frozen product/runner |
| Batch-Output-RED/GREEN.log | real coordinator test proves old capture folder precreated runner output; corrected command-<label> separation passes |
| Batch-Controls-Final.log | 8PASS, hash/account/existing attempt/source drift/Git mismatch/VerifyOnly/output contract/known-warning refusals |
| Actual PS7 VerifyOnly | exit0;741file seals; no selected runtime or normal output created |

Final broad log SHA90143f4bed003b2a89a77d48422cb54ec0e4b9c19e5e70cb84ce322e6851421f.
Frozen product receipt20353bytes SHA752789b3133de2e4ec3c015d76e129369af4fdc206640962c7c9166bbbb36ed7.
Fresh independent product native-gate and startup-reader reviews returned SHIP.
Final coherent full batch/launcher review SHIP is retained in phase Final-Review.md.
The reviewer resumed after a credit interruption and inspected this exact final
hash set; the earlier unissued-draft mismatch is closed. No new runtime was run.

## One combined selected batch

Source-under-test has685authored files, exact4changed/2added relative to the683file
accepted prior Source-Recipe. Source-Acceptance.json binds every file, exact deltas
and the consumed Nov5 runtime receipt/recipe. Authored source/runtime originals
are checked directly; no restricted historical DATA original is reopened here.

selected_runner.py uses the existing ReadyCopy(root=) API to place only default
TEST housekeeping under the run's owned retained scratch. Real default_root resolver
remains callable/tested, explicit roots and intentional test overrides retain their
behavior. No native dispatch is intercepted. Known pre-existing Git ignore warning
is accepted only for the exact HOME/.config/git/ignore path and exact bounded text;
unrelated warning/fatal/path drift refuses. Raw warning bytes remain in receipts.

Selected-Inputs.json451023bytes SHA87727eff5ada400e875faf895844db4bf9a42f5684f50f9620b2956ac7a0530b,
741sealed records/53versions/14groups. Source-acceptance91571bytes SHA
5f226d351b286dccefe221adb7ab7b9dee0730de1b3c7370e160fb9291188c27.
Run-Integrated-Native.ps1 SHA00382d1f7ad988a4ae4b66bf979db395baab8c93c6828b7f245da742c6108536.

The fixed absent normal output is C:/Users/sakth/Documents/Codex/rp3-native-product-20261106.
One fresh normal1001/nonadmin invocation runs identity/dependencies BEFORE, actual
product Git/Python proof, discovery and all14ownership/lifecycle/recursive/budget/
READY/startup groups, original ordered four public retrieval modes with fresh replay
and lease refusals, identity/dependencies AFTER and complete741input/source/HEAD/
index revalidation. Each command prints elapsed seconds; original traceback,
native per-segment proof, command Intent/Command.json and full stdout/stderr are
retained. Failed test logs are complete at their printed result paths.

Default120/public90/startup10/shutdown5/group watchdog60/ordered600/work3600 stay
unchanged. Work admission will not reset or extend the fixed clock. No expiring
reader, separate command per test, old attempt retry, package install, ACL/security/
global/Git change or old-data deletion is included. Local301PASS is controller3.14,
not selected3.12 integration. Native broker internals and exact old C2 cause remain
unknown; no production/readiness confidence beyond observed layers is claimed.

Expected new success status is INTEGRATED_PRODUCT_RUNTIME_OBSERVED_PENDING_HISTORICAL_AFTER.
It deliberately keeps stage_complete=false. Parent must inspect raw batch output;
then fresh historical ORIGINAL AFTER using the approved existing-access copy method
and final Stage review are still required. Reuse passed runtime evidence for that
final step; do not rerun tests merely to refresh old private history. Full RP3,
Gate1, release, installed and producer-authentication claims remain separate.

## Current shell caller pin correction — observed before any attempt

User's outer block refused because cached pwsh.exe changed from the previous
362a356c...ad139 pin. Current same-path file is Microsoft-signed/Valid PowerShell
7.6.9,301360bytes,SHA2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233;
signer thumbprintAB172913A2960A224809EE8A0C371CD47A079B72. The cache replacement
actor is not proven. Exact current shell version observation and existing
launcher VerifyOnly exit0; all741seals and all reviewed frozen files unchanged.
Normal output remains absent. No test or selected runtime started from the user
refusal or these checks. Only external shell caller authority is rebound; no
old guard/source/input repinning. Fresh independent caller-only review SHIP is
retained as phase Shell-Caller-Review.md; tested caller file
Run-Integrated-Native-CurrentShell.ps1 SHAde31cb30edc9278ad6fe9d12ddfdfa8526e66de0d6bb12c3b22da48cdaf9459b.
Full runtime/historicalAFTER/Stage remain pending. No broad tests were repeated.

## Actual selected runtime accepted; ND4 historical copy tail

Actual selected rootReceipt97469bytes SHAb103015f47b698449d4f94616c6cce61fc4d4958af86a6e54e693f1f765e0b9e
has nullfailure/postcheck/segment and14groups complete.177focused cases plus1
original ordered case:178PASS0fail/error/skip. Native independent raw review SHIP;
34streams/captures,14discovery/log/suite sets,12ordered calls and741seals match.
Git BOTH calls exercise missing-membership assignment with OUTER5/exits;Python
tree3/exits. Identity+53versions BEFORE/AFTER stable. Wall244.135seconds;ordered
command86.548seconds. These actuals supersede selected-UNRUN statements above.

Fresh historical AFTER has13662objects matching accepted BEFORE13966objects.
53Normal1001-only folders cover304remainingobjects;never ignored. Fresh18DATA
original/copy native identity/ancestor/byte samples match. Protected358baseline
withONLY6acceptedrepairdeltas/source/runtime/53versions pass. New metadata-only
copier historical_after_copy.py5265bytesSHA12249ac6069c952c03242fb37cd38618adbfb69c0010c2c8c8015f206bacace3
uses same sealed SnapshotSet.copy_denied,roles reversed. RequestSHA7e363dcf...5d58d
binds current workload and accepted BEFORE. VerifyOnly/wrong-account-no-output
controls pass;fresh native copier review SHIP. One Normal copy-only invocation,
then parentmerge/current readable recheck/full13966comparison/finalStage review.
No tests rerun. FullRP3/Gate1/release/install not inferred from runtime success.
