"""Public-only FIFO work consumer. No environment, fixture or evaluator imports."""
from time import perf_counter_ns
from experimental_online_pln.agenda import Agenda, Limits, enumerate_work, wire, digest
from experimental_work_bridge.capture import acquire
from experimental_work_bridge.project import project, Limits as GraphLimits, ObligationWorkView
from experimental_work_bridge.capture import digest as work_digest
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import evaluate


def observe(session, manifest, graph_limits=GraphLimits()):
    """One lock binds the frozen full capture, registry, public receipts and work."""
    started=perf_counter_ns()
    with session.service._lock:
        frame,acquisition=acquire(session)
        public=session.read()
        cap=immutable(frame.data()['capture']);assessments={};evaluation={}
        for kind in ('A','B'):
            assessments[kind],evaluation[kind]=evaluate(cap,manifest,kind)
        view,projection=project(frame,manifest,assessments['A'],assessments['B'],graph_limits)
    return public,frame,view,dict(acquisition=acquisition,evaluation=evaluation,projection=projection,
                                 observation_inclusive_ns=perf_counter_ns()-started)


def operation_matches(candidate,node,snapshot):
    """Match exact registered record, ordered tuple, probe opportunity and costs."""
    p=node['producer'];kind=p['kind'];record=p['record']
    if kind=='observation':
        return (candidate.kind=='request' and candidate.target==record['probe_id']
            and candidate.premise_ids==(record['opportunity'],)
            and candidate.cost==record['cost'] and candidate.acquisition_cost==record['cost']
            and any(wire(x)==record for x in snapshot.probes))
    registry=snapshot.rules if kind=='deduction' else snapshot.models
    target=record['rule_id'] if kind=='deduction' else record['model_id']
    return (candidate.kind==kind and candidate.target==target
        and list(candidate.premise_ids)==node['ordered_premises']
        and any(wire(x)==record for x in registry))


def relevant_reports(snapshot,view):
    """Include contrary and unclassified reports; never inspect truth or roots."""
    task_nodes=[n for n in view['nodes'] if n['kind']=='task']
    if not task_nodes:return set()
    target=task_nodes[0]['criterion']['conclusion']
    opposite=dict(target,positive=not target['positive'])
    literals=[target,opposite]
    for node in view['nodes']:
        if node['kind']=='operation' and node['producer']['kind']=='deduction':
            literals.extend(node['producer']['requirements'])
        elif node['kind']=='missing-premise' and node.get('literal'):
            literals.append(node['literal'])
    return {r.evidence.evidence_id for r in snapshot.reports if wire(r.evidence.content) in literals}


def describe(snapshot,view,frontier):
    """Deterministic finite task scope, pending receipt adapter and exact mappings."""
    nodes={n['id']:n for n in view['nodes']};current={b.belief_revision_id for v in snapshot.numerical for b in v.current}
    required=[n for n in nodes.values() if n['kind']=='operation' and n['producer']['kind'] in ('deduction','revision')]
    review=[dict(node=n['id'],producer=n['producer'],premises=n['ordered_premises'],
                 status='MATERIALIZED_CURRENT' if set(n['materialized_result_ids'])&current else 'UNRESOLVED',
                 readiness=n['readiness']) for n in required]
    relevant=relevant_reports(snapshot,view)
    # Receipt presence is independent from adoption eligibility or truth values.
    adopted={b.transition.evidence_id for v in snapshot.numerical for b in v.current if b.transition.kind=='observation'}
    pending=sorted(r.evidence.evidence_id for r in snapshot.reports
        if r.evidence.evidence_id in relevant and r.evidence.evidence_id not in adopted and not r.revoked)
    needed={n['id'] for n in required if not set(n['materialized_result_ids'])&current}
    for obligation in view['obligations']:
        if obligation['status']!='PASS':needed.update(obligation['routes'])
    # Traverse only the already described graph, with its declared limits.
    queue=list(sorted(needed))
    while queue:
        src=queue.pop(0)
        for edge in view['edges']:
            if edge['source']==src and edge['type'] in ('AND_PREREQUISITE','OR_OBSERVATION_OPPORTUNITY') and edge['target'] not in needed:
                needed.add(edge['target']);queue.append(edge['target'])
    ready={'INPUTS_PRESENT','OBSERVATION_OPPORTUNITY','OBSERVATION_AVAILABILITY_UNKNOWN'}
    graph={}
    if view['complete']:
        for candidate in frontier.candidates:
            matching=[n['id'] for n in nodes.values() if n['id'] in needed and n['kind']=='operation'
                      and n['readiness'] in ready and operation_matches(candidate,n,snapshot)]
            if matching:graph[candidate.logical_id]=sorted(matching)
    examined={n['producer']['record'].get('rule_id') for n in required if n['producer']['kind']=='deduction'}
    optional=[wire(r) for r in snapshot.rules if r.rule_id not in examined]
    return dict(review=sorted(review,key=lambda r:r['node']),pending_reports=pending,graph_candidates=graph,
                review_complete=view['complete'] and not pending and all(r['status']=='MATERIALIZED_CURRENT' for r in review),
                optional_unexamined_producers=optional)


