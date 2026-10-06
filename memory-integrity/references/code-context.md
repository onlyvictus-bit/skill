# Repository and code-context integrity

## Contents

1. Two code-reading modes
2. Repository identity
3. Aider RepoMap
4. Graphify
5. Token budgeting
6. Direct-read rule
7. Complete repository audits
8. Worktree changes
9. Caches
10. Verification

## 1. Two code-reading modes

### Relevance mode

Goal: find the small set of code likely needed for the current task.

Use:

- user-mentioned files/symbols;
- failing-test symbols;
- changed files;
- imports/references;
- Graphify relationships;
- Aider RepoMap ranking.

### Complete-audit mode

Goal: prove every file/unit in a declared repository scope was processed.

Use an explicit source set + source registry + coverage manifests/receipts.

Do not confuse relevance mode with complete-audit mode.

## 2. Repository identity

Prefer immutable identities:

- commit SHA for committed repository state;
- Git tree/blob SHA for directory/file content;
- explicit hashes for dirty/untracked files included in scope.

A branch name is not immutable.

For active worktrees record:

- base commit;
- modified tracked files;
- untracked files in scope;
- deletions;
- submodule state;
- generated/vendor exclusions.

## 3. Aider RepoMap

Use Aider RepoMap as a task-specific relevance ranker.

Current inspected implementation uses definition/reference tags, graph ranking/PageRank, mentioned-file/identifier weighting, and bounded map generation.

Consequences:

- map output is a candidate index, not source truth;
- open real files before making claims;
- its long-text token calculation is an estimate, so use explicit `tiktoken` for governed budgets;
- mtime-based tag cache validation is operationally useful but not a sufficient source identity for governed proof.

## 4. Graphify

Use Graphify for persistent relationship discovery across project material.

Useful outputs:

- file-to-symbol links;
- requirement-to-code relationships;
- concept neighborhoods;
- likely dependent sources.

Never let a graph edge satisfy a complete read or current-source proof.

## 5. Token budgeting

A selected source set still has to fit active context.

Budget from explicit configuration:

```text
input_budget = context_limit
             - reserved_output
             - fixed_system/tool/history_overhead
             - safety_margin
```

Count selected text with the configured tokenizer. Unknown tokenizer/model mapping must fail closed.

## 6. Direct-read rule

The safe path is:

```text
RepoMap/Graphify/search candidate
    -> open real source
    -> verify source identity
    -> inspect relevant range or complete file as required
    -> create evidence/receipt
```

Never:

```text
repo map summary -> claim complete source read
```

## 7. Complete repository audits

Define scope explicitly:

- source extensions;
- directories;
- generated/vendor/test fixtures;
- binary assets;
- submodules;
- historical revisions or current tree only.

Enumerate the source set first. Register every required file or use a deterministic tree manifest. Then process that declared set.

A complete audit is impossible to verify if the set of required files itself is undefined.

## 8. Worktree changes

Dirty worktrees matter because repository HEAD may not equal the code being executed.

Before consequential code reasoning:

- inspect status/diff;
- preserve existing edits;
- bind source identity to actual working content;
- do not use only remote/default-branch files when local changes are in scope.

## 9. Caches

Any derived cache must be keyed/validated by content identity strong enough for the task.

Examples:

- RepoMap tags;
- embeddings;
- parsed ASTs;
- Graphify graph;
- Docling extraction;
- token counts.

If a cache cannot prove it corresponds to current content, treat it as a candidate optimization and regenerate/validate before consequential use.

## 10. Verification

For a code task, completion evidence should connect:

```text
requirement/source
  -> relevant file/symbol
  -> changed behavior
  -> tests
  -> end-to-end observation
```

For complete-audit tasks, add coverage proof over the declared repository scope.
