"""Per-process, bounded timing records for an isolated diagnostic copy.

This module is deliberately dependency-free so the controller may copy it into
``knowledge_bridge/_extended_timing.py``.  It records observation only: it
does not select a worker, alter a timeout, retry an operation, or keep an open
log handle.  A recorder write failure is explicit so an incomplete trace is
never mistaken for a completed observation.
"""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
import functools
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Any, Callable, Iterator


SCHEMA = 1
ENV_CONFIG = 'MEMORY_INTEGRITY_EXTENDED_TIMING_CONFIG'
ENV_ROOT = 'MEMORY_INTEGRITY_EXTENDED_TIMING_ROOT'
_MAX_ASSOCIATIONS = 256
_lock = threading.RLock()
_configuration: tuple[Path, tuple[Path, ...], int] | None = None
_log_created = False
_log_identity: tuple[int, int] | None = None
_span = 0
_byte_associations: deque[tuple[bytes, dict[str, Any]]] = deque(maxlen=_MAX_ASSOCIATIONS)


class TimingLogError(RuntimeError):
    """The diagnostic trace is incomplete and must not be treated as evidence."""


def _ordinary_directory(value: Path | str, label: str) -> Path:
    path = Path(value).absolute()
    if not path.is_absolute() or not path.exists() or not path.is_dir():
        raise ValueError('E_TIMING_' + label + '_DIRECTORY')
    for item in (path, *path.parents):
        info = item.lstat()
        if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('E_TIMING_' + label + '_REDIRECT')
    return path.resolve(strict=True)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).is_relative_to(root)
    except (FileNotFoundError, OSError, ValueError):
        return False
    return path.resolve(strict=True).is_relative_to(root)


def _configuration_or_error() -> tuple[Path, tuple[Path, ...], int]:
    if _configuration is None:
        raise TimingLogError('E_TIMING_NOT_CONFIGURED')
    return _configuration


def configure(root: Path | str, watched_roots: list[Path | str], budget: int = 120) -> None:
    """Set one immutable per-process diagnostic context.

    ``root`` is an already-created exclusive output directory.  Repeating the
    exact configuration is safe because copied module entrypoints may all call
    this function; changing any setting in a process is rejected.
    """
    global _configuration
    output = _ordinary_directory(root, 'ROOT')
    if type(budget) is not int or not 1 <= budget <= 3600:
        raise ValueError('E_TIMING_BUDGET')
    if not isinstance(watched_roots, list) or not watched_roots:
        raise ValueError('E_TIMING_WATCHED_ROOTS')
    watched = tuple(_ordinary_directory(item, 'WATCHED_ROOT') for item in watched_roots)
    if len(set(watched)) != len(watched):
        raise ValueError('E_TIMING_DUPLICATE_WATCHED_ROOT')
    candidate = (output, watched, budget)
    with _lock:
        if _configuration is None:
            _configuration = candidate
            return
        if _configuration != candidate:
            raise ValueError('E_TIMING_CONFIGURATION_IMMUTABLE')


