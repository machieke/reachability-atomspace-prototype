"""An independent durable simulator, with explicit idempotency and fencing.

Each submission models one accepted effect; it does not fabricate completion,
product availability or goal relief. The executor has its own journal/lock.
"""
from pathlib import Path
from threading import RLock
from uuid import uuid4

from .codec import dumps, loads
from .dispatch_model import DispatchRequest, ExecutorProfile, ExecutorReceipt
from .errors import IdempotencyConflict
from .journal import RecoveryError, SQLiteJournal, digest


class SimulatedExecutor:
    def __init__(self, database: str | Path, *, executor_id: str | None = None,
                 supports_idempotency: bool | None = None, supports_query: bool | None = None,
                 supports_release: bool | None = None):
        requested = (executor_id, supports_idempotency, supports_query, supports_release)
        initial = ExecutorProfile(executor_id or "executor", str(uuid4()),
            True if supports_idempotency is None else supports_idempotency,
            True if supports_query is None else supports_query,
            True if supports_release is None else supports_release)
        self._lock = RLock()
        self._closed = False
        self._broken = False
        self._sequence = 0
        self._requests: dict[str, DispatchRequest] = {}
        self._receipts: dict[str, ExecutorReceipt] = {}
        self._journal = SQLiteJournal(database, {"implementation": "simulated-executor/v1", "profile": initial})
        try:
            stored = self._journal.initial
            if stored["implementation"] != "simulated-executor/v1" or not isinstance(stored["profile"], ExecutorProfile):
                raise RecoveryError("unsupported executor journal")
            self._profile = stored["profile"]
            actual = (self.profile.executor_id, self.profile.supports_idempotency,
                      self.profile.supports_query, self.profile.supports_release)
            if any(wanted is not None and wanted != found for wanted, found in zip(requested, actual)):
                raise RecoveryError("executor configuration does not match its durable identity")
            for entry in self._journal.entries():
                request = loads(entry.payload)
                receipt = self._calculate(entry.command, request, entry.sequence)
                if digest(dumps(receipt)) != entry.result_digest:
                    raise RecoveryError("executor replay differs from the recorded receipt")
                self._requests[request.request_id] = request
                self._receipts[request.request_id] = receipt
                self._sequence = entry.sequence
        except BaseException as error:
            self.close()
            if isinstance(error, Exception):
                raise RecoveryError("executor journal recovery failed") from error
            raise

    @property
    def profile(self) -> ExecutorProfile:
        return self._profile

    def _ensure_open(self):
        if self._closed or self._broken:
            raise RecoveryError("executor requires reopening after close or storage failure")

    def _validate_request(self, request: DispatchRequest):
        if not isinstance(request, DispatchRequest) or request.intent.executor_id != self.profile.executor_id:
            raise ValueError("request executor binding is invalid")
        previous = self._requests.get(request.request_id)
        if previous is not None and previous != request:
            raise IdempotencyConflict("executor request identity cannot be rebound")

    def _receipt(self, request, state, sequence, effect_count=0):
        return ExecutorReceipt(self.profile.executor_id, self.profile.instance_id, request.request_id,
                               request.fingerprint, state, sequence, effect_count, state == "released")

    def _calculate(self, command, request, sequence):
        self._validate_request(request)
        if command not in ("submit", "release"):
            raise ValueError("unknown executor command")
        if command == "release" and not self.profile.supports_release:
            raise ValueError("executor does not support authoritative release")
        previous = self._receipts.get(request.request_id)
        if previous is not None and (previous.fenced or command == "submit" and self.profile.supports_idempotency):
            return previous
        count = previous.effect_count if previous is not None else 0
        return self._receipt(request, "released" if command == "release" else "accepted",
                             sequence, count if command == "release" else count + 1)

    def _write(self, command, request):
        with self._lock:
            self._ensure_open()
            receipt = self._calculate(command, request, self._sequence + 1)
            if receipt == self._receipts.get(request.request_id):
                return receipt
            try:
                sequence = self._journal.append(command, f"executor-event:{self._sequence + 1}",
                    dumps(request), digest(dumps(receipt)), self._sequence)
            except BaseException:
                self._broken = True
                raise
            self._requests[request.request_id] = request
            self._receipts[request.request_id] = receipt
            self._sequence = sequence
            return receipt

    def submit(self, request: DispatchRequest) -> ExecutorReceipt:
        return self._write("submit", request)

    def query(self, request: DispatchRequest) -> ExecutorReceipt:
        with self._lock:
            self._ensure_open()
            self._validate_request(request)
            if not self.profile.supports_query:
                return self._receipt(request, "unknown", 0)
            return self._receipts.get(request.request_id) or self._receipt(request, "absent", self._sequence)

    def release(self, request: DispatchRequest) -> ExecutorReceipt:
        """Release effects and permanently reject future effects for this request.

        A tombstone is durable even when the request has not arrived yet. This
        closes the delayed-submission race that an ordinary 'not found' cannot.
        """
        return self._write("release", request)

    @property
    def total_effects(self) -> int:
        """Simulator instrumentation: historical effects, including released ones."""
        with self._lock:
            self._ensure_open()
            return sum(receipt.effect_count for receipt in self._receipts.values())

    def close(self):
        with self._lock:
            self._closed = True
            self._journal.close()

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, *_):
        self.close()


class NonIdempotentSimulatedExecutor(SimulatedExecutor):
    def __init__(self, database: str | Path, *, executor_id: str | None = None,
                 supports_query: bool = False, supports_release: bool = False):
        super().__init__(database, executor_id=executor_id, supports_idempotency=False,
                         supports_query=supports_query, supports_release=supports_release)
