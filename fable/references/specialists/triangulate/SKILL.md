---
name: triangulate
description: >
  Confluence-based reasoning for judgments where multiple signals exist. Locates
  or grades anything by requiring several INDEPENDENT lenses to point at the same
  answer, merging correlated witnesses into families, grading overlap tightness
  (TIGHT / PARTIAL / SCATTERED / NONE), and refusing no-overlap targets. Use for
  trading zone grading (POC ∩ OI ∩ PRZ), multi-timeframe alignment, validating a
  project plan (budget + timeline + risk lenses), verifying research/news before
  acting on it, root-causing bugs (logs + metrics + repro), and any "how confident
  are we really" question. Triggers: /triangulate, $triangulate, "confluence",
  "independence check", "cross-check this", "how strong is this signal".
---

# Triangulate — Independence-Weighted Confluence

Many different eyes must see the same thing — but only if the eyes belong to
different people. Two witnesses who read the same newspaper are ONE witness.

The strength of a conclusion comes from three things: how many independent lens
families agree, how tightly their answers overlap, and nothing else. Agreement
count alone lies; correlated agreement is one agreement wearing costumes.

## When to run it

Run this instead of free-form judgment whenever a decision has 2+ measurable
signals pointing somewhere:

- **Trading zones**: is POC ∩ OI wall ∩ PRZ a real level? Grade A/B/C/D.
- **Multi-timeframe**: do daily + hourly + 15m agree on direction?
- **Project plans**: does the budget lens, timeline lens, dependency lens, and
  risk lens each support the same go/no-go?
- **Research/news**: two sources claim X — do they share an origin?
- **Debugging**: do logs, metrics, and a local repro all name the same culprit?

Do NOT run it when only one lens exists; say so and ask what second measurement
could be obtained rather than inventing confidence.

## The loop

### 1. TARGET
State in one line exactly what is being located or judged: "NIFTY support zone
for a long entry", "this plan is safe to execute", "this bug's root cause".
A moving target invalidates all downstream grades. If the target shifts
mid-analysis, restart from here.

### 2. LENSES
Enumerate every method that measures this target. For a price zone: POC, OI
wall, CPR, pivots, VWAP, fib, prior S/R. For a plan: cost model, schedule
estimate, dependency map, risk register, precedent (similar past projects).
For each lens write: what raw data it reads, and what decision rule turns data
into an answer. A lens you cannot state the data source for is not a lens.

### 3. INDEPENDENCE — the load-bearing step
Mark which lenses share the same underlying data or the same crowd:

- Same dataset → twins → merge into ONE family.
- Same derivation (fib retrace and fib extension) → one family.
- Same crowd (OI and options volume both = options traders' positioning)
  → correlated → count as one family unless shown to diverge historically.
- Model output citing its own training priors twice → still one witness.

Output a family table: `FAMILY | members | shared source`. Only FAMILIES carry
confidence weight. Typical independent families in trading: price structure
(levels), activity (volume/OI flow), time-cycle, external context (news/macro).

### 4. OVERLAP
Convert each family's answer into a RANGE (a zone, a date window, a cost band),
then intersect ranges across families:

- **TIGHT** — all family ranges share a small common region → grade A. Strong;
  act with normal sizing.
- **PARTIAL** — most families overlap, 1 outlier → grade B. Trade smaller /
  plan with contingency on the outlier dimension.
- **SCATTERED** — weak pairwise overlaps, no common core → grade C. Treat as
  watchlist, not actionable.
- **NONE** — no intersection → NO-GO. The honest output is "no trade / no
  approval", never a forced average of disagreeing lenses.

Grade numeric bands per domain (trading example: TIGHT ≤ 0.25×ATR spread,
PARTIAL ≤ 1×ATR). If the domain has no natural unit, define the band BEFORE
looking at the overlap, not after.

Bayesian weighting: confidence ≈ product of per-family likelihood ratios.
First agreeing family sets the base; each ADDITIONAL independent agreeing
family multiplies up (cap at ~×3 total); correlated additions multiply by ~1.0.
Two tight families beat five noisy ones.

### 5. OUTPUT
Emit exactly this shape:

```
TARGET: <one line>
FAMILIES:
| Family | Members | Shared source | Answer (range) |
OVERLAP: <TIGHT/PARTIAL/SCATTERED/NONE> — <common region or why none>
GRADE: A/B/C/NO-GO
RECOMMENDATION: <one clear action, or explicit no-go>
WEAKNESS: <which single family, if it flipped, collapses the conclusion>
```

The WEAKNESS line is mandatory: it names the cheapest thing to monitor that
would falsify the call.

## Anti-patterns (each voids the analysis)

1. **False confluence** — counting twins separately ("5 signals align!" where
   4 share one dataset). Fix: the family table is non-negotiable.
2. **Lens shopping** — adding lenses until agreement appears. Fix: fix the lens
   set at Step 2, before seeing any answers.
3. **Precision theater** — two weak lenses overlapping tightly ≠ strong. A
   grade inherits the weakest family's reliability; note lens quality per row.
4. **Averaging a NO-GO** — reporting "midpoint of scattered lenses" as if it
   were a finding. Disagreement IS the finding.
5. **Post-hoc bands** — choosing overlap thresholds after seeing where ranges
   land so the desired grade pops out.
6. **Silent target drift** — starting with "is this support" and ending with
   "is this a good stock". Restart the loop.

## Plugging into other skills

- **fable-method**: use triangulate as the decide step (its Step 3): the
  recommendation needs ≥ PARTIAL confluence of ≥2 independent families; a
  NO-GO routes back to evidence gathering, not to persuasion.
- **quant-compare**: run triangulate per candidate strategy before accepting
  its DEPLOY verdict; the sentiment overlay counts as one family max.
- **Plan reviews**: budget/timeline/risk/precedent are four families; a plan
  passing only budget+timeline (both derived from the same estimate sheet) is
  ONE family — demand a second origin (actual quotes, actual team velocity).

## Domain quick-starts

- **Zone grading (trading)**: families = structure (POC/pivots/S-R),
  positioning (OI/options crowd), geometry (fib/CPR). A-zone = all three
  within defined band; log every graded zone to build the historical hit-rate
  that later calibrates your bands.
- **MTF alignment**: higher timeframe sets family 1 (structure), mid TF
  momentum family 2, entry-TF trigger family 3. All must point the same way
  within their own units; never let the entry chart outvote the daily.
- **News verification**: find the earliest origin of each claim (who published
  first); N outlets citing one wire = one family. Act only when origins differ.
- **Root cause**: repro, logs, metrics are three families; a fix backed by only
  logs is hypothesis, not diagnosis — get the repro or metric confirmation.
