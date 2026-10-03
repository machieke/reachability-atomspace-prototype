"""Descriptive aggregation of the sealed recall comparison; no controller inputs."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys


def analyze(path):
    path=Path(path);report=json.loads((path/'report.json').read_text());groups={};decisions={};maxima=Counter();query_kinds=Counter()
    for result in report['results']:
        key=result['mode']+'/'+result['arm']
        group=groups.setdefault(key,dict(executions=0,certified_zero=0,external_zero=0,work=0,selections=0,tuple_visits=0,
            formula_calls=0,epochs=0,elapsed_ns=0,costs_ns=Counter(),discovery_costs_ns=Counter(),recall_costs=Counter(),statuses=Counter(),fallback_reasons=Counter(),stops=Counter(),query_counts=Counter(),query_time_ns_by_position=Counter(),native_counts_sum=Counter(),outcomes={}))
        group['executions']+=1
        group['certified_zero']+=result['outstanding']==0;group['external_zero']+=result['external_loss']==0
        for name in ('work','selections','tuple_visits','elapsed_ns'):group[name]+=result[name]
        group['formula_calls']+=len(result['runtime_calls']);group['epochs']+=result.get('native_epochs',0)
        for name in ('costs_ns','discovery_costs_ns','recall_costs'):group[name].update(result.get(name,{}))
        group['stops'][result['stop']]+=1
        casekey=result['case_id']+'/w'+str(result['budget'])
        group['outcomes'][casekey]=dict(certified_loss=result['outstanding'],external_loss=result['external_loss'],effects=result['effects'],stop=result['stop'])
        directory=path/f"{result['mode']}-{result['case_id']}-w{result['budget']}-{result['arm']}"
        rows=[json.loads(line) for line in (directory/'trace.jsonl').read_text().splitlines()]
        compact=[]
        for row in rows:
            if row['discovery'].get('fallback'):group['fallback_reasons'][row['discovery']['fallback']]+=1
            c=row['selected']
            if c:
                group['statuses'][row['result']['status']]+=1
                compact.append(dict(work=row['work'],kind=c['kind'],target=c['target'],premise_ids=c['premise_ids'],status=row['result']['status'],external_loss=row['external_loss'],certified_loss=row['after']['outstanding'],decision=row['after']['decision'],scope=row['discovery'].get('scope')))
            at_epoch_start=False
            for event in row['native_events']:
                if event['kind']=='open_view':
                    counts=event['receipt']['counts'];group['native_counts_sum'].update(counts)
                    for name,value in counts.items():maxima[name]=max(maxima[name],value)
                    at_epoch_start=True
                if event['kind']=='query':
                    q=event['result'];kind=q['request']['kind'];group['query_counts'][kind]+=1;query_kinds[kind]+=1
                    group['query_time_ns_by_position']['first_after_load' if at_epoch_start else 'subsequent_same_view']+=q['elapsed_ns']
                    at_epoch_start=False
        decisions[key+'/'+casekey]=compact
    classification={}
    for mode in ('finite','native'):
        left=groups[mode+'/Goal-scan'];right=groups[mode+'/Goal-native']
        classification[mode]=dict(terminal_outcomes_equal=left['outcomes']==right['outcomes'],native_minus_scan_tuple_visits=right['tuple_visits']-left['tuple_visits'],
            native_selection_time_ratio=right['discovery_costs_ns']['selection_inclusive_ns']/left['discovery_costs_ns']['selection_inclusive_ns'],
            native_total_time_ratio=right['elapsed_ns']/left['elapsed_ns'])
    return dict(schema='native-recall-descriptive-analysis/v1',revision=report['sources']['revision'],groups=groups,maxima=dict(maxima),native_query_kinds=dict(query_kinds),classification=classification,decision_sequences=decisions,
        limits='One ordered pass with concurrent regression load; nested inclusive timings are not additive; no uncertainty estimate, speed or scale claim. RSS, isolated native compute, physical sensing latency and isolated SQL/fsync latency are unmeasured.')


if __name__=='__main__':
    result=analyze(sys.argv[1]);text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if len(sys.argv)>2:Path(sys.argv[2]).write_text(text)
    else:print(text,end='')
