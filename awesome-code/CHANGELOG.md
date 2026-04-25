# Changelog

All notable changes to the `awesome-code` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.6.0] - 2026-04-19

### Added（新增）
- 新增 `plans/2026-04-19-subagent-invocation-guarantee.md`，规划把 `awesome-code` 从“推荐合适子 agent”升级为“必要时强制进入调度链、缺失则阻塞并留痕”的实现路线
- 新增 `scripts/subagent_policy.py`：把任务命中结果升级为 `required / preferred / optional` 三层 dispatch requirement
- 新增 `scripts/subagent_dispatch_audit.py`：生成 `dispatch_manifest` 并校验 `dispatch_receipts`
- 新增单元测试 `tests/unit/test_subagent_policy.py`、`tests/unit/test_subagent_dispatch_audit.py`、`tests/unit/test_dispatch_policy_integration.py`
- 为 6 个子代理新增 `references/legacy-skill-full.md`：保留完整长文档内容，同时让子代理 `SKILL.md` 保持精简（≤ 500 行）

### Changed（变更）
- `config.yaml` 新增 `multi_agent.dispatch_policy`，集中管理 required route、design direction keyword 和缺失 required agent 的阻塞开关
- `scripts/agent_coordinator.py` 从“推荐代理”升级为“分层分派 + 门禁 + 留痕”，输出 `required_agents`、`preferred_agents`、`optional_agents`、`dispatch_gate`、`dispatch_manifest`
- `awesome-code/SKILL.md`、`README.md` 与 `agents/multi-agent-coordinator/SKILL.md` 同步更新为策略驱动口径，明确 required agent 缺失时必须阻塞
- `awesome-code/SKILL.md` 与 6 个超长子代理 `SKILL.md`（multi-agent-coordinator/devops-specialist/security-specialist/backend-specialist/code-reviewer/documentation-specialist）按社区最佳实践瘦身到 ≤ 500 行；长模板/示例下沉到各自 `references/legacy-skill-full.md`
- `awesome-code/references/INDEX.md` 移除版本历史与本地 markdown 链接，避免形成多层引用链；相关引用改为代码路径形式
- **新增硬编码引导步骤**：`get_path.py` 脚本，用于动态获取技能真实安装路径，解决 AI 无法预知技能安装位置的问题
- 优化脚本调用说明：区分 AI 调用流程（三步骤：获取路径→解析 JSON→使用绝对路径）和用户手动调用（直接调用/shell 别名）
- 新增 shell 别名推荐配置，简化日常使用（`ac-coordinator`/`ac-test`/`ac-analyze`/`ac-git`/`ac-session`）
- 新增 `references/SCRIPT_PATH_STRATEGY.md`：详细说明脚本路径策略与技术实现
- README.md"快速开始"章节新增"开放性探索"用法，指导用户如何让 AI 自主决定项目优化方向
- `agent_coordinator.py` 改为从 `config.yaml` 读取 `enabled_agents` 与 `agent_priorities`，减少硬编码与配置漂移
- `agent_coordinator.py` 增强可解释性：输出 `matched_keywords`/`priority`，并改进置信度算法（减少仅凭 priority 的误报）
- `agent_coordinator.py` 增强中文可用性：补充中文关键词与简单 CJK 2 字滑窗启发式（不引入分词依赖）
- `agent_coordinator.py` JSON 输出改为 `ensure_ascii=False`，中文更可读
- `create_test_session.py` 改为从 `config.yaml` 读取 `ab_test_optimization.plans_dir/tests_dir`，支持目录结构可配置
- 新增 `templates/`：为 A/B 轮会话与报告提供标准模板，减少 fallback 产物质量波动
- `SKILL.md` 移除过期的 config 示例块，明确以 `config.yaml` 为准
- 版本号从 `2.5.0` 升级到 `2.6.0`，并同步 `pyproject.toml`

### Fixed（修复）
- 修复 `create_test_session.py` 的测试 ID 校验与路径遍历风险（严格要求 `vYYYYMMDDHHMM`，并增加越界防护）
- 修复 `create_test_session.py` 在校验越界前就创建目录的问题（先校验再 mkdir，避免 config 误配导致越界写入）
- 修复 `create_test_session.py` 的 B 轮可追溯性：新增 `--a-test-id`，无模板时也会写入关联信息
- 修复 `create_test_session.py` 时间源不一致问题：统一使用单次 `now` 生成 id/时间字段
- 修复 `test_runner.py` 子进程调用解释器不稳定问题：改用 `sys.executable`，并补齐 watch 模式返回码
- 修复 `test_runner.py` watch 模式的稳定性与性能：忽略常见重目录并处理文件竞态异常
- 修复 `code_analyzer.py` 常量命名检查不可达问题（可捕获混合大小写疑似常量）
- 修复 `SKILL.md` 的时间/规模硬编码宣传语（提升通用性）
- 修复 `SKILL.md` B 轮维度描述与模板不一致问题：更新为"八大原则"（含配置集中化）
- 修复 templates 在 A 轮生成时可能残留 `{{A_TEST_ID}}` 的问题：从通用 TEST_PLAN/REPORT 模板移除该变量
- 修复 `pyproject.toml` 与 `config.yaml` 版本号漂移问题

