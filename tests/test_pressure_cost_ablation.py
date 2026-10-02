"""Exploratory policy isolation, numerical ratios and unchanged hard gates."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability import pressure_controller as controller
from reachability.model import Clause, Status
from reachability.pressure import PressureLimits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work, holds, operation_cost
from reachability.service import AdmissionDenied
from reachability.trace_protocol import fingerprint
from validation_lab import audit_pressure_comparison as audit
from validation_lab.pressure_cost_ablation import (
    POLICIES, ORIGINAL_RANK, diagnostic_cases, experiment, matrix, rank_cost, ranking_policy, sources)
from validation_lab.pressure_episodes import episodes
from validation_lab.run_pressure_comparison import configurations, run_one


class PressureCostAblationTests(unittest.TestCase):
    def test_frozen_sources_and_predeclared_matrix(self):
        self.assertEqual(len(sources()['frozen_files']),71)
        cells=list(matrix(experiment()))
        self.assertEqual(len(cells)*len(POLICIES),200)
        self.assertEqual(sum(group=='frozen' for group,_,_ in cells)*len(POLICIES),80)
        self.assertEqual(len(diagnostic_cases()),24)

    def test_original_policy_exactly_reproduces_frozen_ranks_fields_and_restores_bindings(self):
        with TemporaryDirectory() as d, ReasoningSession(episodes()[0]['public'],d) as session:
            session.observe(1,'seed'); snapshot=session.read()
            candidates=enumerate_work(session.public,snapshot).candidates
            original=ORIGINAL_RANK(session.public,snapshot,candidates,PressureLimits())
            for policy in POLICIES:
                if policy=='B0': continue
                with self.subTest(policy=policy):
                    with self.assertRaisesRegex(RuntimeError,'restore'):
                        with ranking_policy(policy) as calls:
                            result=controller.rank_b3(session.public,snapshot,candidates,PressureLimits())
                            self.assertEqual(calls['ranking_calls'],1)
                            if policy=='B3-cost-both': self.assertEqual(result[:2],original[:2])
                            else: self.assertEqual(result[1]['binding']['cost_placement'],policy)
                            raise RuntimeError('restore')
                    self.assertIs(controller.rank_b3,ORIGINAL_RANK)
                    self.assertIs(audit.rank_b3,ORIGINAL_RANK)

    def test_parallel_cost_ratios_match_independent_formula(self):
        for case in diagnostic_cases():
            if case['diagnostic']['family']!='parallel-route-cost': continue
            with TemporaryDirectory() as d, ReasoningSession(case['public'],d) as session:
                session.observe(1,'seed'); snapshot=session.read()
                candidates=enumerate_work(session.public,snapshot).candidates
                by_rule={dict(c.arguments)['rule_id']:c for c in candidates}
                for policy,flags in POLICIES.items():
                    if flags is None: continue
                    with self.subTest(cost=case['diagnostic']['cost'],policy=policy):
                        ranks,field,_,_=rank_cost(session.public,snapshot,candidates,PressureLimits(),policy)
                        actual=ranks[by_rule['cheap'].candidate_id][0]/ranks[by_rule['costly'].candidate_id][0]
                        # Equal graph depth and common target: each enabled
                        # placement contributes exactly one inverse-cost factor.
                        expected=case['diagnostic']['cost']**sum(flags)
                        self.assertAlmostEqual(actual,expected,places=10)
                        self.assertTrue(field['converged'])

    def test_equivalent_depth_cases_preserve_truth_frontier_and_have_expected_attenuation(self):
        base=None
        for case in diagnostic_cases():
            if case['diagnostic']['family']!='equivalent-condition-depth' or case['diagnostic']['cost']!=1: continue
            condition=case['public']['goals'][0]['condition']
            for bits in product((False,True),repeat=3):
                facts={i+1 for i,value in enumerate(bits) if value}
                self.assertEqual(holds(condition,facts),2 in facts)
            with TemporaryDirectory() as d, ReasoningSession(case['public'],d) as session:
                session.observe(1,'seed'); snapshot=session.read()
                candidates=enumerate_work(session.public,snapshot).candidates
                wires=[c.wire() for c in candidates]
                if base is None: base=wires
                self.assertEqual(wires,base)
                ranks,field,_,_=rank_cost(session.public,snapshot,candidates,PressureLimits(),'B3-cost-neither')
                self.assertAlmostEqual(field['scores']['rule:high']['value'],3*.85**(case['diagnostic']['depth']+2))

    def test_each_policy_preserves_authority_and_rejects_invalid_or_stale_work(self):
        for policy in POLICIES:
            if policy=='B0': continue
            with self.subTest(policy=policy), TemporaryDirectory() as d, ReasoningSession(episodes()[0]['public'],d) as session:
                session.observe(1,'seed'); snapshot=session.read()
                candidates=enumerate_work(session.public,snapshot).candidates
                before=deepcopy({k:getattr(session.service,k) for k in session.service._STATE_FIELDS})
                journal=session.service._journal.entries()
                rank_cost(session.public,snapshot,candidates,PressureLimits(),policy)
                self.assertEqual(before,{k:getattr(session.service,k) for k in session.service._STATE_FIELDS})
                self.assertEqual(journal,session.service._journal.entries())
                selected=next(c for c in candidates if dict(c.arguments).get('rule_id')=='shared')
                transition=session.call('propose_transition',session.context_id,'shared',(session.aliases['seed'],))
                pre=session.call('precertify',transition,session.service.snapshot(session.context_id).knowledge_revision)
                session.call('revoke_evidence','seed')
                self.assertEqual(session.execute(selected,fingerprint(snapshot))['status'],'STALE')
                with self.assertRaises(AdmissionDenied) as caught: session.service.infer(transition,pre)
                self.assertIs(caught.exception.status,Status.STALE)
                # No fresh missing-premise candidate appears under any weighting.
                self.assertFalse(any(c.kind=='derive' for c in enumerate_work(session.public,session.read()).candidates))
                session.observe(1,'new-seed')
                state=session.service.snapshot(session.context_id)
                session.call('replace_policy',session.context_id,'forbid-shared',(Clause((session.literal(-2),)),),state.knowledge_revision)
                fresh=session.read()
                self.assertEqual(session.execute(selected,fingerprint(fresh))['status'],'FAIL')

    def test_certified_runs_replay_under_declared_policy_and_affordability_is_unchanged(self):
        case=next(c for c in diagnostic_cases() if c['case_id']=='depth-2-cost-8')
        config=deepcopy(configurations()[0]); config['budget']['operation_work']=0
        for policy in POLICIES:
            with self.subTest(policy=policy),TemporaryDirectory() as d:
                path=Path(d)/'run'
                with ranking_policy(policy):
                    result=run_one(case,'B0' if policy=='B0' else 'B3',config,path)
                    self.assertEqual(result['stop_reason'],'WORK_BUDGET')
                    self.assertEqual(result['work']['actions'],0)
                    self.assertEqual(result['final']['external_weighted_loss'],4)
                    self.assertEqual(audit.audit_run(path,case,config,result),0)
        config=configurations()[0]
        for policy in POLICIES:
            with self.subTest(policy=policy),TemporaryDirectory() as d:
                path=Path(d)/'run'
                with ranking_policy(policy):
                    result=run_one(case,'B0' if policy=='B0' else 'B3',config,path)
                    self.assertEqual(result['final']['certified_weighted_loss'],0)
                    self.assertEqual(result['work']['operation_work'],11)
                    self.assertEqual(audit.audit_run(path,case,config,result),4)


if __name__=='__main__': unittest.main()
