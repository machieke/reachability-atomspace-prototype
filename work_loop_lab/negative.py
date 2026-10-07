"""Isolated sealed-package mutations; published records are never rewritten."""
import argparse,json,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from validation_lab.decision_comparison import write,seal
from reachability.trace_protocol import canonical
from .audit import audit


def run(directory,allow_dirty=False):
    outcomes=[]
    for mutation in ('unsealed','missing-AND','skipped-review','changed-selected-tuple','hidden-objection','stale-accepted','invented-relief','removed-adoption'):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'comparison';shutil.copytree(directory,dest)
            name='finite-adverse' if mutation=='hidden-objection' else 'finite-freshness' if mutation=='stale-accepted' else 'finite-positive'
            path=dest/name/'trace.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()]
            if mutation=='unsealed':rows[0]['view']['complete']=False
            elif mutation=='missing-AND':rows[0]['view']['edges'].remove(next(e for e in rows[0]['view']['edges'] if e['type']=='AND_PREREQUISITE'))
            elif mutation=='skipped-review':rows[0]['choice']['review_complete']=True
            elif mutation=='changed-selected-tuple':rows[0]['selected']['premise_ids'].reverse()
            elif mutation=='hidden-objection':rows[-1]['view']['global_blockers']=[b for b in rows[-1]['view']['global_blockers'] if b['category']!='OBJECTION_REQUIRES_REVIEW']
            elif mutation=='stale-accepted':next(r for r in rows if r.get('result',{}).get('status')=='STALE')['result']['status']='PASS'
            elif mutation=='invented-relief':rows[0]['before_environment']['outstanding']=0
            elif mutation=='removed-adoption':rows.remove(next(r for r in rows if r['selected'] and r['selected']['kind']=='adopt'))
            path.write_text(''.join(canonical(r)+'\n' for r in rows))
            if mutation!='unsealed':seal(dest)
            try:audit(dest,allow_dirty)
            except (ValueError,AssertionError,KeyError) as error:outcomes.append(dict(mutation=mutation,rejected=True,reason=str(error)))
            else:raise AssertionError('mutation accepted: '+mutation)
    return dict(status='PASS',cases=outcomes)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();r=run(a.directory,a.allow_dirty);write(a.output,r);print(json.dumps(r,indent=2))

if __name__=='__main__':main()
