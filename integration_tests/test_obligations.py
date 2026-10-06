"""Small actual PeTTa/PLN and AtomSpace boundary checks, no scheduler sweep."""
import unittest
from tempfile import TemporaryDirectory
from experimental_obligations.evaluate import evaluate
from obligations_lab.cases import construct,manifests,setup,report,infer
from obligations_lab.historical import historical
from obligations_lab.reference import frozen,qualified
from experimental_obligations.capture import capture,state_digest


class NativeObligationTests(unittest.TestCase):
    def check_parent(self,parent):
        with TemporaryDirectory() as tmp:
            rows,result=construct(parent,tmp,native=True)
            self.assertTrue(result['runtime_calls']);self.assertTrue(result['reconstruction']['authority_equal']);self.assertTrue(result['reconstruction']['projection_equal'])
            self.assertEqual(result['executor_effects'],0)
            self.assertEqual(result['reconstruction']['native_calls_before'],result['reconstruction']['native_calls_after'])
            for row in rows:
                d=row['capture'].data();self.assertEqual(frozen(d),d['live_criterion_statuses'][0])
                for name in row['manifests']:
                    m=manifests()[name];a=evaluate(row['capture'],m,'A')[0].data();b=evaluate(row['capture'],m)[0].data()
                    self.assertEqual(a['numerical_status'],d['live_criterion_statuses'][0]);self.assertEqual(b['numerical_status'],qualified(d,m)[0])
            return rows,result
    def test_native_weak_deduction_and_direct_report(self):
        rows,_=self.check_parent('weak-augmented');cap=rows[-1]['capture'];self.assertEqual(evaluate(cap,manifests()['alternatives'])[0].status,'PASS');self.assertEqual(evaluate(cap,manifests()['mandatory_method'])[0].status,'UNKNOWN')
    def test_native_revision_parents_remain_current(self):
        rows,_=self.check_parent('revision-family');self.assertEqual(len(rows[-1]['capture'].data()['pairs'][0][0]['current']),3)
    def test_native_new_adverse_deduction_without_external_observation(self):
        rows,result=self.check_parent('adverse-inference');self.assertEqual([evaluate(r['capture'],manifests()['alternatives'])[0].status for r in rows],['PASS','FAIL']);self.assertTrue(result['temporal'][0]['external_observations_unchanged'])
    def test_native_shadow_cannot_satisfy_live_permission(self):
        with TemporaryDirectory() as tmp:
            s=setup(tmp,native=True)
            try:
                report(s);infer(s);before=state_digest(s.service);cap,_=capture(s.service)
                for interpretation in ('A','B'):
                    result,_=evaluate(cap,manifests()['alternatives'],interpretation)
                    with self.assertRaises(ValueError):s.service.reserve_and_record_intent(result,idempotency_key='native-shadow-'+interpretation)
                self.assertEqual(state_digest(s.service),before);self.assertEqual(s.reserve()['status'],'UNKNOWN');self.assertEqual(s.executor.total_effects,0)
            finally:s.close()
    def test_historical_complete_ledger_matches_frozen_inspection(self):
        with TemporaryDirectory() as tmp:
            rows,receipt=historical(tmp);self.assertTrue(receipt['counterfactual_roles']);self.assertEqual(receipt['runtime_calls'],[])
            for row in rows:
                self.assertEqual(frozen(row['capture'].data()),row['capture'].data()['live_criterion_statuses'][0])
                for name in row['manifests']:
                    a=evaluate(row['capture'],manifests()[name],'A')[0].data();b=evaluate(row['capture'],manifests()[name])[0].data()
                    self.assertEqual(a['reason'],'COMPLETE');self.assertEqual(b['reason'],'COMPLETE');self.assertEqual(a['numerical_status'],frozen(row['capture'].data()));self.assertEqual(b['numerical_status'],qualified(row['capture'].data(),manifests()[name])[0])
