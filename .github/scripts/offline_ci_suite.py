"""Run one complete portable suite with retained per-case diagnostics.

This runner is CI-only.  It never selects an alternate runtime, filters tests,
or changes package bytes.  Its output directory must be a new sibling outside
the package under test.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
import unittest


ALLOWED_TEST_DIRS = {'tests', 'tests_v2', '.github/tests'}
CI_METADATA = {'pythonlocation', 'python_root_dir', 'python2_root_dir', 'python3_root_dir'}


def need(value, code):
    if not value:
        raise ValueError('E_OFFLINE_CI_SUITE_' + code)


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + '\n')


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def detail(err):
    if isinstance(err, tuple):
        return ''.join(traceback.format_exception(*err))
    return str(err)


def hosted_environment(env, scratch):
    """Create an explicit hosted-test fixture; never change the account profile."""
    result = dict(env)
    if result.get('GITHUB_ACTIONS') != 'true':
        return result
    removed = {key: result.pop(key) for key in list(result) if key.casefold() in CI_METADATA}
    source_home = Path(result.get('HOME') or result.get('USERPROFILE') or Path.home())
    source = source_home/'.gitconfig'
    data = b''
    existed = source.exists()
    if existed:
        need(source.is_file() and not source.is_symlink() and source.stat().st_nlink == 1 and
             source.stat().st_size <= 65536, 'HOSTED_GIT_CONFIG')
        data = source.read_bytes()
    home = scratch/'ci-git-home'
    home.mkdir()
    (home/'.gitconfig').write_bytes(data)
    result['HOME'] = str(home)
    save(scratch/'CI-Environment.json', {'scope': 'HOSTED_TEST_PROCESS_ONLY',
         'metadata_keys_removed': sorted(removed), 'original_config_present': existed,
         'config_sha256': hashlib.sha256(data).hexdigest(), 'fixture_home': str(home),
         'original_home_unchanged': True})
    return result


class Events(unittest.TextTestResult):
    def __init__(self, *args, events, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = events
        self.started = {}
        self.outcomes = {}

    def event(self, value):
        self.events.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + '\n')
        self.events.flush()

    def startTest(self, test):
        ident = test.id()
        self.started[ident] = time.monotonic()
        self.event({'event': 'START', 'id': ident, 'monotonic': self.started[ident]})
        super().startTest(test)

    def set_outcome(self, test, outcome, cause=''):
        self.outcomes[test.id()] = {'outcome': outcome, 'cause': cause}

    def addSuccess(self, test):
        self.set_outcome(test, 'success'); super().addSuccess(test)

    def addFailure(self, test, err):
        self.set_outcome(test, 'failure', detail(err)); super().addFailure(test, err)

    def addError(self, test, err):
        self.set_outcome(test, 'error', detail(err)); super().addError(test, err)

    def addSkip(self, test, reason):
        self.set_outcome(test, 'skipped', str(reason)); super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.set_outcome(test, 'expected_failure', detail(err)); super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.set_outcome(test, 'unexpected_success'); super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.set_outcome(test, 'failure' if issubclass(err[0], test.failureException) else 'error', detail(err))
        super().addSubTest(test, subtest, err)

    def stopTest(self, test):
        ident = test.id()
        value = self.outcomes.get(ident, {'outcome': 'incomplete', 'cause': ''})
        self.event({'event': 'END', 'id': ident, 'seconds': time.monotonic() - self.started[ident],
                    **value})
        super().stopTest(test)


class Runner(unittest.TextTestRunner):
    def __init__(self, *args, events, **kwargs):
        self.events = events
        self.active_result = None
        super().__init__(*args, **kwargs)

    def _makeResult(self):
        self.active_result = Events(self.stream, self.descriptions, self.verbosity, events=self.events)
        return self.active_result


@contextmanager
def memory_integrity_ready_fixture(package, scratch):
    if package.name != 'memory-integrity':
        yield
        return
    scripts = str(package / 'scripts')
    sys.path.insert(0, scripts)
    try:
        from knowledge_bridge import windows_ready_copy as ready
        original, default = ready.ReadyCopy.__init__, ready.default_root

        def fixture_init(channel, source, token, *, root=None):
            if root is None and ready.default_root is default:
                root = scratch / 'managed' / 'ready-copies-v1'
            return original(channel, source, token, root=root)

        ready.ReadyCopy.__init__ = fixture_init
        try:
            yield
        finally:
            ready.ReadyCopy.__init__ = original
    finally:
        sys.path.remove(scripts)


def parse(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--test-dir', required=True)
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--output-dir', type=Path, required=True)
    return parser.parse_args(argv)


def run(argv=None):
    args = parse(argv)
    package = args.package_root.resolve(strict=True)
    need(package.is_dir(), 'PACKAGE_ROOT')
    need(args.test_dir.replace('\\', '/') in ALLOWED_TEST_DIRS, 'TEST_DIR')
    tests = (package / args.test_dir).resolve(strict=True)
    need(tests.is_dir() and tests.is_relative_to(package), 'TEST_ROOT')
    output = args.output_dir.resolve(strict=False)
    need(not output.exists(), 'OUTPUT_EXISTS')
    need(not output.is_relative_to(package), 'OUTPUT_IN_PACKAGE')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    scratch = output / 'retained-temp'
    scratch.mkdir()
    event_path = output / 'Cases.jsonl'
    log_path = output / 'unittest.log'
    old_cwd, old_path = Path.cwd(), list(sys.path)
    old_tempdir = tempfile.tempdir
    affected = {'TEMP', 'TMP', 'TMPDIR', 'PYTHONDONTWRITEBYTECODE', 'HOME'}
    affected.update(key for key in os.environ if key.casefold() in CI_METADATA)
    old_env = {name: os.environ.get(name) for name in affected}
    old_directory = tempfile.TemporaryDirectory
    old_bytecode = sys.dont_write_bytecode
    result = None
    failure = None
    interrupted = False
    discovered = []
    try:
        tempfile.tempdir = str(scratch)
        for name in ('TEMP', 'TMP', 'TMPDIR'):
            os.environ[name] = str(scratch)
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        sys.dont_write_bytecode = True
        class RetainedDirectory:
            def __init__(self, suffix=None, prefix=None, dir=None, **unused):
                self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
            def __enter__(self): return self.name
            def __exit__(self, *unused): return False
            def cleanup(self): pass
        tempfile.TemporaryDirectory = RetainedDirectory
        os.chdir(package)
        sys.path[:0] = [str(tests), str(package)]
        with event_path.open('x', encoding='utf-8', newline='\n') as events, \
                log_path.open('x', encoding='utf-8', newline='\n') as log:
            runner = Runner(stream=log, verbosity=2, events=events)
            try:
                clean = hosted_environment(os.environ, scratch)
                for key in list(os.environ):
                    if key.casefold() in CI_METADATA and key not in clean:
                        del os.environ[key]
                os.environ.update(clean)
                # A fresh process owns each suite; the test fixture is active
                # during discovery as well as case execution.
                with memory_integrity_ready_fixture(package, scratch):
                    suite = unittest.defaultTestLoader.discover(str(tests), pattern=args.pattern)
                    discovered = list(cases(suite))
                    result = runner.run(unittest.TestSuite(discovered))
            except KeyboardInterrupt:
                result = runner.active_result
                interrupted = True
                failure = 'KeyboardInterrupt'
                log.write('\nINTERRUPTED\n')
            except BaseException:
                result = runner.active_result
                failure = traceback.format_exc()
                log.write('\nRUNNER_EXCEPTION\n' + failure)
    finally:
        os.chdir(old_cwd)
        sys.path[:] = old_path
        tempfile.tempdir = old_tempdir
        tempfile.TemporaryDirectory = old_directory
        sys.dont_write_bytecode = old_bytecode
        for name, value in old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    receipt = {
        'scope': 'CI_RETAINED_TEST_TEMP_AND_HOSTED_ENV_FIXTURES', 'package_root': str(package),
        'test_dir': args.test_dir, 'pattern': args.pattern, 'discovered': len(discovered),
        'ids': [test.id() for test in discovered], 'interrupted': interrupted, 'runner_failure': failure,
        'tests_run': 0 if result is None else result.testsRun,
        'failures': [] if result is None else [{'id': test.id(), 'cause': cause} for test, cause in result.failures],
        'errors': [] if result is None else [{'id': test.id(), 'cause': cause} for test, cause in result.errors],
        'skipped': [] if result is None else [{'id': test.id(), 'cause': why} for test, why in result.skipped],
        'expected_failures': [] if result is None else [{'id': test.id(), 'cause': cause} for test, cause in result.expectedFailures],
        'unexpected_successes': [] if result is None else [test.id() for test in result.unexpectedSuccesses],
        'log': str(log_path), 'log_sha256': hashlib.sha256(log_path.read_bytes()).hexdigest(),
        'events': str(event_path), 'events_sha256': hashlib.sha256(event_path.read_bytes()).hexdigest(),
    }
    save(output / 'Receipt.json', receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if result is not None and result.testsRun > 0 and result.wasSuccessful() and result.testsRun == len(discovered) and not interrupted and failure is None else 1


if __name__ == '__main__':
    raise SystemExit(run())
