# 分析图、数据产品与缓存契约

## 1. 分析计划

以 `templates/analysis_plan_template.yaml` 为起点。计划是需求映射和依赖检查入口，不是调度框架。每个单元包含：稳定 ID、名称、目的、依赖、输入、代码、产品、是否缓存、报告和完成判据。

含缓存单元时，把 Skill 的 `templates/checkpoint_helpers.R` 复制到项目 `scripts/lib/checkpoint_helpers.R`；该 helper 是代码 identity 的一部分。旧项目原有 `templates/checkpoint_helpers.R` 继续兼容，不因维护任务移动。缺失时 strict checker 会阻断运行。

计划完成后运行：

```bash
python3 <skill-root>/scripts/check_analysis_workflow.py <项目根> --plan analysis-plan.yaml
```

报告模式用于早期迭代；首次真实昂贵运行和交付前增加 `--strict`。

## 2. 选择 checkpoint

以下任一情况通常值得持久化：

- 计算或外部请求昂贵；
- 多个下游复用；
- 高风险、有损或不可逆转换；
- 需要人工审查；
- 中断后重做代价高。

纯展示对象、毫秒内可重建的派生值、只服务下一行的中间变量不缓存。数据体量很大时，主对象保持完整高效格式，人类副本使用 schema、统计摘要和有限预览，不复制一份巨大 TSV。

## 3. 产品最小契约

```text
<products_dir>/<workflow>/<AA.BB.CC. 名称>/
├── main.rds          # 完整主对象，可替换为领域所需完整格式
├── preview.tsv       # 矩形数据按需；巨大对象允许仅受控预览
├── summary.md        # 人类可读结构、统计摘要与注意事项
├── metadata.yaml     # 身份、输入、参数、代码、上游、输出、耗时
└── SUCCESS           # 最后写入
```

`metadata.yaml` 不记录绝对私有路径、凭据、原始个人信息或完整大体积输入。相对路径与摘要足以证明身份。

## 4. 缓存身份

最小身份组成：

- 原始/外部输入的相对路径、大小和内容摘要；
- 影响当前结果的参数；
- 当前 `.R`、按需 `_functions.R` 和 checkpoint helper 的代码摘要；
- 直接上游产品的 product identity；
- 输出契约版本；
- 只有确实改变结果时才纳入 R/关键包版本。

不得纳入运行时间、文件修改时间或日志路径。报告层阈值与配色不进入上游重型单元身份。

当前 helper 采用完整文件摘要作为可靠默认值。若真实大文件证明摘要成本不可接受，先测量，再由项目显式选择替代策略；不得以仅时间戳作为默认身份。

## 5. 写入与命中

产品根默认 `products/`，只通过项目统一的 `BENSZ_PRODUCTS_DIR`/`00.Environment.R` 设置覆盖；`bensz_product_dir()` 会拒绝项目外路径、保留目录与 symlink 逃逸。正式产品可恢复、可审查，不是可以无条件删除的技术缓存；`_targets/`、renv library 等才是运行缓存。

`scripts/lib/checkpoint_helpers.R` 的顺序是：

1. 删除旧 `SUCCESS`；
2. 写同目录临时文件；
3. 重新读取主对象、预览和元数据；
4. 逐文件提交正式名称；
5. 最后写 `SUCCESS`；
6. 再次按元数据哈希验证。

命中必须同时满足：`SUCCESS` 存在、元数据可读、本单元预期 cache identity 一致、所有声明输出存在且摘要一致。文件存在但任一条件不满足即为 miss。cache identity 决定本单元能否复用；根据实际输出摘要生成的 product identity 用于向下游传播内容变化。

本版只保证单进程完成标记语义，不提供并发锁或分布式调度。若同一产品目录存在并发写入需求，应先停止并增加项目级串行约束；不要假装已支持并发。

## 6. 失效与恢复

已有项目已经采用历史 runner 时，`scripts/run_analysis_workflow.py` 先执行严格检查，再按编号遍历全部 `.R` 计算节点。新项目不使用该 runner：simple 直接运行正式入口，complex 使用 targets。直接上游的 product identity 是下游 cache identity 的一部分，因此即使上游在相同静态输入下被强制重算，只要实际产品改变，也会传播到必要下游；没有依赖关系的单元不应被连带重算。

- `--force-step 02.00.00`：通过环境传给各 R 单元，强制指定单元运行；它的新身份/产品会决定下游是否失效。
- `--resume-from 03.00.00`：编号更早的单元必须有效并记录命中，否则停止；从失败边界继续。

不要把这两个控制放入 Rmd YAML。Rmd YAML 只包含展示、筛选与解读参数。

## 7. 人类审查

RDS 保持 R 对象保真，但不是人类审查界面。`summary.md` 至少说明目的、对象类型/维度、关键缺失或异常、主要统计摘要和下游注意事项。矩形数据优先提供全量可读表；体量不允许时写 schema、行列数、列级摘要和有限预览，并说明完整对象的位置。
