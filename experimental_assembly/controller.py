"""One shared protected-assembly rule around unchanged native assembly and field."""
from collections import OrderedDict
from time import perf_counter_ns
from experimental_attention.controller import Agenda as FrozenAgenda,Search,MODES
from experimental_attention.controller import anchor,key,extract_task,source_id,full_frontier
from experimental_attention.workspace import Workspace as FrozenWorkspace,Caps,Bound,size
from experimental_attention.field import StaleField
from experimental_native_recall.backend import IncompleteRecall
from experimental_online_pln.agenda import Limits,Frontier,wire
from .service import offers,first_affordable,PREPARATION_READS

CONTRACTS=('frozen','assembly')


class Workspace(FrozenWorkspace):
    def __init__(self,binding,context,caps,owner):
        self.owner=owner;super().__init__(binding,context,caps)
    def log(self,kind,**values):
        start=perf_counter_ns()
        try:return super().log(kind,at_query=getattr(self.owner,'used_queries',0),at_episode_query=self.owner.total_queries,at_ns=perf_counter_ns()-self.owner.decision_start,**values)
        finally:self.owner.costs['event_recording_ns']+=perf_counter_ns()-start


class Agenda(FrozenAgenda):
    def __init__(self,contract='assembly',mode='WS-queue',limits=Limits(work=16),caps=Caps(active=48,active_bytes=524288),search=Search(16),backend=None):
        if contract not in CONTRACTS or search.complete:raise ValueError('only declared bounded contracts supported')
        super().__init__(mode,limits,caps,search,backend)
        self.contract=contract;self.phase='control';self.prepare_hold=0;self.protected_used=False;self.service=None
    def available(self):
        return min(self.search.queries-self.used_queries,
                   self.search.queries*(self.limits.selections+1)-self.total_queries,
                   self.backend.limits.queries-self.backend.query_count)
    def enqueue(self,kind,target,owner):
        identity=anchor(kind,target);old=identity in self.jobs or identity in self.done
        super().enqueue(kind,target,owner)
        if not old:
            job=self.jobs[identity];job['known_query']=self.total_queries
            try:self.metadata_check()
            except Bound:
                self.jobs.pop(identity);raise
            self.ws.log('job_known',job=wire(job),remaining=self.available())
    def inspect_offers(self):
        start=perf_counter_ns()
        try:
            values=offers(self.jobs.values(),self.ws.entries,self.ws.pins,self.caps,self.available(),self.limits.tuple_visits-self.visits)
            self.ws.log('assembly_offers',offers=values,remaining=self.available(),used_slot=self.protected_used)
            return first_affordable(values)
        finally:self.costs['affordability_inclusive_ns']+=perf_counter_ns()-start
    def query(self,kind,**args):
        if self.contract=='assembly' and self.phase=='inspection' and self.prepare_hold and self.available()<=self.prepare_hold:
            self.ws.log('query_protected',kind_name=kind,hold=self.prepare_hold,remaining=self.available())
            raise Bound('PREPARATION_QUERY_RESERVE')
        self.ws.log('query_start',kind_name=kind,arguments=wire(args),phase=self.phase,hold=self.prepare_hold,remaining=self.available())
        start=perf_counter_ns()
        try:
            result=super().query(kind,**args)
            self.ws.log('query_end',kind_name=kind,ids=[i for i,_ in result],phase=self.phase,remaining=self.available())
            return result
        finally:self.costs['query_facade_inclusive_ns']+=perf_counter_ns()-start
    def control(self):
        start=perf_counter_ns();queries=self.used_queries
        try:return super().control()
        finally:
            self.costs['control_inclusive_ns']+=perf_counter_ns()-start
            self.ws.log('control_end',queries=self.used_queries-queries,pins=sorted(self.ws.pins))
    def add(self,kind,target,premises=(),inputs=(),tie=(),cost=1,acquisition=0,needs=()):
        super().add(kind,target,premises,inputs,tie,cost,acquisition,needs)
        if kind in ('deduction','revision'):
            self.ws.log('tuple_candidate',kind_name=kind,target=target,premises=premises,needs=needs)
    def join(self,rule_id):
        start=self.used_queries;visits=self.visits;before=set(self.candidates)
        job=getattr(self,'active_job',{})
        self.ws.log('join_begin',producer=rule_id,known_query=job.get('known_query'),wait_queries=self.total_queries-job.get('known_query',self.total_queries),
                    remaining=self.available(),resident=sorted(self.ws.entries),pins=sorted(self.ws.pins),phase=self.phase)
        reason='COMPLETE_ATTEMPT'
        try:super().join(rule_id)
        except (Bound,IncompleteRecall) as error:
            reason='BOUNDED:'+str(error);raise
        finally:
            join_event=next((e for e in reversed(self.ws.events) if e['kind']=='join' and e['rule']==rule_id),None)
            added=[c for i,c in self.candidates.items() if i not in before]
            if reason=='COMPLETE_ATTEMPT':
                reason=('MISSING_PREMISES' if join_event and any(not group for group in join_event['alternatives']) else
                        'COMPLETE_CANDIDATE' if added else 'NO_NEW_TUPLE')
            self.ws.log('join_end',producer=rule_id,queries=self.used_queries-start,tuple_visits=self.visits-visits,
                        new_candidates=wire(added),reason=reason,remaining=self.available(),phase=self.phase)
    def expand(self,job):
        self.active_job=job
        if self.phase!='assembly':return super().expand(job)
        start=self.used_queries
        try:return super().expand(job)
        finally:
            self.prepare_hold=PREPARATION_READS if any(self.eligible(c) for c in self.candidates.values()) else 0
            self.service.update(state='SERVED',queries=self.used_queries-start,prepare_hold=self.prepare_hold)
            self.ws.log('assembly_served',service=dict(self.service),remaining=self.available(),eligible=any(self.eligible(c) for c in self.candidates.values()))
    def prepare(self,c):
        self.phase='preparation';held=self.prepare_hold;self.prepare_hold=0
        needs=self.needs.get(c.logical_id,());missing=[i for i in needs if i not in self.ws.entries]
        self.ws.log('preparation_begin',candidate=wire(c),needs=needs,missing=missing,held=held,remaining=self.available(),
                    resident_bytes=sum(e[1] for e in self.ws.entries.values()),pins=sorted(self.ws.pins))
        start=self.used_queries
        try:return super().prepare(c)
        except Bound as error:
            self.ws.log('preparation_blocked',reason=str(error),missing=missing,remaining=self.available());raise
        finally:self.ws.log('preparation_end',queries=self.used_queries-start,pins=sorted(self.ws.pins),remaining=self.available())
    def measured_guard(self,guard,phase):
        def check():
            start=perf_counter_ns()
            try:return guard()
            finally:self.costs[phase+'_guard_read_ns']+=perf_counter_ns()-start
        return check
    def choose(self,snapshot,current_binding=None):
        self.phase='control';self.prepare_hold=0;self.protected_used=False;self.service=None
        self.decision_start=perf_counter_ns()
        try:return self._choose(snapshot,current_binding)
        except StaleField:
            if self.service is not None:
                self.service['state']='ABANDONED_STALE';self.prepare_hold=0
                self.ws.log('assembly_abandoned',service=dict(self.service),reason='STALE_BINDING')
            raise
        finally:self.costs['coordinator_total_ns']+=perf_counter_ns()-self.decision_start
    def _choose(self,snapshot,current_binding=None):
        started=perf_counter_ns();binding=snapshot.binding
        if self.round>=self.limits.selections+1:
            self.stop='SESSION_DECISION_BOUND';return Frontier((),False,self.stop,0,0),None
        guard=self.measured_guard(current_binding or (lambda:binding),'coordinator')
        field_guard=self.measured_guard(current_binding or (lambda:binding),'field')
        if guard()!=binding:raise StaleField('stale selection snapshot')
        if self.pending_pins:raise ValueError('release selected tuple after execution before next choice')
        self.snapshot=snapshot;self.context=snapshot.context.context_id;self.binding=binding
        invalidated=None
        fresh=self.workspace is None or self.workspace.binding!=binding
        if self.workspace is not None and fresh:
            self.workspace.invalidate();invalidated=dict(kind='workspace_invalidated',old=self.workspace.binding,residual=self.workspace.field.residual())
        if fresh:
            self.ws=self.workspace=Workspace(binding,self.context,self.caps,self)
            self.jobs=OrderedDict();self.done={};self.answers={};self.literals={};self.serial=0
            self.candidates={};self.needs={}
        else:
            self.ws=self.workspace;self.ws.events=[];self.ws.event_bytes=0;self.ws.costs.clear();self.ws.peak.clear();self.ws.sample()
        if invalidated:self.ws.log(**invalidated)
        self.used_queries=self.visits=0
        self.backend.open_view(snapshot)
        self.scope=dict(authority=self.backend.receipt.authority,context=self.context,task=wire(snapshot.goal.episode),session_round=self.round,binding=binding)
        self.used_queries=self.visits=0;reason='EXPLORED_RELEVANT_FRONTIER';complete=False
        field_epoch_start=self.ws.field.epoch
        self.task=extract_task(snapshot)
        if len(self.task.roots)>64 or size(self.task)>65536:raise Bound('ROOT_DESCRIPTOR_BOUND')
        self.policy=(snapshot.policy,snapshot.context.policy_revision,snapshot.context.assumptions,snapshot.context.constraints,snapshot.context.usable)
        selected=None;fallback=False
        try:
            self.control_ids=set();self.servicing_control=True
            try:self.control()
            finally:self.servicing_control=False
            roots=[]
            for root in sorted(self.task.roots,key=key):
                if root.kind=='numeric':roots.append(self.literal(root.target))
            roots+=sorted(k for k in self.ws.controls if k.startswith(('control-product:','control-health:')))
            seed_amount=self.ws.field.seed(roots) if self.mode!='WS-queue' else 0.0
            self.ws.log('seed',transferred=seed_amount,roots=sorted(set(roots)),activation=dict(self.ws.field.activation),reservoir=self.ws.field.reservoir,residual=self.ws.field.residual())
            self.enqueue('models',None,roots[0])
            control_ready=any(self.eligible(self.candidates[i]) for i in self.control_ids)
            if not control_ready or self.search.complete:
                while self.jobs:
                    if self.used_queries>=self.search.queries:raise Bound('QUERY_BUDGET')
                    if self.contract=='assembly' and self.prepare_hold and self.available()<=self.prepare_hold:raise Bound('PREPARATION_QUERY_RESERVE')
                    if guard()!=binding:raise StaleField('stale expansion epoch')
                    field_start=perf_counter_ns()
                    if self.mode=='WS-flow':
                        for _ in range(4):
                            if self.field_steps>=135168 or self.ws.field.epoch-field_epoch_start>=4096:raise Bound('FIELD_WORK_BOUND')
                            guard_before=self.costs['field_guard_read_ns'];kernel_start=perf_counter_ns()
                            event=self.ws.field.step(tuple(self.ws.arcs.values()),field_guard);self.field_steps+=1
                            self.costs['field_kernel_excluding_guards_ns']+=perf_counter_ns()-kernel_start-(self.costs['field_guard_read_ns']-guard_before)
                            self.ws.log('field',**event)
                    self.costs['field_ns']+=perf_counter_ns()-field_start
                    offer=self.inspect_offers()
                    self.phase='inspection'
                    if self.contract=='assembly' and not self.protected_used and offer is not None:
                        self.service=dict(offer,state='PROTECTED',protected_at=self.used_queries)
                        self.protected_used=True;self.prepare_hold=offer['prepare_queries'];self.phase='assembly'
                        self.ws.log('assembly_protected',service=dict(self.service),remaining=self.available())
                        job=self.jobs[offer['job_id']]
                    else:
                        job=min(self.jobs.values(),key=lambda j:((-self.ws.field.activation.get(j['anchor'],0.0) if self.mode!='WS-queue' else 0),j['order']))
                    self.jobs.pop(job['id']);self.done[job['id']]='PARTLY_EXPLORED'
                    self.ws.log('expand',job=wire(job),score=self.ws.field.activation.get(job['anchor'],0.0))
                    self.expand(job);self.done[job['id']]='LOCALLY_EXPLORED'
                    if self.mode!='WS-queue':
                        moved=self.ws.field.cool();self.ws.log('cool',amount=moved,residual=self.ws.field.residual())
                    self.metadata_check()
                complete=all(state=='LOCALLY_EXPLORED' for state in self.done.values())
                if not complete:reason='PARTLY_EXPLORED_FRONTIER'
            else:reason='CONTROL_OBLIGATION_SERVICE';self.costs['control_service']+=1
        except (Bound,IncompleteRecall) as error:
            reason=str(error)
            try:self.ws.log('bounded_stop',reason=reason)
            except Bound:pass
        self.phase='inspection'
        items=tuple(sorted(self.candidates.values(),key=lambda c:(c.kind,c.target,c.semantic_tie)))
        ready=[c for c in items if self.eligible(c)]
        if self.search.complete and complete and not ready:
            # Explicit nonbinding conformance fallback, never a primary rescue.
            t=perf_counter_ns();frontier=full_frontier(snapshot,self.limits);self.costs['conformance_fallback_ns']+=perf_counter_ns()-t
            fallback=True;complete=frontier.complete;items=frontier.candidates
            for c in items:self.age(c.logical_id)
            ready=[c for c in items if self.eligible(c)] if complete else []
        if self.selections>=self.limits.selections:self.stop='SELECTION_BUDGET';ready=[]
        elif ready:
            choice=min(ready,key=lambda c:(self.first_ready[c.logical_id],c.semantic_tie))
            try:
                if not fallback:self.prepare(choice)
                else:
                    if choice.kind=='deduction':
                        r=next(r for r in snapshot.rules if r.rule_id==choice.target)
                        self.needs[choice.logical_id]=(self.record_key('rule',r),*(source_id('support',self.context,i) for i in choice.premise_ids))
                    elif choice.kind=='adopt':self.needs[choice.logical_id]=(source_id('report',self.context,choice.target),)
                    elif choice.kind=='request':self.needs[choice.logical_id]=(source_id('probe',self.context,(choice.target,choice.premise_ids[0])),)
                    elif choice.kind=='revision':self.needs[choice.logical_id]=(source_id('model',self.context,choice.target),*(source_id('support',self.context,i) for i in choice.premise_ids))
                    self.prepare(choice)
                if guard()!=binding:raise StaleField('stale candidate publication')
                selected=choice;self.attempted.add((choice.logical_id,choice.basis));self.selections+=1;self.work+=choice.cost;self.acquisitions+=choice.acquisition_cost
            except Bound as error:reason=str(error);self.stop='BOUNDED_SEARCH_UNKNOWN:'+reason
        elif self.stop is None:
            self.stop=('BOUNDED_SEARCH_UNKNOWN:'+reason if not complete else
                       'WORK_OR_ACQUISITION_BUDGET' if any((c.logical_id,c.basis) not in self.attempted for c in items) else
                       'BOUNDED_NO_MORE_RELEVANT_WORK' if not self.search.complete else
                       'QUIESCENT_UNRESOLVED' if snapshot.goal.projection.outstanding_loss else 'OBSERVED_GOAL')
        self.ws.log('service_end',service=self.service,unused_prepare_credit=self.prepare_hold,remaining=self.available())
        self.prepare_hold=0
        self.ws.sample();self.round+=1
        self.diagnostic=dict(contract=self.contract,service=self.service,mode=self.mode,binding=binding,scope=self.scope,discovery_complete=complete,reason=reason,fallback=fallback,
            events=self.ws.events,peaks=dict(self.ws.peak),workspace_costs=dict(self.ws.costs),native_queries=self.used_queries,
            episode_queries=self.total_queries,tuple_visits=self.visits,field_steps=self.ws.field.epoch-field_epoch_start,field_epoch=self.ws.field.epoch,
            root_descriptor_bytes=size(self.task),history_bytes=size((self.first_ready,sorted(self.attempted))),history_identities=len(self.first_ready),
            allocation_residual=self.ws.field.residual(),query_states={k:dict(v,local_state='PARTLY_EXPLORED' if any(i not in self.ws.entries for i in v['ids']) else 'RETAINED_COMPLETE') for k,v in self.answers.items()},job_states=self.done,
            pending_jobs=wire(tuple(self.jobs.values())),eligible=wire(ready),ages={c.logical_id:self.first_ready[c.logical_id] for c in ready},
            native_view=wire(self.backend.receipt),pins=sorted(self.ws.pins),stopping_policy='bounded-relevant-stop/v1' if not self.search.complete else 'complete-with-frozen-fallback/v1')
        self.costs['selection_inclusive_ns']+=perf_counter_ns()-started
        return Frontier(items,complete,reason,self.visits,perf_counter_ns()-started),selected
