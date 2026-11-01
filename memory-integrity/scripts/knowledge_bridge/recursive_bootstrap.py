"""Owned-worker startup audit and sealed recursive Python dispatcher.

The protected runtime package and cooperative filesystem are the trust base.
This is an application launch profile, not an OS sandbox or a concurrent-writer
defence. No site-packages, interpreter configuration or global state is written.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import zipfile
import ctypes
import importlib.util
import math
import runpy
import subprocess
import time
import types
import uuid
import configparser
import re
import shutil
import threading

LIMIT = 262144


def require(value, code):
    if not value:
        raise ValueError('E_RP_' + code)


def ordinary(path, *, directory=False):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        info = item.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, 'st_file_attributes', 0) & 0x400, 'REPARSE')
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) if directory else
            stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'ORDINARY')
    return path


def audit_site_roots(roots):
    for root in roots:
        for item in ordinary(root, directory=True).iterdir():
            name = item.name.casefold()
            require(not name.endswith('.pth') and
                    not name.startswith(('sitecustomize', 'usercustomize')), 'STARTUP_CUSTOM')
    return True


def audit_path_configuration(pth_candidates, registry_values, approved=()):
    require(registry_values == list(approved), 'STARTUP_REGISTRY')
    for path in pth_candidates:
        require(not startup_exists(path), 'STARTUP_PTH')
    return True


def audit_archive(path):
    if not startup_exists(path):
        return None
    require(ordinary(path).stat().st_size <= 33554432, 'ARCHIVE_BOUND')
    with zipfile.ZipFile(path) as archive:
        rows = archive.infolist()
        require(len(rows) <= 10000 and sum(len(r.filename.encode('utf-8')) for r in rows) <= 1048576,
                'ARCHIVE_BOUND')
        for row in rows:
            name = row.filename
            require(len(name.encode('utf-8')) <= 8192, 'ARCHIVE_BOUND')
            first = name.replace('\\', '/').split('/')[0].casefold()
            require(not first.startswith(('sitecustomize', 'usercustomize')), 'STARTUP_ARCHIVE')
    return True


def startup_exists(path):
    """Absence is FileNotFound, never an unreadable path hidden by lexists."""
    path=Path(path).absolute()
    try:
        path.lstat()
    except FileNotFoundError:
        parent=path.parent
        while True:
            try:
                parent.lstat()
                break
            except FileNotFoundError:
                require(parent.parent!=parent,'STARTUP_PARENT')
                parent=parent.parent
        ordinary(parent,directory=True)
        return False
    return True


def decode_request(raw):
    require(type(raw) is bytes and len(raw) <= LIMIT, 'REQUEST_SIZE')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'REQUEST_DUPLICATE')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('E_RP_REQUEST_CONSTANT')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('E_RP_REQUEST_JSON') from error
    require(type(value) is dict and set(value) == {'version','nonce','command','profile'}, 'REQUEST_SCHEMA')
    require(type(value['version']) is int and value['version'] == 1 and
            type(value['nonce']) is str and len(value['nonce']) == 32 and
            all(c in '0123456789abcdef' for c in value['nonce']), 'REQUEST_FIELDS')
    require(type(value['command']) is dict and type(value['profile']) is dict, 'REQUEST_FIELDS')
    return value


def loader_literal(paths, bootstrap, digest, request, request_digest):
    """All literals come from the trusted parent, never from the request itself.

    CPython initializes site before inserting -c path0. Parent audits that earlier
    startup surface. Here, remove path0 before the first path-resolved import.
    Read, hash and execute the same in-memory bytes; never reopen via import.
    """
    require(type(paths) is list and len(paths) <= 20 and all(type(p) is str and
            os.path.isabs(p) and '\0' not in p for p in paths), 'LOADER_ARGUMENTS')
    require(all(type(p) is str and os.path.isabs(p) and '\0' not in p for p in (bootstrap,request)),
            'LOADER_ARGUMENTS')
    require(all(type(d) is str and len(d) == 64 and all(c in '0123456789abcdef' for c in d)
                for d in (digest,request_digest)), 'LOADER_ARGUMENTS')
    body = (
        "import sys\n"
        "_rp_loader_stage='loader-path0'\n"
        "if sys.path[0] != '': raise RuntimeError('E_RP_LOADER_PATH0')\n"
        "sys.path.pop(0)\n"
        "_rp_loader_stage='loader-paths'\n"
        "if [p.replace('/','\\\\').casefold() for p in sys.path] != " +
        repr([p.replace('/','\\').casefold() for p in paths]) + ": raise RuntimeError('E_RP_LOADER_PATHS')\n"
        "import hashlib,os,stat\n"
        "_rp_loader_stage='loader-source'\n"
        "p=" + repr(str(bootstrap)) + "\n"
        "q=os.path.abspath(p)\n"
        "while True:\n"
        " s=os.lstat(q)\n"
        " if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400: raise RuntimeError('E_RP_LOADER_REPARSE')\n"
        " parent=os.path.dirname(q)\n"
        " if parent==q: break\n"
        " q=parent\n"
        "s=os.stat(p)\n"
        "if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1: raise RuntimeError('E_RP_LOADER_FILE')\n"
        "with open(p,'rb') as f: raw=f.read(262145)\n"
        "if len(raw)>262144 or hashlib.sha256(raw).hexdigest()!=" + repr(digest) + ": raise RuntimeError('E_RP_LOADER_SOURCE')\n"
        "ns={'__name__':'rp1_sealed_bootstrap','__file__':p}\n"
        "_rp_loader_stage='loader-exec'\n"
        "exec(compile(raw,p,'exec'),ns)\n"
    )
    nonce = Path(request).stem
    if len(nonce) != 32 or any(c not in '0123456789abcdef' for c in nonce): nonce = uuid.uuid4().hex
    # Publication cannot depend on successfully importing the failed bootstrap.
    # Restore only the trusted parent's literal search paths before diagnostic
    # imports, even when path0/path comparison itself was the original failure.
    failure = (
        "except BaseException as _rp_loader_error:\n"
        " try:\n"
        "  import sys\n"
        "  sys.path[:]= " + repr(paths) + "\n"
        "  import os,json,stat\n"
        "  d={'version':1,'scope':'RP1_CORRECTED_LOADER_FAILURE','phase':'loader',"
        "'nonce':" + repr(nonce) + ",'stage':_rp_loader_stage,'pid':os.getpid(),'ppid':os.getppid(),"
        "'authored_child_started':False,'error_type':type(_rp_loader_error).__name__[:128],"
        "'error':str(_rp_loader_error)[:256],'notes':[str(n)[:128] for n in getattr(_rp_loader_error,'__notes__',[])[:2]],"
        "'bootstrap_sha256':" + repr(digest) + ",'request_sha256':" + repr(request_digest) + "}\n"
        "  raw=json.dumps(d,ensure_ascii=True,allow_nan=False,sort_keys=True).encode('utf-8')\n"
        "  if len(raw)>8192: raise RuntimeError('E_RP_LOADER_FAILURE_BOUND')\n"
        "  dirs=[" + repr(str(Path(request).parent)) + "]\n"
        "  try:\n"
        "   cwd=os.getcwd()\n"
        "   if cwd not in dirs: dirs.append(cwd)\n"
        "  except OSError: pass\n"
        "  published=False\n"
        "  for directory in dirs:\n"
        "   try:\n"
        "    q=os.path.abspath(directory)\n"
        "    while True:\n"
        "     s=os.lstat(q)\n"
        "     if not stat.S_ISDIR(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400: raise RuntimeError('E_RP_LOADER_FAILURE_PATH')\n"
        "     parent=os.path.dirname(q)\n"
        "     if parent==q: break\n"
        "     q=parent\n"
        "    final=os.path.join(directory," + repr('rp1-loader-' + nonce + '.failure.json') + ")\n"
        "    temporary=final[:-4]+'pending'\n"
        "    with open(temporary,'xb') as f: f.write(raw)\n"
        "    os.rename(temporary,final)\n"
        "    published=True\n"
        "    break\n"
        "   except BaseException as e: _rp_loader_error.add_note('E_RP_LOADER_FAILURE_RECORD: '+repr(e)[:256])\n"
        "  if not published: _rp_loader_error.add_note('E_RP_LOADER_FAILURE_UNPUBLISHED')\n"
        " except BaseException as e: _rp_loader_error.add_note('E_RP_LOADER_FAILURE_RECORD: '+repr(e)[:256])\n"
        " raise\n"
    )
    prologue = 'try:\n' + ''.join(' ' + line + '\n' for line in body.splitlines()) + failure
    # The immutable public contract recognizes the outer enter boundary at
    # literal line20. Keep that frame stable while the trusted prologue grows;
    # none of the additional loader frames surrounds authored execution.
    code = '_rp_prologue=' + repr(prologue) + '\nexec(_rp_prologue)\n' + '\n' * 17
    code += "ns['enter'](" + repr(str(request)) + ',' + repr(request_digest) + ")\n"
    require(len(code.encode('utf-16-le'))//2 < 24000, 'LOADER_ARGUMENTS')
    return code


def image():
    if os.name != 'nt':
        return os.path.abspath(sys.executable)
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    api.GetModuleFileNameW.restype = ctypes.c_uint32
    value = ctypes.create_unicode_buffer(32768)
    size = api.GetModuleFileNameW(None, value, len(value))
    require(0 < size < len(value), 'IMAGE')
    return value.value


def norm(value):
    return os.path.normcase(os.path.abspath(value))


def record(path):
    path = Path(path).absolute()
    # Runtime package executables can have approved hard links; ordinary policy
    # source/request files cannot. Record and recheck runtime link counts.
    for item in (path, *path.parents):
        info = item.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, 'st_file_attributes', 0) & 0x400, 'REPARSE')
    with path.open('rb') as stream:
        raw = stream.read()
    return {'path':str(path), 'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest(),
            'links':path.stat().st_nlink}


def registry_values(version=None):
    if os.name != 'nt':
        return []
    import winreg
    version = list(sys.version_info[:2]) if version is None else version
    require(type(version) is list and len(version)==2 and
            all(type(n) is int and 0 < n < 100 for n in version), 'STARTUP_VERSION')
    found = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                key = winreg.OpenKey(hive, 'Software\\Python\\PythonCore\\'+
                    f'{version[0]}.{version[1]}'+r'\PythonPath',
                    0, winreg.KEY_READ | view)
            except FileNotFoundError:
                continue
            with key:
                # A profile binds every value/subkey; no unrecorded path is accepted.
                values = []
                count, nvalues, _ = winreg.QueryInfoKey(key)
                require(count == 0 and nvalues <= 8, 'STARTUP_REGISTRY')
                for index in range(nvalues):
                    name, data, kind = winreg.EnumValue(key,index)
                    require(type(data) is str and len(data) < 8192, 'STARTUP_REGISTRY')
                    values.append([name,data,kind])
                found.append({'hive':str(hive),'view':view,'values':values})
    return found


def audit(profile, cwd, *, stage_callback=None):
    _stage(stage_callback, 'audit-startup')
    startup = profile['startup']
    audit_path_configuration(startup['pth_candidates'], registry_values(startup['version']), startup['registry'])
    audit_site_roots(startup['roots'])
    for archive in startup['archives']:
        audit_archive(archive)
    for row in startup['pins']:
        require(record(row['path']) == row, 'STARTUP_PIN')
    _stage(stage_callback, 'audit-cwd')
    cwd = ordinary(cwd, directory=True)
    require(not any(p.suffix.casefold() in ('.dll','.pyd') for p in cwd.iterdir()), 'STARTUP_CWD_DLL')
    _stage(stage_callback, 'audit-deadline')
    require(profile['deadline_clock'] == deadline_clock(), 'DEADLINE_CLOCK')
    require(time.monotonic() < profile['deadline'], 'DEADLINE')


def policy(profile):
    row = profile['policy']
    source = ordinary(row['path'])
    with source.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT and hashlib.sha256(raw).hexdigest() == row['sha256'], 'POLICY_SOURCE')
    namespace = {'__name__':'rp1_sealed_policy','__file__':str(source)}
    exec(compile(raw, str(source), 'exec'), namespace)
    return types.SimpleNamespace(**namespace)


def validate_profile(value):
    fields = {'variant','image','selected','prefix','base_prefix','base_executable','paths',
              'startup','policy','bootstrap','deadline','deadline_clock','requests','native_commands','user_site','store_userbase'}
    require(type(value) is dict and set(value) == fields, 'PROFILE_SCHEMA')
    require(value['variant'] in ('CONTROLLER_ONLY','OWNED_SELECTED_PROTOTYPE','OWNED_RUNTIME') and
            type(value['deadline']) in (int,float) and math.isfinite(value['deadline']), 'PROFILE')
    require(type(value['deadline_clock']) is str and value['deadline_clock'], 'PROFILE_CLOCK')
    for name in ('image','selected','prefix','base_prefix','base_executable','requests'):
        require(type(value[name]) is str and os.path.isabs(value[name]) and '\0' not in value[name], 'PROFILE_PATH')
    require(type(value['paths']) is list and all(type(p) is str and os.path.isabs(p)
            for p in value['paths']), 'PROFILE_PATHS')
    require(type(value['user_site']) is bool, 'PROFILE_SITE')
    base = value['store_userbase']
    store_base = (value['user_site'] is False and type(base) is str and
                  0 < len(base) <= 4096 and os.path.isabs(base) and '\0' not in base)
    require((value['variant'] == 'CONTROLLER_ONLY' and base is None) or
        (value['variant'] == 'OWNED_SELECTED_PROTOTYPE' and store_base) or
        (value['variant'] == 'OWNED_RUNTIME' and (base is None or store_base)), 'PROFILE_STORE_BASE')
    require(type(value['startup']) is dict and set(value['startup']) ==
            {'roots','archives','pth_candidates','pins','registry','version'} and type(value['native_commands']) is dict, 'PROFILE_STARTUP')
    for field in ('policy','bootstrap'):
        row = value[field]
        require(type(row) is dict and set(row) == {'path','size','sha256','links'} and
                os.path.isabs(row['path']) and type(row['sha256']) is str and
                len(row['sha256']) == 64, 'PROFILE_SOURCE')
    return value


def controller_profile(root, executable, env):
    """Controller3.14 test fixture only; never a selected-runtime authority."""
    require(sys.version_info[:2] == (3,14) and norm(executable) == norm(sys.executable), 'CONTROLLER')
    root = ordinary(root, directory=True)
    env = dict(env)
    env['__PYVENV_LAUNCHER__'] = str(executable)
    probe = ('import sys,json,site;print(json.dumps({"paths":sys.path[1:],'
             '"prefix":sys.prefix,"base_prefix":sys.base_prefix,'
             '"base_executable":sys._base_executable,"user_site":site.ENABLE_USER_SITE,'
             '"user_site_path":site.getusersitepackages()}))')
    observation = json.loads(subprocess.check_output([str(executable),'-B','-c',probe],
                executable=image(), env=env, cwd=root))
    paths = observation['paths']
    roots = [p for p in paths if Path(p).is_dir()]
    native = Path(image())
    pins = [record(native), record(Path(sys.base_prefix)/'Lib/site.py')]
    dll = Path(sys.base_prefix)/f'python{sys.version_info.major}{sys.version_info.minor}.dll'
    if dll.exists():
        pins.append(record(dll))
    requests = root/'requests'
    requests.mkdir()
    profile = {'variant':'CONTROLLER_ONLY', 'image':str(native), 'selected':str(executable),
        **{key:observation[key] for key in ('prefix','base_prefix','base_executable','user_site')},
        'paths':paths, 'startup':{'roots':roots, 'archives':[p for p in paths if p.endswith('.zip')],
            'pth_candidates':[str(native.with_suffix('._pth')), str(dll.with_suffix('._pth'))],
            'pins':pins, 'registry':registry_values(), 'version':list(sys.version_info[:2])},
        'policy':record(Path(__file__).with_name('recursive_policy.py')),
        'bootstrap':record(__file__), 'deadline':time.monotonic()+120, 'deadline_clock':deadline_clock(),
        'requests':str(requests), 'native_commands':{}, 'store_userbase':None}
    validate_profile(profile)
    if observation['user_site']:
        # The controller fixture allows normal startup only while its optional
        # user-site directory is absent. Bind absence before future children;
        # the selected venv always disables user-site through its pinned cfg.
        profile['startup']['pth_candidates'].append(observation['user_site_path'])
    audit(profile, root)
    return profile


def _env_value(name):
    rows = []
    for key, value in os.environ.items():
        require(type(key) is str and type(value) is str, 'ENV_SHAPE')
        if key.casefold() == name.casefold():
            rows.append(value)
    require(len(rows) <= 1, 'ENV_DUPLICATE')
    return rows[0] if rows else None


def _in_any_job():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetCurrentProcess.restype = ctypes.c_void_p
    api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    inside = ctypes.c_int()
    require(api.IsProcessInJob(api.GetCurrentProcess(), None, ctypes.byref(inside)) and
            inside.value, 'OUTSIDE_JOB')


def _owned_store_runtime():
    family = '\\program files\\windowsapps\\pythonsoftwarefoundation.python.3.12_'
    native, base = norm(image()), norm(sys.base_prefix)
    return (sys.version_info[:2] == (3, 12) and family in native and family in base and
            native.endswith('\\python3.12.exe') and norm(Path(native).parent) == base)


def _store_local_root():
    """Derive the account-local role from the already-attested Store alias."""
    alias = Path(sys._base_executable)
    require(alias.is_absolute() and len(alias.parents) >= 4 and
            alias.name.casefold() == 'python.exe' and
            re.fullmatch(r'PythonSoftwareFoundation\.Python\.3\.12_[a-z0-9]+',
                         alias.parent.name, re.IGNORECASE) is not None and
            alias.parents[1].name.casefold() == 'windowsapps' and
            alias.parents[2].name.casefold() == 'microsoft' and
            alias.parents[3].name.casefold() == 'local' and
            alias.parents[3].parent.name.casefold() == 'appdata', 'STORE_FAMILY')
    return alias.parents[3], alias.parent.name


def _validate_store_userbase(value):
    local, family = _store_local_root()
    expected = local / 'Packages' / family / 'LocalCache/local-packages'
    require(type(value) is str and 0 < len(value) <= 4096 and os.path.isabs(value) and
            '\0' not in value and '..' not in Path(value).parts and
            norm(value) == norm(expected), 'STORE_USERBASE')
    return value  # Preserve actual spelling at the public child boundary.


def owned_profile(bound):
    """Bind the already-attested child without launching an identity probe."""
    require(type(bound) is dict and set(bound) ==
            {'version','deadline','requests','bootstrap','policy'}, 'OWNED_PROFILE_SCHEMA')
    require(type(bound['version']) is int and bound['version'] == 1 and
            type(bound['deadline']) in (int, float) and math.isfinite(bound['deadline']),
            'OWNED_PROFILE_DEADLINE')
    requests = ordinary(bound['requests'], directory=True)
    for name in ('bootstrap', 'policy'):
        row = bound[name]
        require(type(row) is dict and set(row) == {'path','size','sha256','links'} and
                record(row['path']) == row, 'OWNED_PROFILE_SOURCE')
    import site
    paths = sys.path[1:]
    require(paths and all(type(path) is str and os.path.isabs(path) for path in paths),
            'OWNED_PROFILE_PATHS')
    roots, archives = [], []
    for path in paths:
        if path.casefold().endswith('.zip'):
            archives.append(path)
        else:
            require(startup_exists(path), 'STARTUP_PATH')
            roots.append(str(ordinary(path, directory=True)))
    native, base_prefix = Path(image()), Path(sys.base_prefix)
    dll = base_prefix / f'python{sys.version_info.major}{sys.version_info.minor}.dll'
    pins = [record(native), record(dll), record(base_prefix / 'Lib/site.py')]
    if norm(sys.prefix) != norm(sys.base_prefix):
        pins.append(record(Path(sys.prefix) / 'pyvenv.cfg'))
    user_site, userbase = site.ENABLE_USER_SITE, _env_value('PYTHONUSERBASE')
    if _owned_store_runtime():
        require(type(userbase) is str and userbase and os.path.isabs(userbase) and
                user_site is False and _env_value('PYTHONNOUSERSITE') == '1', 'OWNED_PROFILE_STORE')
        _validate_store_userbase(userbase)
    else:
        require(userbase is None, 'OWNED_PROFILE_STORE')
    startup = {'roots': roots, 'archives': archives,
        'pth_candidates': [str(native.with_suffix('._pth')), str(dll.with_suffix('._pth'))] +
                          ([site.getusersitepackages()] if user_site else []),
        'pins': pins, 'registry': registry_values(), 'version': list(sys.version_info[:2])}
    return validate_profile({'variant': 'OWNED_RUNTIME', 'image': str(native),
        'selected': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
        'base_executable': sys._base_executable, 'paths': paths, 'startup': startup,
        'policy': bound['policy'], 'bootstrap': bound['bootstrap'], 'deadline': bound['deadline'],
        'deadline_clock': deadline_clock(), 'requests': str(requests), 'native_commands': {},
        'user_site': user_site, 'store_userbase': userbase})


def install_owned_root(bound, startup_deadline):
    """The source-local owner has completed identity/Job/go checks in this child."""
    nonce, cwd, profile = uuid.uuid4().hex, None, None
    try:
        _check_startup_deadline(startup_deadline)
        cwd = os.getcwd()
        profile = owned_profile(bound)
        return install_root(profile, startup_deadline)
    except BaseException as error:
        error.add_note('E_RP2_INSTALL_STAGE: ' + ('profile' if profile is None else 'install'))
        if profile is None:
            try:
                fallback = {'requests': bound.get('requests') if type(bound) is dict else None,
                    'deadline': bound.get('deadline') if type(bound) is dict else None,
                    'selected': sys.executable, 'image': '', 'deadline_clock': deadline_clock()}
                _publish_failure('install', nonce, 'profile', fallback, cwd, error,
                                 env=os.environ, startup_deadline=startup_deadline)
            except BaseException as publication:
                error.add_note('E_RP_FAILURE_RECORD: ' + _safe(repr(publication), 256))
        raise


def prepare_launch(args, profile, options, *, stage_callback=None):
    _stage(stage_callback, 'profile')
    validate_profile(profile)
    require(not options.get('shell', False) and options.get('executable') is None, 'CREATE_FORM')
    require(not options.get('creationflags', 0) & 0x01000000, 'BREAKAWAY')
    _stage(stage_callback, 'policy-source')
    p = policy(profile)
    _stage(stage_callback, 'argv')
    command = p.parse_argv(args, profile['selected'])
    _stage(stage_callback, 'environment')
    env = p.clean_env(dict(os.environ) if options.get('env') is None else options['env'], command['argv'][0],
                      store_userbase=profile['store_userbase'])
    profile=environment_profile(profile,env)
    cwd = options.get('cwd') or os.getcwd()
    audit(profile, cwd, stage_callback=stage_callback)
    # Refuse modified/missing code before the process exists, then verify again
    # from the literal to retain a pre-authored gate in the child itself.
    _stage(stage_callback, 'bootstrap-source')
    for row in (profile['bootstrap'], profile['policy']):
        p.read_checked(row['path'], row['sha256'], LIMIT)
    request = {'version':1, 'nonce':uuid.uuid4().hex, 'command':command, 'profile':profile}
    raw = json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    require(len(raw) <= LIMIT, 'REQUEST_SIZE')
    _stage(stage_callback, 'request-directory')
    path = ordinary(profile['requests'], directory=True)/(request['nonce']+'.json')
    _stage(stage_callback, 'request-write')
    with path.open('xb') as stream:
        stream.write(raw)
    code = loader_literal(profile['paths'], profile['bootstrap']['path'],
        profile['bootstrap']['sha256'], str(path), hashlib.sha256(raw).hexdigest())
    argv = [command['argv'][0], *command['flags'], '-c', code]
    require(len(subprocess.list2cmdline(argv).encode('utf-16-le'))//2 <= 32766, 'COMMAND_LENGTH')
    result = dict(options, env=env, executable=profile['image'])
    return argv, result


def _recursive_time(profile):
    require(profile['deadline_clock'] == deadline_clock(), 'DEADLINE_CLOCK')
    require(time.monotonic() < profile['deadline'], 'DEADLINE')


def install(profile):
    validate_profile(profile)
    original = subprocess.Popen
    require(not getattr(original, '_rp1_guard', False), 'ALREADY_INSTALLED')
    binding_lock = threading.Lock()
    class GuardedPopen(original):
        _rp1_guard = True
        @classmethod
        def _rp_bind_runtime_git(cls, root):
            """Trusted editable-runtime code may bind one exact read-only Git root."""
            require(profile['variant'] == 'OWNED_RUNTIME', 'GIT_BIND_PROFILE')
            with binding_lock:
                _recursive_time(profile)
                old = profile['native_commands'].get('git')
                if old is not None:
                    require(norm(root) == norm(old['root']), 'GIT_REBIND')
                git = shutil.which('git')
                require(git is not None and Path(git).name.casefold() == 'git.exe', 'GIT_IMAGE')
                if old is not None:
                    require(norm(git) == norm(old['image']['path']), 'GIT_REBIND')
                home = os.environ.get('HOME') or os.environ.get('USERPROFILE')
                if home is None and _owned_store_runtime():
                    local, _family = _store_local_root()
                    home = str(local.parent.parent)
                require(type(home) is str and os.path.isabs(home), 'GIT_HOME')
                spec = native_spec(git, root, bound_home=home)
                _recursive_time(profile)
                require(old is None or old == spec, 'GIT_REBIND')
                profile['native_commands']['git'] = spec

        def __init__(self, args, *positional, **options):
            nonce, stage, started = uuid.uuid4().hex, 'classify', False
            cwd = options.get('cwd')
            def progress(value):
                nonlocal stage
                stage = value
            try:
                cwd = cwd or os.getcwd()
                require(not positional, 'POSITIONAL_OPTIONS')
                first = os.fspath(args[0]) if isinstance(args,(list,tuple)) and args else ''
                if norm(first) != norm(profile['selected']):
                    _stage(progress, 'audit-deadline'); _recursive_time(profile)
                    spec = profile['native_commands'].get(first)
                    require(spec is not None, 'NATIVE_COMMAND')
                    if profile['variant'] == 'OWNED_RUNTIME':
                        require(list(args) in [
                            ['git','-C',spec['root'],'rev-parse','HEAD'],
                            ['git','-C',spec['root'],'status','--porcelain','--untracked-files=all']],
                            'GIT_VECTOR')
                    argv, kwargs = route_native(args,spec,options)
                    _recursive_time(profile)
                else:
                    argv, kwargs = prepare_launch(args, profile, options, stage_callback=progress)
                _stage(progress, 'create-process'); _recursive_time(profile); started = 'UNKNOWN'
                super().__init__(argv, **kwargs)
                self.args = args
            except BaseException as original_error:
                try:
                    _publish_failure('dispatch', nonce, stage, profile, cwd, original_error,
                        env=options.get('env', os.environ), argv=args, started=started)
                except BaseException as publication_error:
                    original_error.add_note('E_RP_FAILURE_RECORD: ' + _safe(repr(publication_error), 256))
                raise
    subprocess.Popen = GuardedPopen
    return GuardedPopen


def attest(profile, *, stage_callback=None):
    validate_profile(profile)
    require(profile['deadline_clock'] == deadline_clock(), 'DEADLINE_CLOCK')
    if profile['variant'] == 'OWNED_SELECTED_PROTOTYPE':
        require(os.environ.get('PYTHONNOUSERSITE') == '1' and
                os.environ.get('PYTHONUSERBASE') == profile['store_userbase'], 'STORE_ENV')
    for key, observed in (('image',image()), ('selected',sys.executable), ('prefix',sys.prefix),
            ('base_prefix',sys.base_prefix), ('base_executable',sys._base_executable)):
        require(norm(observed) == norm(profile[key]), 'FRAME_'+key.upper())
    import site
    require(list(sys.version_info[:2]) == profile['startup']['version'], 'STARTUP_VERSION')
    if site.ENABLE_USER_SITE is not profile['user_site'] or [norm(p) for p in sys.path] != [norm(p) for p in profile['paths']]:
        error=ValueError('E_RP_STARTUP_FRAME')
        error.add_note(json.dumps({'expected_user_site':profile['user_site'],
            'observed_user_site':site.ENABLE_USER_SITE,'expected_paths':profile['paths'],
            'observed_paths':sys.path},ensure_ascii=True)[:8192])
        raise error
    if profile['variant'] == 'OWNED_SELECTED_PROTOTYPE':
        require(sys.version_info[:2] == (3,12) and site.ENABLE_USER_SITE is False, 'SELECTED_FRAME')
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.GetCurrentProcess.restype = ctypes.c_void_p
        api.IsProcessInJob.argtypes = [ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
        inside = ctypes.c_int()
        require(api.IsProcessInJob(api.GetCurrentProcess(),None,ctypes.byref(inside)) and inside.value,
                'OUTSIDE_JOB')
    elif profile['variant'] == 'OWNED_RUNTIME':
        _in_any_job()
        require(not profile['user_site'] or not startup_exists(site.getusersitepackages()), 'USER_SITE')
        require(_env_value('PYTHONUSERBASE') == profile['store_userbase'], 'STORE_ENV')
        if _owned_store_runtime():
            require(type(profile['store_userbase']) is str and profile['store_userbase'] and
                    site.ENABLE_USER_SITE is False and _env_value('PYTHONNOUSERSITE') == '1', 'STORE_ENV')
            _validate_store_userbase(profile['store_userbase'])
        else:
            require(profile['store_userbase'] is None, 'STORE_ENV')
    audit(profile, os.getcwd(), stage_callback=stage_callback)


def install_root(profile, startup_deadline):
    """Install after the owner's identity/go gates, before authored work."""
    nonce, stage, cwd = uuid.uuid4().hex, 'profile', None
    def progress(value):
        nonlocal stage
        stage = value
    try:
        cwd = os.getcwd()
        validate_profile(profile)
        profile = environment_profile(dict(profile), os.environ)
        _check_startup_deadline(startup_deadline)
        initial = sys.path[:]
        try:
            if sys.path and [norm(p) for p in sys.path[1:]] == [norm(p) for p in profile['paths']]:
                sys.path.pop(0)
            attest(profile, stage_callback=progress); _check_startup_deadline(startup_deadline)
            profile = observed_profile(profile)
            _stage(progress, 'policy-source'); policy(profile); _check_startup_deadline(startup_deadline)
            result = install(profile); _check_startup_deadline(startup_deadline)
            return result
        finally:
            sys.path[:] = initial
    except BaseException as original_error:
        try:
            _publish_failure('install', nonce, stage, profile, cwd, original_error,
                env=os.environ, startup_deadline=startup_deadline)
        except BaseException as publication_error:
            original_error.add_note('E_RP_FAILURE_RECORD: ' + _safe(repr(publication_error), 256))
        raise


