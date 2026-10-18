# N1 core-memory acceptance - 2026-10-18

Current status: VERIFIED_WITH_CAVEATS after one review-driven harness fix.
The initial run and its limits are retained below; final evidence is in the
last section. This is a bounded source-retention/
recall observation, not a release, semantic/model-quality or native verdict.

## Authority, implementation and source identity

The user requested committing the completed offline correction, then the next
required step after a deep plan. That correction is locally committed as
6c5ba969feecabcdb1c05be12de41512aec01220 (eight paths, no file deletion, no push).
They separately approved "N1 acceptance harness and local tests (Recommended)".
The existing practical-fence-plan.md retains the full design, alternatives,
acceptance matrix N1-A through N1-H and stop/approval boundaries.

Only a new external test harness and Fable records are added for N1. No existing
package code/test, instructions, capability flag, SQL, ZIP, content manifest or
installed copy changed. The matching companion remains explicit. No model,
provider, graph worker, Beads or Dolt operation ran.

Initial private harness (now retained byte-for-byte as
Core-Memory-Acceptance-20261018-initial-cf4e08be.py):
build-validation/Core-Memory-Acceptance-20261018.py
SHA-256 cf4e08bef563b7d6734e28f594afbab5cd1f0e9607469c073ad00c4dd4103670.
It invokes the actual unchanged public offline-run/verify CLI through a Python
runpy startup shim. The shim retains Python temporary directories and restricts
subprocesses to the inspected companion capabilities and proof/partition probes.
This is not unchanged CI or an OS security sandbox. No deletion/cleanup of
baseline files is allowed; SQLite owns its new private transient journals.

## Observed public behavior

The retained bundle contains exact copies of four actual source/test files:
memory_integrity_workflow.py, integrity_v2/recall.py, companion partition.py,
and test_r2_workflow.py. Framing identifies original file ranges/hashes. One
separately labelled synthetic Unicode line exceeds 4096 bytes to test safe
child-span boundaries. This is a framed single text-source workflow, not proof
of an automatic repository/directory/multiple-source ingestion feature.

Measured bundle: 60,704 UTF-8 bytes, 965 primary units, four chunks. Review
fixtures explicitly declare structural TEST_ONLY retention. They are not
genuine semantic review, an LLM response, or independent truth labels.

| Check | Observed result |
| --- | --- |
| N1-A | PASS: fresh-process exhaustive recall returned all 965 primary IDs in exact order, once; original excerpts reassembled the entire 60,704 bytes; TEST_ONLY and no generated answer |
| N1-B | PASS: literal E_RUNMAP_STALE located its one matching unit; the absent literal returned zero; a universal query still enumerated all units |
| N1-C | PASS: unchanged resume reported resumed=true, with the complete saved-run inventory/ledger byte-identical |
| N1-D | PASS: a distinct source copy changed one code string; current-source verify returned STALE with E_RUNMAP_STALE and no recall; original source/run remained current |
| N1-E | PASS: a fresh clone omitted one response artifact without deleting the original; E_RUNMAP_ARTIFACT refused recall |
| N1-F | PASS: a fresh clone contained corrupt response bytes; outer hash validation refused with E_RUNMAP_ARTIFACT and no recall |
| N1-G | PASS: a copied ledger's provider was changed and its outer hash rebound in a new run map; inner request/approval proof refused with E_REQUEST_APPROVAL, not an outer hash failure |
| N1-H | PASS: the actual assertion helpers rejected truncated recall, a false stale-success response and an unrelated companion-spawn error substituted for the required artifact refusal |

A pristine clone passed before the copied negative cases, establishing that
relocation itself is not the cause of their rejection. The untouched original
passed fresh verification at the end and its complete run inventory remained
unchanged. All 526 repository baseline files remained byte-identical during
the N1 harness run. Every variant and log is retained privately, including
the unchanged original run. No product fix was necessary for these observations.

N1-D proves changed source invalidation, not task-dependency graph repair-set
calculation, ownership fencing or semantic meaning of a dependency change.
N1-G proves this particular rehashed approval tamper is refused; it is not a
general defense against an administrator who can rewrite all local authority.

## Exact retained receipts and regression boundary

