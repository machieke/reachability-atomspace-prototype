"""Saved comparison corruption witnesses, including resealed semantic changes."""
from contextlib import closing, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from validation_lab.audit_pressure_comparison import (
    AuditError, audit_bundle, audit_run, run_name, seal_bundle, source_inputs)
from validation_lab.run_pressure_comparison import main


class PressureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.original = Path(cls.temporary.name)/'original'
        with patch.object(sys, 'argv', ['comparison', '--seeds', '7', '--output', str(cls.original)]), redirect_stdout(StringIO()):
            main()
        cls.report = json.loads((cls.original/'report.json').read_text())
        cls.configuration = json.loads((cls.original/'configuration.json').read_text())

    def setUp(self):
        self.temporary = TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)/'bundle'
        shutil.copytree(self.original, self.output)
        self.result = deepcopy(next(r for r in self.report['results'] if r['case_id'] == 'competing-routes'
                                    and r['configuration'] == 'work-16' and r['variant'] == 'B3'))
        self.case = next(c for c in self.configuration['episodes'] if c['case_id'] == self.result['case_id'])
        self.config = next(c for c in self.configuration['configurations'] if c['name'] == self.result['configuration'])
        self.run = self.output/run_name(self.result)

    def rows(self):
        return [json.loads(line) for line in (self.run/'trace.jsonl').read_text().splitlines()]

    def write_rows(self, rows):
        (self.run/'trace.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))

    def check_run(self):
        return audit_run(self.run, self.case, self.config, self.result)

    def reseal(self, report=None):
        if report is not None:
            (self.output/'report.json').write_text(json.dumps(report)+'\n')
        (self.output/'bundle.json').unlink()
        seal_bundle(self.output)

    def test_command_audits_complete_matrix_and_offline_audit_leaves_bundle_unchanged(self):
        audit = json.loads((self.output/'audit.json').read_text())
        self.assertEqual(audit['status'], 'PASS'); self.assertEqual(audit['runs'], 16)
        self.assertFalse(audit['charged_to_controllers'])
        def inventory():
            return {str(p.relative_to(self.output)): sha256(p.read_bytes()).hexdigest()
                    for p in self.output.rglob('*') if p.is_file()}
        before = inventory()
        run = subprocess.run([sys.executable, '-m', 'validation_lab.audit_pressure_comparison', str(self.output)],
                             capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['selections_reproduced'], self.report['candidate_frontiers_audited'])
        self.assertEqual(inventory(), before)

    def test_missing_artifact_or_changed_bytes_fail_closed(self):
        path = self.run/'trace.jsonl'; original = path.read_bytes()
        path.write_bytes(original+b'\n')
        with self.assertRaisesRegex(AuditError, 'artifact digest'): audit_bundle(self.output)
        path.unlink()
        with self.assertRaisesRegex(AuditError, 'missing'): audit_bundle(self.output)

    def test_incomplete_matrix_rejected_even_after_resealing(self):
        report = deepcopy(self.report); report['results'].pop()
        self.reseal(report)
        with self.assertRaisesRegex(AuditError, 'matrix'): audit_bundle(self.output)

    def test_source_or_configuration_change_rejected_after_resealing(self):
        report = deepcopy(self.report)
        report['source_files']['reachability/pressure.py'] = '0'*64
        self.reseal(report)
        with self.assertRaisesRegex(AuditError, 'source bindings'): audit_bundle(self.output)
        self.reseal(self.report)
        config = deepcopy(self.configuration); config['configurations'][0]['budget']['actions'] += 1
        (self.output/'configuration.json').write_text(json.dumps(config))
        self.reseal()
        with self.assertRaisesRegex(AuditError, 'frozen comparison configuration'): audit_bundle(self.output)

    def test_bad_source_commit_fails_and_current_files_are_explicitly_bound(self):
        self.assertEqual(self.report['source_files'], source_inputs())
        with self.assertRaises((AuditError, subprocess.CalledProcessError)):
            audit_bundle(self.output, source_commit='24fa237')

    def test_rank_or_pressure_tampering_rejected_by_recomputation(self):
        original = self.rows()
        for mutate, message in (
            (lambda r: r[0]['ranks'][r[0]['selected']['candidate_id']].__setitem__(0, 1), 'recomputed ranks'),
            (lambda r: r[0]['pressure'].__setitem__('converged', False), 'recomputed pressure'),
            (lambda r: r[0].__setitem__('ranking_path', 'b0-conditional-plan-best-first'), 'ranking code path')):
            with self.subTest(message=message):
                rows = deepcopy(original); mutate(rows); self.write_rows(rows)
                with self.assertRaisesRegex(AuditError, message): self.check_run()

    def test_nonminimal_selection_and_changed_work_are_rejected(self):
        original = self.rows(); rows = deepcopy(original)
        rows[0]['selected'] = next(c for c in rows[0]['candidates'] if c != rows[0]['selected'])
        self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'ranked selection'): self.check_run()
        rows = deepcopy(original); rows[0]['work']['operation_work'] += 1; self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'selection work'): self.check_run()

    def test_receipt_reordering_truncation_and_changed_status_rejected(self):
        original = self.rows()
        for rows, message in ((original[:-2], 'stop'), (original[1:]+original[:1], 'stop')):
            self.write_rows(rows)
            with self.assertRaisesRegex(AuditError, message): self.check_run()
        rows = deepcopy(original); rows[1]['receipt']['status'] = 'UNKNOWN'; self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'replayed receipt status'): self.check_run()

    def test_missing_and_prerequisite_cannot_be_added_to_replay_snapshot(self):
        from reachability.trace_protocol import fingerprint
        rows = self.rows(); rows[0]['snapshot']['supports'].append(dict(reference='invented', literal=3,
            belief_revision=2, valid_until=None))
        rows[0]['snapshot_digest'] = fingerprint(rows[0]['snapshot']); self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'replayed public snapshot'): self.check_run()

    def test_outcomes_cannot_claim_free_relief_or_shortened_horizon(self):
        original = deepcopy(self.result)
        self.result['outcomes'][0]['external_weighted_loss'] = 0
        with self.assertRaisesRegex(AuditError, 'outcome history'): self.check_run()
        self.result = deepcopy(original); self.result['evaluation_horizon'] = 8
        with self.assertRaisesRegex(AuditError, 'horizon'): self.check_run()

    def test_journal_corruption_and_wrong_receipt_belief_are_rejected(self):
        path = self.run/'admission.db'; original = path.read_bytes()
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("UPDATE events SET result_digest='invalid' WHERE sequence=1")
            connection.commit()
        with self.assertRaisesRegex(RuntimeError, 'recovery failed'): self.check_run()
        path.write_bytes(original)
        rows = self.rows()
        rows[1]['receipt']['belief'] = rows[3]['receipt']['belief']; self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'receipt belief revision'): self.check_run()

    def test_uncheckpointed_journal_cannot_be_audited_as_a_closed_bundle(self):
        with closing(sqlite3.connect(self.run/'admission.db')) as connection:
            connection.execute("UPDATE events SET result_digest='invalid' WHERE sequence=1")
            connection.commit()
            with self.assertRaisesRegex(AuditError, 'uncheckpointed'): audit_bundle(self.output)

    def test_normalized_event_ids_still_require_exact_saved_journal_prefixes(self):
        goal = next(g for g in self.result['controller_stop_snapshot']['goals'] if g['relief_events'])
        goal['relief_events'][0] = 'invented-relief-event'
        with self.assertRaisesRegex(AuditError, 'historical relief_events'): self.check_run()

    def test_stop_counts_and_elapsed_accounting_cannot_be_rewritten(self):
        original = self.rows(); rows = deepcopy(original)
        rows[-1]['work']['candidate_visits'] += 1
        self.result['work']['candidate_visits'] += 1; self.write_rows(rows)
        with self.assertRaisesRegex(AuditError, 'derived stop work'): self.check_run()
        self.write_rows(original); self.result['work']['candidate_visits'] -= 1
        self.result['costs_ns']['other_controller_ns'] += 1
        with self.assertRaisesRegex(AuditError, 'residual controller time'): self.check_run()

    def test_replayed_phase_counts_include_rejections_and_idle_tail_for_both_controllers(self):
        for variant in ('B0', 'B3'):
            with self.subTest(variant=variant):
                result = next(r for r in self.report['results'] if r['case_id'] == self.case['case_id']
                              and r['configuration'] == self.config['name'] and r['variant'] == variant)
                self.assertEqual(result['failures']['STALE'], 1)
                self.assertEqual(result['setup_costs']['inference_calls'], 1)
                self.assertEqual(result['setup_costs']['certificates'], 2)
                self.assertEqual(result['evaluation_costs']['inference_calls'], 0)
                self.assertEqual(result['evaluation_costs']['certificates'], 0)
                self.assertGreater(result['evaluation_costs']['journal_commands'], 0)
                rows = [json.loads(line) for line in (self.output/run_name(result)/'trace.jsonl').read_text().splitlines()]
                receipts = [r['receipt'] for r in rows if r['stage'] == 'receipt']
                self.assertGreater(result['work']['journal_commands'], sum(r['costs']['journal_commands'] for r in receipts))
                self.assertEqual(audit_run(self.output/run_name(result), self.case, self.config, result), result['work']['actions'])

    def test_setup_and_evaluation_cannot_invent_inference_or_certificate_counts(self):
        original = deepcopy(self.result)
        for phase in ('setup_costs', 'evaluation_costs'):
            for counter in ('inference_calls', 'certificates'):
                with self.subTest(phase=phase, counter=counter):
                    self.result = deepcopy(original); self.result[phase][counter] += 100
                    with self.assertRaisesRegex(AuditError, 'authority work'): self.check_run()

    def test_balanced_journal_transfers_between_phases_are_rejected(self):
        from validation_lab.audit_pressure_comparison import audit_costs
        original = deepcopy(self.result)
        receipts = [r['receipt'] for r in self.rows() if r['stage'] == 'receipt']
        phases = ('setup_costs', 'work', 'evaluation_costs')
        for donor in phases:
            for recipient in phases:
                if donor == recipient: continue
                with self.subTest(donor=donor, recipient=recipient):
                    self.result = deepcopy(original)
                    self.result[donor]['journal_commands'] -= 1
                    self.result[recipient]['journal_commands'] += 1
                    # Sum-only accounting still balances; certified replay must
                    # establish where the commands actually occurred.
                    audit_costs(self.result, receipts)
                    with self.assertRaisesRegex(AuditError, 'authority work'): self.check_run()

    def test_phase_and_receipt_counter_inventories_must_match_replay(self):
        original, original_rows = deepcopy(self.result), self.rows()
        for location in ('setup_costs', 'work', 'evaluation_costs', 'receipt'):
            for change in ('extra', 'missing'):
                with self.subTest(location=location, change=change):
                    self.result = deepcopy(original); rows = deepcopy(original_rows)
                    counts = rows[1]['receipt']['costs'] if location == 'receipt' else self.result[location]
                    if change == 'extra': counts['invented_calls'] = 0
                    else: del counts['inference_calls']
                    self.write_rows(rows)
                    with self.assertRaisesRegex(AuditError, 'authority work'): self.check_run()

    def test_phase_count_corruption_is_rejected_after_resealing_complete_bundle(self):
        report = deepcopy(self.report)
        result = next(r for r in report['results'] if r['case_id'] == self.case['case_id']
                      and r['configuration'] == self.config['name'] and r['variant'] == self.result['variant'])
        result['setup_costs']['journal_commands'] += 1
        result['evaluation_costs']['journal_commands'] -= 1
        self.reseal(report)
        with self.assertRaisesRegex(AuditError, 'setup authority work'): audit_bundle(self.output)

    def test_semantic_change_is_rejected_after_resealing_complete_bundle(self):
        rows = self.rows(); rows[0]['ranks'][rows[0]['selected']['candidate_id']][0] = 100
        self.write_rows(rows); self.reseal()
        with self.assertRaisesRegex(AuditError, 'recomputed ranks'): audit_bundle(self.output)

    def test_cli_failure_is_machine_readable_and_nonzero(self):
        (self.output/'bundle.json').unlink()
        run = subprocess.run([sys.executable, '-m', 'validation_lab.audit_pressure_comparison', str(self.output)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)['status'], 'FAIL')
        self.assertEqual(run.stderr, '')


if __name__ == '__main__':
    unittest.main()
