# Phase 6D one-time frozen final comparison

结论：Phase 6D 已执行一次 frozen final comparison；final test 已读取。
读取后不得再调参、改 pipeline、改 metrics、改 candidate universe
或改 final labels。

## 运行边界

- Protocol: `phase-6b-final-comparison-protocol/v1`
- Final split: `test`
- Final test read: `true`
- Training: `not_executed`
- A100 / SSH / GPU: `false`
- Model download: `not_executed`
- Benchmark improvement claim: `not supported`

## 实际运行的 systems

- `bm25`
- `bm25_lexical_rrf`
- `lexical_cosine`
- `mock_visual`

## Not available / not run

- `tiny_lora_adapter`
- `zero_shot_visual_backend`

## 解读

本次结果只支持最终冻结比较已经执行这一事实。
没有清晰 benchmark improvement claim。`mock_visual` 是 deterministic
mock scaffold；tiny A100 runner proof 仍是 pipeline proof，
不是正式训练收益。

## Evidence

- `reports/final-comparison/final-comparison-run-manifest.json`
- `reports/final-comparison/final-metrics.json`
- `reports/final-comparison/final-comparison-report.md`
- `reports/final-comparison/final-claim-checklist.json`
- `reports/final-comparison/no-retune-pledge.md`
