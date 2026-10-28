"""SC: staged no-ACL SR3 evidence copies. Old attempts/code remain immutable.

Copied history is inert data. Authoritative checks remain direct. Runtime output
is provisional until a separate fresh-original AFTER and raw-result review.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace, FunctionType
import traceback

REPO=Path(__file__).absolute().parents[2]
ROOT=Path(r'C:\Users\sakth\Documents\Codex\sr3-copy-20261027-4a52cd8d')
SESSION='4a52cd8d336b40c29587dfb5ece35522'
SCOPE='SR3_COPY_STAGED_NO_ACL_V1'
SCRIPTS=REPO/'.github/scripts'
SR3_SHA='f224d215d0eb8ac898ac6a185cb388d1aa45b627765a006ae266455b800aff69'
DATA_SHA='4fa0afdaa1219b243421717eca9a8d2939c4f653a8d9b27110e2b63c80e27299'
CHECKOUT_HEAD='f63f62496f82fb479e352bdd9c90accf9f869e8b'
CHECKOUT_ADDITIONS={
    '.github/scripts/Run-Gate1-Current-Source.ps1':'712dd7cd96d70121d89d77fcbf72671e6311cd0ec4d106d4785e7e3d152b83a8',
    '.github/scripts/gate1_current_preflight.py':'5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861',
    '.github/tests/test_gate1_current_preflight.py':'fcd3ca27163aee7e68e52ba61168a022e2a29485d743c39e89daae0b25391a4e',
    'docs/fable/evidence/offline-first-20261020/gate1-current-source-20261023.md':'18bcb5cb8d8a505d6482e68defa5913e3a681ca9c14964252b3ba160b9475a25'}
ROOTS={name:REPO/'.github/run-artifacts'/name for name in (
    'cleanup-repair-20261023','cleanup-process-timing-20261024',
    'cleanup-lifetime-stack-20261024','cleanup-membership-20261025')}
CONSUMED={
    'sr3-prepare/Failure.json':'779800f964182b9a68a10f67299160151a5e03507cbe18a0c4e06ea4549d4c48',
    'sr3-prepare/Claim.json':'b47f548be8ed3cba3a7e50efc4c5b564b1073002b6e72faa2a987046410d173f'}
MODES=('Before','InspectBefore','BindPolicy','CopyBefore','VerifyBefore','Run','After','CopyAfter','Finalize')
_ACTIVE_CLAIM=None


def require(value,code):
    if not value: raise ValueError(code)


def load_checked(path,digest):
    path=Path(path)
    for part in (path,*path.parents):
        require(not part.is_symlink() and not getattr(part,'is_junction',lambda:False)(),'E_SC_REDIRECT')
    require(path.stat().st_nlink==1,'E_SC_CODE_LINK')
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'E_SC_CODE_SEAL: '+str(path))
    spec=importlib.util.spec_from_file_location('sc_'+path.stem,path)
    module=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def sr3(): return load_checked(SCRIPTS/'shutdown_repair_verification.py',SR3_SHA)


def data(): return load_checked(SCRIPTS/'shutdown_copy_data.py',DATA_SHA)


def c1_module():
    s=sr3(); path=SCRIPTS/'gate1_current_preflight.py'
    return load_checked(path,s.C1_SHA)


def normal(): c1_module().normal_account()


def record(path): return sr3().record(Path(path))


def read(path):
    def unique(pairs):
        value={}
        for key,item in pairs:
            require(key not in value,'E_SC_DUPLICATE_KEY'); value[key]=item
        return value
    raw=sr3().ordinary(Path(path)).read_bytes()
    return json.loads(raw,object_pairs_hook=unique)


def save(path,value): sr3().save(Path(path),value)


def claim(mode):
    global _ACTIVE_CLAIM
    require(mode in MODES,'E_SC_PHASE')
    path=ROOT/(mode+'-Claim.json')
    require(not os.path.lexists(path),'E_SC_PHASE_CONSUMED')
    save(path,{'scope':SCOPE,'session':SESSION,'mode':mode,'started_utc':datetime.now(timezone.utc).isoformat()})
    _ACTIVE_CLAIM=mode


def validate_arguments(mode,config_sha,input_sha,before_sha):
    def sealed(value):
        return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    require(mode in MODES,'E_SC_PHASE')
    require((mode=='Before' and config_sha is None and input_sha is None and before_sha is None) or
            (mode!='Before' and sealed(config_sha) and
             (sealed(input_sha) if mode in ('InspectBefore','BindPolicy','CopyBefore','VerifyBefore','CopyAfter','Finalize') else input_sha is None) and
             (sealed(before_sha) if mode in ('Run','After','Finalize') else before_sha is None)),
            'E_SC_REQUIRED_SEALS')


def history_ast(adapt=False):
    """Reuse the exact pinned guard; alter ONLY two named DATA observations."""
    load_checked(SCRIPTS/'shutdown_repair_verification.py',SR3_SHA)
    tree=ast.parse((SCRIPTS/'shutdown_repair_verification.py').read_bytes())
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='history']
    require(len(functions)==1,'E_SC_HISTORY_SHAPE')
    function=functions[0]
    if adapt:
        changed=[0,0]
        class Adapt(ast.NodeTransformer):
            def visit_Assign(self,node):
                if (len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
                        and node.targets[0].id=='rows'):
                    require(ast.unparse(node.value)=='{str(root): c1.source_manifest(root) for root in HISTORY_ROOTS}',
                            'E_SC_HISTORY_SHAPE')
                    node.value=ast.parse('_evidence_manifests()',mode='eval').body; changed[0]+=1
                return self.generic_visit(node)
            def visit_Call(self,node):
                if ast.unparse(node)=="c1.source_manifest(Path(ld['failed_receipt']['path']).parent)":
                    node.func=ast.Name(id='_evidence_submanifest',ctx=ast.Load()); changed[1]+=1
                return self.generic_visit(node)
        function=Adapt().visit(function)
        require(changed==[1,1],'E_SC_HISTORY_SHAPE')
    return ast.fix_missing_locations(function)


def submanifest(path,maps):
    path=Path(path).absolute()
    matches=[(Path(root),rows) for root,rows in maps.items() if path.is_relative_to(Path(root))]
    require(len(matches)==1,'E_SC_DATA_SCOPE')
    root,rows=matches[0]; prefix=path.relative_to(root).as_posix()
    if prefix=='.': return dict(rows)
    prefix+='/'
    subset={name[len(prefix):]:digest for name,digest in rows.items() if name.startswith(prefix)}
    require(subset,'E_SC_DATA_SCOPE_EMPTY')
    return subset


def checkout_transition(c1):
    """User-approved exact checkout-only metadata transition, not a new source."""
    evaluated=sr3().HEAD
    require(c1.git('rev-parse','HEAD').decode().strip()==CHECKOUT_HEAD,'E_SC_CHECKOUT_HEAD')
    require(c1.git('rev-list','--parents','-n','1',CHECKOUT_HEAD).decode().strip().split()==
            [CHECKOUT_HEAD,evaluated],'E_SC_CHECKOUT_PARENT')
    raw=c1.git('diff-tree','--no-commit-id','--name-status','-r','-z',evaluated,CHECKOUT_HEAD)
    parts=raw.rstrip(b'\0').split(b'\0')
    require(len(parts)==2*len(CHECKOUT_ADDITIONS) and
            {tuple(parts[i:i+2]) for i in range(0,len(parts),2)}==
            {(b'A',name.encode()) for name in CHECKOUT_ADDITIONS},'E_SC_CHECKOUT_DELTA')
    entries=c1.git('ls-tree','-rz',CHECKOUT_HEAD,'--',*sorted(CHECKOUT_ADDITIONS))
    found={}
    for entry in entries.split(b'\0'):
        if not entry: continue
        meta,name=entry.split(b'\t',1); mode,kind,blob=meta.split(); name=name.decode()
        require(mode==b'100644' and kind==b'blob' and name in CHECKOUT_ADDITIONS and name not in found,
                'E_SC_CHECKOUT_MODE')
        digest=hashlib.sha256(c1.git('cat-file','blob',blob.decode())).hexdigest()
        require(digest==CHECKOUT_ADDITIONS[name] and record(REPO/name)['sha256']==digest,'E_SC_CHECKOUT_BLOB')
        found[name]=digest
    require(found==CHECKOUT_ADDITIONS,'E_SC_CHECKOUT_SET')
    return {'checkout_head':CHECKOUT_HEAD,'evaluated_source_head':evaluated,'additions':found}


def source_basis(c1):
    """Change only original source_basis's HEAD predicate; archive stays a382."""
    s=sr3(); tree=ast.parse((SCRIPTS/'shutdown_repair_verification.py').read_bytes())
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_basis']
    require(len(functions)==1,'E_SC_SOURCE_GUARD_SHAPE'); function=functions[0]
    expected="require(c1.git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_SR3_HEAD')"
    require(ast.unparse(function.body[0])==expected,'E_SC_SOURCE_GUARD_SHAPE')
    function.body[0]=ast.parse('_checkout_transition(c1)').body[0]
    namespace=dict(s.__dict__); namespace['_checkout_transition']=checkout_transition
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),
                 '<sealed-SR3-source-exact-approved-checkout-transition>','exec'),namespace)
    return namespace['source_basis'](c1)


