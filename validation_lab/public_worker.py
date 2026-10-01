"""Evaluator-owned, bounded pipes; only runtime Python files enter the bundle.

Isolated Python startup, clean environment and a separate cwd limit accidental
leakage. They are not an OS filesystem, network or hostile-code sandbox.
"""
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
from time import monotonic

from reachability.trace_protocol import canonical
from .shrink_replay import digest_file

ROOT = Path(__file__).resolve().parents[1]
MAX_RESPONSE = 4 * 1024 * 1024


class WorkerError(RuntimeError):
    pass


class WorkerTimeout(WorkerError):
    pass


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def runtime_bundle(path):
    path = Path(path)
    package = path/'reachability'
    package.mkdir(parents=True)
    for source in sorted((ROOT/'reachability').glob('*.py')):
        shutil.copyfile(source,package/source.name)
    receipt = {str(p.relative_to(path)):digest_file(p) for p in sorted(package.glob('*.py'))}
    write_json(path/'bundle.json',receipt)
    return receipt


class PublicWorker:
    def __init__(self, bundle, profile, state, evidence, *, resume=False, timeout=15, max_response=MAX_RESPONSE):
        self.evidence = Path(evidence).resolve()
        self.evidence.mkdir(parents=True)
        self.work = self.evidence/'cwd'
        self.work.mkdir()
        self.timeout,self.max_response = timeout,max_response
        self.buffer,self.closed = b'',False
        # This bootstrap contains only a runtime-bundle path. No case filename,
        # evaluator module, future event, schedule or reference state is passed.
        bootstrap = 'import sys; sys.path.insert(0, '+repr(str(Path(bundle).resolve()))+'); from reachability.stream_worker import main; main()'
        argv = [sys.executable,'-I','-B','-c',bootstrap,'--profile',profile,'--database-dir',str(Path(state).resolve())]
        if resume:
            argv.append('--resume')
        environment = {'PATH':os.defpath,'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
        self.input_log = (self.evidence/'stdin.jsonl').open('wb')
        self.output_log = (self.evidence/'stdout.jsonl').open('wb')
        self.error_log = (self.evidence/'stderr.log').open('wb')
        try:
            self.process = subprocess.Popen(argv,cwd=self.work,env=environment,stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=self.error_log,bufsize=0,close_fds=True)
        except BaseException:
            for stream in (self.input_log,self.output_log,self.error_log):
                stream.close()
            raise
        os.set_blocking(self.process.stdin.fileno(),False)
        os.set_blocking(self.process.stdout.fileno(),False)
        write_json(self.evidence/'launch.json',dict(schema='public-worker-launch/v1',argv=argv,environment=environment,
            cwd=str(self.work),pid=self.process.pid,parent_pid=os.getpid(),profile=profile,resume=resume,
            timeout_seconds=timeout,max_response_bytes=max_response))

    def request(self, value):
        data = (canonical(value)+'\n').encode()
        if len(data)>65536:
            raise ValueError('request exceeds public frame bound')
        return self.exchange_bytes(data)

    def exchange_bytes(self, data):
        """Raw boundary entry for malformed-frame tests; logs precede parsing."""
        if self.closed:
            raise WorkerError('worker is closed')
        self.input_log.write(data)
        self.input_log.flush()
        deadline,sent = monotonic()+self.timeout,0
        try:
            while sent<len(data):
                if not select.select([], [self.process.stdin], [], max(0,deadline-monotonic()))[1]:
                    raise WorkerTimeout('worker input deadline expired')
                sent += os.write(self.process.stdin.fileno(),data[sent:])
        except (BrokenPipeError,OSError) as error:
            raise WorkerError('worker input pipe closed') from error
        while b'\n' not in self.buffer:
            if not select.select([self.process.stdout], [], [], max(0,deadline-monotonic()))[0]:
                raise WorkerTimeout('worker response deadline expired')
            chunk = os.read(self.process.stdout.fileno(),65536)
            if not chunk:
                raise WorkerError('worker exited without a complete response')
            self.output_log.write(chunk)
            self.output_log.flush()
            self.buffer += chunk
            if len(self.buffer)>self.max_response:
                raise WorkerError('worker response exceeds size bound')
        line,self.buffer = self.buffer.split(b'\n',1)
        if self.buffer:
            raise WorkerError('worker emitted unsolicited extra response bytes')
        def unique(pairs):
            value={}
            for key,item in pairs:
                if key in value:
                    raise WorkerError('duplicate worker response field')
                value[key]=item
            return value
        def invalid(_):
            raise WorkerError('nonfinite worker response')
        try:
            return json.loads(line,object_pairs_hook=unique,parse_constant=invalid)
        except (ValueError,UnicodeError) as error:
            raise WorkerError('malformed worker JSON response') from error

    def stop(self, *, kill=False):
        if self.closed:
            return
        self.closed=True
        requested='kill' if kill else 'eof'
        try:
            if kill and self.process.poll() is None:
                self.process.kill()
            self.process.stdin.close()
            try:
                code=self.process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                code=self.process.wait(timeout=5)
                requested='deadline-kill'
            # Keep any incomplete or unsolicited tail, including crash output.
            while True:
                chunk=os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    break
                self.output_log.write(chunk)
            write_json(self.evidence/'exit.json',dict(schema='public-worker-exit/v1',requested=requested,returncode=code))
        finally:
            self.process.stdout.close()
            for stream in (self.input_log,self.output_log,self.error_log):
                stream.close()
        if not kill and (code!=0 or requested=='deadline-kill'):
            raise WorkerError('worker did not exit cleanly')
