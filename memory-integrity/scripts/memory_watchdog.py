#!/usr/bin/env python3
"""GPT Monitor: fail-closed AgentMemory integrity checks.

Current AgentMemory REST contract (verified against rohitg00/agentmemory):
  GET  /agentmemory/health
  GET  /agentmemory/status
  POST /agentmemory/remember
  POST /agentmemory/smart-search
  POST /agentmemory/forget
  GET  /agentmemory/memories/:id

Commands: status | roundtrip | recall-audit | bridge-seed | bridge-verify
Exit codes: 0 check completed, 1 integrity finding, 2 usage/contract error.
"""

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

TIMEOUT = 30


def call(server, method, path, body=None, secret=None):
    url = server.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if secret:
        req.add_header("Authorization", "Bearer " + secret)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError:
                parsed = {"_raw": raw[:500]}
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        return exc.code, {"_http_error": exc.code, "_detail": detail}
    except Exception as exc:
        return None, {"_transport_error": "%s: %s" % (type(exc).__name__, exc)}


def compact_hits(payload):
    """Return normalized smart-search hits without inventing missing fields."""
    if not isinstance(payload, dict):
        return [], ["unrecognized search body type: %s" % type(payload).__name__]
    raw = payload.get("results")
    if not isinstance(raw, list):
        # Compatibility with older/alternate shapes, but still explicit.
        for key in ("memories", "hits", "items", "data"):
            if isinstance(payload.get(key), list):
                raw = payload[key]
                break
    if not isinstance(raw, list):
        return [], ["unrecognized search shape, top-level keys: %s" % sorted(payload.keys())]

    out = []
    notes = []
    for item in raw:
        if not isinstance(item, dict):
            notes.append("non-object hit encountered")
            continue
        hit_id = item.get("obsId") or item.get("id") or item.get("memoryId")
        text = item.get("title") or item.get("text") or item.get("content") or item.get("summary") or ""
        score = item.get("score", item.get("similarity", item.get("relevance")))
        out.append({"id": hit_id, "text": text, "score": score, "raw": item})
    return out, notes


def scoped_payload(query=None, limit=None, project=None, agent_id=None):
    body = {}
    if query is not None:
        body["query"] = query
    if limit is not None:
        body["limit"] = limit
    if project:
        body["project"] = project
    if agent_id:
        body["agentId"] = agent_id
    return body


def cmd_status(server, secret):
    code, body = call(server, "GET", "/agentmemory/health", secret=secret)
    if code != 200 or not isinstance(body, dict):
        print("MEMORY: BLIND - /agentmemory/health failed (code=%s, err=%s)" % (code, body))
        return 1
    code2, body2 = call(server, "GET", "/agentmemory/status", secret=secret)
    if code2 != 200 or not isinstance(body2, dict):
        print("MEMORY: BLIND - health reachable but /agentmemory/status failed (code=%s, err=%s)" % (code2, body2))
        return 1
    print("MEMORY: UNVERIFIED - AgentMemory is live, but liveness is not a memory proof; run roundtrip in this session")
    return 0


