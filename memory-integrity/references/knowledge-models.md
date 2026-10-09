# Optional local learned models / bridge 1.2

Core graph remains off by default. No provider credentials are needed for the qualified local route. This skill never automatically downloads weights or installs model packages.

## Prepare explicitly
From the matching GitHub repository checkout, use a separate supported Python 3.12 environment:

```sh
python3.12 -m venv /absolute/models-env
/absolute/models-env/bin/python -m pip install -r semantica-runtime/requirements-models.in
python semantica-runtime/Prepare-Models.py --destination /absolute/model-cache
python semantica-runtime/Verify-Models.py --manifest /absolute/model-cache/models.json
```

The preparation command downloads exactly the revision/file hashes in `semantica-runtime/models-lock.json`; changed existing files, partial transfers, extra files, symlinks and path escape fail. Model inference is offline and checks the complete file set every operation. The separate pinned Semantica interpreter retains its original runtime requirements. Windows uses the selected environment's `Scripts/python.exe`.

## Use through the front door
Supply `--model-python /absolute/models-env/bin/python --model-manifest /absolute/model-cache/models.json` plus the existing matching companion and pinned `--worker-python`.

- `knowledge-retrieve --query-text ... --embedding-mode learned`: actual mean-pooled, normalized MiniLM ONNX embeddings.
- Add `--rerank`: Qwen causal Yes/No likelihood scoring. This is a learned relevance score, not a model trained/qualified as a reranker.
- `knowledge-project` or `knowledge-refresh` with the selected model runtime additionally parses JavaScript/TypeScript syntax, preserving exact ranges and symbols. Import/call syntax is retained as navigation; unresolved targets are not invented. Python keeps its conservative static binding analysis.
- `knowledge-syntax --output NEW.json`: explicitly retained JS/TS source-bound parser observations.
- `knowledge-process --output NEW.json`: run the real local model on every authorized source unit, retaining raw prompts, token IDs/counts, source quotes and errors. COMPLETE is processing/quote identity only. Proposals remain unreviewed, unadmitted and semantic-truth UNVERIFIED.
- `knowledge-model-benchmark --output NEW.json`: actual generated whole-file patches in disposable projects; three independently authored boundary bugs, four comparison arms, fixed regression oracles. Malformed/truncated/unsafe patches and import/test failures remain failed model outcomes. A completed measurement can have zero successful patches.

Protected `offline-run` / `verify` use explicit `--knowledge-model-python` and `--knowledge-model-manifest` when replaying a learned/reranked schema-3 pack. A missing runtime, changed file/manifest, changed source/access, wrong generation, forged diagnostics or changed model operation blocks replay. No historical offline fixture becomes actual model evidence.

## Separate bounds and qualification
Learned retrieval supports at most 999 authorized nodes plus query; every embedding input is at most256 actual tokens including specials. Reranking supports at most100 authorized candidates. Generation renders the actual chat template and enforces4096 combined input+reserved output tokens, with at most2048 generated tokens. Inputs are never silently truncated. Corpus units that exceed a model bound produce retained errors/partial processing.

Observed runtime: MiniLM pinned revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41; Qwen2.5-Coder-0.5B-Instruct revisionea3f2471cf1b1f0db85067f1ef93848e38e88c25. Local socket/offline flags are best effort, not an OS sandbox. Never treat model prose as executable instructions or authoritative facts. Source-linked semantic review and task-relative admission remain independent.

The 12-trial coding experiment found0/3 regression passes in every arm. No coding benefit was shown, and graph remains opt-in. These small authored tasks and one repeat do not establish production workload quality or statistical significance. The public measurement summary and original-report fingerprint are retained in `docs/fable/derived/model-benefit.json`. Detailed prompts, outputs and test receipts remain in the user's private verification artifact; this skill never automatically exports runtime/source receipts to a public repository.

The direct benchmark CLI is qualified on POSIX with per-generation timers and refuses unsupported platforms. Core offline packages remain portable; this does not claim Windows qualification for the direct benchmark CLI.
