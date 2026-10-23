# Gate1 ordered accounting repair — closed, verified with caveats

Scope: the displayed E_ORDERED_UNIT_ACCOUNTING harness bug and its error masking
ONLY. This is not a cleanup/timeout production repair or full Gate1 qualification.
AUTH: user requested root-cause verification/fix ONLY this stage and continuation.
INTENT: retain real FAIL/ERROR results with exact subtest identities and exit code,
not erase errors to turn a failed run green. No new numerical run is needed to
verify this accounting behavior against the consumed saved evidence.

## Confirmed original cause

Actual V3 receipt8538bytes SHA
14c350e4fa63561ecf794cf1aa06e05f18d84fa779dd2d39789180d93901be28.
Unit receipt811bytes SHA555bd29f46757dc01a0795d7f78f029ca4fa81040bb7ed8752aab163cb392160.
Ordered-Outcomes28078bytes SHA4fb9bb0b46cd19ba1320ddc8d92c096870ccf9ba184c1b3b187bd0b1dc98e768.
Unittest log9247bytes SHA880296d46e835d1cf8854e7aaeebbdda85fcc5d7d3662f39ca7674f435f8431d.
All six outer streams and all nine call records agree with their saved hashes.

The method executed one parent with four subtests. Standard unittest addSubTest
stores assertion failures and non-assertion exceptions separately, with full
child IDs including parameters. The old validator incorrectly required
failures=[parent TARGET] and errors=[]. Its old synthetic fixture repeated that
assumption. This was a harness bug, not a user-command error or a successful run.

| Mode | Public call | Replay/refusal | Actual result |
|---|---|---|---|
| community/single | Internal E_WORKER_TIMEOUT | Not reached | FAIL |
| global/single | Passed | Replay passed; bad lease refused | PASS |
| drift/single | Passed | Replay passed; bad lease refused | PASS |
| vector/distributed-local | Passed | Replay E_DISTRIBUTED_CLEANUP; bad lease not reached | ERROR |

The original unit remains1test/1failed subtest/1errored subtest/exit1. Original
outer HARNESS_OR_CAPTURE_FAILED receipt is preserved, never rewritten as success.

## Narrow implementation

Only ordered driver and its focused tests changed. Exact pre-edit V3 driver,
runner and tests were copied to new private ordered-consumed-v3 first. Original
runner, retained helper, product, original tests, runtime, packages, contracts,
launchers, cache/data/evidence trees and Git HEAD were not changed by this repair.

The validator now requires the exact four expected mode identities, exact failing
child IDs, disjoint/no-duplicate arrays and canonical per-category order, correct
integer counts/exit code, no skips/exclusions/expected failure/interruption, and
FAIL/ERROR category agreement with the SHA-bound unittest log. Unknown parent or
other-child IDs, category swaps, omitted errors and malformed counts still refuse.

Real failed public timeout is retained as INTERNAL_WORKER_TIMEOUT_CAUSE_UNPROVEN
and does not prevent a later valid cleanup diagnostic from being reported. No
timeout budget, retry policy, cleanup mechanism or permission setting changed.

One reviewer Important finding: hashing a log and then independently rereading it
for parsing creates a hash/read race. The correction verifies and parses the SAME
raw byte buffer, retaining existing ordinary/single-link path checks. A real
filesystem replacement regression demonstrates rejection after the hash step.

Final driver SHA1797c2fb1753704fb675e5d37388b37a3b267f9c8debb6f77647cfafaee506ca.
Final tests SHAdb76d612c85b201cd698a10f55f1b86218b4523c1a906fe589f83c2bcf66d44e.
Unchanged runner23f67d1ddaa543071857a773a2917df86967a9d14a5d600408763f6f2a8c81b8.
Unchanged retained helper4aba6fe49641f86dcb548219f0c6efc8bbd2fbaa4e32f5be40703a1cee18453b.

## Observed tests and actual saved-result verification

- Original accounting RED28cases/5failure records/0errors a-50510749; GREEN28
  a-fd6a13fa and broader184 a-5b7de4fc retained, not overwritten.
