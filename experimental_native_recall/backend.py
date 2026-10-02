"""Bounded immutable native view lifetime and typed query transport."""
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import subprocess
from time import monotonic,perf_counter_ns
from reachability.adapter_runtime import AdapterError,ROOT,verify_native_build,lockfile
from reachability.atomspace_adapter import NativeGraph,_hex,_unhex
from reachability.model import Literal
from experimental_online_pln.agenda import wire
from .schema import Projection,QueryLimits,KINDS,SCHEMA,source_id


class RecallError(AdapterError):pass
class IncompleteRecall(Exception):
    def __init__(self,result):self.result=result;super().__init__(result.reason)


@dataclass(frozen=True)
class ViewReceipt:
    view_id: str
    authority: str
    context_id: str
    snapshot_binding: str
    schema: str
    build_identity: str
    complete: bool
    source_ids: tuple
    counts: dict
    input_sha256: str
    readback_sha256: str


@dataclass(frozen=True)
class QueryResult:
    view_id: str
    request: dict
    ids: tuple
    complete: bool
    reason: str
    visits: int
    elapsed_ns: int
    details: tuple=()


def verify_build(root=ROOT/'artifacts'):
    root=Path(root);verify_native_build(root)
    try:
        receipt=json.loads((root/'recall-build.json').read_text())
        expected={'base_receipt_sha256':root/'adapter-build.json','lock_sha256':ROOT/'adapters.lock.json',
                  'source_sha256':ROOT/'native/atomspace_recall.cc','script_sha256':ROOT/'scripts/build_native_recall.py',
                  'binary_sha256':root/'bin/atomspace_recall'}
        if receipt['schema']!='native-recall-build/v1':raise ValueError('schema')
        for key,path in expected.items():
            if sha256(path.read_bytes()).hexdigest()!=receipt[key]:raise ValueError('build drift: '+key)
    except (OSError,KeyError,ValueError) as error:raise RecallError('missing/invalid recall build; run scripts/build_native_recall.py: '+str(error)) from error
    return sha256((root/'recall-build.json').read_bytes()).hexdigest()


class Process:
    """One immutable epoch; bounded binary pipes with explicit request deadlines."""
    def __init__(self,binary,timeout=30):
        if not 0<timeout<=30:raise ValueError('timeout bound')
        self.timeout=timeout;self.buffer=b''
        self.process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):os.set_blocking(stream.fileno(),False)
    def close(self):
        if self.process.poll() is None:self.process.kill()
        self.process.wait(timeout=2)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):stream.close()
    def _fail(self,message):
        try:extra=os.read(self.process.stderr.fileno(),1000).decode(errors='replace')
        except (BlockingIOError,OSError):extra=''
        raise RecallError(message+(': '+extra if extra else ''))
    def send(self,data):
        deadline=monotonic()+self.timeout;sent=0
        while sent<len(data):
            remaining=deadline-monotonic()
            if remaining<=0:self._fail('native write timeout')
            if not select.select([], [self.process.stdin], [], remaining)[1]:self._fail('native write timeout')
            try:sent+=os.write(self.process.stdin.fileno(),data[sent:sent+65536])
            except (BrokenPipeError,OSError) as error:self._fail('native helper lost: '+str(error))
    def receive(self,end_prefix):
        deadline=monotonic()+self.timeout;lines=[];size=0
        while True:
            while b'\n' in self.buffer:
                raw,self.buffer=self.buffer.split(b'\n',1);size+=len(raw)+1
                if len(raw)>262144 or size>33554432:self._fail('native response bound')
                try:line=raw.decode('ascii')
                except UnicodeError:self._fail('malformed native response encoding')
                lines.append(line)
                if line.startswith(end_prefix):return lines
            if len(self.buffer)>262144:self._fail('native line bound')
            remaining=deadline-monotonic()
            if remaining<=0 or not select.select([self.process.stdout],[],[],max(0,remaining))[0]:self._fail('native response timeout')
            data=os.read(self.process.stdout.fileno(),65536)
            if not data:self._fail('native helper lost/incomplete response')
            self.buffer+=data


