"""Immutable bridge release IDs, version monotonicity, and historical preservation."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class ReleaseIdentity(unittest.TestCase):
    def test_new_bridge_is_not_same_version_replacement(self):
        old=json.loads((ROOT/'release/Knowledge-Bridge-Manifest.json').read_text())
        new=json.loads((ROOT/'release/Knowledge-Bridge-Manifest-v2.json').read_text())
        self.assertNotEqual(old['release'],new['release'])
        self.assertNotEqual(old['bridge_version'],new['bridge_version'])
        self.assertEqual(old['release'],'knowledge-bridge-v1')
        self.assertEqual(new['release'],'knowledge-bridge-v2')
        self.assertEqual(set(old['packages']),set(new['packages']))
        for name in old['packages']:
            previous=old['packages'][name]
            current=new['packages'][name]
            self.assertNotEqual(previous['zip'],current['zip'])
            for row in (previous,current):
                payload=(ROOT/'release'/row['zip']).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(),row['sha256'])
                self.assertEqual(len(payload),row['bytes'])

if __name__=='__main__':
    unittest.main()
