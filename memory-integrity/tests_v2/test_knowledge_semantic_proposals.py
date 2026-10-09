"""Exact quotation is support identity, never a semantic truth oracle."""
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from knowledge_bridge import contracts as c


class ProposalContract(unittest.TestCase):
    def test_quoted_proposal_contract_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.semantic_proposals'),
                             'source-bound semantic proposals are missing')
    def test_complete_declared_processing_entrypoint_exists(self):
        from knowledge_bridge import semantic_proposals
        self.assertTrue(hasattr(semantic_proposals,'process'), 'per-unit model processing is missing')

    def proposal(self):
        return {'quote': 'Never send data unless approved.', 'text': 'Sending requires approval',
                'polarity': 'negative', 'conditions': ['unless approved'], 'type': 'Requirement'}

    def test_exact_negative_conditional_quote_stays_unreviewed(self):
        from knowledge_bridge.semantic_proposals import validate
        raw = 'café\nNever send data unless approved.\n'.encode()
        proposal = self.proposal()
        result = validate(raw, 'SRC-1', c.digest(raw), [proposal])
        self.assertEqual(result['proposals'][0]['polarity'], 'negative')
        self.assertEqual(result['proposals'][0]['conditions'], ['unless approved'])
        self.assertEqual(result['proposals'][0]['review_status'], 'unreviewed')
        self.assertEqual(result['semantic_truth'], 'UNVERIFIED')
        start, end = result['proposals'][0]['range']
        self.assertEqual(raw[start:end].decode(), proposal['quote'])

    def test_absent_quote_rejected(self):
        from knowledge_bridge.semantic_proposals import validate
        raw = b'Never send data unless approved.'
        p = self.proposal(); p['quote'] = 'Send data without approval.'
        with self.assertRaisesRegex(ValueError, 'E_PROPOSAL_QUOTE'):
            validate(raw, 'SRC-1', c.digest(raw), [p])

    def test_duplicate_quote_requires_explicit_byte_range(self):
        from knowledge_bridge.semantic_proposals import validate
        raw = b'Never send data unless approved. Never send data unless approved.'
        with self.assertRaisesRegex(ValueError, 'E_PROPOSAL_AMBIGUOUS_QUOTE'):
            validate(raw, 'SRC-1', c.digest(raw), [self.proposal()])

    def test_source_change_and_false_review_flags_rejected(self):
        from knowledge_bridge.semantic_proposals import validate
        raw = b'Never send data unless approved.'
        with self.assertRaisesRegex(ValueError, 'E_STALE_SOURCE'):
            validate(raw, 'SRC-1', '0' * 64, [self.proposal()])
        p = dict(self.proposal(), review_status='reviewed')
        with self.assertRaises(ValueError):
            validate(raw, 'SRC-1', c.digest(raw), [p])


if __name__ == '__main__':
    unittest.main()
