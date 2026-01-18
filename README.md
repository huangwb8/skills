<div align="center">

# Skills Development Pipeline

[![Version](https://img.shields.io/github/v/tag/huangwb8/skills?label=version&sort=semver)](https://github.com/huangwb8/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#platform-compatibility)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[English](README.md) | [中文](README_ZH.md)

<strong>Reusable Agent Skills Library following the Agent Skills Open Standard</strong>

</div>

A unified skills development pipeline for AI agents, maintaining reusable **Agent Skills** conforming to the [Agent Skills Open Standard](https://agentskills.io) for seamless cross-platform compatibility. Skills are **write-once, run-anywhere** – working identically across Claude Code, OpenAI Codex, Cursor, and other compatible platforms.

## Highlights

- **🔄 Unified Skill Library** – Single codebase for multiple agent platforms
- **📋 Open Standard** – Follows [agentskills.io](https://agentskills.io) specifications
- **🚀 System-wide Installation** – Skills available in any project via installer
- **🎯 Organic Updates** – Guided by SOLID, KISS, YAGNI, DRY principles
- **📚 Progressive Disclosure** – Three-layer architecture: metadata → operations → knowledge
- **🔍 Semantic Discovery** – Skills trigger based on natural language intent

## Platform Compatibility

| Platform | Status | Install Path |
|----------|--------|--------------|
| [Claude Code](https://code.anthropic.com) | ✅ Native | `~/.claude/skills/` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | ✅ Native | `~/.codex/skills/` |
| Cursor | ✅ Compatible | `~/.cursor/skills/` |
| GitHub | ✅ Compatible | `.github/skills/` |
| VS Code | ✅ Compatible | `.vscode/skills/` |

## Recommended Development Environment

### 💡 VS Code + Claude Code / Codex Extension

For the best skill development experience, we recommend using **VS Code** with the **Claude Code** or **Codex** extension.

**Why this combination?**

| Benefit | Description |
|---------|-------------|
| **🎯 Native Skill Integration** | Extensions load skills from `~/.claude/skills/` or `~/.codex/skills/` automatically |
| **⚡ Real-time Validation** | Test skill triggers instantly with natural language prompts |
| **🔍 Context-Aware Editing** | AI understands your project structure and applies organic update principles |
| **🛠️ Integrated Workflow** | No context switching – edit, test, and iterate in one environment |
| **📝 Smart Documentation** | AI helps maintain header-body alignment across SKILL.md, README.md, and config.yaml |

## Project Structure

```
skills/
├── AGENTS.md              # Core project instructions (engineering principles)
├── CLAUDE.md              # Claude Code specific configuration
├── README.md              # English documentation
├── README_ZH.md           # 中文文档
│
├── init-project/          # Skill: Project documentation generator
│   ├── SKILL.md          # Skill definition (AI-facing)
│   ├── README.md         # User guide (human-facing)
│   ├── config.yaml       # Configuration parameters
│   ├── scripts/          # Automation scripts
│   │   └── generate.py   # Generate AGENTS.md + CLAUDE.md
│   └── templates/        # Document templates
│
├── install-bensz-skills/  # Skill: System-wide installer
│   ├── SKILL.md          # Skill definition
│   ├── README.md         # User guide
│   ├── CHANGELOG.md      # Changelog
│   └── scripts/          # Installation scripts
│
├── git-commit/            # Skill: Smart Git commits
│   ├── SKILL.md          # Skill definition
│   ├── README.md         # User guide
│   └── scripts/          # Automation scripts
│
├── git-publish-release/   # Skill: GitHub release publisher
│   ├── SKILL.md          # Skill definition
│   ├── README.md         # User guide
│   └── scripts/          # Automation scripts
│
├── auto-test-skill/       # Skill: Skill-level automated testing
│   ├── SKILL.md          # Skill definition
│   ├── README.md         # User guide
│   ├── config.yaml       # Configuration parameters
│   └── scripts/          # Testing scripts
│
└── auto-test-project/     # Skill: Project-level automated testing
    ├── SKILL.md          # Skill definition
    ├── README.md         # User guide
    └── config.yaml       # Configuration parameters
```

## Quick Start

### 🚀 How to Install Skills in This Project

**Step 1: Clone this project**

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
```

**Step 2: Open Claude Code or Codex in the project's root directory, then type:**

> `"install-bensz-skills this skill install skills in this project to Codex and Claude Code"`

That's it! All skills will be installed system-wide and available in any project.

### 🎯 How to Use Skills in This Project

**Open this project in Claude Code or Codex, then use natural language to trigger skills:**

```text
# Project initialization
"init-project this skill help me initialize project"

# System-wide installation
"install-bensz-skills this skill install skills in this project to Codex and Claude Code"

# Automated testing
"auto-test-skill this skill help me test init-project this skill"
```

**It's that simple!** Natural language programming is the soul of Vibe Coding!

## Skill Development

### File Structure

```
my-skill/
├── SKILL.md           # Required: AI instructions (includes YAML frontmatter)
├── README.md          # Recommended: User guide
├── config.yaml        # Recommended: Configuration parameters
├── CHANGELOG.md       # Optional: Version history
├── references/        # Optional: Detailed documentation
│   └── advanced-guide.md
└── scripts/           # Optional: Automation scripts
    └── process.py
```

### Quick Start

```bash
mkdir my-new-skill
cd my-new-skill
touch SKILL.md README.md config.yaml
```

### Architecture Layers

| Layer | File/Directory | Purpose | When Loaded |
|-------|---------------|---------|-------------|
| **Metadata** | YAML Frontmatter | Skill discovery and activation | At session start |
| **Operations** | SKILL.md | AI execution instructions | When skill triggers |
| **Knowledge** | references/ | Detailed background and theory | On-demand |
| **Tools** | scripts/ | Automation and computation | When needed |

### Best Practices

- **YAML Frontmatter** – Keep `description` clear and semantic
- **Progressive Disclosure** – Keep SKILL.md lean (<500 lines), move details to references/
- **Header-Body Alignment** – Sync metadata with actual behavior
- **Lazy Loading** – Don't load everything at startup
- **Platform Agnostic** – Avoid platform-specific code when possible

For comprehensive development guidelines, see [AGENTS.md](AGENTS.md).

## Contributing

Contributions welcome! Please ensure:

1. **Follow the Standard** – Comply with [agentskills.io](https://agentskills.io)
2. **Complete Documentation** – SKILL.md + README.md at minimum
3. **Organic Updates** – Maintain header-body consistency
4. **Test Across Platforms** – Verify on Claude Code and Codex if possible

## Resources

- [Agent Skills Open Standard](https://agentskills.io)
- [AGENTS.md](AGENTS.md) – Project instructions and philosophy
- [CLAUDE.md](CLAUDE.md) – Claude Code specific notes
- [Skill Directory](https://github.com/huangwb8/skills) – Browse all skills

## License

MIT License – See [LICENSE](LICENSE) for details.
