"""Stdlib-only pre-work gate for a directly launched current Windows image."""
import argparse
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import runpy
import sys
import time


def _module_image():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleFileNameW.argtypes = [w.HMODULE, w.LPWSTR, w.DWORD]
    kernel.GetModuleFileNameW.restype = w.DWORD
    size = 260
    while True:
        value = ctypes.create_unicode_buffer(size)
        written = kernel.GetModuleFileNameW(None, value, size)
        if not written:
            raise ctypes.WinError(ctypes.get_last_error())
        if written < size - 1:
            return os.path.normcase(os.path.abspath(value.value))
        size *= 2


def _in_any_job():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)]
    kernel.IsProcessInJob.restype = w.BOOL
    result = w.BOOL()
    if not kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(result)):
        raise ctypes.WinError(ctypes.get_last_error())
    return bool(result.value)


def _write_new(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with open(temporary, "x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.flush()
        os.fsync(stream.fileno())
    os.rename(temporary, path)


_IDENTITY_FIELDS = ("image", "sys_executable", "prefix", "base_prefix", "base_executable", "launcher")
_MAX_FAILURE_DETAIL = 512
_MAX_FAILURE_BYTES = 4096


def _bounded(value):
    text = str(value)
    return text if len(text) <= _MAX_FAILURE_DETAIL else text[:_MAX_FAILURE_DETAIL-14] + '...[TRUNCATED]'


def _frame(expected, observed):
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        return None
    return {"expected": {field: expected.get(field) for field in _IDENTITY_FIELDS},
            "observed": {field: observed.get(field) for field in _IDENTITY_FIELDS}}


def _fail(path, token, code, detail, expected=None, observed=None):
    try:
        value = {"token": token, "code": str(code)[:128], "detail": _bounded(detail)}
        frame = _frame(expected, observed)
        if frame is not None:
            value["identity"] = frame
        if len(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')) > _MAX_FAILURE_BYTES:
            value.pop('identity', None)
            value['detail'] = _bounded('E_OWNED_BOOTSTRAP_IDENTITY_OVERSIZE: ' + str(detail))
        _write_new(path, value)
    except Exception:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--ready", required=True)
    parser.add_argument("--go", required=True)
    parser.add_argument("--failure", required=True)
    parser.add_argument("--script", required=True)
    args = parser.parse_args(argv)
    token = "unknown"
    expected = observed = None
    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        token = contract["token"]
        observed = {
            "token": token, "pid": os.getpid(), "image": _module_image(),
            "sys_executable": os.path.normcase(os.path.abspath(sys.executable)),
            "prefix": os.path.normcase(os.path.abspath(sys.prefix)),
            "base_prefix": os.path.normcase(os.path.abspath(sys.base_prefix)),
            "base_executable": os.path.normcase(os.path.abspath(getattr(sys, "_base_executable", sys.executable))),
            "launcher": os.environ.get("__PYVENV_LAUNCHER__"), "in_any_job": _in_any_job(),
        }
        expected = contract["expected"]
        for field in _IDENTITY_FIELDS:
            if observed[field] != expected[field]:
                raise ValueError("E_OWNED_BOOTSTRAP_" + field.upper())
        if not observed["in_any_job"]:
            raise ValueError("E_OWNED_BOOTSTRAP_OUTSIDE_JOB")
        _write_new(args.ready, observed)
        while not Path(args.go).exists():
            if time.monotonic() >= contract["deadline"]:
                raise TimeoutError("E_OWNED_BOOTSTRAP_GO_DEADLINE")
            time.sleep(.002)
        if Path(args.go).read_text(encoding="utf-8") != token:
            raise ValueError("E_OWNED_BOOTSTRAP_GO_TOKEN")
        script = os.path.normcase(os.path.abspath(args.script))
        if script != contract["script"]:
            raise ValueError("E_OWNED_BOOTSTRAP_SCRIPT")
        if time.monotonic() >= contract['deadline']:
            raise TimeoutError('E_OWNED_BOOTSTRAP_WORK_DEADLINE')
    except BaseException as error:
        _fail(args.failure, token, type(error).__name__, error, expected, observed)
        return 71
    # From this boundary onward it is the authored worker, not the bootstrap.
    # Preserve SystemExit (including a normal zero exit) and worker exceptions.
    sys.argv = [script]
    # Match direct ``python script.py`` startup, including sibling imports;
    # run_path alone leaves this bootstrap's own directory at sys.path[0].
    sys.path[0] = str(Path(script).parent)
    runpy.run_path(script, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
