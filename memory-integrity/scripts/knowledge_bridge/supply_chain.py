#!/usr/bin/env python3
"""Phase 1: hash-locked third-party pins. No shadow upgrades.

controlled_pins() returns the committed lock table. verify_pins() requires a
table identical to the committed lock: any version/revision/source deviation
is a tampering signal, never silently adopted. provenance_status() reports
VERIFIED only for an installed package matching the pin; absent packages are
UNVERIFIED, never green. Standard library only.
"""
import importlib.metadata
import importlib.util
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
    """VERIFIED only when installed AND matching the pin. Else never green."""
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
    return "VERIFIED"
