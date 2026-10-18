OFFLINE_REPAIR_VERIFIED_NATIVE_UNVERIFIED

Saved offline implementation and tests satisfy the current bounded A-I contract. This is not NATIVE_QUALIFIED, RELEASE_READY, SKILL_COMPLETE or installed readiness. A correctly connected uncertain race deliberately remains INCONCLUSIVE.

**Repository and authority.**

Repository: `C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git`. HEAD remains `3ea23556fd336ba64a3ebcf6b4fc169e71051d11`, branch `development/r5-practical-fence-wip-20261014`. Arrival was ten modified tracked files and five untracked files, rechecked against Git. The retained write probe succeeded. The 501-file before-edit inventory and raw dirty diff are retained. No reset, revert or commit occurred.

The primary review was read completely: `C:\Users\sakth\.codex\attachments\7a890120-d7c4-40c7-a7e9-6b8357998ddb\Pasted text.txt`, SHA-256 `61303dcd9331865434e9dd62eead6875c42d697da5c94d5a6d61997bef7aef3d`. It supplied hypotheses, not authority over requirements. Fable governed the approved local scope; Systematic Debugging traced component contracts, TDD saved failing regressions before fixes, and Verification Before Completion required fresh saved-source observations. No duplicate workflow, additional agent or external AI consultation was used.

**1. Saved implementation and governance hashes.**

Six implementation/test files and four existing campaign records were changed in this repair. The full saved-file-inventory.csv also lists supporting evidence files and distinguishes the nine pre-existing dirty code files left unchanged. All hashes below are SHA-256 over saved bytes.

| Absolute file | SHA-256 |
| --- | --- |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\tests_v2\test_practical_race_harness.py | cf303bb18230eb0659d5520b35edd2de12b10eb3aef48e4397ea1ad5feba4c2b |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\scripts\hybrid_bridge\practical_race_alice.py | 6439a43cba2c2bba678446a9cd3db4e40098d14361c0b64603b6722cdc8e4c4a |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\scripts\hybrid_bridge\practical_race_controller.py | f71dfcb6471b7b725f50ad50f4828ebdf70774fa65cdde08faafdabed17e156a |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\scripts\hybrid_bridge\practical_race_verify.py | 97647f56effadcadf123a35366c48f261549d8d9c6d42b2af82c7504ea0cc020 |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\tests_v2\test_practical_race_offline_sequence.py | 63b037a132242d44002d467f9422bb8e56c0af237805fdd335fea41fd87c6374 |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity\tests_v2\practical_race_transport_model.py | f92fce5eea725be883708f9fa7f001ce05fb5c9a1048dcda6c48dec78356d37a |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\docs\fable\derived\practical-fence-plan.md | fef69bbf0b42cb66387a0561c7dceb7c719435b5b516060c2f3a31c3408bedf2 |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\docs\fable\state.json | 2fb0711c64463c95bf525bfcb0c7933b26a7e00607782cdd7f5defceb0400b66 |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\docs\fable\GATES-lease-reassign.md | f260de8dd04874c532db393d20bff7cdf2a9e35b4364bf200a6bc0f6ef9c2d8b |
| C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\docs\changes\2026-10-14-practical-fence-wip.md | 45cc2cb1394be71ca6390c3b9b5192939990bb21643cf43e31f4db4e75873442 |

**2. Requirement -> implementation -> regression.**

