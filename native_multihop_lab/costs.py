"""Descriptive nested cost totals; inclusive timers are never summed together."""
import json
from collections import defaultdict
from pathlib import Path
from validation_lab.decision_comparison import write


def collect(root,report):
    groups={}
    for arm in ('MH-scan','MH-native'):
        group=dict(episodes=0,rows=0,elapsed_ns=0,formula_calls=0,fresh_native_pln_calls=0,epochs=0,
                   native_counters={},nested_timers_ns={},capture_bytes=0,frame_serialized_bytes=0)
        timers=defaultdict(int);counters=defaultdict(int)
        def timing(prefix,value):
            if isinstance(value,dict):
                for k,v in value.items():
                    path=prefix+'.'+k
                    if k.endswith('_ns') and isinstance(v,int):timers[path]+=v
                    elif isinstance(v,dict):timing(path,v)
        for result in report['results']:
            if result['arm']!=arm:continue
            group['episodes']+=1;group['elapsed_ns']+=result['elapsed_ns'];group['formula_calls']+=len(result['runtime_calls']);group['fresh_native_pln_calls']+=sum(c['mode']=='native' for c in result['runtime_calls']);group['epochs']+=result.get('native_epochs',0)
            timing('session',result['costs_ns']);timing('environment',result['environment_costs_ns'])
            for k,v in result.get('native_costs',{}).items():
                if not k.endswith('_ns'):counters[k]+=v
            path=Path(root)/(arm+'-'+result['mode']+'-'+result['parent'])/'trace.jsonl'
            for row in map(json.loads,path.read_text().splitlines()):
                group['rows']+=1;timing('observation',row['costs']);timers['consumer.selection_inclusive_ns']+=row['choice']['selection_elapsed_ns'];timers['consumer.frontier_nested_ns']+=row['frontier']['elapsed_ns'];timing('revalidation',row.get('revalidation',{}))
                from reachability.trace_protocol import canonical
                group['frame_serialized_bytes']+=len(canonical(row['frame']).encode())
                d=row['costs'].get('native_retrieval',{});group['capture_bytes']+=d.get('capture_bytes',0)
        group['native_counters']=dict(counters);group['nested_timers_ns']=dict(timers);groups[arm]=group
    return dict(schema='native-multihop-descriptive-costs/v1',revision=report['sources']['revision'],groups=groups,
                overlap='Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.',
                scope='Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.',
                unmeasured=report['unmeasured'])


def render(data):
    a,b=(data['groups'][x] for x in ('MH-scan','MH-native'));lines=['# Descriptive cost accounting','',data['overlap'],'',
        '| Quantity | MH-scan | MH-native |','|---|---:|---:|']
    for key in ('episodes','rows','formula_calls','fresh_native_pln_calls','epochs','frame_serialized_bytes'):
        lines.append(f'| {key} | {a[key]} | {b[key]} |')
    lines.append(f"| Total episode seconds | {a['elapsed_ns']/1e9:.6f} | {b['elapsed_ns']/1e9:.6f} |")
    lines+=['','| Timer (seconds, nested) | MH-scan | MH-native |','|---|---:|---:|']
    for k in sorted(set(a['nested_timers_ns'])|set(b['nested_timers_ns'])):
        lines.append(f"| {k} | {a['nested_timers_ns'].get(k,0)/1e9:.6f} | {b['nested_timers_ns'].get(k,0)/1e9:.6f} |")
    lines+=['',data['scope'],'','Unmeasured: '+', '.join(data['unmeasured'])+'.',
      '', 'Whole snapshots are loaded. Neither short native responses nor same-binding reuse establishes bounded total memory or realistic warm-workload performance. Logical time does not advance with wall-clock computation.']
    return '\n'.join(lines)+'\n'
