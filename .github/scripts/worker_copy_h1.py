"""One separately sealed COPY-H1 session; immutable V1 is never rerun.

Only fixed function code is reused with closed successor bindings. Copied
historical files are read as bytes, never imported. No deletion/ACL/Git writes.
"""
import argparse
from pathlib import Path
import sys
import traceback
import types

import archive_copy_snapshot as v
import archive_copy_h1 as h
import worker_copy_successor as prior

HERE = Path(__file__).absolute()
REPO = HERE.parents[2]
ROOT = Path(r'C:\Users\sakth\Documents\Codex\w-h1-20261022-80b78d91')
SESSION = '80b78d91a63b4e91b5d7e5f70abc9202'
CONFIG = ROOT/'Input-Seal.json'
POLICY = ROOT/'Historical-Data-Policy-exact.json'
ENTRY = ROOT/'Protected-Entry-exact.json'
OLD_ROOT = prior.ROOT
OLD_SHA = '6cb2c070072e98dc5000ed7e3b4805da74b44b4fdd6cb293f637d2a5a5bb6288'


def check_failed_history(root,expected):
    observed,denied = v.collect(root)
    v.require(not denied and observed == expected,'E_H1_FAILED_HISTORY_CHANGED')


def validate_scope_entry(policy,entry,originals=False):
    """Semantically bind the separately sealed origin, scope and source facts.

    The normal account need not open restricted originals. The preparing reader
    runs originals=True before freezing; copy stages reopen them under policy.
    """
    context = h.Context(policy)
    observation = entry.get('scope_observation')
    v.require(isinstance(observation,dict) and set(observation) ==
              {'allowed_historical_paths','unresolved_root_source','origin','origin_call',
               'observed_utc','reader_scan_scope'} and
              observation['origin'] == v.record(REPO/'.github/tests/test_gate1_cleanup_preservation.py') and
              observation['origin_call'] == 'os.link(self.cache, alias) deliberate negative fixture' and
              observation['reader_scan_scope'] == 'ONLY_6058_EXACT_PRIOR_REQUEST_TARGETS_NOT_WHOLE_ARCHIVE' and
              observation['unresolved_root_source'] == v.record(OLD_ROOT/'before/Request.json') and
              observation['unresolved_root_source']['sha256'] ==
              '662384f96ba8ba4c3cc2b5572fde9ed2fbe4ee4e5cc6837a72a59998801d1245',
              'E_H1_SCOPE_ENTRY')
    request = v.load(OLD_ROOT/'before/Request.json',observation['unresolved_root_source']['sha256'])
    rows = observation['allowed_historical_paths']
    v.require(isinstance(rows,dict) and set(rows) == set(policy['allowed']) and len(rows) == 56,
              'E_H1_SCOPE_ENTRY')
    try: context.validate_objects(rows)
    except ValueError as error:
        raise ValueError('E_H1_SCOPE_ENTRY: '+str(error)) from error
    for name,row in rows.items():
        v.require(all(row[k] == policy['allowed'][name][k] for k in
                      ('identity','size','sha256','permission_sha256')) and
                  row['size'] == 18 and row['identity'][2] == 2 and
                  row['sha256'] == '664060c3688d750c287ee877ab18697a76d020c7c96be866ee1191a318dae64b' and
                  any(v.within(name,target) for target in request['unresolved']),'E_H1_SCOPE_ENTRY')
        if originals: v.require(context.read_file(context.root/name) == row,'E_H1_SCOPE_ENTRY_CHANGED')
    return context


def verify_config(external_sha):
    config = v.load(CONFIG,external_sha)
    old_config,w = prior.verify_config(OLD_SHA)
    extra = {str(path) for path in (HERE,HERE.with_name('archive_copy_h1.py'),
        REPO/'.github/tests/test_archive_copy_h1.py',REPO/'.github/tests/test_worker_copy_h1.py',
        POLICY,ENTRY,OLD_ROOT/'Input-Seal.json',HERE.with_name('prepare_copy_h1_inputs.py'))}
    v.require(isinstance(config,dict) and set(config) ==
              {'scope','root','session','head','archive','files','old_config_sha256'} and
              config['scope'] == 'COPY_H1_STAGED_SUCCESSOR' and config['root'] == str(ROOT) and
              config['session'] == SESSION and config['head'] == w.HEAD and
              config['archive'] == str(w.ARTIFACTS) and config['old_config_sha256'] == OLD_SHA and
              set(config['files']) == set(old_config['files']) | extra,'E_H1_CONFIG')
    prior.check_roles(config['files'])
    policy = v.load(POLICY,config['files'][str(POLICY)]['sha256'])
    entry = v.load(ENTRY,config['files'][str(ENTRY)]['sha256'])
    v.require(set(entry) == {'old_root','old_objects','scope_observation','producer_authentication'} and
              entry['old_root'] == str(OLD_ROOT) and entry['producer_authentication'] is False,
              'E_H1_ENTRY')
    check_failed_history(OLD_ROOT,entry['old_objects'])
    v.require(policy['root'] == str(w.ARTIFACTS),'E_H1_POLICY_ROOT')
    context = validate_scope_entry(policy,entry)
    return config,w,context