| Criterion | Required outcome | Implementation | Observed regression |
| --- | --- | --- | --- |
| A | False refusal attribution removed | stale_refusal_attribution; actual resume_alice/run_race; raw Alice outcome retained | RefusalCausationRegressionTests (3); a-attribution-red.json -> passing saved implementation |
| B | Namespace/selection propagation | bootstrap UUID readback and independent fresh metadata validation before registration; immutable selection during seed | NamespacePropagationRegressionTests (3 with malformed/missing/mismatched/existing cases); l-minted-namespace-shape-red/green |
| C | Actual operation identities | actual Alice request/schedule/barrier/child-ID validation; actual post-claim transfer packet/batch retained; duplicate start refused | OperationPropagationRegressionTests (2), connected binding assertions and duplicate-start test; c-operation-red, m-transfer-schedule-red/green |
| D | Physical/schema/result contracts | actual store_identity; explicit physical/logical map and dependencies; nested Beads shape; validated complete backend packets; actual CM bindings/events and chain/replay; S2 mapping before controls | ObservationContractRegressionTests (5), connected packet test; de-observation-invariants-red, h-producer-packets-red/green, j-schema-adversarial-red/green |
| E | Applicable complete S1/S2 invariants | one committed-transfer validator; owner/status/task/store/node; frozen original lease/deadline; required grant snapshots; prior tombstone/facts; pointer/revision/token/history/operations; preserved baseline rows and unsafe effects | 8 transfer invariant tests, including 14 phase-matrix subcases, duplicate contradictions and later collection error; g-complete-relationships-red, i-s1-operation-red/green |
| F | Stateful complete offline workflow | actual driver, generated SQL packets, real worker, sealed backend, consumer, retained CM SQLite and canonical verifier; only unavoidable native boundaries modeled | FullSequenceOfflineTests (6); 16 fault subcases; connected-evidence.json contains 18 fresh executions and no PASSED case |
| G | Broader differences accounted | 501-file observed baseline copied with every byte reverified; same safety adapter and explicit outcome-set comparison | MI v2 615 -> 642; CM v2 208 -> 208; both legacy 21 -> 21; identical existing problem sets |
| H | Accurate existing evidence records | approved practical plan appendix, state, WIP, gate ledger; original plan/WIP byte prefixes preserved | 54 parsed gates: 43 met, 11 unmet; H2 reopened then closed by real connected evidence; independent review stays open |
| I | Actual saved bytes/preservation | acceptance-source.json; verify_saved.py; scope/inventory and whitespace checks; no original definition or file removed | 6 source hashes verified; every arrival file retained; unrelated dirty files byte-identical |

**3. Failing-before and passing-after evidence.**

The original attribution regression used actual resume_alice() and run_race(). `a-attribution-red.json` records `PASSED`, `reasons=[]` for UNKNOWN with unrelated transport failure and current Bob authority; both new tests failed as intended. The smallest attribution correction keeps the outcome UNKNOWN and returns `{by: null, code: E_HARNESS_EXECUTION_CAUSE_UNPROVEN}`. The saved regression now passes. Current authority is a separate observation; caller-created worker cause fields are ignored.

Other saved red receipts expose late namespace rebinding, wrong Alice ID, physical aliases, backend/companion status confusion, incomplete S1 checks, lost baseline history, hidden duplicate effects, missing S1 operation rows, lost raw observations and a stale transfer schedule packet. The stateful sequence also first failed because the worker recreated the parent CM work item; after that fix it reached the genuine S2/control operation-mapping mismatch. Each intermediate receipt is retained, including test-construction errors and corrected invalid fixtures; none is counted as a pass. The final race suite is 159/159 and the direct new module is 27/27. The older six component integration tests remain, with their narrower coverage labeled.

**4. Actual connected TEST_ONLY sequence.**

The following values come from connected-evidence.json, captured using the real canonical verifier. They are modeled native observations, not a Dolt execution or a real runtime pin measurement. Database UUID and all clock samples are supplied only by the TEST_ONLY transport boundary.

- Run: `race-9e9e7811443168de`
- Task: `mipx-1`
- DB-minted modeled namespace: `c0dec0de-2026-4017-8017-000000000017`
- Registered selection digest: `bad9914e71aa30898bc38f2e0cc6841f5a62fbe1530f8581c63c25ea83c043e8`
- Actual backend selection digest: `bad9914e71aa30898bc38f2e0cc6841f5a62fbe1530f8581c63c25ea83c043e8`
- Observed physical tables: `dependencies, issues, leases, mi_practical_v2_current_grants, mi_practical_v2_grant_history, mi_practical_v2_grants, mi_practical_v2_metadata, mi_practical_v2_operations, mi_practical_v2_token_history`

