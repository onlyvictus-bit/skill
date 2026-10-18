# Practical Fence — Next Build Handoff (give this to GPT)

> **Status:** specification, not a report. Nothing here is an authorization.
> **Repo:** `C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git`
> **Branch:** `development/r5-practical-fence-wip-20261014`
> **HEAD:** `c6bde65` — `wip(native-fence): lease-live verification and heartbeat guard, offline-tested`
> **Never pushed. Never merged.**

---

## 1. Purpose — what this system is for

This repo ships a **memory-integrity** skill plus a **claude-mon** companion that enforce one rule: **no claimed completion without evidence.**

When a coding agent says "done," the system refuses to believe it. It independently opens the artifacts, re-runs the checks, and refuses a claim when any of these is true:

1. a required source file was never actually opened,
2. a named check does not exist or does not fail as described,
3. a closure claim has no receipt, log, or artifact behind it,
4. a dependency changed *after* the last passing run, so the passing run no longer describes the current tree.

The `practical fence` branch is the **native** half of that system. Today the skill can audit *offline* work. This branch adds the ability to fence **real mutation** on a live database — so that when an agent performs an approved native change, the system can prove afterwards that exactly the intended change happened, to exactly the intended owner, and that nobody else could act on a stale belief in between.

**The word "fence" is literal.** It prevents a second worker from writing based on a grant that is no longer true.

---

## 2. Advantage — why this design

