import contextlib
import importlib.util
import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "memory_watchdog.py"
spec = importlib.util.spec_from_file_location("memory_watchdog", SCRIPT)
mw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mw)


class State:
    def __init__(self):
        self.memories = {}
        self.next_id = 1
        self.paths = []


class Handler(BaseHTTPRequestHandler):
    state = None

    def log_message(self, *args):
        pass

    def _json(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        self.state.paths.append(("GET", self.path))
        if self.path == "/agentmemory/health":
            return self._json(200, {"status": "healthy", "service": "agentmemory"})
        if self.path == "/agentmemory/status":
            return self._json(200, {"service": {"status": "ok"}})
        if self.path.startswith("/agentmemory/memories/"):
            mid = self.path.rsplit("/", 1)[-1]
            if mid in self.state.memories:
                return self._json(200, {"memory": self.state.memories[mid]})
            return self._json(404, {"error": "not found"})
        return self._json(404, {"error": "unknown"})

    def do_POST(self):
        self.state.paths.append(("POST", self.path))
        body = self._body()
        if self.path == "/agentmemory/remember":
            mid = f"mem_{self.state.next_id}"
            self.state.next_id += 1
            content = body["content"]
            mem = {"id": mid, "content": content, "title": content[:80], "type": body.get("type", "fact")}
            self.state.memories[mid] = mem
            return self._json(201, {"success": True, "memory": mem})
        if self.path == "/agentmemory/smart-search":
            q = body.get("query", "")
            results = []
            for m in self.state.memories.values():
                if q in m["content"] or m["content"] in q:
                    results.append({"obsId": m["id"], "title": m["title"], "type": m["type"], "score": 1.0})
            return self._json(200, {"mode": "compact", "results": results, "lessons": []})
        if self.path == "/agentmemory/forget":
            mid = body.get("memoryId")
            deleted = 1 if self.state.memories.pop(mid, None) else 0
            return self._json(200, {"success": True, "deleted": deleted})
        return self._json(404, {"error": "unknown"})


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.state = State()
        Handler.state = self.state
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def capture(self, fn, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fn(*args)
        return rc, buf.getvalue()

    def test_status_uses_current_agentmemory_api_and_does_not_claim_healthy(self):
        rc, out = self.capture(mw.cmd_status, self.url, None)
        self.assertEqual(0, rc)
        self.assertIn("UNVERIFIED", out)
        self.assertNotIn("MEMORY: HEALTHY", out)
        self.assertIn(("GET", "/agentmemory/health"), self.state.paths)
        self.assertIn(("GET", "/agentmemory/status"), self.state.paths)

    def test_roundtrip_uses_current_api_and_cleans_canary(self):
        rc, out = self.capture(mw.cmd_roundtrip, self.url, None)
        self.assertEqual(0, rc)
        self.assertIn("MEMORY: HEALTHY", out)
        self.assertEqual({}, self.state.memories)
        methods_paths = set(self.state.paths)
        self.assertIn(("POST", "/agentmemory/remember"), methods_paths)
        self.assertIn(("POST", "/agentmemory/smart-search"), methods_paths)
        self.assertIn(("POST", "/agentmemory/forget"), methods_paths)

    def test_recall_audit_reads_compact_result_titles(self):
        self.state.memories["mem_99"] = {
            "id": "mem_99",
            "content": "deployment steps use blue green",
            "title": "deployment steps use blue green",
            "type": "fact",
        }
        rc, out = self.capture(mw.cmd_recall_audit, self.url, None, "deployment steps", 1)
        self.assertEqual(0, rc)
        self.assertIn("returned 1 hits", out)
        self.assertIn("deployment steps", out)

    def test_bridge_seed_and_verify_proves_persisted_canary_and_cleans_it(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            state_file = Path(td) / "bridge.json"
            rc, out = self.capture(mw.cmd_bridge_seed, self.url, None, state_file)
            self.assertEqual(0, rc)
            self.assertTrue(state_file.exists())
            self.assertIn("BRIDGE: SEEDED", out)
            self.assertEqual(1, len(self.state.memories))

            rc2, out2 = self.capture(mw.cmd_bridge_verify, self.url, None, state_file)
            self.assertEqual(0, rc2)
            self.assertIn("BRIDGE: PERSISTED", out2)
            self.assertFalse(state_file.exists())
            self.assertEqual({}, self.state.memories)


if __name__ == "__main__":
    unittest.main()
