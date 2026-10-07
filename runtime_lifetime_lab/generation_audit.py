"""Recorded generation structure checks; cryptographic preparation ran in cohort."""
import json
from hashlib import sha256
from pathlib import Path
from reachability.trace_protocol import canonical
from work_loop_lab.audit import equal
from experimental_runtime_lifetime.generation import POLICY


def check_generation(path,result,events):
    attempts=json.loads((path/'runtime-attempts.json').read_text());equal(len(attempts),1,'one generation attempt in ordinary core');equal(attempts[0]['costs'],result['runtime_costs'],'all attempt costs retained')
    runtime=json.loads((path/'runtime-events.json').read_text());equal(attempts[0]['events'],runtime,'all generation events retained');prepared=[e for e in runtime if e['kind']=='prepared'];launches=[e for e in runtime if e['kind']=='launch']
    equal(len(prepared),1,'one prepared generation per episode');p=prepared[0];d=p['descriptor'];equal(d,result['runtime_generation'],'generation descriptor binding')
    payload=dict(d);identity=payload.pop('generation_id');equal(sha256(canonical(payload).encode()).hexdigest(),identity,'generation identity digest');equal(d['schema'],POLICY,'generation policy')
    # Original exact build receipts remain the source of covered artifact digests.
    root=path.parent;base=json.loads((root/'adapter-build.json').read_text());recall=json.loads((root/'recall-build.json').read_text())
    expected=dict(base['files']);expected['bin/atomspace_recall']=recall['binary_sha256']
    artifacts={a['name']:a for a in d['artifacts']};equal(set(artifacts),set(expected)|{'@host-loader'},'generation artifact inventory')
    for name,h in expected.items():equal(artifacts[name]['sha256'],h,'sealed artifact expected digest')
    equal(d['build_identity'],sha256((root/'recall-build.json').read_bytes()).hexdigest(),'generation original build receipt')
    equal(d['base_receipt_sha256'],sha256((root/'adapter-build.json').read_bytes()).hexdigest(),'generation base receipt');equal(d['lock_sha256'],sha256((root/'adapters.lock.json').read_bytes()).hexdigest(),'generation lock')
    equal(d['launch']['environment'],{'LANG':'C','LC_ALL':'C'},'controlled launch environment');equal(d['launch']['flags'],['--inhibit-rpath','','--inhibit-cache','--library-path','<generation-alias-directory>'],'explicit isolated launch')
    equal(result['runtime_state'],'closed','owned generation cleanup');equal(result['runtime_costs']['preparations'],1,'runtime preparation count');equal(result['runtime_costs']['original_verifications'],1,'original cryptographic verification count')
    size=sum(a['size'] for a in artifacts.values());equal(result['runtime_costs']['bytes_copied'],size,'generation copied bytes');equal(result['runtime_costs']['sealed_bytes_hashed'],size,'sealed verification bytes')
    equal(len(launches),result['native_epochs'],'one helper per cold knowledge view');equal(result['runtime_costs']['helper_launches'],len(launches),'recorded launches');equal(result['runtime_costs']['loaded_mapping_checks'],len(launches),'actual mapped artifact checks')
    equal(len(runtime),len(launches)+1,'no hidden runtime errors or preparations')
    covered={'bin/atomspace_recall','@host-loader'}|{n for n in artifacts if Path(n).name in p['covered_loaded_libraries']}
    identities={}
    for launch in launches:
        equal(launch['generation_id'],identity,'all launches use one generation');equal(launch['alias_directory'],p['directory'],'alias directory binding')
        equal(launch['command'][1:6],['--inhibit-rpath','','--inhibit-cache','--library-path',p['directory']],'launch flags and path')
        mappings=launch['covered_mappings'];equal({x['artifact'] for x in mappings},covered,'complete mapped covered closure')
        for item in mappings:
            equal(item['sha256'],artifacts[item['artifact']]['sha256'],'mapped artifact digest')
            if not item['path'].startswith('/memfd:'):raise AssertionError('mutable original mapping')
            actual=(item['device'],item['inode']);prior=identities.setdefault(item['artifact'],actual);equal(actual,prior,'same sealed inode across fresh helpers')
        equal(launch['host_mappings'],p['uncovered_host_libraries'],'declared host mapping scope')
    views=[e for e in events if e['kind']=='open_view'];equal(len(views),len(launches),'knowledge view / runtime launch correspondence')
    for e in views:equal(e['receipt']['runtime_generation_id'],identity,'view runtime generation binding')
    return dict(recorded_generation_checks=1,recorded_launch_mapping_checks=len(launches),fresh_generation_integrity_checks_during_replay=0)
