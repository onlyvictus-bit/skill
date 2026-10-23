# Gate1 actual host result: one public distributed cleanup failure

Date2026-10-21; HEAD923de16c91a9ef4381e7ac975e3a3780f42a4bf5 unchanged.
Current work is read-only result diagnosis plus campaign/checkpoint records.
No production/helper/contract/launcher edit, new runtime, retry, deletion, ACL/
trust/admin change, package build, install, commit, push or qualification.

## Host receipt and direct parent verification

Root: C:\Users\sakth\Documents\Codex\gate1-923de16-20261021\image-successor-20261021.
Receipt.json:14138 bytes, SHA256
19c95ff5462c42aa6e8780c4ee4a8bbb473eaa10492c93b29f3bc32e71d82c26.
Parent directly read the saved bytes and matched the user's printed identity.
All14 bound stdout/stderr records for seven commands matched size/SHA. Every
command was contained/exited without timeout, output-limit or capture errors.
suite-3 exited1, all earlier commands0; all outer stderr streams are empty.
The useful test traceback is in tests-3/unittest.log, NOT suite-3/stderr.log.

Parent verified contract/Expected-Runtime/runtime-observation/cleanup records
against main receipt hashes. Expected-Runtime.json EXACTLY equals observed
runtime JSON, including image, safe environment and PATH digest. Both prior
identity/case fixes now pass on the actual selected Store3.12.10, not just a mock.
evaluation-claim.json exists; the successor attempt is consumed and closed.

## Observed stages and coverage

| Stage | Actual result |
|---|---|
| Input/history preflight and identity | Passed |
| Standalone real-worker cwd/cleanup | PASS_REAL_WORKER_CWD_AND_CLEANUP |
| MI native containment suite |3/3 PASS |
| MI native paths suite |2/2 PASS |
| MI offline release profile suite |16/16 PASS |
| Knowledge suite |191 completed:177 PASS,1 FAIL,13 declared SKIP |
| CM offline release profile |NOT RUN (5 cases remain) |
| Final24-arm coding acceptance |NOT RUN |

212 named cases completed in total:198 PASS,1 FAIL,13 SKIP,0 ERROR. All191
knowledge case IDs match the frozen source contract and every case finished.
All13 skips match the explicit optional-parser/model/POSIX allowlist; none
silently bypasses the failing public distributed path. The first three suite
Case-Outcomes hashes match the main receipt. Parent recorded the fourth hash
separately; a failing suite is not promoted into the accepted-suite list.

Knowledge log SHA256 bf8c2c0f1edeb6a9806ca041e4a5ae1f1de31a4e7b5ebb0e1b90e7f0f4664a82,
verified against its retained suite receipt. Actual elapsed504.066 seconds.
Failing unittest:
test_knowledge_completion.RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay
Only failing subcase: strategy='vector', execution='distributed-local'.
CLI exit2, no reported adapter calls or approval consumption, overall BLOCKED:
ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP.
The earlier community/global/drift subcases are not reported failing; they do
not substitute for vector/distributed success or the unrun24-arm comparison.

## What the cleanup positive really proves

Helper returned real handshake and lexical two-shard results. Parent verified
all three pre-cleanup snapshot inventories/hashes and independently observed
FileNotFoundError at all three original owned cwd paths (not permission refusal).
Three directly launched processes were recorded, all observed reaped by helper;
all caches were isolated under invocation-owned cwd before removal. No source
or old-data deletion is implied. This is a real bounded positive control.

It does not prove every public CLI lifecycle path or descendant timing case.
The helper snapshots files before deleting; that adds work before cleanup. Its
direct-PID observation is not complete OS descendant-tree proof. No claim that
snapshot timing caused/masked this failure is established. Preserve both the
positive result AND the conflicting public-path failure; do not discard either.

## Exact cause boundary: cleanup location known, low-level cause UNKNOWN

distributed_retrieval.py finally collects stop/close exceptions. When there was
no primary exception, it raises E_DISTRIBUTED_CLEANUP, adding each underlying
failure as a note and chaining the first. Therefore this public worker reported
an otherwise-completing operation refused during final resource cleanup.

worker.py lines226-227 serializes ONLY type(exc).__name__ + str(exc). It omits
the exception cause, traceback, notes, failing resource, errno/winerror and lane.
worker_client.py then wraps that generic error. The public test log cannot
recover the missing low-level exception from that string alone. This is a
verified diagnostic-loss boundary, not proof of the original Windows cause.

Read-only inspection also shows _Session.stop kills/waits only its direct Popen
process, whereas WorkerClient._process has a Windows taskkill-tree fallback.
That is a lifecycle asymmetry worth falsifying, NOT proof that an orphan caused
this run. File sharing, process/writer timing and path/temporary-resource issues
remain hypotheses until the actual exception/resource is captured. Do not ship
a sleep/retry, suppress cleanup failure or change termination from speculation.

The agent's recursive file discovery encountered Access Denied inside many new
normal-user temp directories. That is a DIFFERENT observation from the normal
host's cleanup failure. It does not prove deleted data, broken host permissions
or the exact cleanup cause. No permission changes were attempted. Subsequent
inspection used known logs and manifests without recursing those directories.
An initial read used an incorrect image-successor/source sibling; corrected to
the actual shared root/source. No file was changed by either inspection.

## Preservation and retained result review

Host main receipt preservation=true, no preservation_failure. Parent freshly
verified all567 clean source hashes, three original protected inventories and
all9 files of the earlier failed identity-only attempt. The current sealed
contract/helper/launcher and v1 helpers remain unchanged. This fresh parent
comparison does not claim every new normal-user temp directory was readable.

Private Gate1-Image-Host-Result-Review-20261021.json records exact case bindings,
counts, snapshot/source checks and limits. SHA256
1950a968075c6146ce36ec9104993d8adf2dd71c7f10c661772b59d7fd82ae9c.
It is a self-reported parent observation, not authenticated producer proof.

## Next recommendation — focused evidence, not another full Gate1 run

No-build preserves safe BLOCKED state but cannot close Gate1. Recommended:
prepare a separately reviewed focused diagnostic of the ONE failing public
distributed path, retaining full exception chains/notes, resource names and
owned process/writer/handle states. Instrument only new diagnostic artifacts;
keep current source/helper/seals/attempt read-only. Ensure observation does not
turn cleanup into a no-op or silently add retries/delays. Observe every original
refusal instead of changing exit codes or skipping this required subcase.

First seek the actual Windows exception/affected resource with a bounded normal-
account probe using the existing runtime. Do not run the full191/217 ladder or
24 arms again merely to rediscover the same generic error. The one approved
image-successor run has been used; no automatic/fresh runtime retry authorized.
After evidence identifies the cause, propose the smallest repair plus a failing
regression and bounded review. Only then qualify the corrected integrated path
and finish the remaining Gate1 cases/comparison/preservation/result review.

Silently excluding distributed-local would change the included release scope;
that is not an authorized way to make this gate green. Broad lifecycle rewrite
or native Beads work is unnecessary for this diagnosis. No API key/model install
is needed. Exact low-level cause remains the weak link; no fix is claimed.

PENDING: a reviewed focused diagnostic and separate authority for its bounded
normal-host execution. No new runnable command, source correction or retry has
been issued. Final package/extraction/exact CI/install remain later gates.
