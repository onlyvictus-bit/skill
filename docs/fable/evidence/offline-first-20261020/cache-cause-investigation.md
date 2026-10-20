# Cache investigation from6361868 — partial, no product correction

Basis:6361868ff45d645517ffdfef6a16835a146e24be, development/r5-practical-fence-wip-20261014.
User requested a controlled scratch regression BEFORE changing either worker
builder. Existing Tasks1–5 cover this local investigation, not new full host
qualification, commit/push, installed-copy changes or a waived review gate.

## Complete reading coverage

The six original documents were read line by line; missing/truncated combined
tool-output sections were reread individually. Counts are BEFORE appended records:

| Path relative to docs/fable | Original lines |
| --- | ---: |
| derived/offline-first-checkpoint-20261020.md |144/144|
| evidence/offline-first-20261020/host-a1-findings.json |277/277|
| evidence/offline-first-20261020/progress.md |191/191|
| evidence/offline-first-20261020/review-disposition.md |43/43|
| derived/offline-first-release-plan-20261020.md |376/376|
| derived/offline-first-release-design-20261020.md |258/258|

Total1,289 original lines. The latest pasted continuation transcript, attachment
63784f2c-5997-4d53-9835-631ab95d79e5, was read1,717/1,717 numbered lines. It repeats
this investigation, not independent evidence or new authority. Relevant worker
code was inspected directly; this is NOT a claim to have read every repository/
history file. Binary caches were hash-checked, not described as line-readable.

## Confirmed code/context observations — cache cause NOT established

- Single env: memory-integrity/scripts/knowledge_bridge/worker_client.py:17;
  Popen:21. SHA75b911dd7e5c5becf6555dcf77be9538b6a0f98751ca36c11a8157a5c54a6ed8.
- Shard env: memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py:43;
  Popen:50. SHA10a32d856b7d9ca8ce06ea17468fe77f2a1a94be8883d0ef8726133dbb144783.
- Both allow only PATH,SYSTEMROOT,WINDIR,TEMP,TMP,LANG,LC_ALL plus four offline/
  bytecode flags. Neither supplies cwd. SystemDrive/ProgramData/ALLUSERSPROFILE
  are omitted. These facts do NOT prove those omissions caused the six DBs.
- Real authored echo subprocesses through EACH unchanged source boundary inherit
  a new scratch cwd and write a relative authored file there. A deliberately
  seeded dummy secret and SystemDrive do not reach either child. The shard script
  path alone is replaced with the authored fixture. This proves context behavior,
  NOT numerical/runtime/cache behavior. No actual cache-symptom RED is observed.
- Twin inventory: _process also serves model/syntax clients; those operations
  were NOT invoked. Benchmark/test-evidence launch paths own cwd differently.
  Product code is unchanged. Broad user-env inheritance/global cache writes
  are rejected alternatives; no production correction is selected as proven.

## New diagnostic and local verification

New .github/scripts/cache_cause_probe.py:
f73797611c6938712e2df9dcd66b08a5179fce92c903de5835598315d87adeba.
New .github/tests/test_cache_cause_probe.py:
b508960c646f0dbd8639b3287808c83fa4cf048044e38d373596f954009f0dde.

Fixed arms: controller3.14 startup, selected3.12 startup-a/startup-b, unchanged
single WorkerClient handshake, unchanged _Session startup/EOF. Each owns a NEW
cwd/temp folder. Existing filter retained; TEMP/TMP use owned scratch. Only temp
stream retention is instrumented, not runtime identity/env/cwd logic. No full
retrieval, learned model, native Beads/Dolt, setup, security change or cleanup.
Reuse existing owned-tree capture; first nonzero/incomplete capture stops with
retained streams. Exact helper/package/executable inputs and external Prepared
hash are checked. Package inventory includes ALL files/caches/bytecode. Existing
output, protected-package output, incomplete/changed basis refuse before writing.
Packets are unauthenticated observations; qualification flags remain false.

Private root: .github/run-artifacts/offline-first-20261020/.

| Result | Retained identity |
| --- | --- |
| RED6 missing-helper failures, NOT cache RED |tests-e7d3eab1012641e3970f8f5a73626fd1/Receipt.json SHAb23120d08462adaaf0cc4a57ea563e7339d287379b823c2ffb779d50efb71e47|
| Focused10/10,0 errors/skips |tests-5342bdbb9f75472bbdb14477f8ac6a34/Receipt.json SHA39fb2f75f31861cefd043c9bd4245a5f3d76e1ae2ea316f0c6cb47e5de35d076; log665b5e75cabe62673bb744f290d1aaa2f5f0161dccf7e936a54fc1c3c5d17396|
| Repository harness75/75,0 errors/skips/exclusions |tests-2ca0023a9e4a47fabad475ca2489d15c/Receipt.json SHA491329b5b9bfd756f340d7f20833f189039c34cb648d09332dde795be2a18533; loge0b846fa47fe0d098daf68b7386c687eb2ae5da7c24eefc469e07ea99176ec12|