def readback(lines,expected):
    encoded,expected_aliases,expected_atoms,expected_values=expected
    aliases=[];atoms={};values={}
    try:
        for line in lines[:-1]:
            t=line.split();tag=t[0]
            if tag=='A':
                if int(t[1])!=len(aliases):raise ValueError('atom sequence')
                ref=int(t[2]);aliases.append(ref)
                if t[3]=='L':
                    if int(t[4])!=len(t)-5:raise ValueError('arity')
                    atom=('L',tuple(map(int,t[5:])))
                elif t[3] in ('N','P') and len(t)==5:atom=(t[3],_unhex(t[4]))
                else:raise ValueError('atom type')
                if ref in atoms and atoms[ref]!=atom:raise ValueError('alias conflict')
                atoms[ref]=atom
            elif tag in ('S','F'):
                pair=(int(t[1]),int(t[2]))
                if pair in values:raise ValueError('duplicate Value')
                if tag=='S' and len(t)==4:value=_unhex(t[3])
                elif tag=='F' and int(t[3])==len(t)-4:value=tuple(map(float,t[4:]))
                else:raise ValueError('Value syntax')
                values[pair]=value
            else:raise ValueError('unknown readback entry')
        ready=lines[-1].split()
        if len(ready)!=6 or ready[0]!='READY':raise ValueError('missing seal')
        size=int(ready[2]);marker=int(any(a!=k for a,k in values) and ('P','*-IsKeyFlag-*') not in atoms.values())
        if tuple(aliases)!=expected_aliases or atoms!=expected_atoms or values!=expected_values or size!=len(atoms)+marker:
            raise ValueError('structural/Value readback differs')
        return NativeGraph(tuple(aliases),atoms,values,size),ready
    except (ValueError,KeyError,IndexError,UnicodeError) as error:raise RecallError('invalid native readback: '+str(error)) from error


