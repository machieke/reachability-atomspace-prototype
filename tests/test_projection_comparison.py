"""Experimental policy wiring, certified replay and report corruption checks."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability import pressure_controller as controller
from reachability.pressure import PressureLimits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work
from validation_lab import audit_pressure_comparison as audit
from validation_lab.pressure_cost_ablation import ORIGINAL_RANK
from validation_lab.projection_cases import mixed_case
from validation_lab.projection_comparison import (POLICIES, experiment, matrix, ranking_policy,
    name, sources, semantic_checks, evaluated_fields, trace, primary_ties, compare_fields)
from validation_lab.run_pressure_comparison import configurations, run_one


class ProjectionComparisonTests(unittest.TestCase):
    def test_fixed_matrix_and_frozen_files(self):
        config = experiment()
        self.assertEqual(len(config['diagnostic_cases']),55)
        self.assertEqual(len(list(matrix(config)))*len(POLICIES),639)
        self.assertEqual(len(sources()['frozen_files']),71)
        self.assertEqual(len(set(c['case_id'] for c in config['diagnostic_cases'])),55)

    def test_named_paths_keep_frozen_b3_exact_and_charge_normalization(self):
        case = mixed_case('and-or',11)
        with TemporaryDirectory() as directory, ReasoningSession(case['public'],directory) as session:
            session.observe(1,'seed'); snapshot=session.read()
            candidates=enumerate_work(session.public,snapshot).candidates
            original=ORIGINAL_RANK(session.public,snapshot,candidates,PressureLimits())
            for policy in POLICIES[1:]:
                with self.subTest(policy=policy):
                    with self.assertRaisesRegex(RuntimeError,'restore'):
                        with ranking_policy(policy) as recorded:
                            ranks,field,construction,iteration=controller.rank_b3(session.public,snapshot,candidates,PressureLimits())
                            m=recorded['metrics']
                            self.assertEqual(m['ranking_calls'],1)
                            self.assertEqual(m['normalization_ns']+m['graph_ns'],construction)
                            self.assertEqual(recorded['evaluations'][0]['iteration_ns'],iteration)
                            if policy=='B3-cost-both': self.assertEqual((ranks,field),original[:2])
                            if policy.startswith('B3-normalized-'):
                                self.assertGreater(m['normalization_ns'],0)
                                self.assertIn('projection',field['binding'])
                            else: self.assertEqual(m['normalization_ns'],0)
                            raise RuntimeError('restore')
                    self.assertIs(controller.rank_b3,ORIGINAL_RANK)
                    self.assertIs(audit.rank_b3,ORIGINAL_RANK)

    def test_certified_closed_loop_equivalence_and_replay_all_placements(self):
        cases=[mixed_case('and-or',seed) for seed in (None,11)]
        config=configurations()[0]
        with TemporaryDirectory() as directory:
            root=Path(directory); results=[]
            for case in cases:
                for policy in POLICIES:
                    key=name(case,config,policy)
                    with ranking_policy(policy) as measured:
                        result=run_one(case,'B0' if policy=='B0' else 'B3',config,root/key)
                    entry=dict(name=key,group='diagnostic',policy=policy,result=result,**measured)
                    with ranking_policy(policy):
                        self.assertEqual(audit.audit_run(root/key,case,config,result),result['work']['actions'])
                    self.assertEqual(result['final']['external_weighted_loss'],0)
                    self.assertEqual(measured['metrics']['normalization_ns']+measured['metrics']['graph_ns'],
                                     result['costs_ns']['pressure_construction_ns'])
                    self.assertEqual(measured['metrics']['ranking_calls'],len(evaluated_fields(trace(root,entry))))
                    results.append(entry)
            checks=semantic_checks(root,results,dict(diagnostic_cases=cases))
            for check in checks:
                if check['policy'].startswith('B3-normalized-'):
                    for field in ('complete_trajectory','candidates_equal','rankings_equal','source_accounting_equal',
                                  'pressure_equal','choices_equal','outcomes_equal'):
                        self.assertTrue(check[field],field)
            self.assertTrue(any(not c['pressure_equal'] for c in checks if not c['policy'].startswith('B3-normalized-')))

    def test_ties_and_changed_field_are_explicit(self):
        row=dict(ranks={'a':[-1.,1], 'b':[-1.-1e-13,1], 'c':[-2.,1]},pressure={'error_bound_l1':0.})
        self.assertEqual(len(primary_ties(row)),1)
        self.assertEqual(set(primary_ties(row)[0]['candidates']),{'a','b'})
        field=dict(sources={'s':dict(observed_relief_events=[])},error_bound_l1=0.,fields={'s':dict(values={'rule:a':1.})})
        changed=deepcopy(field); changed['fields']['s']['values']['rule:a']=2.
        self.assertFalse(compare_fields(field,changed,all_nodes=True)['pressure_equal'])
        changed=deepcopy(field); changed['sources']['s']['outstanding_loss']=3
        self.assertFalse(compare_fields(field,changed,all_nodes=True)['source_accounting_equal'])

    def test_zero_budget_never_issues_normalized_operation(self):
        case=mixed_case('or-and',29); config=deepcopy(configurations()[0]); config['budget']['operation_work']=0
        for policy in POLICIES:
            with TemporaryDirectory() as directory,ranking_policy(policy):
                result=run_one(case,'B0' if policy=='B0' else 'B3',config,Path(directory)/'run')
                self.assertEqual(result['stop_reason'],'WORK_BUDGET')
                self.assertEqual(result['selected'],[])
                self.assertEqual(audit.audit_run(Path(directory)/'run',case,config,result),0)


if __name__=='__main__': unittest.main()
