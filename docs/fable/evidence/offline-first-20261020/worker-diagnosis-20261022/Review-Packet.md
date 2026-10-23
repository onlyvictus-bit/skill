# W1 diagnostic implementation — fresh review request

AUTH: user APPROVE AND COMPLETE THE ISSUE, then continue from where you stoped.
Scope W1-W3 DIAGNOSIS ONLY. This review is of W1 implementation before freezing
the W2 normal-account handoff. No new runtime/Prepare/Run command is issued yet.

Spec: docs/fable/derived/offline-first-release-design-20261020.md section W.
Plan: docs/fable/derived/offline-first-release-plan-20261020.md W1-W3.
Ledger: this directory/GATES.md, existing main progress/checkpoint/state.
HEAD and BASE remain923de16c91a9ef4381e7ac975e3a3780f42a4bf5. Dirty files predate
this slice; use exact files below, not git HEAD..HEAD (these are untracked).

New code snapshots:
- .github/scripts/worker_diagnostic_events.py F128FEA4A4B00BD897987CF4D33256CA1CB121B2DF72935639BF6131F5C6707B
- .github/scripts/worker_lock_probe.py F3DDAE8615797BB9A3E453F222D987EF2FE369CF97C82DFCA57344D9CAFF5979
- .github/scripts/worker_timing_lifetime_diagnostic.py 2D6033D69705423BAA194C6328C648720E718EE89DB4E931E87413B156E0B46C
- .github/tests/test_worker_timing_lifetime_diagnostic.py 7DF121C7F34B1A3F534673DF0001189E1C0870F3D36A9A63E932DE666C9972C0

Original product source, runtime, tests and closed accounting not edited. Entry
hashes in Entry-Baseline.json. Accounting tests/driver remain exactly recorded.

Implementation: diagnostic-only hash-bound AST copies; one stdlib event module
in observed copy only, bounded new sidecars, query-only native Restart Manager,
known-holder versus separately released-holder fixture, fixed two-arm controller,
full original historical checks, explicit archived-code transition for the old
V3 driver replaced by the closed accounting repair. No generic trust override.

Rulings for review:
1. Existing Fable store replaces skill-default .superpowers ledger/commits/deletion.
2. Semantic AST removal is a static check, not runtime equivalence proof; actual
   small _process Popen success/error is also executed, no selected numerical run.
3. Old V3 contract helper path legitimately contains repaired accounting now.
   Preserve original contract and verify exact historical bytes in consumed-v3
   archive, with current driver independently pinned. Do not skip arbitrary rows.
4. Raw capture means existing outer streams plus sidecars; no intrusive reading
   or copying baseline internal temporary streams before cleanup.
5. Unfinished child phases are INCOMPLETE, not cause-proven or a repaired worker.

Observed evidence:
- w1-red-01:11 expected missing-implementation failures,0errors/skips.
- w1-green-01: two AST anchor/reversal errors, retained; corrected in green02.
- w1-red-02: bad observer path replaced work error; fixed, original error retained.
- w1-green-03: advanced strategy anchor matched validation as well as dispatch;
  tightened to the exact community equality; green04 13/13.
- w1-red-03: six missing-controller failures; green05 19/19.
- w1-red-04: copy scope missing and concurrent query/main capture ambiguity;
  narrow fixes; green06 21/21,0errors/skips/exclusions/expectedfailures.
- .github/run-artifacts/offline-first-20261020/w1-policy-01/Receipt.json:
  206/206,0errors/skips/exclusions/expectedfailures/interruption; log SHA
  00c84405e30af39abf9bb47e273441c7ca946044f8fc2aa3f2d1a677a16df5cc.
Retained negative synthetic packets printed by older tests are not aggregate errors.

Review Focus (from plan, verbatim): wrong SID/runtime or replaced/linked input;
inaccessible old data; missing/out-of-order/overflow/exception telemetry; PID
reuse/unknown holder; observer-created handle or timing perturbation; mixed
FAIL/ERROR must not PASS.

Check full end-to-end controller feasibility too, not only unit greenness.
In particular assess observer quota versus real distributed lifecycle, exact
seal/schema/role closure, history transitions, bounded process/handle cleanup,
sampler/capture synchronization and filename confinement. External seals and
PowerShell handoff have not been generated; that remaining W2 work is explicit,
not an implemented capability. Do not qualify an unbuilt handoff.

Independent review must be read-only. No selected interpreter, old command,
normal Prepare/Run, native RM/control process, install, network/model/API,
security/permission action, Git write or deletion of old data. No subagents.
Report severity/file:line/effect and SHIP/FIX-FIRST for W1; enumerate all declined
behavior. No actual worker or whole-Gate1/release/installed qualification.
