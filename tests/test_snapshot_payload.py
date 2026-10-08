"""Projection fidelity without native installation; complete input caps retained."""
import ast,json,subprocess,unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from experimental_snapshot_payload.schema import Projection,validate_envelope,PROJECTION_SCHEMA
from experimental_native_recall.schema import Projection as Full
from snapshot_payload_lab.reference import expected_graph,check_projection,envelope
from multihop_lab.cases import setup,initialize
from reachability.trace_protocol import canonical

class PayloadContracts(unittest.TestCase):
    def snapshot(self):
        t=TemporaryDirectory();self.addCleanup(t.cleanup);s=setup(Path(t.name),False);self.addCleanup(s.close);initialize(s,'two-hop');return s,s.read()
    def test_complete_catalog_registered_structure_and_determinism(self):
        s,v=self.snapshot();before=s.authority_records();p=Projection(v);q=Projection(v)
        self.assertEqual(p.wire(),q.wire());self.assertEqual(before,s.authority_records());self.assertEqual(p.envelope,envelope(v))
        check_projection(v,p,expected_graph(p));self.assertLess(len(p.wire()[0]),len(Full(v).wire()[0]));self.assertFalse(s.runtime.calls)
    def test_complete_export_cap_even_with_small_recall_universe(self):
        s,v=self.snapshot();large=replace(v,received=(*v.received,{'opaque-operational-note':'x'*2097152}))
        for cls in (Full,Projection):
            with self.assertRaisesRegex(ValueError,'2 MiB'):cls(large)
    def test_envelope_exact_type_size_digest_identity_and_schema(self):
        s,v=self.snapshot();p=Projection(v);graph=expected_graph(p);self.assertEqual(validate_envelope(p,v,graph),envelope(v))
        pair=(graph.aliases[p.metadata_ref],graph.aliases[p.envelope_ref])
        for name,value in (('snapshot_sha256','0'*64),('snapshot_bytes',True),('snapshot_binding','foreign'),('projection_schema','wrong'),('snapshot_representation','fully-embedded')):
            d=dict(p.envelope);d[name]=value;bad=replace(graph,values={**graph.values,pair:canonical(d)})
            with self.assertRaisesRegex(ValueError,'envelope differs'):validate_envelope(p,v,bad)
        other=replace(v,received=(*v.received,{'opaque-operational-note':'different'}))
        with self.assertRaises(ValueError):validate_envelope(p,other,graph)
    def test_source_strings_matching_metadata_names_are_not_filtered(self):
        s,v=self.snapshot();from reachability.probability_model import ProbabilityRule
        from reachability.pln_adapter import DeductionRule
        s.register_rule(ProbabilityRule('snapshot:chunk:0','1',DeductionRule('snapshot:external-envelope/v1','snapshot:chunk:1','other')))
        v=s.read();p=Projection(v);check_projection(v,p,expected_graph(p));self.assertIn('snapshot:chunk:0','\n'.join(x[2] for x in p.catalog.values()))
    def test_frozen_implementations_builds_and_envelope_only_constructor_delta(self):
        for name in ('experimental_native_recall/schema.py','experimental_native_recall/backend.py','experimental_runtime_lifetime/backend.py','experimental_runtime_lifetime/generation.py','experimental_multihop/consumer.py','native/atomspace_recall.cc'):
            self.assertEqual(Path(name).read_bytes(),subprocess.check_output(['git','show','d2446bf:'+name]))
        # Both constructors keep exactly the source-building suffix, using the
        # original methods for source payloads/structure/relations/wire encoding.
        original=Path('experimental_native_recall/schema.py').read_text();new=Path('experimental_snapshot_payload/schema.py').read_text();marker='        for contract in snapshot.contracts:'
        old=original[original.index(marker):original.index('\n    @staticmethod')].strip();self.assertEqual(new[new.index(marker):].strip(),old)
        self.assertEqual(Projection.add_record,Full.add_record);self.assertEqual(Projection.wire,Full.wire)
    def test_runtime_import_boundary_and_counterbalanced_protocol(self):
        for p in Path('experimental_snapshot_payload').glob('*.py'):
            for node in ast.walk(ast.parse(p.read_text())):
                if isinstance(node,ast.ImportFrom):self.assertFalse(any(k in (node.module or '') for k in ('_lab','consumer','reference')))
        from snapshot_payload_lab.config import cells,ARMS
        rows=list(cells());self.assertEqual(len(set(rows)),72)
        for i in range(0,72,3):self.assertEqual([x[1] for x in rows[i:i+3]],list(ARMS if rows[i][0]==0 else reversed(ARMS)))
