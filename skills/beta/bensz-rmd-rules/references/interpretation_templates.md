# 深度解读写作骨架（证据锚定版）

本文件提供一组“可复用但不套话”的写作骨架与要点清单，用于把四层内涵（数据描述 / 统计见解 / 领域映射 / 局限与后续）落到**当前结果的证据**上。

重要提醒：这些内容用于**写作前整理证据与推理**。常规交付时应把四层内容**合并为 1–2 段连贯叙述**，不要机械输出“数据描述：…统计见解：…”四段标签。

使用规则：
- 任何占位内容都必须替换为本次结果的具体对象与数值（推荐用 `` `r ...` `` 动态嵌入）。
- 所有阈值一律来自 YAML `params`（单一真相来源），并在文本中同时报告“阈值 + 当前值”。
- 任何“可能/提示/建议进一步研究”等句式都必须补齐：对象 + 动作 + 判据（见 `references/four_tier_interpretation_framework.md`）。
- 默认采用自然标题与论文口吻；对关键观点做适度加粗；禁止通过代码生成解释文本（可用 `` `r ...` `` 动态嵌入数字）。
- 若解读依赖图表作为证据载体，图表应默认达到 Nature 级别可读性标准（字体/配色/输出格式等），详见 `references/plot_quality_standards.md`。

## 解读前四问（先想清楚再写）

1. **研究者视角**：如果我是项目负责人，看到这个结果，我最想确认/反驳的是什么？
2. **领域映射**：这个统计发现如何改变我对机制/分层/风险的理解（只写可证伪推断）？
3. **决策帮助**：基于这个结果，我会优先做什么？不做什么？为什么？
4. **风险边界**：如果该结论不复现，最可能的原因是什么（样本量/混杂/批次/模型假设）？

## 禁止：机械套用模板（硬门槛）

- ❌ “这张图/表在本次数据中的直接观察是：... 这在统计层面的含义是：... 对研究者的直接意义是：... 你可以立即执行的下一步是：...”
- ❌ “数据描述：... 统计见解：... 领域见解：... 局限与后续：...” 的机械分项（把四层当成固定四段/固定四行标签）

---

## 连贯叙述式模板（默认推荐）

四层是**内容门槛**而非固定四段。常规交付优先使用下述连贯叙述式骨架：

```markdown
本次分析在 `r N` 个样本/对象上评估了 `r target`，阈值为 `r threshold`（来自 `params`）；在此标准下共有 `r n_sig` 个信号入围。
**最强信号集中在 `r top_1`、`r top_2`、`r top_3`**（`r metric` = `r value`，方向 `r direction`），并与 `r anchor` 的总体趋势一致（`r consistency_metric`）。
从领域角度，这意味着 `r domain_mapping`；但不确定性主要来自 `r uncertainty_source`（`r uncertainty_value`），因此当前结论更适合定位为 `r evidence_level`。
后续建议：1) `r method_1` 于 `r input_1` 上验证，判据为 `r criterion_1`；2) `r method_2` 于 `r input_2` 上验证，判据为 `r criterion_2`。
```

### Top 3 汇总小表（推荐固定产出）

```markdown
| Rank | 对象 | 指标/效应 | 不确定性 | 备注 |
|---|---|---|---|---|
| 1 | `r top_1` | `r metric_1` | `r ci_1` | `r note_1` |
| 2 | `r top_2` | `r metric_2` | `r ci_2` | `r note_2` |
| 3 | `r top_3` | `r metric_3` | `r ci_3` | `r note_3` |
```

---

## 反模式：模板化写作 vs 专家级写作

### 模板化写作的特征（避免）

- 不看数据也能写出一段"看起来正确"的通用解释（大量"用于判断/当…时/提示可能/建议进一步验证"）。
- 只报统计量（p/rho/HR/beta），但不说明其在**本次结果**中的量级含义与具体落点（哪一组/哪一簇/哪几个对象最突出）。
- "局限/后续"停留在宣言式空话（无方法/无输入/无判据）。
- 使用**教学口吻**（"该图展示...用于判断..."）而非**论文口吻**（"本次结果显示..."）。

**典型的模板化句式**（禁止）：

