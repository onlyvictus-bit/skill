"""P1b initial-lease claim request contract.

This module deliberately owns only the new schema-v2 initial claim. Existing
v1 grant-seed request types remain historical and unqualified; they are not
silently upgraded into native-lease authority by this parser.
"""
from dataclasses import dataclass
from typing import Any, Mapping

from .practical_contract import (
    PracticalContractError,
    _exact_mapping,
    _text,
    canonical_command_digest,
    validate_digest,
)


_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1
_CLAIM_KEYS = frozenset({
    'schema_version', 'work_item_id', 'operation_id', 'action', 'task_id', 'actor',
    'expected_status', 'expected_assignee', 'expected_row_lock', 'new_grant_id',
    'command_digest',
})


def _observed_initial_row_lock(value: Any) -> int:
    """Initial native issue creation uses the observed schema-default zero.

    This exception is intentionally local to an open/unassigned first claim.
    It does not relax the nonzero token rules for issued title operations.
    """
    if isinstance(value, bool) or not isinstance(value, int) or not _INT64_MIN <= value <= _INT64_MAX:
        raise PracticalContractError('E_MI2_INITIAL_CLAIM_ROW_LOCK')
    return value


@dataclass(frozen=True)
class LeaseClaimRequest:
    """Exact v2 input for minting the first real native lease.

    There is deliberately no caller-supplied authorization deadline, lease
    timestamp, native node, or minted conflict token. The SQL transaction
    obtains those facts from its one backend clock sample and selected node.
    """
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
    command_digest: str

    @classmethod
    def from_value(cls, value: 'LeaseClaimRequest | Mapping[str, Any]') -> 'LeaseClaimRequest':
        if isinstance(value, cls):
            value.validate()
            return value
        data = _exact_mapping(value, _CLAIM_KEYS, 'E_MI2_INITIAL_CLAIM_SCHEMA')
        request = cls(**data)
        request.validate()
        return request

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}

    def validate(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 2:
            raise PracticalContractError('E_MI2_INITIAL_CLAIM_SCHEMA_VERSION')
        if self.action != 'initial_claim_lease':
            raise PracticalContractError('E_MI2_INITIAL_CLAIM_ACTION')
        for key in ('work_item_id', 'operation_id', 'task_id', 'actor', 'new_grant_id'):
            _text(getattr(self, key), 'E_MI2_INITIAL_CLAIM_' + key.upper())
        if self.expected_status != 'open':
            raise PracticalContractError('E_MI2_INITIAL_CLAIM_STATUS')
        if self.expected_assignee is not None:
            raise PracticalContractError('E_MI2_INITIAL_CLAIM_ASSIGNEE')
        _observed_initial_row_lock(self.expected_row_lock)
        validate_digest(self.command_digest)
        if self.command_digest != canonical_command_digest(self.as_dict()):
            raise PracticalContractError('E_PRACTICAL_COMMAND_DIGEST')
