# Qualification status

R4 / 2.0.0-m12 is the formal successor candidate to the R3/m11 offline pair.
R3 release archives remain unchanged for rollback and audit history.

## R4 native capability boundary

| Capability | R4 status | Evidence / limit |
|---|---|---|
| Read-only native observation | QUALIFIED for pinned v1.3.1 selection | Exact executable/project/database identity, complete issue/dependency observation, strict diagnostics |
| Durable native journal/recovery | QUALIFIED within observed pilot scope | CM journal and after-effect interruption reconciliation; OS kill inside the claim remains unverified |
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

## Generated formal pair

Release builder run 37606792629 generated and verified the formal pair and
committed it as 71a90d2e02cee5baca3e6716fed03df2f8408edd.
The release manifest records memory-integrity-r4.zip SHA-256
888d435b4fb5a2eac3d8e14ac783c40399b0d473aee676ff164189b08d87bc6a
and claude-mon-r4.zip SHA-256
5cf842c5e02c05e3e34069090a7d00e05d8eee250701fb786eaa638b3e6bba57.

## R5 step-1 planning record (2026-10-10)

The missing M7/R5 requirements freeze is now recorded in the existing Fable
control plane. See [the recovered basis and boundaries](fable/derived/r5-step1.md)
and [acceptance mappings](fable/derived/r5-acceptance-matrix.md).
Planning records are constructed; original-specification recovery remains
PARTIAL. The exact historical four-trap comparison was not recovered; four
source-reconstructed candidates are explicitly provisional. That gap blocks
claiming the original M7 comparison complete.

Ownership/expiry fencing, real conflicting native merge and OS kill inside a
native claim remain UNVERIFIED. The current pilot injects interruption after
the native effect returns; it does not establish the during-command kill case.
R5 runtime qualification, package release and installed promotion are not
complete. Existing R4/knowledge packages and capability flags are unchanged.

## Source/evidence reconciliation (2026-10-10)

The supplied recovery excerpts identify an October 3 four-case proposal:
missing requirement/source, failing check, Beads closure without evidence and a
changed dependency after a passing run. The original native-M7 grouping remains
unconfirmed; no original-comparison or R5 qualification pass is declared.

Historical CI receipt archives for runs 37597856215 and 37606183562 were recovered
from GitHub and their ZIP SHA-256 values matched the artifact digests. Receipt
commands/events and scope were inspected. These are retained historical results,
not new native executions, independent database replay or proof on the user host.
The source correction and concrete next probes are in
[the reconciliation report](fable/derived/r5-source-reconciliation.md).
