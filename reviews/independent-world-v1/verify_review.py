"""Verify one logical review archive (optionally split for repository limits)."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
from tempfile import TemporaryFile


def digest(path):
    h=sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify(directory):
    directory=Path(directory);expected={}
    for line in (directory/'SHA256SUMS').read_text().splitlines():
        value,name=line.split()
        if name in expected or not re.fullmatch(r'[0-9a-f]{64}',value):raise ValueError('invalid checksum declaration')
        if name!='ARCHIVE.json' and not re.fullmatch(r'review\.tar\.(?:xz|gz)(?:\.part-[0-9]{3})?',name):
            raise ValueError('unexpected archive filename')
        expected[name]=value
        if digest(directory/name)!=value:raise ValueError('archive checksum differs: '+name)
    metadata=json.loads((directory/'ARCHIVE.json').read_text())
    if 'ARCHIVE.json' not in expected or metadata['schema']!='independent-world-review-archive/v1':raise ValueError('missing archive descriptor')
    name=metadata['archive'];parts=metadata['parts']
    if name not in ('review.tar.xz','review.tar.gz') or not parts or len(parts)>16:raise ValueError('invalid archive parts')
    allowed=[name] if len(parts)==1 else [name+f'.part-{i:03d}' for i in range(len(parts))]
    if parts!=allowed or set(expected)!=set(parts)|{'ARCHIVE.json'}:raise ValueError('archive part inventory differs')
    prefix='independent-world-review-v1/'
    with TemporaryFile() as combined:
        h=sha256();size=0
        for part in parts:
            with (directory/part).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):
                    h.update(chunk);combined.write(chunk);size+=len(chunk)
        if h.hexdigest()!=metadata['sha256'] or size!=metadata['bytes']:raise ValueError('combined archive differs')
        combined.seek(0)
        with tarfile.open(fileobj=combined,mode='r:*') as archive:
            files={}
            for member in archive.getmembers():
                p=PurePosixPath(member.name)
                if p.is_absolute() or '..' in p.parts or not(member.isfile() or member.isdir()):raise ValueError('unsafe member')
                if member.isdir():continue
                if not member.name.startswith(prefix) or member.name in files or member.size>64*1024*1024:
                    raise ValueError('unexpected, duplicate or oversized member')
                files[member.name]=member
            manifest=json.load(archive.extractfile(files[prefix+'review.json']))
            if manifest['schema']!='independent-world-independent-review/v1':raise ValueError('unknown review schema')
            if set(files)!={prefix+n for n in manifest['files']}|{prefix+'review.json'}:raise ValueError('archive inventory differs')
            for item,expected_digest in manifest['files'].items():
                if sha256(archive.extractfile(files[prefix+item]).read()).hexdigest()!=expected_digest:
                    raise ValueError('artifact differs: '+item)
    return dict(status='PASS',archive_sha256=metadata['sha256'],archive_bytes=size,parts=len(parts),
        files_verified=len(manifest['files']),experiment_revision=manifest['experiment_revision'],
        limitation='Integrity against published checksums; not publisher authentication or semantic replay.')


if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
