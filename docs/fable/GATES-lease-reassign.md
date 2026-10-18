# Gates ledger — practical lease-reassign offline slice

Scope of this ledger: the offline harness for the in-place lease transfer
(adopted EXPERIMENTAL custom protected-adapter protocol, disposable
fence-owned local stores only). It does not authorize native execution.

Baseline: checkout HEAD 3ea23556fd336ba64a3ebcf6b4fc169e71051d11 with 10
modified tracked files and 5 untracked files.

Status label: OFFLINE_REPAIR_VERIFIED_NATIVE_UNVERIFIED. Every native
qualification flag stays false. No gate here can promote the candidate to
NATIVE_QUALIFIED, RELEASE_READY or SKILL_COMPLETE.

**Disproven and repaired, twice.** An independent read-only review first
refuted the first pass's completeness claim: six further verifier false
passes and six driver wiring defects were reproduced, not accepted on
assertion. A second review then found that connecting the driver to the real
components exposed contract mismatches the mocks concealed: the driver read a
result field the companion never returns, fresh setup could not reach a valid
claim, the executed paused SQL lacked the marker's watcher searched for, and
three more evidence cases still passed. Both rounds are recorded below and in
the WIP. Gates D5 and E2 were reopened because their evidence overstated what
had been proven. Gate G is the first repair round; gate H is the second.

Measured environment: Windows PowerShell 5.1, Python 3.14.3, Node from
C:\PROGRA~1\nodejs, runner shell cmd.exe. Gate CWD is repository-relative to
the checkout root.

Parser contract for this file, verified against
C:\Users\sakth\.agents\skills\unlazy\scripts\lib\gates.mjs: gate lines are
`- [ ] ID: Observable outcome`; CHECK/EXPECT/CWD/EVIDENCE are indented
attribute lines with no nested bullet marks; runnable gates carry both a
non-blank CHECK and EXPECT; a met gate requires a checked box plus non-pending
EVIDENCE.

C:\PROGRA~1\nodejs is used instead of the quoted long path because a quoted
path containing spaces does not survive the checker's shell wrapping.

OWNS: memory-integrity/scripts/hybrid_bridge/practical_race_controller.py, memory-integrity/scripts/hybrid_bridge/practical_race_verify.py, memory-integrity/scripts/hybrid_bridge/practical_race_alice.py, memory-integrity/tests_v2/test_practical_race_harness.py, docs/fable/GATES-lease-reassign.md

## Gate A — exact resulting-heartbeat validation

- [x] A1: repro probe refuses a wrong resulting heartbeat through the real consumer and sealed backend
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_consumer.py" -v -k wrong_resulting_heartbeat
  EXPECT: test_reassign_wrong_resulting_heartbeat_refuses_despite_bounds
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; authorization 10:00:01.500000 with resulting heartbeat 10:00:01.000000 yields UNKNOWN and zero APPLIED events

- [x] A2: a valid result still completes the winner dispatch as APPLIED
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_consumer.py" -v -k reassign_winner_dispatch_then_real_readback_applies
  EXPECT: test_reassign_winner_dispatch_then_real_readback_applies
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; winner reassign dispatch then real operation readback applies through the sealed backend and registered journal reader, after the consumer dispatch body was refactored onto one shared protected path

- [x] A3: the reassign receipt refuses invalid-precision and missing resulting-heartbeat evidence
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_lease_backend.py" -v -k receipt_refuses_invalid_precision_and_missing_heartbeat
  EXPECT: test_reassign_receipt_refuses_invalid_precision_and_missing_heartbeat
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; nonzero microseconds, absent key and suffix-less value each raise E_MI2_RECEIPT_HEARTBEAT, and the untouched receipt still validates so the refusals are not a broken fixture

- [x] A4: non-vacuity — the superseded bounds-only rule accepts the probe the validator refuses
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_consumer.py" -v -k bounds_only_check_would_accept_the_probe
  EXPECT: test_bounds_only_check_would_accept_the_probe
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; the old weak bounds rule accepts the probe that the strict validator refuses, so the strictness is not vacuous

## Gate B — integrated offline verification

- [x] B1: focused lease suites are green with counts read from actual output
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_lease_*.py"
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 44 tests; OK; contract 7, sql 14, backend 19, after the backend dispatch refactor onto _execute_protected and the addition of the bounded paused dispatch

