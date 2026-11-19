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
    written = kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
    if not written:
        error = ctypes.WinError(ctypes.get_last_error())
        error.add_note('GetShortPathNameW fixture path: ' + str(path))
        raise error
    if written >= len(buffer):
        raise OSError('GetShortPathNameW fixture exceeded buffer')
    return buffer.value


def identity_fixture(candidates):
    """Select a real read-only alias without requiring ancestor list access.

    Windows may allow access to the fixture but deny the parent-name query.
    Existing interpreter directories are sufficient for these pure path/info
    checks: no database is opened or initialized by either assertion.
    """
    unavailable = []
    for path in dict.fromkeys(map(str, candidates)):
        try:
            short = short_form(path)
        except OSError as error:
            if getattr(error, 'winerror', None) != 5:
                raise
            unavailable.append(str(path) + ': WinError5 parent-name query denied')
            continue
        if os.path.normcase(short) == os.path.normcase(str(path)):
            unavailable.append(str(path) + ': unchanged long name')
            continue
        print('SHORT_PATH_FIXTURE', {'path': str(path), 'alias': short,
                                     'unavailable_candidates': unavailable})
        return str(path), short
    raise unittest.SkipTest('no usable 8.3 alias in read-only fixture candidates: ' + '; '.join(unavailable))


class PathIdentityTests(unittest.TestCase):
    def test_short_and_long_forms_unify(self):
        if os.name != "nt":
            self.skipTest("Windows short-name forms only")
        with tempfile.TemporaryDirectory(prefix="longdirname-") as temp:
            path, short = identity_fixture([temp, sys.base_prefix, Path(sys.executable).parent])
            self.assertEqual(obs._long_path(short), obs._long_path(path))

    def test_info_accepts_short_database_path(self):
        if os.name != "nt":
            self.skipTest("Windows short-name forms only")
        with tempfile.TemporaryDirectory(prefix="longdirname-") as temp:
            path, short = identity_fixture([temp, sys.base_prefix, Path(sys.executable).parent])
            value = {"database_path": short, "mode": "direct",
                     "issue_count": 0, "config": {"issue_prefix": "mip"}}
            self.assertEqual(obs._info(value, Path(path), "mip"), 0)

    def test_long_database_path_does_not_require_an_83_fixture(self):
        with tempfile.TemporaryDirectory(prefix='longdirname-') as temp:
            value = {'database_path': temp, 'mode': 'direct', 'issue_count': 0,
                     'config': {'issue_prefix': 'mip'}}
            self.assertEqual(obs._info(value, Path(temp), 'mip'), 0)
            value['database_path'] = str(Path(temp)/'another-database')
            with self.assertRaisesRegex(ValueError, 'E_NATIVE_DATABASE_PATH'):
                obs._info(value, Path(temp), 'mip')


if __name__ == "__main__":
    unittest.main(verbosity=1)
