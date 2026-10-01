"""Bounded deterministic whole-event deletion with explicit minimality evidence.

The predicate supplies evidence, not a Boolean: unsupported replays and errors
cannot establish deletion minimality. No runtime or mutation implementation is
imported here. Input events, identities, arguments and relative order are retained.
"""
from copy import deepcopy
from hashlib import sha256
import json


KINDS = {'WITNESS', 'NO_WITNESS', 'INVALID', 'ORACLE_GAP', 'CONTROL_MISMATCH', 'ERROR'}
DECIDED_NEGATIVE = {'NO_WITNESS', 'INVALID', 'CONTROL_MISMATCH'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def shrink(events, assess, *, max_evaluations=256, emit=None):
    """Return a witnessed subsequence and a fresh single-deletion audit.

    `assess(events, trial_id)` must return a JSON record with a `kind` in KINDS;
    WITNESS additionally requires a nonempty structured `signature`. Other fields
    are retained as evidence. Each call counts, including rejected/error trials.
    The final witness is replayed separately; no callback-result cache is used.
    """
    if type(events) is not list or len(events) > 128 or any(type(e) is not dict or type(e.get('event_id')) is not str or not e['event_id'] for e in events):
        raise ValueError('up to 128 events with unique string identities required')
    if len({e['event_id'] for e in events}) != len(events):
        raise ValueError('duplicate event identity')
    if type(max_evaluations) is not int or not 0 <= max_evaluations <= 4096:
        raise ValueError('evaluation budget must be an integer in [0,4096]')
    original = json.loads(canonical(events))
    current, signature, trials, accepted, audit = deepcopy(original), None, [], [], []
    selected_trial, final_trial = None, None
    budget_exhausted = False

    def probe(candidate, phase, parent):
        nonlocal budget_exhausted
        if len(trials) >= max_evaluations:
            budget_exhausted = True
            return None
        index = len(trials)
        request = dict(schema='trace-shrink-trial-request/v1', trial=index, phase=phase,
                       parent_digest=digest(parent), candidate_digest=digest(candidate),
                       event_ids=[e['event_id'] for e in candidate],
                       deleted_event_ids=[e['event_id'] for e in parent if e['event_id'] not in {x['event_id'] for x in candidate}])
        if emit is not None:
            emit(deepcopy(request))  # Persist the attempted candidate before replay.
        try:
            assessment = assess(deepcopy(candidate), index)
            if type(assessment) is not dict or assessment.get('kind') not in KINDS:
                raise ValueError('invalid assessment kind')
            if assessment['kind'] == 'WITNESS' and (type(assessment.get('signature')) is not dict or not assessment['signature']):
                raise ValueError('a witnessed failure requires a structured signature')
            assessment = json.loads(canonical(assessment))
        except Exception as error:
            assessment = dict(kind='ERROR', error_type=type(error).__name__, error=str(error))
        preserved = assessment['kind'] == 'WITNESS' and (signature is None or canonical(assessment['signature']) == canonical(signature))
        row = dict(request, schema='trace-shrink-trial/v1', assessment=assessment, preserves_signature=preserved)
        trials.append(row)
        if emit is not None:
            emit(deepcopy(row))
        return row

    def select(candidate, trial):
        nonlocal current, selected_trial
        accepted.append(dict(trial=trial['trial'], from_digest=digest(current), to_digest=digest(candidate),
                             removed=trial['deleted_event_ids']))
        current, selected_trial = candidate, trial['trial']

    baseline = probe(current, 'original', current)
    status = 'BUDGET_EXHAUSTED' if baseline is None else 'SEED_NOT_WITNESSED'
    if baseline is not None and baseline['assessment']['kind'] == 'WITNESS':
        signature, selected_trial = deepcopy(baseline['assessment']['signature']), baseline['trial']
        # Coarse contiguous chunk deletion. Every surviving complement is replayed
        # unchanged; dangling references are not repaired or silently removed.
        granularity = 2
        while len(current) >= 2 and not budget_exhausted:
            width = (len(current)+granularity-1)//granularity
            reduced = False
            for start in range(0, len(current), width):
                candidate = current[:start]+current[start+width:]
                trial = probe(candidate, 'chunk', current)
                if trial is None:
                    break
                if trial['preserves_signature']:
                    select(candidate, trial)
                    granularity = max(2, granularity-1)
                    reduced = True
                    break
            if reduced:
                continue
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity*2)
        # Re-evaluate every singleton deletion against the final candidate. If one
        # succeeds, restart the audit: earlier negatives may no longer apply.
        while not budget_exhausted:
            audit, reduced = [], False
            for index in range(len(current)):
                candidate = current[:index]+current[index+1:]
                trial = probe(candidate, 'single-deletion', current)
                if trial is None:
                    break
                audit.append(dict(removed_event_id=current[index]['event_id'], trial=trial['trial'],
                                  kind=trial['assessment']['kind'], preserves_signature=trial['preserves_signature']))
                if trial['preserves_signature']:
                    select(candidate, trial)
                    reduced = True
                    break
            if not reduced:
                break
        if not budget_exhausted:
            final = probe(current, 'final-replay', current)
            if final is not None:
                final_trial = final['trial']
                if not final['preserves_signature']:
                    status = 'FINAL_REPLAY_FAILED'
                else:
                    decided = all(t['kind'] in DECIDED_NEGATIVE or t['kind'] == 'WITNESS' and not t['preserves_signature'] for t in audit)
                    status = 'ONE_MINIMAL' if len(audit) == len(current) and decided else 'MINIMALITY_UNPROVEN'
        if budget_exhausted:
            status = 'BUDGET_EXHAUSTED'
    return dict(schema='trace-shrink-result/v1', status=status, original_digest=digest(original), reduced_digest=digest(current),
        original_events=original, reduced_events=deepcopy(current), signature=signature,
        removed_event_ids=[e['event_id'] for e in original if e['event_id'] not in {x['event_id'] for x in current}],
        one_minimal=status == 'ONE_MINIMAL', global_minimum=False,
        minimality_domain='order-preserving whole-event deletions with valid protocol, passing unmodified oracle control and identical first-divergence signature',
        max_evaluations=max_evaluations, evaluations=len(trials), selected_trial=selected_trial, final_trial=final_trial,
        accepted=accepted, deletion_checks=audit, trials=trials)
