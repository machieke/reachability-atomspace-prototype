"""Fail-closed worker gate for an explicitly prepared reconciliation decision."""
from pathlib import Path
from .journal import RecoveryError

MARKER = 'reconciliation-pending.json'
ARCHIVE = 'worker-reconciliations'


def require_settled(directory):
    path = Path(directory)/MARKER
    if path.exists() or path.is_symlink():
        raise RecoveryError('unfinished reconciliation requires explicit decision retry before worker resume')
