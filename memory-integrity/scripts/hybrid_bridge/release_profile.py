"""Package-local restrictive release policy, not a native authority issuer."""
import json
from pathlib import Path


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('E_RELEASE_PROFILE_INVALID: duplicate key')
        out[key] = value
    return out


def load_active_profile():
    try:
        document = json.loads((Path(__file__).resolve().parents[2] /
                               'capabilities-v2.json').read_text(encoding='utf-8'),
                              object_pairs_hook=_unique)
        profile = document['active_release_profile']
        flags = ('native_subprocesses_enabled', 'native_mutations_enabled', 'live_provider_enabled')
        if not isinstance(profile, dict) or set(profile) != {'id', *flags} or \
                profile['id'] != 'offline-first-v1' or any(profile[k] is not False for k in flags):
            raise ValueError('invalid offline profile')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError('E_RELEASE_PROFILE_INVALID: required restrictive package profile') from exc
    return dict(profile)


def require_native_execution_enabled():
    load_active_profile()
    raise ValueError('E_RELEASE_PROFILE_NATIVE_DISABLED: offline-first-v1 permits no native subprocess or outcome')
