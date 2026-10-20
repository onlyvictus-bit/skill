# N3 child-context repair - local checkpoint, not runtime qualification

The failed484d2ca host run is retained, not retried or relabelled as successful.
Python3.12.10 identity passed. The first child failed Git's ownership check before
the retrieval CLI; empty stdout then produced a misleading parent JSON error.
Zero comparison arms and zero selected runtime tests completed.

## Diagnosed mechanism

The private evaluator reused the installer's environment allowlist. That removes
USERPROFILE/HOME and hides the existing user Git configuration from the child.
Parent Git checks preserve their current environment and succeed. The child
enters the exact-commit gate with scrubbed environment and fails before retrieval.
Git is correctly refusing a differently owned repository, not requesting an API
key. The existing Python install is not the cause.

Paired read-only implementation observation in the AGENT context: original
scrubbed environment -> Git exit128; repaired adapter adding only the validated
existing USERPROFILE -> exit0/correctHEAD. No safe.directory or wildcard entry,
ownership/ACL/global setting was added. This agent experiment explains the
mechanism; it does not prove a corrected normal-host evaluation. The original
host's complete parent environment was not captured and is not reconstructed.

Official reference: [Git configuration and protected safe.directory semantics](https://git-scm.com/docs/git-config).

## What this authorized local checkpoint includes

- `.github/scripts/n3_child_transport.py`: portable stdlib-only environment and
  retained-result decoder. Adds only matching existing USERPROFILE, rejects
  unknown base variables and relaxed offline controls, does not modify installer
  behavior or global config. Physical directory/SID checks remain host duties.
- `.github/tests/test_n3_child_transport.py`:14 RED-before/GREEN-after contracts
  for profile, secrecy, real output bytes, command failure and valid refusal.
- This report and `child-context-observations.json`: sanitized factual summary,
  not raw Windows profile/config/streams or runtime/environment contents.
- The existing four Fable records: completed prior correction history and exact
  next resume instructions. No skills, package metadata, release archives or
  content manifests are changed to make tests green.

## Separate local successor integration

New private files under the existing n3-retrieval run:
Evaluate-N3-Context-20261020.py, Test-N3-Context-20261020.py,
Run-N3-Context-20261020.ps1, continuation-context-20261020/continuation.py.
All original helpers/failed receipts/markers remain unchanged.

The new run validates actual normal identity and the sealed inputs, then launches
a real `--child-context` subprocess with the SAME intended restricted environment
and validated inherited profile. That child rechecks exactHEAD/added source/
doc/helper/input/index hashes before printing a no-query observation. Only its
same-process successful digest may precede the existing Python identity probe
and evaluation claim. A caller-seeded JSON is insufficient. Failures have their
own create-new records, retain stdout/stderr, and cannot automatically repeat.

Result decoding now checks complete captured stream hashes and actual command
outcome first. Nonzero+empty/malformed stdout is a process failure, not a JSON
decoder exception. Valid nonzero JSON stays nonzero for domain-refusal checking.
Timeout/spawn/stream substitution cannot become successful retrieval evidence.
No raw stderr/environment/exception payload is automatically disclosed.

## Verification and important limits

14portable transport controls pass after14expected failures. The full changed-
area repository contract suite passes33; behavioral eval self-tests10; existing
measurement contracts25. Real captured host failure is decoded with original
exit1/stdout0/stderr2432/hash retained. The real agent Git comparison succeeds
with the repair and leaves the Git index unchanged.

Before commit,20/21successor controls pass. The remaining exact input-clone test
is BLOCKED by the intended uncommitted added-file scope, not skipped or counted
green. The old guard's final-revision control is similarly blocked early by
that scope;4new explicit added-file policy tests pass after4RED failures. After
the containing commit is made, bind exact committed added-file hashes and rerun
all21successor+29guard controls; stop rather than weaken the guard if they fail.

Full source/package suites and unmodified CI are NOT rerun here: legacy tests
contain unlink/cleanup, conflicting with the user's no-deletion constraint.
All525old product files are required unchanged. Existing release-manifest drift
remains historical/intentional and is not repaired by this harness checkpoint.
The29runtime tests/24comparison arms/N3-D and semantic benefit remain UNVERIFIED.

## Exact resume after local commit

1. Obtain this containing commit's actual SHA; no push was authorized. Check
   exact staged/committed paths, no deletions, old525product identities and old
   failed artifact hashes. Never rerun the484d2ca Prepare/Run handoff.
2. Rebind ONLY the NEW private successor to that SHA. Enumerate the four added
   public paths and committed hashes in the new guard; verify tracked set equals
   original529plus those4, with525old product hashes unchanged. No arbitrary new
   path or old-file replacement is allowed. Freeze guard/core/test/launcher hashes.
3. Run all relevant postbinding controls/preservation, and retain a postcommit
   proof privately WITHOUT editing Fable records and movingHEAD again. Record
   the exact new hashes/command in the private successor HANDOFF.
4. Normal-host Prepare creates a fresh input-only clone, never resets the old
   attempt. Parent must independently check its external Prepared seal before
   one new Run under the user's approved bounded successor recovery. The child
   context check occurs BEFORE consuming that new evaluation attempt.
5. Observe24arms/replay/safety/exact29tests and perform N3-D result review before
   deciding readiness. No skill install, release, native fence/merge qualification
   or model/provider call is implied by this checkpoint.

The private chain/pin corrections and original failed evidence are NOT a portable
release: this public checkpoint does not include the existing17,273file private
environment or the historical private N3 bundle. Local artifacts remain required.

Rulings: one existing Fable ledger/current isolated checkout; no cleanup; existing
verified output ancestor chain covers physical profile identity, so environment
construction stays pure rather than duplicating a denied filesystem resolve.
Cost if wrong: host preparation/context gate refuses, not a new trust exception.
No second independent approval is inferred from parent test results. The review
disposition and one parent correction pass are recorded below before publication.

## Review correction and publication boundary

One fresh native `fable_sol_reviewer` judged the initial snapshot FIX_FIRST:
zero Critical findings and two Important findings. The findings were the dirty-
document allowance and inaccurate transition-state wording in these records.
The parent accepted both and performed one consolidated correction pass. No
second independent SHIP or approval of the corrected bytes is claimed.

The inherited guard permitted uncommitted changes to the four Fable documents.
That is inappropriate for an exact-commit successor. A new retained regression
failed for all four paths before the correction; it passes after requiring a
fully clean worktree. This is the29th guard test. No historical guard is edited.

This document records the precommit verification boundary. The containing Git
commit identifies these public bytes; its actual SHA and subsequent21+29test
results must be recorded in the separate private postcommit proof, not guessed
here or written back into this record to moveHEAD. Remaining host evaluation
and N3-D claims remain unverified. No independent approval of the corrected
bytes is implied by the parent's correction tests.

The reviewer explicitly declined to judge postcommit binding/tests, a sealed
host handoff, actual normal-account execution, general public CLI integration,
full source/package/CI health, retrieval quality, native operations or release/
installation readiness. Existing production CLI code does not import the new
transport module; only the separate private coordinator integrates it. The
containing commit is a reusable offline checkpoint, not a general CLI fix.
