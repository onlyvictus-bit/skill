# Watchdog checks

Each check states procedure, evidence, and failure meaning. Do not weaken a check after seeing a bad result.

## 1. Liveness (`status`)

Procedure:

1. `GET /agentmemory/health`.
2. `GET /agentmemory/status`.

Pass condition: both return HTTP 200 with JSON.

Verdict: `UNVERIFIED`, not `HEALTHY`. Liveness proves only that the service responds.

Failure: `BLIND`. Do not make memory-dependent claims.

## 2. Current-session round trip (`roundtrip`)

Procedure, in order:

1. Health check.
2. `POST /agentmemory/remember` with a unique short canary.
3. Require HTTP 201, `success: true`, and nested `memory.id`.
4. `POST /agentmemory/smart-search` for the exact canary in the same project/agent scope.
5. Require the exact id AND exact full canary content (or full compact title); reject malformed search results. Verify direct id/content and requested scope as well.
6. `POST /agentmemory/forget` with that `memoryId`.
7. Require success and `deleted >= 1`.
8. `GET /agentmemory/memories/:id`; require 404.
9. Smart-search the canary again; require no id/title ghost.

Pass: `HEALTHY` for the memory store/recall/delete path in this session.

Store/unreachable failure: `BLIND`. Recall, cleanup, direct-id, or ghost failure after a successful store: `DEGRADED`.

## 3. Real recall audit (`recall-audit`)

Procedure:

1. Smart-search the user's real query in the correct scope.
2. Record hit count, top id, top score, title, and lexical overlap.
3. Compare count with the predeclared `--expect-min`.
4. A human/model must inspect topical correctness before the result is relied upon.

Fewer hits than expected: `MISSING`.

Enough hits: `UNVERIFIED` until topical inspection. The script deliberately does not convert lexical overlap into a semantic-health claim.

Never lower `--expect-min` because the observed result was inconvenient.

## 4. Session bridge

At session start, run liveness plus a round trip before trusting stored context for consequential work. Then recall the specific prior fact/query needed by the task.

At session end, store durable decisions/fixes only when the governing workflow allows it; read back what matters. Memory is derived continuity, not project authority.

## 5. Staleness

For facts that originate in authoritative files or repository state, re-read the source when its hash/version changed. A memory can be perfectly retrievable and still be obsolete.

## Verdicts

- `HEALTHY`: current-session round trip passed.
- `UNVERIFIED`: service is live or hits were returned, but the required proof/audit is incomplete.
- `DEGRADED`: storage/retrieval/cleanup behavior contradicted the expected contract after partial success.
- `BLIND`: service/contract path is unavailable; do not rely on memory.
- `MISSING`: expected scoped recall did not return enough candidates.

## 6. Cross-session persistence bridge — corrected 2026-11-17

The legacy CLI has no qualified independent session/service-boundary observer.
`bridge-seed` stores a unique canary and retains identity/query/scope metadata.
`bridge-verify` checks exact direct id/content and requested scope, exact scoped
search identity/content, confirmed deletion, direct absence and no search ghost.

Even when every readback/cleanup check passes, it returns exit 1 and
`BRIDGE: UNVERIFIED`. It cannot emit `BRIDGE: PERSISTED`. Caller-provided restart
flags or generation numbers cannot upgrade that verdict. The state file remains
as seed evidence; the canary was deleted, so a future boundary test must use a
NEW seed. Never retry a consumed canary as a persistence proof.

A real persistence claim additionally requires a qualified independent observer
of the intended boundary and reuse of the same persistent datastore. Neither is
implemented by this CLI. Graceful restart, crash durability and fresh-session
retrieval are distinct boundaries. Authentication and live API compatibility must
be checked against the explicitly selected backend before a separately authorized
live test. A TEST_ONLY backend never qualifies the real memory service.
