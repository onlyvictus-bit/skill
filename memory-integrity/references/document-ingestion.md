# Rich-document ingestion and extraction proof

## Contents

1. Why extraction is a separate proof
2. Original inventory
3. Canonical document representation
4. PDF/scanned documents
5. Tables and layout
6. Office documents
7. Page/element identities
8. Extraction verdicts
9. Verification strategy
10. Limits

## 1. Why extraction is a separate proof

A downstream coverage engine can prove only the canonical representation it receives.

If the extractor silently lost a table, page, image label, or OCR text, 100% canonical coverage still misses the original content.

Therefore:

```text
ORIGINAL COMPLETENESS != CANONICAL COVERAGE
```

## 2. Original inventory

Before extraction record, where applicable:

- original file SHA-256;
- byte size;
- MIME/format;
- page/slide/sheet count;
- encryption/protection state;
- embedded files/objects if in scope;
- acquisition provenance;
- parser/extractor version and options.

For a PDF, page count is a minimum inventory. For scanned pages, presence of a page image with zero extracted text is not proof the page is empty.

## 3. Canonical document representation

Prefer a structured representation that preserves:

- page identity;
- element type;
- reading order;
- table structure;
- section hierarchy;
- bounding/provenance information where useful;
- image/figure references;
- extractor warnings.

Docling's `DocumentConverter`/`DoclingDocument` path is suitable as an adapter when available. The monitor's own hashes/manifests remain the completeness authority.

Do not make a lossy Markdown export canonical merely because it is convenient to read.

## 4. PDF/scanned documents

Classify pages:

- native text available;
- mixed native text + image;
- image-only scan;
- extraction error;
- encrypted/unsupported;
- intentionally excluded.

OCR/vision should be invoked only where required, and its output should carry lower-confidence/provenance status when appropriate.

A page that fails OCR remains a visible failure. Do not replace it with empty text.

## 5. Tables and layout

Tables create common silent-loss modes:

- merged cells flattened;
- row/column headers detached;
- footnotes lost;
- multi-page tables split incorrectly;
- visual grouping mistaken for reading order.

When tables matter, canonicalize cells/rows with stable identities and preserve page/section provenance. Semantic audit must compare important table claims against structured cell evidence, not only flattened prose.

## 6. Office documents

DOCX/PPTX/XLSX can contain:

- headers/footers;
- speaker notes;
- comments;
- text boxes;
- charts;
- hidden rows/slides;
- embedded objects;
- tracked changes;
- formulas vs displayed values.

Define which content classes are in scope before declaring extraction complete.

## 7. Page/element identities

Recommended identity pattern:

```text
DOC-<source-id>
PAGE-0001
PAGE-0001-ELEM-0001
PAGE-0001-TABLE-0001-ROW-0003-CELL-0002
```

IDs should be deterministic for a fixed canonical extraction when possible.

Bind each element to:

- page/slide/sheet;
- canonical serialized content hash;
- original source hash;
- extractor version;
- optional coordinates/structure metadata.

## 8. Extraction verdicts

Use:

- `NOT_APPLICABLE` — direct canonical text/code;
- `COMPLETE` — all required content classes were extracted with no unresolved failures;
- `PARTIAL` — some required content is missing/uncertain;
- `ERROR` — extraction failed materially;
- `UNKNOWN` — completeness was not assessed.

Do not use `COMPLETE` merely because the extractor returned a document object.

## 9. Verification strategy

For consequential rich-document work:

1. compare original page count with canonical page inventory;
2. flag zero-text pages for visual inspection unless known blank;
3. compare table counts/important tables where feasible;
4. inspect extractor warnings;
5. visually sample difficult pages, first/last pages, and pages with tables/figures;
6. preserve unresolved pages as explicit failures;
7. only then run canonical source coverage.

Use built-in vision before OCR when a human-style visual inspection is available; OCR is a fallback for machine text extraction, not a proof of visual completeness.

## 10. Limits

There is no universal extractor that mathematically proves it captured every meaningful visual fact from arbitrary documents.

The correct engineering response is explicit extraction evidence, page/element inventories, visual challenge checks, and honest uncertainty—not the word "lossless" used without qualification.
