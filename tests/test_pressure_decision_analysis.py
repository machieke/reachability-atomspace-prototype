from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from validation_lab.analyze_pressure_decisions import decisions, decompose
from validation_lab.audit_pressure_comparison import AuditError, audit_run
from validation_lab.pressure_episodes import episodes
from validation_lab.run_pressure_comparison import configurations, run_one


class DecisionAnalysisTests(unittest.TestCase):
    def rich_outcomes(self):
        # Hand-specified goal timing, independent of the pressure implementation.
        first=[]; second=[]
        for tick in range(17):
            a=3 if tick<10 else 0; b=3 if tick<12 else 0
            side_a=int(tick<12); side_b=int(tick not in (2,3) and tick<8)
            for rows,answer,side in ((first,a,side_a),(second,b,side_b)):
                rows.append(dict(time=tick,external_weighted_loss=float(2*answer+side),
                    certified_weighted_loss=7.,goals=[dict(goal_id='answer',external_loss=answer),dict(goal_id='side',external_loss=side)]))
        return (dict(outcomes=first,integrated_external_loss=72.),
                dict(outcomes=second,integrated_external_loss=78.))

    def test_full_sequence_decomposes_late_answer_cost_and_early_side_benefit(self):
        first,second=self.rich_outcomes()
        result=decompose(episodes()[0],first,second)
        self.assertEqual(result['by_goal'],dict(answer=12.,side=-6.))
        self.assertEqual(result['B3_minus_B0'],6.)
        self.assertEqual([(r['time'],r['total_delta']) for r in result['ticks'] if r['total_delta']],
                         [(2,-1.),(3,-1.),(8,-1.),(9,-1.),(10,5.),(11,5.)])
        self.assertEqual(len(result['ticks']),16)

    def test_decomposition_rejects_misaligned_time_or_unexplained_loss(self):
        first,second=self.rich_outcomes(); changed=deepcopy(second)
        changed['outcomes'][0]['time']=1
        with self.assertRaisesRegex(AuditError,'outcome times'): decompose(episodes()[0],first,changed)
        changed=deepcopy(second); changed['integrated_external_loss']=77.
        with self.assertRaisesRegex(AuditError,'integrated loss'): decompose(episodes()[0],first,changed)

    def test_same_snapshot_analysis_uses_real_shared_frontier_and_preserves_receipts(self):
        case=episodes()[1]; config=configurations()[1]
        with TemporaryDirectory() as d:
            for variant in ('B0','B3'):
                path=Path(d)/variant; result=run_one(case,variant,config,path)
                self.assertEqual(audit_run(path,case,config,result),2)
                rows=decisions(path,case['public'],result)
                self.assertEqual([r['selected'] for r in rows],['derive:answer','monitor:answer'])
                for row in rows:
                    self.assertEqual(row['receipt']['status'],'PASS')
                    self.assertEqual(set(row['same_snapshot_choices'].values()),{row['selected']})
                    self.assertEqual(len(row['scores']),1)


if __name__=='__main__': unittest.main()
