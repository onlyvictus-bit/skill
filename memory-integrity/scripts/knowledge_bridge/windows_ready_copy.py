"""Read-only READY signal with a parent-owned, current-token copy and scoped TTL.

No ACL/attribute changes or access bypass. Only new cache payloads whose accepted
read AND native worker exit are recorded can expire; originals are never removed.
"""
import ctypes
from ctypes import wintypes as w
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import time
import uuid

SCOPE='MEMORY_INTEGRITY_READY_COPY_V1'
MAGIC=b'RDYCOPY1'
LIMIT=4096
FRAME_LIMIT=44+LIMIT
RETENTION_DAYS=3
READ=0x80000000
WRITE=0x40000000
INVALID=ctypes.c_void_p(-1).value


def require(value,code):
    if not value:raise ValueError('E_READY_COPY_'+code)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def _norm(path):return os.path.normcase(os.path.abspath(os.fspath(path)))
def _now(value=None):
    value=datetime.now(timezone.utc) if value is None else value
    require(isinstance(value,datetime) and value.tzinfo is not None and value.utcoffset()==timedelta(0),'UTC')
    return value


def _json(raw):
    require(type(raw) is bytes and len(raw)<=16384,'JSON_SIZE')
    def pairs(items):
        result={}
        for key,value in items:require(key not in result,'JSON_DUPLICATE');result[key]=value
        return result
    def constant(value):raise ValueError('E_READY_COPY_JSON_CONSTANT:'+value)
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)


def _ordinary(path):
    path=Path(path).absolute()
    for part in (path,*path.parents):
        info=part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'REDIRECT')
    return path


def _mkdir(path):
    path=Path(path).absolute();missing=[];parent=path
    while not parent.exists():missing.append(parent);parent=parent.parent
    _ordinary(parent)
    for item in reversed(missing):
        _ordinary(item.parent)
        try:item.mkdir()
        except FileExistsError:pass
        require(_ordinary(item).is_dir(),'ROOT_TYPE')
    return _ordinary(path)


class _Info(ctypes.Structure):
    _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),
        ('written',w.FILETIME),('volume',w.DWORD),('size_high',w.DWORD),('size_low',w.DWORD),
        ('links',w.DWORD),('index_high',w.DWORD),('index_low',w.DWORD)]


class _Disposition(ctypes.Structure):
    _fields_=[('delete',ctypes.c_ubyte)]