- [x] B2: history assertions are associated per write
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_lease_sql.py" -v -k reassign_tombstones_prior_grant_and_mints_granted_successor
  EXPECT: test_reassign_tombstones_prior_grant_and_mints_granted_successor
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; prior grant tombstoned and GRANTED successor minted, with the TOMBSTONED assertion before the MINTED insert

- [x] B3: companion journal and dispatch regressions are green
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_*.py"
  EXPECT: OK
  CWD: claude-mon
  EVIDENCE: exit=0; cwd claude-mon; Ran 18 tests; OK; journal 10 and dispatch 8; the companion ledger was not modified in either pass

- [ ] B4: full memory-integrity suite reports zero errors (preservation failure retained)
  CHECK: python -B -m unittest discover -s tests_v2
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: Current safe offline adaptation: baseline 615 to repaired 642, both failures=2/errors=36/skipped=54/expected failures=1; same existing outcome sets. Preservation drift remains; containment taskkill is blocked; 34 errors are blocked actions and two are Windows short-path observations. This is not a full-green or unchanged CI run. See evidence/offline-repair-20261017/acceptance-mi-v2.json and regression-comparison.json

- [ ] B5: full companion suite reports zero errors (preservation failure retained)
  CHECK: python -B -m unittest discover -s tests_v2
  EXPECT: OK
  CWD: claude-mon
  EVIDENCE: Current safe offline adaptation: baseline and repaired 208, both failures=1/errors=1; unchanged existing outcomes. Preservation drift remains and the graph-removal test is blocked by no-deletion. See evidence/offline-repair-20261017/baseline-cm-aligned.json and safe-python-final-cm.json

## Gate C — one canonical fail-closed verifier

- [x] C1: the gate ledger itself parses and reports every gate status
  CHECK: C:\PROGRA~1\nodejs\node.exe "C:\Users\sakth\.agents\skills\unlazy\scripts\gate-check.mjs" --status --root "C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git" "C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git\docs\fable\GATES-lease-reassign.md" & if errorlevel 2 (exit /b 1) else (exit /b 0)
  EXPECT: GATES-lease-reassign.md: 54 gates
  CWD: .
  EVIDENCE: status-only parser reports 54 gates, 43 met and 11 unmet with zero parse errors; direct status exit=1 reflects unmet gates. It executes no CHECK command and changes no gate. Historical 45-gate evidence is retained in the arrival snapshot

- [x] C2: run_race rejects a wait_barrier result of None (case A previously PASSED)
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k case_a_none_barrier
  EXPECT: test_case_a_none_barrier_is_inconclusive_through_run_race
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; before the fix PASSED for a None barrier, now INCONCLUSIVE with BAR_INVALID evidence rejected and both owned processes released

- [x] C3: run_race fails a stale backend success record whose CM journal stays UNKNOWN (case B previously PASSED)
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k case_b_stale_backend_success_record
  EXPECT: test_case_b_stale_backend_success_record_with_unknown_journal_fails
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; before the fix PASSED, now FAILED with STALE_BACKEND_SUCCESS_RECORD

- [x] C4: run_race fails extended expiry, wrong grant actor and disagreeing grant revision (case C previously PASSED)
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k case_c_extended_expiry_wrong_actor
  EXPECT: test_case_c_extended_expiry_wrong_actor_and_grant_revision_disagreement_fails
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; before the fix PASSED, now FAILED reporting EXPIRY_MOVED, GRANT_ACTOR_MISMATCH, GRANT_REVISION_MISMATCH and GRANT_LEASE_FACTS_MISMATCH together

- [x] C5: an unverified Beads marker string alone is never observed identity (case D previously PASSED)
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k case_d_unverified_beads_marker
  EXPECT: test_case_d_unverified_beads_marker_only_is_inconclusive
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; before the fix PASSED, now INCONCLUSIVE with IDENTITY_UNVERIFIED because a marker path and a caller-supplied hash are not a queried store identity

- [x] C6: control phases present in the schedule but never executed cannot pass (case E previously PASSED)
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k case_e_controls_scheduled_but_not_executed
  EXPECT: test_case_e_controls_scheduled_but_not_executed_is_inconclusive
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; before the fix the orchestration returned PASSED with both controls never invoked, now INCONCLUSIVE with CONTROL_NOT_EXECUTED

