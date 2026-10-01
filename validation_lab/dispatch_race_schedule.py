"""Evaluator-only checkpoints around the actual simulator's submit call."""
from queue import Queue, Empty
from threading import Event, Thread, local
from unittest.mock import patch

from .interleaving_schedule import ObservedLock, ScheduleError


def dispatch_pair(session, first, second, checkpoint, emit, note, *, timeout=5):
    if checkpoint not in ('before_send', 'before_ack'):
        raise ValueError('unsupported submission checkpoint')
    service, executor = session.service, session.executor
    original_lock, original_submit = service._lock, executor.submit
    messages, proceed, contender = Queue(), Event(), Event()
    state, outcomes, errors = local(), {}, {}
    done = [Event(), Event()]

    class DeliveryLock(ObservedLock):
        def acquire(self):
            if getattr(state, 'index', None) == 1 and not contender.is_set():
                # Actually try the real lock. Failure is definitive blocking
                # evidence; hold the contender outside it until the first
                # worker's raw post-state has been recorded.
                if self.lock.acquire(blocking=False):
                    self.lock.release()
                    raise ScheduleError('contender acquired authority lock during submission')
                messages.put(('blocked', 1, None))
                if not contender.wait(timeout):
                    raise ScheduleError('contender watchdog expired')
            return super().acquire()

    observed = DeliveryLock(original_lock, lambda: None)

    def pause():
        held = observed.owned()
        messages.put((checkpoint, 0, held))
        if not held:
            raise ScheduleError('authority lock absent at submission checkpoint')
        if not proceed.wait(timeout):
            raise ScheduleError('submission checkpoint watchdog expired')

    def submit(request):
        if checkpoint == 'before_send':
            pause()
        receipt = original_submit(request)
        if checkpoint == 'before_ack':
            pause()
        return receipt

    def worker(index, event):
        state.index = index
        try:
            outcomes[index] = session.execute(event)
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

    threads = [Thread(target=worker, args=(i,e), name='dispatch-race-'+str(i), daemon=True) for i,e in enumerate((first,second))]
    started = []
    service._lock = observed
    try:
        with patch.object(executor, 'submit', submit):
            threads[0].start()
            started.append(threads[0])
            point, index, held = receive()
            if index != 0 or point not in (checkpoint, 'done'):
                raise ScheduleError('unexpected dispatch checkpoint')
            note(dict(point=point,event_id=first['event_id'],authority_lock_held=held,executor_effects=executor.total_effects))
            if point == 'done':
                finish(0)
                emit(first,outcomes[0])
                contender.set()
                threads[1].start()
                started.append(threads[1])
            else:
                if not held:
                    raise ScheduleError('authority lock absent at submission checkpoint')
                threads[1].start()
                started.append(threads[1])
                point, index, _ = receive()
                if (point,index) != ('blocked',1):
                    finish(1)
                    raise ScheduleError('contender did not block at submission')
                note(dict(point='contender-blocked',event_id=second['event_id'],blocked_by_first=True))
                proceed.set()
                finish(0)
                emit(first,outcomes[0])
                contender.set()
            finish(1)
            emit(second,outcomes[1])
    finally:
        proceed.set()
        contender.set()
        for thread in started:
            thread.join(timeout)
        service._lock = original_lock
        if any(t.is_alive() for t in started):
            raise ScheduleError('dispatch worker failed to terminate')
