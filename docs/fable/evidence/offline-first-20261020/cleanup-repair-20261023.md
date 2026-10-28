# CR1–CR3 Windows shard shutdown repair — retained working checkpoint

Authority: user said `approve`, then `continue` from the saved two failing
lifetime controls. Base HEAD remains a38297dd797eeecd25e41ab0af1df4e3db8fa984.
This is an uncommitted source correction, not a release, installed replacement
or new Gate1 pass. All old C1/C2 commands, contracts and attempts stay immutable.

## CURRENT — MP1 consumed; SR local repair in progress2026-10-26

User said "start fixing , i will give some more idea for this fix". Existing SR
plan is the sole authority store. Do NOT run any historical handoff below.
MP1 Receipt9846bytes SHA0a61222897b210c2500a5c461b7bacc5f00e296b4d2f5678a51f82b256c488d7
and all6 bound stdout/stderr streams matched. Membership capture completed EXITED1,
not a watchdog timeout. Saved native events show launcher35012 and child19464
outside the session Job and unsignalled after stop, writer alive; exact pipe
holder/escape mechanism/original C2 cleanup cause remain unproven.

SR1 adds NEW cleanup_shutdown_evidence.py/tests only; old probe/helper/launcher/
Inputs/attempt remain immutable. It distinguishes complete nonzero capture from
incomplete capture and pre-write consistency from post-termination association/
signalling transitions. Old probe remains rejected; derived gap is not a repair,
authenticated producer, usable fresh MP1 acceptance or stage completion. The old
Probe-error omitted observation_errors and a fallback pre-terminate snapshot;
these missing observations are disclosed, never reconstructed as raw evidence.

Retained local RED15run14fail confirms missing interpreter plus actual old
validator rejection. Initial GREEN1 had1phase-binding failure; GREEN2 was15/15.
Fresh independent FIX-FIRST then found incomplete transition grammar and a
rounded derived export. Additional RED19run10failure records preceded current
19/19GREEN. Deleting each retained termination/failure event, rearranging phases,
corrupting native-return types/errors, stop-error inconsistency and emergency
event/receipt mismatch now refuse. All original checks remain intact.

IMPORTANT: initial new Saved-Evidence.json is RETAINED BUT SUPERSEDED/FAULTY:
parent JavaScript JSON.parse/stringify rounded13 utc_ns values by +/-100ns.
Original Incremental.jsonl NEVER changed. Authoritative new
Saved-Evidence-exact.json was saved from unparsed CLI text with CRLF->LF only.
Python verified exact integer/type/raw-data equality against fresh CLI and
review_saved_attempt(); first affected value is1793001733541399500. Metadata in
Exact-Export-Verification.json retains argv, raw stdout size11598/SHA
2ffbfc1a634ac41501e297910fae87dac2328be7c3976add3a38563729ed30e1,
and normalized artifact size11597/SHA
de56fc9f1dc507be9e1b3aa3ac915d9fd54fda830b7decaff888c717c5753067.
Raw probe events/markers are not hash-bound by the old failed receipt; derived
report explicitly declares that historical-provenance limitation.

Broad controller at first SR1 bytes439run0fail/7errors, then reviewed SR1 bytes
443run0fail/7errors, exact ordered nonpass IDs equal retained424baseline; not green.
Existing lifecycle6/6, cwd7/7, timeout-budget7/7 PASS. Current SR1 focused logSHA
477b2578a78904a28276001169b4c3336de79deb0040fa10a53bda8c345c5c56.

### SR2 CURRENT — isolated cancellation candidate verified with caveats

INTENT: independently release a blocked synchronous writer while its reader is
still alive, then observe native thread exit/Python join before disposing stdin.
New windows_writer.py is NOT connected to retrieval; distributed_retrieval.py
and windows_job.py retain their exact Before hashes. Windows raw/unbuffered stdin
is required. Startup readiness does not transfer handle ownership: locked
PENDING_WORKER ->ACCEPTED_CONTROLLER or RETIRING_WORKER arbitration prevents a
late start or simultaneous handle close/cancellation. Pre-I/O no-handle failure
can be Python-joined and safely disposed but native_thread_exited remains false.
Failed self-retirement retains the original error/close note and explicit debt.
Only actual successful native wait allows native_thread_exited=true. Closing
before join is refused. Partial writes advance only over remaining bytes;
failed writes are not resent and Boolean write counts are rejected.

Retained RED5 absent candidate; intermediate8controls; RED12/1 Boolean count;
review RED15/4 startup invariants ->GREEN15, RED16/1 retirement error masking
->GREEN16, final RED18/2 concurrent readiness/retirement ->GREEN18/18 with
ResourceWarning-as-error and no nonpass/interruption/exclusion. No existing
test skip/assertion/timeout was weakened. Fresh native read-only exact re-review
returned SHIP_CANDIDATE_WITH_CAVEATS, no remaining blocker, for writer
72dde9c3a495f0326bf95a1eef25e2eb81ac1333921889a8e48656840f475d29 and tests
f3f89b80864a909abb704007db24503d475575365a79f02e64fef006cd969b62.

Final artifacts under cleanup-shutdown-repair-20261026:

| Evidence | Observation |
| --- | --- |
| writer-handoff-red/Receipt.json |18run2fail0error; log614a8385210bd88195a59ff113877ca6411cc0ac2375569772cdd99579e058a4 |
| writer-handoff-green/Receipt.json |18/18PASS; logbf85c3f96b243e51ac663932c883d38218f9a0507e1f68f1228615ef1e6cddf2 |
| knowledge-writer-handoff-final/Receipt.json |228run174PASS54SKIP0fail/error; loge1615634bf25343859f19b51a5b978abe72e62686669b68b3cacd3b0a3d5855d |
| controller-writer-permitted/Receipt.json |443run0fail7exact baseline pin errors; logf86d6332d9ea4b3b6bb18439ba2805dea2025548df4a6105fc9ab2e19da854e2 |
| writer-handoff-green/Run-Inputs.json |Exact parent controller/source/test/runner hash readback, RED/GREEN/broad receipts+logs,9unchanged Before controls; NOT authenticated producer proof |

First broad controller run at this continuation had23errors:16fresh-fixture
creation WinError5 plus7historical pin errors. It remains retained. Scoped tool
grants permitted only new uniquely named test fixtures in the two existing test
output directories; no manual ACL edit, test change, waiver or old-file deletion.
The resulting443run's exact7ordered error IDs match the recorded424baseline.
This is NOT all-green CI. Fresh lifecycle6/cwd7/budget7 also PASS.

One controlled real-pipe timing (reader alive across cancellation/native/Python
join), writer-handoff-green/retained-temp/windows-writer-lj9wesed/Timings.json
SHA05bf55c0733aefb1d8f251203710918435453f29bf6ce96f548277feb20e4b03:

| Segment | Seconds |
| --- | ---: |
| Blocked-write setup, including deliberate0.1s test hold |0.109043600 |
| Cancel request |0.000198000 |
| Native exit / Python join check |0.000181000 |
| Reader-still-alive check |0.000004700 |
| Separate1168-to-WriteFile race cancellation+join |0.012150400 |

These inclusive/independent observations are not summed or presented as a
selected-runtime speedup. Reader termination happens only after the success
assertions, not as the means of releasing the writer. This establishes the SR2
controller-native cancellation axis, not process-tree ownership or the exact
historical C2 holder/cause. Controller3.14 is NOT selected3.12 proof.

TWINS: same lifetime-total/live-handle comparisons remain in old windows_job.py
at156/164 and sealed observers; distributed_retrieval.py still has the original
buffered stdin write/flush and writer joins. They are deliberately not changed
by the isolated SR2 candidate; deleting a total check alone cannot own escaped
workers. No new site matching isinstance(written,int) remains in the candidate.

NEXT/design gate: the existing plan proposes launching the EXACT previously
pinned loaded interpreter image directly with the SAME venv identity freshly
re-proved, then suspended Job assignment before resume. This changes the launch
contract, so approve that description before new launch code/normal-host handoff.
No interpreter installation/substitution, same-hash-image shortcut, pin relaxation
or stop-time ancestry sweep is included. Exact normal-account identity/Job/child
exit feasibility precedes integration and combined shutdown/public initial/replay.
See plan SR3 mechanism decision for alternatives, primary sources and falsifier.

SR1/SR2 are complete ONLY as saved-data interpretation and isolated cancellation
candidate. Selected3.12, SR3 process ownership, combined lifecycle, public replay,
stage/Gate1/release/install remain incomplete. No old retry, selected3.12 agent
start, package installation, manual ACL/security change, deletion, Git action,
source-copy replacement or production qualification was performed.

New exclusive retained output: .github/run-artifacts/cleanup-shutdown-repair-20261026.
Before.json records18 target/control identities and dirty HEADa38297d. The9 old
control/source files freshly compared still match exactly. Earlier "UNRUN" and
"output absent" statements below are historical, not instructions to run again.

## Historical — MP1 preparation verified; handoff before consumed runtime

User returned successful MP1_INPUTS_ONLY_NO_SELECTED_RUNTIME. Parent readback
Inputs175926bytes SHA457fc256b81f52572695b787344cd5778f3bd06bdc14939b5416508ceeacf5a4
matches the user record, with links1 and ordinary file. Exact18keys,7false flags,
629source files and unchanged helper/probe/TC1Input/TC1Receipt/HEAD/budgets verified.
Preparation is CONSUMED; never rerun it. No membership runtime has run yet.

Agent full TC1 inventory walk stops WinError5 at normal-timing/tests/retained-temp/
owned-shutdown-proof-470z594_; full old-private guard also refuses. Thus666TC1
inventory entries and old private inventories are HOST-PREPARED only, not freshly
agent-compared. Both full comparisons remain mandatory in normal context before
and after the witness. No skipped required files, permission/copy workaround or
baseline replacement. Input metadata is not native behavior or producer proof.

Added ONLY new .github/scripts/Run-Cleanup-Membership.ps1 (3154bytes), SHA
0738e9510cb114ae7617d296bd06794e018ac280c61d420a2c58f768e9eb5562,
plus existing Fable records. No helper/probe/source/budget/test changes. It follows
the existing ancestry/hash/SID1001/nonadmin/output-exclusivity pattern and calls
only existing coordinator --sha256457fc256.... Parent PS7 parse0errors,
VerifyOnlyPASS, wrong-contract hash refusal and actual SID1003 refusal observed
before Python/output. Exact sealed existing PS7 -File route VerifyOnly/account
refusal also observed; output/claim still absent. Fresh read-only exact-handoff
review SHIP_WITH_CAVEATS, no Critical/Important finding. Reviewer independently
compared629/629source (zero missing/extra/mismatch), current seals/non-reparse
paths, and retained34focused/424broader receipt/log hashes plus exact7error IDs.
Prior34focused/424broader7historical errors are retained evidence,
not newly rerun this turn because their implementation bytes are unchanged.

NEXT: ONE sealed normal-account process-membership witness,
identity/dependencies/full guards then focused fixture; retained receipt/probe
review before any cause-supported fix. Rootcause/fix/stage/Gate1/release/install
stay false. No numerical retrieval/install/security/Git/delete/retry action.
Outer command seals existing PS7 engine362a356c and new launcher0738e951 before
VerifyOnly, checks exit, rehashes BOTH immediately before ONE actual invocation,
checks exit again. Any error means stop/share, no fallback. This is clearance for
an observation, not a repair or stage/Gate1 completion verdict.

## Historical — MP1 stable correction/code review2026-10-26

INTENT: observe actual four-role membership and native exit, not speculate about
the selected Store boundary or change MI production behavior. Final worker froze
probe7598e119...33535bytes and native tests1fa1db1f...9720bytes; one last local
CloseHandle-exception path superseded earlier33/423 snapshots. Its original
birth-mismatch ValueError now retains close failure as a note. The worker's two
last RED observations were terminal-only (writer-close lost note; local-close
exception replacing original), not invented retained Receipt paths.

Parent independently reran exact final bytes:34/34PASS (23contracts+11native/API
fault cases), ResourceWarning-as-error,0fail/error/skip/exclusion/interruption.
ReceiptSHA189f37f1ff80108ffd7f41ce52890c073ade038ba3c69edb5f2d4de1dc9da1ee,
logd6f0106d63c4c51ab13030a9259b2ee3894d64016df01d773fcf082fca212fae.
Broader424run0fail/7errors/0skip/exclusion/xfail/interruption; exact ordered7error
IDs equal retained390baseline. NOT green CI. ReceiptSHA
5a73b9c7664e0dd4c282ff3cffd3ce36bc447f65190413a9940570a1ffbce02d;
log0208ada6a31b04f8e4c6a208a6f43e922a98f1bcec0e88dc2691e33dc7fa5a1a.
Evidence directories cleanup-membership-stable-focused-20261026 and
cleanup-membership-stable-controller-20261026 retain complete receipts/logs.

Same native reviewer returned CODE SHIP after re-reading exact stable bytes:
all7 Critical/Important code findings closed. It independently inspected code,
not selected runtime; parent test observations remain a separate evidence class.
Native test controls include API injection; the real forced pre-stop cancellation
control is NOT actual job-survivor evidence or proof that cancellation alone fixes
the original product. All rootcause/fix/stage/Gate1/release/install flags stay false.