def bind(context,root,session):
    """Closed bindings, not a CLI runner/guard/plugin injection surface."""
    namespace = dict(prior.__dict__)
    snapshot = dict(v.__dict__)
    for name in ('collect','validate_context','validate_request','scan','bundle_from_copies',
                 'merge','compare','copy_denied','verify_copies'):
        snapshot[name] = getattr(context,name)
    namespace.update(ROOT=Path(root),SESSION=session,CONFIG=Path(root)/'Input-Seal.json',
                     s=types.SimpleNamespace(**snapshot),verify_config=verify_config)
    namespace['request_path'] = lambda base,phase:Path(base)/phase.upper()/'Request.json'
    namespace['bundle_path'] = lambda base,phase:Path(base)/phase.upper()/'Bundle.json'
    namespace['copies_path'] = lambda base,phase:Path(base)/phase.upper()/'reader-copy'
    for name in ('load_before','after_binding','save_provisional','sealed_request',
                 'verify_existing_bundle','verify_before','run_workload','finalize'):
        old = getattr(prior,name)
        namespace[name] = types.FunctionType(old.__code__,namespace,name,old.__defaults__)
    return namespace


def prepare(phase,w,namespace,before_sha):
    w.normal_account()
    folder = ROOT/phase.upper()
    v.require(not folder.exists(),'E_H1_EXISTING_PHASE_NO_RETRY')
    print('Mandatory pinned history first; then exact H1 supplementary data scan. No worker.',flush=True)
    prior.mandatory_reader(w)()
    binding = namespace['after_binding'](ROOT,before_sha) if phase == 'after' else None
    request = namespace['s'].scan(w.ARTIFACTS,SESSION,phase.upper(),binding)
    folder.mkdir()
    v.save(folder/'Request.json',request)
    return {'status':'H1_'+phase.upper()+'_REQUEST_NO_WORKER','request':v.record(folder/'Request.json'),
            'readable_objects':len(request['objects']),'unresolved_targets':len(request['unresolved']),
            'workload_attempt_consumed':False,'producer_authentication':False,'gate1_complete':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=prior.PHASES,required=True)
    parser.add_argument('--config-sha256',required=True)
    parser.add_argument('--input-sha256')
    parser.add_argument('--before-sha256')
    args = parser.parse_args()
    config,w,context = verify_config(args.config_sha256)
    ns = bind(context,ROOT,SESSION)
    try:
        v.require(not (ROOT/(args.mode+'-Failure.json')).exists(),'E_H1_FAILED_PHASE_NO_RETRY')
        if args.mode in ('Before','After'):
            result = prepare(args.mode.lower(),w,ns,args.before_sha256)
        elif args.mode in ('CopyBefore','CopyAfter'):
            phase = 'before' if args.mode == 'CopyBefore' else 'after'
            request = ns['sealed_request'](phase,args.input_sha256)
            context.copy_denied(request,ns['copies_path'](ROOT,phase))
            result = {'status':'H1_COPIES_CREATED_NORMAL_VERIFICATION_REQUIRED',
                      'copies':v.record(ns['copies_path'](ROOT,phase)/'Copies.json'),
                      'producer_authentication':False,'gate1_complete':False}
        elif args.mode == 'VerifyBefore':
            w.normal_account()
            v.require(not ns['bundle_path'](ROOT,'before').exists(),'E_H1_BEFORE_ALREADY_VERIFIED')
            request = ns['sealed_request']('before',v.record(ns['request_path'](ROOT,'before'))['sha256'])
            result = context.merge(request,ns['copies_path'](ROOT,'before'),args.input_sha256)
            v.save(ns['bundle_path'](ROOT,'before'),result)
            result = {'status':'H1_BEFORE_SAMPLE_VERIFIED_NO_WORKER',
                      'bundle':v.record(ns['bundle_path'](ROOT,'before')),'gate1_complete':False}
        elif args.mode == 'Run': result = ns['run_workload'](config,w,args.before_sha256)
        else:
            w.normal_account()
            v.require(not (ROOT/'Final.json').exists() and not ns['bundle_path'](ROOT,'after').exists(),
                      'E_H1_FINALIZATION_ALREADY_ATTEMPTED')
            request = ns['sealed_request']('after',v.record(ns['request_path'](ROOT,'after'))['sha256'])
            after = context.merge(request,ns['copies_path'](ROOT,'after'),args.input_sha256)
            v.save(ns['bundle_path'](ROOT,'after'),after)
            result = ns['finalize'](w,args.before_sha256,v.record(ns['bundle_path'](ROOT,'after'))['sha256'])
        print(__import__('json').dumps(result))
        return 0
    except BaseException:
        failure = {'status':'COPY_H1_STOP_NO_AUTOMATIC_RETRY','mode':args.mode,
                   'failure':traceback.format_exc(),'gate1_complete':False,'producer_authentication':False}
        try: v.save(ROOT/(args.mode+'-Failure.json'),failure)
        except FileExistsError: pass
        print(__import__('json').dumps(failure))
        return 1


if __name__ == '__main__': raise SystemExit(main())
