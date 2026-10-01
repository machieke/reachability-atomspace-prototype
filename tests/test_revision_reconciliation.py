"""Exact numerical revision chains, restored aliases and immutable historical replies."""
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
from reachability.revision_reconciliation import ACTION, COMMANDS
from reachability.journal import JournalEntry, RecoveryError, SQLiteJournal
from reachability.model import Status
from reachability.pln_adapter import PeTTaFormulaRuntime, PLNAdapter, TruthValue
from reachability.probability_model import ProbabilityPolicy
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.reconciliation_state import ARCHIVE, MARKER
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import fingerprint
from reachability.trace_worker_state import DurableAdmissionSession, SCHEMA
from reachability.worker_inspection import inspect_worker, capture_names, file_inventory
import reachability.worker_reconciliation as reconciliation
from validation_lab.generate_admission_cases import initial, scenarios
from validation_lab.run_public_workers import REFERENCES


def revision(identity='recovered', **changes):
    args=dict(context_id='c0',premises=['e001','e002'],model_id='m0')
    args.update(changes)
    return event(identity,'revise',**args)


def estimate(identity='fresh'):
    return event(identity,'estimate',context_id='c0',literal=1,roots=['fresh-source'],valid_until=None,strength=1.,confidence=.5)


def persisted(root, *, prefix=None, pending=None, through=4, wrong_key=None, commit_delta=0,
              pre_delta=0, native=False, alteration=None, history_limit=None):
    prefix=scenarios()[12]['events'][:5] if prefix is None else prefix
    pending=pending or revision()
    with DurableAdmissionSession(initial(),root/'state',native=native) as session:
        for message in prefix:
            session.apply(message)
            if history_limit is not None and message['kind']=='context':
                session.service.configure_probability_policy('c0',ProbabilityPolicy('limited',('sensor',),max_beliefs=history_limit),
                    expected_revision='p1',idempotency_key='limit-policy')
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
            transition=s.propose_probability(ctx,'revision',premise_revision_ids=session.references(a['premises'],True),
                independence_id=a['model_id'],idempotency_key=key())
        if through>=2:
            rev=s.snapshot(ctx).knowledge_revision
            pre=s.precertify_probability(transition,rev+pre_delta,idempotency_key=key());certificates.append(pre)
        if through>=3:
            adapter=PLNAdapter(PinnedFormulaRuntime())
            proposal=(s._derive_probability(transition,s._contexts[ctx],adapter) if pre_delta else
                s.infer_probability(transition,pre,adapter=adapter))
            if alteration=='formula': proposal=replace(proposal,formula_id='wrong-formula')
            if alteration=='truth':
                truth=proposal.support.truth
                proposal=replace(proposal,support=replace(proposal.support,truth=TruthValue(math.nextafter(truth.strength,1.),truth.confidence)))
            if alteration=='assumptions': proposal=replace(proposal,assumptions=('unbound-model',))
            if alteration=='premises': proposal=replace(proposal,premise_ids=())
            if alteration=='lineage': proposal=replace(proposal,support=replace(proposal.support,lineage_roots=('wrong',)))
            post=s.postcertify_probability(proposal,pre,idempotency_key=key());certificates.append(post)
        if through>=4: result=s.commit_probability(proposal,pre,post,rev+commit_delta,idempotency_key=key())
    return pending,before,result,certificates


def inspect(root, name='inspection'):
    report=inspect_worker('admission',root/'state',root/name)
    return report,reconciliation.make_request(root/name,'adopt-revision',ACTION)


def rewrite_checkpoint(root,edit):
    path=root/'state'/'worker-checkpoint.json';body=read_checkpoint(path,schema=SCHEMA);edit(body)
    body=encode(body);atomic_write(path,dict(schema=SCHEMA,body=body,digest=fingerprint(body)))


