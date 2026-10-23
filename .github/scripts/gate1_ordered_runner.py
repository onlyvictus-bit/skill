"""Select and observe ONE unchanged ordered Gate1 method; never a full suite."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve()
LEGACY = HERE.with_name('gate1_runner.py')
if hashlib.sha256(LEGACY.read_bytes()).hexdigest() != '13bf5ebccbd5f707f2f66c8dcd48ff73c18fb484bfc7f17b6698a66c574d51ae':
    raise ValueError('E_ORDERED_LEGACY_RUNNER_CHANGED')
_spec = importlib.util.spec_from_file_location('sealed_ordered_legacy_runner', LEGACY)
legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(legacy)
TARGET = 'test_knowledge_completion.RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay'
MODES = [('community','single'),('global','single'),('drift','single'),('vector','distributed-local')]
TEST_SHA = 'bb4156c62abe1e03aa69fd555c93a952612e1672090312ebee6a427c3ddaa89f'
RETAINED_SHA = '4aba6fe49641f86dcb548219f0c6efc8bbd2fbaa4e32f5be40703a1cee18453b'


def require(condition, reason):
    if not condition: raise ValueError(reason)


def choose_case(suite):
    cases = list(legacy.cases(suite))
    require(not any('_FailedTest' in case.id() for case in cases), 'E_ORDERED_CASE_SELECTION')
    selected = [case for case in cases if case.id() == TARGET]
    require(len(selected) == 1, 'E_ORDERED_CASE_SELECTION')
    return unittest.TestSuite(selected)


def ordinary(path):
    for part in (path, *path.parents):
        require(not part.is_symlink() and not getattr(part,'is_junction',lambda:False)(),
                'E_ORDERED_REDIRECTED_OUTPUT')
    if path.exists():
        require(path.is_dir() or path.stat().st_nlink == 1, 'E_ORDERED_LINKED_OUTPUT')


def save(path, value):
    ordinary(path)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,ensure_ascii=True)
        stream.write('\n')


class Observation:
    """Observe originals, never fabricate worker/test/verifier outcomes."""
    def __init__(self, source, worker, output, original_run, original_verify):
        self.source, self.worker, self.output = Path(source),Path(worker),Path(output)
        self.original_run, self.original_verify = original_run,original_verify
        self.events, self.fixture, self.active = [],None,None
        self.capture_errors = []

    def record(self, row):
        row['sequence'] = len(self.events)
        self.events.append(row)
        try:
            target = self.output/'Ordered-Calls'
            ordinary(target)
            target.mkdir(exist_ok=True)
            save(target/(str(row['sequence']).zfill(2)+'.json'),row)
        except Exception as error:
            # Preserve the original return/exception, but prohibit a usable verdict.
            self.capture_errors.append(type(error).__name__+': '+str(error))

    def run(self, argv, *args, **kwargs):
        if not isinstance(argv,(list,tuple)) or 'knowledge-retrieve' not in argv:
            return self.original_run(argv,*args,**kwargs)
        require(not args and kwargs == {'capture_output':True,'text':True,'timeout':90},
                'E_ORDERED_PUBLIC_OPTIONS')
        count = sum(row['phase']=='public' for row in self.events)
        require(count < len(MODES), 'E_ORDERED_PUBLIC_ORDER')
        require(len(argv)==24 and list(argv[:4]) == [sys.executable,'-B',
                str(self.source/'memory-integrity/scripts/memory_integrity_workflow.py'),'knowledge-retrieve'],
                'E_ORDERED_PUBLIC_ARGV')
        flags = dict(zip(argv[4::2],argv[5::2]))
        require(len(flags)==10 and set(flags)=={'--claude-mon-root','--project-root','--index-dir',
                '--policy-file','--task-file','--query-text','--evidence-pack','--worker-python',
                '--strategy','--execution'}, 'E_ORDERED_PUBLIC_ARGV')
        mode = (flags['--strategy'],flags['--execution'])
        require(mode==MODES[count], 'E_ORDERED_PUBLIC_ORDER')
        root = Path(flags['--project-root'])
        require(root.is_absolute() and root.parent==self.output/'retained-temp', 'E_ORDERED_FIXTURE')
        if self.fixture is None: self.fixture=root
        require(root==self.fixture and flags == {
            '--claude-mon-root':str(self.source/'claude-mon'),'--project-root':str(root),
            '--index-dir':str(root/'index'),'--policy-file':str(root/'policy.json'),
            '--task-file':str(root/'task.json'),'--query-text':'work',
            '--evidence-pack':str(root/('-'.join(mode)+'.json')),'--worker-python':str(self.worker),
            '--strategy':mode[0],'--execution':mode[1]}, 'E_ORDERED_FIXTURE')
        row = {'phase':'public','mode':list(mode),'argv':list(argv),'timeout':90,
               'capture_encoding':'SUBPROCESS_TEXT_REENCODED_UTF8_NOT_RAW_OS_BYTES'}
        self.active = {'mode':mode,'replays':0,'public_ok':False}
        try:
            result = self.original_run(argv,**kwargs)
            row.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
            self.active['public_ok']=result.returncode==0
            return result
        except BaseException as error:
            row.update(error_type=type(error).__name__,error=str(error))
            raise
        finally:
            self.record(row)

    def verify(self, pack, doc, root, policy, task, worker=None):
        active = self.active
        require(active is not None and active['public_ok'] and active['replays']<2 and
                Path(root)==self.fixture, 'E_ORDERED_REPLAY_ORDER')
        engine = pack['retrieval']['engine']
        require((engine['strategy'],engine['execution'])==active['mode'], 'E_ORDERED_REPLAY_ORDER')
        negative = active['replays']==1
        require((engine['generation_lease']=='0'*64)==negative, 'E_ORDERED_REPLAY_ORDER')
        row = {'phase':'negative-lease' if negative else 'replay','mode':list(active['mode']),
               'pack_digest':pack['pack_digest'],'generation':pack['generation'],
               'generation_lease':engine['generation_lease'],'lease_refusal':False}
        active['replays']+=1
        try:
            result = self.original_verify(pack,doc,root,policy,task,worker)
            row['returned']=True
            return result
        except BaseException as error:
            text=str(error)
            row.update(error_type=type(error).__name__,error=text[:131072],
                       error_complete=len(text)<=131072,
                       lease_refusal=negative and isinstance(error,ValueError) and 'LEASE' in text)
            raise
        finally:
            self.record(row)


def validate_ordered_result(row):
    require(row.get('target')==TARGET and row.get('selected_ids')==[TARGET] and
            row.get('outcomes',{}).get('started')==[TARGET] and
            len(row.get('outcomes',{}).get('finished',[]))==1 and
            row['outcomes']['finished'][0].get('id')==TARGET and
            row['outcomes']['finished'][0].get('outcome') in ('PASS','FAIL','ERROR') and
            row.get('capture_errors')==[], 'E_ORDERED_CASE_OUTCOME')
    subtests=row.get('subtests',[])
    require(len(subtests)==4 and
            [test.get('params') for test in subtests]==[
                {'strategy':s,'execution':e} for s,e in MODES] and
            all(test.get('outcome') in ('PASS','FAIL') for test in subtests),
            'E_ORDERED_SUBTESTS')
    events=row.get('events',[])
    require([e.get('mode') for e in events if e.get('phase')=='public']==[list(m) for m in MODES],
            'E_ORDERED_PHASES')
    ordered=[]
    for mode,subtest in zip(MODES,subtests):
        group=[event for event in events if event.get('mode')==list(mode)]
        ordered.extend(group)
        phases=[event.get('phase') for event in group]
        require(phases in (['public'],['public','replay'],['public','replay','negative-lease']),
                'E_ORDERED_PHASES')
        if subtest['outcome']=='PASS':
            require(phases==['public','replay','negative-lease'] and
                    group[0].get('returncode')==0 and group[1].get('returned') is True and
                    group[2].get('lease_refusal') is True and group[2].get('error_type')=='ValueError' and
                    group[2].get('error_complete') is True, 'E_ORDERED_PHASES')
    # Filtered per-mode order alone would accept a replay crossing the next
    # public boundary. The actual chronology must be contiguous ordered blocks.
    require(ordered==events, 'E_ORDERED_PHASES')
    all_pass=all(test['outcome']=='PASS' for test in subtests)
    require((row['outcomes']['finished'][0]['outcome']=='PASS')==all_pass, 'E_ORDERED_CASE_OUTCOME')
    return 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE' if all_pass else 'ORDERED_FAILURE_REQUIRES_DETAIL_REVIEW'


def bootstrap(package):
    require(package.name=='memory-integrity' and
            hashlib.sha256((package/'tests_v2/test_knowledge_completion.py').read_bytes()).hexdigest()==TEST_SHA,
            'E_ORDERED_ORIGINAL_TEST_CHANGED')
    target=HERE.with_name('retained_unittest.py')
    ordinary(target)
    raw=target.read_bytes()
    require(len(RETAINED_SHA)==64 and hashlib.sha256(raw).hexdigest()==RETAINED_SHA,
            'E_ORDERED_RETAINED_RUNNER_CHANGED')
    # Execute only the already checked bytes at the explicit helper path;
    # neither package/scripts nor PYTHONPATH may supply an import shadow.
    spec=importlib.util.spec_from_file_location('sealed_ordered_retained_unittest',target)
    retained=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(target),'exec'),retained.__dict__)
    return retained


def main():
    package = Path(sys.argv[sys.argv.index('--package-root')+1]).resolve(strict=True)
    output = Path(sys.argv[sys.argv.index('--output-dir')+1]).absolute()
    require(sys.argv[sys.argv.index('--pattern')+1]=='test_knowledge_completion.py' and
            '--exclude' not in sys.argv, 'E_ORDERED_SELECTION_ARGUMENTS')
    retained_unittest=bootstrap(package)
    if '--bootstrap-only' in sys.argv:
        require(len(sys.argv)==8,'E_ORDERED_BOOTSTRAP_ARGUMENTS')
        print(json.dumps({'status':'ORDERED_BOOTSTRAP_VERIFIED_NO_WORKER',
                          'retained_sha256':RETAINED_SHA,'retained_path':str(HERE.with_name('retained_unittest.py')),
                          'worker_started':False,'test_output_created':False}))
        return 0
    sys.path[:0]=[str(package/'scripts'),str(HERE.parent)]
    from knowledge_bridge import retrieval
    observation=Observation(package.parent,Path(os.environ['KNOWLEDGE_WORKER_PYTHON']),output,
                            subprocess.run,retrieval.verify_pack)
    records={'started':[],'finished':[]}; subtests=[]; discovered=[]
    class OrderedResult(legacy.RecordingResult):
        def addSubTest(self,test,subtest,error):
            subtests.append({'params':dict(subtest.params),'outcome':'PASS' if error is None else 'FAIL',
                             'error':None if error is None else str(error[1])})
            super().addSubTest(test,subtest,error)
    OrderedResult.records=records
    original_discover=unittest.TestLoader.discover
    def discover(loader,*args,**kwargs):
        suite=original_discover(loader,*args,**kwargs)
        discovered.extend(case.id() for case in legacy.cases(suite))
        return choose_case(suite)
    original_class=unittest.TextTestRunner.resultclass
    unittest.TestLoader.discover=discover
    unittest.TextTestRunner.resultclass=OrderedResult
    subprocess.run=observation.run; retrieval.verify_pack=observation.verify
    try:
        code=retained_unittest.main()
    finally:
        subprocess.run=observation.original_run; retrieval.verify_pack=observation.original_verify
        unittest.TestLoader.discover=original_discover; unittest.TextTestRunner.resultclass=original_class
        if output.is_dir():
            save(output/'Ordered-Outcomes.json',{'target':TARGET,'original_test_sha256':TEST_SHA,
                'selected_ids':[TARGET],'all_discovered_ids':discovered,'outcomes':records,
                'subtests':subtests,'events':observation.events,'capture_errors':observation.capture_errors,
                'observation_only':True,'gate1_complete':False})
    return code


if __name__=='__main__':
    raise SystemExit(main())