class NativeFiles:
    def __init__(self):
        require(os.name=='nt','WINDOWS_REQUIRED')
        self.api=ctypes.WinDLL('kernel32',use_last_error=True);self.handles=set()
        signatures={
            'CreateFileW':([w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE],w.HANDLE),
            'GetFileInformationByHandle':([w.HANDLE,ctypes.POINTER(_Info)],w.BOOL),
            'GetFileType':([w.HANDLE],w.DWORD),
            'SetFilePointerEx':([w.HANDLE,ctypes.c_int64,ctypes.c_void_p,w.DWORD],w.BOOL),
            'ReadFile':([w.HANDLE,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.c_void_p],w.BOOL),
            'WriteFile':([w.HANDLE,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.c_void_p],w.BOOL),
            'FlushFileBuffers':([w.HANDLE],w.BOOL),
            'SetFileInformationByHandle':([w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD],w.BOOL),
            'CloseHandle':([w.HANDLE],w.BOOL)}
        for name,(args,result) in signatures.items():
            function=getattr(self.api,name);function.argtypes=args;function.restype=result

    def check(self,value,operation):
        if not value:
            error=ctypes.WinError(ctypes.get_last_error());error.add_note('E_READY_NATIVE_OPERATION: '+operation)
            error.ready_operation=operation;raise error
        return value

    def open(self,path,access=READ,share=7,creation=3):
        path=Path(path).absolute()
        _ordinary(path.parent if creation==1 else path)
        handle=self.api.CreateFileW(str(path),access,share,None,creation,0x200080,None)
        if handle==INVALID:
            error=ctypes.WinError(ctypes.get_last_error());error.add_note('E_READY_NATIVE_OPERATION: CreateFileW; access='+hex(access)+'; path='+str(path))
            error.ready_operation='CreateFileW';raise error
        self.handles.add(handle);return handle

    def open_read(self,path):return self.open(path,READ,7,3)

    def info(self,handle):
        value=_Info();self.check(self.api.GetFileInformationByHandle(handle,ctypes.byref(value)),'GetFileInformationByHandle')
        require(self.api.GetFileType(handle)==1 and not value.attributes&0x410 and value.links==1,'FILE_TYPE')
        return {'identity':[value.volume,(value.index_high<<32)|value.index_low],
            'size':(value.size_high<<32)|value.size_low,'links':value.links,
            'attributes':value.attributes,'written':(value.written.dwHighDateTime<<32)|value.written.dwLowDateTime}

    def read(self,handle,limit,*,stable=True):
        before=self.info(handle);require(before['size']<=limit,'SIZE')
        self.check(self.api.SetFilePointerEx(handle,0,None,0),'SetFilePointerEx.read')
        data=bytearray()
        while len(data)<before['size']:
            size=before['size']-len(data);buffer=ctypes.create_string_buffer(size);got=w.DWORD()
            self.check(self.api.ReadFile(handle,buffer,size,ctypes.byref(got),None),'ReadFile')
            require(0<got.value<=size,'SHORT_READ');data.extend(buffer.raw[:got.value])
        after=self.info(handle)
        require(before==after if stable else before['identity']==after['identity'],'FILE_CHANGED')
        return bytes(data)

    def write(self,handle,raw,offset):
        self.check(self.api.SetFilePointerEx(handle,offset,None,0),'SetFilePointerEx.write');sent=0
        while sent<len(raw):
            block=ctypes.create_string_buffer(raw[sent:],len(raw)-sent);written=w.DWORD()
            self.check(self.api.WriteFile(handle,block,len(raw)-sent,ctypes.byref(written),None),'WriteFile')
            require(0<written.value<=len(raw)-sent,'SHORT_WRITE');sent+=written.value
        self.check(self.api.FlushFileBuffers(handle),'FlushFileBuffers')

    def close(self,handle):
        if handle in self.handles:
            self.check(self.api.CloseHandle(handle),'CloseHandle');self.handles.remove(handle)

    def close_all(self,original=None):
        first=original
        for handle in tuple(self.handles):
            try:self.close(handle)
            except Exception as error:
                if first is None:first=error
                else:first.add_note('E_READY_CLOSE: '+repr(error))
        if self.handles and first is not None:first.owned_ready_native=self
        if first is not None and original is None:raise first


def _read_file(path,limit=16384):
    native=NativeFiles()
    try:raw=native.read(native.open_read(path),limit)
    except BaseException as error:native.close_all(error);raise
    native.close_all();return raw


def default_root():
    """Resolve the user's physical cache without Store redirection or env guesses."""
    class GUID(ctypes.Structure):
        _fields_=[('a',ctypes.c_uint32),('b',ctypes.c_uint16),('c',ctypes.c_uint16),('d',ctypes.c_ubyte*8)]
    shell=ctypes.WinDLL('shell32',use_last_error=True);ole=ctypes.WinDLL('ole32',use_last_error=True)
    ole.CoInitializeEx.argtypes=[ctypes.c_void_p,w.DWORD];ole.CoInitializeEx.restype=ctypes.c_long
    ole.CoTaskMemFree.argtypes=[ctypes.c_void_p];ole.CoTaskMemFree.restype=None
    ole.CoUninitialize.argtypes=[];ole.CoUninitialize.restype=None
    shell.SHGetKnownFolderPath.argtypes=[ctypes.POINTER(GUID),w.DWORD,w.HANDLE,ctypes.POINTER(w.LPWSTR)]
    shell.SHGetKnownFolderPath.restype=ctypes.c_long
    result=ole.CoInitializeEx(None,2);require(result in (0,1,-2147417850),'COM_INITIALIZATION')
    initialized=result in (0,1)
    pointer=w.LPWSTR()
    try:
        ident=GUID.from_buffer_copy(uuid.UUID('F1B32785-6FBA-4FCF-9D55-7B8E7F157091').bytes_le)
        result=shell.SHGetKnownFolderPath(ctypes.byref(ident),0x10000,None,ctypes.byref(pointer))
        require(result==0 and bool(pointer),'KNOWN_FOLDER')
        return Path(pointer.value)/'MemoryIntegrity/ready-copies-v1'
    finally:
        if pointer:ole.CoTaskMemFree(ctypes.cast(pointer,ctypes.c_void_p))
        if initialized:ole.CoUninitialize()


