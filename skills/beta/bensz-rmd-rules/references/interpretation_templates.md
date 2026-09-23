# 深度解读写作骨架（证据锚定）

用于把四层内容（数据描述、统计见解、领域映射、局限与后续）写成当前结果的连贯叙述。占位符必须替换为本次对象和数值，数值优先使用 `` `r ...` ``；阈值统一来自 YAML `params`。任何“可能/提示/建议验证”都要补对象、动作和判据。禁止用代码拼接整句解释文本。

## 写作前四问与硬门槛

1. 负责人最想确认/反驳什么？
2. 发现如何改变机制、分层或风险理解（只写可证伪推断）？
3. 基于结果优先做/不做什么，为什么？
4. 不复现时最可能的样本量、混杂、批次或模型原因是什么？

不要机械输出“数据描述：…统计见解：…”四段，也不要写“这张图/表用于……”而不陈述当前观察。最终正文通常为 1–2 段自然叙述，关键观点可加粗。

## 默认连贯叙述

```markdown
本次分析在 `r N` 个样本/对象上评估了 `r target`，阈值为 `r threshold`（来自 `params`），共有 `r n_sig` 个信号入围。
**最强信号为 `r top_1`、`r top_2`、`r top_3`**（`r metric` = `r value`，方向 `r direction`），并与 `r anchor` 一致。
这对 `r domain_context` 的意义是 `r domain_mapping`；不确定性来自 `r uncertainty_source`（`r uncertainty_value`），当前证据等级为 `r evidence_level`。
后续：1) 用 `r method_1` 在 `r input_1` 上验证，判据 `r criterion_1`；2) 用 `r method_2` 在 `r input_2` 上验证，判据 `r criterion_2`。
```

可为每个 cohort/亚组附核心结论：Top 1–3、证据强度、主要不确定性和后续动作。小表应只汇总当前对象、数值、排名/对比、证据等级和下一步，不重复整段解释。

## 反模式与替代

- 只报 p/q，不报效应大小、方向和不确定性。
- 只写“具有临床意义/可解释/可行动”，不落到变量、决策动作和验证。
- 写“建议进一步研究”，但没有方法、输入、判据。
- 写“可能混杂/非线性”，但不指出对象和检验方式。

替换为：“`X` 的效应为 …（CI …），与 `Y` 相比 …；不确定性来自 …。用 … 在 … 上验证，支持条件为 …。”

## 模板 0：核心结论（cohort/亚组）

```markdown
本 cohort（`r cohort_label`，N=`r n_all`）中，`r event_set` 与目标呈 `r direction` 趋势（rho=`r rho`，p=`r p`），主导维度为 `r dominant_dimension`。
**最强信号为 `r top_1`、`r top_2`、`r top_3`**（当前值 + 阈值 + 稳健性证据），与宏观方向 `r consistency`。因此证据等级为 `r evidence_level`，主要不确定性是 `r uncertainty`。
后续：1) `r stratified_method` 于 `r input`，判据 `r criterion_1`；2) `r resampling_method`，判据 `r criterion_2`；3) 必要时在 `r external_cohort` 复现，判据 `r criterion_3`。
```

## 模板 1：单因素筛选 / 批量回归

报告候选特征数、方法/结局、q/p 阈值和入围数；Top 1–3 给对象、方向、beta/OR/HR/差值、CI/SE 和 q/p；说明整体效应量级与模式。领域段须把一个 Top 信号映射到可检验假设（方法 + 输入 + 判据）。后续至少包括：

```markdown
1. 多因素校正：`r model` 加入 `r covariates`；判据为 Top 信号方向一致且 `r stability_rule`。
2. 稳定性：`r resampling_method`（`r n_resamples` 次）；判据为入选频率/CI 达到 `r threshold`。
```

## 模板 2：多因素模型（logistic/Cox/线性）

报告 N、事件数、参数数、EPV（适用时）、模型/结局、特征集和缺失处理。Top 1–3 给系数或 OR/HR、CI、方向和 p/q；说明校准、PH、共线性或 bootstrap 稳健性。领域段明确决策动作和适用边界。后续包括：

```markdown
1. 假设诊断：`r diagnostic_method` 检查 `r assumption`；判据 `r diagnostic_criterion`。
2. 泛化：`r validation_method` 评估性能/系数稳定性；判据为性能下降 ≤ `r drop_threshold` 且方向一致率 ≥ `r stability_threshold`。
```

## 模板 3：模型性能与验证

报告验证方案、训练/验证/测试规模和事件数；给 AUC/C-index、Brier、校准 slope、net benefit 等及 CI；比较基线提升、训练—测试差距与稳定性。将性能映射到具体阈值、收益、代价和人群边界。后续至少包括：

```markdown
1. 外部验证：在 `r external_dataset` 复现；判据性能 ≥ `r floor` 且 slope ∈ `r slope_range`。
2. 阈值/决策：用 `r decision_method`；判据 net benefit 在 `r range` 内为正或优于基线。
```

## 数据溯源

统计量引用模型摘要或计算变量，N 引用维度/计数，比例引用计算逻辑，阈值引用 `params`。写完逐项核对解读中的数字能在代码/数据中定位；图表证据应符合 `plot_quality_standards.md`。
