# Qualification status

The full requested native skill is unfinished. This repository separates a
verified offline baseline from the read-only native development candidate.

## Offline baseline: R3 / m11

The matching release pair has retained offline verification of 383 packaged
tests. Its 79 Memory Integrity and 65 claude-mon content-manifest entries were
hash-checked again for this publication copy; each package also contains its
content manifest. Release ZIP bytes are unchanged.

During publication preparation on 2026-10-06, the portable verifier was rerun
on these exact copied archives: all 383 tests passed, with `TEST_ONLY` evidence
and native qualification false. This is local-copy verification, not a GitHub
readback or an installed/native-runtime observation.

| Feature | Built/tested boundary | Remaining native boundary |
|---|---|---|
| Task dependencies | Complete fixture graph validation, cycle/missing-node refusal and prerequisite evidence checks | Full current native graph/identity observation connected to execution |
| Blocked work | Companion guards preparation, dispatch, approval use, acceptance and later consumption | Effective native ownership/fence and native-to-companion connection |
| Branch merging | Compatible/conflicting fixture policy and retained origin evidence | Observed native ancestry, real compatible/conflicting Dolt merges, fresh post-merge evidence |
| Append-only history | Normal SQL mutation guards, typed replay, hash chain and supplied checkpoints | Integrated native intent/outcome/UNKNOWN and crash/recovery qualification |

## Development: R4

Five baseline package files changed and five new files were added: modified
README.md, docs/STATUS.md, memory-integrity/SKILL.md,
scripts/hybrid_bridge/native.py and scripts/memory_integrity_workflow.py; new
docs/R4-NATIVE.md, memory-integrity/references/m7-native-observation.md,
scripts/hybrid_bridge/native_observation.py,
tests_v2/native_consent_scenarios.json and tests_v2/test_m7_observation.py. The
companion core and shared contract pin are unchanged. Original R3 SKILL.md bytes
are retained as an exact prefix of the R4 instructions.

The retained branch test run, observed 2026-10-06 from each package root,
is fully green: Memory Integrity v1 21/21 and v2 173/173, claude-mon v1
21/21 and v2 190/190, plus eval harness self-tests 7/7 with the good sample
scoring 10/10 and the bad sample 0/10. Total 405 suite tests + 7 eval tests,
zero failures. The two former R3-manifest mismatches are resolved by
committed R4-CONTENT.json manifests (regeneration is an explicit release
action: change files, regenerate, review the diff, commit). The single
deliberate-failure statement below described the pre-manifest state and no
longer applies to this branch.

The observer refuses unknown diagnostics, incomplete or unsupported dependency
data, selected-identity drift and unsafe reads. Reads never activate writes or
turn an observed lease into an effective qualified fence. Actual native reads in
the development host were refused on workspace-gate/database diagnostics.
Direct-child timeout/output-bound handling is tested; descendant process-tree
containment is not qualified. Independent final rereview was unavailable; do
not represent parent-verified repairs as an independent final approval.

## Still required for full completion

1. Clean native observations through the adapter, then protected native
   operations connected to companion evidence/prerequisite guards.
2. Actual native ownership, branch conflict, interrupted recovery and
   OFF/cards/native comparison with retained command/result evidence.
3. Matching successor metadata/contracts/manifests/ZIPs, full checks and review,
   then separately authorized installation and installed public verification.

No live AI call, native-runtime installation, database mutation or global skill
promotion is performed merely by cloning or publishing this repository.

## Public-consent clarification

Before publication, the R4-only SKILL appendix was clarified: an approval from
another project or a pasted historical receipt grants no current-environment
authority. A verified approval for the unchanged exact read-only selection may
be retained without another question. No native code or R3 prefix/ZIP changed.
Three synthetic consumer decision scenarios are retained in
`memory-integrity/tests_v2/native_consent_scenarios.json`. Baseline and corrected
decision checks are not live runtime or general model-compliance qualification.
