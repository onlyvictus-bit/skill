"""Short-name fixtures must exercise a real alias or declare the prerequisite."""
import unittest
from unittest.mock import patch

import test_native_paths as paths


class ShortPathFixtureTests(unittest.TestCase):
    def test_denied_parent_can_use_existing_readable_runtime_alias(self):
        denied = PermissionError('parent listing denied')
        denied.winerror = 5
        with patch.object(paths, 'short_form', side_effect=[denied, 'C:\\PYTHON~1']):
            self.assertEqual(paths.identity_fixture(['C:\\private', 'C:\\Python314']),
                             ('C:\\Python314', 'C:\\PYTHON~1'))

    def test_unchanged_long_name_is_not_short_name_coverage(self):
        with patch.object(paths, 'short_form', return_value='C:\\longname'):
            with self.assertRaisesRegex(unittest.SkipTest, 'no usable 8.3 alias'):
                paths.identity_fixture(['C:\\longname'])

    def test_unexpected_native_error_is_not_skipped(self):
        error = OSError('fixture disappeared')
        error.winerror = 2
        with patch.object(paths, 'short_form', side_effect=error):
            with self.assertRaises(OSError) as caught:
                paths.identity_fixture(['C:\\missing'])
        self.assertIs(caught.exception, error)


if __name__ == '__main__':
    unittest.main()
