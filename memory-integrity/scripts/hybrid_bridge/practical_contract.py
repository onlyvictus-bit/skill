"""Strict data contract for the isolated R5 ordinary-local candidate.

This module intentionally describes a *candidate* scratch-only fence.  It does
not enable generic native writes, accept a Beads adapter, or establish any
runtime qualification.  Inputs are exact shaped records so unsupported aliases
and accidentally broadened callers fail before a process can be started.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


class PracticalContractError(ValueError):
    """A deterministic request/selection refusal before a SQL subprocess."""


ROUTE = "APPROVED_SCRATCH_PRACTICAL_CONTRACT"
SCHEMA_VERSION = 1
_SHA256 = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}")
_STATUS = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}")
_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1
_ACTIONS = frozenset({"claim", "reassign", "unclaim", "reclaim", "heartbeat"})


def _exact_mapping(value: Any, keys: frozenset[str], code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise PracticalContractError(code)
    return dict(value)


def _text(value: Any, code: str, *, pattern: re.Pattern[str] | None = _IDENTIFIER) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise PracticalContractError(code)
    if "\x00" in value or (pattern is not None and pattern.fullmatch(value) is None):
        raise PracticalContractError(code)
    return value


def _int64_nonzero(value: Any, code: str) -> int:
    # bool is an int subclass but never a task revision.
    if isinstance(value, bool) or not isinstance(value, int) or not (_INT64_MIN <= value <= _INT64_MAX) or value == 0:
        raise PracticalContractError(code)
    return value


def _deadline(value: Any, code: str) -> str:
    return _text(value, code, pattern=_TIMESTAMP)


def strict_canonical_json(value: Any) -> bytes:
    """Serialize only JSON types with finite integer-only numeric values.

    Numeric strings are not rewritten and floats are refused: a digest binding
    must not depend on two serializers disagreeing about 1, 1.0, or NaN.
    """
    def check(item: Any) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            return
        if isinstance(item, (float, bytes, bytearray)):
            raise PracticalContractError("E_PRACTICAL_NONCANONICAL_JSON")
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise PracticalContractError("E_PRACTICAL_NONCANONICAL_JSON")
                check(child)
            return
        raise PracticalContractError("E_PRACTICAL_NONCANONICAL_JSON")

    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_command_digest(value: Mapping[str, Any]) -> str:
    """SHA-256 over the request excluding its self-referential digest field."""
    if not isinstance(value, Mapping):
        raise PracticalContractError("E_PRACTICAL_COMMAND_TYPE")
    payload = dict(value)
    payload.pop("command_digest", None)
    return hashlib.sha256(strict_canonical_json(payload)).hexdigest()


@dataclass(frozen=True)
class PracticalSelection:
    scratch_root: str
    dolt_executable: str
    dolt_sha256: str
    host: str
    port: int
    database: str
    main_branch: str
    incarnation: str
    native_node_id: str
    candidate_route: str

    @classmethod
    def from_value(cls, value: "PracticalSelection | Mapping[str, Any]") -> "PracticalSelection":
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, frozenset(cls.__dataclass_fields__), "E_PRACTICAL_SELECTION_SCHEMA")
        selected = cls(**data)
        selected.validate()
        return selected

    def validate(self) -> None:
        for key in ("scratch_root", "dolt_executable"):
            item = getattr(self, key)
            if not isinstance(item, str) or not item or "\x00" in item:
                raise PracticalContractError("E_PRACTICAL_SELECTION_" + key.upper())
        if not isinstance(self.dolt_sha256, str) or _SHA256.fullmatch(self.dolt_sha256.lower()) is None:
            raise PracticalContractError("E_PRACTICAL_SELECTION_DOLT_SHA256")
        if self.host != "127.0.0.1":
            raise PracticalContractError("E_PRACTICAL_HOST")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise PracticalContractError("E_PRACTICAL_PORT")
        for key in ("database", "main_branch", "incarnation", "native_node_id"):
            _text(getattr(self, key), "E_PRACTICAL_SELECTION_" + key.upper())
        if self.main_branch != "main":
            raise PracticalContractError("E_PRACTICAL_MAIN_BRANCH")
        if self.candidate_route != ROUTE:
            raise PracticalContractError("E_PRACTICAL_CANDIDATE_ROUTE")

    @property
    def digest(self) -> str:
        return hashlib.sha256(strict_canonical_json({
            "scratch_root": self.scratch_root,
            "dolt_executable": self.dolt_executable,
            "dolt_sha256": self.dolt_sha256.lower(),
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "main_branch": self.main_branch,
            "incarnation": self.incarnation,
            "native_node_id": self.native_node_id,
            "candidate_route": self.candidate_route,
        })).hexdigest()


_COMMON_REQUEST_KEYS = frozenset({
    "schema_version", "work_item_id", "operation_id", "action", "task_id", "actor",
    "expected_status", "grant_id", "target_actor", "new_grant_id", "expected_row_lock",
    "fixed_deadline_utc", "new_deadline_utc", "command_digest",
})


@dataclass(frozen=True)
class TransitionRequest:
    schema_version: int
    work_item_id: str
    operation_id: str
    action: str
    task_id: str
    actor: str
    expected_status: str
    grant_id: str
    target_actor: str
    new_grant_id: str
    expected_row_lock: int
    fixed_deadline_utc: str
    new_deadline_utc: str
    command_digest: str

    @classmethod
    def from_value(cls, value: "TransitionRequest | Mapping[str, Any]") -> "TransitionRequest":
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, _COMMON_REQUEST_KEYS, "E_PRACTICAL_REQUEST_SCHEMA")
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PracticalContractError("E_PRACTICAL_SCHEMA_VERSION")
        if self.action not in _ACTIONS:
            raise PracticalContractError("E_PRACTICAL_ACTION")
        for key in ("work_item_id", "operation_id", "task_id", "actor", "grant_id", "target_actor", "new_grant_id"):
            _text(getattr(self, key), "E_PRACTICAL_" + key.upper())
        _text(self.expected_status, "E_PRACTICAL_EXPECTED_STATUS", pattern=_STATUS)
        _int64_nonzero(self.expected_row_lock, "E_PRACTICAL_ROW_LOCK")
        _deadline(self.fixed_deadline_utc, "E_PRACTICAL_FIXED_DEADLINE")
        _deadline(self.new_deadline_utc, "E_PRACTICAL_NEW_DEADLINE")
        if not isinstance(self.command_digest, str) or _SHA256.fullmatch(self.command_digest) is None:
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")


@dataclass(frozen=True)
class GuardedTitleRequest(TransitionRequest):
    title: str

    @classmethod
    def from_value(cls, value: "GuardedTitleRequest | Mapping[str, Any]") -> "GuardedTitleRequest":
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, _COMMON_REQUEST_KEYS | {"title"}, "E_PRACTICAL_TITLE_SCHEMA")
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    def validate(self) -> None:
        if self.action != "guarded_title":
            raise PracticalContractError("E_PRACTICAL_TITLE_ACTION")
        # Reuse all common binding checks except the operation action allowlist.
        if self.schema_version != SCHEMA_VERSION:
            raise PracticalContractError("E_PRACTICAL_SCHEMA_VERSION")
        for key in ("work_item_id", "operation_id", "task_id", "actor", "grant_id", "target_actor", "new_grant_id"):
            _text(getattr(self, key), "E_PRACTICAL_" + key.upper())
        _text(self.expected_status, "E_PRACTICAL_EXPECTED_STATUS", pattern=_STATUS)
        _int64_nonzero(self.expected_row_lock, "E_PRACTICAL_ROW_LOCK")
        _deadline(self.fixed_deadline_utc, "E_PRACTICAL_FIXED_DEADLINE")
        _deadline(self.new_deadline_utc, "E_PRACTICAL_NEW_DEADLINE")
        if not isinstance(self.title, str) or not self.title or len(self.title) > 4096 or "\x00" in self.title:
            raise PracticalContractError("E_PRACTICAL_TITLE")
        if not isinstance(self.command_digest, str) or _SHA256.fullmatch(self.command_digest) is None:
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")


_EXPIRED_REACQUIRE_KEYS = frozenset({
    "schema_version", "work_item_id", "operation_id", "action", "task_id", "actor",
    "expected_status", "prior_grant_id", "prior_deadline_utc", "expected_row_lock",
    "target_actor", "new_grant_id", "fresh_authorization_deadline_utc", "new_deadline_utc",
    "command_digest",
})


@dataclass(frozen=True)
class ExpiredReacquireRequest:
    """A newly approved generation, never a revival of an expired operation."""
    schema_version: int
    work_item_id: str
    operation_id: str
    action: str
    task_id: str
    actor: str
    expected_status: str
    prior_grant_id: str
    prior_deadline_utc: str
    expected_row_lock: int
    target_actor: str
    new_grant_id: str
    fresh_authorization_deadline_utc: str
    new_deadline_utc: str
    command_digest: str

    @classmethod
    def from_value(cls, value: "ExpiredReacquireRequest | Mapping[str, Any]") -> "ExpiredReacquireRequest":
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, _EXPIRED_REACQUIRE_KEYS, "E_PRACTICAL_REACQUIRE_SCHEMA")
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.action != "expired_reacquire":
            raise PracticalContractError("E_PRACTICAL_REACQUIRE_ACTION")
        for key in ("work_item_id", "operation_id", "task_id", "actor", "prior_grant_id", "target_actor", "new_grant_id"):
            _text(getattr(self, key), "E_PRACTICAL_" + key.upper())
        _text(self.expected_status, "E_PRACTICAL_EXPECTED_STATUS", pattern=_STATUS)
        _int64_nonzero(self.expected_row_lock, "E_PRACTICAL_ROW_LOCK")
        for key in ("prior_deadline_utc", "fresh_authorization_deadline_utc", "new_deadline_utc"):
            _deadline(getattr(self, key), "E_PRACTICAL_" + key.upper())
        if not isinstance(self.command_digest, str) or _SHA256.fullmatch(self.command_digest) is None:
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")


_INITIAL_CLAIM_KEYS = frozenset({
    "schema_version", "work_item_id", "operation_id", "action", "task_id", "actor",
    "expected_status", "expected_assignee", "expected_row_lock", "new_grant_id",
    "fresh_authorization_deadline_utc", "new_deadline_utc", "command_digest",
})


@dataclass(frozen=True)
class InitialClaimRequest:
    """First protected grant for an observed open/unassigned native task."""
    schema_version: int
    work_item_id: str
    operation_id: str
    action: str
    task_id: str
    actor: str
    expected_status: str
    expected_assignee: None
    expected_row_lock: int
    new_grant_id: str
    fresh_authorization_deadline_utc: str
    new_deadline_utc: str
    command_digest: str

    @classmethod
    def from_value(cls, value: "InitialClaimRequest | Mapping[str, Any]") -> "InitialClaimRequest":
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, _INITIAL_CLAIM_KEYS, "E_PRACTICAL_INITIAL_CLAIM_SCHEMA")
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.action != "initial_claim":
            raise PracticalContractError("E_PRACTICAL_INITIAL_CLAIM_ACTION")
        for key in ("work_item_id", "operation_id", "task_id", "actor", "new_grant_id"):
            _text(getattr(self, key), "E_PRACTICAL_" + key.upper())
        _text(self.expected_status, "E_PRACTICAL_EXPECTED_STATUS", pattern=_STATUS)
        if self.expected_assignee is not None:
            raise PracticalContractError("E_PRACTICAL_INITIAL_CLAIM_ASSIGNEE")
        _int64_nonzero(self.expected_row_lock, "E_PRACTICAL_ROW_LOCK")
        _deadline(self.fresh_authorization_deadline_utc, "E_PRACTICAL_FRESH_AUTHORIZATION_DEADLINE")
        _deadline(self.new_deadline_utc, "E_PRACTICAL_NEW_DEADLINE")
        if not isinstance(self.command_digest, str) or _SHA256.fullmatch(self.command_digest) is None:
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")


def validate_operation_id(value: Any) -> str:
    return _text(value, "E_PRACTICAL_OPERATION_ID")


def validate_digest(value: Any) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
    return value


# Lease-bound replacement. The earlier candidate records remain inspectable;
# the backend disables their mutation entry points until this revision is
# integrated and native-tested. Parsing a record is never permission/proof.
def _native_lease_timestamp(value: Any, code: str):
    from datetime import datetime
    value = _deadline(value, code)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError as exc:
        raise PracticalContractError(code) from exc
    # Pinned native leases use DATETIME, not DATETIME(6). Do not bind an
    # impossible fractional snapshot to a truncated native field.
    if parsed.microsecond != 0:
        raise PracticalContractError(code)
    return parsed


@dataclass(frozen=True)
class LeasePracticalSelection(PracticalSelection):
    native_node_id: str

    def validate(self) -> None:
        super().validate()
        _text(self.native_node_id, "E_PRACTICAL_NATIVE_NODE")
        if self.main_branch != "main":
            raise PracticalContractError("E_PRACTICAL_MAIN_BRANCH")

    @property
    def digest(self) -> str:
        self.validate()
        return hashlib.sha256(strict_canonical_json({
            key: getattr(self, key) for key in self.__dataclass_fields__
        })).hexdigest()


@dataclass(frozen=True)
class LeaseGuardedTitleRequest:
    """An exact previously observed real lease, not a caller-minted deadline."""
    schema_version: int
    work_item_id: str
    operation_id: str
    action: str
    task_id: str
    actor: str
    title: str
    expected_status: str
    grant_id: str
    expected_row_lock: int
    lease_holder: str
    lease_granted_node: str
    lease_granted_at_utc: str
    lease_expires_at_utc: str
    lease_heartbeat_at_utc: str
    command_digest: str

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, frozenset(cls.__dataclass_fields__),
                              "E_PRACTICAL_LEASE_TITLE_SCHEMA")
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self):
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    @property
    def fixed_deadline_utc(self):
        return self.lease_expires_at_utc

    def validate(self):
        if type(self.schema_version) is not int or self.schema_version != 2 \
                or self.action != "guarded_title_lease":
            raise PracticalContractError("E_PRACTICAL_LEASE_TITLE_ACTION")
        for key in ("work_item_id", "operation_id", "task_id", "actor", "grant_id",
                    "lease_holder", "lease_granted_node"):
            _text(getattr(self, key), "E_PRACTICAL_" + key.upper())
        if self.expected_status != "in_progress" or self.actor != self.lease_holder:
            raise PracticalContractError("E_PRACTICAL_LEASE_TITLE_OWNER")
        _int64_nonzero(self.expected_row_lock, "E_PRACTICAL_ROW_LOCK")
        if not isinstance(self.title, str) or not self.title or len(self.title) > 500 or "\x00" in self.title:
            raise PracticalContractError("E_PRACTICAL_TITLE")
        granted = _native_lease_timestamp(self.lease_granted_at_utc, "E_PRACTICAL_LEASE_GRANTED")
        heartbeat = _native_lease_timestamp(self.lease_heartbeat_at_utc, "E_PRACTICAL_LEASE_HEARTBEAT")
        expiry = _native_lease_timestamp(self.lease_expires_at_utc, "E_PRACTICAL_LEASE_EXPIRY")
        if not granted <= heartbeat < expiry:
            raise PracticalContractError("E_PRACTICAL_LEASE_ORDER")
        validate_digest(self.command_digest)
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError("E_PRACTICAL_COMMAND_DIGEST")
