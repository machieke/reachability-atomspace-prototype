"""Pinned native calls, stale-result rejection and projection/readback in new scope."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from goal_pln_lab.cases import configuration
from goal_pln_lab.compare import run_case


class NativeGoalPLNTests(unittest.TestCase):
    def test_selected_native_chain_stale_proposal_and_monitoring(self):
        with TemporaryDirectory() as directory:
            for name in ('path-three','change-producer','supported-reopen'):
                fixture=next(f for f in configuration()['fixtures'] if f['id']==name)
                with self.subTest(case=name):
                    result=run_case(fixture,Path(directory)/name,arm='Goal-index',budget=16,native=True)
                    self.assertEqual(result['conformance'],'PASS',result.get('traceback'))
                    self.assertTrue(result['reconstruction']['projection_equal'])
                    self.assertTrue(result['reconstruction']['authority_equal'])
                    if name!='supported-reopen':
                        self.assertTrue(result['runtime_calls'])
                    self.assertTrue(all(c['formula_agreement'] is True for c in result['runtime_calls']))