def _root_id(root):
    info=_ordinary(root).stat();return [info.st_dev,info.st_ino]


def _save(path,value):
    path=Path(path);_ordinary(path.parent)
    if os.path.lexists(path):require(_ordinary(path).is_file() and path.stat().st_nlink==1,'METADATA_TYPE')
    temporary=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    with temporary.open('xb') as stream:
        stream.write((json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode());stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def _check_root(root,*,create=False):
    root=Path(root).absolute();require(root.name=='ready-copies-v1' and root.drive and not root.drive.startswith('\\'),'ROOT_SCOPE')
    existed=root.exists()
    if create:_mkdir(root)
    _ordinary(root);marker=root/'.owner.json'
    if create and not marker.exists():
        require(not existed or not any(root.iterdir()),'UNMANAGED_ROOT')
        _save(marker,{'scope':SCOPE,'root':_norm(root),'identity':_root_id(root)})
    value=_json(_read_file(marker))
    require(value=={'scope':SCOPE,'root':_norm(root),'identity':_root_id(root)},'UNMANAGED_ROOT')
    return root


def _token(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
def _payload(raw,token):
    require(len(raw)<=LIMIT,'READY_SIZE');value=_json(raw)
    require(isinstance(value,dict) and value.get('token')==token,'READY_TOKEN')
    return value


def publish(info,raw,publish_original):
    """Fill only the parent's existing file; commit LAST after original publish."""
    require(isinstance(info,dict) and set(info)=={'scope','root','copy','source','token','identity'} and info['scope']==SCOPE and _token(info['token']),'CONTRACT')
    root=_check_root(info['root']);path=root/('ready-'+info['token']+'.copy')
    require(_norm(path)==info['copy'] and Path(info['source']).is_absolute() and type(raw) is bytes and len(raw)<=LIMIT,'CONTRACT')
    native=NativeFiles()
    try:
        handle=native.open(path,WRITE|0x80,7,3);before=native.info(handle)
        require(before['identity']==info['identity'] and before['size']==0,'COPY_IDENTITY')
        native.write(handle,struct.pack('<I',len(raw))+hashlib.sha256(raw).digest()+raw,8)
        publish_original()
        require(native.info(handle)['identity']==info['identity'],'COPY_IDENTITY')
        native.write(handle,MAGIC,0)
    except BaseException as error:native.close_all(error);raise
    native.close_all()


def _schedule(root,meta_path,meta):
    day=datetime.fromisoformat(meta['expires_utc']).date().isoformat()
    folder=_mkdir(root/'.expiry-queue'/day)
    pointer=folder/('ready-'+meta['token']+'.pending.json')
    require(not os.path.lexists(pointer),'QUEUE_COLLISION')
    _save(pointer,{'scope':SCOPE,'token':meta['token'],'receipt':_norm(meta_path),
        'receipt_sha256':sha(_read_file(meta_path))})


def _quarantine(root,path,observation):
    """Persist causes/outcomes, then move only a checked cache queue object."""
    try:
        path=_ordinary(path)
        require(path.resolve().is_relative_to(root.resolve()/'.expiry-queue'),'QUEUE_ARCHIVE_PATH')
        info=path.stat()
        require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) and info.st_nlink==1,'QUEUE_ARCHIVE_TYPE')
        audit=_mkdir(root/'.expiry-audit');event=audit/(uuid.uuid4().hex+'.audit.json')
        _save(event,dict(observation,scope=SCOPE,queue=str(path),utc=_now().isoformat()))
        path.rename(event.with_suffix('.retained'))  # Originals/receipts never enter this queue.
    except Exception as error:
        error.add_note('E_READY_COPY_QUEUE_QUARANTINE_FAILED: '+str(path))
        error.owned_ready_queue_unsafe=True
        raise


