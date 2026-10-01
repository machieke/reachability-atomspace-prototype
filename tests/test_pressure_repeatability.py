"""Fresh controller runs, semantic divergence and honest wall-cap reporting."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from validation_lab.audit_pressure_comparison import AuditError, run_name
from validation_lab.repeat_pressure_comparison import (
    authority_ids, compare_bundles, compare_run, differences, main,
    semantic_result, semantic_trace)


class PressureRepeatabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)/'experiment'
        process = subprocess.run([sys.executable, '-m', 'validation_lab.repeat_pressure_comparison',
            '--output', str(cls.output), '--seeds', '7'], capture_output=True, text=True)
        if process.returncode:
            raise AssertionError(process.stdout+process.stderr+(cls.output/'repeatability.json').read_text())
        cls.summary = json.loads((cls.output/'repeatability.json').read_text())
        cls.bundles = [cls.output/f'repeat-{i}' for i in (1, 2)]
        cls.reports = [json.loads((p/'report.json').read_text()) for p in cls.bundles]

    def setUp(self):
        self.temporary = TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.results = [deepcopy(next(r for r in report['results'] if r['case_id'] == 'competing-routes'
            and r['configuration'] == 'work-16' and r['variant'] == 'B3')) for report in self.reports]
        self.traces = [semantic_trace(p/run_name(r)) for p, r in zip(self.bundles, self.results)]

    def compare(self, mode='matched-operation-work'):
        return compare_run(*self.results, *self.traces, mode)

    def test_two_real_processes_fresh_authorities_and_complete_paired_matrix(self):
        self.assertEqual(self.summary['status'], 'PASS')
        self.assertEqual(self.summary['work_limited_matches'], 8)
        self.assertEqual(len(self.summary['comparisons']), 16)
        self.assertEqual(len(self.summary['attempts']), 2)
        self.assertTrue(all(a['returncode'] == 0 for a in self.summary['attempts']))
        self.assertTrue(all(a['status'] == 'PASS' for a in self.summary['audits']))
        self.assertEqual(self.summary['distinct_authorities'], 32)
        self.assertFalse(self.summary['charged_to_controllers'])
        a, b = [authority_ids(p, r) for p, r in zip(self.bundles, self.reports)]
        self.assertFalse(a & b)
        for row in self.summary['comparisons']:
            if row['mode'] == 'matched-operation-work':
                self.assertEqual(row['first_semantic_sha256'], row['second_semantic_sha256'])

    def test_fresh_ids_and_times_normalize_without_mutating_inputs(self):
        self.assertNotEqual(self.results[0]['final_snapshot'], self.results[1]['final_snapshot'])
        before = deepcopy(self.results)
        self.assertEqual(semantic_result(self.results[0]), semantic_result(self.results[1]))
        self.assertEqual(self.traces[0], self.traces[1])
        self.assertEqual(self.compare()['status'], 'PASS')
        self.assertEqual(self.results, before)

    def test_work_outcome_and_scope_differences_cannot_be_hidden_by_normalization(self):
        original = deepcopy(self.results[1])
        mutations = [lambda r: r['work'].__setitem__('inference_calls', r['work']['inference_calls']+1),
            lambda r: r['outcomes'][0].__setitem__('external_weighted_loss', 0),
            lambda r: r['initial_snapshot']['revisions'].__setitem__('policy', 'changed'),
            lambda r: r['final_snapshot']['goals'][0]['relief_events'].append('extra'),
            lambda r: r.__setitem__('unknown_new_semantic_field', 1),
            lambda r: r.__setitem__('stop_reason', 'BLOCKED')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.results[1] = deepcopy(original); mutate(self.results[1])
                row = self.compare()
                self.assertEqual(row['status'], 'FAIL')
                self.assertTrue(row['difference_paths'])
                self.assertNotEqual(row['first_semantic_sha256'], row['second_semantic_sha256'])

    def test_rank_pressure_and_receipt_differences_are_retained(self):
        original = deepcopy(self.traces[1])
        mutations = [lambda rows: rows[0]['ranks'][rows[0]['selected']['candidate_id']].__setitem__(0, 100),
            lambda rows: rows[0]['pressure'].__setitem__('residual_l1', 1),
            lambda rows: rows[0]['pressure']['sources'][next(iter(rows[0]['pressure']['sources']))].__setitem__('open_demand', 100),
            lambda rows: rows[1]['receipt'].__setitem__('status', 'FAIL')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.traces[1] = deepcopy(original); mutate(self.traces[1])
                self.assertEqual(self.compare()['status'], 'FAIL')

    def test_timing_changes_are_reported_but_not_semantic_failures(self):
        original = self.results[1]['controller_elapsed_ns']
        self.results[1]['controller_elapsed_ns'] += 12345
        self.results[1]['costs_ns']['candidate_discovery_ns'] += 1
        row = self.compare()
        self.assertEqual(row['status'], 'PASS')
        self.assertEqual(row['controller_elapsed_ns'][1], original+12345)
        self.assertEqual(row['all_costs_ns'][1], self.results[1]['costs_ns'])

    def test_wall_variation_is_reported_without_forcing_a_match(self):
        self.results[1]['outcomes'][0]['external_weighted_loss'] = 0
        row = self.compare('matched-wall-cap')
        self.assertEqual(row['status'], 'OBSERVED_VARIATION')
        self.assertFalse(row['semantics_identical'])
        self.assertTrue(row['difference_paths'])

    def test_work_limited_wall_stop_is_inconclusive_even_if_both_match(self):
        for row in self.results:
            row['stop_reason'] = 'WALL_BUDGET'
        self.assertEqual(self.compare()['status'], 'INCONCLUSIVE')
        for row in self.results:
            row['stop_reason'] = 'OBSERVED_GOALS'; row['wall_overrun_ns'] = 1
        self.assertEqual(self.compare()['status'], 'INCONCLUSIVE')

    def test_copied_bundle_cannot_count_as_an_independent_repeat(self):
        copied = self.directory/'copied'; shutil.copytree(self.bundles[0], copied)
        # Input audit behavior is separately exercised by the real CLI fixture;
        # isolate the subsequent authority-reuse check here.
        with patch('validation_lab.repeat_pressure_comparison.audit_bundle', return_value=self.summary['audits'][0]):
            with self.assertRaisesRegex(AuditError, 'reuse authorities'):
                compare_bundles(self.bundles[0], copied)
        with self.assertRaisesRegex(AuditError, 'distinct comparison bundles'):
            compare_bundles(self.bundles[0], self.bundles[0])

    def test_corrupt_bundle_is_not_compared_based_on_its_cached_audit(self):
        copied = self.directory/'corrupted'; shutil.copytree(self.bundles[0], copied)
        path = copied/run_name(self.results[0])/'trace.jsonl'; path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(AuditError, 'artifact digest'):
            compare_bundles(copied, self.bundles[1])

    def test_changed_sources_or_configuration_rejected_before_semantic_comparison(self):
        copied = self.directory/'changed'; shutil.copytree(self.bundles[0], copied)
        for name, mutate, message in (
            ('report.json', lambda r: r['source_files'].__setitem__('reachability/pressure.py', '0'*64), 'source inputs'),
            ('configuration.json', lambda r: r['configurations'][0]['budget'].__setitem__('actions', 7), 'configurations')):
            with self.subTest(name=name):
                path = copied/name; original = path.read_text(); value = json.loads(original); mutate(value)
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(AuditError, message): compare_bundles(copied, self.bundles[1])
                path.write_text(original)

    def test_difference_diagnostics_are_bounded(self):
        paths = differences(list(range(100)), list(range(1,101)))
        self.assertEqual(len(paths), 32)
        self.assertEqual(paths[0], '$[0]')

    def test_failed_child_preserved_and_no_automatic_retry(self):
        destination = self.directory/'failed'
        with patch.object(sys, 'argv', ['repeat', '--output', str(destination)]), redirect_stdout(StringIO()), \
                patch('validation_lab.repeat_pressure_comparison.subprocess.run', return_value=subprocess.CompletedProcess([], 1)) as child:
            with self.assertRaises(SystemExit) as caught: main()
        self.assertEqual(caught.exception.code, 1); self.assertEqual(child.call_count, 1)
        report = json.loads((destination/'repeatability.json').read_text())
        self.assertEqual(report['status'], 'FAIL'); self.assertEqual(report['attempts'][0]['returncode'], 1)
        self.assertTrue((destination/'repeatability.md').is_file())

    def test_inconclusive_cli_exit_is_distinct_from_success_and_failure(self):
        destination = self.directory/'inconclusive'; result = deepcopy(self.summary); result['status'] = 'INCONCLUSIVE'
        with patch.object(sys, 'argv', ['repeat', '--output', str(destination), '--bundles', *map(str,self.bundles)]), \
                patch('validation_lab.repeat_pressure_comparison.compare_bundles', return_value=result), redirect_stdout(StringIO()):
            with self.assertRaises(SystemExit) as caught: main()
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(json.loads((destination/'repeatability.json').read_text())['status'], 'INCONCLUSIVE')

    def test_existing_output_or_output_inside_input_is_refused(self):
        destination = self.directory/'existing'; destination.mkdir(); (destination/'sentinel').write_text('keep')
        with patch.object(sys, 'argv', ['repeat', '--output', str(destination)]):
            with self.assertRaises(FileExistsError): main()
        self.assertEqual((destination/'sentinel').read_text(), 'keep')
        destination = self.bundles[0]/'nested-report'
        with patch.object(sys, 'argv', ['repeat', '--output', str(destination), '--bundles', *map(str,self.bundles)]), \
                redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit): main()
        self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
