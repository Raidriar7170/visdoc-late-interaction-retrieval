## Why

The repository now has a deterministic diagnostic MVP pipeline and an optional
local visual zero-shot backend scaffold, but later adaptation work still needs a
split-safe hard-negative mining checkpoint. This change creates the CPU-only
mining evidence needed before any future LoRA / QLoRA visual retriever training
without running training or claiming benchmark improvement.

## What Changes

- Add a config-driven hard-negative mining command,
  `PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives --config configs/hard_negatives.json`,
  for the fixed synthetic smoke corpus.
- Generate train/dev hard-negative JSONL triples from existing local ranking
  surfaces: BM25, lexical cosine, available RRF/hybrid text ranking, deterministic
  mock visual MaxSim ranking, same-document wrong pages, and tag-aware negatives
  when metadata support exists.
- Report unsupported or zero-support negative sources explicitly with
  `support: 0` or `null` evidence instead of fabricating results.
- Add leakage checks that prevent query/positive/test split leakage, reject final
  test usage in training artifacts, dedupe repeated candidates, and enforce
  deterministic ordering.
- Emit `data/derived/hard_negatives/train.jsonl`,
  `data/derived/hard_negatives/dev.jsonl`, `reports/hard-negatives/*`,
  a concise Chinese human brief, and a `reports/progress-ledger.yaml` entry.
- Add tests for leakage, split boundaries, duplicate removal, deterministic
  ordering, hard-negative schema round-trip, unsupported source reporting, CLI
  outputs, and unchanged MVP behavior.

## Capabilities

### New Capabilities

- `hard-negative-mining`: CPU-safe, deterministic train/dev hard-negative
  mining pipeline with split leakage checks, source-support reporting, JSONL
  triples, summary reports, run card, human brief, and progress-ledger evidence.

### Modified Capabilities

- None.

## Impact

- Affected code: `src/visdoc_retrieve/` hard-negative miner/config/CLI modules
  plus focused tests.
- Affected artifacts: `configs/hard_negatives.json`,
  `data/derived/hard_negatives/*`, `reports/hard-negatives/*`,
  `docs/human-briefs/*`, and `reports/progress-ledger.yaml`.
- No new runtime dependency, network access, model download, GPU/A100
  requirement, ColPali/ColQwen/BGE/sentence-transformers inference, training,
  adapter/checkpoint output, final-test evaluation, RAG/chatbot behavior,
  deployment, or benchmark-improvement claim is introduced.
