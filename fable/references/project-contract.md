# Fable project contract — schema v2

`docs/fable/` is the authoritative project record. Keep it machine-readable, diffable, and single-source. StrictDoc, GSD, reports, dashboards, and specialist skills may derive from these files; they never become a second authority.

## Canonical files

- `requirements.json`: requirements, atomized acceptance criteria, test IDs, and optional source links.
- `plan.json`: approved work tasks mapped to requirement IDs, criterion IDs, test IDs, and artifact paths.
- `tests.json`: typed verification definitions. Test definitions are approval-bound content.
- `approvals.json`: append-only approval records bound to requirements, plan, tests, and the repository write-set baseline.
- `state.json`: resumable state bound to the same three content digests.
- `evidence/index.json`: pointer/index for append-only evidence runs.
- `evidence/runs/<run-id>.json`: immutable-by-contract observations for one verification run.
- `derived/`: non-authoritative generated projections such as StrictDoc. Derived files may be deleted and regenerated.

All canonical JSON documents use `"schema": 2`. Schema v1 is rejected rather than guessed or silently migrated during a gate.

## Requirements

```json
{
  "schema": 2,
  "requirements": [
    {
      "id": "REQ-01",
      "text": "Preserve all approved requirement details",
      "priority": "required",
      "criteria": [
        {
          "id": "REQ-01-A",
          "text": "A missing approved detail blocks execution",
          "test_ids": ["TEST-01"],
          "source_links": [
            {"path": "src/requirements.py", "function": "validate_requirements"}
          ]
        }
      ],
      "test_ids": ["TEST-01"],
      "source_links": []
    }
  ]
}
```

Priorities are exactly: `blocking`, `required`, `recommended`, `future`, `rejected`.

Every `blocking` or `required` requirement must declare one or more `test_ids`. Every criterion must also declare one or more `test_ids`; criterion-to-verification traceability is direct, not inferred from a task merely mentioning the criterion.

IDs must be non-empty and unique in their namespace. All requirement, criterion, test, and plan references must resolve. Unknown fields are schema errors so a typo such as `requred` cannot silently weaken enforcement.

`source_links` are optional and are for traceability. Each link has a project-relative `path`, plus at most one of `function` or `class`, and optionally a positive `[start, end]` `line_range`. Paths must remain inside the project root.

## Plan

```json
{
  "schema": 2,
  "plan_id": "m1-v1",
  "milestone": "M1",
  "tasks": [
    {
      "id": "TASK-01",
      "requirement_ids": ["REQ-01"],
      "criterion_ids": ["REQ-01-A"],
      "test_ids": ["TEST-01"],
      "artifacts": ["src/requirements.py"],
      "action": "Implement deterministic requirement preservation"
    }
  ]
}
```

Artifact paths must be project-relative and must not be absolute, contain `..`, use a drive/UNC escape, or resolve through a symlink outside the project root.

The plan gate requires every blocking/required requirement, each of its criteria, and every required test to be represented by mapped tasks. A task may map multiple related IDs, but it may not reference unknown IDs.

## Verification definitions

Prefer argument-vector execution so the shell is not involved:

```json
{
  "schema": 2,
  "tests": [
    {
      "id": "TEST-01",
      "kind": "automated",
      "argv": ["python", "-m", "unittest", "tests.test_requirements"],
      "expect": "exit=0",
      "source_links": [
        {"path": "tests/test_requirements.py", "function": "test_missing_detail_blocks"}
      ]
    },
    {
      "id": "TEST-VISUAL-01",
      "kind": "visual",
      "instructions": "Inspect the rendered page at desktop and mobile sizes and confirm no clipping.",
      "source_links": []
    }
  ]
}
```

Verification `kind` is exactly one of: `automated`, `runtime`, `visual`, `manual`, `performance`, `data`, `operational`.

The built-in runner executes only `automated` verification. `argv` is run with `shell=False`. The runner intentionally supports only `expect: "exit=0"`; richer automated assertions belong inside the invoked test program so Fable cannot claim to have checked semantics it did not evaluate.

A shell command is an exceptional escape hatch. It is valid only when the test definition includes `shell_authorized: true` and a non-empty `authorization_ref`. Because `tests.json` is approval-bound by `tests_digest`, later replacing a strong test with a weaker command invalidates the approval before the command can run.

Non-automated verification uses `instructions` and is recorded with the `record-evidence` command after the observation actually occurred. Never fabricate a manual, visual, runtime, performance, data, or operational pass.

