"""Descriptive nested cost totals; inclusive timers are never summed together."""
import json
from collections import defaultdict
from pathlib import Path
from validation_lab.decision_comparison import write
from .config import ARMS,folder


def collect(root,report):
    groups={}
    for arm in ARMS:
        group=dict(episodes=0,rows=0,elapsed_ns=0,formula_calls=0,fresh_native_pln_calls=0,epochs=0,
                   native_counters={},runtime_counters={},coarse_disjoint_ns={},nested_timers_ns={},capture_bytes=0,frame_serialized_bytes=0)
        timers=defaultdict(int);counters=defaultdict(int);runtime=defaultdict(int);coarse=defaultdict(int)
        def timing(prefix,value):
            if isinstance(value,dict):
                for k,v in value.items():
                    path=prefix+'.'+k
                    if k.endswith('_ns') and isinstance(v,int):timers[path]+=v
                    elif isinstance(v,dict):timing(path,v)
        for result in report['results']:
            if result['arm']!=arm:continue
            group['episodes']+=1;group['elapsed_ns']+=result['elapsed_ns'];group['formula_calls']+=len(result['runtime_calls']);group['fresh_native_pln_calls']+=sum(c['mode']=='native' for c in result['runtime_calls']);group['epochs']+=result.get('native_epochs',0)
            timing('runtime',result.get('runtime_costs',{}))
            for k,v in result.get('runtime_costs',{}).items():
                if not k.endswith('_ns'):runtime[k]+=v
            for k,v in result['coarse_disjoint_ns'].items():coarse[k]+=v
            timing('session',result['costs_ns']);timing('environment',result['environment_costs_ns'])
            for k,v in result.get('native_costs',{}).items():
                if not k.endswith('_ns'):counters[k]+=v
            path=Path(root)/folder(result['sweep'],arm,result['mode'],result['parent'])/'trace.jsonl'
            for row in map(json.loads,path.read_text().splitlines()):
                group['rows']+=1;timing('observation',row['costs']);timers['consumer.selection_inclusive_ns']+=row['choice']['selection_elapsed_ns'];timers['consumer.frontier_nested_ns']+=row['frontier']['elapsed_ns'];timing('revalidation',row.get('revalidation',{}))
                from reachability.trace_protocol import canonical
                group['frame_serialized_bytes']+=len(canonical(row['frame']).encode())
                d=row['costs'].get('native_retrieval',{});group['capture_bytes']+=d.get('capture_bytes',0)
        group['coarse_disjoint_ns']=dict(coarse);group['runtime_counters']=dict(runtime);group['native_counters']=dict(counters);group['nested_timers_ns']=dict(timers);groups[arm]=group
    return dict(schema='native-runtime-lifetime-costs/v1',revision=report['sources']['revision'],groups=groups,
                overlap='Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.',
                scope='Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.',
                unmeasured=report['unmeasured'])


def render(data):
    groups=[data['groups'][a] for a in ARMS];lines=['# Runtime lifetime costs','',data['overlap'],'',
        '| Quantity | '+ ' | '.join(ARMS)+' |','|---|---:|---:|---:|']
    for key in ('episodes','rows','formula_calls','fresh_native_pln_calls','epochs','frame_serialized_bytes'):
        lines.append('| '+key+' | '+' | '.join(str(g[key]) for g in groups)+' |')
    lines.append('| Total episode seconds | '+' | '.join(f"{g['elapsed_ns']/1e9:.6f}" for g in groups)+' |')
    for field,label in (('coarse_disjoint_ns','Disjoint coarse phases'),('nested_timers_ns','Nested detailed timers')):
        lines+=['','## '+label,'','| Seconds | '+' | '.join(ARMS)+' |','|---|---:|---:|---:|']
        for k in sorted(set().union(*(g[field] for g in groups))):
            lines.append('| '+k+' | '+' | '.join(f"{g[field].get(k,0)/1e9:.6f}" for g in groups)+' |')
    lines+=['',data['scope'],'','Unmeasured: '+', '.join(data['unmeasured'])+'.',
      '', 'Whole snapshots remain cold loads. Sealed bytes staged are not RSS. Logical time does not advance with wall-clock computation.']
    return '\n'.join(lines)+'\n'


def paired(report):
    """Paired descriptive differences; six fixed tasks, no significance estimate."""
    rows=[]
    for sweep in (0,1):
        for mode in ('finite','native'):
            for parent in dict.fromkeys(r['parent'] for r in report['results']):
                group={r['arm']:r['elapsed_ns'] for r in report['results'] if (r['sweep'],r['mode'],r['parent'])==(sweep,mode,parent)}
                rows.append(dict(sweep=sweep,mode=mode,parent=parent,elapsed_ns=group,
                    session_minus_strict_ns=group['MH-native-session']-group['MH-native-strict'],
                    session_minus_scan_ns=group['MH-native-session']-group['MH-scan']))
    spread=[]
    for arm in ARMS:
        for mode in ('finite','native'):
            for parent in dict.fromkeys(r['parent'] for r in report['results']):
                values=[r['elapsed_ns'][arm] for r in rows if (r['mode'],r['parent'])==(mode,parent)]
                spread.append(dict(arm=arm,mode=mode,parent=parent,sweep0_ns=values[0],sweep1_ns=values[1],range_ns=max(values)-min(values),mean_ns=sum(values)/2))
    return dict(pairs=rows,repeat_variability=spread,interpretation='Two serial sweeps of six fixed parent tasks; local descriptive reproducibility only. Negative differences favor session; zero is neutral; positive differences favor comparator.')


def render_pairs(data):
    lines=['# Paired wall times','',data['interpretation'],'', '| Sweep | Mode | Parent | Scan s | Strict s | Session s | Session minus strict s | Session minus scan s |','|---|---|---|---:|---:|---:|---:|---:|']
    for r in data['pairs']:
        values=[r['elapsed_ns'][a] for a in ARMS]+[r['session_minus_strict_ns'],r['session_minus_scan_ns']]
        lines.append('| '+' | '.join(map(str,(r['sweep'],r['mode'],r['parent'])))+' | '+' | '.join(f'{x/1e9:.6f}' for x in values)+' |')
    lines+=['','## Variability between sweeps','','| Arm | Mode | Parent | Sweep 0 s | Sweep 1 s | Range s |','|---|---|---|---:|---:|---:|']
    for r in data['repeat_variability']:
        lines.append('| '+' | '.join(str(r[k]) for k in ('arm','mode','parent'))+' | '+' | '.join(f'{r[k]/1e9:.6f}' for k in ('sweep0_ns','sweep1_ns','range_ns'))+' |')
    return '\n'.join(lines)+'\n'
