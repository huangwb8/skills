# install-bensz-skills 优化日志

## [Unreleased]

### Changed
- **install-bensz-skills 自身现在也会被安装**：不再硬编码排除自身，改为通过 SKILL.md 中的 `category` 字段控制
  - 修改 SKILL.md：`category` 从 `auxiliary` 改为 `normal`，说明"包括 install-bensz-skills 自身"
  - 修改 install.py：移除硬编码的 `auxiliary_patterns = {"install-bensz-skills"}` 逻辑
  - 修改 install.py：移除 `exclude = {"install-bensz-skills"}` 变量
  - 影响：现在 `install-bensz-skills` 也会被安装到系统级目录（~/.codex/skills 和 ~/.claude/skills）
  - 理由：使安装器本身也能在任意项目中被发现与调用，提高可用性

### Added
- 新增远程 skills_path 缺失的错误提示文案（`remote_skills_path_missing`）
- 新增 A/B 轮测试会话与计划文档（`tests/v202601230716/`、`tests/B轮-v202601230716/`、`plans/v202601230716.md`、`plans/B轮-v202601230716.md`）
- 新增远程源过滤功能：支持按源 ID 选择性安装远程技能
  - 新增 `config.yaml` 中每个源的 `id` 字段（如 `general`、`research`）
  - 新增动态命令行参数：自动为配置中的每个源 ID 生成 `--<id>` 参数（如 `--general`、`--research`）
  - 新增 `source_filter` 参数到 `_remote_install_main()` 函数
  - 支持同时选择多个源：`--remote --auto --general --research`
  - 支持无效 ID 检测与警告提示
  - 新增国际化消息：`remote_source_filter_selected`、`remote_source_filter_invalid`
- 新增远程安装功能：支持从 GitHub 仓库下载并安装技能
  - 新增 `--remote --check` 模式：交互式远程安装，下载后对比并询问用户确认
  - 新增 `--remote --auto` 模式：自动强制远程安装，无需确认
  - 新增 `config.yaml` 配置文件：定义远程技能源，支持多源配置
  - 新增 `SkillComparison` 数据类：记录远程与本地技能的对比结果
  - 新增函数：`_load_config()`, `_check_git_available()`, `_create_temp_dir()`, `_cleanup_temp_dir()`, `_download_remote_source()`, `_compare_remote_skills()`, `_print_comparison_report()`, `_prompt_user_install()`, `_prompt_source_install()`, `_install_remote_skills()`, `_remote_install_main()`
- 新增命令行参数：`--remote`, `--check`, `--auto`
- 新增国际化消息：远程安装相关的中英文提示和错误消息
- 新增 [references/install-report-template.md](references/install-report-template.md)：定义安装报告的标准格式规范，包括章节标题、分隔符、状态图标、多语言支持等
- 新增 `skill_info` 元数据到 [config.yaml](config.yaml)，作为版本与描述的单一来源

### Changed
- 临时目录名净化并加入 URL 哈希后缀，避免路径异常与冲突
- 更新 [SKILL.md](SKILL.md) 示例与参数说明，补充 `--source` 与 `--{id}` 过滤用法
- 更新 [README.md](README.md) 示例与参数说明，补充 `--source` 与 `--{id}` 过滤用法
- 远程源配置示例补齐 `id` 字段以匹配动态参数
- 表格输出按显示宽度对齐（CJK/emoji 兼容）
- 版本号更新至 0.4.1（见 [config.yaml](config.yaml)）
- 优化 [SKILL.md](SKILL.md) 的 `description` 字段，明确说明"默认同时安装到 Codex 和 Claude Code"，并添加远程安装模式说明
- 优化命令行参数帮助文本（`i18n.py`），为 `--codex` 和 `--claude` 添加默认行为说明，让用户清楚理解这两个参数是"单一目标选项"
- 更新 [SKILL.md](SKILL.md) 文档结构：区分本地安装和远程安装模式，添加远程源配置说明和参数组合示例
- 更新 [SKILL.md](SKILL.md) 中的安装报告示例，引用新的报告模板规范文档
- 更新 [SKILL.md](SKILL.md) 常见问题：添加远程安装相关问题和解决方案
- 版本检测改为对可安装文件集合计算 MD5（排除 tests/plans/缓存）
- dry-run 只做预览：不创建目标目录、不迁移旧 manifest
- 远程临时目录每次运行前清理，避免残留导致克隆失败
- 多源合并新增同名技能冲突检测并中止
- 远程配置加载错误改为显式提示依赖缺失/解析失败
- 版本号更新至 0.4.2（见 [config.yaml](config.yaml)）

