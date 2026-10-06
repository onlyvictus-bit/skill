# R2 integrity verifier handoff

`report.verify_run(run_map_path, source_digests_now, claude_mon_root)` is the
only authoritative offline result function in this candidate.  It returns
`VERIFIED_OFFLINE` only after reopening the saved layout; caller-supplied
`READY` strings and digest-looking strings cannot make `ok` true.

The public facade must write a schema-v3 run map with these exact fields:

```text
schema_version, run_dir, generation, source_digests, artifact_digests,
source_id, task_digest, profile_digest
```

`artifact_digests` must bind SHA-256 hashes for `source.bin`, `manifest.json`,
`task.json`, `profile.json`, `scope.json`, `extraction.json`, `semantic.json`,
`ledger.sqlite`, and every request/response CAS path as `artifacts/<sha256>`.
All artifact paths are relative, non-symlinked descendants of `run_dir`.

The facade’s records must be:

```text
task.json:    {schema_version:3, instructions:<text>}
profile.json: {profile fields...}
scope.json:   schema_version/source_id/source_digest/task_digest/generation,
              required_unit_ids in exact manifest unit order
extraction.json: same binding; expected={units:N}, produced={units:N},
                 diagnostics=[], evidence_class=TEST_ONLY, format=utf8-text
semantic.json: same binding; reviews=[{unit_id, reviewer, findings:list,
               unresolved:list, source_digest, task_digest}, ...]
```

For each non-revoked `accepted` ledger row, its response CAS JSON is an offline
provider envelope:

```text
{terminal_state:"ok", evidence_class:"TEST_ONLY",
 results:{unit_id: rich_result_schema2, ...}}
```

Each rich result must have the exact `complete_read_v2.results.make_result`
schema, with its `attempt_id` equal to that accepted ledger attempt and its
`task_digest` equal to the map. Multiple rich unit results may belong to a
chunk work-item attempt. The verifier requires exact total manifest-unit
coverage across all accepted response maps, a consumed approval whose request
hash equals the attempt request hash, and real CAS files for both hashes.

`claude_mon_root` remains explicit in the signature so callers cannot quietly
search for a companion. The verifier performs a pinned schema-v2 handshake
against that root and invokes the companion manifest validator through the
explicit path. The current pinned canonical contract digest is
`d1f80fa59c4bb760cf40108216ccd4bbefd910e9c66144d8c52a23b1ca867571`.
Task and profile identities are recomputed as SHA-256 of canonical JSON with
only their optional self-digest field excluded; an included self-digest that
does not equal that recomputation blocks the run. No embedded digest is
trusted by itself.

`TEST_ONLY` means the supplied offline interpretation fixture was processed;
it never states that a live model was called or that semantic understanding is
proven.