def provisional(row,before_record):
    row['workload_status']=row['status']
    if row['status']=='SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1' and row.get('failure') is None:
        row['status']='SC_WORKLOAD_OBSERVED_PENDING_AFTER'
    row.update(preservation=False,stage_complete=False,copy_before=before_record,
               supplementary_preservation='PENDING_FRESH_ORIGINAL_AFTER',producer_authentication=False)


def final_gate(workload,sampled,observed):
    require(sampled is True and observed is True and
            workload.get('status')=='SC_WORKLOAD_OBSERVED_PENDING_AFTER' and
            workload.get('workload_status')=='SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1' and
            workload.get('failure') is None and workload.get('preservation') is False and
            all(workload.get(k) is False for k in sr3().FLAGS),'E_SC_FINAL_GATE')
    return True


def direct_authority():
    """No copy reader can replace these original code/runtime/protected checks."""
    s=sr3(); c1=c1_module(); manifest,tree=source_basis(c1)
    rows={name:s.record(REPO/name) for name in s.LIVE_DELTA}; s.validate_source_seals(rows)
    for name,digest in s.OLD_SEALS.items():
        require(s.record(REPO/name)['sha256']==digest,'E_SC_OLD_INPUT_CHANGED')
    for name,digest in CONSUMED.items():
        require(s.record(s.ROOT/name)['sha256']==digest,'E_SC_CONSUMED_CHANGED')
    cr=read(REPO/'.github/run-artifacts/cleanup-repair-20261023/Runtime-Inputs.json')
    protected=c1.protected()
    require(set(protected)==set(cr['protected']),'E_SC_PROTECTED_ROOTS')
    for root,old in cr['protected'].items():
        allowed={name.removeprefix('memory-integrity/') for name in s.LIVE_DELTA} if root==str(REPO/'memory-integrity') else set()
        s.validate_protected_delta(old,protected[root],allowed)
    c1_inventory=c1.source_manifest(c1.OUTPUT)
    require(c1_inventory==cr['c1_inventory'],'E_SC_C1_ORIGINALS')
    c1.verify_source(c1.OUTPUT/'source',cr['source'])
    require(s.record(REPO/'semantica-runtime/requirements-lock.txt')['sha256']==manifest['semantica-runtime/requirements-lock.txt'],
            'E_SC_LOCK_CHANGED')
    authority={'helper':s.record(Path(__file__).absolute()),'data':s.record(SCRIPTS/'shutdown_copy_data.py'),
            'source_manifest':manifest,'tree':tree,'live_delta':rows,'support':s.support_records(),
            'runtime':c1.fixed_inputs(),'dependencies':c1.dependency_versions(),'protected':protected,
            'consumed':dict(CONSUMED),'controller':s.record(s.CONTROLLER),
            'c1_inventory':c1_inventory,'checkout_head':CHECKOUT_HEAD,'evaluated_source_head':s.HEAD}
    identities={}
    for path in sorted(protected_paths(authority),key=str):
        info=s.ordinary(path).stat()
        require(s.stat.S_ISREG(info.st_mode),'E_SC_PROTECTED_TYPE')
        identities[str(path)]=[info.st_dev,info.st_ino]
    authority['protected_identity_paths']=identities
    authority['protected_identities']=[list(row) for row in sorted({tuple(row) for row in identities.values()})]
    return authority


