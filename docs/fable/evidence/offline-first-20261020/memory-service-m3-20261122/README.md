# AgentMemory M3 acceptance

**Full M3 verdict: PASS.** The November 23, 2026 Windows qualification observed one exact test memory survive a graceful service restart with the same physical datastore on the isolated AgentMemory 0.9.33 instance. Raw review confirmed all 12 stages and 13 recorded checks passed, with no runtime or cleanup failure. The fresh run closes the datastore-identity evidence gap in the historical continuation below.

| Check | Verdict | Reviewed evidence |
| --- | --- | --- |
| Real backend and distinct new service instance | PASS | The service used the accepted M2 configuration and owned its loopback listeners before and after restart. The supported stop and native Windows process handles established the original exit and distinct new process identities. See `Restart-Witness.json` and the native process ledgers. |
| Physical datastore continuity | PASS | Windows volume and directory file IDs matched at initial observation, immediately before shutdown, while stopped, and after restart. The stopped datastore inventory was rechecked before startup. See `Datastore-Initial-Identity.json`, `Datastore-Before-Stop.json`, `Datastore-Stopped-Identity.json`, and `Restart-Witness.json`. |
| Exact readback and recall | PASS | Before and after records matched the test memory ID, project, agent scope, and content digest. The 14-request trace has exactly one memory write, before shutdown, and the post-restart search check passed. |
| Cleanup and final stop | PASS | Deletion returned HTTP 200, direct lookup returned HTTP 404, and the follow-up search passed the absence check. The final native ledgers accounted for 14 service processes and three stop-command processes, all exited gracefully. The qualification ports had no listeners after the run. |
| Installed-skill integration | UNVERIFIED | M4 is a separate qualification. |

The raw evidence is retained locally under `memory-service-m3-full-20261123/`. The success marker in the receipt requested raw review, which was completed by cross-checking the identity records, native ledgers, request trace, and cleanup checks. The table below records SHA-256 digests of UTF-8 text with LF newlines for the two principal evidence files.

| File | SHA-256 (LF-normalized text) |
| --- | --- |
| `Receipt.json` | `af7906e62490f8a04ecd59cf412f14f3e40153fd0efec0be92ba1415cad9cb5d` |
| `Restart-Witness.json` | `47ea4355f0d330748d4082680ea68f48e311b5b80f5d59b0888f7d1f053a28da` |

## Historical partial attempt

Observed November 21, 2026. Reviewed November 22, 2026. This checkpoint follows the [accepted M1/M2 evidence](../memory-service-m1-m2-20261121/README.md) and retains the verified portion of one isolated AgentMemory 0.9.33 experiment.

| Check | Verdict | Reviewed evidence |
| --- | --- | --- |
| One scoped canary write | PASS | `canary-write.json` and `HTTP-03.json` record a completed write with HTTP 201. |
| Pre-restart direct read | PASS | `Canary-ID.json` and `Readback-Before.json` agree on the exact ID, scope and content digest. `HTTP-04.json` records HTTP 200. |
| Pre-restart recall | PASS | The exact result and its scoped direct recheck passed. See `pre-restart-search.json`, `HTTP-05.json` and `HTTP-06.json`. |
| Graceful shutdown | PASS | The supported stop command exited zero in a stage lasting 64.014 seconds. The native final ledgers show graceful exit for all 14 service-job processes and all three stop-command processes, with no forced termination or ledger gaps. |
| New instance, datastore continuity, post-restart readback and recall, cleanup | UNVERIFIED | The runner stopped before issuing the restart command. |
| Installed-skill integration | UNVERIFIED | Outside this deployment test. |

The runner published a stage record named `cold-datastore.json`, then tried to create `Cold-Datastore.json` for the detailed storage record. The case-insensitive Windows directory resolved both spellings to the same file, so exclusive creation raised `FileExistsError`. The stopped-storage stage record survived. The detailed storage record was lost and cannot be reconstructed as a historical observation.

The raw files remain in the original local M3 evidence directory. This checkpoint publishes only the reviewed results, evidence file names, and the remaining acceptance criteria.

### Continuation results before full qualification

The November 22 continuation used the existing canary. Review compared the original and resumed process ledgers, the physical datastore witness, the readback and recall records, and the HTTP trace. The preserved receipt is `memory-service-m3-resume-20261122/Receipt.json`.

| Check | Verdict | Reviewed evidence |
| --- | --- | --- |
| New service instance | PASS | `Restart-Witness.json` binds the earlier graceful exit ledgers to distinct new Windows process identities. The resumed instance matched the accepted configuration and owned its loopback listeners. |
| Datastore identity from the captured stopped baseline through startup | PASS | `Datastore-Before-Start.json` records the stopped baseline. `Restart-Witness.json` records matching Windows volume and directory file IDs for both the instance and datastore across startup. |
| Exact canary readback and recall after startup | PASS | `Readback-After.json` and `Recall-After.json` match the original ID, project and agent scope, and content digest. The continuation trace contains no memory write. |
| Deletion and absence | PASS | `HTTP-06.json` records successful deletion. Direct lookup of that item returned HTTP 404 in `HTTP-07.json`. The follow-up search passed the absence check, as recorded by `HTTP-08.json` and `stage-delete-and-check-absence.json`. |
| Final graceful shutdown | PASS | The service ledger accounted for all 14 tracked processes. The stop-command ledger accounted for all three. Both recorded native exit without forced termination, and the qualification ports no longer had listeners. |
| Continuous physical datastore identity from the original shutdown | UNVERIFIED | The original attempt did not save its detailed stopped datastore identity. The physical witness starts at the later captured stopped baseline. |
| Installed-skill integration | UNVERIFIED | Requires its own qualification. |

The original canary survived the recorded stop and later start, and its cleanup was verified. The comprehensive persistence field in the receipt remains `UNVERIFIED` for the original physical-identity evidence gap. This checkpoint retains the observed results and the filenames needed to locate the local evidence.

### Continuation plan recorded before the run

1. Reconcile the retained M3 receipt, matching canary records and native shutdown ledgers, and confirm the isolated service is still stopped. Review any evidence of intervening service activity or storage replacement.
2. Open a new evidence directory. Use distinct file names for stage records and detailed storage evidence and exercise that behavior before starting the service. Capture the physical identity of the stopped instance and datastore, compare the instance identity with accepted M2 evidence, and record the stopped storage metadata.
3. Start the same isolated deployment once. Verify its expected loopback listeners, pinned configuration and process creation identities against the earlier native records. Recheck the physical datastore identity and account for the unavailable original storage record. Keep any continuity claim qualified if intervening changes cannot be ruled out.
4. Fetch the already-written canary by its recorded ID. Check exact scope and the recorded content hash, then verify the supported recall route. Preserve that evidence before deleting the exact canary. Confirm direct absence, absence from search, and final graceful shutdown.
5. Publish only the new checks supported by retained evidence. Keep installed-skill integration and broader crash or reboot guarantees outside the M3 verdict.
