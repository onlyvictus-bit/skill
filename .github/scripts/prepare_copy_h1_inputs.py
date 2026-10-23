"""One input-only COPY-H1 capture using Python integer-safe JSON throughout.

Writes NEW exact input files, retains earlier unsealed drafts, starts no copy
phase or worker. No deletion, ACL edits or old-state/baseline replacement.
"""
import os
from pathlib import Path
import stat

import archive_copy_snapshot as v
import archive_copy_h1 as h
import worker_copy_successor as prior
import worker_copy_h1 as c


def main():
    v.require(not c.CONFIG.exists() and not (c.ROOT/'BEFORE').exists() and
              not c.POLICY.exists() and not c.ENTRY.exists(),'E_H1_PREPARATION_ALREADY_FROZEN_OR_CREATED')
    old,w = prior.verify_config(c.OLD_SHA)
    request = v.load(prior.ROOT/'before/Request.json',
        '662384f96ba8ba4c3cc2b5572fde9ed2fbe4ee4e5cc6837a72a59998801d1245')
    protected = [Path(path) for path in old['files']]
    for package in ('memory-integrity','claude-mon'):
        for parent,dirs,files in os.walk(prior.REPO/package,followlinks=False):
            for name in dirs+files: v.ordinary(Path(parent)/name)
            protected.extend(Path(parent)/name for name in files)
    allowed = []
    def denied(error): raise error
    for target in request['unresolved']:
        for parent,dirs,files in os.walk(w.ARTIFACTS/target,followlinks=False,onerror=denied):
            for name in dirs+files:
                path = v.ordinary(Path(parent)/name); info = path.stat()
                if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
                    v.require(info.st_nlink == 2 and info.st_size == 18 and
                              path.read_bytes() == b'old retained cache','E_H1_UNKNOWN_HISTORICAL_LINK')
                    allowed.append(path)
    v.require(len(allowed) == 56,'E_H1_SCOPE_INCOMPLETE')
    policy = h.make_policy(w.ARTIFACTS,allowed,protected)
    context = h.Context(policy)
    observations = {path.relative_to(w.ARTIFACTS).as_posix():context.read_file(path) for path in allowed}
    objects,unresolved = v.collect(prior.ROOT)
    v.require(not unresolved,'E_H1_FAILED_HISTORY_UNREADABLE')
    entry = {'old_root':str(prior.ROOT),'old_objects':objects,
        'scope_observation':{'allowed_historical_paths':observations,
            'unresolved_root_source':v.record(prior.ROOT/'before/Request.json'),
            'origin':v.record(prior.REPO/'.github/tests/test_gate1_cleanup_preservation.py'),
            'origin_call':'os.link(self.cache, alias) deliberate negative fixture',
            'observed_utc':h.now(),
            'reader_scan_scope':'ONLY_6058_EXACT_PRIOR_REQUEST_TARGETS_NOT_WHOLE_ARCHIVE'},
        'producer_authentication':False}
    c.validate_scope_entry(policy,entry,originals=True)
    c.check_failed_history(prior.ROOT,entry['old_objects'])
    v.save(c.POLICY,policy); v.save(c.ENTRY,entry)
    print(__import__('json').dumps({'status':'EXACT_INTEGER_INPUTS_ONLY_NO_COPY_OR_WORKER',
        'policy':v.record(c.POLICY),'entry':v.record(c.ENTRY),
        'historical_paths':len(allowed),'failed_history_objects':len(objects)}))


if __name__ == '__main__': main()