## [2.5.0] - 2026-03-18

### Added（新增）
- 在 `config.yaml` 中新增 `multi_agent.frontend_design_keywords`，把前端/UI 设计路由词集中到配置管理
- 在 `config.yaml` 中新增 `multi_agent.frontend_design_companion_agents`，明确前端设计任务的默认陪跑代理

### Changed（变更）
- `agents/frontend-specialist/SKILL.md` 补充设计优先工作流、审美护栏、反模式清单与 design-to-code 口径，前端子代理从“能实现”升级为“先定方向再落地”
- `agents/brainstorming/SKILL.md` 新增“自主模式/静默设计简报”，当用户明确要求自主推进时不再把追问流程变成阻塞
- `scripts/agent_coordinator.py` 扩充 `frontend-specialist` 的 UI 设计关键词，并支持从 `config.yaml` 追加前端设计关键词/陪跑代理；前端设计任务会自动补齐 `brainstorming`，同时压制“登录页 UI”误命中调试/后端代理的问题
- `SKILL.md` 与 `README.md` 明确前端/UI 任务的推荐编排口径：优先组合 `brainstorming + frontend-specialist`
- 版本号从 `2.4.1` 升级到 `2.5.0`

### Fixed（修复）
- 修复 `pyproject.toml` 中一行缺少注释符号导致 `pytest` 无法解析配置文件的问题

## [2.4.1] - 2026-01-23

### Added（新增）
- 在 `agent_coordinator.py` 与 `config.yaml` 中补齐 writing-plans 代理（启用与优先级）
- 轻量测试会话：`tests/v202601231224/` 与 `tests/B轮-v202601231224/`

### Changed（变更）
- `SKILL.md` 触发条件与关键词按规范精简，代理团队更新为 14 个，并补齐 Codex 路径示例
- `mirror_optimizer.py` 改为读取 `config.yaml:mirror_optimization`，支持 provider 兜底与 output_dir 配置
- 镜像源报告按检测结果条件渲染，npm/yarn 分支与 Ruby/Rust 使用说明补齐
- `agents/mirror-optimizer/SKILL.md` 补充 output_dir 可配置与跳过清单说明
- `README.md` 备选用法补充 Codex 安装路径提示

### Fixed（修复）
- 修复 mirror-optimizer provider 缺失导致的崩溃
- 修复 `config.yaml` performance 重复定义覆盖问题
- 修复 agent_coordinator 未包含 mirror-optimizer/writing-plans 的推荐缺失
- 修复 pip trusted-host 固定为 aliyun 的不一致问题
- 修复 Gradle 验证命令误用 Maven 的报告错误
- 修复 config_dir 缺乏校验导致的潜在路径逃逸

---

## [2.4.0] - 2026-01-23

### Added（新增）
- **新增 mirror-optimizer 代理**
  - 新增 `agents/mirror-optimizer/SKILL.md`：智能镜像源优化代理，支持自动检测项目技术栈并生成国内镜像源配置
  - 新增 `agents/mirror-optimizer/references/mirror-configuration-best-practices.md`：镜像源配置最佳实践指南
  - 新增 `agents/mirror-optimizer/references/china-mirror-sources.md`：国内镜像源完整列表（含 Docker、Python、Node.js、Go、Java、Ruby、Rust 等）
  - 新增 `agents/mirror-optimizer/references/dockerfile-mirror-templates.md`：Dockerfile 镜像源优化模板集合
  - 新增 `scripts/mirror_optimizer.py`：镜像源检测和配置生成脚本（硬编码逻辑）
  - 在 `config.yaml` 的 `agent_priorities` 中添加 mirror-optimizer（优先级 7）
  - 在 `config.yaml` 的 `enabled_agents` 中添加 mirror-optimizer
  - 在 `config.yaml` 中新增 `mirror_optimization` 配置节，包含镜像源提供商、包管理器检测规则等配置

### Changed（变更）
- 版本号从 2.3.0 升级到 2.4.0
- 代理团队从 12 个扩展到 13 个

---

## [2.3.0] - 2026-01-20

