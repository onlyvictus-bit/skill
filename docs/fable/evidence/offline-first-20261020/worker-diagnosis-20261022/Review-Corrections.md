# W1 fresh review and parent correction pass — 2026-10-22

Scope: W1-W3 isolated DIAGNOSIS ONLY. No production worker correction or Gate1
qualification. Accounting A1-A3 remains closed, unchanged and uncommitted.
HEAD remains923de16c91a9ef4381e7ac975e3a3780f42a4bf5. Nothing committed/pushed.

## Independent initial verdict: FIX-FIRST

Configured read-only seat worker_diagnostic_final_review checked the exact four
hashes in Review-Packet.md, old accounting pins and retained21/206 receipts.
The green receipts are genuine but did not exercise the critical mechanisms.
No selected runtime, normal Prepare/Run or Restart Manager API was executed.

Critical findings and accepted corrections:

1. Generic close instrumentation called stream.closed on a _Session, preventing
   its original close. RED actually reproduced this AttributeError. Overlay now
   distinguishes stream closes from session lifecycle methods; safe snapshots
   cannot replace the original work return/exception. Session method decorators
   retain lifecycle observation without intercepting session.close as a stream.
2.128events/16KiB could not hold the distributed coordinator's instrumentation.
   Polling Event.wait and writer join are no longer instrumented; function entry
   and exit are two records, not three repeated snapshots. A real transformed
   DistributedClient with two stdlib stub subprocesses, fit/initialize/seed/
   neighbor protocol, stop-all then close-all, real pipes/files and actual NEW
   directory removal passed. Saved Lifecycle-Volume.json:73events,30037bytes,
   two child processes and two actual cleanup calls. This is not Semantica proof.
3. Balanced fragments could become OBSERVED without required roles/processes.
   A fragment now has a distinct non-complete label. Controller passes exact
   filenames and outer capture root PID into strict role/phase, immutable PID+
   creation, parent/spawn closure and monotonic-clock validation. Missing whole
   phases/processes, foreign PID, generation change, wrong/duplicate filename,
   wrong role or clock regression stay INCOMPLETE. Metadata is self-reported,
   never producer authentication. Actual killed work's open phase is incomplete.
4. Old companion handshake could create bytecode in historical source because
   main -B is not inherited. Historical readback now has a scoped controller
   guard for PYTHONDONTWRITEBYTECODE=1/PYTHONNOUSERSITE=1 and parent bytecode
   suppression; env restored afterward. Real engine_client.handshake on a NEW
   sealed scratch companion imports a module without changing any file/directory
   inventory or mtime. Historical handshake is not skipped or replaced.

Important: exact seal/Prepared key sets and required file-role set now reject
empty/missing/extra/wrong-path roles and wrong Prepared state. External Prepared
hash remains required before Run. The launcher checks the same fixed file set.
Launcher byte identity is a normalized template in the seal; the user's external
launcher hash binds the actual literal seal digest. This avoids a circular hash,
not a waiver for arbitrary launcher edits. Current launcher remains NOT FROZEN.

## Explicit diagnostic design rulings

- Coordinator limit is now512events/64KiB per PID. Ordinary child limit stays
 128events/16KiB. Total accepted telemetry stays1MiB, max64PIDs, max4KiB/event.
 The measured tiny full coordinator already needs30037bytes, so retaining16KiB
 would guarantee incomplete observation. This is a bounded diagnostic capacity
 amendment, not a product budget/deadline change or evidence of search speed.
- Shard idle blocking readline is not an unfinished work phase. Observe each
 received request through its original error/serialization/flush path; idle
 lifetime is correlated with parent stop/wait/close, not claimed as a completed
 shard main function. Unfinished requests remain INCOMPLETE.
- No architecture substitution: controller remains selected
 Python3.14 and the future workload remains the SAME pinned Python3.12 image.
 All production30/90/600second deadlines and original payloads remain unchanged.
- No second governor, workspace cleanup, global setup or automatic Git action.

## Retained verification

All paths are relative to .github/run-artifacts/offline-first-20261020/:

- w1-review-red-01:37tests,4failures+1error;12 inherited observer contracts were
  accidentally counted twice. Duplicate inheritance removed, not a dropped
  unique contract. Failure includes the real session-close AttributeError.
- w1-review-green-01:26unique tests pass, zero errors/skips/expected failures;
  log fd7d8b6c8f34518cea5569c14b11c5fa30b5f319a8b3108429a2bf47d603f2e0.
