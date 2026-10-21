# Diagnostic review corrections and normal-account handoff — NOT a skill release

Basis:a9ae630772b2fa299767796daae28e2f3dbd08f9 plus current local diagnostic/test/docs
changes. User requested finishing the existing four work groups and a PowerShell
path if needed. Existing local Tasks1–5 continue; no new commit/push/install or
security change is inferred. All original caches/receipts remain preserved.

## Design/plan use

Brainstorming/Writing Plans/Executing Plans reuse the approved offline-first
design and existing plan/ledger. No redesign, second governor, automatic commit
or skill-mandated workspace deletion. The continuation checklist is appended to
derived/offline-first-release-plan-20261020.md. A/B is diagnostic review/handoff;
C–F depend on actual normal-account results, final bytes and later approvals.

## Independent review obtained, not a repeat of the old unavailable review

Native Fable Sol cache_probe_review completed a bounded read-only review of
a9ae630's diagnostic, tests, helpers, retained results and preservation. Verdict
FIX_FIRST, with two Important findings and one evidentiary field correction:

1. Launcher-only hashing does not bind pyvenv.cfg's actual runtime choice;
   classify ignored stdout/version and could attribute cache behavior to a drifted
   runtime. Bind exact cfg, expected prefix/version and in-arm identities.
2. Package-only preservation does not prove historical receipt preservation.
   Enumerate and content-hash the named external artifacts pre/post every arm.
3. The shard's literal runtime_identity_before_eof=true did not retain identity
   contents. Rename to the narrower control-flow fact and explicitly report
   identity_contents_observed=false.

Reviewer independently confirmed prior10/10 and75/75 receipts,319 protected file
hashes, old host artifact hashes and actual consumed exit103. It ran no runtime,
N3, old host or numerical operation. No external AI consultation occurred.

## Parent fix pass, retained RED then GREEN

Five controls failed before the fix, including a concrete wrong-version input
that the OLD classifier incorrectly labelled repeated relative-cache evidence.
The four other controls expose absent cfg/base/startup/prior-artifact binding.
No product code was changed: only .github diagnostic/test behavior and Fable docs.

- New schema2 refuses old Prepared packets; they are preserved, never edited.
- Exact venv launcher/cfg bytes, version and prefix are bound. A readable base
  binary is hash-bound and drift-tested. An unreadable AppExecAlias is explicitly
  UNVERIFIED_CACHE_CAUSE_ONLY, not silently authenticated.
- Startup JSON must have exact fields/version/cwd/launcher/prefix; control is3.14,
  A/B are matching3.12 identities. Their returned base/prefix values are retained.
- Twelve required historical artifacts bind old Prepared/Inputs/receipt/launcher,
  consumed cache diagnostic inputs/receipt, and cited focused/repository receipts
  and logs. Omission or drift refuses before output, after every arm and at final.
- Both package inventories still include ALL DBs and bytecode. No old baseline
  or exclusion was changed; no deleted/moved file or old-attempt reset.
- Shard field is now worker_startup_completed_before_eof_exit=true;
  identity_contents_observed=false. No numerical/qualification inference.

Private root:.github/run-artifacts/offline-first-20261020/.

| Evidence | Identity |
| --- | --- |
| RED15run/5fail/0error |tests-bae507b2cd824674910607970468f660/Receipt.json SHA3fd754d624c3b221d195d55bff4a1236cdfe56a96c4c191764f50a27b3f1f637; log18f722b4048539524281608cffb528a759cea88891b3cf2edd22b73a5b02c7d2|
| First corrected15/15 |tests-8eb161cbceaf4b6fa057d32c90dab5cd/Receipt.json SHAaf51fe9fb003282612ba7c4fd66faac4e7b4550de3160af1aba6eee26a41ebc1|
| Final repository harness81/81,0 errors/skips/exclusions |tests-2dadb9a4d2fe4c2aa4ada2db7eaef558/Receipt.json SHA06671aa056214ad53644a72c9e3b6739f024e65b7886764a4694c732cb79d361; logb76ef5d6a516c1d101421ce1208ee2de381a09730d5d3f039ca943260f0643f1|

