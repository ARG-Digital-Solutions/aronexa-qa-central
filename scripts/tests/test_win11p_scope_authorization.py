import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from win11p_contract import validate_scope

class OwnerScopeTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'qa/plans/WIN11P_RECEPTION_E2E.json').read_text())
        self.manifest=json.loads((ROOT/'qa/reviews/QA38_MAVEN_LIFECYCLE_REVIEW.json').read_text())

    def test_owner_authorized_exact_26_paths_without_human_signoff(self):
        self.assertEqual(len(self.plan['authorized_changed_paths']),26)
        self.assertEqual(self.plan['authorized_changed_paths'],self.manifest['proposed_changed_paths'])
        self.assertTrue(self.manifest['owner_scope_authorized'])
        self.assertEqual(self.plan['reviewer']['disposition'],'NOT_REVIEWED')
        self.assertEqual(self.plan['disposition'],'NOT_RUN')
        validate_scope(self.plan,self.manifest['proposed_changed_paths'])

    def test_expansion_does_not_accept_missing_extra_or_duplicate_paths(self):
        paths=self.manifest['proposed_changed_paths']
        for changed in (paths[:-1],paths+['backend/src/main/java/Unapproved.java'],paths+[paths[0]]):
            with self.subTest(changed=changed[-1]):
                with self.assertRaises(ValueError):validate_scope(self.plan,changed)

if __name__=='__main__':unittest.main()