_STAGES = frozenset({'classify', 'profile', 'policy-source', 'argv', 'environment',
    'audit-startup', 'audit-cwd', 'audit-deadline', 'bootstrap-source',
    'request-directory', 'request-write', 'create-process'})


def deadline_clock(): return time.get_clock_info('monotonic').implementation


def _stage(callback, value):
    require(value in _STAGES, 'FAILURE_STAGE')
    if callback is not None: callback(value)


def _safe(value, maximum=512):
    try: return str(value)[:maximum]
    except Exception: return '<unavailable>'


def _check_startup_deadline(value):
    require(type(value) in (int, float) and math.isfinite(value) and
            time.monotonic() < value, 'STARTUP_DEADLINE')


def _publish_failure(phase, nonce, stage, profile, cwd, original, *, env=None,
                     argv=None, started=False, startup_deadline=None):
    require(phase in ('install', 'dispatch') and len(nonce) == 32 and
            all(c in '0123456789abcdef' for c in nonce) and stage in _STAGES, 'FAILURE_FRAME')
    def finite(value):
        return value if type(value) in (int, float) and math.isfinite(value) else None
    profile = profile if type(profile) is dict else {}
    try: directory = ordinary(profile.get('requests'), directory=True)
    except Exception: directory = ordinary(cwd, directory=True)
    try:
        argv_bytes = json.dumps([os.fspath(v) for v in argv], ensure_ascii=True).encode() if isinstance(argv, (list, tuple)) else b'<unavailable>'
    except Exception: argv_bytes = b'<unavailable>'
    keys = sorted(_safe(key, 96) for key in env.keys())[:64] if hasattr(env, 'keys') else []
    detail = {'version': 1, 'scope': 'RP1_CORRECTED_PREAUTHORED_FAILURE',
        'publication_method': 'EXCLUSIVE_PENDING_THEN_RENAME', 'phase': phase, 'nonce': nonce, 'stage': stage,
        'pid': os.getpid(), 'ppid': os.getppid(), 'authored_child_started': started,
        'cwd': _safe(cwd, 1024), 'selected': _safe(profile.get('selected'), 1024),
        'expected_image': _safe(profile.get('image'), 1024),
        'deadline_clock': _safe(profile.get('deadline_clock'), 128),
        'recursive_deadline': finite(profile.get('deadline')), 'startup_deadline': finite(startup_deadline),
        'monotonic_now': time.monotonic(), 'argv_digest': hashlib.sha256(argv_bytes).hexdigest(),
        'environment_keys': keys, 'error_type': type(original).__name__, 'error': _safe(original, 1024),
        'notes': [_safe(note, 384) for note in getattr(original, '__notes__', [])[:4]]}
    raw = json.dumps(detail, ensure_ascii=True, allow_nan=False, sort_keys=True).encode()
    if len(raw) > 8192:
        detail.update(environment_keys=[], notes=[], cwd=detail['cwd'][:256],
            selected=detail['selected'][:256], expected_image=detail['expected_image'][:256],
            error=detail['error'][:256])
        raw = json.dumps(detail, ensure_ascii=True, allow_nan=False, sort_keys=True).encode()
    require(len(raw) <= 8192, 'FAILURE_SIZE')
    validate_failure_record(detail)
    pending = directory / ('rp1-' + phase + '-' + nonce + '.failure.pending')
    final = directory / ('rp1-' + phase + '-' + nonce + '.failure.json')
    with pending.open('xb') as stream: stream.write(raw)
    os.rename(pending, final)  # Windows refuses an existing final path.
    return final


