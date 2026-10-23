# Gates: W worker timing and handle diagnosis

OWNS: .github/scripts/worker_diagnostic_events.py, .github/scripts/worker_lock_probe.py, .github/scripts/worker_timing_lifetime_diagnostic.py, .github/tests/test_worker_timing_lifetime_diagnostic.py, docs/fable/**

Scope: Approved isolated W1-W3 diagnosis, not worker repair or Gate1 qualification.
AUTH: user: APPROVE AND COMPLETE THE ISSUE. Existing W1-W3 spec applies.
Execution: inline/native; no automatic commits, push, workspace deletion or install.

- [x] G1: Focused observer controls execute nonvacuously and pass with retained logs.
  CHECK: "C:\Python314\python.exe" -B .github/scripts/retained_unittest.py --package-root .github/tests --test-dir . --pattern test_worker_timing_lifetime_diagnostic.py --output-dir .github/run-artifacts/offline-first-20261020/w1-final-v2
  EXPECT: OK
  EVIDENCE: observed27/27,0errors/skips/exclusions/xfails; logded81e7223b826fd6e18925ef72816e23c61941b207417c92fba1641eedaaf62; receipt0ecfe3fd65a3088caf62933a3e443c2452a7112d4a3d5124b8890586e6a76e71. Retained earlier w1-final; do not rerun either consumed path.

- [x] G2: Relevant complete controller suite passes with no concealed failures.
  CHECK: "C:\Python314\python.exe" -B .github/scripts/retained_unittest.py --package-root .github/tests --test-dir . --pattern test_*.py --output-dir .github/run-artifacts/offline-first-20261020/w1-policy-final-v2
  EXPECT: OK
  EVIDENCE: observed212/212,0errors/skips/exclusions/xfails/interruption; logd5c59e47ea606abe525ac9894864958a52737aecea29798243dd9896f5c0ec96; receiptd0ec60271049be4f5989310e11f071b6d342cc11a8a6934948c524e5fbcfc5d9. Retained earlier w1-policy-final; no repeat.

- [x] G3: Fresh independent exact-code review and parent fix verification complete.
  EVIDENCE: same configured fresh seat SHIP for corrected W1/W2 PREPARE-ONLY seal freeze; parent RED/GREEN and static all27role/template verification exit0, PS parse0. See Review-Corrections.md. No runtime/cause/repair qualification implied.

- [ ] G4: Normal-account full historical readback, controls, exactly two arms and preservation observed.
  EVIDENCE: BLOCKED. User normal Prepare failed at supplemental all-artifact inventory, WinError5 on protected agent-owned a-0ce101b0/retained-temp/tmp2f5t5rme. No Prepared/claim/selected worker. See W2-Prepare-Access-Finding.md; no retry/skip/ACL-write authority.

- [ ] G5: Results explain known observations, alternatives and remaining uncertainty without claiming a repair.
  EVIDENCE: pending; correlate actual saved events and original failures.

Ruling: Reuse Fable's approved plan/progress store instead of a second .superpowers ledger.
Ruling: Source copies and diagnostics only. Old accounting, worker policy, timeout and cleanup semantics unchanged.
Ruling: No authoritative missing history may be skipped. New first-observation maps are labelled as such.
Preflight: W1 produces event/overlay/query interfaces consumed by W2 sealed controller; W3 consumes only reviewed Prepared inputs and fixed two-arm plan. Interfaces from approved spec match.
