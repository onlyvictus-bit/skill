# Semantic audit after mechanical coverage

## Contents

1. Purpose
2. Claim schema
3. Audit passes
4. High-risk language
5. Cross-chunk reasoning
6. Independent review
7. Completion wording

## 1. Purpose

Mechanical coverage can prove that every canonical chunk received a valid processing attempt. It cannot prove that the processor interpreted each chunk correctly.

Semantic audit is the layer that tries to falsify the synthesis.

## 2. Claim schema

For consequential findings, prefer a structure like:

```json
{
  "claim_id": "C-0042",
  "claim": "Entries after 11:30 are prohibited.",
  "source_id": "SRC-ORB-PLAN",
  "unit_ids": ["P001921"],
  "chunk_ids": ["CHUNK-000087"],
  "source_version": "sha256:...",
  "status": "SUPPORTED",
  "notes": []
}
```

Keep claims separate when scopes differ. Do not merge similar wording that has different conditions.

## 3. Audit passes

### Pass A — exact-value sweep

Recheck:

- numbers;
- thresholds;
- percentages;
- dates;
- times;
- counts;
- identifiers;
- versions;
- currency/units.

### Pass B — exception sweep

Search processed results and source units for:

- except;
- unless;
- only if;
- must not;
- never;
- at least / at most;
- before / after;
- deprecated;
- optional;
- unavailable;
- unknown;
- fallback.

### Pass C — contradiction sweep

Look for claims about the same subject that differ by:

- time/version;
- environment;
- instrument/user type;
- branch;
- mode;
- authority level;
- source priority.

Preserve genuine conflicts instead of forcing one answer.

### Pass D — boundary sweep

Inspect the first and last primary unit/chunk, very large units, tables, footnotes, appendices, and transitions between chunks.

### Pass E — negative-evidence sweep

Ensure that missing/unknown data was not converted into `false`, `zero`, `safe`, or `neutral`.

## 4. High-risk language

Pay special attention to:

- negations;
- double negatives;
- modal words (`must`, `should`, `may`);
- conditional logic;
- nested exceptions;
- comparative statements;
- legal/compliance language;
- formula definitions;
- unit conversions;
- temporal ordering.

## 5. Cross-chunk reasoning

Chunking can separate definitions from later usage.

Before final synthesis:

1. identify cross-references;
2. reopen defining units;
3. connect each dependent claim to the definition actually in force;
4. prevent a later example from silently replacing a governing rule;
5. distinguish repeated evidence from independent evidence.

Graphify can help discover relationships, but the audit must reopen direct source units.

## 6. Independent review

An independent model/reviewer can reduce correlated mistakes, but it is not an oracle.

Give the reviewer:

- the claim set;
- exact source-unit references;
- authority hierarchy;
- explicit request to disprove claims;
- permission to return `UNVERIFIED`.

Do not give only the first model's prose summary and call that independent verification.

## 7. Completion wording

Preferred:

`MECHANICAL COVERAGE: COMPLETE; SEMANTIC AUDIT: PASSED FOR DECLARED CHECKS; absolute understanding is not provable.`

Avoid:

`GPT understood every word perfectly.`