def validate_loader_failure_record(value):
    fields = {'version', 'scope', 'phase', 'nonce', 'stage', 'pid', 'ppid', 'authored_child_started',
              'error_type', 'error', 'notes', 'bootstrap_sha256', 'request_sha256'}
    require(type(value) is dict and set(value) == fields and type(value['version']) is int and
        value['version'] == 1 and value['scope'] == 'RP1_CORRECTED_LOADER_FAILURE' and
        value['phase'] == 'loader' and value['stage'] in
        ('loader-path0', 'loader-paths', 'loader-source', 'loader-exec'), 'LOADER_FAILURE_SCHEMA')
    for key, size in (('nonce', 32), ('bootstrap_sha256', 64), ('request_sha256', 64)):
        require(type(value[key]) is str and len(value[key]) == size and
                all(c in '0123456789abcdef' for c in value[key]), 'LOADER_FAILURE_DIGEST')
    require(type(value['pid']) is int and value['pid'] > 0 and type(value['ppid']) is int and
            value['ppid'] >= 0 and value['authored_child_started'] is False, 'LOADER_FAILURE_STATE')
    require(type(value['error_type']) is str and len(value['error_type']) <= 128 and
        type(value['error']) is str and len(value['error']) <= 256 and type(value['notes']) is list and
        len(value['notes']) <= 2 and all(type(n) is str and len(n) <= 128 for n in value['notes']), 'LOADER_FAILURE_ERROR')
    return True


