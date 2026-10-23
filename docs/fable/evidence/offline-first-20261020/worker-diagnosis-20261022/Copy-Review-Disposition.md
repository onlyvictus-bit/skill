# W-COPY whole-change review and correction disposition

Fresh configured fable_sol_reviewer read all five new implementation/test files,
approved W-COPY design/plan and retained results. Initial verdict FIX-FIRST, not
SHIP. No external provider consultation or runtime execution occurred in review.

Accepted findings:
1. Critical: a rehashed Bundle object map was not derived again from the verified
   request/copies, allowing equal edited maps to hide actual different content.
2. Important: AFTER could reference a BEFORE other than the workload's Prepared
   BEFORE. Receipt bytes alone did not establish the complete binding.
3. Important evidence corrections: rerun complete controllers after latest
   junction correction and update the stale25/248 ledger counts.

One correction pass: added3regressions, watched all3fail (c2-review-red,
14run/3fail/0error), then corrected bundle_from_copies/verify_existing_bundle
to require exact field-for-field derivation and after_binding to reopen/validate
the exact receipt-anchored Prepared file, current configuration and BEFORE row.
All3GREEN in c2-review-green. Added a real-file positive parser/binding control
to guard against over-refusal; this positive case is not claimed a RED.
Final C1=26, C2=15; complete controller253/253,0errors/skips/exclusions/xfails.
Exact independently reopened receipt/log hashes: Copy-Verification.json.

Additional parent pre-review correction: real new scratch NTFS junction exposed
a recursive-mkdir outside-directory write before rejection. RED1failure in
c1-redirect-red; copy_directory now checks each parent before creating a child.
GREEN26/26 c1-redirect-green, and final full253covers those latest bytes. All
fixture data/negative runs retained, no old source or archive was modified.

Handoff condition: initial launcher had intentional nonhash placeholder. After
the correction tests, created33role Input-Seal outside ARTIFACTS and substituted
ONLY its exact literal SHA into the reviewed launcher. PS parser0errors;
VerifyOnly passes. Exact final launcher SHA is stored independently in
Copy-Verification.json and user handoff. No claim of another reviewer SHIP:
accepted defects are parent-verified RED/GREEN under the one-review execution
method, not a second independent source review.

Declined/runtime gaps carried forward: actual normal-account complete scan,
agent-account copying of its requested restricted roots, normal copied-byte
readback, selected3.12 W workload/lifetime observations, actual AFTER/finalization,
continuous immutability, atomic snapshots, authenticated producer, Gate1,
release/package/install/CI/Git readiness remain UNVERIFIED. None is inferred
from synthetic OS visibility or253controller tests. Before-only handoff is the
next actual observation; no old command or automatic retry is allowed.

Rulings carried: existing inline checkout/ledger retained (no worktree or Git
mutation); retain all test/evidence workspaces despite skill cleanup defaults;
exact hash-bound W routine/guard reuse with a closed successor namespace (no
generic runner/guard injection); separate same-API identity checks for Windows
path/handle ctime semantics, with common file identity/size/mtime cross-checks.
Costs: future W source changes need a fresh pin/review; content samples do not
prove continuous or authenticated history. No deferred implementation minors;
the launcher's external-hash condition has been fulfilled, not ignored.