### Fixed
- 修复远程检查模式错误地强制重装未变化技能
- 修复远程安装 manifest `source` 写入临时路径导致不可追溯的问题
- 修复 `category` 解析仅限前 30 行导致类型识别失败的问题
- 修复 `skills_path` 不存在时静默失败的问题
- 修复英文对比提示包含中文计数单位的问题
- 修复 `_ignore_patterns()` 函数，添加 `plans` 目录到忽略列表，确保 skill 根目录下的 `plans/` 和 `tests/` 子目录不会被安装到系统中
- 修复总体摘要中技能个数统计逻辑：使用 set 去重，确保同一技能在多个平台安装时只计数一次（如 3 个技能安装到 2 个平台应显示 3 个，而非 6 个）
- 修复文档与实现不一致：更新 manifest 命名规则与 MD5 说明
- 修复中文本地化输出中 legacy 文案未翻译的问题
- 修复从系统级已安装位置运行安装器时，默认源目录误指向 `~/.codex/skills` / `~/.claude/skills` 的问题：现在优先从当前工作目录自动识别 `./pipelines/skills`、`./skills` 或当前目录

## 2026-01-12: Manifest 文件存储优化

### 变更内容

#### 1. 专用存储目录

**旧位置**：`~/.bensz-skills-install-manifest.*.json`（直接散落在用户根目录）

**新位置**：`~/.install-bensz-skills/manifests/install-manifest.*.json`（集中管理）

#### 2. 自动迁移功能

每次运行安装脚本时，自动检测并迁移旧位置的 manifest 文件到新目录：

```python
def _migrate_old_manifests() -> list[str]:
    """迁移旧位置的 manifest 文件到新目录。

    旧位置：~/.bensz-skills-install-manifest.*.json
    新位置：~/.install-bensz-skills/manifests/
    """
```

#### 3. 新增辅助函数

- `_get_manifest_dir()` — 获取 manifest 专用存储目录，自动创建目录结构
- `_migrate_old_manifests()` — 自动迁移旧 manifest 文件，返回迁移结果列表

### 设计原则

**最小惊讶原则**：
- 专用隐藏目录符合用户对临时/缓存文件的存放预期
- 历史记录集中管理，便于清理和查找

**关注点分离**：
- manifest 文件与用户主目录分离
- 安装记录与用户文件分离

**向后兼容性**：
- 自动迁移旧文件，无需手动操作
- 迁移失败不影响正常安装流程

### 用户影响

**之前的输出**：
```
📝 Installation manifest saved: /Users/xxx/.bensz-skills-install-manifest.20260112-162559.json
```

**现在的输出**：
```
📦 迁移旧 manifest 文件到 .install-bensz-skills/manifests/:
   • .bensz-skills-install-manifest.20260112-144237.json -> .install-bensz-skills/manifests/install-manifest.20260112-144237.json
📝 Installation manifest saved: .install-bensz-skills/manifests/install-manifest.20260112-162559.json
💡 提示: 历史记录保存在 .install-bensz-skills/manifests/
```

### 目录结构

```
~/.install-bensz-skills/
└── manifests/
    ├── install-manifest.20260112-144237.json
    ├── install-manifest.20260112-162559.json
    └── ...
```

### 技术实现

