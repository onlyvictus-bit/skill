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
  merge has no native CLI path (no checkout/switch): untested natively,
  covered by R2/R3 fixture tests only.
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