| 模板化句式 | 问题 |
|-----------|------|
| "[图表类型]展示[变量]在[层面]的[形态]，用于判断..." | 教学口吻，在定义图表而非陈述发现 |
| "当[条件]时，更支持[解释]" | 通用规则，不看数据也能写 |
| "统计锚点为 [统计量] = `r x`" | 只报数值，未解释量级含义 |
| "局限在于[通用局限]" | 未绑定当前数据的具体不确定性 |
| "后续应结合[方法]，优先选择[策略]" | 无输入、无判据的空话 |

### 专家级写作的特征（必须做到）

- 结论句绑定本次对象与证据：对象 + 对比/排序/方向 + 数值（优先 `` `r ...` ``）。
- 明确指出 1–3 个"本次最强信号"（对象明确，可追溯到指标/排名）。
- 解释统计量的**量级含义**（如 rho=0.72 是"强正相关"，HR=1.5 是"中等风险提升"）。
- 即使写"局限/后续"，也绑定本次结果的具体不确定性来源，并给出可执行验证动作（方法 + 输入 + 判据）。

**专家级写作的核心公式**：

```
[本次结果中] + [具体对象] + [呈现了什么模式] + [`r 具体数值`] + [意味着什么]
```

## 推荐默认策略：证据链收敛叙事（先收敛、再分解）

当结果模块较多、或包含多个 cohort/亚组时，最容易“写了很多但读者抓不住结论”。推荐默认采用：

- 每个 cohort 固定产出 1 个“**核心结论（证据链收敛）**”小节（读者主入口）
- 其余模块只在“会改变结论”的关键节点保留解读
- 四层框架是**内容门槛**，不是“每图四段模板”；交付时优先写成 1–2 段连贯叙述

### 模板 0：核心结论（证据链收敛）

适用：
- 每个 cohort/亚组的总收束段落
- 读者只看这一段也能回答：Top 1–3 是谁？证据强度如何？下一步怎么做？

```markdown
本 cohort（`r cohort_label`，N=`r n_all`）中，`r params$event_set_main` 的总体改变负荷与 normCCS 呈 **{方向}** 趋势（rho=`r sprintf(\"%.3f\", macro_spearman_rho)`，p=`r signif(macro_spearman_p, 3)`），且主导维度更偏向 **{mutation/cnv_del/cnv_amp}**（|rho| 最大：`r ...`）。

**最强信号落在 {Top 1–3 位点/主题}**：{各给出 event_rate/q/effect/稳健性“当前值+阈值”}；并与宏观方向一致（{一致性证据}）。因此当前结论更适合定位为 **{证据等级：强/中/弱}**，主要不确定性来自 {样本不均衡/分层样本量/构成混杂/稀疏性}（{对应当前数值}）。

下一步建议：
1) {分层同向性复核：方法 + 输入 + 判据}；
2) {bootstrap/阈值敏感性：方法 + 输入 + 判据}；
3) {外部队列复现：方法 + 输入 + 判据}。
```

注意：
- `{...}` 由作者根据当前数据填充；数值优先用 `` `r ...` `` 动态嵌入
- **禁止**用代码拼接生成整句解释文本（只能动态嵌入数字/少量词语）
- 所有阈值一律来自 YAML `params`（单一真相来源），并在文本中同时报告“阈值 + 当前值”

**示例对比**：

| 模板化写作 | 专家级写作 |
|-----------|-----------|
| "宏观负荷图展示扩增负荷的梯度形态，用于判断扩增是否主导总体差异" | "本次 `r n_samples` 个样本中，扩增负荷与 normCCS 呈现**强正相关**（rho = `r rho`，p < 0.001）" |
| "rho = 0.35，具有统计学显著性" | "rho = `r rho`（p < 0.001）对应**中等正相关**（Cohen 标准），即负荷每增加 1 SD，normCCS 平均上升 `r rho` SD" |
| "高 normCCS 组呈现更高的负荷" | "高 normCCS 组（n = `r n_high`）的中位负荷为 `r median_high`（IQR: `r iqr_high`），高于低组（n = `r n_low`）的 `r median_low`（IQR: `r iqr_low`），差异为 `r diff`（p = `r p_diff`）" |
| "可能受混杂因素影响，建议进一步验证" | "该结论的不确定性来自 `r confound_var`（当前与暴露的相关性为 `r r_confound`）。后续可在分层模型中调整 `r confound_var`；判据：调整后 rho 方向一致且 p < 0.05" |

## 模板 1：单因素筛选（univ screening / LRT / 批量回归）

适用输出：
- 一张筛选结果表（每行一个特征/变量），包含 p/q、效应（beta/OR/HR/差值）等。

### 四层内容清单（写作前列要点；交付时合并为叙述）

使用方式：
- 先用它把“本次数据的证据锚点”写清楚（对象/方向/量级/不确定性/阈值）。
- 再把这些要点融合成 1–2 段连贯叙述；不要保留四层标签行作为最终交付正文。

```markdown
**数据描述**
- 本次对 `r n_features_tested` 个候选特征进行了单因素筛选（方法：`r method_name`；结局：`r outcome_name`）。
- 阈值：`r sprintf("q ≤ %.3f", q_cutoff)`（/ 或 `p ≤ ...`）；通过阈值的特征数为 `r n_sig`（占比 `r sprintf("%.1f%%", 100*n_sig/n_features_tested)`）。
- 当前表展示的是 Top `r top_k`（排序依据：`r rank_metric`），并给出效应大小与不确定性（`r uncertainty_type`）。

