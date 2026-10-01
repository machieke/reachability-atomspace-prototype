"""Explicit bounded development schedules and immutable delivery-order controls."""
import argparse
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from reachability.trace_protocol import DeploymentInitial
from .run_dispatch_races import ROOT, CORPUS, reduce_case, semantic_result, source_paths, write
from .shrink_replay import digest_file


def event(event_id, kind, **arguments):
    return dict(schema='dispatch-race-event/v1',event_id=event_id,kind=kind,arguments=arguments)


def scenarios():
    e=event
    def op(name,kind,attempt='a',**args):
        return e(name,kind,attempt_id=attempt,**args)
    ready=[e('t','fact',name='tested',valid_until=None),e('c','fact',name='credential',valid_until=None),
           e('f','forecast',strength=.8,confidence=.8,valid_until=None),op('a','attempt'),op('r','reserve')]
    prepare=op('p','prepare')
    revoke=e('v','revoke',evidence_id='c')
    expiry=e('x','tick',time=10)
    send=op('s','dispatch',fault='none')
    lost=op('s','dispatch',fault='lost_reply')
    queued=op('s','dispatch',fault='queued')
    arrive=e('arrive','arrive',request_event='s')
    deliver=e('ack','deliver',receipt_event='arrive')
    release=op('release','release')
    reconcile=op('query','reconcile')
    ack=e('ack','deliver',receipt_event='s')
    retry=op('retry','dispatch',fault='none')
    other=[op('b','attempt','b'),op('rb','reserve','b')]
    restore=e('restore','fact',name='credential',valid_until=None)
    cases=[]
    def add(label,tail,*,prefix=ready,pair=(),checkpoint='before_send',mutant=None):
        cases.append(deepcopy(dict(schema='dispatch-race-case/v1',case_id=f'dr{len(cases)+1:02}',
            parent_instance_id='dispatch-race-parent-0',split='development',control=label,
            public=asdict(DeploymentInitial()),events=[*prefix,*tail],
            schedule=dict(schema='dispatch-race-schedule/v1',pair=list(pair),checkpoint=checkpoint),mutant=mutant)))
    add('revoke-before-final-send',[e('noise','restart'),prepare,revoke,send],mutant='cached-send-gate')
    add('revoke-before-preparation-then-restore',[revoke,send,restore,retry])
    add('lease-expired-before-final-send',[prepare,expiry,send],mutant='expire-uncertain')
    add('lease-expired-before-preparation',[expiry,send])
    for checkpoint in ('before_send','before_ack'):
        for contender in (revoke,expiry):
            add(checkpoint+'-blocks-'+contender['kind'],[send,contender,release],pair=('s',contender['event_id']),checkpoint=checkpoint)
    add('lost-ack-after-expiry',[lost,expiry,ack,*other,reconcile,release,op('again','reserve','b')])
    add('delayed-request-after-expiry',[queued,expiry,*other,arrive,deliver,reconcile,release,op('again','reserve','b')])
    add('release-fences-delayed-arrival',[queued,expiry,release,arrive,deliver,*other,op('sb','dispatch','b',fault='none')])
    add('old-ack-after-fence',[lost,release,ack,retry])
    add('duplicate-delivery-and-arrival',[queued,arrive,deliver,e('arrive2','arrive',request_event='s'),
        e('ack2','deliver',receipt_event='arrive2'),e('ack3','deliver',receipt_event='arrive'),retry])
    add('absent-query-does-not-release',[queued,reconcile,expiry,*other,arrive,op('query2','reconcile'),deliver])
    add('same-wrapper-inbox-across-both-journal-reopens',[queued,e('reopen1','restart'),arrive,e('reopen2','restart'),deliver])
    add('missing-transport-references',[arrive,ack,dict(deliver,event_id='ack-arrive')])
    add('unsent-failure-has-no-deliverable-request',[op('s','dispatch',fault='before_effect'),arrive,ack,reconcile,release])
    add('historical-success-retry-skips-send-checkpoint',[send,retry,revoke],pair=('retry','v'))
    add('early-rejected-dispatch-skips-checkpoint',[revoke,send,expiry],pair=('s','x'))
    add('queued-send-before-revocation-still-arrives',[queued,revoke,arrive,deliver,release])
    add('lost-ack-query-before-delivery',[lost,reconcile,ack,retry])
    add('old-request-fenced-while-another-is-accepted',[lost,release,*other,op('sb','dispatch','b',fault='none'),
        ack,e('old-arrive','arrive',request_event='s'),e('old-ack','deliver',receipt_event='old-arrive')])
    add('prepared-restored-gate-control',[prepare,revoke,restore,send,release])
    add('no-intent-and-no-attempt-race',[send,expiry],prefix=[],pair=('s','x'))
    return cases


def generate(output):
    cases=scenarios()
    output.mkdir(parents=True)
    for case in cases:
        for folder,value in (('public',case['public']),('evaluator',{k:v for k,v in case.items() if k!='public'})):
            (CORPUS/folder).mkdir(parents=True,exist_ok=True)
            write(CORPUS/folder/(case['case_id']+'.json'),value)
    (CORPUS/'mutations').mkdir(parents=True,exist_ok=True)
    for case in cases:
        if case['mutant']:
            result=reduce_case(case,case['mutant'],output/case['mutant'])
            if not result['one_minimal']:
                raise ValueError('unproven minimality: '+case['mutant']+' '+result['status'])
            write(CORPUS/'mutations'/(case['mutant']+'.json'),dict(case=case,result=semantic_result(result)))
            print(case['mutant'],len(case['events']),'->',len(result['reduced_events']),flush=True)
    fixtures=sorted(str(p.relative_to(ROOT)) for folder in ('public','evaluator','mutations') for p in (CORPUS/folder).glob('*.json'))
    write(CORPUS/'manifest.json',dict(schema='dispatch-race-corpus/v1',split='development',parent_instance_id='dispatch-race-parent-0',
        case_count=len(cases),event_prefixes=sum(len(c['events']) for c in cases),family_complete_fixtures=0,
        fixture_files={p:digest_file(ROOT/p) for p in fixtures},source_files={p:digest_file(ROOT/p) for p in source_paths()},
        scope='final-send lock and delayed-request/receipt ordering; local simulator; same-wrapper inbox recovery; diagnostic mutations only'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts'/'dispatch-race-generation')
    generate(parser.parse_args().output)
