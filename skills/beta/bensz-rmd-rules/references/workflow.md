# 计算、环境与重建

低成本、只有一份报告的比较从 simple 开始。多个报告共享结果、拟合或重采样需要增量恢复时，用 complex。现有项目以实际入口为准；报告修改可以只消费其可核验产物。

## 项目布局

| 路径 | 职责 |
| --- | --- |
| `00.Environments/` | `environment.R` 集中确定依赖库；`packages.txt` 声明所需 R 包；`renv.lock` 锁定环境；`analysis.R` 演示一份独立、受版本控制的分析设置 |
| `raw/` | 保护真实输入和唯一来源快照；随骨架附上的 CSV 都是合成样例 |
| `R/`, `_targets.R`, `_targets/` | complex 的计算函数、正式 DAG、可丢失的存储 |
| `products/`, `reports/` | 可复用的科学结果；单独交付的图、表和补充附件 |
| `scripts/tests/`, `tmp/tests/<run-id>/`, `tmp/scratch/` | 按需放入项目测试、独立运行副本和探索产物 |
| `run.R`, `report.Rmd`, `report.html` | 起步入口和报告；报告也可以放在项目内的其他位置，HTML 默认在 Rmd 旁 |

目录按需创建。用户已有的合法布局优先。正式输出与输入、环境、测试和 store 分开。正式入口从项目根运行，使用项目内相对路径；把待交付的附件放在与报告链接匹配的位置。

## 环境生命周期

骨架需要 R、Pandoc 及在宿主 R 库显式安装的 `renv`。从项目根运行：

- `Rscript --vanilla run.R prepare`：为新项目安装已声明的包及依赖到项目库，生成 `00.Environments/renv.lock`。锁文件已存在时中止。
- `Rscript --vanilla run.R restore`：根据现有锁文件恢复项目库。恢复需要可用的软件源、包缓存或当地镜像。
- `Rscript --vanilla run.R update-lock`：经审阅后更新依赖并重写锁文件；在恢复旧结果时用 restore。
- `Rscript --vanilla run.R build`：从输入计算并生成报告；complex 先让 targets 更新失效结果再渲染。
- `Rscript --vanilla run.R report`：只渲染。simple 的低成本分析随 Rmd 执行；complex 的 Rmd 先确认所读 target 仍有效，再消费它。可给 build/report 传一个项目内的 Rmd 路径；工作目录仍以项目根为准。

`renv/` 的项目库默认在 `00.Environments/` 下，库和下载缓存可重建；将包声明、锁文件、环境入口和分析设置纳入版本管理。模板通过显式入口选择项目库并核对锁定版本，普通 compute/render 不触发安装。根据数据和方法记录 renv 不管理的前提：R 发行版、Pandoc、系统库、编译器、外部资料版本和必要的字体/locale。默认 CRAN 用于演示；真实项目可依实际包来源显式配置软件源和复原方式。

## 把结果放在对的层

- simple：用 Rmd 执行轻量分析；如果已有单独 R 入口，就让它产生明确的结果文件并记录来源。
- complex：把外部文件和参数文件声明为 `format = "file"` 的依赖，从 `R/` 显式加载函数，报告通过 `targets::tar_read()` 读取。让计算代码所用的环境或锁定版本参与失效判断。外部资源以允许保留的固定版本或校验和为准；报告排版参数留在报告。
- 报告读取前用同一脚本、同一 store 和结果集合检查 `tar_outdated()`，保持依赖遍历；检查会解析 DAG，应让 DAG 声明无昂贵或写入动作。缺失、损坏或失效时提示正式构建；不要在报告内调用 `tar_make()`。固定汇总包则核对来源、参数、版本及内容哈希，交付时说明适用范围。报告层不维护第二套缓存。
- 需要独立交付的模型、表或图可从正式入口导出。对每项关键结果写明输入/版本、参数、生成它的代码或 target、结果位置及重建命令；遇到难以重做的来源先把可复核材料保存下来。