def protected_paths(authority):
    """Closed derivation, never a caller-selected trusted-input omission list."""
    s=sr3(); paths={REPO/name for name in authority['source_manifest']}
    paths.update(REPO/name for name in (*s.LIVE_DELTA,*s.OLD_SEALS,*CHECKOUT_ADDITIONS))
    paths.update(s.ROOT/name for name in CONSUMED)
    paths.update(c1_module().OUTPUT/name for name in authority['c1_inventory'])
    for root,manifest in authority['protected'].items(): paths.update(Path(root)/name for name in manifest)
    paths.update(SCRIPTS/name for name in ('shutdown_copy_verification.py','shutdown_copy_data.py',
        'shutdown_repair_verification.py','Run-Shutdown-Copy.ps1',*data().PINNED_PRIMITIVES))
    def visit(value):
        if isinstance(value,dict):
            if 'path' in value: paths.add(Path(value['path']))
            for item in value.values(): visit(item)
        elif isinstance(value,list):
            for item in value: visit(item)
    visit(authority)
    return paths


def session(config_sha):
    base_path=ROOT/'Inputs.json'; base_record=record(base_path); base=read(base_path)
    value=base; bound=base_record['sha256']!=config_sha
    if bound:
        path=ROOT/'Policy-Inputs.json'
        require(record(path)['sha256']==config_sha,'E_SC_EXTERNAL_CONFIG')
        value=read(path)
        require(set(value)==set(base)|{'lineage'} and
                {k:v for k,v in value.items() if k not in ('policies','lineage')}==
                {k:v for k,v in base.items() if k!='policies'},'E_SC_POLICY_LINEAGE')
        require(value['lineage']=={'base_config':base_record,'base_request':record(ROOT/'BEFORE/Request.json'),
                'proposal':record(ROOT/'Policy-Proposal.json')},'E_SC_POLICY_LINEAGE')
        expected=validate_policy(read(ROOT/'Policy-Proposal.json'),read(ROOT/'BEFORE/Request.json'),
                                 base['authority']['protected_identities'],ROOTS)
        require(value['policies']==expected,'E_SC_POLICY_CHANGED')
    require(set(base)=={'scope','root','session','roots','authority','budgets','groups','policies'} and
            base['policies']=={},'E_SC_BASE_CONFIG')
    require(value['scope']==SCOPE and value['root']==str(ROOT) and value['session']==SESSION and
            value['roots']=={k:str(v) for k,v in ROOTS.items()},'E_SC_CONFIG')
    s=sr3(); s.validate_budgets(value['budgets']); require(value['groups']==s.group_plan(),'E_SC_GROUPS')
    require(value['authority']['helper']==record(Path(__file__).absolute()) and
            value['authority']['data']==record(SCRIPTS/'shutdown_copy_data.py'),'E_SC_COORDINATOR_CHANGED')
    snapshot=data().SnapshotSet(ROOTS,SESSION,value['policies'] if bound else None)
    snapshot.sc_policy_bound=bound
    return value,snapshot


