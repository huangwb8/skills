# 轻量测试协议

## 适用范围与通过定义

每个新建或实质修改的分析流程必须选择一种测试风格，并从正式入口真实运行适用的计算与报告。checker、静态检查、R 语法检查、targets graph 预览和 `--dry-run` 只算预检；只有 R/Rmd/target 图实际执行且断言通过，才能写 PASS。

测试代码进入 `scripts/tests/` 并版本化；每次测试使用唯一 `tmp/tests/<run-id>/`，其中包含 fixture/子集、隔离 products/reports/store、日志与渲染结果，默认加入 `.gitignore`。运行前后比较正式 `raw/`、products、reports、`_targets/` 以及相关代码/配置，必须保持不变。

## 测试风格

### synthetic_fixture

在没有授权真实数据、数据敏感或原始数据过大时使用。fixture 至少保留：

- 与正式输入一致的列名、类型、主键和关键分组；
- 业务允许的缺失模式；
- 至少一个会触发重要分支或边界的案例；
- 固定随机种子及生成规则。

不要为了“容易通过”删除正式流程必须处理的复杂性，也不要把真实敏感值复制进 fixture。

### project_subset

存在授权数据和已有流程时优先。抽样规则必须确定、可复述且有代表性，覆盖关键分组、结局、缺失和异常边界。除非顺序本身有业务意义且已说明，不能只用 `head(n)`。子集采用最小字段和最少样本的真实副本，不链接回原始文件；断言后默认删除，只保留抽样规则、schema、行列数、非敏感摘要与不可还原证据。只有人类明确要求且项目具备合适访问控制时才保留。

## 隔离与同入口

- simple：测试 wrapper 准备隔离输入后，调用与正式运行相同的 Rscript 或 `rmarkdown::render()` 入口；输出重定向到本次 run root。
- complex/pipeline：同一 `_targets.R` 和 target 图接收隔离输入，`targets::tar_make(store = file.path(run_root, "_targets"))`；不得写正式 `_targets/`。至少一次在前序 target 成功后中断下游，再次 `tar_make()`，用 `tar_meta()`/outdated 证明前序复用；不得用 SUCCESS 或自定义 checkpoint 替代。
- 测试专用 helper 只存在于 `scripts/tests/` 或隔离副本。不得向业务逻辑添加长期 `analysis_mode`、`test_mode` 或两套科学行为。
- harness 先设置 `BENSZ_TEST_RUN_ROOT`，再用正式入口已经识别的 `BENSZ_ANALYSIS_INPUT`、`BENSZ_PRODUCTS_DIR` 和 `BENSZ_REPORTS_DIR` 把输入、产品和报告绑定到同一 run root；`00.Environment.R` 只接受与该 run root 精确匹配的 `tmp/tests/<run-id>/{products,reports}`，不能借测试变量放宽任意 `tmp/` 写入。
- 正式与测试必须调用同一计算函数和同一报告入口。若正式代码无法在不加入测试分支的情况下隔离路径，应先修正路径边界。

existing 项目实质修改后仍应沿用原入口做可行的轻量运行，但不得为测试补建 renv、targets、编号布局或新版测试框架。可以使用一次性隔离副本；若旧入口硬编码绝对路径或会覆盖正式结果，将其记录为 `path_isolation` 阻塞/风险，请人类决定是否授权最小可测试性改造。

## 最低断言

按任务补充科学断言，通用最低集包括：

1. 输入 schema、列类型和必需字段；
2. 行列数、主键唯一性与关键分组覆盖；
3. 重要数值范围或统计不变量；
4. 预期产品、表格、图和报告确实生成且可读；
5. `raw/` 内容摘要在运行前后不变；
6. 测试未修改正式 products/reports/targets store 或代码/配置；
7. 对 complex，隔离 store 中存在实际构建结果，且中断恢复复用仍有效 target，而非仅图解析成功。

## 执行—诊断—修正—重跑

一次尝试至少记录：命令、退出状态、失败类别、修正摘要、断言结果和剩余风险。失败类别固定为：

- `environment_dependency`
- `fixture_or_subset`
- `path_isolation`
- `analysis_code`
- `scientific_assertion`
- `report_rendering`
- `external_service`

失败后只修正对应层并重跑真实受影响路径。不得无限重试；遇到权限、网络、缺失依赖或数据授权等外部阻塞时，停止并明确未验证项。不得把跳过、预检通过或旧缓存命中写成端到端通过。

运行记录至少包含：`project_state`、`workflow_mode`、已有项目观察机制、`test_style`、`formal_entrypoint`、相对 `run_root` 与路径覆盖、R/renv 来源、绑定代码/配置/lockfile 的 `subject_identity`、`preflight`、`lightweight_execution`、`full_data_execution`、断言、正式路径前后对照、尝试和 cleanup。三种执行状态取 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_RUN`；未实际运行全量数据时，`full_data_execution` 必须为 `NOT_RUN`。

轻量测试通过只证明该代码路径和指定不变量在轻量输入上成立，不证明全量资源消耗、罕见值、外部服务稳定性或最终科学结论。审查修正若影响执行、输出或断言，旧 subject identity 的证据立即过期，必须对最新版本重跑。

## 模板入口

- `templates/tests/synthetic_fixture.R`：模拟数据骨架；
- `templates/tests/project_subset.R`：授权子集骨架；
- `templates/tests/simple_smoke_test.R`：simple 真实入口；
- `templates/tests/complex_smoke_test.R`：complex 隔离 target store 入口。
- `templates/tests/test_harness.R`：唯一 run root、subject identity、正式路径不变性与运行记录 helper。

复制到项目后按真实 schema、文件名和科学不变量修改，不能保留占位断言后声称通过。
