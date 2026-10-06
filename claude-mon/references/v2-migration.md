# v2 migration (claude-mon)

v1 and v2 share no trust. v1 receipts, COMPLETE marks, manifests, and
ledgers are read as historical input and labeled LEGACY_UNVERIFIED; they
cannot satisfy v2 gates, and no importer promotes them automatically.

To migrate a v1 run: re-freeze its sources with v2 inventory (new digests),
rebuild manifests with v2 partition, re-validate, and re-execute through
the v2 runner. Reuse exact byte snapshots only after validation passes.
Delete nothing: failed v1 attempts remain visible as history.

Ledger databases migrate v2-schema to v3-schema automatically on open
(new nullable columns only); older or foreign schemas are rejected, never
guessed. Deployment to an existing live or shared store is a separate
approval boundary outside this document.
