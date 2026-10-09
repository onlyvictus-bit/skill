# GSD Core integration

Use GSD Core as a subordinate engine, never as a second governor.

## Verified capability boundary

GSD Core v1.14.0 documents a researcher -> planner -> plan-checker workflow, requirement-ID coverage checks, plan verification, state/session operations, and project health/consistency checks. These capabilities are useful for planning and continuity.

Fable adds controls that must remain authoritative: exact approval binding, atomized acceptance-criteria coverage, artifact-bound fresh evidence, and final completion gating.

## Authority model

1. `docs/fable/` is canonical.
2. GSD `.planning/` files, when used, are generated working inputs or mirrors. Never let `.planning/` silently replace Fable requirements, approvals, state, or evidence.
3. Convert canonical Fable requirements into the format GSD needs. After GSD planning/checking, import accepted tasks back into `docs/fable/plan.json` and run the Fable plan gate again.
4. Fable approval is required after the final imported plan is stable. GSD plan acceptance is not user approval.
5. GSD execution summaries are evidence leads, not completion proof. Fable's evidence and completion gates still run.

## Runtime procedure

- First detect whether the installed GSD runtime and its expected researcher/planner/checker roles are actually callable.
- If available, use the runtime-supported phase-planning flow and its checker. Use GSD state/session tooling for continuity where helpful.
- Run available GSD structural/health checks such as plan-structure, consistency, and state checks when they materially add coverage.
- If agent dispatch reports an unknown role, the CLI is absent, or installation is unavailable, record `GSD_UNAVAILABLE` with the observed reason. Fall back to Fable planning and deterministic enforcement. Never represent a source-code capability audit as a successful runtime GSD check.

## Avoid duplicate machinery

Do not rebuild a custom researcher/planner/checker merely because Fable can. Reuse GSD when its runtime is available and the capability is demonstrated.

Do not add StrictDoc by default. Fable's requirement/criterion/test mappings already provide deterministic traceability for the pilot. Add a heavier requirements system only if a real-project test demonstrates a remaining traceability need that this contract cannot represent economically.
