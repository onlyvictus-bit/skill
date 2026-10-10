"""Real disposable native probes; completed experiments never promote capabilities."""
from __future__ import annotations
import argparse
import base64
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
from hybrid_bridge import native_observation as obs
from hybrid_bridge.native_pilot import build_env, init_argv, _parse_issue

REVISION='c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c'
EXECUTABLE_SHA='ac5b60114e5e7ef9de8878b45fc35941937341d3447366c99bc91c81557be7a4'
RESULT_KEYS={'claim','expiry','changed_owner','aba','compatible_merge','native_conflict'}

def need(condition,message):
    if not condition: raise ValueError(message)

def utc(): return dt.datetime.now(dt.timezone.utc)
def lease_time(value):
    if not isinstance(value,str): raise ValueError('lease missing')
    t=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(t.tzinfo is not None,'naive lease'); return t

def expired(expiry,observed):
    need(expiry.tzinfo is not None and observed.tzinfo is not None,'naive timestamp')
    return observed>=expiry

def valid_revision(value):
    # Claimed rows use fresh nonzero signed int64 row_lock tokens.
    if not isinstance(value,str):return False
    try:n=int(value,10)
    except ValueError:return False
    return str(n)==value and -(2**63)<=n<2**63 and n!=0

def capture_ok(r):
    need(r.get('capture_complete') is True and r.get('timed_out') is False and r.get('output_limit_exceeded') is False and r.get('capture_errors')==[],'uncertain capture')
    need(type(r.get('exit_code')) is int and isinstance(r.get('stdout'),bytes) and isinstance(r.get('stderr'),bytes),'invalid capture')

def raw_record(out,err):
    return {k+'_'+suffix:v for k,b in [('stdout',out),('stderr',err)] for suffix,v in [('base64',base64.b64encode(b).decode('ascii')),('sha256',hashlib.sha256(b).hexdigest()),('bytes',len(b))]}

def verify_raw(r):
    for k in ['stdout','stderr']:
        b=base64.b64decode(r[k+'_base64'],validate=True)
        need(len(b)==r[k+'_bytes'] and hashlib.sha256(b).hexdigest()==r[k+'_sha256'],'raw receipt hash mismatch')

def strict_json(raw):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def guard_mismatch(code,stderr,ident):
    if code!=13:return False
    try:v=strict_json(stderr.decode('utf-8').splitlines()[-1])
    except (ValueError,IndexError):return False
    return isinstance(v,dict) and isinstance(v.get('failed'),list) and len(v['failed'])==1 and v['failed'][0].get('id')==ident and v['failed'][0].get('guard_mismatch') is True

def check_reclaim(v,ident,owner):
    expected=[] if owner is None else [{'id':ident,'previous_owner':owner}]
    need(v.get('scoped') is True and type(v.get('count')) is int and v['count']==len(expected) and (v.get('reclaimed')==expected or (owner is None and v.get('reclaimed') is None)),'unexpected reclaim result')

def has_args(c,args):
    argv=c.get('argv',[])
    return any(argv[i:i+len(args)]==args for i in range(len(argv)-len(args)+1))

def bind_guard(c,ident,owner):
    need(has_args(c,['update',ident]) and has_args(c,['--actor',owner]) and has_args(c,['--if-assignee',owner]) and has_args(c,['--if-status','in_progress']),'conditional command target/actor/guards mismatch')

def native_conflict(code,raw):
    text=raw.decode('utf-8','strict').lower()
    return code!=0 and 'merge conflict' in text and 'autocommit' in text

