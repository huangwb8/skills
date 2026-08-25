# SkillsMP 搜索指南

> 最后更新：2026-01-18
> 注意：本文档可能随外部平台变化而失效，请以官方文档为准

## SkillsMP 概述

**网址**：https://skillsmp.com/

SkillsMP 是 Agent Skills 的主要市场平台，收录超过 37,000 个技能。

## 主要功能

### 1. 智能搜索
- **AI 语义搜索**：理解自然语言查询
- **关键词搜索**：传统关键词匹配
- **分类浏览**：按功能类别浏览

### 2. 质量指标
- Stars 数量
- 下载次数
- 社区评分
- 最后更新时间

### 3. 一键安装
- 支持 marketplace.json
- 兼容 Claude Code、Codex CLI、ChatGPT

## 搜索技巧

### 语义搜索
直接描述需求：
- "帮我做测试驱动开发"
- "需要调试代码的工具"
- "自动生成 Git 提交信息"

### 关键词搜索
使用技术术语：
- "TDD"
- "debugging"
- "git commit"
- "code review"

### 分类浏览
- 测试驱动开发
- 调试与诊断
- 代码质量
- Git 工作流
- Web 开发
- 安全与合规
- DevOps

## API 使用

SkillsMP 提供 API 用于程序化搜索：

```bash
# 搜索技能
curl "https://skillsmp.com/api/search?q=TDD&limit=10"

# 获取技能详情
curl "https://skillsmp.com/api/skills/{skill_id}"
```

## 相关链接

- **官方网站**：https://skillsmp.com/
- **GitHub**：https://github.com/skillsmp/skillsmp
- **文档**：https://docs.skillsmp.com/