class Backend:
    def __init__(self,root=ROOT/'artifacts',limits=QueryLimits(),timeout=30):
        self.root=Path(root);self.limits=limits;self.timeout=timeout
        self.process=None;self.receipt=None;self.projection=None;self.graph=None
        self.costs=defaultdict(int);self.events=[];self.query_count=0;self.epochs=0
    def close(self):
        if self.process is not None:self.process.close()
        self.process=self.receipt=self.projection=self.graph=None
    def open_view(self,snapshot):
        start=perf_counter_ns();binding=snapshot.binding
        if self.receipt is not None and self.receipt.snapshot_binding==binding:
            if self.process.process.poll() is not None:
                self.close();raise RecallError('native helper lost; explicit rebuild required')
            self.costs['view_reuses']+=1;return self.receipt
        old=self.receipt
        self.close()
        try:
            check_start=perf_counter_ns();build=verify_build(self.root)
            self.costs['native_build_verification_ns']+=perf_counter_ns()-check_start
            p=Projection(snapshot);self.costs['projection_construction_ns']+=p.elapsed_ns
            self.costs['projection_snapshot_serialization_ns']+=p.serialization_ns
            encode_start=perf_counter_ns();expected=p.wire();encoded=expected[0]
            self.costs['projection_wire_ns']+=perf_counter_ns()-encode_start
            boot=perf_counter_ns();self.process=Process(self.root/'bin/atomspace_recall',self.timeout)
            header=self.process.receive('native-atomspace-recall/v1 ')
            if header!=[SCHEMA+' '+lockfile()['sources']['atomspace']['commit']]:raise RecallError('native pin/protocol header mismatch')
            self.costs['native_startup_ns']+=perf_counter_ns()-boot
            load=perf_counter_ns();self.process.send(encoded);lines=self.process.receive('READY ')
            self.costs['native_load_and_readback_io_ns']+=perf_counter_ns()-load
            validate=perf_counter_ns();graph,ready=readback(lines,expected)
            if _unhex(ready[1])!=binding or int(ready[4])!=len(p.catalog) or int(ready[5])!=len(expected[3]):
                raise RecallError('native view receipt mismatch')
            self.costs['readback_validation_ns']+=perf_counter_ns()-validate
            receipt=ViewReceipt(binding,p.authority,p.context,binding,SCHEMA,build,True,tuple(sorted(p.catalog)),
                dict(atoms=graph.size,relations=int(ready[3]),values=len(graph.values),source_records=len(p.catalog),
                     load_bytes=len(encoded),public_export_bytes=p.export_bytes),sha256(encoded).hexdigest(),
                sha256(('\n'.join(lines)+'\n').encode()).hexdigest())
            self.projection,self.graph,self.receipt=p,graph,receipt;self.query_count=0;self.epochs+=1
            self.events.append(dict(kind='open_view',receipt=wire(receipt),epoch=self.epochs,replaced=old is not None))
            self.costs['view_open_inclusive_ns']+=perf_counter_ns()-start
            if old is not None:self.costs['epoch_replacement_inclusive_ns']+=perf_counter_ns()-start
            return receipt
        except Exception as error:
            self.events.append(dict(kind='view_error',binding=binding,error=type(error).__name__+': '+str(error)))
            self.close()
            if isinstance(error,RecallError):raise
            raise RecallError('native view failed: '+str(error)) from error
    def query(self,kind,*,binding,context=None,literal=None,report_type=None,target=None,record_id=None,limits=None):
        start=perf_counter_ns();limits=limits or self.limits
        if self.receipt is None or binding!=self.receipt.snapshot_binding:raise RecallError('stale/unpublished live view')
        if kind not in KINDS:raise RecallError('unknown typed native query')
        if self.process.process.poll() is not None:
            self.close();raise RecallError('native helper lost; explicit rebuild required')
        request=dict(kind=kind,context=context,literal=wire(literal),report_type=report_type,target=wire(target),record_id=record_id,
                     limits=wire(limits))
        if self.query_count>=limits.queries:
            r=QueryResult(binding,request,(),False,'QUERY_BOUND',0,perf_counter_ns()-start)
            self.events.append(dict(kind='query',result=wire(r)));return r
        self.query_count+=1
        nonce=str(self.query_count)
        args=['Q',nonce,_hex(binding),kind,str(limits.visits),str(limits.results)]
        def add_literal(value):
            if type(value) is not Literal:raise ValueError('typed literal query required')
            strings=(value.statement.predicate,*value.statement.arguments)
            if len(strings)>4096 or sum(len(s.encode()) for s in strings)>65536:raise ValueError('query literal size bound')
            args.extend(['+' if value.positive else '-',_hex(strings[0]),str(len(strings)-1),*map(_hex,strings[1:])])
        if kind=='record':args.append(_hex(record_id))
        else:
            args.append(_hex(context))
            if kind=='probes':
                if report_type not in ('numeric','product','health'):raise ValueError('typed probe channel required')
                args.append(report_type)
                if report_type=='numeric':add_literal(target)
                else:args.append(_hex(target))
            elif kind not in ('models','all_rules','all_current'):add_literal(literal)
        data=(' '.join(args)+'\n').encode()
        if len(data)>262144:raise ValueError('query transport bound')
        try:
            self.process.send(data);lines=self.process.receive('END '+nonce)
            t=lines[0].split()
            if len(t)!=6 or t[:2]!=['QRESULT',nonce] or t[2] not in ('COMPLETE','INCOMPLETE') or lines[-1]!='END '+nonce:
                raise ValueError('query header/nonce mismatch')
            visits,count=int(t[4]),int(t[5]);complete=t[2]=='COMPLETE';reason=t[3]
            if (visits>limits.visits or count>limits.results or count!=len(lines)-2 or visits<0 or count<0
                or complete!=(reason=='COMPLETE') or reason not in ('COMPLETE','VISIT_BOUND','RESULT_BOUND')):
                raise ValueError('query completeness/bound mismatch')
            ids=[];details=[]
            for line in lines[1:-1]:
                row=line.split();ident=_unhex(row[1])
                if ident not in self.projection.catalog:raise ValueError('unknown returned source ID')
                if kind=='record':
                    if len(row)!=3 or row[0]!='D' or ident!=record_id:raise ValueError('record response syntax')
                    if _unhex(row[2])!=self.projection.catalog[ident][2]:raise ValueError('record Value differs from epoch source')
                    detail=None
                else:
                    if row[0]!='I' or int(row[2])!=len(row)-3:raise ValueError('query structural detail syntax')
                    refs=tuple(map(int,row[3:]));record=self.projection.catalog[ident][1]
                    if kind in ('producers','all_rules'):
                        by_ref={self.graph.aliases[r]:lit for lit,r in self.projection.literal_refs.items()}
                        detail=tuple(by_ref[r] for r in refs)
                        if detail!=record.deduction.premises:raise ValueError('native ordered premises differ from exact source')
                    elif kind=='models':
                        detail=tuple(self.graph.atoms[r][1].removeprefix('record:') for r in refs)
                        if detail!=tuple(source_id('support',context,p) for p in record.premise_revision_ids):raise ValueError('native exact model supports differ')
                    elif kind=='probes':
                        if len(refs)!=1:raise ValueError('probe opportunity detail')
                        detail=self.graph.atoms[refs[0]][1]
                        if detail!='integer:'+str(record.opportunity):raise ValueError('native opportunity differs')
                    else:
                        if refs:raise ValueError('unexpected query detail')
                        detail=None
                ids.append(ident);details.append(detail)
            if ids!=sorted(set(ids)):raise ValueError('duplicate/noncanonical native result IDs')
            r=QueryResult(binding,request,tuple(ids),complete,reason,visits,perf_counter_ns()-start,tuple(details))
            self.costs['native_queries']+=1;self.costs['native_relation_visits']+=visits;self.costs['native_results']+=count
            self.costs['native_query_inclusive_ns']+=r.elapsed_ns
            self.events.append(dict(kind='query',result=wire(r),response_sha256=sha256(('\n'.join(lines)+'\n').encode()).hexdigest()))
            return r
        except Exception as error:
            self.events.append(dict(kind='query_error',view_id=binding,request=request,error=str(error)))
            self.close()
            if isinstance(error,RecallError):raise
            raise RecallError('invalid native query response: '+str(error)) from error
    def recall(self,kind,**args):
        result=self.query(kind,**args)
        if not result.complete:raise IncompleteRecall(result)
        return tuple(self.projection.catalog[i][1] for i in result.ids)
