# Disposable real native expiry and conflict probes

User scope: Finish complete real expiry/fencing and native-conflict probes.

Done means retained real pinned Windows Beads commands, actual five-minute lease expiry without clock/timestamp/TTL overrides, independently reopened results, native compatible merge and same-cell conflict, with negative guarantees reported as REFUTED rather than qualified. Shared databases, installed skills, production activation, original four-trap adoption, and full R5 release remain outside this probe scope.

## Observed completion (2026-10-10)

The real experiments are complete; full native fencing is unqualified. Windows Actions [run 38063816470](https://github.com/onlyvictus-bit/skill/actions/runs/38063816470) succeeded at code commit `0bd04d11bc6d71902d0f654d46d1f37c79c42afa`. Root and two independent reviewers reopened the retained 60-command receipt and verified command identity, hashes, chronology and actual readbacks. All 19 repository tests pass; root rejected ten falsification variants and each reviewer rejected six. These counts describe separate attacks and repeated verification, not additional unique tests.

| Experiment | Observed result | Limit |
|---|---|---|
| Competing real claim processes | One winner; overlapping distinct processes; loser reports already claimed | Disposable selected task only |
| Live lease reclaim | Zero reclaimed before expiry | Native default TTL is unchanged |
| Real expiry and reclaim | 302.1957938 seconds elapsed; exactly the expired task reclaimed | No fake clock, TTL override or timestamp rewrite |
| Expired owner conditional write before reclaim | Write succeeded | Automatic expiry fencing **REFUTED** |
| Changed-owner conditional write | Exit 13 guard mismatch; full issue and HEAD unchanged | Assignee/status conditional fence observed |
| ABA ownership cycle | Different signed revision; old actor/status guard write succeeded | Generation fencing **REFUTED** |
| Compatible native merge | New commit contains source/target ancestry and both title changes | Released CLI merge; helper authors real source branch |
| Same-cell native conflict | Exit 1, native Error 1105/autocommit rollback; no resolution | HEAD, full exports/status and source preserved; no remaining conflicts |

Receipt SHA-256: `a92afa231fefb09699cb0c4ce650632e3c66ead33b8310433736b01a43b73daf`. Downloaded artifact ZIP SHA-256 matched GitHub's digest: `613ad966014f304f17c9d6224f429f57c86eb6719c8e532d5c1f13a1171c3e87`. The [evidence manifest](r5-native-probes-evidence.json) records pinned identities, operation references, artifact/run IDs, exact results and all three BLOCKED receipts; the [complete raw receipt](../evidence/native/r5-real-native-probes.json) is retained byte-for-byte in Git.

The helper's pinned connection and native schema initializer preserved branch HEAD and initialized empty ignored leases. No ownership lease was manufactured. This is a new Windows CI execution, not a test on the user's PC. The 60 commands were byte/hash-verified and their summaries/readbacks examined; no human line-by-line reading of every encoded transcript byte is claimed.

Repository CI run 38063816437 passed all eight Windows/Ubuntu Python3.11–3.14 jobs at the exact probe code commit. Optional Semantica run 38063819524 passed both Ubuntu jobs; both Windows jobs passed 178 checkout runtime tests but failed extracted-package cleanup with WinError32 in the unchanged DistributedSession.close temporary output handling. That separate package defect remains unresolved in this bounded probe change; a clean full release is not claimed. Final publication CI is assessed on the final GitHub commit separately.

The next production requirement is an atomic current-lease and generation comparison at the actual effect/acceptance boundary. Actor/status guards alone cannot provide it. Shared database authority, generic native write promotion, full native merge qualification, original four-trap adoption, during-command OS kill recovery, R5 package release and installed-copy promotion remain unfinished. All four receipt qualification/authority flags stay false.

TWINS: checked both original/new revision validation sites and repository revision guards; both harness sites accept signed nonzero int64 tokens. Branch operations were inspected together and now use the same pinned native SQL connection. Ignored-schema initialization applies to every source-branch operation. Existing package code and tests were not weakened or changed.

## Decision and design

Use the pinned released bd.exe for claims, expiry/reclaim, guarded writes and merges. Build a probe-only helper from exact upstream c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c to select real embedded branches. The v1.3.1 CLI has no branch checkout and embedded bd sql refuses, so CLI-only divergent branch construction is unavailable. Fixture-only claims cannot prove native expiry; editing lease timestamps or shortening the TTL would not prove real expiry. A production fencing redesign before observing the gap would expand scope prematurely.

Cortex: source evidence, native commands, and retained readback are distinct evidence families; artifact hashes bind observations. Blueprint: outcome is bounded probes; actors are disposable owner A/B; front door is a qualification CLI; state is isolated .beads; effects are native title changes and branch merges; boundaries require fresh workspace and pinned binary/helper; failures preserve BLOCKED receipts; verification reopens rows/heads and hashes every transcript; handoff retains false generic qualification flags. Weak link is helper CGO/branch feasibility: build and branch roundtrip precede the five-minute wait. GSD/Graphify/Unlazy runtime is not needed for this bounded harness; no successful invocation is claimed.

Scope: .github/scripts/r5_native_probes.py, .github/scripts/r5_native_probe_helper.go, .github/tests/test_r5_native_probes.py, .github/workflows/r5-native-probes.yml, docs/fable intake/requirements/plan/tests/approvals/state/specialists/evidence, this report and docs/STATUS.md. Both installed skill packages and release archives remain byte-identical.

Checklist: establish strict verifier tests RED; implement bounded raw capture and fresh-workspace guard; build exact source helper; test genuine branch ancestry/compatible merge/conflict; wait real lease expiry and test pre/post reclaim and actor ABA; retain failures and successful experiments without promoting refuted guarantees; adversarial review; publish exact reviewed tree and verify exact-head CI.

Risks: native expiry alone may not fence ordinary field edits; assignee/status CAS may not fence ABA. A successful experiment is not a successful guarantee. Merge errors may leave a working set: inspect and report partial effects, never automatically resolve or import accepted proof. Receipt production flags always remain false.

## Historical runtime recovery observations (superseded by the completed run below)

Run 38062363017 (cc07c474) stopped on a harness bug: valid negative signed int64 revision tokens were rejected. The actual receipt records revision -9219145960942753114 and remains BLOCKED. Signed-token regression tests now pass. Run 38062595748 (03cb1cd2) stopped before expiry on native branch read selecting main. Root cause is driver/v2 v2.2.0 conn.go IsValid returning false and ResetSession returning ErrBadConn: pooled sessions are discarded between setup and operations. The probe helper now acquires one native SQL connection, reapplies USE and checkout, uses pinned Beads issueops/versioncontrolops on that connection, and restores main. Separate released-CLI readback checks main did not move. No upstream or installed runtime code was modified. At that checkpoint the next real run was pending; neither failed receipt counts as complete native expiry/conflict evidence.

Independent review found and repaired summary-only receipt verification, an overly broad conflict classifier, incomplete partial-effect checks, missing signed-token support and missing operation binding. Meaningful regressions were observed failing before repair; current 19 repository tests pass. Retained verification now reconstructs command-indexed pinned identity, exact issue/actor/guard bindings, chronology, lease expiry/reclaim, title effects, divergent heads/native history, full export/status and actual native conflict diagnostics. Generic native, native fencing and native merge qualification remain false.

Run 38063260511 (44125e59) selected the source branch correctly, then stopped on its missing native leases table. These tables are deliberately dolt_ignored and absent from committed branch history. The helper now invokes Beads' own schema.MigrateUp on the selected pinned source connection, retains pre/post initialization HEAD equality and an empty source lease count, and refuses tracked-head movement or unexpected source leases. No lease fixtures, clock overrides, shortened TTLs or timestamp rewrites are used. The ownership database is separate and its lease is untouched by source-branch initialization. This failed run remains BLOCKED; at that checkpoint final real native results remained pending.
