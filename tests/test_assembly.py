"""Independent mechanical accounting and identical public-stream selection."""
from dataclasses import replace
from itertools import permutations
from pathlib import Path
import ast,unittest
from experimental_assembly.service import offers,first_affordable
from experimental_attention.workspace import Caps


class AssemblyServiceTests(unittest.TestCase):
    def jobs(self):return [dict(id=str(i),kind='join',order=i,target='rule'+str(i),anchor='a'+str(i)) for i in range(3)]
    def test_conservative_bounds_include_missing_producer_and_preparation(self):
        jobs=self.jobs();caps=Caps(active=48)
        rows=offers(jobs,{'rule1'},set(),caps,12,128)
        self.assertEqual([r['total'] for r in rows],[13,12,13]);self.assertEqual(first_affordable(rows)['job_id'],'1')
        self.assertIsNone(first_affordable(offers(jobs,set(),set(),caps,12,128)))
        self.assertEqual(first_affordable(offers(jobs,set(),set(),caps,13,128))['job_id'],'0')
        self.assertTrue(all(r['prepare_queries']==6 for r in rows))
    def test_identical_streams_use_FIFO_not_orderer_activation_or_success_labels(self):
        jobs=self.jobs();caps=Caps(active=48)
        for permutation in permutations(jobs):
            for mode in ('WS-queue','WS-local','WS-flow'):
                values=[dict(j,activation=0 if j['order']==0 else 1,expected_success=j['order']!=0,orderer=mode) for j in permutation]
                self.assertEqual(first_affordable(offers(values,set(),set(),caps,16,128))['job_id'],'0')
        self.assertEqual(jobs,self.jobs())
    def test_mechanical_capacity_failures_are_not_semantic_absence(self):
        caps=Caps(active=48)
        cases=((replace(caps,active=6),'BUNDLE_CAPACITY'),(replace(caps,joint_records=4),'JOINT_CAPACITY'),
               (replace(caps,response_records=0),'RESPONSE_CAPACITY'),(replace(caps,candidates=0),'CANDIDATE_CAPACITY'))
        for c,reason in cases:
            r=offers(self.jobs(),set(),set(),c,48,128)[0];self.assertFalse(r['affordable']);self.assertEqual(r['reason'],reason)
            self.assertEqual(r['response_and_tuple_sizes'],'UNKNOWN_UNTIL_NATIVE_RESPONSES')
        self.assertEqual(offers(self.jobs(),set(),set(),caps,48,0)[0]['reason'],'TUPLE_BUDGET')
    def test_inspection_jobs_are_never_assembly_opportunities(self):
        jobs=[dict(j,kind='current') for j in self.jobs()]
        self.assertEqual(offers(jobs,set(),set(),Caps(),48,128),[])
    def test_finite_exhaustive_no_overspend_for_selected_opportunities(self):
        for credit in range(49):
            for mask in range(8):
                resident={'rule'+str(i) for i in range(3) if mask&(1<<i)}
                r=first_affordable(offers(self.jobs(),resident,set(),Caps(active=48),credit,128))
                if r:
                    self.assertLessEqual(r['join_queries']+6,credit)
                    self.assertEqual(r['join_queries'],6+int(r['producer'] not in resident))
    def test_runtime_has_no_evaluator_or_hidden_fixture_imports(self):
        for p in Path('experimental_assembly').glob('*.py'):
            for n in ast.walk(ast.parse(p.read_text())):
                names=[n.module or ''] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names] if isinstance(n,ast.Import) else []
                self.assertFalse(any(m.startswith(('assembly_lab','attention_lab','goal_pln_lab','validation_lab')) for m in names))
