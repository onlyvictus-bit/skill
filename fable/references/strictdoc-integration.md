# StrictDoc integration — optional derived traceability

StrictDoc is an optional projection and visualization layer. `docs/fable/` remains the only authoritative requirement, plan, approval, state, and evidence store.

## Boundary

Never hand-edit generated StrictDoc as a way to change Fable requirements. The flow is one way:

```text
docs/fable/ canonical JSON
        |
        v
strictdoc_adapter.py
        |
        v
docs/fable/derived/strictdoc/
```

Deleting the derived directory must not lose authoritative information. If a StrictDoc report disagrees with canonical Fable JSON, Fable JSON wins and the projection must be regenerated.

## What the adapter projects

`requirements.json` requirements and criteria become StrictDoc requirements with stable UIDs. Criterion records receive Parent relations to their requirement. Optional Fable `source_links` become StrictDoc File relations with function, class, or line-range detail. Test `source_links` are projected onto the requirements/criteria that declare those test IDs, which gives a requirement → test source relationship without moving authority into StrictDoc.

Supported test-report copies are intentionally narrow and match the StrictDoc 0.30.1 integration formats used by this adapter: pytest, CTest, Google Test, LLVM LIT, cargo-nextest JUnit XML, and Robot Framework XML. Generic XML is not imported merely because it has an `.xml` suffix.

StrictDoc's own documentation labels parts of test-report integration experimental. Treat generated traceability reports as additional evidence/visualization, not as a Fable completion oracle.

Official references used when this adapter was built:

- Release notes: https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_04_release_notes.html
- User guide / test reports: https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide-TRACE.html
- Requirement/source traceability: https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_21_l2_high_level_requirements-TRACE.html

The adapter target is StrictDoc `0.30.1`. Re-verify the current StrictDoc schema and CLI before changing that target.

## Commands

Generate or refresh the derived projection:

```text
python <skill>/scripts/strictdoc_adapter.py generate --project <root>
```

Verify that the derived projection still matches canonical requirements, plan, and tests digests and has not been edited:

```text
python <skill>/scripts/strictdoc_adapter.py check --project <root>
```

Check whether an actual StrictDoc runtime is available:

```text
python <skill>/scripts/strictdoc_adapter.py runtime-status --project <root>
```

If the CLI is absent, record `STRICTDOC_UNAVAILABLE`. Do not describe generation of `.sdoc` text as a successful StrictDoc runtime/export test.

Installing StrictDoc is a dependency-install action and requires the normal Fable authorization boundary. Do not auto-install it merely because the adapter exists.

## Completion role

StrictDoc may add useful traceability views such as requirement → source/function/range and requirement → test/report relationships. It does not waive any Fable gate. Completion still requires Fable's exact approval basis, write-set gate, typed fresh evidence, artifact freshness, and adversarial verification.