def validate_failure_record(value):
    fields = {'version', 'scope', 'publication_method', 'phase', 'nonce', 'stage', 'pid', 'ppid',
        'authored_child_started', 'cwd', 'selected', 'expected_image', 'deadline_clock',
        'recursive_deadline', 'startup_deadline', 'monotonic_now', 'argv_digest',
        'environment_keys', 'error_type', 'error', 'notes'}
    require(type(value) is dict and set(value) == fields and type(value['version']) is int and
        value['version'] == 1 and value['scope'] == 'RP1_CORRECTED_PREAUTHORED_FAILURE' and
        value['publication_method'] == 'EXCLUSIVE_PENDING_THEN_RENAME' and
        value['phase'] in ('install', 'dispatch') and value['stage'] in _STAGES and
        type(value['nonce']) is str and len(value['nonce']) == 32 and
        all(c in '0123456789abcdef' for c in value['nonce']), 'FAILURE_SCHEMA')
    require(type(value['pid']) is int and value['pid'] > 0 and type(value['ppid']) is int and value['ppid'] >= 0 and
        (value['authored_child_started'] is False or value['authored_child_started'] == 'UNKNOWN'), 'FAILURE_STATE')
    for key, bound in (('cwd', 1024), ('selected', 1024), ('expected_image', 1024),
                       ('deadline_clock', 128), ('error_type', 128), ('error', 1024)):
        require(type(value[key]) is str and len(value[key]) <= bound, 'FAILURE_STRING')
    for key in ('recursive_deadline', 'startup_deadline', 'monotonic_now'):
        require(value[key] is None or (type(value[key]) in (int, float) and math.isfinite(value[key])), 'FAILURE_CLOCK')
    require(type(value['argv_digest']) is str and len(value['argv_digest']) == 64 and
            all(c in '0123456789abcdef' for c in value['argv_digest']), 'FAILURE_ARGV_DIGEST')
    for key, count, bound in (('notes', 4, 384), ('environment_keys', 64, 96)):
        require(type(value[key]) is list and len(value[key]) <= count and
                all(type(item) is str and len(item) <= bound for item in value[key]), 'FAILURE_LIST')
    return True


