# Verified offline-first ZIP-pair checkpoint — 2026-11-13

AUTH: user said "YES COMMIT AND PUSH".

This backup contains the exact tested release ZIPs, their manifest, new release
builder/verifier/archive controls, Fable status, and byte-exact inert snapshots
of raw qualification evidence. 1112cases:1098PASS/13permittedSKIP/1declaredliveDolt
XFAIL;0FAIL/ERROR.24arms/24freshreplays/11checks,69commands/138streams/2224events.
Windows selectedPython3.12.10 and53dependencies verified before/after. Independent
raw result reviewSHIP. Sourcea2a28bf code is inherited unchanged from parent14cbf4b.
Only generatedOFFLINE1 manifests are added inside the delivered ZIPs.

Final authority is archive/phase/Package-Acceptance.json.snapshot. Raw runtime
pending-review labels remain immutable history; the separate final acceptance
closes that review. Archive-Manifest maps every snapshot to original path/size/hash.
Old absolute paths/one-use launchers are evidence, not reusable commands to run.
Generated SQLite ledger, runtime caches, index, managed copies, retained-temp
trees, private dirty-tree inventory and environments stay local. No credentials
or new model/native binaries are included. Only the two declared ZIPs are binary.

This is a backup branch, not main/development promotion or a published release.
Release-source/manifest and exact-commit CI integration remain separate. Source
commit predates generatedOFFLINE1 manifests, so existing source CI is not asserted
green. This commit does not weaken/skip CI or change package source/workflow code.
Installation, whole-skill/model/nativeDB/semantic truth/authenticated producer
qualification remain unverified. Current development HEAD and index are preserved.
