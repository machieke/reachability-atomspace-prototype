"""Non-native seam contracts; actual helper exercises live in integration_tests."""
import ast,subprocess,unittest
from pathlib import Path
from experimental_native_multihop.access import Access,DiscoveryFailure
from experimental_native_multihop.observe import Observer
from experimental_native_recall.schema import QueryLimits
from native_multihop_lab.config import configuration
from multihop_lab.cases import configuration as frozen


class NativeMultiHopContracts(unittest.TestCase):
    def test_original_sources_are_unchanged(self):
        for name in ('experimental_multihop/project.py','experimental_multihop/consumer.py','multihop_lab/run.py','multihop_lab/cases.py','experimental_native_recall/backend.py','experimental_native_recall/schema.py','native/atomspace_recall.cc','reviews/bounded-multihop-v1/fixtures.json'):
            self.assertEqual(Path(name).read_bytes(),subprocess.check_output(['git','show','c4686bc:'+name]))
    def test_registered_factors_only_extend_original_configuration(self):
        cfg=configuration()
        for k,v in frozen().items():self.assertEqual(cfg[k],v)
        self.assertEqual(cfg['retrieval_arms'],['MH-scan','MH-native']);self.assertEqual(cfg['query_limits'],QueryLimits().__dict__)
    def test_runtime_has_no_evaluator_or_alternate_policy_import(self):
        for path in Path('experimental_native_multihop').glob('*.py'):
            for n in ast.walk(ast.parse(path.read_text())):
                if isinstance(n,ast.ImportFrom):
                    self.assertFalse(any(x in (n.module or '') for x in ('_lab','reference','consumer','agenda.enumerate_work')))
    def test_catalog_access_is_exact_native_returned_identity(self):
        source=Path('experimental_native_multihop/access.py').read_text()
        self.assertEqual(source.count('.catalog'),1);self.assertIn('catalog[i][1]) for i in result.ids',source)
    def test_failure_latch_requires_explicit_rebuild(self):
        class Fake:
            def close(self):self.closed=True
        backend=Fake();observer=Observer(backend);observer.failed='NATIVE_QUERY_FAILED:lost'
        self.assertIsNotNone(observer.failed);observer.rebuild();self.assertIsNone(observer.failed);self.assertTrue(backend.closed)
