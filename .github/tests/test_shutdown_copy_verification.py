"""Closed copy-coordinator guards; never select numerical Python3.12."""
import ast
import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).absolute().parents[1]/'scripts/shutdown_copy_verification.py'


class CopyCoordinator(unittest.TestCase):
    def controller(self):
        self.assertTrue(SCRIPT.exists(), 'SC1 copy coordinator absent; old SR3 only reads originals')
        spec=importlib.util.spec_from_file_location('sc_coordinator_test',SCRIPT)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_new_session_never_reuses_consumed_destinations(self):
        c=self.controller()
        self.assertEqual(c.ROOT.name,'sr3-copy-20261027-4a52cd8d')
        self.assertNotEqual(c.ROOT,c.sr3().ROOT)
        self.assertEqual(set(c.ROOTS.values()),set(c.sr3().HISTORY_ROOTS))
        self.assertFalse(any(c.ROOT.is_relative_to(p) for p in c.ROOTS.values()))

    def test_history_changes_only_two_data_inventory_expressions(self):
        c=self.controller(); a=c.history_ast(); b=c.history_ast(adapt=True)
        self.assertEqual(len(a.body),len(b.body))
        self.assertEqual(sum(ast.dump(x)!=ast.dump(y) for x,y in zip(a.body,b.body)),2)
        calls=[ast.unparse(n.func) for n in ast.walk(b) if isinstance(n,ast.Call)]
        for name in ('c1.fixed_inputs','c1.protected','c1.verify_source','_evidence_manifests','_evidence_submanifest'):
            self.assertIn(name,calls)
        self.assertEqual(calls.count('c1.source_manifest'),1)

    def test_submanifest_cannot_redirect_authoritative_or_outside_paths(self):
        c=self.controller()
        with tempfile.TemporaryDirectory(prefix='sc-subset-') as name:
            root=Path(name); maps={str(root/'data'):{'nested/a.json':'a'*64,'b.log':'b'*64}}
            self.assertEqual(c.submanifest(root/'data/nested',maps),{'a.json':'a'*64})
            with self.assertRaisesRegex(ValueError,'E_SC_DATA_SCOPE'):
                c.submanifest(root/'live-source',maps)

    def test_success_is_provisional_until_after(self):
        c=self.controller()
        row={'status':'SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1','failure':None,'preservation':True,**dict.fromkeys(c.sr3().FLAGS,False)}
        row['stage_complete']=True; c.provisional(row,{'sha256':'a'*64})
        self.assertEqual(row['status'],'SC_WORKLOAD_OBSERVED_PENDING_AFTER')
        self.assertFalse(row['stage_complete']); self.assertFalse(row['preservation'])

    def test_workload_failure_never_becomes_pending_success(self):
        c=self.controller(); row={'status':'PARTIAL_OR_FAILED_NO_RETRY','failure':'CONTROL','preservation':False,**dict.fromkeys(c.sr3().FLAGS,False)}
        c.provisional(row,{'sha256':'a'*64})
        self.assertEqual(row['status'],'PARTIAL_OR_FAILED_NO_RETRY'); self.assertEqual(row['failure'],'CONTROL')

    def test_final_requires_after_and_observed_workload(self):
        c=self.controller(); good={'status':'SC_WORKLOAD_OBSERVED_PENDING_AFTER','workload_status':'SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1','failure':None,'preservation':False,**dict.fromkeys(c.sr3().FLAGS,False)}
        self.assertTrue(c.final_gate(good,True,True))
        for row,sampled,observed in ((good,False,True),(good,True,False),({**good,'failure':'CONTROL'},True,True)):
            with self.assertRaisesRegex(ValueError,'E_SC_FINAL_GATE'): c.final_gate(row,sampled,observed)

    def test_wrong_account_before_creates_no_session(self):
        c=self.controller()
        with tempfile.TemporaryDirectory(prefix='sc-account-') as name:
            target=Path(name)/'absent'
            with patch.object(c,'ROOT',target),patch.object(c,'normal',side_effect=ValueError('CONTROL_ACCOUNT')):
                with self.assertRaisesRegex(ValueError,'CONTROL_ACCOUNT'): c.before()
                self.assertFalse(target.exists())

    def test_bad_module_seal_prevents_execution(self):
        c=self.controller()
        with tempfile.TemporaryDirectory(prefix='sc-module-') as name:
            path=Path(name)/'untrusted.py'; path.write_text('raise RuntimeError("MUST_NOT_EXECUTE")',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'E_SC_CODE_SEAL'): c.load_checked(path,'0'*64)

    def test_consumed_attempt_has_exact_required_pins(self):
        c=self.controller()
        self.assertEqual(c.CONSUMED['sr3-prepare/Failure.json'],'779800f964182b9a68a10f67299160151a5e03507cbe18a0c4e06ea4549d4c48')
        self.assertEqual(c.CONSUMED['sr3-prepare/Claim.json'],'b47f548be8ed3cba3a7e50efc4c5b564b1073002b6e72faa2a987046410d173f')

    def test_phase_claim_is_exclusive_even_if_later_work_fails(self):
        c=self.controller()
        self.assertTrue(callable(getattr(c,'claim',None)),'Missing exclusive per-phase claims')
        with tempfile.TemporaryDirectory(prefix='sc-claim-') as name:
            root=Path(name)
            with patch.object(c,'ROOT',root):
                c.claim('CopyBefore')
                self.assertTrue((root/'CopyBefore-Claim.json').exists())
                with self.assertRaisesRegex(ValueError,'E_SC_PHASE_CONSUMED'):
                    c.claim('CopyBefore')

    def test_phase_cannot_accept_unbound_optional_hash(self):
        c=self.controller()
        self.assertTrue(callable(getattr(c,'validate_arguments',None)),'Missing required external phase seals')
        for mode in ('InspectBefore','BindPolicy','CopyBefore','VerifyBefore','Run','After','CopyAfter','Finalize'):
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'E_SC_REQUIRED_SEALS'):
                c.validate_arguments(mode,None,None,None)

    def test_actual_before_request_only_uses_copies_for_evidence(self):
        import hashlib
        c=self.controller(); data_path=SCRIPT.with_name('shutdown_copy_data.py')
        self.assertTrue(data_path.exists(),'DATA adapter not yet available')
        with tempfile.TemporaryDirectory(prefix='sc-before-flow-') as name:
            base=Path(name); original=base/'old-data'; original.mkdir()
            (original/'data.txt').write_bytes(b'old evidence')
            before_acl=c.load_checked(data_path,hashlib.sha256(data_path.read_bytes()).hexdigest()).permission_digest(original/'data.txt')
            target=base/'new-session'
            with patch.object(c,'ROOT',target),patch.object(c,'ROOTS',{'fixture':original}), \
                 patch.object(c,'DATA_SHA',hashlib.sha256(data_path.read_bytes()).hexdigest()), \
                 patch.object(c,'normal'),patch.object(c,'direct_authority',return_value={'direct':'CONTROL_ONLY_NO_RUNTIME'}):
                result=c.before()
                self.assertEqual(result['status'],'SC_BEFORE_REQUEST_ONLY_NO_SELECTED_RUNTIME')
                self.assertTrue((target/'BEFORE/Request.json').exists())
                self.assertFalse((target/'run').exists())
                with self.assertRaisesRegex(ValueError,'E_SC_EXISTING_SESSION_NO_RETRY'): c.before()
            observed=c.load_checked(data_path,hashlib.sha256(data_path.read_bytes()).hexdigest()).permission_digest(original/'data.txt')
            self.assertEqual(before_acl,observed)

    def test_real_copy_before_readback_and_fresh_after_workflow(self):
        """Real fixture bytes/phases; fake workload explicitly is NOT runtime proof."""
        import hashlib
        c=self.controller(); data_path=SCRIPT.with_name('shutdown_copy_data.py')
        with tempfile.TemporaryDirectory(prefix='sc-phase-flow-') as name:
            base=Path(name); original=base/'old-data'; original.mkdir()
            (original/'data.txt').write_bytes(b'old evidence')
            target=base/'new-session'
            authority={'helper':c.record(SCRIPT),'data':c.record(data_path),'direct':'FIXTURE_NOT_RUNTIME','protected_identities':[[1,2]]}
            with patch.object(c,'ROOT',target),patch.object(c,'ROOTS',{'fixture':original}), \
                 patch.object(c,'DATA_SHA',hashlib.sha256(data_path.read_bytes()).hexdigest()), \
                 patch.object(c,'normal'),patch.object(c,'direct_authority',return_value=authority), \
                 patch.object(c,'validate_before_history',return_value={'fixture_only':'NOT_REAL_HISTORY'}):
                first=c.before(); config_sha=first['config']['sha256']
                proposal=c.inspect_before(config_sha,first['request']['sha256'])
                policy=c.bind_policy(config_sha,proposal['proposal']['sha256']); config_sha=policy['config']['sha256']
                copied=c.copy_phase('BEFORE',config_sha,policy['request']['sha256'])
                result=c.verify_before(config_sha,copied['copies']['sha256'])
                self.assertEqual(result['status'],'SC_BEFORE_VERIFIED_NO_WORKLOAD')
                before_sha=result['bundle']['sha256']
                run=target/'run'; run.mkdir()
                row={'status':'SC_WORKLOAD_OBSERVED_PENDING_AFTER','failure':None,
                     'workload_status':'SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1',
                     'preservation':False,**dict.fromkeys(c.sr3().FLAGS,False)}
                c.save(run/'Receipt.json',row)
                later=c.after(config_sha,before_sha)
                copied_after=c.copy_phase('AFTER',config_sha,later['request']['sha256'])
                c.save(target/'Runtime-Inputs.json',{'FIXTURE':'NOT_A_REAL_RUNTIME_CONTRACT'})
                from types import SimpleNamespace
                with patch.object(c,'runtime_namespace',return_value={'validate_contract':lambda *args:None}), \
                     patch.object(c,'validate_workload',return_value=True):
                    final=c.finalize(config_sha,before_sha,copied_after['copies']['sha256'])
                self.assertTrue(final['stage_complete'])
                self.assertFalse(final['gate1_complete'])
                self.assertEqual(c.read(run/'Receipt.json'),row,'Provisional receipt must remain unchanged')

    def test_before_bundle_requires_original_positive_history_checks(self):
        from types import SimpleNamespace
        c=self.controller()
        self.assertTrue(callable(getattr(c,'validate_before_history',None)),'Missing separated BEFORE positive-baseline gate')
        with tempfile.TemporaryDirectory(prefix='sc-before-mandatory-') as name:
            root=Path(name); (root/'BEFORE').mkdir(); c.save(root/'BEFORE/Request.json',{})
            snapshot=SimpleNamespace(merge=lambda *args:{'fixture':'merged'})
            with patch.object(c,'ROOT',root),patch.object(c,'normal'), \
                 patch.object(c,'session',return_value=({'authority':{},'lineage':{}},snapshot)), \
                 patch.object(c,'direct_authority',return_value={}), \
                 patch.object(c,'validate_before_history',side_effect=PermissionError('CONTROL_ORIGINAL_POSITIVE_CHECK')):
                with self.assertRaisesRegex(PermissionError,'CONTROL_ORIGINAL_POSITIVE_CHECK'):
                    c.verify_before('a'*64,'b'*64)
                self.assertFalse((root/'BEFORE/Bundle.json').exists())

    def test_compiled_history_does_not_require_a_published_before_bundle(self):
        c=self.controller()
        with tempfile.TemporaryDirectory(prefix='sc-unpublished-') as name,patch.object(c,'ROOT',Path(name)):
            self.assertTrue(callable(c.runtime_namespace(None,{},None,{})['history']))

    def test_approved_checkout_is_exact_and_evaluation_stays_old_source(self):
        c=self.controller()
        self.assertTrue(callable(getattr(c,'source_basis',None)),'Approved exact checkout transition not implemented')
        files,tree=c.source_basis(c.c1_module())
        self.assertEqual(len(files),627)
        self.assertEqual(len(tree),627)
        self.assertEqual(c.sr3().HEAD,'a38297dd797eeecd25e41ab0af1df4e3db8fa984')
        self.assertNotIn('.github/scripts/gate1_current_preflight.py',files)

    def test_unknown_head_parent_extra_file_wrong_mode_or_blob_are_refused(self):
        from types import SimpleNamespace
        c=self.controller()
        self.assertTrue(callable(getattr(c,'checkout_transition',None)),'Missing exact transition proof')
        real=c.c1_module(); seen={}
        def capture(*argv):
            seen[argv]=real.git(*argv); return seen[argv]
        c.checkout_transition(SimpleNamespace(git=capture))
        variants=[]
        for args,raw in seen.items():
            if args[0]=='rev-parse': variants.append((args,b'0'*40+b'\n'))
            elif args[0]=='rev-list': variants.append((args,raw.replace(c.sr3().HEAD.encode(),b'0'*40)))
            elif args[0]=='diff-tree': variants.append((args,raw+b'A\0unexpected.txt\0'))
            elif args[0]=='ls-tree': variants.append((args,raw.replace(b'100644',b'100755',1)))
            elif args[0]=='cat-file': variants.append((args,b'CONTROL_CHANGED_BLOB'))
        self.assertGreaterEqual(len(variants),5)
        for changed,value in variants:
            def altered(*argv): return value if argv==changed else seen[argv]
            with self.subTest(args=changed),self.assertRaisesRegex(ValueError,'E_SC_CHECKOUT'):
                c.checkout_transition(SimpleNamespace(git=altered))

    def test_protected_paths_are_derived_from_all_authority_families(self):
        c=self.controller()
        self.assertTrue(callable(getattr(c,'protected_paths',None)),'Missing complete authority-derived protected identities')
        authority={'source_manifest':{'src.py':'a'*64},'protected':{str(c.REPO/'package'):{'data.txt':'b'*64}},
                   'c1_inventory':{'source/original.py':'c'*64},'runtime':{'entry':{'path':str(c.REPO/'runtime.exe')}}}
        paths=c.protected_paths(authority)
        for path in (c.REPO/'src.py',c.REPO/'package/data.txt',c.c1_module().OUTPUT/'source/original.py',
                     c.REPO/'runtime.exe',c.SCRIPTS/'archive_copy_h1.py',c.sr3().ROOT/'sr3-prepare/Failure.json'):
            self.assertIn(path,paths)

    def test_reviewed_policy_child_is_required_before_copy_and_original_request_is_immutable(self):
        import hashlib
        c=self.controller(); data_path=SCRIPT.with_name('shutdown_copy_data.py')
        self.assertTrue(callable(getattr(c,'inspect_before',None)),'Missing unapproved policy inspection phase')
        self.assertTrue(callable(getattr(c,'bind_policy',None)),'Missing separately sealed policy binding phase')
        with tempfile.TemporaryDirectory(prefix='sc-policy-flow-') as name:
            base=Path(name); original=base/'old-data'; original.mkdir(); (original/'data.txt').write_bytes(b'evidence')
            target=base/'new-session'
            authority={'helper':c.record(SCRIPT),'data':c.record(data_path),'direct':'FIXTURE_NOT_RUNTIME','protected_identities':[[1,2]]}
            with patch.object(c,'ROOT',target),patch.object(c,'ROOTS',{'fixture':original}), \
                 patch.object(c,'DATA_SHA',hashlib.sha256(data_path.read_bytes()).hexdigest()), \
                 patch.object(c,'normal'),patch.object(c,'direct_authority',return_value=authority):
                first=c.before(); base_sha=first['config']['sha256']; initial=first['request']
                with self.assertRaisesRegex(ValueError,'E_SC_POLICY_NOT_BOUND'):
                    c.copy_phase('BEFORE',base_sha,initial['sha256'])
                proposal=c.inspect_before(base_sha,initial['sha256'])
                self.assertFalse(c.read(target/'Policy-Proposal.json')['policy_approved'])
                self.assertFalse((target/'BEFORE/reader-copy').exists())
                with self.assertRaisesRegex(ValueError,'E_SC_EXTERNAL_POLICY'):
                    c.bind_policy(base_sha,'0'*64)
                bound=c.bind_policy(base_sha,proposal['proposal']['sha256'])
                self.assertEqual(c.record(target/'BEFORE/Request.json'),initial)
                self.assertEqual(c.record(target/'Inputs.json')['sha256'],base_sha)
                value,_=c.session(bound['config']['sha256'])
                self.assertEqual(value['lineage']['proposal'],proposal['proposal'])
                copied=c.copy_phase('BEFORE',bound['config']['sha256'],bound['request']['sha256'])
                self.assertTrue(Path(copied['copies']['path']).exists())

    def test_policy_cannot_add_paths_outside_denied_coverage_or_omit_protected_ids(self):
        import copy
        c=self.controller()
        self.assertTrue(callable(getattr(c,'validate_policy',None)),'Missing closed policy validation')
        with tempfile.TemporaryDirectory(prefix='sc-policy-scope-') as name:
            root=Path(name); d=c.load_checked(SCRIPT.with_name('shutdown_copy_data.py'),__import__('hashlib').sha256(SCRIPT.with_name('shutdown_copy_data.py').read_bytes()).hexdigest())
            snapshot=d.SnapshotSet({'fixture':root},c.SESSION); request=snapshot.scan('BEFORE')
            protected=[[1,2]]; proposal=snapshot.inspect_denied_policies(request,protected)
            self.assertIsNotNone(c.validate_policy(proposal,request,protected,{'fixture':root}))
            changed=copy.deepcopy(proposal); changed['roots']['fixture']['protected_identities']=[]
            with self.assertRaisesRegex(ValueError,'E_SC_POLICY_PROTECTED'): c.validate_policy(changed,request,protected,{'fixture':root})
            changed=copy.deepcopy(proposal)
            changed['roots']['fixture']['allowed']['retained-temp/outside.txt']={'role':'HISTORICAL_NEGATIVE_TEST_CACHE_DATA_ONLY',
                'identity':[1,3,2,1,1,1],'size':1,'sha256':'a'*64,'permission_sha256':'b'*64}
            with self.assertRaisesRegex(ValueError,'E_SC_POLICY_COVERAGE'): c.validate_policy(changed,request,protected,{'fixture':root})

    def test_nonempty_denied_hardlink_policy_binds_and_copies_real_bytes(self):
        """Only access denial/account/history are controlled; file/link/policy/readback are real."""
        import copy
        import hashlib
        import os
        c=self.controller(); data_path=SCRIPT.with_name('shutdown_copy_data.py')
        d=c.load_checked(data_path,hashlib.sha256(data_path.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory(prefix='sc-linked-policy-flow-') as name:
            base=Path(name); original=base/'evidence'; original.mkdir(); hidden=original/'retained-temp'; hidden.mkdir()
            linked=hidden/'cache.bin'; linked.write_bytes(b'inert linked historical data')
            os.link(linked,hidden/'alias.bin'); original_acl=d.permission_digest(linked)
            target=base/'session'; authority={'helper':c.record(SCRIPT),'data':c.record(data_path),'protected_identities':[[1,2]]}
            real_scandir=os.scandir
            def normal_denied(path):
                if Path(path)==hidden: raise PermissionError('CONTROL_NORMAL_READER_DENIED')
                return real_scandir(path)
            with patch.object(c,'ROOT',target),patch.object(c,'ROOTS',{'fixture':original}),patch.object(c,'data',return_value=d), \
                 patch.object(c,'normal'),patch.object(c,'direct_authority',return_value=authority), \
                 patch.object(c,'validate_before_history',return_value={'fixture':'NOT_REAL_HISTORY'}):
                with patch('os.scandir',side_effect=normal_denied): first=c.before()
                self.assertEqual(c.read(target/'BEFORE/Request.json')['roots']['fixture']['unresolved'],{'retained-temp':'directory'})
                proposed=c.inspect_before(first['config']['sha256'],first['request']['sha256'])
                proposal=c.read(target/'Policy-Proposal.json'); self.assertEqual(len(proposal['roots']['fixture']['allowed']),2)
                info=linked.stat(); protected=[[info.st_dev,info.st_ino]]; bad=copy.deepcopy(proposal)
                bad['roots']['fixture']['protected_identities']=protected
                with self.assertRaisesRegex(ValueError,'TRUSTED_LINK'):
                    c.validate_policy(bad,c.read(target/'BEFORE/Request.json'),protected,{'fixture':original})
                with patch('os.scandir',side_effect=normal_denied):
                    bound=c.bind_policy(first['config']['sha256'],proposed['proposal']['sha256'])
                copied=c.copy_phase('BEFORE',bound['config']['sha256'],bound['request']['sha256'])
                with patch('os.scandir',side_effect=normal_denied):
                    verified=c.verify_before(bound['config']['sha256'],copied['copies']['sha256'])
                self.assertEqual(verified['status'],'SC_BEFORE_VERIFIED_NO_WORKLOAD')
                output=target/'BEFORE/reader-copy/fixture/data/retained-temp'
                for path in (output/'cache.bin',output/'alias.bin'):
                    self.assertEqual(path.read_bytes(),linked.read_bytes()); self.assertEqual(path.stat().st_nlink,1)
                self.assertEqual(linked.stat().st_nlink,2); self.assertEqual(d.permission_digest(linked),original_acl)


if __name__=='__main__': unittest.main()