def require_policy(value): require('lineage' in value,'E_SC_POLICY_NOT_BOUND')


def request_path(snapshot,phase):
    return ROOT/phase/('Policy-Request.json' if phase=='BEFORE' and getattr(snapshot,'sc_policy_bound',False) else 'Request.json')


def validate_policy(proposal,request,protected,roots):
    """Exact unapproved discovery becomes usable only by an externally sealed bind."""
    d=data(); strict=d.SnapshotSet(roots,SESSION); strict._validate(request)
    require(request['phase']=='BEFORE' and set(proposal)=={'scope','session','request_sha256','roots','origin',
                'producer_authentication','policy_approved'} and proposal['scope']=='SR3_COPY_POLICY_PROPOSAL_V1' and
            proposal['session']==SESSION and proposal['request_sha256']==d.digest(request) and
            proposal['origin']=='CURRENT_REQUESTED_HISTORICAL_DATA_READ_NOT_AUTHENTICATED' and
            proposal['producer_authentication'] is False and proposal['policy_approved'] is False and
            set(proposal['roots'])==set(roots),'E_SC_POLICY_CONTEXT')
    for label,policy in proposal['roots'].items():
        require(policy.get('root')==str(roots[label]) and policy.get('protected_identities')==sorted(protected),
                'E_SC_POLICY_PROTECTED')
        for name in policy['allowed']:
            require(any(target=='.' or name==target or name.startswith(target+'/')
                        for target in request['roots'][label]['unresolved']),'E_SC_POLICY_COVERAGE')
    d.SnapshotSet(roots,SESSION,proposal['roots'])  # Existing strict H1 role/identity/ACL/path validation.
    return proposal['roots']


