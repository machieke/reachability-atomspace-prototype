"""Scenario helpers, not an oracle. All writes use the public service API."""
from itertools import count

from reachability.model import Evidence, Literal, Statement


def lit(name):
    return Literal(Statement(name))


class Driver:
    def __init__(self, service):
        self.service = service
        self._keys = count()

    def key(self):
        return f"driver-{next(self._keys)}"

    def context(self, name="ctx", **kwargs):
        return self.service.open_context(name, idempotency_key=self.key(), **kwargs)

    def record(self, name, conclusion, context="ctx", roots=None):
        evidence = Evidence(name, context, conclusion, "source", 0,
                            tuple(roots or (f"origin:{name}",)))
        return self.service.record_evidence(evidence, idempotency_key=self.key())

    def prepare(self, transition):
        revision = self.service.snapshot(transition.context_id).knowledge_revision
        pre = self.service.precertify(transition, revision, idempotency_key=self.key())
        proposal = self.service.infer(transition, pre)
        post = self.service.postcertify(proposal, pre, idempotency_key=self.key())
        return proposal, pre, post, revision

    def finish(self, prepared, key=None):
        return self.service.commit(*prepared, idempotency_key=key or self.key())

    def adopt(self, name, conclusion, context="ctx", roots=None):
        self.record(name, conclusion, context, roots)
        transition = self.service.propose_evidence(context, name, idempotency_key=self.key())
        return self.finish(self.prepare(transition))

    def transition(self, rule, premises, context="ctx"):
        return self.service.propose_transition(context, rule, tuple(premises),
                                               idempotency_key=self.key())