- [x] C7: the retained negative cases all stay non-passing through run_race
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k RetainedNegative
  EXPECT: Ran 10 tests
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 10 tests; OK; empty evidence, absent journal, absent dispatch, title-only stale change, missing rows and tables, disappeared grant row, duplicate dispatch, unrelated refusal, unknown refusal code, and unsafe effect with incomplete evidence

- [x] C8: the verifier rejects malformed evidence types, duplicate row identities and contradictory observations
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k EvidenceSchema
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 15 tests; OK; includes that a malformed section produces a reason instead of an exception, that a duplicate composite identity is reported rather than collapsed, and that a second observation of the same operation must agree with the first

- [x] C9: one canonical verdict path is the only scored entry
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k single_canonical_verdict_path
  EXPECT: test_single_canonical_verdict_path_is_the_only_scored_entry
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; the controller calls judge_evidence exactly once, contains no _judge_predicates or verify_winner_predicates, and the verifier exports judge_evidence as its only judge_ entry point

## Gate D — complete orchestration and controls

- [x] D1: orchestration executes the enabled arm, then the positive control, then the fence-disabled comparison
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k orchestration_executes_enabled_positive_and_disabled_arms
  EXPECT: test_orchestration_executes_enabled_positive_and_disabled_arms_in_order
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; every protocol phase is called in order, the transfer precedes Alice's completion, both controls run after it, and both owned processes are released at the end

- [x] D2: barrier evidence must be a validated mapping bound to run, operation and database session
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k Barrier
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 8 tests; OK; None, empty mapping, list, string and boolean all rejected; a caller-supplied boolean session and a sleep string are refused; run and operation binding, authorization/transfer/resume ordering and unsupported synchronization each covered

- [x] D3: the transfer uses valid transferor authorization and never an unguarded mutation
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k legitimate_transfer
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; Alice still holds the live lease at transfer time, so her own unchanged authority is the transferor basis; an uncommitted transfer stops the run before Alice resumes

- [x] D4: winner requests are built from resulting facts, not original fixture packets
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k winner_requests_built_from_resulting_facts
  EXPECT: test_winner_requests_built_from_resulting_facts_not_fixture_packets
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; the transfer takes the observed holder and original grant while the follow-up title takes the post-transfer holder, successor grant, rotated token and derived heartbeat

- [x] D5: the disabled comparison really executes, is independently observed, and exposes no production switch
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k disabled_comparison
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 3 tests; OK. REOPENED: the earlier evidence claimed this arm was covered, but review showed it could not execute at all because its comment-led batch was refused and zero SQL ran. It now executes its update in one builder-verified batch, confirms the stale effect by independent readback, reports executed false when it cannot run, and no disable_fence switch exists

- [x] D6: the synthetic fixture covers every table the generated SQL references
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k synthetic_fixture_covers_every_referenced_table
  EXPECT: test_synthetic_fixture_covers_every_referenced_table
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; the generated transfer joins dependencies, which the previous fixture omitted, so the synthetic schema now creates issues, leases and dependencies

- [x] D7: datetime conversion assumptions are labeled runtime-dependent with boundary coverage
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k datetime
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; no universal MySQL claim remains, fractional-second boundaries plus minute, hour, day and year rollover are covered, and a rounding runtime's heartbeat fails rather than being accommodated

## Gate E — live driver implemented but not executed

- [x] E1: no live-driver method is a placeholder or refusal stub
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k live_driver_has_no_placeholder_methods
  EXPECT: test_live_driver_has_no_placeholder_methods
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; every refusal-stub marker is gone and each driver method has a real body. Having a body is not the same as being correctly wired; gate G covers the wiring, and these methods have still never run against a live server

- [x] E2: the driver transports are exercised at the process boundary
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k LiveDriverTransport
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 24 tests; OK. REOPENED: the earlier evidence overstated coverage, because each method was tested in isolation while the connections between methods were wrong. These tests now cover argv, allowlist, batch execution, bounded capture, timeout, result shape, owned handles and the disabled arm's execution; the cross-method wiring is gate G2

- [x] E3: the driver never terminates by process name or port-wide cleanup
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k owned_handles_only
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; no taskkill, Stop-Process, killall, pkill, netstat or Get-NetTCPConnection appears in the driver, and both the server and the client are released only through their retained owned handles

