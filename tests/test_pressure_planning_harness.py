"""Certified wiring/replay checks on named old hand controls, not measurements."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from validation_lab.planning_comparison import run_closed, common, configurations, load
from validation_lab.planning_audit import check_closed, check_common
from validation_lab.decision_reference import Reference
from validation_lab.decision_tasks import parents, budgets


class HarnessTests(unittest.TestCase):
    def fixture(self):
        task=deepcopy(next(t for t in parents() if t['task_id']=='completion-1'))
        task['task_id']=task['parent_id']='planning-wiring-control'
        return task

    def test_each_arm_actual_execution_and_replay(self):
        task=self.fixture();b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        main,wall=configurations(dict(wall_caps_ns=[1_000_000,5_000_000]))
        selected=main[:2]+[c for c in main if c['mode']=='attempts' and c['limits']['attempts']==4]+wall
        with TemporaryDirectory() as tmp:
            for config in selected:
                with self.subTest(config=config['name']):
                    path=Path(tmp)/config['name'];entry=run_closed(task,b,config,ref,path)
                    self.assertEqual(entry['result']['failures'],{})
                    check_closed(path,task,b,ref)

    def test_common_readonly_and_replay(self):
        task=self.fixture();b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        main,wall=configurations(dict(wall_caps_ns=[1_000_000]))
        selected=main[:2]+[c for c in main if c['mode']=='attempts' and c['limits']['attempts']==4]+wall
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'common';common(task,b,ref,ref.initial(),[],selected,path)
            self.assertGreater(check_common(path,task,b,ref),0)

    def test_changed_search_limits_fail_even_with_same_arm_name(self):
        from validation_lab.planning_comparison import write
        from validation_lab.audit_pressure_comparison import AuditError
        task=self.fixture();b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        main,_=configurations(dict(wall_caps_ns=[]))
        config=next(c for c in main if c['name']=='PLAN-neutral-n4')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'common';common(task,b,ref,ref.initial(),[],[config],path)
            result=load(path/(config['name']+'.json'));result['limits']['attempts']=5
            write(path/(config['name']+'.json'),result)
            with self.assertRaises(AuditError):check_common(path,task,b,ref)


if __name__=='__main__':unittest.main()
