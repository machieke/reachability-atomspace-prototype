"""Existing deterministic review archive layout; explicit fresh staging."""
import argparse,json,shutil,tarfile
from hashlib import sha256
from pathlib import Path
from validation_lab.decision_comparison import write
from .cases import ROOT


def build(work,development,review):
    work=Path(work);review=Path(review);stage=work/'review-stage'
    if stage.exists() or (review/'review.tar.xz').exists():raise ValueError('fresh publication staging required')
    stage.mkdir()
    for name in ('comparison','validation'):shutil.copytree(work/name,stage/name,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(development,stage/'development',ignore=shutil.ignore_patterns('__pycache__'))
    for p in review.iterdir():
        if p.is_file() and p.name not in ('review.tar.xz','ARCHIVE.json','SHA256SUMS','PUBLICATION.json'):
            target=stage/'review'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
    sources=json.loads((stage/'comparison/sources.json').read_text())
    manifest=dict(schema='closed-loop-obligations-independent-review/v1',experiment_revision=sources['revision'],files={str(p.relative_to(stage)):sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file()})
    write(stage/'review.json',manifest);archive=review/'review.tar.xz'
    with tarfile.open(archive,'w:xz',preset=6) as tar:
        for path in sorted(stage.rglob('*')):
            if not path.is_file():continue
            if path.is_symlink():raise ValueError('symlink')
            info=tar.gettarinfo(str(path),'closed-loop-obligations-review-v1/'+str(path.relative_to(stage)))
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.mode=0o644
            with path.open('rb') as stream:tar.addfile(info,stream)
    data=archive.read_bytes();metadata=dict(schema='closed-loop-obligations-review-archive/v1',archive=archive.name,parts=[archive.name],sha256=sha256(data).hexdigest(),bytes=len(data),measured_revision=sources['revision'],auditor_revision=sources['revision'])
    write(review/'ARCHIVE.json',metadata);(review/'SHA256SUMS').write_text(''.join(sha256((review/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ('ARCHIVE.json',archive.name)))
    return dict(**metadata,files=len(manifest['files']))


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--development',required=True);p.add_argument('--review',default='reviews/closed-loop-obligations-v1');a=p.parse_args();print(json.dumps(build(a.work,a.development,a.review),indent=2))

if __name__=='__main__':main()
