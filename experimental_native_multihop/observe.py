"""Coherent frozen assessment plus disposable native discovery for one session."""
from time import perf_counter_ns
from experimental_online_pln.agenda import wire
from experimental_work_bridge.capture import acquire
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import evaluate
from .backend import RecordedBackend as Backend
from experimental_work_bridge.project import Limits
from .project import project
from .access import Access


class Observer:
    def __init__(self,backend=None):self.backend=backend or Backend();self.last={};self.failed=None
    def close(self):self.backend.close()
    def rebuild(self):
        """Explicit caller decision after a failed helper, no automatic restart."""
        self.backend.close();self.failed=None
    def __call__(self,session,manifest,graph_limits=Limits()):
        started=perf_counter_ns();offset=len(self.backend.events);before=dict(self.backend.costs)
        with session.service._lock:
            frame,acquisition=acquire(session);public=session.read();cap=immutable(frame.data()['capture']);ab={};evaluation={}
            for kind in ('A','B'):ab[kind],evaluation[kind]=evaluate(cap,manifest,kind)
            access=Access(self.backend,public,blocked=self.failed);view,projection=project(frame,manifest,ab['A'],ab['B'],access,graph_limits)
        reason=view.data()['reason']
        if reason.startswith(('NATIVE_VIEW_FAILED','NATIVE_QUERY_FAILED','NATIVE_STALE')):self.failed=reason
        delta={k:v-before.get(k,0) for k,v in self.backend.costs.items()}
        self.last=dict(schema='native-multihop-retrieval/v1',binding=public.binding,epoch=self.backend.epochs,
            events=wire(self.backend.events[offset:]),costs=delta,query_and_decode_inclusive_ns=access.query_ns,
            view_open_inclusive_ns=access.open_ns,python_traversal_tuples_serialization_ns=max(0,projection.get('dependency_discovery_ns',0)-access.query_ns-access.open_ns),
            capture_bytes=len(frame.payload_json.encode()),queried_reports=access.reports,complete=view.data()['complete'],reason=view.data()['reason'],fallback=None)
        return public,frame,view,dict(acquisition=acquisition,evaluation=evaluation,projection=projection,
            native_retrieval=self.last,observation_inclusive_ns=perf_counter_ns()-started)