**manifest 目录创建**：
```python
def _get_manifest_dir() -> Path:
    """获取 manifest 文件的专用存储目录。

    目录位置：~/.install-bensz-skills/manifests/
    """
    manifest_dir = Path.home() / ".install-bensz-skills" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir
```

**manifest 文件保存**：
```python
# 使用专用目录存储 manifest 文件
manifest_dir = _get_manifest_dir()
stamp = _now_stamp()
manifest_path = manifest_dir / f"install-manifest.{stamp}.json"
```

### 清理建议

用户可以安全地删除整个 manifest 目录来清理历史记录：

```bash
# 清理所有 manifest 历史记录
rm -rf ~/.install-bensz-skills/

# 或只清理旧的 manifest 文件
find ~/.install-bensz-skills/manifests/ -name "*.json" -mtime +30 -delete
```

## 2026-01-03: 技能类型分类系统（v4.0）

### 新增功能

#### 1. 技能类型分类系统

**新增三种技能类型**：
- **普通技能（normal）**：供用户使用的功能技能，会被安装
- **辅助技能（auxiliary）**：仅用于开发的工具，不会被安装
- **测试技能（test）**：用于测试的技能，不会被安装

**识别优先级**：
1. YAML frontmatter 中的 `category` 字段（最高优先级）
2. 基于路径和目录名的启发式规则

**辅助技能识别规则**：
- YAML `category` 为 `auxiliary`/`dev`/`development`
- 目录名匹配：`auto-test-skill`, `install-bensz-skills`

**测试技能识别规则**：
- YAML `category` 为 `test`/`testing`
- 位于 `test/` 或 `tests/` 目录下
- 目录名以 `test` 开头或包含 `test-`、`-test`、`_test`、`test_`
- 时间戳格式目录名（如 `20260103_123456`）

#### 2. 新增安装报告格式

**分类报告**：
- 【安装摘要】：仅显示普通技能的表格（可安装的技能）
- 【辅助技能】：列出被忽略的辅助技能及原因
- 【测试技能】：列出被忽略的测试技能及原因
- 📊 统计：按类型汇总（普通技能 X 个已安装、Y 个跳过；辅助技能 Z 个已忽略...）

**示例**：
```
【辅助技能（已忽略，仅用于开发）】(2 个)
   • auto-test-skill ⏭️ 跳过
     原因: 辅助技能（开发用，不安装到生产环境）
   • install-bensz-skills ⏭️ 跳过
     原因: 辅助技能（开发用，不安装到生产环境）

【测试技能（已忽略，仅用于测试）】(1 个)
   • v20260103_123456 ⏭️ 跳过
     原因: 测试技能（测试用，不安装到生产环境）

------------------------------------------------------------
📊 统计
------------------------------------------------------------
普通技能: 1 个已安装, 1 个跳过
辅助技能: 2 个已忽略（开发用，不安装）
测试技能: 1 个已忽略（测试用，不安装）
```

#### 3. 增强 InstallReport 数据类

**新增字段**：
- `auxiliary_skills: list[SkillInfo]` — 辅助技能列表
- `test_skills: list[SkillInfo]` — 测试技能列表
- `skill_type: str` — 每个技能的类型标识

**manifest 文件增强**：
```json
{
  "auxiliary_count": 2,
  "test_count": 1,
  "skills": [
    {
      "type": "normal",  // 或 "auxiliary", "test"
      ...
    }
  ]
}
```

#### 4. 新增函数

- `_get_skill_category_from_yaml(skill_dir)` — 从 YAML 读取 category 字段
- `_determine_skill_type(skill_dir, skills_root)` — 确定技能类型（综合判断）
- `_print_skill_list_by_type(skills, title, t)` — 打印指定类型的技能列表

#### 5. 新增 README.md

创建完整的用户文档，包含：
- 快速开始指南
- 技能类型分类说明
- 安装报告示例
- 为技能添加类型标记的方法
- 常见问题解答

