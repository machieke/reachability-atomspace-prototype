"""Matched public histories, candidates and certificates; explicit opaque fields."""
import json
from pathlib import Path
from reachability.trace_protocol import canonical
from experimental_online_pln.agenda import Snapshot,wire
from work_loop_lab.audit import equal
from .config import ARMS,folder

# Authority-generated identities are checked against actual SQLite/receipts in
# each run by the retained audit. Compare their full nonopaque content here.
OPAQUE={'pre_certificate_id','post_certificate_id','certificate_id','snapshot_digest','instance_id','request_fingerprint','request_id','intent_id','reservation_id','monitor_id','event_id','revision_id','fingerprint','basis','expected_binding','goal_fingerprint'}
def normal(value):
    if isinstance(value,dict):return {k:normal(v) for k,v in value.items() if k not in OPAQUE and not k.endswith('_ns')}
    if isinstance(value,(list,tuple)):
        if value and value[0]=='authority-identity/v1':return ['authority-identity/v1','<per-episode-authority>']
        return [normal(v) for v in value]
    return value

def semantics(row):
    choice=row['choice']
    return dict(public=normal(wire(Snapshot.from_records(row['public_records']))),tick=row['tick'],slot=row['slot'],frontier=normal(row['frontier']),selected=normal(row['selected']),result=normal(row.get('result')),calls=normal(row.get('calls',[])),after=row['after'],stop=row.get('stop'),budget=choice['budget'],eligible=normal(choice.get('eligible',[])),review=sorted([dict(producer=normal(r['producer']),status=r['status'],applications=len(r['applications'])) for r in choice.get('review',[])],key=canonical),review_complete=choice.get('review_complete'),pending_reports=choice.get('pending_reports'),selected_origin=choice.get('selected_origin'))

def divergence(a,b,path=''):
    if a==b:return None
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            found=divergence(a.get(k),b.get(k),path+'/'+k)
            if found:return found
    elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        for i,(x,y) in enumerate(zip(a,b)):
            found=divergence(x,y,path+'/'+str(i))
            if found:return found
    return dict(path=path,left=a,right=b)

def compare_pair(root,left,right):
    if any(r.get('conformance')!='PASS' for r in (left,right)):return dict(status='INCOMPLETE',parent=left['parent'],errors=[r.get('error') for r in (left,right)],scope='Retain failed trajectories; no successful parity claim')
    paths=[Path(root)/folder(r['sweep'],r['arm'],r['mode'],r['parent']) for r in (left,right)]
    rows=[[json.loads(l) for l in (p/'trace.jsonl').read_text().splitlines()] for p in paths]
    for i,(a,b) in enumerate(zip(*rows)):
        d=divergence(semantics(a),semantics(b))
        if d:return dict(status='MISMATCH',parent=left['parent'],earliest_row=i,tick=a['tick'],divergence=d)
    if len(rows[0])!=len(rows[1]):return dict(status='MISMATCH',parent=left['parent'],earliest_row=min(map(len,rows)),divergence=dict(path='row count',left=len(rows[0]),right=len(rows[1])))
    for key in ('metrics','selections','work','acquisitions','committed_depths','longest_dependency_path','dependency_reference','effects','stage'):
        d=divergence(left[key],right[key],key)
        if d:return dict(status='MISMATCH',parent=left['parent'],divergence=d)
    certs=[{k:sorted(normal(v),key=canonical) for k,v in json.loads((p/'authority-certificates.json').read_text()).items()} for p in paths]
    d=divergence(*certs)
    if d:return dict(status='MISMATCH',parent=left['parent'],divergence=d,scope='all persisted certificates')
    return dict(status='PASS',parent=left['parent'],rows=len(rows[0]),certificate_counts={k:len(v) for k,v in certs[0].items()},scope='whole public histories, complete frontiers, eligible priorities/ages, exact selections/inputs, calls/results, all certificate content, observed outcomes and budgets; per-authority identity checks retained independently')

def report(root,results):
    out=[]
    for left in results:
        if left['arm']!=ARMS[0]:continue
        right=next(r for r in results if r['arm']==ARMS[1] and r['parent']==left['parent']);out.append(compare_pair(root,left,right))
    return dict(status='PASS' if all(r['status']=='PASS' for r in out) else 'MISMATCH',parents=out,opaque_fields=sorted(OPAQUE))

def closed_loop_parity(root,report_data):
    d=report(root,report_data['results']);equal(d,json.loads((Path(root)/'parity.json').read_text()),'retained pair diagnostics');equal(d['status'],'PASS','matched histories: '+canonical(d));return len(d['parents'])
