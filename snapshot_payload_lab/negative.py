"""Resealed altered-copy row witnesses against the complete audit's row checker.

This is targeted projection/envelope evidence, not 17 reruns of the historical
whole-cohort runtime mutation suite. No actual source or build is modified.
"""
import argparse,copy,json,tempfile
from pathlib import Path
from hashlib import sha256
from reachability.trace_protocol import canonical
from validation_lab.decision_comparison import write,seal
from .row_audit import check_row
from .config import folder


def run(root):
    root=Path(root);report=json.loads((root/'report.json').read_text());result=next(r for r in report['results'] if r['arm']=='MH-native-session-compact')
    rows=[json.loads(x) for x in (root/folder(result['sweep'],result['arm'],result['mode'],result['parent'])/'trace.jsonl').read_text().splitlines()];row=rows[0]
    check_row(row,result['arm']);out=[]
    def receipt(r):return next(e['receipt'] for e in r['costs']['native_retrieval']['events'] if e['kind']=='open_view')
    mutations=[]
    for k,v in [('snapshot_sha256','0'*64),('snapshot_bytes',1),('snapshot_binding','stale'),('projection_schema','native-atomspace-recall/v1'),('snapshot_representation','embedded')]:
        mutations.append((k,lambda r,k=k,v=v:receipt(r)['full_snapshot_envelope'].__setitem__(k,v)))
    mutations.extend([
        ('projection-declaration',lambda r:receipt(r).__setitem__('projection_schema','wrong')),
        ('embedded-claim',lambda r:receipt(r)['completeness'].__setitem__('whole_snapshot_embedded',True)),
        ('source-omission',lambda r:receipt(r)['source_ids'].pop()),
        ('wire-digest',lambda r:receipt(r).__setitem__('input_sha256','0'*64)),
        ('readback-byte-accounting',lambda r:r['costs']['payload'].__setitem__('native_readback_wire_bytes',1)),
        ('raw-ordered-premise',tamper_detail),
    ])
    for name,change in mutations:
        altered=copy.deepcopy(row);change(altered)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);write(path/'row.json',altered);write(path/'sources.json',report['sources']);seal(path)
            sealed=json.loads((path/'bundle.json').read_text());fresh=json.loads((path/'row.json').read_text())
            try:check_row(fresh,result['arm'])
            except (AssertionError,ValueError,KeyError,IndexError) as error:
                out.append(dict(name=name,status='REJECTED',error=str(error),sealed_files=sealed['files']))
            else:raise AssertionError('mutation accepted: '+name)
    return dict(status='PASS',source=report['sources'],normal_control='PASS',mutations=out,scope='Focused resealed row source/projection/raw-query checks used by complete audit; historical full-cohort runtime mutations not repeated.')


def tamper_detail(row):
    events=row['costs']['native_retrieval']['events'];e=next(e for e in events if e['kind']=='query' and e['result']['request']['kind'] in ('producers','all_rules') and e['result']['ids'])
    lines=e['transport']['response_lines'];t=lines[1].split();t[3],t[4]=t[4],t[3];lines[1]=' '.join(t)
    e['response_sha256']=sha256(('\n'.join(lines)+'\n').encode()).hexdigest();e['transport']['response_bytes']=sum(len(x.encode())+1 for x in lines)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--output',required=True);a=p.parse_args();out=run(a.root);write(a.output,out);print(json.dumps(dict(status=out['status'],rejected=len(out['mutations']))))