Scoped retained local runner, not unchanged CI or all MI/CM source tests. The
authored echo is a context test, not an observed RED for the six-cache symptom.

## Actual agent attempt: stopped at existing runtime visibility boundary

Private folder:cache-cause-6361868-20261020/.
Prepared.json SHAcbb3f474019f510c7ba577246bcfc62a1f9bac7c909f3f6380f54135ed8bb114.
This is a NEW diagnostic inventory, not a replacement for host-a1's baseline.
agent-attempt/Receipt.json SHA9f2849ae8eddb8740b944a0fde5948cc4f87894d35c1f904b31b8e243cc48dcc.
Status DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING; preservation_observed=true.

- Control3.14: exit0, complete/error-free Windows-job capture; no cwd/temp files.
- Selected3.12 startup-a: exit103, complete/error-free capture, empty stdout;
  no cwd/temp files. stderr SHAa03fd5bce6a250abe3d2062bd544f81669721c8971286ce6c6f8f4dac2e474f4:
  No Python at the existing WindowsApps PythonSoftwareFoundation.Python.3.12 base.
- Startup-b/single/shard NOT RUN after failure. No relative-cache reproduction
  in the two attempted arms. Do not repeat the blocked agent call, substitute
  Python, install or change security to force it through.

## Preservation verified after all local runs

All diagnostic inventory hashes match MI204/204 and CM115/115 files, including
six DBs and all bytecode. Original host-a1's EXISTING __pycache__ exclusion still
gives exactly6 known DB additions,0 modified/missing originals; CM0 differences.
The new all-files inventory additionally binds25 MI/42 CM bytecode files already
present in its Prepared. An initial all-files-vs-old-filter comparison differed
by that policy; it did NOT establish new bytecode changes. No deletion or new
exclusion was used to resolve the comparison. All6 DB hashes match findings.json.

Old host-a1 receipt unchanged:
01934889c0a87314f14fcc8971b503d92f7d535ad52911c964bc389d2569f79d.
Old Prepared unchanged:
7ce4922f4879a0e258f23c65ef8239dd30f2173a216acd30476bf093780ea4c4.
Old launcher unchanged (DO NOT RUN):
f57a03a8ba028495301705509723a6c284fa3d550d70e025f0bfad4fc66fd0f7.
No product/profile/instructions/package/installed copy or old evidence changed.

## Review and exact next position

Parent scoped verification is above. Fresh native Fable Sol reviewer
cache_probe_review failed to start: workspace out of credits. No verdict or
independent findings exist. UNAVAILABLE_NOT_PASSED, never SHIP.

Next is fresh bounded read-only review of the two diagnostic files, THEN one
separately sealed normal-account SCRATCH diagnostic if cleared. No runnable host
handoff issued. Do not silently waive review, run old N3/host-a1 commands, reset
markers, delete/move caches or modify old Prepared. Any explicitly approved review
gate change must be recorded as a decision, not falsely called a passed review.

After actual causal observation, define the symptom RED and minimum shared
env/cwd correction with both boundary regressions. Then review a separate clean
source successor and request a NEW full-host qualification attempt. Existing35
Windows passes remain useful but do not close preservation/advanced/completion/
24-arm acceptance. Final matching packages/clean extraction/CI/installation remain
pending. Current diagnostic/docs/test changes are local/uncommitted; no push.

## Superseding local checkpoint authorization

AUTH: user said "COMMIT it". This approves one local WIP checkpoint of the eight
diagnostic/test/Fable files, NOT a push, review waiver, normal-host run or product
qualification. Parent is6361868ff45d645517ffdfef6a16835a146e24be; resolve the saved
commit with git log rather than embedding a self-referential commit hash here.
Fresh precommit repository harness75/75 passed with0 failures/errors/skips:
tests-933fa601575e497a96d3d102ecd461b3/Receipt.json (same private root), log
SHA9f59514f6ed6ca35ff5c5155ac7a83dde7187cdc982939f3018b3e9b9018793f.
All earlier results/receipts remain retained. Next action remains bounded fresh
read-only review, then a sealed normal-account scratch diagnostic if cleared.
