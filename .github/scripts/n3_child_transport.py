"""Offline N3 harness transport, not skill/native execution authority.

Preserve one validated existing profile without adding Git trust/configuration.
Interpret complete retained command bytes before callers inspect JSON payloads.
No filesystem, subprocess, network, installation, retry or global-config writes.
"""
from hashlib import sha256
import json
from pathlib import PureWindowsPath


BASE_NAMES = frozenset({
    'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'LANG', 'LC_ALL',
    'NUMBER_OF_PROCESSORS', 'TEMP', 'TMP', 'PIP_CONFIG_FILE', 'PYTHONNOUSERSITE',
    'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING', 'HF_HUB_OFFLINE',
    'TRANSFORMERS_OFFLINE', 'GIT_TERMINAL_PROMPT', 'PYTHONUTF8', 'GIT_OPTIONAL_LOCKS',
})


def evaluation_environment(base, inherited, expected_profile):
    """Add only an inherited USERPROFILE equal to the caller's pinned profile.

    The Windows host verifies current SID, non-elevation and physical ancestor
    identities separately. This lexical check does not assert those observations
    or authenticate any user. Never inherit HOME/PYTHONPATH/GIT_CONFIG_* or keys.
    """
    if not isinstance(base, dict) or not set(base) <= BASE_NAMES:
        raise ValueError('E_N3_ENV_BASE_SCOPE')
    for key, wanted in (('HF_HUB_OFFLINE', '1'), ('TRANSFORMERS_OFFLINE', '1'),
                        ('PYTHONNOUSERSITE', '1'), ('GIT_TERMINAL_PROMPT', '0')):
        if base.get(key) != wanted:
            raise ValueError('E_N3_ENV_OFFLINE_CONTROL')
    profile = inherited.get('USERPROFILE')
    for value in (profile, expected_profile):
        if not isinstance(value, str) or not value or '\x00' in value:
            raise ValueError('E_N3_PROFILE_REQUIRED')
        path = PureWindowsPath(value)
        if (not path.is_absolute() or len(path.drive) != 2 or not path.drive.endswith(':')
                or any(part == '..' or ':' in part for part in path.parts[1:])):
            raise ValueError('E_N3_PROFILE_PATH')
    if PureWindowsPath(profile) != PureWindowsPath(expected_profile):
        raise ValueError('E_N3_PROFILE_MISMATCH')
    return {**base, 'USERPROFILE': profile}


class ChildCommandFailure(ValueError):
    """Unsuccessful command/protocol, never a fabricated retrieval response."""
    def __init__(self, code, details):
        self.code, self.details = code, details
        # Original streams stay in the existing Start/Result/log artifacts.
        # Do not copy arbitrary stderr, stdout, environment or exception text.
        super().__init__(code + ': ' + json.dumps(details, sort_keys=True))


def decode_command_output(result, stdout, stderr):
    """Return (exit_code, dict) or a structured failure bound to actual bytes.

    Nonzero valid JSON is returned AS nonzero: consumers still must validate
    their expected domain refusal. Empty/malformed nonzero output remains a
    process failure, not JSONDecodeError and not a legitimate domain refusal.
    Local stream hashes establish byte consistency, not producer authentication.
    """
    if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        raise ValueError('E_N3_CHILD_RAW_BYTES_REQUIRED')
    details = {'stdout': {'bytes': len(stdout), 'sha256': sha256(stdout).hexdigest()},
               'stderr': {'bytes': len(stderr), 'sha256': sha256(stderr).hexdigest()},
               'producer_authentication': False}
    if not isinstance(result, dict):
        raise ChildCommandFailure('E_N3_CHILD_RESULT_SCHEMA', details)
    started, exit_code, error = result.get('started'), result.get('exit_code'), result.get('error')
    details.update(started=started if type(started) is bool else None,
                   exit_code=exit_code if type(exit_code) is int else None,
                   command_error_present=error is not None)
    if type(started) is not bool or (exit_code is not None and type(exit_code) is not int):
        raise ChildCommandFailure('E_N3_CHILD_RESULT_SCHEMA', details)
    artifacts = result.get('artifacts')
    if not isinstance(artifacts, dict) or set(artifacts) != {'stdout.log', 'stderr.log'}:
        raise ChildCommandFailure('E_N3_CHILD_STREAM_BINDING', details)
    for name, fact in (('stdout.log', details['stdout']), ('stderr.log', details['stderr'])):
        expected = artifacts[name]
        if (not isinstance(expected, dict) or type(expected.get('bytes')) is not int
                or expected.get('bytes') != fact['bytes'] or expected.get('sha256') != fact['sha256']):
            raise ChildCommandFailure('E_N3_CHILD_STREAM_BINDING', details)
    if not started or error is not None or exit_code is None:
        raise ChildCommandFailure('E_N3_CHILD_TRANSPORT_FAILED', details)
    if not stdout.strip():
        code = 'E_N3_CHILD_PROCESS_FAILED' if exit_code else 'E_N3_CHILD_STDOUT_MISSING'
        raise ChildCommandFailure(code, details)

    def reject_nonfinite(value):
        raise ValueError('E_NONFINITE_JSON')

    try:
        output = json.loads(stdout.decode('utf-8'), parse_constant=reject_nonfinite)
    except (UnicodeError, ValueError) as exc:
        code = 'E_N3_CHILD_PROCESS_FAILED' if exit_code else 'E_N3_CHILD_STDOUT_NOT_JSON'
        raise ChildCommandFailure(code, details) from exc
    if not isinstance(output, dict):
        raise ChildCommandFailure('E_N3_CHILD_OUTPUT_SCHEMA', details)
    return exit_code, output
