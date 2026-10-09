# Concurrent edit and dirty-worktree safety

Use at adaptive depth 2 or 3, and whenever other humans/agents may edit the same workspace.

## Before editing

1. Inspect repository status and record the dirty-worktree baseline.
2. Identify intended edit targets.
3. Record each target's content hash when practical; otherwise record mtime plus size and enough surrounding content to detect replacement.
4. Distinguish pre-existing user/agent edits from changes created by this task.

## Immediately before writing

Re-read/re-hash each target. If it changed since inspection, do not overwrite from the stale copy. Diff the concurrent change, integrate it deliberately, update the plan if scope/intent changed, and rerun any gate invalidated by the change.

## During execution

Use bounded concurrency. Parallel workers must have disjoint file ownership or isolated worktrees. Do not run competing formatters/generators over the same files. Never use reset, checkout, stash-pop, or bulk overwrite to erase unrelated work unless explicitly authorized.

## Before completion

Inspect the final diff/status. Verify every touched file belongs to declared scope or is separately explained. Remove scratch debris. For shared repositories, a clean targeted test does not prove concurrent edits were preserved; inspect the diff.
