"""Read-only descriptive summary and explicit attempt comparison; no policy code.

python reviews/decision-value-v1/summarize_review.py ACCEPTED FAILED OUTPUT.json
Run after the corrected experiment's audit. No uncertainty or runtime superiority
claim is inferred from these repeated, fixed parent cases.
"""
from collections import Counter,defaultdict
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from reachability.codec import loads
from reachability.trace_protocol import canonical,fingerprint
from validation_lab.repeat_pressure_comparison import semantic_result,semantic_trace,differences
from validation_lab.decision_runtime import POLICIES


def load(path):return json.loads(Path(path).read_text())
def mean(rows,key):return sum(key(r) for r in rows)/len(rows) if rows else None


def normalize_projection_bindings(value):
    # Projection bindings hash the exact snapshots (including opaque event IDs).
    # The accepted audit rechecks these separately; compare cross-authority
    # structure, numerical fields, provenance and source accounts here.
    if isinstance(value,dict):
        if value.get('schema')=='scoped-boolean-projection/v1':
            value.pop('binding',None)
            for source in value.get('sources',[]): source['relief_events']=len(source['relief_events'])
        for v in value.values(): normalize_projection_bindings(v)
    elif isinstance(value,list):
        for v in value:normalize_projection_bindings(v)


def summarize(accepted,failed):
    a=load(accepted/'analysis.json');old=load(failed/'analysis.json');report=load(accepted/'report.json')
    checked=load(accepted/'audit.json')
    if checked['status']!='PASS':raise ValueError('accepted audit required')
    if load(accepted/'configuration.json')!=load(failed/'configuration.json'):raise ValueError('changed configuration')
    result=dict(schema='decision-review-summary/v1',source=report['sources'],audit=checked,
        configuration_digest=report['configuration_digest'],primary_parents=48,primary_budget_cells=96,
        summary_method='State agreement counts are descriptive. Mean regret also reported as equal-weight mean of parent state means. No CI; siblings excluded.',
        headline=[],partition_budget=[],costs=[],common_costs=[],siblings=[],attempts=[],reference_coverage=report['coverage'])
    index=load(accepted/'index.json');paired={(r['task_id'],r['configuration'],r['policy']):r for r in a['closed']}
    parent_common=[r for r in a['common'] if not r['sibling']]
    query_costs=[]
    for cell in index:
        if cell['task']['sibling']:continue
        for place in cell['common']:
            for rank in load(accepted/place/'result.json')['rankings']:
                query_costs.append(dict(policy=rank['policy'],elapsed_ns=rank['elapsed_ns'],discovery_ns=rank['discovery_ns'],
                    normalization_ns=rank['metrics']['normalization_ns'],graph_ns=rank['metrics']['graph_ns'],
                    iteration_ns=sum(e['iteration_ns'] for e in rank['evaluations'])))
    for p in POLICIES:
        queries=[r for r in query_costs if r['policy']==p]
        result['common_costs'].append(dict(policy=p,queries=len(queries),
            means={k:mean(queries,lambda r:r[k]) for k in ('elapsed_ns','discovery_ns','normalization_ns','graph_ns','iteration_ns')}))
        rows=[r for r in a['closed'] if not r['sibling'] and r['policy']==p]
        common=[r for r in parent_common if r['policy']==p]
        by_parent=defaultdict(list)
        for r in common:by_parent[r['parent_id']].append(r['regret'])
        delta=[r['loss']-paired[r['task_id'],r['configuration'],'B0']['loss'] for r in rows]
        result['headline'].append(dict(policy=p,budget_cells=len(rows),optimal_episodes=sum(r['gap']==0 for r in rows),
            mean_episode_gap=mean(rows,lambda r:r['gap']),maximum_episode_gap=max(r['gap'] for r in rows),
            agreement=sum(r['agreement'] for r in common),states=len(common),
            state_mean_regret=mean(common,lambda r:r['regret']),parent_mean_regret=sum(sum(v)/len(v) for v in by_parent.values())/len(by_parent),
            max_decision_regret=max(r['regret'] for r in common),primary_ties=sum(r['primary_tied'] for r in common),
            reference_ties=sum(r['reference_tied'] for r in common),favorable=sum(d<0 for d in delta),neutral=sum(d==0 for d in delta),unfavorable=sum(d>0 for d in delta)))
        result['costs'].append(dict(policy=p,cells=len(rows),mean_requests=mean(rows,lambda r:r['work']['actions']),
            mean_operation_work=mean(rows,lambda r:r['work']['operation_work']),mean_observation_work=mean(rows,lambda r:r['work']['observation_work']),
            mean_total_ns=mean(rows,lambda r:r['total_elapsed_ns']),mean_normalization_ns=mean(rows,lambda r:r['normalization_ns']),
            mean_graph_ns=mean(rows,lambda r:r['graph_ns']),mean_costs_ns={k:mean(rows,lambda r:r['costs_ns'][k]) for k in rows[0]['costs_ns']},
            mean_work={k:mean(rows,lambda r:r['work'][k]) for k in rows[0]['work']},
            mean_terminal_external=mean(rows,lambda r:r['external']),mean_terminal_certified=mean(rows,lambda r:r['certified']),
            unresolved_goal_rows=sum(len(r['unresolved_goals']) for r in rows),unresolved_commitments=sum(len(r['unresolved_commitments']) for r in rows)))
        for partition in ('development','confirmation'):
            for b in sorted({r['configuration'] for r in rows}):
                cells=[r for r in rows if r['partition']==partition and r['configuration']==b]
                cr=[r for r in common if r['partition']==partition and r['configuration']==b]
                ds=[r['loss']-paired[r['task_id'],r['configuration'],'B0']['loss'] for r in cells]
                result['partition_budget'].append(dict(policy=p,partition=partition,configuration=b,budget=cells[0]['budget'],parents=len(cells),
                    mean_gap=mean(cells,lambda r:r['gap']),agreement=sum(r['agreement'] for r in cr),states=len(cr),
                    mean_regret=mean(cr,lambda r:r['regret']),favorable=sum(d<0 for d in ds),neutral=sum(d==0 for d in ds),unfavorable=sum(d>0 for d in ds)))
        for kind in ('identifiers','dominated-option'):
            siblings=[r for r in a['siblings'] if r['policy']==p and r['kind']==kind]
            pairs=[x for r in siblings for x in r['common']]
            result['siblings'].append(dict(policy=p,kind=kind,cells=len(siblings),unchanged_optimum=all(r['reference_optimum_equal'] for r in siblings),
                changed_trajectories=sum(not r['trajectory_equal'] for r in siblings),changed_outcomes=sum(r['loss_delta']!=0 for r in siblings),
                outcome_deltas=[dict(task_id=r['task_id'],configuration=r['configuration'],delta=r['loss_delta']) for r in siblings if r['loss_delta']],
                common_queries=len(pairs),changed_common_choices=sum(r['changed'] for r in pairs),
                changed_without_either_primary_tie=sum(r['changed'] and not(r['parent_tie'] or r['sibling_tie']) for r in pairs)))
    authority_ids=set();selections=0;pressure_calls=0;statuses=Counter();stop_reasons=Counter();reference_matches=0
    for cell in index:
        left=load(accepted/cell['name']/'labels.json');right=load(failed/cell['name']/'labels.json')
        for data in (left,right):
            for key in ('reference','enumeration'):data[key].pop('elapsed_ns')
        if left!=right:raise ValueError('reference labels changed between attempts')
        reference_matches+=1
        for place in cell['closed']:
            current=load(accepted/place/'result.json');previous=load(failed/place/'result.json')
            x=dict(result=semantic_result(current['result']),trace=semantic_trace(accepted/place))
            y=dict(result=semantic_result(previous['result']),trace=semantic_trace(failed/place))
            normalize_projection_bindings(x);normalize_projection_bindings(y)
            paths=differences(x,y)
            result['attempts'].append(dict(path=place,semantics_equal=not paths,difference_paths=paths,
                current_hash=fingerprint(x),previous_hash=fingerprint(y)))
            selections+=len(current['result']['selected']);pressure_calls+=current['metrics']['ranking_calls']
            statuses.update(r['status'] for r in current['result']['selected']);stop_reasons.update([current['result']['stop_reason']])
            for directory in (accepted,failed):
                path=directory/place/'admission.db'
                with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)) as db:
                    identity=loads(db.execute('SELECT value FROM metadata WHERE id=1').fetchone()[0])['initial']['authority_id']
                    if identity in authority_ids:raise ValueError('authority reused across attempts')
                    authority_ids.add(identity)
    result.update(totals=a['totals'],accepted_selections=selections,pressure_calls=pressure_calls,statuses=dict(statuses),stop_reasons=dict(stop_reasons),
        identical_reference_cells=reference_matches,distinct_closed_authorities=len(authority_ids),same_semantic_runs=sum(r['semantics_equal'] for r in result['attempts']),
        reference_solver_enumeration_ns=report['reference_elapsed_ns'],experiment_elapsed_ns=report['experiment_elapsed_ns'],audit_elapsed_ns=checked['elapsed_ns'],
        remaining_unallocated_costs='Reference model initialization/validation, report serialization, witness close/copy and harness orchestration are included in experiment total but not separated into individual timings; peak RSS unmeasured.',
        failed_attempt='d7fa062 completed measurements but failed audit serialization; retained verbatim, not accepted audited measurement.',
        analysis_tool_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    return result


if __name__=='__main__':
    accepted,failed,output=map(Path,sys.argv[1:]);value=summarize(accepted,failed)
    output.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(canonical({k:value[k] for k in ('totals','accepted_selections','distinct_closed_authorities','same_semantic_runs','statuses')}))
