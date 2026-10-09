# Triangulate: independent evidence and honest overlap

Read the preserved [Triangulate source](specialists/triangulate/SKILL.md) after this adapter.

## Input

Provide a fixed decision target, evidence sources with dates/identities, each lens's raw-data lineage and decision rule, domain units, and predeclared overlap criteria. Same dataset, shared derivation, copied news, nested timeframe transformations, or the same model viewpoint do not automatically give independence.

## Procedure

1. State TARGET in one line. Fix the lens set and thresholds before inspecting outcomes. Changing the target restarts this analysis.
2. List each lens, its data origin(s), method, answer/range, freshness, reliability and limitations. A lens without provenance is unsupported.
3. Build connected evidence families: if lenses share any underlying origin, merge them, transitively. Record correlated uncertainty rather than counting each lens separately. Multiple hats reading one design are one origin family.
4. Reconcile disagreement within a family explicitly. For numeric summaries the utility uses a conservative enclosing interval; it does not shrink correlated readings to manufacture precision. Keep the raw intervals visible.
5. With fewer than two independent families, output `INSUFFICIENT`, no confluence grade, and the cheapest missing independent measurement.
6. For comparable numeric ranges, calculate intersections. TIGHT requires all families to share a common region and all family answers to fall within the predeclared uncertainty-width budget. A very wide unreliable interval cannot earn TIGHT by overlapping everything. PARTIAL requires a common core across more than half the families, with the dissenting families visible. Pairwise overlap without a majority common core is SCATTERED; no overlap is NONE.
7. For categorical or mixed-unit evidence, use a declared domain decision table instead of forcing interval arithmetic. State PASS/FAIL/UNKNOWN per family and material contradictions. Missing measurements remain unknown.
8. Report TARGET, FAMILIES table, OVERLAP, GRADE, RECOMMENDATION, WEAKNESS and cheapest falsifier. Grades are qualitative evidence descriptions, not calibrated probabilities or action authorization.

## Runnable numeric helper

Run `python <fable>/scripts/specialist_tools.py triangulate --input <reviewed-json>` after reviewing provenance and numeric units. Input shape:

```json
{"target":"scratch range check","unit":"seconds","max_tight_width":4,"lenses":[
 {"id":"measurement","origins":["direct-run"],"range":[10,12]},
 {"id":"independent-estimate","origins":["capacity-model"],"range":[11,13]}
]}
```

The utility calculates family grouping and overlap only. The model still has to verify independence, source quality, units, interpretation and recommendation. Save its stdout to a planned report if needed; it does not write canonical requirements or approvals.

## Compatibility and verification

The source's approximate Bayesian multipliers and trading sizing are retained as source text, not applied as universal rules. Do not manufacture confidence percentages or likelihood ratios. Do not infer a live trading action from A/B grades. Calibrated probabilities require a named measured dataset and validated model.

Verify duplicate origins collapse to one family, transitive origins merge, disjoint intervals produce NONE, contradictory families remain visible, missing sources fail validation, and broad ranges cannot create TIGHT. Register the actual family report and its independent review in Fable. Agreement is decision support, not proof of the underlying claim.