Frozen INPUT-ONLY launcher Run-Cleanup-Membership-Prepare.ps1 (2673 bytes) SHA
5272ae81108b70ffbb110c8f37e5b3e358436547cf130216d95e87c24cbc7956.
Pins coordinator2c87f117..., probe7598e119..., unchangedTC helper883ec3cd... and
controllercce21c0e.... Parent observed PS7.6.5 parse0errors/VerifyOnlyPASS,
wrong-helper-hash refusal and actual SID1003 refusal BEFORE Python/output. PS5
parser0errors; actual PS5 File loading denied by agent script policy. No bypass,
policy/ACL change or install. Same reviewer separately returned SHIP_WITH_CAVEATS
for exact launcher/seal and the existing PS7 route; no Critical/Important handoff
finding. This is INPUT-ONLY clearance, never a selected-runtime or fix verdict.
Existing shell path is C:/Users/sakth/.cache/codex-runtimes/codex-primary-runtime/
dependencies/native/powershell/pwsh.exe,301368bytes SHA
362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139.
Parent and reviewer independently rehashed shell/launcher and non-reparse paths.
Outer command rehashes BOTH before VerifyOnly and again before ONE actual call;
each uses -NoLogo -NoProfile -NonInteractive -File and checks LASTEXITCODE. Parent
observed the exact PS5 command -> PS7 File route: VerifyOnlyPASS, actual SID1003
refusal before Python/root. It does not change or evade PS5 File policy; it invokes
the separately reviewed existing PS7 application without installing anything.
At that earlier input-only checkpoint, MP1 root/Inputs/runtime launcher were
absent; this historical absence is superseded by the returned preparation above.
There was no selected3.12 or host claim at that checkpoint.
Full old history inventory remains mandatory normal-context because agent private
walk refuses WinError5. No new permission/copy workaround or omitted required file.

TWINS: existing writer/join/close and cumulative-accounting scan remains retained;
the two production TotalProcesses checks and original buffered fixture are not
silently edited by MP1. MI source/job/test hashes f78ea987/4b8631c9/86a8576e and
TC helper/observer883ec3cd/00ee0acf freshly unchanged, HEADa38297d unchanged.

## Historical — TC1 actual failure; MP1 review continuation2026-10-25

The timing launcher was run once by the user. Preparation/runtime are CONSUMED;
normal-timing is no longer absent. Parent independently re-hashed Receipt.json
91344bytes SHA6d58fc03166bf752bfa60d2a8f8b4b6b724d1cc5c8132c75018f0372c4bd9b11,
Timings.json130791bytes SHA3b6f26b37c3a745c1e2d0834d53900d7b13ef445cc4a75aefb98c75a531cdc8b,
and Timings.md44122bytes SHA486cf111917e39c12487192bb0c0cbf89127683fc31ee36d1669cae018cbabbd.
Status TIMING_TIMEOUT_NOT_FIXED; original error OBSERVED; normal-context pinned
preservation true; root_cause_confirmed/fix_validated/stage/Gate1 all false.

UTC receipt12:09:19.959583 ->12:10:50.055577 =90.095994s (not whole PowerShell
command time). Identity0.880, dependencies2.575, input recheck7.220, new copy9.688,
lifecycle capture60.509, final preservation7.282 and new-source check1.439 seconds.
Inclusive spans overlap; do not sum nested times. Metadata/import max0.313 and
data max0.032 do not implicate installs. The deliberate blocked fixture is stdlib.

Actual chain: unit30500 ->root46384 ->relay39520 ->launcher29608 ->child13920,
all native creation identities retained. First terminate0.063s returned, two
native waits returned, but writer join4.953s left writer alive; whole stop5.047s
failed. Second cleanup raises E_SHARD_TREE_UNOBSERVED_MEMBER. Fixture then hangs
in buffered stdin.close. Child13920 later records60.016s wait completion at
12:10:42.865634, after inner termination and outer capture return12:10:41.165548.
Raw event hashes include child ced586ae... and unit fc502297...; see actual receipt
for full records. No returned job PID list was logged, so exact alias/nested-job
mechanism remains unknown. Cumulative TotalProcesses cannot prove a live leak.
Current broad capture's tree_contained label is not independent descendant proof.

Fresh native design review is FIX-FIRST, not clearance. User CONTINUE approves
MP1 focused creation-bound membership witness, bounded fixture-only emergency
cleanup, controller guards/review and new input-only handoff. Plan/design contain
exact scope, falsifier/pivots; live MI bytes and all consumed artifacts stay fixed.
No reinstall, timeout increase, blind full rerun, ACL/trust/Git/deletion. RC2/RC3
and Gate1 incomplete. New13-case controller RED retains missing-witness failures
(0errors/skips), log8758d291...; subsequent implementation verification pending.

MP1 guard correction observation: first16controller guards passed. Fresh native
read-only reviewer found omitted nested release/install/producer flags. Parent
reproduced6 false/missing-flag failures in19run, plus2 native snapshot validation
errors (valid outside members and sorted JSON role keys); all now covered by
corrected19/19 controller run, no skip/error/exclusion, logSHA
c47345fc907f7360ec9092c6f65a794f16948b0d3e3ee1301ba756ef4833905a.
Topology guard independently accepts a fully valid selected candidate then
changes only topology; missing flags cannot make that check vacuously pass.

These are diagnostic guards, NOT Windows selected-runtime or stage proof. Native
first draft wrongly used synthetic topology unconditionally and had unsafe thread
ID/LastError/partial-cleanup issues. No handoff clearance. Native worker/reviewer
credit errors are infrastructure interruptions, not acceptance; same-seat work
resumed only after new user CONTINUE. All first-draft outputs retained as controls.
Prepare launcher remains FREEZE_AFTER_REVIEW; MP1 normal root absent/unconsumed.
Fresh full old-history read still refuses WinError5 at old control-tests retained
mi-worker-9rtyb1xz. Mandatory normal-account checks not waived or monkeypatched.

### MP1 final-review findings and retained checks2026-10-25

Parent observed25/25 focused controller/native cases PASS with ResourceWarning
as error; log7d38ed0e9df354b6a658a2ad415318b7df69f8d4a76ea1b76e3e33f2759cef71.
Broader415run has0failures/7errors/0skips/exclusions/expected failures and is not
green. Exact ordered error IDs equal the earlier390-case baseline. Broad log
89f8443a8c154d623bdbb5f20adddb216b337cc5757fd071864a21bde8edb3b2.
Related timing controller23/23PASS, log380c950020df6bbebc839e5f7efef983de8cd553de053e0071a30fff8bda7e9c.
These are controller checks, not another consumed host attempt.

Fresh final native review of probe b04b8003... returned FIX-FIRST despite those
passes. It found borrowed-root/double-close ownership on birth mismatch; native
handle-close failures after a saved success; emergency completion ignoring errors;
unexpected request errors losing session.writer; native thread-ID reuse checks
missing after OpenThread; an uncontracted10second marker wait; and stale LastError
values on successful native calls. Forced-stop control raises BEFORE session.stop
and cannot prove a member survived actual job termination. No command is cleared.
Corrections stay within MP1, with native worker owning probe/native tests and parent
owning coordinator contracts. No MI source, frozen history, or old pin is changed.

Parent first reproduced9 acceptance failures in23cases: cleanup errors/missing
writer-role exit proof and missing/failed native-handle finalization were accepted.
RED log6670cf8ca4a34ee181a02806b76e04c31b74dc1f7defb5ba59c6dc55934fc5f4;
after the bounded validation correction23/23PASS, log
6edfa3440853c8a8623a210fc2482ef3fc49865c9dedabf5043ce0d403b8a803.
Native correction controls, final regression and same-seat re-review still pending.
Prepare launcher remains unfrozen; input root absent. Runtime/stage remain false.

## Historical — TC1 inputs reviewed; exact runtime handoff SHIP2026-10-24

Normal preparation completed once: Inputs85251bytes SHA
cf45dfde1fae5d2bb5f601a8d54c4fa68e62d5db35e3248ffe9bdfecf9476d62.
Parent stable read/hash, exact15key schema, helper/3support rows,629frozen source
files,12case IDs,0.1/5/60/120budgets, prior stack Inputs/Receipt rows, HEAD and
unchanged cr.verify(C1/runtime/protected/history) passed. Full CR3 walk denied at
mi-worker-9rtyb1xz; full stack walk denied at owned-shutdown-proof-112v6tbq. Those
two private full-inventory comparisons are HOST-PREPARED only, not agent-complete.
Runtime coordinator still requires both completely in normal context before and
after capture; no skip, monkeypatch, path substitution or ACL workaround.

INTENT: add only external runtime launcher for reviewed coordinator + returned
Inputs. New Run-Cleanup-Timing.ps13472bytes SHA
3b049895ebd0af70cd1e1c25811bea4a63d7d35db92766a84532304a0b2b1aa2.
Fresh PS parse0errors and actual VerifyOnly emitted
TC1_RUNTIME_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT. In-memory wrong-contract hash probe
and actual wrong-agent-account invocation both refused BEFORE Python/output.
Normal-timing remained absent. Only new launcher and existing Fable records were
written; helper883ec3cd/observer00ee0acf/tests ef7b71f7/Inputs unchanged. Retained
23guard/390controller receipts still match; broader suite still7historical pin
errors, NOT a freshly rerun fullygreen suite. No product behavior/test change.

First fresh reviewer attempt failed with workspace-credit error, NOT clearance.
User continued; same reviewer retried once and returned actual SHIP for this exact
launcher and ONE normal-account TC1 diagnostic. Reviewer independently checked
all6seals, contract shape/roles/budgets/falseflags, guard order, mandatory inherited
normal-context checks, nonzero/finalization failure handling and unused output.
It did not rewalk denied private folders or rerun writing suites/selected runtime.
No source/Git/install/model/security operation was substituted for that review.

NEXT: external SHA-check new Run-Cleanup-Timing.ps1; VerifyOnly then one normal
non-admin invocation. Share retained Receipt.json/Timings.md/Timings.json and
stacks if created. Preparation is consumed: never rerun it or old stack/CR3/C2.
No runtime attempt has started; root cause, fix, RC2/RC3, stage/Gate1/release/install
remain UNVERIFIED. A timing timeout still is not a fix; retain it without retry.

## Historical — TC1 implemented/reviewed; selected timing UNRUN2026-10-24

AUTH: user said "aprove, add timing show code in all part and stage and
segment". This authorizes TC1 timing-only local work and a new sealed diagnostic,
not a package reinstall or rerun of consumed attempts. INTENT: observe imports,
per-package installed metadata, fixture/data writes, process creation/lineage,
request serialization, separate write/flush, deadline/readiness waits, owned job
assignment/resume/membership/termination/native waits, writer join, stream/directory
cleanup and original exception BEFORE fixture close. UTC/monotonic wall/processCPU,
PID+creation/PPID/thread, original frozen file/line/function, bytes/status retained.

New .github/scripts/cleanup_timing_observer.py SHA
00ee0acf6dc4205fd2a853fb80fdc481772a19b71b8afc7c5e44fab2875f6473;
cleanup_timing_diagnostic.py SHA
883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554;
tests/test_cleanup_timing.py SHA
ef7b71f746dacce4a6086f139780ec7dd17657772a8a0b355a3a7633e5f1b520.
Existing extended_timing_log0b234e49 and worker_diagnostic_events5e7d3053 remain
unchanged. New copy is630files:629frozen repaired source with only3AST overlays
and1new observer. Original AST is recovered exactly by inverse; original12cases,
assertions and0.1/5/60/120budgets preserved. No payload-content logging or installer.

Focused final: cleanup-timing-final-guards-20261024 Receipt
349186021f7a6c07d267cdf9944bb54c1a22fd94601dd25f717b4b4b5a112667,
log0b8a9e8ebf9957c4adb3bb36617d208e38b2273c2b30d84529709cb9d0a37116:
23/23PASS, no fail/error/skip/exclusion/interruption. Includes real C31412case
instrumented copy, actual small pipe write/flush, exception preservation, AST
inverse, malformed/orphan/unfinished rejection, wrong helper alias refusal,
per-module entries, exact child cleanup on observer-END failure, creation-bound
parent edges, target-interval error capture and timeout/preservation flow guards.
Initial missing-adapter RED9FAIL and later review REDs are retained; these are
diagnostic feature regressions, NOT reproductions of the selected3.12 defect.

Broader: cleanup-timing-controller-20261024 Receipt
7de0118d21dc2e39a9bd02c0c2b9132d982449933a501b915c7f135807e80ab0,
logd3b2f725d96880f5a172e0aeaee3a34b3d943771572a27ea492f348e02ede73d:
390run,0FAIL,7ERROR,0SKIP/xfail/exclusion, no interruption. Parent compared the
full7error list with prior367baseline: exact equality (1E_EXT_GIT_SOURCE_DRIFT,
1E_CURRENT_LIVE_SOURCE_CHANGED,5E_DIAG_SOURCE_PIN). NOT green CI; no pins weakened.
Full MI712 baseline is retained, not freshly rerun here; no MI bytes changed.