- [x] E4: a failed stop blocks a successful completion label and stays visible
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k failed_stop_blocks_success_label
  EXPECT: test_failed_stop_blocks_success_label_and_stays_visible
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 1 test; OK; otherwise-passing evidence with a failed stop becomes INCONCLUSIVE with stopped false and a HARNESS_ERROR reason, and a failed release never hides an observed unsafe effect

- [x] E5: native confirmation is refused before any native side effect
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k ConfirmationRefusal
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 2 tests; OK; only the exact boolean True is accepted, and refusal happens before the driver is even constructed, so no process can start

## Gate G — review repair round (independent findings)

- [x] G1: the six further verifier false passes are all rejected through run_race
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k ReviewerVerifierCaseTests
  EXPECT: Ran 10 tests
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 10 tests; OK. Before the repair all six review cases reported PASSED through run_race; now empty grant history is GRANT_HISTORY_INCOMPLETE, a stale row in the final operations snapshot is STALE_BACKEND_SUCCESS_RECORD plus OPERATION_RECORD_DISAGREEMENT, a vanished unrelated task is ROW_LOST, disagreeing successor lease facts are GRANT_LEASE_FACTS_MISMATCH, a foreign-namespace pointer is POINTER_MISMATCH, and an unattributable refusal is REFUSAL_UNKNOWN

- [x] G2: the real driver methods are wired correctly behind fake process and SQL boundaries
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k DriverWiringTests
  EXPECT: Ran 18 tests
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 18 tests; OK. Before the repair apply_ddl refused its own schema batch, cm_observations raised a string-plus-list TypeError, run_transfer subscripted a dataclass, read_state misplaced rows across tables, positive_control reported applied true for an UNKNOWN outcome, the disabled arm ran zero SQL, and identity was observed before the sidecar existed

- [x] G3: the paused experiment is derived by the sealed backend, never supplied by the caller
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k paused_dispatch
  EXPECT: Ran 2 tests
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 2 tests; OK; the worker receives only a pause length, the batch is built inside LeaseScratchBackend from the validated request with a bounded pause of 1..30, and the ordinary protected dispatch, consumption and receipt path is shared rather than duplicated

## Gate H — real-component contract integration (second review)

- [x] H1: the driver reads the real companion completion shape, not a mock field
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k RealContractTests
  EXPECT: OK
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 7 tests; OK; before the repair completion_outcome read an observed_state field the companion never returns, so a mock supplying one reported success the real ledger never produced

- [x] H2: actual connected fresh setup, claim, race, controls and canonical uncertain verdict
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k FullSequenceOfflineTests
  EXPECT: Ran 6 tests
  CWD: memory-integrity
  EVIDENCE: REOPENED because the earlier six RealComponentIntegrationTests substitute authority/clock/consumer/snapshots and did not prove the claimed complete workflow. Closed by six new stateful FullSequenceOfflineTests, including sixteen fault subcases, using actual driver/builders/worker/consumer/retained companion/verifier. Unrelated transport failure reaches the canonical verifier as INCONCLUSIVE with only REFUSAL_UNKNOWN; native cause remains unproved. The older six component tests are retained and accurately labeled

- [x] H3: the second review's three further false passes are rejected
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_harness.py" -v -k SecondRoundVerifierCaseTests
  EXPECT: Ran 5 tests
  CWD: memory-integrity
  EVIDENCE: exit=0; cwd memory-integrity; Ran 5 tests; OK; before the repair all three reported PASSED through run_race
## Gate I — current bounded offline repair, OFFLINE-A through OFFLINE-I

- [x] I1: actual resume/run_race never treats current staleness or worker-created cause as proof
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k RefusalCausationRegressionTests
  EXPECT: Ran 3 tests
  CWD: memory-integrity
  EVIDENCE: saved red a-attribution-red.json records PASSED with no reasons for the unrelated failure; fresh saved implementation rejects it, preserves UNKNOWN and refuses worker-created attribution

- [x] I2: minted namespace is validated and bound before registration without adopting an existing store
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k NamespacePropagationRegressionTests
  EXPECT: Ran 3 tests
  CWD: memory-integrity
  EVIDENCE: missing, malformed UUID, duplicate, mismatched, already-registered and foreign bootstrap observations refuse; correct bootstrap registration uses the same namespace and selection digest. Red/green b-namespace and l-minted-namespace-shape receipts retained