- Plain ordinary-temp test exposed a fixture-lifetime error b-c96abf23 that the
  retention wrapper concealed. Only test indentation corrected to use its log
  inside the temp context. Plain28 b-24df676f then final plain29 b-90912bec PASS.
- Hash/parse real-file replacement RED29cases/1failure/0errors a-17e0fe4f; final
  GREEN29 a-0ce101b0 receiptSHA
  9fe091ac0b1388b4a7d2d3d1377f220b27b9256d5eddcfbf4f4c14a3fc8ad550,
  logeae7238f978af74c024e24ca15947274807f9ae4ae7b31a12b95efd3f52d8cfa.
- Final whole-controller185/185 a-2172645b receiptSHA
  38c0d19756bb3263ee325aeccdc58bdb53c7bd02db76fbd25bc42ddd2689e43d,
  loge2b85f79f1258dafbe3a135ba135209bdf561345778e4ca8410d4622d62da32f.
  Final retained suites have0errors/skips/exclusions/expectedfailures/interruption;
  raw log hashes rechecked. These are local controller tests, not unchanged CI,
  the full numerical Gate1 suite or installed-workflow proof.
- Actual read-only classification of consumed V3 now returns
  CAUSE_OBSERVED_PENDING_REVIEW with two details: internal timeout cause UNKNOWN
  and vector replay complete cleanup exception chain containing WinError32.
  No retrieval/worker was rerun; source/evidence files were not edited.
- Nineteen readable original receipt/log/stream/call records remained identical
  before/after analysis; full567file ordfix source-copy map remained
  ab96bcaaa99b495cbe8a205de0d17963bacc4214d099be36d3535325ee357721.

## Exact preservation limits; no security workaround

Agent full V3 temp inventory stopped at Access Denied for retained-temp/
mi-worker-2wgddbhy. Additional read-only fixture/pack reopening stopped at
retained-temp/tmppf9x3f29/client.py. Neither check is called passed; no inaccessible
path was skipped or permission changed. Full old-tree/pack readback remains
UNVERIFIED, separate from the19readable input hashes and567source-copy proof.

WinError32 in the ORIGINAL run is a file-sharing/lifetime failure while cleaning
tmp0tv9zmhl/output. It is not the agent's later WinError5 read-access limitation.
The original lock holder is UNKNOWN. Community internal deadline expiry is
observed, but startup/import/compute/stall cause is UNKNOWN. No antivirus/process
attribution, ACL fix, arbitrary sleep, ignored cleanup error or increased timeout
is justified by this accounting repair alone.

## Review and continuation

Same configured accounting reviewer resumed after credits. It found the Important
hash/parse gap above; parent verified RED/GREEN and sent final bytes back to the
same reviewer. Final same-seat verdict SHIP: no Critical/Important accounting
defects remain. Reviewer independently checked final29/185 receipt/log hashes,
original v3 streams/call records, exact child IDs/categories and false flags.
Parent independently reran tests/classification and verified actual bytes instead
of accepting a completion claim alone. No worker ran during review or repair.
User attachments contained only the interrupted review transcript; the actual
native reviewer subsequently completed. No second model or provider substituted.

Final review expressly declines worker/cleanup/timeout qualification, full old
fixture/pack readback, full Gate1, release, packaging, installed behavior, native
capabilities, and any new retry/evaluation/security/Git/install actions. The hash
repair makes category evidence consistent; it does not authenticate a producer.

TWINS: the parent-only [TARGET]/no-errors assumption occurs only in this ordered
accounting validator and its replaced fixture; remaining matches are explicit
negative controls or unrelated full-green requirements, not the same classifier.

V3 is CONSUMED/CLOSED. Do not run any old command, remove markers, modify old
receipts or replace baselines. Old V3 launcher hash pins intentionally no longer
match the corrected driver; do NOT rehash them to make it run. No new launcher
or evaluation attempt was created. A1..A3 now CLOSED for ACCOUNTING ONLY;
Gate1, cleanup/timeout repair, full217cases/fivegroups/24arms, matching
packages/CI and installation remain pending. No commit/push/install/security/
API/model/native action or deletion of pre-existing files/data occurred here.