def cmd_roundtrip(server, secret, project=None, agent_id=None):
    hcode, hbody = call(server, "GET", "/agentmemory/health", secret=secret)
    if hcode != 200:
        print("MEMORY: BLIND - AgentMemory health check failed (code=%s, err=%s)" % (hcode, hbody))
        return 1

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    canary = "gpt-monitor-canary-%s-%s" % (stamp, uuid.uuid4().hex[:8])
    remember = {"content": canary, "type": "fact", "concepts": ["gpt-monitor-canary"]}
    if project:
        remember["project"] = project
    if agent_id:
        remember["agentId"] = agent_id

    code, body = call(server, "POST", "/agentmemory/remember", remember, secret)
    memory = body.get("memory") if isinstance(body, dict) else None
    mem_id = memory.get("id") if isinstance(memory, dict) else None
    if code != 201 or not mem_id or body.get("success") is not True:
        print("MEMORY: BLIND - canary store failed current API contract (code=%s, body=%s)" % (code, body))
        return 1

    code, found = call(
        server,
        "POST",
        "/agentmemory/smart-search",
        scoped_payload(canary, 10, project, agent_id),
        secret,
    )
    if code != 200:
        print("MEMORY: DEGRADED - canary stored but smart-search failed (code=%s)" % code)
        _cleanup_canary(server, secret, mem_id)
        return 1
    hits, notes = compact_hits(found)
    matched = [h for h in hits if h["id"] == mem_id or canary in (h["text"] or "")]
    if not matched:
        print("MEMORY: DEGRADED - canary stored but NOT recalled (%d hits)%s" % (
            len(hits), (" [" + "; ".join(notes) + "]") if notes else ""))
        _cleanup_canary(server, secret, mem_id)
        return 1

    dcode, dbody = call(server, "POST", "/agentmemory/forget", {"memoryId": mem_id}, secret)
    if dcode != 200 or not isinstance(dbody, dict) or dbody.get("success") is not True or int(dbody.get("deleted", 0)) < 1:
        print("MEMORY: DEGRADED - canary recall passed but cleanup failed (id=%s, code=%s, body=%s)" % (mem_id, dcode, dbody))
        return 1

    # Direct identity check: storage deletion must be observable.
    qid = urllib.parse.quote(mem_id, safe="")
    gcode, gbody = call(server, "GET", "/agentmemory/memories/%s" % qid, secret=secret)
    if gcode != 404:
        print("MEMORY: DEGRADED - canary delete acknowledged but memory id still resolves (id=%s, code=%s, body=%s)" % (mem_id, gcode, gbody))
        return 1

    code2, found2 = call(
        server,
        "POST",
        "/agentmemory/smart-search",
        scoped_payload(canary, 10, project, agent_id),
        secret,
    )
    if code2 != 200:
        print("MEMORY: DEGRADED - cleanup storage check passed but post-delete recall failed (code=%s)" % code2)
        return 1
    hits2, _ = compact_hits(found2)
    ghosts = [h for h in hits2 if h["id"] == mem_id or canary in (h["text"] or "")]
    if ghosts:
        print("MEMORY: DEGRADED - deleted canary is still searchable (id=%s, ghost_hits=%d)" % (mem_id, len(ghosts)))
        return 1

    scope = []
    if project:
        scope.append("project=%s" % project)
    if agent_id:
        scope.append("agentId=%s" % agent_id)
    suffix = " [%s]" % ", ".join(scope) if scope else ""
    print("MEMORY: HEALTHY - current-session round-trip passed: store -> smart-search -> forget -> no ghost%s" % suffix)
    return 0



