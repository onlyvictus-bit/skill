# Refresh project continuity after actual work

Fable state and current source remain authority. Resume is read-only; it NEVER
regenerates hashes to hide drift. A STALE result blocks using saved conclusions,
not investigation of the changed originals.

At the end of approved work:
1. Reopen changed originals, reconcile actual decisions/pending work in Fable.
2. Preserve Basis.json under a new uniquely named history file before replacing
   the current pointer. Keep every old source, review and protected-run folder.
3. Write a NEW versioned Current-Project source with precise citations, restrictions,
   unresolved failures and next work. Author real reviews of every declared unit.
4. Use installed memory_integrity_workflow.py offline-run with explicit companion,
   new source/reviews and a NEW run-dir. This is TEST_ONLY review accounting.
5. Explicitly approve the new source basis after reviewing the differences, then
   seal the referenced canonical files, helper/tests/AGENTS, installed skill files,
   new source/reviews/run-map and every protected artifact in a NEW Basis document.
   Publish the current Basis.json only after the existing verifier accepts the run.
6. Run verify_project_resume.py in a separate process. Retain output and hashes.
Never re-use a consumed run-dir for changed reviews. Never label this service
restart persistence, complete repository comprehension or automatic global recall.
A new chat must obey AGENTS instructions; observed model recovery is bounded to
its declared checkpoint facts. A filesystem owner can replace both basis/source.

Reusable installed helper: memory-integrity/scripts/project_continuity.py.
Follow references/codex-project-continuity.md for Seal-Request schema. After
reviewed new records, call --seal-request docs/fable/continuity/Seal-Request.json
with --expected-basis-sha256 of the exact previous Basis.json. The helper first
verifies the new protected run, retains the old basis and checks a publication
lease. Then run the normal read-only entry again. Never edit a frozen run.
