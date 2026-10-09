# Project Memory routing and ownership

This reference preserves the Project Memory activity map while keeping Fable compact. Fable owns authority/state. Specialist skills provide judgment. Deterministic scripts/tools provide mechanical truth. Autonomous Operator is only the entry point. Fable Judge attacks the final claims.

## Canonical pipeline

Use this conceptual order for substantial project work:

`immutable intake -> source coverage -> authority/conflict resolution -> requirement ledger -> topic registry -> independent discovery -> required read set -> read receipt gate -> Work Compiler -> dependency DAG -> Prompt Compiler -> proof queue -> implementation/verification -> global integration -> reverse audit -> memory integrity -> Fable Judge`.

Do not rely on one giant prompt. Compile a small evidence-backed task capsule for each proof unit.

## Activity ownership

| Activity | Owner / helper | Mechanical evidence |
|---|---|---|
| User-facing end-to-end entry | `autonomous-operator` -> Fable | none; Fable owns state |
| Immutable intake journal | Fable | exact source, source identity, digest, repository/file/line metadata when applicable |
| Source coverage | Fable + `fable-judge` adversarial pass | source-span/fragment dispositions; preserve IDs, numbers, modal/negative constraints, lists/tables |
| Requirement/constraint extraction | Fable | stable IDs and provenance |
| Consequential interpretation or conflict analysis | `deep-plan` under Fable | evidence families, weakest link, cheapest falsifier, pivot |
| Authority/conflict resolution | Fable | explicit authority order; unresolved item = `CONFLICTED` |
| Domain/global invariants | `fable-domain` when a reusable adapter is needed | invariant matrix attached to affected proof units |
| Topic registry | Fable | machine-readable stable topic/document IDs |
| Open-world document discovery | Fable + optional `graphify` | graph candidates + Git + links/backlinks + lexical search + requirement IDs + symbol refs + optional semantic candidates |
| Required read set | Fable | candidate dispositions and current source identities |
| Instrumented reading | Fable | deterministic chunks; `COMPLETE`, `PARTIAL`, `TRUNCATED`, `ERROR`, `STALE` read receipt states |
| Work Compiler | Fable; `deep-plan` only for difficult decomposition | Campaign -> Milestone -> Requirement -> Proof Unit -> Verification |
| Dependency DAG | deterministic Fable mechanism | unique IDs, dependency resolution, cycle detection, parent blocking, write ownership/collision checks |
| Prompt Compiler | deterministic Fable mechanism | compact capsule: source spans, requirement atoms, dependencies, invariants, allowed writes, acceptance/tests/integration obligations |
| Proof queue execution | `fable-loop` | execute only READY, approved proof units |
| Exhaustive/deep completion discipline | optional `unlazy` under Fable | Depth Tree/four-pass review/parent reverify as advisory derived work; Fable remains authority |
| New behavior/bug fix | `test-driven-development` | RED -> GREEN -> REFACTOR |
| Unexpected failure | `systematic-debugging` | reproduction -> root cause -> one hypothesis -> verified correction; bounded retries |
| Requirement -> implementation | Fable trace subsystem | SCIP/Tree-sitter/Git or equivalent symbol evidence |
| Requirement -> consumer | Fable trace subsystem | references/call graph plus integration/runtime evidence when required |
| Requirement -> test | `fable_guard.py` | explicit requirement/criterion test IDs |
| Test -> executed code | Fable evidence layer | coverage contexts or equivalent execution mapping |
| Critical test strength | Fable evidence layer | mutation testing or another falsifier; surviving critical mutant may become `TEST_WEAK` |
| Runtime integration | Fable / `fable-loop` | replay, integration test, logs/traces/OpenTelemetry as applicable |
| Local vs composition proof | Fable | proof-unit evidence plus separate milestone/system integration proof |
| Reverse audit | deterministic Fable + `fable-judge` | requirement -> code and changed behavior -> requirement; unknown behavior = `UNACCOUNTED_BEHAVIOR` |
| Transitive invalidation | Fable guard/memory mechanism | upstream source/requirement/config changes mark dependent mappings, capsules, tests, evidence, parents `STALE` |
| Derived checkboxes/status MD | deterministic projection only | checkbox appears only from satisfied proof obligations; GPT never hand-ticks canonical status |
| Obsidian | optional `graphify`/projection; `fable-design` only for visual UX | generated Markdown/Wikilinks/graph; never canonical |
| Cleanup | Fable governance | `ACTIVE -> SUPERSEDED -> CLEANUP_CANDIDATE -> QUARANTINED -> DELETE_AUTHORIZED -> DELETED/TOMBSTONED` |
| Schema migration | Fable + TDD; debugging on failure | versioned migration + backward-compatibility tests |
| Skill package development | `skill-creator` | validate/package full Skill; not an ordinary project runtime dependency |
| Final completion attack | `fable-judge` | reproduce claims, inspect scope/tests/debris, label unverifiable layers |

## Non-success states

Use more than DONE/NOT-DONE. Relevant states include `DISCOVERED`, `CAPTURED`, `SPECIFIED`, `READ_BASIS_PROVEN`, `MAPPED`, `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `OBSERVED`, `VERIFIED`, plus `PARTIAL`, `BLOCKED`, `CONFLICTED`, `STALE`, `SUPERSEDED`, `REJECTED`, `NOT_APPLICABLE`, `UNAVAILABLE`, `INVALID`, and `TEST_WEAK` where applicable.

A parent BUILD is not green merely because every leaf is green. Require separate composition/global-invariant proof.

## Staleness and revisions

Bind evidence and task completion to the identities that make the result meaningful: requirement/source basis, repository/branch/HEAD or equivalent project identity, relevant configuration, verifier/guard version, and the exact tests/evidence definition. Source, requirement, test, policy, graph/index, or relevant configuration drift must reopen the dependent work rather than silently reusing old completion.

Mid-build user instructions become a new intake event and trigger affected-dependency analysis. Never leave an acceptance-changing instruction only in chat memory.

## Specialist availability

`unlazy`, `graphify`, GSD Core, design/domain helpers, and external tools are conditional. Use them only when actually available and appropriate. Record a precise unavailable status and continue with the Fable fallback rather than inventing their output or weakening gates.


# Standing prompt and Graphify-memory override

The standing **Universal Project Operating Prompt** at the start of `SKILL.md` replaces runtime prompt compilation. **Do not implement, create, or run a Prompt Compiler.** Keep all legacy references to `Prompt Compiler` in this file for history/compatibility, but interpret them as non-runtime conceptual language only. Do not add a `prompt_compiler.py`, prompt-ledger authority, generated-prompt state store, or another prompt-management skill. Execution uses the standing prompt plus canonical Fable state and the current required source/read basis directly.

For **Graphify-derived memory integrity**, reuse the current Graphify graph/cache first when it exists and Graphify is available. Validate repository identity, source identities/hashes, Graphify/runtime version when known, and projection freshness; then incrementally update changed or newly discovered sources instead of rebuilding unchanged material. Feed the current derived graph into candidate discovery, topic/document relationships, requirement-to-document and requirement-to-symbol candidates, consumer/call/reference paths, change-impact analysis, excluded-source reconsideration, rename/alias lineage, reverse-audit candidates, and Obsidian navigation. Graphify data accelerates recall and relationship recovery; Fable still performs authority resolution, required-read receipts, requirement capture, approval, evidence, and completion gates.
