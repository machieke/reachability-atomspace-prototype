"""Additional offline diagnostic replay, capacity inventory and sensitivity report."""
import json
from pathlib import Path
from experimental_goal_pln.agenda import Agenda
from experimental_online_pln.agenda import Limits, Snapshot, wire
from goal_pln_lab.compare import replay_pair, check_prefixes


def normalized(rows):
    result=[]
    for row in rows:
        c=row['selected']
        if c is None:continue
        view=Snapshot.from_records(row['public_records'])
        target=c['target']
        if c['kind']=='deduction':
            rule=next(r for r in view.rules if r.rule_id==target)
            target=wire(rule.deduction)
        elif c['kind']=='adopt':
            target=wire(next(r.evidence.content for r in view.reports if r.evidence.evidence_id==target))
        elif c['kind']=='request':
            target=wire(next((p.report_type,p.target) for p in view.probes if p.probe_id==target))
        result.append((c['kind'],target,row['result']['status'],row['after']['outstanding'],row['external_loss']))
    return result


def check(root):
    root=Path(root);report=json.loads((root/'report.json').read_text())
    diagnostics=[];max_estimates=max_rules=max_index_entries=0;scope_limits=fallbacks=0
    for r in report['results']:
        folder=root/f"{r['mode']}-{r['case_id']}-w{r['budget']}-{r['arm']}"
        for line in (folder/'trace.jsonl').read_text().splitlines():
            row=json.loads(line);view=Snapshot.from_records(row['public_records'])
            max_estimates=max(max_estimates,sum(len(v.current) for v in view.numerical));max_rules=max(max_rules,len(view.rules))
            max_index_entries=max(max_index_entries,row['discovery'].get('index_entries',0))
            scope_limits+=int(row['discovery'].get('discovery_complete') is False)
            fallbacks+=int(row['discovery'].get('fallback') is not None)
    for d in report['diagnostics']:
        folder=root/'diagnostics'/f"diagnostic-{d['transformation']}-{d['case_id']}-w{d['budget']}-{d['arm']}"
        rows=[json.loads(s) for s in (folder/'trace.jsonl').read_text().splitlines()]
        agenda=Agenda(d['arm'],Limits(work=d['budget']))
        for row in rows:
            view=Snapshot.from_records(row['public_records'])
            replay_pair(view,agenda,agenda.limits)
            frontier,selected=agenda.choose(view)
            if wire(selected)!=row['selected'] or wire(frontier.candidates)!=row['frontier']['candidates']:
                raise ValueError('diagnostic replay mismatch')
        check_prefixes(rows,d)
        base=next(r for r in report['results'] if (r['mode'],r['case_id'],r['budget'],r['arm'])==('finite',d['case_id'],d['budget'],d['arm']))
        base_rows=[json.loads(s) for s in (root/f"finite-{d['case_id']}-w{d['budget']}-{d['arm']}"/'trace.jsonl').read_text().splitlines()]
        old,new=normalized(base_rows),normalized(rows)
        diagnostics.append(dict(case_id=d['case_id'],transformation=d['transformation'],arm=d['arm'],budget=d['budget'],
            normalized_sequence_equal=old==new,first_divergence=next((i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b),None),
            certified_loss_pair=[base['outstanding'],d['outstanding']],external_loss_pair=[base['external_loss'],d['external_loss']],
            work_pair=[base['work'],d['work']],operations=new))
    return dict(status='PASS',diagnostic_executions=len(diagnostics),diagnostics=diagnostics,
        primary_capacity=dict(max_current_estimates=max_estimates,estimate_cap=32,max_rules=max_rules,rule_cap=16,
                              max_index_entries=max_index_entries,incomplete_dependency_or_discovery_scopes=scope_limits,
                              declared_fallback_rows=fallbacks),
        limitation='Identifier tie-breaking can change operation order. These 24 siblings are not independent parents.')


if __name__=='__main__':
    import sys
    print(json.dumps(check(sys.argv[1]),indent=2))