Primary private receipt:
core-memory-acceptance-14b735d8008744579f61b9c2616dd9d6/Receipt.json
SHA-256 81cf6203ec30f1a9a28851496a4340dadf82b602035598ef2954bbe5b7ee30a8.
It records the harness/commit identity, all eight check outcomes, every command,
exit code and stdout/stderr hash. Before/After inventories and source/fixture/
manifest/original/tampered variants remain in the same private run directory.

Fresh precommit practical MI run: execution-provenance-precommit-
24db89fb96f64abda6feff54de00d63b/Receipt.json,
SHA-256 1272886e83cb30af2d6d0aa24d28d48097c94a1ed6166110b8e0f929657e74fd.
280 cases: 279 passed and one existing expected-failure live-dolt-ignore
placeholder, not actual live database proof.

Fresh CM regression: execution-n1-regression-cm-
fd1fc15e0ccd42958ddc7611111d89d2/Receipt.json,
SHA-256 e9d16311d5d661e89adf70e6ce94ccc027616fdb3ecc20e69ac4df9ed0c27211.
18/18 passed with stable source. These are retained-fixture adapted checks,
not whole-tree clean CI. The earlier 942-case before/after comparison and its
remaining failures/errors remain in the provenance-correction report; they
are not erased, counted green, or rerun by this N1 milestone. Exact-release
CI and source/package manifest closure remain separate work.

Fresh practical CLI preflight regression: execution-n1-regression-cli-
8b74ad1d002949d2a17f42137ef9c076/Receipt.json,
SHA-256 dc73592063d2d66eb395d621d72d52b2e939d6d6d210b01546e72f0c329850d9.
9/9 passed. The N1 harness itself invoked the public workflow 12 times: eight
successful controls and four nonzero refusals with their required causes.

Independent parent artifact verifier:
build-validation/Verify-Core-Memory-Acceptance-20261018.py. First proof
Core-Memory-Acceptance-Verified-c0397d3b9dbb45f0be94e330de231537.json,
SHA-256 ae4618b1422f142a11de05188b4d5dea58ab20bc99e6a0273a99bbeb8ab7d507.
It reopens source copies and all 965 returned excerpts, verifies every command
log hash and refusal cause, the clean-clone/original controls, rebound copied
ledger hash, all 526 retained baseline files, and unchanged package trees.
The original passing run's 24 files are byte-identical. Fable docs alone may
advance after this proof; current package source remains the committed bytes.

## Review and current gate

Fresh read-only Fable Sol review is requested against the harness, exact
receipts, plan and unchanged product source. Until observed, independent
acceptance is pending. The parent directly ran the CLI harness, not a simulated
reviewer report. No model-quality, large-project coding benefit, unlimited
context, persistent live memory service, native qualification, release readiness
or installed readiness follows from N1's mechanical checks.

Next after acceptance: define and separately authorize task-relative retrieval/
model quality evaluation, or prepare a scoped core release with native features
still disabled after broad regression/clean-package gates. Do not silently
install models, regenerate historical manifests, push or replace installed skills.

## Independent review, missing control and final correction

Fresh reviewer /root/core_memory_n1_review returned FIX-FIRST for the initial
N1 result. Important finding: N1-F's outer-corruption test plus N1-G's rehashed
approval test did not satisfy the separate rehashed fabricated-response control
required by the approved matrix. The initial eight local check flags were not
sufficient to claim full N1 acceptance. This was a harness coverage gap, not an
observed product defect. The reviewer independently verified the other source,
artifact, control/refusal, preservation and regression claims. Its minor was
stale resume/next-action wording, now advanced as required checkpoint maintenance.

Parent ruling: accept the important finding and add the missing control in one
fix pass, without changing product behavior or relaxing the specification.
The initial harness and verifier have retained byte-for-byte copies; all prior
run directories and proofs remain. No historical result was rewritten to green.

Failing-before check:
Check-N1-Rehashed-Response-Control-20261018.py against the initial receipt
failed with MISSING_REHASHED_RESPONSE_CONTENT_CONTROL. Retained red proof
N1-Rehashed-Response-Control-870a720f076c4a9990c7d1006dc98c99.json,
SHA-256 06e1ba2bd0e65bc3c4c9128ecbc27fe1ebdee23d7f0a51d021a9f43db781c391.

