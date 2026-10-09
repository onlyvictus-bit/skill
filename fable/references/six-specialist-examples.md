# Worked examples and verification boundaries

These examples are synthetic exercises, not claims about an actual deployed product.

## Cortex example: CSV import with graph documentation

Request: design and implement a CSV import, preserve existing data, show errors accessibly, map the affected code, and prepare a release without deployment.

| Need | Route | Stage | Result/check |
|---|---|---|---|
| Preserve exact scope and data | Fable + Cortex | intake | Requirement/constraint matrix and complete roster |
| Discover import consumers | Graphify if runtime exists, plus direct source reads | discovery | Known import-to-storage relationship; source confirmation |
| Complete import behavior | Blueprint | design | Valid/invalid/duplicate/interrupted cases, contracts, recovery |
| Judge two performance claims | Triangulate only with independent sources | decision | Provenance families; two copies of one benchmark count once |
| Multi-part implementation | Unlazy | execute | Parse/store/UI leaves plus parent integration gate |
| Prepared release, no deploy | Release Helper | delivery | Validated artifact/config identity; deployment remains pending |

When Graphify is unavailable, the roster records a graph-runtime gap. Direct source inspection can help implementation but does not satisfy the explicit native graph requirement. When the performance claims are copies of one run, the verdict is INSUFFICIENT.

## Blueprint example: two deliberate design omissions

Seed design: upload form sends CSV to an import endpoint, writes database rows, and shows success. It describes neither validation failures nor recovery from a partially applied import.

- Designer finding: error/partial states absent; user cannot identify rejected rows. Required correction: per-row validation results, accessible error summary and safe retry behavior, with a rendered invalid-input check.
- Developer/tester finding: interrupted writes can leave partially applied data. Required correction: transaction or staged import with explicit idempotency semantics; test mid-write interruption and duplicate retry.
- Operations finding: rollback/restore path absent. Required correction: define exact previous-state recovery and rehearse in scratch; a written command is only a plan.
- Security finding: upload size/type validation and authorization absent. Inspect the actual application before choosing limits; proposed limits need acceptance and measurement.

These remain unresolved design findings until corrected. A success-only screen plus unit tests cannot establish production readiness.

## Triangulate examples

Run the numeric helper with independent [10,12] and [11,13] second ranges and a predeclared width budget of 4 seconds: two families, common region [11,12], TIGHT. The same inputs with one shared origin: one family, INSUFFICIENT. Independent [1,2] and [5,6]: NONE. A wide [0,1000] interval plus [10,12] must not earn TIGHT with a width budget of 4. These are interval calculations; source reliability still needs review.

## Unlazy example

Create a scratch Node assertion that reads a JSON fixture and validates its actual value. A `--status` call must leave the fixture, check side effects and ledger unchanged. Run the reviewed check with `--approve`: expect a passing observation. Change the fixture to violate the assertion, then `--reverify`: the checked gate must return to unmet. A parent ledger that additionally contains a pending manual integration observation must stay incomplete even when its child command passes.

## Graphify example

Use `a.py` importing `b.py`, then run the real package's detect/extract/build/export and inspect the relationship. Modify the import and delete `b.py`, refresh, and ensure stale relationships are removed/invalidated. A status probe or manually authored graph is not this test. If the package is missing, the correct result is unavailable, not pass.

## Release example

Use labelled synthetic observations only. Matching environment/digest, zero exit, health and authorization pass consistency checks. Change one field at a time: wrong environment, stale digest, unhealthy runtime, nonzero exit or no authorization must fail. A string saying `Shipped.` cannot compensate for any of them. None of these local checks constitutes a real deployment or consent.

## Run the packaged regression suite

`python <fable>/tests/test_specialist_integration.py`

Tests use temporary directories, local fixtures and the bundled Unlazy runner. They do not install dependencies, invoke external models, install hooks or deploy. The suite tests deterministic helpers and gate behavior, plus native Unlazy execution. Cortex/Blueprint output semantics and full Graphify extraction need their separately stated observations; do not infer them from a unit-test count.