class RevisionReconciliationTests(unittest.TestCase):
    def test_restores_belief_alias_certificates_counter_and_prior_ordered_history(self):
        prefix=[*scenarios()[12]['events'][:5],
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
            self.assertEqual(prepared['schema'],reconciliation.REVISION_RECORD_SCHEMA)
            self.assertEqual(prepared['authority_entries'],report['journals']['authority']['appended'])
            self.assertEqual(reconciliation.verify_reconciliation(archive,root/'inspection'),response['result'])
            self.assertEqual(raw,{str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()})
            with DurableAdmissionSession(initial(),root/'state',resume=True) as session:
                self.assertEqual(session.numeric[pending['event_id']],committed.belief.belief_revision_id)
                self.assertEqual(session._metadata()['next_key'],before['metadata']['next_key']+4)
                self.assertEqual(session._metadata()['numeric'][:-1],before['metadata']['numeric'])
                self.assertEqual(session._metadata()['hard'],before['metadata']['hard'])
                for identity,saved in before['completed'].items(): self.assertEqual(session.completed[identity],saved)
                row=session.apply(pending)
                self.assertTrue(session.replayed);self.assertEqual(row['outcome']['status'],'PASS')
                self.assertEqual(decode(row['diagnostics']['certificates']),tuple(certificates))
                self.assertEqual(session.certificates,certificates)
                self.assertEqual(row['projection'],REFERENCES['admission'](initial().wire(),[*prefix,pending])['projection'])
                self.assertEqual(session.apply(pending),row)
                altered=deepcopy(pending);altered['arguments']['model_id']='different'
                with self.assertRaisesRegex(ValueError,'identity'): session.apply(altered)
                continuation=[estimate(),event('model-recovered','independence',context_id='c0',model_id='recovered-model',
                    premises=['fresh',pending['event_id']],justification='independent sources'),
                    revision('revision-recovered',model_id='recovered-model',premises=['fresh',pending['event_id']])]
                for message in continuation: revised=session.apply(message)
                self.assertEqual(revised['outcome']['status'],'PASS')
                self.assertEqual(revised['projection']['numeric']['revision-recovered']['confidence'],.75)
                self.assertEqual(revised['projection'],REFERENCES['admission'](initial().wire(),[*prefix,pending,*continuation])['projection'])
            self.assertEqual(reconciliation.reconcile(request,root/'state',root/'missing'),dict(result=response['result'],replayed=True))

    def test_each_partial_chain_and_extra_progress_are_refused(self):
        for through in range(6):
            if through==4: continue
            with self.subTest(through=through),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root,through=min(through,4))
                if through==5:
                    with AdmissionService(database=root/'state'/'admission.db') as s: s.advance_clock('c0',1,idempotency_key='extra')
                _,request=inspect(root);before=file_inventory(root/'state',capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError,'exactly four'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertEqual(before,file_inventory(root/'state',capture_names(root/'state')))
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_every_primitive_idempotency_key_must_match_saved_counter(self):
        for index,command in enumerate(COMMANDS):
            with self.subTest(command=command),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root,wrong_key=index);_,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'persisted revision command differs: '+command):
                    reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_pending_premises_model_context_identity_and_counter_are_bound(self):
        edits=[lambda b:b['pending']['arguments'].update(premises=['e001','missing']),
            lambda b:b['pending']['arguments'].update(premises=['e001','e001']),
            lambda b:b['pending']['arguments'].update(model_id=None),
            lambda b:b['pending']['arguments'].update(model_id='wrong'),
            lambda b:b['pending']['arguments'].update(context_id='missing'),
            lambda b:b['pending'].update(event_id='wrong'),lambda b:b['metadata'].update(next_key=100)]
        for edit in edits:
            with self.subTest(edit=edit),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root);rewrite_checkpoint(root,edit);_,request=inspect(root)
                before=file_inventory(root/'state',capture_names(root/'state'))
                with self.assertRaises(RecoveryError): reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertEqual(before,file_inventory(root/'state',capture_names(root/'state')))
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_altered_formula_truth_provenance_failed_certificates_and_commits_are_refused(self):
        for failure in ('formula','truth','assumptions','premises','lineage','pre','commit','limit'):
            with self.subTest(failure=failure),TemporaryDirectory() as directory:
                root=Path(directory)
                _,_,result,_=persisted(root,alteration=failure,pre_delta=int(failure=='pre'),
                    commit_delta=int(failure=='commit'),history_limit=2 if failure=='limit' else None)
                self.assertIsNot(result.status,Status.PASS)
                _,request=inspect(root)
                with self.assertRaises(RecoveryError): reconciliation.reconcile(request,root/'state',root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_expiry_report_and_model_revocation_preserve_history_but_block_new_revision(self):
        for retirement in ('expiry','report','model'):
            with self.subTest(retirement=retirement),TemporaryDirectory() as directory:
                root=Path(directory);prefix=deepcopy(scenarios()[12]['events'][:5])
                prefix[1]['arguments']['valid_until']=5
                pending,_,_,_=persisted(root,prefix=prefix)
                _,request=inspect(root);reconciliation.reconcile(request,root/'state',root/'inspection')
                with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                    original=s.apply(pending)
                    s.apply(estimate())
                    s.apply(event('model','independence',context_id='c0',model_id='m',premises=['fresh','recovered'],justification='independent'))
                    retire={'expiry':event('retire','tick',context_id='c0',time=5),
                        'report':event('retire','revoke',evidence_id='e001'),
                        'model':event('retire','revoke_model',context_id='c0',model_id='m0')}[retirement]
                    s.apply(retire)
                    self.assertFalse(s.projection()['numeric']['recovered']['current'])
                    self.assertEqual(s.apply(pending),original)
                    self.assertEqual(s.apply(revision('revise',model_id='m',premises=['fresh','recovered']))['outcome']['status'],'STALE')

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
                self.assertEqual(reconciliation.verify_reconciliation(archive,root/'inspection')['schema'],reconciliation.REVISION_RECORD_SCHEMA)
                self.assertTrue(reconciliation.reconcile(request,root/'state',root/'missing')['replayed'])
                self.assertEqual(reconciliation.journal_evidence(report['evidence']),reconciliation.journal_evidence(file_inventory(root/'state',capture_names(root/'state'))))

    def test_changed_source_before_or_after_preparation_refuses_without_further_changes(self):
        for prepared in (False,True):
            with self.subTest(prepared=prepared),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root);_,request=inspect(root)
                if prepared:
                    with patch.object(reconciliation,'finish',side_effect=OSError('crash')),self.assertRaises(OSError):
                        reconciliation.reconcile(request,root/'state',root/'inspection')
                with AdmissionService(database=root/'state'/'admission.db') as s: s.revoke_probability_independence('c0','m0',idempotency_key='external')
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
                    for i in range(2,4):
                        entries[i]['previous_digest']=entries[i-1]['entry_digest']
                        entries[i]['entry_digest']=JournalEntry(**entries[i]).computed_digest()
                atomic_write(path,reconciliation.control(record))
                with self.assertRaisesRegex(RecoveryError,'prepared revise adoption'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_last_event_slot_and_overflow_preserve_stream_bounds(self):
        for count in (127,128):
            with self.subTest(count=count),TemporaryDirectory() as directory:
                root=Path(directory);prefix=[*scenarios()[12]['events'][:5],*[event(str(i),'restart') for i in range(count-5)]]
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
        for kind in ('evidence','estimate'):
            with self.subTest(kind=kind),TemporaryDirectory() as directory:
                root=Path(directory);persisted(root)
                arguments=dict(context_id='c0',literal=1,roots=['new'],valid_until=None)
                if kind=='estimate': arguments.update(strength=.5,confidence=.5)
                rewrite_checkpoint(root,lambda b:b['pending'].update(kind=kind,arguments=arguments))
                _,request=inspect(root)
                with self.assertRaisesRegex(RecoveryError,'numerical-revision commands'):
                    reconciliation.reconcile(request,root/'state',root/'inspection')

    def test_idempotent_commit_restores_alias_without_new_belief_or_revision(self):
        prefix=scenarios()[12]['events']
        with TemporaryDirectory() as directory:
            root=Path(directory);pending,before,result,certificates=persisted(root,prefix=prefix,pending=revision(premises=['e002','e001']))
            self.assertEqual(result.belief.belief_revision_id,dict(before['metadata']['numeric'])['e005'])
            self.assertEqual(result.detail,'idempotent numerical support')
            self.assertNotEqual(result.belief.pre_certificate_id,certificates[0].certificate_id)
            report,request=inspect(root);reconciliation.reconcile(request,root/'state',root/'inspection')
            with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                self.assertEqual(s.numeric['recovered'],s.numeric['e005'])
                self.assertEqual(s._metadata()['numeric'][:-1],before['metadata']['numeric'])
                self.assertEqual(len(s.service._probability.beliefs),3)
                row=s.apply(pending)
                self.assertEqual(row['projection']['aliases']['numeric']['recovered'],'e005')
                self.assertEqual(row['projection']['numeric']['e005']['confidence'],2/3)
                self.assertEqual(decode(row['diagnostics']['certificates']),tuple(certificates))
                self.assertEqual(row['diagnostics']['knowledge_revisions'],before['completed'][prefix[-1]['event_id']]['record']['diagnostics']['knowledge_revisions'])
                self.assertEqual(s._metadata()['next_key'],before['metadata']['next_key']+4)
                self.assertEqual(row['projection'],REFERENCES['admission'](initial().wire(),[*prefix,pending])['projection'])

    def test_model_binding_cannot_be_replaced_by_another_declaration(self):
        prefix=[*scenarios()[12]['events'][:5],estimate(),
            event('other-model','independence',context_id='c0',model_id='other',premises=['e001','fresh'],justification='other pair')]
        with TemporaryDirectory() as directory:
            root=Path(directory);persisted(root,prefix=prefix)
            rewrite_checkpoint(root,lambda b:b['pending']['arguments'].update(model_id='other'))
            _,request=inspect(root)
            with self.assertRaisesRegex(RecoveryError,'exact active independence'):
                reconciliation.reconcile(request,root/'state',root/'inspection')