**统计见解**
- **最强信号集中在 `r top_feature_1`、`r top_feature_2`、`r top_feature_3`**（按 `r rank_metric` 排序）。
  - `r top_feature_1`：方向 `r direction_1`，效应 `r effect_1`（`r ci_1`），q=`r q_1`。
  - `r top_feature_2`：方向 `r direction_2`，效应 `r effect_2`（`r ci_2`），q=`r q_2`。
  - `r top_feature_3`：方向 `r direction_3`，效应 `r effect_3`（`r ci_3`），q=`r q_3`。
- 效应大小的整体量级为 `r effect_scale_summary`，并呈现 `r pattern_summary`（例如：正负方向占比、是否出现“少数强信号 + 大量弱信号”的长尾）。

**领域见解**
- 从本领域角度，上述 Top 信号意味着：`r domain_meaning_one_sentence`（必须指向本次结果对象与方向）。
- 可执行映射（至少 1 条）：如果把 `r top_feature_1` 作为 `r use_case`，一个直接可检验的假设是 `r testable_hypothesis`；我们可以用 `r verification_method` 在 `r verification_input` 上验证，判据为 `r verification_criterion`。

**局限与后续**
1. 多因素校正：用 `r multiv_model_type` 将 `r top_k` 个候选特征与 `r key_covariates` 联合建模；判据：Top 信号在校正后仍保持 `r stability_criterion`（方向一致 + 效应量级相近 / q 仍过阈值 / bootstrap 入选率≥阈值）。
2. 稳定性/敏感性：用 `r resampling_method`（`r n_resamples` 次）评估 Top 信号的稳定性；判据：`r stability_rule`（例如入选频率≥70% 或 CI 不跨越 1/0）。
```

---

## 模板 2：多因素模型（logistic / Cox / 线性回归）

适用输出：
- 模型系数表（beta/OR/HR + CI/SE + p/q）
- 可能包含：校准、区分度（AUC/C-index）、PH 检验、VIF/共线性等

### 四层内容清单（写作前列要点；交付时合并为叙述）

使用方式：
- 先把“主要驱动项 + 量级 + 不确定性 + 使用边界”写成要点。
- 交付时用论文口吻合并为 1–2 段叙述，再补 1–3 条可执行后续（方法 + 输入 + 判据）。

```markdown
**数据描述**
- 建模样本量 `r N`，事件数 `r n_events`（若适用），候选参数个数 `r n_params`，EPV=`r sprintf("%.2f", n_events/n_params)`。
- 模型：`r model_type`；特征：`r feature_set_desc`；结局：`r outcome_desc`；缺失处理：`r missingness_strategy`。