def enter(request, digest):
    # The literal supplied this request digest from its trusted parent boundary.
    try:
        source = ordinary(request)
        with source.open('rb') as stream:
            raw = stream.read(LIMIT+1)
        require(hashlib.sha256(raw).hexdigest() == digest, 'REQUEST_DIGEST')
        doc = decode_request(raw)
        profile = validate_profile(doc['profile'])
        p = policy(profile)
        command = p.parse_argv(doc['command']['argv'], profile['selected'])
        require(command == doc['command'], 'COMMAND_BINDING')
        attest(profile)
        install(observed_profile(profile))
    except BaseException as original:
        try:
            # A retained failure belongs only to this exclusive parent request.
            path = Path(request)
            require(len(path.stem) == 32 and all(c in '0123456789abcdef' for c in path.stem), 'FAILURE_NONCE')
            detail = {'nonce':path.stem, 'error_type':type(original).__name__,
                'error':str(original)[:2048], 'notes':[str(n)[:512] for n in getattr(original,'__notes__',[])[:4]]}
            temporary = path.with_suffix('.failure.pending')
            with temporary.open('x',encoding='utf-8') as stream:
                json.dump(detail,stream,ensure_ascii=True)
            os.rename(temporary,path.with_suffix('.failure.json'))
        except Exception as cleanup:
            original.add_note('E_RP_FAILURE_RECORD: '+repr(cleanup)[:256])
        raise
    sys.orig_argv = command['argv'][:]
    mode, target, tail = command['mode'], command['target'], command['tail']
    main = types.ModuleType('__main__')
    sys.modules['__main__'] = main
    main.__dict__.update(__builtins__=__builtins__, __package__=None, __spec__=None,
                         __loader__=None, __cached__=None)
    if mode == 'm':
        sys.argv = ['-m', *tail]
        sys.path.insert(0, os.getcwd())
        runpy._run_module_as_main(target, alter_argv=True)
    elif mode == 'c':
        sys.argv = ['-c', *tail]
        sys.path.insert(0, '')
        authored = compile(target, '<string>', 'exec')
        # Python3.14 registers CLI -c source for traceback rendering. Replace the
        # trusted loader's cache with the actual command's source, as direct -c
        # does.3.12 lacks this API and retains its ordinary traceback behavior.
        import linecache
        if hasattr(linecache, '_register_code'):
            linecache._register_code(authored,target,'<string>')
        exec(authored, main.__dict__)
    else:
        filename = os.path.abspath(target)
        sys.argv = [target, *tail]
        sys.path.insert(0, str(Path(filename).parent))
        main.__file__ = filename
        from importlib.machinery import SourceFileLoader
        main.__loader__ = SourceFileLoader('__main__', filename)
        with open(filename, 'rb') as stream:
            authored = stream.read()
        exec(compile(authored, filename, 'exec'), main.__dict__)


