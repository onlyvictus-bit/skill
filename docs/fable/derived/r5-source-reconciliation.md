# R5 source and historical native evidence reconciliation

Status: source/evidence reconciliation performed; original native-M7 specification and full R5 qualification remain PARTIAL.
Date: 2026-10-10. Baseline: e36cbe57190e033c862161a80b2a14868c47c3a9.
Canonical authority remains the existing requirements, plan, tests, approvals and state under docs/fable. This is a derived report for R5-RECONCILE-SOURCE/PROOF/NEXT.

## 1. Intake, source basis and limits

The user supplied Pasted text(10).txt (205 lines), M7_Source_Recovery_Manifest.json (321 lines) and M7_Recovered_Source_Passages.md (283 lines). All 809 lines were read; identities are in r5-reconciliation-evidence.json. The manifest parses and all seven passage source paths occur in its 25-file inventory.

These are the supplied recovery report, inventory and excerpts. The full M7_Library_Source_Recovery.zip, original October 3 plan bytes and the complete historical native-M7 plan were not attached. Reported source-plan hashes are provenance claims from that inventory, not independently verified original-file hashes. This milestone does not publish the private raw source-recovery files or their account identifiers.

Current GitHub main and available Git history were checked. docs/FOUR-FEATURE-PLAN.md, docs/NATIVE-QUAL-01.md and docs/R4-NATIVE.md exist; no deletion commits for them were found in the available non-shallow history. The public summary's first committed version, 6200793, already says the full text lives in the project workspace. Missing from a recovery archive does not establish deletion from Git. Full original text may have remained external; whether it was ever committed outside the checked history remains unknown.

## 2. Recovered October 3 proposal, not confirmed original native M7

Source: supplied M7_Recovered_Source_Passages.md lines 269-283, quoting the amended Memory_Integrity_Beads_Hybrid_Plan.md lines 373-381, section 13.12. The recovery inventory reports original-plan SHA-256 3f22d41ae417086b893b0de05eaf8ad0c83b1ec42125778ef949444a565312c6 and amended-plan SHA-256 e071534e30ec546331b6513f16f1d6591f1d1757ee941e9d24b98c7dbf4ddaeb. The excerpt is directly supplied; those original bytes remain unavailable here.

| Proposed case | Source condition | Required observation in that proposal |
|---|---|---|
| Missing requirement/source | Remove a required obligation or supporting source | The gap stays visible through interruption/resume and blocks final acceptance |
| Failing check | Keep a required check failed | It cannot become passed through closure, summary or resume |
| Beads closure without evidence | Close native task state without accepted proof | Closure does not satisfy the evidence obligation |
| Changed dependency after passing run | Change a dependency after earlier valid work | Stale evidence cannot qualify affected consumers; affected aggregate checks enter the repair set |

The proposal compares three configurations on the same real project slice and frozen data: current Fable+v2, compact cards only, compact cards+Beads. Model/provider, prompts, authorization scope, token budget and injected failure schedule are held constant; ground truth is declared in advance with unseen cases. Deterministic fixtures and live-provider trials are separate. No provider call is made in this milestone.

Across all four cases: interrupt and resume; preserve visibility; reject acceptance for the correct reasons; retain unaffected valid work; include affected consumers/aggregate checks in the repair set; repeat OFF mode without Beads. Measure false acceptance, missed obligations, duplicated work, stale-evidence reuse, invalidated-check coverage, recovery accuracy, steps/time to valid action, tokens/calls, latency, memory and database growth. Fewer tests alone is not a success metric. Keep baseline when even compact cards weaken/duplicate behavior; leave Beads inactive when coordination benefit is unproved or false-closure/stale/crash failures cannot be contained.

The proposal's H0-H6 structure does not establish its adoption into the original M3-M7 milestone. The four earlier reconstructed R5 candidates remain separate regression expectations, not another proven original proposal. The three synthetic consent cases are also a separate set. R5-ORIGINAL-SPEC and TEST-R5-ORIGINAL-SPEC remain open. This turn records source evidence, not exact user adoption of replacement cases; the original comparison cannot be marked complete.

