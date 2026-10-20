"""N3 harness transport contracts, independent of a private runtime or model."""
import copy
from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/n3_child_transport.py'
transport = None
if SOURCE.exists():
    spec = importlib.util.spec_from_file_location('n3_child_transport', SOURCE)
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)


class ChildTransport(unittest.TestCase):
    def api(self, name):
        self.assertIsNotNone(transport, 'Missing N3 context/command correction')
        return getattr(transport, name)

    def base(self):
        return {'PATH': 'controlled-path', 'TEMP': 'controlled-temp', 'TMP': 'controlled-temp',
                'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
                'PYTHONNOUSERSITE': '1', 'GIT_TERMINAL_PROMPT': '0'}

    def command(self, code=0, stdout=b'{"ok":true}', stderr=b''):
        return {'label': 'freshness-literal-discovery', 'started': True, 'exit_code': code,
                'error': None, 'pid': 71, 'artifacts': {name: {'path': '/retained/' + name,
                'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)} for name, raw in
                (('stdout.log', stdout), ('stderr.log', stderr))}}

    def test_only_existing_matching_profile_is_added_not_secrets_or_git_overrides(self):
        build = self.api('evaluation_environment')
        original = self.base(); inherited = {'USERPROFILE': r'C:\Users\owner',
            'NVIDIA_API_KEY': 'test-value', 'PYTHONPATH': 'untrusted', 'HOME': 'other-home',
            'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_VALUE_0': '*'}
        result = build(original, inherited, r'C:\Users\owner')
        self.assertEqual(result, {**original, 'USERPROFILE': r'C:\Users\owner'})
        self.assertEqual(original, self.base(), 'Do not mutate the installer environment')

    def test_missing_or_wrong_profile_refuses(self):
        build = self.api('evaluation_environment')
        for inherited in ({}, {'USERPROFILE': ''}, {'USERPROFILE': r'C:\Users\other'}):
            with self.subTest(inherited=inherited), self.assertRaises(ValueError):
                build(self.base(), inherited, r'C:\Users\owner')

    def test_noncanonical_profile_and_unc_refuse(self):
        build = self.api('evaluation_environment')
        for profile in (r'C:owner', r'C:\Users\other\..\owner', r'\\server\share\owner',
                        r'C:\Users\owner:stream', 'relative', 'C:/Users/owner\x00'):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                build(self.base(), {'USERPROFILE': profile}, profile)

    def test_windows_profile_case_does_not_require_a_fabricated_value(self):
        build = self.api('evaluation_environment')
        result = build(self.base(), {'USERPROFILE': r'c:\users\OWNER'}, r'C:\Users\owner')
        self.assertEqual(result['USERPROFILE'], r'c:\users\OWNER')

    def test_injected_base_config_and_disabled_offline_controls_refuse(self):
        build = self.api('evaluation_environment')
        for key, value in (('GIT_CONFIG_GLOBAL', 'elsewhere'), ('HOME', 'elsewhere'),
                           ('UNRELATED_SECRET', 'test-value'), ('HF_HUB_OFFLINE', '0'),
                           ('PYTHONNOUSERSITE', '0'), ('GIT_TERMINAL_PROMPT', '1')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                build({**self.base(), key: value}, {'USERPROFILE': r'C:\Users\owner'}, r'C:\Users\owner')

    def test_valid_json_success_is_returned(self):
        decode = self.api('decode_command_output'); stdout = b'{"ok":true}'
        self.assertEqual(decode(self.command(stdout=stdout), stdout, b''), (0, {'ok': True}))

    def test_valid_nonzero_structured_refusal_is_not_transport_success(self):
        decode = self.api('decode_command_output')
        stdout = b'{"ok":false,"blockers":["E_QUERY_NO_LEXICAL_SUPPORT"]}'
        code, output = decode(self.command(2, stdout), stdout, b'')
        self.assertEqual(code, 2); self.assertFalse(output['ok'])
        self.assertEqual(output['blockers'], ['E_QUERY_NO_LEXICAL_SUPPORT'])

    def test_nonzero_empty_output_exposes_exit_and_stream_facts_not_json_exception(self):
        decode = self.api('decode_command_output'); stderr = b'controlled ownership refusal'
        try:
            decode(self.command(1, b'', stderr), b'', stderr)
        except ValueError as exc:
            self.assertEqual(exc.code, 'E_N3_CHILD_PROCESS_FAILED')
            self.assertEqual(exc.details['exit_code'], 1)
            self.assertEqual(exc.details['stdout']['bytes'], 0)
            self.assertEqual(exc.details['stderr']['sha256'], sha256(stderr).hexdigest())
            self.assertNotIn('controlled ownership refusal', str(exc), 'Raw stderr is retained, not auto-disclosed')
        else: self.fail('Nonzero empty stdout must not be accepted')

    def test_nonzero_malformed_output_remains_original_process_failure(self):
        decode = self.api('decode_command_output'); stdout = b'not json'
        with self.assertRaisesRegex(ValueError, 'E_N3_CHILD_PROCESS_FAILED'):
            decode(self.command(1, stdout), stdout, b'')

    def test_timeout_or_start_failure_cannot_be_relabelled_as_empty_json(self):
        decode = self.api('decode_command_output')
        for values in ({'started': False, 'error': 'OSError', 'exit_code': None},
                       {'started': True, 'error': 'E_N3_COMMAND_TIMEOUT_NO_RESEND', 'exit_code': None}):
            result = self.command(stdout=b''); result.update(values)
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, 'E_N3_CHILD_TRANSPORT_FAILED'):
                decode(result, b'', b'')

    def test_success_without_output_is_a_protocol_failure(self):
        decode = self.api('decode_command_output')
        with self.assertRaisesRegex(ValueError, 'E_N3_CHILD_STDOUT_MISSING'):
            decode(self.command(stdout=b''), b'', b'')

    def test_bad_json_utf8_nonfinite_and_nonobject_output_refuse(self):
        decode = self.api('decode_command_output')
        for raw in (b'not json', b'\xff', b'{"score":NaN}', b'[]', b'null'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(self.command(stdout=raw), raw, b'')

    def test_stream_bytes_cannot_be_substituted_after_result(self):
        decode = self.api('decode_command_output'); result = self.command()
        for stdout, stderr in ((b'{"ok":false}', b''), (b'{"ok":true}', b'changed')):
            with self.subTest(stderr=stderr), self.assertRaisesRegex(ValueError, 'E_N3_CHILD_STREAM_BINDING'):
                decode(result, stdout, stderr)

    def test_malformed_exit_or_stream_record_does_not_gain_acceptance(self):
        decode = self.api('decode_command_output')
        for key, value in (('exit_code', True), ('exit_code', '0'), ('started', 1), ('artifacts', {})):
            result = copy.deepcopy(self.command()); result[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decode(result, b'{"ok":true}', b'')


if __name__ == '__main__':
    unittest.main()