def verify_receipt(v):
    need(v.get('schema')==1 and v.get('ok') is True and v.get('overall')=='REAL_NATIVE_PROBES_COMPLETED','incomplete experiments')
    need(set(v.get('results',{}))==RESULT_KEYS,'missing experiments')
    cmds=v.get('commands',[]);need(len(cmds)>=30,'missing commands')
    for flag in ['native_beads_qualified','native_fencing_qualified','native_merge_qualified','shared_database_authorized']:
        need(v.get(flag) is False,'capability promotion forbidden')
    need(v.get('identity',{}).get('executable_sha256')==EXECUTABLE_SHA and v.get('source_revision')==REVISION,'missing pinned identity')
    for i,c in enumerate(cmds):
        verify_raw(c);need(c.get('index')==i and c['capture_complete'] is True and c['timed_out'] is False and not c['capture_errors'] and c['output_limit_exceeded'] is False,'uncertain retained command')
    def ref(result,name,label):
        i=result.get('refs',{}).get(name);need(type(i) is int and 0<=i<len(cmds),'missing command reference: '+name)
        c=cmds[i];need(c.get('label')==label,'wrong referenced command: '+name);return c
    def data(c):return strict_json(base64.b64decode(c['stdout_base64']))
    def issue(c):
        need(c['exit_code']==0,'issue read failed');x=data(c);need(isinstance(x,list) and len(x)==1,'issue read cardinality');return x[0]
    def raw(c,key):return base64.b64decode(c[key+'_base64'])
    version=next((c for c in cmds if c.get('label')=='pinned runtime version'),None)
    need(version is not None and version['exit_code']==0 and data(version).get('version')=='1.3.1' and data(version).get('commit')==REVISION,'runtime revision not observed')
    claim=v['results']['claim'];ident=claim.get('issue_id');owner=claim.get('owner');other=claim.get('loser')
    claims=[ref(claim,k,'competing native process claim') for k in ['race_a','race_b']]
    need(claims[0]['process_id']!=claims[1]['process_id'] and sum(c['exit_code']==0 for c in claims)==1,'not one real process winner')
    won=next(c for c in claims if c['exit_code']==0);need(won['argv'][won['argv'].index('--actor')+1]==owner,'wrong winning actor')
    held=issue(ref(claim,'read','independent issue read'));need(held['id']==ident and held.get('assignee')==owner and held['status']=='in_progress','claim readback mismatch')
    need(valid_revision(held.get('revision')) and held.get('revision')==claim['original_revision'],'original generation mismatch')
    expiry=lease_time(held.get('lease_expires_at'));need(expiry==lease_time(claim['lease_expires_at']),'lease summary mismatch')
    loser=cmds[claim['refs']['semantic_loser']];need(loser['exit_code']!=0 and 'already claimed' in (raw(loser,'stderr')+raw(loser,'stdout')).decode().lower(),'semantic loser refusal missing')
    live_reclaim=ref(claim,'live_reclaim','live lease reclaim control');check_reclaim(data(live_reclaim),ident,None)
    need(lease_time(live_reclaim['finished_at'])<expiry,'live reclaim was not pre-expiry')
    e=v['results']['expiry'];before=issue(ref(e,'before','independent issue read'));after=issue(ref(e,'after','independent issue read'));c=ref(e,'write','conditional title write')
    need(before.get('assignee')==owner and lease_time(before['lease_expires_at'])==expiry and expired(expiry,lease_time(c['started_at'])),'expiry not reached with original lease')
    need(expired(expiry,lease_time(e['observed_at'])) and e['elapsed_monotonic_seconds']>=295,'real TTL not elapsed')
    need((lease_time(c['started_at'])-lease_time(won['started_at'])).total_seconds()>=295,'retained commands did not wait default TTL')
    need(before['id']==after['id']==ident and e['refs']['before']<e['refs']['write']<e['refs']['after'],'expiry target or chronology mismatch');bind_guard(c,ident,owner)
    allowed=c['exit_code']==0;need(allowed==e['expired_conditional_write_allowed'] and e['automatic_expiry_fence']==('REFUTED' if allowed else 'OBSERVED_REFUSAL'),'expiry result mismatch')
    if allowed:need(after['title']=='expired old owner write' and after['lease_expires_at']==before['lease_expires_at'],'expired write or unchanged lease unproved')
    else:need(guard_mismatch(c['exit_code'],raw(c,'stderr'),ident) and after==before,'unclassified expiry refusal')
    check_reclaim(data(ref(e,'reclaim','real expired lease scoped reclaim')),ident,owner)
    freed=issue(ref(e,'freed','independent issue read'));need(freed['id']==ident and freed['status']=='open' and not freed.get('assignee') and not freed.get('lease_expires_at'),'reclaim readback missing')
    f=v['results']['changed_owner'];before=issue(ref(f,'before','independent issue read'));after=issue(ref(f,'after','independent issue read'));c=ref(f,'write','conditional title write')
    need(before['id']==after['id']==ident and f['refs']['before']<f['refs']['write']<f['refs']['after'],'changed owner target or chronology mismatch');bind_guard(c,ident,owner)
    need(f['stale_write_refused'] is True and f['issue_unchanged'] is True and before['assignee']==other and guard_mismatch(c['exit_code'],raw(c,'stderr'),ident) and before==after,'changed-owner guard/effect not proved')
    h1=data(ref(f,'head_before','native branch read'))['head'];h2=data(ref(f,'head_after','native branch read'))['head'];need(h1==h2==f['before_head']==f['after_head'],'stale write moved head')
    a=v['results']['aba'];before=issue(ref(a,'before','independent issue read'));after=issue(ref(a,'after','independent issue read'));c=ref(a,'write','conditional title write')
    need(valid_revision(before.get('revision')) and before['assignee']==owner and before['status']=='in_progress' and before['revision']!=held['revision'] and before['revision']==a['new_revision'],'ABA generation absent')
    need(before['id']==after['id']==ident and a['refs']['before']<a['refs']['write']<a['refs']['after'],'ABA target or chronology mismatch');bind_guard(c,ident,owner)
    allowed=c['exit_code']==0;need(allowed==a['old_actor_status_token_allowed'] and a['generation_fence']==('REFUTED' if allowed else 'OBSERVED_REFUSAL'),'ABA result mismatch')
    if allowed:need(after['title']=='old actor status token replay','ABA effect missing')
    else:need(guard_mismatch(c['exit_code'],raw(c,'stderr'),ident) and before==after,'ABA refusal unclassified')
    for kind in ['compatible_merge','native_conflict']:
        m=v['results'][kind];source=data(ref(m,'source','native branch write'));target=data(ref(m,'target','native branch read'));result=data(ref(m,'result','native branch read'));fork=data(ref(m,'fork_read','native branch read'))
        need(fork['head']==m['base_head'] and source['before_head']==m['base_head'] and source['head']==m['source_head'] and target['head']==m['target_head'] and result['head']==m['result_head'],'branch head summaries mismatch')
        need(source['branch']==m['source_branch'] and target['branch']==result['branch']=='main' and len({m['base_head'],m['source_head'],m['target_head']})==3,'not native divergent branches')
        need(m['refs']['fork_read']<m['refs']['source']<m['refs']['target']<m['refs']['merge']<m['refs']['result'],'native merge chronology mismatch')
        if kind=='compatible_merge':
            c=ref(m,'merge','compatible native merge');need(has_args(c,['vc','merge',m['source_branch']]) and '--strategy' not in c['argv'] and c['exit_code']==0 and data(c).get('conflicts')==0 and m['both_changes_retained'] is True,'compatible merge unsuccessful')
            ia=issue(ref(m,'read_a','independent issue read'));ib=issue(ref(m,'read_b','independent issue read'));need(ia['id']==source['issue']['id'] and ib['id']==target['issue']['id'] and ia['id']!=ib['id'] and ia['title']=='compatible source A' and ib['title']=='compatible target B','merged changes not read back')
            need(m['result_head'] not in {m['base_head'],m['source_head'],m['target_head']},'new merge commit absent')
            history={x['Hash'] for x in result['log']};need({m['base_head'],m['source_head'],m['target_head']}<=history,'native merge ancestry absent')
        else:
            c=ref(m,'merge','actual native same-cell conflict');need(has_args(c,['vc','merge',m['source_branch']]) and '--strategy' not in c['argv'] and native_conflict(c['exit_code'],raw(c,'stderr')+raw(c,'stdout')),'not actual native merge conflict')
            need(m['native_refused'] is True and m['target_and_source_preserved'] is True and m['partial_effects_observed'] is False and m['resolution_attempted'] is False,'contradictory conflict verdict')
            need(source['issue']['id']==target['issue']['id']==result['issue']['id'],'conflict issue mismatch')
            need(target['issue']['title']=='conflict target title' and source['issue']['title']=='conflict source title' and result['issue']==target['issue'] and result['head']==target['head'],'conflict target changed')
            need(issue(ref(m,'read_source','independent issue read'))['title']=='conflict source title','source conflict changed')
            need(data(ref(m,'source_after','native branch read'))['head']==source['head'],'conflict source head changed')
            need(raw(ref(m,'export_before','native full export'),'stdout')==raw(ref(m,'export_after','native full export'),'stdout'),'conflict changed native full export')
            need(data(ref(m,'status_before','post-conflict native status'))==data(ref(m,'status_after','post-conflict native status')),'conflict changed working set status')
            need(not result['conflicts'],'unresolved conflicts remain')
    return v

