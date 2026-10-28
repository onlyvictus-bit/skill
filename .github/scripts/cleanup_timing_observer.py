"""TC1 observation adapter. Used only in NEW, AST-equivalent diagnostic copies."""
import ast
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time

TARGETS = ('memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py',
           'memory-integrity/scripts/knowledge_bridge/windows_job.py',
           'memory-integrity/tests_v2/test_knowledge_windows_shutdown.py')
LOGGER_SHA = '0b234e4988127d711e9183100bf47e13adefe772e5671bd5637535d2bdc4c87e'
IDENTITY_SHA = '5e7d30538b296acb763972e6553e927309c7c8319a2670a651920f7c793a6a88'
_log = _identity = _config = None
_sequence = 0
_guard = threading.RLock()
MAX_SPANS, MAX_DETAILS = 4096, 16384


def require(value, message):
    if not value: raise ValueError(message)


def load(name, digest=None):
    path = Path(__file__).with_name(name+'.py')
    raw = path.read_bytes()
    if digest: require(hashlib.sha256(raw).hexdigest() == digest, 'E_TC_SUPPORT_HASH')
    spec = importlib.util.spec_from_file_location('tc_'+name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def error_chain(error):
    result, seen = [], set()
    while error is not None and id(error) not in seen and len(result) < 8:
        seen.add(id(error))
        result.append({'type':type(error).__name__, 'message':str(error)[:1024],
                       'notes':[str(n)[:512] for n in getattr(error, '__notes__', [])[:8]]})
        error = error.__cause__ if error.__cause__ is not None else error.__context__
    return result


def bootstrap(config, target_file=None):
    global _log, _identity, _config
    require(_config in (None, config), 'E_TC_CONFIG_CHANGED')
    if _config is None:
        _log = load('extended_timing_log', LOGGER_SHA)
        identity = load('worker_diagnostic_events', IDENTITY_SHA)
        value = json.loads(Path(config).read_bytes())
        _log.configure(value['root'], value['watched_roots'], value['budget'])
        _identity = {'creation':identity.process_identity(os.getpid()), 'ppid':os.getppid(),
                     'parent_creation':identity.process_identity(os.getppid())}
        _config = config
    with span('module-entry', target_file or __file__, 0, 'bootstrap'):
        pass


@contextlib.contextmanager
def span(action, file, line, function, **extra):
    """Bounded recorder; active error is captured BEFORE potentially blocking close."""
    global _sequence
    require(_log is not None, 'E_TC_NOT_CONFIGURED')
    with _guard:
        _sequence += 1
        require(_sequence <= MAX_SPANS, 'E_TC_SPAN_LIMIT')
    fields = dict(_identity, code_file=file, line=line, function=function,
                  active_error=error_chain(sys.exception()), **extra)
    require(len(json.dumps(fields)) <= MAX_DETAILS, 'E_TC_DETAIL_LIMIT')
    with _log.span(action, **fields) as details:
        try:
            yield details
        except BaseException as error:
            details['error_chain'] = error_chain(error)
            raise


def size(value):
    return len(value) if isinstance(value, (bytes, str)) else None


def spawn(function, *args, **kwargs):
    """Observe the exact Popen call; do not change args, environment or ownership."""
    identity = load('worker_diagnostic_events', IDENTITY_SHA)
    caller = sys._getframe(1)
    process = None
    try:
        with span('process-create', caller.f_code.co_filename, caller.f_lineno,
                  caller.f_code.co_name) as fields:
            process = function(*args, **kwargs)
            fields.update(child_pid=process.pid, child_creation=identity.process_identity(process.pid))
        return process
    except BaseException as original:
        # Observation can fail AFTER Popen but BEFORE caller receives its handle.
        # Do not leak that exact owned process. Root creation is still suspended;
        # relay children also remain inside the caller's existing owned job.
        if process is not None:
            until = time.monotonic()+5
            try:
                if process.poll() is None: process.kill()
                process.wait(timeout=max(0,until-time.monotonic()))
                if process.stdin is not None: process.stdin.close()
            except Exception as cleanup:
                original.add_note('E_TC_CREATED_PROCESS_CLEANUP: '+repr(cleanup))
        raise


def child_source(raw, filename, config):
    with span('observer-child-overlay', filename, 0, 'child_source'):
        return overlay(raw.encode(), filename, config).decode()


def metadata(function, label, file, line, caller, *args, **kwargs):
    with span(label, file, line, caller, package=str(args[0])[:128] if args else None):
        return function(*args, **kwargs)


def _call_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute): return _call_name(node.value)+'.'+node.attr
    return ''


