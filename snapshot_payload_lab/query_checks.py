"""All typed forms, source expectations and actual full/compact query comparison."""
from experimental_native_recall.schema import QueryLimits,record_payload,source_id
from experimental_native_recall.backend import _unhex
from native_recall_lab.reference import answers,queries
from reachability.model import Literal,Statement
from .reference import result_semantics,check_projection


def requests(snapshot):
    yield from queries(snapshot)
    for r in snapshot.rules:yield 'record',dict(record_id=source_id('rule',snapshot.context.context_id,(r.rule_id,r.revision)))
    for q in snapshot.numerical:
        for b in q.historical:yield 'record',dict(record_id=source_id('support',snapshot.context.context_id,b.belief_revision_id))
    for r in snapshot.reports:yield 'record',dict(record_id=source_id('report',snapshot.context.context_id,r.evidence.evidence_id))
    for p in snapshot.probes:yield 'record',dict(record_id=source_id('probe',snapshot.context.context_id,(p.probe_id,p.opportunity)))
    for m in snapshot.models:yield 'record',dict(record_id=source_id('model',snapshot.context.context_id,m.model_id))
    yield 'record',dict(record_id='absent-record')
    for kind in ('producers','current','historical','reports'):yield kind,dict(context=snapshot.context.context_id,literal=Literal(Statement('absent-literal')))
    yield 'probes',dict(context=snapshot.context.context_id,report_type='product',target='absent-product')
    for kind in ('models','all_rules','all_current'):yield kind,dict(context='absent-context')


def check(full,compact,snapshot,boundaries=True):
    receipts=[b.open_view(snapshot) for b in (full,compact)];check_projection(snapshot,compact.projection,compact.graph)
    cases=[];limits=[QueryLimits()]
    if boundaries:limits.extend((QueryLimits(visits=0),QueryLimits(results=0),QueryLimits(visits=1),QueryLimits(results=1),QueryLimits(queries=0)))
    for kind,args in requests(snapshot):
        expected=answers(snapshot,kind,**args)
        for limit in limits:
            pair=[b.query(kind,binding=snapshot.binding,limits=limit,**args) for b in (full,compact)]
            a,b=map(result_semantics,pair)
            if a!=b:raise AssertionError(('native full/compact query differs',kind,args,limit,a,b))
            if pair[0].complete and pair[0].ids!=expected:raise AssertionError('independent source membership: '+kind)
            if kind=='record' and pair[0].complete and pair[0].ids:
                ident=pair[0].ids[0];want=record_payload(full.projection.catalog[ident][1])[0]
                for backend in (full,compact):
                    line=backend.events[-1]['transport']['response_lines'][1]
                    if _unhex(line.split()[2])!=want:raise AssertionError('actual native record payload fidelity')
            cases.append(dict(kind=kind,request=a['request'],complete=a['complete'],reason=a['reason'],visits=a['visits'],ids=a['ids'],details=a['details']))
    return dict(status='PASS',cases=cases,query_pairs=len(cases),kinds=sorted({x['kind'] for x in cases}))
