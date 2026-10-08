"""Source/receipt and raw typed-answer checks, also used by focused mutations."""
from hashlib import sha256
from types import SimpleNamespace
from experimental_online_pln.agenda import Snapshot,wire
from experimental_native_recall.schema import Projection as FullProjection,source_id
from experimental_snapshot_payload.schema import Projection as CompactProjection
from reachability.atomspace_adapter import _hex
from work_loop_lab.audit import equal
from .reference import envelope,expected_graph,check_projection
from .payload import account


def check_row(row,arm):
    from .retrieval_audit import query_events
    public=Snapshot.from_records(row['public_records']);compact=arm=='MH-native-session-compact'
    p=(CompactProjection if compact else FullProjection)(public);g=expected_graph(p)
    if compact:check_projection(public,p,g)
    events=row['costs']['native_retrieval']['events'];counts=query_events(events,public)
    original=FullProjection(public) # Exact source records, independent of compact catalog.
    for event in events:
        if event['kind']=='open_view':
            r=event['receipt'];equal(r['schema'],'native-atomspace-recall/v1','legacy query receipt')
            equal(r['authority'],p.authority,'authority identity');equal(r['context_id'],p.context,'context')
            equal(r['source_ids'],sorted(original.catalog),'whole source inventory')
            equal(r['input_sha256'],sha256(p.wire()[0]).hexdigest(),'declared projection wire digest')
            equal(r['counts'],dict(atoms=g.size,relations=len(set(g.aliases[x] for x in p.relations)),values=len(g.values),source_records=len(original.catalog),load_bytes=len(p.wire()[0]),public_export_bytes=p.export_bytes),'declared projection counts')
            if compact:
                equal(r['projection_schema'],'native-atomspace-recall-compact/v1','projection declaration')
                equal(r['full_snapshot_envelope'],envelope(public),'independent external full capture envelope')
                equal(r['completeness'],dict(authoritative_capture=True,supported_discovery_universe=True,native_projection_readback=True,whole_snapshot_embedded=False),'separate completeness properties')
            else:equal(set(r),{'view_id','authority','context_id','snapshot_binding','schema','build_identity','complete','source_ids','counts','input_sha256','readback_sha256','runtime_generation_id'},'unchanged full receipt fields')
            measured=dict(row['costs']['payload']);measured.pop('accounting_ns')
            expected=account(p,g,SimpleNamespace(**r));expected.pop('accounting_ns');equal(measured,expected,'validated payload accounting')
            continue
        r=event['result'];request=r['request'];kind=request['kind'];raw=event['transport']['requests'][0].split();limits=request['limits']
        args=['Q',raw[1],_hex(public.binding),kind,str(limits['visits']),str(limits['results'])]
        def literal(value):
            st=value['statement'];return ['+' if value['positive'] else '-',_hex(st['predicate']),str(len(st['arguments'])),*map(_hex,st['arguments'])]
        if kind=='record':args.append(_hex(request['record_id']))
        else:
            args.append(_hex(request['context']))
            if kind=='probes':args.extend([request['report_type']]+(literal(request['target']) if request['report_type']=='numeric' else [_hex(request['target'])]))
            elif kind not in ('models','all_rules','all_current'):args.extend(literal(request['literal']))
        equal(event['transport']['requests'],[' '.join(args)+'\n'],'exact typed request arguments and limits')
        details=[]
        for ident,line in zip(r['ids'],event['transport']['response_lines'][1:-1]):
            tokens=line.split();source=original.catalog[ident][1]
            if kind=='record':
                equal(tokens,['D',_hex(ident),_hex(original.catalog[ident][2])],'complete native source payload');detail=None
            else:
                equal(tokens[:2],['I',_hex(ident)],'typed result identity');refs=tuple(map(int,tokens[3:]));equal(int(tokens[2]),len(refs),'detail arity')
                if kind in ('producers','all_rules'):
                    by_ref={g.aliases[ref]:lit for lit,ref in p.literal_refs.items()};detail=tuple(by_ref[ref] for ref in refs);equal(detail,source.deduction.premises,'native ordered five-premise source detail')
                elif kind=='models':
                    detail=tuple(g.atoms[ref][1].removeprefix('record:') for ref in refs);equal(detail,tuple(source_id('support',request['context'],i) for i in source.premise_revision_ids),'exact native model inputs')
                elif kind=='probes':
                    equal(len(refs),1,'opportunity arity');detail=g.atoms[refs[0]][1];equal(detail,'integer:'+str(source.opportunity),'native opportunity identity')
                else:equal(refs,(),'no unexpected native detail');detail=None
            details.append(wire(detail))
        equal(r['details'],details,'decoded actual native typed details')
    return counts
