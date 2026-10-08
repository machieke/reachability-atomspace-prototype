"""Independent source query checks and separately counted native reexecution."""
import json
from hashlib import sha256
from pathlib import Path
from experimental_online_pln.agenda import Snapshot,wire
from experimental_work_bridge.capture import detached
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import evaluate
from experimental_native_multihop.access import Access
from experimental_runtime_lifetime.backend import Backend as RecordedBackend
from experimental_native_multihop.project import project
from native_recall_lab.reference import answers
from native_recall_lab.compare import request_args
from multihop_lab.cases import manifest
from work_loop_lab.audit import equal
from .config import ARMS,folder
from runtime_lifetime_lab.generation_audit import check_generation


def query_events(events,public):
    binding=public.binding
    counts=dict(recorded_query_answers=0,recorded_native_query_invocations=0,query_request_bytes=0,query_response_bytes=0)
    for event in events:
        if event['kind']=='open_view':
            r=event['receipt'];equal(r['snapshot_binding'],binding,'native epoch binding');equal(r['view_id'],binding,'native view identity');equal(r['complete'],True,'native complete view')
        elif event['kind']=='query':
            r=event['result'];equal(r['view_id'],binding,'native response epoch');equal(r['complete'],True,'nonexhausted core query')
            expected=answers(public,r['request']['kind'],**request_args(r['request']));equal(r['ids'],list(expected),'independent native query membership')
            transport=event['transport'];requests=transport['requests'];lines=transport['response_lines'];equal(len(requests),1,'actual query request');equal(len(lines),len(r['ids'])+2,'native reply length')
            request_tokens=requests[0].split();header=lines[0].split();equal(request_tokens[0],'Q','typed query command');equal(bytes.fromhex(request_tokens[2]).decode(),binding,'wire binding');equal(request_tokens[3],r['request']['kind'],'wire query form')
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
    if event['kind']=='open_view':event['receipt'].pop('runtime_generation_id',None)
    return event


def semantic(event):
    if event['kind']=='open_view':return dict(kind='open_view',binding=event['receipt']['snapshot_binding'],source_ids=event['receipt']['source_ids'])
    r=dict(event['result']);r.pop('elapsed_ns');return dict(kind='query',result=r)


def audit_retrieval(root,report,reexecute=True):
    counts=dict(native_rows=0,native_epochs=0,recorded_query_answers=0,recorded_native_query_invocations=0,
        query_request_bytes=0,query_response_bytes=0,native_query_reexecutions=0,matched_native_graph_reexecutions=0,recorded_generation_checks=0,recorded_launch_mapping_checks=0,fresh_generation_integrity_checks_during_replay=0,fresh_session_preparations=0)
    for result in report['results']:
        if result['arm']=='MH-scan':continue
        path=Path(root)/folder(result['sweep'],result['arm'],result['mode'],result['parent']);m=manifest(result['parent']);backend=RecordedBackend();all_events=[]
        try:
            for row in map(json.loads,(path/'trace.jsonl').read_text().splitlines()):
                public=Snapshot.from_records(row['public_records']);recorded=row['costs']['native_retrieval'];events=recorded['events'];all_events.extend(events)
                equal(recorded['binding'],public.binding,'retrieval input binding');equal(recorded['complete'],True,'complete core discovery');equal(recorded['fallback'],None,'no scan fallback')
                from .row_audit import check_row
                for k,v in check_row(row,result['arm']).items():counts[k]+=v
                counts['native_rows']+=1;counts['native_epochs']+=sum(e['kind']=='open_view' for e in events)
                if reexecute:
                    start=len(backend.events);frame=detached(row['frame']);cap=immutable(frame.data()['capture']);ab={k:evaluate(cap,m,k)[0] for k in ('A','B')};access=Access(backend,public)
                    view,_=project(frame,m,ab['A'],ab['B'],access)
                    equal(view.data(),row['view'],'reexecuted native graph');fresh=backend.events[start:]
                    equal([semantic(e) for e in fresh],[semantic(e) for e in events],'fresh full-native typed query semantics')
                    equal(access.reports,recorded['queried_reports'],'report discovery receipt')
                    pass # Both recorded projections are checked against fresh frozen full views.
                    counts['native_query_reexecutions']+=sum(e['kind']=='query' for e in fresh);counts['matched_native_graph_reexecutions']+=1
            equal(all_events,json.loads((path/'native-events.json').read_text()),'whole episode native receipt inventory')
            equal(sum(e['kind']=='open_view' for e in all_events),result['native_epochs'],'recorded cold epochs')
            equal(sum(e['kind']=='query' for e in all_events),result['native_costs']['native_queries'],'recorded helper query calls')
            if result['arm']!='MH-scan':
                for k,v in check_generation(path,result,all_events).items():counts[k]+=v
        finally:
            counts['fresh_session_preparations']+=backend.runtime_costs().get('preparations',0)
            backend.shutdown()
    return counts


def closed_loop_parity(root,report):
    pairs=0
    def sequence(result):
        path=Path(root)/folder(result['sweep'],result['arm'],result['mode'],result['parent'])/'trace.jsonl';out=[]
        for row in map(json.loads,path.read_text().splitlines()):
            c=row['selected']
            if c:c={k:v for k,v in c.items() if k not in ('basis','expected_binding')}
            out.append(dict(tick=row['tick'],slot=row['slot'],selected=c,status=row.get('result',{}).get('status'),after=row['after'],stop=row.get('stop'),budget=row['choice']['budget']))
        return out
    for result in report['results']:
        if result['arm']!='MH-scan':continue
        mode,parent,sweep=result['mode'],result['parent'],result['sweep']
        baseline=sequence(result)
        for arm in ARMS[1:]:
            other=next(r for r in report['results'] if (r['arm'],r['mode'],r['parent'],r['sweep'])==(arm,mode,parent,sweep))
            equal(baseline,sequence(other),'closed-loop exact selections, responses, observations, budgets and stops')
            for k in ('metrics','selections','work','acquisitions','committed_depths','longest_dependency_path','dependency_reference','effects','stage'):
                equal(result[k],other[k],'closed-loop '+k)
            pairs+=1
        strict=next(r for r in report['results'] if (r['arm'],r['mode'],r['parent'],r['sweep'])==('MH-native-session-full',mode,parent,sweep))
        session=next(r for r in report['results'] if (r['arm'],r['mode'],r['parent'],r['sweep'])==('MH-native-session-compact',mode,parent,sweep))
        for k in ('native_epochs',):equal(strict[k],session[k],'same cold view counts')
        for k in ('native_queries','native_relation_visits','native_results','query_request_bytes'):
            equal(strict['native_costs'][k],session['native_costs'][k],'same native query sequence/count '+k)
    # Repeated sweeps must reproduce exact nonopaque task behavior as well.
    for result in report['results']:
        if result['sweep']!=0:continue
        other=next(r for r in report['results'] if (r['arm'],r['mode'],r['parent'],r['sweep'])==(result['arm'],result['mode'],result['parent'],1))
        equal(sequence(result),sequence(other),'repeat-sweep semantics')
    return pairs
