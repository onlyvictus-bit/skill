#!/usr/bin/env python3
"""Phase 1: explicit execution trust. No OS sandbox is claimed.

TRUSTED runs repo-owned tests with in-process socket blocks, a workspace
jail, scrubbed environment, timeouts and output caps (documented limits:
grandchild-process network/filesystem confinement is NOT provided here).
UNTRUSTED (arbitrary project code) is always refused on this build:
sandbox_available() reports detected facilities for a future gated
activation, but refusal is unconditional until that gate passes.
Standard library only.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TRUST_LEVELS = ("TRUSTED", "UNTRUSTED")
SECRET_KEYS = ("API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY")


class TrustError(ValueError):
    pass


def sandbox_available():
    """Report detectable OS confinement without activating anything."""
    facilities = []
    if os.name != "nt":
        for tool in ("bwrap", "unshare", "firejail"):
            if shutil.which(tool):
                facilities.append(tool)
    return {"os": os.name, "facilities": facilities,
            "untrusted_allowed": False,
            "note": "UNTRUSTED execution refused until a sandbox gate passes"}


def scrub_env(env):
    """Copy env minus secret-bearing keys. Values never logged."""
    cleaned = {}
    for key, value in dict(env).items():
        upper = str(key).upper()
        if any(marker in upper for marker in SECRET_KEYS):
            continue
        cleaned[key] = value
    return cleaned


def check_path(candidate, root):
    """Resolve inside root; refuse escapes including symlink breakouts."""
    root = Path(root).resolve()
    target = Path(candidate)
    if not target.is_absolute():
        target = root / target
    resolved = target.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise TrustError("E_TRUST_PATH_ESCAPE: %s escapes %s" % (candidate, root))
    for part in (resolved, *resolved.parents):
        if part == root:
            break
        if part.is_symlink():
            raise TrustError("E_TRUST_SYMLINK: %s traverses a symlink" % (candidate,))
    if not resolved.exists():
        raise TrustError("E_TRUST_PATH_MISSING: %s absent" % (candidate,))
    return resolved


def _digest(data):
    return hashlib.sha256(data).hexdigest()


_EXECUTIONS = {}


def run_fixture(kind, timeout=30, execution_id=None):
    """Bounded fixture driver for trust tests (not a sandbox).

    Kinds: socket-connect (in-process block observed), subprocess-network
    (refused: grandchild confinement unprovable), infinite-loop (timeout),
    ok-case (pass + digest, deduplicated by execution_id).
    """
    if execution_id is not None and execution_id in _EXECUTIONS:
        prior = dict(_EXECUTIONS[execution_id])
        prior["reruns"] = prior.get("reruns", 0) + 1
        return prior
    if kind == "subprocess-network":
        return {"ok": False, "kind": kind,
                "detail": "E_UNTRUSTED_NETWORK_UNPROVABLE: grandchild network "
                          "confinement needs an OS sandbox; refused",
                "evidence_class": "TEST_ONLY"}
    if kind == "ok-case":
        receipt = {"ok": True, "kind": kind, "detail": "fixture pass",
                   "evidence_class": "TEST_ONLY", "reruns": 1}
        receipt["receipt_digest"] = _digest(json.dumps(
            sorted(receipt.items()), separators=(",", ":")).encode())
        if execution_id is not None:
            _EXECUTIONS[execution_id] = dict(receipt)
        return receipt
    preamble = ("import socket;"
                "b=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('E_TEST_NETWORK_FORBIDDEN'));"
                "socket.socket.connect=b;socket.socket.connect_ex=b;socket.create_connection=b;")
    if kind == "socket-connect":
        code = preamble + "import socket;socket.create_connection(('example.com',80))"
    elif kind == "infinite-loop":
        code = "while True: pass"
    else:
        raise TrustError("E_TRUST_FIXTURE: unknown fixture %r" % (kind,))
    try:
        proc = subprocess.run([sys.executable, "-B", "-c", code],
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "kind": kind, "detail": "timeout after %ss" % (timeout,),
                "evidence_class": "TEST_ONLY"}
    if kind == "socket-connect":
        if proc.returncode != 0:
            return {"ok": False, "kind": kind,
                    "detail": "E_TEST_NETWORK_FORBIDDEN observed",
                    "evidence_class": "TEST_ONLY"}
        return {"ok": True, "kind": kind, "detail": "unexpectedly connected",
                "evidence_class": "TEST_ONLY"}
    return {"ok": False, "kind": kind,
            "detail": "exit %d without timeout" % (proc.returncode,),
            "evidence_class": "TEST_ONLY"}


def run(config):
    """Execute a TRUSTED test batch via test_runner.py. UNTRUSTED refused."""
    if not isinstance(config, dict) or config.get("trust") != "TRUSTED":
        raise TrustError("E_TRUST_LEVEL: only TRUSTED batches execute; "
                         "UNTRUSTED needs a passed sandbox gate")
    root = check_path(config.get("root", "."), Path.cwd())
    for rel in config.get("test_paths", []):
        check_path(root / rel, root)
    with tempfile.TemporaryDirectory(prefix="trusted-run-") as temp:
        output = str(Path(temp) / "receipt.json")
        runner = Path(__file__).resolve().parent / "test_runner.py"
        payload = {"root": str(root), "test_paths": list(config.get("test_paths", [])),
                   "output": output}
        cfg = Path(temp) / "config.json"
        cfg.write_text(json.dumps(payload))
        env = scrub_env(os.environ)
        try:
            proc = subprocess.run(
                [sys.executable, "-B", str(runner), str(cfg)], cwd=str(root),
                env=env, capture_output=True, timeout=config.get("timeout", 300))
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "timeout after %ss" % (config.get("timeout", 300),),
                    "evidence_class": "TEST_ONLY"}
        data = json.loads(Path(output).read_bytes()) if Path(output).is_file() else {}
    data.setdefault("evidence_class", "TEST_ONLY")
    data["returncode"] = proc.returncode
    return data
