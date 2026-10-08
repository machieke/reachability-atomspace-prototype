"""Only duplicate full-snapshot embedding changes; every source structure stays."""
from hashlib import sha256
from time import perf_counter_ns
from experimental_native_recall.schema import Projection as FullProjection,source_id
from reachability.atomspace_adapter import RecordProjection
from reachability.trace_protocol import canonical

PROJECTION_SCHEMA='native-atomspace-recall-compact/v1'
ENVELOPE_SCHEMA='native-public-snapshot-envelope/v1'
ENVELOPE_KEY='snapshot:external-envelope/v1'
ENCODING='reachability.trace_protocol.canonical(snapshot.records())/utf-8'
COMPLETENESS=dict(authoritative_capture=True,supported_discovery_universe=True,native_projection_readback=True,whole_snapshot_embedded=False)


def make_envelope(binding,size,digest):
    return dict(schema=ENVELOPE_SCHEMA,projection_schema=PROJECTION_SCHEMA,canonical_encoding=ENCODING,
        snapshot_sha256=digest,snapshot_bytes=size,snapshot_binding=binding,snapshot_representation='external-full-capture')


def validate_envelope(projection,snapshot,graph):
    """Compare the actual native StringValue with this complete canonical input."""
    public=canonical(snapshot.records()).encode()
    if len(public)>2097152:raise ValueError('complete public export exceeds 2 MiB view cap')
    expected=make_envelope(snapshot.binding,len(public),sha256(public).hexdigest())
    metadata=graph.aliases[projection.metadata_ref];key=graph.aliases[projection.envelope_ref]
    if graph.atoms[metadata]!=('N','view:'+snapshot.binding) or graph.atoms[key]!=('P',ENVELOPE_KEY):
        raise ValueError('compact envelope metadata identity differs')
    if graph.values.get((metadata,key))!=canonical(expected):raise ValueError('compact envelope differs from complete public capture')
    return expected


class Projection(FullProjection):
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
        metadata=self.batch.node('view:'+self.binding);self.metadata_ref=metadata
        # Full input remains captured, serialized and bounded, even though its
        # duplicate opaque native Values are replaced by a binding envelope.
        serial_start=perf_counter_ns();public=canonical(snapshot.records()).encode()
        if len(public)>2097152:raise ValueError('complete public export exceeds 2 MiB view cap')
        self.serialization_ns=perf_counter_ns()-serial_start;self.export_bytes=len(public)
        t=perf_counter_ns();h=sha256(public).hexdigest();self.snapshot_hash_ns=perf_counter_ns()-t
        t=perf_counter_ns();self.envelope=make_envelope(self.binding,len(public),h)
        self.envelope_ref=self.batch.node(ENVELOPE_KEY,predicate=True)
        self.batch.set_value(metadata,self.envelope_ref,canonical(self.envelope))
        self.envelope_construction_ns=perf_counter_ns()-t
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