| Phase | Actual operation/binding | Observation |
| --- | --- | --- |
| Fresh setup/bootstrap | Namespace read before registration | c0dec0de-2026-4017-8017-000000000017 |
| Registration | bad9914e71aa30898bc38f2e0cc6841f5a62fbe1530f8581c63c25ea83c043e8 | Same namespace, database, branch and node |
| Initial claim | op-claim-race-9e9e7811443168de | Open task -> current lease/grant; baseline receipt retained; direct sealed-backend mechanism-only route |
| Alice request/paused dispatch | op-stale-race-9e9e7811443168de | Post-claim original row token and grant; same namespace/digest |
| Observed barrier | op-stale-race-9e9e7811443168de | TEST_ONLY-session-4242 |
| Legitimate transfer | op-reassign-1 | Prior grant tombstoned, successor minted; original granted time/node/expiry frozen |
| S1 | op-reassign-1 | Committed transfer invariants and baseline records observed |
| Alice completion | op-stale-race-9e9e7811443168de | UNKNOWN; authority currently stale; execution cause unproven |
| S2 and operation mapping | op-claim-race-9e9e7811443168de, op-reassign-1 | Captured before controls; no stale backend success/effect |
| Companion | {'op-stale-race-9e9e7811443168de': 1, 'op-reassign-1': 1} | Actual intent bindings/events retained; internal chain and projection replay VERIFIED |
| Positive control | op-positive-race-9e9e7811443168de | Same protected consumer; WORKING_SET_APPLIED readback and own later state |
| Disabled comparison | Harness-only bare update | Unsafe modeled effect observed in its own later snapshot |
| Canonical verifier/cleanup | INCONCLUSIVE | One canonical call; only REFUSAL_UNKNOWN; owned resource releases true |

The complete path uses real driver methods, builders, the worker entry point, sealed backend, consumer, companion SQLite journal and canonical verifier. Store identity, current authority, read_state, consumer completion and final verdict are not replaced by canned successful results. Native eligibility/preflight, process handles and SQL transport are modeled; the model consumes complete generated binding/receipt templates and evolves one physical-table state. It does not execute or validate Dolt SQL grammar, native conflicts, actual barrier timing or durability. The real-Beads nested identity shape is unit-tested only; real-Beads runtime observation stays UNVERIFIED.

**5. Focused and broader regressions.**

Interpreter: `C:\Python314\python.exe`, CPython 3.14.3. Package CWDs are recorded exactly in test-run-index.csv and each JSON receipt. The project discovery commands are `python -B -m unittest discover -s tests_v2`, `-s tests`, `-s .github/tests`, and `-s .` from their actual package/root/evals directories.

| Receipt | Tests | Failures | Errors | Skips | Expected failures | Adapted |
| --- | --- | --- | --- | --- | --- | --- |
| m-transfer-schedule-green.json | 159 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |
| final-lease.json | 44 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |
| final-consumer.json | 17 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |
| final-cm-practical.json | 18 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |
| acceptance-mi-v2.json | 642 | 2 | 36 | 54 | 1 | YES: retention/safety adapter |
| safe-python-final-cm.json | 208 | 1 | 1 | 0 | 0 | YES: retention/safety adapter |
| final-mi-legacy.json | 21 | 0 | 4 | 0 | 0 | YES: retention/safety adapter |
| final-cm-legacy.json | 21 | 3 | 14 | 0 | 0 | YES: retention/safety adapter |
| final-repository.json | 19 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |
| final-evals.json | 10 | 0 | 0 | 0 | 0 | YES: retention/safety adapter |

Direct unchanged invocation of the new test module: from `C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\memory-integrity`, `python -B -m unittest discover -s tests_v2 -p test_practical_race_offline_sequence.py`: 27 tests, zero failures/errors/skips/expected failures; acceptance-direct-full-sequence.log. Direct `-k FullSequenceOfflineTests`: six tests, zero failures/errors/skips/expected failures; gate-h2-direct.log. These test-owned fixtures are retained without deleting cleanup.

Other source-suite runs use a retention/safety adapter, not unchanged CI. Version 1 retains TemporaryDirectory fixtures and denies all subprocess/deletion requests. Version 2 also installs an inherited offline policy permitting guarded Python subprocesses only; it denies deletion, network and native/non-Python/unguarded processes. The v2 guarded_python_children_allowed flag and recorded policy/runner bytes describe that behavior; older generic adapters text inherited from v1 is less precise. Exact wrapper commands, CWDs and runner hashes are in test-run-index.csv. The original unmodified test bodies are retained except the explicitly authorized harness fixture and invalid expectation corrections listed in the source diff.

