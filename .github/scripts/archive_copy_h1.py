"""COPY-H1: exact-path historical DATA reads, never a trusted-input link waiver.

Reuses the immutable V1 traversal/binding code in a private closed namespace.
No old module globals change. No deletion, ACL write, imported copied code,
retry, source link creation or destination replacement exists here.
"""
import ctypes
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
import types
import uuid

import archive_copy_snapshot as v

SCOPE = 'W_COPY_H1_EXACT_HISTORICAL_CONTENT'
ROLE = 'HISTORICAL_NEGATIVE_TEST_CACHE_DATA_ONLY'


def now(): return datetime.now(timezone.utc).isoformat()


def permission_digest(path):
    """Read owner/group/DACL only. SACL needs privileges and is not requested."""
    path = v.ordinary(Path(path))
    if os.name != 'nt':
        info = path.stat()
        return v.digest([info.st_uid,info.st_gid,info.st_mode])
    from ctypes import wintypes
    api = ctypes.WinDLL('advapi32',use_last_error=True).GetFileSecurityW
    api.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p,
                    wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    api.restype = wintypes.BOOL
    needed = wintypes.DWORD()
    api(str(path),7,None,0,ctypes.byref(needed))  # OWNER|GROUP|DACL
    if not needed.value: raise ctypes.WinError(ctypes.get_last_error())
    buffer = ctypes.create_string_buffer(needed.value)
    if not api(str(path),7,buffer,len(buffer),ctypes.byref(needed)):
        raise ctypes.WinError(ctypes.get_last_error())
    return hashlib.sha256(buffer.raw[:needed.value]).hexdigest()


def _read_regular(path,destination=None):
    """Data capture primitive; only Context's exact policy authorizes links."""
    path = v.ordinary(Path(path).absolute()); before = path.stat()
    v.require(stat.S_ISREG(before.st_mode),'E_COPY_FILE_TYPE')
    permissions = permission_digest(path)
    hashed,size = hashlib.sha256(),0
    with path.open('rb') as source:
        opened = os.fstat(source.fileno())
        v.require(v.identity(opened)[:5] == v.identity(before)[:5],'E_COPY_READ_CHANGED')
        target = None
        try:
            if destination is not None:
                destination = Path(destination); v.ordinary(destination.parent)
                target = destination.open('xb')
            while block := source.read(1024*1024):
                hashed.update(block); size += len(block)
                if target is not None: target.write(block)
            v.require(v.identity(os.fstat(source.fileno())) == v.identity(opened),'E_COPY_READ_CHANGED')
        finally:
            if target is not None: target.close()
    v.require(v.identity(v.ordinary(path).stat()) == v.identity(before) and
              size == before.st_size and permission_digest(path) == permissions,'E_COPY_READ_CHANGED')
    return {'kind':'file','size':size,'sha256':hashed.hexdigest(),
            'identity':v.identity(before),'permission_sha256':permissions}


def make_policy(root, allowed_paths, protected_paths):
    """Caller supplies explicit approved files, never a wildcard or extension.

    The sealed controller, not this reusable library, selects the real manifest.
    No source with a protected live identity may acquire the data-only role.
    """
    root = v.ordinary(Path(root).absolute())
    protected = []
    for path in protected_paths:
        path = v.ordinary(Path(path)); info = path.stat()
        protected.append([info.st_dev,info.st_ino])
    allowed = {}
    for path in allowed_paths:
        path = Path(path).absolute()
        v.require(path.is_relative_to(root),'E_H1_LINK_SCOPE')
        name = v.relative(path.relative_to(root).as_posix())
        v.require('retained-temp' in Path(name).parts,'E_H1_LINK_SCOPE')
        info = v.ordinary(path).stat()
        v.require(stat.S_ISREG(info.st_mode) and info.st_nlink > 1,'E_H1_LINK_SCOPE')
        v.require([info.st_dev,info.st_ino] not in protected,'E_H1_TRUSTED_LINK')
        v.require(name not in allowed,'E_H1_LINK_SCOPE')
        row = _read_regular(path)
        allowed[name] = {'role':ROLE,**{k:row[k] for k in
                        ('identity','size','sha256','permission_sha256')}}
    policy = {'scope':SCOPE,'root':str(root),'allowed':dict(sorted(allowed.items())),
              'protected_identities':sorted(protected)}
    return policy


