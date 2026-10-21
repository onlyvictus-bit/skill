# Cache observation and worker-cwd correction — source checkpoint, not release

## Authority and scope

User supplied the completed new normal-account scratch result, then requested
"after complete check commit it" and "continue". This authorizes the local
completed checkpoint commit, NOT a push, install, security change or consumed
command retry. Existing approved offline-first Tasks1–5 govern the correction.
All old caches, receipts, packages, installed skills and native experiments stay.

Basis before this checkpoint: a9ae630772b2fa299767796daae28e2f3dbd08f9 plus the
previously uncommitted diagnostic-review corrections. Those corrections are
included, not overwritten or silently omitted. See cache-cause-review-correction-
20261020.md for their independent review, RED/GREEN and identity limitations.

## Actually observed normal-account evidence

Private root: .github/run-artifacts/offline-first-20261020/.
Consumed new run: cache-cause-a9ae630-20261020-v2/normal-attempt/Receipt.json.
SHA256: a1a37f4a1128bc2d5be42bd2a11ac758e844e3a4746630e32f2add2e1141f6dc.
Prepared SHA256: 89f8796dfe0ed54b35d3401fc9194d13f62566b8a9ac83b5ff59e843be5fb4cd.
Parent read the receipt and recomputed its status from retained arm records:
RELATIVE_CACHE_WRITE_REPEATED_IN_DISTINCT_STARTUP_CWDS. Five arms, zero failure.

| Arm | Runtime/boundary | Relative cache DBs |
| --- | --- | ---: |
| startup-control | existing CPython3.14.3 | 0 |
| startup-a | selected venv3.12.10, before retrieval | 4 |
| startup-b | identical reported3.12 identity, distinct cwd | 4 |
| single | actual unchanged WorkerClient handshake | 4 |
| shard | actual unchanged _Session startup and EOF | 4 |

All four paths are under literal %SystemDrive%/ProgramData/Microsoft/Windows/Caches.
The three generation1 DB contents match the original6-file finding. cversions.2.db
is now SHA02b8b4c7d5e1eaee06f3779d63969ec50599f1baf3df0627e121cfaaf9f9d212,
not the old content. The two historical generation2 DBs did not reproduce. Never
describe this as an exact reproduction of all six original databases.

Parent rechecked all5 Arm.json/Command.json records, all10 outer stdout/stderr
hashes and all16 reported cache-file hashes. All match. Four complete cwd/temp
inventories also match. The agent cannot read the shard's retained-streams/
tmpub3zgv3c directory (Access Denied); its output-file bytes remain unavailable
for fresh agent readback. No permission change or claim of full scratch-content
verification. The externally hash-bound receipt reports its source preservation.

Before production edits, direct parent comparison confirmed MI204/CM115 protected
file hashes and all12 named historical artifacts unchanged. Every original cache
is included, not filtered from inventory. Base authentication remains explicitly
UNVERIFIED_CACHE_CAUSE_ONLY; matching in-arm identities are not exact-base proof.

## Inference and minimum correction

The selected runtime repeatedly writes relative cache paths during startup;
both owning boundaries previously inherited caller cwd. That explains how such
writes can contaminate caller source. It does not identify a precise Windows
DLL/service writer, prove which omitted variable causes the unresolved path, or
establish any retrieval-quality improvement. No SystemDrive/environment/trust/ACL
repair is inferred. Relative cwd containment is not an OS security sandbox.

INTENT: isolate relative side effects without broadening the environment filter.

- worker_client._process uses one new owned mi-worker-* directory as explicit cwd.
  Interpreter/script selections become caller-absolute without resolving venv
  symlinks. Streams close and the owned child is reaped before cwd cleanup.
- distributed_retrieval._Session reuses its existing owned directory as cwd.
  Its stop-all/stream-close/directory-cleanup ordering is unchanged.
- workflow's benchmark dispatch makes its companion/output CLI paths caller-
  absolute. Model manifest is already absolute. Generic _process does not guess
  which arbitrary arguments are paths.
- Single-worker cwd cleanup reports E_WORKER_CWD_CLEANUP on success-plus-cleanup
  failure. If the worker also fails, its original exception remains primary and
  receives a named cleanup note. Worker refusal is checked before leaving cwd.
- Diagnostic retention supports the new directory interface. The old inherited-
  cwd characterization becomes an isolation regression, with credential/offline
  environment checks retained; historical RED evidence/old source remain.

