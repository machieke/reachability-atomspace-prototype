"""Finite schema/read-only tests; no native build required by the default suite."""
import ast
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from experimental_native_recall.schema import Projection,QueryLimits
from experimental_native_recall.session import Session
from experimental_native_recall.backend import readback,RecallError
from goal_pln_lab.cases import World,configuration


class NativeRecallSchemaTests(unittest.TestCase):
    def setup_case(self):
        t=TemporaryDirectory();self.addCleanup(t.cleanup)
        s=Session(t.name);self.addCleanup(s.close);w=World(configuration()['fixtures'][1]);w.setup(s)
        return s,w
    def test_complete_universe_projection_is_readonly_and_exact(self):
        s,_=self.setup_case();snapshot=s.read();before=s.authority_records();seq=s.service._journal_sequence
        p=Projection(snapshot);q=Projection(snapshot)
        self.assertEqual(p.wire(),q.wire());self.assertEqual(before,s.authority_records())
        self.assertEqual(seq,s.service._journal_sequence);self.assertFalse(s.runtime.calls)
        self.assertEqual(sum(k=='rule' for k,_,_ in p.catalog.values()),len(snapshot.rules))
        self.assertGreater(len(p.catalog),len(snapshot.rules));self.assertIn('authority-identity/v1',[r[0] for r in snapshot.contracts])
    def test_duplicate_conflicting_identity_rejected_before_native(self):
        s,_=self.setup_case();view=s.read()
        with self.assertRaisesRegex(ValueError,'duplicate'):
            Projection(replace(view,rules=view.rules+(view.rules[0],)))
        changed=replace(view.rules[0],deduction=view.rules[1].deduction)
        with self.assertRaisesRegex(ValueError,'duplicate'):
            Projection(replace(view,rules=(view.rules[0],changed)))
    def test_input_and_query_limits_are_explicit(self):
        s,_=self.setup_case();view=s.read()
        with self.assertRaisesRegex(ValueError,'capacity'):
            Projection(replace(view,rules=view.rules*6))
        for args in (dict(visits=4097),dict(results=513),dict(queries=4097),dict(visits=-1),dict(visits=True)):
            with self.assertRaises(ValueError):QueryLimits(**args)
        with self.assertRaisesRegex(ValueError,'authority'):
            Projection(replace(view,contracts=tuple(c for c in view.contracts if c[0]!='authority-identity/v1')))
    def test_partial_or_malformed_readback_cannot_publish(self):
        s,_=self.setup_case();p=Projection(s.read())
        for response in ([],['READY bogus 0 0 0 0'],['A 0 0 N ff','READY bogus 1 0 0 0']):
            with self.assertRaises(RecallError):readback(response,p.wire())
    def test_view_binding_covers_time_and_opportunity(self):
        s,_=self.setup_case();old=s.read();s.service.advance_clock('ctx',2**80+7,idempotency_key=s.key());s.service.advance_resource_clock(2**80+7,idempotency_key=s.key());new=s.read()
        self.assertNotEqual(Projection(old).binding,Projection(new).binding)
        probe=s.probes['source-report'];s.publish_probe(replace(probe,opportunity=1))
        self.assertNotEqual(Projection(new).binding,Projection(s.read()).binding)
        self.assertIn(str(2**80+7),'\n'.join(str(v) for v in Projection(new).wire()[3].values()))
    def test_runtime_does_not_import_evaluator_or_new_scheduler(self):
        for p in Path('experimental_native_recall').glob('*.py'):
            imports=[n.module or '' for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any(i.startswith(('native_recall_lab','goal_pln_lab','validation_lab','experimental_pressure')) for i in imports))
        self.assertEqual(Path('adapters.lock.json').read_bytes(),__import__('subprocess').check_output(['git','show','846053a:adapters.lock.json']))