Local C314 ONLY illustrative timings, not selected3.12 or historical C2 proof:
final guards retained-temp/tc-native-smoke-9o4x62x7/Timings.json and Timings.md
contain370individual segments/13process nodes, original error NOT_REPRODUCED.
Values below are MAX individual completed inclusive spans, NOT category totals.

| Local observation category | Maximum completed seconds | Unfinished spans |
|---|---:|---:|
| Imports/metadata (stdlib/module imports here, NOT installs) |0.2488939|0|
| Fixture/data preparation |0.0304462|0|
| IPC write |0.1230141|0|
| Process startup/wait |0.5062405|1|
| Shutdown/cleanup |0.2753318|0|
| Observer child-overlay overhead |0.0235230|0|

The deliberately blocked child wait has no END after owned cancellation; its
duration is UNKNOWN, not60exactly. All12tests still passed. Nested/parallel spans
and processCPU are never summed into wall totals; data writes include observation
generation, which has a separate nested overhead span. Cold startup/site/DLL time
before the first observer module event remains UNINSTRUMENTED. Report coverage
marks absent paths NOT_REACHED_OR_NOT_OBSERVED; flush is not fabricated when write
fails first. Original_error_status OBSERVED requires a nonempty bounded chain
inside this blocked test's PID/thread/time interval; otherwise explicitly unknown.
Process joins use PID+creation and actual PPID, not launcher=interpreter guesses.

Fresh independent review initially FIX_FIRST found post-Popen observer ownership,
lineage, coverage, module-entry/alias and code-line/category gaps. Relevant REDs
observed and corrected. Final review SHIP for INPUT-ONLY normal preparation; final
two-literal external seal separately reviewed SHIP. TWINS: searched existing
logger span/Popen observation boundaries; reused logger unchanged, fixed ownership
only in new throwing spawn adapter. No speculative original lifecycle fix added.

New Run-Cleanup-Timing-Prepare.ps1 (2777bytes) SHA
9101c4d21730687d416a93f4b727cf2d05773e11067713a39b60268c819ac6d0.
Parent observed0PS parse errors and actual VerifyOnly
TC1_PREPARATION_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT. Final reviewer verified all5
input seals, reparse guards, exact normal non-admin SID and absent one-shot root.
NEXT: run only this INPUT-ONLY normal preparation, return new Inputs path/size/SHA,
review exact contract before freezing timing runtime launcher. ROOT/Inputs and
normal-timing currently absent. It neither runs selected3.12 nor consumes workload.
Full old-private inventories remain mandatory normal-context checks; no ACL bypass.

TC1 selected runtime table/root cause/fix/stage/Gate1/release/install UNVERIFIED.
No new selected interpreter ran, no old command retried, no install/security/Git
write/delete. Live distributed/windows_job/tests retain f78ea987/4b8631c9/86a8576e;
old stack Receiptc803e2fa/stack6fcc6477 hashes still match. Next measurement stays
same12cases/0.1request/5shutdown/60watchdog/120default; retain failures, no autoretry.

## Historical — stack consumed; timing proposal before approval2026-10-24

Actual normal-stack Receipt8462bytes SHA
c803e2fa4010837398be9448a44013181040f4eb576105c6d4e3e29449189b8a;
Slow-Stack.log3108bytes SHA6fcc64771d6df416fe2e8671c1a9e2e7dd3d29c383fb4dafc047aa109fceea0f.
Status TIMEOUT_STACK_CAPTURED_NOT_FIXED, no receipt failure, named preservation
verified. Stack at10seconds has writer in distributed_retrieval.py:76 write/flush
and main thread in test_knowledge_windows_shutdown.py:64 fixture stdin.close.
One casePASS, blocked-writer case incomplete; no inner suite receipt/outcomes.
This locates the wait but does not recover the original exception that led to
fixture teardown. The diagnostic attempt is consumed; do not rerun it.

Read-only receipt interval is74.648245seconds (UTC08:07:56.568863 to08:09:11.217108).
It includes metadata probes, validation,60watchdog/capture and final protection;
it is NOT a per-stage/per-process timer or pure worker CPU duration. Root capture
PIDs:38944identityPASS,47724dependency-metadataPASS,25052lifetimeTIMEOUT. Actual
interpreter/relay/child PID lineage is not fully timed here. No invented split
of the remaining14.648245seconds into package/import/cleanup costs is allowed.

Package check: frozen fixture source launches a stdlib subprocess relay and a
stdlib actual child. blocked=True explicitly waits60seconds without reading
stdin, to test cancellation. Request writes1,000,000text characters with a0.1s
test-specific deadline; production default120 is not that fixture deadline.
No pip/install command appears in the retained argv or fixture call path;
dependency probe reads53installed-distribution metadata versions, not installer
work. Advanced Semantica imports are inside retrieval functions not called by
this fixture. Startup/environment effects remain possible; absence of installer
calls is not a claim every installed package or DLL is healthy.

Previous timing evidence independently re-opened and hash-matched: old Receipt
b4bf001140ad6d4c486f4674bd7b82cf3c0ea23879e1c7bf994000c11822f569,
Timings.json036ad2857df4c64c61a5e80cad089c16d5e3084fc71211233cfcbf33c7a8e88d.
Its initial community Semantica import27.453s and numerical imports12.234s were
LOAD time, not package INSTALL time. Those observations must not be transplanted
onto this stdlib blocked-writer fixture. Nested/parallel timings are not summed.

User now asks per-process/per-stage timing as before. Proposed TC1 below in the
same plan, no new implementation/run yet: reuse the bounded timing recorder,
new reviewed diagnostic-only copy/adapter and output; explicit launcher/actual
interpreter/relay/child identities; START/END wall/process-CPU spans for startup,
declared imports, request serialization, pipe write/flush, deadline detection,
owned-job membership/terminate/wait, writer join, stream close and fixture cleanup.
Capture active exception/notes BEFORE fixture stdin.close so the hidden original
error is not lost. Unfinished spans UNKNOWN/lower-bound only, not exact60seconds.
Same test data,0.1fixture deadline,5shutdown allowance,60watchdog,120production
default; no skip, installer, old-source/pin mutation or automatic retry. Need
approval of this bounded timing extension before building or another host run.

## Historical — host inputs reviewed; stack diagnostic then unrun2026-10-24

User executed input-only preparation. Parent independently verified Inputs.json
189744bytes, single-link, SHAead95373d25ee2750a10c52e4e2bbf7cf3cabb087166b00df2533458bec27075.
Exact16keys/scope/head/source/output/helper/parent-contract/failed-receipt match;
12case IDs, stack10/watchdog60 and allfalse readiness/auth labels are exact.
Returned inventory has1339safe relative file/hash entries. Parent checked current
C1/runtime/protected bindings, complete627control/629repaired source copies and
all8old command streams. No source overlay or test/budget/helper edit occurred.

Private scratch boundary: successful normal preparation is the actual host
evidence for the mandatory full walk. The agent did NOT independently compare
all1339private files and makes no whole-private-archive claim. No skip or waiver
was applied. Runtime verify_inputs must compare every inventory entry in normal
context before creating output, again before the diagnostic marker and after
capture; mismatch/unreadable input remains fail-closed.

Fresh independent final seal review: SHIP for ONE normal-account stack-only
diagnostic, not rootcause/fix/CR3 completion. It checked exact returned schema/
pins/cases/budgets/false flags, readable12runtime/15history/3replacement records,
critical frozen runner/test/failure entries, absent normal-stack, full-inventory
guard placement and strict capture/unit accounting. Same private-access caveat
retained. No selected runtime or old command was started in review.

Only two runtime-launcher hash literals changed after clearance. Final
Run-Cleanup-Lifetime-Diagnostic.ps1 SHA
ffabc697263406c7598d1f59d2f718bfa65b6486d82f631fe096c67bf2e6df86.
Helper SHA remainsb03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031.
Parent observed0PS parse errors and actual -VerifyOnly success:
LIFETIME_DIAGNOSTIC_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT.
normal-stack absent; no diagnostic marker, selected stack run or fix exists.

Next one outer-hash-checked invocation of ONLY that new runtime launcher in
NORMAL NON-ADMIN PowerShell, VerifyOnly then run. Do not rerun preparation or
old CR3/C2/N3, change guards/policy, remove/rename output, or retry a failure.
Return normal-stack/Receipt.json and normal-stack/tests/Slow-Stack.log if written.
Captured timeout returns failure and NOT_FIXED; missing stack is INCONCLUSIVE.
All12 passing would still be NOT_CR3_COMPLETE until actual cause/fix and ordered
proof are reviewed. Focused13guard/broad367 evidence unchanged, not rerun here;
broader7pin errors remain visible. Gate1/release/install remain false.

## CURRENT actual CR3 failure and Deep Plan root-cause continuation2026-10-24

CR3 is CONSUMED, not still unused. Actual normal Receipt168066bytes SHA
d214498c4e7ff2b613ebb933c4174e7c19a3125dc60350c34c1c5491d456c9d7 was checked
against the user's console. Identity/dependency probes PASS. All4original-code
ordered modes PASS with exact initial/replay/negative-lease accounting; historical
cleanup failure not reproduced. Repaired lifetime suite case1PASS, blocked-real-
pipe-writer case2 starts with no finish. Outer Command.json records TIMEOUT,
timed_out=true, capture_complete=true, no capture errors/overflow, contained tree,
watchdog60. stdout/stderr are empty. The internal328byte unittest log is the
progress witness; there is no lifetime Receipt/Case-Outcomes and repaired-ordered
was never called. Do not infer a failed assertion, successful shutdown or exact
blocked frame. Parent verified8streams,627/629source copies and named C1/runtime/
protected pins. This is one actual runtime evidence family, not independent votes.

User requests Deep Plan root-cause/fix/stage completion. The existing plan now
contains RC1–RC3, target/done, alternatives, lenses, evidence families, weakest
link, cheapest falsifier and pivot. No second plan store. Recommendation: reuse
existing retained_unittest --stack-after10 with same12frozen lifecycle cases,
same60watchdog, new exclusive output; no source overlay, skipped case, timeout
increase or speculative production repair. Full stage requires selected-runtime
12/12 plus repaired ordered proof and protection, not just a captured stack.

New diagnostic glue: cleanup_lifetime_diagnostic.py, corresponding13guard cases,
Run-Cleanup-Lifetime-Diagnostic.ps1 and input-only Run-Cleanup-Lifetime-Prepare.ps1.
It reuses exact CR3/C1/capture/runner inputs and additionally freezes the complete
failed-attempt file inventory. A timeout with a usable stack is explicitly
TIMEOUT_STACK_CAPTURED_NOT_FIXED, returns failure, and keeps root_cause_confirmed,
fix_validated, stage_complete, Gate1/release/install flags false. Setup errors
retain a receipt; preservation failure overrides any diagnostic classification.

Observed focused guards13/13PASS, no skips/errors/exclusions. Tests include real
C314 child/unchanged retained-runner stack dump (not selected3.12 proof), exact
argv/no skip/no budget override, timeout/missing-stack/incomplete/uncontained/
overflow refusal, wrong-account/setup refusal, coordinated timeout retention
and protection-failure refusal. Initial new-feature RED10cases lacked helper;
do not misrepresent that as reproduction of the original runtime deadlock.
Final focused logSHAdd8e81e2b2d2d003a1c4c93ebdb0101bf80aafcaf7c8274a7da81101539680ae.
Real stack-smoke file1131bytes SHA1e3345d18786c0c383b685b43601137abf04476e2445300bb6a8241d6da3027a.

Fresh broader controller367run,0failures,7same exact source-pin errors,0skips,
0exclusions, no interruption. Parent verified logSHA
905b877467d12b39baa7d0ecb1279929d74ad3552b25268072fe194360324f70.
No current MI code/test bytes changed, so earlier712full-MI evidence remains
historical baseline rather than being relabelled freshly rerun. Broad is NOTgreen.

New RC1 preparation blocker: complete failed-attempt walk raises WinError5 at
normal-comparison/control-tests/retained-temp/mi-worker-9rtyb1xz in agent context.
This does not prove the lifecycle hang's cause and cannot be skipped. All pins
before that full walk passed; no Inputs/root/normal diagnostic claim was created.
Pivot is input-only preparation under normal non-admin account, not ACL/trust,
owner, copy or security workaround. Runtime launcher remains FREEZE pending
reviewed host Inputs. No new selected runtime, diagnostic workload or fix ran.
Independent review is checking code and this two-phase handoff; it cannot verify
the unreadable private inventory from the agent seat. RC1 remains partial.

### Input-only preparation clearance and exact seal2026-10-24

Fresh independent native review returned NARROW CLEARANCE/ship for INPUT-ONLY
preparation. No concrete Critical/Important blocker was found in that boundary.
Reviewer confirmed the private full inventory remains mandatory and fail-closed,
exact normal SID/non-admin before execution, no existing ROOT overwrite, no
selected-runtime call or diagnostic claim from --prepare. It did not execute
preparation, selected3.12 or the old commands. Runtime clearance is NOT given.

