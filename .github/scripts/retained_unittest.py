"""Retained, scratch-scoped unittest runner; never reported as unchanged CI.

SQLite transient journal housekeeping is not an OS-level no-delete guarantee.
"""
import argparse
import hashlib
import fnmatch
import faulthandler
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--pattern', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--test-dir', default='tests_v2')
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--stack-after', type=int, default=0)
    args = parser.parse_args()
    package = args.package_root.resolve(strict=True)
    from offline_release_acceptance import new_output, outside_packages
    output = args.output_dir.absolute()
    if output.is_relative_to(package):
        raise ValueError('E_TEST_OUTPUT_IN_PACKAGE')
    outside_packages(output, [package])
    output = new_output(output)
    scratch = output/'retained-temp'
    scratch.mkdir()
    tempfile.tempdir = str(scratch)
    for name in ('TEMP','TMP','TMPDIR'):
        os.environ[name] = str(scratch)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    class RetainedDirectory:
        def __init__(self, suffix=None, prefix=None, dir=None, **unused):
            self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        def __enter__(self): return self.name
        def __exit__(self, *unused): pass
        def cleanup(self): pass
    tempfile.TemporaryDirectory = RetainedDirectory
    def retained_file(mode='w+b', buffering=-1, encoding=None, newline=None,
                      suffix=None, prefix=None, dir=None, errors=None, **unused):
        fd, _path = tempfile.mkstemp(suffix=suffix or '', prefix=prefix or 'stream-', dir=dir)
        return os.fdopen(fd, mode, buffering=buffering, encoding=encoding,
                         newline=newline, errors=errors)
    tempfile.TemporaryFile = retained_file
    def audit(event, values):
        if event in ('os.remove', 'os.rmdir', 'shutil.rmtree'):
            # User-approved exception: only new files under this invocation's
            # exclusive scratch root. Receipts/logs and prior runs are outside.
            candidate = Path(os.fsdecode(values[0])).absolute()
            if not candidate.resolve().is_relative_to(scratch.resolve()) or candidate == scratch:
                raise PermissionError('OFFLINE_RELEASE_RETAIN_FILES: ' + event)
            for part in (candidate, *candidate.parents):
                if part == scratch.parent:
                    break
                if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
                    raise PermissionError('OFFLINE_RELEASE_NO_REDIRECTED_CLEANUP')
            if candidate.is_file() and candidate.stat().st_nlink != 1:
                raise PermissionError('OFFLINE_RELEASE_NO_LINKED_CLEANUP')
            if len(values) > 1 and values[1] not in (None, -1):
                raise PermissionError('OFFLINE_RELEASE_NO_DIRFD_CLEANUP')
        if event in ('socket.connect', 'socket.bind', 'socket.getaddrinfo'):
            raise PermissionError('OFFLINE_RELEASE_NO_NETWORK: ' + event)
        if event == 'subprocess.Popen' and Path(str(values[0])).name.lower() in ('bd','bd.exe','dolt','dolt.exe','pip','pip.exe'):
            raise PermissionError('OFFLINE_RELEASE_NO_NATIVE_OR_INSTALL')
    sys.addaudithook(audit)
    os.chdir(package)
    sys.path.insert(0, str(package))
    tests = (package/args.test_dir).resolve(strict=True)
    if not tests.is_relative_to(package):
        raise ValueError('E_TEST_ROOT_ESCAPE')
    sys.path.insert(0, str(tests))
    suite = unittest.defaultTestLoader.discover(str(tests), pattern=args.pattern)
    def cases(group):
        for item in group:
            if isinstance(item, unittest.TestSuite):
                yield from cases(item)
            else:
                yield item
    discovered = list(cases(suite))
    excluded = [t.id() for t in discovered if any(fnmatch.fnmatchcase(t.id(), p) for p in args.exclude)]
    suite = unittest.TestSuite(t for t in discovered if t.id() not in excluded)
    class ReportingRunner(unittest.TextTestRunner):
        def _makeResult(self):
            self.active_result = super()._makeResult()
            return self.active_result
    interrupted = False
    fault = None
    if args.stack_after:
        if not 1 <= args.stack_after <= 60:
            raise ValueError('E_STACK_DEADLINE')
        fault = (output/'Slow-Stack.log').open('xb')
        faulthandler.dump_traceback_later(args.stack_after,file=fault)
    with (output/'unittest.log').open('x', encoding='utf-8') as stream:
        runner = ReportingRunner(stream=stream, verbosity=2)
        try:
            result = runner.run(suite)
        except KeyboardInterrupt:
            result = runner.active_result
            interrupted = True
            stream.write('\nINTERRUPTED_NO_AGGREGATE_VERDICT\n')
        finally:
            if fault is not None:
                faulthandler.cancel_dump_traceback_later()
                fault.close()
    raw = (output/'unittest.log').read_bytes()
    receipt = {'scope':'RETAINED_LOCAL_SCOPED_TEMP_CLEANUP_NOT_UNCHANGED_CI','pattern':args.pattern,
               'tests_run':result.testsRun,'failures':[t.id() for t,_ in result.failures],
               'errors':[t.id() for t,_ in result.errors],
               'skipped':[(t.id(),why) for t,why in result.skipped],
               'expected_failures':[t.id() for t,_ in result.expectedFailures],
               'interrupted':interrupted,'discovered':len(discovered),'excluded':excluded,
               'log':str(output/'unittest.log'),'log_sha256':hashlib.sha256(raw).hexdigest()}
    (output/'Receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt));print(raw.decode('utf-8')[-4500:])
    return 0 if result.wasSuccessful() and result.testsRun and not interrupted else 1


if __name__ == '__main__':
    raise SystemExit(main())


