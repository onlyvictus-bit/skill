# Qualification status

R4 / 2.0.0-m12 is the formal successor candidate to the R3/m11 offline pair.
R3 release archives remain unchanged for rollback and audit history.

## R4 native capability boundary

| Capability | R4 status | Evidence / limit |
|---|---|---|
| Read-only native observation | QUALIFIED for pinned v1.3.1 selection | Exact executable/project/database identity, complete issue/dependency observation, strict diagnostics |
| Durable native journal/recovery | QUALIFIED | CM NATIVE_INTENT/OUTCOME/UNKNOWN/RECONCILED, exactly-once recovery |
| Shared-project claim protocol | QUALIFIED | Run 37606183562: production adapter, one claim, readonly readback, idempotent repeat, CM chain/replay VERIFIED |
| Generic native writes | NOT QUALIFIED | No create/close/delete/arbitrary update authority |
| Native merge | NOT QUALIFIED | Fixture policy exists; real conflicting native merge is not a release claim |
| Shared database standing authority | NONE | Every real claim requires an exact current per-operation authorization |
| Live AI/provider execution | NOT QUALIFIED | Separate approval and evidence required |

R4 deliberately keeps native_beads_qualified=false. The truthful release-level
capability is native_shared_claim_protocol_qualified=true, with
generic_native_write_qualified=false and native_merge_qualified=false.

## Shared-claim proof

GitHub Actions run 37606183562 executed the production SharedNativeClaimAdapter
against pinned Beads v1.3.1 on windows-latest. The retained receipt observed:

- exactly one bd update <id> --claim;
- readonly bd show readback proving the selected actor/state;
- CM NATIVE_INTENT -> NATIVE_OUTCOME;
- second invocation returned IDEMPOTENT_NATIVE_APPLIED without another claim;
- CM internal history chain VERIFIED;
- CM projection replay VERIFIED;
- generic native and native merge qualification remained false.

Protocol qualification does not authorize another project. An actual shared
workspace needs a fresh NativeSelection, current observation, current companion
dispatch guard and exact SHARED_PROJECT_CLAIM authorization bound to selection
digest, operation ID, work-item ID, native task ID and actor.

## Release packaging gate

The formal R4 release is a matching two-package pair: memory-integrity m12 and
claude-mon m12. The release builder regenerates each R4-CONTENT manifest, creates
both ZIPs, creates the R4 release manifest, runs the portable verifier against
the extracted pair, and then the normal Windows/Ubuntu Python 3.11-3.14 matrix
must pass on the generated commit before promotion to main.

Installed-copy replacement is separate from repository release promotion.
