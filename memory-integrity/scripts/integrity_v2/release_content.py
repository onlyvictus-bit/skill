"""Portable content selection; offline profile never falls back to old hashes."""
import hashlib
import json
from pathlib import Path

ACTIVE = 'tests_v2/OFFLINE1-CONTENT.json'
PROFILE = {'id':'offline-first-v1','native_subprocesses_enabled':False,
           'native_mutations_enabled':False,'live_provider_enabled':False}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, code):
    if not ok:
        raise ValueError(code)


def read(path):
    def pairs(rows):
        out = {}
        for key, value in rows:
            require(key not in out, 'E_CONTENT_DUPLICATE')
            out[key] = value
        return out
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('E_CONTENT_MISSING_OR_INVALID') from exc


def selected_name(root):
    root = Path(root)
    caps = read(root/'capabilities-v2.json')
    require(isinstance(caps,dict), 'E_CONTENT_SELECTION')
    if 'active_release_profile' in caps or 'active_content_manifest' in caps:
        value = caps.get('active_release_profile')
        require(isinstance(value,dict) and set(value) == set(PROFILE) and
                value.get('id') == PROFILE['id'] and
                all(value.get(k) is False for k in PROFILE if k != 'id') and
                caps.get('active_content_manifest') == ACTIVE, 'E_CONTENT_SELECTION')
        return ACTIVE
    for name in ('R4-CONTENT.json','R3-CONTENT.json','R2-CONTENT.json'):
        if (root/'tests_v2'/name).is_file():
            return 'tests_v2/'+name
    raise ValueError('E_CONTENT_MISSING')


def inventory(root, exclude=ACTIVE):
    root = Path(root)
    require(not root.is_symlink() and not getattr(root,'is_junction',lambda:False)(),
            'E_CONTENT_REDIRECT')
    result = {}
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        require(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),
                'E_CONTENT_REDIRECT: '+rel)
        if '__pycache__' in path.parts or path.suffix in ('.pyc','.pyo'):
            continue
        if path.is_file() and rel != exclude:
            require(path.stat().st_nlink == 1, 'E_CONTENT_HARDLINK: '+rel)
            result[rel] = sha(path.read_bytes())
    return result


def content_document(root):
    root = Path(root)
    require(selected_name(root) == ACTIVE, 'E_CONTENT_SELECTION')
    actual = inventory(root)
    baseline = read(root/'tests_v2/baseline-r1.json')
    original = {r['path']:r['sha256'] for r in baseline['files']}
    require(not set(original)-set(actual), 'E_CONTENT_ORIGINAL_MISSING')
    row = next(r for r in baseline['files'] if r['path'] == 'SKILL.md')
    skill = (root/'SKILL.md').read_bytes()
    require(len(skill) >= row['bytes'] and sha(skill[:row['bytes']]) == row['sha256'],
            'E_CONTENT_SKILL_PREFIX')
    return {'schema_version':1,'release':'offline-first-v1','files':actual,
            'changed_r1_files':sorted(p for p in original if original[p] != actual[p]),
            'added_files':sorted(set(actual)-set(original))}


def verify_content(root):
    root = Path(root)
    selected = selected_name(root)
    path = root/selected
    require(path.is_file(), 'E_CONTENT_MISSING: '+selected)
    recorded = read(path)
    if selected == ACTIVE:
        require(recorded == content_document(root), 'E_CONTENT_DRIFT')
    else:
        require(recorded.get('files') == inventory(root, selected), 'E_CONTENT_DRIFT')
    return recorded

