# Supplementary historical RP2 Linux evidence - 2026-11-07

Status: EXTERNAL_RESULTS_REPORTED_RAW_EXECUTION_VALIDATION_PENDING.
AUTH: user said "COMMIT AND PUSH IT, IF NEED SEND THE CODE TO RUN IN POWER SHELL".

Six supplied artifacts are preserved byte-exactly. The .crdownload contains
parseable Python matching the briefing's hash; archive as a .py.snapshot, not as
an installed/trusted verifier. Original Downloads and attachment files unchanged.
All 3,845 supplied lines were read. No supplied command or Linux test ran here.

Local consistency checks: acceptance snapshot 16,283 bytes SHA
feb82bdbecfa8fef0c37ba72f7d4601b4fb0febea05e6cb101adc5aa1f078369 matches Git
e801c3587e5bb87e7ea85bbdbf1ab6edd3b245ef, tree
48264d0700abe1f012e3da79199941595f92ac42. Exactly 55 unique reported IDs equal
its 54 knowledge skips plus one compatibility skip. Records report 55 PASS/exit0,
41 runtime+4 parser+6 model+3 POSIX+1 symlink, summed elapsed 326.558 seconds.
Separate rerun summary has same IDs. This checks reports, not actual execution.

Limitations found in line-by-line review:
1. Bundle JSON has hashes/summary lines, no raw stdout/stderr. Full execution
records, commands,cwd,module-origin evidence, environment and artifact manifest
and evidence ZIP were not supplied. The briefing's raw-log inclusion claim is
unsupported by this JSON. Existing raw artifacts must be obtained and checked.
2. Harness lines 909-919 mark remaining exit0 as PASS without requiring OK or
Ran 1 test, weaker than briefing's claimed classification contract.
3. Lines 1960-1964 create a single post-run source manifest and write that same
object as BEFORE and AFTER. This does not prove preservation during execution.
4. Gate/rerun timestamps Nov4, filenames/purpose Nov5, final bundle Nov6 require
separate run provenance. Do not invent chronology or merge them as one run.
5. Tested e801c358 differs from final a2a28bf in recursive_bootstrap.py; policy
matches. No transfer of Linux3.12.16 verdict to latest code or Windows3.12.10.

Decision: evidence-only descendant of a2a28bf. Keep original report claims intact
as imported data, qualified by this review. No production/test changes or edits
to old skips/accepted receipts. Completed focused RP2/RP3 status is preserved.
This does not close full Gate1, release, installation or latest-code Linux proof.
First validate existing raw artifacts before deciding whether reruns are needed.
No install, download, runtime execution, source overlay, ACL change or cleanup.