- w1-review-green-02:26/26 after full DistributedClient fixture, zero omissions;
  log0979eac4a445974a9aa4d40dd82d99eb7ae523414e864184cd049907031c2d47.
- w1-review-policy-01:211/211 complete relevant controller tests, zero errors,
  skips/exclusions/expected failures/interruption. Parent will independently
  recheck receipt/log hash before final evidence freeze.

Initial review findings retained here; same configured seat is verifying this
one parent correction pass. That delta review is pending, not a SHIP verdict.
W2 seal has not yet been created.

Final narrow falsifiers: w1-review-red-02 proved a complete unclaimed extra
worker could still pass forward-only spawn closure; inverse spawn closure
corrected it. Omitted-whole-phase test now resequences its remaining filenames,
so refusal proves required phase closure rather than only a sequence gap.
w1-review-red-03 proved a snapshot failure lost its persistent marker. Error
marker now reuses only the established exact PID/environment root, without
recursive context lookup; parser also rejects nested observation_error.
No native workload was used or retried in these controller regressions.

Final exact-code focused w1-final-v2:27/27,0errors/skips/omissions; log
ded81e7223b826fd6e18925ef72816e23c61941b207417c92fba1641eedaaf62;
receipt0ecfe3fd65a3088caf62933a3e443c2452a7112d4a3d5124b8890586e6a76e71.
Full controller w1-policy-final-v2:212/212,0errors/skips/exclusions/xfails/
interruption; logd5c59e47ea606abe525ac9894864958a52737aecea29798243dd9896f5c0ec96;
receiptd0ec60271049be4f5989310e11f071b6d342cc11a8a6934948c524e5fbcfc5d9.
These final paths are consumed evidence, never future rerun commands.

## Remaining exact boundary

No normal-account history readback, planted/released holder control, selected
retrieval runtime or either numerical workload arm has run. Agent SID mismatch
and WinError5 reading an old retained worker folder were observed read-only.
Do not skip them, elevate, change ACLs or reuse any consumed command. No file
from prior source/cache/evidence/package/install was deleted or overwritten.
Root causes remain UNKNOWN; phase timing plus holder correlation is the next
actual observation, not a reason to change architecture, deadlines or chunking.

## Final same-seat disposition and W2 static freeze

Configured independent reviewer returned SHIP for corrected W1 and the W2
PREPARE-ONLY seal freeze. No remaining Critical/Important/Minor implementation
defect identified. Parent separately ran all final checks and static seal
verification; no completion claim rests only on the reviewer's message.
Reviewer declined all normal/history/native/numerical/cause/repair judgments.

Input-Seal.json created under the NEW worker-diagnosis private root,27exact
roles; SHA2d7cb8c9e7d37d60e613f987bb8b9d7746cfd2ef178b1fbd7bbb2778c8425f1f.
Only PS sentinel replaced after review; launcher actual SHA
96d82487ab04a764cc530f8092db44e15ebde2eb04a946b2b5fc8a23f4d26cf3.
Parent verify_own_seal exit0, normalized template+all27records matched;
PowerShell AST parser0errors. New source aliases and Prepared still absent.
No launcher/normal Prepare/Run was executed. HANDOFF.md contains only the new
Prepare-only command. Agent cannot substitute for the required normal account.
Await actual Prepared bytes, independently inspect/seal them, then issue Run
under existing W1-W3 approval. Never infer authorization or observed runtime
from SHIP code review. No old sealed command/input/marker changed.

## Evidence-dependent alternatives, NOT implemented fixes

If actual timing concentrates in startup/imports, first consider the narrowest
unneeded-import removal; process reuse is a stronger alternative requiring its
own generation/access/lifetime proof, not an automatic change. If graph work
dominates, consider bounded generation-bound precomputation. If payload size
really dominates, sequentially partition with explicit coverage and a complete
repair/merge inventory; never drop chunks to meet a deadline. The current tiny
test fixture alone is not evidence of a large-file problem. If an exact file
holder is observed, repair that identified process/handle lifetime, not ACLs or
arbitrary delays. If the holder/phase cannot be captured, retain UNKNOWN and
propose a separately reviewed scope decision rather than claim a diagnosis.
Keeping unsupported advanced modes disabled in an explicitly narrower release
is a possible product decision, not something W silently applies. No timeout
increase, architecture replacement, data truncation or hidden mode skip here.
