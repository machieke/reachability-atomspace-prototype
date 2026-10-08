"""Common measured accounting of fully validated native graphs; no discovery."""
from time import perf_counter_ns
from reachability.atomspace_adapter import _hex
from experimental_native_recall.schema import SCHEMA


def readback_bytes(graph,binding,relations,records):
    # The C++ Value map may emit values in any handle order; total bytes do not
    # depend on that order. No serialization work is elided from native loading.
    total=0
    for i,ref in enumerate(graph.aliases):
        atom=graph.atoms[ref]
        text=('L '+str(len(atom[1]))+''.join(' '+str(x) for x in atom[1])) if atom[0]=='L' else atom[0]+' '+_hex(atom[1])
        total+=len(f'A {i} {ref} {text}\n'.encode())
    for (a,k),value in graph.values.items():
        if isinstance(value,str):text='S '+str(a)+' '+str(k)+' '+_hex(value)
        else:text='F '+str(a)+' '+str(k)+' '+str(len(value))+''.join(' '+format(x,'.17g') for x in value)
        total+=len((text+'\n').encode())
    return total+len(f'READY {_hex(binding)} {graph.size} {relations} {records} {len(graph.values)}\n'.encode())


def account(projection,graph,receipt):
    t=perf_counter_ns();p=projection;r=receipt
    metadata=next(i for i,a in graph.atoms.items() if a==('N','view:'+r.snapshot_binding))
    values={key:v for (a,key),v in graph.values.items() if a==metadata}
    envelope_key=next((k for k in values if graph.atoms[k]==('P','snapshot:external-envelope/v1')),None)
    full=envelope_key is None
    chunks=[]
    if full:
        for n in range((p.export_bytes+32767)//32768):
            key=next(k for k in values if graph.atoms[k]==('P','snapshot:chunk:'+str(n)))
            chunks.append(values[key])
    string_bytes=sum(len(v.encode()) for v in graph.values.values() if isinstance(v,str))
    result=dict(projection_schema=getattr(r,'projection_schema',SCHEMA),
        completeness=dict(authoritative_capture=True,supported_discovery_universe=True,native_projection_readback=True,whole_snapshot_embedded=full),
        public_export_bytes=p.export_bytes,source_records=len(p.catalog),source_payload_bytes=sum(len(x[2].encode()) for x in p.catalog.values()),
        native_atoms=graph.size,emitted_atom_commands=len(graph.aliases),native_values=len(graph.values),metadata_values=len(values),metadata_key_atoms=len(values),
        metadata_value_content_bytes=sum(len(v.encode()) if isinstance(v,str) else 8*len(v) for v in values.values()),
        whole_snapshot_chunk_bytes=sum(len(x.encode()) for x in chunks),envelope_bytes=0 if full else len(values[envelope_key].encode()),
        native_string_value_content_bytes=string_bytes,native_float_value_scalars=sum(len(v) for v in graph.values.values() if not isinstance(v,str)),
        native_load_wire_bytes=r.counts['load_bytes'],native_readback_wire_bytes=readback_bytes(graph,r.snapshot_binding,r.counts['relations'],len(p.catalog)))
    result['accounting_ns']=perf_counter_ns()-t;return result


class MeasuredObserver:
    """Same accounting after original full or compact observation, charged alike."""
    def __init__(self,observer):self.observer=observer
    @property
    def backend(self):return self.observer.backend
    def close(self):return self.observer.close()
    def rebuild(self):return self.observer.rebuild()
    def __call__(self,*args,**kwargs):
        public,frame,view,costs=self.observer(*args,**kwargs)
        events=costs['native_retrieval']['events']
        if any(e['kind']=='open_view' for e in events):
            data=account(self.backend.projection,self.backend.graph,self.backend.receipt)
            costs['payload']=data;costs['observation_inclusive_ns']+=data['accounting_ns']
        return public,frame,view,costs