def _safe_details(details: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = json.dumps(details, sort_keys=True, ensure_ascii=True, allow_nan=False,
                         separators=(',', ':'))
        result = json.loads(raw)
    except (TypeError, ValueError, UnicodeError) as error:
        raise TimingLogError('E_TIMING_DETAILS:' + type(error).__name__) from error
    if not isinstance(result, dict):
        raise TimingLogError('E_TIMING_DETAILS_OBJECT')
    return result


def _event(event: str, action: str, span: int, *, path: Path | str | None = None,
           status: str, duration_ns: int | None = None, cpu_duration_ns: int | None = None,
           details: dict[str, Any] | None = None, error_type: str | None = None) -> None:
    global _log_created, _log_identity
    root, _watched, budget = _configuration_or_error()
    if event not in ('START', 'END') or not isinstance(action, str) or not action:
        raise TimingLogError('E_TIMING_EVENT_SCHEMA')
    row: dict[str, Any] = {
        'schema': SCHEMA,
        'event': event,
        'utc': datetime.now(timezone.utc).isoformat(),
        'monotonic_ns': time.monotonic_ns(),
        'cpu_ns': time.process_time_ns(),
        'pid': os.getpid(),
        'thread': threading.get_ident(),
        'span': span,
        'action': action,
        'status': status,
        'diagnostic_budget_seconds': budget,
    }
    if path is not None:
        row['path'] = str(Path(path).resolve(strict=False))
    if duration_ns is not None:
        if type(duration_ns) is not int or duration_ns < 0:
            raise TimingLogError('E_TIMING_DURATION')
        row['duration_ns'] = duration_ns
    if cpu_duration_ns is not None:
        if type(cpu_duration_ns) is not int or cpu_duration_ns < 0:
            raise TimingLogError('E_TIMING_CPU_DURATION')
        row['cpu_duration_ns'] = cpu_duration_ns
    if details:
        safe = _safe_details(details)
        # File-size and digest are first-class report columns.  Other context
        # remains namespaced so callers cannot overwrite recorder identity.
        for key in ('bytes', 'sha256'):
            if key in safe:
                row[key] = safe.pop(key)
        if safe:
            row['details'] = safe
    if error_type is not None:
        row['error_type'] = error_type
    raw = json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False,
                     separators=(',', ':')).encode('utf-8') + b'\n'
    target = root / (str(os.getpid()) + '.jsonl')
    try:
        # Every call opens and closes its own handle.  The first use refuses an
        # existing name; later records append only to the file this PID created.
        with _lock:
            _ordinary_directory(root, 'ROOT')
            if not _log_created:
                with target.open('xb') as stream:
                    info = os.fstat(stream.fileno())
                    _log_identity = (info.st_dev, info.st_ino)
                    stream.write(raw)
                _log_created = True
            else:
                info = target.lstat()
                if target.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or \
                        info.st_nlink != 1 or (info.st_dev, info.st_ino) != _log_identity:
                    raise TimingLogError('E_TIMING_LOG_IDENTITY')
                # No O_CREAT: a removed/replaced file must not become a new log.
                descriptor = os.open(target, os.O_WRONLY | os.O_APPEND | getattr(os, 'O_BINARY', 0))
                with os.fdopen(descriptor, 'ab') as stream:
                    opened = os.fstat(stream.fileno())
                    if opened.st_nlink != 1 or (opened.st_dev, opened.st_ino) != _log_identity:
                        raise TimingLogError('E_TIMING_LOG_IDENTITY')
                    stream.write(raw)
    except Exception as error:
        raise TimingLogError('E_TIMING_LOG_WRITE:' + type(error).__name__) from error


def _next_span() -> int:
    global _span
    with _lock:
        value = _span
        _span += 1
        return value


def _add_note(original: BaseException, note: str) -> None:
    try:
        original.add_note(note)
    except AttributeError:
        pass


@contextmanager
def span(action: str, path: Path | str | None = None, **details: Any) -> Iterator[dict[str, Any]]:
    """Record an exact START/END pair while preserving the wrapped behavior.

    The yielded details mapping may receive post-operation fields such as
    ``bytes``.  It is serialized only at each event boundary.
    """
    span_id = _next_span()
    started = time.monotonic_ns()
    cpu_started = time.process_time_ns()
    fields = dict(details)
    try:
        _event('START', action, span_id, path=path, status='STARTED', details=fields)
    except TimingLogError:
        raise
    try:
        yield fields
    except BaseException as original:
        try:
            final_path = fields.pop('_event_path', path)
            _event('END', action, span_id, path=final_path, status='EXCEPTION',
                   duration_ns=time.monotonic_ns() - started,
                   cpu_duration_ns=time.process_time_ns() - cpu_started,
                   details=fields, error_type=type(original).__name__)
        except TimingLogError as logging_error:
            _add_note(original, str(logging_error))
        raise
    else:
        final_path = fields.pop('_event_path', path)
        _event('END', action, span_id, path=final_path, status='RETURNED',
               duration_ns=time.monotonic_ns() - started,
               cpu_duration_ns=time.process_time_ns() - cpu_started,
               details=fields)


def _watched(path: Path | str) -> Path | None:
    try:
        candidate = Path(path).absolute()
        root, watched_roots, _budget = _configuration_or_error()
        del root
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError, ValueError, TimingLogError):
        return None
    return resolved if any(_inside(resolved, item) for item in watched_roots) else None


def _remember_bytes(value: bytes, path: Path) -> None:
    with _lock:
        _byte_associations.append((value, {'path': str(path), 'bytes': len(value)}))


