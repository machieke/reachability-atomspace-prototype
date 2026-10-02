"""Verify the published archive and its complete inventory without extracting."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import tarfile


def verify(directory):
    directory=Path(directory)
    entries=(directory/'SHA256SUMS').read_text().splitlines()
    if len(entries)!=1: raise ValueError('expected one published archive checksum')
    expected,name=entries[0].split()
    if name!='review.tar.gz': raise ValueError('unexpected archive filename')
    path=directory/name
    if sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('archive checksum differs')
    prefix='b0-b3-review-3e8fd7b/'
    with tarfile.open(path,'r:gz') as archive:
        members=archive.getmembers(); files={}
        for member in members:
            parts=PurePosixPath(member.name).parts
            if PurePosixPath(member.name).is_absolute() or '..' in parts or not (member.isfile() or member.isdir()):
                raise ValueError('unsafe archive member')
            if member.isdir(): continue
            if not member.name.startswith(prefix) or member.name in files or member.size>64*1024*1024:
                raise ValueError('unexpected, duplicate or oversized archive member')
            files[member.name]=member
        manifest=json.load(archive.extractfile(files[prefix+'review.json']))
        if manifest['schema']!='b0-b3-independent-review/v1': raise ValueError('unknown review schema')
        expected_files={prefix+name for name in manifest['files']}|{prefix+'review.json'}
        if set(files)!=expected_files: raise ValueError('archive inventory differs')
        for name,digest in manifest['files'].items():
            content=archive.extractfile(files[prefix+name]).read()
            if sha256(content).hexdigest()!=digest: raise ValueError('artifact checksum differs: '+name)
    return dict(status='PASS',archive_sha256=expected,files_verified=len(manifest['files']),
        frozen_revision=manifest['frozen_revision'],diagnostic_revision=manifest['diagnostic_revision'],
        limitation='Byte integrity against the published checksum, not publisher authentication or semantic replay.')


if __name__=='__main__': print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