class Probe:
    def __init__(self,args):
        self.args=args;self.commands=[];self.lock=threading.Lock();self.results={}
        self.receipt={'schema':1,'ok':False,'overall':'BLOCKED','source_revision':REVISION,'commands':self.commands,'results':self.results,
                      'native_beads_qualified':False,'native_fencing_qualified':False,'native_merge_qualified':False,'shared_database_authorized':False}
    def save(self):
        path=self.args.receipt;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(self.receipt,indent=2)+'\n',encoding='utf-8')
    def run(self,argv,cwd,env,expect=0,label=''):
        start=utc();r=obs._capture_process([str(x) for x in argv],cwd=str(cwd),env=env,timeout=45,shell=False)
        record={k:v for k,v in r.items() if k not in ['stdout','stderr']}
        record.update(raw_record(r['stdout'],r['stderr']),label=label,argv=[str(x) for x in argv],started_at=start.isoformat(),finished_at=utc().isoformat())
        with self.lock:
            record['index']=len(self.commands);self.commands.append(record);self.save()
        r['_index']=record['index']
        capture_ok(r)
        if expect is not None:
            need(r['exit_code']==expect, f'{label} exited {r["exit_code"]}: '+r['stderr'].decode('utf-8','replace'))
            if expect==0:
                lines=r['stderr'].decode('utf-8').splitlines()
                need(all(not s.strip() or s.strip()==obs.JSON_MIGRATION_NOTE for s in lines),f'{label}: unexpected stderr: '+r['stderr'].decode('utf-8'))
        return r
    def bd(self,project,args,actor='r5actora',expect=0,label=''):
        root,launcher,env,meta=project
        return self.run([self.args.bd,'--sandbox','--actor',actor,'--json',*args],launcher,env,expect,label)
    def issue(self,project,ident,branch=None):
        args=['--readonly','show',ident]
        if branch:args+=['--as-of',branch]
        r=self.bd(project,args,label='independent issue read');self.last_issue_index=r['_index'];v=_parse_issue(r['stdout'])
        need(v['id']==ident,'wrong issue read');return v
    def helper(self,project,branch,op,ident,title=''):
        root,launcher,env,meta=project
        r=self.run([self.args.helper,root,meta['dolt_database'],meta['project_id'],branch,op,ident,title],launcher,env,label='native branch '+op)
        self.last_helper_index=r['_index'];return strict_json(r['stdout'])
    def setup(self,name):
        root=self.args.workspace/name;root.mkdir();launcher=root/'launcher';launcher.mkdir()
        env=build_env(root/'.beads');env['BEADS_NODE_ID']='r5disposableprobe'
        self.run(['git','init','--quiet'],launcher,env,label='disposable launcher init')
        self.run(['git','config','beads.role','maintainer'],launcher,env,label='disposable maintainer role')
        self.run(init_argv(self.args.bd),launcher,env,label='native disposable init')
        meta=strict_json((root/'.beads/metadata.json').read_bytes())
        need(meta.get('backend')=='dolt' and meta.get('dolt_mode')=='embedded','wrong native backend')
        marker={'root':str(root),'database':meta['dolt_database'],'project':meta['project_id']}
        (root/'r5-disposable-probe.json').write_text(json.dumps(marker),encoding='utf-8')
        return root,launcher,env,meta
    def create(self,project,title):
        return _parse_issue(self.bd(project,['create',title,'--type','task'],label='create disposable task')['stdout'])['id']
    def update(self,project,ident,title,actor='r5actora',owner=None,expect=0):
        args=['update',ident,'--title',title]
        if owner:args+=['--if-assignee',owner,'--if-status','in_progress']
        return self.bd(project,args,actor,expect,'conditional title write' if owner else 'native title write')
    def export(self,p):
        return self.bd(p,['--readonly','export','--all','--no-memories'],label='native full export')
    def status(self,p):
        return self.bd(p,['--readonly','vc','status'],label='post-conflict native status')
    def merge_probes(self):
        p=self.setup('merge');a=self.create(p,'merge base A');b=self.create(p,'merge base B')
        base=self.helper(p,'main','read',a)['head']
        self.helper(p,'main','fork','r5probecompatible')
        need(self.helper(p,'r5probecompatible','read',a)['head']==base,'fork is not at base');fork_idx=self.last_helper_index
        source=self.helper(p,'r5probecompatible','write',a,'compatible source A')['head'];source_idx=self.last_helper_index
        need(self.issue(p,a,'r5probecompatible')['title']=='compatible source A','source not independently visible')
        self.update(p,b,'compatible target B');target=self.helper(p,'main','read',b)['head'];target_idx=self.last_helper_index
        need(len({base,source,target})==3,'not divergent histories')
        merge=self.bd(p,['vc','merge','r5probecompatible'],label='compatible native merge')
        need(strict_json(merge['stdout']).get('conflicts')==0,'compatible native conflict count nonzero')
        after=self.helper(p,'main','read',a);result_idx=self.last_helper_index
        need(self.issue(p,a)['title']=='compatible source A','source change lost');read_a=self.last_issue_index
        need(self.issue(p,b)['title']=='compatible target B','target change lost');read_b=self.last_issue_index
        self.results['compatible_merge']={'base_head':base,'source_head':source,'target_head':target,'result_head':after['head'],'both_changes_retained':True,'source_branch':'r5probecompatible','refs':{'fork_read':fork_idx,'source':source_idx,'target':target_idx,'result':result_idx,'merge':merge['_index'],'read_a':read_a,'read_b':read_b}};self.save()
        base=after['head'];self.helper(p,'main','fork','r5probeconflict')
        need(self.helper(p,'r5probeconflict','read',a)['head']==base,'conflict fork mismatch');fork_idx=self.last_helper_index
        source=self.helper(p,'r5probeconflict','write',a,'conflict source title')['head'];source_idx=self.last_helper_index
        self.update(p,a,'conflict target title');before=self.helper(p,'main','read',a);target_idx=self.last_helper_index
        need(len({base,source,before['head']})==3,'conflict histories not divergent')
        need(self.issue(p,a,'r5probeconflict')['title']=='conflict source title','conflict source read missing')
        export_before=self.export(p);status_before=self.status(p)
        r=self.bd(p,['vc','merge','r5probeconflict'],expect=None,label='actual native same-cell conflict')
        need(native_conflict(r['exit_code'],r['stderr']+r['stdout']),'actual native conflict not refused')
        after=self.helper(p,'main','read',a);result_idx=self.last_helper_index;target_issue=self.issue(p,a);source_issue=self.issue(p,a,'r5probeconflict');read_source=self.last_issue_index
        source_after=self.helper(p,'r5probeconflict','read',a);source_after_idx=self.last_helper_index
        status_after=self.status(p);export_after=self.export(p)
        no_partial=before['head']==after['head'] and after['issue']==before['issue'] and source_after['head']==source and not after['conflicts'] and target_issue['title']=='conflict target title' and source_issue['title']=='conflict source title' and export_before['stdout']==export_after['stdout'] and strict_json(status_before['stdout'])==strict_json(status_after['stdout'])
        self.results['native_conflict']={'base_head':base,'source_head':source,'target_head':before['head'],'result_head':after['head'],'native_refused':True,'target_and_source_preserved':no_partial,'partial_effects_observed':not no_partial,'source_branch':'r5probeconflict','resolution_attempted':False,'refs':{'fork_read':fork_idx,'source':source_idx,'target':target_idx,'result':result_idx,'merge':r['_index'],'read_source':read_source,'source_after':source_after_idx,'export_before':export_before['_index'],'export_after':export_after['_index'],'status_before':status_before['_index'],'status_after':status_after['_index']}};self.save()
        need(no_partial,'conflict left partial effects: retained receipt requires investigation')
    def ownership_probes(self):
        p=self.setup('ownership');ident=self.create(p,'ownership base title');actors=['r5actora','r5actorb'];barrier=threading.Barrier(2)
        start=time.monotonic()
        def claim(actor):
            barrier.wait();return actor,self.bd(p,['update',ident,'--claim'],actor,expect=None,label='competing native process claim')
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(claim,actors))
        winners=[actor for actor,r in outcomes if r['exit_code']==0]
        need(len(winners)==1,'race must have exactly one successful native claim')
        owner=winners[0];other=next(a for a in actors if a!=owner)
        read=self.issue(p,ident);need(read.get('assignee')==owner and read.get('status')=='in_progress','claim readback mismatch')
        claim_read_idx=self.last_issue_index;original_revision=read.get('revision');need(valid_revision(original_revision),'invalid original revision');expiry=lease_time(read.get('lease_expires_at'))
        need(not expired(expiry,utc()),'claim already expired')
        loser=next(r for a,r in outcomes if a==other);text=(loser['stderr']+loser['stdout']).decode('utf-8','replace').lower()
        infrastructure='exclusive lock' in text or 'another process' in text
        if infrastructure:loser=self.bd(p,['update',ident,'--claim'],other,expect=None,label='semantic loser retry after race')
        need(loser['exit_code']!=0 and 'already claimed' in (loser['stderr']+loser['stdout']).decode('utf-8','replace').lower(),'loser is not a semantic claim refusal')
        self.results['claim']={'issue_id':ident,'owner':owner,'loser':other,'exactly_one_winner':True,'race_loser_infrastructure_lock':infrastructure,'competition_scope':'PROCESS_LAUNCH_RACE_WITH_SEQUENTIAL_SEMANTIC_REFUSAL' if infrastructure else 'NATIVE_PROCESS_CLAIM_RACE','original_revision':original_revision,'lease_expires_at':expiry.isoformat(),'refs':{'race_a':outcomes[0][1]['_index'],'race_b':outcomes[1][1]['_index'],'read':claim_read_idx,'semantic_loser':loser['_index']}};self.save()
        live=self.bd(p,['reclaim','--older-than','0s','--id',ident],label='live lease reclaim control');check_reclaim(strict_json(live['stdout']),ident,None);self.results['claim']['refs']['live_reclaim']=live['_index']
        self.merge_probes()
        need((expiry-utc()).total_seconds()<370,'unexpected lease TTL')
        while not expired(expiry+dt.timedelta(seconds=1),utc()):
            need(time.monotonic()-start<370,'real lease expiry wait exceeded bounded deadline')
            time.sleep(min(2,max(.05,(expiry+dt.timedelta(seconds=1)-utc()).total_seconds())))
        observed=utc();before=self.issue(p,ident);need(before.get('assignee')==owner and lease_time(before['lease_expires_at'])==expiry,'ownership or lease changed during wait')
        expiry_before_idx=self.last_issue_index
        r=self.update(p,ident,'expired old owner write',owner,owner,expect=None)
        after=self.issue(p,ident);allowed=r['exit_code']==0
        if allowed:need(after['title']=='expired old owner write','expired success effect absent')
        else:need(guard_mismatch(r['exit_code'],r['stderr'],ident) and after['title']==before['title'],'unclassified expiry refusal')
        self.results['expiry']={'lease_expires_at':expiry.isoformat(),'observed_at':observed.isoformat(),'elapsed_monotonic_seconds':time.monotonic()-start,'automatic_expiry_fence':'REFUTED' if allowed else 'OBSERVED_REFUSAL','expired_conditional_write_allowed':allowed,'refs':{'before':expiry_before_idx,'after':self.last_issue_index,'write':r['_index']}};self.save()
        reclaim=self.bd(p,['reclaim','--older-than','0s','--id',ident],label='real expired lease scoped reclaim');check_reclaim(strict_json(reclaim['stdout']),ident,owner);self.results['expiry']['refs']['reclaim']=reclaim['_index']
        freed=self.issue(p,ident);need(freed['status']=='open' and not freed.get('assignee') and not freed.get('lease_expires_at'),'reclaim readback mismatch')
        self.results['expiry']['reclaim_verified']=True;self.results['expiry']['refs']['freed']=self.last_issue_index
        self.bd(p,['update',ident,'--claim'],other,label='new owner reclaim')
        before=self.issue(p,ident);need(before.get('assignee')==other and before['status']=='in_progress','new owner missing')
        need(not expired(lease_time(before['lease_expires_at']),utc()),'new claim lease expired')
        owner_before_idx=self.last_issue_index;head_before=self.helper(p,'main','read',ident)['head'];head_before_idx=self.last_helper_index
        r=self.update(p,ident,'stale owner must not land',owner,owner,expect=None)
        after=self.issue(p,ident);owner_after_idx=self.last_issue_index;head_after=self.helper(p,'main','read',ident)['head'];head_after_idx=self.last_helper_index
        need(guard_mismatch(r['exit_code'],r['stderr'],ident),'stale owner refusal not structured guard mismatch')
        need(after==before and head_before==head_after,'stale conditional write changed native state')
        self.results['changed_owner']={'stale_write_refused':True,'before_head':head_before,'after_head':head_after,'new_owner':other,'old_owner':owner,'issue_unchanged':True,'refs':{'before':owner_before_idx,'after':owner_after_idx,'head_before':head_before_idx,'head_after':head_after_idx,'write':r['_index']}};self.save()
        self.bd(p,['unclaim',ident,'--if-assignee',other],other,label='new owner voluntarily releases')
        self.bd(p,['update',ident,'--claim'],owner,label='original actor claims new generation')
        generation=self.issue(p,ident);need(valid_revision(generation.get('revision')),'invalid new revision');need(generation.get('assignee')==owner and generation['revision']!=original_revision,'ABA generation not changed')
        aba_before_idx=self.last_issue_index
        r=self.update(p,ident,'old actor status token replay',owner,owner,expect=None);after=self.issue(p,ident);allowed=r['exit_code']==0
        if allowed:need(after['title']=='old actor status token replay','ABA replay effect missing')
        else:need(guard_mismatch(r['exit_code'],r['stderr'],ident) and after['title']==generation['title'],'unclassified ABA refusal')
        self.results['aba']={'original_revision':original_revision,'new_revision':generation['revision'],'old_actor_status_token_allowed':allowed,'generation_fence':'REFUTED' if allowed else 'OBSERVED_REFUSAL','refs':{'before':aba_before_idx,'after':self.last_issue_index,'write':r['_index']}};self.save()
    def execute(self):
        need(self.args.workspace.is_absolute() and not self.args.workspace.exists(),'workspace must be new absolute disposable path')
        need(self.args.bd.is_file() and self.args.helper.is_file(),'runtime binaries absent')
        exe_hash=hashlib.sha256(self.args.bd.read_bytes()).hexdigest();need(exe_hash==EXECUTABLE_SHA,'pinned release executable hash mismatch')
        need(hashlib.sha256(self.args.helper.read_bytes()).hexdigest()==self.args.helper_sha,'helper hash mismatch')
        self.args.workspace.mkdir(parents=True)
        self.receipt['identity']={'executable_sha256':exe_hash,'helper_sha256':self.args.helper_sha,'helper_source_sha256':hashlib.sha256((ROOT/'.github/scripts/r5_native_probe_helper.go').read_bytes()).hexdigest(),'platform':sys.platform,'python':sys.version,'workflow_commit':os.environ.get('GITHUB_SHA'),'default_lease_ttl_seconds':300}
        r=self.run([self.args.bd,'--sandbox','--json','version'],self.args.workspace,build_env(self.args.workspace/'.beads'),label='pinned runtime version')
        version=strict_json(r['stdout']);need(version.get('version')=='1.3.1' and version.get('commit')==REVISION,'pinned version/revision mismatch')
        self.ownership_probes();self.receipt.update(ok=True,overall='REAL_NATIVE_PROBES_COMPLETED')
        verify_receipt(self.receipt);self.save();print(json.dumps({'overall':self.receipt['overall'],'results':self.results},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bd',type=Path,required=True);ap.add_argument('--helper',type=Path,required=True);ap.add_argument('--helper-sha',required=True);ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True)
    args=ap.parse_args();probe=Probe(args)
    try:probe.execute()
    except Exception as exc:
        probe.receipt.update(ok=False,overall='BLOCKED',error=str(exc));probe.save();print(str(exc),file=sys.stderr);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
