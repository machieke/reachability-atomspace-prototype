"""Independent brute-force source scans. Never reads projected AtomSpace links."""
from experimental_native_recall.schema import source_id


def answers(snapshot,kind,*,context=None,literal=None,report_type=None,target=None,record_id=None):
    ctx=snapshot.context.context_id
    if context!=ctx and kind!='record':return ()
    result=[]
    if kind in ('producers','all_rules'):
        result=[source_id('rule',ctx,(r.rule_id,r.revision)) for r in snapshot.rules
                if kind=='all_rules' or r.deduction.conclusion==literal]
    elif kind in ('current','historical','all_current'):
        for view in snapshot.numerical:
            for b in (view.historical if kind=='historical' else view.current):
                if kind=='all_current' or b.proposal.support.conclusion==literal:
                    result.append(source_id('support',ctx,b.belief_revision_id))
    elif kind=='reports':
        result=[source_id('report',ctx,r.evidence.evidence_id) for r in snapshot.reports if r.evidence.content==literal]
    elif kind=='probes':
        result=[source_id('probe',ctx,(p.probe_id,p.opportunity)) for p in snapshot.probes if (p.report_type,p.target)==(report_type,target)]
    elif kind=='models':result=[source_id('model',ctx,m.model_id) for m in snapshot.models]
    elif kind=='record':
        candidates=[]
        candidates.extend(source_id('rule',ctx,(r.rule_id,r.revision)) for r in snapshot.rules)
        candidates.extend(source_id('support',ctx,b.belief_revision_id) for v in snapshot.numerical for b in v.historical)
        candidates.extend(source_id('report',ctx,r.evidence.evidence_id) for r in snapshot.reports)
        candidates.extend(source_id('probe',ctx,(p.probe_id,p.opportunity)) for p in snapshot.probes)
        candidates.extend(source_id('model',ctx,m.model_id) for m in snapshot.models)
        result=[record_id] if record_id in candidates else []
    else:raise ValueError('unknown reference query')
    return tuple(sorted(set(result)))


def queries(snapshot):
    ctx=snapshot.context.context_id
    literals={c.conclusion for c in snapshot.decision.contract.criteria}
    literals|={lit.negate() for lit in tuple(literals)}
    for r in snapshot.rules:literals.update((r.deduction.conclusion,*r.deduction.premises))
    for v in snapshot.numerical:literals.add(v.conclusion)
    for r in snapshot.reports:literals.add(r.evidence.content)
    from experimental_goal_pln.relevance import key
    for literal in sorted(literals,key=key):
        for kind in ('producers','current','historical','reports'):
            yield kind,dict(context=ctx,literal=literal)
    for probe in snapshot.probes:yield 'probes',dict(context=ctx,report_type=probe.report_type,target=probe.target)
    for kind in ('models','all_rules','all_current'):yield kind,dict(context=ctx)


def check(backend,snapshot):
    receipt=backend.open_view(snapshot);count=0
    for kind,args in queries(snapshot):
        result=backend.query(kind,binding=receipt.snapshot_binding,**args)
        expected=answers(snapshot,kind,**args)
        if not result.complete or result.ids!=expected:raise AssertionError('native/reference query differs: '+kind)
        count+=1
    for ident in receipt.source_ids:
        result=backend.query('record',binding=receipt.snapshot_binding,record_id=ident)
        if result.ids!=(ident,) or not result.complete:raise AssertionError('exact native record readback differs')
        count+=1
    return count
