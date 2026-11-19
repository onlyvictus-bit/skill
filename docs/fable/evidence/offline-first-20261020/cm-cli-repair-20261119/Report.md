F01/F02 fixed in active source, not installed. Completion 2026-11-19.
F01: preflight has no authoritative task-spec identity before prepare. Any
supplied --task-spec-digest (including empty) now returns structured exit2
before run paths/input reads/ledger creation. Omitted option still passes;
--expect-task-digest still enforces the work-item task; prepare binding unchanged.
F02: uncaught operational OSError/UnicodeError/sqlite3.Error at the CLI boundary
now emit one JSON error with original type/message/errno/path/notes/cause chain.
Existing domain failures keep exit1; SystemExit/KeyboardInterrupt and programmer
errors are not swallowed. Missing query source is directly observed exit2 with
FileNotFoundError cause and empty stderr. No retry or timeout increase.
CM224 and legacy21 pass; MI921 has0fail/error,54declared skips,1expectedfailure.
New11-case CLI regressions pass inside CM224. Original RED retained.
CM derived manifest and independently pinned MI source hash updated deliberately
for these reviewed bytes; old manifests/preimages retained. Installed pair stays
unchanged (MI204/CM74), so it does not yet contain these new fixes.
Two independent attackers exhausted credits before verdicts. Parent checks and
runtime evidence passed; independent clearance is UNVERIFIED, never inferred.
No Git/install/dependency/service/ACL change or old evidence deletion occurred.
TWINS: searched unguarded CLI source reads; found6 other source-read sites plus
instruction/output/run-directory/SQLite sites, all covered by the central boundary.
No general JSON-envelope claim is made for argparse usage or programmer errors.
