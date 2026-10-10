# Native qualification observations — disposable TEMP DB (this session)

Date: 2026-10-06. bd.exe v1.3.1 pinned (`ac5b6011…`), embedded Dolt,
disposable `bd-qual2` database. Removed after observation.

## Init hazards (observed, not theorized)
- `bd init` without cwd discipline initialized the *shell* directory: git
  repo + hooks + AGENTS.md + `.beads` + gate locks landed in TEMP root and
  had to be removed by hand. Never auto-init; always pin cwd first.
- `bd init --skip-agents --skip-hooks` still creates a git repo; its final
  git commit warns (exit 128, no git identity in sandbox) while the Dolt
  database itself initializes fine. Init success ≠ git commit success.
- Nonexistent `-C` target fails cleanly; `--sandbox/--readonly` semantics
  verified on reads.

## Lifecycle round-trip (disposable DB)
- create → dep add → dep cycles clean → claim → close: all exit 0.
- Claiming a *blocked* issue succeeds natively (IN_PROGRESS + lease).
  Native state never enforces prerequisites: blocked-work fencing must live
  in the adapter (R3 design confirmed, not contradicted).
- Compatible branch create + merge: exit 0, heads advance. Conflicting
  merge is untested natively: `bd vc merge` with `--strategy ours|theirs`
  exists upstream, but setting up divergent branches still needs a checkout
  path this CLI surface does not expose; covered by R2/R3 fixture tests only.
- Crash: SIGKILL-equivalent mid-batch (Stop-Process -Force at count 22 of
  200) → counts stable, vc clean, history intact, no lock errors; probe
  batch removed afterwards with `--force` delete.

## Concurrency (two real processes, distinct actors)
- `racer-1` vs `racer-2` claiming one issue: exactly one winner.
  Loser: "issue already claimed by racer-1". Assignee bound to winner,
  lease ~4 min. Single-winner holds natively; stale-lease/reclaim and
  kill-during-claim remain unobserved.

## Still not observed
Conflicting native merge, kill-during-claim recovery, reclaim/expiry
timing, server-mode behavior, live provider calls.


## 2026-10-07 M7 exactly-once claim recovery — REAL NATIVE GREEN

GitHub Actions run `37597856215`, job `112714739126`, on
`development/m7-completion@9fa76107f3a974bd6255ac151bd39ad97bdcaa25`
completed successfully on `windows-latest` with the official Beads v1.3.1
Windows AMD64 release asset. The workflow verified the published release ZIP
SHA-256 before extraction and then verified the extracted `bd.exe` as
`ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4`.

The retained artifact is `m7-native-pilot-receipt`, artifact
`11471297205`, artifact digest
`sha256:5f999ea603db1495cda26c224b65cc63a5c853ca180ef3843d07e1885520470e`.

Observed real command sequence included:
- pinned readonly `version`;
- isolated launcher `git init --quiet` and local
  `git config beads.role maintainer`;
- external disposable `BEADS_DIR` initialization with
  `init --quiet --stealth`;
- readonly `info`;
- one disposable task `create`;
- exactly one native `update <id> --claim`;
- readonly `show <id>` for recovery.

The receipt proves:
- `claim_invocations=1`;
- interruption result `UNKNOWN`;
- journal sequence exactly
  `NATIVE_INTENT -> NATIVE_UNKNOWN -> NATIVE_RECONCILED`;
- recovery `RECONCILED_NATIVE_APPLIED`;
- second recovery `IDEMPOTENT_RECONCILED`;
- recovered task remained `in_progress`, assigned to
  `memory-integrity-pilot`;
- CM internal hash chain `VERIFIED`;
- CM projection replay `VERIFIED`;
- `pilot_native_write_observed=true`.

The receipt deliberately retains:
`native_beads_qualified=false`,
`shared_database_authorized=false`, and
`installed_promoted=false`.
This is disposable-environment native qualification only, not authority to
mutate a shared/project database.

This observes reconciliation after an injected interruption following a returned
native claim effect. The pilot calls `adapter.execute(...)` before raising
`InterruptedError`; it does not kill the OS process inside the native claim.
Kill-during-command recovery and conflicting native branch merge remain separate
unobserved boundaries.

The two retained historical Windows receipt archives were recovered and checked
again on 2026-10-10. See the [source and evidence reconciliation](fable/derived/r5-source-reconciliation.md)
for exact artifact/receipt identities and the remaining qualification gaps.
