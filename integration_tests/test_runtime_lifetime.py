"""Actual sealed artifacts, loader mappings, cold views and frozen authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import fcntl,json,os,shutil,unittest
from dataclasses import replace
from experimental_runtime_lifetime.generation import Generation,SEALS,F_GET_SEALS,memfd
from experimental_runtime_lifetime.backend import Backend,GenerationProcess
from experimental_runtime_lifetime.observe import Observer
from experimental_native_recall.backend import RecallError
from experimental_native_recall.schema import QueryLimits
from integration_tests import test_native_multihop as seam
from experimental_multihop.consumer import execute_current
from reachability.adapter_runtime import ROOT

class LifetimeIntegration(unittest.TestCase):
    session=seam.NativeMultiHopSeam.session
    step=seam.NativeMultiHopSeam.step
    compute=seam.NativeMultiHopSeam.compute
    choose=seam.NativeMultiHopSeam.choose
    def observer(self,s):
        if not hasattr(s,'_test_session_observer'):
            s._test_session_observer=Observer();self.addCleanup(s._test_session_observer.close)
        return s._test_session_observer
    def generation(self):
        g=Generation();self.addCleanup(g.close);g.prepare();return g
    def copied_root(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        files=json.loads((ROOT/'artifacts/adapter-build.json').read_text())['files']
        for name in (*files,'bin/atomspace_recall','adapter-build.json','recall-build.json'):
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'artifacts'/name,dest)
        return root

    test_missing_AND=seam.NativeMultiHopSeam.test_missing_AND
    test_shared_identity=seam.NativeMultiHopSeam.test_shared_identity
    test_unavailable_no_reset=seam.NativeMultiHopSeam.test_unavailable_no_reset
    test_wrong_order_authority=seam.NativeMultiHopSeam.test_wrong_order_and_phantom_authority
    test_cycle=seam.NativeMultiHopSeam.test_cycle
    test_depth_four=seam.NativeMultiHopSeam.test_depth_four
    test_revoke_descendants=seam.NativeMultiHopSeam.test_revoke_descendants_unrelated_survives
    test_equal_replacement_stale=seam.NativeMultiHopSeam.test_equal_replacement_stale
    test_rule_revision=seam.NativeMultiHopSeam.test_rule_revision
    test_new_producer=seam.NativeMultiHopSeam.test_new_relevant_registry
    test_opposite=seam.NativeMultiHopSeam.test_opposite_report
    test_weak_alternative=seam.NativeMultiHopSeam.test_weak_alternative
    test_readonly_authority=seam.NativeMultiHopSeam.test_readonly_no_authority
    test_no_scanner_rescue=seam.NativeMultiHopSeam.test_native_answers_causal_even_when_validator_graph_is_destroyed
    test_lost_helper_latch=seam.NativeMultiHopSeam.test_helper_loss_latched_explicit_rebuild_and_budget_continuity
    test_accepted_uncertain=seam.NativeMultiHopSeam.test_accepted_uncertain_control_survives_failed_discovery
    test_same_binding=seam.NativeMultiHopSeam.test_unchanged_binding_reuses_helper_but_runs_actual_queries
    test_forged_omission=seam.NativeMultiHopSeam.test_unrelated_inventory_and_forged_complete_omission_audit
    test_unsupported_model=seam.NativeMultiHopSeam.test_relevant_revision_model_stays_unsupported

    def test_one_generation_fresh_views_native_intermediate_then_stale_descendant(self):
        s,w,p,c,m=self.session(native=True);o=self.observer(s)
        for _ in range(3):chosen,r=self.step(s,c,m)
        mid=r['commit'].belief;g=o.backend.generation;generation_id=g.generation_id;binding=o.backend.receipt.snapshot_binding;pid=o.backend.process.process.pid
        selected,public,f,v,why=self.choose(s,c,m)
        self.assertEqual(o.backend.generation.generation_id,generation_id);self.assertNotEqual(binding,o.backend.receipt.snapshot_binding);self.assertNotEqual(pid,o.backend.process.process.pid)
        self.assertIn(mid.belief_revision_id,selected.premise_ids)
        self.assertTrue(any(mid.belief_revision_id in ident for e in o.last['events'] if e['kind']=='query' and e['result']['request']['kind']=='current' for ident in e['result']['ids']))
        self.assertEqual(execute_current(s,selected)[0]['status'],'PASS');old=selected
        from multihop_lab.cases import fixture
        source=next(x for x in fixture('two-hop')['sources'] if x['missing']);s.emit('revoke',evidence_id=source['id'])
        self.assertEqual(execute_current(s,old)[0]['status'],'STALE');self.choose(s,c,m)
        self.assertEqual(g.generation_id,generation_id);self.assertEqual(g.costs['original_verifications'],1)
        self.assertFalse(any(b.belief_revision_id==mid.belief_revision_id for q in s.read().numerical for b in q.current));self.assertTrue(any(b.belief_revision_id==mid.belief_revision_id for q in s.read().numerical for b in q.historical))
        self.assertEqual(g.costs['helper_launches'],o.backend.epochs)
    def test_actual_seals_block_content_mutation(self):
        g=self.generation()
        for name in ('bin/atomspace_recall','build/atomspace/opencog/atomspace/libatomspace.so'):
            a=g.item(name);self.assertEqual(fcntl.fcntl(a.fd,F_GET_SEALS),SEALS)
            for action in (lambda:os.pwrite(a.fd,b'X',0),lambda:os.ftruncate(a.fd,a.size+1)):
                with self.assertRaises(PermissionError):action()
        g.check(g.root,g.generation_id);self.assertEqual(g.state,'valid')
    def test_wrong_missing_receipt_binary_library_and_lock_reject(self):
        root=self.copied_root()
        for name in ('recall-build.json','adapter-build.json','bin/atomspace_recall','build/atomspace/opencog/atomspace/libatomspace.so'):
            p=root/name;original=p.read_bytes();p.write_bytes(original+b'corrupt')
            g=Generation(root);self.addCleanup(g.close)
            with self.assertRaises(RecallError):g.prepare()
            self.assertEqual(g.state,'failed');self.assertEqual(g.costs['preparations'],1);self.assertGreater(g.costs['preparation_inclusive_ns'],0);self.assertFalse(g._building);p.write_bytes(original)
        (root/'recall-build.json').unlink();g=Generation(root)
        with self.assertRaises(RecallError):g.prepare()
        shutil.copyfile(ROOT/'artifacts/recall-build.json',root/'recall-build.json')
        # Actual changed lock in a disposable source root, leaving originals intact.
        src=root/'fake-source';src.mkdir();(src/'adapters.lock.json').write_text('{}')
        from reachability import adapter_runtime
        with patch.object(adapter_runtime,'ROOT',src):
            with self.assertRaisesRegex(RecallError,'different dependency lock'):Generation(root).prepare()
    def test_original_tree_drift_does_not_switch_active_generation(self):
        root=self.copied_root();s,w,p,c,m=self.session();backend=Backend(root=root);o=Observer(backend);self.addCleanup(o.close);a=o(s,m);g=backend.generation
        for name in ('bin/atomspace_recall','build/atomspace/opencog/atomspace/libatomspace.so'):
            with (root/name).open('ab') as f:f.write(b'original-drift')
        s.emit('tick',time=1);b=o(s,m);self.assertTrue(b[2].data()['complete']);self.assertEqual(backend.generation,g);self.assertEqual(g.costs['original_verifications'],1);self.assertEqual(backend.epochs,2)
        fresh=Generation(root)
        with self.assertRaises(RecallError):fresh.prepare()
    def test_alias_missing_replaced_and_fd_identity_drift_close_generation(self):
        for change in ('missing','alias','descriptor'):
            g=self.generation();os.chmod(g.directory,0o700);path=g.directory/'libatomspace.so';a=g.item('bin/atomspace_recall')
            if change=='missing':path.unlink()
            elif change=='alias':path.unlink();os.symlink(str(ROOT/'artifacts/build/atomspace/opencog/atomspace/libatomspace.so'),path)
            else:
                fd=memfd('test-unsealed-replacement');os.dup2(fd,a.fd);os.close(fd)
            with self.assertRaises(RecallError):g.check(g.root,g.generation_id)
            self.assertEqual(g.state,'failed');self.assertFalse(g._building)
    def test_loaded_mapping_rejects_baked_in_original_libraries(self):
        g=self.generation();command=g.command
        with patch.object(g,'command',side_effect=lambda **kw:command(inhibit=False,**kw)):
            process=GenerationProcess(g);self.addCleanup(process.close)
            with self.assertRaisesRegex(RecallError,'unpinned mapped'):process.receive('native-atomspace-recall/v1 ')
        self.assertEqual(g.state,'failed');self.assertEqual(g.costs['helper_launches'],0)
    def test_closed_wrong_root_protocol_id_and_descriptor_reject(self):
        for kind in ('closed','root','protocol','identity','descriptor'):
            g=self.generation();args=[g.root,g.generation_id];kwargs={}
            if kind=='closed':g.close()
            elif kind=='root':args[0]=g.root/'other'
            elif kind=='protocol':kwargs['protocol']='unknown'
            elif kind=='identity':args[1]='unrecognized'
            else:
                d=g.descriptor;d['lock_sha256']='changed';g.descriptor_json=json.dumps(d)
            with self.assertRaises(RecallError):g.check(*args,**kwargs)
    def test_query_bounds_stale_epoch_malformed_readback_no_reset(self):
        s,w,p,c,m=self.session()
        for limit in (QueryLimits(queries=0),QueryLimits(results=0),QueryLimits(visits=0)):
            o=Observer(Backend(limits=limit));self.addCleanup(o.close);public,f,v,_=o(s,m);self.assertFalse(v.data()['complete']);self.assertIsNone(c.choose(public,v)[1]);self.assertEqual(c.selections,0)
        o=self.observer(s);o(s,m);real=o.backend.query
        with patch.object(o.backend,'query',side_effect=lambda *a,**k:replace(real(*a,**k),view_id='old')):public,f,v,_=o(s,m)
        self.assertEqual(v.data()['reason'],'NATIVE_STALE_RESPONSE');self.assertIsNone(c.choose(public,v)[1]);o.rebuild()
        with patch('experimental_native_recall.backend.readback',side_effect=RecallError('malformed readback')):public,f,v,_=o(s,m)
        self.assertFalse(v.data()['complete']);self.assertIsNone(c.choose(public,v)[1]);self.assertIsNotNone(o.failed)

    def test_explicit_rebuild_charges_both_generations_and_keeps_consumer(self):
        s,w,p,c,m=self.session();o=self.observer(s);selected,*_=self.choose(s,c,m)
        state=(c.selections,c.work,c.acquisitions,set(c.attempted));first=o.backend.generation
        o.backend.process.process.kill();o.backend.process.process.wait();o(s,m);self.assertIsNotNone(o.failed)
        o.rebuild();public,f,v,_=o(s,m);self.assertTrue(v.data()['complete']);self.assertEqual(first.state,'closed')
        self.assertEqual(len(o.backend.generations),2);self.assertEqual(o.backend.runtime_costs()['preparations'],2)
        self.assertEqual(o.backend.epochs,2);self.assertEqual(state,(c.selections,c.work,c.acquisitions,set(c.attempted)))
        self.assertIsNone(c.choose(public,v)[1])
    def test_loader_environment_overrides_do_not_enter_generation(self):
        s,w,p,c,m=self.session();o=self.observer(s)
        with patch.dict(os.environ,{'LD_LIBRARY_PATH':'/untrusted','LD_PRELOAD':'/missing.so','LD_AUDIT':'/missing-audit.so'}):
            public,f,v,_=o(s,m)
        self.assertTrue(v.data()['complete']);self.assertEqual(o.backend.generation.descriptor['launch']['environment'],{'LANG':'C','LC_ALL':'C'})
