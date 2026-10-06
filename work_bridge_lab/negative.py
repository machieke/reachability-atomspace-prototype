"""Isolated bundle mutations; measured evidence is never rewritten."""
import argparse,json,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from validation_lab.decision_comparison import write,seal
from .audit import audit


def run(directory,allow_dirty=False):
    cases=[]
    for mutation in ('unsealed','missing-AND','duplicate-obligation','hidden-objection','hidden-live-block','invented-relief','missing-route','changed-inventory'):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'comparison';shutil.copytree(directory,dest)
            name='finite-method-gap/registered.primary.json'
            if mutation=='hidden-objection':name='finite-objection/derived.primary.json'
            if mutation=='hidden-live-block':name='finite-optional-weak/after.primary.json'
            p=dest/name;d=json.loads(p.read_text());v=d['view']
            if mutation=='unsealed':v['complete']=False
            elif mutation=='missing-AND':v['edges'].remove(next(e for e in v['edges'] if e['type']=='AND_PREREQUISITE'))
            elif mutation=='duplicate-obligation':v['obligations'].append(v['obligations'][0])
            elif mutation=='hidden-objection':v['global_blockers']=[b for b in v['global_blockers'] if b['category']!='OBJECTION_REQUIRES_REVIEW']
            elif mutation=='hidden-live-block':v['global_blockers']=[b for b in v['global_blockers'] if b['category']!='LIVE_POLICY_BLOCK']
            elif mutation=='invented-relief':v['observed']['goal']['projection']['outstanding_loss']=0
            elif mutation=='missing-route':v['nodes']=[n for n in v['nodes'] if n['kind']!='operation']
            elif mutation=='changed-inventory':
                q=dest/d['input_file'];f=json.loads(q.read_text());f['inventory']['models']=[];write(q,f)
            write(p,d)
            if mutation!='unsealed':seal(dest)
            try:audit(dest,allow_dirty)
            except (ValueError,AssertionError) as error:cases.append(dict(mutation=mutation,rejected=True,reason=str(error)))
            else:raise AssertionError('accepted '+mutation)
    return dict(status='PASS',cases=cases)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);a=p.parse_args();result=run(a.directory);write(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
