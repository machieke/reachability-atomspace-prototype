"""Two-thread deterministic check/publication controller around the real RLock.

Lock ownership establishes blocking; timeouts only abort broken evaluator runs.
Public commands carry no scheduling instructions. No production lock is disabled.
"""
from queue import Queue, Empty
from threading import Event, Lock, Thread, get_ident, local
from unittest.mock import patch


class ScheduleError(RuntimeError):
    pass


class ObservedLock:
    def __init__(self, lock, requested):
        self.lock, self.requested = lock, requested
        self.guard, self.owner, self.depth = Lock(), None, 0

    def acquire(self):
        self.requested()
        self.lock.acquire()
        with self.guard:
            self.owner, self.depth = get_ident(), self.depth+1
        return True

    def release(self):
        with self.guard:
            self.depth -= 1
            if not self.depth:
                self.owner = None
            self.lock.release()

    def owned(self):
        with self.guard:
            return self.owner == get_ident()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.release()


def reserve_pair(session, first, second, emit, note, *, timeout=5):
    """Emit fresh reservations in fixed order, allowing the contender into the gap.

    In the correct implementation the first worker holds the authority lock at
    `checked`; the contender demonstrably requests that held lock before release.
    A split-check mutant reaches `checked` without ownership, so both checks can
    finish before either publication. Rejected preparations need no checkpoint.
    """
    service = session.service
    if session.projection()['intents']:
        raise ScheduleError('paired reservation checkpoints require fresh attempts')
    original_lock, original_prepare = service._lock, service._prepare_execution_intent
    messages, first_gate, second_gate = Queue(), Event(), Event()
    worker_state, outcomes, errors, done = local(), {}, {}, {0: Event(), 1: Event()}
    requested_once = Event()
    def requested():
        if getattr(worker_state, 'index', None) == 1 and not requested_once.is_set():
            requested_once.set()
            messages.put(('request', 1, None))
    observed = ObservedLock(original_lock, requested)
    def checked(permit):
        intent = original_prepare(permit)
        worker = worker_state.index
        held = observed.owned()
        messages.put(('checked', worker, held))
        if not (first_gate if worker == 0 else second_gate).wait(timeout):
            raise ScheduleError('publication checkpoint watchdog expired')
        return intent
    def worker(index, event):
        worker_state.index = index
        try:
            outcomes[index] = session.apply(event)
        except BaseException as error:
            errors[index] = error
        finally:
            done[index].set()
            messages.put(('done', index, None))
    def receive():
        try:
            return messages.get(timeout=timeout)
        except Empty as error:
            raise ScheduleError('scheduler checkpoint watchdog expired') from error
    def finish(index):
        if not done[index].wait(timeout):
            raise ScheduleError('worker completion watchdog expired')
        if index in errors:
            raise errors[index]
    threads = [Thread(target=worker, args=(i, e), name='interleave-'+e['actor'], daemon=True) for i, e in enumerate((first, second))]
    started = []
    service._lock = observed
    try:
        with patch.object(service, '_prepare_execution_intent', checked):
            threads[0].start()
            started.append(threads[0])
            point, index, held = receive()
            if index != 0 or point not in ('checked', 'done'):
                raise ScheduleError('unexpected first-worker checkpoint')
            note(dict(point=point, event_id=first['event_id'], authority_lock_held=held))
            if point == 'done':
                finish(0)
                emit(first, outcomes[0])
                second_gate.set()
                threads[1].start()
                started.append(threads[1])
            else:
                threads[1].start()
                started.append(threads[1])
                point2, index2, _ = receive()
                if index2 != 1 or point2 not in ('request', 'done'):
                    raise ScheduleError('unexpected contender checkpoint')
                note(dict(point='contender-'+point2, event_id=second['event_id'], blocked_by_first=bool(held and point2 == 'request')))
                if not held and point2 != 'done':
                    point2, index2, held2 = receive()
                    if index2 != 1 or point2 not in ('checked', 'done'):
                        raise ScheduleError('unexpected second-worker check')
                    note(dict(point=point2, event_id=second['event_id'], authority_lock_held=held2))
                first_gate.set()
                finish(0)
                emit(first, outcomes[0])
                second_gate.set()
            finish(1)
            emit(second, outcomes[1])
    finally:
        first_gate.set()
        second_gate.set()
        for thread in started:
            thread.join(timeout)
        service._lock = original_lock
        if any(t.is_alive() for t in started):
            raise ScheduleError('worker failed to terminate')