**统计见解**
- 主要驱动项（Top 1–3，按 `r rank_metric`）：`r term_1`、`r term_2`、`r term_3`。
  - `r term_1`：效应 `r effect_1`（`r ci_1`），方向 `r direction_1`，p/q=`r p_or_q_1`。
  - `r term_2`：效应 `r effect_2`（`r ci_2`），方向 `r direction_2`，p/q=`r p_or_q_2`。
  - `r term_3`：效应 `r effect_3`（`r ci_3`），方向 `r direction_3`，p/q=`r p_or_q_3`。
- 不确定性与稳健性：`r uncertainty_summary`（例如 CI 宽度、bootstrap 系数分布、PH 假设是否满足、共线性是否提示不稳定）。

**领域见解**
- 在 `r target_scenario` 场景下，这意味着：`r domain_interpretation_one_sentence`（必须落到本次变量与方向）。
- 如果要落地使用，一个直观的决策动作是：`r actionable_step`（例如“按 `r risk_score` 分层并采用阈值 `r threshold`”）；但该动作的边界是 `r boundary_condition`（例如样本外泛化/亚组差异）。

**局限与后续**
1. 假设与诊断：用 `r diagnostic_method` 检查关键假设（例如 Cox 的 PH、logistic 的线性假设/离群点影响）；判据：`r diagnostic_criterion`。
2. 泛化与过拟合：用 `r validation_method`（CV/Bootstrap/外部验证）评估性能与系数稳定性；判据：性能下降 `r performance_drop_threshold` 以内，且关键项方向一致率 `r direction_stability_threshold` 以上。
```

---

## 模板 3：模型性能与验证（AUC/C-index、校准、决策曲线、Bootstrap/CV）

适用输出：
- AUC/C-index（可带 CI），训练/验证/测试对比
- 校准曲线/校准指标（如 slope/intercept、Brier）
- 决策曲线（net benefit）或阈值分析
- Bootstrap/CV 稳定性（入选频率、性能分布）

### 四层内容清单（写作前列要点；交付时合并为叙述）

使用方式：
- 先把“性能数字 → 阈值动作 → 适用边界/不确定性”写清楚。
- 交付时避免空泛宣言（如“具有临床意义”），必须给出可执行阈值/动作与复现判据。

```markdown
**数据描述**
- 验证方式：`r validation_scheme`（例如 5-fold CV / 200 次 bootstrap / train-test split）。
- 数据规模：训练 `r n_train`，验证 `r n_val`（/测试 `r n_test`）；事件数（若适用）分别为 `r events_train` / `r events_test`。
- 报告指标：`r metric_list`（AUC/C-index、Brier、校准 slope、net benefit 等）。

**统计见解**
- 区分度：`r metric_main`（`r ci_main`）；与基线/旧模型相比提升为 `r delta_metric`（`r ci_delta`）。
- 校准：`r calibration_summary`（例如 slope 是否接近 1、是否系统性高估/低估风险）。
- 稳定性：在 `r resampling_method` 下性能分布为 `r perf_distribution_summary`；若训练-测试差距为 `r generalization_gap`，提示 `r overfitting_interpretation`。

**领域见解**
- 这类性能水平在 `r domain_context` 中意味着：`r domain_meaning`（例如“可用于粗筛/分层/辅助决策”，但必须给出具体阈值或使用方式）。
- 若采用阈值 `r decision_threshold`，预期收益是 `r expected_benefit`，代价是 `r expected_cost`；适用人群边界为 `r population_boundary`。

**局限与后续**
1. 外部验证：在 `r external_dataset` 上复现性能；判据：AUC/C-index 不低于 `r external_perf_floor` 且校准 slope 处于 `r slope_range`。
2. 阈值与决策：用 `r dca_or_threshold_method` 确定可接受阈值区间；判据：net benefit 在 `r threshold_range` 内稳定为正（或优于 treat-all/treat-none）。
```

---

## 常见失败模式（写完立刻自检）

- 只写显著性，不写效应大小/方向/不确定性。
- 只说“有意义/可解释/可行动”，不说明“怎么用 + 怎么验证 + 判据是什么”。
- “建议进一步研究/验证”但不给方法、输入、判据。
- 说“可能受混杂/非线性影响”但不定位对象，也不给验证方案。
