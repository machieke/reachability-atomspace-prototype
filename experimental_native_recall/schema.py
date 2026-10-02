"""Complete bounded discovery-universe projection; no task closure or answer sets."""
from dataclasses import dataclass, fields
from hashlib import sha256
from time import perf_counter_ns
from experimental_online_pln.agenda import wire, digest
from reachability.atomspace_adapter import RecordProjection, _hex
from reachability.codec import encode
from reachability.model import Literal
from reachability.trace_protocol import canonical

SCHEMA='native-atomspace-recall/v1'
KINDS=('producers','current','historical','reports','probes','models','record','all_rules','all_current')


@dataclass(frozen=True)
class QueryLimits:
    visits: int=4096
    results: int=512
    queries: int=4096
    def __post_init__(self):
        if any(type(v) is not int or not 0<=v<=cap for v,cap in zip((self.visits,self.results,self.queries),(4096,512,4096))):
            raise ValueError('query limit outside declared bounds')


def source_id(kind,context,identity):
    return canonical((kind,context,identity))


def record_payload(value):
    # Reports and probes are public receipt descriptors, not authority records.
    if type(value).__name__=='Report':value=(value.evidence,value.report,value.revoked)
    if type(value).__name__=='Probe':value=tuple(getattr(value,f.name) for f in fields(value))
    return canonical(encode(value)),value


