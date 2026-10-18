# Exact-commit independent diagnostics review - 2026-10-18

Verdict: FIX-FIRST for the bounded offline repair, not a native-authority break.
Independent review is completed for this exact diff; it is no longer pending
workspace credits. Historical reports saying PENDING remain historical.

## Scope and reviewer

Fresh read-only native Fable Sol reviewer:
/root/diagnostics_exact_commit_review, role fable_sol_reviewer.
Base fbabbab5e69e924ac4aae6c3a4fb6de62aae3d55.
Head 0f1fe58b66a03e34244b1f2ac56e5588d2489eee.
The reviewer examined source, tests, retained evidence and no-write in-memory
probes; no external provider or native database was called. This is a concise
consolidation of its report and the parent's independently executed checks,
not a claim that the parent is the independent reviewer.

## P2 / moderate finding: diagnostic provenance is self-reported

Supported reserve_practical_native_intent -> consume_practical_native_dispatch
-> mark_practical_native_unknown calls accept a caller-created canonical
packet as an UNKNOWN reason. The reader can report available=true and
capture_complete=true with source=SEALED_DOLT_CLIENT despite no backend or
subprocess invocation. Changing port and command_sha256 and recomputing the
packet self-hash also passes validation. This does not require DBA access,
Python introspection, module patching or a forbidden extra field.

Source locations on exact head:

- practical_execution.py:93-120: hashes and selected shapes checked; command
  digest need only look like SHA-256 and port need only be in range.
- practical_execution.py:152-184: the reader accepts that protected reason and
  exposes it as available/possibly complete diagnostic output.
- claude-mon/scripts/complete_read_v2/ledger.py:395,430,471: supported existing
  lifecycle APIs used by the reproduction; their generic uncertainty reason
  behavior is pre-existing, not itself a new ledger defect.
- test_practical_execution.py:129-142 rejects a forbidden refusal field, but
  does not cover a fully schema-valid public-API fabrication.
- The stronger original/exact-command wording in the dated practical plan and
  verification.md:25-34 is not established for that ordinary supported API path.

### Actual impact and containment

Causal status stays UNVERIFIED, evidence class stays TRANSPORT_DIAGNOSTICS_ONLY,
and the reproduction creates zero PRACTICAL_NATIVE_APPLIED events. The reader
makes zero database writes. Refusal attribution ignores these packets and
dispatch consumption still suppresses replay. This is a provenance/claim
accuracy defect, not demonstrated unauthorized native execution or acceptance.

Hashes establish packet/history self-consistency, not authenticated origin.
Complete captured bytes do not mean a real native command produced them.

## Parent reproduction and fresh regressions

Local evidence root:
C:/Users/sakth/Documents/Codex/2026-10-02/ad/work/R5-practical-fence-20261013/build-validation.

- Review-Execution-Public-APIs-20261018.py executes only in-memory CM APIs and
  blocks native subprocesses and deletion. Receipt:
  Execution-Review-Public-API-a58a6a0d42d640e0a51498f35b629c39.json.
  SHA-256 fa2604252b4bbb15f47643c50429f251eadf98e75719c7031ce9c6c74d3f7f47.
  Observed: fabricated packet available/complete, producer label echoed,
  changed command identity accepted, history/projection VERIFIED, reader
  writes zero, APPLIED zero, causal status UNVERIFIED.
- MI: execution-review-exact-commit-9891b1dc523a4479acfa692d383d2579/Receipt.json.
  SHA-256 fd459138efe5ddc4dc52aa15214b3b44783902daea24362c2eed66cc85e6f0fe.
  275 run: 274 passes and one known expected-failure placeholder.
- CM: execution-review-cm-c588f55b6df54deb946d4b9ee205c24f/Receipt.json.
  SHA-256 7a84e5238dc79660d63accf6162afd85248ce303fe6b862297c108d399e18fb5.
  18/18 pass.
- CLI: execution-review-cli-46031622901746aa9bca64067feb94f2/Receipt.json.
  SHA-256 ec491129bccaa30253aae64aa027e6e435b345875051f6575e3f3b8b917f13aa.
  9/9 public preflight checks pass.

All final groups record stable source during execution. Total 302 run,
301 passes, one expected failure, zero unexpected failures/errors. MI/CM use
the existing retained-fixture adapter, blocking deletion/unmocked subprocess;
CLI uses direct Python. They are not unchanged full CI or native evidence.
The expected failure remains the live-dolt-ignore placeholder, not a native run.

The reviewer separately exercised guarded title process failure, lease-transfer
foreign receipt and lease-transfer spawn failure using real backend/CM logic
with mocked process boundaries. Diagnostics survived, missing bytes remained
incomplete, no APPLIED was created. Parent additionally reproduced the actual
public-API boundary and re-ran the 302 focused checks above.

## Verified strengths and untouched surfaces

The exact ten-file diff is scoped. The companion ledger/schema, protected
consumer, lease SQL predicates and practical contract did not change in it.
Original diagnostic bytes/status are retained on the actual tested failure
paths; the controller reads CM independently from its worker result file;
canonical refusal attribution remains unchanged. The new diagnostic module
is included in the source manifest. Historical handoff's first 17,991 bytes
remain identical, SHA-256
1dc09c0129af24a4fb162ac6d61dcf98127d207f5ea2b44655e94f2eb4019332.

Pinned existing Dolt and Beads files were read/hashed successfully by the
parent. Their bytes match the retained runtime pins. No binary was executed;
version output, grammar, rollback and runtime containment remain unobserved.

## Decision, declined scope and next gate

Recommended: explicitly label diagnostics as unauthenticated/self-reported,
separate byte completeness from provenance and independent invocation identity,
and add the schema-valid supported-API regression. Retain old packet/history
bytes and unchanged no-authority behavior. This precise evidence-contract
correction is awaiting human approval; it has not been implemented here.
If authenticated sealed-producer provenance is required instead, obtain
approval for that stronger trust-boundary design rather than renaming the
current self-hash as authentication.

Native preflight must not proceed with the misleading distinction unresolved.
The exact next-task order is in the new dated section of the existing practical
plan. Review completion does not mean review acceptance or native qualification.

Declined/unverified: native grammar/assertion rollback and actual error format;
synchronized fence/current-owner/disabled controls; real expiry/heartbeat/ABA;
in-command client kill and server crash/restart; full unmodified regressions
and exact-commit CI; releases, packages, installation and full M7/Gate B.
The pre-existing PIPE collection is not streaming memory-bounded; retaining
64 KiB prefixes does not close native process/output containment. These are
open campaign gates, not concealed failures of this narrow review.

No skill code, SQL/CM schema, native flag, manifest, ZIP or installed copy was
changed by this review. No new commit/push, native command, data/file deletion,
installation or external AI call occurred. Existing evidence is retained.

Subsequent continuation: the human approved the recommended explicit
unauthenticated-diagnostics correction. It is implemented and separately
reviewed in provenance-correction.md. This original FIX-FIRST verdict applies
to published 0f1fe58 and is preserved; it is not the final saved-successor
verdict and is not retroactively changed to a pass.
