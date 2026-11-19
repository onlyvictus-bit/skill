Source Windows repair verified under controller Python 3.14.

Six old ownership/startup failures: account user-site was probed before authored
code. Owned launch now disables user-site only in its copied child environment.
Required startup audits and Store userbase/identity checks remain fail closed.

Pipe-holder failure: taskkill returned ERROR Access denied, while the Job closed
only after reader joins. Capture now assigns a suspended root before resume,
terminates through the owned Job, observes active=0 and root native exit, then
releases before pipe joins. Proof is Job-level, not per-descendant native handles.

Two path errors: GetShortPathNameW returned WinError5 on parent-name queries.
The pure path/info tests now select a genuine existing readable 8.3 alias.
Unexpected errors still fail, unchanged long names are not alias coverage, and
long-path acceptance/foreign-path refusal remain explicitly tested.
Microsoft API reference: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getshortpathnamew

The first broader run also exposed one intermittent GO-token CRT sharing refusal.
A real rename-capable test handle reproduces it. Modern GO uses the already
source-bound shared native reader, exact token and size/identity stability;
the immutable legacy transport branch is unchanged.

Final tests: {"expected_failure": 1, "skipped": 54, "success": 866}; MI legacy 38/38 pass. Every one of the prior nine failed
or errored IDs now passes. Source stability was checked across all 204 MI files.
The first full run's stale-manifest error and all RED evidence remain retained.
Native independent review cleared the actual source with runtime scope caveats.

Installed MI200 and CM74 are unchanged. A concrete 9-file update (5 replacement,
4 added tests, zero deletion) is prepared in Install-Plan.json; separate install
approval is required. No Git action, ACL change, package install, timeout increase,
historical selected-runtime retry, real DB, provider call or original deletion.
Store Python3.12, a new release pair, website and live service persistence have
not been newly qualified. The separate legacy model-worker taskkill fallback was
found by recurrence search; no reproduction or repair of that optional path is
claimed. Source regression success is not a universal Windows/product guarantee.
