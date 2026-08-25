# 变更日志

本文档记录 find-best-skill 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Changed
- 版本升级：0.4.0 → 0.4.1；默认缓存目录从 `~/.find-best-skill/` 迁移到当前工作目录下 `.bensz-api/skills/find-best-skill/cache/`，同步更新配置与脚本 fallback。

---

## [0.4.0] - 2026-01-18

### Changed
- **搜索方式简化**：社区调研改用 WebSearch 类工具或搜索类 MCP 工具（如 SearXNG、Tavily）
  - 直接利用模型内置搜索能力，无需依赖 GitHub API
  - 提供 `site:github.com "SKILL.md" {关键词}` 等搜索语法示例
  - GitHub SEO 良好，普通搜索即可获得高质量结果

### Removed
- **移除 `search_github_skills.py`**：功能已被 WebSearch 替代，遵循 KISS 原则
- **移除 `references/github-api.md`**：不再需要 GitHub API 相关文档
- **简化 `config.yaml`**：移除 `platforms.github.search_url` 和 `platforms.github.api_url`

---

## [0.3.1] - 2026-01-18

### Added
- **统一配置加载器**（P1）
  - 新增 `scripts/config_loader.py`，为 scripts 提供 `config.yaml` 单一真相来源

### Fixed
- **GitHub 搜索链接类型修复**（P0）
  - `search_github_skills.py` 生成 GitHub code search（`type=code`），避免 repo 搜索 + code 限定符混用导致的误导
  - `config.yaml:platforms.github.search_url` 同步口径
- **缓存健壮性修复**（P0）
  - `cache_manager.py` 的缓存/索引写入改为原子落盘（降低半写入导致损坏的风险）
  - 缓存 JSON 损坏自动备份并自愈
  - 非法 `cached_at` 不再导致 `--stats/--cleanup` 崩溃（视为已过期）
- **README 配置项口径修复**（P2）
  - 修正 `recommendation.min_count/max_count` 等已不存在的字段名，改为以 `config.yaml` 为准

### Changed
- **缓存参数以 `config.yaml:cache` 为准**（P0）
  - `cache_manager.py` 默认从 `config.yaml` 读取 `dir/ttl_days/max_size/similarity_threshold`（CLI 可覆盖）
- **文档口径同步**（P1）
  - `SKILL.md` 补充“配置来源与覆盖优先级”说明

### Quality
- 通过 auto-test-skill A 轮测试（v202601182019）
  - 验证脚本可运行：`search_github_skills.py`、`cache_manager.py`
  - 验证缓存自愈：损坏 JSON 备份并重置
  - 验证非法时间字段容错：`cached_at=not-iso` 不崩溃（判为 expired）
- 通过 auto-test-skill B 轮质量检查（B轮-v202601182024）

---

## [0.3.0] - 2026-01-18

### Added
- **本地缓存机制**（P0）
  - 新增 `scripts/cache_manager.py` 缓存管理脚本
  - 缓存目录：`~/.find-best-skill/`
  - 支持技能元数据缓存、关键词搜索、相似度匹配
  - TTL 硬编码为 180 天（半年）
  - 自动过期清理、访问时间更新
- **缓存配置**（P0）
  - config.yaml 新增 `cache` 节（enabled, dir, ttl_days, max_size, similarity_threshold）
  - config.yaml 新增 `cache_strategy` 节（on_hit, on_miss, after_search 策略）
- **工作流改造**（P0）
  - 第2步增加"缓存查询"环节
  - 第4步增加"结果合并与缓存更新"环节
  - 原第3-5步顺延为第5-7步
- **辅助脚本扩展**（P1）
  - 新增缓存管理命令：`--stats`, `--search`, `--clear`
  - 集成到 SKILL.md"辅助脚本"章节

### Changed
- **版本号升级**：0.2.0 → 0.3.0（新增缓存功能，次版本号更新）

### Quality
- 轻量测试通过：
  - 缓存读写功能正常
  - 关键词搜索功能正常
  - 统计和清理功能正常

---

## [0.1.1] - 2026-01-18

### Fixed
- **P0**：修复 Python 语法错误（scripts/get_skill_info.py:95）
  - 将 `choices["text", "json"]` 修正为 `choices=["text", "json"]`
- **P0**：重新定位技能描述，更符合实际能力
  - 将 YAML description 从"智能推荐"改为"搜索辅助"
  - 明确功能边界：生成搜索链接和研究清单

### Changed
- **P1**：删除过度设计的评价权重配置
  - 移除 config.yaml 中的 `scoring_weights` 节（8个未使用的权重参数）
- **P1**：统一推荐数量配置范围
  - config.yaml 中 `min_count` 从 3 改为 5
  - SKILL.md 同步更新为"目标 8 个（范围 5-10 个）"
- **P1**：修复参考文档时效性问题
  - 将"2025年12月"改为"2025年"（更通用）
- **P1**：改进官方仓库列表维护
  - 添加"最后验证"时间标记
  - 将不存在的仓库注释掉

### Added
- **P1**：输入验证和错误处理
  - search_github_skills.py：添加长度检查（200字符）和空值检查
  - 两个脚本都添加了 try-except 和友好错误消息
- **P2**：参考文档时效性标记
  - 所有 references/*.md 文件添加"最后更新"时间

### Quality
- 通过 auto-test-skill A 轮测试（v202601181359）
- 通过 auto-test-skill B 轮质量检查（B轮-v202601181410）
- 质量评分：109/115（优秀，生产就绪）

---

## [0.1.0] - 2025-12-XX

### Added
- 初始版本发布
- 核心 search_github_skills.py 和 get_skill_info.py 脚本
- GitHub、SkillsMP、Reddit 搜索平台支持
- 配置文件和参考文档

---

## 版本说明

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正