class Consumer(Agenda):
    """Ephemeral relevant-basis FIFO; B constrains task readiness, never permission."""
    def choose(self,snapshot,work_view):
        t=perf_counter_ns();frontier=enumerate_work(snapshot,self.limits)
        invalid=dict(complete=False,reason='MALFORMED_OR_MISMATCHED_WORK_VIEW',nodes=[],edges=[],obligations=[],global_blockers=[],A={},B={})
        try:
            if type(work_view) is not ObligationWorkView:raise ValueError('typed work view required')
            v=work_view.data()
            if v['schema']!='obligation-work-view/v0' or v['authority'] is not False:raise ValueError('invalid work schema')
            if v['complete']:
                if (v['bindings']['assessment_A']!=work_digest(v['A']) or v['bindings']['assessment_B']!=work_digest(v['B'])
                    or v['observed']['goal']!=wire(snapshot.goal) or v['observed']['operation']!=wire(snapshot.operation)
                    or v['observed']['lifecycle']!=wire(snapshot.lifecycle)
                    or v['observed']['intent']!=wire(snapshot.intent) or v['observed']['dispatch']!=wire(snapshot.dispatch)):
                    raise ValueError('work/public binding mismatch')
            if not isinstance(v['nodes'],list) or not isinstance(v['edges'],list):raise ValueError('malformed graph')
            d=describe(snapshot,v,frontier)
        except (ValueError,KeyError,TypeError):
            v=invalid;d=describe(snapshot,v,frontier)
        d['work_input_reason']=v['reason'];d['selection_elapsed_ns']=0
        self.stop=None
        def done(reason,candidate=None):
            self.stop=reason;d['selection_elapsed_ns']=perf_counter_ns()-t
            d['budget']=dict(selections=self.selections,work=self.work,acquisitions=self.acquisitions)
            return frontier,candidate,d
        if not frontier.complete:return done(frontier.reason)
        if self.selections>=self.limits.selections:return done('SELECTION_EXHAUSTED')
        accepted=snapshot.dispatch is not None and snapshot.dispatch.state in ('accepted','uncertain')
        eligible=[];blocked_budget=False
        for c in frontier.candidates:
            priority=None;source=None
            probe=next((p for p in snapshot.probes if p.probe_id==c.target),None) if c.kind=='request' else None
            if accepted and (c.kind in ('query','complete') or probe and probe.report_type in ('product','health')):
                priority,source=0,'existing-operational-control'
            elif v['complete'] and c.kind=='adopt' and c.target in d['pending_reports']:
                priority,source=1,'received-report-adapter'
            elif c.logical_id in d['graph_candidates']:
                priority,source=2,'exact-work-route'
            elif (c.kind in ('reserve','dispatch') and v['complete'] and d['review_complete']
                  and v['A']['numerical_status']=='PASS' and v['B']['numerical_status']=='PASS'
                  and not any(b['category'] in ('OBJECTION_REQUIRES_REVIEW','APPLICABILITY_REQUIRES_REVIEW','SCOPE_OR_BUDGET_INCOMPLETE') for b in v['global_blockers'])):
                priority,source=3,'fresh-live-authorization'
            if priority is None:continue
            self.first_ready.setdefault(c.logical_id,self.round)
            if (c.logical_id,c.basis) in self.attempted:continue
            # Reserve finite headroom for control and observation after dispatch.
            work_cap=self.limits.work-(8 if priority in (1,2) else 0)
            acq_cap=self.limits.acquisitions-(4 if priority in (1,2) else 0)
            selection_cap=self.limits.selections-(8 if priority in (1,2) else 0)
            affordable=(self.work+c.cost<=work_cap and self.acquisitions+c.acquisition_cost<=acq_cap and self.selections<selection_cap)
            eligible.append(dict(candidate=c,priority=priority,origin=source,age=self.first_ready[c.logical_id],affordable=affordable))
            blocked_budget |= not affordable
        self.round+=1
        d['eligible']=[dict(candidate=wire(x['candidate']),priority=x['priority'],origin=x['origin'],first_ready=x['age'],affordable=x['affordable']) for x in eligible]
        affordable=[x for x in eligible if x['affordable']]
        if affordable:
            chosen=min(affordable,key=lambda x:(x['priority'],x['age'],x['candidate'].semantic_tie));c=chosen['candidate']
            self.attempted.add((c.logical_id,c.basis));self.selections+=1;self.work+=c.cost;self.acquisitions+=c.acquisition_cost
            d['selected_origin']=chosen['origin'];d['selected_nodes']=d['graph_candidates'].get(c.logical_id,[])
            return done(None,c)
        if blocked_budget:return done('WORK_OR_ACQUISITION_EXHAUSTED')
        if accepted:
            if snapshot.goal.projection.outstanding_loss==0 and snapshot.lifecycle.episode.stage=='BUILT':return done('OBSERVED_COMPLETION')
            return done('WAITING_EXTERNAL_OUTCOME')
        if not v['complete']:return done('INPUT_OR_WORK_INCOMPLETE')
        if any(b['category'] in ('OBJECTION_REQUIRES_REVIEW','APPLICABILITY_REQUIRES_REVIEW') for b in v['global_blockers']):return done('OBJECTION_OR_UNKNOWN_APPLICABILITY')
        if v['B']['numerical_status']=='PASS' and v['A']['numerical_status']!='PASS':return done('TASK_RESOLVED_LIVE_BLOCKED')
        if any(x['readiness'] in ('UNAVAILABLE','OBSERVATION_AVAILABILITY_UNKNOWN','OBSERVATION_PRECONDITION_UNRESOLVED') for x in v['nodes'] if x['kind']=='operation'):return done('WAITING_EXTERNAL_OPPORTUNITY')
        if snapshot.intent is not None and snapshot.intent.readiness.value=='STALE':return done('STALE_STATE_REQUIRES_REFRESH')
        return done('NO_KNOWN_SUPPORTED_ROUTE')


def execute_current(session,candidate):
    """Return only a real frontier member; the unchanged session repeats all checks."""
    start=perf_counter_ns();public=session.read();frontier=enumerate_work(public,session.limits)
    check=dict(public_binding=public.binding,candidate=wire(candidate),frontier_complete=frontier.complete,
               frontier_reason=frontier.reason,member=candidate in frontier.candidates,
               elapsed_ns=perf_counter_ns()-start)
    # Even stale/absent candidates reach the original rejection path, never a rewrite.
    result=session.execute(candidate)
    return result,check