| Suite pair | Observed baseline | Observed repaired | Existing outcome differences |
| --- | --- | --- | --- |
| MI v2 | {'tests': 615, 'failures': 2, 'errors': 36, 'skips': 54, 'expected_failures': 1, 'unexpected_successes': 0} | {'tests': 642, 'failures': 2, 'errors': 36, 'skips': 54, 'expected_failures': 1, 'unexpected_successes': 0} | None |
| CM v2 | {'tests': 208, 'failures': 1, 'errors': 1, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | {'tests': 208, 'failures': 1, 'errors': 1, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | None |
| MI legacy | {'tests': 21, 'failures': 0, 'errors': 4, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | {'tests': 21, 'failures': 0, 'errors': 4, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | None |
| CM legacy | {'tests': 21, 'failures': 3, 'errors': 14, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | {'tests': 21, 'failures': 3, 'errors': 14, 'skips': 0, 'expected_failures': 0, 'unexpected_successes': 0} | None |

The baseline copy contains all 501 arrival files, individually reverified against observed hashes; it is not a reset to historical HEAD. The copy has no Git state. Its missing retained-fixture parent caused 18 CM setup errors on the first copied-tree run; that parent was created and the comparable rerun is baseline-cm-aligned.json. The earlier receipt remains retained. MI adds exactly 27 passing test bodies. No original function/class/test definition was removed.

Full regression and release gates remain unmet. Both preservation tests still fail against their historical manifests, already failing at arrival; no manifest was regenerated or weakened. The other MI v2 failure is the containment test because taskkill is blocked. Of 36 MI v2 errors, 34 are blocked operations and two are unavailable Windows short-path observations. CM v2 has one blocked graph-file-removal error. MI legacy has four blocked loopback-server binds; CM legacy has three failures and fourteen errors caused by blocked cleanup/deletion. Those same outcomes were observed on the byte-verified baseline copy. All remaining failure/error identities and complete tracebacks are below and in remaining-failures.csv.

| Receipt | Type | Exact test | Classification | Final traceback line |
| --- | --- | --- | --- | --- |
| acceptance-mi-v2.json | failures | test_grandchild_pipe_holder_killed (test_native_containment.ContainmentTests.test_grandchild_pipe_holder_killed) | Blocked native/non-Python/unguarded process | AssertionError: False is not true : ['tree-sweep: OFFLINE_REPAIR_NO_UNGUARDED_PROCESS: taskkill /PID 44552 /T /F'] |
| acceptance-mi-v2.json | failures | test_release_exact_content_and_declared_changes (test_preservation.Preservation.test_release_exact_content_and_declared_changes) | Existing preservation manifest drift | Diff is 18189 characters long. Set self.maxDiff to None to see it. |
| acceptance-mi-v2.json | errors | test_degraded_pack_cannot_claim_shacl_or_lineage (test_knowledge_audit_integrity.OptionalReceiptIntegrity.test_degraded_pack_cannot_claim_shacl_or_lineage) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_foreign_backend_cannot_qualify_optional_pack (test_knowledge_audit_integrity.OptionalReceiptIntegrity.test_foreign_backend_cannot_qualify_optional_pack) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_public_preflight_rejects_forged_pack_before_run_state (test_knowledge_audit_integrity.OptionalReceiptIntegrity.test_public_preflight_rejects_forged_pack_before_run_state) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_unknown_nested_receipt_keys_are_refused (test_knowledge_audit_integrity.OptionalReceiptIntegrity.test_unknown_nested_receipt_keys_are_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_valid_direct_fallback_preserves_protected_workflow (test_knowledge_audit_integrity.OptionalReceiptIntegrity.test_valid_direct_fallback_preserves_protected_workflow) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_corrupted_generation_and_changed_branch_refused (test_knowledge_bridge.AdditionalContracts.test_corrupted_generation_and_changed_branch_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_current_acl_loader_does_not_reopen_denied_sources (test_knowledge_bridge.AdditionalContracts.test_current_acl_loader_does_not_reopen_denied_sources) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_different_query_embedding_model_refused (test_knowledge_bridge.AdditionalContracts.test_different_query_embedding_model_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_nonaxis_query_pack_verifies_without_rounding_drift (test_knowledge_bridge.AdditionalContracts.test_nonaxis_query_pack_verifies_without_rounding_drift) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_optional_pack_cannot_falsify_embedding_provenance (test_knowledge_bridge.AdditionalContracts.test_optional_pack_cannot_falsify_embedding_provenance) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_rehashed_forged_assertion_pack_refused (test_knowledge_bridge.AdditionalContracts.test_rehashed_forged_assertion_pack_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_unreviewed_derivation_cycle_refused (test_knowledge_bridge.AdditionalContracts.test_unreviewed_derivation_cycle_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_bad_endpoint_missing_unit_duplicate_id_unknown_field_refused (test_knowledge_bridge.Bridge.test_bad_endpoint_missing_unit_duplicate_id_unknown_field_refused) (change='endpoint') | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_canonical_manifest_reopen_and_drift (test_knowledge_bridge.Bridge.test_canonical_manifest_reopen_and_drift) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_interrupted_publication_preserves_current_and_writer_lock (test_knowledge_bridge.Bridge.test_interrupted_publication_preserves_current_and_writer_lock) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_missing_worker_and_bad_query_vector_block (test_knowledge_bridge.Bridge.test_missing_worker_and_bad_query_vector_block) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_permission_filter_before_worker_and_pack (test_knowledge_bridge.Bridge.test_permission_filter_before_worker_and_pack) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_revoked_required_scope_budget_unknown_worker_result_blocks (test_knowledge_bridge.Bridge.test_revoked_required_scope_budget_unknown_worker_result_blocks) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_source_escape_refused (test_knowledge_bridge.Bridge.test_source_escape_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_backend_label_cannot_qualify_graph_required_pack (test_knowledge_bridge.SavedPackSecurity.test_backend_label_cannot_qualify_graph_required_pack) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_derivation_premise_units_reopened (test_knowledge_bridge.SavedPackSecurity.test_derivation_premise_units_reopened) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_rehashed_unauthorized_path_refused (test_knowledge_bridge.SavedPackSecurity.test_rehashed_unauthorized_path_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_branch_change_blocks_current_use (test_knowledge_completion.Completion.test_branch_change_blocks_current_use) | Blocked native/non-Python/unguarded process | PermissionError: OFFLINE_REPAIR_NO_UNGUARDED_PROCESS: git -C C:\Users\sakth\Documents\Codex\2026-10-17\paste-the-entire-prompt-below-into\work\retained-fixtures\tmpa1fzmru2 init |
| acceptance-mi-v2.json | errors | test_empty_skipped_and_forged_test_receipt_cannot_pass (test_knowledge_completion.Completion.test_empty_skipped_and_forged_test_receipt_cannot_pass) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_real_tests_fail_and_stale_pass_never_admits (test_knowledge_completion.Completion.test_real_tests_fail_and_stale_pass_never_admits) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_requested_extraction_checks_reject_failed_required_parser (test_knowledge_completion.Completion.test_requested_extraction_checks_reject_failed_required_parser) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_same_branch_unrelated_commit_and_incremental_reuse (test_knowledge_completion.Completion.test_same_branch_unrelated_commit_and_incremental_reuse) | Blocked native/non-Python/unguarded process | PermissionError: OFFLINE_REPAIR_NO_UNGUARDED_PROCESS: git -C C:\Users\sakth\Documents\Codex\2026-10-17\paste-the-entire-prompt-below-into\work\retained-fixtures\tmp_xza17ef init |
| acceptance-mi-v2.json | errors | test_source_edit_between_extraction_and_publication_is_refused (test_knowledge_completion.Completion.test_source_edit_between_extraction_and_publication_is_refused) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_info_accepts_short_database_path (test_native_paths.PathIdentityTests.test_info_accepts_short_database_path) | Windows short-path observation unavailable | OSError: no short form |
| acceptance-mi-v2.json | errors | test_short_and_long_forms_unify (test_native_paths.PathIdentityTests.test_short_and_long_forms_unify) | Windows short-path observation unavailable | OSError: no short form |
| acceptance-mi-v2.json | errors | test_missing_result_artifact_blocks_fresh_read (test_r2_workflow.Workflow.test_missing_result_artifact_blocks_fresh_read) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_changed_dirty_bytes_change_observed_identity (test_r3_branch.BranchPolicyTests.test_changed_dirty_bytes_change_observed_identity) | Blocked native/non-Python/unguarded process | PermissionError: OFFLINE_REPAIR_NO_UNGUARDED_PROCESS: git init C:\Users\sakth\Documents\Codex\2026-10-17\paste-the-entire-prompt-below-into\work\retained-fixtures\tmpovxrzb3f |
| acceptance-mi-v2.json | errors | test_non_git_is_an_explicit_boundary (test_r3_branch.BranchPolicyTests.test_non_git_is_an_explicit_boundary) | Blocked native/non-Python/unguarded process | PermissionError: OFFLINE_REPAIR_NO_UNGUARDED_PROCESS: git -C not-a-repository rev-parse --show-toplevel |
| acceptance-mi-v2.json | errors | test_conflict_and_missing_cas_leave_dirty_origin_and_ledger_unchanged (test_r3_central_merge.CentralMerge.test_conflict_and_missing_cas_leave_dirty_origin_and_ledger_unchanged) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_retained_merge_reopens_all_origins_and_reconciles_interrupted_intent (test_r3_central_merge.CentralMerge.test_retained_merge_reopens_all_origins_and_reconciles_interrupted_intent) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| acceptance-mi-v2.json | errors | test_missing_source_blocked (test_source_binding.BindingTests.test_missing_source_blocked) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| safe-python-final-cm.json | failures | test_release_exact_content_and_declared_changes (test_preservation.Preservation.test_release_exact_content_and_declared_changes) | Existing preservation manifest drift | Diff is 7186 characters long. Set self.maxDiff to None to see it. |
| safe-python-final-cm.json | errors | test_missing_or_corrupt_graph_cas_blocks_prepare_dispatch_and_accept (test_r3_coordination.CoordinationTests.test_missing_or_corrupt_graph_cas_blocks_prepare_dispatch_and_accept) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-mi-legacy.json | errors | test_bridge_seed_and_verify_proves_persisted_canary_and_cleans_it (test_memory_watchdog.WatchdogTests.test_bridge_seed_and_verify_proves_persisted_canary_and_cleans_it) | Blocked network/system action | PermissionError: OFFLINE_REPAIR_OFFLINE_ONLY: socket.bind |
| final-mi-legacy.json | errors | test_recall_audit_reads_compact_result_titles (test_memory_watchdog.WatchdogTests.test_recall_audit_reads_compact_result_titles) | Blocked network/system action | PermissionError: OFFLINE_REPAIR_OFFLINE_ONLY: socket.bind |
| final-mi-legacy.json | errors | test_roundtrip_uses_current_api_and_cleans_canary (test_memory_watchdog.WatchdogTests.test_roundtrip_uses_current_api_and_cleans_canary) | Blocked network/system action | PermissionError: OFFLINE_REPAIR_OFFLINE_ONLY: socket.bind |
| final-mi-legacy.json | errors | test_status_uses_current_agentmemory_api_and_does_not_claim_healthy (test_memory_watchdog.WatchdogTests.test_status_uses_current_agentmemory_api_and_does_not_claim_healthy) | Blocked network/system action | PermissionError: OFFLINE_REPAIR_OFFLINE_ONLY: socket.bind |
| final-cm-legacy.json | failures | test_end_to_end_cli_materializes_chunk_and_status_hides_content (test_cli.CliTests.test_end_to_end_cli_materializes_chunk_and_status_hides_content) | Blocked file deletion/cleanup |  |
| final-cm-legacy.json | failures | test_register_preserves_provenance_when_cli_option_is_omitted (test_cli.CliTests.test_register_preserves_provenance_when_cli_option_is_omitted) | Blocked file deletion/cleanup |  |
| final-cm-legacy.json | failures | test_verify_returns_nonzero_on_stale_source (test_cli.CliTests.test_verify_returns_nonzero_on_stale_source) | Blocked file deletion/cleanup |  |
| final-cm-legacy.json | errors | test_chunk_manifest_has_exact_primary_coverage_and_context_is_not_primary (test_core.ClaudeMonCoreTests.test_chunk_manifest_has_exact_primary_coverage_and_context_is_not_primary) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_chunk_payload_materializes_exact_bytes_and_hash (test_core.ClaudeMonCoreTests.test_chunk_payload_materializes_exact_bytes_and_hash) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_chunk_verifier_detects_missing_and_duplicate_primary_units (test_core.ClaudeMonCoreTests.test_chunk_verifier_detects_missing_and_duplicate_primary_units) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_receipt_becomes_stale_after_source_change_without_rewriting_history (test_core.ClaudeMonCoreTests.test_receipt_becomes_stale_after_source_change_without_rewriting_history) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_receipt_cannot_be_complete_without_exact_input_hashes (test_core.ClaudeMonCoreTests.test_receipt_cannot_be_complete_without_exact_input_hashes) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_receipt_complete_is_task_bound_and_append_only (test_core.ClaudeMonCoreTests.test_receipt_complete_is_task_bound_and_append_only) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_register_changed_content_preserves_version_history (test_core.ClaudeMonCoreTests.test_register_changed_content_preserves_version_history) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_register_uses_content_hash_and_rejects_outside_root (test_core.ClaudeMonCoreTests.test_register_uses_content_hash_and_rejects_outside_root) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_status_does_not_emit_source_content (test_core.ClaudeMonCoreTests.test_status_does_not_emit_source_content) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_unit_manifest_is_exact_deterministic_and_unicode_safe (test_core.ClaudeMonCoreTests.test_unit_manifest_is_exact_deterministic_and_unicode_safe) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_unitize_rejects_invalid_utf8 (test_core.ClaudeMonCoreTests.test_unitize_rejects_invalid_utf8) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_verify_receipt_rechecks_input_hashes_in_saved_receipt (test_core.ClaudeMonCoreTests.test_verify_receipt_rechecks_input_hashes_in_saved_receipt) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_gate_blocks_stale_receipt (test_fable_bridge.FableBridgeTests.test_gate_blocks_stale_receipt) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |
| final-cm-legacy.json | errors | test_gate_blocks_until_matching_complete_task_receipt_exists (test_fable_bridge.FableBridgeTests.test_gate_blocks_until_matching_complete_task_receipt_exists) | Blocked file deletion/cleanup | PermissionError: OFFLINE_REPAIR_NO_DELETION: os.remove |

**6. Adversarial saved-source results.**

The original false PASS is absent through both actual resume/run_race and the full connected transport-failure case. Missing cause reaches the canonical verifier for the correct reason; no namespace, operation, schema, result-format, history or control error contaminates that case. Forged worker cause fields, wrong/missing worker operation IDs, malformed/foreign namespace, every missing physical table, malformed/duplicate schema names, status confusion, invalid S1, stale effects/receipts, missing history/receipts, contradictory receipts, missing/ineffective controls, duplicate dispatch observations, duplicate Alice submission and failed cleanup are exercised.

| Fault/case | Canonical calls | Verdict | Stopped | Reason codes |
| --- | --- | --- | --- | --- |
| unrelated_transport_failure | 1 | INCONCLUSIVE | True | REFUSAL_UNKNOWN |
| missing_execution_cause | 1 | INCONCLUSIVE | True | REFUSAL_UNKNOWN |
| foreign_namespace | 0 | INCONCLUSIVE | True | IDENTITY_UNVERIFIED |
| wrong_worker_operation | 1 | INCONCLUSIVE | True | REFUSAL_UNKNOWN |
| missing_physical_table | 0 | INCONCLUSIVE | True | IDENTITY_UNVERIFIED |
| backend_companion_status_confusion | 0 | INCONCLUSIVE | True | OBSERVATION_INCOMPLETE |
| invalid_s1 | 1 | FAILED | True | REFUSAL_UNKNOWN; WINNER_STATE_LOST |
| invalid_s1_lease | 1 | FAILED | True | GRANT_LEASE_FACTS_MISMATCH; REFUSAL_UNKNOWN |
| stale_effect | 1 | FAILED | True | OBSERVATION_INCOMPLETE; OPERATION_RECORD_DISAGREEMENT; REFUSAL_UNKNOWN; STALE_BACKEND_SUCCESS_RECORD; STALE_COMMITTED_EFFECT; STALE_SUCCESS_RECEIPT; UNEXPLAINED_CHANGE |
| stale_success_record | 1 | FAILED | True | OBSERVATION_INCOMPLETE; OPERATION_RECORD_DISAGREEMENT; REFUSAL_UNKNOWN; STALE_BACKEND_SUCCESS_RECORD; STALE_SUCCESS_RECEIPT; UNEXPLAINED_CHANGE |
| missing_history | 1 | INCONCLUSIVE | True | GRANT_HISTORY_INCOMPLETE; REFUSAL_UNKNOWN |
| ineffective_positive_control | 1 | INCONCLUSIVE | True | CONTROL_INEFFECTIVE; REFUSAL_UNKNOWN |
| ineffective_disabled_control | 1 | INCONCLUSIVE | True | CONTROL_NOT_EXECUTED; REFUSAL_UNKNOWN |
| failed_cleanup | 1 | INCONCLUSIVE | False | HARNESS_ERROR; REFUSAL_UNKNOWN |
| missing_receipt | 1 | INCONCLUSIVE | True | HARNESS_ERROR; OBSERVATION_INCOMPLETE; REFUSAL_UNKNOWN |
| contradictory_receipt | 1 | INCONCLUSIVE | True | HARNESS_ERROR; OBSERVATION_INCOMPLETE; REFUSAL_UNKNOWN |
| duplicate_dispatch | 1 | FAILED | True | CONTROL_INEFFECTIVE; DUPLICATE_DISPATCH; JOURNAL_HISTORY_INVALID; REFUSAL_UNKNOWN |
| missing_s1_operation | 1 | FAILED | True | OPERATION_RECORD_DISAGREEMENT; REFUSAL_UNKNOWN |

Early namespace/schema/transfer-receipt faults correctly refuse before the canonical race verdict. The duplicate-dispatch fault appends a deliberately invalid event to a retained TEST_ONLY companion fixture; production journal guards are unchanged. The failed-cleanup case intentionally has stopped=false and cannot be labeled complete. Observed unsafe effects remain FAILED even when a later read is missing or a contradictory duplicate row is present. TWINS: the central production attribution helper is corrected; the coarse legacy exception-source classifier is diagnostic and does not provide execution-cause proof. Canonical pure-evidence unit fixtures can state a test premise about refusal; the actual worker cannot supply its own cause. Backend receipt comparison uses WORKING_SET_APPLIED, and all other existing dirty modules were preserved.

**7. Gate and campaign status.**

The parser reports 54 gates: 43 met and 11 unmet, zero parse errors. Its direct status exit 1 means unmet gates, not a parse failure. H2 was reopened because the old six component tests overstated complete-workflow coverage, and is now closed only by the new six connected tests. OFFLINE-A through OFFLINE-I map to I1-I9. B4/B5 remain unmet for full suites. F1-F9 remain unmet for native cases, public workflow qualification, independent review, regression/release closure, packages, exact-commit publication/CI and installed verification. The original plan and WIP bytes are exact retained prefixes, with current corrections appended. State keeps parent P1-P5 open and records only the bounded offline result.

**8. Explicit unverified boundaries.**

No native Dolt/Beads execution, SQL grammar/rollback/atomicity proof, actual native barrier/race, expiry/heartbeat/ABA proof, native crash/restart/recovery proof, real-Beads runtime observation, public claim-dispatch qualification, merge/replication qualification, fresh remote CI, independent review by another reviewer, release/package verification or installed-copy testing is established. All adopted native/strict/merge/acceptance/installed qualification flags remain false. Confidence is high in the bounded offline contract because the saved source and connected Python execution are observed; implementation and model tests are correlated evidence and are not a second native witness. Judge verdict: VERIFIED WITH CAVEATS for offline repairs only.

**9. Scope and preservation confirmation.**

All 501 arrival files remain. The nine pre-existing dirty code files outside the repair are byte-identical. The stopped predecessor, adopted timing contract, companion journal, historical manifests, packages and retained evidence remain. Existing definitions are preserved. No file-deleting cleanup, native database execution, installation/upgrade, Git commit/push/reset, workflow dispatch, external AI, extra agent/task, publication, release-manifest regeneration, release packaging or installed-copy replacement occurred. Normal Python offline test subprocesses were allowed only under the inherited safety policy; prohibited attempts are recorded as blocked. Saved-file inventory and final scope receipts distinguish this repair from arrival dirt. No further implementation remains within the approved offline A-I contract. Native/release/install work requires a separate request and authorization.

**Recheck commands.**

From the repository root:

```powershell
python -B docs/fable/evidence/offline-repair-20261017/verify_saved.py
python -B docs/fable/evidence/offline-repair-20261017/verify_regressions.py
git diff --check
```

From memory-integrity:

```powershell
python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py"
```

Do not run all existing suites unchanged under the standing no-deletion boundary. Use the recorded retention/safety runner commands for those adapted suites. The evidence directory retains every measured red/green run and the full command index.
