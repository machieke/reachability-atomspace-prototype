"""Local compute-credit bounds. No authority, probabilities or outcome labels."""
PREPARATION_READS=6


def offers(jobs,resident,pins,caps,remaining,tuple_remaining):
    result=[]
    for job in sorted((j for j in jobs if j['kind']=='join'),key=lambda j:(j['order'],j['id'])):
        producer_read=int(job['target'] not in resident)
        join_queries=6+producer_read;total=join_queries+PREPARATION_READS
        reason=('QUERY_RESERVATION' if remaining<total else
                'TUPLE_BUDGET' if tuple_remaining<1 else
                'RESPONSE_CAPACITY' if caps.response_records<1 or caps.response_bytes<1 else
                'JOINT_CAPACITY' if caps.joint_records<5 or caps.joint_slots<5 or caps.joint_bytes<1 else
                'BUNDLE_CAPACITY' if len(pins)+7>caps.active or caps.active_bytes<1 else
                'CANDIDATE_CAPACITY' if caps.candidates<1 or caps.candidate_bytes<1 else 'AFFORDABLE_ATTEMPT')
        result.append(dict(job_id=job['id'],order=job['order'],producer=job['target'],producer_read=producer_read,
                           join_queries=join_queries,prepare_queries=PREPARATION_READS,total=total,reason=reason,
                           affordable=reason=='AFFORDABLE_ATTEMPT',response_and_tuple_sizes='UNKNOWN_UNTIL_NATIVE_RESPONSES'))
    return result


def first_affordable(values):return next((v for v in values if v['affordable']),None)
