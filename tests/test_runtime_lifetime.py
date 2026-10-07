"""Protocol and preservation checks independent of native installation."""
import subprocess,unittest
from pathlib import Path
from runtime_lifetime_lab.config import cells,configuration,ARMS
from multihop_lab.cases import configuration as original

class LifetimeContracts(unittest.TestCase):
    def test_frozen_paths_unchanged(self):
        for name in ('experimental_native_recall/backend.py','experimental_native_recall/schema.py','experimental_native_multihop/project.py','experimental_native_multihop/observe.py','experimental_multihop/consumer.py','native/atomspace_recall.cc','scripts/build_native_recall.py','scripts/build_adapters.py'):
            self.assertEqual(Path(name).read_bytes(),subprocess.check_output(['git','show','c088775:'+name]))
    def test_two_sweeps_reverse_arms_without_changing_tasks(self):
        c=list(cells());self.assertEqual(len(c),72);self.assertEqual(len(set(c)),72)
        for start in range(0,72,3):self.assertEqual([x[1] for x in c[start:start+3]],list(ARMS if c[start][0]==0 else reversed(ARMS)))
        cfg=configuration()
        for key,value in original().items():
            if key!='order':self.assertEqual(cfg[key],value)
    def test_runtime_layer_does_not_import_controller_or_evaluator(self):
        import ast
        for p in Path('experimental_runtime_lifetime').glob('*.py'):
            for node in ast.walk(ast.parse(p.read_text())):
                if isinstance(node,ast.ImportFrom):self.assertFalse(any(x in (node.module or '') for x in ('_lab','consumer','reference')))
