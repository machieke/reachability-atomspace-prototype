"""Frozen observer semantics; explicit generation ownership and reconstruction."""
from experimental_native_multihop.observe import Observer as OriginalObserver
from .backend import Backend

class Observer(OriginalObserver):
    def __init__(self,backend=None):super().__init__(backend or Backend())
    def close(self):self.backend.shutdown()
    def rebuild(self):
        self.backend.reconstruct();self.failed=None
