# RP3 READY access repair and three-day managed-copy retention

Status: SOURCE_AND_CONTROLLER_ACCEPTED_NATIVE_REVIEW_SHIP_SELECTED_RUNTIME_UNVERIFIED. Full RP3 is
INCOMPLETE: no new selected Python3.12 run or fresh ORIGINAL AFTER has occurred.

AUTH: user requested strict read-only access and a copy fallback based on the
existing approach, then answered "3 நாட்கள்" for retention. This permits only
new managed-copy expiry; originals, consumed attempts and old logs stay intact.
INTENT: remove READY-open access as a single startup failure point without
weakening native process ownership, changing permissions, or hiding bad data.

## Actual selected-runtime failure

The consumed normal RP3 run's Receipt.json is121949bytes, SHA
5dc1bea4946e620a7db9914413735cb2d8b0e2ee634b2fe0b66ba3cd7c861af2.
Its BEFORE readback, selected3.12 identity/dependencies,17ownership controls and
18writer controls passed. Combined shutdown ran12:11PASS/1ERROR. The error is
PermissionError opening owned-bootstrap-e076...ready.json in verify_bootstrap
while constructing the fixture, BEFORE its broken-stdin assertion. Capture was
complete and not timed out. Public ordered groups and fresh ORIGINAL AFTER did
not run. The error does not distinguish an ACL denial from an incompatible
sharing handle. It is not package-install or data-preparation timing evidence.
Do NOT retry old RP3-Complete-Command.ps1 or reuse its expired reader session.

## Implemented behavior

- Source READY access uses native GENERIC_READ only. Sharing read/write/delete
  does not grant the reader write access. Native error operation, code, message,
  notes and copy/source/read elapsed times are attached to startup proof.
- Parent creates one ordinary independent single-link cache file and opens its
  read-only handle BEFORE worker launch. The exact source module is hash-sealed
  for the child. Child fills this current-token file, publishes original READY,
  then commits the copy frame. Original publication failure cannot commit it.
- Direct original read remains first. Only native errors5/32 may use the framed
  copy. Duplicate/nonfinite JSON, bad hash/token/shape, unsafe links, changed
  identity, unread source errors of other classes and unresolved close debt
  cannot select fallback. Existing native PID/image/venv/Job checks run before
  READY acceptance or the GO gate. Producer authentication is not claimed.
- Cache root is Windows known-folder LocalAppData, with per-call physical-path
  lookup: C:/Users/sakth/AppData/Local/MemoryIntegrity/ready-copies-v1. No ACL,
  file-attribute, environment-global or OS-scheduler changes were made.
- Only accepted READY plus successful startup, actual native worker-tree exit
  and clean release schedules expiry. Due time is three days after read/exit
  completion. Repeated release does not reset it. Failed/unaccepted startups
  stay retained. Application-off time postpones cleanup until a later startup.
- Cleanup uses a due-date queue rather than scanning permanent receipts. Each
  start scans at most128 queue entries and reserves at most64 deletion attempts;
  a0.1second cooperative check limits further work, without claiming native
  filesystem calls can be preempted. Receipts are never the deletion queue.
- Each removal needs exclusive native access, correct root/path/file identity,
  ordinary type/single link and exact frame/payload hashes. A durable DELETE
  intent precedes marking. A separate audit envelope persists deletion/error
  facts before queue metadata moves into retained audit. Only the new managed
  payload and NEW empty queue-date directories can be removed. Originals never
  enter that delete path. Locked/unsafe payloads remain with error evidence;
  unsafe active queue traversal fails startup explicitly.

## Verification and limits

Focused final:32/32 PASS; logSHA 3ad6bdda25e5de0984a015100d3a5052a2b5f9051beb4acf6ab9793693ec7566.

Broader final:324run,270PASS,54SKIP,0FAIL/ERROR; logSHA bfca88d5b82be4f6f401b0a3c960c8fff9b1f86e97b2ef9e5b96d67f7f33b127.
The54 skip IDs/reasons exactly match RP2 knowledge-final-02. They require
explicit numerical/parser/model/POSIX runtimes. Windows ownership/writer/session/
startup/shutdown controls and all32 READY-copy tests are included in this total.
These overlapping counts must not be added.

Tests cover real native read-only write refusal, real native sharing-error32
fallback, actual owned worker startup under an injected native5 source-open
error, exact process exit, duplicate/NaN/token/hash/source drift, source/copy
hardlinks, replaced copy path, close debt, accepted-read/exit/GO TTL guards,
simulated three-day expiry, post-delete receipt-write failure with maximum1,
150 permanent tombstones,150 interrupted queue temps,150 invalid queue-day
folders, a second live reader, and native queue scan/rmdir access faults.
Three days were simulated through an explicit UTC test clock, not elapsed live
wall time. Selected Store3.12 behavior and actual default cache creation are
UNVERIFIED; these tests use controller Python3.14.

Controller wrapper substitutes ONLY the cache root into exclusive retained
scratch and sets the existing PYTHONNOUSERSITE=1 policy. It also retains raw
CalledProcessError argv/exit/stdout/stderr. Original test bodies/assertions are
unchanged. Earlier failed attempts remain: default LocalAppData creation was
denied in the sandbox account; missing disabled-user-site exposed that actor's
Roaming site denial; one Job setup fault was initially masked by premature cache
creation and was corrected by establishing _Job first. Two scratch Git errors
were precisely path263 Filename-too-long failures; a shorter fresh output
basename fixed them without changing global Git settings or product behavior.

Retained RED/GREEN cases precede every behavior correction. First native review
found deletion-bound/tombstone scan faults; second found stale-queue and durable
audit gaps; follow-up found silent queue permission deferral. Each finding has
specific failing cases and corresponding green checks in the retained phase.
Current exact source is frozen in Source-Candidate.json plus sealed-source/.
Final native correction review returned SHIP for these exact frozen bytes.
Independent-Review.md and Controller-Accepted.json retain scope and caveats;
this is not acceptance of selected3.12/default-cache access or full RP3.

## Source scope, alternatives and continuation

Changed: windows_owned_process.py, windows_owned_bootstrap.py. New:
windows_ready_copy.py and test_knowledge_windows_ready_copy.py. No existing
test assertion was weakened, excluded or skipped. Existing Source-Recipe680,
RP2-Accepted, rp3_runtime helper and consumed receipt hashes were rechecked.
HEADfee69861 and the empty staged index remain unchanged. No commit/push,
install, ACL change, selected runtime retry or original-data removal occurred.

TWINS: repository search located the live owned-bootstrap READY read at
CurrentImageOwner.verify_bootstrap; it now routes through the strict copy reader.
Failure-sidecar and immutable historical/prototype readers retain their current
paths. No unsupported broad process or POSIX rewrite was added.

No-build leaves the actual failure unresolved. A read-only file attribute does
not grant access. A full pipe-transport redesign adds scope; the chosen bounded
parent-created signal copy retains native attestation and original-source
checks. Weakest link remains actual Store3.12/cache access. Cheapest remaining
falsifier is a new exact-source selected-runtime run, including original ordered
public initial/replay and fresh original BEFORE/AFTER preservation evidence.

Resume only with a NEW separately sealed successor after final review. Its
source must include these exact four deltas; old recipe/launchers are historical
controls, never repinned. Reuse the already approved cooperating-account copy
approach for inaccessible evidence. One combined normal-account workflow should
perform BEFORE readback, selected integrated verification, fresh ORIGINAL AFTER
and raw review. No command is issued/frozen by this candidate report. Full RP3,
Gate1, release, installed use, archive-wide preservation and historical C2 cause
stay unqualified until their own observations exist.
