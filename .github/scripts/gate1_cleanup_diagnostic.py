#!/usr/bin/env python3
"""One diagnostic-only Gate1 public cleanup observation; never fixes cleanup."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback


HERE = Path(__file__).resolve()
IMAGE_HELPER = HERE.with_name('gate1_image_successor.py')
IMAGE_HELPER_SHA = 'b1ef45b105f5d1b79bf25c4953dc2e6544ddfe994026e354313e30ddbf8df3af'
WORKER_RELATIVE = 'memory-integrity/scripts/knowledge_bridge/worker.py'
WORKER_SHA = '6ae67511cefef46bf1c80541bb1ceb0252f4649c03cbcd9f1422c5c51bbe108c'
OUTPUT_NAME = 'public-cleanup-diagnostic-20261021'
SCOPE = 'GATE1_PUBLIC_DISTRIBUTED_CLEANUP_DIAGNOSTIC'
MARKER = 'GATE1_CLEANUP_DIAGNOSTIC='
IMAGE_CONTRACT_SHA = 'dab1c6676e77c84fbe8780408c6a25040799857261d53d02d97d46a624a8856d'
IMAGE_RECEIPT_SHA = '19c95ff5462c42aa6e8780c4ee4a8bbb473eaa10492c93b29f3bc32e71d82c26'
PINNED_IMAGE_RECORDS = {
    'Expected-Runtime.json': '14e32a08969d50982a2153be9304816225013228c76b0e8c6f927e089ccea49d',
    'cleanup/Receipt.json': 'd2549b637f8d5ca4199657f02836f90f12115cc29ce5adfe7764a96fbd68a3dc',
    'tests-3/Case-Outcomes.json': '5574ce44852fae6481bdabce6601a0a660c8aaeb4bee5cc6d5b0149ce2b28ac3',
    'tests-3/unittest.log': 'bf8c2c0f1edeb6a9806ca041e4a5ae1f1de31a4e7b5ebb0e1b90e7f0f4664a82',
}

if hashlib.sha256(IMAGE_HELPER.read_bytes()).hexdigest() != IMAGE_HELPER_SHA:
    raise ValueError('E_CLEANUP_IMAGE_HELPER_CHANGED')
_spec = importlib.util.spec_from_file_location('sealed_gate1_image_successor', IMAGE_HELPER)
i = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(i)
g = i.g
OUTPUT = g.WORKSPACE / OUTPUT_NAME
IMAGE_CONTRACT = g.REPO / '.github/run-artifacts/offline-first-20261020/Gate1-Image-Contract-20261021.json'
CONTRACT_KEYS = {
    'schema_version', 'scope', 'head', 'parent_prepared', 'image_contract',
    'image_receipt', 'image_bound_records', 'image_history_coverage', 'source',
    'original_worker', 'overlay_sha256', 'diagnostic_source_manifest', 'output',
    'helper', 'fixture', 'producer_authentication', 'release_ready', 'installed',
    'native_execution', 'whole_skill_ready', 'gate1_complete', 'fix_validated', 'retry_authorized'
}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8')


_OLD_HANDLER = b"""    except Exception as exc:\n        sys.stdout.buffer.write(c.canonical({'ok':False,'error':type(exc).__name__+': '+str(exc)}));return 2\n"""


def _diagnostic_error_handler_bytes():
    """The active overlay formatter; it runs only after a worker error."""
    return b'''    except Exception as exc:
        # Diagnostic copy only: do not change cleanup/retry/success behavior.
        def _gate1_text(value, limit):
            try:text=str(value)
            except BaseException:text='<unprintable>'
            return (text if len(text)<=limit else text[:limit],len(text)>limit)
        def _gate1_frames(error):
            frames=[];cursor=error.__traceback__;cut=False
            while cursor is not None and len(frames)<32:
                frame=cursor.tb_frame;filename,cut1=_gate1_text(frame.f_code.co_filename,4096);function,cut2=_gate1_text(frame.f_code.co_name,256)
                cut=cut or cut1 or cut2;frames.append({'filename':filename,'function':function,'line':cursor.tb_lineno});cursor=cursor.tb_next
            return frames,cut or cursor is not None
        def _gate1_detail(error):
            seen=set();chain=[];current=error;relation='root';truncated=False
            while current is not None and id(current) not in seen and len(chain)<12:
                seen.add(id(current));message,cut=_gate1_text(current,4096);truncated=truncated or cut
                type_name,cut=_gate1_text(type(current).__name__,256);truncated=truncated or cut;frames,cut=_gate1_frames(current);truncated=truncated or cut
                row={'relation':relation,'type':type_name,'message':message,'frames':frames}
                notes=getattr(current,'__notes__',None)
                if isinstance(notes,list):
                    truncated=truncated or len(notes)>16;row['notes']=[]
                    for note in notes[:16]:text,cut=_gate1_text(note,2048);truncated=truncated or cut;row['notes'].append(text)
                for name in ('errno','winerror','filename','filename2'):
                    value=getattr(current,name,None)
                    if value is not None:
                        if name in ('errno','winerror'):
                            if isinstance(value,int) and not isinstance(value,bool):row[name]=value
                            else:truncated=True
                        else:text,cut=_gate1_text(value,4096);truncated=truncated or cut;row[name]=text
                chain.append(row)
                if current.__cause__ is not None:current=current.__cause__;relation='cause'
                else:current=current.__context__;relation='context'
            if current is not None:truncated=True
            root=chain[0] if chain else {'relation':'root','type':'Unknown','message':'','frames':[]}
            detail={'schema_version':1,'exception':root,'chain':chain,'frames':root['frames'],'truncated':truncated}
            while len(c.canonical(detail))>49152:
                detail['truncated']=True
                if detail['chain'] and detail['chain'][-1].get('notes'):detail['chain'][-1]['notes']=detail['chain'][-1]['notes'][:-1]
                elif detail['chain'] and detail['chain'][-1].get('frames'):detail['chain'][-1]['frames']=detail['chain'][-1]['frames'][:-1]
                elif len(detail['chain'])>1:detail['chain']=detail['chain'][:-1]
                else:detail={'schema_version':1,'exception':{'relation':'root','type':'DiagnosticTruncated','message':'detail exceeds bound','frames':[]},'chain':[],'frames':[],'truncated':True};break
            return detail
        try:
            detail=_gate1_detail(exc);message,unused=_gate1_text(exc,4096)
            error=type(exc).__name__+': '+message+'\\nGATE1_CLEANUP_DIAGNOSTIC='+c.canonical(detail).decode('utf-8')
        except BaseException:
            error='diagnostic serialization failed\\nGATE1_CLEANUP_DIAGNOSTIC={"truncated":true,"capture":"serializer-failed"}'
        sys.stdout.buffer.write(c.canonical({'ok':False,'error':error}));return 2
'''


# One formatter is used by the diagnostic copy; interrupted drafts are archived
# separately, not kept as competing implementations or test-only formatters.
_NEW_HANDLER = _diagnostic_error_handler_bytes()


def diagnostic_worker_bytes(original):
    g.require(g.sha(original) == WORKER_SHA, 'E_CLEANUP_WORKER_ORIGINAL_CHANGED')
    g.require(original.count(_OLD_HANDLER) == 1, 'E_CLEANUP_OVERLAY_PATTERN')
    overlay = original.replace(_OLD_HANDLER, _NEW_HANDLER)
    # Both normal serialization and the serializer-failure fallback include the
    # marker. Either branch remains an exit-2 error response.
    g.require(overlay.count(MARKER.encode('ascii')) == 2 and overlay.count(_OLD_HANDLER) == 0,
              'E_CLEANUP_OVERLAY_PATTERN')
    return overlay


def _bound_records(receipt):
    records = {}
    def add(record):
        if isinstance(record, dict) and set(record) >= {'path', 'size', 'sha256'}:
            actual = g.file_record(Path(record['path']))
            g.require(actual == record, 'E_CLEANUP_BOUND_RECORD_CHANGED')
            records[record['path']] = actual
    image_receipt = g.file_record(i.OUTPUT/'Receipt.json')
    g.require(image_receipt['sha256'] == IMAGE_RECEIPT_SHA, 'E_CLEANUP_IMAGE_RECEIPT_CHANGED')
    add(g.file_record(IMAGE_CONTRACT)); add(g.file_record(i.PREPARED)); add(image_receipt)
    for path in (i.OUTPUT/'Expected-Runtime.json', i.OUTPUT/'evaluation-claim.json', i.OUTPUT/'cleanup/Receipt.json',
                 i.OUTPUT/'tests-3/Case-Outcomes.json', i.OUTPUT/'tests-3/Receipt.json', i.OUTPUT/'tests-3/unittest.log'):
        record = g.file_record(path)
        relative = path.relative_to(i.OUTPUT).as_posix()
        if relative in PINNED_IMAGE_RECORDS:
            g.require(record['sha256'] == PINNED_IMAGE_RECORDS[relative], 'E_CLEANUP_PINNED_RECORD_CHANGED')
        add(record)
    for row in receipt.get('commands', []):
        for name in ('stdout', 'stderr'):
            add(row.get(name))
        command = Path(row['stdout']['path']).parent/'Command.json'
        intent = command.with_name('Intent.json')
        if command.is_file(): add(g.file_record(command))
        if intent.is_file(): add(g.file_record(intent))
    for row in receipt.get('suites', []):
        add(row.get('report'))
        if isinstance(row.get('report'), dict):
            case = json.loads(Path(row['report']['path']).read_text(encoding='utf-8'))
            for name in ('log', 'receipt'):
                value = case.get(name)
                if isinstance(value, str) and Path(value).is_file(): add(g.file_record(Path(value)))
    return dict(sorted(records.items()))


def _fixture_values(output):
    # Completion.setUp uses Path.write_text(newline=None). Match the host's
    # actual bytes, including Windows CRLF; all three sources are ASCII.
    client = 'from worker import work\ndef call():\n    return work()\n'.replace('\n', os.linesep).encode('ascii')
    worker = 'def work():\n    return 2\n'.replace('\n', os.linesep).encode('ascii')
    test = 'import unittest\nfrom worker import work\nclass Check(unittest.TestCase):\n    def test_work(self):\n        self.assertEqual(work(), 2)\n'.replace('\n', os.linesep).encode('ascii')
    mapping = {'schema_version':1,'workspace_id':'w','repository':'example','sources':[
        {'id':'client','path':'client.py','authority':'AUTHORITATIVE'},
        {'id':'worker','path':'worker.py','authority':'AUTHORITATIVE'},
        {'id':'test','path':'test_sample.py','authority':'SUPPORTING'}]}
    policy = {'schema_version':1,'workspace_id':'w','task_id':'t','allowed_source_ids':['client','worker','test']}
    task = {'schema_version':1,'task_id':'t','required_units':[{'source_id':'worker','unit_id':'U000001'}],
            'require_graph':True,'max_bytes':200000,
            'execution_task_digest':g.sha(_json({'schema_version':3,'instructions':'inspect work'}))}
    files = {'client.py':client,'worker.py':worker,'test_sample.py':test,
             'policy.json':_json(policy),'task.json':_json(task)}
    task_root = output/'task'; clone = output/'source'
    argv = [str(g.CONTROLLER),'-B',str(clone/'memory-integrity/scripts/memory_integrity_workflow.py'),'knowledge-retrieve',
            '--claude-mon-root',str(clone/'claude-mon'),'--project-root',str(task_root),'--index-dir',str(task_root/'index'),
            '--policy-file',str(task_root/'policy.json'),'--task-file',str(task_root/'task.json'),'--query-text','work',
            '--evidence-pack',str(task_root/'vector-distributed-local.json'),'--worker-python',str(g.WORKER),'--strategy','vector','--execution','distributed-local']
    return {'files':{name:g.sha(raw) for name,raw in sorted(files.items())},
            'mapping_sha256':g.sha(_json(mapping)), 'timeout_seconds':90,
            'stages':['sources','index','policy-task','public-vector-distributed'],
            'task_digest':task['execution_task_digest'],'argv':argv}, files, mapping


def build_contract():
    image_value = g.load_sealed(IMAGE_CONTRACT, IMAGE_CONTRACT_SHA)
    doc = i.validate_contract(image_value)
    i.check_preserved(image_value, doc, g.file_record(IMAGE_CONTRACT))
    receipt = g.load_sealed(i.OUTPUT/'Receipt.json', IMAGE_RECEIPT_SHA)
    original = Path(doc['source']) / WORKER_RELATIVE
    source_manifest = dict(doc['source_manifest'])
    overlay = diagnostic_worker_bytes(original.read_bytes())
    source_manifest[WORKER_RELATIVE] = g.sha(overlay)
    fixture, _, _ = _fixture_values(OUTPUT)
    return {'schema_version': 1, 'scope': SCOPE, 'head': g.HEAD,
            'parent_prepared': g.file_record(i.PREPARED), 'image_contract': g.file_record(IMAGE_CONTRACT),
            'image_receipt': g.file_record(i.OUTPUT/'Receipt.json'),
            'image_bound_records': _bound_records(receipt),
            'image_history_coverage': 'BOUND_RECORDS_ONLY_NOT_FULL_TEMP_TREE',
            'source': str(doc['source']), 'original_worker': g.file_record(original),
            'overlay_sha256': g.sha(overlay), 'diagnostic_source_manifest': source_manifest,
            'output': str(OUTPUT), 'helper': g.file_record(HERE), 'fixture': fixture,
            'producer_authentication': False, 'release_ready': False, 'installed': False,
            'native_execution': False, 'whole_skill_ready': False, 'gate1_complete': False,
            'fix_validated': False, 'retry_authorized': False}


def prepare_contract():
    """Normal-account input preparation only; never creates a runtime attempt."""
    private = g.REPO/'.github/run-artifacts/offline-first-20261020'
    g.ordinary(private)
    contract = private/'Gate1-Cleanup-Diagnostic-Contract-20261021.json'
    observation = private/'Gate1-Cleanup-Preparation-20261021.json'
    g.require(not contract.exists() and not observation.exists(), 'E_CLEANUP_PREPARATION_EXISTS')
    g.require(not OUTPUT.exists(), 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED')
    # All original validators remain mandatory. A denied historical read stops
    # here BEFORE a new input file, diagnostic copy or runtime attempt exists.
    value = build_contract()
    validate_contract(value)
    before = g.inventory(i.OUTPUT)
    check_bound_records(value)
    g.require(g.inventory(i.OUTPUT) == before, 'E_CLEANUP_IMAGE_ATTEMPT_CHANGED')
    result = {'scope':SCOPE,'status':'INPUT_ONLY_PREPARATION_FAILED_NO_RETRY',
              'producer_authentication':False,'gate1_complete':False,'worker_started':False,
              'diagnostic_attempt_created':False,'new_source_created':False,
              'release_ready':False,'installed':False,'native_execution':False,
              'retry_authorized':False,'failure':None}
    try:
        g.require(not OUTPUT.exists(), 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED')
        g.require(not contract.exists() and not observation.exists(), 'E_CLEANUP_PREPARATION_EXISTS')
        g.save(contract, value)
        result['contract'] = g.file_record(contract)
        g.require(build_contract() == value, 'E_CLEANUP_PREPARATION_INPUT_CHANGED')
        g.require(g.inventory(i.OUTPUT) == before, 'E_CLEANUP_IMAGE_ATTEMPT_CHANGED')
        g.require(not OUTPUT.exists(), 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED')
        g.require(g.file_record(contract) == result['contract'] and
                  g.load_sealed(contract, result['contract']['sha256']) == value,
                  'E_CLEANUP_PREPARATION_SAVED_CHANGED')
        g.require(not observation.exists(), 'E_CLEANUP_PREPARATION_EXISTS')
        result['status'] = 'INPUT_ONLY_CONTRACT_PREPARED_DIAGNOSTIC_UNRUN'
        result['prior_attempt_file_count'] = len(before)
        result['prior_attempt_map_digest'] = g.map_digest(before)
    except BaseException:
        result['failure'] = traceback.format_exc()
    g.ordinary(private)
    g.save(observation, result)
    print(json.dumps(dict(result, receipt=g.file_record(observation))))
    return 0 if result['status'] == 'INPUT_ONLY_CONTRACT_PREPARED_DIAGNOSTIC_UNRUN' else 1


def validate_contract(value):
    g.require(isinstance(value, dict) and set(value) == CONTRACT_KEYS and value['schema_version'] == 1 and
              value['scope'] == SCOPE and value['head'] == g.HEAD and value['source'] == str(g.WORKSPACE/'source') and
              value['output'] == str(OUTPUT) and value['fixture'] == _fixture_values(OUTPUT)[0] and
              value['image_history_coverage'] == 'BOUND_RECORDS_ONLY_NOT_FULL_TEMP_TREE' and
              all(value[k] is False for k in ('producer_authentication', 'release_ready', 'installed', 'native_execution', 'whole_skill_ready', 'gate1_complete', 'fix_validated', 'retry_authorized')),
              'E_CLEANUP_CONTRACT')
    g.require(value['parent_prepared'] == g.file_record(i.PREPARED) and value['parent_prepared']['sha256'] == i.PREPARED_SHA and
              value['image_contract'] == g.file_record(IMAGE_CONTRACT) and value['image_contract']['sha256'] == IMAGE_CONTRACT_SHA and
              value['image_receipt'] == g.file_record(i.OUTPUT/'Receipt.json') and value['image_receipt']['sha256'] == IMAGE_RECEIPT_SHA and
              value['helper'] == g.file_record(HERE), 'E_CLEANUP_INPUT_CHANGED')
    original = Path(value['source']) / WORKER_RELATIVE
    overlay = diagnostic_worker_bytes(original.read_bytes())
    g.require(value['original_worker'] == g.file_record(original) and value['overlay_sha256'] == g.sha(overlay),
              'E_CLEANUP_WORKER_CHANGED')
    expected_map = dict(i.g.load_sealed(i.PREPARED, i.PREPARED_SHA)['source_manifest'])
    expected_map[WORKER_RELATIVE] = value['overlay_sha256']
    g.require(value['diagnostic_source_manifest'] == expected_map,
              'E_CLEANUP_SOURCE_MANIFEST')
    receipt = g.load_sealed(i.OUTPUT/'Receipt.json', IMAGE_RECEIPT_SHA)
    g.require(value['image_bound_records'] == _bound_records(receipt),
              'E_CLEANUP_BOUND_RECORDS')
    return i.g.load_sealed(i.PREPARED, i.PREPARED_SHA)


def check_bound_records(value):
    for expected in value['image_bound_records'].values():
        g.require(g.file_record(Path(expected['path'])) == expected, 'E_CLEANUP_BOUND_RECORD_CHANGED')


def check_preserved(value, doc, prior_inventory, contract_record=None, diagnostic_source=None, baseline_record=None):
    g.require(g.file_record(HERE) == value['helper'], 'E_CLEANUP_HELPER_CHANGED')
    i.check_preserved(g.load_sealed(IMAGE_CONTRACT, IMAGE_CONTRACT_SHA), doc, g.file_record(IMAGE_CONTRACT))
    check_bound_records(value)
    g.require(g.inventory(i.OUTPUT) == prior_inventory, 'E_CLEANUP_IMAGE_ATTEMPT_CHANGED')
    if contract_record is not None:
        g.require(g.file_record(Path(contract_record['path'])) == contract_record, 'E_CLEANUP_CONTRACT_CHANGED')
    if diagnostic_source is not None:
        g.verify_manifest(diagnostic_source, value['diagnostic_source_manifest'])
    if baseline_record is not None:
        g.require(g.file_record(Path(baseline_record['path'])) == baseline_record,
                  'E_CLEANUP_START_MAP_CHANGED')


def preflight(contract, digest):
    record = g.file_record(Path(contract))
    g.require(record['sha256'] == digest, 'E_CLEANUP_EXTERNAL_SEAL')
    value = g.load_sealed(Path(contract), digest)
    doc = validate_contract(value)
    prior_inventory = g.inventory(i.OUTPUT)
    check_preserved(value, doc, prior_inventory, record)
    g.require(not OUTPUT.exists(), 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED')
    return value, doc, prior_inventory, record


def parse_public_reply(exit_code, stdout, stderr):
    g.require(exit_code in (0, 2), 'E_CLEANUP_CHILD_EXIT: '+str(exit_code))
    g.require(isinstance(stderr, bytes), 'E_CLEANUP_STDERR')
    if exit_code == 2 and not stdout.strip():
        raise ValueError('E_CLEANUP_CHILD_EXIT: 2: '+stderr[:4096].decode('utf-8', errors='replace'))
    try:
        reply = json.loads(stdout.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('E_CLEANUP_JSON') from error
    g.require(isinstance(reply, dict), 'E_CLEANUP_REPLY_SHAPE')
    return reply


def classify_public_reply(exit_code, reply, expected_pack):
    """Validate this exact public route before assigning a diagnostic state."""
    error = 'E_CLEANUP_PUBLIC_CONTRACT'
    g.require(isinstance(reply, dict), error)
    if exit_code == 2:
        g.require(set(reply) == {'ok','overall','evidence_class','adapter_calls','approvals_consumed','blockers'} and
                  reply['ok'] is False and reply['overall'] == 'BLOCKED' and reply['evidence_class'] == 'TEST_ONLY' and
                  type(reply['adapter_calls']) is int and reply['adapter_calls'] == 0 and
                  type(reply['approvals_consumed']) is int and reply['approvals_consumed'] == 0 and
                  isinstance(reply['blockers'], list) and len(reply['blockers']) == 1 and
                  isinstance(reply['blockers'][0], str), error)
        prefix = 'ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP'
        blocker = reply['blockers'][0]
        g.require(blocker == prefix or blocker.startswith(prefix+'\n'+MARKER), error)
        detail = diagnostic_from_blockers(reply['blockers'])
        return ('CAUSE_OBSERVED_PENDING_REVIEW', detail) if detail is not None else (
            'DIAGNOSTIC_MISSING_OR_TRUNCATED_INCONCLUSIVE', None)
    g.require(exit_code == 0 and set(reply) == {
        'ok','overall','generation','pack_digest','units','coverage','semantic_truth',
        'evidence_pack','retrieval_backend','limits_reached'}, error)
    def digest(value):
        return isinstance(value, str) and len(value) == 64 and all(ch in '0123456789abcdef' for ch in value)
    g.require(reply['ok'] is True and reply['overall'] == 'SOURCE_REOPENED' and
              digest(reply['generation']) and digest(reply['pack_digest']) and
              type(reply['units']) is int and reply['units'] > 0 and
              reply['coverage'] == 'UNVERIFIED' and reply['semantic_truth'] == 'UNVERIFIED' and
              reply['evidence_pack'] == str(expected_pack) and reply['retrieval_backend'] == 'SEMANTICA_OBSERVED' and
              isinstance(reply['limits_reached'], list) and
              all(isinstance(v, str) and v in ('max_visits','max_results') for v in reply['limits_reached']) and
              len(reply['limits_reached']) == len(set(reply['limits_reached'])), error)
    return 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE', None


def diagnostic_from_blockers(blockers):
    """Accept exactly one complete marker, never infer a cause from a wrapper."""
    if not isinstance(blockers, list):
        return None
    text = '\n'.join(item for item in blockers if isinstance(item, str))
    if text.count(MARKER) != 1:
        return None
    try:
        detail = json.loads(text.split(MARKER, 1)[1].strip())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(detail, dict) or set(detail) != {'schema_version','exception','chain','frames','truncated'} or \
            type(detail['schema_version']) is not int or detail['schema_version'] != 1 or \
            detail['truncated'] is not False or not isinstance(detail['chain'], list) or \
            not 2 <= len(detail['chain']) <= 12 or len(_json(detail)) > 49152:
        return None
    for number, row in enumerate(detail['chain']):
        if not isinstance(row, dict) or not {'relation','type','message','frames'} <= set(row) or \
                set(row) - {'relation','type','message','frames','notes','errno','winerror','filename','filename2'} or \
                row['relation'] not in (('root',) if number == 0 else ('cause','context')):
            return None
        for name, limit in (('type',256),('message',4096),('filename',4096),('filename2',4096)):
            if name in row and (not isinstance(row[name],str) or len(row[name]) > limit):
                return None
        for name in ('errno','winerror'):
            if name in row and type(row[name]) is not int:
                return None
        if 'notes' in row and (not isinstance(row['notes'],list) or len(row['notes']) > 16 or
                              any(not isinstance(note,str) or len(note) > 2048 for note in row['notes'])):
            return None
        if not isinstance(row['frames'],list) or len(row['frames']) > 32:
            return None
        for frame in row['frames']:
            if not isinstance(frame,dict) or set(frame) != {'filename','function','line'} or \
                    not isinstance(frame['filename'],str) or len(frame['filename']) > 4096 or \
                    not isinstance(frame['function'],str) or len(frame['function']) > 256 or \
                    type(frame['line']) is not int or frame['line'] <= 0:
                return None
    root = detail['chain'][0]
    if detail['exception'] != root or detail['frames'] != root['frames'] or \
            root['message'] != 'E_DISTRIBUTED_CLEANUP' or root['type'] != 'ValueError':
        return None
    if not any(row.get('errno') is not None or row.get('winerror') is not None or row.get('filename')
               for row in detail['chain'][1:]):
        return None
    return detail


def _copy_source(doc, value, output):
    source, clone = Path(doc['source']), output/'source'
    shutil.copytree(source, clone, copy_function=shutil.copyfile)
    worker = clone/WORKER_RELATIVE
    original = worker.read_bytes()
    g.require(g.sha(original) == value['original_worker']['sha256'], 'E_CLEANUP_COPY_WORKER')
    worker.write_bytes(diagnostic_worker_bytes(original))
    g.verify_manifest(clone, value['diagnostic_source_manifest'])
    return clone


def _fixture(output, expected):
    task, store = output/'task', output/'task/index'
    fixture, files, mapping = _fixture_values(output)
    g.require(fixture == expected, 'E_CLEANUP_FIXTURE_BINDING')
    task.mkdir()
    for name, raw in files.items():
        if name not in ('client.py','worker.py','test_sample.py'): continue
        (task/name).write_bytes(raw)
        g.require(g.sha((task/name).read_bytes()) == fixture['files'][name], 'E_CLEANUP_FIXTURE_WRITE')
    # The original index sees only three source files. Build metadata belongs
    # outside the source root; policy/task are written AFTER impact.build.
    with (output/'Build-Mapping.json').open('xb') as handle: handle.write(_json(mapping))
    _check_fixture(output, expected, requests_written=False, index_built=False)
    return task, store


def _fixture_request_files(output, expected):
    fixture, files, _ = _fixture_values(output)
    g.require(fixture == expected and (output/'task/index').is_dir(), 'E_CLEANUP_FIXTURE_BINDING')
    _check_fixture(output, expected, requests_written=False, index_built=True)
    for name in ('policy.json','task.json'):
        target = output/'task'/name
        with target.open('xb') as handle: handle.write(files[name])
        g.require(g.sha(target.read_bytes()) == expected['files'][name], 'E_CLEANUP_FIXTURE_WRITE')
    _check_fixture(output, expected, requests_written=True)


def _check_fixture(output, expected, requests_written, index_built=None):
    fixture, _, _ = _fixture_values(output)
    g.require(fixture == expected, 'E_CLEANUP_FIXTURE_BINDING')
    g.require(g.file_record(output/'Build-Mapping.json')['sha256'] == expected['mapping_sha256'],
              'E_CLEANUP_FIXTURE_MAPPING_CHANGED')
    names = ('client.py','worker.py','test_sample.py')
    if requests_written: names += ('policy.json','task.json')
    for name in names:
        g.require(g.file_record(output/'task'/name)['sha256'] == expected['files'][name],
                  'E_CLEANUP_FIXTURE_CHANGED: '+name)
    if not requests_written:
        g.require(all(not (output/'task'/name).exists() and not (output/'task'/name).is_symlink()
                      for name in ('policy.json','task.json')), 'E_CLEANUP_FIXTURE_STAGE')
    if requests_written: index_built = True
    store = output/'task/index'
    if index_built is True:
        g.require(store.is_dir(), 'E_CLEANUP_FIXTURE_STAGE')
        g.ordinary(store)
    elif index_built is False:
        g.require(not store.exists() and not store.is_symlink(), 'E_CLEANUP_FIXTURE_STAGE')


def run(contract, digest):
    value, doc, prior_inventory, record = preflight(contract, digest)
    env = i.windows_environment(dict(os.environ))
    g.require(env.get('USERPROFILE') == r'C:\Users\sakth', 'E_CLEANUP_NORMAL_CONTEXT')
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               KNOWLEDGE_WORKER_PYTHON=str(g.WORKER))
    for name in ('MODEL_PYTHON','KNOWLEDGE_MODEL_MANIFEST'): env.pop(name, None)
    output = g.new_workspace(OUTPUT, [Path(doc['source']), g.REPO, i.OUTPUT])
    commands = []
    baseline_record = None
    fixture_stage = None
    receipt = {'schema_version':1,'scope':SCOPE,'status':'HARNESS_OR_CAPTURE_FAILED','contract':record,
               'commands':commands,'failure':None,'preservation':False,'producer_authentication':False,
               'release_ready':False,'whole_skill_ready':False,'native_execution':False,'installed':False,
               'inference_sent':None,'gate1_complete':False,'fix_validated':False,'retry_authorized':False,
               'image_history_coverage':value['image_history_coverage']}
    try:
        g.save(output/'Before-Image-Attempt.json', prior_inventory)
        baseline_record = g.file_record(output/'Before-Image-Attempt.json')
        receipt['prior_attempt_start_map'] = baseline_record
        receipt['prior_attempt_start_map_digest'] = g.map_digest(prior_inventory)
        check_preserved(value, doc, prior_inventory, record, baseline_record=baseline_record)
        clone = _copy_source(doc, value, output)
        check_preserved(value, doc, prior_inventory, record, clone, baseline_record)
        host = g.sibling_module('offline_host_validation', clone/'.github/scripts')
        temp = output/'temp'; temp.mkdir(); env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
        def capture(label, argv, timeout, exits=(0,)):
            target = output/label; target.mkdir(); completed, row = host.capture_owned(argv, target, output, env, timeout)
            commands.append(dict(row, label=label))
            g.require(completed is not None and completed.returncode in exits, 'E_CLEANUP_CAPTURE: '+label)
            check_preserved(value, doc, prior_inventory, record, clone, baseline_record)
            return completed, target
        capture('preclaim-git',[str(g.GIT),'--no-optional-locks','-C',doc['repo'],'rev-parse','HEAD'],30)
        probe, probe_dir = capture('preclaim-runtime',[str(g.WORKER),'-B','-c',g.runtime_probe()],60)
        i.validate_runtime_observation(json.loads((probe_dir/'stdout.log').read_text(encoding='utf-8')), env, output)
        task, store = _fixture(output, value['fixture'])
        fixture_stage = False
        build_code = "import sys;sys.path.insert(0,sys.argv[1]);from knowledge_bridge import impact;import json;from pathlib import Path;impact.build(Path(sys.argv[2]),json.loads(Path(sys.argv[5]).read_text(encoding='utf-8')),Path(sys.argv[3]),Path(sys.argv[4]))"
        capture('build-index',[str(g.CONTROLLER),'-B','-c',build_code,str(clone/'memory-integrity/scripts'),str(task),str(store),str(clone/'claude-mon'),str(output/'Build-Mapping.json')],120)
        _check_fixture(output, value['fixture'], requests_written=False, index_built=True)
        _fixture_request_files(output, value['fixture'])
        fixture_stage = True
        argv = value['fixture']['argv']
        completed, target = capture('public-vector-distributed', argv, value['fixture']['timeout_seconds'], exits=(0,2))
        _check_fixture(output, value['fixture'], requests_written=True)
        reply = parse_public_reply(completed.returncode, (target/'stdout.log').read_bytes(), (target/'stderr.log').read_bytes())
        receipt['status'], detail = classify_public_reply(completed.returncode, reply, task/'vector-distributed-local.json')
        if detail is not None: receipt['diagnostic'] = detail
        receipt['inference_sent'] = False
        receipt['inference_claim_basis'] = 'sealed offline request and validated public reply; not network monitoring'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
        receipt['status'] = 'HARNESS_OR_CAPTURE_FAILED'
    finally:
        if fixture_stage is not None:
            try:
                _check_fixture(output, value['fixture'], requests_written=fixture_stage)
                receipt['fixture_preservation'] = True
            except BaseException:
                receipt['fixture_preservation'] = False
                receipt['fixture_preservation_failure'] = traceback.format_exc()
                receipt['status'] = 'HARNESS_OR_CAPTURE_FAILED'
        try:
            check_preserved(value, doc, prior_inventory, record, output/'source' if (output/'source').exists() else None,
                            baseline_record)
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'HARNESS_OR_CAPTURE_FAILED'
        g.save(output/'Receipt.json', receipt)
    print(json.dumps({'status':receipt['status'],'receipt':g.file_record(output/'Receipt.json'),
                      'failure':receipt['failure'],'whole_skill_ready':False}))
    return 0 if receipt['status'] in ('CAUSE_OBSERVED_PENDING_REVIEW','FAILURE_NOT_REPRODUCED_INCONCLUSIVE') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract'); parser.add_argument('--sha256')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--preflight-only', action='store_true'); args = parser.parse_args()
    if args.prepare_only:
        if args.contract or args.sha256 or args.preflight_only:
            parser.error('input preparation cannot also execute/preflight a diagnostic')
        sys.exit(prepare_contract())
    if not args.contract or not args.sha256:
        parser.error('--contract and --sha256 are required for diagnostic preflight/run')
    if args.preflight_only:
        preflight(args.contract, args.sha256); print('CLEANUP_DIAGNOSTIC_INPUTS_VERIFIED_NO_WORKER')
    else:
        sys.exit(run(args.contract, args.sha256))