## Approval snapshot and trust boundary

After the plan gate passes and immediately before asking for approval, generate the exact approval basis:

```text
python <skill>/scripts/fable_guard.py snapshot --project <root>
```

The snapshot returns:

- `requirements_digest`
- `plan_digest`
- `tests_digest`
- `write_set_baseline` — current Git write-set paths mapped to their content identity

An approval record requires:

```json
{
  "id": "APP-M1-001",
  "scope": "M1",
  "approved": true,
  "requirements_digest": "<sha256>",
  "plan_digest": "<sha256>",
  "tests_digest": "<sha256>",
  "write_set_baseline": {},
  "approved_at": "<ISO-8601 timestamp>",
  "actor": "user",
  "authorization": {
    "source": "conversation",
    "quote": "<the user's authorizing words>"
  }
}
```

The guard checks that all three digests still match. Any requirement, plan, or test-definition change invalidates approval.

Authorization metadata makes the trust boundary explicit but is not a cryptographic proof that a chat message came from the user. The orchestrator must populate it from actual user authorization; a local script cannot authenticate a conversation on its own. Do not manufacture the quote to satisfy the schema.

## Approved write-set

Execution and completion compare the current Git write set with `write_set_baseline`. A pre-existing dirty file is grandfathered only at the exact identity present at approval; changing that file later is a new write.

New or changed paths after approval must be either:

1. an artifact explicitly named in the approved plan, or
2. permitted Fable metadata under `docs/fable/`, including append-only evidence runs and derived StrictDoc files.

An unplanned changed file blocks execution/completion. The guard requires the supplied project root to be the Git repository root for write-set enforcement.

## Recovery state

`state.json` uses schema v2 and binds recovery to all three content digests:

```json
{
  "schema": 2,
  "milestone": "M1",
  "current_task": "TASK-01",
  "next_action": "Run focused verification",
  "completed_requirement_ids": [],
  "basis": {
    "requirements_digest": "<sha256>",
    "plan_digest": "<sha256>",
    "tests_digest": "<sha256>"
  }
}
```

A fresh session must pass the `resume` gate before work continues. Requirement, plan, or test drift blocks recovery until the canonical records and approval are reconciled.

## Append-only typed evidence

Automated execution:

```text
python <skill>/scripts/fable_guard.py run-tests --project <root>
```

Typed non-automated observation:

```text
python <skill>/scripts/fable_guard.py record-evidence \
  --project <root> \
  --test-id TEST-VISUAL-01 \
  --requirement-id REQ-01 \
  --criterion-id REQ-01-A \
  --result pass \
  --observer "<who observed it>" \
  --source "<where/how it was observed>" \
  --note "<concise observation>"
```

Each invocation creates a new `evidence/runs/<run-id>.json` and appends that ID to `evidence/index.json`; it does not replace previous run files. Evidence is bound to the current requirements, plan, and tests digests plus the exact planned artifact set and its current content digest.

Completion accepts only the declared evidence type, correct requirement/criterion links, exact approved artifact scope, current artifact content, and current three-digest basis.

The append-only rule is a project contract. The guard refuses to overwrite a run ID it creates, but a user with raw filesystem access can still delete or rewrite files. Use source control or an external append-only store if tamper-evident audit history is required beyond the local project threat model.

## Semantic-loss rule

A long requirement with several independently important details is not one atomic requirement. Split those details into stable criterion IDs before approval. The guard can enforce IDs and mappings; it cannot prove semantic equivalence of arbitrary prose that was never atomized.

## Change rule

Never edit an old approval to make changed requirements, plan, or tests look approved. Preserve the old record and append a new approval with a fresh snapshot. Evidence from the old basis remains historical and does not prove the changed basis.


## Additive recovery-example correction and specialist record

The earlier recovery example omits two fields required by the supplied validator. Preserve that example for history; when authoring state, also supply non-empty `campaign_id` and `phase`, for example `"campaign_id": "my-project", "phase": "verify"`. All other existing state fields and digest requirements remain.

The extension record is `docs/fable/specialists.json`, schema `1`, with the structure in `six-specialist-operation.md`. It supplements, never replaces, schema-v2 requirements/plan/tests. Declare this exact path and specialist result files in approved plan artifacts: the original guard automatically exempts only its listed metadata and StrictDoc paths, not arbitrary specialist directories. The wrapper checks the record and original guard together. Do not add unknown fields to the original schema-v2 documents.
