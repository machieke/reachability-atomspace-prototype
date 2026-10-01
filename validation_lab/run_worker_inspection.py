"""Development crash probes with independent expectations and raw inspection evidence."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
import sys
from pathlib import Path

from reachability.codec import decode
from reachability.trace_protocol import canonical, fingerprint
from reachability.worker_inspection import inspect_worker, verify_inspection
from .generate_admission_cases import initial as admission_initial, scenarios as admission_cases
from .generate_deployment_cases import scenarios as deployment_cases
from .generate_dispatch_race_cases import scenarios as dispatch_cases
from .public_worker import PublicWorker, WorkerError, ROOT, runtime_bundle, write_json
from .run_public_workers import check_ready, check_event
from .shrink_replay import digest_file
from reachability.trace_protocol import DeploymentInitial

SCHEMA = 'worker-inspection-probes/v1'
EXIT_CODE = 79


def cases():
    result = []
    for profile, source, public in (
        ('admission', admission_cases()[0], admission_initial().wire()),
        ('deployment', deployment_cases()[0], asdict(DeploymentInitial())),
        ('dispatch', dispatch_cases()[8], asdict(DeploymentInitial()))):
        for cut in ('before', 'after', 'published'):
            result.append(dict(case_id=f'{profile}-{cut}', profile=profile, public=public, prefix=[],
                event=source['events'][0], cut=cut, parent_instance_id=source['parent_instance_id'],
                expected=dict(status='no_pending_marker' if cut=='published' else
                    'pending_no_journal_change' if cut=='before' else 'pending_journal_progress',
                    completed=int(cut=='published'), evidence=int(profile!='admission' and cut!='before'),
                    contexts=int(profile!='admission' or cut!='before'), numerical=0, reports=0, effects=0, dispatch=None)))
    numerical=admission_cases()[12]
    result.append(dict(case_id='admission-partial-estimate', profile='admission', public=admission_initial().wire(),
        prefix=numerical['events'][:1], event=numerical['events'][1], cut='estimate',
        parent_instance_id=numerical['parent_instance_id'], expected=dict(status='pending_journal_progress',
            completed=1,evidence=1,contexts=1,numerical=0,reports=1,effects=0,dispatch=None)))
    context=admission_cases()[0]
    result.append(dict(case_id='admission-partial-context',profile='admission',public=admission_initial().wire(),
        prefix=[],event=context['events'][0],cut='context',parent_instance_id=context['parent_instance_id'],
        expected=dict(status='pending_journal_progress',completed=0,evidence=0,contexts=1,numerical=0,reports=0,effects=0,dispatch=None)))
    for cut in ('evidence-commit','after'):
        result.append(dict(case_id='admission-evidence-'+('commit' if cut=='evidence-commit' else 'after'),
            profile='admission',public=admission_initial().wire(),prefix=context['events'][:1],event=context['events'][1],
            cut=cut,parent_instance_id=context['parent_instance_id'],
            expected=dict(status='pending_journal_progress',completed=1,evidence=1,contexts=1,numerical=0,reports=0,effects=0,dispatch=None)))
    for cut in ('estimate-commit','after'):
        result.append(dict(case_id='admission-estimate-'+('commit' if cut=='estimate-commit' else 'after'),
            profile='admission',public=admission_initial().wire(),prefix=numerical['events'][:2],event=numerical['events'][2],
            cut=cut,parent_instance_id=numerical['parent_instance_id'],
            expected=dict(status='pending_journal_progress',completed=2,evidence=2,contexts=1,numerical=2,reports=2,effects=0,dispatch=None)))
    for profile,source,index in (('deployment',deployment_cases()[2],6),('dispatch',dispatch_cases()[8],5)):
        result.append(dict(case_id=profile+'-remote-effect',profile=profile,public=asdict(DeploymentInitial()),
            prefix=source['events'][:index],event=source['events'][index],cut='effect',
            parent_instance_id=source['parent_instance_id'],expected=dict(status='pending_journal_progress',
                completed=index,evidence=3,contexts=1,numerical=1,reports=1,effects=1,dispatch='uncertain')))
    deployment=deployment_cases()[0]
    result.append(dict(case_id='deployment-partial-fact',profile='deployment',public=asdict(DeploymentInitial()),
        prefix=[],event=deployment['events'][0],cut='fact',parent_instance_id=deployment['parent_instance_id'],
        expected=dict(status='pending_journal_progress',completed=0,evidence=1,contexts=1,numerical=0,reports=0,effects=0,dispatch=None)))
    result.append(dict(case_id='deployment-partial-attempt',profile='deployment',public=asdict(DeploymentInitial()),
        prefix=deployment['events'][:3],event=deployment['events'][3],cut='attempt',parent_instance_id=deployment['parent_instance_id'],
        expected=dict(status='pending_journal_progress',completed=3,evidence=3,contexts=1,numerical=1,reports=1,effects=0,dispatch=None)))
    monitor=deployment_cases()[6]
    result.append(dict(case_id='deployment-partial-sample',profile='deployment',public=asdict(DeploymentInitial()),
        prefix=monitor['events'][:1],event=monitor['events'][1],cut='sample',parent_instance_id=monitor['parent_instance_id'],
        expected=dict(status='pending_journal_progress',completed=1,evidence=2,contexts=1,numerical=0,reports=0,effects=0,dispatch=None)))
    return result


def fault_spec(case):
    profile,cut=case['profile'],case['cut']
    if cut in ('before','after'):
        name='dispatch_worker_state.py' if profile=='dispatch' else 'trace_worker_state.py'
        needle=('row = super().apply(message)' if profile=='dispatch' else 'row=super().apply(message)')
        indent='            '
        replacement=(f'__import__("os")._exit({EXIT_CODE})\n'+indent+needle if cut=='before'
                     else needle+'\n'+indent+f'__import__("os")._exit({EXIT_CODE})')
    elif cut=='published':
        name,needle='stream_worker.py','def emit(value):'
        replacement=needle+f'\n    if value.get("kind")=="event":\n        __import__("os")._exit({EXIT_CODE})'
    elif cut=='effect':
        name,needle='simulated_executor.py','return self._write("submit", request)'
        replacement=f'self._write("submit", request)\n        __import__("os")._exit({EXIT_CODE})'
    elif cut=='estimate':
        name,needle='admission_trace.py','transition = s.propose_probability(ctx, "observation", evidence_id=e.event_id, idempotency_key=self.key())'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n                '+needle
    elif cut=='context':
        name,needle='admission_trace.py','self.contexts.add(ctx)'
        replacement=needle+f'\n            __import__("os")._exit({EXIT_CODE})'
    elif cut in ('evidence-commit','estimate-commit'):
        name,needle='admission_trace.py','(self.numeric if numeric else self.hard)[event_id] = result.belief.belief_revision_id'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n        '+needle
    elif cut=='attempt':
        name,needle='deployment_trace.py','s.select_operation(attempt, operation.revision, idempotency_key=self.key())'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n            '+needle
    elif cut=='sample':
        name,needle='deployment_trace.py','s.record_goal_sample(event.event_id, c.goal_id, "healthy", a["healthy"], belief.belief_revision_id,'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n            '+needle
    else:
        name,needle='deployment_trace.py','if truth is not None:'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n        '+needle
    return name,needle,replacement


def inject(bundle, case):
    name,needle,replacement=fault_spec(case)
    path=Path(bundle)/'reachability'/name
    original=path.read_text()
    if original.count(needle)!=1:
        raise ValueError('crash injection point is not unique')
    modified=original.replace(needle,replacement)
    path.write_text(modified)
    return dict(file=name,before=sha256(original.encode()).hexdigest(),after=digest_file(path),needle=needle,replacement=replacement)


def evaluate(case,report):
    """Expected primitive effects are declared independently of journal replay."""
    body=decode(report['checkpoint'])
    state=report['authority']
    ledgers=state['ledgers']
    dispatch=[decode(value).state for value in state['views']['dispatch'].values()]
    actual=dict(status=report['status'],completed=len(body['completed']),evidence=len(ledgers['evidence']),
        contexts=len(state['views']['contexts']),numerical=len(ledgers['probability']['beliefs']),
        reports=len(ledgers['probability']['reports']),effects=report['executor']['total_effects'] if report['executor'] else 0,
        dispatch=dispatch[0] if dispatch else None)
    if actual!=case['expected'] or report['errors'] or report['continuation_authorized']:
        raise ValueError('inspection differs from independent crash expectation: '+case['case_id']+' '+canonical(actual))
    pending=None if case['cut']=='published' else case['event']
    if report['pending']!=pending:
        raise ValueError('pending public command differs')
    if case['cut']=='context' and ledgers['probability']['policies']:
        raise ValueError('partial context incorrectly acquired a probability policy')
    if case['cut']=='fact' and any(ledgers['hard_beliefs'].values()):
        raise ValueError('partial fact incorrectly acquired an admitted belief')
    if case['case_id'].startswith('admission-evidence-'):
        if (len(ledgers['hard_beliefs']['c0'])!=1 or len(ledgers['certificates'])!=2 or body['metadata']['hard']
                or [entry['command'] for entry in report['journals']['authority']['appended']]!=[
                    'record_evidence','propose_evidence','precertify','postcertify','commit']):
            raise ValueError('persisted evidence differs from expected committed belief with missing wrapper alias')
    if case['case_id'].startswith('admission-estimate-'):
        if (any(ledgers['hard_beliefs'].values()) or len(ledgers['probability']['certificates'])!=4
                or len(body['metadata']['numeric'])!=1 or case['event']['event_id'] in dict(body['metadata']['numeric'])
                or [entry['command'] for entry in report['journals']['authority']['appended']]!=[
                    'record_evidence','record_probability_report','propose_probability',
                    'precertify_probability','postcertify_probability','commit_probability']):
            raise ValueError('persisted estimate differs from expected numerical belief with missing wrapper alias')
    if case['cut']=='attempt':
        operation=decode(state['views']['operations']['a0']).operation
        if operation.selected or body['metadata']['attempts']:
            raise ValueError('partial operation was selected or acquired a wrapper alias')
    if case['cut']=='sample' and ledgers['goals']['samples']:
        raise ValueError('partial sample was registered before the crash')
    if case['cut']=='published':
        row=body['completed'][case['event']['event_id']]['record']
        check_event(case,[*case['prefix'],case['event']],dict(schema='public-stream-worker/v1',kind='event',
            profile=case['profile'],event_digest=fingerprint(case['event']),
            replayed=False,record=row))
    return actual


def run_case(case,output):
    output=Path(output)
    output.mkdir(parents=True)
    write_json(output/'case.json',case)
    runtime_bundle(output/'runtime')
    # Establish only the completed prefix with the unmodified worker first.
    worker=PublicWorker(output/'runtime',case['profile'],output/'state',output/'prefix')
    try:
        check_ready(case,[],worker.request(case['public']))
        prefix=[]
        for event in case['prefix']:
            prefix.append(event)
            check_event(case,prefix,worker.request(event))
    finally:
        worker.stop()
    write_json(output/'fault.json',inject(output/'runtime',case))
    worker=PublicWorker(output/'runtime',case['profile'],output/'state',output/'crash',resume=True)
    try:
        check_ready(case,case['prefix'],worker.request(case['public']))
        try:
            worker.request(case['event'])
        except WorkerError:
            pass
        else:
            raise ValueError('crash probe unexpectedly replied')
    finally:
        worker.stop(kill=True)
    if json.loads((output/'crash'/'exit.json').read_text())['returncode']!=EXIT_CODE:
        raise ValueError('worker did not exit at the injected boundary')
    report=inspect_worker(case['profile'],output/'state',output/'inspection')
    return evaluate(case,report)


def source_files():
    return {str(p.relative_to(ROOT)):digest_file(p) for p in sorted((ROOT/'reachability').glob('*.py'))} | {
        'validation_lab/'+name+'.py':digest_file(ROOT/'validation_lab'/(name+'.py')) for name in (
            'run_worker_inspection','public_worker','run_public_workers','generate_admission_cases',
            'generate_deployment_cases','generate_dispatch_race_cases','admission_oracle','deployment_oracle','dispatch_race_oracle',
            'run_deployment','shrink_replay')} | {'adapters.lock.json':digest_file(ROOT/'adapters.lock.json')}


def verify_report(output):
    output=Path(output)
    receipt=json.loads((output/'report.json').read_text())
    actual_files={str(p.relative_to(output)):digest_file(p) for p in sorted(output.rglob('*')) if p.is_file() and p!=output/'report.json'}
    if receipt['schema']!=SCHEMA or receipt['files']!=actual_files or receipt['sources']!=source_files():
        raise ValueError('inspection probe sources/files differ')
    expected_cases=cases()
    results={}
    for case in expected_cases:
        root=output/case['case_id']
        if json.loads((root/'case.json').read_text())!=case:
            raise ValueError('inspection probe case differs')
        name,needle,replacement=fault_spec(case)
        original=(ROOT/'reachability'/name).read_text()
        modified=original.replace(needle,replacement)
        fault=dict(file=name,before=sha256(original.encode()).hexdigest(),after=sha256(modified.encode()).hexdigest(),
                   needle=needle,replacement=replacement)
        if json.loads((root/'fault.json').read_text())!=fault:
            raise ValueError('inspection fault receipt differs')
        bundle=root/'runtime'
        originals={'reachability/'+p.name:digest_file(p) for p in (ROOT/'reachability').glob('*.py')}
        if json.loads((bundle/'bundle.json').read_text())!=originals:
            raise ValueError('inspection original runtime receipt differs')
        bundled={str(p.relative_to(bundle)):digest_file(p) for p in (bundle/'reachability').rglob('*') if p.is_file()}
        expected_bundle=dict(originals); expected_bundle['reachability/'+name]=fault['after']
        if bundled!=expected_bundle:
            raise ValueError('inspection injected runtime differs')
        # Replay the original successful wire prefixes against independent models.
        for stage,prefix in (('prefix',case['prefix']),('crash',[])):
            launch=json.loads((root/stage/'launch.json').read_text())
            bootstrap='import sys; sys.path.insert(0, '+repr(str(bundle.resolve()))+'); from reachability.stream_worker import main; main()'
            argv=[sys.executable,'-I','-B','-c',bootstrap,'--profile',case['profile'],'--database-dir',str((root/'state').resolve())]
            if stage=='crash':
                argv.append('--resume')
            if (launch['argv']!=argv or launch['profile']!=case['profile'] or launch['resume']!=(stage=='crash')
                    or launch['environment']!=dict(PATH=os.defpath,LANG='C.UTF-8',LC_ALL='C.UTF-8')
                    or launch['pid']==launch['parent_pid'] or launch['cwd']!=str((root/stage/'cwd').resolve())):
                raise ValueError('inspection worker launch differs')
            if stage=='prefix' and json.loads((root/stage/'exit.json').read_text())['returncode']!=0:
                raise ValueError('inspection prefix worker failed')
            messages=[json.loads(line) for line in (root/stage/'stdin.jsonl').read_text().splitlines()]
            replies=[json.loads(line) for line in (root/stage/'stdout.jsonl').read_text().splitlines()]
            expected_inputs=[case['public'],*(prefix if stage=='prefix' else [case['event']])]
            if messages!=expected_inputs or len(replies)!=1+len(prefix):
                raise ValueError('inspection raw process exchanges differ')
            check_ready(case,[] if stage=='prefix' else case['prefix'],replies[0])
            for index,row in enumerate(replies[1:],1):
                check_event(case,prefix[:index],row)
        if json.loads((root/'crash'/'exit.json').read_text())['returncode']!=EXIT_CODE:
            raise ValueError('inspection crash evidence differs')
        report=verify_inspection(root/'inspection')
        # The original worker directory must still contain exactly its captured
        # evidence bytes after inspection and offline report verification.
        from reachability.worker_inspection import file_inventory,capture_names
        if file_inventory(root/'state',capture_names(root/'state'))!=report['evidence']:
            raise ValueError('inspection changed original worker evidence')
        results[case['case_id']]=evaluate(case,report)
    if receipt['results']!=results:
        raise ValueError('inspection probe results differ')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True)
    results={case['case_id']:run_case(case,args.output/case['case_id']) for case in cases()}
    files={str(p.relative_to(args.output)):digest_file(p) for p in sorted(args.output.rglob('*')) if p.is_file()}
    write_json(args.output/'report.json',dict(schema=SCHEMA,sources=source_files(),results=results,files=files))
    verify_report(args.output)
    print(canonical(dict(cases=len(results),passed=True,output=str(args.output))),flush=True)


if __name__=='__main__':
    main()
