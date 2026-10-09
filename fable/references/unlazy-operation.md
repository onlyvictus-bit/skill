# Unlazy: completion depth with a real runner

Read [the original Unlazy skill](specialists/unlazy/SKILL.md), its [security contract](specialists/unlazy/SECURITY.md), and [gate grammar](specialists/unlazy/references/gates.md). For orchestration/depth work also read its method/orchestration references; for parallel work read parallel.md first. All scripts, libraries, templates, tests, and original supporting files are bundled intact.

## Input

Use approved Fable requirement/criterion IDs, proof-unit dependencies, allowed file ownership, intended outputs/consumers, exact acceptance checks and parent integration obligations. Do not invent a second plan authority.

## Procedure

1. Build a derived Depth Tree from accepted outcomes. Split until each leaf is a coherent independently testable deliverable; keep branch integration and regression checks separate. Map every leaf/branch to Fable IDs and planned paths.
2. Copy the bundled leaf/node templates into approved derived output locations and replace every example with a real check. Each runnable gate needs ID, observable outcome, CHECK, EXPECT and evidence. Manual checks need an actual observation; never hand-tick pending evidence.
3. Perform all four passes: complete the deliverable, inspect it as a domain expert, hunt correctness/integration/portability/performance/evidence defects, then polish and repeat until another review finds no actionable gap. Record fixes and limitations, not private reasoning.
4. Parse the ledger without execution: `node <fable>/references/specialists/unlazy/scripts/gate-check.mjs --status <ledger>`.
5. Inspect each CHECK, called script, working directory, shell and expected output. CHECK is arbitrary shell code. Fable approval is not arbitrary command approval. Keep checks sequential unless independence is proven.
6. Configure `UNLAZY_APPROVAL_DIR` to an explicitly permitted directory outside the target repository when avoiding the default home write. Run the reviewed approved checks with `node <runner> --root <project> --cwd <project> --approve <ledger>`. Runtime approval records are execution controls, not Fable project truth.
7. Independently rerun completed leaf checks using `--reverify`, inspect decisive outputs, then rerun parent integration checks. A green child does not prove its parent. Re-read invoked scripts after changes even if command text is unchanged; the native approval does not hash transitive dependencies.
8. Import observations and surviving findings into canonical Fable evidence using its normal typed evidence workflow. Keep ledgers derived. Recompute measured met/unmet/abandoned counts before reporting.

## Failure handling

Nonzero exit, wrong expected output, timeout, missing tools, malformed/empty ledgers, duplicate IDs and absent evidence are failure or pending, never success. `ABANDON: ID reason` preserves an impossible gate visibly; it is not completion of a required outcome. Bound repeated no-progress attempts and report the blocker. Do not install the optional Claude Stop hook unless explicitly authorized. Its host-specific hook is not Codex enforcement.

## Verification

Use a disposable local ledger that checks a real fixture file. Prove: pending status does not execute; approved check reads and validates the fixture; changing the fixture breaks `--reverify`; parent remains incomplete while a child check fails. Run the shipped native tests when their environment and side effects are suitable. The new package tests exercise these behaviors without global hook installation.
