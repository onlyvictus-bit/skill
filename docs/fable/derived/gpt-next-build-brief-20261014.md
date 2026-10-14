# GPT Build Brief — Practical Local Fence (R5 native track)

Date: 2026-10-14. Status: WORK IN PROGRESS, NOT qualified, NOT releasable.
This file is a handoff, not proof. Nothing below claims native qualification.

## 1. Purpose (what and why)

Stale-worker protection for task coordination: if Alice holds a task, loses
ownership to Bob, then Alice's old operation must leave **zero committed
changes** — while a valid current owner always succeeds. Today the check lives
in Python (check-then-act gap) or not at all. The fence moves enforcement into
committed database transactions: compare current grant, owner, status, original
revision and live lease at authorization; mutate title plus fresh conflict
token plus operation receipt atomically; refuse everything else loudly.

## 2. Advantage and use

- **Advantage over alternatives:** reuses the pinned Beads/Dolt conflict
  mechanism (`row_lock` CAS) instead of inventing a lock service; reuses the
  companion journal instead of a second ledger; offline-testable SQL text;
  rollback is intact old packages plus append-only history.
- **Use:** disposable scratch databases only, main branch, no-dependency
  scratch path. Explicitly NOT for: shared/project databases, installed
  copies, releases, merges, replication, provider calls.
- **Non-goals until separately proven:** native merges, full M7/R5, strict
  expiry-before-save, power-loss proof, production activation.

## 3. What is finished (observed, all offline)

Branch `development/r5-practical-fence-wip-20261014`, HEAD `c6bde65`
(plus uncommitted reviewer plan appendix; unpushed — see §7):

- v2 grant schema (`mi_practical_v2_*`): grants PK, append-only history,
  metadata, token/operations uniqueness, assert procedure, no DELETE/DROP.
- Mint transitions: initial-claim, reassign (tombstone+mint), release,
  reclaim — all atomic batches with cardinality asserts and strict input
  validation. Lease snapshots stored on grant rows; namespace identity minted
  once per incarnation.
- Lease-live verification on mint paths; read-only heartbeat guard
  (no mutation, no fallback re-arm); strict `<` expiry equality refusal;
  spelling-mismatch refusal at the contract boundary.
- Tests: 22/22 in `test_practical_v2_schema.py` (21 pass + 1 documented
  dolt-ignore gap); full Memory Integrity suite 427 tests with ONLY the
  pre-existing known set (1 unfinished-integration failure + 10 unfinished
  consumer/CLI errors + by-design manifest staleness). Companion journal 10/10.
- Backend entry points still raise STOPPED. All qualification flags false.
- Dolt v2.4.2 windows-amd64 ZIP downloaded and hash-verified
  (`sha256:317526a9…659564e8d`, 40,184,586 bytes) at
  `C:\Users\sakth\AppData\Local\Temp\opencode\`. dolt.exe runs
  (`dolt version 2.4.2`). **Critical:** `dolt init` fails on this host in
  every directory with `FileSystem.access` — native proof is environment-
  blocked here, not design-blocked. No workaround was attempted.

## 4. Settled design decisions (do not relitigate without new evidence)

- Currency = equality-with-current-state (expected vs stored grant/row_lock),
  NOT numeric ordering. Ordered counters are rejected: Dolt merges identical
  concurrent cell updates silently, so counters can lose increments.
- Grant IDs are caller-proposed, database-enforced (PK collision refuses).
- Equality at the deadline refuses (`<`, never `<=`); grace/sync margins are
  deployment doctrine, not a substitute boundary.
- The strict expiry-before-save contract stays unsatisfied and labeled so;
  this work proceeds under the explicitly adopted practical contract.
- Tombstones, never deletes, in v2 tables. Native lease-row removal on claim
  end is a Beads invariant that CONFLICTS with no-deletion: release/unclaim/
  reclaim are BLOCKED pending explicit narrow permission (see plan §lease
  retirement). Do not tombstone-and-pretend.

## 5. Next steps, in order (first unfinished item is next)

1. **dolt_ignore proof** (marked `expectedFailure` in tests): verify the real
   ignore mechanism from the pinned source; never emit a guessed procedure.
2. **Fence-disabled live control**: run the fenced batch and the identical
   batch with fence predicates stripped against a WORKING database; the
   stripped batch must authorize a stale request the fenced batch refuses.
3. **Native lease-mint wiring**: bind transitions to real lease rows
   (DB-minted 300s expiry, namespace identity read back, heartbeat/ABA/
   spelling/foreign cases).
4. **Scratch proof ladder** (needs a host where `dolt init` works — this host
   is proven unable): synchronized old-owner-vs-new-grant race with positive
   and disabled controls, ABA replay, client-kill and server-crash recovery
   with fresh-process readback and zero second writes.
5. **Consumer/CLI integration** (closes the 11 known failures), independent
   review, manifests regen at final, packaging, push, CI — each separately
   approved. **Do not begin public CLI wiring or packaging before 1–4 pass.**

## 6. Hard constraints (violations stop the work immediately)

- No file/data deletion, no history rewrites, no releases/SKILL/capability
  edits, no installs, no pushes/merges without separate human approval.
- `docs/fable/derived/practical-fence-plan.md` contains another reviewer's
  uncommitted +227 appendix — read it, never rewrite or rebase it away.
- `ledger.py` is the journal worker's surface; fable JSON is the parent's.
  Stay in `practical_*` modules and their tests.
- Tests must fail first (TDD), assert generated text/shape/binding (never
  live behavior from offline runs), and keep the known-failure set byte-
  identical unless the fix is the documented unfinished work.
- Publish negative results (REFUTED stays published). Never weaken a check,
  mock a runtime, or relabel this WIP as qualified.

## 7. Key locations and pins

- Work tree: `C:/Users/sakth/Documents/Codex/2026-10-02/ad/work/R5-practical-fence-20261013/source-git` (branch above).
- Builders: `memory-integrity/scripts/hybrid_bridge/practical_lease_sql.py`
  (schema, transitions, heartbeat guard). Contract + stopped backend:
  `practical_contract.py`, `practical_backend.py`. Tests:
  `memory-integrity/tests_v2/test_practical_v2_schema.py`.
- Decisions/record: `docs/fable/derived/practical-fence-plan.md` (+227
  reviewer appendix), `practical-fence-contract.json`,
  `practical-resume-20261014.md`, `docs/changes/2026-10-14-practical-fence-wip.md`.
- Pins: Beads v1.3.1 commit `c1c4b642…`; `bd.exe` sha `ac5b6011…`;
  Dolt v2.4.2 + digest above. `dolt_executable` in backend selections MUST
  be a Dolt binary (it speaks `sql-server` protocol: `--host/--port/
  --use-db/--branch` + `sql -r json`), never `bd.exe`.
- Verify with: `python -B -m unittest tests_v2.test_practical_v2_schema`
  (expect 17 pass + 1 expectedFailure) from `memory-integrity/`.
