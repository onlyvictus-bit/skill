"""Real subprocess refusal/envelope regressions; all state is fixture-only."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from complete_read_v2 import ledger, partition
CLI = ROOT/'scripts/claude_mon_v2.py'


class CliInputContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cm-input-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source.txt'; self.source.write_bytes(b'alpha\nbeta\n')
        self.manifest = self.root/'manifest.json'
        self.manifest.write_text(json.dumps(partition.build_manifest('SRC-1', self.source.read_bytes())))
        self.profile = self.root/'profile.json'
        self.profile.write_text(json.dumps({'schema_version':2,'provider':'test-only','model':'m-1',
            'encoding':'e','encoding_version':'v','context_limit':100000,'output_limit':500,
            'counting_method':'synthetic-word-split','endpoint':'test-only-transport',
            'purpose':'cli-regression','max_spend':0}))
        self.run = self.root/'run'; self.run.mkdir()
        db = ledger.connect(str(self.run/'ledger.db'))
        ledger.create_work_item(db,'W','task-A','SRC-1'); db.close()

    def call(self, *args):
        p = subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],
                           capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(p.stderr, '', p.stderr)
        return p.returncode, json.loads(p.stdout)

    def preflight(self, *extra):
        return self.call('preflight','--run-dir',self.run,'--work-item','W',
            '--manifest-file',self.manifest,'--source-file',self.source,
            '--profile-file',self.profile,'--per-unit-output','10',
            '--expect-task-digest','task-A','--counter-words',*extra)

    def test_preflight_without_unsupported_option_still_passes(self):
        code, result = self.preflight()
        self.assertEqual(code,0,result); self.assertTrue(result['ok'])

    def test_every_supplied_task_spec_is_explicitly_refused(self):
        for value in ('spec-A','DELIBERATELY-WRONG',''):
            with self.subTest(value=value):
                code, result = self.preflight('--task-spec-digest',value)
                self.assertEqual(code,2,result)
                self.assertFalse(result['ok'])
                self.assertIn('E_PREFLIGHT_TASK_SPEC_UNSUPPORTED',result['error'])

    def test_unsupported_option_refuses_before_files_or_ledger_creation(self):
        target = self.root/'must-not-create'
        code,result=self.call('preflight','--run-dir',target,'--work-item','W',
            '--manifest-file',self.root/'absent.json','--source-file',self.root/'absent.txt',
            '--profile-file',self.root/'absent-profile.json','--per-unit-output','10',
            '--task-spec-digest','wrong')
        self.assertEqual(code,2,result)
        self.assertIn('E_PREFLIGHT_TASK_SPEC_UNSUPPORTED',result['error'])
        self.assertFalse(target.exists())

    def test_existing_task_digest_mismatch_remains_domain_refusal(self):
        code,result=self.preflight('--expect-task-digest','wrong')
        self.assertEqual(code,1,result);self.assertFalse(result['ok'])

    def test_missing_source_routes_emit_original_os_cause(self):
        missing=self.root/'absent.txt'
        for command,extra in [('query',['--text','alpha']),('verify',[]),
                              ('open-unit',['--unit-id','U000001']),
                              ('preflight',['--run-dir',self.run,'--work-item','W',
                                  '--profile-file',self.profile,'--per-unit-output','10','--counter-words'])]:
            with self.subTest(command=command):
                code,result=self.call(command,'--manifest-file',self.manifest,'--source-file',missing,*extra)
                self.assertEqual(code,2,result);self.assertFalse(result['ok'])
                self.assertEqual(result['cause']['type'],'FileNotFoundError')
                self.assertEqual(result['cause']['filename'],str(missing))

    def test_export_output_error_is_json(self):
        code,result=self.call('export','--run-dir',self.run,'--out',self.root)
        self.assertEqual(code,2,result);self.assertFalse(result['ok'])
        self.assertIn('Error',result['cause']['type'])

    def test_sqlite_connection_error_is_json(self):
        (self.run/'ledger.db').unlink();(self.run/'ledger.db').mkdir()
        code,result=self.call('status','--run-dir',self.run)
        self.assertEqual(code,2,result)
        self.assertEqual(result['cause']['type'],'OperationalError')

    def test_json_input_failure_is_not_double_emitted(self):
        bad=self.root/'bad.json';bad.write_text('{')
        code,result=self.call('query','--manifest-file',bad,'--source-file',self.source,'--text','alpha')
        self.assertEqual(code,2,result);self.assertIn('E_INPUT_MANIFEST',result['error'])

    def test_prepare_invalid_instruction_encoding_is_json(self):
        bad=self.root/'instructions.txt';bad.write_bytes(b'\xff')
        units=self.root/'units.json';units.write_text('{}')
        schema=self.root/'schema.json';schema.write_text('{}')
        code,result=self.call('prepare','--run-dir',self.run,'--work-item','W',
            '--task-digest','task-A','--task-spec-digest','spec-A','--units-file',units,
            '--instructions-file',bad,'--schema-file',schema,'--profile-file',self.profile,
            '--counter-words')
        self.assertEqual(code,2,result)
        self.assertEqual(result['cause']['type'],'UnicodeDecodeError')

    def test_encoding_cause_chain_and_notes_survive(self):
        spec=importlib.util.spec_from_file_location('cli_contract_fixture',CLI)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        original=OSError(5,'original OS cause','fixture.txt')
        error=UnicodeDecodeError('utf-8',b'\xff',0,1,'invalid fixture')
        error.__cause__=original;error.add_note('retained fixture note')
        with patch.dict(cli.HANDLERS,{'capabilities':lambda _: (_ for _ in ()).throw(error)}), \
                patch.object(cli,'emit',return_value=2) as emit:
            self.assertEqual(cli.main(['capabilities']),2)
        result=emit.call_args.args[0]
        self.assertEqual(result['cause']['type'],'UnicodeDecodeError')
        self.assertEqual(result['cause']['chain'][0]['type'],'OSError')
        self.assertIn('retained fixture note',result['cause']['notes'])

    def test_programming_errors_and_interrupts_are_not_hidden(self):
        spec=importlib.util.spec_from_file_location('cli_programming_fixture',CLI)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        for error in (TypeError('programmer'),KeyError('programmer'),AssertionError('programmer'),SystemExit(7),KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), \
                    patch.dict(cli.HANDLERS,{'capabilities':lambda _, e=error: (_ for _ in ()).throw(e)}):
                with self.assertRaises(type(error)):
                    cli.main(['capabilities'])


if __name__=='__main__':unittest.main()
