# Qualification status

The released R3/m11 pair remains the verified offline baseline. The
`development/m7-completion` branch adds guarded M7 native-observation,
durable native-operation recovery and a disposable exactly-once pilot, but it
is not a promoted successor release and does not authorize shared/project
native writes.

## Offline baseline: R3 / m11

The matching release pair has retained offline verification of 383 packaged
tests. Its 79 Memory Integrity and 65 claude-mon content-manifest entries were
hash-checked again for the publication copy; each package also contains its
content manifest. Release ZIP bytes remain unchanged.

During publication preparation on 2026-10-06, the portable verifier was rerun
on those exact copied archives: all 383 tests passed, with `TEST_ONLY`
evidence and native qualification false. That baseline remains intact.

## Development: M7 completion branch

The development branch now contains these additional M7 layers:

| Feature | Implemented / verified repository boundary | Remaining boundary |
|---|---|---|
| Native read observation | Pinned v1.3.1 executable/project/database checks; full issue/dependency enumeration; repeated head/info/export reads; strict diagnostics and capture evidence | Fresh host receipt for the exact current disposable selection |
| Process containment | Windows Job Object / taskkill fallback and POSIX process-group timeout containment; clean non-job exits explicitly unverified/unproven | Host-specific residual behavior remains receipt-scoped |
| Blocked work / prerequisites | Existing CM dependency guards plus a native wrapper that derives `guard(..., "dispatch")` internally before intent | Shared/project execution remains disabled until separately qualified |
| Durable native journal | CM `NATIVE_INTENT`, `NATIVE_OUTCOME`, `NATIVE_UNKNOWN`, `NATIVE_RECONCILED`; immutable operation/work-item/command/selection binding | Real host pilot must supply native readback evidence |
| Interruption recovery | Tests inject interruption after effect, reopen CM, reconcile by readback only, require no second write, and require idempotent repeat recovery | Native host observation still required; ambiguous readback remains UNKNOWN |
| Disposable pilot | One-command helper verifies SHA + pinned build before init, uses explicit `BEADS_DIR` and git-free stealth init, creates one disposable task and exercises exactly-one claim recovery | Scope is `DISPOSABLE_PILOT`; it does not qualify shared databases |
| Branch merging | Compatible/conflicting deterministic fixture policy, retained origins/CAS and stale-head refusal; prior disposable compatible native merge observation exists | Conflicting native merge and post-merge native evidence revalidation still require direct observation |
| Release | R4 content manifests track development files and existing R3 archives remain unchanged | Successor ZIPs/promotion/install require separate release approval |

### Repository verification

A full GitHub Actions matrix for commit
`0d73d82d0a603be295bce4266998ba6b706763c7` completed successfully across
Ubuntu and Windows, Python 3.11–3.14, after the durable M7 journal and
cross-platform containment fix. A later full matrix at
`cb5c48b46b44ab8bdc8aff613aba7894649983b7` also completed successfully
after adding the disposable pilot adapter/helpers and refreshing the R4
manifest. Later guard/CLI/version-pin changes remain subject to the final
current-head matrix before release claims are made.

The prior Ubuntu failure was a contract wording mismatch: tests required the
receipt to include `unverified` while the non-Windows clean-exit path emitted
only `containment unproven`. It now reports
`containment unverified/unproven` without upgrading the proof claim.

The durable native-operation tests prove the core exactly-once orchestration
invariant:

> after a durable intent, recovery either proves one native effect by readback
> or stays UNKNOWN; it never blindly repeats the native write.

The public/native wrapper does not trust a caller-provided guard result. It
calls the matching companion coordination guard itself; a blocked guard
produces no native intent and no native adapter call.

## Disposable host pilot

The development skill exposes:

```text
python scripts/m7_native_pilot.py \
  --bd <absolute-bd.exe> \
  --expected-executable-sha256 <64-hex-sha256> \
  --workspace <absolute-new-disposable-workspace> \
  --receipt <absolute-new-receipt.json> \
  --claude-mon-root <matching-companion>
```

The command refuses an existing workspace/receipt, verifies the selected
binary SHA and pinned Beads v1.3.1/commit before initialization, then uses
explicit `BEADS_DIR` with `init --quiet --stealth`. It creates only a
disposable pilot task, issues exactly one claim, injects an interruption after
the claim effect, reopens CM, and reconciles by readonly native state.

A successful receipt reports
`overall=M7_DISPOSABLE_PILOT_VERIFIED` and
`pilot_native_write_observed=true` while deliberately retaining
`native_beads_qualified=false`, `shared_database_authorized=false` and
`installed_promoted=false`.

## Still required before a final native successor

1. Run the current one-command pilot against the exact selected Windows
   `bd.exe`/disposable workspace and retain its receipt. If the agent sandbox
   cannot launch the binary, this is the one host-only action the user may
   need to execute.
2. Observe the remaining native branch-conflict/merge boundary if full native
   merge qualification is required; never substitute fixture success for that
   observation.
3. Perform an independent/adversarial final review of the current head and
   fresh full regression matrix.
4. Build matching successor metadata/manifests/ZIPs only after those gates.
5. Merge/promote/install/replace the released or installed pair only with
   separate authorization.

No live AI call, shared database mutation, installation, global skill
promotion, or released R3 archive replacement is performed merely by this
development work.

## Public-consent clarification

Approval from another project or a pasted historical receipt grants no
current-environment authority. A verified approval for an unchanged exact
readonly selection may be retained without duplicate questioning. A
disposable-pilot approval is limited to that selected disposable environment;
failure never authorizes initialization or mutation elsewhere.