def observed_profile(profile):
    """After attestation, retain real CPython spelling; identities already match.

    Windows path casing is not a different native file. Never rewrite authored
    sys.path/sys.executable just to match a coordinator's spelling.
    """
    return dict(profile,image=image(),selected=sys.executable,prefix=sys.prefix,
        base_prefix=sys.base_prefix,base_executable=sys._base_executable,paths=sys.path[:])


def environment_profile(profile,env):
    # Existing sanitized _Session environments explicitly disable user-site.
    # Accept this stricter controller mode, without enabling any new import
    # directory or changing real interpreter flags. Selected3.12 remains False.
    no_user=next((v for k,v in env.items() if k.upper()=='PYTHONNOUSERSITE'),None)
    if profile['variant']=='CONTROLLER_ONLY' and profile['user_site'] and no_user=='1':
        return dict(profile,user_site=False)
    return profile


def native_spec(git, root, *, bound_home=None):
    """Closed read-only Git profile. Unknown repository features fail closed."""
    root=ordinary(root,directory=True)
    gitdir=ordinary(root/'.git',directory=True)
    require(not os.path.lexists(root/'.gitmodules') and
            not os.path.lexists(gitdir/'config.worktree'), 'GIT_FEATURE')
    # Preserve the existing account trust settings. Bind ordinary system/global
    # config instead of replacing them with an empty global config (which changes
    # safe.directory behavior). This closed prototype supports these exact roots.
    home=Path(bound_home if bound_home is not None else
              (os.environ.get('HOME') or os.environ.get('USERPROFILE') or Path.home()))
    require(home.is_absolute(),'GIT_HOME')
    configs=[gitdir/'config', Path(git).parent.parent/'etc/gitconfig',home/'.gitconfig']
    optional=[home/'.config/git/config']
    require(not os.environ.get('XDG_CONFIG_HOME'),'GIT_CONFIG_XDG')
    for candidate in optional:
        require(not os.path.lexists(candidate),'GIT_CONFIG_XDG')
    rows=[]
    for config in configs:
        ordinary(config)
        require(config.stat().st_size<=65536,'GIT_CONFIG')
        # Git deliberately supports repeated values (notably safe.directory).
        # This parser only screens section/key names; exact full bytes, including
        # every repeated value, remain bound by the file record.
        parser=configparser.RawConfigParser(strict=False,interpolation=None)
        parser.read_string(config.read_text(encoding='utf-8'))
        require(not parser.defaults(),'GIT_CONFIG')
        core={'repositoryformatversion','filemode','bare','logallrefupdates','symlinks',
              'ignorecase','longpaths','autocrlf','safecrlf','quotepath','eol','fscache'}
        for section in parser.sections():
            lower=section.casefold()
            require(lower in ('core','user','safe','http','pull','init','credential','filter "lfs"','diff "astextplain"') or
                    lower.startswith(('remote "','branch "','credential "')), 'GIT_CONFIG_SECTION')
            if lower=='core':
                require(set(parser[section])<=core,'GIT_CONFIG_HELPER')
        rows.append(record(config))
    vectors=[['git','--version']]
    vectors += [['git','-C',str(root),*tail] for tail in (
        ['rev-parse','HEAD'],['status','--porcelain','--untracked-files=all'],
        ['symbolic-ref','--short','HEAD'])]
    return {'image':record(git),'root':str(root),'configs':rows,'absent':[str(p) for p in optional],
            'home':str(home),'vectors':vectors}


