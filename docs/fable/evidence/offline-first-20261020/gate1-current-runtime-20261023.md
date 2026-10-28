# G1-C2 runtime continuation — partial; distributed cleanup blocker

## New read-only lead and proposed repair description — 2026-10-23

After user requested SOLVE THAT ERROR with Fable Method/Brainstorming, the
parent inspected already retained successful extended-timing evidence without
rerunning it. Vector sidecars demonstrate separate launcher/interpreter PIDs:
44836->47924 and27764->8088. Current _Session.stop still waits only on the
launcher handle. Git diff b71b75b..a38297d for distributed_retrieval.py confirms
the only intervening change is default30->120, not shutdown behavior.

Four raw sidecars, relative to
`.github/run-artifacts/extended-worker-timing-20261023/Attempt/vector-distributed-local/events/`:

- 43060-026.json,372bytes, SHAcb1744ac397627dba5a3e124cee5894adbb2a95cee46a450daaa898e7a73abbb:
 coordinator43060 records Popen child44836.
- 43060-030.json,372bytes, SHAd32064aa3c8bfad737758c9a8aa679ece588b96e800656155d950d409d3c3643:
 coordinator43060 records Popen child27764.
- 47924-000.json,293bytes, SHA920a6a8014c4874f67f39fba4d9a83c5557037219b56f5b2c370f7c28643c981:
 distributed-worker-entry47924 records parent44836.
- 8088-000.json,292bytes, SHAde66d974367f8a1b22ccec79466f5c20606d6f5fefef4647fe6d62df7113c088:
 distributed-worker-entry8088 records parent27764.

This demonstrates a real-interpreter exit verification gap. It is NOT proof
that these workers remained alive indefinitely or held the C2failed file.
CPython main launcher source also uses child-job termination on launcher
death, so an asynchronous termination/cleanup race is a hypothesis; permanent
orphanhood must not be asserted. The selected3.12binary is not authenticated
against CPython main. Microsoft Job Objects docs explain group ownership but
do not prove this failed run's holder. Source links and exact proposed scope
are recorded in the existing design's "C2 cleanup repair description" section.

Description proposes failure-first launcher/descendant handle observation,
bounded cleanup-cause capture with existing formatter, then only a cause-
supported shutdown-order repair and reviewed fresh selected-runtime comparison.
No new code/tests/workload or production change has been built in this planning
turn. Brainstorming's full-description approval gate applies before implementation.

## ACTUAL normal-account result — 2026-10-23

The reviewed C2 command was run once and consumed. Its stopping behavior is
correct; do not rerun it or remove its workload claim. No new workload was run
by the parent after receiving the failed result.

Receipt `C:/Users/sakth/Documents/Codex/gate1-current-a38297d-20261023-c2/Receipt.json`,
11165bytes, SHA2564424beb7298567755735500144eae66b6a43ea7192446c554ea5f559a14b0c07.
Parent directly verified that hash, all10child-command stream size/hash records,
exact case IDs/order/counts in all4executed groups, all4unittest log hashes,
and a fresh C1/source/helper/protected-file readback. Receipt preservation=true
and the fresh pinned preservation check passes. This is not full scratch/archive
or worker-handle proof. The source C1copy and consumed C2inputs remain unchanged.

| Group | Run | PASS | FAIL | ERROR | SKIP |
| --- | ---: | ---: | ---: | ---: | ---: |
| MI containment | 3 | 3 | 0 | 0 | 0 |
| MI paths | 2 | 2 | 0 | 0 | 0 |
| MI offline profile | 16 | 16 | 0 | 0 | 0 |
| MI knowledge | 198 | 184 | 1 | 0 | 13 |

All13skips are the known platform/optional-runtime cases listed in the retained
knowledge Receipt. No excluded, expected-failure or incomplete cases occurred.
Total219run,205PASS,1FAIL,13SKIP. CM offline group and24acceptance comparisons
were not executed. C3 remains unexecuted; no Gate1/release/install qualification.

