# Optional adapter contracts

The core must remain usable without these packages. Run `scripts/runtime_status.py` first. Missing dependencies are capability gaps, not permission to install them automatically.

## tiktoken — exact token accounting

Use `scripts/context_budget.py` when `tiktoken` is available.

Current upstream behavior:

- `tiktoken.encoding_for_model(model)` maps recognized model names/prefixes to encodings.
- Unknown mappings raise `KeyError` and instruct callers to use `get_encoding(...)` explicitly.

Claude Mon therefore fails closed for an unknown model instead of guessing a tokenizer. The batching function preserves required chunk order and schedules **all** chunks across as many batches as needed. If one required chunk exceeds usable context, split/rebuild it; never truncate it.

Primary references:
- https://github.com/openai/tiktoken
- https://github.com/openai/tiktoken/blob/main/tiktoken/model.py

## Docling — complex document extraction

Use Docling only as an extraction adapter, not as proof that every visual fact was captured.

Current official APIs document:

```python
from docling.document_converter import DocumentConverter
result = DocumentConverter().convert(path)
doc = result.document
```

`ConversionResult.status` can report success/partial/failure states and exposes parse/inference/timeout error checks. `DoclingDocument.save_as_json(..., sort_keys=True)` or `export_to_dict()` provides a structured JSON representation.

Safe integration sequence:

1. Hash/register the original binary as `kind=document`.
2. Convert locally with remote services disabled unless separately authorized.
3. Inspect conversion status and errors; preserve `PARTIAL_SUCCESS`/failures.
4. Serialize the `DoclingDocument` JSON deterministically where supported.
5. Hash/register that JSON separately as `kind=extracted-document` with provenance linking the original hash and extractor version.
6. Run Claude Mon unit/chunk/receipt coverage on the extracted representation.
7. Keep extraction completeness separate from model-processing coverage.
8. For scanned/layout-critical material, add page-image/visual comparison when the task requires fidelity the extractor cannot prove.

Do not use hypothetical fields such as `page.is_corrupted` or fake `0000...` hashes for failures.

Primary references:
- https://docling-project.github.io/docling/reference/document_converter/
- https://docling-project.github.io/docling/reference/docling_document/
- https://docling-project.github.io/docling/v2/

## Aider RepoMap — relevance ranking only

Aider's repository map is a concise, token-bounded view of important code symbols. It is useful for selecting which real files/symbols to open for a task; it is intentionally not a complete source read.

Current Aider implementation also keys its tag cache validity to file modification time. If integrating it into Claude Mon/Fable, bind accepted candidates to Claude Mon SHA-256 source versions and force refresh/rebuild when content identity differs.

Safe flow:

`changed/user-mentioned/failing symbols + Graphify candidates -> RepoMap ranking -> open actual source -> Claude Mon receipt`

Never:

`RepoMap output -> COMPLETE receipt`

Primary references:
- https://aider.chat/docs/repomap.html
- https://github.com/Aider-AI/aider/blob/main/aider/repomap.py

## Graphify — derived relationship memory

When Graphify is actually available, use it as candidate discovery and persistent derived relationship memory. Its graph may help find related documents/symbols before those sources are completely read.

Do **not** require a source to be `COMPLETE` before Graphify can help discover it; that would create a discovery deadlock. Instead distinguish:

- **discovery graph**: may contain hash-bound candidates not yet read;
- **trusted projection**: relationships used operationally must cite current source identities and stay subordinate to direct source verification.

Graphify never mints read receipts, requirements, approvals, or completion.

## Repomix — export/interoperability only

Use Repomix to create portable repository snapshots when needed. Its compression mode intentionally removes implementation details while preserving structures/signatures, so compressed output cannot satisfy complete-read requirements.

Its `--token-budget` is an export guard: current docs state output is still generated and the process exits non-zero when over budget. Do not reuse this as Claude Mon's execution token authority.

Primary references:
- https://repomix.com/guide/code-compress
- https://repomix.com/guide/command-line-options

## External model execution

Claude Mon deliberately does not hard-code a model provider. The host operator must:

- authorize any external content disclosure;
- supply the exact chunk payload and task spec;
- record the processor/model identity actually used;
- detect provider/tool truncation signals;
- preserve output artifacts/results separately;
- verify consequential semantics against source passages.
