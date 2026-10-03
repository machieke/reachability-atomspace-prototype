"""Incremental native recall. No eager index or full frontier in bounded modes."""
from collections import Counter,OrderedDict
from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns
from experimental_online_pln.agenda import Agenda as History,Candidate,Frontier,Limits,digest,wire,enumerate_work as full_frontier
from experimental_goal_pln.relevance import extract_task,key
from experimental_native_recall.backend import Backend,RecallError,IncompleteRecall
from experimental_native_recall.schema import QueryLimits,source_id
from reachability.model import Status
from reachability.trace_protocol import canonical
from .field import Arc,StaleField
from .workspace import Workspace,Caps,Bound,size

MODES=('WS-queue','WS-local','WS-flow')


@dataclass(frozen=True)
class Search:
    queries: int=16
    complete: bool=False
    def __post_init__(self):
        if self.queries not in (16,48,4096) or (self.queries==4096)!=self.complete:raise ValueError('undeclared discovery budget')


def anchor(kind,target):return kind+':'+digest(target)


def probe_permit(snapshot,probe):
    if probe.availability=='unavailable':return 'FAIL','PUBLICLY_UNAVAILABLE'
    if 'acknowledged' in probe.preconditions and (snapshot.dispatch is None or snapshot.dispatch.state!='accepted'):
        return 'UNKNOWN','ACK_REQUIRED'
    if 'exact_product' in probe.preconditions and 'exact_product_observed' not in snapshot.operation.current_milestones:
        return 'UNKNOWN','EXACT_PRODUCT_REQUIRED'
    return 'PASS','PUBLIC_REQUEST_DESCRIPTOR'