Final cleanup_lifetime_diagnostic.py helper SHA
b03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031.
Final Run-Cleanup-Lifetime-Prepare.ps1 SHA
b0eabad1fe626c76c47c9d2bb9d1d73940657c11accbaf0a4a4986fc4d563931.
Parent verified zeroPS parser errors and actual -VerifyOnly output
LIFETIME_PREPARE_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT. Input ROOT remains absent;
diagnostic runtime launcher still contains FREEZE_AFTER_REVIEW. Old CR3 helper,
launcher, failed Receipt and production owned-job module hashes remain exact.

Next one outer-hash-checked NORMAL NON-ADMIN invocation of ONLY the new prepare
launcher: VerifyOnly then run. Return Inputs path/size/hash and console. Do not
precreate/delete/rename ROOT, retry a failed partial preparation, bypass policy,
change permissions or run the diagnostic launcher. Successful preparation is
only an input record, not an actual stack observation, root cause, fix or stage
completion. Review that exact returned Inputs before separately sealing runtime.

## Continuation and review corrections — 2026-10-24

Fresh read-only review returned FIX-FIRST, not a pass. Parent reproduced and
corrected the three concrete findings without changing old sealed helpers:

1. Handle-close failures masked original thread-owner, membership and job-setup
   errors. Three RED failures at review-r1-red-20261024 now pass. The owned-job
   helper attempts every owned handle close, annotates an active operation error,
   and still raises close failure when no primary exists. Failed job release
   retains its handle identity. This also fixes the constructor's same masking
   pattern (TWINS); no unrelated process-management primitive was changed.
2. The old broad substring control gate accepted unrelated community failure
   alongside vector cleanup, replay-only cleanup, and a cause-free wrapper.
   Behavior-neutral extraction first reproduced all three actual acceptances
   in cleanup-review-r2-characterized-red-20261024. The corrected gate requires
   PASS/PASS/PASS/FAIL, only initial vector/public exit2, and a complete parsed
   cleanup cause. All-pass control remains non-reproduction, not historical
   cause proof. Existing exact ordered accounting and capture remain unchanged.
3. Post-output setup failure escaped receipt handling. Two RED subcases
   (support import/environment builder) created no receipt under the old code.
   Setup is now inside the existing try/finally. Both GREEN subcases retain
   PARTIAL_OR_FAILED_NO_RETRY, traceback, empty commands, no workload claim,
   and exit1. No actual selected-runtime attempt was consumed by these controls.

Latest focused results:12/12 Windows lifecycle/error controls and11/11 handoff
guards PASS, with no skips/errors/exclusions. Seven lifecycle cases use real
Windows processes/handles; the five additional close/error cases inject faults
at the native API boundary and are not numerical-runtime proof.

Retained log hashes:

- R1 RED:6c80611392074e7dc962f06abe90b53079d6c153c56f30e0cef6770aea2ecf5f.
- R2 characterized RED:0fc37365ec311922a1807d93fb35a553e79ba0e008966a4cfa4597c75f1c097d.
- Setup RED:0583ee77dc015b16abca1067901724beab50808f642c81ef1dd35655de59389f.
- Final native GREEN:048c4407f8488c381e5e21ffe6e4908c4cddb56bfc6531af7c83554c6bd17257.
- Final helper GREEN:e99a3f9a31296dff673245d702401eb91821362fbe0879f6639537e0cca2ef00.

The exact committed-source baseline completed700 tests with1failure,3errors,
54skips and1expected failure. Its complete failure/error/skip/expected-failure
lists equal the earlier repaired706 snapshot, and both log hashes were checked.
Baseline Receipt SHA129b15b4607aec6252344b491d00f575040a9fb1fc66c641263de752fe569bc1.
This bounded comparison does not make either suite green or prove every
environment-dependent result unrelated to the repair.

Fresh broad controller353 tests:0failures,7error records,0skips/exclusions;
same exact error identities as the earlier343 snapshot. Log SHA
b5ae4cbfb7f7c56350529e709b366a093dfb20d891541ce9002707d2ec3190c5.
That broad run predates the final setup correction; its added guard passed
in the final11-case focused run. Fresh full-MI result is pending below.

Parent named-preservation probe passed627 immutable C1 source files,15 old
C1/C2 history/stream records,4protected roots (only3approved MI path deltas),
and12fixed runtime inputs. No new Runtime-Inputs contract or normal-comparison
output existed at that probe. Final correction rereview and sealing are pending;
the earlier review interruption was never treated as approval to issue a command.

### Final correction clearance and broad result2026-10-24

Same fresh native reviewer resumed and returned `ship`: no Critical/Important
findings remain in this bounded source correction/handoff code. Clearance is
ONLY to prepare/seal and issue one focused normal-account CR3 comparison. The
reviewer verified that the outer capture helper returns no completed process
on incomplete/overflow/timed-out/uncontained capture; CR3 refuses that result
before parsing the expected negative control. No new capture primitive needed.

Parent independently read the completed fresh full-MI receipt/log, verified the
log hash, exact712 discovered/run, no interruption/exclusion, and equality of
ALL failure/error/skip/expected-failure lists against baseline700. Result:
653PASS,1failure,3errors,54skips,1expected failure. The12 additional shutdown/
error cases introduce no additional non-pass record in this observation. This
is NOT green CI. Fresh full-MI Receipt SHA
7cf1692beb3e2110bcef282d1e2b2e3ffda98beb44fcf668d7b65bef62d0d5c1;
log SHAaae504f66bb09a1d0346ae8dcf924a8707bafa78d46f9a340399d0db01945396.
The353-case controller retains the same7 pin-error records,0failures/skips.
Final setup correction is separately verified by the11-case focused suite.

No numerical CR3 comparison, old-command retry or selected3.12 run occurred.
Historical C2 cause, Gate1,24arms,C3/release/install qualification remain open.

### Frozen CR3 inputs and handoff2026-10-24 — numerical outcome UNRUN

Input-only prepare succeeded with no selected-runtime launch. New exclusive
Runtime-Inputs.json is211348bytes, SHA
18b1d93425f0f52965b94ed7349acf11042065348aafc26b8152ce7c6b595838.
It binds627 immutable C1 source records,15 old history/stream records,4protected
roots,12fixed runtime roles and exactly3approved replacement paths. No old
source/cache/contract/helper/receipt/claim was rewritten. Named-scope protection
does not authenticate a producer or qualify the entire private archive.

Final helper SHA8bc851bfbc59848b1730bbd141987c4fff80156a5f5adc23467e7f706fbafc2f.
Final .github/scripts/Run-Cleanup-Repair.ps1 SHA
c9fb41897545625f3b152315fcef276b5afe343a75ac478183d7d8cf11086c59.
Only the two exact hash literals changed after code review. Parent observed
zero PowerShell parse errors and ACTUAL launcher -VerifyOnly success:
CR3_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_ATTEMPT. Independent Python input probe
also returned CR3_FINAL_ALL_INPUTS_VERIFIED_NO_SELECTED_RUNTIME_OR_WORKLOAD,
rechecking all above named records and absent normal-comparison output.

One invocation is intended in NORMAL NON-ADMIN PowerShell, outer launcher hash
checked first, then VerifyOnly and actual launcher. It uses the existing exact
selected3.12 runtime, default120, original ordered public method/timeout90,
12shutdown/error controls and both control/repaired copies. It stops and retains
failure; no retry/remove/rename/rebaseline/security workaround. Normal output:
.github/run-artifacts/cleanup-repair-20261023/normal-comparison/Receipt.json.
Do not run old N3/C1/C2 launchers. If execution policy or any input/account check
refuses, retain the error and do not bypass it. User approval for CR1–CR3 already
covers this one new focused comparison; no extra scope approval is requested.

Result must still be read back with actual raw streams, mode outcomes, native
lifetime evidence and fresh preservation before claiming focused runtime repair.
Even a green focused comparison is not complete Gate1,24arms, final C3 archive
proof, release packaging or installation. No commit/push was performed.

Final independent exact-seal rereview: NARROW CLEARANCE, no concrete mismatch
or blocker. Reviewer independently checked current helper13694bytes, contract
211348bytes, launcher2891bytes and controller hashes; ordinary/non-reparse/
single-name identities; all5support pins; exact3replacement set;12test methods;
15history records;12runtime roles;627/627C1source and642/642C1inventory; all4
protected roots; absent output; launcher AST, exact SID/non-admin and one-shot
refusal order. No worker, launcher, prepare or file edit ran in that review.
This is exact handoff clearance only. Parent final input and VerifyOnly probes
above are separate direct observations; actual numerical outcome remains UNRUN.

## Observations and boundaries

The original C2 public vector/distributed-local INITIAL retrieval reported
E_DISTRIBUTED_CLEANUP. Its actual underlying OS error/holder is still UNKNOWN:
the saved public serializer omitted exception causes/notes. Do not rewrite
that historical fact as a proven WinError32 or permanent orphan.

CR1's newly authored stdlib-only relay uses two real PIDs. The original
_Session.stop killed/waited the launcher, then returned while the actual
interpreter's native exit handle was still unsignalled. BOTH initial controls
failed for that intended reason, not a missing installed dependency:
`.github/run-artifacts/cleanup-repair-20261023/red-lifetime/unittest.log`,
SHA1f3f3424ce31ff899d4008961804250d0218d324b8e666d794d39e5ff3f73c17.
This proves a shutdown-ordering defect, not the missing historical C2 cause.

The first repair made both controls green. Further controls exposed failed
stdin close abandoning the tree, and one cancellation run exposed job
active-count zero preceding the interpreter's signalled exit handle. These
failures and intermediate implementation/test-fixture mistakes remain retained;
no failed output was overwritten or promoted to a pass.

## Scoped implementation

- Windows shards start suspended; their own new non-breakaway Job Object is
  assigned BEFORE resume. Setup failure kills/reaps only the new owned root.
- Idle completed sessions close stdin to deliver EOF, then wait for the root
  and owned job within the existing five-second shutdown allowance.
- Cancellation/blocked writers terminate the owned job, pin member process
  handles, independently await their exit, and join the writer before disposal.
  Membership accounting changes/unobserved members refuse success. No global
  Python sweep, PID-only fallback, arbitrary repair sleep or timeout increase.
- Failed shutdown remains failed and retains output; it cannot set _stopped or
  proceed to directory removal. Original exceptions remain primary with cleanup
  notes. POSIX behavior and default120 are unchanged.
- TWINS: worker_client._process's normal-success path already waits for normal
  worker completion; it does not unconditionally kill the live launcher at the
  end of every successful shard session. Its Windows timeout taskkill path is
  a separate limitation, not proven equivalent by these tests; it is unchanged.
  The generic hybrid_bridge capture guard is also unchanged. No global process
  supervisor or public success-schema change was introduced.

The ownership primitive is explained by Microsoft's Job Objects, Thread32 and
ResumeThread documentation. Public docs guide API use; they do not authenticate
the selected installed Python binary or prove the original C2 OS error.

## Verification observed so far

| Check | Observed result |
|---|---|
| Original two-PID lifetime controls | RED2/2 intended failures, then GREEN2/2 |
| Final native Windows controls | 7/7 PASS, no skip/error/exclusion |
| Existing lifecycle controls | 6/6 PASS |
| Existing cwd controls | 7/7 PASS |
| Existing timeout-budget controls | 7/7 PASS; default120 unchanged |
| New CR3 input/overlay controls | 5/5 PASS after failure-first checks |
| Full MI (six native cases at that snapshot) | 706run,1failure,3errors,54skips,1expected failure; NOT green |
| Broad controller before five new helper cases | 343run,0failures,7error records,0skip/exclusions; NOT green |
| Actual selected3.12 from agent | Refused before Python entry: WindowsApps base unavailable |
| Fresh independent review | Requested; not yet accepted at this checkpoint |
| New CR3 selected-runtime comparison | NOT RUN; contract/launcher not frozen yet |

Full MI failures/errors by exact identity:

- test_native_containment.ContainmentTests.test_grandchild_pipe_holder_killed:
  capture_complete false, `tree-sweep: taskkill exit 1`.
- test_native_paths.PathIdentityTests.test_info_accepts_short_database_path and
  test_short_and_long_forms_unify: `OSError: no short form`.
- test_preservation.Preservation.test_release_exact_content_and_declared_changes:
  E_CONTENT_MISSING: tests_v2/OFFLINE1-CONTENT.json (release work still pending).

All54 skips and the one deliberately expected live-Dolt failure are retained
individually in full-mi/Receipt.json. No unchanged full CI claim is made.
Controller seven error records: extended timing E_EXT_GIT_SOURCE_DRIFT; current
C1 extraction E_CURRENT_LIVE_SOURCE_CHANGED for the intentionally corrected
distributed module; and five E_DIAG_SOURCE_PIN records in historical observer
tests (two subtest records in test_overlay_removes_only_observation_nodes_to_original_ast).
Historical inputs/pins were NOT loosened to make those tests green.

Full MI logSHA01b255a5e4155b5d3f37b869ffd97e484bf508d0d33a61c909100351930cb51f.
Controller logSHA3086b71b8a5ea4f7e7f6c6db434d18a933fe5d05dca5687a4d4b3439732f069a.
Final native logSHAa98be0eb7099ba5ddb005d866621b3096ae068a68cb6e04c6fadb384bbd54cc0.
Five helper logSHA80a438fd75aa84b535e03c88d920defd379d25d1b0c6e0feee68626144fad41e.

