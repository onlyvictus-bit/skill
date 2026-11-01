"""Deterministic filesystem publication controls; no selected worker runtime."""
import ast
import hashlib
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT/'tests_v2/test_knowledge_windows_owned_process.py'
CONTROL_SHA = '00c837f55f8527cefe361c5421155b2b8a4e51b177296506b9f249613eb223c4'
OLD = b"                'Path('+repr(str(ready))+').write_text(str(child.pid))\\n'\n"
NEW = (b"                'marker=Path('+repr(str(ready))+'); pending=marker.with_name(marker.name+\".ready-tmp\")\\n'\n"
       b"                'pending.write_text(str(child.pid)); pending.rename(marker)\\n'\n")


class FixturePublication(unittest.TestCase):
    def control_source(self):
        raw = SOURCE.read_bytes()
        original = raw if hashlib.sha256(raw).hexdigest() == CONTROL_SHA else raw.replace(NEW, OLD, 1)
        self.assertEqual(hashlib.sha256(original).hexdigest(), CONTROL_SHA,
                         'only the explicitly approved publisher may differ from the original17 control')
        return raw

    def publisher(self, ready):
        tree = ast.parse(self.control_source())
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and
                      node.name == 'test_nested_job_descendant_has_independent_native_exit_proof')
        call = next(node for node in ast.walk(method) if isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'script' and node.func.attr == 'write_text')
        script = eval(compile(ast.Expression(call.args[0]), '<sealed-nested-fixture>', 'eval'),
                      {'__builtins__': {'repr': repr, 'str': str}}, {'ready': ready})
        body = ast.parse(script).body
        child_at = next(index for index, node in enumerate(body) if isinstance(node, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == 'child' for target in node.targets))
        self.assertIsInstance(body[-1], ast.Expr)
        self.assertEqual(ast.unparse(body[-1]), 'time.sleep(60)')
        # Execute just the real publisher, not native Job setup, Popen or sleep.
        return compile(ast.fix_missing_locations(ast.Module(body=body[child_at+1:-1], type_ignores=[])),
                       '<sealed-fixture-publisher>', 'exec')

    def test_only_atomic_publisher_diff_restores_exact_original17_bytes(self):
        raw = self.control_source()
        self.assertEqual(raw.count(NEW), 1, 'the nested PID publisher is still non-atomic')
        self.assertEqual(hashlib.sha256(raw.replace(NEW, OLD, 1)).hexdigest(), CONTROL_SHA)

    def test_marker_is_not_visible_until_complete_pid_bytes_are_published(self):
        with tempfile.TemporaryDirectory(prefix='atomic-pid-publisher-') as name:
            ready = Path(name)/'nested.pid'
            publisher = self.publisher(ready)
            opened, release = threading.Event(), threading.Event()
            original_open = Path.open
            errors = []
            def delayed_open(path, mode='r', *args, **kwargs):
                stream = original_open(path, mode, *args, **kwargs)
                if 'w' in mode and path.parent == ready.parent:
                    opened.set()
                    if not release.wait(5):
                        stream.close()
                        raise TimeoutError('CONTROL_WRITER_RELEASE_NOT_OBSERVED')
                return stream
            def publish():
                try:
                    exec(publisher, {'Path': Path, 'child': SimpleNamespace(pid=4821)})
                except BaseException as error:
                    errors.append(error)
            with patch.object(Path, 'open', delayed_open):
                writer = threading.Thread(target=publish)
                writer.start()
                try:
                    self.assertTrue(opened.wait(5), 'publisher did not open its actual output')
                    self.assertFalse(ready.exists(), 'exists-only reader can see an empty PID marker')
                finally:
                    release.set()
                    writer.join(5)
            self.assertFalse(writer.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(ready.read_text(encoding='utf-8'), '4821')


if __name__ == '__main__':
    unittest.main()
