# Durable memory integrity model

## Contents

1. Memory classes
2. Health dimensions
3. Canary strategy
4. Session persistence
5. Scope and isolation
6. Retrieval quality
7. Staleness and supersession
8. Conflict handling
9. Recovery rules
10. What `HEALTHY` means

## 1. Memory classes

Do not treat every stored representation as the same kind of memory.

### Authoritative source memory

Original files, repository blobs, databases, approved requirements, and other primary sources.

This is truth-bearing input and must be reread when changed.

### Governed project state

Requirements, approvals, plans, evidence, and completion state controlled by Fable when Fable governs the project.

This is the canonical execution state, not a convenience memory.

### Episodic/fact memory

AgentMemory or similar stores that preserve decisions, lessons, conventions, and prior-session facts.

Useful for continuity. Never stronger than the current source.

### Relationship memory

Graphify or another graph/index representing relationships among files, concepts, symbols, and events.

Useful for navigation/discovery. Derived, not authoritative.

### Active working context

The bounded material loaded for the current model call.

Ephemeral and token-limited.

### Summaries

Compressed derived representations. Useful for speed, but inherently lossy unless the task explicitly defines a reversible representation.

## 2. Health dimensions

A durable memory service is not simply up/down. Audit at least these dimensions:

1. **Liveness** — service responds.
2. **Write integrity** — a new record is durably accepted.
3. **Direct read integrity** — written identity can be read back directly where supported.
4. **Retrieval integrity** — search/recall can surface the written item.
5. **Scope integrity** — project/user/agent boundaries return the intended data and do not leak other scope.
6. **Persistence integrity** — memory survives a session or service restart when persistence is promised.
7. **Deletion integrity** — deleted records disappear from direct storage and indexes.
8. **Index consistency** — stored records and retrieval indexes agree.
9. **Staleness integrity** — derived memory is invalidated/reconciled when source truth changes.
10. **Supersession integrity** — outdated versions do not masquerade as current.
11. **Duplicate integrity** — repeated writes do not create uncontrolled conflicting twins.
12. **Provenance integrity** — recalled memory can be traced to its origin where consequential.
13. **Capacity/latency health** — recall remains usable at expected scale.

A liveness probe covers only item 1.

## 3. Canary strategy

A useful canary is:

- unique;
- short enough to survive title/preview truncation;
- scoped exactly like the real memory path being tested;
- harmless;
- deleted after the check unless it is intentionally a bridge canary.

Current-session roundtrip:

```text
health
  -> remember canary
  -> recall canary in same scope
  -> verify returned identity
  -> delete by identity
  -> direct identity must be absent
  -> search must have no ghost
```

Do not return `HEALTHY` before this passes in the current session.

## 4. Session persistence

A same-session roundtrip does not prove persistence across restart/session boundaries.

Use the two-phase bridge:

```text
SESSION A
  -> seed persistence canary
  -> persist canary id + query + scope locally
  -> end session / restart service if that is the boundary under test

SESSION B
  -> health check
  -> direct-id read
  -> scoped recall
  -> verify same canary identity
  -> cleanup
  -> confirm no direct/search ghost
```

Report this separately as `BRIDGE: PERSISTED`.

If the canary is missing after restart, do not infer the old facts from model context. Treat persistence as failed until source or user restores the information.

## 5. Scope and isolation

An empty recall can mean:

- missing data;
- wrong project;
- wrong user;
- wrong agent id;
- isolated-memory mode without an allowed identity;
- wrong environment/data directory;
- wrong server instance;
- index drift.

Before declaring `MISSING`, record:

- endpoint/server instance;
- project scope;
- agent/user scope where available;
- query;
- direct memory id if known;
- data directory/instance when operationally relevant.

Never fix a missing scoped recall by blindly switching to wildcard/global scope in a sensitive project.

## 6. Retrieval quality

Retrieval has two questions:

1. Did it return enough candidates?
2. Are those candidates actually about the user's requested fact?

Do not convert a similarity score into a semantic truth verdict.

For consequential use:

- inspect top candidates;
- prefer direct source-linked facts;
- expand/read the actual stored record when search returns only titles/previews;
- record false positives/false negatives;
- compare with the authoritative source if the fact can change.

`recall-audit` can prove candidate presence. It cannot prove the candidate is correct without inspection.

## 7. Staleness and supersession

Memory can be perfectly retrievable and still wrong because the world/source changed.

Treat a memory as stale when:

- its source hash/version no longer matches;
- the governing project state advanced;
- a newer memory explicitly supersedes it;
- its validity interval expired;
- the data provider corrected history;
- the repository branch/head changed beyond the stored basis.

Preferred pattern:

```text
memory fact
  + origin/source identity
  + knowledge timestamp
  + optional supersedes/superseded-by link
```

If provenance is unavailable, lower trust rather than inventing it.

## 8. Conflict handling

When two memories disagree:

1. Do not merge them into a compromise.
2. Identify scope, timestamp, provenance, and source version for each.
3. Re-read the authoritative source.
4. Mark the obsolete memory superseded/stale where the memory system supports it.
5. Preserve the disagreement as evidence if the source itself is conflicted.

`unknown != false`, `missing != neutral`, and `old != current`.

## 9. Recovery rules

### Service unavailable

Verdict: `BLIND`.

Continue only with direct authoritative sources that are available. Do not claim cross-session recall.

### Write succeeds, recall fails

Verdict: `DEGRADED`.

Check index health, scope, and current API contract. A successful write response is not proof of recall integrity.

### Direct read succeeds, search fails

Likely index/scope problem. Do not duplicate the memory to "make search find it" until root cause is known.

### Search succeeds after delete

Ghost/index inconsistency. Treat deletion as failed.

### Persistence bridge fails

Reconstruct only from source/project state/user input. Do not fill the gap from model priors.

### Recalled fact is stale

Source wins. Refresh derived memory only after reading current source.

## 10. What `HEALTHY` means

Use precise verdicts:

- `MEMORY: HEALTHY` — current-session store/recall/delete/no-ghost path passed.
- `BRIDGE: PERSISTED` — a deliberately seeded canary survived the tested boundary.
- `MEMORY: UNVERIFIED` — service/hits exist, but required proof or topical audit is incomplete.
- `MEMORY: DEGRADED` — partial path worked but another integrity property failed.
- `MEMORY: BLIND` — service/contract unavailable.
- `MEMORY: MISSING` — expected scoped recall did not return enough candidates.

Do not let `HEALTHY` imply source freshness, complete-file coverage, or semantic correctness.
