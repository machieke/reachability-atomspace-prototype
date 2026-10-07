"""Independent source query checks and separately counted native reexecution."""
import json
from hashlib import sha256
from pathlib import Path
from experimental_online_pln.agenda import Snapshot,wire
from experimental_work_bridge.capture import detached
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import evaluate
from experimental_native_multihop.access import Access
from experimental_native_multihop.backend import RecordedBackend
from experimental_native_multihop.project import project
from native_recall_lab.reference import answers
from native_recall_lab.compare import request_args
from multihop_lab.cases import manifest
from work_loop_lab.audit import equal


def query_events(events,public):
    counts=dict(recorded_query_answers=0,recorded_native_query_invocations=0,query_request_bytes=0,query_response_bytes=0)
    for event in events:
        if event['kind']=='open_view':
            r=event['receipt'];equal(r['snapshot_binding'],public.binding,'native epoch binding');equal(r['view_id'],public.binding,'native view identity');equal(r['complete'],True,'native complete view')
        elif event['kind']=='query':
            r=event['result'];equal(r['view_id'],public.binding,'native response epoch');equal(r['complete'],True,'nonexhausted core query')
            expected=answers(public,r['request']['kind'],**request_args(r['request']));equal(r['ids'],list(expected),'independent native query membership')
            transport=event['transport'];requests=transport['requests'];lines=transport['response_lines'];equal(len(requests),1,'actual query request');equal(len(lines),len(r['ids'])+2,'native reply length')
            request_tokens=requests[0].split();header=lines[0].split();equal(request_tokens[0],'Q','typed query command');equal(bytes.fromhex(request_tokens[2]).decode(),public.binding,'wire binding');equal(request_tokens[3],r['request']['kind'],'wire query form')
            equal(header[:4],['QRESULT',request_tokens[1],'COMPLETE','COMPLETE'],'wire query header');equal(int(header[4]),r['visits'],'wire relation visits');equal(int(header[5]),len(r['ids']),'wire result count');equal(lines[-1],'END '+request_tokens[1],'wire query seal')
            equal([bytes.fromhex(x.split()[1]).decode() for x in lines[1:-1]],r['ids'],'raw result identities')
            equal(sha256(('\n'.join(lines)+'\n').encode()).hexdigest(),event['response_sha256'],'raw query checksum')
            equal(transport['request_bytes'],sum(len(x.encode()) for x in requests),'query request byte count');equal(transport['response_bytes'],sum(len(x.encode())+1 for x in lines),'query response byte count')
            counts['recorded_query_answers']+=1;counts['recorded_native_query_invocations']+=1
            for k in ('query_request_bytes','query_response_bytes'):counts[k]+=transport[k.removeprefix('query_')]
        else:raise AssertionError('unexpected core native event: '+event['kind'])
    return counts


def stable(event):
    event=json.loads(json.dumps(event))
    if event['kind']=='query':event['result'].pop('elapsed_ns')
    return event


def audit_retrieval(root,report,reexecute=True):
    counts=dict(native_rows=0,native_epochs=0,recorded_query_answers=0,recorded_native_query_invocations=0,
        query_request_bytes=0,query_response_bytes=0,native_query_reexecutions=0,matched_native_graph_reexecutions=0)
    for result in report['results']:
        if result['arm']!='MH-native':continue
        path=Path(root)/(result['arm']+'-'+result['mode']+'-'+result['parent']);m=manifest(result['parent']);backend=RecordedBackend();all_events=[]
        try:
            for row in map(json.loads,(path/'trace.jsonl').read_text().splitlines()):
                public=Snapshot.from_records(row['public_records']);recorded=row['costs']['native_retrieval'];events=recorded['events'];all_events.extend(events)
                equal(recorded['binding'],public.binding,'retrieval input binding');equal(recorded['complete'],True,'complete core discovery');equal(recorded['fallback'],None,'no scan fallback')
                for k,v in query_events(events,public).items():counts[k]+=v
                counts['native_rows']+=1;counts['native_epochs']+=sum(e['kind']=='open_view' for e in events)
                if reexecute:
                    start=len(backend.events);frame=detached(row['frame']);cap=immutable(frame.data()['capture']);ab={k:evaluate(cap,m,k)[0] for k in ('A','B')};access=Access(backend,public)
                    view,_=project(frame,m,ab['A'],ab['B'],access)
                    equal(view.data(),row['view'],'reexecuted native graph');fresh=backend.events[start:]
                    equal([stable(e) for e in fresh],[stable(e) for e in events],'fresh native query transport and view receipts')
                    equal(access.reports,recorded['queried_reports'],'report discovery receipt')
                    counts['native_query_reexecutions']+=sum(e['kind']=='query' for e in fresh);counts['matched_native_graph_reexecutions']+=1
            equal(all_events,json.loads((path/'native-events.json').read_text()),'whole episode native receipt inventory')
            equal(sum(e['kind']=='open_view' for e in all_events),result['native_epochs'],'recorded cold epochs')
            equal(sum(e['kind']=='query' for e in all_events),result['native_costs']['native_queries'],'recorded helper query calls')
        finally:backend.close()
    return counts


def closed_loop_parity(root,report):
    pairs=0
    for result in report['results']:
        if result['arm']!='MH-scan':continue
        mode,parent=result['mode'],result['parent'];other=next(r for r in report['results'] if (r['arm'],r['mode'],r['parent'])==('MH-native',mode,parent))
        def sequence(arm):
            path=Path(root)/(arm+'-'+mode+'-'+parent)/'trace.jsonl';out=[]
            for row in map(json.loads,path.read_text().splitlines()):
                c=row['selected']
                if c:c={k:v for k,v in c.items() if k not in ('basis','expected_binding')}
                # Different authorities issue different opaque binding/certificate
                # IDs. Exact bindings already replayed within each authority.
                out.append(dict(tick=row['tick'],slot=row['slot'],selected=c,status=row.get('result',{}).get('status'),after=row['after'],stop=row.get('stop'),budget=row['choice']['budget']))
            return out
        equal(sequence('MH-scan'),sequence('MH-native'),'closed-loop exact selected premises, responses, observations, budgets and stops')
        for k in ('metrics','selections','work','acquisitions','committed_depths','longest_dependency_path','dependency_reference','effects','stage'):
            equal(result[k],other[k],'closed-loop '+k)
        pairs+=1
    return pairs