### 变更理由

1. **明确技能用途**：区分可安装的普通技能和仅用于开发/测试的技能
2. **防止污染生产环境**：辅助技能和测试技能不应被分发到用户环境
3. **提高透明度**：用户可以清楚地看到哪些技能被安装、哪些被忽略及原因
4. **支持显式标记**：通过 YAML `category` 字段，开发者可以明确指定技能类型

### 技术实现

#### 数据结构变更

**之前**：
```python
def _find_skill_dirs(skills_root, exclude_names) -> tuple[list[Path], list[Path]]:
    # 返回: (普通技能, 测试技能)
    skill_dirs = []
    skipped_tests = []
    ...
    return skill_dirs, skipped_tests
```

**现在**：
```python
def _find_skill_dirs(skills_root, exclude_names) -> dict[str, list[Path]]:
    # 返回: {"normal": [...], "auxiliary": [...], "test": [...]}
    skill_dirs_by_type = {
        SkillType.NORMAL: [],
        SkillType.AUXILIARY: [],
        SkillType.TEST: [],
    }
    ...
    return skill_dirs_by_type
```

#### SkillInfo 数据类增强

**之前**：
```python
@dataclass
class SkillInfo:
    name: str
    src: Path
    dest: Path
    md5: str
    installed: bool = False
    skipped: bool = False
    reason: str = ""
```

**现在**：
```python
@dataclass
class SkillInfo:
    name: str
    src: Path
    dest: Path
    md5: str
    skill_type: str = SkillType.NORMAL  # 新增：技能类型
    installed: bool = False
    skipped: bool = False
    reason: str = ""
```

### 设计原则

**SOLID 原则**：
- **单一职责**：每个函数只做一件事（类型判断、报告打印等）
- **开闭原则**：易于扩展新的技能类型，无需修改现有代码
- **依赖倒置**：通过 `SkillType` 枚举和 `SkillInfo` 数据类解耦

**DRY（杜绝重复）**：
- 统一的类型判断逻辑
- 共享的技能信息结构

**KISS（简单至上）**：
- 类型识别规则清晰直观
- 报告格式简单易读

### 向后兼容性

- ✅ 无破坏性变更
- ✅ 旧的安装脚本仍可正常工作
- ✅ 未标记 `category` 的技能默认为普通技能（保持原有行为）

### 用户影响

**之前的行为**：
```
installed: auto-test-skill
installed: systematic-literature-review
🙈 已忽略的目录 (test/ 和 tests/)
   - v20260103_123456 (systematic-literature-review/test/)
```

**现在的行为**：
```
installed: systematic-literature-review

【辅助技能（已忽略，仅用于开发）】(1 个)
   • auto-test-skill ⏭️ 跳过
     原因: 辅助技能（开发用，不安装到生产环境）

【测试技能（已忽略，仅用于测试）】(1 个)
   • v20260103_123456 ⏭️ 跳过
     原因: 测试技能（测试用，不安装到生产环境）
```

### 如何验证

1. **运行安装脚本**：
   ```bash
   python3 install-bensz-skills/scripts/install.py --dry-run
   ```

2. **检查报告**：
   - 确认普通技能被正确识别
   - 确认辅助技能和测试技能被忽略
   - 检查统计信息是否准确

3. **验证安装**：
   ```bash
   python3 install-bensz-skills/scripts/install.py --claude
   # 检查 ~/.claude/skills/ 中不包含辅助技能和测试技能
   ```

---

## 2025-12-28: 移除备份机制（简化安装）

### 变更内容

#### 移除功能
- ❌ **移除备份机制**：不再在安装前备份旧版本到 `.bensz-skills-backup/` 目录

#### 变更理由
1. **Git 已提供版本控制**：本仓库使用 Git 管理所有 skills，可以随时回退到任意历史版本
2. **新版本通常更好**：更新的 skill 一般比旧版本更好，备份旧版本没有实际价值
3. **简化安装流程**：减少不必要的文件操作，提高安装效率