class Agenda(History):
    def __init__(self,mode='WS-queue',limits=Limits(work=16),caps=Caps(),search=Search(),backend=None):
        if mode not in MODES:raise ValueError('unknown bounded mode')
        super().__init__(limits);self.mode=mode;self.caps=caps;self.search=search
        self.backend=backend or Backend(limits=QueryLimits(results=32))
        self.workspace=None;self.binding=None;self.costs=Counter();self.tuple_visits=0;self.total_queries=0
        self.field_steps=0;self.diagnostic={};self.pending_pins=False
    def close(self):self.backend.close()
    def release(self):
        if self.workspace is not None:self.workspace.release()
        self.pending_pins=False
    def record_key(self,kind,value):
        ident={'rule':lambda:(value.rule_id,value.revision),'support':lambda:value.belief_revision_id,
               'report':lambda:value.evidence.evidence_id,'probe':lambda:(value.probe_id,value.opportunity),
               'model':lambda:value.model_id}[kind]()
        return source_id(kind,self.context,ident)
    def route(self,source,target,purpose,status='PASS',reason='PUBLIC_SCOPED_INSPECTION'):
        self.ws.arc(Arc(source,target,purpose,self.context,self.binding,status,reason))
    def metadata_check(self):
        ids=sum(len(r['ids']) for r in self.answers.values())
        values=(list(self.jobs.values()),self.done,self.answers,self.literals,sorted(self.ws.seen))
        amount=size(values)
        if len(self.jobs)+len(self.done)>self.caps.jobs:raise Bound('JOB_VISITED_BOUND')
        if ids>self.caps.answer_ids or amount>self.caps.metadata_bytes:raise Bound('DISCOVERY_METADATA_BOUND')
        for k,v in dict(pending_jobs=len(self.jobs),visited_jobs=len(self.done),cached_answer_ids=ids,metadata_bytes=amount).items():
            self.ws.peak[k]=max(self.ws.peak[k],v)
    def enqueue(self,kind,target,owner):
        ident=anchor(kind,target)
        if ident in self.jobs or ident in self.done:return
        if len(self.jobs)+len(self.done)>=self.caps.jobs:raise Bound('JOB_VISITED_BOUND')
        self.serial+=1;self.jobs[ident]=dict(id=ident,kind=kind,target=target,anchor=owner,order=self.serial)
        try:self.metadata_check()
        except Bound:
            self.jobs.pop(ident);raise
    def literal(self,literal,parent=None):
        ident=anchor('inspect',literal)
        self.ws.admit(ident,dict(kind='literal-inspection',literal=wire(literal)),anchor=True)
        if parent:self.route(parent,ident,'ordered-premise-inspection')
        if ident not in self.literals:
            self.literals[ident]=literal
            try:self.metadata_check()
            except Bound:
                self.literals.pop(ident);raise
            for kind in ('current','producers','reports','probes'):self.enqueue(kind,literal,ident)
        return ident
    def query(self,kind,**args):
        if self.used_queries>=self.search.queries or self.total_queries>=self.search.queries*(self.limits.selections+1):
            raise Bound('QUERY_BUDGET')
        self.used_queries+=1;self.total_queries+=1
        typed=dict(args)
        if kind!='record':typed['context']=self.context
        request_key=digest((kind,typed));requery=request_key in self.answers
        result=self.backend.query(kind,binding=self.binding,**typed)
        self.costs['requeries']+=requery
        old_answer=self.answers.get(request_key)
        self.answers[request_key]=dict(kind=kind,ids=result.ids,native_complete=result.complete,
            state='COMPLETE_NONEMPTY' if result.complete and result.ids else 'COMPLETE_EMPTY' if result.complete else 'NATIVE_INCOMPLETE')
        try:self.metadata_check()
        except Bound:
            if old_answer is None:self.answers.pop(request_key)
            else:self.answers[request_key]=old_answer
            raise
        if not result.complete:raise IncompleteRecall(result)
        records=tuple((ident,self.backend.projection.catalog[ident][1]) for ident in result.ids)
        byte_count=sum(size(r) for _,r in records)
        if len(records)>self.caps.response_records or byte_count>self.caps.response_bytes:raise Bound('NATIVE_RESPONSE_CAPACITY')
        self.ws.peak['response_records']=max(self.ws.peak['response_records'],len(records));self.ws.peak['response_bytes']=max(self.ws.peak['response_bytes'],byte_count)
        self.ws.log('query_consumed',request_key=request_key,kind_name=kind,ids=result.ids,native_complete=True,
                    local_state='PARTLY_EXPLORED' if records else 'COMPLETE_EMPTY',requery=requery)
        return records
    def retain(self,records,anchor_records=False):
        for ident,record in records:self.ws.admit(ident,record,anchor=anchor_records)
    def add(self,kind,target,premises=(),inputs=(),tie=(),cost=1,acquisition=0,needs=()):
        logical=digest((kind,target,premises))
        c=Candidate(kind,target,self.context,premises,digest(inputs),logical,
                    canonical(wire((kind,target,tie))),self.binding,cost,acquisition)
        if logical not in self.candidates and len(self.candidates)>=self.caps.candidates:raise Bound('CANDIDATE_CAPACITY')
        new_candidates=dict(self.candidates);new_needs=dict(self.needs)
        new_candidates[logical]=c;new_needs[logical]=tuple(needs)
        if size((new_candidates,new_needs))>self.caps.candidate_bytes:raise Bound('CANDIDATE_BYTE_BOUND')
        self.candidates,self.needs=new_candidates,new_needs
        if getattr(self,'servicing_control',False):self.control_ids.add(logical)
        self.ws.peak['candidates']=max(self.ws.peak['candidates'],len(self.candidates))
        self.ws.peak['candidate_bytes']=max(self.ws.peak['candidate_bytes'],size((self.candidates,self.needs)))
        self.age(logical)
    def age(self,logical):
        if logical not in self.first_ready:
            if len(self.first_ready)>=8192 or size((self.first_ready,sorted(self.attempted)))>4194304-1024:raise Bound('EPISODE_HISTORY_BOUND')
            self.first_ready[logical]=self.round
    def probes(self,records,owner):
        self.retain(records,True)
        for ident,p in records:
            self.route(owner,ident,'probe-inspection')
            use=anchor('request-use',(p.probe_id,p.opportunity))
            self.ws.admit(use,dict(kind='request-use',probe=p.probe_id,opportunity=p.opportunity),anchor=True)
            status,reason=probe_permit(self.snapshot,p);self.route(ident,use,'request-use',status,reason)
            if status=='PASS':self.add('request',p.probe_id,(p.opportunity,),p,(p.opportunity,),p.cost,p.cost,needs=(ident,))
    def query_current(self,literal):
        records=self.query('current',literal=literal);self.retain(records);return records
    def join(self,rule_id):
        # Six queries form one charged, bounded join job. No partial proof.
        if self.search.queries-self.used_queries<6:raise Bound('JOIN_QUERY_BUDGET')
        rule=self.ws.get(rule_id)
        if rule is None:
            records=self.query('record',record_id=rule_id);self.retain(records,True)
            rule=self.ws.get(rule_id)
            if rule is None:raise RecallError('registered producer disappeared from immutable view')
            if self.search.queries-self.used_queries<6:raise Bound('JOIN_QUERY_BUDGET')
        groups=[];unique={};slots=0;amount=0
        for lit in (*rule.deduction.premises,rule.deduction.conclusion):
            group=self.query('current',literal=lit);proposed=dict(unique);proposed.update(group)
            amount=sum(size(v) for v in proposed.values());slots+=len(group)
            if len(proposed)>self.caps.joint_records or amount>self.caps.joint_bytes or slots>self.caps.joint_slots:raise Bound('JOINT_BUFFER_CAPACITY')
            unique=proposed;groups.append(group)
        self.ws.peak['joint_records']=max(self.ws.peak['joint_records'],len(unique));self.ws.peak['joint_bytes']=max(self.ws.peak['joint_bytes'],amount);self.ws.peak['joint_slots']=max(self.ws.peak['joint_slots'],slots)
        self.retain(tuple(unique.items()))
        alternatives=[sorted(g,key=lambda pair:(pair[1].proposal.support.evidence_ids,pair[1].belief_revision_id)) for g in groups[:5]]
        for chosen in product(*alternatives):
            if self.visits>=self.limits.tuple_visits:raise Bound('TUPLE_BUDGET')
            self.visits+=1;self.tuple_visits+=1
            supports=tuple(b for _,b in chosen);premises=tuple(b.belief_revision_id for b in supports)
            if any(b.transition.kind=='deduction' and b.transition.rule_id==rule.rule_id and b.transition.rule_revision==rule.revision and b.transition.premise_revision_ids==premises for _,b in groups[5]):continue
            self.add('deduction',rule.rule_id,premises,(rule,supports,self.policy),tuple(b.proposal.support.evidence_ids for b in supports),needs=(rule_id,*(i for i,_ in chosen)))
        self.ws.log('join',rule=rule_id,ordered_slots=wire(rule.deduction.premises),alternatives=[[i for i,_ in g] for g in groups[:5]],complete=True)
    def expand(self,job):
        kind,target,owner=job['kind'],job['target'],job['anchor']
        if owner not in self.ws.entries:
            if owner in self.literals:self.ws.admit(owner,dict(kind='literal-inspection',literal=wire(self.literals[owner])),anchor=True)
            elif kind=='join':pass
            else:raise Bound('EVICTED_OPERATION_ANCHOR')
        if kind=='current':self.query_current(target)
        elif kind=='producers':
            records=self.query('producers',literal=target);self.retain(records,True)
            for ident,rule in records:
                self.route(owner,ident,'producer-discovery');self.enqueue('join',ident,ident)
                for literal in rule.deduction.premises:self.literal(literal,ident)
        elif kind=='reports':
            if self.search.queries-self.used_queries<2:raise Bound('REPORT_QUERY_BUDGET')
            current=self.query_current(target)
            adopted={b.transition.evidence_id for _,b in current if b.transition.kind=='observation'}
            del current
            records=self.query('reports',literal=target)
            self.retain(records)
            for ident,r in records:
                e=r.evidence;now=self.snapshot.context.logical_time
                if e.evidence_id not in adopted and not r.revoked and e.observed_at<=now and (e.valid_until is None or now<e.valid_until):
                    self.add('adopt',e.evidence_id,inputs=(r,self.policy),needs=(ident,))
        elif kind=='probes':self.probes(self.query('probes',report_type='numeric',target=target),owner)
        elif kind=='join':self.join(target)
        elif kind=='models':
            records=self.query('models');self.retain(records)
            for ident,model in records:self.enqueue('revision',ident,owner)
        elif kind=='revision':self.revision(target)
        else:raise ValueError('unknown expansion job')
    def revision(self,ident):
        if self.search.queries-self.used_queries<5:raise Bound('REVISION_QUERY_BUDGET')
        model=self.ws.get(ident)
        if model is None:
            records=self.query('record',record_id=ident);self.retain(records);model=self.ws.get(ident)
        if model.model_id in self.snapshot.revoked_models:return
        parents=[]
        for pid in model.premise_revision_ids:
            records=self.query('record',record_id=source_id('support',self.context,pid))
            if not records:return
            parents.append(records[0])
        if not any(anchor('inspect',b.proposal.support.conclusion) in self.literals for _,b in parents):return
        current={i:b for _,b in parents for i,b in self.query_current(b.proposal.support.conclusion)}
        if not all(i in current for i,_ in parents):return
        if any(b.transition.kind=='revision' and b.transition.independence_id==model.model_id and b.transition.premise_revision_ids==model.premise_revision_ids for b in current.values()):return
        self.add('revision',model.model_id,model.premise_revision_ids,(model,tuple(b for _,b in parents),self.policy),tuple(b.proposal.support.evidence_ids for _,b in parents),needs=(ident,*(i for i,_ in parents)))
    def control(self):
        s=self.snapshot;op=s.operation.operation.attempt_id
        self.ws.control(anchor('control-attempt',op),dict(kind='attempt-control',attempt=op))
        for root in self.task.roots:
            if root.kind not in ('product','health'):continue
            owner=anchor('control-'+root.kind,root.target)
            self.ws.control(owner,dict(kind=root.kind,target=wire(root.target)))
            self.probes(tuple((i,p) for i,p in self.query('probes',report_type=root.kind,target=root.target[0]) if p.source in root.target[1]),owner)
        if s.intent is None and s.decision.status is Status.PASS:
            self.add('reserve',op,inputs=(s.decision.basis_id,s.operation,s.resource,s.hard,s.contracts))
        if s.intent is not None and s.dispatch is None:self.add('dispatch',op,inputs=(s.intent,s.decision.basis_id,s.operation,s.contracts))
        if s.dispatch is not None and s.dispatch.state=='uncertain':self.add('query',op,inputs=(s.dispatch,s.intent))
        if s.goal.projection.outstanding_loss==0 and s.lifecycle.episode.stage!='BUILT':self.add('complete',op,inputs=(s.goal,s.operation,s.lifecycle,s.dispatch,s.contracts))
    def eligible(self,c):return (c.logical_id,c.basis) not in self.attempted and self.work+c.cost<=self.limits.work and self.acquisitions+c.acquisition_cost<=self.limits.acquisitions
    def prepare(self,c):
        records=[]
        for ident in self.needs.get(c.logical_id,()):
            value=self.ws.get(ident)
            if value is None:
                found=self.query('record',record_id=ident)
                if len(found)!=1:raise RecallError('selected exact tuple record unavailable')
                value=found[0][1]
            records.append((ident,value))
        records.append(('candidate:'+c.logical_id,c));self.ws.pin_bundle(records);self.pending_pins=True
    def choose(self,snapshot,current_binding=None):
        started=perf_counter_ns();binding=snapshot.binding
        if self.round>=self.limits.selections+1:
            self.stop='SESSION_DECISION_BOUND';return Frontier((),False,self.stop,0,0),None
        guard=current_binding or (lambda:binding)
        if guard()!=binding:raise StaleField('stale selection snapshot')
        if self.pending_pins:raise ValueError('release selected tuple after execution before next choice')
        self.snapshot=snapshot;self.context=snapshot.context.context_id;self.binding=binding
        invalidated=None
        fresh=self.workspace is None or self.workspace.binding!=binding
        if self.workspace is not None and fresh:
            self.workspace.invalidate();invalidated=dict(kind='workspace_invalidated',old=self.workspace.binding,residual=self.workspace.field.residual())
        if fresh:
            self.ws=self.workspace=Workspace(binding,self.context,self.caps)
            self.jobs=OrderedDict();self.done={};self.answers={};self.literals={};self.serial=0
            self.candidates={};self.needs={}
        else:
            self.ws=self.workspace;self.ws.events=[];self.ws.event_bytes=0;self.ws.costs.clear();self.ws.peak.clear();self.ws.sample()
        if invalidated:self.ws.log(**invalidated)
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
                    if guard()!=binding:raise StaleField('stale expansion epoch')
                    field_start=perf_counter_ns()
                    if self.mode=='WS-flow':
                        for _ in range(4):
                            if self.field_steps>=135168 or self.ws.field.epoch-field_epoch_start>=4096:raise Bound('FIELD_WORK_BOUND')
                            event=self.ws.field.step(tuple(self.ws.arcs.values()),guard);self.field_steps+=1
                            self.ws.log('field',**event)
                    self.costs['field_ns']+=perf_counter_ns()-field_start
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
        self.ws.sample();self.round+=1
        self.diagnostic=dict(mode=self.mode,binding=binding,scope=self.scope,discovery_complete=complete,reason=reason,fallback=fallback,
            events=self.ws.events,peaks=dict(self.ws.peak),workspace_costs=dict(self.ws.costs),native_queries=self.used_queries,
            episode_queries=self.total_queries,tuple_visits=self.visits,field_steps=self.ws.field.epoch-field_epoch_start,field_epoch=self.ws.field.epoch,
            root_descriptor_bytes=size(self.task),history_bytes=size((self.first_ready,sorted(self.attempted))),history_identities=len(self.first_ready),
            allocation_residual=self.ws.field.residual(),query_states={k:dict(v,local_state='PARTLY_EXPLORED' if any(i not in self.ws.entries for i in v['ids']) else 'RETAINED_COMPLETE') for k,v in self.answers.items()},job_states=self.done,
            pending_jobs=wire(tuple(self.jobs.values())),eligible=wire(ready),ages={c.logical_id:self.first_ready[c.logical_id] for c in ready},
            native_view=wire(self.backend.receipt),pins=sorted(self.ws.pins),stopping_policy='bounded-relevant-stop/v1' if not self.search.complete else 'complete-with-frozen-fallback/v1')
        self.costs['selection_inclusive_ns']+=perf_counter_ns()-started
        return Frontier(items,complete,reason,self.visits,perf_counter_ns()-started),selected