class ReadyCopy:
    def __init__(self,source,token,*,root=None):
        require(_token(token),'TOKEN');self.token=token;self.source=Path(source).absolute()
        require(self.source.name=='owned-bootstrap-'+token+'.ready.json','SOURCE_NAME')
        self.root=_check_root(default_root() if root is None else root,create=True)
        self.cleanup_observation=cleanup(self.root)
        self.copy_path=self.root/('ready-'+token+'.copy');self.meta_path=self.root/('ready-'+token+'.receipt.json')
        require(not os.path.lexists(self.copy_path) and not os.path.lexists(self.meta_path),'COLLISION')
        self.native=NativeFiles();self.handle=None;self.observation={};self.raw=None;self._accepted=None;self._finished=False
        try:
            creator=self.native.open(self.copy_path,WRITE|0x80,7,1);self.identity=self.native.info(creator)['identity'];self.native.close(creator)
            self.handle=self.native.open_read(self.copy_path)
            path_info=self.copy_path.stat();self.path_identity=[path_info.st_dev,path_info.st_ino]
            self.meta={'scope':SCOPE,'token':token,'root':_norm(self.root),'root_identity':_root_id(self.root),
                'copy':_norm(self.copy_path),'source':_norm(self.source),'identity':self.identity,
                'created_utc':_now().isoformat(),'read_completed_utc':None,'exit_proved_utc':None,'expires_utc':None,
                'startup_completed':False,'native_exit_proved':False,'frame_sha256':None,'payload_sha256':None,'deleted':False}
            _save(self.meta_path,self.meta)
        except BaseException as error:
            self.native.close_all(error)
            if self.native.handles:error.owned_ready_copy_debt=self
            raise

    def contract(self):
        return {'scope':SCOPE,'root':str(self.root),'copy':_norm(self.copy_path),'source':str(self.source),
            'token':self.token,'identity':self.identity}

    def _frame(self):
        raw=self.native.read(self.handle,FRAME_LIMIT,stable=False)
        if not raw.startswith(MAGIC):return None
        require(len(raw)>=44,'FRAME_SIZE');size=struct.unpack('<I',raw[8:12])[0]
        require(size<=LIMIT and len(raw)==44+size,'FRAME_SIZE');payload=raw[44:]
        require(hashlib.sha256(payload).digest()==raw[12:44],'FRAME_HASH')
        require(self.native.info(self.handle)['identity']==self.identity,'COPY_IDENTITY')
        info=_ordinary(self.copy_path).stat()
        require(info.st_nlink==1,'FILE_TYPE')
        require([info.st_dev,info.st_ino]==self.path_identity,'COPY_PATH_CHANGED')
        self.frame_sha256=sha(raw);return payload

    def ready(self):return self._frame() is not None

    def read_ready(self):
        started=time.monotonic()
        backup=self._frame();require(backup is not None,'UNCOMMITTED')
        copy_seconds=time.monotonic()-started;source_started=time.monotonic()
        native_error=None
        try:raw=_read_file(self.source,LIMIT)
        except OSError as error:
            if getattr(error,'winerror',None) not in (5,32) or getattr(error,'owned_ready_native',None) is not None:raise
            native_error=error;raw=backup
        value=_payload(raw,self.token);_payload(backup,self.token)
        require(raw==backup,'SOURCE_COPY_HASH_CHANGED')
        self.raw=raw;self.observation={'mode':'DIRECT_READ_ONLY' if native_error is None else 'VERIFIED_PARENT_COPY',
            'source_winerror':None if native_error is None else native_error.winerror,'source':str(self.source),
            'source_error':None if native_error is None else {'type':type(native_error).__name__,
                'message':str(native_error),'operation':getattr(native_error,'ready_operation',None),
                'notes':list(getattr(native_error,'__notes__',[]))},
            'copy':str(self.copy_path),'copy_sha256':sha(raw),'copy_identity':self.identity,
            'copy_read_seconds':copy_seconds,'source_read_seconds':time.monotonic()-source_started,
            'elapsed_seconds':time.monotonic()-started,'producer_authentication':False}
        return raw

    def accept(self,observed,*,now=None):
        require(self.raw is not None and _payload(self.raw,self.token)==observed,'ACCEPT_UNREAD')
        self._accepted=_now(now);self.meta['read_completed_utc']=self._accepted.isoformat()
        self.meta.update(frame_sha256=self.frame_sha256,payload_sha256=sha(self.raw));_save(self.meta_path,self.meta)

    def close(self):
        self.native.close_all()
        if not self.native.handles:self.handle=None

    def finish(self,*,native_exit_proved,startup_completed,release_complete=True,now=None):
        self.close()
        if self._finished:return
        if native_exit_proved is not True or startup_completed is not True or release_complete is not True or self._accepted is None:return
        exited=_now(now);require(exited>=self._accepted,'EXIT_TIME')
        self.meta.update(native_exit_proved=True,startup_completed=True,exit_proved_utc=exited.isoformat(),
            expires_utc=(max(self._accepted,exited)+timedelta(days=RETENTION_DAYS)).isoformat())
        _save(self.meta_path,self.meta)
        _schedule(self.root,self.meta_path,self.meta);self._finished=True


