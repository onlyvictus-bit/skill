#!/usr/bin/env python3
"""M3: immutable content-addressed artifacts. No partial file is ever visible.

store_bytes() writes to a hidden temp name, flushes to disk, atomically
renames to the content digest, then re-reads and verifies. A crash can only
leave an orphaned temp file (reconciled as debris), never a half-written
addressable artifact. Disk-full and I/O errors propagate and block acceptance.
"""
import hashlib
import os
import re
from pathlib import Path


class ArtifactError(OSError):
    pass


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def store_bytes(store_dir, data):
    """Persist bytes under their SHA-256. Returns the digest."""
    store = Path(store_dir)
    store.mkdir(parents=True, exist_ok=True)
    digest = digest_bytes(data)
    target = store / digest
    if target.is_file():
        if target.read_bytes() != data:
            raise ArtifactError("E_ARTIFACT_COLLISION: digest present with different bytes")
        return digest
    tmp = store / (".tmp-%d-%s" % (os.getpid(), digest[:16]))
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except OSError as exc:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise ArtifactError("E_ARTIFACT_WRITE: %s" % (exc,))
    if target.read_bytes() != data:
        raise ArtifactError("E_ARTIFACT_VERIFY: stored bytes do not verify")
    return digest


def open_verified(store_dir, digest):
    """Read an artifact, verifying bytes. Missing/corrupt blocks the caller."""
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ArtifactError("E_ARTIFACT_ADDRESS: canonical SHA256 address required")
    target = Path(store_dir) / digest
    if target.is_symlink() or any(p.is_symlink() for p in target.parents):
        raise ArtifactError("E_ARTIFACT_ADDRESS: symlinked artifact/store is not permitted")
    try:
        data = target.read_bytes()
    except OSError:
        raise ArtifactError("E_ARTIFACT_MISSING: %s absent" % (digest,))
    if digest_bytes(data) != digest:
        raise ArtifactError("E_ARTIFACT_CORRUPT: %s content mismatch" % (digest,))
    return data


def reconcile_orphans(store_dir):
    """List hidden temp files left by crashed writers. Informational only."""
    store = Path(store_dir)
    if not store.is_dir():
        return []
    return sorted(p.name for p in store.iterdir()
                  if p.is_file() and p.name.startswith(".tmp-"))
