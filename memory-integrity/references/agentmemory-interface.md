# AgentMemory interface used by GPT Monitor

Verified against `rohitg00/agentmemory` default-branch source surfaced at commit `ab3e4efd282659b87d31b36c8514c6bc6b871f0b` on 2026-09-29. Treat future contract drift as an error to inspect, not a reason to invent a fallback.

## Server

Default REST/MCP HTTP endpoint: `http://localhost:3111`.

Related defaults in current upstream: streams `3112`, viewer `3113`, iii worker WebSocket `49134`.

When `AGENTMEMORY_SECRET` is configured, send `Authorization: Bearer <secret>`.

## Endpoints required by this skill

| Method | Path | Purpose |
|---|---|---|
| GET | `/agentmemory/health` | Health/liveness state |
| GET | `/agentmemory/status` | Detailed service status |
| POST | `/agentmemory/remember` | Store durable memory |
| POST | `/agentmemory/smart-search` | Hybrid recall |
| POST | `/agentmemory/forget` | Delete by `memoryId` or session scope |
| GET | `/agentmemory/memories/:id` | Direct identity readback |

### Remember

Request fields used here:

```json
{
  "content": "...",
  "type": "fact",
  "concepts": ["..."],
  "project": "optional",
  "agentId": "optional"
}
```

Current success response is HTTP `201` and contains `success: true` plus a nested `memory` object with its `id`.

### Smart search

Request fields used here:

```json
{
  "query": "...",
  "limit": 10,
  "project": "optional",
  "agentId": "optional"
}
```

Current compact results use fields such as `obsId`, `sessionId`, `title`, `type`, `score`, and `timestamp`. They do **not** guarantee full memory text in the compact result. The watchdog therefore matches the short canary by id/title and uses `/memories/:id` for direct deletion verification.

### Forget

For the canary:

```json
{"memoryId": "mem_..."}
```

Current success response is HTTP `200` with `success: true` and a numeric `deleted` count.

## Scope

AgentMemory can scope writes/search by `project` and `agentId`. Empty recall can mean the wrong scope, not necessarily lost data. Record the queried scope before declaring `MISSING`.

Current upstream also supports isolated agent scope; when isolation is enabled without an available agent id, smart-search fails closed rather than reading cross-agent rows.

## Why the uploaded first version was unsafe

The earlier watchdog targeted `/health`, `/v1/status`, `/v1/memories`, and `/v1/recall`. Those are not the current primary AgentMemory paths above. It also expected recall hits to contain full text and expected a top-level stored id. The repaired watchdog binds itself to the current contract and reports a contract failure instead of claiming health.
