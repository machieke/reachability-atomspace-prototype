"""Epoch-bound query-only record access; no parallel Python membership index."""
from time import perf_counter_ns
from experimental_online_pln.agenda import wire
from experimental_native_recall.backend import RecallError
from reachability.model import Literal,Statement
from reachability.trace_protocol import canonical


class DiscoveryFailure(Exception):pass


def literal(value):
    return Literal(Statement(value['statement']['predicate'],tuple(value['statement']['arguments'])),value['positive'])


class Access:
    def __init__(self,backend,snapshot,blocked=None):
        self.backend=backend;self.snapshot=snapshot;self.binding=snapshot.binding
        self.blocked=blocked;self.cache={};self.opened=False;self.query_ns=0;self.open_ns=0;self.reports={}
    def validate(self,frame):
        """Full-source coherence check, before any relevance membership lookup."""
        f=frame.data();s=self.snapshot;inv=f['inventory'];cap=f['capture']
        authority=next((c[1] for c in s.contracts if c[0]=='authority-identity/v1'),None)
        if authority!=cap['authority'] or wire(s.context)!=cap['context']:
            raise DiscoveryFailure('NATIVE_STALE_CAPTURE_BINDING')
        if sorted(wire(s.numerical),key=canonical)!=sorted(cap['probability_export'][3],key=canonical):
            raise DiscoveryFailure('NATIVE_STALE_CAPTURE_BINDING')
        for name in ('rules','models','revoked_models','probes'):
            if sorted(wire(getattr(s,name)),key=canonical)!=sorted(inv[name],key=canonical):
                raise DiscoveryFailure('NATIVE_STALE_CAPTURE_BINDING')
        for name in ('goal','lifecycle','operation','resource','intent','dispatch'):
            if wire(getattr(s,name))!=f['observed'][name]:raise DiscoveryFailure('NATIVE_STALE_CAPTURE_BINDING')

    def open(self):
        if self.blocked:raise DiscoveryFailure(self.blocked)
        if self.opened:return
        started=perf_counter_ns()
        try:
            receipt=self.backend.open_view(self.snapshot)
            authority=next((c[1] for c in self.snapshot.contracts if c[0]=='authority-identity/v1'),None)
            if (not receipt.complete or receipt.snapshot_binding!=self.binding or receipt.view_id!=self.binding
                or receipt.authority!=authority or receipt.context_id!=self.snapshot.context.context_id):
                raise RecallError('mismatched view binding')
            self.opened=True
        except RecallError as e:raise DiscoveryFailure('NATIVE_VIEW_FAILED:'+str(e)) from e
        finally:self.open_ns+=perf_counter_ns()-started
    def records(self,kind,**arguments):
        self.open();key=canonical((kind,arguments))
        if key in self.cache:return self.cache[key]
        args=dict(context=self.snapshot.context.context_id,**arguments)
        if 'literal' in args:args['literal']=literal(args['literal'])
        if args.get('report_type')=='numeric':args['target']=literal(args['target'])
        t=perf_counter_ns()
        try:
            result=self.backend.query(kind,binding=self.binding,**args)
            if result.view_id!=self.binding:raise DiscoveryFailure('NATIVE_STALE_RESPONSE')
            if not result.complete:raise DiscoveryFailure('NATIVE_INCOMPLETE:'+result.reason)
            # IDs come exclusively from the native answer. Exact decoding only.
            values=[wire(self.backend.projection.catalog[i][1]) for i in result.ids]
            self.cache[key]=values
            if kind=='reports':self.reports[canonical(arguments['literal'])]=list(result.ids)
            return values
        except RecallError as e:raise DiscoveryFailure('NATIVE_QUERY_FAILED:'+str(e)) from e
        finally:self.query_ns+=perf_counter_ns()-t
    def history(self):
        # Complete history/depth accounting is intentionally full-scope. The
        # declared literal inventory selects query forms, never matching IDs.
        # Native answers determine all historical membership, including retired
        # and unrelated records. No returned record can become current here.
        result={}
        for q in self.snapshot.numerical:
            for b in self.records('historical',literal=wire(q.conclusion)):
                result[b['belief_revision_id']]=b
        return result
