"""Native query facade used by the frozen directed traversal and tuple joins."""
from .backend import Backend


class QueryMap:
    def __init__(self,index,kind):self.index,self.kind=index,kind
    def get(self,literal,default=()):
        return self.index.backend.recall(self.kind,binding=self.index.binding,context=self.index.context,literal=literal)


class NativeIndex:
    def __init__(self,snapshot,backend):
        self.backend=backend;self.receipt=backend.open_view(snapshot)
        self.binding=self.receipt.snapshot_binding;self.context=self.receipt.context_id
        self.rules,self.estimates,self.reports=(QueryMap(self,k) for k in ('producers','current','reports'))
        self.by_id={b.belief_revision_id:b for b in self.current()}
        self.entries=self.receipt.counts['source_records']
        self.elapsed_ns=0  # full cold-view costs are measured by Backend, never hidden here
    def current(self):return self.backend.recall('all_current',binding=self.binding,context=self.context)
    def all_rules(self):return self.backend.recall('all_rules',binding=self.binding,context=self.context)
    def models(self):return self.backend.recall('models',binding=self.binding,context=self.context)
    def probes_for_scope(self,dependencies):
        results={}
        def query(kind,target):
            for probe in self.backend.recall('probes',binding=self.binding,context=self.context,report_type=kind,target=target):
                results[probe.probe_id,probe.opportunity]=probe
        for literal in dependencies.by_literal:query('numeric',literal)
        for root in dependencies.task.roots:
            if root.kind in ('product','health'):query(root.kind,root.target[0])
        return tuple(results.values())