def inspect_before(config_sha,request_sha):
    value,snapshot=session(config_sha)
    require('lineage' not in value,'E_SC_POLICY_ALREADY_BOUND')
    request=sealed_request(snapshot,'BEFORE',request_sha)
    claim('InspectBefore')
    proposal=snapshot.inspect_denied_policies(request,value['authority']['protected_identities'])
    validate_policy(proposal,request,value['authority']['protected_identities'],ROOTS)
    save(ROOT/'Policy-Proposal.json',proposal)
    return {'status':'SC_POLICY_PROPOSAL_ONLY_REVIEW_AND_EXTERNAL_SEAL_REQUIRED',
            'proposal':record(ROOT/'Policy-Proposal.json'),'stage_complete':False}


def bind_policy(config_sha,proposal_sha):
    normal(); value,strict=session(config_sha)
    require('lineage' not in value,'E_SC_POLICY_ALREADY_BOUND')
    require(record(ROOT/'Policy-Proposal.json')['sha256']==proposal_sha,'E_SC_EXTERNAL_POLICY')
    request=read(ROOT/'BEFORE/Request.json')
    policies=validate_policy(read(ROOT/'Policy-Proposal.json'),request,value['authority']['protected_identities'],ROOTS)
    require(direct_authority()==value['authority'],'E_SC_DIRECT_CHANGED')
    strict.verify_readable(request)
    snapshot=data().SnapshotSet(ROOTS,SESSION,policies)
    claim('BindPolicy')
    fresh=snapshot.scan('BEFORE')
    require(all(fresh['roots'][label]['objects']==request['roots'][label]['objects'] and
                fresh['roots'][label]['unresolved']==request['roots'][label]['unresolved'] for label in ROOTS),
            'E_SC_POLICY_PARTITION_CHANGED')
    child={**value,'policies':policies,'lineage':{'base_config':record(ROOT/'Inputs.json'),
        'base_request':record(ROOT/'BEFORE/Request.json'),'proposal':record(ROOT/'Policy-Proposal.json')}}
    require(direct_authority()==value['authority'],'E_SC_DIRECT_CHANGED')
    save(ROOT/'BEFORE/Policy-Request.json',fresh); save(ROOT/'Policy-Inputs.json',child)
    return {'status':'SC_POLICY_BOUND_INPUTS_ONLY_NO_COPY_OR_RUNTIME','config':record(ROOT/'Policy-Inputs.json'),
            'request':record(ROOT/'BEFORE/Policy-Request.json'),'stage_complete':False}


def before():
    normal()
    require(not os.path.lexists(ROOT),'E_SC_EXISTING_SESSION_NO_RETRY')
    require(len(DATA_SHA)==64,'E_SC_DATA_NOT_FROZEN')
    data(); authority=direct_authority()
    sr3().ordinary(ROOT.parent); ROOT.mkdir(); sr3().ordinary(ROOT)
    claim('Before')
    try:
        config={'scope':SCOPE,'root':str(ROOT),'session':SESSION,'roots':{k:str(v) for k,v in ROOTS.items()},
                'authority':authority,'budgets':sr3().BUDGETS,'groups':sr3().group_plan(),'policies':{}}
        save(ROOT/'Inputs.json',config)
        request=data().SnapshotSet(ROOTS,SESSION).scan('BEFORE')
        folder=ROOT/'BEFORE'; folder.mkdir(); save(folder/'Request.json',request)
        require(direct_authority()==authority,'E_SC_DIRECT_CHANGED')
        return {'status':'SC_BEFORE_REQUEST_ONLY_NO_SELECTED_RUNTIME','config':record(ROOT/'Inputs.json'),
                'request':record(folder/'Request.json'),'stage_complete':False}
    except BaseException:
        save(ROOT/'Before-Failure.json',{'status':'SC_BEFORE_FAILED_NO_RETRY','failure':traceback.format_exc(),'stage_complete':False})
        raise


def sealed_request(snapshot,phase,digest):
    path=request_path(snapshot,phase)
    require(record(path)['sha256']==digest,'E_SC_EXTERNAL_REQUEST')
    request=read(path)
    require(request.get('phase')==phase and request.get('session')==SESSION,'E_SC_REQUEST_PHASE')
    return request


def copy_phase(phase,config_sha,request_sha):
    # Source reader uses existing access only, not normal runtime authority.
    value,snapshot=session(config_sha); require_policy(value)
    request=sealed_request(snapshot,phase,request_sha)
    output=ROOT/phase/'reader-copy'
    claim('CopyBefore' if phase=='BEFORE' else 'CopyAfter')
    snapshot.copy_denied(request,output)
    return {'status':'SC_COPIES_REQUIRE_NORMAL_READBACK','copies':record(output/'Copies.json'),'stage_complete':False}


