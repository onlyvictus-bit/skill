# Gate1 host result: definite loaded-image filename mismatch, not retrieval failure

Date:2026-10-21. HEAD923de16c91a9ef4381e7ac975e3a3780f42a4bf5.
Scope: read-only diagnosis of the one newly reported Gate1 host run; campaign
records only. No new runtime/worker/evaluation, code correction, install, deletion,
Git write or guard bypass. Gate1 and release remain incomplete.

## Raw evidence verified directly

Host root: C:\Users\sakth\Documents\Codex\gate1-923de16-20261021.
normal-attempt/Receipt.json:5801 bytes, SHA256
8336cf9eca7e72ec8c6b26ca9b9a54747a06b0d5e6634f83ddf1c052dfb68d6c.
Prepared.json:145897 bytes, SHA256
6911308139ce8208327829b2ee1be57e59a5982d792ec66fbfa76d004fa37d5a.
Both match the printed independently pinned values. All four command stdout/
stderr byte counts and hashes match their bound receipt entries. Runtime stdout:
1372 bytes, SHA256
f2800472a667beb5b8dcc61b9b419debf25262cdfee804546db2ea7f3aba3ad7.
Both child commands exited0 and their stderr files are empty.

The outer normal readback, clean Git copy, separate manifest and independent
Prepared seal passed. Actual selected3.12 started for the identity probe ONLY.
It reported version[3,12,10], the selected venv/alias/prefix and owned attempt cwd.
The runtime validator then rejected; no evaluation-claim.json, cleanup command,
test suite, acceptance run or retrieval arm exists. normal-attempt DOES exist:
the old one-shot launcher is closed despite the absent evaluation claim.

The host failure receipt says preservation=true. Parent freshly compared all
567 clean source files and three protected original inventories successfully.
That fresh parent comparison is not a claim to have reread every historical
agent-inaccessible stream. The host preflight/final receipt covers that scope;
any successor must require the full original-history check again, without omission.

## Definite rejecting comparison and root cause

.github/scripts/gate1_validation.py validate_runtime_observation requires
Path(observed['image_path']) == BASE. BASE pins the Store package's python.exe.
The actual OS image probe returned python3.12.exe in the SAME exact package:

C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\python3.12.exe

Both filenames were reopened read-only. Each is172912 bytes, single-linked,
not a symlink/reparse point, with SHA256
5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0.
They are DISTINCT files: samefile=false, inode1125899907075372 versus
1125899907075381 on the same volume. Identical bytes do not mean the same file,
an authenticated producer, or permission to accept any other path with that hash.

This is a harness modeling error: the approved base-file name was incorrectly
treated as the exact loaded process-image name. It is not an observed wrong
Python version, corrupt binary, user-command typo or retrieval defect.

The aggregate E_G1_RUNTIME_OBSERVATION does not list each failed predicate.
The original parent PATH hash was not separately retained as an expectation, so
this diagnosis does NOT claim all original environment comparisons are proven
equal or that this is the only possible later mismatch. The path comparison
above is independently false and alone sufficient to reject the recorded run.

## Controlled read-only falsification

Using existing controller3.14 only, imported the unchanged validator. Replayed a
copy of the retained frame, with an EXPLICIT synthetic PATH and matching digest
because the original parent PATH is not available. Current exact image pin
rejects it. Changing ONLY the expected BASE path IN MEMORY to the recorded
python3.12.exe allows that isolated replay. Restored BASE immediately.
Eleven separate substitutions remain rejected: version, venv executable, alias,
prefix, base prefix, image path, image hash, cwd, environment, PATH hash, model.
No on-disk code or runtime input was changed. This is a mechanism isolation,
NOT a completed regression fix, real host environment pass or Gate1 run.

Why prior tests/review missed this: runtime_frame constructed image_path from
the same BASE constant used by the validator; its happy-path fixture could not
reveal the Store-specific name difference. The real OS-image probe control used
controller3.14, not the selected Store3.12. Earlier bounded SHIP explicitly left
actual3.12 UNJUDGED; those code/handoff verdicts cannot override this host result.

## Proposed narrow successor (NOT built or executed)

Intent: retain strict runtime identity while distinguishing the already pinned
base file/alias from the exact observed loaded image. Do not alter any sealed
old helper, Prepared, launcher, marker or receipt to make the failure disappear.

Options: leave blocked (safe, not completion); pin the exact observed image as a
separate required role with its path/hash/file checks (recommended); accept any
same-hash executable or filename pattern (rejected: broadens identity authority).

1. Preserve the v1 helpers/seals and complete failed bundle. Build a separate
   minimal successor; reuse the freshly verified567-file source copy READ-ONLY
   rather than restarting source diagnosis or rewriting production workers.
2. Add a captured Store-image regression that fails against v1, without deriving
   its expected loaded filename from the implementation's BASE constant. Pin
   python3.12.exe separately; retain the original python.exe/venv/cfg/alias pins.
3. Refuse wrong package/path/hash, redirected/replaced files, wrong version/venv,
   cwd/user/PATH changes and model selection. Never rely on same bytes alone.
   Report named failed fields, not just one aggregate code. Retain expected safe
   environment fields and PATH digest without publishing the complete PATH.
4. Run focused and broader offline guards, check all unchanged raw artifacts,
   obtain bounded independent review and independently seal the new contract.
5. Only with separate authority for ONE fresh normal-account attempt, create a
   distinct successor output area. Existing normal-attempt stays closed. Actual
   cleanup,217 named cases,24 arms and full preservation/result review remain
   required; no release/native/installation flag follows from identity passing.

Weak link: actual selected3.12 startup/context plus later worker cleanup remains
unproven. Cheapest next runtime falsifier is the exact identity probe before
claim/cleanup; any failure stops, with all bytes retained and no automatic retry.
No dependencies, new Git trust, ACL/ownership/admin changes, deletion, package
rebuild, API/model/native backend, commit/push or installed-copy replacement.

TWINS: repository search found the exact mistaken image==BASE coupling in this
one validator and its self-derived runtime_frame test. The Win32 primitive and
controller-only test are not themselves equivalent production image contracts.

PENDING: implementation/review of the separately sealed correction and explicit
authority for a fresh normal-account attempt. No new runnable command issued.
