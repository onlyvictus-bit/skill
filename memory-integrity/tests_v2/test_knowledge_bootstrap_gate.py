"""GO is a bounded, shared read through the already source-bound transport."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parents[1]/'scripts'))
from knowledge_bridge import windows_owned_bootstrap as boot


@unittest.skipUnless(os.name == 'nt', 'Windows native file-sharing proof required')
class SharedGateTests(unittest.TestCase):
    def test_rename_capable_handle_allows_native_read_without_crt_sharing(self):
        from knowledge_bridge.windows_ready_copy import NativeFiles
        token = 'a'*64
        with tempfile.TemporaryDirectory(prefix='owned-go-sharing-') as name:
            root = Path(name); pending = root/'go.tmp'; path = root/'go'
            pending.write_bytes(token.encode('ascii')); os.rename(pending, path)
            holder = NativeFiles()
            try:
                holder.open(path, 0x00010000, 7, 3)  # DELETE access, fully shared.
                with self.assertRaises(PermissionError):
                    path.read_text(encoding='utf-8')
                boot._read_go(path, token, {'NativeFiles': NativeFiles})
            finally:
                holder.close_all()

    def test_wrong_nonascii_and_oversized_tokens_are_refused(self):
        from knowledge_bridge.windows_ready_copy import NativeFiles
        with tempfile.TemporaryDirectory(prefix='owned-go-invalid-') as name:
            for index, raw in enumerate((b'b'*64, b'\xff'*64, b'a'*65, b'a'*63)):
                with self.subTest(raw=raw):
                    path = Path(name)/str(index); path.write_bytes(raw)
                    with self.assertRaises(ValueError):
                        boot._read_go(path, 'a'*64, {'NativeFiles': NativeFiles})


class GateFailureTests(unittest.TestCase):
    def test_read_failure_remains_primary_when_close_also_fails(self):
        original = OSError('CONTROL_READ')
        class Native:
            def open_read(self, path): return 1
            def read(self, handle, limit): raise original
            def close_all(self, error=None):
                if error is not None: error.add_note('CONTROL_CLOSE')
                else: raise OSError('CONTROL_CLOSE')
        with self.assertRaises(OSError) as caught:
            boot._read_go('fixture', 'a'*64, {'NativeFiles': Native})
        self.assertIs(caught.exception, original)
        self.assertIn('CONTROL_CLOSE', original.__notes__)

    def test_close_failure_after_good_read_is_not_accepted(self):
        class Native:
            def open_read(self, path): return 1
            def read(self, handle, limit): return b'a'*64
            def close_all(self, error=None): raise OSError('CONTROL_CLOSE')
        with self.assertRaisesRegex(OSError, 'CONTROL_CLOSE'):
            boot._read_go('fixture', 'a'*64, {'NativeFiles': Native})


if __name__ == '__main__':
    unittest.main()