## 3. Historical Windows receipts recovered from GitHub

| Scope | Run / job / commit | Artifact and downloaded ZIP SHA-256 | JSON SHA-256 |
|---|---|---|---|
| Disposable M7 pilot | 37597856215 / 112714739126 / 9fa76107f3a974bd6255ac151bd39ad97bdcaa25 | 11471297205 / 5f999ea603db1495cda26c224b65cc63a5c853ca180ef3843d07e1885520470e | 8a2c07a82f2e83be9e93183e2d8e999e98769ae5c259e8d32aaf51b64d408647 |
| Production shared-claim protocol | 37606183562 / 112742102265 / dec5229c8c7b006ec1dd24070230937112bd1357 | 11474434366 / b17d6c5d466fd72dafbc3e2731c47e37ff388e60fe4adc4a2204d6c8e475cda7 | bd1242cada22f8f8bb24794127e62f18691e5d0e3799008bba2568a8f1cc6de1 |

GitHub returned both jobs completed successfully and both artifacts unexpired at this inspection. Downloaded ZIP bytes exactly matched the returned artifact digests. Each archive contains one JSON receipt. Each receipt has eight command records, all exit 0, with exactly one update --claim record matching claim_invocations=1. Each retains native_beads_qualified=false and shared_database_authorized=false.

M7 retains UNKNOWN, NATIVE_INTENT -> NATIVE_UNKNOWN -> NATIVE_RECONCILED, RECONCILED_NATIVE_APPLIED and IDEMPOTENT_RECONCILED. Its bd.exe hash is ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4. Shared claim retains NATIVE_INTENT -> NATIVE_OUTCOME, NATIVE_APPLIED then IDEMPOTENT_NATIVE_APPLIED, and generic-native/merge qualification false. Both report CM internal-chain and projection-replay VERIFIED.

These establish availability and consistency of the retained historical receipts with successful jobs. Their JSON retains command-output hashes, not the full stdout bodies or CM database/CAS needed for independent database replay. Reported replay is not re-performed here. This recovery is not a fresh native run or proof on the user's Windows machine. No receipt in these two artifacts supplies the full four-trap comparison, native expiry/reclaim, stale-owner effect fencing or native merge qualification.

## 4. Proof correction and existing consumer path

In memory-integrity/scripts/hybrid_bridge/native_pilot.py, InterruptAfterEffect.execute calls adapter.execute(op_id, payload) and then raises InterruptedError. The returned-effect interruption is observed before reconciliation; there is no OS process-kill instruction inside that command. docs/NATIVE-QUAL-01.md previously claimed the kill/interruption-during-claim boundary was closed. That wording is corrected; its historical run/artifact identities remain intact.

Native operation path remains: explicit selection/authorization -> current observation and CM eligibility -> durable intent -> permitted effect -> readback -> outcome or UNKNOWN -> reconciliation/replay. Fable governs requirements; Memory Integrity owns the public entry; the matching claude-mon owns CM evidence/history; Beads remains the native store. No second evidence authority, new adapter, scheduler or permission ledger is introduced.

## 5. Next runnable qualification route

This Linux session has Python but no bd, PowerShell/pwsh, Wine or Go executable. No Beads installation or native mutation occurred. Two existing Windows routes are already committed:

- .github/workflows/m7-native-pilot.yml: workflow_dispatch, windows-latest, pinned v1.3.1 ZIP hash 48cd82e1d3e311c9bf9a5d6d67ad1a8542ae13d4e20c5bfb527656c5e666af76, invokes memory-integrity/scripts/m7_native_pilot.py and retains the disposable receipt.
- .github/workflows/r4-shared-claim-pilot.yml: workflow_dispatch, same pinned Windows runtime, invokes memory-integrity/scripts/r4_shared_claim_pilot.py and retains the production claim protocol receipt. Its database is disposable; it grants no standing authority elsewhere.

