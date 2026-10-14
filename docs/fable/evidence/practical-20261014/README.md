# Retained practical-fence evidence — 14 October 2026

Status: HISTORICAL_PARTIAL_NOT_RELEASE_READY. These are offline tests and an agent-host setup refusal, not native qualification receipts.

`retained-artifacts.json` preserves 13 original files as Base64-encoded raw bytes, with original byte counts and SHA-256 hashes. Encoding preserves Windows log line endings and immutable historical identities. It is not encryption or a secrecy boundary. No patterned provider/GitHub keys or private-key material were found when the original text was scanned before inclusion. No databases, executable runtimes, pilot workspaces, caches or credentials are included.

The retained files are the original 401-file source baseline; four helper/policy scripts; the fresh test checkpoint; before/after source identity maps; four complete test logs; and the blocked agent-host receipt. Decode each `base64` value, verify its byte count and SHA-256 against its entry, and inspect it as historical evidence. Do not execute recovered helpers from this evidence directory: their relative paths refer to the original isolated workspace layout, recorded in the receipts. The native pilot is not yet integrated or qualified.

Fresh checkpoint identity: `8f3de2b9a467b02f7eae03a0b171fc85efb04321bb40a9d13c56ffd652081154`. The preserved original file remains outside the checkout at `work/R5-practical-fence-20261013/checkpoints/checkpoint-4eeb61499e704108bc50efcbf06526b7/Practical-Checkpoint.json` within the local project workspace.

Observed tests: lease/SQL-template/quarantine10 passed; practical journal plus legacy regressions48 passed; runtime policy4 passed. The separate unfinished integration group ran21 tests with one failure and ten errors. The diagnostic capture script's exit0 establishes capture/hash/AST completion only; it does not override failed test subprocesses or make the candidate ready.

The tests' source was stable during capture. All46 checked prior release and Semantica files matched their baseline hashes. Subsequent commit approval, change-history and archive documents are later additions, not claimed to be present in the pre-commit source snapshot.

Historical receipts correctly say `commit_or_push_performed=false` at capture time. The user's later `COMMIT IT` authorizes a local WIP commit only; it does not retroactively change those receipts or authorize a push.

The [resume checkpoint](../../derived/practical-resume-20261014.md) records the incomplete v2 schema, lease transitions, native transport/consumer/CLI, native race/expiry/interruption proof, review and release work. All native qualification flags remain false; no old content manifest or ZIP was regenerated to hide the unfinished source.
