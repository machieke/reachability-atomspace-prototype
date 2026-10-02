"""Verify published projection review inventory without extracting it."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import tarfile


def verify(directory):
    directory=Path(directory)
    lines=(directory/'SHA256SUMS').read_text().splitlines()
    if len(lines)!=1: raise ValueError('expected one archive checksum')
    expected,name=lines[0].split()
    if name!='review.tar.gz': raise ValueError('unexpected archive filename')
    if sha256((directory/name).read_bytes()).hexdigest()!=expected:
        raise ValueError('archive checksum differs')
    prefix='pressure-projection-review-v1/'
    with tarfile.open(directory/name,'r:gz') as archive:
        files={}
        for member in archive.getmembers():
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not(member.isfile() or member.isdir()):
                raise ValueError('unsafe archive member')
            if member.isdir(): continue
            if not member.name.startswith(prefix) or member.name in files or member.size>64*1024*1024:
                raise ValueError('unexpected, duplicate or oversized archive member')
            files[member.name]=member
        manifest=json.load(archive.extractfile(files[prefix+'review.json']))
        if manifest['schema']!='pressure-projection-independent-review/v1': raise ValueError('unknown review schema')
        if set(files)!={prefix+n for n in manifest['files']}|{prefix+'review.json'}:
            raise ValueError('archive inventory differs')
        for name,digest in manifest['files'].items():
            if sha256(archive.extractfile(files[prefix+name]).read()).hexdigest()!=digest:
                raise ValueError('artifact checksum differs: '+name)
    return dict(status='PASS',archive_sha256=expected,files_verified=len(manifest['files']),
        frozen_revision=manifest['frozen_revision'],experimental_revision=manifest['experimental_revision'],
        limitation='Integrity against the published checksum, not publisher authentication or semantic replay.')


if __name__=='__main__': print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