def cmd_bridge_seed(server, secret, state_file, project=None, agent_id=None):
    """Seed a canary that must survive into a later session/restart."""
    hcode, hbody = call(server, "GET", "/agentmemory/health", secret=secret)
    if hcode != 200:
        print("BRIDGE: BLIND - AgentMemory health check failed (code=%s, err=%s)" % (hcode, hbody))
        return 1
    state_path = Path(state_file).resolve()
    if state_path.exists():
        print("BRIDGE: ERROR - state file already exists; verify or remove it first: %s" % state_path)
        return 2
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    canary = "gpt-monitor-bridge-%s-%s" % (stamp, uuid.uuid4().hex[:8])
    body = {"content": canary, "type": "fact", "concepts": ["gpt-monitor-bridge"]}
    if project:
        body["project"] = project
    if agent_id:
        body["agentId"] = agent_id
    code, response = call(server, "POST", "/agentmemory/remember", body, secret)
    memory = response.get("memory") if isinstance(response, dict) else None
    mem_id = memory.get("id") if isinstance(memory, dict) else None
    if code != 201 or not mem_id or response.get("success") is not True:
        print("BRIDGE: BLIND - persistence canary store failed (code=%s, body=%s)" % (code, response))
        return 1
    state = {
        "schema_version": 1,
        "memory_id": mem_id,
        "canary": canary,
        "project": project,
        "agent_id": agent_id,
        "seeded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("BRIDGE: SEEDED - canary stored; end/restart the session or memory service, then run bridge-verify with %s" % state_path)
    return 0


def cmd_bridge_verify(server, secret, state_file):
    """Verify a previously seeded canary survived, then clean it up."""
    state_path = Path(state_file).resolve()
    if not state_path.exists():
        print("BRIDGE: ERROR - state file not found: %s" % state_path)
        return 2
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("BRIDGE: ERROR - invalid state file: %s: %s" % (type(exc).__name__, exc))
        return 2
    if state.get("schema_version") != 1 or not state.get("memory_id") or not state.get("canary"):
        print("BRIDGE: ERROR - state file missing required fields")
        return 2
    mem_id = state["memory_id"]
    canary = state["canary"]
    project = state.get("project")
    agent_id = state.get("agent_id")

    hcode, hbody = call(server, "GET", "/agentmemory/health", secret=secret)
    if hcode != 200:
        print("BRIDGE: BLIND - AgentMemory health check failed (code=%s, err=%s)" % (hcode, hbody))
        return 1

    qid = urllib.parse.quote(mem_id, safe="")
    gcode, gbody = call(server, "GET", "/agentmemory/memories/%s" % qid, secret=secret)
    if gcode != 200:
        print("BRIDGE: MISSING - persisted memory id no longer resolves (id=%s, code=%s)" % (mem_id, gcode))
        return 1

    scode, found = call(
        server,
        "POST",
        "/agentmemory/smart-search",
        scoped_payload(canary, 10, project, agent_id),
        secret,
    )
    if scode != 200:
        print("BRIDGE: DEGRADED - direct memory exists but smart-search failed (id=%s, code=%s)" % (mem_id, scode))
        return 1
    hits, notes = compact_hits(found)
    matched = [h for h in hits if h["id"] == mem_id or canary in (h["text"] or "")]
    if not matched:
        print("BRIDGE: DEGRADED - direct memory exists but recall cannot surface it (id=%s, hits=%d%s)" % (
            mem_id, len(hits), (", notes=" + "; ".join(notes)) if notes else ""))
        return 1

    dcode, dbody = call(server, "POST", "/agentmemory/forget", {"memoryId": mem_id}, secret)
    if dcode != 200 or not isinstance(dbody, dict) or dbody.get("success") is not True or int(dbody.get("deleted", 0)) < 1:
        print("BRIDGE: DEGRADED - persistence verified but cleanup failed (id=%s, code=%s, body=%s)" % (mem_id, dcode, dbody))
        return 1
    gcode2, _ = call(server, "GET", "/agentmemory/memories/%s" % qid, secret=secret)
    if gcode2 != 404:
        print("BRIDGE: DEGRADED - cleanup acknowledged but id still resolves (id=%s, code=%s)" % (mem_id, gcode2))
        return 1
    state_path.unlink()
    print("BRIDGE: PERSISTED - canary survived the boundary, remained directly readable and searchable, and cleanup passed")
    return 0

def _cleanup_canary(server, secret, mem_id):
    if not mem_id:
        return False
    code, body = call(server, "POST", "/agentmemory/forget", {"memoryId": mem_id}, secret)
    return code == 200 and isinstance(body, dict) and body.get("success") is True and int(body.get("deleted", 0)) >= 1


def _topic_overlap(query, text):
    qt = {t for t in re.findall(r"[A-Za-z0-9_\-]+", query.lower()) if len(t) > 1}
    tt = {t for t in re.findall(r"[A-Za-z0-9_\-]+", (text or "").lower()) if len(t) > 1}
    return len(qt & tt), len(qt)


def cmd_recall_audit(server, secret, query, expect_min, project=None, agent_id=None):
    limit = max(10, min(100, expect_min * 4))
    code, body = call(
        server,
        "POST",
        "/agentmemory/smart-search",
        scoped_payload(query, limit, project, agent_id),
        secret,
    )
    if code != 200:
        print("MEMORY: BLIND - smart-search request failed (code=%s, body=%s)" % (code, body))
        return 1
    hits, notes = compact_hits(body)
    note = (" [" + "; ".join(notes) + "]") if notes else ""
    if len(hits) < expect_min:
        print("MEMORY: MISSING - query %r returned %d hits, expected >= %d%s" % (query, len(hits), expect_min, note))
        return 1

    top = hits[0]
    overlap, qcount = _topic_overlap(query, top.get("text") or "")
    score = top.get("score")
    print("MEMORY: UNVERIFIED - query %r returned %d hits; top id=%s score=%s title=%r lexical_overlap=%d/%d%s" % (
        query, len(hits), top.get("id"), score, (top.get("text") or "")[:200], overlap, qcount, note))
    print("AUDIT REQUIRED - inspect the returned hit for topical correctness before using it in a consequential decision")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["status", "roundtrip", "recall-audit", "bridge-seed", "bridge-verify"])
    ap.add_argument("--server", default="http://localhost:3111")
    ap.add_argument("--secret", default=None)
    ap.add_argument("--project", default=None)
    ap.add_argument("--agent-id", default=None)
    ap.add_argument("--query", default=None)
    ap.add_argument("--expect-min", type=int, default=1)
    ap.add_argument("--state-file", default=".gpt-monitor-bridge.json")
    args = ap.parse_args()

    if args.command == "status":
        return cmd_status(args.server, args.secret)
    if args.command == "roundtrip":
        return cmd_roundtrip(args.server, args.secret, args.project, args.agent_id)
    if args.command == "bridge-seed":
        return cmd_bridge_seed(args.server, args.secret, args.state_file, args.project, args.agent_id)
    if args.command == "bridge-verify":
        return cmd_bridge_verify(args.server, args.secret, args.state_file)
    if not args.query:
        print("recall-audit needs --query", file=sys.stderr)
        return 2
    if args.expect_min < 1:
        print("--expect-min must be >= 1", file=sys.stderr)
        return 2
    return cmd_recall_audit(
        args.server,
        args.secret,
        args.query,
        args.expect_min,
        args.project,
        args.agent_id,
    )


if __name__ == "__main__":
    sys.exit(main())
