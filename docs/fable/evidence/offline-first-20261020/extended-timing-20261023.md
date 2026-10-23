# Extended-time measurement, not a worker repair or Gate1 pass

## Latest observation - normal-account run completed (2026-10-23)

The one approved run is consumed and retained. DO NOT run its launcher again,
remove markers, edit frozen helpers/source, or replace its Prepared baseline.
The earlier prepare-only/runtime-pending text below is retained history.

Actual Receipt.json SHA256
b4bf001140ad6d4c486f4674bd7b82cf3c0ea23879e1c7bf994000c11822f569.
Timings.json SHA256 036ad2857df4c64c61a5e80cad089c16d5e3084fc71211233cfcbf33c7a8e88d.
Timings.md SHA256 9d9328ecae25e48701cec47c0c465137d54effab8f76d9c992b18e273686d267.
All are under the private root's Attempt directory. Whole observed wall time
81.87439320003614seconds includes runtime probe/fixture/workload, not a summed
total of nested or parallel phase spans.

| Operation | Outer command seconds | Worker-client seconds | Result |
| --- | ---: | ---: | --- |
| Index build | 2.790943 | N/A | PASS |
| Community initial | 43.768587 | 41.906 | PASS |
| Community fresh-process replay | 6.189088 | 4.593 | PASS |
| Vector/two-worker initial | 10.331388 | 8.563 | PASS |
| Vector/two-worker fresh-process replay | 12.547688 | 11.078 | PASS |

First community dependency phases: Semantica27.453seconds; numerical imports
12.234seconds inside vectors12.313seconds. Do NOT add vectors+numerical imports:
they overlap. Community hierarchy/reports/strategy phases recorded0.000seconds;
this is recorded timer granularity, not proof of literally zero cost. First
fixture source reads were31/32/16milliseconds for54/25/133byte files, respectively;
these instrumented spans include recorder overhead, not pure disk I/O benchmarks.
This212byte coding fixture is not a large-repository performance qualification.

All5command exit codes0; no timeout, output limit, capture error or containment
failure. All10stream size/hash bindings and2pack hashes independently verified.
Each pack contains required worker/U000001 and worker/U000002,2units from ONE
source, not2distinct source files. Protected265input/249copy bindings still match;
static input verification passed after execution. No historical archive-wide
AFTER claim is made. No observer error markers; all raw phase START/END pairs
closed for48/48/141/141events across the4search/replay operations.

### Important reviewer qualification

Timings has417rows:404RETURNED,5EXITED,8UNFINISHED. The8UNFINISHED rows are DERIVED
spawn-to-module-entry joins, NOT unfinished search or replay operations. Windows
venv launchers have different PIDs from their interpreter children; the frozen
renderer joined only direct PIDs. Raw parent/creation identities show the chain
43604client ->36616launcher ->47616worker, and analogous chains for all8spawns.
Internal worker phases remain usable. The original table's direct startup-gap
values must remain UNKNOWN; do not silently overwrite them or call the receipt's
timing_observation_complete=true a proof of complete process-start telemetry.
Final native read-only result review: SHIP AS BOUNDED DIAGNOSTIC EVIDENCE WITH
THIS CAVEAT. This is not authenticated producer evidence or an independent
repeat experiment. Parent separately checked the primary receipt/raw streams.

Conclusion: this observed initial community worker needed more than30seconds,
predominantly in dependency-loading phases. The precise reason imports were
slow (OS caches, DLL/file loading, security scanning or another cause) is not
isolated. Faster fresh replay is observed, not proof of a particular cache.
This explains the present comparable run, not the exact uninstrumented historical
timeout retrospectively. Vector WinError32 was NOT REPRODUCED; successful
wait/close/cleanup spans in this run do not prove an intermittent defect repaired.

Current completion: timing measurement executed and reviewed WITH CAVEATS.
H1 BEFORE stays closed; old W/fresh archive AFTER still unrun. Permanent worker
repair, original30second Gate1 qualification, full five-group/24-arm integration,
release/installation remain incomplete. No rerun or new timing build is needed
to obtain the results already saved. Next choose the smallest justified runtime
budget/cold-start handling and Gate1 continuation through the existing plan;
no speculative production architecture change, timeout change, commit or push
is authorized by this result readback alone.

INTENT: user requested measuring the two failing paths beyond30seconds, with
per-file/action records and a timing table. Existing ET section in the approved
offline-first plan governs this work; this is not another memory-engine build.

## Exact scope and implementation

Source checkpoint b71b75b77b8e9432eb9d51c0828825e3e344ce12, existing selected
Python3.12 environment only. New diagnostic helpers/tests are under .github;
live memory-integrity and claude-mon package bytes are unchanged. A new package
copy receives hash-checked phase observation and per-file read/hash/path checks.
Historical fixture copies are DATA only and are never executed or imported.

Both community/single and vector/distributed-local initial retrieval and fresh
process replay select the existing supported120second WorkerClient setting.
Production default30/API maximum120 stay fixed. Outer captured child180seconds,
whole workload900seconds; no phase restarts the worker budget. This is NOT an
unlimited run. If120seconds expires, natural completion time remains unknown.

Records retain UTC, monotonic duration, PID/thread, path, physical bytes where
known, hashes associated only with the exact bytes object read, and original
errors. Unfinished spans remain UNKNOWN. Process-creation and spawn-to-module
entry are separately labelled; they include observer overhead/possible overlap,
not a claim of pure interpreter startup time. Nested/parallel times are NOT added
to obtain wall time. Path validation is not a whole-disk filename search.

