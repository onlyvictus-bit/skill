# Remediation authorization and proof contract

Source: Victus `development/victus-judge-r4-remediation`. Derived operation instructions subordinate to the canonical Fable requirements and system authorization.

- **Hidden SPARQL reads**: arbitrary justification strings never grant access. A trusted issuer must supply an out-of-repository `SPARQL_HIDDEN_APPROVAL_KEY` and an approval containing `graph_sha256` and HMAC-SHA256 `signature`; signed bytes are `sparql-hidden:` followed by lowercase sha256 of canonical JSON graph.
- **GraphRAG**: a trusted issuer must supply `GRAPHRAG_APPROVAL_KEY`; sign `graphrag:<approver>:<project_id>:<graph_sha256>`. The graph object must contain that exact `project_id`, and every query verifies the same graph digest. Mutation or cross-project reuse fails closed. The HMAC itself is not proof of human permission when signing key custody is unknown.
- **Independent reviewer witness**: use `INDEPENDENT_REVIEW_WITNESS_KEY` supplied by a trusted issuer outside the subject model's control; HMAC message `review:<reviewer_id>:<producer_id>:<run_id>:<artifact_digest>:<oracle_digest>`. Refuse absent/incorrect signatures. A synthetic signed test does not establish a real independent reviewer.
- **Wheel provenance**: a real Semantica wheel's `semantica/__init__.py` RECORD digest was identical in four hosted jobs. The pin proves only that member. The verifier parses CSV RECORD, compares hashes and checks installed bytes for fully pinned distributions, but **returns UNVERIFIED** while RECORD contains unpinned hashed entries; it never upgrades partial observations to VERIFIED.
- **Bitemporal mutation**: retraction/correction require explicit valid normalized UTC timestamps. Unknown timestamps are rejected, not silently interpreted as the end of time.
- **Release**: v1 ZIPs are retained immutable. New content lives in `knowledge-bridge-v2`, two v2 archives plus `Knowledge-Bridge-Manifest-v2.json`. The release builder validates bundled tests and source parity. No deployed-version assertion is authorized or made.

## Evidence snapshots and unclosed gates

- RED adversarial run: `37931932607` (original defects reproduced)
- RED metadata forgery run: `37934028726` (altered installed bytes accepted before fix)
- Exact-head all-OS matrix success before latest wheel-byte change: `37933284257`, commit `f60953c`
- V2 portable builder with wheel-byte fix: `37934182396`, success, artifact commit `b221ece`
- Full exact-head CI, native real signer identity/key custody, complete wheel pin coverage and Fable specialist completion gate are **OPEN pending evidence**. Do not mark REQ-24..31 closed from this document.

No credentials, signing keys, external user identifiers, or live activation are stored here. This derived note never grants approval.
