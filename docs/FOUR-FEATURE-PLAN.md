# Four-feature plan (public summary)

Goal: extend the verified offline pair with task coordination, safe branch
policy, and protected evidence history — preserving rollback and manual-mode
truthfulness. Full text lives with the project workspace; this file records
the milestones, gates, and boundaries enforced here.

## Milestones
- **M3** contracts + adapter seams (isolated build, no activation).
- **M4** dependency graph + prerequisite enforcement (zero downstream calls
  on forced closure/late revocation; stale applicability refused).
- **M5** protected audit history (mutation refused, checkpoint-anchored
  replay, revocation preserved).
- **M6** branch policy + single-skill routing (compatible/conflicting cases
  in fixtures; old evidence never re-accepted post-merge).
- **M7** disposable native pilot + release (real round trips, four-trap
  comparison; requires separate runtime/installation approval).

## Non-goals until qualified
Native writes, effective ownership fences, live memory backends, OCR
transcription, and live model calls. Each needs its own approval and
observed evidence; offline `TEST_ONLY` results never qualify them.

## Source-recovery follow-up (2026-10-10)

An October 3 amended hybrid proposal supplies four concrete cases in the
user-provided recovered excerpts. Its connection to this native M7 grouping is
unconfirmed; it is not silently adopted as the original specification.
See [the source/evidence reconciliation and proposed cases](fable/derived/r5-source-reconciliation.md).
The full original plan and complete native four-trap qualification remain open.
