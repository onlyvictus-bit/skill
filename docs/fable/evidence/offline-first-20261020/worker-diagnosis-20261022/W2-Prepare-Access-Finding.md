# W2 normal Prepare access failure — 2026-10-22

BLOCKED_NORMAL_READBACK, not retrieval failure or worker diagnosis. User's new
command was correct. User console is reported evidence, not authenticated raw
capture. No rerun, code/ACL repair or diagnostic workload occurred this turn.

## Stopping point

VerifyOnly passed. ModePrepare entered prepare_inputs -> readonly_python ->
historical_readback, then stopped at controller line265:

```text
'private_artifacts': g.inventory(ARTIFACTS)
gate1_validation.py:86: os.walk(..., onerror=failed)
gate1_validation.py:85: raise error
PermissionError [WinError 5]:
.github\run-artifacts\offline-first-20261020\a-0ce101b0\retained-temp\tmp2f5t5rme
```

The preceding straight-line pinned checks and V3 maps returned without raising
in the reported host run. This is a control-flow conclusion from the trace,
not an independently saved complete host receipt or whole preservation pass.
The additional all-artifact first-observation inventory never completed.

## Direct read-only evidence

Exact denied directory exists, with two immediate entries as seen by this agent.
Owner SAKTHI\CodexSandboxOffline, SID1003; inheritance disabled. Allow entries
only OWNER RIGHTS, SYSTEM and Administrators FullControl. No normal sakth1001
entry. Parent retained-temp DOES inherit normal sakth access. Exact SDDL:

```text
O:S-1-5-21-2571509308-2482563067-4170768140-1003G:S-1-5-21-2571509308-2482563067-4170768140-513D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)
```

Sibling tmp3w773g39 has the same protected ACL/owner. a-0ce101b0 is the retained
29/29 accounting-focused test run already cited in existing records. Accounting
remains closed; no rerun needed.

retained_unittest.py:41-46 replaces TemporaryDirectory with a retained wrapper
but still calls tempfile.mkdtemp. Installed C:/Python314/Lib/tempfile.py calls
os.mkdir(file,0o700). Windows mode0o700 deliberately restricts access to the
creating account/administrators. Observed ACL matches this creation mechanism.
[Official Python documentation](https://docs.python.org/3.14/library/os.html#os.mkdir).
This is cross-account retained-scratch handling, not missing/deleted evidence.

Wide read-only survey:19471directories enumerated,12748ACLs inspected before
40second limit. Other account-owned paths were unreadable; output was too large
and truncated. Survey is INCOMPLETE, not an exact permission target manifest,
normal-token effective-access proof or complete preservation check. No recursive
grant may be derived from it.

Fresh parent verification: all27sealed roles and normalized launcher still match;
launcher96d82487ab04a764cc530f8092db44e15ebde2eb04a946b2b5fc8a23f4d26cf3,
seal2d7cb8c9e7d37d60e613f987bb8b9d7746cfd2ef178b1fbd7bbb2778c8425f1f.
lstat confirms worker-observe1-20261022, wrkbas and wrkobs ABSENT. No Prepared,
preclaim, selected3.12 workload or native-holder control/API was created/run.

## Decision before any repair

No-build: retain failure and stop, safe but blocked.
Recommended: separately approve a bounded exact-manifest-first read-access repair
for verified agent-owned retained scratch trees under this artifact root. FIRST
freeze target paths/ACL/owner/link/reparse identities and readable content hashes;
stop on unexplained targets. THEN add only normal sakth file-read and directory
list/traverse rights on those explicit targets, preserving every existing ACE,
owner, inheritance flag and byte. No broad project/root grant, FullControl,
takeown/reset, elevation workaround, deny removal or automatic retry. Verify
exact approved ACL deltas/content, then prepare a separately reviewed handoff.

Stronger alternative: explicitly redesign the supplemental all-artifact coverage
contract while retaining every authoritative pinned check. This changes agreed
coverage and needs its own decision; silently ignoring AccessDenied, excluding
retained-temp, replacing maps or treating unreadable directories as empty is
forbidden. Not implemented or recommended as a green-test shortcut.

W1-W3 excludes security/ACL changes. Previous named N1 audit grants do not cover
this different collection. No repair script or permission change made. Do not
repeat the frozen Prepare merely because its output remains absent. No install,
old-file deletion, Git mutation, worker fix or Gate1 qualification occurred.

## User selected one-file copy instead of an ACL grant — 2026-10-22

AUTH: user: "you need only read access to that file, than make a copy of file
and read that copy". This is NOT approval to change permissions or silently
change the sealed preservation contract.

Copied ONLY the303byte retained workflow substitute to a NEW ordinary folder:
C:/Users/sakth/Documents/Codex/w2-fixture-copy-20261022-4abc8938/memory_integrity_workflow.py.
Read copied content successfully; did NOT execute it. Original before/after and
copy SHA256 all9e5048c72f1f04dcc4977a651ea27da396b9dda4b49fa4af8f60592c5e673a12.
Original file ACL before/after identical. Copy inherits ordinary workspace ACL,
including normal sakth1001 access; normal-account read itself is not observed.
No manual grant/reset/owner/inheritance change. Receipt in new folder records
observed bytes/hash/ACL, not producer authentication or whole skill readiness.

Current g.inventory(ARTIFACTS) still visits the protected original paths. A copy
does not prove that its original stayed unchanged during later work and cannot
automatically replace the original in that guard. No sealed helper, launcher,
input, old artifact or claim modified; no diagnostic rerun. To use copied
supplementary evidence in a successor requires a reviewed explicit source/copy
mapping and an honest preservation contract; do not turn this one-file copy
request into a whole-archive mirror or silent inaccessible-original exclusion.

## Latest user direction: fresh BEFORE/AFTER copies — design only

The user now explicitly selects fresh verified copies at the required times,
not merely inspection of the303byte fixture. Acknowledged: copy-based content
comparison CAN work; direct normal-account reads of every restricted original
are not inherently necessary. The source-reading account must actually read the
original at each snapshot time. Same denied account cannot bypass source access
by calling copy(), and the old one-time copy is not a fresh preservation record.

Proposed full description: W-COPY section at the end of the existing release
design. It keeps complete supplementary archive coverage through disjoint
normal-readable maps and agent-reader copies, with exact source/copy hashes,
fresh phase bindings, refusal of incomplete observations and a final AFTER gate.
No ACL change, skipped path, baseline replacement or producer-authentication
claim. Mandatory pinned checks remain direct/unchanged. Supplementary restricted
content is explicitly sampled BEFORE/AFTER, not at every intermediate normal
guard; workload outcome stays pending until the post-run comparison is complete.

Current action is a design/builder check, not an implemented copy fallback. Old
sealed helper/launcher/input and originals remain unchanged; no diagnostic retry
or new whole-archive copy has run. Do not close the actual automated error or
worker-failure gates based only on this accepted design direction.