def verify_bundle(snapshot,phase):
    folder=ROOT/phase
    request=read(request_path(snapshot,phase)); bundle=read(folder/'Bundle.json')
    snapshot.verify_bundle(bundle,request,folder/'reader-copy',record(folder/'reader-copy/Copies.json')['sha256'])
    return bundle,request


def verify_before(config_sha,copies_sha):
    normal(); value,snapshot=session(config_sha); require_policy(value)
    require(not os.path.lexists(ROOT/'BEFORE/Bundle.json'),'E_SC_BEFORE_CONSUMED')
    require(direct_authority()==value['authority'],'E_SC_DIRECT_CHANGED')
    request=read(request_path(snapshot,'BEFORE'))
    claim('VerifyBefore')
    result=snapshot.merge(request,ROOT/'BEFORE/reader-copy',copies_sha)
    validate_before_history(snapshot,result,request,value['authority'])
    save(ROOT/'BEFORE/Bundle.json',result)
    return {'status':'SC_BEFORE_VERIFIED_NO_WORKLOAD','bundle':record(ROOT/'BEFORE/Bundle.json'),'stage_complete':False}


def runtime_namespace(snapshot,before_bundle,request,authority):
    """Closed exact-code SR3 reuse; no user-supplied runner or generic read override."""
    s=sr3(); ns=dict(s.__dict__)
    ns.update(ROOT=ROOT,CONTRACT=ROOT/'Runtime-Inputs.json',OUTPUT=ROOT/'run',__file__=__file__,source_basis=source_basis)
    def maps():
        require(direct_authority()==authority,'E_SC_DIRECT_CHANGED')
        snapshot.verify_readable(request)
        return snapshot.file_manifests(before_bundle)
    def subset(path):
        ld=read(REPO/'.github/run-artifacts/cleanup-lifetime-stack-20261024/Inputs.json')
        require(Path(path)==Path(ld['failed_receipt']['path']).parent,'E_SC_DATA_SCOPE')
        return submanifest(path,maps())
    ns.update(_evidence_manifests=maps,_evidence_submanifest=subset)
    function=history_ast(adapt=True)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),
                 '<sealed-SR3-history-two-data-observations>','exec'),ns)
    for name in ('verify_history','build_contract','validate_contract'):
        old=getattr(s,name); ns[name]=FunctionType(old.__code__,ns,name,old.__defaults__)
    def save_provisional(path,row):
        if Path(path)==ROOT/'run/Receipt.json': provisional(row,record(ROOT/'BEFORE/Bundle.json'))
        s.save(path,row)
    def workload_groups(groups,preserved,ordered):
        s.validate_stage(groups,preserved,ordered)
        return False  # Restricted data awaits ORIGINAL AFTER, regardless of all-pass runtime.
    ns.update(save=save_provisional,validate_stage=workload_groups)
    ns['run']=FunctionType(s.run.__code__,ns,'run',s.run.__defaults__)
    return ns


def validate_before_history(snapshot,bundle,request,authority):
    """Known positive inventory baselines pass BEFORE publishing the bundle."""
    namespace=runtime_namespace(snapshot,bundle,request,authority)
    return namespace['history'](c1_module())


def run(config_sha,before_sha):
    normal(); value,snapshot=session(config_sha); require_policy(value)
    require(record(ROOT/'BEFORE/Bundle.json')['sha256']==before_sha,'E_SC_EXTERNAL_BEFORE')
    bundle,request=verify_bundle(snapshot,'BEFORE')
    ns=runtime_namespace(snapshot,bundle,request,value['authority'])
    require(not os.path.lexists(ROOT/'Runtime-Inputs.json') and not os.path.lexists(ROOT/'run'),
            'E_SC_RUNTIME_CONSUMED')
    claim('Run')
    contract=ns['build_contract'](c1_module()); save(ROOT/'Runtime-Inputs.json',contract)
    ns['run'](record(ROOT/'Runtime-Inputs.json')['sha256'])
    result=read(ROOT/'run/Receipt.json')
    require(result.get('status')=='SC_WORKLOAD_OBSERVED_PENDING_AFTER' and result.get('failure') is None,
            'E_SC_RUNTIME_FAILED_NO_RETRY')
    return {'status':result['status'],'receipt':record(ROOT/'run/Receipt.json'),'preservation':False,'stage_complete':False}


