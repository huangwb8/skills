# 计算、环境与重建

按科学阶段用 `targets` 计算，`renv` 锁环境，Rmd 交付。小分析可用小依赖图，依资源和失效范围拆阶段、队列或重采样任务。沿用现有入口及布局，无框架时可在独立目录接入获准只读输入、已有算法和可核验结果。迁移原项目需授权。

## 项目布局

配对骨架可取用、调整或跳过。优先沿用原布局，按需建目录，分放输入、正式输出、环境、测试和 store。

| 路径 | 职责 |
| --- | --- |
| `00.Environments/` | `environment.R` 选库，`packages.txt` 声明依赖，`renv.lock` 锁定环境，`analysis.R` 示范独立的版本化参数 |
| `raw/` | 保护原始输入和唯一快照，随骨架附带的 CSV 为合成数据 |
| `R/`、`_targets.R`、`_targets/` | 计算函数、依赖图、可重建 store。示例 `R/paired.R` 含配对、估计和稳健性诊断 |
| `products/`、`reports/` | 可复用结果与单独交付的图、表和附件 |
| `scripts/tests/`、`tmp/tests/<run-id>/`、`tmp/scratch/` | 测试、独立运行副本与探索产物 |
| `run.R`、`01.01.01-paired-change.Rmd`、`01.01.01-paired-change.html` | 示例入口及报告。可指定其他 Rmd，默认输出同目录同名 HTML |

从项目根运行，chunk 路径相对项目根，HTML 链接相对 HTML 所在目录，骨架会调整链接。单交 HTML 时附获准交付的引用附件。

## 环境生命周期

骨架需要 R、Pandoc 及在宿主 R 库显式安装的 `renv`。从项目根运行：

- `Rscript --vanilla run.R prepare` 安装声明的包及依赖，生成 `00.Environments/renv.lock`。已有锁文件时中止。
- `Rscript --vanilla run.R restore` 按锁文件记录的 R 版本恢复项目库，需要可用的软件源、缓存或镜像。
- `Rscript --vanilla run.R update-lock` 经审阅后更新依赖并重写锁。恢复旧结果用 restore。
- `Rscript --vanilla run.R build` 更新缺失或失效的 targets 后渲染。
- `Rscript --vanilla run.R report` 检查 targets 有效后读结果并渲染。build 和 report 均可指定项目内 Rmd，工作目录仍为项目根。

`renv/` 项目库默认在 `00.Environments/`，库与缓存可重建。版本管理包清单、锁、环境入口和分析设置。模板显式选库并核版本，普通计算与渲染禁止隐式安装。记录 R、Pandoc、系统库、编译器、外部资料版本及字体/locale。示例用 CRAN，正式项目写明软件源及恢复方式。

## 把结果放在对的层

- 按科学阶段声明 targets，保护原始数据并记录纳入排除，生成估计、诊断和稳健性结果。外部及参数文件用 `format = "file"`，显式加载 `R/` 函数，按需跟踪环境和锁定版本。外部资源与固定汇总用可验快照、版本或校验和，保留来源和范围。
- 报告用同一脚本、store 及所需结果检查 `tar_outdated()`，保留依赖遍历，使 DAG 声明可安全读取。随后用 `targets::tar_read()` 取正式结果，展示真实代码，执行取数、可视化、排版与一致性核对。缺失、损坏或失效时提示正式构建，禁止在报告另建计算或缓存入口。[代码与数字](report.md#代码怎么展示数字怎么引用)
- 模型、表和图可由正式入口独立导出。关键结果注明输入/版本、参数、代码或 target、结果位置和重建命令。难以重获的来源提前保全可复核材料。