def _wrap(body, action, file, line, function, extra=()):
    call = ast.Call(ast.Attribute(ast.Name('_tc', ast.Load()), 'span', ast.Load()),
                    [ast.Constant(action), ast.Constant(file), ast.Constant(line), ast.Constant(function)], list(extra))
    return ast.With([ast.withitem(call)], body)


def overlay(raw, file, config, helper=None):
    """Add only observation wrappers. Inverse AST MUST equal the original AST."""
    original = ast.parse(raw)
    class Observe(ast.NodeTransformer):
        function = '<module>'
        polling = 0

        def visit_FunctionDef(self, node):
            previous = self.function; self.function = node.name
            node = self.generic_visit(node); self.function = previous
            if node.name in ('__init__','request','stop','close','resume','terminate',
                             'wait_empty','release','close_handles','relay','write') or node.name.startswith('test_'):
                first = 1 if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str) else 0
                node.body[first:] = [_wrap(node.body[first:], 'function:'+node.name, file, node.lineno, node.name)]
            return node

        def visit_While(self, node):
            self.polling += 1
            node = self.generic_visit(node)
            self.polling -= 1
            return _wrap([node], 'readiness-or-deadline-wait', file, node.lineno, self.function)

        def visit_Try(self, node):
            node = self.generic_visit(node)
            if self.function == 'relay' and node.finalbody:
                node.finalbody = [_wrap(node.finalbody, 'fixture-finally', file, node.lineno, self.function)]
            return node

        def visit_Call(self, node):
            # Fixture strings are transformed at their existing write boundary.
            # Keep the original literal inside child_source so inverse is exact.
            name = _call_name(node.func)
            if name.endswith('.write_text') and node.args:
                try: value = ast.literal_eval(node.args[0])
                except (ValueError, TypeError): value = None
                target = ast.unparse(node.func)
                if (isinstance(value, str) and ('import ' in value)) or 'actual.py' in target or 'distributed_worker.py' in target:
                    node.args[0] = ast.Call(ast.Attribute(ast.Name('_tc', ast.Load()), 'child_source', ast.Load()),
                        [node.args[0], ast.Constant(file+':generated-child'), ast.Constant(config)], [])
            node = self.generic_visit(node)
            if name in ('m.version','m.distribution'):
                node.args[:0] = [node.func, ast.Constant('installed-package-metadata'), ast.Constant(file),
                                 ast.Constant(node.lineno), ast.Constant(self.function)]
                node.func = ast.Attribute(ast.Name('_tc', ast.Load()), 'metadata', ast.Load())
            elif name in ('subprocess.Popen', 'popen'):
                node.args.insert(0, node.func)
                node.func = ast.Attribute(ast.Name('_tc', ast.Load()), 'spawn', ast.Load())
            return node

        def generic_visit(self, node):
            node = super().generic_visit(node)
            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Import, ast.ImportFrom, ast.If)):
                return node
            if self.polling: return node  # No per-poll event flood.
            calls = [n for n in ast.walk(node.test if isinstance(node,ast.If) else node) if isinstance(n, ast.Call)]
            names = [_call_name(n.func) for n in calls]
            action, extra = None, []
            if isinstance(node, (ast.Import, ast.ImportFrom)): action = 'imports'
            for call, name in zip(calls, names):
                if name.endswith('.write'):
                    action = 'pipe-write' if '.stdin.' in name else 'stream-write'
                    if call.args: extra = [ast.keyword('bytes', ast.Call(ast.Attribute(ast.Name('_tc',ast.Load()),'size',ast.Load()),[call.args[0]],[]))]
                elif name.endswith('.flush'): action = 'pipe-flush'
                elif name.endswith('.canonical'): action = 'request-serialize'
                elif name.endswith('.write_text'): action = 'fixture-data-write'
                elif name.endswith('.read_text'): action = 'fixture-data-read'
                elif name.endswith('.close'): action = 'stdin-close' if '.stdin.' in name else 'stream-close'
                elif name.endswith('.join'): action = 'writer-join'
                elif name.endswith('.wait'): action = 'fixture-child-wait' if 'Event' in ast.unparse(call) else 'process-wait'
                elif name.endswith('.AssignProcessToJobObject'): action = 'job-assign'
                elif name.endswith('.TerminateJobObject'): action = 'job-terminate'
                elif name.endswith('.QueryInformationJobObject'): action = 'job-membership-query'
                elif name.endswith('.WaitForSingleObject'): action = 'native-process-wait'
                elif name.endswith('.ResumeThread'): action = 'job-resume-thread'
                elif name.endswith('.cleanup'): action = 'directory-cleanup'
            if action: return _wrap([node], action, file, node.lineno, self.function, extra)
            return node
    changed = Observe().visit(ast.parse(raw))
    helper_path = str(Path(helper or __file__).absolute())
    prefix = ast.parse('import importlib.util as _tc_util\n'
        '_tc_spec=_tc_util.spec_from_file_location("tc_runtime",'+repr(helper_path)+')\n'
        '_tc=__import__("sys").modules.get("tc_runtime")\n'
        'if _tc is None:\n    _tc=_tc_util.module_from_spec(_tc_spec)\n'
        '    __import__("sys").modules["tc_runtime"]=_tc\n    _tc_spec.loader.exec_module(_tc)\n'
        'elif getattr(_tc,"__file__",None) != '+repr(helper_path)+':\n    raise ValueError("E_TC_RUNTIME_ALIAS")\n'
        '_tc.bootstrap('+repr(config)+','+repr(file)+')\n').body
    first = 1 if changed.body and isinstance(changed.body[0],ast.Expr) and isinstance(changed.body[0].value,ast.Constant) and isinstance(changed.body[0].value.value,str) else 0
    changed.body[first:first] = prefix
    result = ast.unparse(ast.fix_missing_locations(changed)).encode()+b'\n'
    require(inverse(result) == ast.dump(original, include_attributes=False), 'E_TC_INVERSE')
    compile(result, file, 'exec')
    return result


