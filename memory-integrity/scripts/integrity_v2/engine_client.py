#!/usr/bin/env python3
"""Read-only structured calls to a versioned claude-mon engine CLI.

The engine root is ALWAYS explicit (--claude-mon-root). No implicit search
for a same-named skill, no copied second implementation of the ledger. Every
failure returns a structured error dict; nothing here can mint proof.
"""
import json
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 60


def _error(code, message):
    return {"ok": False, "error": {"code": code, "message": message}}


def run_engine(engine_root, argv):
    """Run <engine_root>/scripts/claude_mon_v2.py with argv. Never searches PATH."""
    entry = Path(engine_root) / "scripts" / "claude_mon_v2.py"
    if not entry.is_file():
        return None, {"code": "E_COMPANION_MISSING",
                      "message": "no claude_mon_v2.py at %s" % (entry,)}
    try:
        proc = subprocess.run([sys.executable, str(entry)] + list(argv),
                              text=True, capture_output=True, timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, {"code": "E_COMPANION_SPAWN",
                      "message": "cannot execute engine entrypoint: %s" % (exc,)}
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
    return True, env
