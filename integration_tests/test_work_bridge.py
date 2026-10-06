"""Focused fresh native boundary reconstruction, not a scheduling experiment."""
import unittest
from tempfile import TemporaryDirectory
from work_bridge_lab.cases import construct,manifests,assess
from work_bridge_lab.reference import validate
from experimental_work_bridge.project import project


class NativeWorkBridgeTests(unittest.TestCase):
    def check_case(self,parent):
        with TemporaryDirectory() as tmp:
            rows,receipt=construct(parent,tmp,native=True)
            self.assertTrue(receipt['runtime_calls']);self.assertTrue(receipt['reconstruction']['authority_equal']);self.assertTrue(receipt['reconstruction']['projection_equal']);self.assertEqual(receipt['executor_effects'],0)
            self.assertEqual(receipt['reconstruction']['native_calls_before'],receipt['reconstruction']['native_calls_after'])
            for call in receipt['runtime_calls']:self.assertEqual(call['mode'],'native');self.assertTrue(call['formula_agreement'])
            for row in rows:
                for variant in row['variants']:
                    m=manifests()[variant];ab,_=assess(row['frame'],m);view,_=project(row['frame'],m,ab['A'],ab['B']);self.assertTrue(view.data()['complete'],view.data()['reason']);validate(row['frame'],m,ab['A'],ab['B'],view)
            return rows,receipt
    def test_native_new_registered_method_result_closes_only_declared_gap(self):
        rows,receipt=self.check_case('method-gap');m=manifests()['primary'];before,_=assess(rows[1]['frame'],m);after,_=assess(rows[2]['frame'],m)
        self.assertEqual((before['B'].status,after['B'].status),('UNKNOWN','PASS'));self.assertEqual(after['A'].status,'UNKNOWN');self.assertEqual(receipt['observed_final']['goal']['projection']['outstanding_loss'],10)
    def test_native_objection_remains_global_after_positive_witnesses(self):
        rows,receipt=self.check_case('objection');m=manifests()['primary'];ab,_=assess(rows[-1]['frame'],m);view,_=project(rows[-1]['frame'],m,ab['A'],ab['B']);v=view.data()
        self.assertEqual((v['A']['status'],v['B']['status']),('FAIL','FAIL'));self.assertEqual(len([x for x in v['global_blockers'] if x['category']=='OBJECTION_REQUIRES_REVIEW']),2)
        self.assertEqual(receipt['timeline'][0]['evidence_before'],receipt['timeline'][0]['evidence_after'])