- [x] I3: actual Alice operation identity survives schedule, barrier and validated worker outcome
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k OperationPropagationRegressionTests
  EXPECT: Ran 2 tests
  CWD: memory-integrity
  EVIDENCE: generated op-stale run identity replaces op-1; wrong/missing child IDs refuse; actual transfer packet/batch is retained and duplicate uncertain Alice start does not dispatch again

- [x] I4: real connected workflow has an honest uncertainty verdict and sixteen exercised fault cases
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k FullSequenceOfflineTests
  EXPECT: Ran 6 tests
  CWD: memory-integrity
  EVIDENCE: connected-evidence.json records 18 actual modeled executions: two uncertainty cases reach judge_evidence once with only REFUSAL_UNKNOWN and sixteen fault cases cannot pass. Complete producer-shaped packets and state are modeled only at native boundaries; no SQL execution proof is claimed

- [x] I5: S1 and S2 enforce shared transfer relationships and retain earlier unsafe observations
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k Transfer
  EXPECT: Ran 8 tests
  CWD: memory-integrity
  EVIDENCE: phase matrix, missing lease fields, open S1 status, wrong grant/task/pointer/deadline/history/token/operation, lost baseline claim history, contradictory duplicate rows and later receipt-read failure are rejected; original false passes have saved red receipts

- [x] I6: actual physical schema and backend/companion packet contracts are validated separately
  CHECK: python -B -m unittest discover -s tests_v2 -p "test_practical_race_offline_sequence.py" -v -k ObservationContractRegressionTests
  EXPECT: Ran 5 tests
  CWD: memory-integrity
  EVIDENCE: all nine required physical tables checked, aliases cannot replace observations, nested Beads shape consumed, WORKING_SET_APPLIED remains distinct from PRACTICAL_NATIVE_APPLIED, duplicate/missing/contradictory operation packets cannot pass

- [x] I7: broader regression differences are accounted against measured byte-verified baseline results
  CHECK: python -B docs/fable/evidence/offline-repair-20261017/verify_regressions.py
  EXPECT: BASELINE_DIFFERENCES_ACCOUNTED
  CWD: .
  EVIDENCE: four baseline/after suite pairs have identical existing failure/error/skip/expected-failure sets; MI v2 adds 27 passing regressions. Every blocked action and preservation failure is retained; B4/B5 remain unmet

- [x] I8: campaign state and traceability describe the bounded offline result and open qualification gates
  CHECK: python -B -m json.tool docs/fable/state.json
  EXPECT: OFFLINE_REPAIR_VERIFIED_NATIVE_UNVERIFIED
  CWD: .
  EVIDENCE: existing practical plan, WIP and state map OFFLINE-A through OFFLINE-I to saved implementation/tests/evidence. Parent native/release/install stages remain open and all adopted qualification flags remain false

- [x] I9: saved source and retained baseline evidence are verified without deletion or native execution
  CHECK: python -B docs/fable/evidence/offline-repair-20261017/verify_saved.py
  EXPECT: SAVED_SOURCE_VERIFIED
  CWD: .
  EVIDENCE: six acceptance-source hashes verified, all 501 arrival files retained, unrelated dirty files unchanged, no baseline definition removed, 18 connected cases non-passing and native qualification flags false

## Gate F — native execution and later release gates (separate authorization)

These have no executable offline check. They stay unmet and are not claimed.

- [ ] F1: real-Beads race, positive control and fence-disabled comparison with retained receipts bound to exact source and runtime bytes
  EVIDENCE: pending

- [ ] F2: remaining ownership, heartbeat and ABA cases on a real store
  EVIDENCE: pending

- [ ] F3: genuine in-command client interruption and owned-server crash/restart with fresh-process reconciliation and no replay
  EVIDENCE: pending

- [ ] F4: public workflow qualification
  EVIDENCE: pending

- [ ] F5: independent adversarial review of the exact diff and evidence
  EVIDENCE: REVIEW_PENDING

- [ ] F6: required regression closure and final matching skill and companion metadata and packages
  EVIDENCE: pending

- [ ] F7: clean-extracted-package verification
  EVIDENCE: pending

- [ ] F8: separately authorized commit, push and exact-commit CI
  EVIDENCE: pending

- [ ] F9: separately authorized installation plus smoke and rollback test
  EVIDENCE: pending