### 技术实现

#### 替换函数

**之前：**
```python
def _backup_existing(dest: Path, backup_root: Path, dry_run: bool) -> None:
    """备份已存在的目录到 .bensz-skills-backup/"""
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / dest.name
    shutil.move(str(dest), str(backup_path))
```

**现在：**
```python
def _remove_existing(dest: Path, dry_run: bool) -> None:
    """直接删除已存在的 skill 目录或文件。

    不再备份，因为：
    1. Git 已提供版本控制，可随时回退
    2. 新版本通常比旧版本更好
    """
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    else:
        shutil.rmtree(dest)
    print(f"removed: {dest}")
```

### 设计原则

**KISS（简单至上）：**
- 移除不必要的备份目录
- 简化安装流程：直接删除 → 安装新版本
- 代码更简洁，维护成本更低

**YAGNI（精益求精）：**
- 备份功能在实际使用中几乎从未被需要
- Git 已经提供了更强大的版本控制

**DRY（杜绝重复）：**
- 不再重复实现版本控制功能

### 向后兼容性

- ✅ 无兼容性问题
- ✅ 旧的 `.bensz-skills-backup/` 目录不会被自动清理（可手动删除）
- ✅ 版本检查和安装报告功能保持不变

### 用户影响

**之前的行为：**
```
removed legacy symlink: /Users/xxx/.claude/skills/pipeline-skills
backed up existing dir: /Users/xxx/.claude/skills/nsfc-abstract-writer -> /Users/xxx/.claude/skills/.bensz-skills-backup/20251228-204613/nsfc-abstract-writer
installed: /Users/xxx/.claude/skills/nsfc-abstract-writer
```

**现在的行为：**
```
removed legacy symlink: /Users/xxx/.claude/skills/pipeline-skills
removed: /Users/xxx/.claude/skills/nsfc-abstract-writer
installed: /Users/xxx/.claude/skills/nsfc-abstract-writer
```

### 如何回退到旧版本

如果需要回退到某个 skill 的旧版本：

1. 使用 Git 回退源代码：
   ```bash
   git checkout <commit-hash> -- <skill-name>
   ```

2. 重新运行安装脚本：
   ```bash
   python3 install-bensz-skills/scripts/install.py
   ```

---

## 2025-12-28: MD5 版本控制机制

### 新增功能

#### 1. MD5 哈希版本控制
- **版本计算**：每个 skill 的 `SKILL.md` 内容计算 MD5 哈希值作为版本标识
- **版本存储**：安装后在目标目录生成 `.skill-manifest.json` 记录版本信息
- **智能安装**：仅安装版本有变化的 skills，跳过未变化的版本

#### 2. 详细安装报告
安装完成后输出清晰的报告，包括：
- ✅ **已安装/更新**：列出本次新安装或版本变化的 skills（含 MD5）
- ⏭️ **跳过**：列出版本未变化未安装的 skills（含原因）
- 📊 **总体摘要**：汇总各目标（Codex/Claude Code）的安装情况

#### 3. 新增命令行参数
- `--force`：强制重新安装所有 skills，忽略 MD5 检查

### 设计原则

**KISS（简单至上）：**
- MD5 计算仅基于 `SKILL.md` 文件（核心定义），而非整个目录
- 版本信息存储为简单的 JSON 文件
- 报告格式清晰直观

**YAGNI（精益求精）：**
- 仅实现必要的版本检查功能
- 不添加复杂的依赖管理
- 不支持回滚等过度功能

**DRY（杜绝重复）：**
- 统一的版本检查逻辑
- 共享的安装/跳过决策流程

**SOLID 原则：**
- **单一职责**：每个函数只做一件事（计算 MD5、检查版本、安装、报告）
- **开闭原则**：易于扩展新的版本控制策略
- **依赖倒置**：通过 `SkillInfo` 数据类解耦数据与逻辑
