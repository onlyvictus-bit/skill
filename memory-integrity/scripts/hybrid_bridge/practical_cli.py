"""Public practical candidate preflight, deliberately stopped before native work.

This facade accepts only exact schema-2 lease/title inputs.  It neither imports
the experimental backend nor opens the CM ledger: a valid packet is evidence
of syntactic binding only, never authority to dispatch or write.
"""
from __future__ import annotations

import json
from pathlib import Path

from .practical_contract import (
    LeaseGuardedTitleRequest,
    LeasePracticalSelection,
    PracticalContractError,
)


COMMANDS = frozenset(("practical-title", "practical-reconcile"))
MAX_INPUT_BYTES = 1024 * 1024


class PracticalCLIError(ValueError):
    """A deterministic public preflight refusal."""


def _code(exc: BaseException) -> str:
    text = str(exc)
    if text.startswith("E_PRACTICAL_"):
        return text.split(":", 1)[0]
    return "E_PRACTICAL_INPUT"


def refusal(exc: BaseException) -> dict:
    """Return the fixed zero-effect public result; never write a receipt."""
    code = _code(exc)
    return {
        "ok": False,
        "overall": "BLOCKED",
        "evidence_class": "PREFLIGHT_ONLY",
        "code": code,
        "blockers": [str(exc)],
        "adapter_calls": 0,
        "approvals_consumed": 0,
        "database_write_performed": False,
        "inference_sent": False,
        "native_gate_a_qualified": False,
        "native_acceptance_qualified": False,
        "native_merge_qualified": False,
        "native_beads_qualified": False,
        "receipt_written": False,
        "artifact_written": False,
    }


def _absolute(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise PracticalCLIError("E_PRACTICAL_PATH_ABSOLUTE: absolute paths required")
    return path


def _no_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise PracticalCLIError("E_PRACTICAL_JSON_DUPLICATE_KEY: duplicate JSON object key")
        value[key] = item
    return value


def _strict_json(path: Path) -> dict:
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise PracticalCLIError("E_PRACTICAL_INPUT_MISSING: " + str(path)) from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise PracticalCLIError("E_PRACTICAL_INPUT_TOO_LARGE: " + str(path))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PracticalCLIError("E_PRACTICAL_JSON_UTF8: " + str(path)) from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                PracticalCLIError("E_PRACTICAL_NONCANONICAL_JSON: non-finite JSON number")),
        )
    except PracticalCLIError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise PracticalCLIError("E_PRACTICAL_JSON_MALFORMED: " + str(path)) from exc
    if not isinstance(value, dict):
        raise PracticalCLIError("E_PRACTICAL_JSON_OBJECT: object required")
    return value


def _preflight(args) -> tuple[LeasePracticalSelection, LeaseGuardedTitleRequest]:
    # Validate all visible path arguments before reading a request.  Output
    # locations are deliberately not created or opened by this checkpoint.
    paths = {name: _absolute(getattr(args, name)) for name in (
        "claude_mon_root", "selection_file", "request_file", "cm_ledger",
        "artifacts_dir", "receipt",
    )}
    if not paths["claude_mon_root"].is_dir():
        raise PracticalCLIError("E_PRACTICAL_CLAUDE_MON_ROOT: existing directory required")
    try:
        selection = LeasePracticalSelection.from_value(_strict_json(paths["selection_file"]))
        request = LeaseGuardedTitleRequest.from_value(_strict_json(paths["request_file"]))
    except PracticalContractError:
        raise
    return selection, request


def dispatch(args) -> dict:
    """Validate an exact packet then explicitly refuse all native/CM actions."""
    _preflight(args)
    if args.command == "practical-title":
        raise PracticalCLIError(
            "E_PRACTICAL_NATIVE_PROOF_PENDING: native mechanism unproved; "
            "preflight is not authority to dispatch, create/migrate CM state, or write a receipt"
        )
    if args.command == "practical-reconcile":
        raise PracticalCLIError(
            "E_PRACTICAL_CM_INTEGRATION_PENDING: sealed CM integration is unavailable; "
            "no receipt is inferred from a title and no successful result is emitted"
        )
    raise PracticalCLIError("E_PRACTICAL_ARGUMENTS: unsupported practical command")


def register(subparsers) -> None:
    """Register the fixed public argument surface with no activation option."""
    for name in sorted(COMMANDS):
        command = subparsers.add_parser(name)
        for key in ("claude-mon-root", "selection-file", "request-file", "cm-ledger",
                    "artifacts-dir", "receipt"):
            command.add_argument("--" + key, required=True)