## Preservation and next bounded action

Before.json39754bytes SHA9ab4cd15cee406a1305d8736df6634c533ebdbd197e9ea28848eaa7eeef6cd32
was saved before production edits. New contracts must explicitly allow only
the named distributed module, owned-job helper and new regression test; never
replace old C1/C2 baselines. Immutable C1source/records, C2receipt/helpers/streams,
MI/CM/source-cache/release trees are checked again before and after CR3.
This is named-scope preservation, NOT a whole private-archive verdict.

The new CR3 composition reuses the existing ordered-method runner, its repaired
subtest accounting, capture helper, and bounded error-chain formatter. Both
new control/repaired copies get exactly the same ERROR-ONLY worker serializer
overlay. No success/search algorithm overlay. The original community/global/
DRIFT/vector order, public timeout90 and lease-refusal probes stay unchanged.
Control failure is an expected negative ONLY for the demonstrated cleanup
class; any unrelated failure stops. Repaired method must pass, with all seven
native controls and pinned preservation. Old baseline failing to reproduce is
reported honestly; it does not magically prove the historical C2 cause.

Selected runtime identity/dependencies precede the new workload claim. Only a
new reviewed, externally sealed normal-account launcher may run it. No old
N3/C1/C2 command, install, ACL/trust change, deletion, commit/push or whole-skill
qualification is included. Copies/receipts remain retained for review.

## Latest SR3 result2026-10-27 — implementation verified; selected runtime pending

VERIFIED WITH CAVEATS for code/controller-native behavior and exact one-shot
handoff. NOT a selected3.12, full-stage, Gate1, release or installation verdict.
AUTH: user "USE ALL REQUIRED SKILL AND SOLVE THE ISSUE" and repeated continue
authorize the existing SR3 local implementation/testing/review and new handoff.
No external AI call, install, security/ACL edit, Git write or old-data deletion.

INTENT: replace the demonstrated launcher-only exit gap with pre-work owned
current-image process-tree control, and integrate the exact reviewed SR2 native
synchronous writer cancellation. One5s cleanup deadline covers both owners;
proof/accounting/cancellation/close failures remain errors and retain resources.
Default120/public90/lifecycle60 unchanged. POSIX/public success schema unchanged.

### Claims and observations

| Claim | Parent observation |
|---|---|
| Current native owner enforces root/child/grandchild shutdown |17/17 current-byte tests PASS; real native handles, nested Job, unrelated process survives; Python3.14 only |
| Startup/stream failures preserve errors and cleanup debt |7/7 integrated Session tests PASS; all attempted closes and retained directory/finalizer debt checked |
| Combined cancellation is bounded and releases blocked writer |12/12 combined legacy shutdown tests PASS; exact SR2 writer18tests also pass in final knowledge run |
| New verifier fails closed and makes exact source copy |16/16 PASS including real627file source copy and exact support/source seal controls |
| Relevant broader knowledge tests remain healthy in tested scope |252run198PASS54existing runtime-dependentSKIP0fail/error/exclusion |
| Broad controller is green |FALSE:459run0fail11errors0skip/exclusion; exact categories below |
| Exact handoff/code review cleared |Same-seat native read-only reviewer rechecked exact final source; final helper/launcher/source/support review SHIP for ONE normal-account focused run |
| Selected3.12/runtime public replay proves complete repair |UNVERIFIED: not executed by agent; normal output/input/preparation absent |
| Original historical C2 exception/escaping handle known |FALSE: saved MP1 outside survivors/writer failure are direct evidence, not exact historical C2 cause proof |

Evidence root for receipts below: .github/run-artifacts/cleanup-shutdown-repair-20261026/.

| Current receipt | SHA256 | Bound log SHA256 |
|---|---|---|
|sr3-script-import-green-01/Receipt.json|f12f87ea6c996ded1beea0618502608909e0e907393b763e52694f1747a4a080|4516c0ff5575e614118fab039247eaefcdca57e949344078297208d18eafdd95|
|sr3-review-session-green-01/Receipt.json|53acaabd1b21709c817c9d08e70da83d9410032d5c577bfd64d2889882dce29e|c51f9b0dc2c2b5e5c4e1a443e35fb56917a5e53513c980ecd42c2db46f1b48f0|
|sr3-review-combined-green-01/Receipt.json|d6895ddabafa12138c81d5eea8c3e84a25129b7b92830d25c0f61d3f55ce655b|d4d2949161470112bf8b3afadbcc3eb573b6d229d15d557481b7cddfd252f0db|
|sr3-handoff-source-frozen-01/Receipt.json|ffca116e9bc2af9ffae757ca74eebef7288ed8fd5fc5ee1c1703d54553b5b28c|435a19f5ce1dc17134d44a7d4c0df82a5b623a8f8473be9e28f30cb6f2eca68c|
|sr3-final-knowledge-reviewed-01/Receipt.json|1b49c2432d98225a41719af9eca27fedcc969a38fa13669f334f8088b69bde10|ea9f2bac9da3e24ce5be3c13ecb7d567bfd4bfb45fa77ccb1f3dd88a32b8227f|
|sr3-final-controller-reviewed-02/Receipt.json|0924f60be78518b5410e122a2571f1b671528a575f563b42de5186c3d21dd158|a36471fb96e9e7c59b1f7e12d1ce46117aba7eedba905e67a0d56937255408ea|

Meaningful RED/GREEN corrections retained: assignment-failure root survival;
proof-gap preventing termination; bootstrap SystemExit/consumed-launcher-env
false refusals; CloseHandle masking original/skipping siblings; expired gate and
unbounded notification-drain; lost constructor/close debt; failed Popen ownership
reference; retained stream failure with auto-delete finalizer; actual script
sibling-import loss; non-atomic active/PID-list false refusal. Final native review
cleared these corrections; no check weakening, new skip, timeout increase or old
input repinning made them green. Initial denied-fixture and earlier red outputs
remain retained, not overwritten. Native creation integers stay in Python-written
proof JSON; no lossy JavaScript-number conversion authenticates process identity.

### Exact current seals

| File | SHA256 |
|---|---|
|memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py|423dd7eec705fe8f209336d6fc7aaba41b51d637ce2871a188578427c2906f32|
|memory-integrity/scripts/knowledge_bridge/windows_owned_process.py|07cddf0821323c5f0388653dda1102d1b46d1f02c20139c2be980f1c32bbe56a|
|memory-integrity/scripts/knowledge_bridge/windows_owned_bootstrap.py|9e7b2c7f2740244aa79d1dd69dd43eb3ae20b92d816b22bc4ea96bea28be3851|
|memory-integrity/scripts/knowledge_bridge/windows_writer.py|72dde9c3a495f0326bf95a1eef25e2eb81ac1333921889a8e48656840f475d29|
|memory-integrity/scripts/knowledge_bridge/windows_job.py (immutable old control)|4b8631c9e4710ecb115e3d1ddb536a0f398a25ef1f7558bc21f527aa38137cb0|
|memory-integrity/tests_v2/test_knowledge_windows_owned_process.py|00c837f55f8527cefe361c5421155b2b8a4e51b177296506b9f249613eb223c4|
|memory-integrity/tests_v2/test_knowledge_windows_session.py|5b989dc3e7e0dfe3aa324caef1f7135cf7001ec4e9a10139a2965603f49852ee|
|memory-integrity/tests_v2/test_knowledge_windows_writer.py|f3f89b80864a909abb704007db24503d475575365a79f02e64fef006cd969b62|
|memory-integrity/tests_v2/test_knowledge_windows_shutdown.py|86a8576e980a28fd062445e7d076917701befbdd6705e08efa22401ded98dbd7|
|memory-integrity/tests_v2/test_knowledge_process_lifecycle.py|cccbb0f88b47b0a0d537e96cd320d25cc93f17ddd39d713a8869a1ca7367355b|
|.github/scripts/shutdown_repair_verification.py|f224d215d0eb8ac898ac6a185cb388d1aa45b627765a006ae266455b800aff69|
|.github/scripts/Run-Shutdown-Repair.ps1|010305e3a8e75ad62c4b6fe4ef527203e31dabea16ca88f87f2c476c9944109b|

Final16case verifier tests additionally hash the source/support contract and
actual copy behavior. Lifecycle test's construction-failure deadline was changed
from expired literal1 to monotonic()+5 to reach the intended Popen fault; original
exception/stream close assertions remain. No production deadline increased.

### Broader nonpasses — visible, not waived

Seven historical error records match prior source-pin baseline categories:
extended copied-index E_EXT_GIT_SOURCE_DRIFT; current-C1 extraction
E_CURRENT_LIVE_SOURCE_CHANGED; transformed two-session observer, live overlay,
actual process overlay and two role subtest records with E_DIAG_SOURCE_PIN.
All exact test/subtest IDs remain in final controller Receipt.json.

Four additional ERRORs are frozen MembershipNativeControls tests:
test_actual_probe_close_failure_becomes_error_receipt_not_success_probe;
test_blocked_writer_uses_its_native_thread_handle_before_fixture_termination;
test_native_probe_binds_four_roles_and_records_emergency_result;
test_nonvalue_error_after_real_writer_start_retains_writer_cleanup.
Their consumed diagnostic expects the former private session._tree.handle API;
CurrentImageOwner intentionally differs. Frozen probe also assumes the earlier
plain Thread API rather than SR2's absolute-deadline native writer. The separate
sr3-legacy-membership-characterization-01 reproduced11run7PASS4ERROR0fail, log
84b0259bca4f201cb76bfbd2040fdd4f1101b3d46c288481716f28d5648b09f2.
Actual worker sibling-import regression found during characterization WAS fixed
and native regressions rerun; remaining4API errors are not hidden as passes.
Immutable old probe/pins remain unchanged; relevant new owner/writer/Session and
combined tests independently check the repaired behavior. This does not turn a
red broader suite green or prove readiness outside the bounded repair.

TWINS: searched stdin.write/accounting().total/writer.join/CancelSynchronousIo
through knowledge_bridge. Old cumulative-total/live-member comparison remains
only in immutable windows_job control, not new Windows launch path. Direct old
writer path is POSIX/legacy fallback. Single-worker WorkerClient and hybrid
capture have no matching demonstrated regression authorizing a broader rewrite;
their separate limitations remain unchanged.

### Reviewed next action, not an executed runtime result

Existing sealed PS7 SHA362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139.
Actual -NoLogo -NoProfile -File VerifyOnly returns
SR3_EXTERNAL_SEALS_MATCH_NO_PYTHON_OR_WORKLOAD; parse0errors. Actual agent-SID
invocation refuses BEFORE Python/output. Parent readback verifies10source,
7support and6oldcontract seals. SR3Inputs/sr3-prepare/sr3-normal are absent.
Independent final review SHIP permits ONE fresh NORMAL NON-ADMIN invocation;
rehash shell and new launcher before VerifyOnly and again before actual run.
No execution-policy bypass or admin is prescribed.

The new helper must fully traverse/recheck all mandatory old/private histories
in that normal account. Agent denial is NOT waived. It creates exclusive
SR3-Inputs.json after preparation; failed preparation retains Claim/Failure in
sr3-prepare and consumes that attempt. Selected3.12 identity/53dependencies are
checked before and after74controls:17ownership+18writer+12shutdown+7session+
6lifecycle+7cwd+7budget; then original ordered community/global/DRIFT/vector
initial retrieval/replay/negative lease method. All groups/discovery/public calls
use selected g.WORKER; sealed copied support helpers run, no unpinned live module.

Read actual sr3-normal/Receipt.json plus bound raw logs/preservation after user
execution. Only all required current-byte observations can set focused-stage
complete. Gate1/release/install/producer-authentication/historical-C2-cause flags
stay false. On any failure preserve/share output and STOP, no automatic retry,
source-pin replacement, inaccessible-file waiver or old command invocation.

## Actual SR3 preparation failure2026-10-27 — no selected-runtime workload

BLOCKED by evidence-folder access, not by an observed failure of repaired
shutdown. User executed exact reviewed Run-Shutdown-Repair.ps1 once; external
seals passed. prepare/build_contract/history stopped at source_manifest/os.walk
on cleanup-repair-20261023/baseline-mi/retained-temp/audit-emwso553 WinError5.
The selected3.12 process,74controls and public replay were not started. Thus the
previous actual-runtime UNVERIFIED gap remains; no new runtime test failed.

Parent readback: sr3-prepare/Claim.json93bytes SHA
b47f548be8ed3cba3a7e50efc4c5b564b1073002b6e72faa2a987046410d173f,
started_utc2026-10-27T08:39:25.461674+00:00. Failure.json1989bytes SHA
779800f964182b9a68a10f67299160151a5e03507cbe18a0c4e06ea4549d4c48,
status PREPARATION_FAILED_NO_RETRY_NO_WORKLOAD; stage/Gate1false. SR3-Inputs.json
and sr3-normal absent. Exact helperf224d215.../launcher010305e3... and HEADa38297d
still match. No command was retried; no marker/data/permission was changed.