def _expire(root,pointer,day,now,result):
    queued=_json(_read_file(pointer));token=queued.get('token')
    require(set(queued)=={'scope','token','receipt','receipt_sha256'} and queued['scope']==SCOPE and
        _token(token) and pointer.name=='ready-'+token+'.pending.json','QUEUE_SCOPE')
    meta_path=root/('ready-'+token+'.receipt.json')
    require(queued['receipt']==_norm(meta_path),'QUEUE_PATH')
    raw_meta=_read_file(meta_path);require(sha(raw_meta)==queued['receipt_sha256'],'QUEUE_RECEIPT_CHANGED')
    meta=_json(raw_meta)
    require(meta.get('token')==token and meta.get('scope')==SCOPE and meta.get('root')==_norm(root) and
        meta.get('root_identity')==_root_id(root),'RETENTION_SCOPE')
    path=root/('ready-'+token+'.copy');require(meta.get('copy')==_norm(path),'RETENTION_PATH')
    require(meta.get('native_exit_proved') is True and meta.get('startup_completed') is True and
        bool(meta.get('read_completed_utc')) and meta.get('deleted') is False,'RETENTION_ACCEPTANCE')
    read,exited,expires=(_now(datetime.fromisoformat(meta[key])) for key in ('read_completed_utc','exit_proved_utc','expires_utc'))
    require(expires==max(read,exited)+timedelta(days=RETENTION_DAYS) and expires.date().isoformat()==day,'RETENTION_TIME')
    if now<expires:return False
    native=NativeFiles()
    try:
        # Exclusive open proves there is no other data reader/writer whose
        # handle could keep a delete-pending payload alive after our close.
        handle=native.open(path,READ|0x10000,0,3);info=native.info(handle)
        require(info['identity']==meta['identity'],'RETENTION_IDENTITY')
        raw=native.read(handle,FRAME_LIMIT)
        require(sha(raw)==meta.get('frame_sha256'),'RETENTION_HASH')
        require(raw.startswith(MAGIC) and len(raw)>=44 and len(raw)==44+struct.unpack('<I',raw[8:12])[0] and
            hashlib.sha256(raw[44:]).digest()==raw[12:44] and sha(raw[44:])==meta.get('payload_sha256'),'RETENTION_HASH')
        _payload(raw[44:],token);require(native.info(handle)==info,'RETENTION_CHANGED')
        # Reserve the deletion slot BEFORE marking. Even a close/persistence
        # fault cannot let this invocation attempt more than its fixed bound.
        result['deletion_attempts']+=1
        audit=_mkdir(root/'.expiry-audit')
        _save(audit/(uuid.uuid4().hex+'.intent.json'),{'scope':SCOPE,'state':'DELETE_INTENT',
            'copy':str(path),'receipt':str(meta_path),'identity':info['identity'],
            'frame_sha256':sha(raw),'utc':now.isoformat()})
        disposition=_Disposition(1)
        native.check(native.api.SetFileInformationByHandle(handle,4,ctypes.byref(disposition),ctypes.sizeof(disposition)),'SetFileInformationByHandle.expire')
        native.close(handle)
        result['deleted'].append(str(path))  # Actual removal precedes metadata I/O.
        meta['deleted']=True;meta['deleted_utc']=now.isoformat();_save(meta_path,meta)
    except BaseException as error:native.close_all(error);raise
    native.close_all();return True


