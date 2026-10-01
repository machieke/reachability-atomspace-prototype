"""Independent conformance across a separate-process, serial public boundary."""
import argparse
import json
from pathlib import Path

from reachability.admission_protocol import AdmissionInitial, AdmissionEvent
from reachability.dispatch_race_protocol import parse as dispatch_event
from reachability.trace_protocol import DeploymentInitial, DeploymentEvent, canonical, fingerprint
from . import admission_oracle, deployment_oracle, dispatch_race_oracle
from .public_worker import PublicWorker, ROOT, runtime_bundle, write_json
from .run_deployment import ConformanceMismatch
from .shrink_replay import digest_file

CORPUS=ROOT/'validation_lab'/'public_worker_cases'
REFERENCES={'admission':admission_oracle.reference_prefix,'deployment':deployment_oracle.reference_prefix,'dispatch':dispatch_race_oracle.reference_prefix}


def compare(expected,actual,event_id,path='projection'):
    if isinstance(expected,dict) and isinstance(actual,dict) and set(expected)==set(actual):
        for key in expected:
            compare(expected[key],actual[key],event_id,path+'.'+key)
    elif isinstance(expected,list) and isinstance(actual,list) and len(expected)==len(actual):
        for index,(left,right) in enumerate(zip(expected,actual)):
            compare(left,right,event_id,path+'.'+str(index))
    elif isinstance(expected,bool)!=isinstance(actual,bool) or expected!=actual:
        raise ConformanceMismatch(event_id,path,expected,actual)


def validate_case(case):
    profile=case['profile']
    if profile not in REFERENCES:
        raise ValueError('unsupported process profile')
    if profile=='admission':
        initial=AdmissionInitial.parse(case['public'])
        parse=lambda e:AdmissionEvent.parse(e,len(initial.atoms))
    else:
        DeploymentInitial.parse(case['public'])
        parse=dispatch_event if profile=='dispatch' else DeploymentEvent.parse
    events=case['events']
    if type(events) is not list or len(events)>(64 if profile=='dispatch' else 128):
        raise ValueError('bounded event list required')
    for event in events:
        parse(event)
    if len({e['event_id'] for e in events}) != len(events):
        raise ValueError('duplicate public event identity')
    if case['recovery'] != ('kill-and-retry-every-prefix' if profile=='dispatch' else 'fresh-worker'):
        raise ValueError('unsupported process recovery schedule')


def check_ready(case,prefix,response):
    expected=REFERENCES[case['profile']](case['public'],prefix)
    fields={'schema','kind','profile','initial_digest','completed','projection'}
    if case['profile']!='admission':
        fields.add('executor_effects')
    if (type(response) is not dict or set(response)!=fields or response['schema']!='public-stream-worker/v1'
            or response['kind']!='ready' or response['profile']!=case['profile']
            or response['initial_digest']!=fingerprint(case['public'])
            or type(response['completed']) is not int
            or response['completed']!=(len(prefix) if case['profile']=='dispatch' else 0)):
        raise ValueError('worker ready envelope differs from public session')
    compare(expected['projection'],response['projection'],'ready')
    if 'executor_effects' in expected:
        compare(expected['executor_effects'],response['executor_effects'],'ready','executor_effects')


def check_event(case,prefix,response,*,replayed=False,reference=None):
    event=prefix[-1]
    if (type(response) is not dict or set(response)!={'schema','kind','profile','event_digest','replayed','record'}
            or response['schema']!='public-stream-worker/v1' or response['kind']!='event'
            or response['profile']!=case['profile'] or response['event_digest']!=fingerprint(event)
            or response['replayed'] is not replayed):
        raise ValueError('worker event response correlation differs')
    row=response['record']
    schemas=dict(admission='admission-trace/v1',deployment='deployment-trace/v1',dispatch='dispatch-race-trace/v1')
    if type(row) is not dict or row.get('schema')!=schemas[case['profile']]:
        raise ValueError('worker trace schema differs')
    expected=(reference or REFERENCES[case['profile']])(case['public'],prefix)
    compare(expected['status'],row['outcome']['status'],event['event_id'],'outcome.status')
    compare(expected['projection'],row['projection'],event['event_id'])
    if row['initial_digest']!=fingerprint(case['public']) or row['projection_digest']!=fingerprint(row['projection']):
        raise ValueError('worker trace digest mismatch')
    if case['profile']=='dispatch':
        if row['outcome']['event_id']!=event['event_id']:
            raise ValueError('worker trace event identity differs')
        effects=row['executor_effects']
    else:
        if row['event_id']!=event['event_id'] or row['event_digest']!=fingerprint(event) or type(row['step']) is not int or row['step']!=len(prefix):
            raise ValueError('worker trace sequence/identity differs')
        effects=row.get('instrumentation',{}).get('executor_effects')
    if 'executor_effects' in expected:
        compare(expected['executor_effects'],effects,event['event_id'],'executor_effects')


