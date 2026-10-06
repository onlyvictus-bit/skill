# R2 companion dispatch handoff

This candidate remains offline-only. `TestOnlyAdapter` is the only adapter
used by the public R2 workflow and every result is `TEST_ONLY`; none of these
paths authorizes a provider call.

## Required profile

The facade supplies a schema-2 profile with the existing token fields plus:

```json
{
  "provider": "test-only",
  "model": "offline-fixture",
  "endpoint": "offline://fixture",
  "purpose": "offline-audit",
  "output_limit": 1000,
  "max_spend": 0
}
```

Use a deterministic injected character counter for the offline workflow:
`counter=lambda text: text`. The persisted final measurement is labelled
`TEST_ONLY`; it cannot be treated as a live-token qualification.

## Per-manifest-chunk flow

For `chunk` from the validated manifest, create exactly one work item with
`work_item_id=chunk["id"]`. `units_text` maps only its ordered primary unit
IDs to strict UTF-8 slices of `source_bytes`. Context belongs in
`context_sections`, using explicit deterministic names such as
`context_before_U000003`. The primary source text is never substituted with
the context payload.

```python
attempt_id, request_digest = runner.prepare(
    db, artifacts_dir, chunk["id"], task_digest, units_text, instructions,
    result_schema, context_sections, task_spec_digest, profile,
    counter=lambda text: text, manifest=manifest, source_bytes=source_bytes,
)
runner.approve(db, attempt_id, "offline-fixture-approval")
approval_id = ledger.issue_approval(
    db, attempt_id, request_digest, profile["provider"], profile["model"],
    profile["endpoint"], profile["purpose"], profile["output_limit"],
    {"max_spend": profile["max_spend"]},
)
runner.dispatch_via_adapter(db, artifacts_dir, adapter, attempt_id, approval_id)
runner.accept(db, artifacts_dir, attempt_id, task_digest, manifest, source_bytes,
              {"provider": profile["provider"], "model": profile["model"],
               "endpoint": profile["endpoint"], "purpose": profile["purpose"],
               "max_output_tokens": profile["output_limit"]})
```

`prepare` validates the manifest/source and stores both in CAS. The serialized
request includes their immutable digests and primary-unit hashes. It also
stores a second CAS record containing the exact final serialized-request token
count, output reserve, context bound, request digest and profile digest, then
appends its digest as `REQUEST_MEASUREMENT_BOUND` in the ledger. `dispatch_via_adapter`
re-verifies every one of those facts before it consumes approval or calls the
adapter. It refuses source-less requests.

## Rich offline responses

The adapter's `("ok", mapping)` payload must map every primary ID to the
full result made for this actual attempt, not to a plain string:

```python
record = results.make_result(source_bytes, manifest, unit_id, task_digest,
                             attempt_id, interpretation, findings=[])
adapter = providers.TestOnlyAdapter([("ok", {unit_id: record})])
```

`runner.accept` rejects empty lists, strings, mismatched task/attempt IDs,
foreign unit IDs, excerpt changes, duplicate/missing rich records, or an
approval whose provider/model/endpoint/purpose/output/spend differs from the
request profile.

If an adapter raises after the dispatch state is written, the attempt is
`DELIVERY_UNKNOWN`. A new `prepare` is blocked until
`runner.record_retry_decision(db, work_item_id, attempt_id, reason)` records
an explicit decision. Saved/validated/accepted attempts must resume rather
than resend.
