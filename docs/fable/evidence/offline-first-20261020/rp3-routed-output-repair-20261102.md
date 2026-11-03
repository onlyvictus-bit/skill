# RP3 separate actor output repair, 2026-11-02

partial: Code/controller verification complete; actual normal transport and
selected3.12 runtime remain UNRUN. Old failed-b command is consumed and retained.
User invokes Fable Method to solve confirmed cross-account output refusal.

INTENT: code sends reader writes into normal ROOT; required handoff lets each
account write only its own outputs; approved no-ACL copy design uses separate
readable copies and exact source-to-copy/hash/BEFORE-AFTER verification.

Explicit normal ROOT stays short; reader session outbox is under private phase;
normal transport channel is separate and normal-owned. Existing SnapshotSet
copy/merge/verification primitives are unchanged. Copied metadata retains actual
paths, hashes, file identities, request/policy/session bindings; no relocation of
JSON records or generic filesystem redirection. Product4files/682recipe unchanged.

Reader policy/inspection/CopyInputs/BEFORE/AFTER/ready/result/envelopes now live
in its outbox. Normal prep/source/runtime/bundles/results/requests stay normalROOT.
Factory validates every module ROOT/READER_ROOT and exact new helper seals on
reopen. Actor guard rejects peer-root JSON writes and retains original OSError
with operation/actor/path/errno/winerror notes. Failure logs use actor-owned roots.

Cheap preflight precedes expensive preparation: reader seed is hash-bound in its
claim then externally pinned service; normal writes ping, reader only reads it;
reader writes ack, normal only reads it and publishes normal accepted marker.
Exact SID/PID/session/nonce/manifest/service/content/fileID/mtime bindings checked;
current proof rechecked at reader-ready and final stage. Service keeps original
single3600second UTC+monotonic window. Atomic markers hide incomplete JSON.
Both roles exchange files in controller tests; these are same-account synthetic
roles, NEVER proof of the real normal-account interaction. Real interaction is
the first segment of the single normal command, not a separate test handoff.

Protocol expected-RED4errors before guard implementation retained; GREEN tests
verify peerwrite refusal and originalerrornotes. Behavioral controls run frozen
failed metadata functions with scratch data to expose wrong normal writes, then
new helper routes succeed. Normal merge reads outbox and writes normal bundle;
AFTER uses original normal request and only reader-owned copies. No old selected
workload/command or actual original fixture was retried.

51 controller checks PASS12.145testseconds/12.8468harnessseconds, no timeout,
logSHA b0bbe2c909f2012459b7a2cc333f3174ca32e535b4724e156dd2bc2e184f46b9.
37existing registry/source/budget/publication/FSM checks plus4copy and10protocol.
Old synthetic-hook fixtures keep their one actor fixture for publication ordering;
separate new routing tests enforce different actor roots and peerwrite refusal.
No new source/runtime broader run: productbytes unchanged, previous accepted
324broader270PASS54existingSKIP and32focused source evidence remains historical.

TWINS: searched reader-owned ROOT writes - found 3 other helper surfaces:
rp3_finish.py, ready_workflow.py, ready_factory.py. New copy/bound/runtime/finish/
workflow/envelope/factory routes and pins corrected together. AST checked reader
inspection/BEFORE/AFTER/reader_watch write destinations:0normalROOTwrites.
All consumed copies remain historical controls, not editable repair targets.

Native design review endorsed explicit two-root mechanism; final implementation
review pending. Old failed-b3records+4product hashes unchanged. No install, ACL,
global/Git change or original deletion. Retention3days remains only accepted,
exited managedREADYpayloads; all diagnostic/source/evidence artifacts retained.