Read-only Get-Acl on exact target gives owner
SAKTHI/CodexSandboxOffline SID S-1-5-21-2571509308-2482563067-4170768140-1003;
AreAccessRulesProtected=true. Exact SDDL:
`O:S-1-5-21-2571509308-2482563067-4170768140-1003G:S-1-5-21-2571509308-2482563067-4170768140-513D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)`.
Allows only OWNER RIGHTS, SYSTEM and Administrators; normal SID1001 is absent.
Immediate retained-temp/baseline-mi parents have inheritance enabled and normal
SID1001 FullControl, but protected child does not inherit those grants. This
descriptor plus actual normal-account WinError5 establishes the access mismatch;
no need to speculate about antivirus, package corruption or slow model imports.

Bounded recurrence inspection: direct330directories under baseline-mi/retained-
temp, all330with the same protected owner/system/admin-only DACL pattern,
0descriptor-read errors. This was NOT recursive, did not read all file contents,
and does not prove full history readability in either account. Test source
test_source_binding.py:21 creates TemporaryDirectory(prefix=audit-); immutable
retained_unittest RetainedDirectory uses tempfile.mkdtemp; local Python314
tempfile.mkdtemp invokes os.mkdir(file,0o700). Retention preserves that private
fixture instead of normalizing its security descriptor. The owner/ACL observation
is confirmed; no unique historical creator invocation or all-descendant ACL
inventory is inferred merely from the matching fixture pattern.

The earlier assumption that a normal-account handoff resolves all old-private
access failures is disproved. Keep history mandatory. No-build remains blocked;
smallest recommended recovery is separately approved exact-target read-only
normal-user access, preserving owner/existing ACEs/content and recording ACL
delta. A two-account verifier could avoid ACL edits but needs a new explicit
preservation/provenance design. Do not skip folders, reset ACLs, grant FullControl
or rerun as admin. Permission repair and NEW reviewed/sealed preparation require
fresh explicit authority; current consumed files stay immutable. No selected
runtime/code edits, installs, deletion, Git action or retry occurred this turn.

## Correction: established no-ACL copy route applies to newer SR3 evidence2026-10-27

User correctly identifies the missing precedent. Prior ACL recommendation was
premature: diagnosis of denial is valid, but changing permissions is not needed
as the default recovery. Existing approved copy design already supports fresh
source-reader copies plus normal readback, BEFORE/workload/fresh ORIGINAL AFTER,
without ACL writes. Current normal direct-read SR3 implementation omitted that
integration for newer history. User selects the no-ACL route; no permission
repair is proposed or authorized by this correction.

Fresh parent readback, not memory: old workspace
C:/Users/sakth/Documents/Codex/w-h1-20261022-80b78d91/BEFORE/reader-copy/Copies.json
is39851134bytes SHA956f2c50c5c7290a45f4788f0470a649fa52d735a1d80146492ff3ec33e67951,
status COMPLETE_CONTENT_COPY,46010objects/27208file mappings. Same workspace
BEFORE/Bundle.json13247059bytes SHA
0def61c9a3d9a54bc0ec465c154a110e6ab924049c42fb93c004bb158ef86770,
48799objects, status COMPLETE_BEFORE_SAMPLE_NOT_WORKLOAD_QUALIFICATION. Original
root is .github/run-artifacts/offline-first-20261020, not the newer cleanup roots.
Both actual object-key maps have0cleanup-repair-20261023 and0audit-emwso553 hits.
This proves recorded old BEFORE copy/readback success and missing new scope,
not a previously observed complete workload/AFTER cycle.

Opened implementation evidence: archive_copy_snapshot.collect/scan explicitly
partition readable objects and denied obligations; copy_denied fresh-reads source
subtrees and writes exclusive destinations; verify_copies/bundle_from_copies/merge
verify bytes and disjoint complete coverage. archive_copy_h1.Context adds fixed
historical-data identity/permission/link policy, mappings, session/phase/time
binding and final compare. worker_copy_h1 stages Before/CopyBefore/VerifyBefore/
Run/After/CopyAfter/Finalize with provisional runtime result. Its immutable config
and56path link policy are old-scope-specific, not generic newer-file permission.
Tests inspected include original changes despite intact old copy, added/missing
data, tampered maps/phase/root, partial output, unreadable and protected-input
guards. No test or old staged command was executed by this read-only investigation.

Current shutdown_repair_verification.history still constructs all four roots
via direct c1.source_manifest and then performs additional mandatory checks.
New adapter must explicitly separate historical DATA mapping from direct live
source/runtime/helper/protected guards, preserve all known older expected
inventories, and never claim a copy-only read is a fresh original observation.
Nothing should globally replace source_manifest or weaken original guard code.

Plan/design/checkpoint/state now record SC1-SC3 bounded adaptation: exact roots,
new input-only successor/controls, verified fresh BEFORE, unchanged74controls+
ordered public method with provisional result, fresh original-based AFTER and
final comparison. New exclusive paths only, no old-marker reset or old command
retry. Current Claim/Failure and old H1 maps remain immutable. User has selected
mechanism; detailed successor implementation gate remains pending. No new code,
copy or selected-runtime workload was authored/run, and no ACL was changed.

## SC1 implementation and input-only handoff checks2026-10-27

AUTH: user "start" approved SC1-SC3; user "Approve the exact transition" separately
authorizes NEW verifier's exact checkout f63f62496f82fb479e352bdd9c90accf9f869e8b
predicate. It is the sole a38297d child with four fixed C1 additions, checked by
parent list, exact A-only diff, modes/blob SHA256 and matching live bytes. Tested
evaluation source remains a38297d627files+10named approved deltas. Neither old
HEAD guard, historical source/receipts nor Git state is changed by this work.

INTENT: complete historical evidence verification using existing-access copies
and original-based BEFORE/AFTER samples, not by skipping unreadable data or
changing ACLs. New files are shutdown_copy_data.py/shutdown_copy_verification.py,
their two tests and Run-Shutdown-Copy.ps1. Existing archive-copy primitives are
hash-checked and reused in isolated namespaces. No old module globals change.

The DATA adapter covers exactly four current SR3 roots and validates root/phase/
session/policy bindings, complete disjoint coverage, physical identities, file
hashes and permission digests. BEFORE strict normal request records denied
obligations. Source-reader inspection emits only unapproved exact hardlink policy
proposal; normal externally sealed BindPolicy creates separate immutable child
Inputs/Request after live-authority/visibility rechecks. Protected IDs derive
from every trusted source, runtime, helper, protected-root, original C1 and
consumed-input record. Historical linked data cannot acquire trusted-input role.
Copy refuses an unbound base config. Known original positive history checks
execute before complete verified BEFORE publication. Only two named DATA reads
are adapted; authoritative checks remain direct. Provisional workload stays false
until fresh ORIGINAL AFTER, complete comparison and raw runtime outcome review.

Observed retained controls under sr3-copy-development:

- DATA policy RED12 (missing new API), GREEN12log
  a3ba6e53215d6ce09463483d35f3c47f40afc663b5980009e7e8a143d8409af8.
- Exact checkout RED17/2FAIL, then GREEN17 actual627-file source observation.
- Policy coordinator RED20/3FAILlog
  c5be31cfab1bf7ade38f995d0c11c2889fd8fb87ba79f0e79058ae99106ab283,
  then GREEN20 and final linked-policy GREEN21log
  6f546b335ebae1c4f232550ed6f419a1341966637988562910fe85c93858c5e7.
  Final case drives real denied retained-temp hardlink pair through policy
  proposal/seal/bind/copy/readback; source remains2links/ACLunchanged, destinations
  are1link with equal bytes. Access denial/account/real positive history are
  explicitly controlled; this is NOT real cross-account historical qualification.
- Copy regression106PASS0nonpasslog
  9666e18493d17532d4a1c6e2f1ae15299097bfa06e1279029636e6f563affdb7.
- First broad controller491run:2FAIL24ERROR0SKIPlog
  247c9175358def84ada3fa9cd8414593c8f49cdc699463e3e6d0ac59c5f59a87.
  Sixteen error records are denied old test-output folders; eight are old
  source/HEAD pins. Two local nested-run failures retained. Timing nested stdout
  proves WinError267 invalid child working directory at the long new development
  path. Targeted unchanged timing23 and gate23 PASS from a shorter test-output
  location, logs33c9152b46e9ca090e7bd86bd507a8c174c662111c81649e2ae7be0bdf953b4c
  andb45f57637e6f2d0cfff10aadd80bed4dd620ebb3bbaa4b93a0817e49d4b36e04.
  No guard/test was weakened. A dedicated short Documents root was denied and
  stayed absent; existing writable test-only output used without ACL changes.

Sealed candidate coordinator234dd24e90a33feeee9fbacd5e75f03b2099c8393b7be86d3d9f994d99946cd3,
DATA4fa0afdaa1219b243421717eca9a8d2939c4f653a8d9b27110e2b63c80e27299,
BEFORE-only launcher5554f4b3d45514262f2e497636642e435f2c535f9249957fdede7073c45ea7e1.
Existing PS7hash362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139
matched. Observed parse0, actual PS7VerifyOnly pass, deliberately wrong helper
seal refused before Python, and actual SID1003 invocation refused exit1 before
Python/normal-root creation. Source21fixed source/old-input pins freshly match,
including consumed SR3Claim/Failure and old launcher/primitives. No actual normal
request/copy/runtime ran. Independent final exact-input clearance is pending.

TWINS: recurrence search finds consumed SR3's direct four-root inventory and old
W/H1 copy-phase controllers. Old files remain historical immutable controls;
new closed adapter alone handles approved data transport. No generic inventory
substitution or duplicate worker supervisor introduced. PENDING: actual normal
BEFORE, source-reader proposal, reviewed child bind/copy/readback, selected312
74controls+orderedmethod, fresh AFTER and independent final raw-result review.
All actual focused-stage/Gate1/release/install flags remain false.

### Final SC1 narrow verdict — VERIFIED WITH CAVEATS2026-10-27

Same native independent reviewer inspected exact frozen files and final nonempty
hardlink integration receipt: SHIP ONE normal non-administrator BEFORE invocation
only, no Critical/Important for that action. This does NOT clear InspectBefore,
BindPolicy, copy, runtime, AFTER/finalization or actual stage acceptance. These
need actual prior-phase records and their own sealed/action review. Final parent
rehashed coordinator/DATA/launcher and verified new normal root ABSENT.

Larger feasible regression at shorter existing test output completed492cases,
0FAIL12ERROR0SKIP, retained log
270736b1864cd23a2bf6a227517cafe700c5d8f578e11786d965937612442ce2.
Exact errors:4old membership probe CurrentImageOwner.handle AttributeErrors;
8oldguard records (5E_DIAG_SOURCE_PIN,1E_EXT_GIT_SOURCE_DRIFT,1E_CURRENT_HEAD,
1E_SR3_HEAD). This is not clean CI. Scoped capability grants for existing test
output allowed the16scratch-denial records to be observed further, without ACL
change. Both initial nested failures pass unchanged under shorter cwd. No old
pin guard was repointed at f63; the approved predicate lives only in NEW helper.

Handoff only: existing PS7plus frozen Run-Shutdown-Copy.ps1, VerifyOnly followed
by one normal Before invocation. It calls only existing Python314; writes new
Inputs/Request (and phase claim/failure if necessary), not selected312or copies.
Share both printed path/size/SHA records. Stop on any failure and retain all
outputs; do not delete destination/retry old command or infer stage completion.

## SC2 actual normal BEFORE and source-reader inspection2026-10-27

User ran the sealed BEFORE-only normal command. Parent freshly matched both raw
records: Inputs596109bytes49f19acc752bb0b97594db194873c1f3f994212edca3dc7ba1af50021094b21a,
Request1227544bytesc81c2d9b095c108893dee9fe0b10ce625462d3b736e2a41c3782eca5aac70e42.
Actual Before-Claim155bytes SHA5ab3b8d167eaadb83368e19d907e87f6fa2f665d5182770db963360deb735aa0.
No Before-Failure exists. Actual session/sealed-request/DATA validators pass:
627source/tree,10deltas,7support,12runtime records,53dependencies,642C1inventory,
4protected manifests and1379complete positive unique protected physical IDs.
Exact checkout f63/a382/four-additions proof remains valid. Three roots have
43/50/726readable objects,0unresolved. cleanup-repair has2432readable objects,
1240exact unresolved directories, never treated as empty coverage.

Independent read-only actual-artifact review SHIP ONE InspectBefore only.
Metadata traversal of all1240targets observed1800dirs/4396regular files,
0access errors/redirects/overlap/protected-ID hits/hardlinks. Existing source
reader SID1003 owns sampled denied data and has inherited Modify on successor
destination. No ACL edit was made. Metadata alone was not claimed as content
proof: parent then executed exact frozen InspectBefore once with both external
seals after checking controller/helper/DATA/basefiles. Exit0; actual proposal
225555bytes SHAdce8bda736214950bc69e63d585027a750982789ae4ca69e9062f66bbd78b1c5,
InspectClaim162bytesbc6addbfbb8ed40340043c164b75a6f0a8b908c8d31fc72702023e80aa01526e.
Frozen code double-reads all unresolved originals and checks content/physical
identity/permission stability before success publication. Completed proposal
passes root/request/protected-ID validation, allFOURallowlistsEMPTY, no linked
exception requested. policy_approved=false/producer_authentication=false. Parent
rehashed initialInputs/Request unchanged and confirmed no InspectionFailure,
normalBindClaim/childinputs/copy/run/AFTER/Final exists. Claim-to-proposalmtime
97.865s is approximate sampled wall time only, not monotonic/CPU/import timing.