def inverse(raw):
    class Remove(ast.NodeTransformer):
        def visit_With(self, node):
            if len(node.items)==1 and _call_name(getattr(node.items[0].context_expr,'func',None))=='_tc.span':
                result = []
                for item in node.body:
                    changed = self.visit(item)
                    result.extend(changed if isinstance(changed,list) else [changed])
                return result
            return self.generic_visit(node)
        def visit_Call(self, node):
            name = _call_name(node.func)
            if name == '_tc.spawn': node.func = node.args.pop(0)
            elif name == '_tc.child_source': return self.visit(node.args[0])
            elif name == '_tc.metadata': node.func = node.args[0]; node.args = node.args[5:]
            return self.generic_visit(node)
    tree = ast.parse(raw)
    first = 1 if isinstance(tree.body[0],ast.Expr) and isinstance(tree.body[0].value,ast.Constant) and isinstance(tree.body[0].value.value,str) else 0
    require(isinstance(tree.body[first],ast.Import) and tree.body[first].names[0].asname=='_tc_util', 'E_TC_BOOTSTRAP')
    del tree.body[first:first+5]
    return ast.dump(Remove().visit(tree), include_attributes=False)


def report(paths):
    logger = load('extended_timing_log', LOGGER_SHA)
    segments = logger.summarize(paths)
    processes = {}
    for row in segments:
        d = row['details']
        if 'creation' in d:
            key = str(row['pid'])+':'+d['creation']
            value = {'pid':row['pid'], **{k:d[k] for k in ('creation','ppid','parent_creation')}}
            require(key not in processes or processes[key]==value, 'E_TC_PROCESS_IDENTITY_CHANGED')
            processes[key] = value
    for row in segments:
        d = row['details']
        if 'child_pid' not in d: continue
        require(type(d['child_pid']) is int and isinstance(d.get('child_creation'),str), 'E_TC_CHILD_IDENTITY')
        key = str(d['child_pid'])+':'+d['child_creation']
        node = {'pid':d['child_pid'],'creation':d['child_creation'],'ppid':row['pid'],'parent_creation':d['creation']}
        require(key not in processes or processes[key]==node, 'E_TC_CHILD_PARENT_MISMATCH')
        processes[key] = node
    lineage = []
    def known(value): return isinstance(value,str) and not value.startswith(('UNKNOWN','NONWINDOWS_UNVERIFIED'))
    for child in processes.values():
        parent = processes.get(str(child['ppid'])+':'+child['parent_creation'])
        matched = parent is not None and known(child['creation']) and known(child['parent_creation'])
        lineage.append({'child_pid':child['pid'],'child_creation':child['creation'],
                        'parent_pid':child['ppid'],'parent_creation':child['parent_creation'],
                        'status':'MATCHED_CREATION' if matched else 'UNMATCHED_OR_UNKNOWN'})
    expected = ('imports','installed-package-metadata','process-create','fixture-data-write',
                'readiness-or-deadline-wait','request-serialize','pipe-write','pipe-flush',
                'job-assign','job-resume-thread','job-membership-query','job-terminate',
                'native-process-wait','writer-join','stdin-close','stream-close','fixture-finally','directory-cleanup')
    coverage = {name:('OBSERVED' if any(r['action']==name for r in segments) else 'NOT_REACHED_OR_NOT_OBSERVED') for name in expected}
    categories = {'package_import_or_metadata':[], 'data_preparation':[], 'process_startup_or_wait':[],
                  'ipc':[], 'shutdown_cleanup':[], 'observer_overhead':[]}
    for row in segments:
        action = row['action']
        category = ('package_import_or_metadata' if action in ('imports','installed-package-metadata') else
                    'data_preparation' if action in ('request-serialize','fixture-data-write','fixture-data-read') else
                    'process_startup_or_wait' if action in ('process-create','process-wait','readiness-or-deadline-wait','fixture-child-wait') else
                    'ipc' if action in ('pipe-write','pipe-flush') else
                    'observer_overhead' if action=='observer-child-overlay' else
                    'shutdown_cleanup' if action.startswith('job-') or action in ('native-process-wait','writer-join','stdin-close','stream-close','fixture-finally','directory-cleanup') else None)
        if category: categories[category].append(row)
    category_view = {name:{'completed_max_seconds':max((r['duration_seconds'] for r in rows if r['duration_seconds'] is not None), default=None),
                           'unfinished':len([r for r in rows if r['status']=='UNFINISHED']),
                           'span_keys':[[r['pid'],r['thread'],r['span']] for r in rows]} for name,rows in categories.items()}
    unfinished_ipc = any(r['status']=='UNFINISHED' for r in categories['ipc'])
    unfinished_cleanup = any(r['status']=='UNFINISHED' for r in categories['shutdown_cleanup'])
    target_spans = [r for r in segments if r['action']=='function:test_blocked_real_pipe_writer_is_released_before_cleanup']
    original_errors = [r for r in segments if r['action']=='fixture-finally' and r['details'].get('active_error') and any(
        r['pid']==target['pid'] and r['thread']==target['thread'] and r['start_monotonic_ns']>=target['start_monotonic_ns'] and
        (target['end_monotonic_ns'] is None or r['start_monotonic_ns']<=target['end_monotonic_ns']) for target in target_spans)]
    return {'scope':'TC1_TIMING_ONLY_NOT_QUALIFICATION','segments':segments,'processes':list(processes.values()),
            'lineage':lineage,'coverage':coverage,'category_view':category_view,
            'original_error_status':'OBSERVED' if original_errors else 'NOT_REPRODUCED_OR_NOT_OBSERVED',
            'original_errors':[{'pid':r['pid'],'thread':r['thread'],'code':r['details'].get('code_file'),
                                'chain':r['details']['active_error']} for r in original_errors],
            'conclusion':'IPC_OR_CLEANUP_UNFINISHED_CAUSE_UNCONFIRMED' if unfinished_ipc or unfinished_cleanup else 'INCONCLUSIVE_PENDING_RESULT_REVIEW',
            'stage_complete':False,'gate1_complete':False,'root_cause_confirmed':False,
            'interpretation':'Inclusive spans overlap; never sum them. CPU is process-wide, not exclusive thread CPU. '
                'Missing END means unfinished/unknown duration. Python/site/DLL startup before first module event is uninstrumented. '
                'Recorder/import overhead perturbs the measured path. No package-install conclusion from metadata reads.'}


