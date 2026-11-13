"""Record actual unittest identities/outcomes while reusing the retained runner."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


def allowed_skips():
    result = {'test_knowledge_languages.LanguageContract.'+name: 'isolated parser runtime required'
              for name in ('test_typescript_exports_imports_calls_and_exact_utf8_ranges',
                           'test_malformed_syntax_is_failed_not_partial_success',
                           'test_dynamic_calls_have_no_invented_target',
                           'test_parsed_symbols_enter_source_bound_project_projection')}
    for name in ('test_real_learned_embeddings_have_paraphrase_support_and_measured_tokens',
                 'test_real_embedding_refuses_truncation',
                 'test_real_generation_is_deterministic_and_receipts_account_for_raw_tokens',
                 'test_real_reranking_scores_every_candidate_with_bound_model',
                 'test_real_generation_refuses_truncation'):
        result['test_knowledge_model_runtime.RealLocalModels.'+name] = 'explicit local model manifest and interpreter not selected'
    result['test_knowledge_model_benchmark.RealModelBenchmark.test_one_actual_case_keeps_equal_oracles_and_complete_raw_receipts'] = 'explicit actual model and worker runtimes not selected'
    if os.name == 'nt':
        result.update({
            'test_knowledge_model_benchmark.ModelBenchmarkContracts.test_direct_model_budget_interrupts_overdue_work': 'POSIX-only',
            'test_knowledge_completion.RemainingPublicContract.test_timeout_terminates_worker_descendants': 'POSIX process-group observation required',
            'test_knowledge_distributed.DistributedRetrieval.test_suspended_worker_expires_shared_deadline_and_is_reaped': 'POSIX pinned runtime required'})
    return result


def cases(group):
    for item in group:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


class RecordingResult(unittest.TextTestResult):
    records = None

    def startTest(self, test):
        self.records['started'].append(test.id())
        self.current = {'id': test.id(), 'outcome': 'INCOMPLETE', 'reason': ''}
        super().startTest(test)

    def addSuccess(self, test):
        self.current['outcome'] = 'PASS'
        super().addSuccess(test)

    def addSkip(self, test, reason):
        self.current.update(outcome='SKIP', reason=reason)
        super().addSkip(test, reason)

    def addError(self, test, error):
        self.current.update(outcome='ERROR', reason=str(error[1]))
        super().addError(test, error)

    def addFailure(self, test, error):
        self.current.update(outcome='FAIL', reason=str(error[1]))
        super().addFailure(test, error)

    def addExpectedFailure(self, test, error):
        self.current.update(outcome='EXPECTED_FAILURE', reason=str(error[1]))
        super().addExpectedFailure(test, error)

    def addUnexpectedSuccess(self, test):
        self.current.update(outcome='UNEXPECTED_SUCCESS')
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, error):
        if error is not None:
            self.current.update(outcome='FAIL', reason=str(error[1]))
        super().addSubTest(test, subtest, error)

    def stopTest(self, test):
        self.records['finished'].append(dict(self.current))
        super().stopTest(test)


def main():
    if '--discover' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--discover', action='store_true')
        parser.add_argument('--package-root', type=Path, required=True)
        parser.add_argument('--pattern', required=True)
        args = parser.parse_args()
        package = args.package_root.resolve(strict=True)
        sys.path[:0] = [str(package), str(package/'tests_v2')]
        suite = unittest.TestLoader().discover(str(package/'tests_v2'), pattern=args.pattern)
        ids = [case.id() for case in cases(suite)]
        if not ids or any('_FailedTest' in ident for ident in ids):
            raise ValueError('E_G1_DISCOVERY')
        print(json.dumps(ids))
        return 0
    package = Path(sys.argv[sys.argv.index('--package-root')+1]).resolve(strict=True)
    output = Path(sys.argv[sys.argv.index('--output-dir')+1]).absolute()
    sys.path.insert(0, str(package.parent/'.github/scripts'))
    import retained_unittest
    records = {'started': [], 'finished': []}
    discovered = []
    RecordingResult.records = records
    original_discover = unittest.TestLoader.discover
    def observe_discovery(loader, *args, **kwargs):
        suite = original_discover(loader, *args, **kwargs)
        discovered.extend(case.id() for case in cases(suite))
        return suite
    unittest.TestLoader.discover = observe_discovery
    unittest.TextTestRunner.resultclass = RecordingResult
    code = retained_unittest.main()
    with (output/'Case-Outcomes.json').open('x', encoding='utf-8') as stream:
        json.dump({'expected_ids': discovered, 'outcomes': records}, stream, sort_keys=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
