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
                   native_counters={},runtime_counters={},payload_counters={},coarse_disjoint_ns={},nested_timers_ns={},capture_bytes=0,frame_serialized_bytes=0)
        timers=defaultdict(int);counters=defaultdict(int);runtime=defaultdict(int);coarse=defaultdict(int);payload=defaultdict(int)
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

                for k,v in row['costs'].get('payload',{}).items():
                    if isinstance(v,int) and not isinstance(v,bool) and not k.endswith('_ns'):payload[k]+=v
                group['rows']+=1;timing('observation',row['costs']);timers['consumer.selection_inclusive_ns']+=row['choice']['selection_elapsed_ns'];timers['consumer.frontier_nested_ns']+=row['frontier']['elapsed_ns'];timing('revalidation',row.get('revalidation',{}))
                from reachability.trace_protocol import canonical
                group['frame_serialized_bytes']+=len(canonical(row['frame']).encode())
                d=row['costs'].get('native_retrieval',{});group['capture_bytes']+=d.get('capture_bytes',0)
        group['payload_counters']=dict(payload);group['coarse_disjoint_ns']=dict(coarse);group['runtime_counters']=dict(runtime);group['native_counters']=dict(counters);group['nested_timers_ns']=dict(timers);groups[arm]=group
    return dict(schema='frozen-transfer-costs/v1',revision=report['sources']['revision'],groups=groups,
                overlap='Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.',
                scope='Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.',
                unmeasured=report['unmeasured'])


def render(data):
    groups=[data['groups'][a] for a in ARMS];lines=['# Frozen transfer costs','',data['overlap'],'',
        '| Quantity | '+ ' | '.join(ARMS)+' |','|---|---:|---:|']
    for key in ('episodes','rows','formula_calls','fresh_native_pln_calls','epochs','frame_serialized_bytes'):
        lines.append('| '+key+' | '+' | '.join(str(g[key]) for g in groups)+' |')
    lines.append('| Total episode seconds | '+' | '.join(f"{g['elapsed_ns']/1e9:.6f}" for g in groups)+' |')
    lines+=['','## Payload quantities','','StringValue content is logical payload, not RSS; readback bytes are derived from the fully validated native wire grammar. The native arm retains the existing accounting work; scan costs are reported separately.','','| Quantity | '+' | '.join(ARMS)+' |','|---|---:|---:|']
    for k in sorted(set().union(*(g['payload_counters'] for g in groups))):
        lines.append('| '+k+' | '+' | '.join(str(g['payload_counters'].get(k,0)) for g in groups)+' |')
    for field,label in (('coarse_disjoint_ns','Disjoint coarse phases'),('nested_timers_ns','Nested detailed timers')):
        lines+=['','## '+label,'','| Seconds | '+' | '.join(ARMS)+' |','|---|---:|---:|']
        for k in sorted(set().union(*(g[field] for g in groups))):
            lines.append('| '+k+' | '+' | '.join(f"{g[field].get(k,0)/1e9:.6f}" for g in groups)+' |')
    lines+=['',data['scope'],'','Unmeasured: '+', '.join(data['unmeasured'])+'.',
      '', 'Every changed binding remains a cold view load. Sealed bytes staged are not RSS. Logical time does not advance with wall-clock computation.']
    return '\n'.join(lines)+'\n'


def paired(report):
    rows=[]
    for p in dict.fromkeys(r['parent'] for r in report['results']):
        values={r['arm']:r['elapsed_ns'] for r in report['results'] if r['parent']==p}
        rows.append(dict(parent=p,elapsed_ns=values,native_minus_scan_ns=values[ARMS[1]]-values[ARMS[0]]))
    return dict(pairs=rows,interpretation='Twelve fixed new parent structures, two arms, one counterbalanced pass. No independent-population, optimality or pressure advantage claim.')

def render_pairs(data):
    lines=['# Paired wall times','',data['interpretation'],'','| Parent | Scan seconds | Native seconds | Native minus scan |','|---|---:|---:|---:|']
    for r in data['pairs']:lines.append('| '+r['parent']+' | '+' | '.join(f'{v/1e9:.6f}' for v in (r['elapsed_ns'][ARMS[0]],r['elapsed_ns'][ARMS[1]],r['native_minus_scan_ns']))+' |')
    return '\n'.join(lines)+'\n'
