"""Independent frozen schedule and actual serial-execution prefix comparisons."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.resource_planning import ResourceController, ResourcePublic
from reachability.resource_planning_session import ResourceSession
from reachability.trace_protocol import canonical, fingerprint
from .resource_planning_oracle import exact_plan, feasible, reference_prefix
from .run_deployment import compare

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'validation_lab'/'resource_planning_cases'


def load_cases():
    cases=[]
    for path in sorted((CORPUS/'evaluator').glob('*.json')):
        c=json.loads(path.read_text())
        c['public']=json.loads((CORPUS/'public'/path.name).read_text())
        cases.append(c)
    return cases


def verify_corpus():
    m=json.loads((CORPUS/'manifest.json').read_text())
    if m['schema']!='resource-planning-corpus/v1':
        raise ValueError('unsupported resource corpus')
    files={str(p.relative_to(ROOT)) for folder in ('public','evaluator') for p in (CORPUS/folder).rglob('*.json')}
    if files!=set(m['fixture_files']):
        raise ValueError('missing or unlisted resource fixture')
    if not {str(p.relative_to(ROOT)) for p in (ROOT/'reachability').glob('*.py')} <= set(m['source_files']):
        raise ValueError('unlisted runtime source')
    for group in ('fixture_files','source_files'):
        for path,digest in m[group].items():
            if sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
                raise ValueError('resource corpus/source receipt mismatch: '+path)
    cases=load_cases()
    if len(cases)!=m['case_count'] or any(c['split']!=m['split'] or c['parent_instance_id']!=m['parent_instance_id'] for c in cases):
        raise ValueError('resource corpus ancestry or count mismatch')
    return m


class ResourceWorld:
    def __init__(self, session, case, *, emit=None, recover=True):
        self.session,self.case=session,deepcopy(case)
        self.emit,self.recover=emit,recover
        self.events,self.records,self.references=[],[],[]
        self.counts={}
        self.recovered=0
        self.snapshot=None
        session.emit=self.on_event

    def log(self, **record):
        if self.emit:
            self.emit(record)

    def on_event(self, message, actual):
        self.events.append(deepcopy(message))
        self.records.append(actual)
        self.log(record_type='runtime',event=message,actual=actual)
        expected=reference_prefix(self.session.public.wire(),self.events)
        for key in ('status','projection','executor_effects'):
            compare(expected[key],actual[key],message['event_id'],key)
        compare(fingerprint(actual['projection']),actual['projection_digest'],message['event_id'],'projection_digest')
        if self.recover:
            self.session.restart()
            compare(expected['projection'],self.session.projection(),message['event_id'],'recovered_projection')
            compare(expected['executor_effects'],self.session.executor.total_effects,message['event_id'],'recovered_effects')
            self.recovered+=1

    def on_selection(self, row):
        self.log(record_type='controller',actual=row)
        if row['schema']!='resource-controller-step/v1' or row['search_work'] is None:
            return
        compare(fingerprint(self.snapshot),row['snapshot_digest'],str(row['index']),'snapshot_digest')
        expected=exact_plan(self.session.public.wire(),self.snapshot)
        self.references.append(expected)
        if expected['status']=='NOT_COMPUTED':
            raise ValueError('resource reference incomplete; no exact comparison')
        if row['stop_reason']=='BUDGET_EXHAUSTED':
            compare(None,row['plan'],str(row['index']),'budget.plan')
        elif row['plan'] is None:
            compare(expected['status'],row['stop_reason'],str(row['index']),'search.status')
        else:
            p=row['plan']
            compare(row['snapshot_digest'],p['snapshot_digest'],str(row['index']),'plan.snapshot_digest')
            objective=feasible(self.session.public.wire(),self.snapshot,p['steps'])
            compare(expected['objective'],objective,str(row['index']),'plan.feasibility')
            compare(objective,[p['cost'],p['finishes_at']],str(row['index']),'plan.objective')

    def execute(self, action):
        kind=action['kind']
        before,cost=len(self.records),self.session.spent
        self.counts[kind]=self.counts.get(kind,0)+1
        for hook in self.case['hooks']:
            if (hook['kind'],hook['occurrence'])==(kind,self.counts[kind]):
                for message in hook['events']:
                    self.session.observe(message)
        if action['snapshot_digest']!=fingerprint(self.session.read()):
            status='STALE'
        elif kind=='observe':
            a=self.session.active
            m=self.session.modes[a['mode_id']]
            response=self.case['responses'].get(m['mode_id'],{})
            intent=self.session.service.inspect_execution_intent(a['attempt']).intent
            # Outcomes require a selected public observation and an actual effect.
            receipt=self.session.executor.query(self.session.service.inspect_dispatch(a['attempt']).dispatch.request)
            now=self.session.read()['time']
            status='PASS'
            if response is not None and receipt.effect_count and now>=intent.created_at+m['duration']+response.get('delay',0):
                product='product:'+a['job_id']
                if now<response.get('wrong_until',0):
                    product+='0'
                status=self.session.send('outcome',product_id=product)['status']
        elif kind=='dispatch':
            faults=self.case['faults']
            i=self.counts[kind]-1
            status=self.session.send('dispatch',fault=faults[i] if i<len(faults) else 'none')['status']
        else:
            status=self.session.execute(action)['status']
        emitted=self.records[before:]
        return dict(status=status,public_events=len(emitted),charged=self.session.spent-cost,
                    journal_commands=sum(r['diagnostics']['journal_commands'] for r in emitted),
                    certificates=sum(len(r['diagnostics']['certificates']['$tuple']) for r in emitted))

    def port(self):
        world=self
        class PublicPort:
            def read(self):
                world.snapshot=world.session.read()
                return deepcopy(world.snapshot)
            def execute(self, action):
                return world.execute(action)
        return PublicPort()


def run_case(case, *, trace_path=None, recover=True, controller_factory=ResourceController):
    public=ResourcePublic.parse(case['public']['profile'])
    output=open(trace_path,'w') if trace_path else None
    def emit(row):
        if output:
            output.write(canonical(row)+'\n')
            output.flush()
    try:
        with TemporaryDirectory() as directory,ResourceSession(public,directory) as session:
            world=ResourceWorld(session,case,emit=emit,recover=recover)
            for message in case['public']['events']:
                session.observe(message)
            result=controller_factory(public).run(world.port(),visit_limit=case['visit_limit'],emit=world.on_selection)
            final=session.read()
            completed=all(j['completed'] for j in final['jobs'].values()) and final['active'] is None and final['time']<=public.wire()['deadline']
            first=result['records'][0]['plan'] if result['records'] else None
            objective=None if first is None else [first['cost'],first['finishes_at']]
            if case['expected'] is not None:
                for key,value in (('completed',completed),('objective',objective),('stop_reason',result['stop_reason'])):
                    compare(case['expected'][key],value,case['case_id'],key)
            else:
                compare(world.references[0]['status']=='SOLVED',completed,case['case_id'],'frozen-realization')
            receipts=[r['receipt'] for r in result['records'] if 'receipt' in r]
            compare(sum(r['charged'] for r in receipts),session.spent,case['case_id'],'charged_work')
            return dict(case_id=case['case_id'],status='PASS',completed=completed,stop_reason=result['stop_reason'],
                objective=objective,spent=session.spent,final_time=final['time'],executor_effects=session.executor.total_effects,
                compared_prefixes=len(world.events),recovered_prefixes=world.recovered,compared_plans=len(world.references),
                work=dict(requests=len(receipts),search_candidates=sum((r['search_work'] or {}).get('candidates',0) for r in result['records']),
                          public_events=sum(r['public_events'] for r in receipts),journal_commands=sum(r['journal_commands'] for r in receipts),
                          certificates=sum(r['certificates'] for r in receipts)),
                records=result['records'],events=world.events,projection=session.projection())
    finally:
        if output:
            output.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts'/'resource-planning-validation')
    args=parser.parse_args()
    receipt=verify_corpus()
    args.output.mkdir(parents=True,exist_ok=True)
    results=[]
    for case in load_cases():
        path=args.output/(case['case_id']+'.jsonl')
        try:
            r=run_case(case,trace_path=path)
            results.append({k:v for k,v in r.items() if k not in ('records','events','projection')})
        except Exception as error:
            results.append(dict(case_id=case['case_id'],status='FAIL',error_type=type(error).__name__,error=str(error),
                                recorded_lines=len(path.read_text().splitlines()) if path.exists() else 0))
    report=dict(schema='resource-planning-report/v1',variant='B0-serial-renewable/v1',mode='frozen-plans-and-closed-loop',corpus=receipt,
                results=results,family_complete_fixtures=0,concurrent_execution=False,comparative_performance=False,evaluator_process_isolation=False)
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(cases=len(results),passed=sum(r['status']=='PASS' for r in results),report=str(args.output/'report.json')),indent=2))
    if any(r['status']!='PASS' for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    main()
