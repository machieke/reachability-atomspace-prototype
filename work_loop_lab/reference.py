"""Independent structural/receipt expectations; does not import the consumer."""
from experimental_online_pln.agenda import Snapshot,enumerate_work,wire,Limits
from reachability.model import Status
from .cases import configuration


def require(test,why):
    if not test:raise AssertionError(why)


def check_step(row,attempts):
    snapshot=Snapshot.from_records(row['public_records']);selected=row['selected'];v=row['view']
    require(snapshot.binding==row['public_binding'],'public binding')
    require(v['observed']['goal']==wire(snapshot.goal),'coherent observed goal')
    require(v['observed']['lifecycle']==wire(snapshot.lifecycle),'coherent lifecycle')
    require(v['observed']['operation']==wire(snapshot.operation),'coherent operation')
    if selected is None:return
    frontier=enumerate_work(snapshot,Limits(**configuration()['limits']))
    require(frontier.complete and selected in wire(frontier.candidates),'selected public membership')
    key=(selected['logical_id'],selected['basis']);require(key not in attempts,'duplicate basis retry');attempts.add(key)
    kind=selected['kind'];target=selected['target'];result=row['result'];origin=row['choice']['selected_origin']
    if origin=='exact-work-route':
        require(v['complete'],'partial graph executed')
        mapped=[n for n in v['nodes'] if n['id'] in row['choice']['selected_nodes']]
        require(bool(mapped),'missing mapped route')
        for node in mapped:
            producer=node['producer'];record=producer['record']
            require(not node['materialized_result_ids'],'repeated formula as repair')
            if kind=='request':
                require(record in wire(snapshot.probes) and record['probe_id']==target and record['opportunity']==selected['premise_ids'][0],'probe identity')
                require(selected['cost']==record['cost']==selected['acquisition_cost'],'probe cost')
            else:
                registry=wire(snapshot.rules if kind=='deduction' else snapshot.models)
                require(record in registry and record['rule_id' if kind=='deduction' else 'model_id']==target,'exact producer revision')
                require(selected['premise_ids']==node['ordered_premises'] and not node['missing_slots'],'complete ordered tuple')
                require(len([e for e in v['edges'] if e['source']==node['id'] and e['type']=='AND_PREREQUISITE'])==len(selected['premise_ids']),'AND slots')
    elif origin=='received-report-adapter':require(kind=='adopt' and target in row['choice']['pending_reports'],'raw report adoption mapping')
    elif origin=='fresh-live-authorization':
        require(kind in ('reserve','dispatch') and v['complete'],'fresh authorization channel')
        require(v['A']['numerical_status']==v['B']['numerical_status']=='PASS','B bypassed live A')
        require(not row['choice']['pending_reports'],'pending evidence avoided')
        current={b.belief_revision_id for view in snapshot.numerical for b in view.current}
        for n in v['nodes']:
            if n['kind']=='operation' and n['producer']['kind'] in ('deduction','revision'):
                require(bool(current&set(n['materialized_result_ids'])),'unexamined review producer')
    else:require(origin=='existing-operational-control' and snapshot.dispatch is not None,'unknown operation adapter')
    if kind in ('adopt','deduction','revision'):
        require(row['before_environment']['outstanding']==row['before']['outstanding'],'numerical work manufactured relief')
        require(row['before_environment']['effects']==row['before']['effects'],'numerical executor effect')
        if result['status']=='PASS':
            require(result['pre_status']==result['post_status']=='PASS' and result['commit']['status']=='PASS','uncertified numeric result')
            require(result['transition']['premise_revision_ids']==selected['premise_ids'],'committed tuple differs')
            if kind=='deduction':require(len(result['post']['joint_witness'])==8,'missing joint witness')
    if not row['revalidation']['member']:require(result['status'] in ('STALE','FAIL'),'absent current candidate executed')
    if not row['after']['product_observed']:require(row['after']['outstanding']==10,'forecast or acknowledgment became observed relief')
    require(row['after']['hard_forecast']=='UNKNOWN','numeric forecast became hard fact')


def check_episode(parent,rows,result,continuation=None):
    attempts=set()
    for row in rows:check_step(row,attempts)
    require(rows[-1]['selected'] is None and rows[-1]['stop']==result['stop'],'missing explained terminal view')
    if continuation is not None:return
    selected=[r for r in rows if r['selected']]
    kinds=[r['selected']['kind'] for r in selected];last=rows[-1]['view']
    if parent in ('positive','shared'):
        require((result['stage'],result['outstanding'],result['effects'],result['stop'])==('BUILT',0,1,'OBSERVED_COMPLETION'),'positive observed completion')
        losses=[r['after']['outstanding'] for r in selected if r['selected']['target']=='health'];require(losses==[10,10,0],'health durability')
        if parent=='positive':
            require('request' in kinds and 'adopt' in kinds and 'deduction' in kinds,'missing selected observation/adoption/inference')
            require(len(rows[0]['choice']['eligible'])>=2,'no nontrivial initial live choice')
        else:
            require(kinds.count('revision')==1,'shared revision counted twice')
            groups={o['obligation_id']:o for o in rows[0]['view']['obligations']}
            require(groups['method-assessment']['routes']==groups['method-review']['routes'],'shared operation references')
    elif parent=='blocked':
        require(result['effects']==0 and result['outstanding']==10 and result['stop']=='TASK_RESOLVED_LIVE_BLOCKED','lost all-current block')
        require(kinds.count('revision')==1 and (last['A']['numerical_status'],last['B']['numerical_status'])==('UNKNOWN','PASS'),'weak-parent result')
        require(any(r['belief']['proposal']['support']['truth']['confidence']==.2 for r in last['A']['records'] if r['current']),'weak parent disappeared')
    elif parent=='unavailable':require(result['effects']==0 and result['outstanding']==10 and kinds==['request'] and selected[0]['result']['status']=='UNKNOWN','unavailable source fabricated')
    elif parent=='freshness':
        require(any(r['result']['status']=='STALE' and r['selected']['target']=='r-estimate' for r in selected),'old request not rejected')
        require(result['effects']==0 and last['B']['numerical_status']!='PASS','old role rebound to new rule')
        require(any(r['result']['status']=='PASS' and r['selected']['target']=='r-estimate' for r in selected),'fresh revision not rediscovered')
    elif parent=='adverse':
        require(result['effects']==0 and (last['A']['numerical_status'],last['B']['numerical_status'])==('FAIL','FAIL'),'adverse investigation omitted')
        require(any(b['category']=='OBJECTION_REQUIRES_REVIEW' for b in last['global_blockers']),'hidden objection')
        require(kinds==['deduction'],'unexpected adverse actions')
    require(result['reconstruction']['authority_equal'],'authority reconstruction')
    if result['mode']=='native':require(result['reconstruction']['projection_equal'],'native reconstruction')
