# VisDoc Project Milestone Brief

## 一句话结论

VisDoc-Retrieve 目前已经完成到“可复现的检索/训练链路证据体系”阶段：
MVP、文本基线、候选集合、mock visual late-interaction、hard negatives、
训练门禁、A100 门禁、tiny runner proof 和 dev-only eval harness 都有证据，
但还没有 final benchmark，也没有任何 benchmark improvement claim。

## 现在完成了什么

- 有一个本地可运行的 diagnostic MVP pipeline，能生成 dev split 的检索证据。
- 有 BM25、lexical cosine、local-stub neural text、RRF 等文本基线诊断。
- 有 explicit candidate universe，避免候选页集合含糊。
- 有 mock visual late-interaction / MaxSim scaffold，用于链路和缓存验证。
- 有 optional visual backend scaffold，但不是默认真实视觉模型结论。
- 有 hard-negative mining 产物和 leakage check。
- 有 training readiness dry-run、安全门禁、blocked pilot launcher。
- 有 A100 runtime/model-path gate evidence，证明执行环境被逐步门禁化。
- 有 Phase 5J reviewed tiny A100 LoRA runner proof。
- 有 Phase 5K dev-only pilot evaluation harness，可记录 missing adapter 和比较
  schema，而不伪造指标。

## 可以对外展示的成果

- 项目从数据格式、检索基线、候选集合、视觉 late-interaction scaffold 到训练
  safety gates 的完整工程化路径。
- 所有关键阶段都有 reports、Human Brief、OpenSpec 记录。
- 默认路径 fail closed：缺少门禁、模型路径、依赖或 final-test 授权时不会
  悄悄训练或声称结果。
- 证据索引见 `docs/evidence-index.md`。

## 不能对外说成什么

- 不能说已经完成 final benchmark。
- 不能说 final test 已经评测。
- 不能说模型效果提升或超过 baseline。
- 不能把 `max_steps=1` / `sample_limit=1` 的 tiny runner proof 当作性能结果。
- 不能把 dev-only eval harness 当作 final test。
- 不能暗示 repo 提交了模型权重、adapter checkpoint、训练 cache、私有 config
  或 exact private model path。

## 为什么 tiny runner proof 不是 benchmark

Phase 5J 的 `max_steps=1` / `sample_limit=1` 只证明 reviewed A100 tiny LoRA
runner 能通过最小训练链路和安全门禁。这个预算太小，不能代表收敛、泛化、
模型质量或真实检索提升。因此它只能作为 pipeline proof。

## 为什么 dev-only eval harness 不是 final test

Phase 5K 只读取 dev split 和 sanitized pilot manifest。它记录 comparison
schema、missing-adapter `not_available` 状态和 no-fabrication 边界。它不读取
final test，也不生成 final benchmark table。

## 下一步

推荐下一步是受控的 longer dev training 或 final comparison freeze 设计：
先冻结 final-test protocol 和公开 claim 规则，再决定是否运行更长预算训练。
在此之前，GitHub 首页只应描述工程链路完成度和 evidence readiness，不应描述
benchmark improvement。
