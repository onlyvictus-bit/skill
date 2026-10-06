# Memory Integrity — work in progress

An evidence-focused skill for source-reading, audit, recall and recovery workflows.
**This project is not fully built or native-qualified.** Publishing the source
does not establish semantic completeness, production readiness or live AI support.

**This checkout is the R4 development branch.** The R3 archives under `release/`
remain the offline baseline, not a release of this working tree. See
[R4 native-read usage](docs/R4-NATIVE.md); native writes are still disabled.

Memory Integrity is the user-facing skill. **claude-mon is its required companion
engine**, not an optional second skill. Keep the matching pair together and pass
the companion path explicitly; the workflow verifies its contract digest.

## Versions and branches

| Branch | Contents | Evidence boundary |
|---|---|---|
| `main` | R3 / `2.0.0-m11`, the verified offline pair | `TEST_ONLY`; native Beads execution remains disabled |
| `development/r4-native` | R4 read-only native-observation candidate | Work in progress; not packaged or promoted as a new release |

`main` preserves the exact R3 package files and release ZIPs. The development
branch preserves the new observer and its tests without pretending the inherited
R3 manifest is a release manifest for R4. See [status](docs/STATUS.md).

## Repository layout

- `memory-integrity/`: main SKILL.md, workflow, audit modules and tests.
- `claude-mon/`: companion SKILL.md, complete-read engine, ledger and tests.
- `release/`: the matching R3 ZIPs, release manifest and portable verifier.
- `docs/`: public status and usage limitations; no private execution receipts.

No API key, credential configuration, native runtime binary, database, chat
attachment, private host log or generated Python cache is intentionally included.

## Start here

Read [Memory Integrity SKILL.md](memory-integrity/SKILL.md) first and keep its
six evidence states separate. Never claim more than the retained evidence proves.
Read [claude-mon SKILL.md](claude-mon/SKILL.md) for the companion contract.

Python is needed for the executable workflow. From the repository root:

```powershell
python -B memory-integrity/scripts/memory_integrity_workflow.py --help
python -B memory-integrity/scripts/memory_integrity_workflow.py offline-run --help
```

For actual commands, use `--claude-mon-root` to point at this checkout's
`claude-mon` directory. Do not substitute another version without verifying its
contract. See [offline workflow](memory-integrity/references/r2-workflow.md) and
[coordination policy](memory-integrity/references/r3-coordination.md).

To verify the trusted matching R3 archives using standard-library Python:

```powershell
python -B release/Verify-Memory-Integrity-R3.py
```

The verifier checks archive/content hashes, original instruction prefixes and
packaged tests in temporary extraction. Its success is offline test evidence,
not native Beads, live-provider or semantic-comprehension qualification.

For upload-only ChatGPT use without a runner, follow the manual checklist and
label results `MANUAL_REPORTED`. Do not claim strict `READY` or enforced native
dependencies from a manually filled report.

## Beads-inspired features and limits

The offline pair implements dependency-policy checks, blocked-work guards,
fixture branch/merge policy, and a protected companion history ledger. It is
not yet the fully integrated native [Beads](https://github.com/gastownhall/beads)
workflow. A closed task or CLI claim is not accepted audit evidence. A filesystem
owner replacing both ledger and trusted checkpoint is outside the history guarantee.

R4 adds a real read-only observation route, but native writes, effective ownership
fencing, native merge/recovery and comparative qualification remain unfinished.
Do not enable native execution merely because a version check or read succeeds.

## Licensing

MIT — see `LICENSE`. Beads is a separate upstream project; its runtime and
source are not bundled here. Existing source files and notices are preserved
rather than reassigned a license.
