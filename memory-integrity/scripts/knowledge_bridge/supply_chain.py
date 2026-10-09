#!/usr/bin/env python3
"""Phase 1: hash-locked third-party pins. No shadow upgrades.

controlled_pins() returns the committed lock table. verify_pins() requires a
table identical to the committed lock: any version/revision/source deviation
is a tampering signal, never silently adopted. provenance_status() reports
VERIFIED only for an installed package matching the pin; absent packages are
UNVERIFIED, never green. Standard library only.
"""
import csv
import importlib.metadata
import importlib.util
import io
import re
import json
from pathlib import Path

LOCK = Path(__file__).resolve().parent / "supply_chain_pins.json"


class SupplyChainError(ValueError):
    pass


def controlled_pins():
    try:
        table = json.loads(LOCK.read_bytes())
    except (OSError, ValueError) as exc:
        raise SupplyChainError("E_LOCK_UNREADABLE: %s" % (exc,))
    return table


def _shape(table):
    if not isinstance(table, dict) or not isinstance(table.get("pins"), list):
        raise SupplyChainError("E_LOCK_SCHEMA: lock must hold a pins list")
    for entry in table["pins"]:
        if not isinstance(entry, dict):
            raise SupplyChainError("E_LOCK_SCHEMA: pin must be an object")
        for key in ("name", "version", "revision", "source"):
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                raise SupplyChainError("E_LOCK_FIELD: pin.%s required" % (key,))
    return table["pins"]


def verify_pins(table):
    """The given table must equal the committed lock exactly."""
    _shape(table)
    committed = json.loads(LOCK.read_bytes())
    if table != committed:
        raise SupplyChainError("E_LOCK_MISMATCH: pin table differs from committed lock; "
                               "update the lock file explicitly, never in memory")
    return True


def provenance_status(name):
    """VERIFIED only when installed AND matching the pin. Else never green.

    When installed, the distribution version must match; when the lock also
    carries record_sha256 entries, every listed RECORD line hash must match
    the installed wheel metadata. Absent packages are UNVERIFIED.
    """
    table = controlled_pins()
    pin = next((e for e in table["pins"] if e["name"] == name), None)
    if pin is None:
        return "UNKNOWN"
    if importlib.util.find_spec(name) is None:
        return "UNVERIFIED"
    try:
        installed = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "UNVERIFIED"
    if installed != pin["version"]:
        raise SupplyChainError("E_LOCK_DRIFT: installed %s %s != pinned %s"
                               % (name, installed, pin["version"]))
    expected = pin.get("record_sha256") or {}
    # A version/source reference without concrete wheel hashes is NOT hash-verified.
    if not expected:
        return 'UNVERIFIED'
    if expected:
        try:
            dist = importlib.metadata.distribution(name)
            record = dist.read_text("RECORD")
        except (FileNotFoundError, KeyError, ValueError, OSError) as exc:
            raise SupplyChainError("E_LOCK_RECORD_UNREADABLE: %s" % (exc,))
        if record is None:
            raise SupplyChainError("E_LOCK_RECORD_MISSING: no RECORD metadata")
        actual = {}
        for parts in csv.reader(io.StringIO(record)):
            if len(parts) != 3 or not parts[1]:
                continue
            algo, separator, digest = parts[1].partition('=')
            if separator != '=' or algo != 'sha256' or not re.fullmatch(r'[A-Za-z0-9_-]{43}', digest):
                raise SupplyChainError('E_LOCK_RECORD_ALGORITHM: unsupported wheel digest')
            actual[parts[0]] = digest
        missing = sorted(set(expected) - set(actual))
        if missing:
            raise SupplyChainError("E_LOCK_RECORD_FILES: %d RECORD entries absent"
                                   % (len(missing),))
        mismatched = sorted(path for path in expected
                            if path in actual and actual[path] != expected[path])
        if mismatched:
            raise SupplyChainError("E_LOCK_RECORD_HASH: %d RECORD hashes differ"
                                   % (len(mismatched),))
        # A selected-file pin proves only selected-file metadata, not the wheel.
        # Refuse VERIFIED until every hashed RECORD entry has a committed pin.
        hashed_files = {path for path, digest in actual.items() if digest}
        if hashed_files != set(expected):
            return 'UNVERIFIED'
    return "VERIFIED"
