"""Service errors shared by admission and lifecycle operations."""
from .model import Status


class AdmissionDenied(RuntimeError):
    def __init__(self, status: Status, detail: str):
        self.status = status
        super().__init__(detail)


class IdempotencyConflict(ValueError):
    pass
