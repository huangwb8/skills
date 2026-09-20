# R + Rmd 双模式架构

## 项目策略

项目状态与工作流模式是两个维度。新项目先按 [workflow_modes.md](workflow_modes.md) 选择 simple 或 complex；两者都使用 renv 和真实轻量测试，只有 complex 使用 targets。已有项目按现状维护，缺失机制不自动补齐。

## 新项目目录职责

只创建实际需要的目录和文件：

```text
项目根目录/
├── 00.Environment.R
├── AA.BB.CC. 名称.R / _functions.R / .Rmd / .html
├── raw/                         # 只读原始输入
├── products/                    # 默认正式派生产品，可统一改路径
├── reports/                     # 正式图、表与补充材料
├── templates/                   # 仅样式和渲染资产
├── scripts/
│   ├── operations/              # 项目重跑、导出、恢复操作
│   ├── lib/checkpoint_helpers.R # 按需，共享基础 helper
│   └── tests/                   # 可重复测试代码
├── tmp/
│   ├── tests/<run-id>/          # 每次运行的隔离现场，默认忽略
│   └── scratch/                 # 可丢弃探索
├── renv/activate.R
├── renv.lock
├── _targets.R                   # 仅 complex
└── _targets/                    # 仅 complex 的正式运行状态
```

标准 renv/targets 入口留在项目根，不新增 `env/` 包裹层。编号分析单元继续留在根目录；`scripts/` 不用于隐式重排已有分析代码。

## 组件职责

| 组件 | 负责 | 不负责 |
| --- | --- | --- |
| `00.Environment.R` | 包加载、项目根、单一 products 设置、跨单元配置 | 单元统计逻辑 |
| 编号 `.R` | 原始/上游读取、完整计算、checkpoint | 报告阈值、展示 Top N |
| 编号 `_functions.R` | 当前单元/项目 helper | 独立执行、公共 Package API |
| 编号 `.Rmd` | 报告筛选、图表、表格、解读 | 重复昂贵计算、改写 raw |
| `products/` | 可恢复、可审查、供下游复用的正式派生产品 | targets 状态或 AI 草稿 |
| `_targets/` | targets 技术运行状态 | 正式数据产品 |
| `reports/` | 论文可直接使用的正式材料 | Rmd/HTML、测试日志 |
| `scripts/tests/` | 可版本化测试代码 | 测试数据副本和运行产物 |
| `tmp/tests/<run-id>/` | 测试副本、日志、临时报告/store 与运行记录 | 正式结论唯一来源 |
| `.bensz-api/` | Agent 草稿、审查、预览、任务日志 | 项目续算唯一数据 |

完整产品与恢复契约见 [analysis_workflow_cache.md](analysis_workflow_cache.md)。Skill 内部仍在 `templates/` 托管脚手架；生成到用户项目时，checkpoint helper 放 `scripts/lib/`，测试模板放 `scripts/tests/`，样式资产才放 `templates/`。

## simple

低成本单报告可只有：

```text
00.Environment.R
01.00.00. 描述性分析.Rmd
01.00.00. 描述性分析.html
scripts/tests/smoke_test.R
tmp/tests/<run-id>/        # 运行时创建
renv.lock
renv/activate.R
raw/
reports/
```

使用 `templates/Rmd_simple_template.Rmd`，由 smoke test 真实 render；不创建 `_targets.R`。若后续需要局部失效、复用、恢复或并行，升级到 complex，不开发第二套调度器。

## complex

复杂流程增加 `_targets.R`、按需 `analysis-plan.yaml`、多个编号单元与正式产品。targets 声明依赖和增量构建；checkpoint helper 负责产品身份、完整性和 `SUCCESS`。测试执行同一 target 图但使用 `tmp/tests/<run-id>/_targets`，正式运行才使用 `_targets/`。

## 产品路径

默认产品根为 `products/`。需要覆盖时只在项目级设置 `BENSZ_PRODUCTS_DIR`，由 `00.Environment.R` 和 `bensz_product_dir()` 统一解析。值必须是项目内安全相对路径，不能指向 `raw/`、`reports/`、`tmp/`、`_targets/` 或 `.bensz-api/`。不要在多个 R/Rmd 中分别硬编码替代路径。

## 旧项目兼容与迁移

现有脚本读取 `tmp/{主脚本名}/`、Rmd 依赖旧 RDS、已有 runner/自动化或历史结果时，保持原入口。可以修 bug、补图表与解读，但不能静默重排目录。

人类明确要求迁移时：列出旧→新映射；复制或重生成并校验，不先删除旧路径；比对数量、关键摘要和报告数字；保留回退入口；清理旧路径前再次确认。