### The actual failure boundary

`test_knowledge_completion.RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay`
failed only its vector/distributed-local subtest, at line51 of the immutable
C1test: the INITIAL public knowledge-retrieve invocation returned exit2.
It did not reach that vector pack's reopen/replay steps. Community/global/DRIFT
subtests report no failure/error under the same sequential method and default120.
This is not a claim that every advanced case is qualified.

The retained public reply is:

```text
ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP
```

`suite-3/Command.json`: child exit1, executionEXITED, timed_out=false,
capture_complete=true, capture_errors=[], output_limit_exceeded=false,
tree_contained=true. No outer watchdog fired. Knowledge198tests took520.096s;
that is total suite time, NOT vector search time or one worker's time.
`tests-3/unittest.log` SHA1df62ff1d2debaa665fc0e2a9303ba2a3fb6cdeb3985eb538989850aac0e596f.

Code trace: DistributedClient finally stops every immediate session, then
closes streams/temporary directories. If cleanup raises after otherwise
successful work it raises E_DISTRIBUTED_CLEANUP with the original cleanup
exceptions chained/noted. `worker.py:main` serializes only type(exc)+str(exc),
and `worker_client._process` propagates only that string. Therefore the saved
public record cannot reveal the original cleanup exception/path/holder.
This is a confirmed observability limit, NOT a confirmed handle-owner cause.

Do NOT infer current WinError32, AccessDenied, a Python descendant, antivirus,
specific file, timeout exhaustion or required timeout change from this wrapper.
Those remain hypotheses. Historical WinError32 is a separate retained result.
Parent attempting supplementary fixture discovery hit AccessDenied on normal-
account retained scratch subdirectories; no filenames/content there are claimed
verified. No ACL change or copy/readback workaround was attempted. This later
agent access limit did not cause the normal-account test failure already saved.

### Next bounded work, not an automatic retry

No-build option: keep the honest negative result; Gate1 remains blocked.
Smallest recommended investigation: reuse the existing diagnostic error-chain
formatter and lifetime observer in a separately sealed fresh diagnostic copy,
preserving original ordered context, default120, assertions and stop conditions.
Capture the actual cleanup exception, notes, file identity and worker/descendant
lifetime before making a cause-specific repair. Do not rebuild the accounting
repair or repeat a full224case run merely to look for another outcome.
Stronger alternative: process-tree ownership redesign or an explicitly narrower
Windows single-worker release; neither is justified as an unapproved silent fix.
Weak link is reproducibility: a successful diagnostic without the failure does
not prove repair. If the original cause is not captured, report inconclusive.

No source fix, new launcher or new diagnostic workload has been made/run by
this result-inspection turn. Only Fable continuity records were updated. No
commit/push, installation, permission change or deletion occurred.

## Historical preparation/review evidence — before the consumed run

## Authority and current result

Same approved sequential C1–C3 continuation: user said "complete this 1 by 1
at a time" and then "CONTINUE". No new product design, production edit,
install, deletion, permission/trust change, commit or push is authorized here.
C1 is closed within its source/environment scope; C2 numerical execution and
C3 worker-handle/cleanup review are not done. No whole-skill claim.

C1 Receipt SHA256f0a8b97b49122ad2dc86c5b7adeb4c38e84d97cc774afa80e8debba0d8e30b14;
Prepared98bfd5870d3d4032cd250dc268a99a3a791b61787081a539f9f4eb2f3818a75d.
627committed files,344protected source/cache/release files,53dependency metadata
versions, Python3.12.10 and both actual120defaults were observed on the normal
account. Independent observation review accepted C1 WITH CAVEATS; that is not
numerical retrieval, producer authentication or real cleanup proof.

## C2 exact scope

