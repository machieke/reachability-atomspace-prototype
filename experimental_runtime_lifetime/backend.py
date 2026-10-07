"""Only verification/launch lifetime changes; native view/query code is frozen."""
from dataclasses import dataclass
from hashlib import sha256
import os,subprocess
from time import perf_counter_ns
from experimental_native_recall import backend as legacy
from experimental_native_recall.backend import RecallError,ViewReceipt,Process,_unhex,lockfile
from experimental_native_recall.schema import Projection,SCHEMA
from experimental_online_pln.agenda import wire
from experimental_native_multihop.backend import RecordedBackend
from .generation import Generation,ENV

@dataclass(frozen=True)
class GenerationViewReceipt(ViewReceipt):
    runtime_generation_id:str

class GenerationProcess(Process):
    def __init__(self,generation,timeout=30):
        if not 0<timeout<=30:raise ValueError('timeout bound')
        self.generation=generation;self.timeout=timeout;self.buffer=b'';self.checked=False
        generation.check(generation.root,generation.generation_id)
        self.process=subprocess.Popen(generation.command(),env=dict(ENV),pass_fds=generation.fds,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):os.set_blocking(stream.fileno(),False)
    def receive(self,end_prefix):
        lines=super().receive(end_prefix)
        if not self.checked:
            self.generation.check_loaded(self.process.pid);self.checked=True
        return lines

class Backend(RecordedBackend):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.generation=None;self.generations=[]
    def require_generation(self):
        t=perf_counter_ns()
        try:
            if self.generation is None:
                self.generation=Generation(self.root);self.generations.append(self.generation);self.generation.prepare()
            self.generation.check(self.root,self.generation.generation_id)
        except RecallError:
            self.close();raise
        finally:self.costs['runtime_preparation_and_guard_ns']+=perf_counter_ns()-t
    def shutdown(self):
        self.close()
        if self.generation is not None:self.generation.close()
    def reconstruct(self):
        """Explicit runtime replacement, retaining all costs/events/epoch counts."""
        self.shutdown();self.generation=None
    def runtime_costs(self):
        totals={}
        for generation in self.generations:
            for name,value in generation.costs.items():totals[name]=totals.get(name,0)+value
        return totals
    def query(self,*args,**kwargs):
        self.require_generation();return super().query(*args,**kwargs)
    def open_view(self,snapshot):
        start=perf_counter_ns();self.require_generation();binding=snapshot.binding
        if self.receipt is not None and self.receipt.snapshot_binding==binding:
            if self.process.process.poll() is not None:
                self.close();raise RecallError('native helper lost; explicit rebuild required')
            self.costs['view_reuses']+=1;return self.receipt
        old=self.receipt
        self.close()
        try:
            build=self.generation.descriptor['build_identity']
            p=Projection(snapshot);self.costs['projection_construction_ns']+=p.elapsed_ns
            self.costs['projection_snapshot_serialization_ns']+=p.serialization_ns
            encode_start=perf_counter_ns();expected=p.wire();encoded=expected[0]
            self.costs['projection_wire_ns']+=perf_counter_ns()-encode_start
            boot=perf_counter_ns();self.process=GenerationProcess(self.generation,self.timeout)
            header=self.process.receive('native-atomspace-recall/v1 ')
            if header!=[SCHEMA+' '+self.generation.descriptor['atomspace_pin']]:raise RecallError('native pin/protocol header mismatch')
            self.costs['native_startup_ns']+=perf_counter_ns()-boot
            load=perf_counter_ns();self.process.send(encoded);lines=self.process.receive('READY ')
            self.costs['native_load_and_readback_io_ns']+=perf_counter_ns()-load
            validate=perf_counter_ns();graph,ready=legacy.readback(lines,expected)
            if _unhex(ready[1])!=binding or int(ready[4])!=len(p.catalog) or int(ready[5])!=len(expected[3]):
                raise RecallError('native view receipt mismatch')
            self.costs['readback_validation_ns']+=perf_counter_ns()-validate
            receipt=GenerationViewReceipt(binding,p.authority,p.context,binding,SCHEMA,build,True,tuple(sorted(p.catalog)),
                dict(atoms=graph.size,relations=int(ready[3]),values=len(graph.values),source_records=len(p.catalog),
                     load_bytes=len(encoded),public_export_bytes=p.export_bytes),sha256(encoded).hexdigest(),
                sha256(('\n'.join(lines)+'\n').encode()).hexdigest(),self.generation.generation_id)
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