def after(config_sha,before_sha):
    normal(); value,snapshot=session(config_sha); require_policy(value)
    require(record(ROOT/'BEFORE/Bundle.json')['sha256']==before_sha,'E_SC_EXTERNAL_BEFORE')
    bundle,_=verify_bundle(snapshot,'BEFORE')
    work=read(ROOT/'run/Receipt.json'); final_gate(work,True,True)
    require(direct_authority()==value['authority'],'E_SC_DIRECT_CHANGED')
    claim('After')
    folder=ROOT/'AFTER'; require(not os.path.lexists(folder),'E_SC_AFTER_CONSUMED'); folder.mkdir()
    request=snapshot.scan('AFTER',{'before':bundle,'workload_sha256':record(ROOT/'run/Receipt.json')['sha256']})
    save(folder/'Request.json',request)
    return {'status':'SC_AFTER_REQUEST_FRESH_ORIGINALS_REQUIRED','request':record(folder/'Request.json'),'stage_complete':False}


def validate_workload(value,receipt):
    """Recheck bound raw outputs, suites, ordering and actual runtime probes."""
    s=sr3(); out=ROOT/'run'; c1=c1_module()
    require(receipt.get('contract')==record(ROOT/'Runtime-Inputs.json'),'E_SC_RUNTIME_CONTRACT')
    require(receipt.get('copy_before')==record(ROOT/'BEFORE/Bundle.json'),'E_SC_WORKLOAD_BEFORE')
    source_manifest=dict(value['source_manifest']); source_manifest.update({k:v['sha256'] for k,v in value['live_delta'].items()})
    c1.verify_source(out/'source',source_manifest)
    groups=receipt['groups']; s.validate_stage(groups,True,True)
    expected_labels=['preclaim-identity','preclaim-dependencies']
    for label,_,_ in s.GROUPS: expected_labels+=['discover-'+label,'command-'+label]
    expected_labels+=['ordered-public','postclaim-identity','postclaim-dependencies']
    require([r['label'] for r in receipt['commands']]==expected_labels,'E_SC_COMMAND_ORDER')
    g=load_checked(SCRIPTS/'gate1_validation.py',s.SUPPORT_SEALS['.github/scripts/gate1_validation.py'])
    c2=load_checked(SCRIPTS/'gate1_current_runtime.py',s.SUPPORT_SEALS['.github/scripts/gate1_current_runtime.py'])
    env=s.environment(c2,out/'temp')
    for row in receipt['commands']:
        label=row['label']; target=out/label
        actual=read(target/'Command.json')
        require(actual=={k:v for k,v in row.items() if k!='label'},'E_SC_COMMAND_CHANGED')
        s.validate_capture(SimpleNamespace(returncode=row['exit_code']),row)
        require(row['argv'][0]==str(g.WORKER),'E_SC_SELECTED_WORKER')
        for role in ('stdout','stderr'):
            path=target/(role+'.log'); bound=row[role]
            observed=record(path)
            require(all(observed[k]==bound[k] for k in ('path','size','sha256')),'E_SC_STREAM_CHANGED')
        if label.endswith('-identity'): c1.validate_runtime(json.loads((target/'stdout.log').read_bytes()),env,target)
        if label.endswith('-dependencies'): c1.validate_dependencies(json.loads((target/'stdout.log').read_bytes()),value['dependencies'])
    counts=[]
    for group,(label,pattern,_) in zip(groups,s.GROUPS):
        folder=out/('tests-'+label); discovery=out/('group-'+label+'-Discovery.json')
        require(group['receipt']==record(folder/'Receipt.json') and group['cases']==record(discovery),'E_SC_GROUP_BINDING')
        ids=read(discovery)['ids']
        require(read(discovery)['pattern']==pattern and
                json.loads((out/('discover-'+label)/'stdout.log').read_bytes())==ids,'E_SC_DISCOVERY_BINDING')
        s.validate_discovery(ids,pattern); unit=read(folder/'Receipt.json'); s.validate_suite(unit,ids)
        require(unit['log']==str(folder/'unittest.log') and record(folder/'unittest.log')['sha256']==unit['log_sha256'],
                'E_SC_UNIT_LOG'); counts.append(unit['tests_run'])
    require(counts==[17,18,12,7,6,7,7],'E_SC_CONTROL_COUNTS')
    ordered=out/'ordered'; unit=read(ordered/'Receipt.json'); report=read(ordered/'Ordered-Outcomes.json')
    runner=load_checked(out/'source/.github/scripts/gate1_ordered_runner.py',s.SUPPORT_SEALS['.github/scripts/gate1_ordered_runner.py'])
    diagnostic=load_checked(out/'source/.github/scripts/gate1_ordered_diagnostic.py',s.SUPPORT_SEALS['.github/scripts/gate1_ordered_diagnostic.py'])
    diagnostic.verify_calls(report,ordered); diagnostic.validate_unit_receipt(unit,0,report)
    s.validate_ordered(report,unit,runner)
    require(unit['log']==str(ordered/'unittest.log') and record(ordered/'unittest.log')['sha256']==unit['log_sha256'],
            'E_SC_ORDERED_LOG')
    return True


