"""Actual reconciliation crashes, exact retries and independent continuation checks."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

from reachability.trace_protocol import canonical, fingerprint
from reachability.worker_inspection import capture_names,file_inventory,verify_inspection
from reachability.worker_reconciliation import make_request,archive_path,journal_evidence,verify_reconciliation
from .public_worker import PublicWorker,WorkerError,ROOT,runtime_bundle,write_json
from .run_public_workers import REFERENCES,compare,check_event
from .run_worker_inspection import cases as inspection_cases,run_case as inspect_probe,source_files as inspection_sources
from .shrink_replay import digest_file

SCHEMA='worker-reconciliation-probes/v1'
EXIT_CODE=83
CUTS=('archive-file','assets','marker','checkpoint','result','stdout')


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


def run_case(profile,cut,root):
    case=next(c for c in inspection_cases() if c['case_id']==profile+'-before')
    inspect_probe(case,root/'probe')
    state,inspection=root/'probe'/'state',root/'probe'/'inspection'
    request=make_request(inspection,'cancel-'+profile+'-'+cut)
    write_json(root/'request.json',request)
    before=journal_evidence(file_inventory(state,capture_names(state)))
    write_json(root/'journals-before.json',before)
    runtime_bundle(root/'runtime')
    path=root/'runtime'/'reachability'/'worker_reconciliation.py'
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
    if actual!=before:
        raise ValueError('reconciliation changed a source journal')
    reply=json.loads((root/'retry'/'stdout.jsonl').read_text())
    if not reply['replayed'] or reply['result']!=verify_reconciliation(archive_path(state,request),inspection):
        raise ValueError('historical decision result differs')
    next_event=deepcopy(case['event']);next_event['event_id']='new-after-cancel'
    worker=PublicWorker(root/'runtime',profile,state,root/'continued-worker',resume=True)
    try:
        ready=worker.request(case['public'])
        compare(REFERENCES[profile](case['public'],[])['projection'],ready['projection'],'cancelled-ready')
        if ready['completed']!=1:
            raise ValueError('cancellation did not consume the event budget')
        cancelled=worker.request(case['event'])
        if (cancelled['replayed'] is not True or cancelled['record']['outcome']['status']!='UNKNOWN'
                or cancelled['record']['step']!=1):
            raise ValueError('cancelled command executed or lost its historical reply')
        compare(ready['projection'],cancelled['record']['projection'],'cancelled-retry')
        continued=worker.request(next_event)
        reference=REFERENCES[profile](case['public'],[next_event])
        compare(reference['status'],continued['record']['outcome']['status'],'new-command','outcome.status')
        compare(reference['projection'],continued['record']['projection'],'new-command')
        if continued['record']['step']!=2 or continued['replayed']:
            raise ValueError('continuation step/replay flag differs')
    finally:
        worker.stop()
    # Exact decision retry remains historical after later checkpoint publication.
    if invoke(root/'runtime',state,inspection,root/'request.json',root/'historical')!=0:
        raise ValueError('historical decision retry failed after continuation')
    if json.loads((root/'historical'/'stdout.jsonl').read_text())!=reply:
        raise ValueError('historical decision receipt changed')
    return dict(profile=profile,cut=cut,passed=True,cancelled_status='UNKNOWN',continued_status=reference['status'])


def source_files():
    return inspection_sources() | {'validation_lab/run_worker_reconciliation.py':digest_file(Path(__file__))}


def verify_report(output):
    output=Path(output);receipt=json.loads((output/'report.json').read_text())
    files={str(p.relative_to(output)):digest_file(p) for p in sorted(output.rglob('*')) if p.is_file() and p!=output/'report.json'}
    if receipt['schema']!=SCHEMA or receipt['files']!=files or receipt['sources']!=source_files():
        raise ValueError('reconciliation probe sources/files differ')
    expected=[]
    for profile in ('admission','deployment'):
        case=next(c for c in inspection_cases() if c['case_id']==profile+'-before')
        for cut in CUTS:
            root=output/(profile+'-'+cut);state=root/'probe'/'state';inspection=root/'probe'/'inspection'
            report=verify_inspection(inspection)
            request=json.loads((root/'request.json').read_text())
            if request!=make_request(inspection,'cancel-'+profile+'-'+cut):
                raise ValueError('reconciliation request evidence differs')
            result=verify_reconciliation(archive_path(state,request),inspection)
            if json.loads((root/'journals-before.json').read_text())!=journal_evidence(report['evidence']) or (
                    root/'journals-before.json').read_bytes()!=(root/'journals-after.json').read_bytes():
                raise ValueError('reconciliation journal preservation evidence differs')
            needle,replacement=fault_spec(cut)
            original=(ROOT/'reachability'/'worker_reconciliation.py').read_text()
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
            next_event=deepcopy(case['event']);next_event['event_id']='new-after-cancel'
            if messages!=[case['public'],case['event'],next_event] or len(rows)!=3:
                raise ValueError('continuation raw exchanges differ')
            baseline=REFERENCES[profile](case['public'],[])
            expected_ready=dict(schema='public-stream-worker/v1',kind='ready',profile=profile,completed=1,
                initial_digest=fingerprint(case['public']),projection=baseline['projection'])
            if profile=='deployment': expected_ready['executor_effects']=0
            compare(expected_ready,rows[0],'ready','envelope')
            check_event(case,[case['event']],rows[1],replayed=True,
                reference=lambda public,prefix:dict(status='UNKNOWN',projection=baseline['projection']))
            if fingerprint(rows[1]['record'])!=result['reply_digest']:
                raise ValueError('cancelled reply differs from decision archive')
            check_event(case,[case['event'],next_event],rows[2],
                reference=lambda public,prefix:REFERENCES[profile](public,prefix[1:]))
            if rows[0]['completed']!=1 or rows[1]['record']['outcome']['status']!='UNKNOWN' or not rows[1]['replayed']:
                raise ValueError('cancelled event reply differs')
            compare(rows[0]['projection'],rows[1]['record']['projection'],'cancelled')
            reference=REFERENCES[profile](case['public'],[next_event])
            compare(reference['projection'],rows[2]['record']['projection'],'continued')
            if rows[2]['record']['step']!=2 or rows[2]['record']['outcome']['status']!=reference['status']:
                raise ValueError('continued event outcome differs')
            expected.append(dict(profile=profile,cut=cut,passed=True,cancelled_status='UNKNOWN',continued_status=reference['status']))
    if receipt['results']!=expected:
        raise ValueError('reconciliation probe results differ')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True)
    results=[run_case(profile,cut,args.output/(profile+'-'+cut)) for profile in ('admission','deployment') for cut in CUTS]
    files={str(p.relative_to(args.output)):digest_file(p) for p in sorted(args.output.rglob('*')) if p.is_file()}
    write_json(args.output/'report.json',dict(schema=SCHEMA,sources=source_files(),files=files,results=results))
    verify_report(args.output)
    print(canonical(dict(cases=len(results),passed=True,output=str(args.output))),flush=True)


if __name__=='__main__':
    main()
