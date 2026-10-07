"""Narrow altered-copy witnesses using the existing seal/replay mechanism."""
import argparse,json,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from reachability.trace_protocol import canonical
from validation_lab.decision_comparison import write,seal
from .audit import audit


def run(directory,allow_dirty=False):
    outcomes=[]
    for mutation in ('unsealed','phantom-intermediate','wrong-premise-order','copied-root-as-independent','stale-descendant-accepted','hidden-adverse-estimate','partial-depth-review-complete','inference-as-physical-relief','replay-as-fresh-native','native-query-omission','native-wrong-epoch','native-raw-response','native-fallback-label','generation-identity','generation-mapped-digest','generation-retry-erasure','generation-view-binding'):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'comparison';shutil.copytree(directory,dest)
            name='finite-replacement' if mutation=='stale-descendant-accepted' else 'finite-adverse' if mutation=='hidden-adverse-estimate' else 'native-two-hop' if mutation=='replay-as-fresh-native' else 'finite-two-hop'
            name='s0-MH-scan-'+name
            if mutation.startswith('native-'):name='s0-MH-native-strict-finite-two-hop'
            if mutation.startswith('generation-'):name='s0-MH-native-session-finite-two-hop'
            path=dest/name/'trace.jsonl';rows=list(map(json.loads,path.read_text().splitlines()))
            if mutation.startswith('generation-'):
                p=dest/name/'runtime-events.json';events=json.loads(p.read_text())
                if mutation=='generation-identity':events[0]['descriptor']['generation_id']='unknown-generation'
                elif mutation=='generation-mapped-digest':next(e for e in events if e['kind']=='launch')['covered_mappings'][0]['sha256']='0'*64
                elif mutation=='generation-retry-erasure':
                    q=dest/name/'runtime-attempts.json';attempts=json.loads(q.read_text());attempts.append(dict(state='failed',costs=dict(preparations=1),events=[]));write(q,attempts)
                else:
                    next(e for e in rows[0]['costs']['native_retrieval']['events'] if e['kind']=='open_view')['receipt']['runtime_generation_id']='unknown-generation'
                write(p,events)
                if mutation!='generation-retry-erasure':
                    q=dest/name/'runtime-attempts.json';attempts=json.loads(q.read_text());attempts[0]['events']=events;write(q,attempts)
            elif mutation.startswith('native-'):
                diag=rows[0]['costs']['native_retrieval']
                event=next(e for e in diag['events'] if e['kind']=='query' and e['result']['ids'])
                if mutation=='native-query-omission':event['result']['ids']=[];event['result']['details']=[]
                elif mutation=='native-wrong-epoch':event['result']['view_id']='old-epoch'
                elif mutation=='native-raw-response':event['transport']['response_lines'][0]='forged-header'
                else:diag['fallback']='successful-scan'
            elif mutation=='unsealed':rows[0]['tick']=999
            elif mutation=='phantom-intermediate':next(r for r in rows if r['selected'] and r['selected']['target']=='r-final')['selected']['premise_ids'][3]='invented-estimate'
            elif mutation=='wrong-premise-order':next(r for r in rows if r['selected'] and r['selected']['target']=='r-final')['selected']['premise_ids'].reverse()
            elif mutation=='copied-root-as-independent':
                row=next(r for r in rows if r['selected'] and r['selected']['target']=='r-final');row['result']['commit']['belief']['proposal']['support']['lineage_roots']=['invented-independent-root']
            elif mutation=='stale-descendant-accepted':
                p=dest/name/'changes.json';changes=json.loads(p.read_text());e=changes[0];old=next(b for q in e['before']['numerical'] for b in q['current'] if b['transition']['rule_id']=='r-mid');target=next(q for q in e['after']['numerical'] if q['conclusion']==old['proposal']['support']['conclusion']);target['current'].append(old);write(p,changes)
            elif mutation=='hidden-adverse-estimate':
                row=next(r for r in rows if any(b['category']=='OBJECTION_REQUIRES_REVIEW' for b in r['view']['global_blockers']));row['view']['global_blockers']=[b for b in row['view']['global_blockers'] if b['category']!='OBJECTION_REQUIRES_REVIEW'];row['view']['A']['records']=[b for b in row['view']['A']['records'] if b['disposition']!='strength_objection']
            elif mutation=='partial-depth-review-complete':
                rows[0]['view']['nodes']=[n for n in rows[0]['view']['nodes'] if n['kind']!='producer-template'];rows[0]['choice']['review_complete']=True
            elif mutation=='inference-as-physical-relief':next(r for r in rows if r['selected'] and r['selected']['kind']=='deduction')['before_environment']['outstanding']=0
            else:
                p=dest/name/'result.json';result=json.loads(p.read_text());result['reconstruction']['native_calls_after']+=1;write(p,result);p=dest/'report.json';report=json.loads(p.read_text());report['results']=[result if r['sweep']==0 and r['arm']=='MH-scan' and r['parent']=='two-hop' and r['mode']=='native' else r for r in report['results']];write(p,report)
            path.write_text(''.join(canonical(r)+'\n' for r in rows))
            if mutation!='unsealed':seal(dest)
            try:audit(dest,allow_dirty,reexecute=False)
            except (ValueError,AssertionError,KeyError) as error:outcomes.append(dict(mutation=mutation,rejected=True,reason=str(error)))
            else:raise AssertionError('mutation accepted: '+mutation)
    return dict(status='PASS',cases=outcomes)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();r=run(a.directory,a.allow_dirty);write(a.output,r);print(json.dumps(r,indent=2))

if __name__=='__main__':main()