def route_native(args,spec,options):
    require(type(spec) is dict and set(spec)=={'image','root','configs','absent','home','vectors'} and
            type(args) in (list,tuple) and list(args) in spec['vectors'], 'GIT_VECTOR')
    require(native_spec(spec['image']['path'],spec['root'],bound_home=spec['home'])==spec,'GIT_CHANGED')
    allowed={'stdin','stdout','stderr','bufsize','close_fds','cwd','env','text',
             'universal_newlines','encoding','errors','creationflags'}
    require(set(options)<=allowed and options.get('creationflags',0) in (0,0x08000000), 'GIT_OPTIONS')
    env=dict(os.environ) if options.get('env') is None else dict(options['env'])
    require(not any(str(k).upper().startswith('GIT_') for k in env),'GIT_ENV')
    # Per-child settings only. Do not edit any user's Git configuration.
    supplied_home=env.get('HOME') or env.get('USERPROFILE')
    require(supplied_home is None or norm(supplied_home)==norm(spec['home']), 'GIT_HOME')
    env.update(GIT_CONFIG_SYSTEM=spec['configs'][1]['path'],GIT_CONFIG_GLOBAL=spec['configs'][2]['path'],
               GIT_OPTIONAL_LOCKS='0')
    argv=[spec['image']['path'],'--no-pager','--no-optional-locks','-c','core.fsmonitor=false',
          '-c','filter.lfs.process=','-c','filter.lfs.clean=','-c','filter.lfs.smudge=',
          '-c','filter.lfs.required=false',*args[1:]]
    return argv,dict(options,env=env,executable=spec['image']['path'])