No product/helper/test/launcher changed this turn; no focused/broader suite
rerun was needed for unchanged code. Actual executed input phase is new evidence,
not selected312shutdown qualification. Prior focused21/DATA12/copy106 receipts
and full492run0FAIL12old diagnostic/pin errors remain exactly caveated, notgreen.
The actualsource-reader content-read path now succeeds without ACL changes.

Next candidate is normal BindPolicy only using exactproposal seal and original
config. Inert review text SC2-Bind-Command.txt SHA
4cc4e3c7f96744647d32d5d0b19e2646ee14ebbd3fc7dd6c382f24bf6dcc85ae
pins6file roles, rejectsexistingphase outputs, callsone frozen Python314 mode.
Observed parse0/singlePythoncall; wrongproposalhash negative refuses before
Python. Actual SID1003 BindPolicy invocation correctly returns
E_CURRENT_NORMAL_ACCOUNT_REQUIRED beforeClaim; it did NOT consume normal binding
or create a failure file. No identity bypass was used. Await independent actual
proposal/exactblock review. User SC1-SC3 authorization remains; do not ask same
design approval again. Copies/readback and actual selected31274controls/public
method/fresh ORIGINAL AFTER/final review remain required. Stage/Gate1/release/
install flags remainfalse. New content inspection is not a package-reinstall
diagnosis or a completed worker-shutdown observation.

### SC2 actual proposal/normal binding handoff — VERIFIED WITH CAVEATS2026-10-27

Independent actual audit: proposal canonical7-key schema; correctsession/origin/
requestdigest;4exact H1root policies, emptyallowedmaps,1379exactprotectedIDs.
Real validate_policy/SnapshotSet pass and fresh direct_authority matches actual
Inputs. All initial/proposal/claim paths ordinarysinglelink, frozenhelper/DATA/
controller hashes and HEADf63 agree. BindClaim/Failure/child/copy/run/AFTER/Final
remain absent. Exact inert outerblock4cc4e3...parse0 hasonePythoncall and reviewed
config/proposalSHA literals. bind_policy beginsnormal() and can only exclusively
claim/rescan/produce childRequest/Inputs, no copy/runtime. No Critical/Important
for this action. Reviewer returned substantiveaudit+SHIP in message before final
workspacecrediterror; onnewusercontinue SAME reviewer finalized SHIP. Crediterror
itself was never treated as clearance. The completed substantive and final
verdict are retained separately in SC2-Before-Inspection-Review.json.

SHIP ONE normal non-admin BindPolicy, full outerblock only. No code changes or
new launchers; initial frozen Beforelauncher remains consumed. Resulting child
hashes/lineage/unchangedempty policies require review before CopyBefore. Stop and
preserve on anyfailure, never retry, deleteclaim or weaken guard. Residual file
seal/checks are not atomic against hostile concurrent same-root writers; sampled
preservation and eventual AFTER remain required. This narrowly cleared binding
does not prove copied-data coverage/readability, worker shutdown, selected312,
Gate1/release/install, historicalC2cause or authenticated producer.

### SC2 normal binding and actual BEFORE copy — partial2026-10-27

User's normal BindPolicy observation was matched against actual childInputs
822007bytes c91235f95b135a1e170893513d3105095fb5dd39feef268eb3b2fec3c4cd3180
and childRequest1227544bytes cd5ce65e48f7a604fb577279e9dea3ab8e8c30bfbddf907c1ab222f5c6b476ff.
InitialInputs/Request/proposal lineage/policies/partition remained unchanged.
Same native read-only reviewer returned FINAL SHIP for exact existing-access
SID1003 nonadmin CopyBefore. Parent checked8pins/identity/absentoutputs, then
ran ONLY that phase once. It completed exit0 SC_COPIES_REQUIRE_NORMAL_READBACK.
CopyClaim159bytes d3ad95e78e25ac84aa1d6376c1801d16983163a4b2b5917c0f68b9137ce20e99;
outerCopies1283bytes f9a38306ee2e4bf351e5d824932e92d486e736668de596cf8bcf223cf78d3b7b.

Restricted root cleanup-repair-20261023 manifest6387158bytes
93889b64bc39798dc5a7f70cfb1c3ca6f67d532a9028f00a2925376435292c57
contains7436objects/3040dirs/4396files,4396exactmappings,33362733bytes and complete
1240requested-directory coverage. Its batchUTC elapsed257.758972s includes
source/copy/readback/validation, not CPU/import/runtime profiling. Other3roots
have no deniedtargets and valid emptycopy manifests589bytes each; their directly
normal-readable histories remain required. Parent ran actual session, outer
bindings and ALL H1manifest/schema/coverage/mapping validators independently;
direct_authority still equals boundInputs. This is not a normal-account byte
readback. No CopyFailure, VerifyBeforeClaim/Failure, Bundle or runtime exists.

Next inert SC2-Verify-Before-Command.txt45a860e33fff4e6670a470ce87014e61a30a50c282519e6dd7b58961849c8089
pins13actualroles including outer+4perroot manifests, exactnormal1001/nonadmin,
and absentreadbackoutputs. Parse0/onePythonVerifyBeforecall, actualwrongSID
beforePython refusal and extracted unchanged pin-guard inmemorywrongouterSHA
refusal observed. First audit incorrectly counted outer scriptblock invocation
as a second Python call; audit predicate corrected, command bytes unchanged.
SAME independent FINAL actualcopy/exactcommand review returned SHIP exactly
one fullblock45a860...normal VerifyBefore. Actual canonical4manifests/path/size/
hash/context/policy/coverage/mappings match, original linkcounts1, no merged
overlap; manifest-only timing/stack/1339CR3 positive baselines satisfy. Reviewer
did NOT claim normal byte-readback or runtime execution. Only real normal
merge/bytevalidation/visibility recheck and old positive originalinventory
guards may publish BEFORE/Bundle.json. Do not chain runtime, retry a consumed
phase, edit oldguards, alter ACLs or claim worker/Gate1/release/install complete.
No source/helper/test code changed, so unchanged suites were not rerun. Prior
focused21/DATA12/copy106 pass and fullcontroller492/0FAIL/12oldAPI+pinERRORS remain
carried accurately, not greenCI. Stage qualification still requires selected312
74controls+orderedpublicmethod, freshORIGINAL AFTER/readback/comparison/review.

### SC2 actual normal BEFORE readback — VERIFIED WITH CAVEATS2026-10-27

User executed reviewed45a860...fullblock ONCE. Status
SC_BEFORE_VERIFIED_NO_WORKLOAD, Bundle3092807bytes
29fba89ef123eb5c4e9df957f0bbfacad58328301787658dfc42a95356a81019.
Parent matched ordinarysinglelink actualrecord and VerifyBeforeClaim161bytes
b7b9a11ed7a30c4e3f5f07f28034db63cb650521ae19b70e439e0bd567d372b4.
All Bundle outer/perrootfields equal exact derivation of sealedpolicyrequest
and aggregate/perrootcopies; noobjectoverlap. Totals7345files/94513658bytes:
repair6617files/77717214bytes; timing666/14395696; stack27/1205614;
membership35/1195134.4396repairfiles supplied by copies, allotherfiles direct.
Normal frozen merge verified destinationbytes/mappings, originalreadabledata/
unresolvedpartition and originalpositivehistory before save. Actualpublish
and absentFailure observed. Fresh parent direct_authority equality passes.
No source-reader normalcontext bypass or duplicate phase. Retained detailed
SC2-Before-Bundle-Observation.json. Thus noACL BEFORE accessblocker closed,
not worker/runtime/fullarchive/producer/continuous preservation qualification.

Next inertSC3Run candidate8f64b8490972e048fe6e0b649d71f8b40f5a9a40004ee7d6e175d2d734c22bf0
pins14roles inclBundle and retains exactnormal1001/nonadmin/absentoutputs.
Parse0/oneRunPythoncall, actualwrongSID outerrefusal beforePython/claim,
inmemorywrongBundleSHA and simulatedexistingclaim refusal observed, nofiles
changed by negativecontrols. SAME independent FINAL read-only actualBundle/
runtime namespace/exactblock review returned SHIP ONE normalnonadmin Run-only.
All4root unions exact,14pins bind, only historicalDATA observations substituted;
originalsource/runtime/dependency/protected/positiveguards remain direct. Exact
f63transition accepts only approved4additions; evaluatedsource627a382+10deltas.
Discovery no-skip/no-exclusion and74counts, unchangedpublicmethod and pre/post
selected312 identity/dependency attestation retained. No realphase inreview.
Raw actualcontract/receipt/captures/discoveries/publicoutputs must be reviewed
before AFTER, which this narrowly cleared Run block does not chain or clear.
Run itself rechecks BEFOREbytes/visibility and directsource/runtime/protected
guards before claiming;74selected312controls then retainedpublicorderedmethod.
120/90/60/600/5budgets unchanged. Runtime success still provisionalfalse until
freshORIGINAL AFTER and fullcomparison/rawreview. No selected312 or RunClaim
exists now; no code/helper/tests changed, no install/ACL/Git/delete/retry.
Prior21/12/106 pass and full492/0FAIL/12oldAPI+pinerrors remain NOTGREEN.

### SC3 actual failed runtime — prior readiness is superseded2026-10-27

User executed exact8f64b849...block ONCE. Actual receiptbeab04ef...10011bytes,
RuntimeInputsf4d945d7...1283822bytes, RunClaima96e942b...152bytes and RunFailure
c908bdc4...1250bytes matched. Raw4commandrecords/8stdoutstderr captures bound;
testreceipt/log/sourcecopy agree with runtimecontract, no retry. Fullrecords in
SC3-Failed-Run-Observation.json. First3commands(identity,dependencies,discovery)
exit0; ownership commandexit1/EXITED, timed_outfalse/capturecomplete/noerrors.
All53installed dependencyversions match.17ownership tests3.424s,9errorrecords,
0assertionfailures/skips/exclusions. All9maintraces reject bootstrapbaseidentity;
unitlog31b890a700844cabbd0636cadf7735610b1c70a2f632a2380a28c94be705eaa8.
No completepassinggroup is appended because capture failed beforegroupreceipt
acceptance. Remaining6groups and orderedpublicmethod notstarted. NoAFTER/Final.

Primary failingpredicate: bootstrap compares observed sys._base_executable to
expected.base_executable; owner constructs expected.base_executable=image.
Actualpassedparentprobe records WindowsAppsuseralias/python.exe as base and
package/python3.12.exe as loadedimage, already handled as different exactroles
by old gate1_image_successor runtime_expectation. Directchild's actualbasevalue
is NOTrecorded in serializedfailure. Source-reader access to selected newprivate
retainedownedtreefixture denied; no capability/ACL/account bypass attempted.
Do not promote parentmetadata into a fabricated childobservation. This is a
startupidentitycheck failure, not evidence of slowimports/dataset processing.

Secondarycleanup notes WinError31/5 and E_OWNED_EXIT_UNKNOWN remain visible.
Code only pinsmembers after ready; earlyexit-before-pinning is a falsifiable
hypothesis, not exactnativecall proof. Both rolecontract and failed-start exit
proof need causalcontrols before any fix. No identityguard removal/samehash
aliasallowance, broaderkill, suppressnotes or largerbudget. Existing Fableplan
now has bounded SR4-D1/D2/D3 proposal; approval pending for new behavior and
fresh successor, not repeated SC3. Independent read-only cause/design review
requested. Product/helper/test bytes unchanged; prior tests not rerun. Stage,
Gate1/release/install/fullpreservation/historicalC2cause remain false.

Independent FINAL cause/design review2026-10-27: FIX-FIRST. It confirms the
roleconflation (singleexpectedbase=image construct), missingdistinctrole assertion
in existinglauncherenv test, and post-ready rootpinning weakness. Exactchildbase
and exactnative31/5 call stay UNKNOWN. Recommended changedstartupcontract:
attestedparent base role separate from exactimage; structured tokenbound
failureframe; native rootpin afterassignment BEFOREresume; explicit unassigned/
assigned-not-resumed/resumed cleanupstate with namedoperation diagnostics and
unchanged5s. TrulyunknownPID/releasebeforeproof still refuse; no suppressions.
Existingplan refined to controllerRED/GREEN -> reviewed ONE newselected312
ownership-only observation -> onlyafterpass new fulloriginal74+newregressions/
public+freshBEFORE/AFTER. Original17ownership cases retained with exact newIDs/
counts; do not weaken tests by deletingaddedcases to retain oldnumeric17/74.
Designreview changes no files and confers no newattempt authority. Approval
pending for bounded SR4range; no oldcommandretry/ACL/install/Git/delete/budget
change. Fable/SystematicDebugging require this scope-changing security contract
to return to plan before another implementation attempt.

### SR4 approved execution — D1 remains under correction, 2026-10-27

AUTH: user said "aprove" to SR4-D1–D3. This supersedes the approval-pending
paragraphs immediately above; there is no second approval gate inside that
range. Local work only, with the original 17-case ownership file, old helpers,
all consumed attempts and their source copies left immutable.