| Design choice | Advantage | What it costs |
|---|---|---|
| **Current-binding equality, not an ordered counter** | No sequence number to allocate, no counter to drift, no wraparound. Two workers cannot both hold "the current grant." | Requires storing full lease snapshots per grant |
| **Never-reused grant IDs** | An old applied event can never be mistaken for the current truth. | Grants accumulate; needs history retention |
| **No `DELETE`/`DROP`/`DOLT_ADD`/`DOLT_COMMIT` in the fence path** | The fence observes and authorizes. It never writes history itself, so it cannot become the thing it audits. | Cannot compact; history grows |
| **Heartbeat is read-only** | A heartbeat can never be the event that re-arms a dead grant. | Requires a separate live-lease query |
| **DB-clock liveness, strict before-expiry** | One clock (the DB's), no host clock skew. Equality refuses, so no boundary is guessed. | Needs a live server to prove |
| **Fail closed on `E_PRACTICAL_*`** | Every unresolved condition refuses rather than proceeds. | More refusals than a permissive design |

**Rejected alternatives, one line each:**
- **Ordered grant counter** — simpler to reason about, but needs a trusted allocator and still does not prove *liveness* (a holder can be dead but hold the highest counter).
- **Optimistic `expected_status` only** — the original design. Fails under ABA: A→B→A leaves a stale holder's belief looking valid. R5 native probes **refuted** both `automatic_expiry_fence` and `generation_fence` on this basis.
- **Host clock instead of DB clock** — no server dependency, but every agent's clock skew becomes a correctness input.

---

## 3. Use — operational runbook (pinned, exact)

### 3.1 Pinned runtimes

| Artifact | Version | Identity | Status |
|---|---|---|---|
| Dolt | `v2.4.2`, `windows-amd64` | zip `dolt-windows-amd64.zip`, 40,184,586 bytes, SHA-256 `317526a94f6c50f5beab1b0638af0c019dbc32162c9b3ca01c370ac659564e8d` | **Downloaded + verified.** At `C:\Users\sakth\AppData\Local\Temp\opencode\dolt-windows-amd64.zip` |
| Dolt binary | `dolt.exe` from that zip | extracted to `C:\Users\sakth\AppData\Local\Temp\opencode\dolt-v2.4.2\dolt-windows-amd64\bin\dolt.exe` | `dolt version` → `2.4.2` ✅ |
| Beads | `v1.3.1` | resolves to commit `c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c`; `bd.exe` SHA-256 `ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4` | **NOT downloaded.** Download needs its own authorization |

### 3.2 Which binary is `dolt_executable`? — SETTLED BY CODE

**`dolt_executable` must be `dolt.exe`, NOT `bd.exe`.** Proven from `memory-integrity/scripts/hybrid_bridge/practical_backend.py:123-131`:

```
<dolt_executable> --host 127.0.0.1 --port <port> --no-tls \
                  --use-db <database> --branch <main_branch> \
                  sql -r json -q <SQL>
```

This is the **Dolt SQL client speaking to a `dolt sql-server`**, not the Beads CLI. The two binaries are not interchangeable. Do not substitute one for the other.

### 3.3 Topology

1. `dolt init --name <name> --email <email>` in a scratch directory (must be inside the approved root).
2. `dolt sql-server` listening on `127.0.0.1:<free port>`, `--no-tls`.
3. Backend connects per-invocation with the argv above; every call is a **new process**, so the fence must be re-evaluated on every call, never cached.

### 3.4 Test harness — this is `unittest`, **not** `pytest`

`pytest` fails with `ModuleNotFoundError: No module named 'tests_v2'`. The correct commands, run from the `memory-integrity` directory:

```powershell
python -B -m unittest discover -s tests_v2 -p "test_practical_v2_schema.py"   # focused
python -B -m unittest discover -s tests_v2                                      # full MI
```

CI uses `python -B -m unittest discover -s tests_v2` (`.github/workflows/ci.yml:28`).

---

## 4. Hard constraints — do not violate

1. **Never delete files or data.** The fence path contains no `DELETE`, `DROP`, `DOLT_ADD`, or `DOLT_COMMIT`. Preserve this.
2. **`docs/fable/` is the only governance control plane.** No external agent, reviewer, or skill output may override it.
3. **Commit, push, merge, deploy, download, install, and native DB mutation each need the user's own words.** A README saying "must push after this" is documentation, never authorization.
4. **Native qualification flags stay `false`** — `native_beads_qualified`, `native_fencing_qualified`, `native_merge_qualified`, `shared_database_authorized` — until live evidence exists for the exact head.
5. **Never weaken a test to make it pass.** Never fabricate the artifact a test looks for.
6. **Report failures as failures,** with output. An honest blocker is a successful outcome.
7. **Pin the working directory first;** use external `BEADS_DIR`; `bd init --quiet --stealth`. Never let a shell-directory auto-init trigger.
8. **Approved scratch root (only this):** `C:/Users/sakth/memory-integrity-practical-fence-20261013`. Enforced in `practical_backend.py` `APPROVED_SCRATCH_ROOTS`. Anything else raises `E_PRACTICAL_SCRATCH_ROOT`.

---

## 5. What is finished

### 5.1 Git history — 4 commits on this branch, never pushed

| Commit | Contents |
|---|---|
| `adbbe1b` | 25-file unqualified checkpoint, **0 deletions** |
| `58a737a` | v2 grant schema + initial/reassign/release/reclaim SQL builders |
| `6a272b3` | P1a schema/query correspondence, lease-bound minting, namespace identity |
| `c6bde65` | live-lease verification, mutation-free heartbeat guard |

### 5.2 Implemented and offline-tested

`memory-integrity/scripts/hybrid_bridge/practical_lease_sql.py` (21,555 bytes) contains:
- tables `mi_practical_v2_grants`, grant history, metadata, token history, operations, `mi_practical_assert_v2`
- initial / reassign / release / reclaim builders
- lease columns `lease_node`, `lease_granted_at`, `lease_expiry`, `lease_heartbeat`
- initial + reassign verify holder, node, all timestamps, and strict DB-clock liveness
- `verify_heartbeat_sql` — pure read, no mutation, no fallback re-arm

**Verified result:**
```
Ran 22 tests in 0.040s
OK (expected failures=1)
```
The one expected failure is the deliberate live `dolt_ignore` proof gap.

### 5.3 Separately completed (other branch, `C:\Users\sakth\AppData\Local\Temp\skill-phase0`)

G03–G13 Victus implementation, 12 commits ending `7632e7c`; same-head suite **544 passed, 34 environmental skips**; portable verifier green; release manifest and ZIP hashes matched. Governance closure is still open (stale approval digests).

### 5.4 Independent audit (remote `development/r5-native-probes` @ `0bd04d11bc6d`)

- 4 ahead / 0 behind `main`, 12 paths, 0 deletions; core trees unchanged.
- 120/120 verified stream hashes.
- **`automatic_expiry_fence: REFUTED`**
- **`generation_fence: REFUTED`**
- Merge held: exact-head Windows cleanup error + incomplete Fable closure.

---

## 6. Verified current baseline

Full MI suite, observed on this exact HEAD:

```
Ran 427 tests in 143.113s
FAILED (failures=2, errors=10, skipped=50, expected failures=1)
```

### 6.1 Root cause of all 12 — measured, not assumed

**The 10 errors are NOT 10 missing features. Nine are stale test fixtures sitting behind a contract that got stricter. Exactly one feature is genuinely unbuilt.**

| Group | Count | Exact cause | Kind |
|---|---|---|---|
| `test_practical_consumer.py` | 7 errors | `E_PRACTICAL_SELECTION_SCHEMA` — the test's `SELECTION` fixture supplies **9 of the 10** contract fields; **`native_node_id` is missing** (added by `58a737a`/`6a272b3`) | fixture drift |
| `test_practical_backend.py` | 2 errors | `E_PRACTICAL_LEASE_REVISION_REQUIRED` — requests built without the lease-revision precondition added by `c6bde65` | fixture drift |
| `test_practical_cli.py` | 1 error + 1 failure | `practical-title` **subcommand does not exist at all**; CLI emits no JSON | **REAL MISSING FEATURE** |
| `test_preservation.py` | 1 failure | manifest drift `capabilities-v2.json` vs `SKILL.md` — by design, pending regeneration | deferred |

Contract fields confirmed by import:
```
candidate_route, database, dolt_executable, dolt_sha256, host,
incarnation, main_branch, native_node_id, port, scratch_root
```
Fixture confirmed by read — 9 fields, `native_node_id` absent.

CLI absence confirmed by the argparse usage string, which lists every subcommand and contains no `practical-*` route.

**This reframes the work:** 9 of 12 failures are mechanical, offline, and unblockable right now. One is a real build. One is deferred by design.

---

## 7. Environment blocker — measured

**`dolt init` cannot initialize a repository anywhere on this host.**

Attempted in 4 distinct locations — the approved scratch root, a Temp directory, a Documents directory, and a git-seeded directory. Every attempt returned identically:

```
NotFound: FileSystem.access (<path>)
```

`dolt version` works. `dolt init` does not. This is a host/binary incompatibility, not a design defect, and it matches this project's history of Windows-only native failures (WinError 5 on the scratch root, WinError 32 in CI cleanup).

**Do not attempt to work around this** by elevating, shimming, disabling AV, or hand-fabricating repository internals — each is outside authorization and one step from manufacturing evidence.

All probe debris was removed. The verified ZIP is retained.

---

## 8. Next build plan — ordered

Work these in order. Each has an explicit gate. **Stop at any gate that fails and report.**

### P1 — Repair the 9 stale fixtures *(offline, no runtime, do first)*

**Why first:** it is mechanical, it needs nothing external, and it converts 9 red into 9 green, which makes every later failure legible.

**Files:** `memory-integrity/tests_v2/test_practical_consumer.py`, `test_practical_backend.py` — tests only. Do **not** weaken `practical_contract.py` to accommodate a test.

1. Add `"native_node_id": "<a stable test identity>"` to the `SELECTION` fixture in `test_practical_consumer.py`. Check `test_practical_backend.py:32` for the value already in use there and match it.
2. In `test_practical_backend.py`, supply the lease-revision precondition at lines ~250 and ~264 so the two tests exercise the *new* contract rather than the superseded one.
3. Re-run the focused files.

**Gate:** `python -B -m unittest discover -s tests_v2 -p "test_practical_consumer.py"` → 7 tests OK; `-p "test_practical_backend.py"` → OK. Full-suite errors drop **10 → 1**.

**Caution:** repairing a fixture must not weaken the assertion it feeds. If a test's *intent* is unclear, read the contract first; a test that cannot be satisfied without weakening the fence is a finding, not a task.

### P2 — Build the missing CLI route *(offline, no runtime)*

**Why:** this is the only genuinely unbuilt feature. Two of the twelve failures are here.

1. Add `practical-title` (and the read-only recovery routes) to the facade in `memory-integrity/scripts/memory_integrity_workflow.py`, matching the style of the existing 27 subcommands.
2. Emit **JSON** on every path, including the fail-closed path. `test_candidate_fails_closed_on_missing_input_without_native_proof` expects parseable JSON when input is missing.
3. Keep it a **facade only** — it must never re-implement the engine or copy its ledger.

**Gate:** `test_practical_cli.py` fully OK. It must produce JSON for both the happy path and the refusal path.

### P3 — Resolve the no-deletion conflict *(decision, not code — escalate)*

**This needs the user. Do not decide it unilaterally.**

Pinned Beads **deletes the active lease row when a claim ends.** The v2 fence path contains no `DELETE`. Therefore `release`, `unclaim`, and `reclaim` **cannot be proven natively** under the current no-deletion rule.

Present exactly three options:
- **(a)** grant narrowly scoped permission for lease-row deletion in the scratch DB only, and record the exception;
- **(b)** keep `release`/`unclaim`/`reclaim` permanently offline-only and prove only initial-grant + heartbeat natively;
- **(c)** redesign the grant lifecycle to end without deleting the row (e.g. closed-state column).

Do **not** tombstone the row and report it as a delete. That is exactly the kind of silent substitution this system exists to catch.

### P4 — Compat probe *(needs a working Dolt host)*

**Blocked on §7.** Run only after the host can `dolt init`.

1. Apply the full v2 DDL against a real `dolt sql-server`.
2. Prove `mi_practical_assert_v2` exists and executes.
3. **Determine whether the new v2 tables are `dolt_ignore`d.** This is the one live `expectedFailure`. If they are **not** ignored, they will appear in `dolt status` and can leak into commits — which would violate constraint 1.
4. Confirm Dolt `v2.4.2` is compatible with Beads' embedded driver `github.com/dolthub/driver/v2 v2.2.0`. v2.4.2 postdates it; if incompatible, that invalidates this pin and needs a fresh download authorization.

**Gate:** DDL applies, assert proc runs, ignore-status known and recorded.

### P5 — Native proof ladder *(needs P3 decision + working host)*

Each rung must pass. Any failure stops the ladder and is reported with output.

1. positive valid-owner control
2. fence-disabled stale-write **control** — *this is the test that the fence is load-bearing; if a stale write succeeds, the fence is not doing anything*
3. race: two holders, only the current one may write
4. reassignment
5. expiry / reclaim
6. heartbeat (prove it cannot re-arm a dead grant)
7. **ABA**: A→B→A, and A's original belief must still be refused
8. spelling / foreign identity mismatch
9. client interruption mid-write
10. server crash mid-write
11. fresh-process **readback-only** recovery

**Gate:** all rungs pass on the exact head, with receipts.

### P6 — Closure

Fable governance update, independent review, manifest regeneration (clears the `test_preservation` failure), exact-head CI, then **request** commit and push authorization. Do not push unasked.

---

## 9. Definition of done

- All 12 current failures resolved: 9 fixtures, 2 CLI, 1 manifest — or each remaining one explicitly and honestly reported as deferred with a reason.
- Full MI suite green, or green minus named, justified environmental skips.
- **No** test weakened. **No** flag flipped without live evidence. **No** claim made that is not backed by an artifact you actually produced.
- Every outward action carries the user's own words behind it.

---

## 10. Files to open first

| Path | Why |
|---|---|
| `memory-integrity/scripts/hybrid_bridge/practical_lease_sql.py` | the v2 fence itself |
| `memory-integrity/scripts/hybrid_bridge/practical_contract.py` | exact fields, error codes, the 10-field selection |
| `memory-integrity/scripts/hybrid_bridge/practical_backend.py` | transport argv, scratch-root fence, hash check |
| `memory-integrity/tests_v2/test_practical_v2_schema.py` | the 22 green tests |
| `memory-integrity/tests_v2/test_practical_consumer.py` | the missing `native_node_id` fixture |
| `memory-integrity/tests_v2/test_practical_backend.py` | lease-revision precondition gaps |
| `memory-integrity/tests_v2/test_practical_cli.py` | the missing CLI route |
| `memory-integrity/scripts/memory_integrity_workflow.py` | where the CLI subcommands are declared |
| `docs/fable/derived/practical-fence-plan.md` | the P1–P5 reviewer's +227-line plan (uncommitted) |
| `docs/fable/derived/practical-fence-contract.json` | the adopted contract |
| `docs/fable/derived/practical-resume-20261014.md` | the live integration + deletion-boundary record |
| `.github/workflows/ci.yml` | the real test invocation |

---

## 11. Honesty rules for whoever builds this

1. **A blocker is a success if reported as a blocker.** Do not manufacture progress.
2. **Never edit a test to match a broken implementation.** Find the intent first — the contract, the docstring, the reviewer plan — then make code, test, and spec agree. If they cannot all agree, surface the disagreement.
3. **Never soften `dolt_ignore` handling.** It stays an `expectedFailure` until proven live. A silently-passing ignore test is worse than a red one.
4. **Report the exact command and its output** for every verification claim.
5. **When something surprises you, stop and say so.** A surprise is the most valuable thing you will find.

---

## HISTORICAL / SUPERSEDED — 2026-10-18

The original 17,991 bytes above are retained unchanged as historical evidence
(SHA-256 of that original prefix: 1dc09c0129af24a4fb162ac6d61dcf98127d207f5ea2b44655e94f2eb4019332).
They are NOT current build instructions. Use the latest dated entry in
`docs/fable/derived/practical-resume-20261014.md`, the existing practical plan
and `docs/fable/state.json` for current routing. Never treat this original
handoff, its test counts, runtime recommendations or next-step sequence as
current authority.

Material corrections: the protected SQL writes grant/operation history while
CM owns its separate existing audit journal; Beads v1.3.1 is present and its
pinned binary hash was verified; the candidate selects Dolt v2.4.1, not an
implicit v2.4.2 switch; adding native_node_id alone cannot activate the stopped
v1 consumer. A lease-v2 backend and internal consumer now exist but the public
commands remain preflight-only. In the disabled comparison an unsafe stale
effect is the required counterfactual, not evidence that the enabled fence
failed. Only an enabled-arm stale committed effect refutes that candidate.

The 2026-10-18 successor retains original command diagnostics in protected CM
UNKNOWN events and reads them independently. It deliberately does not turn
error text or those diagnostic packets into native refusal/success proof.
Native causation, real grammar/rollback/race, independent review, release and
installed verification remain open. No native test or activation follows from
this archival correction.