def finalize(config_sha,before_sha,copies_sha):
    normal(); value,snapshot=session(config_sha); require_policy(value)
    require(record(ROOT/'BEFORE/Bundle.json')['sha256']==before_sha,'E_SC_EXTERNAL_BEFORE')
    before_bundle,_=verify_bundle(snapshot,'BEFORE')
    require(not os.path.lexists(ROOT/'Final.json') and not os.path.lexists(ROOT/'AFTER/Bundle.json'),'E_SC_FINAL_CONSUMED')
    claim('Finalize')
    request=read(ROOT/'AFTER/Request.json')
    after_bundle=snapshot.merge(request,ROOT/'AFTER/reader-copy',copies_sha)
    comparison=snapshot.compare(before_bundle,after_bundle)
    workload_record=record(ROOT/'run/Receipt.json')
    require(after_bundle['binding']['workload_sha256']==workload_record['sha256'],'E_SC_AFTER_WORKLOAD_BINDING')
    contract=read(ROOT/'Runtime-Inputs.json'); workload=read(ROOT/'run/Receipt.json')
    require(direct_authority()==value['authority'],'E_SC_DIRECT_CHANGED')
    # AFTER data must satisfy the original positive history guards as well.
    ns=runtime_namespace(snapshot,after_bundle,request,value['authority'])
    ns['validate_contract'](c1_module(),contract)
    observed=validate_workload(contract,workload)
    complete=final_gate(workload,True,observed)
    save(ROOT/'AFTER/Bundle.json',after_bundle)
    result={'status':'SC_FOCUSED_CLEANUP_STAGE_OBSERVED_NOT_GATE1','stage_complete':complete,
            'checkout_head':CHECKOUT_HEAD,'evaluated_source_head':sr3().HEAD,
            'before':record(ROOT/'BEFORE/Bundle.json'),'after':record(ROOT/'AFTER/Bundle.json'),
            'workload':workload_record,'comparison':comparison,
            **{k:False for k in sr3().FLAGS if k!='stage_complete'}}
    save(ROOT/'Final.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=MODES,required=True)
    p.add_argument('--config-sha256'); p.add_argument('--input-sha256'); p.add_argument('--before-sha256')
    a=p.parse_args()
    try:
        validate_arguments(a.mode,a.config_sha256,a.input_sha256,a.before_sha256)
        if a.mode=='Before': result=before()
        elif a.mode=='InspectBefore': result=inspect_before(a.config_sha256,a.input_sha256)
        elif a.mode=='BindPolicy': result=bind_policy(a.config_sha256,a.input_sha256)
        elif a.mode in ('CopyBefore','CopyAfter'):
            result=copy_phase('BEFORE' if a.mode=='CopyBefore' else 'AFTER',a.config_sha256,a.input_sha256)
        elif a.mode=='VerifyBefore': result=verify_before(a.config_sha256,a.input_sha256)
        elif a.mode=='Run': result=run(a.config_sha256,a.before_sha256)
        elif a.mode=='After': result=after(a.config_sha256,a.before_sha256)
        else: result=finalize(a.config_sha256,a.before_sha256,a.input_sha256)
        print(json.dumps(result)); return 0
    except BaseException:
        failure={'status':'SC_STOP_NO_RETRY','mode':a.mode,'failure':traceback.format_exc(),
                 'stage_complete':False,'gate1_complete':False}
        if _ACTIVE_CLAIM==a.mode and not os.path.lexists(ROOT/(a.mode+'-Failure.json')):
            save(ROOT/(a.mode+'-Failure.json'),failure)
        print(json.dumps(failure)); return 1


if __name__=='__main__': raise SystemExit(main())
