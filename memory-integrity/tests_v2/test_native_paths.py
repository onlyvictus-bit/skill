#!/usr/bin/env python3
"""Native path identity: 8.3 short segments (RUNNER~1) and long segments
(runneradmin) for the same database must compare equal, never as a foreign
database. Stdlib only; Windows long-path proof runs on Windows."""
import ctypes
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hybrid_bridge import native_observation as obs  # noqa: E402


def short_form(path):
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR,
                                           wintypes.DWORD]
    kernel32.GetShortPathNameW.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    if not kernel32.GetShortPathNameW(str(path), buffer, 32768):
        raise OSError("no short form")
    return buffer.value


class PathIdentityTests(unittest.TestCase):
    def test_short_and_long_forms_unify(self):
        if os.name != "nt":
            self.skipTest("Windows short-name forms only")
        with tempfile.TemporaryDirectory(prefix="longdirname-") as temp:
            self.assertEqual(obs._long_path(short_form(temp)),
                             obs._long_path(temp))

    def test_info_accepts_short_database_path(self):
        if os.name != "nt":
            self.skipTest("Windows short-name forms only")
        with tempfile.TemporaryDirectory(prefix="longdirname-") as temp:
            value = {"database_path": short_form(temp), "mode": "direct",
                     "issue_count": 0, "config": {"issue_prefix": "mip"}}
            self.assertEqual(obs._info(value, Path(temp), "mip"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
