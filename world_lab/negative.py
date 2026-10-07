"""Existing isolated copy/reseal mutation pattern; originals remain untouched."""
import argparse,json,shutil
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from experimental_online_pln.agenda import Snapshot
from reachability.trace_protocol import canonical
from validation_lab.decision_comparison import write,seal
from .audit import audit


def run(directory,allow_dirty=False):
    outcomes=[]
    names=('unsealed','observation-creates-product','observation-creates-health',
           'world-relief-from-controller','hidden-truth-authority-input',
           'adverse-observation-rewritten','invented-executor-receipt','duplicate-effect')
    for mutation in names:
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'comparison';shutil.copytree(directory,dest)
            name='finite-early-failure' if mutation=='adverse-observation-rewritten' else 'finite-unobservable' if mutation=='world-relief-from-controller' else 'finite-observable'
            private_path=dest/name/'private.json';private=json.loads(private_path.read_text())
            if mutation in ('observation-creates-product','observation-creates-health'):
                key,value=('installed','artifact-v2') if mutation.endswith('product') else ('healthy',True)
                private['measurements'][0]['physical_after'][key]=value
            elif mutation=='adverse-observation-rewritten':
                m=next(m for m in private['measurements'] if m['sample'] and m['sample']['channel']=='health')
                m['response']['events'][0][1]['healthy']=True
            elif mutation=='invented-executor-receipt':private['state']['accepted'][0]['receipt']['effect_count']=0
            elif mutation=='duplicate-effect':private['state']['accepted'].append(private['state']['accepted'][0])
            elif mutation=='world-relief-from-controller':
                path=dest/name/'result.json';result=json.loads(path.read_text());result['metrics']['J_world']=result['metrics']['J_certified'];write(path,result)
                path=dest/'report.json';report=json.loads(path.read_text());report['results']=[result if r['mode']=='finite' and r['parent']=='unobservable' else r for r in report['results']];write(path,report)
            else:
                path=dest/name/'trace.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()]
                if mutation=='unsealed':rows[0]['tick']=999
                else:
                    public=Snapshot.from_records(rows[0]['public_records'])
                    public=replace(public,received=public.received+({'kind':'hidden-world','goal_deficit':0},))
                    rows[0]['public_records']=public.records();rows[0]['public_binding']=public.binding
                path.write_text(''.join(canonical(r)+'\n' for r in rows))
            write(private_path,private)
            if mutation!='unsealed':seal(dest)
            try:audit(dest,allow_dirty)
            except (ValueError,AssertionError,KeyError) as error:outcomes.append(dict(mutation=mutation,rejected=True,reason=str(error)))
            else:raise AssertionError('mutation accepted: '+mutation)
    return dict(status='PASS',cases=outcomes)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();result=run(a.directory,a.allow_dirty);write(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