The successor harness creates a fresh copied run, writes a fabricated response
to its correctly content-addressed new CAS path, updates only the disposable
ledger's response reference, and binds that ledger hash/new artifact in a new
run map. Every mapped file hash and CAS filename/content identity is valid.
The actual public verifier then returns BLOCKED, E_RESULT_CONTENT,
E_RESULT_COVERAGE and failed history-projection proof; no recall is returned.
It does not return E_RUNMAP_ARTIFACT or E_LEDGER_RESPONSE. Thus the required
inner content check is reached rather than relying on outer hash rejection.
Other integrity checks rejecting the same malicious variant are not suppressed.

Final harness SHA-256:
842779e24236d75b71645beaffce8471c3577e33a39095274737cc5e371c2b24.
Final complete run:
core-memory-acceptance-84d3b1f1dbd14de49676e64ea381053b/Receipt.json,
SHA-256 5102e7159d7a0b968e3fe9f6739ebb95b28dee5eb06154581318355a07ac557f.
All eight acceptance groups pass, now through 13 actual public CLI invocations:
eight success controls and five correctly caused refusals. N1-F includes both
outer-corruption and hash-rebound inner fabricated-content rejection. Clean
clone/original controls passed again; source remains 60,704 bytes/965 units/
four chunks. All 527 repository baseline files remained byte-identical during
the final run. At checkpoint, 523 outside four intended Fable edit targets
remain byte-identical. The original passing run's 24 files are unchanged.

The regression checker now passes against the final receipt. Green proof:
N1-Rehashed-Response-Control-3f85121030fa4e1282e0d62302c8eed2.json,
SHA-256 31fe52cf41117f9433fe8c49f0bf3d3a38f2b469030e88f66e21daf1563a0996.
Updated parent verifier checks both the earlier required controls and this
inner-content arm. Proof Core-Memory-Acceptance-Verified-
2431cdbc28f14019bc090cfdde221eac.json,
SHA-256 a3358e71860da27801d9d63e780de8db366a4c73767042c736334f4f49b988d4.

Fresh post-fix focused regressions (source stable in each):

| Group | Result | Private receipt | SHA-256 |
| --- | --- | --- | --- |
| MI practical | 280 run, 279 pass and one prior expected-failure placeholder | execution-n1-final-mi-7bcc1eae67104ffe894f9e420790a27b/Receipt.json | 029f97c5daad64681642aa5458d0e347c6e5d822060e06a2005ec14a8a84eacd |
| CM journal/dispatch | 18/18 pass | execution-n1-final-cm-02a41114f2f446969f8947ea5def2ef4/Receipt.json | 0f507452b32a7896f8c5841e4552ac1540a2fdee65d5b6d575f180a6828761b4 |
| Public practical preflight | 9/9 pass | execution-n1-final-cli-76fedf283a8a463eadd3530cbddc6c90/Receipt.json | 25fcdb2d762183cfb8fd5f7fa1f56baf0f703d44927b6ee12c94cdc3298d7dac |

Parent also directly challenged the assertion helpers with altered final
excerpt bytes and an illicit recall field on a blocked result; both were
rejected. The project-wide twin search was confined to the relevant acceptance
oracles: missing/corrupt artifact, inner approval and inner response content
are distinct controls; neither of the former is relabelled as the latter.

Final parent verdict: VERIFIED WITH CAVEATS for N1 only. The independent verdict
is retained as FIX-FIRST for the initial harness; there was no second review
of the corrected bytes. The parent verified the review-driven fix using the
observed failing-before checker, passing-after checker, whole N1 rerun, raw
artifact readback and focused regressions. Do not represent that as a fresh
independent SHIP verdict or as full green CI.

N1's test harness/verification receipts remain private and uncommitted; the
repository contains only the plan/checkpoint/report changes. HEAD remains
6c5ba96. Nothing was pushed or installed. No existing product or baseline file
was deleted; only new private SQLite stores manage their own transient journal
lifecycle. No production change, model inference or native Beads/Dolt run.
No minor polishing work is deferred in N1; the older R1 docstring wording minor
remains outside N1 and unchanged. All model/native/release/install limits above
remain. The useful next decision is measured task-relative retrieval/model
evaluation versus a scoped core release after broad/clean-package acceptance.