Preservation scope: exact Git package inputs, existing six source cache files,
diagnostic helpers/controller/runtime bindings, completed H1 BEFORE bundle and
publication receipt. Not a new whole-archive BEFORE/AFTER claim. No completed H1
copy stage, old W/N3/Gate1 command, baseline or consumed attempt is restarted.

## Observed verification (controller, not selected numerical runtime)

All paths below are relative to .github/run-artifacts/extended-timing-tests-20261023.

| Check | Actual result | Retained receipt |
| --- | --- | --- |
| First missing driver/logger contracts | RED retained | driver-red-1; logger agent run |
| Real copied public index and3source timing | PASS | driver-integration-green-1/Receipt.json |
| Original logger parent checks | 8/8 PASS | logger-parent-green/Receipt.json |
| Report safety corrections | 5 expected failures,0errors; then21/21 PASS | report-correction-red; report-correction-green |
| Spawn interval conversion | 1 expected failure; then22/22 PASS | startup-table-red; startup-table-green |
| Real observer parser120accept/30refusal plus all focused controls | 23/23 PASS,0skips/errors/exclusions | parser-parent-green/Receipt.json |
| Relevant whole controller suite | 309/309 PASS,0skips/errors/exclusions/expected failures | controller-current-green/Receipt.json |

Focused log SHA256 cab813b1e304a14456fc3f8c81da1ccc18765ea34dd8eecc7e3575564fb12fa4.
Broader log elapsed54.738seconds is TEST-SUITE time, NOT community-search time.
Synthetic negative fixtures print intentional failure packets; the runner's
final receipt and unittest log determine the suite result.

### Final corrections and frozen handoff (supersedes earlier counts)

Native review initially returned FIX-FIRST for three demonstrated gaps:
fixture creation not timed; thread/base-import readiness omitted from the table;
and the historical cache set dynamically baselined rather than exactly asserted.
review-correction-red/Receipt.json records exactly3 failures and0errors.
All were corrected inside the diagnostic only:

- Six fixture files now each retain path/bytes/timing plus total creation time.
  The overall clock includes the runtime probe and fixture creation.
- Thread IDs, module-entry-to-base-imports-complete, hashes and error types
  survive into the table. This interval does not claim all library startup.
- Exactly six approved cache names AND their known hashes are mandatory at
  preparation and final readback. Missing/extra cache files are not rebaselined.
- Failed cases have explicit all_cases_passed=false and a distinct retained-fail
  status, separate from timing_observation_complete. No diagnostic pass is a fix.

Final focused26/26 PASS: review-correction-green/Receipt.json; log SHA256
695d4d797d686993636635c829b7b39d2c1be8b1b705dddbec144486b1dcd450.
Final broader312/312 PASS: controller-reviewed-corrections/Receipt.json; log SHA256
57117de4f354cfb821814baf4d97d9a6a4b6df443874502cbfc016b967162aa6.
Both have0failures/errors/skips/exclusions/expected failures. Broader45.776seconds
is controller test-suite elapsed time, NOT retrieval completion time.

Same native reviewer rechecked the actual correction bytes: SHIP for preparation,
then independently reviewed the frozen inputs/launcher: SHIP for ONE NORMAL-ACCOUNT
EXTENDED-TIMING RUN ONLY. Earlier credit-unavailable/FIX-FIRST states are retained
history, not the final review status. No successful worker or root cause inferred.

Private root: .github/run-artifacts/extended-worker-timing-20261023.
Prepared.json SHA256
93a11df43f96beae16394b17d0d304cb84eb1e21eed66fac179b1c362545f0a6.
Run-Extended-Timing.ps1 SHA256
65f44d4d215694083d262a1e807c8c9eceb2ac790d0ec0c45fcf21549f23d29c.
Driver SHA256 bc9658d6cb012464b26ec71119c85d76d1a0dccc15095cd101727f29610ee2ea.
265protected input records,249isolated copied package files. PowerShell parser,
launcher VerifyOnly and driver sealed-input verify passed without a worker.
Attempt and Runtime-Preflight are absent at final handoff. After a host run,
read Attempt/Receipt.json and Attempt/Timings.md, not the test-suite durations.

Corrections verified: table no longer drops byte/hash/error fields; invalid
completion statuses and empty numerical-worker traces are refused; appending
refuses a replaced log without touching it. Every event closes its file handle.

## Current observation and honest limits

The agent's existing selected WindowsApps-base Python probe failed before any
numerical work: base Python is unavailable in this execution account. Controller
3.14 tests do not establish selected3.12 performance or repair either failure.
No real community or vector search/replay timing is available yet. The final
same-seat native review cleared the corrected frozen handoff as described above;
selected-runtime measurement itself is still pending normal-account execution.

A: previous H1 BEFORE copy/readback workaround remains closed.
B: this extended timing workload is NOT EXECUTED; old W/fresh AFTER also unrun.
C: historical community timeout and file-holder root causes remain UNKNOWN.
D: Gate1/release/installed qualification remain INCOMPLETE and disabled.

No install/download, old-data deletion, permission/trust change, external AI,
model/native backend, original-project Git write, commit/push or release action.
Only existing worker/new test-owned temporary housekeeping is within approval.

## Resume

Use only the NEW externally hash-checked Run-Extended-Timing.ps1 once from normal
non-administrator PowerShell, VerifyOnly then run under the existing approval.
It verifies all sealed inputs before its Python identity probe and consumes the
new workload attempt only after that probe passes. On any failure, STOP, retain
every file/marker and inspect the receipt/stdout/stderr; no automatic rerun. Do
not edit the frozen driver or source after preparation. Any necessary successor
must preserve these inputs and attempt, not overwrite them. No commit/push yet.
