"""Frozen session generation/query paths, with separately declared compact view."""
from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter_ns
from experimental_native_recall import backend as legacy
from experimental_native_recall.backend import RecallError,_unhex
from experimental_native_recall.schema import SCHEMA
from experimental_online_pln.agenda import wire
from experimental_runtime_lifetime.backend import Backend as SessionBackend,GenerationViewReceipt,GenerationProcess
from .schema import Projection,PROJECTION_SCHEMA,COMPLETENESS,validate_envelope

@dataclass(frozen=True)
class CompactViewReceipt(GenerationViewReceipt):
    projection_schema:str
    full_snapshot_envelope:dict
    completeness:dict

class Backend(SessionBackend):
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
            self.costs['snapshot_hash_ns']+=p.snapshot_hash_ns;self.costs['envelope_construction_ns']+=p.envelope_construction_ns
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
            t=perf_counter_ns();envelope=validate_envelope(p,snapshot,graph);self.costs['envelope_validation_inclusive_ns']+=perf_counter_ns()-t
            receipt=CompactViewReceipt(binding,p.authority,p.context,binding,SCHEMA,build,True,tuple(sorted(p.catalog)),
                dict(atoms=graph.size,relations=int(ready[3]),values=len(graph.values),source_records=len(p.catalog),
                     load_bytes=len(encoded),public_export_bytes=p.export_bytes),sha256(encoded).hexdigest(),
                sha256(('\n'.join(lines)+'\n').encode()).hexdigest(),self.generation.generation_id,PROJECTION_SCHEMA,envelope,dict(COMPLETENESS))
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
