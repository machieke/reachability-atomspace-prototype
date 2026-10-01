"""Strict conformance replay predicate for admission/deployment event shrinking."""
from copy import deepcopy
from dataclasses import asdict
from functools import partial
import json
from pathlib import Path

from reachability.admission_protocol import AdmissionEvent, AdmissionInitial
from reachability.admission_trace import AdmissionSession
from reachability.deployment_trace import DeploymentSession
from reachability.trace_protocol import DeploymentEvent, DeploymentInitial
from . import admission_oracle, deployment_oracle
from .mutations import mutate
from .run_deployment import ConformanceMismatch, run_case
from .trace_shrink import canonical, digest


PROFILES = {'admission': (AdmissionInitial, AdmissionEvent, AdmissionSession, admission_oracle.reference_prefix),
            'deployment': (DeploymentInitial, DeploymentEvent, DeploymentSession, deployment_oracle.reference_prefix)}


class ReplayPredicate:
    """Run the correct implementation first, then one canary-backed mutation.

    Mutation patches are process-global: instances must be invoked sequentially.
    Every replay uses a fresh service/executor directory. Original checkpoints are
    checked only on trial zero; reduced schedules use the independent oracle,
    because original positional checkpoints describe the unreduced trajectory.
    """
    def __init__(self, profile, initial, case, mutant, output, *, native=False):
        if profile not in PROFILES or mutant not in ({'M05'} if profile == 'admission' else {'M06', 'M07', 'M11'}):
            raise ValueError('unsupported profile/mutant pairing')
        self.profile, self.mutant, self.native = profile, mutant, native
        initial_type, self.event_type, factory, self.reference = PROFILES[profile]
        self.initial = initial_type.parse(deepcopy(initial))
        self.public = self.initial.wire() if hasattr(self.initial, 'wire') else asdict(self.initial)
        self.factory = partial(factory, native=native) if profile == 'admission' else factory
        self.case = deepcopy(case)
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)

    def signature(self, error):
        return dict(schema='trace-failure-signature/v1', profile=self.profile, initial_digest=digest(self.public),
                    mutant=self.mutant, event_id=error.event_id, path=error.path,
                    expected=deepcopy(error.expected), actual=deepcopy(error.actual))

    def __call__(self, events, trial):
        if type(trial) is not int or trial < 0:
            raise ValueError('nonnegative integer trial identity required')
        directory = self.output/f'{trial:04d}'
        directory.mkdir()  # Refuse reuse/overwrite of a recorded trial.
        (directory/'events.json').write_text(json.dumps(events, indent=2)+'\n')
        stage, result = 'protocol', None
        try:
            if type(events) is not list or len(events) > 128 or len({e['event_id'] for e in events}) != len(events):
                raise ValueError('bounded unique event stream required')
            for e in events:
                if self.profile == 'admission':
                    self.event_type.parse(e, len(self.initial.atoms))
                else:
                    self.event_type.parse(e)
        except (ValueError, KeyError, TypeError) as error:
            result = dict(kind='INVALID', stage=stage, error_type=type(error).__name__, error=str(error), control_passed=False)
        if result is None:
            case = deepcopy(self.case)
            case['events'] = deepcopy(events)
            if trial != 0 or canonical(events) != canonical(self.case['events']):
                case['checkpoints'] = []
            stage = 'control'
            try:
                run_case(self.initial, case, restart_every_prefix=True, trace_path=directory/'control.jsonl',
                         session_factory=self.factory, reference=self.reference)
            except (admission_oracle.OracleGap, deployment_oracle.OracleGap) as error:
                result = dict(kind='ORACLE_GAP', stage=stage, error_type=type(error).__name__, error=str(error), control_passed=False)
            except ConformanceMismatch as error:
                result = dict(kind='CONTROL_MISMATCH', stage=stage, failure=self.signature(error), control_passed=False)
            except Exception as error:
                result = dict(kind='ERROR', stage=stage, error_type=type(error).__name__, error=str(error), control_passed=False)
            if result is None:
                stage = 'mutant'
                calls = 0
                try:
                    with mutate(self.mutant) as canary:
                        try:
                            run_case(self.initial, case, restart_every_prefix=False, trace_path=directory/'mutant.jsonl',
                                     session_factory=self.factory, reference=self.reference)
                        finally:
                            calls = canary['calls']
                except (admission_oracle.OracleGap, deployment_oracle.OracleGap) as error:
                    result = dict(kind='ORACLE_GAP', stage=stage, error_type=type(error).__name__, error=str(error))
                except ConformanceMismatch as error:
                    if calls == 0:
                        result = dict(kind='ERROR', stage=stage, error='divergence without mutation invocation', failure=self.signature(error))
                    else:
                        position = next((i+1 for i, e in enumerate(events) if e['event_id'] == error.event_id), 0)
                        result = dict(kind='WITNESS', signature=self.signature(error), first_divergent_prefix=position)
                except Exception as error:
                    result = dict(kind='ERROR', stage=stage, error_type=type(error).__name__, error=str(error))
                else:
                    result = dict(kind='NO_WITNESS')
                result.update(control_passed=True, control_recovered_prefixes=len(events), invocations=calls)
        result['artifacts'] = {p.name: dict(sha256=digest_file(p), bytes=p.stat().st_size)
                               for p in sorted(directory.iterdir()) if p.is_file()}
        (directory/'assessment.json').write_text(json.dumps(result, indent=2)+'\n')
        return result


def digest_file(path):
    from hashlib import sha256
    return sha256(Path(path).read_bytes()).hexdigest()
