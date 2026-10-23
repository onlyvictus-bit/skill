"""Cold-start budget regression; no packages/models downloaded or selected worker run."""
import argparse
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from knowledge_bridge import contracts as c, workflow, worker_client as wc
from knowledge_bridge.distributed_retrieval import DistributedClient
import memory_integrity_workflow as public


class KnowledgeTimeoutBudget(unittest.TestCase):
    def delayed_handshake(self, timeout=None):
        """Run the real deadline loop with50s simulated elapsed, no50s sleep."""
        reply={'ok':True,'bridge_version':wc.BRIDGE_VERSION,
               'semantica_version':wc.SEMANTICA_VERSION,'revision':wc.SEMANTICA_REVISION}
        class Process:
            pid=12345
            returncode=0
            def __init__(self): self.polled=False
            def poll(self):
                if not self.polled:
                    self.polled=True
                    return None
                return 0
            def wait(self,timeout): return 0
        def spawn(argv,**kwargs):
            kwargs['stdout'].write(c.canonical(reply));kwargs['stdout'].flush()
            return Process()
        worker=wc.WorkerClient(Path(sys.executable).absolute(),**({} if timeout is None else {'timeout':timeout}))
        # Only the OS process and clock are replaced. The production validation,
        # deadline loop, protocol read, cleanup and runtime-pin checks remain real.
        with patch.object(wc.subprocess,'Popen',side_effect=spawn), \
             patch.object(wc.time,'monotonic',side_effect=[0.0,50.0]), \
             patch.object(wc.time,'sleep'):
            return worker({'op':'handshake'})

    def test_default_worker_allows_50second_loading_then_returns_valid_reply(self):
        try: reply=self.delayed_handshake()
        except ValueError as exc: self.fail('Default rejected supported cold-start interval: '+str(exc))
        self.assertTrue(reply['ok'])

    def test_explicit_short_budget_still_times_out_without_retry(self):
        with self.assertRaisesRegex(ValueError,'E_WORKER_TIMEOUT: no resend'):
            self.delayed_handshake(timeout=30)

    def test_distributed_default_uses_supported_cold_start_budget(self):
        worker=DistributedClient(Path(sys.executable).absolute())
        self.assertEqual(worker.timeout,120)
        self.assertEqual(DistributedClient(Path(sys.executable).absolute(),timeout=15).timeout,15)

    def test_invalid_budgets_still_refuse_before_process_start(self):
        for cls in (wc.WorkerClient,DistributedClient):
            for value in (0,-1,121,float('inf'),float('nan'),True):
                with self.subTest(client=cls.__name__,value=value), self.assertRaisesRegex(ValueError,'TIMEOUT_LIMIT'):
                    cls(Path(sys.executable).absolute(),timeout=value)

    def test_public_retrieve_selects_120_by_default_and_preserves_override(self):
        parser=argparse.ArgumentParser();workflow.register(parser.add_subparsers(dest='command'))
        argv=['knowledge-retrieve','--claude-mon-root','cm','--project-root','project','--index-dir','index',
              '--policy-file','policy.json','--task-file','task.json','--evidence-pack','pack.json','--query-text','work']
        self.assertEqual(parser.parse_args(argv).worker_timeout,120)
        self.assertEqual(parser.parse_args(argv+['--worker-timeout','45']).worker_timeout,45)

    def test_public_offline_and_fresh_verify_select_120_by_default(self):
        for command,args in [('verify',['--run-map','run.json','--source','source.txt']),
                             ('offline-run',['--source','source.txt','--task','task','--responses-file','responses.json','--run-dir','run'])]:
            with self.subTest(command=command):
                output=io.StringIO()
                def observe(parsed): return {'ok':True,'budget':parsed.knowledge_worker_timeout}
                with patch.object(sys,'argv',['memory_integrity_workflow.py',command,'--claude-mon-root','cm',*args]), \
                     patch.object(public,'verify',side_effect=observe),patch.object(public,'offline_run',side_effect=observe), \
                     contextlib.redirect_stdout(output):
                    self.assertEqual(public.main(),0)
                self.assertEqual(json.loads(output.getvalue())['budget'],120)

    def test_programmatic_fresh_preflight_omitted_timeout_uses_120(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            task={'execution_task_digest':c.digest(c.canonical({'schema_version':3,'instructions':'timeout contract'}))}
            for name,value in [('policy',{'allowed_source_ids':[]}),('task',task),('pack',{'retained':'pack'})]:
                (root/(name+'.json')).write_text(json.dumps(value),encoding='utf-8')
            args=SimpleNamespace(knowledge_index=str(root/'index'),knowledge_root=str(root),
                knowledge_policy=str(root/'policy.json'),knowledge_task=str(root/'task.json'),
                knowledge_pack=str(root/'pack.json'),knowledge_worker_python=str(Path(sys.executable).absolute()),
                claude_mon_root='cm',task='timeout contract')
            def verify(pack,doc,project,policy,obligations,worker):
                if worker.timeout<50: raise ValueError('cold-start budget too short for fresh replay')
                self.assertEqual(worker.timeout,120)
            # This test covers preflight's real worker selection/defaulting;
            # graph execution is slow/external and is tested separately.
            with patch.object(workflow.indexing,'load',return_value={}), \
                 patch.object(workflow.retrieval,'verify_pack',side_effect=verify):
                try: result=workflow.preflight(args)
                except ValueError as exc: self.fail(str(exc))
                self.assertEqual(result,{'retained':'pack'})


if __name__=='__main__': unittest.main()