Both CLIs accept --bd, --expected-executable-sha256, --workspace, --receipt and --claude-mon-root. The exact CLI help was opened during reconciliation. Select a new disposable workspace and matching companion; bind the selected runtime and operation authority. Running either existing workflow again reproduces its limited claim/recovery scope, not all R5 outcomes. No dispatch API was available in the current GitHub connector; this milestone did not dispatch those native jobs.

| Next proof unit | Cheapest real probe | Acceptance / failure handling |
|---|---|---|
| Ownership/expiry/fence feasibility | Two actual actors; native lease expires and ownership is reclaimed; attempt stale-owner effect | Independently read winner/state/times; stale owner must fail at the actual effect and acceptance boundaries. A precheck alone cannot qualify fencing |
| Real native conflict feasibility | Construct divergent native branches on the pinned runtime | Prove an actual compatible merge and actual conflict; unknown ancestry, moved heads or unresolved conflict remain blocked; do not choose ours/theirs silently |
| During-command crash | Actual process kill at a recorded native-command boundary | Fresh-process readback and CM reconciliation; ambiguous application remains UNKNOWN; no blind resend or replacement operation that hides unknown delivery |
| Source-bound four-trap comparison | Recover original adoption provenance or explicitly adopt reviewed replacement; freeze three arms and cases | Keep each unsupported/native/fixture outcome separate; unchanged valid work survives; no original-M7 completion until the source/adoption requirement passes |

These require capability probes and then narrowly scoped production changes/tests if gaps are confirmed. Do not guess native APIs or label fixture outcomes as native qualification. The user's local Windows archive folder remains inaccessible from this session; this does not prevent inspecting the available GitHub receipts.

## 6. Decision, surfaces and operating limits

Minimal choice: leave the contradictory proof claim and recovery gap unchanged; rejected because it obscures the actual next test. Selected choice: recover existing receipts, preserve source provenance and correct scope in the existing control plane. Stronger choice: rewrite native coordination or add a service; deferred until feasibility proves the pinned runtime cannot supply the needed fence/conflict behavior. Weakest assumption is that the unavailable full proposal belongs to the original native-M7 acceptance contract. Cheapest falsifier is a provenance/adoption comparison with the full original plan; disagreement reopens requirements.

Cortex mapped source, proof correction and qualification handoff to nine criteria; Blueprint reviewed authority, provenance, CLI states, tests, operations and security. Both are model-executed procedures, not independent witnesses. Release Helper governs documentation publication only. Graphify runtime is unavailable; direct links, source bytes, Git history and receipt identities provide bounded discovery. Existing unrelated specialist records remain historical.

Visible states remain BLOCKED, UNKNOWN, historical scoped verification and NOT QUALIFIED where appropriate. No graphical UI changes; plain CLI help/status makes failures understandable without color. No new performance target or comparative superiority claim is made. Existing command time/output/process-tree limits remain unchanged. SQLite eligibility does not establish an atomic SQLite-Dolt fence; raw native commands remain outside wrapper enforcement. Replacing both history and its trusted checkpoint remains outside the integrity guarantee.

Release target is documentation on the existing GitHub project. Runtime files, capability flags and every release archive remain byte-identical to the baseline. No R5 package, active installation, user-host qualification or database migration is produced. Rollback is a documentation revert; native UNKNOWN recovery remains readback-only. Raw recovered receipts stay private; public records retain only artifact/commit/content identities and observed scope.

## 7. Verification and continuity

Existing native/pilot test discovery ran 28 tests: 26 passed, two platform skips. These are policy/fixture tests in this Linux session, not real Beads mutation. Both receipt archives were read and their consistency assertions passed. Plan/execute gates use current Fable digests and bounded continuation authorization. Preservation, focused documentation scope and final source mapping receive append-only manual evidence. Completion review is self-review; no independent-agent verdict is claimed.

Only this source/evidence reconciliation is ready for publication after the final checks. Original native-M7 and R5 runtime/release/install criteria remain open; historic Semantica and R4 outcomes are retained on their own bases. The next action is the real ownership/fence and native-conflict feasibility milestone on a selected pinned Windows environment, with source/adoption resolved before any original four-trap completion claim.
