# Contributing

Isolated, evidence-first contributions only. Read `README.md`,
`docs/STATUS.md`, and `docs/FOUR-FEATURE-PLAN.md` before changing behavior.
Native/Beads milestones and acceptance gates live in that plan summary.

1. Preserve byte-identity: staged originals, SKILL.md prefixes (append-only),
   and release manifests. Never weaken a test or fixture to get green.
2. New/changed behavior needs reason-specific regression tests run from the
   owning package root: `python -B -m unittest discover -s tests_v2`
   (and `-s tests`), with `PYTHONDONTWRITEBYTECODE=1`.
3. No live provider calls, native writes, installs, or credential handling in
   tests. Fixtures and scripted adapters only; label evidence class honestly
   (`TEST_ONLY`, `MANUAL_REPORTED`, `NATIVE_OBSERVED_UNQUALIFIED`).
4. One authoritative control plane per change: state requirements, acceptance
   checks, and rollback in the PR description. Direct pushes to `main` are
   for releases; land feature work on `development/*` branches.
5. Do not commit caches (`__pycache__`, `.pytest_cache`, `*.pyc`), databases,
   pilot workspaces, or secrets. CI rejects them.

## Commit records and one-commit-at-a-time publication

Each change must include a detailed Markdown record under `docs/changes/` using
`YYYY-MM-DD-topic.md`, with a link from `CHANGELOG.md`. Record the exact added,
updated or deleted paths, what changed and why, checks actually observed,
evidence/CI identifiers, limitations and remaining work. Treat these notes as
derived change history; `docs/fable/` remains the project control plane.

Use a scoped commit message such as `docs(native-probes): describe the change`.
Stage only the intended files, inspect the staged diff and create one commit.
Before each push, fetch/recheck the destination branch and confirm that the range
from its current remote head to the proposed head contains exactly one new
commit. Push that single commit, verify the resulting remote SHA/tree, then
proceed to the next commit. Use development branches for feature work; promotion
to `main` follows existing release rules or explicit user authorization.

Do not batch several unpushed commits, rewrite already published history or
force push to satisfy this rule. If the destination head changes, preserve the
newer work and reconcile before retrying. Never describe a triggered but pending
CI run as passed; attach a later observation separately.
