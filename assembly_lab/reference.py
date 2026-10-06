"""Independent trace-prefix audit of FIFO service and native-query credits.

No import of the runtime affordability function. This audit uses only recorded
admissions, pending jobs, completed queries and public limits, not world outcomes.
"""
from collections import Counter


class ServiceLedger:
    def __init__(self):
        self.binding=None;self.total=0;self.counts=Counter()
    def audit(self,d,caps,search,limits,native_events):
        if self.binding!=d['binding']:
            self.binding=d['binding'];self.resident=set();self.jobs={};self.attempted=set();self.view_queries=0
        used=0;slot=None;hold=0;last_offers=[];pins=set();visits=0;last_start=None;active=None;join_start=None;prep_start=None
        native=[e['result'] for e in native_events if e['kind']=='query'];read_index=0
        def remaining():return min(search.queries-used,search.queries*(limits.selections+1)-self.total,4096-self.view_queries)
        for e in d['events']:
            kind=e['kind']
            if kind=='admit':self.resident.add(e['key'])
            elif kind=='evict':self.resident.remove(e['key'])
            elif kind=='control_end':pins=set(e['pins']);self.counts['control_queries']+=e['queries']
            elif kind=='job_known':
                job=e['job']
                if job['id'] in self.jobs or job['id'] in self.attempted:raise ValueError('duplicate unchanged job')
                if job['known_query']!=self.total:raise ValueError('job age differs')
                self.jobs[job['id']]=job
            elif kind=='assembly_offers':
                expected=[]
                for job in sorted(self.jobs.values(),key=lambda j:(j['order'],j['id'])):
                    if job['kind']!='join':continue
                    read=int(job['target'] not in self.resident);cost=12+read
                    why=('QUERY_RESERVATION' if remaining()<cost else 'TUPLE_BUDGET' if limits.tuple_visits-visits<1 else
                         'RESPONSE_CAPACITY' if min(caps.response_records,caps.response_bytes)<1 else
                         'JOINT_CAPACITY' if caps.joint_records<5 or caps.joint_slots<5 or caps.joint_bytes<1 else
                         'BUNDLE_CAPACITY' if len(pins)+7>caps.active or caps.active_bytes<1 else
                         'CANDIDATE_CAPACITY' if min(caps.candidates,caps.candidate_bytes)<1 else 'AFFORDABLE_ATTEMPT')
                    expected.append(dict(job_id=job['id'],order=job['order'],producer=job['target'],producer_read=read,
                        join_queries=6+read,prepare_queries=6,total=cost,reason=why,affordable=why=='AFFORDABLE_ATTEMPT',
                        response_and_tuple_sizes='UNKNOWN_UNTIL_NATIVE_RESPONSES'))
                if expected!=e['offers'] or e['remaining']!=remaining() or e['used_slot']!=(slot is not None):raise ValueError('reservation offer differs from prefix')
                last_offers=expected;self.counts['affordability_scans']+=1
                self.counts['unaffordable_offer_observations']+=sum(not v['affordable'] for v in expected)
            elif kind=='assembly_protected':
                if d['contract']!='assembly' or slot is not None:raise ValueError('extra protected opportunity')
                expected=next((o for o in last_offers if o['affordable']),None)
                if expected is None or e['service']!=dict(expected,state='PROTECTED',protected_at=used):raise ValueError('not oldest affordable opportunity')
                slot=dict(e['service']);hold=6;self.counts['protected']+=1
            elif kind=='expand':
                job=e['job']
                if self.jobs.pop(job['id'],None)!=job or job['id'] in self.attempted:raise ValueError('unknown or repeated expansion')
                self.attempted.add(job['id']);active=job
                if slot and 'served' not in slot and job['id']!=slot['job_id']:raise ValueError('inspection consumed protected slot')
            elif kind=='query_start':
                if e['remaining']!=remaining() or e['hold']!=hold:raise ValueError('query credit ledger differs')
                if d['contract']=='assembly' and e['phase']=='inspection' and hold and remaining()<=hold:raise ValueError('inspection spent preparation credit')
                last_start=e
            elif kind=='query_consumed':
                if last_start is None or read_index>=len(native):raise ValueError('unlogged native work')
                query=native[read_index];read_index+=1;used+=1;self.total+=1;self.view_queries+=1
                if query['request']['kind']!=last_start['kind_name'] or list(query['ids'])!=list(e['ids']):raise ValueError('query receipt/phase differs')
                if used>search.queries or self.view_queries>4096 or self.total>search.queries*(limits.selections+1):raise ValueError('query overspend')
                if e['at_query']!=used or e['at_episode_query']!=self.total:raise ValueError('query timestamp differs')
                self.counts[last_start['phase']+'_queries']+=1;last_start=None
            elif kind=='join_begin':
                if active is None or active['kind']!='join' or active['target']!=e['producer']:raise ValueError('join job differs')
                if e['known_query']!=active['known_query'] or e['wait_queries']!=self.total-active['known_query']:raise ValueError('pending join wait differs')
                if set(e['resident'])!=self.resident or set(e['pins'])!=pins:raise ValueError('join retention differs')
                join_start=used
            elif kind=='join_end':
                if join_start is None or e['queries']!=used-join_start:raise ValueError('join accounting differs')
                visits+=e['tuple_visits'];self.counts['join_attempts']+=1
                if visits>limits.tuple_visits:raise ValueError('tuple overspend')
                if e['phase']=='assembly':
                    if slot is None or used-join_start>slot['join_queries']:raise ValueError('assembly query overspend')
                    self.counts['protected_'+e['reason']]+=1
                join_start=None
            elif kind=='assembly_served':
                if slot is None or e['service']['queries']>slot['join_queries']:raise ValueError('served without reserved work')
                hold=6 if e['eligible'] else 0
                if e['service']['prepare_hold']!=hold:raise ValueError('negative attempt failed to release credit')
                slot['served']=True;self.counts['served']+=1
            elif kind=='preparation_begin':
                if e['held']!=hold or e['remaining']!=remaining():raise ValueError('preparation credit differs')
                if set(e['missing'])!={i for i in e['needs'] if i not in self.resident}:raise ValueError('uncounted rematerialization')
                prep_start=(used,hold);hold=0
            elif kind=='pin_bundle':pins.update(e['keys'])
            elif kind=='preparation_end':
                if prep_start is None or e['queries']!=used-prep_start[0]:raise ValueError('preparation queries differ')
                if prep_start[1] and e['queries']>prep_start[1]:raise ValueError('preparation exceeded reserved bound')
                if set(e['pins'])!=pins:raise ValueError('selected pins differ')
                self.counts['preparation_queries']+=0;prep_start=None
            elif kind=='service_end':
                if e['unused_prepare_credit']!=hold or e['remaining']!=remaining():raise ValueError('final credit differs')
                hold=0
        if used!=d['native_queries'] or self.total!=d['episode_queries'] or read_index!=len(native) or visits!=d['tuple_visits']:raise ValueError('terminal service work differs')
        if self.jobs!={j['id']:j for j in d['pending_jobs']}:raise ValueError('pending work differs')
        if set(d['pins'])!=pins:raise ValueError('final pins differ')
        self.counts['audited_tranches']+=1