The final suite includes16 diagnostic controls, including unreadable-base claim
limits. These are repository harness tests, not full MI/CM/extracted/runtime CI.
Fresh review found the defects; the parent fixed and tested them. No second
review/independent SHIP of corrected bytes is claimed or required by the selected
one-fix-pass workflow. Final skill/release review is still a separate later gate.

## Rulings

- Ruling: use the reviewer's cache-cause-only alternative, not an extra runtime
  preparation launch. The agent cannot read/resolve the Store alias. Exact cfg
  and matching in-arm versions/prefixes are sufficient ONLY for the scratch
  cache question; exact-base authentication/numerical proof stay unverified.
  Cost if wrong: the experiment may not attribute the original Windows writer;
  it cannot activate a qualification flag or justify a release claim.
- Ruling: preserve the existing Fable ledger/checkout and all files rather than
  create/delete a Superpowers workspace or auto-commit. User constraints and
  approved plan prevail. Cost if wrong: larger retained local disk footprint.

Deferred minors:none reported. No unresolved Important review finding is silently
accepted; normal-context execution, full release and installation are unobserved.

## Newly frozen handoff, not an old command

Private folder:cache-cause-a9ae630-20261020-v2/.
Prepared.json SHA89f8796dfe0ed54b35d3401fc9194d13f62566b8a9ac83b5ff59e843be5fb4cd.
Probe SHA287278ed72aa9251fc6673bf9067bdd9630c14f9b8f892bfa8892a731df74ee1.
Test SHAdb50578d1578d40fe67521a6fca595af6ab9b01107bc6d6c7fa0c20e0e934d08.
pyvenv.cfg SHA79d3400be0f231ad6f2f5cf51f227c8ce4591ad18656e38865f3d00564f8aa6a;
expected Python3.12.10; worker base_binary_authentication=UNVERIFIED_CACHE_CAUSE_ONLY.
Run-Cache-Cause-Normal.ps1 SHA906f6a5b7c6eb50df82db55fa068b9b11053df7ac6926f3e99e5b2a3e7dd38a8.

Launcher checks external hashes of Prepared, checker/imported helpers, controller,
venv launcher and cfg BEFORE Python. Ordinary ancestor checks use DirectoryInfo
type, not provider-only PSIsContainer (observed absent on .Directory objects).
Read-only corrected chain primitive visited15 nodes; PowerShell AST syntax passed.

Actual Windows PowerShell -File -VerifyOnly in the AGENT account was blocked by
its script-execution policy before the script ran. No setting/bypass/alternate
engine workaround was used; this is NOT a successful launcher execution. The
same wrong-account/normal-account behavior is not declared tested from AST checks.
Host call must first run -VerifyOnly; only if that succeeds may the same sealed
launcher run the approved NEW scratch diagnostic. It independently refuses wrong
SID/elevated sessions and any existing normal-attempt directory. No policy/trust/
ACL change, setup, API/model/native backend, deletion or Git write is permitted.

Normal-attempt is still absent. No new3.12 startup or old agent/host/N3 repeat ran.
Source packages remain unchanged. All previously consumed commands remain closed.
If host policy, trust, hashes or access refuse, stop/share the exact result; no
automatic retry, seal replacement, marker deletion or security change.

## Next action

User runs the supplied hash-checked normal-account block ONCE: VerifyOnly first,
then the NEW scratch diagnostic only after successful verification. Share its
printed status and Receipt.json path. This is not full host acceptance or a
completed skill. Analyze that evidence before a product correction. Existing
integrated acceptance, final m13 pair/manifests/ZIPs/extraction/CI, publication and
separately approved target installation still pending. Changes uncommitted; no push.
