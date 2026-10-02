"""Fixed-policy, same-information decision experiment. No runtime policy changes.

Run: python -m validation_lab.decision_comparison --output <new-directory>
The source, protocol and inventory must be committed before policy measurement.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from reachability.service import AdmissionService
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work, operation_cost
from reachability.trace_protocol import canonical, fingerprint
from . import audit_pressure_comparison as audit
from . import projection_comparison as projection
from . import run_pressure_comparison as runner
from .decision_reference import Bounds, Reference, STOP
from .decision_enumeration import enumerate_histories
from .decision_tasks import budgets, cohort, materialize
from .decision_runtime import (POLICIES, public_task, semantic_action, reference_state,
    remaining_budget, rank_fixed, execute_prefix, witness)
from .pressure_episodes import ReasoningWorld

FROZEN='3e8fd7be56362ed21944636bbe505b6a4a7aac6f'
PROJECTION='8542ad538649fd0b967c7047057dd5cebf831be8'
HARNESS_REVISION='decision-value/v1.1'
OWN_FILES=['validation_lab/decision_'+x+'.py' for x in ('reference','enumeration','tasks','runtime','comparison')]+[
    'tests/test_decision_value.py','reviews/decision-value-v1/PROTOCOL.md','reviews/decision-value-v1/inventory.json',
    'reviews/decision-value-v1/feasibility.json','reviews/decision-value-v1/CORRECTION-v1.1.md']


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def configuration():
    return dict(schema='decision-validation/v1',tasks=cohort(),budgets=budgets(),policies=POLICIES,
        bounds=asdict(Bounds()),seeds=[0],
        sampling='Root plus lexicographically first DP-reachable state at each tick 1,2,3 with at least two non-STOP actions; siblings map parent prefixes.',
        common_query_budget='Full shared auxiliary compute and wall budgets per query; remaining semantic budgets after the public prefix. Discovery charged equally to each query.',
        witness_selection='Canonical initial optimal witness in every exact cell; all initial Q witnesses for six parent index-0 controls at both budgets, deduplicated by full action sequence.',
        tie_rule='Frozen rank tuple then candidate ID; primary near-tie tolerance 2*pressure.error_bound_l1+1e-12 (B0: 1e-12), diagnostic only; reference uses complete exact primary-optimal set.',
        secondary='Witness selection only: terminal certified loss, operation work, requests, lexicographic action sequence.',
        objective='Integrated external unresolved loss, ticks 0..15; one tick per request, costs are not durations.',
        stop='Voluntary termination; no subsequent execution during tail. No wait-and-resume capability.',
        partition='Parent indices 0..4 development, 5..7 locked confirmation; no tuning on either.',
        rotation='Policy order rotated left by cell index modulo five.',
        scope='Deterministic permanent supports, no future changes/probes/commitments, public physical assignment; full model supplied equally on public task_contract.',
        statistical_claim='Engineering cohort, no power/CI claim; siblings excluded from parent headline; timings supplementary single runs.')


def source_binding():
    def files_at(revision, names):
        result={}
        for name in names:
            expected=subprocess.check_output(['git','show',revision+':'+name],cwd=audit.ROOT)
            blob=(audit.ROOT/name).read_bytes()
            audit.equal(sha256(blob).hexdigest(),sha256(expected).hexdigest(),'committed source '+name)
            result[name]=sha256(blob).hexdigest()
        return result
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=audit.ROOT,text=True).strip()
    return dict(harness_revision=HARNESS_REVISION,frozen_revision=FROZEN,projection_revision=PROJECTION,experiment_revision=head,
        frozen_files=files_at(FROZEN,audit.source_inputs()),projection_files=files_at(PROJECTION,projection.TOOL_FILES),
        experiment_files=files_at(head,OWN_FILES))


def verify_sources(binding):
    audit.equal(binding['harness_revision'],HARNESS_REVISION,'explicit corrected harness version')
    for key in ('frozen_files','projection_files','experiment_files'):
        for name,digest in binding[key].items():
            audit.equal(sha256((audit.ROOT/name).read_bytes()).hexdigest(),digest,'current source '+name)
    audit.equal(binding['frozen_revision'],FROZEN,'frozen runtime')
    audit.equal(binding['projection_revision'],PROJECTION,'frozen projection')
    for key,revision in (('frozen_files',FROZEN),('projection_files',PROJECTION),('experiment_files',binding['experiment_revision'])):
        for name,digest in binding[key].items():
            audit.equal(sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=audit.ROOT)).hexdigest(),digest,'source revision '+name)
    audit.equal(sorted(binding['experiment_files']),sorted(OWN_FILES),'experiment file inventory')
    audit.equal(sorted(binding['frozen_files']),sorted(audit.source_inputs()),'runtime file inventory')
    audit.equal(sorted(binding['projection_files']),sorted(projection.TOOL_FILES),'projection file inventory')


def reference_cell(task,budget):
    ref=Reference(task,budget['budget']);labels=ref.labels()
    enumeration=enumerate_histories(task,budget['budget'],node_limit=Bounds().enumeration_nodes)
    if labels['status']==enumeration['status']=='EXACT':
        audit.equal(labels['root']['q'],enumeration['q'],'independent complete enumeration')
    return ref,dict(task_id=task['task_id'],budget=budget['budget'],reference=labels,enumeration=enumeration)


def feasibility():
    start=perf_counter_ns();rows=[]
    for task in cohort():
        for budget in budgets():
            _,data=reference_cell(task,budget)
            rows.append(dict(task_id=task['task_id'],configuration=budget['name'],budget=budget['budget'],
                **{k:data['reference'][k] for k in ('status','states','transitions','memory_accounting_bytes','elapsed_ns')},
                enumeration_status=data['enumeration']['status'],enumeration_nodes=data['enumeration']['nodes'],
                enumeration_ns=data['enumeration']['elapsed_ns']))
    return dict(schema='decision-reference-feasibility/v1',policy_measurements=0,bounds=asdict(Bounds()),
        configuration_digest=fingerprint(configuration()),cells=rows,elapsed_ns=perf_counter_ns()-start)


def selected_label(ref,state,action):
    if state not in ref.memo: raise ValueError('observed state is outside fully enumerated public reference model')
    label=ref.memo[state]
    if action not in label['q']: raise ValueError('selected action is not admissible in independent model')
    return dict(state=state.wire(),value=label['value'],q=label['q'],optimal_actions=label['optimal_actions'],
        selected=action,regret=label['q'][action]['value']-label['value'],agreement=action in label['optimal_actions'])


def tie_info(ranks,field):
    tolerance=1e-12+(2*field['error_bound_l1'] if field else 0)
    order=sorted(ranks,key=lambda c:(ranks[c],c))
    top=[] if not order else [c for c in order if abs(ranks[c][0]-ranks[order[0]][0])<=tolerance]
    return dict(tolerance=tolerance,primary_top=top,primary_tied=len(top)>1)


def journal_signature(authority,context):
    state=authority.snapshot(context)
    return dict(commands=[(e.command,e.key) for e in authority._journal.entries()],
        history={str(k):v for k,v in audit.belief_history(authority,context).items()},usable=sorted(b.accepted_at_revision for b in state.usable),
        logical_time=state.logical_time,knowledge_revision=state.knowledge_revision,
        goals={g:dict(outstanding=authority.inspect_goal(g).projection.slices[0].outstanding_loss,
                      coverage=authority.inspect_goal(g).projection.slices[0].estimated_coverage)
               for g in authority._goals.goals})


def save_signature(path,task):
    # Read only the closed local authority through an audited copy.
    with TemporaryDirectory() as temp:
        target=Path(temp)/'journal.db';shutil.copyfile(audit.artifact_path(path,'admission.db'),target)
        with AdmissionService(database=target) as authority: return journal_signature(authority,task['public']['context_id'])



def check_saved_prefix(path,task,rows,snapshot=None):
    """Bind opaque goal event IDs and receipt beliefs to the supplied journal."""
    snapshots=[r['snapshot'] for r in rows if r['stage']=='selection']
    if snapshot is not None: snapshots.append(snapshot)
    with TemporaryDirectory() as temp:
        copied=Path(temp)/'saved.db';shutil.copyfile(audit.artifact_path(path,'admission.db'),copied)
        with AdmissionService(database=copied) as authority:
            beliefs=authority._contexts[task['public']['context_id']].beliefs
            for row in rows:
                if row['stage']=='receipt':
                    belief=row['receipt']['belief']
                    audit.require(belief is None or belief in beliefs,'prefix receipt belief absent from journal')
            for snapshot in snapshots:
                for goal in snapshot['goals']:
                    view=authority.inspect_goal(goal['goal_id'])
                    for key,kind in (('relief_events','observed_relief'),('reopened_events','reopened')):
                        events=[e.event_id for revision in view.history for e in revision.events if e.kind==kind]
                        audit.equal(goal[key],events[:len(goal[key])],'saved prefix exact goal events')


def check_common_costs(saved,fresh,sample):
    for key in ('budget','remaining_budget'):
        audit.equal(saved[key],sample[key],'common query '+key)
    audit.equal(saved['candidate_visits'],sample['budget']['candidate_visits']-sample['remaining_budget']['candidate_visits'],'common discovery work')
    audit.nonnegative_counts({'elapsed_ns':saved['elapsed_ns'],'discovery_ns':saved['discovery_ns']},'common times')
    for key in ('normalization_visits','projected_occurrences','ranking_calls'):
        audit.equal(saved['metrics'][key],fresh['metrics'][key],'common projection '+key)
    for key in ('normalization_ns','graph_ns','normalization_visits','projected_occurrences'):
        audit.equal(saved['metrics'][key],sum(e[key] for e in saved['evaluations']),'common projection sum '+key)
    for evaluation in saved['evaluations']:
        audit.nonnegative_counts({k:v for k,v in evaluation.items() if k!='epoch'},'common projection timing')
        audit.equal(evaluation['epoch'],saved['pressure']['epoch'],'common measured epoch')
    measured=saved['metrics']['normalization_ns']+saved['metrics']['graph_ns']+sum(e['iteration_ns'] for e in saved['evaluations'])
    audit.require(saved['elapsed_ns']>=measured,'common inclusive time below measured categories')


def common_sample(task,budget,ref,prefix,path):
    start=perf_counter_ns();path.mkdir(parents=True,exist_ok=False)
    with (path/'trace.jsonl').open('w') as stream,ReasoningSession(task['public'],path) as session:
        world=ReasoningWorld(session,materialize(task));world.sample_outcomes()
        state=execute_prefix(task,ref,session,world,prefix,lambda row:stream.write(canonical(row)+'\n'))
        snapshot=session.read();prefix_elapsed=perf_counter_ns()-start
        remaining=dict(budget['budget'],actions=state.requests,operation_work=state.operation_work,observation_work=state.observation_work)
        tick=perf_counter_ns();frontier=enumerate_work(task['public'],snapshot,visit_limit=remaining['candidate_visits']);discovery=perf_counter_ns()-tick
        affordable=[c for c in frontier.candidates if operation_cost(task['public'],c)<=state.operation_work and c.observation_cost<=state.observation_work]
        audit.require(frontier.complete,'common discovery exhausted')
        if frontier.terminal or not state.requests: affordable=[]
        audit.equal(sorted(semantic_action(c) for c in affordable),sorted(a for a in ref.actions(state) if a!=STOP),'common independent candidate set')
        remaining['candidate_visits']-=frontier.visits
        rankings=[]
        for policy in POLICIES:
            rank=rank_fixed(task,snapshot,affordable,remaining,policy)
            audit.require(rank['status']=='PASS','common ranking exhausted')
            rank.update(budget=budget['budget'],remaining_budget=remaining,
                discovery_ns=discovery,candidate_visits=frontier.visits,
                label=selected_label(ref,state,rank['selected']),ties=tie_info(rank['ranks'],rank['pressure']))
            rankings.append(rank)
        result=dict(task_id=task['task_id'],budget=budget['budget'],prefix=prefix,state=state.wire(),snapshot=snapshot,
            candidates=[c.wire() for c in affordable],all_candidates=[c.wire() for c in frontier.candidates],
            remaining_budget=remaining,rankings=rankings,prefix_elapsed_ns=prefix_elapsed,
            discovery_ns=discovery,elapsed_ns=perf_counter_ns()-start,prefix_authority_metrics=dict(session.metrics.values))
    result['journal_signature']=save_signature(path,task)
    return result


def decisions(task,budget,ref,result,path):
    rows=[json.loads(line) for line in (path/'trace.jsonl').read_text().splitlines()];labels=[]
    for i,row in enumerate(rows):
        if row['stage']!='selection': continue
        work=dict(row['work']);action=semantic_action(row['selected'])
        work['actions']-=1
        work['operation_work']-=task['public']['costs'][row['selected']['arguments']['rule_id']] if row['selected']['kind']=='derive' else 1
        work['observation_work']-=row['selected']['observation_cost']
        remaining=remaining_budget(budget['budget'],work)
        state=reference_state(task,row['snapshot'],remaining)
        label=selected_label(ref,state,action)
        label.update(budget=budget['budget'],remaining_budget=remaining,step=row['step'],
            candidates=row['candidates'],ranks=row['ranks'],ties=tie_info(row['ranks'],row['pressure']),
            receipt=rows[i+1]['receipt'],outcome_before=result['outcomes'][state.tick],outcome_after=result['outcomes'][state.tick+1])
        labels.append(label)
    state=reference_state(task,result['controller_stop_snapshot'],remaining_budget(budget['budget'],result['work']))
    stop=selected_label(ref,state,STOP)
    return dict(decisions=labels,stop=stop,episode_gap=result['integrated_external_loss']-ref.memo[ref.initial()]['value'])


def witness_labels(task,label):
    values=[('optimal',label)]
    if not task['sibling'] and task['task_id'].endswith('-0'):
        values += [(action.replace('/','-'),item) for action,item in label['q'].items()]
    seen=set();selected=[]
    for name,value in values:
        key=tuple(value['witness'])
        if key not in seen: selected.append((name,value));seen.add(key)
    return selected


def aggregate(directory,index):
    groups=defaultdict(list);paired={};common_groups=defaultdict(list);all_closed=[];all_common=[]
    for cell in index:
        task=cell['task'];budget=cell['configuration'];key=cell['name']
        for name in cell['closed']:
            entry=audit.load(directory,name+'/result.json');r=entry['result'];p=entry['policy']
            paired[(task['task_id'],budget['name'],p)]=entry
            row=dict(task_id=task['task_id'],parent_id=task['parent_id'],family=task['family'],partition=task['partition'],
                sibling=task['sibling'],policy=p,configuration=budget['name'],budget=budget['budget'],
                loss=r['integrated_external_loss'],gap=entry['labels']['episode_gap'],
                external=r['final']['external_weighted_loss'],certified=r['final']['certified_weighted_loss'],
                work=r['work'],costs_ns=r['costs_ns'],normalization_ns=entry['metrics']['normalization_ns'],
                graph_ns=entry['metrics']['graph_ns'],total_elapsed_ns=r['total_elapsed_ns'],failures=r['failures'],
                pressure_exhausted=r['pressure_exhausted'],pressure_converged=r['pressure_converged'],
                unresolved_goals=[g for g in r['final_snapshot']['goals'] if g['outstanding']],
                unresolved_commitments=[g['selected_commitment'] for g in r['final_snapshot']['goals'] if g['selected_commitment'] is not None],path=name)
            all_closed.append(row)
            if not task['sibling']: groups[(task['partition'],task['family'],budget['name'],p)].append(row)
        for name in cell['common']:
            sample=audit.load(directory,name+'/result.json')
            for rank in sample['rankings']:
                row=dict(task_id=task['task_id'],parent_id=task['parent_id'],family=task['family'],partition=task['partition'],
                    sibling=task['sibling'],policy=rank['policy'],configuration=budget['name'],budget=budget['budget'],
                    remaining_budget=rank['remaining_budget'],regret=rank['label']['regret'],agreement=rank['label']['agreement'],
                    primary_tied=rank['ties']['primary_tied'],reference_tied=len(rank['label']['optimal_actions'])>1,
                    selected=rank['selected'],path=name)
                all_common.append(row)
                if not task['sibling']: common_groups[(task['partition'],task['family'],budget['name'],rank['policy'])].append(row)
    summaries=[]
    for key,rows in sorted(groups.items()):
        partition,family,b,p=key;common=common_groups[key]
        delta=[row['loss']-paired[(row['task_id'],b,'B0')]['result']['integrated_external_loss'] for row in rows]
        summaries.append(dict(partition=partition,family=family,configuration=b,policy=p,budget=rows[0]['budget'],parents=len(rows),
            mean_loss=sum(r['loss'] for r in rows)/len(rows),mean_gap=sum(r['gap'] for r in rows)/len(rows),max_gap=max(r['gap'] for r in rows),
            common_states=len(common),optimal_agreement=sum(r['agreement'] for r in common),
            mean_regret=sum(r['regret'] for r in common)/len(common),max_regret=max(r['regret'] for r in common),
            policy_primary_ties=sum(r['primary_tied'] for r in common),reference_ties=sum(r['reference_tied'] for r in common),
            favorable=sum(d<0 for d in delta),neutral=sum(d==0 for d in delta),unfavorable=sum(d>0 for d in delta)))
    siblings=[]
    for cell in index:
        task=cell['task'];b=cell['configuration']['name']
        if not task['sibling']: continue
        inverse={v:k for k,v in task['rename'].items()}
        parent=next(c for c in index if c['task']['task_id']==task['parent_id'] and c['configuration']['name']==b)
        parent_reference=audit.load(directory,parent['name']+'/labels.json')['reference']['root']
        child_reference=audit.load(directory,cell['name']+'/labels.json')['reference']['root']
        for p in POLICIES:
            left=paired[(task['parent_id'],b,p)];right=paired[(task['task_id'],b,p)]
            lchoices=[r['selected'] for r in left['labels']['decisions']]
            rchoices=[inverse.get(r['selected'],r['selected']) for r in right['labels']['decisions']]
            comparisons=[]
            for ln,rn in zip(parent['common'],cell['common']):
                ls=next(x for x in audit.load(directory,ln+'/result.json')['rankings'] if x['policy']==p)
                rs=next(x for x in audit.load(directory,rn+'/result.json')['rankings'] if x['policy']==p)
                comparisons.append(dict(parent=ls['selected'],sibling=inverse.get(rs['selected'],rs['selected']),
                    changed=ls['selected']!=inverse.get(rs['selected'],rs['selected']),parent_tie=ls['ties']['primary_tied'],
                    sibling_tie=rs['ties']['primary_tied'],parent_regret=ls['label']['regret'],sibling_regret=rs['label']['regret']))
            siblings.append(dict(task_id=task['task_id'],parent_id=task['parent_id'],kind=task['sibling_kind'],policy=p,
                configuration=b,budget=cell['configuration']['budget'],reference_optimum_equal=child_reference['value']==parent_reference['value'],
                trajectory_equal=lchoices==rchoices,loss_delta=right['result']['integrated_external_loss']-left['result']['integrated_external_loss'],
                common=comparisons))
    return dict(groups=summaries,closed=all_closed,common=all_common,siblings=siblings,
        totals=dict(closed_runs=len(all_closed),common_rankings=len(all_common),witnesses=sum(len(c['witnesses']) for c in index),
            failures=dict(sum((Counter(r['failures']) for r in all_closed),Counter())),
            pressure_bounds=sum(bool(r['pressure_exhausted']) for r in all_closed),unconverged=sum(not r['pressure_converged'] for r in all_closed)))


def write_readable(report,path):
    a=report['analysis'];lines=['# Bounded decision-value comparison','',
        'Source: `'+report['sources']['experiment_revision']+'`; frozen runtime `'+FROZEN+'`; projection `'+PROJECTION+'`.','',
        'Primary objective: integrated external unresolved loss over ticks 0–15. Operation work is not duration. All five policies are unchanged. No reference answers are supplied to policies.','',
        '48 parent tasks (30 development, 18 locked confirmation); 12 identifier and 6 dominated-option siblings are diagnostics, not independent parents. Complete task/budget rows and per-decision Q values, optimal sets, witness continuations, candidates, scores and receipts are in analysis.json and cell artifacts.','',
        'Budget vectors:','']
    for b in budgets(): lines+=['- `'+b['name']+'`: `'+canonical(b['budget'])+'`.']
    lines+=['','Exact coverage: '+str(report['coverage'])+'. Full independent enumeration cross-checks each initial label and every sampled state. Canonical witnesses and predeclared control Q witnesses execute through the real certified interfaces.','',
        'Agreement and regret below concern predeclared common states. Episode gap is full trajectory loss minus V*, never a sum of overlapping decision regrets. Group means are descriptive; no statistical power, CI, or single-run timing significance is claimed.','',
        '| Partition | Family | Budget | Policy | Parents | Agree/states | Mean regret | Mean gap | Max gap | Vs B0 favorable/neutral/unfavorable |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---|']
    for r in a['groups']:
        lines.append(f"| {r['partition']} | {r['family']} | {r['configuration']} | {r['policy']} | {r['parents']} | {r['optimal_agreement']}/{r['common_states']} | {r['mean_regret']:.3f} | {r['mean_gap']:.3f} | {r['max_gap']:g} | {r['favorable']}/{r['neutral']}/{r['unfavorable']} |")
    lines+=['','## Retained decision divergences','',
        'These are the highest common-state regrets per family and budget (deterministic task/policy tie order). Each link contains every Q continuation, score and exact budget. Subsequent actual trajectories are separate closed-loop traces; these counterfactual regrets do not attribute an entire episode gap.','']
    for family in ('or','and','shared','depth','budget','completion'):
        for b in budgets():
            rows=[r for r in a['common'] if not r['sibling'] and r['family']==family and r['configuration']==b['name']]
            r=min(rows,key=lambda r:(-r['regret'],r['task_id'],r['policy'],r['path']))
            lines.append(f"- {family}, {b['name']}: {r['task_id']} / {r['policy']} chooses `{r['selected']}`, regret {r['regret']}; [complete decision]({r['path']}/result.json).")
    lines+=['','## Accounting and limitations','',
        'Costs include candidate discovery, normalization, graph construction, pressure iteration, ranking, actual inference, certification, persistence and elapsed time. Normalization plus graph equals pressure construction; execution includes authority categories. Do not double count inclusive fields. Common-state discovery is measured once and charged equally to every policy; prefix setup and exact reference work are offline costs. Full rows retain counts, costs, external versus certified loss, unresolved goals and commitments, stale/unknown replies and source ledgers.','',
        'Memory limits are conservative deterministic reference allocation charges, not measured peak RSS. Peak memory, OS scheduling attribution, individual fsync/SQLite bytes and real sensor latency are unmeasured. Recorded timing cannot be reproduced by replay. No native numerical PLN scheduling or transport is claimed.','',
        'The original hidden-event rich episode remains descriptive in the preserved reviews. No same-information Q/V target or hindsight optimum is assigned to it. Original raw B3 remains a regression reference.','',
        'Siblings: '+str(len(a['siblings']))+' policy/budget comparisons; details in analysis.json. Identifier matches are not the definition of correctness; every exact primary-optimal action is accepted. Dominated options retain the old feasible optimal plan.','',
        'Totals: `'+canonical(a['totals'])+'`. Reference generation: '+str(report['reference_elapsed_ns']/1e9)+' s; experiment elapsed (including witness/setup): '+str(report['experiment_elapsed_ns']/1e9)+' s. Independent replay/audit time is in audit.json.','']
    path.write_text('\n'.join(lines))


def run(directory):
    start=perf_counter_ns();sources=source_binding();config=configuration()
    audit.equal(config,json.loads((audit.ROOT/'reviews/decision-value-v1/inventory.json').read_text()),'committed case inventory')
    directory.mkdir(parents=True,exist_ok=False);write(directory/'configuration.json',config);write(directory/'sources.json',sources)
    index=[];refs={};prefixes={};reference_elapsed=0;coverage=Counter()
    # Solve every declared case before policy work. Never substitute easier cases.
    for task in config['tasks']:
        for budget in config['budgets']:
            name=task['task_id']+'/'+budget['name'];cell=dict(name=name,task=task,configuration=budget,common=[],closed=[],witnesses=[])
            ref,labels=reference_cell(task,budget);refs[name]=ref;coverage[labels['reference']['status']]+=1
            reference_elapsed+=labels['reference']['elapsed_ns']+labels['enumeration']['elapsed_ns']
            write(directory/name/'labels.json',labels);index.append(cell)
    write(directory/'index.json',index)
    # Censored labels are retained. This predeclared finite experiment requires
    # exact labels for reference-ranked comparisons; do not mislabel a partial run.
    if coverage.get('REFERENCE_EXHAUSTED'):
        write(directory/'censored.json',dict(coverage=coverage,status='REFERENCE_EXHAUSTED'))
        raise ValueError('reference exhausted; inventory retained without replacement or invented optima')
    for cell_index,cell in enumerate(index):
        task,budget,name=cell['task'],cell['configuration'],cell['name'];ref=refs[name]
        if task['sibling']:
            pp=prefixes[task['parent_id']+'/'+budget['name']]
            selected_prefixes=[[task['rename'].get(a,a) for a in prefix] for prefix in pp]
            parent_ref=refs[task['parent_id']+'/'+budget['name']]
            audit.equal(ref.solve()['value'],parent_ref.solve()['value'],'sibling reference optimum')
            old=ref.initial()
            for action in parent_ref.solve()['witness']:
                if action!=STOP: old=ref.successor(old,task['rename'].get(action,action))
        else: selected_prefixes=[prefix for _,prefix in ref.sampled_states()]
        prefixes[name]=selected_prefixes
        sampled=[]
        for i,prefix in enumerate(selected_prefixes):
            place=name+'/common-'+str(i);sample=common_sample(task,budget,ref,prefix,directory/place)
            enum=enumerate_histories(task,budget['budget'],state=sample['state'],node_limit=Bounds().enumeration_nodes)
            audit.equal(enum['status'],'EXACT','common independent enumeration coverage')
            audit.equal(enum['q'],sample['rankings'][0]['label']['q'],'common independent enumeration Q')
            reference_elapsed+=enum['elapsed_ns'];sample['enumeration']=enum
            write(directory/place/'result.json',sample);cell['common'].append(place);sampled.append(ref.memo[reference_state(task,sample['snapshot'],sample['remaining_budget'])])
        write(directory/name/'sample-labels.json',sampled)
        for label_name,label in witness_labels(task,ref.solve()):
            place=name+'/witness-'+label_name
            result=witness(task,ref,label,directory/place);result['budget']=budget['budget'];result['reference_label']=label
            result['journal_signature']=save_signature(directory/place,task)
            write(directory/place/'result.json',result);cell['witnesses'].append(place)
        rotation=cell_index%len(POLICIES);order=POLICIES[rotation:]+POLICIES[:rotation]
        for policy in order:
            place=name+'/'+policy
            with public_task(task) as delivered,projection.ranking_policy(policy) as measured:
                result=runner.run_one(materialize(task),'B0' if policy=='B0' else 'B3',budget,directory/place)
            audit.equal(delivered,[fingerprint(task)],'policy public task delivery')
            entry=dict(policy=policy,result=result,delivered_contracts=delivered,**measured,
                labels=decisions(task,budget,ref,result,directory/place))
            write(directory/place/'result.json',entry);cell['closed'].append(place)
        write(directory/'index.json',index)
        print(f"completed {cell_index+1}/{len(index)}: {name}",flush=True)
    analysis=aggregate(directory,index);write(directory/'analysis.json',analysis)
    report=dict(schema='decision-value-results/v1',sources=sources,configuration_digest=fingerprint(config),coverage=dict(coverage),
        reference_elapsed_ns=reference_elapsed,experiment_elapsed_ns=perf_counter_ns()-start,analysis=analysis)
    # Do not duplicate large raw rows in report.json.
    write(directory/'report.json',{k:v for k,v in report.items() if k!='analysis'})
    write_readable(report,directory/'comparison.md')
    seal(directory)
    result=audit_experiment(directory);write(directory/'audit.json',result)
    seal(directory)
    return result


def seal(directory):
    files={}
    for p in sorted(directory.rglob('*')):
        if p.is_file() and p.name!='bundle.json' and not p.name.endswith(('.lock','-wal','-shm')):
            files[p.relative_to(directory).as_posix()]=sha256(p.read_bytes()).hexdigest()
    write(directory/'bundle.json',dict(schema='decision-value-bundle/v1',files=files))


def check_projection(entry,rows):
    fields=projection.evaluated_fields(rows);metrics=entry['metrics'];evaluations=entry['evaluations'];r=entry['result']
    audit.equal(metrics['ranking_calls'],len(fields),'live fixed ranking invocation count')
    audit.equal([e['epoch'] for e in evaluations],[f['epoch'] for f in fields],'projection epoch binding')
    for key in ('normalization_ns','graph_ns','normalization_visits','projected_occurrences'):
        audit.equal(metrics[key],sum(e[key] for e in evaluations),'measured projection '+key)
    audit.equal(metrics['normalization_ns']+metrics['graph_ns'],r['costs_ns']['pressure_construction_ns'],'charged construction')
    audit.equal(sum(e['iteration_ns'] for e in evaluations),r['costs_ns']['pressure_iteration_ns'],'charged iteration')
    for field,e in zip(fields,evaluations):
        work=field['binding']['projection']['work']
        audit.equal((e['normalization_visits'],e['projected_occurrences']),(work['visits'],work['projected']),'charged projection work')


def audit_experiment(directory):
    directory=Path(directory);start=perf_counter_ns();config=audit.load(directory,'configuration.json');audit.equal(config,configuration(),'fixed experiment')
    report=audit.load(directory,'report.json');verify_sources(report['sources']);audit.equal(report['configuration_digest'],fingerprint(config),'config binding')
    audit.equal(audit.load(directory,'sources.json'),report['sources'],'source binding')
    bundle=audit.load(directory,'bundle.json');audit.equal(bundle['schema'],'decision-value-bundle/v1','bundle schema')
    for name,digest in bundle['files'].items():
        audit.equal(sha256(audit.artifact_path(directory,name).read_bytes()).hexdigest(),digest,'artifact '+name)
    index=audit.load(directory,'index.json');audit.equal([(c['task'],c['configuration']) for c in index],[(t,b) for t in config['tasks'] for b in config['budgets']],'complete matrix')
    checked=common_count=witness_count=0;references={};sample_prefixes={};coverage=Counter();expected={'configuration.json','sources.json','index.json','analysis.json','report.json','comparison.md'}
    if 'audit.json' in bundle['files']: expected.add('audit.json')
    for cell in index:
        task,budget,name=cell['task'],cell['configuration'],cell['name'];ref,labels=reference_cell(task,budget);references[name]=ref
        saved=audit.load(directory,name+'/labels.json');coverage[saved['reference']['status']]+=1
        for part in ('reference','enumeration'):
            audit.equal({k:v for k,v in saved[part].items() if k!='elapsed_ns'},
                        {k:v for k,v in labels[part].items() if k!='elapsed_ns'},'independent labels '+part)
        expected.update((name+'/labels.json',name+'/sample-labels.json'))
        prefixes=([[task['rename'].get(a,a) for a in prefix] for prefix in sample_prefixes[task['parent_id']+'/'+budget['name']]] if task['sibling'] else [p for _,p in ref.sampled_states()])
        sample_prefixes[name]=prefixes
        audit.equal(cell['common'],[name+'/common-'+str(i) for i in range(len(prefixes))],'common sample inventory')
        samples=[]
        for place,prefix in zip(cell['common'],prefixes):
            saved_sample=audit.load(directory,place+'/result.json')
            with TemporaryDirectory() as temp:
                fresh=common_sample(task,budget,ref,prefix,Path(temp)/'common')
                # Preserve actual relief event identities in saved traces; compare
                # only the established opaque-ID quotient across authorities.
                audit.equal(audit.semantic_snapshot(saved_sample['snapshot']),audit.semantic_snapshot(fresh['snapshot']),'common public state')
                for key in ('task_id','budget','prefix','state','candidates','all_candidates','remaining_budget','journal_signature'):
                    audit.equal(saved_sample[key],fresh[key],'common sample '+key)
                audit.equal(save_signature(directory/place,task),saved_sample['journal_signature'],'saved common journal')
                recorded_trace=[json.loads(x) for x in (directory/place/'trace.jsonl').read_text().splitlines()]
                fresh_trace=[json.loads(x) for x in (Path(temp)/'common/trace.jsonl').read_text().splitlines()]
                compare_prefix_trace(recorded_trace,fresh_trace)
                check_saved_prefix(directory/place,task,recorded_trace,saved_sample['snapshot'])
                audit.equal(audit.authority_work(saved_sample['prefix_authority_metrics']),audit.authority_work(fresh['prefix_authority_metrics']),'common prefix authority work')
                frontier=enumerate_work(task['public'],saved_sample['snapshot']);ids={c['candidate_id'] for c in saved_sample['candidates']}
                candidates=[c for c in frontier.candidates if c.candidate_id in ids]
                audit.equal([r['policy'] for r in saved_sample['rankings']],POLICIES,'common policy inventory')
                for old in saved_sample['rankings']:
                    new=rank_fixed(task,saved_sample['snapshot'],candidates,saved_sample['remaining_budget'],old['policy'])
                    check_common_costs(old,new,saved_sample)
                    for key in ('status','policy','task_digest','selected','ranks','pressure','work'):
                        audit.equal(old[key],new[key],'common ranking '+key)
                    state=reference_state(task,saved_sample['snapshot'],saved_sample['remaining_budget'])
                    audit.equal(old['label'],selected_label(ref,state,old['selected']),'common regret label')
                    audit.equal(old['budget'],budget['budget'],'common full budget')
                    audit.equal(old['ties'],tie_info(old['ranks'],old['pressure']),'common ties')
                    audit.equal(old['discovery_ns'],saved_sample['discovery_ns'],'equal charged common discovery')
                enum=enumerate_histories(task,budget['budget'],state=saved_sample['state'])
                audit.equal(enum['q'],saved_sample['enumeration']['q'],'second sampled-state enumeration')
                audit.equal(enum['q'],saved_sample['rankings'][0]['label']['q'],'sample reference Q')
                samples.append(ref.memo[state]);common_count+=len(POLICIES)
            expected.update(place+'/'+f for f in ('result.json','trace.jsonl','admission.db'))
        audit.equal(audit.load(directory,name+'/sample-labels.json'),samples,'all sampled labels')
        labels_to_replay=witness_labels(task,ref.solve())
        audit.equal(cell['witnesses'],[name+'/witness-'+n for n,_ in labels_to_replay],'witness selection inventory')
        for place,(_,label) in zip(cell['witnesses'],labels_to_replay):
            saved_w=audit.load(directory,place+'/result.json')
            with TemporaryDirectory() as temp:
                fresh=witness(task,ref,label,Path(temp)/'w')
                for key in ('status','witness','integrated_loss','final','outcomes','terminal_state','journal_commands'):
                    audit.equal(saved_w[key],fresh[key],'certified witness '+key)
                audit.equal(saved_w['reference_label'],label,'witness label')
                audit.equal(saved_w['budget'],budget['budget'],'witness budget')
                audit.equal(save_signature(directory/place,task),saved_w['journal_signature'],'saved witness journal')
                audit.equal(save_signature(Path(temp)/'w',task),saved_w['journal_signature'],'reproduced witness journal')
                compare_prefix_trace([json.loads(x) for x in (directory/place/'trace.jsonl').read_text().splitlines()],
                    [json.loads(x) for x in (Path(temp)/'w/trace.jsonl').read_text().splitlines()])
                check_saved_prefix(directory/place,task,[json.loads(x) for x in (directory/place/'trace.jsonl').read_text().splitlines()])
                audit.equal(audit.authority_work(saved_w['metrics']),audit.authority_work(fresh['metrics']),'witness authority work')
                witness_count+=1
            expected.update(place+'/'+f for f in ('result.json','trace.jsonl','admission.db'))
        audit.equal(sorted(cell['closed']),sorted(name+'/'+p for p in POLICIES),'closed policy inventory')
        initial=None
        for place in cell['closed']:
            entry=audit.load(directory,place+'/result.json');r=entry['result'];policy=entry['policy']
            audit.equal(place,name+'/'+policy,'closed identity');audit.equal(entry['delivered_contracts'],[fingerprint(task)],'same public model delivery')
            with public_task(task),projection.ranking_policy(policy):
                checked+=audit.audit_run(directory/place,materialize(task),budget,r)
            pair=(r['initial_snapshot'],r['initial_candidates'])
            if initial is None: initial=pair
            audit.equal(pair,initial,'same initial public inputs')
            audit.equal(entry['labels'],decisions(task,budget,ref,r,directory/place),'closed decision and episode labels')
            rows=[json.loads(x) for x in (directory/place/'trace.jsonl').read_text().splitlines()]
            check_projection(entry,rows)
            expected.update(place+'/'+f for f in ('result.json','trace.jsonl','admission.db'))
    audit.equal(sorted(bundle['files']),sorted(expected),'complete artifact inventory')
    audit.equal(report['coverage'],dict(coverage),'reference coverage')
    analysis=aggregate(directory,index);audit.equal(audit.load(directory,'analysis.json'),analysis,'all outcome aggregations')
    with TemporaryDirectory() as temp:
        target=Path(temp)/'comparison.md';write_readable(dict(report,analysis=analysis),target)
        audit.equal((directory/'comparison.md').read_text(),target.read_text(),'readable comparison')
    return dict(status='PASS',cells=len(index),runs=sum(len(c['closed']) for c in index),
        selections_reproduced=checked,common_rankings_reproduced=common_count,witnesses_reproduced=witness_count,
        coverage=dict(coverage),elapsed_ns=perf_counter_ns()-start,
        limitation='Trusted evaluator replay, not authentication of historical timing or publisher identity.')


def compare_prefix_trace(recorded,fresh):
    audit.equal(len(recorded),len(fresh),'prefix trace length')
    for old,new in zip(recorded,fresh):
        audit.equal(old['stage'],new['stage'],'prefix framing')
        if old['stage']=='selection':
            for key in ('candidates','selected','state'): audit.equal(old[key],new[key],'prefix '+key)
            audit.equal(audit.semantic_snapshot(old['snapshot']),audit.semantic_snapshot(new['snapshot']),'prefix snapshot')
        elif old['stage']=='receipt':
            audit.equal(old['state'],new['state'],'prefix state')
            for key in ('status','detail','knowledge_revision'): audit.equal(old['receipt'][key],new['receipt'][key],'prefix receipt '+key)
            audit.equal(audit.authority_work(old['receipt']['costs']),audit.authority_work(new['receipt']['costs']),'prefix receipt work')
        else: audit.equal(old,new,'prefix terminal result')


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path);group.add_argument('--audit',type=Path);group.add_argument('--feasibility',type=Path)
    args=parser.parse_args()
    if args.feasibility: write(args.feasibility,feasibility());return
    if args.audit: result=audit_experiment(args.audit)
    else:
        try: result=run(args.output)
        except BaseException as error:
            if args.output.exists(): write(args.output/'FAILED.json',dict(status='FAIL',error=repr(error),retained=True))
            raise
    print(canonical(result))


if __name__=='__main__': main()
