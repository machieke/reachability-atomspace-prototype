"""Independent source/whole-graph checks; compact construction is not the oracle."""
from functools import lru_cache
from hashlib import sha256
from reachability.trace_protocol import canonical
from experimental_native_recall.schema import Projection as FullProjection
from experimental_online_pln.agenda import wire


def envelope(snapshot):
    public=canonical(snapshot.records()).encode()
    return dict(schema='native-public-snapshot-envelope/v1',projection_schema='native-atomspace-recall-compact/v1',
        canonical_encoding='reachability.trace_protocol.canonical(snapshot.records())/utf-8',snapshot_sha256=sha256(public).hexdigest(),
        snapshot_bytes=len(public),snapshot_binding=snapshot.binding,snapshot_representation='external-full-capture')


def nonmetadata_graph(p,graph,compact):
    """Normalize handles; ignore only declared duplicate-blob/envelope metadata.

    This is an evaluator comparison, not projection construction or pruning.
    Shared keys with any remaining atom/Value use must stay represented.
    """
    metadata=next(i for i,a in graph.atoms.items() if a==('N','view:'+p.binding))
    names=['snapshot:external-envelope/v1'] if compact else ['snapshot:chunk:'+str(i) for i in range((p.export_bytes+32767)//32768)]
    keys={next(k for (a,k) in graph.values if a==metadata and graph.atoms[k]==('P',name)) for name in names}
    values={pair:v for pair,v in graph.values.items() if not(pair[0]==metadata and pair[1] in keys)}
    used={x for atom in graph.atoms.values() if atom[0]=='L' for x in atom[1]}|{x for pair in values for x in pair}
    omitted=keys-used
    @lru_cache(None)
    def token(ref):
        atom=graph.atoms[ref];data=(atom[0],tuple(token(x) for x in atom[1])) if atom[0]=='L' else atom
        return sha256(canonical(data).encode()).hexdigest()
    atoms={token(i) for i in graph.atoms if i not in omitted}
    vals=sorted((token(a),token(k),v) for (a,k),v in values.items())
    return dict(atoms=sorted(atoms),values=vals)


def expected_graph(p):
    from reachability.atomspace_adapter import NativeGraph
    _,aliases,atoms,values=p.wire();marker=int(any(a!=k for a,k in values) and ('P','*-IsKeyFlag-*') not in atoms.values())
    return NativeGraph(aliases,atoms,values,len(atoms)+marker)


def check_projection(snapshot,compact_projection,compact_graph):
    full=FullProjection(snapshot);graph=expected_graph(full)
    if full.catalog!=compact_projection.catalog:raise AssertionError('complete source catalog/payload fidelity')
    if nonmetadata_graph(full,graph,False)!=nonmetadata_graph(compact_projection,compact_graph,True):raise AssertionError('nonmetadata source/registered structure differs')
    return dict(source_records=len(full.catalog),full_atoms=graph.size,compact_atoms=compact_graph.size)


def result_semantics(result):
    data=wire(result);data.pop('elapsed_ns');return data
