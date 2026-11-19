from pathlib import Path
import subprocess,sys,json,time,os,traceback
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[2];MI=Path(r'C:\Users\sakth\.codex\skills\memory-integrity');CM=Path(r'C:\Users\sakth\.codex\skills\claude-mon');PY=r'C:\Python314\python.exe';commands=[]
def capture(label,argv,timeout=180):
    print(label+': RUNNING',flush=True);t=time.monotonic();folder=ROOT/label;folder.mkdir();fault=None
    try:
        p=subprocess.run([str(x) for x in argv],cwd=ROOT,capture_output=True,timeout=timeout,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'});code=p.returncode;stdout=p.stdout;stderr=p.stderr
    except BaseException as e:
        code=None;stdout=getattr(e,'stdout',b'') or b'';stderr=getattr(e,'stderr',b'') or b'';fault=traceback.format_exc()
    (folder/'stdout.log').write_bytes(stdout);(folder/'stderr.log').write_bytes(stderr);row={'label':label,'argv':list(map(str,argv)),'seconds':time.monotonic()-t,'exit':code,'failure':fault};(folder/'Command.json').write_text(json.dumps(row,indent=2),encoding='utf-8');commands.append(row);print(label+f": {row['seconds']:.3f}s exit={code}",flush=True);return stdout
capture('cm-runtime',[PY,'-B',CM/'scripts/runtime_status.py'])
capture('mi-capabilities',[PY,'-B',MI/'scripts/memory_integrity_v2.py','capabilities','--claude-mon-root',CM])
capture('memory-live-health',[PY,'-B',MI/'scripts/memory_watchdog.py','status','--server','http://127.0.0.1:3111'],15)
worker=Path(r'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\build-validation\n3-retrieval-9ec6fb1db36444acba2945896e8b8d17\venv\Scripts\python.exe')
capture('selected312-identity',[worker,'-I','-S','-B','-c','import sys,json;print(json.dumps({"executable":sys.executable,"version":sys.version,"prefix":sys.prefix,"base_prefix":sys.base_prefix}))'],15)
groups=[('cm-cli',CM,'tests_v2','test_cli_input_contract.py'),('cm-budget',CM,'tests','test_context_budget.py'),('cm-budget-v2',CM,'tests_v2','test_budget.py'),('mi-extraction',MI,'tests_v2','test_extraction*.py'),('mi-pdf',MI,'tests_v2','test_pdf_extraction.py'),('mi-semantic',MI,'tests_v2','test_semantic_obligations.py'),('mi-memory-contract',MI,'tests_v2','test_watchdog*.py'),('mi-memory-boundary',MI,'tests_v2','test_memory_boundaries.py'),('mi-memory-http',MI,'tests','test_memory_watchdog.py'),('mi-offline-knowledge',MI,'tests_v2','test_knowledge_offline_engine.py'),('mi-model-contract',MI,'tests_v2','test_knowledge_model_runtime.py')]
runner=PROJECT/'.github/scripts/offline_ci_suite.py'
for name,package,tests,pattern in groups:capture(name,[PY,'-B',runner,'--package-root',package,'--test-dir',tests,'--pattern',pattern,'--output-dir',ROOT/(name+'-cases')])
(ROOT/'Commands.json').write_text(json.dumps(commands,indent=2),encoding='utf-8');print('BOUNDARY_CHECK_COMMANDS_COMPLETE',flush=True)