def run_case(case,output,*,bundle=None,reference=None):
    validate_case(case)
    output=Path(output)
    output.mkdir(parents=True)
    write_json(output/'case.json',case)
    if bundle is None:
        bundle=output/'runtime'
        runtime_bundle(bundle)
    prefix,worker,starts,retries= [],None,0,0
    with (output/'exchanges.jsonl').open('w') as log:
        def exchange(request,kind):
            response=worker.request(request)
            # The binary stdout log already exists. Retain the decoded envelope
            # before invoking any oracle or comparison as well.
            log.write(canonical(dict(worker=starts-1,kind=kind,request=request,response=response))+'\n')
            log.flush()
            return response
        def start(resume):
            nonlocal worker,starts
            worker=PublicWorker(bundle,case['profile'],output/'state',output/'workers'/f'{starts:04d}',resume=resume)
            starts+=1
            ready=exchange(case['public'],'ready')
            check_ready(case,prefix,ready)
        try:
            start(False)
            for event in case['events']:
                response=exchange(event,'event')
                prefix.append(event)
                check_event(case,prefix,response,reference=reference)
                if case['profile']=='dispatch':
                    worker.stop(kill=True)
                    start(True)
                    retry=exchange(event,'retry')
                    check_event(case,prefix,retry,replayed=True,reference=reference)
                    if retry['record']!=response['record']:
                        raise ValueError('recovered reply differs from completed reply')
                    retries+=1
            worker.stop()
        finally:
            if worker is not None and not worker.closed:
                worker.stop(kill=True)
            write_json(output/'execution.json',dict(prefixes=len(prefix),worker_starts=starts,recovered_prefixes=retries,exact_retries=retries))
    return dict(prefixes=len(prefix),worker_starts=starts,recovered_prefixes=retries,exact_retries=retries)


def source_paths():
    names=['public_worker','run_public_workers','generate_public_worker_cases','admission_oracle','deployment_oracle','dispatch_race_oracle','run_deployment','shrink_replay']
    return sorted(['adapters.lock.json']+['validation_lab/'+n+'.py' for n in names]+[str(p.relative_to(ROOT)) for p in (ROOT/'reachability').glob('*.py')])


def load_cases():
    return [dict(json.loads(p.read_text()),public=json.loads((CORPUS/'public'/p.name).read_text())) for p in sorted((CORPUS/'evaluator').glob('*.json'))]


def verify_corpus():
    receipt=json.loads((CORPUS/'manifest.json').read_text())
    inventory={str(p.relative_to(ROOT)) for p in CORPUS.rglob('*') if p.is_file() and p!=CORPUS/'manifest.json'}
    if (receipt['schema']!='public-worker-corpus/v1' or set(receipt['fixture_files'])!=inventory
            or set(receipt['source_files'])!=set(source_paths())):
        raise ValueError('public worker corpus inventory differs')
    for section in ('fixture_files','source_files','upstream_files'):
        for name,digest in receipt[section].items():
            if digest_file(ROOT/name)!=digest:
                raise ValueError('public worker corpus source/ancestry drift: '+name)
    cases=load_cases()
    if set(receipt['upstream_files'])!={p for case in cases for p in case['source'].values()}:
        raise ValueError('public worker ancestry inventory differs')
    if (len(cases)!=receipt['case_count'] or sum(len(c['events']) for c in cases)!=receipt['event_prefixes']
            or receipt['family_complete_fixtures']!=0 or any(c['split']!='development' for c in cases)):
        raise ValueError('public worker corpus counts/split differ')
    for case in cases:
        validate_case(case)
        upstream=json.loads((ROOT/case['source']['case_path']).read_text())
        if (upstream['events']!=case['events'] or upstream['parent_instance_id']!=case['parent_instance_id']
                or json.loads((ROOT/case['source']['public_path']).read_text())!=case['public']):
            raise ValueError('public worker case ancestry differs')
    return receipt


