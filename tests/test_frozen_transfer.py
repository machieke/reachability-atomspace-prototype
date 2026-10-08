"""Static fixture/evaluator checks; never run a new controller parent."""
import copy,json,subprocess,unittest
from pathlib import Path
from transfer_lab.cases import fixtures,configuration
from transfer_lab.reference import validate_cohort,finite,witness
from transfer_lab.build_fixtures import build
from multihop_lab.cases import fixtures as old
from transfer_lab.parity import normal,divergence
from transfer_lab.config import cells,ARMS
class FrozenTransfer(unittest.TestCase):
    def test_declared_cohort_matches_deterministic_construction(self):self.assertEqual(fixtures(),build())
    def test_twelve_new_nonrenamed_structures_and_finite_checks(self):
        result=validate_cohort(fixtures(),old());self.assertEqual(result,json.loads(Path('reviews/frozen-transfer-v1/CONSTRUCTION.json').read_text()))
    def test_seeded_intermediate_is_rejected(self):
        f=copy.deepcopy(fixtures()['parents'][0]);from multihop_lab.reference import rule_shape
        f['sources'][0]['literal']=rule_shape(f['rules'][0])[0]
        with self.assertRaisesRegex(AssertionError,'seeded'):finite(f)
    def test_changed_joint_mass_rejected(self):
        f=copy.deepcopy(fixtures()['parents'][0]);f['joint_witness']['cells'][0]['mass']='1'
        with self.assertRaises(AssertionError):witness(f)
    def test_renamed_parent_not_independent(self):
        f=fixtures();f['parents'][1]['rules']=copy.deepcopy(f['parents'][0]['rules'])
        with self.assertRaisesRegex(AssertionError,'sibling'):validate_cohort(f,old())
    def test_values_budgets_premises_not_normalized_away(self):
        for key in ('belief_revision_id','premise_ids','strength','confidence','work','acquisitions','rule_id','status'):
            self.assertIsNotNone(divergence(normal({key:'one'}),normal({key:'two'})))
    def test_counterbalanced_twenty_four_native_only(self):
        rows=list(cells());self.assertEqual(len(rows),24);self.assertEqual({r[2] for r in rows},{'native'})
        for i in range(12):self.assertEqual([r[1] for r in rows[2*i:2*i+2]],list(ARMS if i%2==0 else reversed(ARMS)))
    def test_runtime_and_prior_publications_unchanged(self):
        baseline=json.loads(Path('reviews/frozen-transfer-v1/BASELINE.json').read_text())
        from hashlib import sha256
        for name,v in baseline['files'].items():self.assertEqual(sha256(Path(name).read_bytes()).hexdigest(),v['sha256'],name)

    def test_input_adapter_preserves_primitive_roles_without_controller(self):
        from tempfile import TemporaryDirectory
        from transfer_lab.cases import setup,initialize
        from experimental_native_recall.schema import Projection
        from experimental_online_pln.agenda import wire
        for f in fixtures()['parents']:
            with TemporaryDirectory() as tmp:
                s=setup(tmp)
                try:
                    initialize(s,f['id']);snap=s.read();p=Projection(snap)
                    self.assertLessEqual(p.export_bytes,2097152);self.assertEqual(s.runtime.calls,[])
                    actual={r.evidence.evidence_id for r in snap.reports}
                    self.assertEqual(actual,{x['id'] for x in f['sources'] if x['delivery']=='initial'})
                    self.assertTrue(all(b.transition.kind=='observation' for q in snap.numerical for b in q.historical))
                    self.assertEqual(len(s.probes),sum(x['delivery']=='opportunity' for x in f['sources']))
                finally:s.close()