def markdown(result):
    lines = ['# TC1 process and code-segment timings', '', result['interpretation'], '',
             'Conclusion: '+result['conclusion'], '', 'Original exception: '+result['original_error_status'], '',
             'Captured error chains: '+json.dumps(result['original_errors'],ensure_ascii=True), '',
             'Category values below are MAX individual completed spans, NOT totals or exclusive costs.', '',
             '| Category | Max completed seconds | Unfinished |', '|---|---:|---:|']
    for name,row in result['category_view'].items():
        lines.append('| '+name+' | '+str(row['completed_max_seconds'])+' | '+str(row['unfinished'])+' |')
    lines += ['', '## Process relationships', '', '| Child PID / creation | Parent PID / creation | Status |', '|---|---|---|']
    for row in result['lineage']:
        lines.append('| '+str(row['child_pid'])+' / '+row['child_creation']+' | '+str(row['parent_pid'])+' / '+row['parent_creation']+' | '+row['status']+' |')
    lines += ['', '## Coverage', '']+[name+': '+status+'  ' for name,status in result['coverage'].items()]
    lines += ['', '## Individual segments', '',
             '| PID / thread | Code / line / function | Segment | Wall seconds | Process CPU seconds | Status |',
             '|---|---|---|---:|---:|---|']
    for row in result['segments']:
        d = row['details']; wall = row['duration_seconds']; cpu = row['cpu_duration_ns']
        code = str(d.get('code_file','unknown')).replace('|','/')+':'+str(d.get('line','?'))+' '+str(d.get('function','?'))
        lines.append('| '+str(row['pid'])+' / '+str(row['thread'])+' | '+code+' | '+row['action']+' | '+
            ('unknown' if wall is None else f'{wall:.6f}')+' | '+('unknown' if cpu is None else f'{cpu/1e9:.6f}')+' | '+row['status']+' |')
    return '\n'.join(lines)+'\n'
