# VisDoc-Retrieve Resume Bullets

Use these bullets conservatively. Do not add percentage-improvement wording
unless a future reviewed claim checklist explicitly supports it.

## 中文版

- 构建 VisDoc-Retrieve 多模态文档检索评测项目，覆盖页面级数据清单、候选集冻结、BM25/lexical/RRF 基线、mock visual MaxSim 脚手架、hard-negative mining、训练门禁和最终对比协议。
- 设计并执行 one-time frozen final comparison：记录 run manifest、protocol/data/config hash、final metrics、claim checklist 和 no-retune pledge，确保 final test 读取后不再调参或重跑刷分。
- 将 A100 tiny LoRA runner、dev-only evaluation harness 和 final benchmark 明确分层，避免把 pipeline proof 或 scaffold 误写成模型性能收益。
- 产出 evidence index、Human Brief、项目卡和面试材料，使项目成果可审计、可复现、边界清晰。

## English Version

- Built VisDoc-Retrieve, a page-level document retrieval evaluation project with
  split-aware manifests, frozen candidate-universe metadata, BM25/lexical/RRF
  baselines, a mock visual MaxSim scaffold, hard-negative mining, training
  gates, and a frozen final-comparison protocol.
- Executed a one-time frozen final comparison with run manifest, protocol/data
  hashes, final metrics, claim checklist, and no-retune pledge to prevent
  result-driven retuning after final-test access.
- Separated A100 tiny LoRA runner evidence, dev-only evaluation harnesses, and
  final benchmark results so pipeline proofs were not overstated as model
  performance gains.
- Produced recruiter-facing evidence maps, human briefs, project card, and
  interview notes with explicit boundaries around unsupported benchmark claims.

## Conservative Version

- Built an evidence-rich document retrieval benchmark harness with deterministic
  baselines, frozen evaluation contracts, and final-result claim controls.
- Ran a single frozen final comparison and documented that no clear benchmark
  improvement claim was supported.
- Packaged project evidence for review while preserving no-retune, no-overclaim,
  and no-unavailable-metric-fabrication boundaries.

## Stronger Research-Engineering Version

- Designed a research-engineering workflow for multimodal document retrieval:
  candidate-universe freezing, split leakage controls, retrieval metrics,
  hard-negative mining, optional visual backend gates, training safety gates,
  and final benchmark governance.
- Implemented final-run governance with protocol hashes, data hashes,
  immutable run manifests, unsupported-claim blocking, and explicit
  unavailable-system status for missing visual/adapter rows.
- Demonstrated benchmark discipline by reporting mixed results honestly:
  deterministic lexical systems were evaluated, real visual/adapter systems
  remained unavailable, and the final checklist blocked any clear improvement
  claim.
