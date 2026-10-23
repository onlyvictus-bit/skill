# COPY-H1 independent native review — SHIP for first Before only

2026-10-22 configured fable_sol_reviewer, one fresh read-only review seat.
No external AI/provider consultation. Reviewer changed no files, reran no test
suite and ran no COPY phase/selected worker. Parent observed all current tests.

Final verdict: SHIP for COPY-H1 offline code and the first hash-checked normal
account Before handoff ONLY. Critical: none. Important: none remaining.
Minor: synchronize earlier progress/state text to the final counts/seals; this
is part of the planned evidence handoff, not an additional implementation fix.

## Findings and correction evidence

- Initial unsealed JSON round-trip rounded64bitNTFS IDs. Reviewer reproduced
  0/56exact allowed IDs and354/709exact old rows in those drafts. Drafts retained
  unused; NEW *-exact.json inputs written with Python integer-safe JSON. A real
  production-load test failed on those wrong IDs before correction and now
  freshly compares every56full rows and all709old objects successfully.
- Initial exception bound only ID/link count. Parent froze full identity6,
  size/SHA/owner-group-DACL; scoped reader now rejects same-inode drift and a
  whitelisted pathname replaced by a single-link file. Protected-ID schema and
  scope/origin/old-request binding added.22reader/11controller are GREEN after
  retained REDs. No second reviewer or speculative worker repair was started.

Reviewer independently reopened and verified:
HEAD923de16c91a9ef4381e7ac975e3a3780f42a4bf5;56allowed exactpaths;
353protected identities exactly derived from trusted files and both package
trees;709old failed objects unchanged;41sealed roles; every56allowed source
record matches current full ID, size/hash and permissions. BEFORE/run/final
absent. Old failed output and rounded drafts remain intact.

Exact records independently checked:
- Policy ee6b4123a9b51674e1f384168ec77430e9a6557c845415d70308afce236432ea
- Entry 71603a96edc8bd4126626c86b9dec958c145de8338f1cce41aa7b5a3a23838fc
- Config 623a78c6a9226527b24b418cc70bf55377b6607e9de331488d88ced298b02b8a
- Launcher d55041051df653bcba17783f56d30d7a7c4e6bec47457da949a055913de43ec0

Reviewer inspected retained receipts AND matched logs:22reader,11controller,
286complete controller, all0failures/errors/skips/exclusions/expected failures.
Full log28907238dd230a5c09d41ed0e85d52e1d3c559ba6523debee9b81f981e81e183.
See Copy-H1-Verification.json for exact paths/receipt identities and interim
failed/preparation observations, not just the final green result.

Confirmed boundaries: exact-data-only scope; strict trusted record/load and
destination link checks; exclusive independent copies; no complete manifest
before double source/destination verification; original-read identity/ACL race
checks; batch/session/phase/path/hash mapping; AFTER binding; no old namespace
mutation, copied code execution, timeout change, cleanup, Git or installation.

## Declined to judge / parent rulings

Actual normal Before and cross-account completion are unexecuted, so neither
is claimed. Whole BEFORE/workload/fresh AFTER/compare is still pending. Original
timeout and file-holder causes are unknown; no runtime repair/Gate1 readiness.
Packaging, CI, installation, authenticated provenance, continuous immutability
and power-loss durability are outside this verdict and remain unqualified.
These are correct acceptance boundaries, not waived work or hidden passes.

Parent ruling: preserve this first-handoff-only scope. No new approval is needed
within approved COPY-H1/W stages, but use the actual normal account and exact
returned request hash. Never reuse an old command or consume a copy phase from
an inferred/latest-looking request. No actual copy/workload command issued yet.