New helper `.github/scripts/gate1_current_runtime.py`, new launcher
`.github/scripts/Run-Gate1-Current-Runtime.ps1`, matching11-case controller suite.
C1 root and source stay unchanged. No old command is reused. Exclusive new
normal-account output is
`C:/Users/sakth/Documents/Codex/gate1-current-a38297d-20261023-c2`.

Input-only controller discovery observed five exact ID lists: MI containment3,
MI paths2, MI release profile16, MI knowledge198, CM release profile5, total224.
Runtime requires exact order, complete per-case outcomes and aggregate agreement;
no failure/error/exclusion/xfail/interruption is accepted. Only original C1
known optional parser/model/POSIX skips are permitted. Its map stores reason
markers, not always full strings (e.g.POSIX-only), so the matching semantics
are deliberately retained rather than falsely rejecting a legitimate longer
source-pinned reason. Every actual skip must still appear in both records.

The new acceptance copy changes only3exact byte spans: omit initial explicit60,
omit replay explicit60, and bind fixtures to C1's unchanged directory. Both
directions are checked against original SHA297239367be35ff0f920a4c2dbaeb2e8af0333a5c1e236f8e009c7c577911fcd.
The producer's real `__file__` remains the adapted file: fresh subprocess
replay and frozen-oracle generator binding use it; the result validator loads
that exact adapted producer. All original assertions/refusals remain intact.

Acceptance must contain24unique case/mode/mandatory arms, each replay verified,
and the11original checks including save, fresh recall, unchanged resume,
changed-source/access/budget/tamper refusals. Save/resume uses the original
mandatory LITERAL pack, not a newly added ranked-pack save/resume experiment.
Controller3.14, numerical worker existing selected3.12; default worker120,
original outer watchdogs1200/suite,2400acceptance,180/acceptance child unchanged.
No hidden learned model/API/native database is selected.

## RED / GREEN and retained broader evidence

Original7failure-first cases and their prior red/green receipts remain retained.
Added4cases: failed-capture retention, setup failure receipt, wrong-account/
existing-output refusal, and partial/duplicate/unreplayed-arm rejection.
Fresh RED11run:2failures,0errors/skips; capture discarded the failed command
before caller retention, and setup error escaped the receipt boundary.
Fix: return/retain capture record before checking exit/capture or parsing;
put setup within the receipt handler; exceptions cannot keep success status.
GREEN11run:11PASS,0failures/errors/skips/exclusions/xfails.

Retained local controls (not unchanged CI):

- `c2-controls-20261023/red-01/Receipt.json`, logSHA
  9bece40bcbc369d3a04ed3a4d72610f62394631a8762306884bc896a51ac2f27.
- `c2-controls-20261023/green-01/Receipt.json`, logSHA
  f1d2cd586dd2ffb9a61da81026ab8d568049c9a0ed82773a00ca40a234f435c6.
- `c2-controls-20261023/controller-01/Receipt.json`:343run,0failures,
  16error records,0skips/exclusions/xfails; logSHA
  e41308f1b2dfbf3342c5cfe71de066eafd9c8233454d89558061f285d61e9610.
- Final focused rerun (only synthetic reply stdout suppressed in test, no
  helper/seal change): `.github/run-artifacts/gate1-current-20261023/C2/focused-final/Receipt.json`,
  11PASS/0failures/errors/skips/exclusions/xfails; logSHA
  b55992404ce4afd2e998ebc99e126fe8233dd47dc92d2e2b0ac526fbaadef3d1.

This broader result is NOT green.10errors are WinError5 creating new scratch
directories in old `test_extended_timing_log.ExtendedTimingLogContracts`:
`test_append_refuses_replaced_log_without_touching_the_replacement`,
`test_configure_is_idempotent_only_for_same_context_and_never_overwrites_existing_log`,
`test_invalid_completion_status_is_not_a_valid_timing_row`,
`test_lookup_times_the_original_validator_without_claiming_global_search`,
`test_read_and_exact_digest_association_are_per_byte_object_not_same_size_guess`,
`test_source_unit_reopen_decorator_derives_path_and_unit_id`,
`test_span_propagates_original_exception_and_marks_it`,
`test_span_records_exact_start_end_without_stdout_or_retained_handle`,
`test_table_retains_physical_bytes_digest_and_exception_type`,
`test_text_read_records_bytes_but_unwatched_read_is_not_noisily_logged`.
No permissions were changed to make them pass.