def read_bytes(path: Path | str) -> bytes:
    """Read bytes unchanged, timing only an approved watched source path."""
    target = _watched(path)
    if target is None:
        return Path(path).read_bytes()
    with span('file-read-bytes', target) as fields:
        value = target.read_bytes()
        fields['bytes'] = len(value)
        _remember_bytes(value, target)
        return value


def read_text(path: Path | str, *args: Any, **kwargs: Any) -> str:
    """Read text unchanged and record the file size without a second content read."""
    target = _watched(path)
    if target is None:
        return Path(path).read_text(*args, **kwargs)
    with span('file-read-text', target) as fields:
        value = target.read_text(*args, **kwargs)
        fields['bytes'] = target.stat().st_size
        return value


def _known_bytes(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, bytes):
        return None
    with _lock:
        for recorded, metadata in reversed(_byte_associations):
            if recorded is value:
                return dict(metadata)
    return None


def digest(function: Callable[[Any], Any], value: Any) -> Any:
    """Time an existing digest function and associate only an exact read object."""
    known = _known_bytes(value)
    details: dict[str, Any] = {}
    path = None
    if known is not None:
        path = known['path']
        details['bytes'] = known['bytes']
        details['association'] = 'exact-read-object'
    with span('digest', path, **details) as fields:
        result = function(value)
        if isinstance(result, str) and re.fullmatch(r'[0-9a-f]{64}', result):
            fields['sha256'] = result
        return result