class Projection:
    def __init__(self,snapshot):
        started=perf_counter_ns()
        self.snapshot=snapshot;self.binding=snapshot.binding
        identities=[c[1] for c in snapshot.contracts if c[0]=='authority-identity/v1']
        if len(identities)!=1 or not isinstance(identities[0],str):
            raise ValueError('explicit public authority identity required')
        self.authority=identities[0];self.context=snapshot.context.context_id
        if (len(snapshot.rules)>16 or sum(len(v.current) for v in snapshot.numerical)>32
            or len(snapshot.models)>16 or len(snapshot.reports)>128 or len(snapshot.probes)>16):
            raise ValueError('discovery input capacity exceeded')
        history_count=sum(len(v.historical) for v in snapshot.numerical)
        if history_count+len(snapshot.rules)+len(snapshot.reports)+len(snapshot.probes)+len(snapshot.models)>512:
            raise ValueError('view source record capacity exceeded before projection')
        if len({v.conclusion for v in snapshot.numerical})!=len(snapshot.numerical):
            raise ValueError('duplicate numerical view identity')
        self.projection=RecordProjection();self.batch=self.projection.batch
        self.catalog={};self.record_refs={};self.literal_refs={};self.relations=[];self.registrations=[]
        self.tags={n:self.batch.node('recall:'+n+'/v1',predicate=True) for n in
            ('literal','arguments','premises','model-supports','producer','current','historical','report','probe','model')}
        metadata=self.batch.node('view:'+self.binding)
        # All public input, including nonquery operational state and received
        # history, is exactly represented in bounded named StringValue chunks.
        serial_start=perf_counter_ns();public=canonical(snapshot.records()).encode()
        if len(public)>2097152:raise ValueError('complete public export exceeds 2 MiB view cap')
        self.serialization_ns=perf_counter_ns()-serial_start
        self.export_bytes=len(public)
        for n,start in enumerate(range(0,len(public),32768)):
            # ASCII codec JSON uses escaped Unicode, so chunk boundaries are safe.
            self.batch.set_value(metadata,self.batch.node('snapshot:chunk:'+str(n),predicate=True),public[start:start+32768].decode())
        self.batch.set_value(metadata,self.batch.node('snapshot:authority',predicate=True),self.authority)
        self.batch.set_value(metadata,self.batch.node('snapshot:binding',predicate=True),self.binding)
        for label,value in (('logical-time',snapshot.context.logical_time),('knowledge-revision',snapshot.context.knowledge_revision),
                            ('resource-revision',snapshot.resource.revision),('goal-revision',snapshot.goal.projection.goal_revision),
                            ('lifecycle-revision',snapshot.lifecycle.lifecycle_revision)):
            self.batch.set_value(metadata,self.batch.node('snapshot:'+label,predicate=True),str(value))
        for contract in snapshot.contracts:
            if contract[0]=='registered-content/v1':self.projection.add(contract[2])
        self._unique(snapshot.rules,lambda r:(r.rule_id,r.revision),'rule')
        for rule in snapshot.rules:self.add_rule(self.context,rule)
        historical={}
        for view in snapshot.numerical:
            if view.context_id!=self.context:raise ValueError('mixed source context')
            if any(b.proposal.support.conclusion!=view.conclusion for b in (*view.current,*view.historical)):
                raise ValueError('numerical view literal mismatch')
            self._unique(view.historical,lambda b:b.belief_revision_id,'historical support')
            self._unique(view.current,lambda b:b.belief_revision_id,'current support')
            for belief in view.historical:
                if belief.context_id!=self.context:raise ValueError('mixed belief context')
                ident=self.add_record('support',self.context,belief.belief_revision_id,belief)
                self.relation('historical',self.context,belief.proposal.support.conclusion,ident)
                historical[belief.belief_revision_id]=belief
            for belief in view.current:
                if historical.get(belief.belief_revision_id)!=belief:raise ValueError('current support absent from complete history')
                self.relation('current',self.context,belief.proposal.support.conclusion,
                              source_id('support',self.context,belief.belief_revision_id))
        self._unique(snapshot.reports,lambda r:r.evidence.evidence_id,'report')
        for report in snapshot.reports:
            if report.evidence.context_id!=self.context:raise ValueError('mixed report context')
            ident=self.add_record('report',self.context,report.evidence.evidence_id,report)
            self.relation('report',self.context,report.evidence.content,ident)
        self._unique(snapshot.probes,lambda p:p.probe_id,'probe')
        for probe in snapshot.probes:
            ident=self.add_record('probe',self.context,(probe.probe_id,probe.opportunity),probe)
            target=self.literal(probe.target) if probe.report_type=='numeric' else self.symbol(probe.target)
            self.relations.append(self.batch.link((self.tags['probe'],self.ctx(self.context),self.symbol(probe.report_type),target,
                                  self.record_refs[ident],self.batch.node('integer:'+str(probe.opportunity)))))
        self._unique(snapshot.models,lambda m:m.model_id,'model')
        for model in snapshot.models:
            if model.context_id!=self.context:raise ValueError('mixed model context')
            ident=self.add_record('model',self.context,model.model_id,model)
            supports=self.batch.link((self.tags['model-supports'],*(self.batch.node('record:'+source_id('support',self.context,p))
                                                                             for p in model.premise_revision_ids)))
            self.relations.append(self.batch.link((self.tags['model'],self.ctx(self.context),self.record_refs[ident],supports,
                                  self.batch.node('bool:'+str(model.model_id in snapshot.revoked_models).lower()))))
        if len(self.catalog)>512 or len(self.relations)>1024:raise ValueError('view record/relation capacity exceeded')
        self.elapsed_ns=perf_counter_ns()-started

    @staticmethod
    def _unique(records,identity,label):
        ids=[identity(r) for r in records]
        if len(ids)!=len(set(ids)):raise ValueError('duplicate/conflicting '+label+' source identity')

    def symbol(self,text):
        if not isinstance(text,str):raise ValueError('typed string target required')
        return self.batch.node('symbol:'+text)

    def ctx(self,context):return self.batch.node('context:'+context)

    def literal(self,literal):
        if type(literal) is not Literal:raise ValueError('typed literal required')
        if literal not in self.literal_refs:
            arguments=self.batch.link((self.tags['arguments'],*(self.symbol(s) for s in literal.statement.arguments)))
            self.literal_refs[literal]=self.batch.link((self.tags['literal'],self.batch.node('polarity:'+('+' if literal.positive else '-')),
                                                       self.symbol(literal.statement.predicate),arguments))
        return self.literal_refs[literal]

    def add_record(self,kind,context,identity,value):
        ident=source_id(kind,context,identity);payload,structural=record_payload(value)
        if ident in self.catalog:
            if self.catalog[ident]!=(kind,value,payload):raise ValueError('conflicting source identity')
            return ident
        if len(payload.encode())>65536:raise ValueError('source record exceeds native Value bound')
        atom=self.batch.node('record:'+ident)
        self.batch.set_value(atom,self.batch.node('source:payload/v1',predicate=True),payload)
        self.batch.set_value(atom,self.batch.node('source:kind/v1',predicate=True),kind)
        structured=self.projection.add(structural)
        self.batch.link((self.batch.node('source:structural/v1',predicate=True),atom,structured))
        truth=(value.proposal.support.truth if kind=='support' else value.report.truth if kind=='report' else None)
        if truth is not None:self.batch.set_value(atom,self.batch.node('pln:strength-confidence',predicate=True),(truth.strength,truth.confidence))
        self.catalog[ident]=(kind,value,payload);self.record_refs[ident]=atom
        self.registrations.append('R '+_hex(ident)+' '+str(atom))
        return ident

    def relation(self,role,context,literal,ident):
        result=self.batch.link((self.tags[role],self.ctx(context),self.literal(literal),self.record_refs[ident]))
        self.relations.append(result);return result

    def add_rule(self,context,rule):
        ident=self.add_record('rule',context,(rule.rule_id,rule.revision),rule)
        ordered=self.batch.link((self.tags['premises'],*(self.literal(p) for p in rule.deduction.premises)))
        self.relations.append(self.batch.link((self.tags['producer'],self.ctx(context),self.literal(rule.deduction.conclusion),
                                               self.record_refs[ident],ordered)))
        return ident

    def wire(self):
        # Canonicalization is for transport/readback only, never query membership.
        aliases=[];atoms={};index={}
        for i,atom in enumerate(self.batch.atoms):
            normalized=('L',tuple(aliases[x] for x in atom[1])) if atom[0]=='L' else atom
            ref=index.setdefault(normalized,i);aliases.append(ref);atoms[ref]=normalized
        values={};commands=[]
        for command in self.batch.commands:
            token=command.split()
            if token[0] in ('S','F'):
                pair=(aliases[int(token[1])],aliases[int(token[2])])
                value=self.batch.values[int(token[1]),int(token[2])]
                if pair in values:
                    if values[pair]!=value:raise ValueError('conflicting immutable Value')
                    continue
                values[pair]=value
            commands.append(command)
        commands+=self.registrations
        commands+=['T '+_hex(self.binding)+' '+str(len(aliases))+' '+str(len(values))+' '+str(len(self.catalog))+' '+str(len(set(aliases[x] for x in self.relations)))]
        encoded=('\n'.join(commands)+'\n').encode()
        if len(commands)>100000 or len(encoded)>8388608:raise ValueError('native load capacity exceeded')
        return encoded,tuple(aliases),atoms,values
