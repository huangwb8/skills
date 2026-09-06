<!-- Template-ID: skill-body; Sync-Policy: copy-and-hash -->

<!--
This file defines the section interface only. Do not copy its explanatory
sentences into a Skill as filler, and do not place the pre-migration body in
an appendix. During normalization, move the existing Skill-specific rules
into the matching sections and replace every placeholder with real content.
-->

# {Skill 标题}

## 目标

说明 Skill 的用途、触发边界，以及明确不负责的范围。

## 流程

### 输入

列出必需输入、可选输入、来源和敏感信息边界。

### 执行步骤

按依赖顺序描述 Agent、脚本或人工执行的步骤；确定性操作优先使用 `scripts/`。

### 输出

列出交付物、格式、保存位置和失败时的返回形式。

### 输出管理

说明任务工作区、临时产物、正式交付物和覆盖/删除边界。

### 校验

给出可复现的静态检查、测试或人工复核方法及通过标准。

### 失败与恢复

说明错误分类、证据保留、重试条件、等待/取消处理和恢复起点。

## 控制（按需）

仅在显式采用 State、Verifier、Gate、Pack 或其它治理组件时保留本节。说明组件、调用时机、证据绑定、通过条件和人工介入边界。

明确采用 State/Verifier 子 Agent 协作时，引用 `docs/templates/state-verifier-agent-coordination.md`，并在 `config.yaml` 中声明供 LLM/Harness 理解的协作意图；不把条件性条款加入公共约束块。Kernel 不负责跨 Harness 的 Agent 创建、等待或回收。

## 约束

摘要说明工作区、BAC、隐私、文件边界和 `bensz-collect-bugs` 协作要求；详细公共规则引用 `docs/templates/skill-common-constraints.md`。
