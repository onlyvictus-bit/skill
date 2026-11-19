#!/usr/bin/env python3
"""Read-only structured calls to a versioned claude-mon engine CLI.

The engine root is ALWAYS explicit (--claude-mon-root). No implicit search
for a same-named skill, no copied second implementation of the ledger. Every
failure returns a structured error dict; nothing here can mint proof.
"""
import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 60
APPROVED_ENGINE = "claude-mon"
APPROVED_VERSION = "2.0.0-m12"
APPROVED_MANIFEST = "tests_v2/OFFLINE1-CONTENT.json"
# Reviewed matching release, pinned here rather than trusted from the companion.
APPROVED_MANIFEST_SHA256 = "eeeba9be891ef8f10d731748d2c4a37c371068ecb19e8954af7dc842dbf8dfaf"
APPROVED_SCHEMA_DIGEST = "bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f"


def approved_root(engine_root):
    """Validate sampled filesystem identity without executing companion code.

    Before/after checks detect drift; they are not atomic protection against a
    filesystem owner replacing both files between observations.
    """
    from . import release_content
    root = Path(engine_root).absolute()
    for path in (root, *root.parents):
        info = path.lstat()
        if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('E_COMPANION_REDIRECT: ' + str(path))
    manifest = root / APPROVED_MANIFEST
    raw = manifest.read_bytes()
    if manifest.stat().st_nlink != 1 or hashlib.sha256(raw).hexdigest() != APPROVED_MANIFEST_SHA256:
        raise ValueError('E_COMPANION_RELEASE: unapproved content manifest')
    release_content.verify_content(root)
    # The portable content manifest intentionally ignores interpreter caches.
    # Authentication cannot: Python may read bytecode even when -B is used.
    for path in root.rglob('*'):
        if path.is_file() and ('__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo')):
            raise ValueError('E_COMPANION_BYTECODE: unapproved cache: ' + str(path))
    if manifest.read_bytes() != raw:
        raise ValueError('E_COMPANION_CHANGED: manifest changed during validation')
    return root.resolve(strict=True)


def approved_imports(engine_root):
    """Reject cached modules from another companion before using local APIs."""
    # Later lazy imports must not create bytecode outside the approved inventory.
    # This affects only this Python process, never a global interpreter setting.
    sys.dont_write_bytecode = True
    root = approved_root(engine_root)
    scripts = root / 'scripts'
    approved_files = json.loads((root / APPROVED_MANIFEST).read_bytes())['files']
    for name, module in tuple(sys.modules.items()):
        if name != 'complete_read_v2' and not name.startswith('complete_read_v2.'):
            continue
        filename = getattr(module, '__file__', None)
        if not filename:
            raise ValueError('E_COMPANION_IMPORT: missing module origin: ' + name)
        stem = Path(*name.split('.'))
        allowed = {scripts / stem.with_suffix('.py'), scripts / stem / '__init__.py'}
        origin = Path(os.path.abspath(filename))
        if origin not in allowed or origin.relative_to(root).as_posix() not in approved_files:
            raise ValueError('E_COMPANION_IMPORT: cached module from another root: ' + name)
    return root


def _error(code, message):
    return {"ok": False, "error": {"code": code, "message": message}}


def run_engine(engine_root, argv):
    """Run <engine_root>/scripts/claude_mon_v2.py with argv. Never searches PATH."""
    entry = Path(engine_root) / "scripts" / "claude_mon_v2.py"
    if not entry.is_file():
        return None, {"code": "E_COMPANION_MISSING",
                      "message": "no claude_mon_v2.py at %s" % (entry,)}
    try:
        approved_root(engine_root)
    except (OSError, ValueError) as exc:
        return None, {"code": "E_COMPANION_RELEASE", "message": str(exc)}
    try:
        proc = subprocess.run([sys.executable, '-I', '-S', '-B', str(entry)] + list(argv),
                              text=True, capture_output=True, timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, {"code": "E_COMPANION_SPAWN",
                      "message": "cannot execute engine entrypoint: %s" % (exc,)}
    try:
        approved_root(engine_root)
    except (OSError, ValueError) as exc:
        return None, {"code": "E_COMPANION_CHANGED", "message": str(exc)}
    if proc.returncode != 0:
        return None, {"code": "E_COMPANION_BAD_EXIT",
                      "message": "engine exit=%d stderr=%s"
                                 % (proc.returncode, (proc.stderr or "")[-500:])}
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError as exc:
        return None, {"code": "E_COMPANION_BAD_JSON",
                      "message": "engine stdout is not JSON: %s" % (exc,)}


def handshake(engine_root, expect_schema_version=2, expect_digest=None):
    """Capability handshake. Returns (ok_bool, envelope_or_error_dict)."""
    env, error = run_engine(engine_root, ["capabilities"])
    if error is not None:
        return False, {"ok": False, "error": error}
    if not isinstance(env, dict) or env.get("ok") is not True:
        return False, {"ok": False, "error": {"code": "E_COMPANION_BAD_ENVELOPE",
                       "message": "engine did not return ok:true capabilities"}}
    if env.get('engine') != APPROVED_ENGINE or env.get('engine_version') != APPROVED_VERSION:
        return False, _error('E_ENGINE_IDENTITY', 'engine name/version is not the approved release')
    if env.get("schema_version") != expect_schema_version:
        return False, {"ok": False, "error": {"code": "E_SCHEMA_MISMATCH",
                       "message": "engine schema_version %r != expected %r"
                                  % (env.get("schema_version"), expect_schema_version)}}
    digest = env.get("schema_digest", "")
    if not isinstance(digest, str) or len(digest) != 64:
        return False, {"ok": False, "error": {"code": "E_DIGEST_FORMAT",
                       "message": "engine schema_digest is not 64 hex chars"}}
    try:
        int(digest, 16)
    except ValueError:
        return False, {"ok": False, "error": {"code": "E_DIGEST_FORMAT",
                       "message": "engine schema_digest is not hex"}}
    if expect_digest is not None and digest.lower() != expect_digest.lower():
        return False, {"ok": False, "error": {"code": "E_DIGEST_MISMATCH",
                       "message": "engine schema_digest does not match pinned contract"}}
    if digest.lower() != APPROVED_SCHEMA_DIGEST:
        return False, _error('E_DIGEST_MISMATCH', 'engine schema_digest is not the approved contract')
    return True, env
