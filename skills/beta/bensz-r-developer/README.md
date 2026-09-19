<div align="center">
  <h1>bensz-r-developer</h1>
  <p><strong>用类驱动 API、清晰的输出/缓存边界和受控性能策略开发可维护的 R 函数与 Package。</strong></p>
  <p>Beta Skill · R 函数与 Package · S3/S4/R6 · devtools/roxygen2/testthat</p>
  <p>中文 README.md · <a href="README_EN.md">English README_EN.md</a> · <a href="#快速开始">快速开始</a> · <a href="templates/demo-package/">Demo Package</a> · <a href="references/">设计参考</a></p>
</div>

`bensz-r-developer` 把个人开发习惯整理成可复用的工程契约：对象先行、最终输出与缓存分离、函数内保留 `if (FALSE)` 手测块，并对并行、性能和 C++ 升级设置明确门槛。它适合直接开发代码，也适合维护完整 R Package。

## 适用范围

在这些任务中使用：

- 新建或重构 R 函数、S3/S4/R6 类与方法；
- 开发、维护或审查 R Package；
- 设计 `output.dir`、`cache.dir`、覆盖和恢复语义；
- 实现可复现并行，或评估 `cpp11`/`Rcpp` 原生加速。

不用于单纯运行现有代码，也不用于以 R Markdown 报告、科研分析编排或论文级图表为主的任务；后者使用 `bensz-rmd-rules`。

## 快速开始

### 最小 Prompt

```text
请使用 bensz-r-developer 开发一个 R 函数。
输入：一个 data.frame。
要求：先定义合适的类；最终文件写入 output.dir，可重建中间结果写入 cache.dir；函数顶部保留 if (FALSE) 手测块；补 testthat 测试。
```

### 进阶 Prompt

```text
请使用 bensz-r-developer 维护这个 R Package。
先检查现有类、DESCRIPTION、NAMESPACE、R/、tests/ 和 src/，保持公开 API 兼容。
为批量计算加入可复现并行，不得污染调用方 future plan；先 profile，再判断是否需要 cpp11/Rcpp。
完成后运行 devtools::document()、devtools::test() 和 devtools::check(cran = FALSE)，报告串并行等价、缓存恢复和剩余风险。
```

## 输入与输出

| 项目 | 内容 |
|---|---|
| 输入 | 需求、现有 R 文件或 Package、数据契约、R/平台/依赖和硬件约束 |
| 主要输出 | R 源码、类/泛型/方法、roxygen2 文档、testthat 测试、手测块 |
| Package 输出 | 同步的 `DESCRIPTION`、`NAMESPACE`、README/CHANGELOG 及检查结果 |
| 性能输出 | profile/benchmark、串并行或 R/C++ 等价证据、回退路径 |
| 过程材料 | 当前项目唯一 `.bensz-api/task-*/bensz-r-developer/` 工作区 |

## 推荐工作方式

### 函数开发

先写输入、返回、错误和副作用契约。只有数据确有不变量或生命周期时才建类：轻量值对象优先 S3，严格 schema/多分派用 S4，可变资源生命周期用 R6。最终文件与缓存使用独立参数，`NULL` 表示不持久化，默认拒绝覆盖。

### Package 开发

用 `usethis` 建结构、roxygen2 维护文档和 NAMESPACE、testthat 写自动测试、devtools 完成开发闭环。`if (FALSE)` 块服务逐行手测，不替代自动测试；依赖以 `DESCRIPTION` 为准。

### 并行与高性能

先 profile，再改算法、向量化、复制/I/O 和分块；随后才并行或引入原生代码。Package 内尊重调用方 future plan，默认留一个逻辑核；只有显式 aggressive 模式且内存、线程和恢复策略通过评估时才占满设备。C++ 必须保留 R 参考实现和等价测试。

## Demo Package

[templates/demo-package/](templates/demo-package/) 是可运行的最小包，包含 S3 构造/验证/打印/执行方法、`output.dir`/`cache.dir`、带回滚的事务输出与 manifest、`filelock` 缓存锁、future 并行和 testthat。它使用 `iris` 构造手测数据，不包含私人路径或真实业务数据。

```r
devtools::document("templates/demo-package")
devtools::test("templates/demo-package")
devtools::check("templates/demo-package", cran = FALSE)
```

示例已通过 testthat 和 `R CMD check --no-manual`；复制后必须替换包名、作者、许可证、领域对象与示例统计逻辑。

## 与相邻 Skill 的区别

| 需求 | 使用 |
|---|---|
| R 函数、类、Package、并行、原生性能 | `bensz-r-developer` |
| R Markdown、科研分析编排、缓存恢复、论文级图表与解读 | `bensz-rmd-rules` |
| 只把 `.Rmd` 渲染成 HTML | `knit-rmd-html` |
| 明确要求测试某个 Agent Skill | `auto-test-skill` |

## 配置与资料

- [SKILL.md](SKILL.md)：AI 执行契约与安全边界。
- [config.yaml](config.yaml)：类选择、并行、原生加速和 Package 工具的稳定默认值。
- [类与 API](references/class-api-design.md)：S3/S4/R6 选择与最小对象契约。
- [输出与缓存](references/io-cache-contract.md)：落盘、缓存身份、原子写入与 manifest。
- [并行与性能](references/parallel-performance.md)：future、RNG、资源预算和 C++ 门禁。
- [Package 工作流](references/package-workflow.md)：usethis/roxygen2/testthat/devtools 闭环。

## WHICHMODEL：模型选择

> 最后调研：2026-09-19。以下是任务分层建议，不是永久排行榜。

| 场景 | OpenAI | Anthropic | 建议推理档 |
|---|---|---|---|
| 架构、并行、缓存、C++ 边界 | GPT-6 Astra | Claude Opus 5 | 默认从 medium/high；证据不足再提高 |
| 日常函数、roxygen2、testthat、Package 维护 | GPT-5.6 Terra | Claude Sonnet 5 | 默认档 |
| 格式、命名、明确断言下的局部修订 | GPT-5.6 Luna | Claude Haiku 4.5 | low/default |

选择顺序：先用能力较强的模型达到正确性目标并建立测试，再在同一验收集上尝试更快、更便宜的档位。复杂任务提高 reasoning effort 可能改善结果，但会增加时间和 token；通用排行榜不能替代本项目回归测试。

来源：[OpenAI Codex models](https://developers.openai.com/codex/models)、[OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection)、[Claude models overview](https://platform.claude.com/docs/en/models/overview)、[SWE-bench](https://www.swebench.com/)。本次未做跨模型实测，型号与可用性可能变化。

## 常见问题（FAQ）

### 一定要先建类吗？

不一定。对象没有稳定不变量、身份或生命周期时，普通函数更清楚；不要为了统一形式过度设计。

### 为什么同时需要手测块和 testthat？

`if (FALSE)` 让维护者在 IDE 中加载数据、改参数、逐行调试；testthat 才能自动回归并进入 CI。两者解决的问题不同。

### 会自动安装 R 包或修改全局并行设置吗？

不会。缺少依赖时应报告包名和复现命令；Package 函数不得静默改变工作目录、RNG、options 或 future plan。

### 什么时候值得使用 C++？

只有 profiler 证明热点位于适合原生实现的 kernel、成熟 R 包无解、跨语言复制成本可接受，并且已有 R 参考实现与等价测试时。
