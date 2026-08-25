---
name: validate-md-ref
description: 验证 Markdown 文档中的 URL 引用是否可访问，提取各类引用格式，生成验证报告供 AI 进一步处理
metadata:
  author: Bensz Conan
  short-description: Markdown 引用验证工具
  keywords:
    - validate-md-ref
    - 引用验证
    - URL 检查
    - 链接有效性
    - 引用提取
---

# Markdown 引用验证技能

版本由 `config.yaml:skill_info.version` 统一管理。站内 `#anchor` 必须在当前 Markdown 本地校验；外部 URL 的 HEAD 返回 403/405 时允许一次有限 GET 回退。

## BenszAPI 任务工作区

本 Skill 的新任务中间文件统一写入 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/{skill名}/input|output|log/`。同一任务复用一个任务根目录；多 Skill 协作才创建 `shared/`。正式交付物不写入该目录，历史隐藏目录只允许显式兼容读取、迁移或清理。

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

## 技能目标

验证 Markdown 文档中的 URL 引用是否可访问，提取各类引用格式，生成结构化验证报告供 AI 进一步分析和处理。

## 工作流程

### 阶段一：引用提取

1. **读取目标文档**：使用 Read 工具读取用户指定的 Markdown 文件
2. **识别引用模式**：
   - 标准 Markdown 链接：`[文本](URL)`
   - HTML `<a>` 标签：`<a href="URL">文本</a>` 或 `<a href='URL'>文本</a>`
   - 参考文献链接：`[编号]: URL "描述"`
   - 脚注式引用：`[^1]: URL` 或类似格式
3. **建立引用索引**：记录每个引用的位置、类型、URL 和上下文描述

### 阶段二：URL 验证

1. **执行可达性检查**：
   - 使用 Bash 工具执行 `python3 scripts/validate_links.py <markdown_file> [config_file]`
   - 脚本会自动定位技能根目录，无需指定绝对路径
   - 脚本使用 curl 验证每个 URL 的 HTTP 状态码

2. **判断响应状态**：
   - **有效**：HTTP 200-299
   - **重定向**：HTTP 300-399（已跟随重定向）
   - **客户端错误**：HTTP 400-499（标记为无效）
   - **服务器错误**：HTTP 500-599（标记为存疑）
   - **网络错误**：无法连接（标记为无效）

3. **安全验证**：
   - URL 格式验证（防止命令注入）
   - 文件路径验证（防止路径遍历）
   - 协议限制（仅支持 http/https）

### 阶段三：结果分析

1. **解析脚本输出**：JSON 格式的验证结果
2. **分类处理**：
   - 有效引用：保持原样
   - 无效引用：AI 根据上下文决定处理方式（移除/注释/标记）
3. **生成报告**：汇总验证统计和详细结果

### 注意事项

**当前实现范围**（v0.2.0）：
- ✅ URL 可达性验证（通过 scripts/validate_links.py，支持自动路径定位）
- ✅ 引用提取（支持 Markdown 链接、HTML `<a>` 标签、参考文献、脚注）
- ✅ 安全验证（路径、URL 格式）
- ✅ 自动配置加载（默认使用技能内 config.yaml）
- ❌ 内容对比（需 AI 手动处理）
- ❌ 无效链接自动修正（需 AI 手动处理）
- ❌ 引用重编号（需 AI 手动处理）

## 输入要求

- **必需参数**：目标 Markdown 文件路径
- **可选参数**：配置文件路径（不指定时自动使用技能根目录下的 config.yaml）

**用法示例**：
```bash
# 使用默认配置
python3 scripts/validate_links.py "path/to/document.md"

# 指定配置文件
python3 scripts/validate_links.py "path/to/document.md" "custom-config.yaml"
```

## 输出规范

### 1. 脚本输出格式

`scripts/validate_links.py` 输出 JSON 格式：

```json
{
  "file": "path/to/file.md",
  "summary": {
    "total": 10,
    "valid": 8,
    "invalid": 2,
    "skipped": 0,
    "valid_rate": "80.0%"
  },
  "references": [
    {
      "index": 0,
      "type": "standard_link",
      "url": "https://example.com",
      "text": "示例",
      "line_number": 10,
      "full_match": "[示例](https://example.com)",
      "validation": {
        "url": "https://example.com",
        "valid": true,
        "status_code": 200,
        "redirected": false,
        "final_url": "https://example.com",
        "error": null
      }
    }
  ]
}
```

### 2. 验证报告

AI 基于脚本输出生成 `validate-md-ref-report.md`：

```markdown
# Markdown 引用验证报告

## 验证概要
- 文件：{文件路径}
- 扫描时间：{时间戳}
- 发现引用总数：{数量}
- 有效引用：{数量}
- 无效引用：{数量}

## 详细结果

### ✅ 有效引用
- [1] {URL} - {描述}

### ❌ 无效引用（需处理）
- ~~[2] {URL}~~ - 原因：{404 Not Found}

## 建议操作
（AI 根据验证结果手动处理无效引用）
```

## 验证标准

| 维度 | 标准 |
|------|------|
| **URL 可达性** | HTTP 状态码 200-299 或有效重定向 |
| **引用完整性** | 正确识别标准链接、参考文献、脚注等格式 |

## 安全注意事项

- 路径验证：防止路径遍历攻击（验证文件路径在允许范围内）
- URL 验证：防止命令注入（验证 URL 格式，仅支持 http/https）
- 域名过滤：支持白名单/黑名单配置（config.yaml）
- 超时保护：请求超时防止卡死（默认 10 秒）

## 质量保证

- **确定性操作**：引用提取、URL 验证使用 `scripts/validate_links.py`
- **AI 判断**：无效引用处理、内容对比由 AI 动态分析
- **用户确认**：重大修改前生成预览供用户审核

## 技术实现

### 自动路径定位机制

脚本使用多层回退机制自动定位技能根目录，确保在任何工作目录下都能正常运行：

| 优先级 | 定位方式 | 说明 |
|--------|----------|------|
| **1** | `__file__` 解析 | 从脚本自身的绝对路径推导出技能根目录（最可靠） |
| **2** | 环境变量 | 读取 `VALIDATE_MD_REF Skill_PATH`（支持自定义安装路径） |
| **3** | 常见路径探测 | 检查 `~/.claude/skills/`、`~/.codex/skills/` 等标准位置 |
| **4** | 错误提示 | 所有方法失败时提供详细的诊断信息 |

**路径解析示例**：
```
脚本位置: /home/user/.claude/skills/validate-md-ref/scripts/validate_links.py
__file__ 指向: /home/user/.claude/skills/validate-md-ref/scripts/validate_links.py
parents[1]: /home/user/.claude/skills/validate-md-ref/ (技能根目录)
验证: (skill_root / "SKILL.md").exists() → True
```

**跨平台兼容性**：
- 使用 `pathlib.Path` 处理路径（自动处理 Windows/macOS/Linux 差异）
- 始终使用正斜杠作为路径分隔符（通过 `.resolve()` 规范化）
- 脚本通过 `python3` 显式调用，避免shebang兼容性问题

## 配置选项

详见 `config.yaml`：

- `validation.timeout`：请求超时时间（秒）
- `validation.follow_redirects`：是否跟随重定向
- `domain_whitelist`：允许验证的域名列表（空表示不限制）
- `domain_blacklist`：禁止验证的域名列表（localhost、内部网络等）
