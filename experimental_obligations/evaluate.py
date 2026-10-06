"""Finite non-authoritative decision interpretations over immutable full captures."""
from dataclasses import dataclass
from hashlib import sha256
import json
from time import perf_counter_ns
from reachability.trace_protocol import canonical
from .capture import Captured


def digest(value):return sha256(canonical(value).encode()).hexdigest()

def combine(values):
    values=tuple(values)
    if not values or any(v not in ('FAIL','STALE','UNKNOWN','PASS') for v in values):return 'UNKNOWN'
    return next((s for s in ('FAIL','STALE','UNKNOWN') if s in values),'PASS')


@dataclass(frozen=True)
class Bounds:
    records: int=64
    obligations: int=16
    classes: int=32
    classification: int=512
    witnesses: int=64
    bytes: int=2097152
    def __post_init__(self):
        if any(type(v) is not int or not 0<=v<=cap for v,cap in zip(self.__dict__.values(),(64,16,32,512,64,2097152))):raise ValueError('unsupported checker bounds')


@dataclass(frozen=True)
class ShadowAssessment:
    payload_json: str
    def data(self):return json.loads(self.payload_json)
    @property
    def status(self):return self.data()['status']


def _evaluate(snapshot,manifest,interpretation='B',bounds=Bounds()):
    if type(snapshot) is not Captured or interpretation not in ('A','B'):raise ValueError('detached capture and named interpretation required')
    start=perf_counter_ns();m=json.loads(canonical(manifest));costs={};checks=[];records=[];obligations=[];comparisons=0
    d={};criterion=m.get('criterion',{})
    def check(name,status,detail):checks.append(dict(name=name,status=status,detail=detail))
    def finish(numeric,reason='COMPLETE'):
        t=perf_counter_ns()
        output=dict(schema='non-authoritative-shadow-assessment/v0',authority=False,interpretation=interpretation,status=combine([numeric,*(c['status'] for c in checks)]),numerical_status=numeric,
            snapshot_identity=snapshot.identity,manifest_hash=digest(m),basis_hash=digest((snapshot.identity,m,interpretation)),criterion=criterion,checks=checks,obligations=obligations,records=records,
            missing_obligations=[o['id'] for o in obligations if not o['witnesses']],unresolved_obligations=[o['id'] for o in obligations if o['status']!='PASS'],reason=reason,classification_comparisons=comparisons,
            bounds=bounds.__dict__,live_numerical_status=d.get('live_status'),coverage=d.get('coverage'),not_a_permission=True)
        payload=canonical(output);costs['witness_recording_ns']=perf_counter_ns()-t;costs['total_evaluation_ns']=perf_counter_ns()-start
        return ShadowAssessment(payload),costs
    if len(snapshot.payload_json.encode())>bounds.bytes:return finish('UNKNOWN','CAPTURE_BYTE_BOUND')
    d=snapshot.data()
    if d.get('schema')!='complete-decision-shadow-capture/v0' or not d.get('complete') or not d.get('hard_checks_complete'):return finish('UNKNOWN','INCOMPLETE_OR_UNSUPPORTED_CAPTURE')
    if m.get('schema')!='obligation-interpretation/experimental-v0' or len(d.get('pairs',[]))!=1:return finish('UNKNOWN','UNSUPPORTED_FRAGMENT')
    if not 1<=len(m.get('obligations',[]))<=bounds.obligations or not 1<=len(m.get('classes',[]))<=bounds.classes:return finish('UNKNOWN','MANIFEST_BOUND')
    classes=m['classes'];groups=m['obligations'];classids=[c['id'] for c in classes];groupids=[o['id'] for o in groups];assigned=[c for o in groups for c in o['classes']]
    if len(set(classids))!=len(classids) or len(set(groupids))!=len(groupids) or sorted(assigned)!=sorted(classids):return finish('UNKNOWN','AMBIGUOUS_OR_UNASSIGNED_CLASSES')
    if any(c['kind'] not in ('observation','deduction','revision') for c in classes) or any(o['mode'] not in ('any','all') for o in groups):return finish('UNKNOWN','UNSUPPORTED_APPLICABILITY')
    exact=(d['context']['context_id']==m['context'] and d['operation']['operation']['product_id']==m['product'] and [d['contract']['contract_id'],d['contract']['revision']]==m['contract'] and d['contract']['criteria']==[criterion])
    check('exact_scope_and_criterion','PASS' if exact else 'FAIL','immutable context/product/criterion/version binding')
    check('logical_time','PASS' if m['time_window'][0]<=d['context']['logical_time']<m['time_window'][1] else 'STALE','declared half-open applicability window')
    for c in d['hard_checks']:check('required:'+c['name'],c['status'],c['detail'])
    names={c['name'] for c in d['hard_checks']}
    minimum={'clock_alignment','contract_binding','owner','selected','operation_readiness','action_requirements','undispatched_attempt','attempt_identity','resource_capacity'}
    check('finite_required_checks','PASS' if minimum<=names and minimum<=set(m['required_hard_checks']) else 'UNKNOWN','fixed fragment never omits mandatory hard checks')
    check('required_check_inventory','PASS' if set(m['required_hard_checks'])<=names else 'UNKNOWN','no omitted mandatory check is assumed passing')
    for c in d['decision']['checks']:
        if c['name']!=criterion.get('criterion_id'):check(c['name'],c['status'],c['detail'])
    same,opposite=d['pairs'][0];scan_start=perf_counter_ns()
    combined=[]
    for orientation,view in (('same',same),('opposite',opposite)):
        live={b['belief_revision_id'] for b in view['current']}
        history={b['belief_revision_id']:b for b in view['historical']}
        if not live<=history.keys() or len(history)!=len(view['historical']):return finish('UNKNOWN','INCOMPLETE_HISTORY')
        if any(history[b['belief_revision_id']]!=b for b in view['current']):return finish('UNKNOWN','CURRENT_HISTORY_MISMATCH')
        combined.extend((orientation,b,b['belief_revision_id'] in live) for b in history.values())
    if len(combined)>bounds.records:return finish('UNKNOWN','RECORD_BOUND')
    # Cross-check the complete current sets against the actual frozen inspector.
    exports={canonical(v['conclusion']):v for v in d['probability_export'][3]}
    for view in (same,opposite):
        exported=exports.get(canonical(view['conclusion']))
        if exported is not None and exported!=view:return finish('UNKNOWN','INCOMPLETE_PUBLIC_EXPORT')
        if exported is None and (view['current'] or view['historical']):return finish('UNKNOWN','MISSING_PUBLIC_EXPORT')
    actual=d['decision']['criteria'][0]
    for view,key in ((same,'current'),(opposite,'opposite')):
        values=sorted((b['belief_revision_id'],b['proposal']['support']['truth']) for b in view['current'])
        if values!=sorted((b['belief_revision_id'],b['truth']) for b in actual[key]):return finish('UNKNOWN','INCOMPLETE_DECISION_BASIS')
    registry=d['registry'];evidence={e['evidence_id']:e for e in registry['evidence']};certs={c['certificate_id']:c for c in registry['certificates']};rules={(r['rule_id'],r['revision']) for r in registry['rule_versions']};models={r['model_id'] for r in registry['models']}
    for orientation,b,current in sorted(combined,key=lambda item:(item[0],item[1]['belief_revision_id'])):
        support=b['proposal']['support'];transition=b['transition'];truth=support['truth'];ids=support['evidence_ids'];pre=certs.get(b['pre_certificate_id']);post=certs.get(b['post_certificate_id'])
        valid=(b['context_id']==d['context']['context_id'] and support['context_id']==b['context_id'] and all(i in evidence for i in ids) and pre and post and
               registry['certificate_statuses'].get(b['pre_certificate_id'])=='PASS' and registry['certificate_statuses'].get(b['post_certificate_id'])=='PASS' and
               pre['transition_id']==transition['transition_id']==post['transition_id'] and post['pre_certificate_id']==pre['certificate_id'] and
               support['truth']['truth_model']==d['contract']['truth_model'] and
               set(support['lineage_roots'])=={r for i in ids if i in evidence for r in evidence[i]['lineage_roots']})
        if transition['kind']=='deduction':valid=valid and (transition['rule_id'],transition['rule_revision']) in rules
        elif transition['kind']=='revision':valid=valid and transition['independence_id'] in models
        elif transition['kind']!='observation':valid=False
        if valid:
            valid=(combine(c['status'] for c in pre['checks'])=='PASS' and combine(c['status'] for c in post['checks'])=='PASS' and
                   pre['context_id']==post['context_id']==b['context_id'] and bool(ids) and bool(support['lineage_roots']))
        if current and valid:
            tick=d['context']['logical_time'];policy=d['policy']
            valid=bool(policy) and b['probability_policy_revision']==policy['revision'] and b['hard_policy_revision']==d['context']['policy_revision']
            valid=valid and all(i not in registry['revoked'] and evidence[i]['context_id']==b['context_id'] and evidence[i]['source'] in policy['allowed_sources'] and evidence[i]['observed_at']<=tick and (evidence[i]['valid_until'] is None or tick<evidence[i]['valid_until']) for i in ids)
            if transition['kind']=='deduction':valid=valid and (transition['rule_id'],transition['rule_revision']) in {(r['rule_id'],r['revision']) for r in registry['rules']}
            if transition['kind']=='revision':valid=valid and transition['independence_id'] not in registry['revoked_models']
        if current and not valid:check('provenance:'+b['belief_revision_id'],'FAIL','missing certified source/producer/model chain')
        lo,hi,floor=criterion['min_strength'],criterion['max_strength'],criterion['min_confidence']
        interval=lo<=truth['strength']<=hi;adequate=interval and truth['confidence']>=floor
        records.append(dict(id=b['belief_revision_id'],orientation=orientation,current=current,belief=b,eligible_classes=[],applicability=[],adequate=adequate,
            disposition='retired_by_existing_ledger' if not current else 'opposite_objection' if orientation=='opposite' else 'strength_objection' if not interval else 'insufficient_confidence' if not adequate else 'adequate_support',provenance_valid=bool(valid)))
    costs['complete_evidence_scan_ns']=perf_counter_ns()-scan_start
    t=perf_counter_ns()
    for rec in records:
        b=rec['belief'];tr=b['transition'];kind=tr['kind'];support=b['proposal']['support']
        ident=([evidence[tr['evidence_id']]['source']] if kind=='observation' and tr['evidence_id'] in evidence else [tr['rule_id'],tr['rule_revision']] if kind=='deduction' else [tr['independence_id']] if kind=='revision' else [])
        for c in classes:
            if comparisons>=bounds.classification:return finish('UNKNOWN','CLASSIFICATION_BOUND')
            comparisons+=1
            matches=kind==c['kind'] and ident==c['identity']
            roots=set(c['roots'])<=set(support['lineage_roots'])
            # Requiring source-b/root:b cannot be met by another report with root:a.
            eligible=matches and roots and rec['provenance_valid']
            rec['applicability'].append(dict(class_id=c['id'],identity_match=matches,lineage_requirement=roots,eligible=eligible))
            if eligible:rec['eligible_classes'].append(c['id'])
    costs['applicability_classification_ns']=perf_counter_ns()-t;t=perf_counter_ns()
    local=[c['status'] for c in same['checks']]+[same['status']]
    local.append('UNKNOWN' if opposite['current'] else 'PASS')
    curr=[r for r in records if r['current'] and r['orientation']=='same']
    local.append('FAIL' if any(r['disposition']=='strength_objection' for r in curr) else 'PASS' if curr else 'UNKNOWN')
    if interpretation=='A':local.append('PASS' if curr and all(r['adequate'] for r in curr) else 'UNKNOWN')
    else:
        for r in records:
            if r['current'] and not r['eligible_classes']:local.append('UNKNOWN');check('unclassified:'+r['id'],'UNKNOWN','relevant current record retained without an eligible declared role')
        witness_count=0
        for group in groups:
            relevant=[r for r in records if r['orientation']=='same' and set(r['eligible_classes'])&set(group['classes'])]
            current=[r for r in relevant if r['current']];good=[r['id'] for r in current if r['adequate']]
            witness_count+=len(good)
            if witness_count>bounds.witnesses:return finish('UNKNOWN','WITNESS_BOUND')
            status=('STALE' if relevant else 'UNKNOWN') if not current else ('PASS' if (bool(good) if group['mode']=='any' else len(good)==len(current)) else 'UNKNOWN')
            obligations.append(dict(id=group['id'],mode=group['mode'],classes=group['classes'],status=status,witnesses=sorted(good),inspected=[r['id'] for r in current],retired=[r['id'] for r in relevant if not r['current']]))
            local.append(status)
    numeric=combine(local);costs['policy_evaluation_ns']=perf_counter_ns()-t
    # Numerical checks are explicit, distinct from the non-numerical contract checks.
    check('same_literal_ledger',same['status'],'complete current versus retired/missing authoritative views')
    check('opposite_literal','UNKNOWN' if opposite['current'] else 'PASS','every current opposite estimate retained; no complementary model')
    check('strength_objections','FAIL' if any(r['disposition']=='strength_objection' for r in curr) else 'PASS','all current same-literal strengths inspected regardless of confidence')
    if interpretation=='A':check('universal_confidence_floor','PASS' if curr and all(r['adequate'] for r in curr) else 'UNKNOWN','every current same-literal assessment must meet the unchanged floor')
    else:
        for o in obligations:check('obligation:'+o['id'],o['status'],'declared '+o['mode']+' requirement; all qualifying IDs recorded')
    return finish(numeric)


def evaluate(snapshot,manifest,interpretation='B',bounds=Bounds()):
    """Malformed detached input closes; unexpected programming/runtime errors escape."""
    if type(snapshot) is not Captured or interpretation not in ('A','B'):
        raise ValueError('detached capture and named interpretation required')
    start=perf_counter_ns()
    try:return _evaluate(snapshot,manifest,interpretation,bounds)
    except (KeyError,IndexError,TypeError,ValueError) as error:
        output=dict(schema='non-authoritative-shadow-assessment/v0',authority=False,interpretation=interpretation,
            status='UNKNOWN',numerical_status='UNKNOWN',reason='MALFORMED_OR_UNSUPPORTED_INPUT',
            error_type=type(error).__name__,snapshot_identity=snapshot.identity,manifest_hash=digest(manifest),
            basis_hash=digest((snapshot.identity,manifest,interpretation)),criterion=manifest.get('criterion'),
            checks=[],records=[],obligations=[],missing_obligations=[],unresolved_obligations=[],
            bounds=bounds.__dict__,not_a_permission=True)
        return ShadowAssessment(canonical(output)),dict(total_evaluation_ns=perf_counter_ns()-start)
