"""Separate diagnostic mutations; never modify the measured bundle."""
import argparse,json,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from validation_lab.decision_comparison import write,seal
from .audit import audit


def run(directory,allow_dirty=False):
    results=[]
    for mutation in ('unsealed-output','resealed-output','resealed-witness','changed-role','omitted-record','dropped-pair'):
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/'comparison';shutil.copytree(directory,target)
            file=target/'finite-weak-augmented/after.alternatives.json';data=json.loads(file.read_text())
            if mutation in ('unsealed-output','resealed-output'):data['assessments']['B']['status']='FAIL'
            elif mutation=='resealed-witness':data['assessments']['B']['obligations'][0]['witnesses']=[]
            elif mutation=='changed-role':data['manifest']['obligations'][0]['mode']='all'
            elif mutation=='omitted-record':data['assessments']['B']['records'].pop()
            elif mutation=='dropped-pair':
                path=target/'report.json';report=json.loads(path.read_text());report['index'].remove(str(file.relative_to(target)));report['assessment_pairs']-=1;write(path,report)
            write(file,data)
            if mutation!='unsealed-output':seal(target)
            try:audit(target,allow_dirty)
            except (ValueError,AssertionError) as error:results.append(dict(mutation=mutation,rejected=True,reason=str(error)))
            else:raise AssertionError('audit accepted '+mutation)
    return dict(status='PASS',cases=results)


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);a=p.parse_args();result=run(a.directory);write(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
