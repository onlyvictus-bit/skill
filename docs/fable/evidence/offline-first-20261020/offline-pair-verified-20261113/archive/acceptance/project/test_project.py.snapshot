import unittest
from client import run
from storage import reopen, source_digest


class CodingTask(unittest.TestCase):
    def test_current_source(self):
        self.assertEqual(run('தமிழ் café', 1000, 1300), 'தமிழ் café')

    def test_expired_source(self):
        with self.assertRaisesRegex(ValueError, 'STALE_INPUT'):
            run('old', 1000, 1301)

    def test_revoked_access(self):
        with self.assertRaisesRegex(ValueError, 'ACCESS_REVOKED'):
            run('current', 1000, 1100, revoked=True)

    def test_checkpoint_reopening(self):
        saved = {'source_digest':source_digest('தமிழ்\n'), 'completed':['step1']}
        self.assertEqual(reopen(saved, 'தமிழ்\n'), ['step1'])
        with self.assertRaisesRegex(ValueError, 'CHECKPOINT_SOURCE_CHANGED'):
            reopen(saved, 'changed')
