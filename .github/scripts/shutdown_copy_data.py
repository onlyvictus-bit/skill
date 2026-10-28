"""SR3-COPY multi-root envelope over checked immutable no-ACL DATA primitives."""
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import types

SCOPE = 'SR3_COPY_DATA_V1'
PINNED_PRIMITIVES = {
    'archive_copy_snapshot.py': '77c9806674b858cae0d04c459c65a5848c63d7b47a40e1d66d695a88e9ef5e04',
    'archive_copy_h1.py': '8e66fa51dd7fde1f21d50353e67791a58d8803ea782288d203468e1012571780',
    'gate1_validation.py': 'f9b7ef54039756b3d8a95051b05a93e920518c970e6deb1c987bc5bb0aeed22e',
}
_CACHE = None

def _primitives():
    global _CACHE
    if _CACHE is not None: return _CACHE
    here = Path(__file__).absolute().parent; source = {}
    for name, expected in PINNED_PRIMITIVES.items():
        raw = (here / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected: raise ValueError('E_SR3_COPY_PRIMITIVE_HASH')
        source[name] = raw
    saved = {name: sys.modules.get(name) for name in ('gate1_validation', 'archive_copy_snapshot')}
    try:
        gate = types.ModuleType('gate1_validation'); gate.__file__ = str(here / 'gate1_validation.py'); sys.modules['gate1_validation'] = gate
        exec(compile(source['gate1_validation.py'], gate.__file__, 'exec'), gate.__dict__)
        snapshot = types.ModuleType('archive_copy_snapshot'); snapshot.__file__ = str(here / 'archive_copy_snapshot.py'); sys.modules['archive_copy_snapshot'] = snapshot
        exec(compile(source['archive_copy_snapshot.py'], snapshot.__file__, 'exec'), snapshot.__dict__)
        history = types.ModuleType('archive_copy_h1'); history.__file__ = str(here / 'archive_copy_h1.py')
        exec(compile(source['archive_copy_h1.py'], history.__file__, 'exec'), history.__dict__)
    finally:
        for name, old in saved.items():
            if old is None: sys.modules.pop(name, None)
            else: sys.modules[name] = old
    _CACHE = (snapshot, history); return _CACHE

def digest(value): return _primitives()[0].digest(value)
def identity(info): return _primitives()[0].identity(info)
def permission_digest(path): return _primitives()[1].permission_digest(path)
def record(path): return _primitives()[0].record(path)
def _require(value, code): return _primitives()[0].require(value, code)

def _label(label):
    _require(isinstance(label, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', label) is not None and
             label.upper() not in {'CON','PRN','AUX','NUL',*{'COM'+str(n) for n in range(1,10)},*{'LPT'+str(n) for n in range(1,10)}}, 'E_SR3_COPY_LABEL')

class SnapshotSet:
    def __init__(self, roots, session, policies=None):
        v,h = _primitives(); _require(isinstance(roots,dict) and roots,'E_SR3_COPY_ROOTS')
        _require(isinstance(session,str) and len(session)==32 and all(c in '0123456789abcdef' for c in session),'E_SR3_COPY_SESSION')
        _require(policies is None or isinstance(policies,dict),'E_SR3_COPY_POLICIES')
        self.session,self.roots,self.contexts,self.policy_sha256 = session,{}, {}, {}
        _require(len({label.casefold() for label in roots}) == len(roots), 'E_SR3_COPY_LABEL')
        for label,source in roots.items():
            _label(label); root=v.ordinary(Path(source).absolute()); _require(root.is_dir() and label not in self.roots,'E_SR3_COPY_ROOT')
            policy=None if policies is None else policies.get(label)
            if policy in (None,{}): policy={'scope':h.SCOPE,'root':str(root),'allowed':{},'protected_identities':[]}
            context=h.Context(policy); _require(context.root==root,'E_SR3_COPY_POLICY')
            self.roots[label],self.contexts[label],self.policy_sha256[label]=root,context,v.digest(policy)
        _require(policies is None or set(policies)==set(self.roots),'E_SR3_COPY_POLICIES')
        values=list(self.roots.values())
        for index,root in enumerate(values):
            _require(all(root != other and not root.is_relative_to(other) and not other.is_relative_to(root) for other in values[:index]),'E_SR3_COPY_ROOT_OVERLAP')

    @staticmethod
    def _raw(entry):
        raw=dict(entry); raw.pop('policy_sha256',None); return raw

    def _validate(self, request):
        v,_=_primitives(); _require(isinstance(request,dict) and set(request)=={'scope','session','phase','binding','roots','producer_authentication'} and
            request['scope']==SCOPE and request['session']==self.session and request['phase'] in ('BEFORE','AFTER') and request['producer_authentication'] is False and set(request['roots'])==set(self.roots),'E_SR3_COPY_REQUEST')
        if request['phase']=='BEFORE': _require(request['binding'] is None,'E_SR3_COPY_BINDING')
        else: _require(isinstance(request['binding'],dict) and set(request['binding'])=={'before_sha256','workload_sha256'} and all(v.hexdigest(x) for x in request['binding'].values()),'E_SR3_COPY_BINDING')
        for label,context in self.contexts.items():
            entry=request['roots'][label]; _require(isinstance(entry,dict) and entry.get('policy_sha256')==self.policy_sha256[label],'E_SR3_COPY_POLICY'); context.validate_request(self._raw(entry))
            raw=self._raw(entry); _require(raw['root']==str(self.roots[label]) and raw['session']==self.session and raw['phase']==request['phase'], 'E_SR3_COPY_REQUEST')
            if request['phase']=='AFTER': _require(raw['binding']['workload_sha256']==request['binding']['workload_sha256'], 'E_SR3_COPY_BINDING')

    def _validate_before_bundle(self, bundle):
        _require(isinstance(bundle,dict) and bundle.get('scope')==SCOPE and bundle.get('session')==self.session and
            bundle.get('phase')=='BEFORE' and set(bundle.get('roots',{}))==set(self.roots) and bundle.get('producer_authentication') is False,
            'E_SR3_COPY_BUNDLE')
        for label,context in self.contexts.items():
            entry=bundle['roots'][label]; _require(isinstance(entry,dict) and entry.get('policy_sha256')==self.policy_sha256[label], 'E_SR3_COPY_POLICY')
            raw=self._raw(entry); context.validate_context(raw); context.validate_objects(raw['objects']); _require(raw['root']==str(self.roots[label]) and raw['session']==self.session and raw['phase']=='BEFORE', 'E_SR3_COPY_BUNDLE')

    def scan(self, phase, binding=None):
        v,_=_primitives(); _require(phase in ('BEFORE','AFTER'),'E_SR3_COPY_PHASE')
        if phase=='BEFORE': _require(binding is None,'E_SR3_COPY_BINDING'); before=None; outer=None
        else:
            _require(isinstance(binding,dict) and set(binding)=={'before','workload_sha256'} and v.hexdigest(binding['workload_sha256']),'E_SR3_COPY_BINDING')
            before=binding['before']; self._validate_before_bundle(before); outer={'before_sha256':v.digest(before),'workload_sha256':binding['workload_sha256']}
        roots={}
        for label,context in self.contexts.items():
            raw_binding=None if phase=='BEFORE' else {'before_sha256':v.digest(self._raw(before['roots'][label])),'workload_sha256':binding['workload_sha256']}
            roots[label]={**context.scan(self.roots[label],self.session,phase,raw_binding),'policy_sha256':self.policy_sha256[label]}
        result={'scope':SCOPE,'session':self.session,'phase':phase,'binding':outer,'roots':roots,'producer_authentication':False}; self._validate(result); return result

    def copy_denied(self, request, output):
        v,_=_primitives(); self._validate(request); output=Path(output).absolute(); v.ordinary(output.parent)
        _require(all(not output.is_relative_to(root) and not root.is_relative_to(output) for root in self.roots.values()),'E_COPY_OUTPUT_SCOPE')
        output.mkdir(); roots={}
        for label,context in self.contexts.items():
            folder=output/label; context.copy_denied(self._raw(request['roots'][label]),folder); roots[label]=v.record(folder/'Copies.json')
        result={'scope':SCOPE,'session':self.session,'phase':request['phase'],'request_sha256':v.digest(request),'roots':roots,'producer_authentication':False}; v.save(output/'Copies.json',result); return result

    def _copies(self,request,output,copies_sha):
        v,_=_primitives(); self._validate(request); output=v.ordinary(Path(output)); copies=v.load(output/'Copies.json',copies_sha)
        _require(isinstance(copies,dict) and set(copies)=={'scope','session','phase','request_sha256','roots','producer_authentication'} and copies['scope']==SCOPE and copies['session']==self.session and copies['phase']==request['phase'] and copies['request_sha256']==v.digest(request) and copies['producer_authentication'] is False and set(copies['roots'])==set(self.roots),'E_SR3_COPY_BINDING')
        for label in self.roots: _require(v.record(output/label/'Copies.json')==copies['roots'][label],'E_SR3_COPY_BINDING')
        return copies

    def verify_readable(self,request):
        self._validate(request); result={}
        for label,context in self.contexts.items():
            objects,unresolved=context.collect(self.roots[label],True); raw=self._raw(request['roots'][label]); _require(objects==raw['objects'] and unresolved==raw['unresolved'],'E_SR3_COPY_VISIBILITY_CHANGED'); result[label]={'objects':objects,'unresolved':unresolved}
        return result

    def inspect_denied_policies(self, request, protected_identities):
        """Read only the exact unresolved data; return an unapproved H1 policy proposal."""
        v,h=_primitives(); self._validate(request); _require(request['phase']=='BEFORE','E_SR3_COPY_POLICY_PHASE')
        _require(isinstance(protected_identities,list) and all(isinstance(row,list) and len(row)==2 and all(type(item) is int and item>0 for item in row) for row in protected_identities),'E_SR3_COPY_PROTECTED')
        _require(len({tuple(row) for row in protected_identities})==len(protected_identities),'E_SR3_COPY_PROTECTED')
        protected=sorted(protected_identities); policies={}
        for label,root in self.roots.items():
            raw=self._raw(request['roots'][label]); allowed={}
            def visit(path,name):
                path=v.ordinary(path); info=path.stat()
                if stat.S_ISDIR(info.st_mode):
                    names=sorted(entry.name for entry in os.scandir(path))
                    _require(len({child.casefold() for child in names})==len(names),'E_SR3_COPY_COVERAGE_ALIAS')
                    before=(info.st_dev,info.st_ino)
                    for child in names: visit(path/child, v.relative(child if name=='.' else name+'/'+child))
                    _require(names==sorted(entry.name for entry in os.scandir(path)) and before==(v.ordinary(path).stat().st_dev,path.stat().st_ino),'E_SR3_COPY_DIRECTORY_CHANGED')
                    return
                _require(stat.S_ISREG(info.st_mode),'E_COPY_FILE_TYPE')
                first=h._read_regular(path); second=h._read_regular(path)
                _require(first==second,'E_SR3_COPY_READ_CHANGED')
                if first['identity'][2]>1:
                    _require('retained-temp' in Path(name).parts,'E_H1_LINK_SCOPE')
                    _require(first['identity'][:2] not in protected,'E_H1_TRUSTED_LINK')
                    allowed[name]={'role':h.ROLE,**{key:first[key] for key in ('identity','size','sha256','permission_sha256')}}
            for target in raw['unresolved']:
                visit(root if target=='.' else root/target,target)
            policy={'scope':h.SCOPE,'root':str(root),'allowed':dict(sorted(allowed.items())),'protected_identities':protected}
            h.Context(policy)  # Exact existing policy validator, no automatic authorization.
            policies[label]=policy
        return {'scope':'SR3_COPY_POLICY_PROPOSAL_V1','session':self.session,'request_sha256':v.digest(request),
                'roots':policies,'origin':'CURRENT_REQUESTED_HISTORICAL_DATA_READ_NOT_AUTHENTICATED',
                'producer_authentication':False,'policy_approved':False}

    def merge(self,request,output,copies_sha):
        v,_=_primitives(); copies=self._copies(request,output,copies_sha); self.verify_readable(request); roots={}
        for label,context in self.contexts.items(): roots[label]={**context.merge(self._raw(request['roots'][label]),Path(output)/label,copies['roots'][label]['sha256']),'policy_sha256':self.policy_sha256[label]}
        return {'scope':SCOPE,'session':self.session,'phase':request['phase'],'binding':request['binding'],'request_sha256':v.digest(request),'copies_sha256':copies_sha,'roots':roots,'producer_authentication':False,'status':'COMPLETE_'+request['phase']+'_SAMPLE_NOT_WORKLOAD_QUALIFICATION'}

    def verify_bundle(self,bundle,request,output,copies_sha):
        fresh=self.merge(request,output,copies_sha); _require(bundle==fresh,'E_SR3_COPY_BUNDLE_CHANGED'); return fresh

    def file_manifests(self,bundle):
        _require(isinstance(bundle,dict) and bundle.get('scope')==SCOPE and set(bundle.get('roots',{}))==set(self.roots),'E_SR3_COPY_BUNDLE')
        for label,entry in bundle['roots'].items(): _require(entry.get('root')==str(self.roots[label]), 'E_SR3_COPY_BUNDLE')
        return {entry['root']:{name:row['sha256'] for name,row in entry['objects'].items() if row['kind']=='file'} for entry in bundle['roots'].values()}

    def compare(self,before,after):
        v,_=_primitives(); _require(before.get('phase')=='BEFORE' and after.get('phase')=='AFTER' and before.get('scope')==after.get('scope')==SCOPE and before.get('session')==after.get('session')==self.session and set(before.get('roots',{}))==set(after.get('roots',{}))==set(self.roots),'E_SR3_COPY_PHASE')
        _require(after.get('binding')=={'before_sha256':v.digest(before),'workload_sha256':after.get('binding',{}).get('workload_sha256')} and v.hexdigest(after['binding']['workload_sha256']),'E_SR3_COPY_BINDING')
        for label,context in self.contexts.items():
            early,late=self._raw(before['roots'][label]),self._raw(after['roots'][label])
            _require(early['root']==late['root']==str(self.roots[label]) and early['session']==late['session']==self.session and early['phase']=='BEFORE' and late['phase']=='AFTER' and late['binding']['workload_sha256']==after['binding']['workload_sha256'], 'E_SR3_COPY_BINDING')
            context.compare(early,late)
        return {'status':'CONTENT_MATCH_AT_BEFORE_AFTER_SAMPLES','producer_authentication':False,'whole_skill_ready':False,'continuous_immutability_proven':False}