INTENT: distinguish parent-attested base executable from loaded image, pin the
exact assigned suspended root before resume, and retain bounded identity and
named failed-native-operation evidence without permitting disposal before
native exit proof. The shared shutdown allowance remains 5 seconds.

Retained D1 RED at .github/run-artifacts/sr4/d1-red-01: 22 cases, 1 failure and
3 errors, 0 skips/exclusions; all original 17 passed. Missing expected-identity
builder, startup state/pre-resume root record and mismatch rejection were
observed. First candidate d1-green-01 was NOT green: 3 new failures. Later
candidate d1-green-03 passed 22/22 in 6.738s (log SHA
7e6a05669b2c7f028730f233bdf2d2c9454e661d63b6de5cb857d829bfa5feeb).
This candidate result is not D1 clearance: independent read-only review found
missing failed-operation attribution, absent early-EXIT-without-NEW coverage,
root pinning through fresh OpenProcess rather than the assigned Popen handle,
and a resume/handle-close exception boundary that could mislabel startup state.
Corrections and causal tests are in progress; do not freeze these bytes yet.

Parent first observed 14 new handoff guard tests RED before implementation;
the implementation worker retained them and added further strict-frame and
accounting controls. Missing-helper failures establish interface absence, not
14 independent runtime defects. D2 source hashes and exact new case IDs remain
UNFROZEN until D1 is stable and parent verification plus final review pass.

No selected Python 3.12, D2 preparation/run, old-attempt retry, package install,
permission/ACL change, Git action or original-data deletion occurred in this
controller-development layer. All stage/Gate1/release/install and archive-wide
preservation claims remain false. The narrower D2 ownership observation cannot
replace D3's fresh original BEFORE/AFTER evidence.

### SR4 parent completion of interrupted draft — controller evidence2026-10-28

The native implementation and first handoff draft stopped on workspace credits,
not a runtime finding. Parent retained and inspected saved code plus raw REDs,
then completed the approved local work. No discarded/restarted implementation,
no source/reset/old-history rewrite. New final read-only native review is running.

INTENT: parent-attested base role remains separate from exact loaded image; root
ledger uses a same-process non-inheritable duplicate of Popen's assigned handle
before resume. Its original handle remains Popen-owned. Resume-close failures
retain accurate resumed state and recoverable native-handle debt. Assigned but
not resumed cleanup has its own terminate/wait/native-proof path and the same
5second allowance. A signalled known process set still requires a fresh empty
Job/accounting observation; a stale PID snapshot is not a reason to terminate
an already-exited root. Unknown members/exits and failed native calls remain
blocking errors, never successful disposal. Named operation evidence now covers
actual failed waits/termination/accounting/completion queries. Error/ready reads
are byte-bounded; oversized identity failure explicitly omits rather than trusts
a partial identity frame. Normal expected/observed roles remain available.

Microsoft primary references were checked read-only: DuplicateHandle's same-
object/non-inheritable/same-access semantics, ResumeThread's previous suspend
count, and TerminateJobObject's nested-tree contract. No install/login needed.
https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle
https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread
https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject

Retained parent evidence, all under .github/run-artifacts/sr4:

| Observation | Actual result | Retained log SHA256 |
| --- | --- | --- |
| parent-d1-resume-baseline |28/28PASS, interrupted candidate only|3b57e5253637c72e6c604746b6ad345058a17c2897eff7f4d8d2219861736418|
| parent-d1-red-05 |33run,2FAIL/0ERROR; state and false-operation attribution|c8d800cab32794d7226d57c854eb889cfe04052bb8052376fa19ac702c1e83bc|
| parent-d1-green-05 |33run,1FAIL; NOTGREEN, transient fast-exit cleanup boundary retained|4d0e3ffd17df9bbb2902345ab15ced42d191a29a6c370db57d4a6db0626f59a9|
| parent-d1-red-06 |35run,2FAIL; total frame bound/ready read bound|e5a345285c617b439eda18389018963ab8106c555fa4b3f81fe4cf9b1072df26|
| parent-d1-red-07 |36run,2FAIL/1ERROR; bounded-frame controls plus deterministic stale-PID control|3e320f21b27a69666e5e1c0eb08a755823df2923ba9c515029fa581a20275983|
| parent-d1-green-07 |36/36PASS,0skip|8c213173e4601280ac618bca048f3a442020e5db909e317324409bd47c0d783c|
| parent-d1-red-08 |38run,2FAIL; missing query-operation names|c31737b0fdb77379f36a4fc3593935864fe27cadea59d55f2f36ac0b0435faa1|
| parent-d1-green-08 |38/38PASS,11.630s,0skip/exclusion|d1f84f5ab04e2afaed68d02c046aa2ef453c107841f48de7a5561001a3cb8b1f|
| handoff-red-04 |22run,6FAIL/2ERROR; missing evidence/claim/history/source guards, wrong support pin|3d66282e74e9b15ec39b8df48ed045dfd7009e3e7d89e3074d69245789b3f478|
| handoff-green-02 |22/22PASS, before full termination schema correction|61e5840d989d74bd838aa9f890b5e08e4d7ec8658600f15838add6bed6080a38|
| handoff-red-05 |22run,3ERROR; minimal mock termination schema rejected actual full proof shape|29be0192e656d87d8d47aea059577641fddb4372c35d4cf36721b44e88d6518b|
| handoff-green-03 |22/22PASS,2.132s,0skip/exclusion|6be525b737242c4128f5b06b84f4036f22e19db50570cb7300248707cb634e57|
| parent-knowledge-final-01 |273run,0FAIL/0ERROR/54existing runtime skips,97.413s|ab4e18fc9a5b305b929b655f24238a5896e46f6219c4c918c5c109b57e1b4cc8|
| parent-controller-final-01 |514run,0FAIL/12oldAPI+pinERROR/0skip,97.461s,NOTGREENCI|e0c0a947048f5f7e7b157b3bbd6121a479dec9679621cb32f572a28ef456ac46|

Original17test, SC/DATA/SR3 helpers and consumed SC3 critical record/source pins
were freshly rechecked unchanged. Read-only new contract candidate:281611bytes,
SHA2847223633c0cb97c71fb9b9aec9a445f9770fd0a1a1b46135185383642c6005.
Real retained extraction parent-copy-check-01:636files, exact627base+11deltas,
no selectedruntime. Candidate helper SHA4edd413606bdf9495e026888106e8c6aeb63fe1dc20c99f145dd7240562c33ce.
Candidate outer block SHA877335eae64f3c6c6f1c4a155c092e4fbfab4ee3e3034516d9648604645620d7
has0PowerShell parse errors. Review is still pending; no command issued yet.

TWINS: recurrence search over live knowledge_bridge and .github/scripts found
no other active base=image assignment; the existing image-successor validator
already preserves distinct roles. Frozen historical guards were left intact.
This is controller3.14/native-stdlib evidence, not selected3.12 observation or
proof of the exact historical C2/SC3 native31/5 call. D2 will capture full child
identity and unit failure detail, retaining all commands before validation; its
result remains ownership-only with all full-stage/preservation flags false.
Only its actual observed pass permits D3's full controls/public/fresh ORIGINAL
BEFORE/AFTER. No package reinstall, ACL/security/Git change, old deletion/retry,
new Python environment, numerical model or external AI consultation occurred.

### FINAL SR4-D1/D2 judge — VERIFIED WITH CAVEATS2026-10-28

Independent native Sol final read-only verdict: SHIP exact D1 and ONE new normal
1001/nonadmin D2 ownership/startup selected312 observation. No Critical/Important.
It independently inspected actualdiff, original17bytes, all38loggedIDs/order,
native ownership/resume/debt/boundedcleanup, actualreceipts and all oldcritical
pins, source/runtime/protected scope, provisionalfalseflags and exactouterblock.
It independently rebuilt the deterministic input contract. No actual selected
runtime, Prepare/Run, original deletion, ACL/install/Git or oldretry inreview.

Final exact seals supersede the candidate values above:

- helper d845e1077617d2042f0bd2367e700927aeb4310721957469bc9e30c3e36d117e;
- expected Inputs281611bytes,319d71ed8ebcbc324651237213691b79a9f1d76bc0064ae235d484d8b401c3f3;
- .github/run-artifacts/sr4/SR4-D2-Command.txt,
  476e012fe1a923d8309dab15e75c1e5966f9889916c75405d9fee36f842dc3e5, parse0;
- final helper22/22controls, handoff-final-04, log
  905cf89c4d2b58aa03c146b4b20bcfc1da530c2a22d4ef98f9d80ed4d4be1ff9.

Only helper self-description changed in the final reseal; D1sourcebytes and
38focus/273knowledge/514controller evidence remain exactly as above. Normalroot
sr4-owned-20261027 remains absent at issuance. No stage completion is inferred.
The clearance is exact-byte D2 only; changes require fresh seals/review. Stop on
any host failure and retain rawoutput/receipt; no automatic/manual oldblock retry.

One Low nonblocking caveat: new startup test compares a ctypeshandle object to
Popen's integer handle; inequality there is type-driven, not numeric proof.
Production uses real DuplicateHandle with verified Win32 same-object semantics;
other independently observed native exit/retention controls remain load-bearing.
No frozen-byte change was requested for this nonblocking assertion refinement.
Actual selected312childbase and fullworker shutdown remain UNVERIFIED until new
D2 and then D3 controls/public/freshORIGINAL BEFORE-AFTER/copycooperation. This
review does not qualify D3/fullstage/Gate1/release/install/archivepreservation or
production. User's approved D1–D3 range remains in force without another gate.

### ACTUAL SR4-D2 judge — REFUTED descendant proof; no retry/D3,2026-10-28

The previous SHIP was a one-attempt handoff clearance, not runtime acceptance.
User consumed that exact block. Receipt107774bytes SHA
bcbecdbb360261f9992031ea348a13954d2840b7e78b67a10cb3b8022e205651 matched
the pasted output. Main independently revalidated Inputs319d71ed...281611bytes,
all636copiedsourcefiles/current source-runtime-protected/old critical guards,
4Commandrecords/8streams, unitreceipt and all62loglines. Discovery and log have
the exact38IDs/order; all commands exited with complete capture, no timeout or
overflow. Post-runtime identity/dependency commands were not reached after the
failed unit; do not relabel pre-work checks as post-work observations.

| Claim | Observed |
| --- | --- |
| Correct base/image startup | Actual child expected/observed roles match; one-root positive frame native exit/released=true |
| Every descendant stopped before success | REFUTED: owner.stop returned, proof=true, independent descendant native wait258 |
| Nested fixture ready means completePID | REFUTED: int('') at test226 after exists-only _wait_file |
| This is a timeout/package-loading failure | Unsupported:38tests10.874s; capture complete, no timeout; identity/53dependency checks passed |
| Full D2 acceptance | Failed honestly:36PASS/1FAIL/1ERROR, no skips/exclusions; every21newcase passed |

All failing tests belong to the immutable original17. No test weakening,
assertion removal, skip or allowed-error list was used. The one-root positive
artifact has records/accounting=1 and cannot override the tree contradiction.
Original root identity equality and pre-resume exact duplicate mean root was
signalled; either child or grandchild (possibly both) was not. The generic loop
does not log its index, so naming the child specifically would be invented.
Independent final runtime review corrected this ambiguity and returned FIX-FIRST.
Open native handles predate stop, so a later PID reuse is not an explanation.
Outer capture tree_contained=true is safety evidence, not inner exit proof or
evidence that an orphan persisted after capture cleanup.

First cause is confirmed: Path.write_text creates/truncates the PID marker before
complete content, while _wait_file returns on existence alone. The proposed
atomic publication correction strengthens the fixture without weakening its
native wait assertion, but it changes a frozen17file and needs explicit scope.
Second cause remains unknown: no failingcase ledger/events/inner membership/
role image/creation state was saved after the assertion failed. Private reads
of sr3-owned-tree-5iowt4s1/tree.json and sr3-nested-job-hftpqmlz/nested.pid were
denied1003; no permission/account/copy bypass. Store/venv/broker discontinuity
is a hypothesis, not fact. Official contracts independently state nested-job
resource accounting and PID lists include child jobs, and IOCP notifications
are not universally guaranteed; do not use generic nested omission as a cause.
https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port

Raw old run remains immutable. New retained read-only observation record is
.github/run-artifacts/sr4/D2-Failed-Observation.json. The first parent verification
script accidentally counted repeated ERROR/FAIL header IDs as executed cases;
its read-only assertion failed, then the corrected parser restricted IDs to
actual test-start lines and verified all38 in order. No workload was retried.

The SAME Fable plan now compares preserve-failed/no-build, bounded per-role
diagnostic+fixture publication correction (recommended), and a larger controlled
launch supervisor/fence (held outside default scope). Approval pending for the
NEW DR1–DR3 diagnostic/frozen-fixture scope. No diagnostic or product/test edit
was built in this review; no selected runtime re-executed. D1 ownership criterion
is reopened, D2 consumedfailed and D3 remains unrun. Do not issue the old block
again. No install, ACL/security/Git action, original-data deletion or budget
increase. Complete stage/Gate1/release/install/preservation remain false.
