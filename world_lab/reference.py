"""Independent finite physical recurrence and metric checks; no world import."""


def physical_trace(spec,accepted,horizon,goal):
    # Mathematical recurrence over immutable event declarations and actual commands.
    installed=None;health=False;state='absent';streak=0;rows=[]
    for tick in range(horizon+1):
        active=[r for r in accepted if r['accepted_at']<tick]
        if state=='absent' and active:state='pending'
        for r in sorted(active,key=lambda r:r['request']['request_id']):
            if r['accepted_at']+spec['delay']==tick:
                if spec['effect']=='failed':state='failed'
                else:installed=spec['installed'];health=True;state='completed'
        for event in spec['events']:
            if event['tick']==tick:health=event['healthy']
        streak=streak+1 if installed==goal['product'] and health else 0
        rows.append(dict(time=tick,installed=installed,healthy=health,operation=state,healthy_streak=streak,
                         goal_deficit=0 if streak>=goal['consecutive_healthy_ticks'] else goal['deficit_units']))
    return rows


def require(ok,why):
    if not ok:raise AssertionError(why)


def public_boundary(snapshot,initial_contracts):
    require(snapshot.contracts==initial_contracts,'hidden or changed authority input contract')
    for event in snapshot.received:
        kind=event['kind']
        if kind=='numeric_report':require(set(event)=={'kind','report'},'unexpected report input')
        elif kind=='acquisition':
            require(set(event)=={'kind','descriptor','response'},'hidden acquisition input')
            response=event['response']
            require(set(response) in ({'status','numeric'},{'status','events'},{'status','detail'}),'hidden truth in response')
        else:require(kind in ('attempt','fact','tick','account','reserve','cover','dispatch','reconcile','observation','sample','complete','revoke') and set(event)=={'kind','arguments','outcome'},'hidden truth input event')


def metrics(ticks,measurements,duration=1):
    success=[r['time'] for r in ticks if r['physical_sample']['goal_deficit']==0]
    completion=[r['time'] for r in ticks if r['authority_after']['stage']=='BUILT']
    failures=[m['time'] for m in measurements if m['sample'] and m['sample']['channel']=='health' and m['sample']['status']=='PASS' and m['sample']['value'] is False]
    healthy_to_bad=[r['time'] for i,r in enumerate(ticks) if i and ticks[i-1]['physical_sample']['healthy'] and not r['physical_sample']['healthy']]
    recognized=[]
    for tick in healthy_to_bad:
        later=[t for t in failures if t>=tick];recognized.append(dict(change=tick,first_adverse_sample=min(later) if later else None,lag=min(later)-tick if later else None))
    return dict(first_physical_goal=min(success) if success else None,first_observed_completion=min(completion) if completion else None,
      J_world=sum(r['physical_sample']['goal_deficit']*duration for r in ticks),physically_unsatisfied_ticks=sum(r['physical_sample']['goal_deficit']>0 for r in ticks),
      J_certified=sum(r['authority_after']['outstanding']*duration for r in ticks),recognition=recognized,
      final_physical_deficit=ticks[-1]['physical_sample']['goal_deficit'],final_observed_loss=ticks[-1]['authority_after']['outstanding'],
      achievement_to_completion_lag=min(completion)-min(success) if success and completion else None,
      historical_completion=bool(completion),final_observed_failure=ticks[-1]['authority_after']['goal_label']=='OBSERVED_FAILURE')


def classify(tick):
    # Reasons are observational relationships, not accusations of contract failure.
    physical=tick['physical_sample']['goal_deficit'];observed=tick['authority_after']['outstanding']
    reasons=[]
    if physical!=observed:
        if any(m['response']['status']=='UNKNOWN' for m in tick['measurements']):reasons.append('OBSERVATION_UNAVAILABLE')
        if any(s.get('result',{}).get('status')=='FAIL' for s in tick['steps_summary']):reasons.append('REJECTED_REPORT_OR_OPERATION')
        if tick['authority_after']['goal_label']=='UNKNOWN':reasons.append('MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL')
        reasons.append('DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES')
    if tick['authority_before_clock']['outstanding']!=physical:
        reasons.append('UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED')
    return reasons


def validate(spec,cfg,ticks,private,result,core=True):
    expected=physical_trace(spec,private['state']['accepted'],cfg['horizon_inclusive'],cfg['physical_goal'])
    require([t['physical_sample'] for t in ticks]==expected,'independent physical trajectory')
    require(private['state']['history']==expected,'physical history independent of observer')
    require(len(ticks)==cfg['horizon_inclusive']+1,'full horizon despite consumer stop')
    for tick in ticks:
        require(tick['authority_guard_before']==tick['authority_guard_after'],'hidden transition wrote authority')
        require(tick['mismatch_reasons']==classify(tick),'mismatch classification')
    for measurement in private['measurements']:
        require(measurement['physical_before']==measurement['physical_after'],'observation created physical state')
        sample=measurement['sample']
        if sample:
            t=sample['sample_time'];require(t==measurement['time'],'instantaneous sample timestamp')
            if t in spec['outages'].get(sample['channel'],[]):require(sample['status']=='UNKNOWN' and sample['value'] is None,'outage fabricated truth')
            else:
                value=expected[t]['installed' if sample['channel']=='product' else 'healthy'];require(sample['status']=='PASS' and sample['value']==value,'truthful physical sample')
            response=measurement['response'];probe=measurement['probe']
            if sample['status']=='UNKNOWN':require(response==dict(status='UNKNOWN',detail='observation channel unavailable'),'outage relabeled as evidence')
            elif sample['channel']=='health':
                if expected[t]['installed']==probe['target']:require(response==dict(status='PASS',events=[['sample',dict(healthy=sample['value'])]]),'adverse health response rewritten')
                else:require(response==dict(status='UNKNOWN',detail='measurement target is not installed'),'health target mismatch')
            elif sample['value'] is None:require(response==dict(status='UNKNOWN',detail='no installed artifact observed'),'missing artifact fabricated')
            elif sample['value']!=probe['target']:require(response==dict(status='PASS',events=[['observation',dict(attempt_id='attempt',product_id=sample['value'],milestone='exact_product_observed')]]),'wrong artifact substituted')
            else:require(response==dict(status='PASS',events=[['fact',dict(name='product',valid_until=None)],['observation',dict(attempt_id='attempt',product_id=sample['value'],milestone='completion_observed')],['observation',dict(attempt_id='attempt',product_id=sample['value'],milestone='exact_product_observed')]]),'correct artifact observation mapping')
    require(result['metrics']==metrics(ticks,private['measurements'],cfg['tick_duration']),'separate physical metrics')
    if core:
        e=spec['expected'];m=result['metrics'];require((m['first_physical_goal'],m['first_observed_completion'],m['J_world'],m['final_physical_deficit'])==(e['first_physical'],e['first_completion'],e['J_world'],e['final_physical']),'predeclared finite outcome table')
    require(result['effects']==len(private['state']['accepted']),'one scheduled effect per actual unique executor acceptance')
