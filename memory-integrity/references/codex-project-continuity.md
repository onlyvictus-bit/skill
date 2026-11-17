# Codex project continuity: initialize, verify, refresh

Use when a skill is installed but the project has no durable, discoverable current
checkpoint. Installation and unit tests alone do not initialize a project.
Fable owns canonical state and approvals; saved reviews and the basis are derived.
No service, background hook, automatic global recall or perfect understanding is
provided. Local files can survive a process/context change; real service restart
persistence needs a separately observed service/datastore boundary.

## Initialize a real project

1. Inspect the project's existing AGENTS.md, Fable state, checkpoint and source.
   Reuse them; preserve unrelated instructions. Define a narrow recovery scope.
2. Write a versioned UTF-8 checkpoint of actual current decisions, restrictions,
   unresolved failures and next work, with original-source citations. Author real
   per-unit reviews; never invent observations to get a green ledger. The example
   review schema and commands are in r2-workflow.md. Use the existing public
   memory_integrity_workflow.py offline-run with explicit matching companion,
   source, task, responses-file and NEW run-dir. This remains TEST_ONLY accounting
   of assistant-supplied reviews; it does not dispatch another AI or a backend.
3. Create docs/fable/continuity/Seal-Request.json with this exact structure:

```json
{"schema_version":1,"project_id":"your-project","source":"docs/fable/continuity/Current-Project-v1.txt","run_map":"docs/fable/continuity/run-v1/run-map.json","files":["docs/fable/state.json","AGENTS.md"]}
```

   Every listed file must exist. List all original files whose changes invalidate
   the checkpoint's claims, including the actual code/evidence cited in it.
   This is explicit scope, not a whole-repository coverage claim. The script also
   binds the request, checkpoint, run-map, protected artifacts and installed skill
   inventories. The filesystem owner can replace both basis and source; hashes
   are integrity/accounting, not independent author authentication.
4. Add or merge a project-local AGENTS.md instruction to run the read-only command
   below before relying on prior work, reopen task-relevant original citations,
   stop on stale/missing evidence, and refresh the checkpoint after approved work.
   Use actual explicit installed paths for that machine; preserve existing rules.
5. Seal only after reviewing source/review/approval scope:

```text
python -B <memory-root>/scripts/project_continuity.py --project-root <project> --memory-root <memory-root> --companion-root <claude-mon-root> --seal-request docs/fable/continuity/Seal-Request.json
```

   Sealing writes derived checkpoint metadata. No source or ledger is rewritten.
   It first requires the existing protected verifier to accept the new run. A
   failed candidate remains retained and the current Basis.json is not replaced.

## Resume at session entry

```text
python -B <memory-root>/scripts/project_continuity.py --project-root <project> --memory-root <memory-root> --companion-root <claude-mon-root>
```

This verifies original file hashes and exact installed tool identities before and
after invoking the existing protected run verifier and exhaustive recall. Its
isolated validation process reuses the pinned companion partition rules without
temporary source copies; its Python audit guard rejects writes/network in that
process, not arbitrary OS-level effects by descendants. Existing protected proof
checks remain in place. No credentials, install or live backend are needed.

`VERIFIED_PROJECT_FILE_RECOVERY` means the declared saved records reopened under
that exact basis. It is not real memory-service persistence, whole-project semantic
truth or proof that every future Codex chat follows instructions. `--basis-only`
checks file identity only and cannot establish protected recovery.

## Refresh after legitimate changes

STALE means investigate changed originals; never silently recompute hashes during
resume. Preserve the old checkpoint source, review and run. Create new versioned
ones through the existing workflow, update canonical Fable state, and point the
reviewed Seal-Request at the new run. Re-run sealing with the SHA-256 of the exact
current Basis.json as an explicit replacement lease:

```text
python -B <memory-root>/scripts/project_continuity.py --project-root <project> --memory-root <memory-root> --companion-root <claude-mon-root> --seal-request docs/fable/continuity/Seal-Request.json --expected-basis-sha256 <current-basis-sha256>
```

The previous basis is retained under continuity/history. A publication lock
serializes cooperating writers; an old lock means stop and inspect, never delete
it automatically or retry blindly. Installed skill updates also require reviewed
resealing. Retain failures. Finish with another independent read-only resume.

## Acceptance

Require actual save/reopen behavior, stale/missing/tamper/substitute-tool refusal,
retained prior basis on refresh failure, and a fresh reader receiving only the
project entry point. Report the process, model-context, user-chat and service
boundaries actually observed separately. Never call unexecuted checks passed.
