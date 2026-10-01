"""Pin existing development commands for independent process-boundary replay."""
import json
from .run_public_workers import ROOT, CORPUS, source_paths
from .public_worker import write_json
from .shrink_replay import digest_file


def scenarios():
    cases=[]
    for profile,folder,names in (
        ('admission','admission_cases',('a01','a05','a09','a14')),
        ('deployment','deployment_cases',('d01','d02','d03','d05')),
        ('dispatch','dispatch_race_cases',('dr09','dr10','dr11','dr12','dr13','dr14','dr15','dr22')),
        ('admission','admission_cases',('a02','a03','a04','a06','a07','a08','a10','a11','a12','a13','a15','a16')),
        ('deployment','deployment_cases',('d04','d06','d07','d08'))):
        for name in names:
            case_path='validation_lab/'+folder+'/evaluator/'+name+'.json'
            public_path='validation_lab/'+folder+'/public/'+(name+'.json' if profile=='dispatch' else 'initial.json')
            source=json.loads((ROOT/case_path).read_text())
            public=json.loads((ROOT/public_path).read_text())
            cases.append(dict(schema='public-worker-case/v1',case_id=f'w{len(cases)+1:02}',profile=profile,
                parent_instance_id=source['parent_instance_id'],split='development',
                source=dict(case_path=case_path,public_path=public_path,manifest='validation_lab/'+folder+'/manifest.json'),
                recovery='kill-and-retry-every-prefix',public=public,events=source['events']))
    return cases


def generate():
    cases=scenarios()
    for case in cases:
        for folder,value in (('public',case['public']),('evaluator',{k:v for k,v in case.items() if k!='public'})):
            (CORPUS/folder).mkdir(parents=True,exist_ok=True)
            write_json(CORPUS/folder/(case['case_id']+'.json'),value)
    fixtures=sorted(str(p.relative_to(ROOT)) for folder in ('public','evaluator') for p in (CORPUS/folder).glob('*.json'))
    upstream=sorted({p for c in cases for p in c['source'].values()})
    write_json(CORPUS/'manifest.json',dict(schema='public-worker-corpus/v1',split='development',case_count=len(cases),
        event_prefixes=sum(len(c['events']) for c in cases),family_complete_fixtures=0,
        fixture_files={p:digest_file(ROOT/p) for p in fixtures},source_files={p:digest_file(ROOT/p) for p in source_paths()},
        upstream_files={p:digest_file(ROOT/p) for p in upstream},
        scope='serial subprocess conformance; all three profiles have quiescent checkpoints and exact retries; no in-flight automatic recovery or OS sandbox'))


if __name__=='__main__':
    generate()
