"""Cryptographic preparation plus kernel-sealed content, never a boolean cache.

Linux/glibc only. Covered artifacts are immutable memfds; aliases and live mapped
inodes are checked. Trusted Python/kernel/procfs and host system libraries remain
outside the original receipt's scope. Not a malicious-owner security boundary.
"""
from collections import defaultdict
from dataclasses import dataclass
import ctypes,fcntl,json,os,shutil,subprocess,sys,tempfile,uuid
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from experimental_native_recall.backend import RecallError,verify_build
from experimental_native_recall.schema import SCHEMA
from reachability.adapter_runtime import ROOT
from reachability.trace_protocol import canonical

POLICY='sealed-runtime-generation/v1'
# Linux UAPI constants; this portable CPython build omits their Python names.
F_ADD_SEALS=1033
F_GET_SEALS=1034
SEALS=0x000f

def memfd(name):
    if sys.platform!='linux':raise RecallError('sealed runtime requires Linux')
    libc=ctypes.CDLL(None,use_errno=True)
    fn=libc.memfd_create;fn.argtypes=(ctypes.c_char_p,ctypes.c_uint);fn.restype=ctypes.c_int
    fd=fn(name.encode(),3)  # MFD_CLOEXEC | MFD_ALLOW_SEALING
    if fd<0:raise OSError(ctypes.get_errno(),'memfd_create failed')
    return fd
ENV={'LANG':'C','LC_ALL':'C'}

@dataclass(frozen=True)
class Artifact:
    name:str
    fd:int
    device:int
    inode:int
    size:int
    sha256:str

