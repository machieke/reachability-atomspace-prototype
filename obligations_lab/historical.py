"""Reuse only the explicitly named, checksummed published adverse ledger."""
from hashlib import sha256
import importlib.util,json,tarfile
from pathlib import Path
from reachability.service import AdmissionService
from experimental_obligations.capture import capture,state_digest
from .cases import ROOT


def historical(directory):
    review=ROOT/'reviews/completion-aware-recall-v1';spec=importlib.util.spec_from_file_location('frozen_review_verifier',review/'verify_review.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);verified=module.verify(review)
    member='completion-aware-recall-review-v1/comparison/primary-assembly-native-unproductive-early-c48-q16-WS-queue/admission.db'
    db=Path(directory)/'historical.db';db.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(review/'review.tar.xz') as archive:original=archive.extractfile(member).read()
    db.write_bytes(original)
    with AdmissionService(database=db) as service:
        before=state_digest(service);cap,cost=capture(service);after=state_digest(service);assert after==before
    return [dict(label='published-final',capture=cap,costs=cost,manifests=('historical-alternatives','historical-mandatory'),nonmutation=dict(before=before,after=after))],dict(original_archive=verified,original_member=member,original_db_sha256=sha256(original).hexdigest(),original_measured_revision='53d7b0b257ea436dc043e9d497fd3c76dcd0e03c',runtime_calls=[],native_execution='historical only; no new native call',counterfactual_roles=True)