def verify_report(output):
    output=Path(output)
    report=json.loads((output/'report.json').read_text())
    inventory={str(p.relative_to(output)):digest_file(p) for p in sorted(output.rglob('*')) if p.is_file() and p!=output/'report.json'}
    if report['schema']!='public-worker-validation/v1' or report['corpus']!=verify_corpus() or report['files']!=inventory:
        raise ValueError('public worker report sources/files differ')
    bundle={str(p.relative_to(output/'runtime')):digest_file(p) for p in sorted((output/'runtime'/'reachability').glob('*.py'))}
    expected_bundle={str(p.relative_to(ROOT)):digest_file(p) for p in sorted((ROOT/'reachability').glob('*.py'))}
    bundle_files={str(p.relative_to(output/'runtime')) for p in (output/'runtime').rglob('*') if p.is_file()}
    if (bundle!=expected_bundle or bundle_files!=set(expected_bundle)|{'bundle.json'}
            or json.loads((output/'runtime'/'bundle.json').read_text())!=bundle):
        raise ValueError('worker runtime bundle differs from pinned sources')
    cases={c['case_id']:c for c in load_cases()}
    if len(report['results'])!=len(cases) or {r['case_id'] for r in report['results']}!=set(cases) or not all(r['passed'] for r in report['results']):
        raise ValueError('public worker report coverage differs')
    for result in report['results']:
        case=cases[result['case_id']]
        directory=output/case['case_id']
        if json.loads((directory/'case.json').read_text())!=case:
            raise ValueError('public worker saved case differs')
        rows=[json.loads(line) for line in (directory/'exchanges.jsonl').read_text().splitlines()]
        prefix,recovered,worker_index=[],0,0
        expected_requests=[('ready',case['public'])]
        for event in case['events']:
            expected_requests.append(('event',event))
            if case['profile']=='dispatch':
                expected_requests.extend([('ready',case['public']),('retry',event)])
        if [(r['kind'],r['request']) for r in rows]!=expected_requests:
            raise ValueError('worker exchanges omit, add or reorder public inputs')
        originals={}
        for index,row in enumerate(rows):
            kind,response=row['kind'],row['response']
            if kind=='ready':
                if index:
                    worker_index+=1
                check_ready(case,prefix,response)
            elif kind=='event':
                prefix.append(row['request'])
                check_event(case,prefix,response)
                originals[prefix[-1]['event_id']]=response['record']
            else:
                check_event(case,prefix,response,replayed=True)
                if response['record']!=originals[prefix[-1]['event_id']]:
                    raise ValueError('worker retry differs from original reply')
                recovered+=1
            if row['worker']!=worker_index:
                raise ValueError('worker process index differs')
        expected=dict(prefixes=len(prefix),worker_starts=worker_index+1,recovered_prefixes=recovered,exact_retries=recovered)
        if json.loads((directory/'execution.json').read_text())!=expected or any(result[k]!=v for k,v in expected.items()):
            raise ValueError('worker execution counts differ')
        for index in range(worker_index+1):
            path=directory/'workers'/f'{index:04d}'
            subset=[r for r in rows if r['worker']==index]
            incoming=[json.loads(line) for line in (path/'stdin.jsonl').read_text().splitlines()]
            outgoing=[json.loads(line) for line in (path/'stdout.jsonl').read_text().splitlines()]
            launch=json.loads((path/'launch.json').read_text())
            exit_record=json.loads((path/'exit.json').read_text())
            if (incoming!=[r['request'] for r in subset] or outgoing!=[r['response'] for r in subset]
                    or launch['pid']==launch['parent_pid'] or launch['resume'] is not bool(index)
                    or launch['profile']!=case['profile'] or (path/'stderr.log').read_bytes()):
                raise ValueError('raw worker boundary evidence differs')
            expected_exit=dict(schema='public-worker-exit/v1',requested='kill' if index<worker_index else 'eof',returncode=-9 if index<worker_index else 0)
            if exit_record!=expected_exit:
                raise ValueError('worker termination evidence differs')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts'/'public-worker-validation')
    args=parser.parse_args()
    receipt=verify_corpus()
    args.output.mkdir(parents=True)
    runtime_bundle(args.output/'runtime')
    results=[]
    for case in load_cases():
        try:
            result=run_case(case,args.output/case['case_id'],bundle=args.output/'runtime')
            results.append(dict(case_id=case['case_id'],passed=True,**result))
        except Exception as error:
            results.append(dict(case_id=case['case_id'],passed=False,error_type=type(error).__name__,error=str(error)))
    report=dict(schema='public-worker-validation/v1',corpus=receipt,results=results,
        files={str(p.relative_to(args.output)):digest_file(p) for p in sorted(args.output.rglob('*')) if p.is_file()})
    write_json(args.output/'report.json',report)
    print(json.dumps(results,indent=2))
    if not all(r['passed'] for r in results):
        raise SystemExit(1)
    verify_report(args.output)


if __name__=='__main__':
    main()