Other6records are the known historical pins:1E_EXT_GIT_SOURCE_DRIFT in
`test_extended_worker_timing.ExtendedTimingTests.test_real_copied_public_index_logs_each_declared_source_without_worker`;
5E_DIAG_SOURCE_PIN in `test_worker_timing_lifetime_diagnostic`:
`ReviewBlockerRegressions.test_transformed_two_session_lifecycle_is_transparent_and_within_quota`,
`WorkerDiagnosticControllerContracts.test_live_overlay_uses_exact_original_test_and_worker_source`,
`WorkerObserverContracts.test_actual_process_success_and_error_survive_overlay`,
and `WorkerObserverContracts.test_overlay_removes_only_observation_nodes_to_original_ast`
for worker_client.py and distributed_retrieval.py. No old guard was relaxed.

The controls root is retained, including scratch outputs. Raw control contents
are local evidence, not an instruction to stage/publish the entire directory.
Initial creation under Documents/Codex was denied even after file-only sandbox
grants; the existing approved Fable evidence area was used instead. Adding new
files required narrowly scoped creation permission on the existing script/C2
parent directories; no Windows ACL or ownership was changed.

## Seals and host handoff

Helper SHA42ee6ee502ac9b4dc742fa6c9a0a70d56fc04600f1d24800f65ace32db56989f.
Contract `.github/run-artifacts/gate1-current-20261023/C2/C2-Inputs.json`,154977bytes,
SHA6cb6cb39d6b3e2a702b0e2b63cba6a97b44f250fb4c396463bc62f5cd2113c15.
Launcher SHA69544835b9bf37acfa88d3900db332473141c90b73e01134cb1dcdc1e8d1b14d.

Parent --verify-inputs exit0; launcher VerifyOnly actually executed and passed;
PowerShell parser0errors. Actual direct coordinator refused the sandbox SID
before any C2 output or preflight-failure marker. C2 normal-account attempt is
UNUSED. Do not remove markers or run any old command; a failure must stop.
Fresh native independent exact-pin rereview accepts the one normal-account
C2 handoff WITH CAVEATS. It independently checked all5discovery records,
stream hashes, complete contained captures, exact IDs/order/counts, noFailedTest,
empty stderr, ordinary single-link inputs, exact helper/contract/launcher pins,
the successful C1 bindings, the reversible adapter and its own generator binding.
Reviewer independently ran input verification and launcher VerifyOnly, both
exit0; parser0errors. No selected runtime or old command was run by reviewer.
This is code/input/handoff review, not review of a C2 runtime result.

Supplementary discovery streams are retained and were hash-verified by reviewer;
the runtime input contract principally binds the discovered ID lists. Final
C2/C3 review must retain/read the supplemental records too. No producer
authentication is claimed by matching hashes.

INTENT: C2 exercises the current corrected source using the existing acceptance
oracles and default120 on both initial/replay, retaining failures honestly;
it does not modify production behavior or convert C1/inputs into a Gate1 pass.

TWINS: searched C2 capture call sites; all four call boundaries (discovery,
preclaim, suite, acceptance) now validate after retaining the returned record.
Historical capture implementations are unchanged; C1 already has its own
retention boundary. C3 real handle/cleanup observation remains separate.

All evidence is self-reported/unauthenticated. Source preservation means
complete hash comparisons of the specified627clean/344protected files plus
C1's full result tree and pinned histories, not authenticated producer or
archive-wide preservation. No C2 numerical result exists yet. Gate1/release/
installed flags remain false. No commit/push was performed.