### Added（新增）
- **恢复 brainstorming 代理**
  - 恢复 `agents/brainstorming/SKILL.md`（从 git 历史恢复）
  - 在 `SKILL.md` 代理团队表格中添加 brainstorming（从 11 个代理恢复到 12 个）
  - 在 `config.yaml` 的 `agent_priorities` 中添加 brainstorming（优先级 8）
  - 在 `config.yaml` 的 `enabled_agents` 中添加 brainstorming
  - 在 `scripts/agent_coordinator.py` 的 `AgentRole` 枚举和 `AGENT_REGISTRY` 中添加 BRAINSTORMING
  - 更新 `agents/writing-plans/SKILL.md` 中的上下文说明，恢复对 brainstorming skill 的引用

### Changed（变更）
- 版本号从 2.2.0 升级到 2.3.0

---

## [2.2.0] - 2026-01-20

### Removed（移除）
- **移除 brainstorming 代理**
  - 删除 `agents/brainstorming/` 目录
  - 从 `SKILL.md` 代理团队表格中移除 brainstorming（从 12 个代理减少到 11 个）
  - 从 `config.yaml` 的 `agent_priorities` 和 `enabled_agents` 中移除 brainstorming
  - 从 `scripts/agent_coordinator.py` 的 `AgentRole` 枚举和 `AGENT_REGISTRY` 中移除 BRAINSTORMING
  - 更新 `agents/writing-plans/SKILL.md` 中的上下文说明，移除对 brainstorming skill 的引用

### Changed（变更）
- 简化多代理协调系统，减少不必要的复杂性

---

## [2.1.0] - 2026-01-17

### Added（新增）
- **P0-1: 自动化测试基础设施**
  - 新增 pytest 单元测试框架配置 (`pyproject.toml`)
  - 新增 `tests/unit/` 目录，包含核心脚本的单元测试
  - 新增 `tests/unit/test_config.py`：配置加载函数测试
  - 新增 `tests/unit/test_agent_coordinator.py`：代理协调器测试
  - 新增 `tests/unit/test_code_analyzer.py`：代码分析器测试
  - 新增 `tests/unit/test_create_test_session.py`：测试会话创建测试

- **P0-2: 类型注解完善**
  - 为所有脚本添加完整的类型注解
  - 引入 mypy 静态类型检查配置
  - 新增 `from __future__ import annotations` 到所有脚本

- **P1-3: 性能基准测试**
  - 新增 `scripts/performance_benchmark.py`：性能基准测试工具
  - 支持基线设置、性能比较、回归检测
  - 支持装饰器和上下文管理器两种使用方式

- **P1-4: 结构化日志**
  - 新增 `scripts/logger.py`：统一日志模块
  - 支持 SIMPLE/DETAILED/JSON 三种日志格式
  - 提供 `StructuredLogger` 上下文管理器
  - 提供 `@log_execution` 装饰器

- **P1-5: 架构演进路线图**
  - 新增 `ROADMAP.md`：未来 3-12 个月的技术规划
  - 包含版本升级策略和向后兼容性说明
  - 明确技术债务清单和优先级

- **P2-6: 缓存机制**
  - 新增 `scripts/cache.py`：缓存机制模块
  - 实现 `LRUCache` 类和 `lru_cache` 装饰器
  - 实现 `FileCache` 类和 `file_cache` 装饰器
  - 支持缓存过期和自动清理

- **P2-7: Context Window 管理**
  - 新增 `references/CONTEXT_MANAGEMENT_GUIDE.md`：上下文管理优化指南
  - 详细说明压缩策略、掩码策略、缓存策略
  - 提供 Token 监控和自动清理机制

### Changed（变更）
- **scripts/get_path.py**：添加完整类型注解和返回值
- **pyproject.toml**：新增项目配置文件，包含依赖、测试、覆盖率、lint、类型检查配置

### Fixed（修复）
- 无

### Technical Notes
- 测试覆盖率目标：≥ 80%
- 类型检查：mypy strict 模式
- 代码风格：ruff（替代 flake8 + isort）
- 缓存策略：LRU 内存缓存 + 文件持久化缓存

## [2.0.1] - 2026-01-16

### Fixed（A 轮测试优化修复）

#### A 轮第 1 轮（v202601162133）
- 修复版本号不一致（config.yaml 与 SKILL.md 版本统一为 2.0.0）
- 修复 config.yaml 重复配置块（移除 context 和 security 重复定义）
- 修复 test_runner.py 内存风险（限制文件读取大小）
- 修复 code_analyzer.py import 顺序
- 添加 brainstorming 和 multi-agent-coordinator 到 enabled_agents
- 创建 .gitignore 文件

