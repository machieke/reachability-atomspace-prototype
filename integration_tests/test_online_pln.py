from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from validation_lab.online_pln_cases import fixtures
from validation_lab.online_pln_conformance import run_case


class NativeOnlinePLNTests(TestCase):
    def test_all_selected_native_cases_and_projection_reconstruct(self):
        with TemporaryDirectory() as directory:
            for fixture in fixtures():
                with self.subTest(case=fixture['id']):
                    result = run_case(fixture, Path(directory)/fixture['id'], native=True)
                    self.assertEqual(result['conformance'], 'PASS', result.get('traceback'))
                    self.assertTrue(result['reconstruction']['projection_equal'])
                    self.assertGreater(result['reconstruction']['native_atom_count'], 0)
                    self.assertTrue(all(c['mode'] == 'native' for c in result['runtime_calls']))