class Generation:
    def __init__(self,root=ROOT/'artifacts'):
        self.root=Path(root).resolve();self.state='new';self.artifacts=();self.directory=None
        self.costs=defaultdict(int);self.events=[];self.descriptor_json=None;self.generation_id=None
        self.expected_libraries=();self.host_libraries=();self._building=[]
    @property
    def descriptor(self):return json.loads(self.descriptor_json) if self.descriptor_json else None
    def _seal(self,name,source,expected=None):
        fd=memfd('recall-'+name.replace('/','-')[-180:])
        self._building.append(fd);t=perf_counter_ns()
        with Path(source).open('rb') as stream:
            while chunk:=stream.read(1048576):
                self.costs['bytes_copied']+=len(chunk);offset=0
                while offset<len(chunk):offset+=os.write(fd,chunk[offset:])
        self.costs['copy_ns']+=perf_counter_ns()-t
        os.fchmod(fd,0o500);fcntl.fcntl(fd,F_ADD_SEALS,SEALS)
        t=perf_counter_ns();h=sha256();offset=0
        while chunk:=os.pread(fd,1048576,offset):h.update(chunk);offset+=len(chunk)
        self.costs['sealed_bytes_hashed']+=offset;self.costs['sealed_hash_ns']+=perf_counter_ns()-t
        if expected is not None and h.hexdigest()!=expected:raise RecallError('staged artifact digest mismatch: '+name)
        stat=os.fstat(fd)
        return Artifact(name,fd,stat.st_dev,stat.st_ino,stat.st_size,h.hexdigest())
    def prepare(self):
        if self.state!='new':raise RecallError('generation preparation requires new explicit owner')
        start=perf_counter_ns();self.costs['preparations']+=1
        try:
            base_raw=(self.root/'adapter-build.json').read_bytes();recall_raw=(self.root/'recall-build.json').read_bytes()
            base=json.loads(base_raw);recall=json.loads(recall_raw);lock_raw=(ROOT/'adapters.lock.json').read_bytes();files=dict(base['files']);files['bin/atomspace_recall']=recall['binary_sha256']
            if not 1<=len(files)<=64:raise RecallError('generation artifact count bound')
            total=0
            for name in files:
                path=Path(name)
                if path.is_absolute() or '..' in path.parts or not (self.root/path).resolve().is_relative_to(self.root):raise RecallError('artifact outside build root')
                total+=(self.root/path).stat().st_size
            if total>268435456:raise RecallError('generation byte bound')
            t=perf_counter_ns();self.costs['original_verifications']+=1
            try:build=verify_build(self.root)
            finally:self.costs['original_verification_ns']+=perf_counter_ns()-t
            # Count exactly the digest inputs of the unchanged verifier separately
            # from metadata parsing, copying and the sealed-content digest pass.
            digest_paths=[ROOT/'adapters.lock.json',ROOT/'native/atomspace_batch.cc',*(self.root/n for n in base['files']),self.root/'adapter-build.json',ROOT/'adapters.lock.json',ROOT/'native/atomspace_recall.cc',ROOT/'scripts/build_native_recall.py',self.root/'bin/atomspace_recall',self.root/'recall-build.json']
            self.costs['original_bytes_hashed']+=sum(p.stat().st_size for p in digest_paths)
            if sha256(lock_raw).hexdigest()!=recall['lock_sha256'] or build!=sha256(recall_raw).hexdigest() or sha256(base_raw).hexdigest()!=recall['base_receipt_sha256']:raise RecallError('receipt changed during preparation')
            self.artifacts=tuple(self._seal(n,self.root/n,h) for n,h in sorted(files.items()))
            # Additional launch artifact: host loader bytes are captured/sealed,
            # identified explicitly, not represented as originally receipt-pinned.
            loader=Path('/lib64/ld-linux-x86-64.so.2').resolve();self.artifacts+= (self._seal('@host-loader',loader),)
            self.directory=Path(tempfile.mkdtemp(prefix='recall-generation-'))
            aliases={}
            for a in self.artifacts:
                if not a.name.endswith('.so'):continue
                name=Path(a.name).name
                if name in aliases:raise RecallError('ambiguous library basename')
                aliases[name]='/proc/self/fd/'+str(a.fd);os.symlink(aliases[name],self.directory/name)
            os.chmod(self.directory,0o500);self._dir_identity=self.directory.stat().st_dev,self.directory.stat().st_ino
            self._aliases=aliases
            info=dict(schema=POLICY,nonce=uuid.uuid4().hex,root=str(self.root),build_identity=build,
                base_receipt_sha256=sha256(base_raw).hexdigest(),lock_sha256=recall['lock_sha256'],query_protocol=SCHEMA,atomspace_pin=json.loads(lock_raw)['sources']['atomspace']['commit'],
                artifacts=[dict(name=a.name,sha256=a.sha256,size=a.size) for a in self.artifacts],
                launch=dict(loader_source=str(loader),binary='bin/atomspace_recall',flags=['--inhibit-rpath','','--inhibit-cache','--library-path','<generation-alias-directory>'],environment=ENV,alias_policy='exact inherited sealed descriptor',policy=POLICY))
            self.generation_id=sha256(canonical(info).encode()).hexdigest();info['generation_id']=self.generation_id
            self.descriptor_json=canonical(info);self.state='valid';self.check(self.root,self.generation_id)
            t=perf_counter_ns();listing=subprocess.run(self.command(list_only=True),env=dict(ENV),pass_fds=self.fds,capture_output=True,text=True,timeout=30)
            self.costs['loader_resolution_ns']+=perf_counter_ns()-t
            if listing.returncode or listing.stderr:raise RecallError('generation loader resolution failed: '+listing.stderr[:400])
            found=[];hosts=[]
            for line in listing.stdout.splitlines():
                tokens=line.split()
                if '=>' not in tokens:continue
                name,path=tokens[0],tokens[2]
                if name=='/lib64/ld-linux-x86-64.so.2':
                    if path!='/proc/self/fd/'+str(self.item('@host-loader').fd):raise RecallError('loader resolved outside sealed generation')
                elif name in aliases:
                    if path!=str(self.directory/name):raise RecallError('loader resolved mutable original: '+name)
                    found.append(name)
                elif path.startswith('/'):
                    if str(self.root) in path:raise RecallError('uncovered build library: '+path)
                    hosts.append(str(Path(path).resolve()))
                else:raise RecallError('unresolved host dependency: '+line)
            if 'libatomspace.so' not in found:raise RecallError('missing covered dependency resolution')
            self.expected_libraries=tuple(sorted(found));self.host_libraries=tuple(sorted(set(hosts)))
            self.events.append(dict(kind='prepared',descriptor=self.descriptor,aliases=dict(aliases),directory=str(self.directory),loader_listing=listing.stdout,covered_loaded_libraries=self.expected_libraries,uncovered_host_libraries=self.host_libraries))
            return self
        except Exception as error:
            self.state='failed';self.events.append(dict(kind='preparation_error',error=str(error)));self._cleanup()
            if isinstance(error,RecallError):raise
            raise RecallError('runtime preparation failed: '+str(error)) from error
        finally:self.costs['preparation_inclusive_ns']+=perf_counter_ns()-start
    @property
    def fds(self):return tuple(a.fd for a in self.artifacts)
    def item(self,name):return next(a for a in self.artifacts if a.name==name)
    def command(self,list_only=False,inhibit=True):
        flags=['--inhibit-rpath',''] if inhibit else []
        return ['/proc/self/fd/'+str(self.item('@host-loader').fd),*flags,'--inhibit-cache','--library-path',str(self.directory),*(['--list'] if list_only else []),'/proc/self/fd/'+str(self.item('bin/atomspace_recall').fd)]
    def check(self,root,generation_id,protocol=SCHEMA):
        t=perf_counter_ns();self.costs['integrity_checks']+=1
        try:
            if self.state!='valid' or Path(root).resolve()!=self.root or generation_id!=self.generation_id or protocol!=SCHEMA:raise RecallError('closed/failed or mismatched runtime generation')
            descriptor=self.descriptor;declared=descriptor.pop('generation_id')
            if descriptor['launch']['environment']!=ENV or declared!=generation_id or sha256(canonical(descriptor).encode()).hexdigest()!=generation_id:raise RecallError('descriptor identity changed')
            stat=self.directory.stat()
            if (stat.st_dev,stat.st_ino)!=self._dir_identity or set(os.listdir(self.directory))!=set(self._aliases):raise RecallError('generation directory replaced/missing')
            for a in self.artifacts:
                st=os.fstat(a.fd)
                if (st.st_dev,st.st_ino,st.st_size)!=(a.device,a.inode,a.size) or fcntl.fcntl(a.fd,F_GET_SEALS)!=SEALS:raise RecallError('sealed descriptor drift: '+a.name)
            for name,target in self._aliases.items():
                if os.readlink(self.directory/name)!=target:raise RecallError('generation alias drift: '+name)
        except Exception as error:
            self.state='failed';self.events.append(dict(kind='integrity_error',error=str(error)));self._cleanup()
            if isinstance(error,RecallError):raise
            raise RecallError('runtime lifetime invalid: '+str(error)) from error
        finally:self.costs['integrity_checks_ns']+=perf_counter_ns()-t
    def check_loaded(self,pid):
        start=perf_counter_ns();self.costs['loaded_mapping_checks']+=1
        try:
            self.check(self.root,self.generation_id);mapping=[];seen=set();host=[]
            by_identity={(a.device,a.inode):a for a in self.artifacts}
            for line in Path('/proc',str(pid),'maps').read_text().splitlines():
                fields=line.split(None,5)
                if len(fields)<6 or fields[4]=='0':continue
                major,minor=(int(x,16) for x in fields[3].split(':'));identity=os.makedev(major,minor),int(fields[4]);path=fields[5]
                if identity in by_identity:
                    a=by_identity[identity];seen.add(a.name)
                    if a.name not in [x['artifact'] for x in mapping]:mapping.append(dict(artifact=a.name,device=a.device,inode=a.inode,path=path,sha256=a.sha256))
                elif path.startswith('/'):
                    if path not in self.host_libraries:raise RecallError('unexpected/unpinned mapped library: '+path)
                    if path not in host:host.append(path)
                else:raise RecallError('unknown mapped artifact: '+path)
            required={'bin/atomspace_recall','@host-loader'}|{a.name for a in self.artifacts if Path(a.name).name in self.expected_libraries}
            if not required<=seen:raise RecallError('covered loader mapping missing')
            receipt=dict(kind='launch',generation_id=self.generation_id,pid=pid,covered_mappings=sorted(mapping,key=lambda x:x['artifact']),host_mappings=sorted(host),command=self.command(),alias_directory=str(self.directory))
            self.events.append(receipt);self.costs['helper_launches']+=1;return receipt
        except Exception as error:
            self.state='failed';self.events.append(dict(kind='mapping_error',error=str(error)));self._cleanup()
            if isinstance(error,RecallError):raise
            raise RecallError('loaded artifact check failed: '+str(error)) from error
        finally:self.costs['loaded_mapping_checks_ns']+=perf_counter_ns()-start
    def _cleanup(self):
        t=perf_counter_ns()
        for fd in self._building:
            try:os.close(fd)
            except OSError:pass
        self._building=[]
        if self.directory is not None and self.directory.exists():
            os.chmod(self.directory,0o700);shutil.rmtree(self.directory)
        self.costs['cleanup_ns']+=perf_counter_ns()-t
    def close(self):
        self._cleanup()
        if self.state!='failed':self.state='closed'
