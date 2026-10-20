# Authored fixture requirements

Current input is at most 300 seconds old and is never from the future.
Revoked access blocks processing even when the input is fresh.
Checkpoint reopening binds exact UTF-8 source bytes; a changed dependency
must be reopened and verified, not accepted from an old successful run.
This is a mechanical test fixture, not a live AI review or production policy.
