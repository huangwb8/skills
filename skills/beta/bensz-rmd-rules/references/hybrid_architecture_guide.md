# 多分析单元的 R + Rmd 架构

## 项目策略

先区分新项目与已有项目。新项目必须同时使用 `targets` 和 `renv`，即使只有一个分析步骤；已有项目对两者独立兼容，缺失机制不自动补齐，不建立旧 runner 与 targets 的双入口。`_targets.R` 负责依赖图、增量重建和执行顺序，`products/`、`metadata.yaml` 与 `SUCCESS` 仍由产品契约负责。`renv.lock` 是环境身份的一部分，`renv/library/`、staging 和缓存不属于交付。

## 适用模式

新项目默认使用编号分析单元；已有 `tmp/{主脚本名}/` 项目进入兼容模式，除非用户明确要求，不迁移、不重命名、不覆盖。

```text
项目根目录/
├── 00.Environment.R
├── analysis-plan.yaml
├── 01.00.00. 数据整理.R
├── 01.00.00. 数据整理_functions.R   # 按需
├── 02.00.00. 结果报告.Rmd
├── 02.00.00. 结果报告.html
├── templates/checkpoint_helpers.R
├── raw/                              # 原始输入，只读
├── products/main/01.00.00. 数据整理/
│   ├── main.rds
│   ├── preview.tsv                   # 按对象类型选择
│   ├── summary.md
│   ├── metadata.yaml
│   └── SUCCESS
└── reports/
    ├── figures/
    ├── tables/
    └── supplementary/                # 按需
```

四类编号文件均位于项目根目录，但不要求每个单元都有四类文件。`.R` 与 `.Rmd` 由 `_targets.R` 声明为 target；旧项目中才可能由历史 runner 遍历。同词干 `_functions.R` 只由本单元加载，不是节点；HTML 是同名渲染结果。`00.Environment.R` 全项目默认唯一。

## 编号语义

文件词干固定为 `AA.BB.CC. 名称`：

- 数字元组升序是默认执行顺序；
- 紧密相关的小步骤递增较后层级，独立阶段递增较前层级；
- 上游不得指向更晚编号；综合报告必须晚于所有输入；
- 编号身份同时用于 `products/` 子目录和 `reports/` 文件前缀。

不要把 `_functions.R` 计入依赖图，也不要只为填满四件套创建空文件。

## 职责分离

| 组件 | 负责 | 不负责 |
| --- | --- | --- |
| `00.Environment.R` | 包加载、项目根路径、全局选项、跨单元配置 | 单个分析的统计逻辑 |
| 编号 `.R` | 原始/上游产品读取、完整计算、checkpoint | 报告阈值、配色、展示 Top N |
| 编号 `_functions.R` | 同词干单元的领域函数 | 独立执行、通用缓存协议 |
| 编号 `.Rmd` | 报告筛选、图表、表格、解读 | 重复昂贵计算、改写原始输入 |
| `products/` | 正式可恢复数据产品 | AI 临时草稿 |
| `reports/` | 论文可直接使用的正式材料 | Rmd/HTML、模型缓存、审查日志 |
| `.bensz-api/` | AI 中间材料、审查、预览、日志 | 续算所需数据的唯一副本 |

完整缓存契约见 [analysis_workflow_cache.md](analysis_workflow_cache.md)。

多阶段缓存流先把 Skill 的 `templates/checkpoint_helpers.R` 复制到项目同名路径；可运行 `<skill-root>/scripts/bootstrap_liquid_glass.py --project-root <项目根> --with-extras`，默认不覆盖已有文件。

## 简单任务与复杂任务

新项目的最小形态也包含 `_targets.R`、`renv.lock`、`renv/activate.R` 和一个 target：

```text
00.Environment.R
01.00.00. 描述性分析.Rmd
01.00.00. 描述性分析.html
raw/
reports/
```

此路径使用 `templates/Rmd_simple_template.Rmd` 直接只读 `raw/`，但仍通过 targets 编排报告入口并由 renv 锁定包环境。多阶段昂贵分析再拆成多个 target 与持久产品。拆分依据是独立失败边界、复用价值、重算成本和人工审查需要，不是代码行数。

## 旧项目兼容与显式迁移

检测到以下任一信号时优先按旧布局维护：现有脚本读取 `tmp/{主脚本名}/`；Rmd 依赖旧 RDS 名；用户有既有自动化或历史结果。兼容维护可改 bug、补图表和解读，但不静默重排目录。

兼容检查使用 `check_analysis_workflow.py <项目根> --legacy --strict`（或让检查器根据脚本中的真实 `tmp/` 引用识别），不带 `--plan`，也不调用 `run_analysis_workflow.py`。继续使用项目原入口。

用户明确要求迁移时：

1. 列出旧文件到新单元/产品的映射；
2. 复制或重新生成并校验，不先删除旧路径；
3. 同时验证结果数量、关键摘要和报告数字；
4. 给出回退入口；
5. 获得用户确认后才考虑清理旧路径。
