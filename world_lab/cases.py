"""Fixed environment declarations and unchanged numerical setup/task."""
import json,copy
from pathlib import Path
from work_loop_lab.cases import World as Setup,manifest as previous_manifest,setup

ROOT=Path(__file__).resolve().parents[1]
PARENTS=('observable','unobservable','delayed','wrong-artifact','early-failure','regression')


def configuration():return json.loads((ROOT/'reviews/independent-world-v1/environments.json').read_text())
def specification(parent):return copy.deepcopy(next(s for s in configuration()['parents'] if s['id']==parent))
def manifest(task='positive'):return previous_manifest(task)


def initialize(session,task='positive'):
    setup_only=Setup(task);setup_only.initialize(session)
    # Only admitted setup records and the declared missing numerical source payload
    # are reused. The old acquisition/world/after/termination functions are never run.
    return setup_only.responses
