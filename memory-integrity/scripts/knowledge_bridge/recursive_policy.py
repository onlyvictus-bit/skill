"""Fail-closed recursive Python launch policy for owned Windows workers."""
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess


_SUPPORTED_FLAGS = {'-B', '-u', '-O', '-OO'}
_REJECTED_FLAGS = {'-S', '-I', '-E', '-P', '-s'}
_MODULE = re.compile(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z')
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')
_MAX_COMMAND_UTF16 = 32767
_REPARSE_POINT = 0x400


def _fail(code):
    raise ValueError(code)


def _text(value, code):
    if isinstance(value, bytes):
        _fail(code)
    try:
        value = os.fspath(value)
    except TypeError:
        _fail(code)
    if not isinstance(value, str) or '\x00' in value:
        _fail(code)
    return value


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def parse_argv(args, selected):
    """Validate the small application grammar before any target is opened."""
    if isinstance(args, (str, bytes)) or not isinstance(args, (list, tuple)) or not args:
        _fail('E_RP1_ARGV_SHAPE')
    argv = [_text(value, 'E_RP1_ARGV') for value in args]
    selected = _text(selected, 'E_RP1_ARGV')
    if _norm(argv[0]) != _norm(selected):
        _fail('E_RP1_ARGV_EXECUTABLE')
    # CreateProcess includes a terminating UTF-16 NUL in its fixed 32,767-unit limit.
    if len(subprocess.list2cmdline(argv).encode('utf-16-le')) // 2 + 1 > _MAX_COMMAND_UTF16:
        _fail('E_RP1_ARGV_LENGTH')
    flags, index = [], 1
    while index < len(argv) and argv[index].startswith('-'):
        token = argv[index]
        if token in _SUPPORTED_FLAGS:
            flags.append(token); index += 1; continue
        if token in _REJECTED_FLAGS or token.startswith('-X') or token.startswith('-W'):
            _fail('E_RP1_ARGV_STARTUP')
        if token in ('-c', '-m'):
            break
        _fail('E_RP1_ARGV_FLAG')
    if index >= len(argv):
        _fail('E_RP1_ARGV_TARGET')
    token = argv[index]
    if token == '-c':
        if index + 1 >= len(argv):
            _fail('E_RP1_ARGV_TARGET')
        mode, target, tail = 'c', argv[index + 1], argv[index + 2:]
    elif token == '-m':
        if index + 1 >= len(argv) or not _MODULE.fullmatch(argv[index + 1]):
            _fail('E_RP1_ARGV_MODULE')
        mode, target, tail = 'm', argv[index + 1], argv[index + 2:]
    elif token.startswith('-'):
        _fail('E_RP1_ARGV_TARGET')
    else:
        mode, target, tail = 'script', token, argv[index + 1:]
    return {'mode': mode, 'flags': flags, 'target': target, 'tail': tail, 'argv': argv}


def clean_env(env, selected, *, store_userbase=None):
    """Reject Windows case-shadowing and unsafe Python startup inputs."""
    if not isinstance(env, dict):
        _fail('E_RP1_ENV_SHAPE')
    selected = _text(selected, 'E_RP1_ENV')
    if store_userbase is not None:
        store_userbase = _text(store_userbase, 'E_RP1_ENV_STARTUP')
        if not store_userbase or len(store_userbase) > 4096 or not os.path.isabs(store_userbase):
            _fail('E_RP1_ENV_STARTUP')
    result, seen, rows = {}, set(), []
    allowed = {'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE', 'PYTHONUTF8', 'PYTHONIOENCODING'}
    for key, value in env.items():
        key, value = _text(key, 'E_RP1_ENV'), _text(value, 'E_RP1_ENV')
        folded = key.casefold()
        if folded in seen:
            _fail('E_RP1_ENV_DUPLICATE')
        seen.add(folded)
        rows.append((key, value, key.upper()))
    no_user_site = next((value for _, value, upper in rows if upper == 'PYTHONNOUSERSITE'), None)
    for key, value, upper in rows:
        if upper.startswith(('RP_', 'RP1_')):
            _fail('E_RP1_ENV_INTERNAL')
        if upper == '__PYVENV_LAUNCHER__':
            if _norm(value) != _norm(selected):
                _fail('E_RP1_ENV_SELECTOR')
            continue
        if upper.startswith('PYTHON'):
            if upper == 'PYTHONUSERBASE':
                if store_userbase is None or no_user_site != '1' or value != store_userbase:
                    _fail('E_RP1_ENV_STARTUP')
                result[key] = value
                continue
            if upper not in allowed:
                _fail('E_RP1_ENV_STARTUP')
            if upper in {'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE', 'PYTHONUTF8'} and value not in {'0', '1'}:
                _fail('E_RP1_ENV_VALUE')
            if upper == 'PYTHONIOENCODING' and not value:
                _fail('E_RP1_ENV_VALUE')
        result[key] = value
    result['__PYVENV_LAUNCHER__'] = selected
    return result


def _ordinary(path):
    try:
        info = path.lstat()
    except OSError as error:
        failure = ValueError('E_RP1_SOURCE_PATH')
        failure.add_note(('E_RP1_SOURCE_OSERROR: %s errno=%r' % (type(error).__name__, error.errno))[:512])
        raise failure from error
    if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & _REPARSE_POINT:
        _fail('E_RP1_SOURCE_PATH')
    return info


def read_checked(path, digest, maximum):
    """Read bounded source exactly once from an ordinary, non-linked path."""
    if not isinstance(maximum, int) or maximum < 0 or not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        _fail('E_RP1_SOURCE_ARGUMENT')
    path = Path(_text(path, 'E_RP1_SOURCE_PATH'))
    if not path.is_absolute() or any(part in ('.', '..') for part in path.parts):
        _fail('E_RP1_SOURCE_PATH')
    initial = _ordinary(path)
    if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1:
        _fail('E_RP1_SOURCE_PATH')
    for parent in path.parents:
        _ordinary(parent)
    try:
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_nlink) != (initial.st_dev, initial.st_ino, initial.st_nlink):
                failure = ValueError('E_RP1_SOURCE_PATH')
                failure.add_note(('E_RP1_SOURCE_IDENTITY: expected=%r observed=%r' %
                    ((initial.st_dev, initial.st_ino, initial.st_nlink),
                     (opened.st_dev, opened.st_ino, opened.st_nlink)))[:512])
                raise failure
            data = stream.read(maximum + 1)
    except ValueError:
        raise
    except OSError as error:
        failure = ValueError('E_RP1_SOURCE_PATH')
        failure.add_note(('E_RP1_SOURCE_OSERROR: %s errno=%r' % (type(error).__name__, error.errno))[:512])
        raise failure from error
    if len(data) > maximum:
        _fail('E_RP1_SOURCE_SIZE')
    if hashlib.sha256(data).hexdigest() != digest:
        _fail('E_RP1_SOURCE_DIGEST')
    return data
