# Ordered Gate1 diagnostic — final review and single verified fix pass

## Independent review

Fresh configured native role fable_sol_reviewer reviewed the complete authored
slice, approved plan/rulings, exact v1 contract/launcher, original test, sealed
helpers/containment/retrieval calls and retained evidence read-only. No worker,
model or original/normal launcher ran. Verdict FIX-FIRST: zero Critical, ONE
Important, zero Minor. Review is of v1 bytes; no second review is claimed.

Important finding: gate1_ordered_runner.validate_ordered_result checked public
mode order and each mode's filtered phase order, but accepted a negative-lease
event after the next mode's public call. This could classify non-contiguous
execution evidence as nonreproduction. It did not turn Gate1/release flags on,
but violated the approved exact-order proof requirement.

The reviewer otherwise verified original method/hash/selection, public24argv/
tenflags/90timeout, shared fixture/replay, actual APIs, original preservation
chain before any new root, equal-depth/length aliases, ordinary/nonadmin/SID and
sealed one-shot launcher, contained captures, failure receipts and false flags.
Reviewed18focused/174policy receipts and logs were consistent; not runtime proof.

## Parent resolution — one fix pass, not an unobserved promise

Final: fixed global phase interleaving — test_replay_crossing_the_next_public_boundary_is_not_ordered_evidence
RED1failure/0errors across19cases o-7c9d5f28, log14d7e9fb...; require the ACTUAL
event list to equal concatenated per-mode blocks in MODES order. Failed subtest
blocks may remain shorter, but cannot cross mode boundaries. Focused GREEN19/19
o-76b0591e/Receipt.json SHAc620097a17bcd8f0522ed0e024f57795195aa30b1577b7c31f99dec3780fc38d,
log9695cf3197e49bd3f32fc0d1bc956c5ea6193f93cf9b84787443580891268400.
Fresh full policy GREEN175/175 o-5d1eaeff/Receipt.json SHA
73aaf760efb3016a3cff17ae72e2a22c7fa3ac12161b7793f3cb08e67afc90d4,
log76c44b7d993068653c175e9ec07c553009e880fb1a6e3fbe63b31e9bc45e8110.
Both0errors/skips/exclusions/expectedfailures/interruption. Parent rechecked raw
log hashes. This closes the one review finding with observed regression proof;
no new independent post-fix SHIP verdict or numerical-runtime pass is claimed.

TWINS: recurrence search across .github/scripts and .github/tests found the
filtered per-mode event validator only in this ordered runner. No unrelated
legacy source, source test, cache or manifest changed for this fix.

V1 authored helper/runner/tests were copied to new private ordered-reviewed-v1
archive before editing; hashes match reviewed versions. V1 contract/launcher
remain at their original names, unrun and superseded. Neither was overwritten.

## Final sealed handoff

Parent accepts ONE approved normal-account ordered diagnostic, not whole Gate1.
Use ONLY Run-Gate1-Ordered-Context-v2.ps1 SHA
1d224ea7fb458086a3c32245c5e262603ef1370bacca4b0d1673a4b94c9b0cdc.
Contract Gate1-Ordered-Contract-20261021-v2.json148842bytes SHA
29b55a9276e0a31fd3c9c28ef28fede2e483321b29f9a69089b844f1302cf12d.
Driver1ea1128b69ad0707753373e2747ece5fbe0243e301e52d207b32b3abd9fa49da;
runner60df7a731965212c7c9fcbdff29166a9ba14e45876c8cd9d4c8f3254c7b22b55;
testsfa736e76168174819b5411f4ea468f4847a44ba73ba9ddf328e60906d38e743a.
All10launcher pins independently compared to actual bytes; deterministic final
contract matches current readable roles/source/old result. PowerShell AST0errors.
Final agent VerifyOnly correctly refused non1001SID before Python. No new source
or runtime attempt exists. No actual normal-account preflight/run was performed.

## Final review declined-to-judge rulings

Each remains UNVERIFIED, not silently accepted. All old guards stay mandatory.

Final: Ruling: normal-account full old-history readability — defer to mandatory
prewrite host check, never skip inaccessible data — cost if wrong: safe stop.

Final: Ruling: selected Python3.12 loaded image/environment — require actual
pinned-image probe before method, no substitution — cost if wrong: safe stop.

Final: Ruling: actual four-mode public/replay/refusal/timing/containment behavior
— require new retained normal run, not policy counts — cost if wrong: inconclusive
or failed diagnostic, never Gate1 completion.

Final: Ruling: original cleanup reproduction/cause — accept only complete actual
captured detail after source/record checks — cost if wrong: cause stays unknown.

Final: Ruling: cleanup repair/intermittency/production conclusion — explicitly
not authorized or proven by this measurement — cost if wrong: no repair claim.

Final: Ruling: real new-root/copy/runner/timeout/link/redirect lifecycle — actual
execution must pass fail-closed capture and preservation — cost if wrong: retained
failure and no repeat, not deleted/hidden evidence.

Final: Ruling: full217cases/fivegroups/24arms/companion/packages/CI/installed smoke
— remain separate incomplete gates — cost if wrong: release/install blocked.

Final: Ruling: release/install/native/model/authentication/security/Git/deploy
readiness — all false/out-of-scope, no inferred authority — cost if wrong: no
outward or unsupported readiness action.

Final: Ruling:19/175controller counts — support only harness/policy behavior, not
selected numerical runtime — cost if wrong: runtime remains unqualified.

Final: Ruling: sandbox SID refusal — proves only refusal-before-Python, not normal
account success — cost if wrong: normal host still stops on its own guards.

Deferred minors: NONE. No duplicate review dispatched. All old source/caches/
receipts/packages retained; no install/Git/security/model/native action occurred.
