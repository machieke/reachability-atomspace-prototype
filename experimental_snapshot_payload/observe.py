"""Unchanged native observer, failure latch and explicit generation ownership."""
from experimental_runtime_lifetime.observe import Observer as SessionObserver
from .backend import Backend

class Observer(SessionObserver):
    def __init__(self,backend=None):super().__init__(backend or Backend())
