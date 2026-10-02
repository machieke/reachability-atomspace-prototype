"""Build only the new recall helper against the existing locked native libraries."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reachability.adapter_runtime import verify_native_build,verify_source,lockfile


def build(root=ROOT/'artifacts'):
    root=Path(root).resolve();verify_native_build(root)
    for name in ('atomspace','cogutil'):verify_source(name,root)
    old=json.loads((root/'adapter-build.json').read_text())
    libdirs=sorted({str((root/p).parent) for p in old['files'] if p.endswith('.so')})
    syslib=root/'sysroot/usr/lib/x86_64-linux-gnu'
    if syslib.exists():libdirs.append(str(syslib))
    binary=root/'bin/atomspace_recall';source=ROOT/'native/atomspace_recall.cc'
    includes=[root/'upstream/atomspace',root/'build/atomspace',root/'install/include']
    command=['g++-11','-std=c++20','-O2',f'-DATOMSPACE_PIN="{lockfile()["sources"]["atomspace"]["commit"]}"',str(source),'-o',str(binary),
        *('-I'+str(p) for p in includes),*('-L'+p for p in libdirs),'-Wl,-rpath,'+':'.join(libdirs),'-Wl,--disable-new-dtags',
        '-latomspace','-latombase','-lvalue','-latom_types','-lcogutil','-pthread']
    subprocess.run(command,check=True)
    receipt=dict(schema='native-recall-build/v1',base_receipt_sha256=sha256((root/'adapter-build.json').read_bytes()).hexdigest(),
        lock_sha256=sha256((ROOT/'adapters.lock.json').read_bytes()).hexdigest(),source_sha256=sha256(source.read_bytes()).hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),binary_sha256=sha256(binary.read_bytes()).hexdigest(),
        compiler=subprocess.check_output(['g++-11','--version'],text=True).splitlines()[0],command=command,
        upstream={n:lockfile()['sources'][n]['commit'] for n in ('atomspace','cogutil')})
    (root/'recall-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':build(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'artifacts')
