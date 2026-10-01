"""Exact numerical observation chains, restored aliases and immutable historical replies."""
from copy import deepcopy
from dataclasses import replace
import math
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import event
from reachability.admission_trace import AdmissionSession
from reachability.codec import decode, encode
from reachability.dispatch_worker_state import atomic_write, read_checkpoint
from reachability.estimate_reconciliation import ACTION, COMMANDS
from reachability.journal import JournalEntry, RecoveryError, SQLiteJournal
from reachability.model import Evidence, Status
from reachability.pln_adapter import PeTTaFormulaRuntime, TruthValue
from reachability.probability_model import ProbabilityPolicy, ProbabilityReport
from reachability.reconciliation_state import ARCHIVE, MARKER
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import fingerprint
from reachability.trace_worker_state import DurableAdmissionSession, SCHEMA
from reachability.worker_inspection import inspect_worker, capture_names, file_inventory
import reachability.worker_reconciliation as reconciliation
from validation_lab.generate_admission_cases import initial, scenarios
from validation_lab.run_public_workers import REFERENCES


def estimate(identity='recovered', **changes):
    args=dict(context_id='c0',literal=1,roots=['source-recovered'],valid_until=None,strength=.75,confidence=.5)
    args.update(changes)
    return event(identity,'estimate',**args)


def persisted(root, *, prefix=None, pending=None, through=6, wrong_key=None, commit_delta=0, native=False, altered_proposal=False, history_limit=None):
    prefix=scenarios()[0]['events'][:1] if prefix is None else prefix
    pending=pending or estimate()
    with DurableAdmissionSession(initial(),root/'state',native=native) as session:
        for message in prefix: session.apply(message)
        if history_limit is not None:
            session.service.configure_probability_policy('c0',ProbabilityPolicy('limited',('sensor',),max_beliefs=history_limit),
                expected_revision='p1',idempotency_key='limit-policy')
            session.apply(event('checkpoint-policy','restart'))
        session.pending=pending;session._save()
        before=read_checkpoint(root/'state'/'worker-checkpoint.json',schema=SCHEMA)
        session._prefix=pending['event_id']
        s,a=session.service,pending['arguments'];ctx=a['context_id']
        index=0
        def key():
            nonlocal index
            value=session.key();index+=1
            return 'wrong:'+value if index-1==wrong_key else value
        result=None;certificates=[]
        if through>=1:
            s.record_evidence(Evidence(pending['event_id'],ctx,session.literal(a['literal']),'sensor',s.snapshot(ctx).logical_time,
                tuple(a['roots']),a['valid_until']),idempotency_key=key())
        if through>=2: s.record_probability_report(ProbabilityReport(pending['event_id'],TruthValue(a['strength'],a['confidence'])),idempotency_key=key())
        if through>=3: transition=s.propose_probability(ctx,'observation',evidence_id=pending['event_id'],idempotency_key=key())
        if through>=4:
            revision=s.snapshot(ctx).knowledge_revision
            pre=s.precertify_probability(transition,revision,idempotency_key=key());certificates.append(pre)
        if through>=5:
            proposal=s.infer_probability(transition,pre)
            if altered_proposal: proposal=replace(proposal,formula_id='wrong-formula')
            post=s.postcertify_probability(proposal,pre,idempotency_key=key());certificates.append(post)
        if through>=6: result=s.commit_probability(proposal,pre,post,revision+commit_delta,idempotency_key=key())
    return pending,before,result,certificates


def inspect(root, name='inspection'):
    report=inspect_worker('admission',root/'state',root/name)
    return report,reconciliation.make_request(root/name,'adopt-estimate',ACTION)


def rewrite_checkpoint(root,edit):
    path=root/'state'/'worker-checkpoint.json';body=read_checkpoint(path,schema=SCHEMA);edit(body)
    body=encode(body);atomic_write(path,dict(schema=SCHEMA,body=body,digest=fingerprint(body)))


