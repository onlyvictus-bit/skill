# W-COPY actual Before succeeded; reader-copy stopped on deliberate link fixture

Actual2026-10-22 continuation, not a new code build or runtime repair. User ran
the correct sealed new launcher Before. Parent reopened the saved request and
verified its exact SHA662384f96ba8ba4c3cc2b5572fde9ed2fbe4ee4e5cc6837a72a59998801d1245,
size1088921, fixed session/root/BEFORE schema and33current config roles. Normal
execution attribution is user-reported plus sealed guard behavior, not producer
authentication. Request contains2789readable objects and6058unresolved directories.
All unresolved roots are under the exact approved historical artifact archive;
not personal data outside scope. Existing reader-copy/run roots were absent.

## Approved next phase actually executed once

Controller3.14 worker_copy_successor.py --mode CopyBefore under the reader account,
with config6cb2c070072e98dc5000ed7e3b4805da74b44b4fdd6cb293f637d2a5a5bb6288
and exact externally supplied request SHA above. STOP exit1:

```text
archive_copy_snapshot.py read_file:
require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'E_COPY_FILE_LINK')
ValueError: E_COPY_FILE_LINK
```

Failure receipt retained at Documents/Codex/w-copy-20261022-7b7f219a/
CopyBefore-Failure.json;2741bytes,SHA
cff96876b74a8b9b45ff574b53bc6b8e88762dac010bbabcf4f71d5711d119ce.
Never rerun CopyBefore or remove that guard/partial output. No Copies.json,
Before Bundle, selected-runtime process or W workload exists. Partial output
has349files/700objects/1546714bytes; current map digest
0ba5943a7bdbd1ff1f4445f34bcb1359801935918c5e1f096328c847bafe35ee.
This is an observation of partial data, NOT an accepted snapshot or full source
preservation verdict. Output directories exist for88requested roots before the
first uncopied root. All files/receipts remain, no permission/Git/install action.

## Exact cause, verified read-only

First uncopied target:
.github/run-artifacts/offline-first-20261020/a-2172645b/retained-temp/tmphli3yxtt.
Two paths in workspace/old-image are regular files, not symlinks/reparse points:

- cache-alias.db
- cache.db

Both18bytes, content "old retained cache", same device9266887497040332852 and
inode562949955336190, link-count2. Each SHA
664060c3688d750c287ee877ab18697a76d020c7c96be866ee1191a318dae64b.
Current before/after read identities and contents unchanged. This is readable
by the reader account; the stop is NOT another access-denied error.

Primary origin: .github/tests/test_gate1_cleanup_preservation.py:83 explicitly
creates os.link(self.cache,alias), labelled "New test-owned hardlink, not user
evidence", to test that the older authoritative-input guard rejects links.
The observed bytes match setUp's b'old retained cache' at line30. This is a tiny
retained negative-test fixture, NOT the skill's active database.

Design gap: demanding a complete historical test-archive snapshot while refusing
all regular hardlinked fixtures makes this scope impossible. Our approved
W-COPY design explicitly rejects hardlinks; do NOT silently relax that contract
or call the complete snapshot passed. This was missed before handing off.

## Proposed COPY-H1 policy amendment — NOT approved/built

Recommend permitting read-only content capture of regular hardlinked HISTORICAL
SCRATCH DATA under this exact archive's retained-temp subtrees, recording each
original path/file-ID/link-count/size/hash and writing independent single-link
copies. Never copy link relationships, mutate originals, follow redirects or
execute copied historical code. Preserve single-link rejection for every live
source/helper/configuration/authoritative record and for all new destination
files; any nonregular/reparse/symlink object still blocks.

No-build retains this blocked failure. Excluding/moving/deleting old test data
would change coverage or preservation and is not recommended. Privileged OS
snapshot/access services would add unnecessary authority. A separately reviewed
and sealed successor with the narrow data-only policy is the smallest proposed
complete route; preserve the failed session, current code and all manifests.

Cheapest falsifier: two linked new scratch files must produce two independent
single-link copies with equal correct bytes while original IDs/link counts stay
unchanged; mutate the scratch original after BEFORE and require AFTER refusal.
Hardlinked executable/authoritative inputs and redirected sources must remain
refused. Include the known actual18byte fixture as read-only evidence, not a
production mutation. No fresh workload/copy retry until the policy decision and
reviewed successor exist. Current253controller evidence remains valid for old
code, not proof that the proposed amendment has been implemented or tested.