class Context:
    def __init__(self, policy):
        v.require(isinstance(policy,dict) and set(policy) ==
                  {'scope','root','allowed','protected_identities'} and policy['scope'] == SCOPE,
                  'E_H1_POLICY')
        self.policy = policy
        self.root = v.ordinary(Path(policy['root']))
        v.require(isinstance(policy['allowed'],dict) and
                  isinstance(policy['protected_identities'],list),'E_H1_POLICY')
        v.require(all(isinstance(row,list) and len(row) == 2 and
                      all(type(n) is int and n >= 0 for n in row)
                      for row in policy['protected_identities']),'E_H1_POLICY')
        v.require(len({name.casefold() for name in policy['allowed']}) == len(policy['allowed']),
                  'E_H1_POLICY')
        for name,row in policy['allowed'].items():
            v.relative(name)
            v.require('retained-temp' in Path(name).parts and isinstance(row,dict) and
                      set(row) == {'role','identity','size','sha256','permission_sha256'} and row['role'] == ROLE and
                      isinstance(row['identity'],list) and len(row['identity']) == 6 and
                      all(type(x) is int for x in row['identity']) and row['identity'][2] > 1 and
                      type(row['size']) is int and row['size'] >= 0 and row['size'] == row['identity'][3] and
                      v.hexdigest(row['sha256']) and v.hexdigest(row['permission_sha256']) and
                      row['identity'][:2] not in policy['protected_identities'],'E_H1_TRUSTED_LINK_SCOPE')
        # Only archive-data operations get the scoped reader. Strict record/load
        # keep their original module namespace and always require one link.
        namespace = dict(v.__dict__)
        namespace.update(SCOPE=SCOPE,read_file=lambda *a,**k:self.read_file(*a,**k),
            validate_objects=self.validate_objects,content=self.content,
            copy_denied=self.copy_denied,verify_copies=self.verify_copies)
        for name in ('collect','validate_context','validate_request','scan',
                     'expected_copy_objects','bundle_from_copies','merge'):
            old = getattr(v,name)
            function = types.FunctionType(old.__code__,namespace,name,old.__defaults__)
            namespace[name] = function
            setattr(self,name,function)
        self.expected_copy_objects = namespace['expected_copy_objects']

    def read_file(self,path,destination=None):
        path = v.ordinary(Path(path).absolute())
        if not path.is_relative_to(self.root):
            return v.read_file(path,destination)  # Strict destination/trusted path.
        before = path.stat()
        v.require(stat.S_ISREG(before.st_mode),'E_COPY_FILE_TYPE')
        name = path.relative_to(self.root).as_posix()
        allowed = self.policy['allowed'].get(name)
        if allowed is not None:
            v.require(allowed['identity'] == v.identity(before),'E_H1_LINK_IDENTITY_CHANGED')
        else: v.require(before.st_nlink == 1,'E_H1_LINK_SCOPE')
        result = _read_regular(path,destination)
        if allowed is not None:
            v.require(all(result[k] == allowed[k] for k in
                          ('identity','size','sha256','permission_sha256')),'E_H1_LINK_CONTENT_CHANGED')
        return result

    def validate_objects(self,objects):
        v.require(isinstance(objects,dict),'E_COPY_OBJECTS')
        v.require(len({v.relative(k).casefold() for k in objects}) == len(objects),'E_COPY_COVERAGE_ALIAS')
        for name,row in objects.items():
            if row == {'kind':'directory'}: continue
            v.require(isinstance(row,dict) and set(row) ==
                      {'kind','size','sha256','identity','permission_sha256'} and row['kind'] == 'file' and
                      type(row['size']) is int and row['size'] >= 0 and v.hexdigest(row['sha256']) and
                      v.hexdigest(row['permission_sha256']) and isinstance(row['identity'],list) and
                      len(row['identity']) == 6 and all(type(n) is int for n in row['identity']) and
                      row['identity'][2] >= 1 and row['identity'][3] == row['size'],'E_H1_OBJECT')
            if row['identity'][2] != 1:
                allowed = self.policy['allowed'].get(name)
                v.require(allowed is not None and all(allowed[k] == row[k] for k in
                          ('identity','size','sha256','permission_sha256')),
                          'E_H1_LINK_SCOPE')

    @staticmethod
    def content(objects):
        return {k:{field:value for field,value in row.items()
                   if field not in ('identity','permission_sha256')} for k,row in objects.items()}

    def mappings(self,objects,output,batch):
        return {name:{'original':str(self.root/name),'copy':str(Path(output)/'data'/name),
                      'session':batch['session'],'phase':batch['phase'],'batch_id':batch['id'],
                      'size':row['size'],'sha256':row['sha256'],'original_identity':row['identity'],
                      'original_permission_sha256':row['permission_sha256'],
                      'verification':'VERIFIED_CONTENT_COPY_NOT_AUTHENTICATED'}
                for name,row in objects.items() if row['kind'] == 'file'}

    def copy_denied(self,request,output):
        self.validate_request(request)
        v.require(request['root'] == str(self.root),'E_H1_ROOT')
        output = Path(output).absolute(); v.ordinary(output.parent)
        v.require(not output.is_relative_to(self.root) and not self.root.is_relative_to(output),
                  'E_COPY_OUTPUT_SCOPE')
        started = now()
        output.mkdir()  # One use, including after a partial failure.
        data = output/'data'; data.mkdir()
        copied = {}
        for target in request['unresolved']:
            original = self.root if target == '.' else self.root/target
            rows,missing = self.collect(original)
            v.require(not missing,'E_COPY_UNREADABLE')
            wanted = request['unresolved'][target]
            v.require(wanted == 'unknown' or rows['.']['kind'] == wanted,'E_COPY_TYPE_CHANGED')
            for name,row in rows.items():
                name = target if name == '.' else (name if target == '.' else target+'/'+name)
                copied[name] = row
                dest = data if name == '.' else data/name
                if row['kind'] == 'directory': v.copy_directory(data,dest)
                else:
                    v.copy_directory(data,dest.parent)
                    v.require(self.read_file(self.root/name,dest) == row,'E_COPY_SOURCE_CHANGED')
            again,missing = self.collect(original)
            v.require(not missing and again == rows,'E_COPY_SOURCE_CHANGED')
        actual,missing = v.collect(data)  # ALL destinations still strictly single-link.
        v.require(not missing and v.content(actual) == self.expected_copy_objects(copied),'E_COPY_CONTENT')
        batch = {'id':uuid.uuid4().hex,'session':request['session'],'phase':request['phase'],
                 'request_utc':request['observed_utc'],'started_utc':started,'finished_utc':now()}
        value = {'scope':SCOPE,'request_sha256':v.digest(request),'policy_sha256':v.digest(self.policy),
                 'objects':dict(sorted(copied.items())),'producer_authentication':False,
                 'batch':batch,'files':self.mappings(copied,output,batch),'status':'COMPLETE_CONTENT_COPY'}
        self.validate_manifest(request,output,value)
        v.save(output/'Copies.json',value)  # No complete record on any earlier error.
        return value

    def validate_manifest(self,request,output,copies):
        v.require(isinstance(copies,dict) and set(copies) == {'scope','request_sha256',
                  'policy_sha256','objects','producer_authentication','batch','files','status'} and
                  copies['scope'] == SCOPE and copies['request_sha256'] == v.digest(request) and
                  copies['policy_sha256'] == v.digest(self.policy) and
                  copies['producer_authentication'] is False and copies['status'] == 'COMPLETE_CONTENT_COPY',
                  'E_H1_COPY_BINDING')
        objects = copies['objects']; self.validate_objects(objects)
        batch = copies['batch']
        v.require(isinstance(batch,dict) and set(batch) ==
                  {'id','session','phase','request_utc','started_utc','finished_utc'} and
                  isinstance(batch['id'],str) and len(batch['id']) == 32 and
                  all(c in '0123456789abcdef' for c in batch['id']) and
                  batch['session'] == request['session'] and batch['phase'] == request['phase'] and
                  batch['request_utc'] == request['observed_utc'],'E_H1_BATCH_BINDING')
        try:
            times = [datetime.fromisoformat(batch[k]) for k in ('request_utc','started_utc','finished_utc')]
            v.require(all(t.tzinfo is not None and t.utcoffset().total_seconds() == 0 for t in times)
                      and times[0] <= times[1] <= times[2],'E_H1_BATCH_TIME')
        except (TypeError,ValueError): raise ValueError('E_H1_BATCH_TIME') from None
        v.require(copies['files'] == self.mappings(objects,output,batch),'E_H1_FILE_MAPPING')
        targets = request['unresolved']
        v.require(all(sum(v.within(name,target) for target in targets) == 1 for name in objects) and
                  all(target in objects for target in targets),'E_COPY_COVERAGE')
        for name in objects:
            parent = str(Path(name).parent).replace('\\','/')
            v.require(name in targets or objects.get(parent) == {'kind':'directory'},'E_COPY_COVERAGE_PARENT')

    def verify_copies(self,request,output,sha):
        self.validate_request(request)
        output = v.ordinary(Path(output))
        copies = v.load(output/'Copies.json',sha)
        self.validate_manifest(request,output,copies)
        actual,denied = v.collect(output/'data')
        v.require(not denied and v.content(actual) == self.expected_copy_objects(copies['objects']),
                  'E_COPY_CONTENT')
        return copies

    def compare(self,before,after):
        self.validate_context(before); self.validate_context(after)
        self.validate_objects(before['objects']); self.validate_objects(after['objects'])
        v.require(before['phase'] == 'BEFORE' and after['phase'] == 'AFTER','E_COPY_PHASE')
        v.require(before['root'] == after['root'] == str(self.root) and
                  before['session'] == after['session'] and before['nonce'] != after['nonce'] and
                  after['binding']['before_sha256'] == v.digest(before),'E_COPY_BINDING')
        # Includes original IDs/link counts and owner/group/DACL digests, not atime.
        v.require(before['objects'] == after['objects'],'E_COPY_CONTENT_OR_IDENTITY_CHANGED')
        return {'status':'CONTENT_MATCH_AT_BEFORE_AFTER_SAMPLES','producer_authentication':False,
                'whole_skill_ready':False,'continuous_immutability_proven':False}
