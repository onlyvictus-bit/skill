---
name: cortex
description: >
  Meta-cognitive router that reads a prompt, extracts its full requirement set,
  scans every installed skill for what the task actually needs, assembles the
  optimal skill team, and runs the reasoning spine — fable-method (process) ->
  deep-plan (approach) -> blueprint (production design) -> triangulate
  (confidence) — with specialist skills attached at the right stage. Use when
  the user wants the BEST possible result without choosing tools themselves:
  /cortex <task>, "use everything you have", "best possible result",
  "solve this completely", "AGI mode", "pull in whatever skills are needed".
---

# cortex — Requirement-Driven Skill Assembly

A model that picks its own tools per task beats one that uses the same three
every time. This skill turns "what does this prompt NEED?" into an explicit
team roster before any work starts.

## Phase 1 — Requirement extraction

From the user's exact words, produce two lists:

1. **Explicit asks** — what they literally requested.
2. **Implied needs** — what must be TRUE at the end for the result to work:
   data provenance (live market data? docs?), verification type (tests?
   rendered page? backtest stats?), output format (report? code? spreadsheet?
   slides?), domain knowledge (trading? legal? Windows internals?), scale
   (one file vs whole repo), risk surface (money, deploy, irreversible).

An implied need nobody listed is where failures live — sweep for them first.

## Phase 2 — Inventory scan

Match each need against the AVAILABLE SKILLS catalog (visible in system
context). For each candidate record: `need -> skill -> why it fits -> stage
it serves`. Selection rules:

- **Minimal sufficient team**: pick the fewest skills that cover every need.
  Overloading context degrades reasoning more than a missing convenience.
- **Specialist > general**: prefer the dedicated reader/tool skill over a
  generic fallback (e.g., yfinance-data over opencli-reader for stock data).
- **Gap honesty**: if NO skill covers a need, write `GAP: <need> - no tool;
  fallback: <manual research / ask user>`. Never pretend coverage.
- Name each chosen skill's STAGE: evidence gathering, approach decision,
  production design, confidence grading, execution, or delivery format.

## Phase 3 — Assemble and run the spine

Core spine is fixed; specialists attach around it:

```
fable-method   -> process/evidence gate        (always)
  [specialists: data/domain skills feed evidence HERE]
deep-plan      -> council picks the approach    (plan/build decisions)
blueprint      -> production-complete design    (buildable outcomes)
triangulate    -> independence-graded verdict   (before recommending)
  [specialists: export/report/viz skills shape DELIVERY]
execution      -> approved scope only           [tooling skills here]
```

Announce the roster in one line before starting:
`TEAM: fable-method | deep-plan | blueprint | triangulate + <specialists>; GAPS: <none/list>`
then execute. Mid-task discoveries of a new need re-run Phase 2 (say so).

## Phase 4 — Delivery

Final report follows fable Step 6 (outcome-first, caveats, unverified claims
labeled), formatted by whichever delivery skill was rostered. Close with the
roster line again plus what each contributed — so the user learns which tools
earned their place and can prune the rest.

## Hard rules

- Never skip Phase 2 because the task looks familiar; familiarity is where
  stale routing happens.
- A specialist skill beats the base model's memory every time both exist.
- If the roster exceeds ~8 skills, split the task into phases instead of
  loading everything at once.
- The spine is not optional for consequential decisions; specialists extend
  it, they never replace it.
