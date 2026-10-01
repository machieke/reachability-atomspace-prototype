"""Bounded JSON-lines process boundary for three existing public trace profiles.

All profiles support completed-command checkpoint recovery. The worker receives public
initial state, then one delivered command per response; no evaluator imports.
"""
import argparse
from pathlib import Path
import sys

from .admission_protocol import AdmissionInitial
from .dispatch_worker_state import DurableDispatchSession
from .trace_worker_state import DurableAdmissionSession, DurableDeploymentSession
from .trace_protocol import DeploymentInitial, canonical, fingerprint, read_json

SCHEMA = 'public-stream-worker/v1'
MAX_INPUT = 65536
END = object()


def read_frame(stream):
    line = stream.readline(MAX_INPUT+1)
    if not line:
        return END
    if len(line) > MAX_INPUT or not line.endswith(b'\n'):
        raise ValueError('public input requires a complete JSON line of at most 64 KiB')
    return read_json(line.decode('utf-8'))


def emit(value):
    sys.stdout.write(canonical(value)+'\n')
    sys.stdout.flush()


def serve(profile, directory, *, resume=False, input_stream=None):
    stream = sys.stdin.buffer if input_stream is None else input_stream
    public = read_frame(stream)
    if public is END:
        raise ValueError('public initial message required')
    if profile == 'admission':
        initial = AdmissionInitial.parse(public)
        session = DurableAdmissionSession(initial,directory,resume=resume)
    elif profile in ('deployment','dispatch'):
        initial = DeploymentInitial.parse(public)
        session = (DurableDispatchSession(initial,directory,resume=resume) if profile == 'dispatch'
                   else DurableDeploymentSession(initial,directory,resume=resume))
    else:
        raise ValueError('unsupported public worker profile')
    with session:
        ready = dict(schema=SCHEMA,kind='ready',profile=profile,initial_digest=fingerprint(public),
            completed=len(session.completed),projection=session.projection())
        if profile != 'admission':
            ready['executor_effects'] = session.executor.total_effects
        emit(ready)
        while True:
            message = read_frame(stream)
            if message is END:
                break
            row = session.apply(message)
            emit(dict(schema=SCHEMA,kind='event',profile=profile,event_digest=fingerprint(message),
                replayed=session.replayed,record=row))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('admission','deployment','dispatch'),required=True)
    parser.add_argument('--database-dir',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    try:
        serve(args.profile,args.database_dir,resume=args.resume)
    except Exception as error:
        print(type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)


if __name__=='__main__':
    main()