class EstimateReconciliationTests(unittest.TestCase):
    def test_restores_belief_alias_certificates_counter_and_prior_ordered_history(self):
        prefix=[*scenarios()[12]['events'],
            event('hard-old','evidence',context_id='c0',literal=2,roots=['hard'],valid_until=None),
            event('hard-alias','adopt',context_id='c0',evidence_id='hard-old')]
        with TemporaryDirectory() as directory:
            root=Path(directory);pending,before,committed,certificates=persisted(root,prefix=prefix)
            report,request=inspect(root)
            raw={str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()}
            response=reconciliation.reconcile(request,root/'state',root/'inspection')
            self.assertFalse(response['replayed']);self.assertEqual(response['result']['outcome'],'adopted')
            self.assertEqual(response['result']['journals'],request['journals'])
            self.assertEqual(reconciliation.journal_evidence(report['evidence']),
                reconciliation.journal_evidence(file_inventory(root/'state',capture_names(root/'state'))))
            archive=reconciliation.archive_path(root/'state',request)
            prepared=reconciliation.read_control(archive/'prepared.json')
            self.assertEqual(prepared['schema'],reconciliation.ESTIMATE_RECORD_SCHEMA)
            self.assertEqual(prepared['authority_entries'],report['journals']['authority']['appended'])
            self.assertEqual(reconciliation.verify_reconciliation(archive,root/'inspection'),response['result'])
            self.assertEqual(raw,{str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()})
            with DurableAdmissionSession(initial(),root/'state',resume=True) as session:
                self.assertEqual(session.numeric[pending['event_id']],committed.belief.belief_revision_id)
                self.assertEqual(session._metadata()['next_key'],before['metadata']['next_key']+6)
                self.assertEqual(session._metadata()['numeric'][:-1],before['metadata']['numeric'])
                self.assertEqual(session._metadata()['hard'],before['metadata']['hard'])
                for identity,saved in before['completed'].items(): self.assertEqual(session.completed[identity],saved)
                row=session.apply(pending)
                self.assertTrue(session.replayed);self.assertEqual(row['outcome']['status'],'PASS')
                self.assertEqual(decode(row['diagnostics']['certificates']),tuple(certificates))
                self.assertEqual(session.certificates,certificates)
                self.assertEqual(row['projection'],REFERENCES['admission'](initial().wire(),[*prefix,pending])['projection'])
                self.assertEqual(session.apply(pending),row)
                altered=deepcopy(pending);altered['arguments']['roots']=['different']
                with self.assertRaisesRegex(ValueError,'identity'): session.apply(altered)
                session.apply(event('model-recovered','independence',context_id='c0',model_id='recovered-model',
                    premises=['e001',pending['event_id']],justification='independent sources'))
                revised=session.apply(event('revision-recovered','revise',context_id='c0',model_id='recovered-model',
                    premises=['e001',pending['event_id']]))
                self.assertEqual(revised['outcome']['status'],'PASS')
                self.assertEqual(revised['projection']['numeric']['revision-recovered']['confidence'],2/3)
            self.assertEqual(reconciliation.reconcile(request,root/'state',root/'missing'),dict(result=response['result'],replayed=True))

    def test_each_partial_chain_and_extra_progress_are_refused(self):
        for through in range(8):
            if through==6: continue
            with self.subTest(through=through),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root,through=min(through,6))
                if through==7:
                    with AdmissionService(database=root/'state'/'admission.db') as s: s.advance_clock('c0',1,idempotency_key='extra')
                _,request=inspect(root);before=file_inventory(root/'state',capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError,'exactly six'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertEqual(before,file_inventory(root/'state',capture_names(root/'state')))
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_every_primitive_idempotency_key_must_match_saved_counter(self):
        for index,command in enumerate(COMMANDS):
            with self.subTest(command=command),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root,wrong_key=index);_,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'persisted estimate command differs: '+command):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_report_literal_roots_expiry_identity_and_counter_are_bound(self):
        edits=[lambda b:b['pending']['arguments'].update(literal=2),lambda b:b['pending']['arguments'].update(roots=['wrong']),
            lambda b:b['pending']['arguments'].update(valid_until=7),lambda b:b['pending'].update(event_id='wrong'),
            lambda b:b['metadata'].update(next_key=100)]
        for edit in edits:
            with self.subTest(edit=edit),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root);rewrite_checkpoint(root,edit);_,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'persisted estimate command differs: record_evidence'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_failed_post_certificate_stale_commit_and_history_limit_refuse_adoption(self):
        for failure in ('post','commit','limit'):
            with self.subTest(failure=failure),TemporaryDirectory() as directory:
                root=Path(directory)
                prefix=scenarios()[12]['events'][:2] if failure=='limit' else None
                _,_,result,_=persisted(root,prefix=prefix,altered_proposal=failure=='post',
                    commit_delta=int(failure=='commit'),history_limit=1 if failure=='limit' else None)
                self.assertIsNot(result.status,Status.PASS)
                _,request=inspect(root)
                with self.assertRaises(RecoveryError): reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_expiry_and_revocation_preserve_history_but_block_new_numeric_revision(self):
        for retirement in ('expiry','revoke'):
            with self.subTest(retirement=retirement),TemporaryDirectory() as directory:
                root=Path(directory);pending,_,_,_=persisted(root,prefix=scenarios()[12]['events'][:2],pending=estimate(valid_until=5))
                _,request=inspect(root);reconciliation.reconcile(request,root/'state',root/'inspection')
                with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                    original=s.apply(pending)
                    s.apply(event('model','independence',context_id='c0',model_id='m',premises=['e001','recovered'],justification='independent'))
                    s.apply(event('retire','tick',context_id='c0',time=5) if retirement=='expiry' else event('retire','revoke',evidence_id='recovered'))
                    self.assertFalse(s.projection()['numeric']['recovered']['current'])
                    self.assertEqual(s.apply(pending),original)
                    self.assertEqual(s.apply(event('revise','revise',context_id='c0',model_id='m',premises=['e001','recovered']))['outcome']['status'],'STALE')

    def test_no_source_sqlite_append_public_event_or_native_executor_io(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);persisted(root,native=True);_,request=inspect(root)
            connect,append=sqlite3.connect,SQLiteJournal.append
            def private_connect(path,*args,**kwargs):
                self.assertNotIn(str(root/'state'),str(path));return connect(path,*args,**kwargs)
            def private_append(journal,*args,**kwargs):
                self.assertNotEqual(journal.path.parent,root/'state');return append(journal,*args,**kwargs)
            with patch('sqlite3.connect',private_connect),patch.object(SQLiteJournal,'append',private_append), \
                 patch.object(AdmissionSession,'_execute',side_effect=AssertionError('public event')), \
                 patch.object(AdmissionSession,'_admit',side_effect=AssertionError('composite admission')), \
                 patch.object(PeTTaFormulaRuntime,'evaluate',side_effect=AssertionError('native inference')), \
                 patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('submit')), \
                 patch.object(SimulatedExecutor,'query',side_effect=AssertionError('query')), \
                 patch.object(SimulatedExecutor,'release',side_effect=AssertionError('release')):
                result=reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertEqual(reconciliation.verify_reconciliation(reconciliation.archive_path(root/'state',request),root/'inspection'),result['result'])

    def test_publication_failures_keep_gate_and_retry_without_original_inspection(self):
        for name in ('worker-checkpoint.json','result.json'):
            with self.subTest(name=name),TemporaryDirectory() as directory:
                root=Path(directory);pending,_,_,_=persisted(root);report,request=inspect(root)
                original=reconciliation.atomic_write
                def fail(path,value):
                    if path.name==name and (name!='worker-checkpoint.json' or path.parent==root/'state'): raise OSError('failed publication')
                    return original(path,value)
                with patch.object(reconciliation,'atomic_write',fail),self.assertRaises(OSError):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertTrue((root/'state'/MARKER).exists())
                with self.assertRaisesRegex(RecoveryError,'unfinished reconciliation'): DurableAdmissionSession(initial(),root/'state',resume=True)
                archive=reconciliation.archive_path(root/'state',request)
                self.assertEqual(reconciliation.verify_reconciliation(archive,root/'inspection')['schema'],reconciliation.ESTIMATE_RECORD_SCHEMA)
                self.assertTrue(reconciliation.reconcile(request,root/'state',root/'missing')['replayed'])
                self.assertEqual(reconciliation.journal_evidence(report['evidence']),reconciliation.journal_evidence(file_inventory(root/'state',capture_names(root/'state'))))

    def test_changed_source_before_or_after_preparation_refuses_without_further_changes(self):
        for prepared in (False,True):
            with self.subTest(prepared=prepared),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root);_,request=inspect(root)
                if prepared:
                    with patch.object(reconciliation,'finish',side_effect=OSError('crash')),self.assertRaises(OSError):
                        reconciliation.reconcile(request,root/'state',root/'inspection')
                with AdmissionService(database=root/'state'/'admission.db') as s: s.revoke_evidence('recovered',idempotency_key='external')
                before=file_inventory(root/'state',capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError,'journal evidence changed' if prepared else 'stale'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertEqual(before,file_inventory(root/'state',capture_names(root/'state')))
                self.assertEqual((root/'state'/MARKER).exists(),prepared)

    def test_retained_entry_reordering_and_rehashing_cannot_change_original_binding(self):
        for change in ('order','payload'):
            with self.subTest(change=change),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root);_,request=inspect(root)
                reconciliation.reconcile(request,root/'state',root/'inspection')
                path=reconciliation.archive_path(root/'state',request)/'prepared.json';record=reconciliation.read_control(path)
                entries=record['authority_entries']
                if change=='order': entries.reverse()
                else:
                    entries[2]['payload']+=' '
                    for i in range(2,6):
                        entries[i]['previous_digest']=entries[i-1]['entry_digest']
                        entries[i]['entry_digest']=JournalEntry(**entries[i]).computed_digest()
                atomic_write(path,reconciliation.control(record))
                with self.assertRaisesRegex(RecoveryError,'prepared estimate adoption'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_last_event_slot_and_overflow_preserve_stream_bounds(self):
        for count in (127,128):
            with self.subTest(count=count),TemporaryDirectory() as directory:
                root=Path(directory);prefix=[scenarios()[0]['events'][0],*[event(str(i),'restart') for i in range(count-1)]]
                pending,_,_,_=persisted(root,prefix=prefix);_,request=inspect(root)
                if count==128:
                    with self.assertRaisesRegex(RecoveryError,'stream event bound'): reconciliation.reconcile(request,root/'state',root/'inspection')
                else:
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                    with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                        self.assertEqual(s.apply(pending)['step'],128)
                        self.assertEqual(s.apply(pending)['step'],128)
                        with self.assertRaisesRegex(ValueError,'bound'): s.apply(event('overflow','restart'))

    def test_wrong_profile_kind_and_rebound_action_are_refused(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);persisted(root);_,request=inspect(root)
            for profile in ('deployment','dispatch'):
                changed=deepcopy(request);changed['profile']=profile
                with self.assertRaisesRegex(ValueError,'only admission'): reconciliation.parse_request(changed)
            reconciliation.reconcile(request,root/'state',root/'inspection')
            changed=deepcopy(request);changed['action']='adopt_persisted_context'
            with self.assertRaisesRegex(RecoveryError,'identity'): reconciliation.reconcile(changed,root/'state',root/'inspection')
        for kind in ('evidence','revise'):
            with self.subTest(kind=kind),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root)
                arguments=(dict(context_id='c0',literal=1,roots=['source-recovered'],valid_until=None) if kind=='evidence'
                    else dict(context_id='c0',model_id=None,premises=['left','right']))
                rewrite_checkpoint(root,lambda b:b['pending'].update(kind=kind,arguments=arguments))
                _,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'numerical-estimate commands'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_truth_values_bind_exactly_including_signed_zero(self):
        for truth,change in ((dict(strength=.75,confidence=.5),dict(strength=.5)),
                (dict(strength=.75,confidence=.5),dict(confidence=.25)),
                (dict(strength=-0.0,confidence=-0.0),dict(strength=0.0))):
            with self.subTest(truth=truth,change=change),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root,pending=estimate(**truth))
                rewrite_checkpoint(root,lambda b:b['pending']['arguments'].update(change))
                _,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'command differs: record_probability_report'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_zero_confidence_and_signed_zero_remain_estimates_without_hard_assertion(self):
        for strength in (-0.0,1.0):
            with self.subTest(strength=strength),TemporaryDirectory() as directory:
                root=Path(directory);pending,_,committed,_=persisted(root,pending=estimate(strength=strength,confidence=-0.0))
                _,request=inspect(root);reconciliation.reconcile(request,root/'state',root/'inspection')
                with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                    reply=s.apply(pending)
                    self.assertEqual(reply['outcome']['status'],'PASS')
                    self.assertEqual(s.hard,{})
                    self.assertEqual(s.numeric['recovered'],committed.belief.belief_revision_id)
                    truth=s.service._probability.beliefs[s.numeric['recovered']].proposal.support.truth
                    self.assertEqual(truth.strength.hex(),strength.hex())
                    self.assertEqual(math.copysign(1,truth.confidence),-1)
                    self.assertEqual(s.service.query_belief('c0',s.literal(1)).status,Status.UNKNOWN)
