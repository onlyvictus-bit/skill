# Specialist routing

Fable is the governor. Specialists contribute reasoning, execution structure, depth, discovery, design, domain knowledge, or verification; they do not own approvals or project truth. `docs/fable/` stays the single canonical control plane.

## Core routes

- `fable-method`: base evidence/intent/act/observe/report discipline when its explicit method is useful; consume it inside Fable rather than creating another governor.
- `deep-plan`: consequential mechanism choice, alternatives, evidence-family independence, weakest link, cheapest falsifier, pivot condition. Use as reasoning engine only.
- `fable-loop`: non-trivial plan -> execute -> verify orchestration inside the approved Fable scope. Do not nest it inside an already orchestrated GSD phase.
- `fable-judge`: independent adversarial verification of completion claims. Prefer it before consequential completion.
- `test-driven-development`: new behavior, bug fixes, and refactors where executable tests are possible. Test first, observe RED, then implement.
- `systematic-debugging`: failures, regressions, unexpected behavior, build/test/runtime issues. Establish root cause before fixing.

## Project-memory and completion specialists

- `unlazy`: optional completion-depth specialist for exhaustive/multi-part/previously incomplete work. Use the integration contract in `references/unlazy-integration.md`; reuse Depth Tree/four-pass/reverify discipline but keep Unlazy state derived/advisory. Record `UNLAZY_UNAVAILABLE` when it cannot be invoked and use the Fable fallback.
- `graphify`: optional open-world discovery and knowledge-graph specialist for large code/doc corpora and Obsidian projections. Use `references/graphify-integration.md`; graphs are derived candidate maps, not authority or read-completeness proof. Record `GRAPHIFY_UNAVAILABLE` when unavailable and use direct discovery mechanisms.

## Domain and design routes

- `fable-design`: optional UI/UX/design-system specialist; Fable retains requirements, approvals, state, and evidence.
- `fable-domain`: create or improve reusable domain adapters when the user explicitly asks for domain skillization or a persistent invariant adapter.
- `skill-creator`: development-time only when creating/updating/package-validating the Fable/Autonomous Operator Skill bundles; not an ordinary project runtime dependency.

## Optional GSD Core

GSD Core may assist research, planning, plan checking, execution workflow, or continuity only through `references/gsd-integration.md`. Its runtime must be proven available. GSD planning/output is subordinate to the canonical Fable records and gates.

## Domain routing

Use domain-specific evidence and verification when available, but never weaken Fable gates. Examples: design requires rendered/interactive inspection, data work requires provenance and malformed-input checks, devops requires live-state/rollback evidence, research requires source coverage and date/version checks.

## Optional runtime roles

Use native or external roles only when the runtime proves they exist and their invocation does not create a new approval, worktree, cost, or state authority without user authorization. Missing roles are a capability gap, not a reason to invent their output.


## Standing-prompt and memory-integrity clarification

- The standing Universal Project Operating Prompt in Fable is always active for project work. Do not create or run a Prompt Compiler specialist or script.
- When available, `graphify` is the preferred derived relationship-memory substrate for substantial/long-running repositories: reopen and incrementally refresh its existing graph/cache before starting discovery from zero. Its data feeds Fable memory-integrity discovery and trace candidates only; Fable retains canonical authority and all proof gates.


## Six bundled specialists

Read `six-specialist-operation.md` and the matching `*-operation.md` adapter before invoking a bundled specialist. Full source is in `specialists/<name>/SKILL.md`, relative to this reference directory. Cortex supplies routing; Blueprint supplies design completeness; Triangulate supplies independent-family evaluation; Unlazy supplies completion depth; Graphify supplies derived discovery; Release Helper supplies release readiness and verified deployment after authorization. Register every selection or justified non-selection in `docs/fable/specialists.json` and run the new specialist gate wrapper.
