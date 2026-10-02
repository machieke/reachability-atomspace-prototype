"""Verify one published planner review archive without extracting it."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import tarfile


def verify(directory):
    directory=Path(directory);lines=(directory/'SHA256SUMS').read_text().splitlines()
    if len(lines)!=1:raise ValueError('expected one archive checksum')
    digest,name=lines[0].split()
    if name not in ('review.tar.gz','review.tar.xz'):raise ValueError('unexpected archive filename')
    path=directory/name
    hasher=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):hasher.update(chunk)
    if hasher.hexdigest()!=digest:raise ValueError('archive checksum differs')
    prefix='pressure-guided-planning-review-v1/'
    with tarfile.open(path,'r:*') as archive:
        files={}
        for member in archive.getmembers():
            p=PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or not(member.isfile() or member.isdir()):raise ValueError('unsafe member')
            if member.isdir():continue
            if not member.name.startswith(prefix) or member.name in files or member.size>64*1024*1024:
                raise ValueError('unexpected, duplicate or oversized member')
            files[member.name]=member
        manifest=json.load(archive.extractfile(files[prefix+'review.json']))
        if manifest['schema']!='pressure-guided-planning-independent-review/v1':raise ValueError('unknown review schema')
        if set(files)!={prefix+n for n in manifest['files']}|{prefix+'review.json'}:raise ValueError('archive inventory differs')
        for name,expected in manifest['files'].items():
            if sha256(archive.extractfile(files[prefix+name]).read()).hexdigest()!=expected:raise ValueError('artifact differs: '+name)
    return dict(status='PASS',archive_sha256=digest,files_verified=len(manifest['files']),
        experiment_revision=manifest['experiment_revision'],
        limitation='Integrity against published checksum; not publisher authentication or semantic replay.')


if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
