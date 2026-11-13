#!/usr/bin/env python3
"""Portable authored-coding acceptance; never whole-skill or AI-truth proof.

Retains commands, stdout/stderr, generated inputs, mutated copies and receipts.
Only newly created runtime temporary files may be cleaned by existing code.
No installer, learned model, provider, native Beads/Dolt, Git write or retry.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

CASES = ('freshness', 'unicode', 'approval', 'resume')
CHECKS = {'source-accounting','save','fresh-recall','unchanged-resume',
          'changed-source','revoked-access','budget','forged-pack',
          'optional-stale','coding-tests','preservation'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, code):
    if not ok:
        raise ValueError(code)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value))


def ordinary_chain(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        require(not part.is_symlink() and not getattr(part, 'is_junction', lambda:False)(),
                'E_OUTPUT_REDIRECT')
        if part.exists():
            require(not getattr(part.stat(), 'st_file_attributes', 0) & 0x400,
                    'E_OUTPUT_REDIRECT')
    return path


def new_output(path):
    path = ordinary_chain(path)
    require(not path.exists(), 'E_OUTPUT_EXISTS')
    require(path.parent.is_dir(), 'E_OUTPUT_PARENT_REQUIRED')
    path.mkdir(exist_ok=False)
    return path


def outside_packages(path, roots):
    """Resolve the existing parent before a new leaf is opened (incl. Win aliases)."""
    path = ordinary_chain(path)
    # strict resolution invokes the platform's final-path implementation. An
    # unavailable filesystem identity is a refusal, never a lexical fallback.
    physical = path.parent.resolve(strict=True) / path.name
    for root in roots:
        canonical_root = Path(root).resolve(strict=True)
        require(not physical.is_relative_to(canonical_root), 'E_OUTPUT_PHYSICAL_PACKAGE')
    return path


def command_directory(output, label):
    require(label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label),
            'E_COMMAND_LABEL')
    folder = output/'commands'
    folder.mkdir(exist_ok=True)
    target = folder/label
    target.mkdir(exist_ok=False)
    return target


def child_json(completed):
    # Always report the original child failure before considering JSON syntax.
    require(completed.returncode == 0,
            'E_CHILD_EXIT %s: %s' % (completed.returncode,
                 completed.stderr.decode('utf-8', errors='replace')[-3000:]))
    try:
        value = json.loads(completed.stdout.decode('utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('E_CHILD_JSON: retained stdout is not one JSON value') from exc
    require(isinstance(value, dict), 'E_CHILD_JSON_OBJECT')
    return value


def expected_refusal(completed, code):
    require(completed.returncode == 2 and completed.stderr == b'', 'E_EXPECTED_REFUSAL_EXIT')
    try:
        value = json.loads(completed.stdout.decode('utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('E_EXPECTED_REFUSAL_JSON') from exc
    fields = {'ok','overall','evidence_class','adapter_calls','approvals_consumed','blockers'}
    require(isinstance(value,dict) and set(value) == fields and value['ok'] is False and
            value['overall'] == 'BLOCKED' and value['evidence_class'] == 'TEST_ONLY' and
            all(type(value[k]) is int and value[k] == 0 for k in ('adapter_calls','approvals_consumed')) and
            isinstance(value['blockers'],list) and len(value['blockers']) == 1 and
            isinstance(value['blockers'][0],str) and re.fullmatch(
                r'ValueError: '+re.escape(code)+r'(?:: [^\r\n]+)?',value['blockers'][0]),
            'E_EXPECTED_REFUSAL_CAUSE')
    return value


def capture_command(argv, target, cwd, env, timeout):
    argv = list(map(str,argv))
    save(target/'Intent.json', {'argv':argv,'timeout_seconds':timeout})
    completed, stdout, stderr, failure, execution = None, b'', b'', None, 'START_ERROR'
    try:
        completed = subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=timeout)
        stdout, stderr, execution = completed.stdout, completed.stderr, 'EXITED'
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        execution, failure = 'TIMEOUT', repr(exc)
    except OSError as exc:
        failure = repr(exc)
    # subprocess capture is binary. Retain the partial streams on timeout and
    # explicit empty streams on a failed start, not a made-up JSON response.
    require(isinstance(stdout,bytes) and isinstance(stderr,bytes), 'E_CHILD_CAPTURE_BYTES')
    (target/'stdout.log').write_bytes(stdout)
    (target/'stderr.log').write_bytes(stderr)
    record = {'argv':argv,'exit_code':completed.returncode if completed else None,
              'execution':execution,'failure':failure,
              'stdout':stream_record(target/'stdout.log'),'stderr':stream_record(target/'stderr.log')}
    save(target/'Command.json',record)
    return completed, record


def stream_record(path):
    raw = Path(path).read_bytes()
    return {'path':str(path),'size':len(raw),'sha256':sha(raw)}


def check_stream(record):
    path = ordinary_chain(record['path'])
    require(path.is_file() and path.stat().st_nlink == 1, 'E_STREAM_BINDING')
    require(stream_record(path) == record, 'E_STREAM_BINDING')


def check_bindings(receipt):
    check_stream(receipt['fixture_binding'])
    frozen = read(receipt['fixture_binding']['path'])
    project = ordinary_chain(frozen['project'])
    require(inventory(project) == frozen['source_sha256'] and
            sha(Path(__file__).read_bytes()) == frozen['generator_sha256'], 'E_FIXTURE_BINDING')
    runtime = receipt['runtime_identity']
    require(set(runtime) == {'controller','worker'} and isinstance(runtime['controller'],dict),
            'E_RUNTIME_BINDING')
    for entry in (runtime['controller'],runtime['worker']):
        if entry is not None:
            # Explicit executable paths can be venv symlinks; never resolve
            # away the launch identity or apply that exception to evidence.
            path = Path(entry['path'])
            require(path.is_absolute() and path.is_file() and stream_record(path) == entry,
                    'E_RUNTIME_BINDING')


def check_manifest(raw, manifest):
    cursor, pieces, ids = 0, [], set()
    for ordinal, unit in enumerate(manifest['units']):
        a, b = unit['range']
        require(isinstance(unit['id'],str) and re.fullmatch(r'U[0-9]{6}(?:\.[1-9][0-9]*)?',unit['id']) and
                unit['id'] not in ids and unit.get('ordinal',ordinal) == ordinal and a == cursor and
                type(a) is int and type(b) is int and a < b <= len(raw),
                'E_SOURCE_ACCOUNTING')
        if unit.get('parent') is not None:
            require(unit['id'].startswith(unit['parent']+'.'), 'E_SOURCE_ACCOUNTING')
        ids.add(unit['id'])
        part = raw[a:b]
        require(sha(part) == unit['sha256'], 'E_SOURCE_ACCOUNTING')
        part.decode('utf-8')
        pieces.append(part)
        cursor = b
    require(cursor == len(raw) and b''.join(pieces) == raw and bool(raw),
            'E_SOURCE_ACCOUNTING')


def check_pack(pack, sources, root, required):
    require(pack['coverage'] == 'UNVERIFIED' and pack['semantic_audit'] == 'UNVERIFIED',
            'E_FALSE_QUALIFICATION')
    require(pack['required_units'] == required, 'E_REQUIRED_DELIVERY')
    seen = set()
    for unit in pack['units']:
        pair = (unit['source_id'],unit['unit_id'])
        require(pair not in seen, 'E_SOURCE_REOPEN_DUPLICATE')
        seen.add(pair)
        source = sources[unit['source_id']]
        raw = (root/source['path']).read_bytes()
        expected = next(u for u in source['manifest']['units'] if u['id'] == unit['unit_id'])
        a, b = expected['range']
        require(unit['range'] == [a,b] and unit['path'] == source['path'] and
                unit['source_sha256'] == source['source_sha256'] == sha(raw) and
                unit['unit_sha256'] == expected['sha256'] == sha(raw[a:b]) and
                unit['text'].encode('utf-8') == raw[a:b] and
                unit['authority'] == source['authority'], 'E_SOURCE_REOPEN')
    require({(r['source_id'],r['unit_id']) for r in required} <= seen, 'E_REQUIRED_DELIVERY')


def validate_receipt(receipt):
    require(receipt.get('scope') in ('NO_WORKER_CORE_ONLY','RANKED_RUNTIME'),
            'E_ACCEPTANCE_INCOMPLETE')
    checks = receipt.get('checks', [])
    require({c['name'] for c in checks} == CHECKS and len(checks) == len(CHECKS)
            and all(c['passed'] is True for c in checks), 'E_ACCEPTANCE_INCOMPLETE')
    modes = ('literal','lexical','lsa') if receipt['scope'] == 'RANKED_RUNTIME' else ('literal',)
    expected = {(case,mode,mandatory) for case in CASES for mode in modes for mandatory in (False,True)}
    rows = receipt.get('measurements', [])
    require(len(rows) == len(expected) and
            {(r['case'],r['mode'],r['mandatory']) for r in rows} == expected and
            all(r['replay_verified'] is True and r['mandatory_missing'] == [] for r in rows),
            'E_ACCEPTANCE_INCOMPLETE')
    for command in receipt.get('commands', []):
        check_stream(command['stdout'])
        check_stream(command['stderr'])
    require(bool(receipt.get('commands')) and receipt.get('preservation') is True,
            'E_ACCEPTANCE_INCOMPLETE')
    require(receipt.get('whole_skill_ready') is False and receipt.get('semantic_truth') == 'UNVERIFIED',
            'E_FALSE_QUALIFICATION')
    check_bindings(receipt)
    require((receipt['runtime_identity']['worker'] is not None) ==
            (receipt['scope'] == 'RANKED_RUNTIME'), 'E_RUNTIME_BINDING')
    for row in rows:
        require(sha(Path(row['pack']).read_bytes()) == row['pack_sha256'], 'E_MEASUREMENT_BINDING')
        if row['mode'] != 'literal':
            require(bool(row['ranked_results']), 'E_ACCEPTANCE_EMPTY_RANKED_CONTROL')


def inventory(root):
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts}


def replay(args):
    basis = read(args.replay_input)
    scripts = (Path(args.package_root)/'scripts').resolve(strict=True)
    sys.path.insert(0, str(scripts))
    from knowledge_bridge import contracts as c, indexing, retrieval
    from knowledge_bridge.worker_client import WorkerClient
    policy, task = read(basis['policy']), read(basis['task'])
    doc = indexing.load(basis['index'],basis['project'],args.claude_mon_root,
                        allowed_sources=policy['allowed_source_ids'])
    pack = c.read(basis['pack'])
    worker = WorkerClient(args.worker_python,timeout=60) if args.worker_python else None
    retrieval.verify_pack(pack,doc,basis['project'],policy,task,worker)
    print(json.dumps({'ok':True,'pack_digest':pack['pack_digest'],
                      'verification':'FRESH_PROCESS_INTERNAL_PACK_VALIDATOR'}))


def execute(args, output):
    package, companion = Path(args.package_root).resolve(strict=True), Path(args.claude_mon_root).resolve(strict=True)
    require(not output.is_relative_to(package) and not output.is_relative_to(companion), 'E_OUTPUT_INSIDE_PACKAGE')
    before = {'mi':inventory(package),'cm':inventory(companion)}
    commands, checks, measurements = [], [], []
    receipt = {'schema_version':1,'scope':'RANKED_RUNTIME' if args.worker_python else 'NO_WORKER_CORE_ONLY',
               'checks':checks,'measurements':measurements,'commands':commands,
               'package_roots':{'mi':str(package),'cm':str(companion)},'before':before,
               'runtime_identity':{'controller':stream_record(Path(sys.executable).absolute()),
                                   'worker':stream_record(Path(args.worker_python).absolute()) if args.worker_python else None},
               'whole_skill_ready':False,'semantic_truth':'UNVERIFIED','producer_authentication':False,
               'native_beads_execution':False,'learned_model':False,
               'limitations':['Authored mechanical fixture, not AI coding comprehension or general retrieval quality.',
                              'Hash/stream consistency is not authenticated producer provenance.',
                              'Discovery misses remain visible; mandatory delivery is not discovery.',
                              'Only new runtime temporary files may be cleaned; inputs/results remain retained.']}
    temporary = output/'runtime-temp'
    temporary.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    cli = [sys.executable,'-B',str(package/'scripts/memory_integrity_workflow.py')]
    def invoke(label, argv, expected_error=None):
        target = command_directory(output, label)
        completed, record = capture_command(argv,target,output,env,180)
        commands.append(dict(record,label=label))
        require(completed is not None, 'E_CHILD_'+record['execution']+': '+str(record['failure']))
        if expected_error:
            expected_refusal(completed,expected_error)
            return None
        value = child_json(completed)
        require(value.get('ok') is True, 'E_CHILD_NOT_OK: '+label)
        return value
    def call(label, command, *extra, expected_error=None):
        return invoke(label, [*cli,command,'--claude-mon-root',companion,*extra], expected_error)
    def checked(name):
        checks.append({'name':name,'passed':True})
    try:
        fixture = Path(__file__).resolve().parents[1]/'fixtures/offline-first'
        oracle = read(fixture/'oracle.json')
        require(tuple(row['id'] for row in oracle['cases']) == CASES, 'E_ORACLE_CASES')
        project = output/'project'
        project.mkdir()
        names = ['rules.py','pipeline.py','storage.py','client.py','test_project.py','decision.md','distractor.py']
        for name in names:
            (project/name).write_bytes((fixture/name).read_bytes())
        large = oracle['large_source']
        prefix, suffix = large['prefix'].encode('utf-8'), large['suffix'].encode('utf-8')
        raw = prefix + large['fill'].encode('ascii')*(large['bytes']-len(prefix)-len(suffix)) + suffix
        (project/large['path']).write_bytes(raw)
        names.append(large['path'])
        original_project = inventory(project)
        save(output/'Frozen-Oracle.json', {'oracle':oracle,'project':str(project),'source_sha256':original_project,
                                           'generator_sha256':sha(Path(__file__).read_bytes())})
        receipt['fixture_binding'] = stream_record(output/'Frozen-Oracle.json')
        if args.worker_python:
            receipt['runtime_handshake'] = call('runtime-handshake','knowledge-status',
                                                '--worker-python',args.worker_python)
            receipt['runtime_pin_scope'] = 'WorkerClient validates pinned Semantica version/revision; not full environment inventory.'
        source_map = {'schema_version':1,'workspace_id':'offline-fixture','repository':'authored-fixture',
                      'sources':[{'id':Path(name).stem,'path':name,'authority':'AUTHORITATIVE'} for name in names]}
        save(output/'sources.json',source_map)
        index = output/'index'
        call('project','knowledge-project','--project-root',project,'--index-dir',index,
             '--source-map',output/'sources.json')
        generation = (index/'CURRENT').read_text(encoding='ascii').strip()
        doc = read(index/'generations'/generation/'generation.json')
        sources = doc['sources']
        for ident, source in sources.items():
            check_manifest((project/source['path']).read_bytes(), source['manifest'])
        checked('source-accounting')
        policy = {'schema_version':1,'workspace_id':'offline-fixture','task_id':'coding',
                  'allowed_source_ids':sorted(sources)}
        instructions = 'Inspect the authored current-source, Unicode and checkpoint coding fixture.'
        execution_digest = sha(canonical({'schema_version':3,'instructions':instructions}))
        task_base = {'schema_version':1,'task_id':'coding','require_graph':False,'max_bytes':4_000_000,
                     'execution_task_digest':execution_digest}
        save(output/'policy.json',policy)
        worker_flags = ['--worker-python',args.worker_python,'--worker-timeout','60'] if args.worker_python else []
        modes = ('literal','lexical','lsa') if args.worker_python else ('literal',)
        def query(label, task, query_text, mode='literal', root=project, access=None, expected_error=None):
            task_path, policy_path, pack_path = output/(label+'-task.json'), output/(label+'-policy.json'), output/(label+'-pack.json')
            save(task_path, task)
            save(policy_path, access or policy)
            flags = [] if mode == 'literal' else worker_flags
            result = call(label,'knowledge-retrieve','--project-root',root,'--index-dir',index,
                          '--policy-file',policy_path,'--task-file',task_path,
                          '--query-text',query_text,'--evidence-pack',pack_path,
                          '--embedding-mode','lexical' if mode == 'literal' else mode,
                          '--max-hops','0','--seeds','5','--max-results','5',*flags,
                          expected_error=expected_error)
            if expected_error:
                require(not pack_path.exists(), 'E_REFUSAL_LEFT_PACK')
                return None
            pack = read(pack_path)
            check_pack(pack,sources,root,task['required_units'])
            replay_path = output/(label+'-replay.json')
            save(replay_path,{'project':str(root),'index':str(index),'policy':str(policy_path),
                              'task':str(task_path),'pack':str(pack_path)})
            replay_flags = [] if mode == 'literal' else ['--worker-python',args.worker_python]
            invoke('replay-'+label,[sys.executable,'-B',__file__,'--package-root',package,
                                   '--claude-mon-root',companion,'--replay-input',replay_path,*replay_flags])
            return pack, task_path, policy_path, pack_path
        first = None
        for case in oracle['cases']:
            required = [{'source_id':ident,'unit_id':unit['id']} for ident in case['expected_sources']
                        for unit in sources[ident]['manifest']['units']]
            for mode in modes:
                for mandatory in (False,True):
                    task = dict(task_base,required_units=required if mandatory else [],require_graph=mode!='literal')
                    label = case['id']+'-'+mode+('-mandatory' if mandatory else '-discovery')
                    pack, task_path, policy_path, pack_path = query(label,task,case['query'],mode)
                    delivered = sorted({u['source_id'] for u in pack['units']})
                    measurements.append({'case':case['id'],'mode':mode,'mandatory':mandatory,
                         'expected_sources':case['expected_sources'],'delivered_sources':delivered,
                         'discovery_missing':sorted(set(case['expected_sources'])-set(delivered)) if not mandatory else None,
                         'mandatory_missing':sorted(set(case['expected_sources'])-set(delivered)) if mandatory else [],
                         'ranked_results':pack['retrieval']['results'],'reopened_bytes':sum(len(u['text'].encode('utf-8')) for u in pack['units']),
                         'pack_sha256':sha(pack_path.read_bytes()),'pack':str(pack_path),'replay_verified':True})
                    if first is None and mandatory:
                        first = (pack,task_path,policy_path,pack_path)
        test_task = dict(task_base,required_units=[])
        save(output/'test-task.json',test_task)
        tests = call('coding-tests','knowledge-test','--project-root',project,'--index-dir',index,
                     '--policy-file',output/'policy.json','--task-file',output/'test-task.json',
                     '--test-path','test_project.py','--output',output/'coding-tests.json')
        require(tests['tests_run'] == 4 and len(tests['cases']) == 4 and
                all(row['status'] == 'pass' for row in tests['cases']), 'E_CODING_TESTS')
        receipt['tests'] = tests
        checked('coding-tests')
        manifest = sources['long_notes']['manifest']
        reviews = {u['id']:{'interpretation':'Authored fixture review '+u['sha256'],
                            'findings':[],'disposition':'resolved','reviewer':'TEST_ONLY authored fixture',
                            'unresolved':[]} for u in manifest['units']}
        save(output/'reviews.json',reviews)
        pack, task_path, policy_path, pack_path = first
        knowledge = ['--knowledge-index',index,'--knowledge-root',project,
                     '--knowledge-policy',policy_path,'--knowledge-task',task_path]
        source, run = project/large['path'], output/'saved-run'
        run_args = ['--source',source,'--task',instructions,'--responses-file',output/'reviews.json',
                    '--run-dir',run,'--knowledge-pack',pack_path,*knowledge]
        call('save','offline-run',*run_args)
        checked('save')
        recalled = call('fresh-recall','verify','--run-map',run/'run-map.json','--source',source,
                        '--query','every','--require-knowledge',*knowledge)
        require([row['unit_id'] for row in recalled['recall']['records']] == [u['id'] for u in manifest['units']]
                and b''.join(row['original_excerpt'].encode('utf-8') for row in recalled['recall']['records']) == raw,
                'E_RECALL_SOURCE_ACCOUNTING')
        checked('fresh-recall')
        saved_inventory = inventory(run)
        resumed = call('unchanged-resume','offline-run',*run_args)
        require(resumed.get('resumed') is True and inventory(run) == saved_inventory, 'E_RESUME_MUTATED')
        checked('unchanged-resume')
        must = dict(task_base,required_units=[{'source_id':'rules','unit_id':sources['rules']['manifest']['units'][0]['id']}])
        changed = output/'changed-project'
        shutil.copytree(project,changed)
        (changed/'rules.py').write_bytes(b'FRESHNESS_SECONDS = 999\n')
        query('changed-source',must,'fresh',root=changed,expected_error='E_REQUIRED_STALE')
        checked('changed-source')
        query('revoked-access',must,'fresh',access=dict(policy,allowed_source_ids=[i for i in policy['allowed_source_ids'] if i!='rules']),
              expected_error='E_REQUIRED_ACCESS_REVOKED')
        checked('revoked-access')
        query('budget',dict(must,max_bytes=1),'fresh',expected_error='E_PACK_BUDGET')
        checked('budget')
        safe = dict(task_base,required_units=[{'source_id':'storage','unit_id':sources['storage']['manifest']['units'][0]['id']}])
        surviving, *_ = query('optional-stale',safe,'source_digest',root=changed)
        require('rules' not in {u['source_id'] for u in surviving['units']} and
                'storage' in {u['source_id'] for u in surviving['units']}, 'E_UNAFFECTED_LOST')
        checked('optional-stale')
        forged = json.loads(json.dumps(pack))
        forged['units'][0]['text'] = 'fabricated'
        forged['units'][0]['unit_sha256'] = sha(b'fabricated')
        forged['pack_digest'] = sha(canonical({k:v for k,v in forged.items() if k!='pack_digest'}))
        save(output/'forged-pack.json',forged)
        forged_args = list(run_args)
        forged_args[forged_args.index('--knowledge-pack')+1] = output/'forged-pack.json'
        forged_args[forged_args.index('--run-dir')+1] = output/'forged-run'
        call('forged-pack','offline-run',*forged_args,expected_error='E_PACK_SOURCE')
        require(not (output/'forged-run').exists(), 'E_FORGERY_CREATED_RUN')
        checked('forged-pack')
        receipt['preservation'] = (inventory(project) == original_project and
                                   inventory(package) == before['mi'] and inventory(companion) == before['cm'])
        require(receipt['preservation'], 'E_PRESERVATION_CHANGED')
        checked('preservation')
        validate_receipt(receipt)
        receipt['status'] = 'PASS_BOUNDED_RUNTIME' if args.worker_python else 'PASS_CORE_ONLY_RUNTIME_UNVERIFIED'
        receipt['failure'] = None
        code = 0
    except Exception:
        receipt.update(status='PARTIAL_OR_FAILED',failure=traceback.format_exc())
        code = 1
    save(output/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(output/'Receipt.json'),
                      'receipt_sha256':sha((output/'Receipt.json').read_bytes()),
                      'checks_passed':len(checks),'measurements':len(measurements),
                      'whole_skill_ready':False,'failure':receipt.get('failure')}))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root',required=True)
    parser.add_argument('--claude-mon-root',required=True)
    parser.add_argument('--worker-python')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--replay-input',type=Path)
    args = parser.parse_args()
    if args.replay_input:
        replay(args)
        return 0
    require(args.output_dir is not None, 'E_OUTPUT_REQUIRED')
    candidate = ordinary_chain(args.output_dir)
    package = ordinary_chain(args.package_root).resolve(strict=True)
    companion = ordinary_chain(args.claude_mon_root).resolve(strict=True)
    require(not candidate.is_relative_to(package) and not candidate.is_relative_to(companion),
            'E_OUTPUT_INSIDE_PACKAGE')
    outside_packages(candidate, [package,companion])
    return execute(args,new_output(args.output_dir))


if __name__ == '__main__':
    raise SystemExit(main())
