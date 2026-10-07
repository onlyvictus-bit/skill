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