def cleanup(root,*,now=None,maximum=64,scan_limit=128,budget_seconds=.1):
    """Bound cooperative housekeeping; receipts are never a scan/deletion queue.

    Only completed startups schedule new queue pointers. Consumed pointers MOVE
    to the retained audit directory, including failures (copies stay on error).
    Permanent receipts/failed unaccepted copies are never rescanned or removed.
    Native filesystem calls cannot be preempted by this cooperative time budget.
    """
    root=_check_root(root);now=_now(now);started=time.monotonic()
    require(type(maximum) is int and maximum>0 and type(scan_limit) is int and scan_limit>0 and
        type(budget_seconds) in (int,float) and 0<budget_seconds<=1,'CLEANUP_LIMIT')
    result={'deleted':[],'errors':[],'retention_days':RETENTION_DAYS,'deletion_attempts':0,'scanned':0,'bounded':False}
    queue=root/'.expiry-queue'
    if not queue.exists():return result
    _ordinary(queue)
    def limited():
        return result['scanned']>=scan_limit or result['deletion_attempts']>=maximum or time.monotonic()-started>=budget_seconds
    with os.scandir(queue) as days:
        for entry in days:
            if limited():result['bounded']=True;break
            result['scanned']+=1;folder=Path(entry.path)
            try:
                try:_ordinary(folder)
                except Exception as error:
                    error.owned_ready_queue_unsafe=True;raise
                try:
                    require(entry.is_dir(follow_symlinks=False) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',entry.name),'QUEUE_DAY')
                    day=datetime.fromisoformat(entry.name).date()
                    require(day<=now.date()+timedelta(days=RETENTION_DAYS),'QUEUE_FUTURE_DAY')
                except ValueError as error:
                    row={'metadata':str(folder),'error':repr(error)};result['errors'].append(row)
                    _quarantine(root,folder,{'state':'INVALID_QUEUE_DAY','errors':[row],'deleted':[]});continue
                if day>now.date():continue
                with os.scandir(folder) as pending:
                    for item in pending:
                        if limited():result['bounded']=True;break
                        result['scanned']+=1
                        if not re.fullmatch(r'ready-[0-9a-f]{64}\.pending\.json',item.name):
                            row={'metadata':item.path,'error':'E_READY_COPY_INVALID_OR_INTERRUPTED_QUEUE_ENTRY'}
                            result['errors'].append(row)
                            _quarantine(root,Path(item.path),{'state':'INVALID_QUEUE_ENTRY','errors':[row],'deleted':[]});continue
                        pointer=Path(item.path);consumed=False
                        deleted_before=len(result['deleted']);errors_before=len(result['errors'])
                        try:consumed=_expire(root,pointer,entry.name,now,result)
                        except Exception as error:
                            if getattr(error,'owned_ready_native',None) is not None:raise
                            consumed=True
                            result['errors'].append({'metadata':str(pointer),'error':repr(error),'notes':list(getattr(error,'__notes__',[]))})
                        if consumed:
                            # Preserve queue metadata, including a failed removal.
                            # No blind retry of locked/changed data at every start.
                            _quarantine(root,pointer,{'state':'QUEUE_CONSUMED',
                                'deleted':result['deleted'][deleted_before:],
                                'errors':result['errors'][errors_before:],
                                'deletion_attempts':result['deletion_attempts']})
                try:folder.rmdir()  # Only a NEW empty queue day, never evidence.
                except OSError as error:
                    if getattr(error,'winerror',None) not in (145,2,3):raise
            except Exception as error:
                # An active queue directory we cannot inspect/retire cannot be
                # silently deferred forever. Preserve the actual OS error.
                error.add_note('E_READY_COPY_ACTIVE_QUEUE: '+str(folder))
                error.owned_ready_queue_unsafe=True
                raise
    result['elapsed_seconds']=time.monotonic()-started
    return result