## Falsification and focused results

Real authored stdlib children exercise production Popen boundaries, writes,
distinct cwd ownership and payloads. Benchmark coverage uses actual public
dispatch, companion handshake and an authored argv/report child, NOT a model.
Cleanup failure alone is injected; child/stream behavior remains real. This is
not selected3.12 numerical execution or proof of real Windows cache cleanup.

| Stage | Private receipt folder | Result and receipt SHA256 |
| --- | --- | --- |
| Original cwd symptom RED | tests-bead3474cecb492e9e794c0feaadb557 | 2run/2fail/0error; b0629b2712d65ab0725ba3e63c569290b46bc6878d030408dbb73c623a659ab0 |
| Relative benchmark paths RED | tests-ea016f1b8d93498f906d39fd377b0dfd | 3run/1fail/0error; 62a146b4ed90660a2f49ad1b8ce361e6273f13f3bc3b0b8a304b1e1904129387 |
| Cleanup/precedence RED | tests-6699c296b35b4de8b1a44de71e49725a | 6run/3fail/0error; b248316613401044fa91da1a7b4ebaae788fbe169c7df0323eca80ae8792248a |
| Corrected focused GREEN | tests-e139b5fb61a243df9900c9333d6a52eb | 6/6; 56be4e75fc181cf1d01f784eb36830da4c463fa9638f2282aed8c657ef85a944 |
| Lifecycle regression | tests-30a15617f8d44e63a2566780eb9f6f14 | 6/6; 7f18b10b026cb4756159ed538df19e1e16e3cefd9f3726a5e328c61725c17229 |
| Final repository harness | tests-666052a897ef441fa4589062948ec10c | 81/81; 2c3156f17a66ea2b7f1a09a1cbf0f43bb88a8295136983b435958ffd0b1373db |

One intermediate benchmark control passed valid-path behavior but compared
lexical Path objects containing '..' to normalized paths. It failed for that
assertion, not incorrect report placement. The assertion now compares physical
equivalence; no production resolve/symlink policy was weakened. Its retained
receipt is tests-b73f90c87c8946389baace0eed25e941 (one fail, zero errors).

## Review and remaining verification

Independent native Fable Sol source review returned FIX_FIRST: benchmark relative
paths and cwd-cleanup error precedence. Both were reproduced and corrected as
above. On2026-10-21 the fresh native cache_cwd_final_review returned SHIP for this
bounded source correction: no remaining Important or Critical findings. It read
the actual three production changes and tests, verified retained RED/GREEN and
recurrence coverage, and did not qualify runtime/release/installation. Parent
diff review and fresh focused6/6 corroborate the source finding. No external AI
consultation or review waiver. The final broad-suite outcome is recorded below.

Reviewed source SHA256 values:

- worker_client.py:75b017e23f9334ac748d4293f1975cf3e2b1eefc039347885cd1f324d8f0b099.
- distributed_retrieval.py:f84371cf78bcd596a594e76c9f649d3e1d2790829f280049b28b5e690f85ff62.
- workflow.py:e26ea26c3fa6d27e3c99b3a1379479a79dd97e514eb4bddc4dff76c29f02896d.

The previous final broad attempt tests-24d9e7cacb974f61932a1e853d2986f5 was
interrupted across the session boundary. Its partial log remains; no Receipt.json
or aggregate verdict exists. It is not passed or silently discarded. A fresh
retained all-tests invocation completes verification of the same final source.
This is a unit-suite run, NOT a repeated consumed host/N3/cache diagnostic.

All test invocations use the retained scratch-scoped wrapper, not unchanged CI.
They keep prior data and forbid network/native/install actions. No exclusions.
CMv2: 213run/212pass/1error, missing tests_v2/OFFLINE1-CONTENT.json; receipt
tests-a64a3d897a9b4af9b0464ff9f4e6b11c SHAfa3bed06bd56b3fa8156c6cdd4a71afa783a5adad0c11a6f7f8082fd5e7baa80.
CMlegacy21/21: tests-5b2203489db94e7984ce2976814518a4
SHA3fab18014ef13843cd3a6d5aee2fec6cd8c9104d6f7de7c3d2720632fe2d331e.
MIlegacy21run/17pass/4errors: tests-e5ba85b1014345629931ab10ff11ea0c
SHAd87b3d135e2b13e33ccb909a0cb97f50d1ee314553d1e7d0330593ee3e8b92fd.
All four are existing test_memory_watchdog fixture setUp socket.bind refusals:
test_bridge_seed_and_verify_proves_persisted_canary_and_cleans_it,
test_recall_audit_reads_compact_result_titles,
test_roundtrip_uses_current_api_and_cleans_canary,
test_status_uses_current_agentmemory_api_and_does_not_claim_healthy.
They are not four established product faults or green tests. Do not loosen the
network guard silently. Final source/extraction/release checks remain open.