def locate(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Time one existing path validator; this is not a filesystem-wide search."""
    with span('path-validation', scope='validator-only') as fields:
        result = function(*args, **kwargs)
        if isinstance(result, (str, os.PathLike)):
            candidate = _watched(Path(result))
            if candidate is not None:
                fields['resolved_path'] = str(candidate)
                fields['_event_path'] = str(candidate)
        return result


# Parent overlays historically call their ``within`` wrapper by this name.
within = locate


def _reopen_details(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Path | None, dict[str, Any]]:
    try:
        doc = args[0] if len(args) > 0 else kwargs['doc']
        root = args[1] if len(args) > 1 else kwargs['root']
        ref = args[2] if len(args) > 2 else kwargs['ref']
        source_id = ref['source_id']
        relative = doc['sources'][source_id]['path']
        candidate = _watched(Path(root) / relative)
        detail = {'source_id': source_id, 'unit_id': ref['unit_id']}
        return candidate, detail
    except (KeyError, TypeError, ValueError, OSError):
        return None, {}


def traced(action: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for copied diagnostic functions; original return/errors survive."""
    if not isinstance(action, str) or not action:
        raise ValueError('E_TIMING_ACTION')
    def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            path, details = _reopen_details(args, kwargs) if action == 'source-unit-reopen' else (None, {})
            with span(action, path, **details):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def _load_rows(paths: Any) -> list[dict[str, Any]]:
    if isinstance(paths, (str, os.PathLike, Path)):
        paths = [paths]
    if not isinstance(paths, (list, tuple)):
        raise ValueError('E_TIMING_MALFORMED_INPUT')
    if paths and all(isinstance(row, dict) for row in paths):
        return [dict(row) for row in paths]
    rows: list[dict[str, Any]] = []
    for item in paths:
        path = Path(item)
        if path.suffix != '.jsonl' or not path.is_file():
            raise ValueError('E_TIMING_MALFORMED_PATH')
        try:
            with path.open('rb') as stream:
                for line in stream:
                    if not line.strip():
                        raise ValueError('E_TIMING_MALFORMED_BLANK')
                    rows.append(json.loads(line.decode('utf-8')))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError('E_TIMING_MALFORMED_RECORD') from error
    return rows


def _required(row: dict[str, Any], event: str) -> None:
    common = {'schema', 'event', 'utc', 'monotonic_ns', 'cpu_ns', 'pid', 'thread', 'span', 'action', 'status'}
    if not common <= set(row) or row.get('schema') != SCHEMA or row.get('event') != event:
        raise ValueError('E_TIMING_MALFORMED_RECORD')
    if (type(row['pid']) is not int or row['pid'] <= 0 or type(row['thread']) is not int or
            type(row['span']) is not int or row['span'] < 0 or not isinstance(row['action'], str) or
            not row['action'] or not isinstance(row['utc'], str) or
            type(row['monotonic_ns']) is not int or type(row['cpu_ns']) is not int):
        raise ValueError('E_TIMING_MALFORMED_RECORD')
    if event == 'END' and (type(row.get('duration_ns')) is not int or row['duration_ns'] < 0):
        raise ValueError('E_TIMING_MALFORMED_RECORD')
    if row['status'] not in ({'STARTED'} if event == 'START' else {'RETURNED','EXCEPTION'}):
        raise ValueError('E_TIMING_MALFORMED_STATUS')


def summarize(paths: Any) -> list[dict[str, Any]]:
    """Return individual span rows; never aggregate overlapping worker times."""
    rows = _load_rows(paths)
    starts: dict[tuple[int, int, int], dict[str, Any]] = {}
    complete: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('E_TIMING_MALFORMED_RECORD')
        event = row.get('event')
        if event not in ('START', 'END'):
            raise ValueError('E_TIMING_MALFORMED_RECORD')
        _required(row, event)
        key = (row['pid'], row['thread'], row['span'])
        duplicate = (*key, event)
        if duplicate in seen:
            raise ValueError('E_TIMING_DUPLICATE_RECORD')
        seen.add(duplicate)
        if event == 'START':
            if key in starts:
                raise ValueError('E_TIMING_DUPLICATE_START')
            starts[key] = row
            continue
        start = starts.pop(key, None)
        if start is None or start['action'] != row['action'] or row['monotonic_ns'] < start['monotonic_ns'] or \
                row['cpu_ns'] < start['cpu_ns']:
            raise ValueError('E_TIMING_PAIR')
        complete.append({
            'pid': row['pid'], 'thread': row['thread'], 'span': row['span'], 'action': row['action'],
            'path': row.get('path', start.get('path')), 'start_utc': start['utc'], 'end_utc': row['utc'],
            'start_monotonic_ns': start['monotonic_ns'], 'end_monotonic_ns': row['monotonic_ns'],
            'duration_ns': row['duration_ns'], 'duration_seconds': row['duration_ns'] / 1_000_000_000,
            'cpu_duration_ns': row.get('cpu_duration_ns'),
            'status': row['status'], 'details': row.get('details', start.get('details', {})),
            **{key:row[key] for key in ('bytes','sha256','error_type') if key in row},
        })
    for start in starts.values():
        complete.append({
            'pid': start['pid'], 'thread': start['thread'], 'span': start['span'], 'action': start['action'],
            'path': start.get('path'), 'start_utc': start['utc'], 'end_utc': None,
            'start_monotonic_ns': start['monotonic_ns'], 'end_monotonic_ns': None,
            'duration_ns': None, 'duration_seconds': None, 'cpu_duration_ns': None, 'status': 'UNFINISHED',
            'details': start.get('details', {}),
        })
    return sorted(complete, key=lambda row: (row['start_monotonic_ns'], row['pid'], row['thread'], row['span']))


def bootstrap_from_environment() -> None:
    """Load controller-written configuration when a copied worker module starts.

    Accepted configuration forms are intentionally narrow: a JSON object with
    ``root``/``watched_roots``/``budget`` or the same keys beneath ``timing``.
    The controller can pass an explicit file path through ``ENV_CONFIG``; the
    root environment fallback is useful for independently copied children.
    """
    config_path = os.environ.get(ENV_CONFIG)
    root_hint = os.environ.get(ENV_ROOT)
    if config_path:
        path = Path(config_path)
    elif root_hint:
        candidate = Path(root_hint)
        path = candidate / 'Config.json' if candidate.is_dir() else candidate
    else:
        return
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode('utf-8'))
        if isinstance(value, dict) and isinstance(value.get('timing'), dict):
            value = value['timing']
        if not isinstance(value, dict) or set(value) - {'root', 'watched_roots', 'budget'} or \
                not {'root', 'watched_roots'} <= set(value):
            raise ValueError('E_TIMING_BOOTSTRAP_SCHEMA')
        configure(value['root'], value['watched_roots'], value.get('budget', 120))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError, TimingLogError) as error:
        raise TimingLogError('E_TIMING_BOOTSTRAP:' + type(error).__name__) from error
