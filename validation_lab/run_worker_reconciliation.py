"""Actual reconciliation crashes, exact retries and independent continuation checks."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

from reachability.trace_protocol import canonical, fingerprint
from reachability.worker_inspection import capture_names,file_inventory,verify_inspection,inspect_worker
from reachability.worker_reconciliation import make_request,archive_path,journal_evidence,verify_reconciliation,ACTION
from reachability.context_reconciliation import ACTION as CONTEXT_ACTION, ADOPT_ACTION
from reachability.evidence_reconciliation import ACTION as EVIDENCE_ACTION
from reachability.admission_protocol import event as admission_event
from .public_worker import PublicWorker,WorkerError,ROOT,runtime_bundle,write_json
from .run_public_workers import REFERENCES,compare,check_event
from .run_worker_inspection import cases as inspection_cases,run_case as inspect_probe,source_files as inspection_sources
from .shrink_replay import digest_file

SCHEMA='worker-reconciliation-probes/v4'
EXIT_CODE=83
CUTS=('archive-file','assets','marker','checkpoint','result','stdout')
CONTEXT_CUTS=(*CUTS,'transaction','committed')


def probes():
    return ([(profile,cut) for profile in ('admission','deployment') for cut in CUTS]
        + [('context',cut) for cut in CONTEXT_CUTS] + [('adopt',cut) for cut in CUTS]
        + [(mode,cut) for mode in ('evidence-commit','evidence-after') for cut in CUTS])


def action(mode):
    return {'context':CONTEXT_ACTION,'adopt':ADOPT_ACTION,
        'evidence-commit':EVIDENCE_ACTION,'evidence-after':EVIDENCE_ACTION}.get(mode,ACTION)


def scenario(mode):
    if mode in ('evidence-commit','evidence-after'):
        return next(c for c in inspection_cases() if c['case_id']=='admission-'+mode)
    profile='admission' if mode in ('context','adopt') else mode
    suffix={'context':'-partial-context','adopt':'-after'}.get(mode,'-before')
    return next(c for c in inspection_cases() if c['case_id']==profile+suffix)


def continuation(case, completing):
    if case['event']['kind']=='evidence' and completing:
        return admission_event('derive-after-adoption','derive',context_id=case['event']['arguments']['context_id'],
            rule_id='r2',premises=[case['event']['event_id']])
    if completing:
        return admission_event('estimate-after-completion','estimate',context_id=case['event']['arguments']['context_id'],
            literal=1,roots=['sensor-after-completion'],valid_until=None,strength=0.8,confidence=0.6)
    event=deepcopy(case['event']);event['event_id']='new-after-cancel'
    return event


def fault_spec(cut):
    if cut=='archive-file':
        needle='os.replace(temporary, path)'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n        '+needle
    elif cut in ('assets','marker'):
        needle='atomic_write(directory/MARKER,control(record))  # Worker gate precedes checkpoint publication.'
        crash=f'__import__("os")._exit({EXIT_CODE})'
        replacement=crash+'\n        '+needle if cut=='assets' else needle+'\n        '+crash
    elif cut=='checkpoint':
        needle="if digest_bytes(path.read_bytes()) != record['after_sha256']:"
        replacement=f'__import__("os")._exit({EXIT_CODE})\n    '+needle
    elif cut in ('transaction','committed'):
        needle="connection.execute('COMMIT')  # Only the validated missing policy entry can be appended."
        crash=f'__import__("os")._exit({EXIT_CODE})'
        replacement=crash+'\n        '+needle if cut=='transaction' else needle+'\n        '+crash
    elif cut=='result':
        needle='marker.unlink()'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n    '+needle
    else:
        needle='print(canonical(result),flush=True)'
        replacement=f'__import__("os")._exit({EXIT_CODE})\n    '+needle
    return needle,replacement


def invoke(bundle,state,inspection,request_path,evidence):
    evidence=Path(evidence);evidence.mkdir(parents=True)
    cwd=evidence/'cwd';cwd.mkdir()
    bootstrap='import sys; sys.path.insert(0, '+repr(str(bundle.resolve()))+'); from reachability.worker_reconciliation import main; main()'
    argv=[sys.executable,'-I','-B','-c',bootstrap,'apply','--request',str(request_path.resolve()),
        '--inspection',str(inspection.resolve()),'--database-dir',str(state.resolve())]
    environment=dict(PATH=os.defpath,LANG='C.UTF-8',LC_ALL='C.UTF-8')
    with (evidence/'stdout.jsonl').open('wb') as out,(evidence/'stderr.log').open('wb') as err:
        proc=subprocess.Popen(argv,cwd=cwd,env=environment,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        write_json(evidence/'launch.json',dict(argv=argv,environment=environment,cwd=str(cwd.resolve()),pid=proc.pid,parent_pid=os.getpid()))
        try:
            code=proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill();proc.wait()
            raise
    write_json(evidence/'exit.json',dict(returncode=code))
    return code


def run_case(mode,cut,root):
    case=scenario(mode);profile=case['profile'];completing=mode not in ('admission','deployment')
    completed=len(case['prefix'])+1
    status='PASS' if completing else 'UNKNOWN'
    inspect_probe(case,root/'probe')
    state,inspection=root/'probe'/'state',root/'probe'/'inspection'
    request=make_request(inspection,'decision-'+mode+'-'+cut,action(mode))
    write_json(root/'request.json',request)
    before=journal_evidence(file_inventory(state,capture_names(state)))
    write_json(root/'journals-before.json',before)
    runtime_bundle(root/'runtime')
    path=root/'runtime'/'reachability'/('context_reconciliation.py' if cut in ('transaction','committed') else 'worker_reconciliation.py')
    original=path.read_text();needle,replacement=fault_spec(cut)
    if original.count(needle)!=1:
        raise ValueError('reconciliation crash point is not unique')
    path.write_text(original.replace(needle,replacement))
    write_json(root/'fault.json',dict(cut=cut,needle=needle,replacement=replacement,before=digest_file(ROOT/'reachability'/path.name),after=digest_file(path)))
    if invoke(root/'runtime',state,inspection,root/'request.json',root/'crash')!=EXIT_CODE:
        raise ValueError('reconciler did not exit at the injected boundary')
    # Until stdout loss, every cut leaves either the original pending event or
    # the reconciliation gate. No worker may accept another public command.
    if cut!='stdout':
        worker=PublicWorker(root/'runtime',profile,state,root/'gated-worker',resume=True)
        try:
            try:
                worker.request(case['public'])
            except WorkerError:
                pass
            else:
                raise ValueError('unfinished reconciliation admitted a worker')
        finally:
            worker.stop(kill=True)
        if json.loads((root/'gated-worker'/'exit.json').read_text())['returncode']!=2:
            raise ValueError('worker gate failed for an unexpected reason')
    path.write_text(original)
    if invoke(root/'runtime',state,inspection,root/'request.json',root/'retry')!=0:
        raise ValueError('exact decision retry failed')
    actual=journal_evidence(file_inventory(state,capture_names(state)))
    write_json(root/'journals-after.json',actual)
    if completing:
        completed_report=inspect_worker(profile,state,root/'after-decision')
        if completed_report['journals']['authority']['current']['sequence']!=request['journals']['authority']['sequence']+int(mode=='context'):
            raise ValueError('context reconciliation journal progress differs')
    if mode!='context' and actual!=before:
        raise ValueError('reconciliation changed a source journal')
    reply=json.loads((root/'retry'/'stdout.jsonl').read_text())
    if not reply['replayed'] or reply['result']!=verify_reconciliation(archive_path(state,request),inspection):
        raise ValueError('historical decision result differs')
    next_event=continuation(case,completing)
    resolved_prefix=[*case['prefix'],*([case['event']] if completing else [])]
    baseline=REFERENCES[profile](case['public'],resolved_prefix)
    worker=PublicWorker(root/'runtime',profile,state,root/'continued-worker',resume=True)
    try:
        ready=worker.request(case['public'])
        compare(baseline['projection'],ready['projection'],'resolved-ready')
        if ready['completed']!=completed:
            raise ValueError('reconciliation did not consume the event budget')
        resolved=worker.request(case['event'])
        if (resolved['replayed'] is not True or resolved['record']['outcome']['status']!=status
                or resolved['record']['step']!=completed):
            raise ValueError('resolved command executed or lost its historical reply')
        compare(ready['projection'],resolved['record']['projection'],'resolved-retry')
        continued=worker.request(next_event)
        reference=REFERENCES[profile](case['public'],[*resolved_prefix,next_event])
        compare(reference['status'],continued['record']['outcome']['status'],'new-command','outcome.status')
        compare(reference['projection'],continued['record']['projection'],'new-command')
        if continued['record']['step']!=completed+1 or continued['replayed']:
            raise ValueError('continuation step/replay flag differs')
    finally:
        worker.stop()
    # Exact decision retry remains historical after later checkpoint publication.
    if invoke(root/'runtime',state,inspection,root/'request.json',root/'historical')!=0:
        raise ValueError('historical decision retry failed after continuation')
    if json.loads((root/'historical'/'stdout.jsonl').read_text())!=reply:
        raise ValueError('historical decision receipt changed')
    return dict(profile=profile,action=request['action'],cut=cut,passed=True,resolved_status=status,continued_status=reference['status'])


def source_files():
    return inspection_sources() | {'validation_lab/run_worker_reconciliation.py':digest_file(Path(__file__))}


def verify_report(output):
    output=Path(output);receipt=json.loads((output/'report.json').read_text())
    files={str(p.relative_to(output)):digest_file(p) for p in sorted(output.rglob('*')) if p.is_file() and p!=output/'report.json'}
    if receipt['schema']!=SCHEMA or receipt['files']!=files or receipt['sources']!=source_files():
        raise ValueError('reconciliation probe sources/files differ')
    expected=[]
    for mode,cut in probes():
        case=scenario(mode);profile=case['profile'];completing=mode not in ('admission','deployment')
        completed=len(case['prefix'])+1
        status='PASS' if completing else 'UNKNOWN'
        root=output/(mode+'-'+cut);state=root/'probe'/'state';inspection=root/'probe'/'inspection'
        report=verify_inspection(inspection)
        request=json.loads((root/'request.json').read_text())
        if request!=make_request(inspection,'decision-'+mode+'-'+cut,action(mode)):
            raise ValueError('reconciliation request evidence differs')
        result=verify_reconciliation(archive_path(state,request),inspection)
        if json.loads((root/'journals-before.json').read_text())!=journal_evidence(report['evidence']):
            raise ValueError('reconciliation journal preservation evidence differs')
        if completing:
            after=verify_inspection(root/'after-decision')
            if (after['errors'] or after['status']!='no_pending_marker'
                    or {key:value['current'] for key,value in after['journals'].items()}!=result['journals']
                    or result['journals']['authority']['sequence']!=request['journals']['authority']['sequence']+int(mode=='context')
                    or json.loads((root/'journals-after.json').read_text())!=journal_evidence(after['evidence'])):
                raise ValueError('context completion journal evidence differs')
        if mode!='context' and (root/'journals-before.json').read_bytes()!=(root/'journals-after.json').read_bytes():
            raise ValueError('reconciliation journal preservation evidence differs')
        needle,replacement=fault_spec(cut)
        original=(ROOT/'reachability'/('context_reconciliation.py' if cut in ('transaction','committed') else 'worker_reconciliation.py')).read_text()
        from hashlib import sha256
        expected_fault=dict(cut=cut,needle=needle,replacement=replacement,before=sha256(original.encode()).hexdigest(),
            after=sha256(original.replace(needle,replacement).encode()).hexdigest())
        if json.loads((root/'fault.json').read_text())!=expected_fault:
            raise ValueError('reconciliation fault receipt differs')
        bundle=root/'runtime'
        originals={'reachability/'+p.name:digest_file(p) for p in (ROOT/'reachability').glob('*.py')}
        actual_bundle={str(p.relative_to(bundle)):digest_file(p) for p in (bundle/'reachability').rglob('*') if p.is_file()}
        if json.loads((bundle/'bundle.json').read_text())!=originals or actual_bundle!=originals:
            raise ValueError('reconciliation restored runtime bundle differs')
        for stage,code in (('crash',EXIT_CODE),('retry',0),('historical',0)):
            if json.loads((root/stage/'exit.json').read_text())['returncode']!=code:
                raise ValueError('reconciliation process exit differs')
            launch=json.loads((root/stage/'launch.json').read_text())
            bootstrap='import sys; sys.path.insert(0, '+repr(str(bundle.resolve()))+'); from reachability.worker_reconciliation import main; main()'
            argv=[sys.executable,'-I','-B','-c',bootstrap,'apply','--request',str((root/'request.json').resolve()),
                '--inspection',str(inspection.resolve()),'--database-dir',str(state.resolve())]
            if (launch['argv']!=argv or launch['pid']==launch['parent_pid']
                    or launch['environment']!=dict(PATH=os.defpath,LANG='C.UTF-8',LC_ALL='C.UTF-8')
                    or launch['cwd']!=str((root/stage/'cwd').resolve())):
                raise ValueError('reconciliation process launch differs')
            if stage=='crash':
                if (root/stage/'stdout.jsonl').read_bytes():
                    raise ValueError('crashed reconciliation unexpectedly replied')
            elif json.loads((root/stage/'stdout.jsonl').read_text())!=dict(result=result,replayed=True):
                raise ValueError('reconciliation exact reply differs')
        if cut!='stdout' and (json.loads((root/'gated-worker'/'exit.json').read_text())['returncode']!=2
                or (root/'gated-worker'/'stdout.jsonl').read_bytes()):
            raise ValueError('worker continuation gate differs')
        messages=[json.loads(line) for line in (root/'continued-worker'/'stdin.jsonl').read_text().splitlines()]
        rows=[json.loads(line) for line in (root/'continued-worker'/'stdout.jsonl').read_text().splitlines()]
        next_event=continuation(case,completing)
        if messages!=[case['public'],case['event'],next_event] or len(rows)!=3:
            raise ValueError('continuation raw exchanges differ')
        resolved_prefix=[*case['prefix'],*([case['event']] if completing else [])]
        baseline=REFERENCES[profile](case['public'],resolved_prefix)
        expected_ready=dict(schema='public-stream-worker/v1',kind='ready',profile=profile,completed=completed,
            initial_digest=fingerprint(case['public']),projection=baseline['projection'])
        if profile=='deployment': expected_ready['executor_effects']=0
        compare(expected_ready,rows[0],'ready','envelope')
        check_event(case,[*case['prefix'],case['event']],rows[1],replayed=True,
            reference=lambda public,prefix:dict(status=status,projection=baseline['projection']))
        if fingerprint(rows[1]['record'])!=result['reply_digest']:
            raise ValueError('resolved reply differs from decision archive')
        reference=REFERENCES[profile](case['public'],[*resolved_prefix,next_event])
        check_event(case,[*case['prefix'],case['event'],next_event],rows[2],reference=lambda public,prefix:reference)
        if rows[0]['completed']!=completed or rows[1]['record']['outcome']['status']!=status or not rows[1]['replayed']:
            raise ValueError('resolved event reply differs')
        compare(rows[0]['projection'],rows[1]['record']['projection'],'resolved')
        compare(reference['projection'],rows[2]['record']['projection'],'continued')
        if rows[2]['record']['step']!=completed+1 or rows[2]['record']['outcome']['status']!=reference['status']:
            raise ValueError('continued event outcome differs')
        expected.append(dict(profile=profile,action=request['action'],cut=cut,passed=True,resolved_status=status,continued_status=reference['status']))
    if receipt['results']!=expected:
        raise ValueError('reconciliation probe results differ')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True)
    results=[run_case(mode,cut,args.output/(mode+'-'+cut)) for mode,cut in probes()]
    files={str(p.relative_to(args.output)):digest_file(p) for p in sorted(args.output.rglob('*')) if p.is_file()}
    write_json(args.output/'report.json',dict(schema=SCHEMA,sources=source_files(),files=files,results=results))
    verify_report(args.output)
    print(canonical(dict(cases=len(results),passed=True,output=str(args.output))),flush=True)


if __name__=='__main__':
    main()
