# Native probe changes and sequential publication record

Recorded: 2026-10-11 (Asia/Calcutta). Repository: [onlyvictus-bit/skill](https://github.com/onlyvictus-bit/skill).

This is a detailed change record derived from Git and retained observations. The authoritative requirements, approvals, state and typed evidence remain in `docs/fable/`. This note does not grant authority or replace those records.

## Scope and exact Git basis

The native probe change spans baseline `ea8c01b7fc4c49b50833879fa387cb7967b9283c` through published commit [`f4af9ae5dbf47fb2b687b27937a1b415ff14643d`](https://github.com/onlyvictus-bit/skill/commit/f4af9ae5dbf47fb2b687b27937a1b415ff14643d). Its final tree is `713159510289a9f8cf7bbcc6b3ac21125395b8bb`. The inventory below contains all 22 added/updated paths in that range. No files were deleted.

Both installable packages (`memory-integrity/`, `claude-mon/`) and `release/` remained byte-identical to the baseline. The probe is repository tooling and evidence; it is not an installed-skill upgrade or a completed R5 package release.

## What was added and where

| Change | Exact repository path | Purpose |
|---|---|---|
| Added | `.github/scripts/r5_native_probe_helper.go` | Probe-only Go helper using exact upstream Beads APIs and one pinned SQL connection; selects real source branches, initializes ignored local tables, commits title edits and restores main. |
| Added | `.github/scripts/r5_native_probes.py` | Disposable experiment runner and strict raw-receipt verifier: claim race, actual five-minute expiry, reclaim, guarded writes, ABA cycle, compatible merge and same-cell conflict. |
| Added | `.github/tests/test_r5_native_probes.py` | Twelve new regression tests covering signed revision tokens, malformed or forged receipts, exact task/owner guards, reclaim binding and expiry comparisons. Combined repository suite has 19 tests. |
| Added | `.github/workflows/r5-native-probes.yml` | Development-branch-only Windows native workflow; pins released Beads binary/archive and source revision, builds the helper, runs experiments and retains/reopens the receipt. |
| Updated | `docs/STATUS.md` | Updates the capability summary with observed probe results, refuted fencing guarantees and explicit unfinished release work. |
| Updated | `docs/fable/approvals.json` | Appends actual continuing user authorization for the bounded probes and recovery changes; preserves historical approval rows. |
| Added | `docs/fable/derived/r5-native-probes-evidence.json` | Derived manifest binding run, artifact and receipt identities, command references, failed attempts and false qualification/authority flags. |
| Added | `docs/fable/derived/r5-native-probes.md` | Design, recovery history, measured results, root causes, independent reviews, CI limits and production handoff. |
| Updated | `docs/fable/evidence/index.json` | Appends identifiers for the three typed, scoped completion receipts; preserves prior evidence identifiers. |
| Added | `docs/fable/evidence/native/r5-native-probes-blocked-38062363017.json` | Unmodified failed native attempt: harness rejected a valid negative signed revision token. Never counted as completed native evidence. |
| Added | `docs/fable/evidence/native/r5-native-probes-blocked-38062595748.json` | Unmodified failed native attempt: pooled SQL sessions lost selected-branch state. Never counted as completion. |
| Added | `docs/fable/evidence/native/r5-native-probes-blocked-38063260511.json` | Unmodified failed native attempt: ignored source-branch lease table was missing. Never counted as completion. |
| Added | `docs/fable/evidence/native/r5-real-native-probes.json` | Unmodified successful Windows receipt containing 60 indexed native command transcripts, exact readbacks and negative guarantees. |
| Added | `docs/fable/evidence/runs/20261011T122922280278Z-a563f911.json` | Typed Fable passing evidence for R5-PROBE-EXPIRY: experiments complete while automatic expiry/generation guarantees are refuted. |
| Added | `docs/fable/evidence/runs/20261011T122922379115Z-3dabd8cd.json` | Typed Fable passing evidence for R5-PROBE-MERGE: compatible merge and scoped real-conflict refusal observations. |
| Added | `docs/fable/evidence/runs/20261011T122922479256Z-d25ac008.json` | Typed Fable passing evidence for R5-PROBE-BOUNDARY: pinned identity, reopened raw evidence, independent review and unchanged packages. |
| Added | `docs/fable/intake-r5-native-probes.txt` | Retains the exact user request and bounded disposable experiment scope. |
| Updated | `docs/fable/plan.json` | Adds the native-probe task, actual implementation/evidence paths and bounded verification/publication sequence. |
| Updated | `docs/fable/requirements.json` | Adds R5-PROBE-EXPIRY, R5-PROBE-MERGE and R5-PROBE-BOUNDARY criteria without marking broad native capabilities qualified. |
| Updated | `docs/fable/specialists.json` | Records selected specialist outputs and updated hashes; preserves historical mappings. |
| Updated | `docs/fable/state.json` | Marks only the three scoped probe requirements complete alongside existing history; retains unfinished production fencing/release handoff. |
| Updated | `docs/fable/tests.json` | Adds TEST-R5-PROBE-EXPIRY, TEST-R5-PROBE-MERGE and TEST-R5-PROBE-BOUNDARY mappings. |

## Existing commits, preserved in order

| Commit | What that commit added or repaired |
|---|---|
| `cc07c47415e3e3b18fd6b94b5c3fb01d16ad8bc2` | Initial native harness/helper, workflow, tests and bounded Fable records. |
| `03cb1cd2ff988a2618e669ffc5b25a8afe01a713` | Signed nonzero int64 revision support and stronger command/evidence binding. |
| `44125e59d54ad820758251d90b63a6d1347541a5` | Pinned native SQL connection so branch checkout survives the driver's pooled-session reset behavior. |
| `0bd04d11bc6d71902d0f654d46d1f37c79c42afa` | Native ignored-schema initialization without modifying ownership leases or tracked branch HEAD. This exact code ran the successful native experiment. |
| `f4af9ae5dbf47fb2b687b27937a1b415ff14643d` | Detailed results, complete raw and BLOCKED receipts, derived manifest, typed scoped evidence and current status. |

These commits were already published before the new one-commit-at-a-time instruction. Their history is preserved. No amend, squash, reset or force push is used to rewrite them.

## Real observations and proof

The successful native run is [38063816470](https://github.com/onlyvictus-bit/skill/actions/runs/38063816470), at `0bd04d11bc6d71902d0f654d46d1f37c79c42afa`, using pinned Beads v1.3.1 source `c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c` on Windows CI. It is not an execution on the user's PC.

| Experiment | Observed outcome | Meaning |
|---|---|---|
| Competing overlapping claim processes | Exactly one winner; native already-claimed refusal for the loser | Native claim race observed on the disposable task. |
| Actual lease expiry/reclaim | 302.1957938 seconds elapsed; zero live claims reclaimed before expiry, exactly the expired task reclaimed afterward | Real native TTL/reclaim behavior observed without clock, TTL or timestamp manipulation. |
| Old owner after ownership changed | Conditional write exits 13; complete issue and native HEAD unchanged | Changed-owner assignee/status guard works in this case. |
| Expired owner before reclaim | Conditional title write succeeds after lease expiry | Automatic expiry fencing REFUTED. |
| Same actor regains ownership (ABA) | New signed revision differs; old actor/status guard write succeeds | Generation fencing REFUTED. |
| Compatible native merge | New native commit contains both histories and both title changes | Actual compatible merge observed. |
| Same-cell native conflict | Exit 1, native Error 1105/autocommit rollback; no resolution attempted | Observed HEAD, exports, status and source preserved; no remaining conflicts. |

Raw receipt SHA-256: `a92afa231fefb09699cb0c4ce650632e3c66ead33b8310433736b01a43b73daf`.
Downloaded artifact ZIP SHA-256, matched against GitHub's digest: `613ad966014f304f17c9d6224f429f57c86eb6719c8e532d5c1f13a1171c3e87`.
Released bd.exe SHA-256: `ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4`.

The downloaded Windows receipts retain their original CRLF bytes. The GitHub tree was checked against the local tree before publication; upload preparation was corrected before pushing to avoid newline normalization and hash changes.

Root and two independent reviewers reopened and verified the 60-command receipt. All 19 repository tests passed. Root rejected ten receipt-falsification variants; each reviewer rejected six. These are attack/review counts, not additional unique test counts.

## Final results from CI on f4af9ae

| Workflow | Exact run | Result |
|---|---|---|
| Regular repository CI | [38139635493](https://github.com/onlyvictus-bit/skill/actions/runs/38139635493) | All eight Windows/Ubuntu Python 3.11–3.14 jobs passed. |
| Optional pinned Semantica runtime | [38139635552](https://github.com/onlyvictus-bit/skill/actions/runs/38139635552) | Ubuntu 3.12/3.13 and Windows 3.13 passed; Windows 3.12 failed. This workflow is not all-green. |

The Windows 3.12 failure is job `114470636158`: the extracted knowledge-package suite has one error in `test_public_advanced_modes_source_closure_and_replay`, vector/distributed-local replay. Its worker reports `PermissionError: [WinError 32]` because a temporary `output` file remains in use. Earlier development-run failures directly traced to `DistributedSession.close()` cleanup in unchanged package code. The current worker error is consistent with that file-lifetime problem; it does not independently establish which process still owns the handle. No cleanup fix or full-release pass is claimed by this documentation change.

Earlier development optional run `38063819524` had two Ubuntu passes and two Windows cleanup failures. The original probe report/manifest preserves that historical result; this note adds the final-main observation without changing old evidence.

## Still unfinished

- Atomic current-lease and generation checks at the actual production effect/acceptance boundary. Actor/status matching alone is insufficient.
- Diagnosis and repair of the Windows distributed worker file-lifetime/cleanup failure, then fresh package verification.
- Broader R5 qualification: current dependency evidence, during-command OS-kill recovery, original four-trap comparison/adoption, full native merge policy, matching release packages and installed-copy promotion.

`native_beads_qualified`, `native_fencing_qualified`, `native_merge_qualified` and `shared_database_authorized` remain false in the probe receipt. A completed experiment is not a passing guarantee or standing shared-database authority.

## This documentation commit

Only these three paths change in this new commit:

| Path | Change |
|---|---|
| `docs/changes/2026-10-11-native-probes.md` | Adds this full path inventory, ordered commit history, proof, final CI result, remaining work and push procedure. |
| `CHANGELOG.md` | Adds a dated native-probe entry linking to this detailed record. |
| `CONTRIBUTING.md` | Adds the requested one-commit-at-a-time publication and per-change documentation rule. |

Commit message: `docs(native-probes): record file inventory and sequential push policy`.
The new commit has exactly one parent: the current remote `main` head `f4af9ae5dbf47fb2b687b27937a1b415ff14643d`. Its own SHA cannot be embedded inside its own content; obtain it with `git log -1 --format=%H -- docs/changes/2026-10-11-native-probes.md` or the GitHub file history.

Publication uses the existing `development/r5-native-probes` branch first, then promotes the same single commit to `main` under the user's explicit push instruction. Each branch update advances by exactly one commit. Recheck each remote head immediately before updating it, require the expected old SHA, use a fast-forward update with force disabled, and reopen the resulting commit/tree/files. Stop and reconcile if a remote head changed; never overwrite newer work.

This commit changes documentation only. Validate Markdown links, exact inventory against Git, clean diff and the one-parent/one-new-commit range. Runtime tests are not rerun solely for this documentation edit. Any CI run triggered by the new push is a new observation and must not be represented as the already completed f4af9ae runs above.
