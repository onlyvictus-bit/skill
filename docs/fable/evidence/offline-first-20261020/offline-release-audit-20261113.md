# Offline-first release pair — 2026-11-13

Partial: exact accepted-source ZIP pair built and fresh extraction verified. Full
selected-runtime package qualification is pending; RP1–RP3 and Full Gate1 remain
complete. No source repair, reinstall, ACL change, Git write or installation.

Accepted Git source a2a28bf547a9c3e187c89eb6aee9f0b6bd822956: all931files
match Gate1 Inputs. Original15release artifacts, including8ZIPs, remain byte-exact.
All8oldZIPs are stale; latest knowledge-v2 MI missing52/changed15, CMmissing5/changed3.
New engine metadata stays accepted2.0.0-m12, schema2, offline-first-v1 profile;
no m13 source version fabricated. Pair digest bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f.

## Exact local archives

- memory-integrity-offline-v1.zip:661030bytes,195entries,
  SHA256 c3869791951e4fef87256b96ba1944834e1b8cf9144e21a211a904751359e526.
- claude-mon-offline-v1.zip:172663bytes,74entries,
  SHA256 1de54793ae104f24a50f84401733d16d714744ea68dd4cc89e628339fb26a6f0.

Location C:/Users/sakth/Documents/Codex/ofpkg-20261113/release. Only generated
tests_v2/OFFLINE1-CONTENT.json is added per package. All other bytes equal the
accepted source. Deterministic ZIP, exact members/modes/path safety/source closure,
SKILL prefix, historic content manifests and both MI companion pins verified.

## Observed checks

11archive controls,6existing content controls,14newqualification guards PASS.
CM21legacy+213v2 PASS. MI21legacy PASS with scoped literal-loopback fakeHTTP
fixture runner (original4socket.bind errors retained). Public literal workflow:
8initial+fresh-replay arms and11checks PASS_CORE_ONLY_RUNTIME_UNVERIFIED.

First generic MIv2 run857:8FAIL/25ERROR/54SKIP/1XFAIL. Reused exact successful
Gate1 scoped READY fixture and PYTHONNOUSERSITE=1; final complete857run:
799PASS,54SKIP,1knownlive-Dolt XFAIL,1native-containment FAIL,2short-path ERROR.
The33initial failure/error records reduced to3 without changing package bytes.
No assertions/exclusions/timeout changes. All original runs/logs retained.
Native failure: tree-sweep taskkill exit1; shortpath API returns no shortform.
These failures remain unverified until a correct normal-account observation,
not reclassified green or dismissed by source reading. Selected3.12 unused.

The parent actor is SID1003, not approved normalSID1001. New sealed qualifier
uses selected3.12.10 identity/53versions/revision/default120 before/after, fresh
extraction,4fullsuites with1112exact IDs,24runtime/replay arms, owned nativecapture,
case timings/Pythonstacks, source/package/seal postchecks. It uses no cooperating
reader or wall-clock expiry. Guard controls ensure wrong account/input/case/xfail/
skip/support drift fails closed. Old input contract retained; final contract:
48ae4403af413c7f289a4d791cf60e1464a1ff28cf2a2d668dbf406fd1422f97.
Normal output ofpkg-20261113/selected-qualification must remain unused until handoff.

INTENT: the existing builder regenerates historical manifests and ZIPs; this task
requires a separate release pair containing the accepted fixes; the release plan
requires new offline-first artifacts, unchanged historical releases, and
verification after fresh extraction.

TWINS: searched loader.exec_module in both new release scripts; found1other
unprotected import in Verify-Offline-First.py; both imports now suppress bytecode.
Observed RED proved consumer import could write pycache without -B; regression GREEN.
Archive test fixtures now copy only Git-tracked files, excluding untracked caches.

Detailed results: .github/run-artifacts/offline-release-20261113/Release-Audit-Result.json.
Immutable raw logs and fixture histories are intentionally retained.
Exact release source/CI integration, final commit/push and installation stay open.
PENDING: release commit/push and exact-release hosted CI - awaiting your authorization.

Final independent read-only review SHIP for exact normal-account one-run handoff:
launcherbe817711...,helperc379646e...,inputs48ae4403...;22seals match,1112IDs,
14controlsPASS,independentactualVerifyOnlyPASS. Selectedruntime stillUNRUN,
outputabsent. Finalarchiveverifier alsoPASS without CLI-B and all931source
files unchanged, confirming bytecode correction. No required failed check waived.


## CURRENT — exact release pair runtime VERIFIED COMPLETE, 2026-11-13

Normal-account selected Python3.12.10 observed all4extracted suites:
1112cases =1098PASS+13declaredoptional/platformSKIP+1exactdeclared live-DoltXFAIL;
0FAIL/ERROR/exclusion/interruption. Native containment and both short-path cases
that failed under agent account nowPASS. No package bytes changed to obtain this.

24acceptance arms+24freshreplays and11safety checks PASS_BOUNDED_RUNTIME.
69commands(9outerexit0;60acceptance56exit0+4correctrefusalexit2),138rawstreams,
2224durable caseevents/timings and4emptyfatal-stacklogs reconciled. Both exact
Python3.12.10/image observations and53dependencies/revision/default120/user-site
false match before/after. Accepted931files,194+73source maps,195+74extracted
files,6supportfiles,22seals and15historicalreleasefiles unchanged. ActiveHEAD/index
unchanged. Independent raw-result reviewSHIP for this exactpair runtime scope.

Runtime receiptSHA770bf22f3fd8bf7d424523029fc0f4cf1931eeb3795a37046d13aea3f932ecc3
stays immutable with its original pending-raw-review label. Separate final record:
.github/run-artifacts/offline-release-20261113/Package-Acceptance.json
SHA256 57a3e422ccf6d3296fd192a4fcc4a3aab78402bc7c27db24b2295b16d3ed1b7d.
Status OFFLINE_FIRST_PAIR_RUNTIME_VERIFIED_COMPLETE. Original controller REDs,
inputcontracts and earlier handoff records remain historical, not current failure.
Do NOT rerun Run-Extracted-Pair.ps1: selected-qualification is consumed/successful.

Exact ZIPs remain memory-integrity-offline-v1.zip661030bytes/195members
SHA c3869791951e4fef87256b96ba1944834e1b8cf9144e21a211a904751359e526;
claude-mon-offline-v1.zip172663bytes/74members
SHA1de54793ae104f24a50f84401733d16d714744ea68dd4cc89e628339fb26a6f0.
Location C:/Users/sakth/Documents/Codex/ofpkg-20261113/release. Acceptedm12
metadata preserved; only generatedOFFLINE1content manifest added per package.

Release source/CI integration, exact-release hostedCI, newcommit/push, installation,
whole-skill/model/nativeDB/producer-authentication remain separate and unqualified.
Source a2a28bf itself predates generatedOFFLINE1manifests; deliveryCI must test the
final release source/manifest commit, not reuse Gate1/oldCI as that proof.
PENDING: release commit/push and exact-release hosted CI - awaiting your authorization.