#### A 轮第 2 轮（v202601162200）
- 修复 SKILL.md 代理数量描述（"10 个专业代理" → "12 个专业代理"）
- 添加 BRAINSTORMING 到 agent_coordinator.py 枚举和配置
- 完善 SKILL.md 代理表格（添加 brainstorming 和 multi-agent-coordinator）
- 修复 config.yaml 示例版本号（1.0.0 → 2.0.0）
- 完善 README.md agents/ 目录结构
- 移除 README.md 中的 "⭐ NEW" 标记
- 创建 references/INDEX.md 索引文件

#### A 轮第 3 轮（v202601162230）
- 精简 SKILL.md 工作流 7（从 110+ 行精简到 ~27 行）
- 精简 YAML description（从 170+ 字符精简到 ~85 字符）
- 改进 create_test_session.py 错误提示（添加 --overwrite 提示）
- 修复 cache_strategy 配置不一致（统一为 moderate）
- 添加 assets/.gitkeep 文件
- 完善 SKILL.md 配置示例（添加 ab_test_optimization 配置节）

#### B 轮质量检查（B轮-v202601162245）
- 修复版本号不一致（统一更新为 2.0.1）
- 评估 session_format 配置（决定保留作为文档说明）
- 通过七大质量原则检查

---

## [2.0.0] - 2026-01-16

### Added

#### 多代理协调系统
- **12 个专业代理**：完整的代理生态系统
  - tdd-workflow：测试驱动开发
  - systematic-debugging：系统化调试与根因分析
  - code-reviewer：代码审查与质量保证
  - git-workflow：Git 工作流自动化
  - frontend-specialist：前端开发专家
  - backend-specialist：后端开发专家
  - devops-specialist：DevOps 专家
  - security-specialist：安全专家
  - documentation-specialist：文档专家
  - context-optimizer：上下文优化
  - brainstorming：交互式设计优化
  - multi-agent-coordinator：多代理协调器

#### 批判性思维驱动的 A/B 轮测试优化工作流
- **三大思考框架**：系统视角、刁钻角度、问题质量标准
- **A 轮测试**：多轮迭代，每轮至少 10 个问题，P0+P1 占比 >= 60%
- **B 轮质量检查**：七大质量原则全面检查

#### 新增参考文档
- CRITICAL_THINKING_GUIDE.md：批判性思维指南
- A_ROUND_PLAN_TEMPLATE.md：A 轮计划模板
- CONSTRUCTIVE_SUGGESTION_GUIDELINES.md：建设性建议标准
- ISSUE_DISCOVERY_TECHNIQUES.md：问题挖掘技巧
- ANTI_PATTERNS_LIBRARY.md：反例库

#### 新增脚本工具
- **agent_coordinator.py**：多代理协调器脚本
- **create_test_session.py**：A/B 轮测试会话管理脚本

### Changed
- 配置文件增加 `ab_test_optimization` 配置节
- 配置文件增加 `multi_agent` 完整配置
- SKILL.md 添加工作流 7（批判性思维驱动测试优化）

### Fixed
- 修复 test_runner.py 中 detect_framework() 的内存问题
- 修复 code_analyzer.py 中 import 顺序问题

---

## [1.0.0] - 2026-01-16

### Added

#### 核心技能
- **SKILL.md**：完整的技能定义，包含六大核心工作流
  - 测试驱动开发（TDD）工作流
  - 系统化调试与根因分析工作流
  - 代码审查与质量保证工作流
  - Git 工作流自动化
  - 多代理协调模式
  - 上下文优化策略

#### 配置文件
- **config.yaml**：集中化配置管理
  - TDD 配置（测试框架、覆盖率、监视模式）
  - 代码审查配置（复杂度阈值、命名规范）
  - Git 工作流配置（提交风格、分支命名）
  - 调试配置（日志级别、追踪深度）
  - 多代理配置（并行任务数、超时）
  - 上下文配置（压缩策略、缓存）
  - 安全配置（敏感数据扫描、漏洞检测）
  - 性能配置（分析、慢查询阈值）

#### 参考文档（references/）
1. **tdd-best-practices.md**：TDD 最佳实践
2. **debugging-systematic.md**：系统化调试与根因分析
3. **code-review-checklist.md**：代码审查与质量保证
4. **git-workflow.md**：Git 工作流规范
5. **multi-agent-patterns.md**：多代理协调模式
6. **context-optimization.md**：上下文优化策略

#### 脚本工具（scripts/）
1. **test_runner.py**：TDD 测试运行器
2. **code_analyzer.py**：代码静态分析工具
3. **git_helper.sh**：Git 工作流辅助脚本

#### 用户文档
- **README.md**：完整的用户指南

### Design Decisions
1. 整合优先：从社区 Skills 中提取六大核心模块
2. 渐进式披露：三层信息架构
3. 硬编码/AI 分离：确定性操作脚本化
4. 配置中心化：所有可配置参数集中在 config.yaml

---

## 版本号说明

遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

当前版本：**v2.0.1**
