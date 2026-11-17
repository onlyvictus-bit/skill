import contextlib
import importlib.util
import io
import json
import threading
import unittest
from unittest.mock import patch
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

    def test_bridge_readback_without_observed_boundary_is_unverified(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            state_file = Path(td) / "bridge.json"
            rc, out = self.capture(mw.cmd_bridge_seed, self.url, None, state_file)
            self.assertEqual(0, rc)
            self.assertTrue(state_file.exists())
            self.assertIn("BRIDGE: SEEDED", out)
            self.assertEqual(1, len(self.state.memories))

            rc2, out2 = self.capture(mw.cmd_bridge_verify, self.url, None, state_file)
            self.assertEqual(1, rc2)
            self.assertIn("BRIDGE: UNVERIFIED", out2)
            self.assertNotIn("BRIDGE: PERSISTED", out2)
            self.assertTrue(state_file.exists())
            self.assertEqual({}, self.state.memories)


class BridgeRefusalTests(unittest.TestCase):
    def exercise(self, fault=None, roundtrip=False):
        import tempfile
        self.deleted = False
        self.requests = []
        def transport(server, method, path, body=None, secret=None):
            self.requests.append((method, path, body))
            if path.endswith('/health'):
                return 200, {'status': 'healthy'}
            if path.endswith('/remember'):
                self.canary = body['content']
                return 201, {'success': True, 'memory': {'id': 'owned', 'content': self.canary}}
            if '/memories/' in path:
                if self.deleted:
                    return (200, {'memory': {'id': 'owned', 'content': self.canary}}) if fault == 'direct-ghost' else (404, {})
                record = {'id': 'owned', 'content': self.canary}
                if fault == 'wrong-direct-content': record['content'] = 'WRONG'
                if fault == 'wrong-direct-id': record['id'] = 'other'
                if fault == 'missing-scope': record.pop('project', None)
                return 200, {'memory': record}
            if path.endswith('/smart-search'):
                if self.deleted:
                    if fault == 'malformed-after': return 200, {'unexpected': []}
                    rows = [{'obsId': 'owned', 'title': self.canary}] if fault == 'search-ghost' else []
                else:
                    rows = [{'obsId': 'other' if fault == 'wrong-search-id' else 'owned',
                             'title': 'WRONG' if fault == 'wrong-search-content' else self.canary}]
                    if fault == 'malformed-before': rows.append('malformed')
                return 200, {'results': rows}
            if path.endswith('/forget'):
                self.deleted = True
                return 200, {'success': True, 'deleted': 'nonsense' if fault == 'malformed-delete' else 1}
            raise AssertionError(path)
        with tempfile.TemporaryDirectory() as td, patch.object(mw, 'call', side_effect=transport):
            path = Path(td)/'bridge.json'
            if roundtrip:
                fn, args = mw.cmd_roundtrip, ('http://fixture', None)
            else:
                self.assertEqual(0, self.capture(mw.cmd_bridge_seed, 'http://fixture', None, path)[0])
                fn, args = mw.cmd_bridge_verify, ('http://fixture', None, path)
            rc, out = self.capture(fn, *args)
            self.assertNotEqual(rc, 0, out)
            self.assertNotIn('BRIDGE: PERSISTED', out)
            self.assertNotIn('MEMORY: HEALTHY', out)
            if fault in ('wrong-direct-content', 'wrong-direct-id', 'wrong-search-id',
                         'wrong-search-content', 'malformed-before') and not roundtrip:
                self.assertFalse(self.deleted, 'retain suspect memory for investigation')
                self.assertIn('BRIDGE: DEGRADED', out)
            if fault in ('search-ghost', 'malformed-after'):
                self.assertTrue(self.deleted)
                self.assertIn('post-delete search absence not proven', out)
            if not roundtrip: self.assertTrue(path.exists(), 'keep seed evidence')
            return out

    def capture(self, fn, *args):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream): rc = fn(*args)
        return rc, stream.getvalue()

    def test_wrong_direct_content_refused(self): self.exercise('wrong-direct-content')
    def test_wrong_direct_identity_refused(self): self.exercise('wrong-direct-id')
    def test_wrong_search_content_refused(self): self.exercise('wrong-search-content')
    def test_wrong_search_identity_refused(self): self.exercise('wrong-search-id')
    def test_search_ghost_refused(self): self.exercise('search-ghost')
    def test_direct_ghost_refused(self): self.exercise('direct-ghost')
    def test_malformed_search_refused(self): self.exercise('malformed-before')
    def test_malformed_post_delete_refused(self): self.exercise('malformed-after')
    def test_malformed_delete_refused_without_crashing(self): self.exercise('malformed-delete')
    def test_same_process_cannot_prove_restart(self):
        self.assertIn('BRIDGE: UNVERIFIED', self.exercise())
    def test_roundtrip_twin_wrong_direct_content(self): self.exercise('wrong-direct-content', True)
    def test_roundtrip_twin_wrong_identity(self): self.exercise('wrong-search-id', True)
    def test_roundtrip_twin_wrong_search_content(self): self.exercise('wrong-search-content', True)

    def test_caller_restart_claim_cannot_upgrade_verdict(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'seed.json'
            path.write_text(json.dumps({'schema_version': 1, 'memory_id': 'owned',
                'canary': 'exact', 'restart_verified': True, 'generation_before': 1,
                'generation_after': 2, 'same_data_identity': True}))
            responses = [(200, {}), (200, {'memory': {'id': 'owned', 'content': 'exact'}}),
                (200, {'results': [{'obsId': 'owned', 'title': 'exact'}]}),
                (200, {'success': True, 'deleted': 1}), (404, {}), (200, {'results': []})]
            with patch.object(mw, 'call', side_effect=responses):
                rc, out = self.capture(mw.cmd_bridge_verify, 'http://fixture', None, path)
            self.assertEqual(rc, 1)
            self.assertIn('BRIDGE: UNVERIFIED', out)

    def test_scoped_direct_record_must_match_scope(self):
        import tempfile
        for record in ({'id':'owned','content':'exact'},
                       {'id':'owned','content':'exact','project':'wrong','agentId':'a'}):
            with self.subTest(record=record), tempfile.TemporaryDirectory() as td:
                path=Path(td)/'seed.json'
                path.write_text(json.dumps({'schema_version':1,'memory_id':'owned',
                    'canary':'exact','project':'p','agent_id':'a'}))
                with patch.object(mw,'call',side_effect=[(200,{}),(200,{'memory':record})]) as call:
                    rc,out=self.capture(mw.cmd_bridge_verify,'http://fixture',None,path)
                self.assertEqual(rc,1)
                self.assertIn('scope mismatch',out)
                self.assertEqual(call.call_count,2)

    def test_invalid_or_duplicate_state_refused_before_transport(self):
        import tempfile
        for raw in ('[]', '{', '{"schema_version":1,"schema_version":1,"memory_id":"m","canary":"x"}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as td:
                path=Path(td)/'seed.json';path.write_text(raw)
                with patch.object(mw,'call') as call:
                    rc,out=self.capture(mw.cmd_bridge_verify,'http://fixture',None,path)
                self.assertEqual(rc,2)
                call.assert_not_called()

    def test_malformed_hit_fields_are_not_silently_accepted(self):
        hits,notes=mw.compact_hits({'results':[{'id':'m','content':['bad']}]})
        self.assertEqual(hits,[])
        self.assertTrue(notes)


if __name__ == "__main__":
    unittest.main()