## Final2026-10-21 parent verification and commit boundary

Fresh final-source MIv2:692run,633pass,1failure,3errors,54skips,1expected failure,
zero exclusions. Complete retained receipt:
tests-8721d36dc8284ea0979620fc99aa98c8/Receipt.json
SHA5fede50db1b97ee8ad692b1f4cb90ea7cf79c5b0ddbbbe069ffaf23a5fb70f8b;
log SHA1629b60126381600ab8efdfca4616f1899b2b9836b0e299b4106ed6c854d508b.
The exact unresolved cases are:

- test_native_containment.ContainmentTests.test_grandchild_pipe_holder_killed:
  capture_complete=false, tree-sweep: taskkill exit1 in this agent context.
- test_native_paths.PathIdentityTests.test_info_accepts_short_database_path and
  test_short_and_long_forms_unify: OSError no short form.
- test_preservation.Preservation.test_release_exact_content_and_declared_changes:
  E_CONTENT_MISSING: tests_v2/OFFLINE1-CONTENT.json (final release not built).
- Expected failure remains the live-Dolt ignore-configuration proof; no native
  execution or false qualification is substituted for it. All54 skips and their
  explicit runtime/platform reasons are retained in the receipt, not passed.

The same unresolved four cases were in the prior complete688-test run; the final
run additionally includes all6 new controls and is not the interrupted log.
Fresh focused rerun6/6: tests-9a1aa39f88c54ce1be9b2f5c44ab614e/Receipt.json
SHAc50814dbf610297285f0df6aebf99358322f2e33b29c93fb6d20ce80d54e5135;
log SHA8253f663192fd0db66048be2d630a4aefede9b2dfcf7ba7ba04978e6db8ddeb6.
No focused error/skip/exclusion. Repository81/81, lifecycle6/6 and CM results above
remain separate evidence, never summed into a whole-green claim.

Final preservation comparison against the consumed scratch Prepared allows ONLY
three named production modifications and one added test file in the packages.
MI201 old hashes plus all115 CM hashes match (316 unchanged); no missing file.
The6 original cache DBs and12 named historical artifacts still match. New normal
scratch Receipt.json retains its supplied hash. No source/readme/manifest/old ZIP
was removed to clean the source tree. Only fresh test-owned temporary cleanup was
permitted by the existing user amendment; all retained evidence stays.

New test SHA256:dad936ff27c4ce20bc9ddaec92d32989e93a44f5c4fada3f92cab520ba3f130b.
Final native review accepted the source-only correction with caveats. Source
hashes above are rechecked, JSON parses and git diff --check passes. Local commit
includes the previous diagnostic-review correction and this source correction,
their tests, findings and resume records. No private runtime/cache/raw receipt is
staged. AUTH: "after complete check commit it". No push/install/CI/qualification
activation is authorized by that commit. Resolve its identity from git log; the
commit's parent is a9ae630772b2fa299767796daae28e2f3dbd08f9.

## Resume without restarting

Read this report then the latest checkpoint section. Never rerun the consumed
cache-cause, old N3 or host-a1 launchers; source changes correctly invalidate their
seals. Never edit those Prepared packets, markers or baselines. Keep the source
tree's six existing caches and all historical releases. A separate clean-source
successor must prove corrected selected3.12 startup/cleanup and integrated
advanced/completion/24-arm retrieval/preservation under normal account, with
separate host-attempt authority and reviewed exact source/runtime bindings.

Then finish matching m13 instructions/capabilities/companion contract, new content
lists, paired archives, full clean-extraction checks and exact-commit CI. Do not
regenerate frozen historical manifests to hide current source changes. Publishing
and target-app installation/smoke require their own authority. Native experiments
stay preserved and disabled. whole_skill_ready/release_ready/installed remain false.
