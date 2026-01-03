<div align="center">

# Skills Development Pipeline

[![Version](https://img.shields.io/github/v/tag/bensz/skills?label=version&sort=semver)](https://github.com/bensz/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#platform-compatibility)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[English](README.md) | [中文](README_ZH.md)

<strong>Reusable Agent Skills Library following the Agent Skills Open Standard</strong>

</div>

A unified skills development pipeline for AI agents. This project maintains a collection of reusable **Agent Skills** that conform to the [Agent Skills Open Standard](https://agentskills.io), enabling seamless cross-platform compatibility.

Skills are **write-once, run-anywhere** – the same skill works identically across Claude Code, OpenAI Codex, Cursor, and other compatible platforms.

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
| [OpenAI Codex](https://openai.com) | ✅ Native | `~/.codex/skills/` |
| Cursor | ✅ Compatible | `~/.cursor/skills/` |
| GitHub | ✅ Compatible | `.github/skills/` |
| VS Code | ✅ Compatible | `.vscode/skills/` |

## Project Structure

```
skills/
├── AGENTS.md              # Core project instructions (engineering principles)
├── CLAUDE.md              # Claude Code specific configuration
├── README.md              # This file
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
│       ├── install.py    # Core installer logic
│       └── i18n.py       # Internationalization
│
└── [future skills]/       # Additional skills following the same structure
```

## Quick Start

### 1. System-wide Installation (Recommended)

Install skills globally to make them available in **any project**:

```bash
# Clone the repository
git clone https://github.com/bensz/skills.git
cd skills

# Run the installer
python3 install-bensz-skills/scripts/install.py
```

The installer will:
- Copy skills to `~/.claude/skills/` and `~/.codex/skills/`
- Use MD5 versioning to update only changed skills
- Support skill categories: normal, auxiliary, test

### 2. Project-local Installation

Copy specific skills to your project:

```bash
# For Claude Code
mkdir -p .claude/skills
cp -r init-project .claude/skills/

# For Codex
mkdir -p .codex/skills
cp -r init-project .codex/skills/
```

### 3. Verify Installation

Start a new session in your AI assistant and test with a trigger phrase:

**Example for `init-project` skill:**
> "Help me initialize a new project with AI context files"

**Example for `install-bensz-skills` skill:**
> "Install these skills system-wide"

## Available Skills

### init-project

**Project documentation generator** – Automatically generates `AGENTS.md` and `CLAUDE.md` for new projects.

**Features:**
- Auto-detects project type (Python/Web/Rust/Go/Java/Data Science/Docs)
- Auto-detects OS language for localization
- Generates comprehensive AI context files
- Template-based customization

**Usage:**
```text
"Initialize a new Python project"
"Generate AGENTS.md for my Rust project"
"Create project instructions for a web app"
```

See [init-project/README.md](init-project/README.md) for details.

### install-bensz-skills

**System-wide installer** – Manages skill installation across platforms.

**Features:**
- Cross-platform installation (Claude Code, Codex, etc.)
- MD5-based version control (incremental updates)
- Skill categorization (normal/auxiliary/test)
- Internationalization support (en/zh)

**Usage:**
```text
"Install these skills system-wide"
"Update all installed skills"
```

See [install-bensz-skills/README.md](install-bensz-skills/README.md) for details.

## Creating Your Own Skills

Skills follow the **Agent Skills Open Standard** with a three-file architecture:

### 1. SKILL.md (Required)

AI-facing instruction file that defines:
- Trigger conditions
- Workflow steps
- Input/output specifications
- Validation criteria

### 2. README.md (Recommended)

User-facing guide that explains:
- What the skill does
- How to trigger it
- Prompt examples
- Tips and best practices

### 3. config.yaml (Recommended)

Configuration file for:
- Tunable parameters
- Thresholds and values
- Platform-specific settings

**Minimum SKILL.md structure:**

```markdown
---
name: my-new-skill
description: What this skill does and when to use it
version: 1.0.0
author: Your Name
metadata:
  keywords: [keyword1, keyword2]
  short-description: One-line summary
---

# Skill Name

## Trigger Conditions
When to use this skill.

## Workflow
1. Step one
2. Step two

## Validation
How to verify success.
```

See [AGENTS.md](AGENTS.md) for comprehensive guidelines on skill development.

## Organic Update Philosophy

This project follows **organic whole-system updates** based on established engineering principles:

- **KISS** – Keep designs simple and straightforward
- **YAGNI** – Implement only what's needed now
- **DRY** – Avoid duplication through abstraction
- **SOLID** – Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion

**Key principle:** When updating a skill, consider its entire ecosystem – metadata, documentation, configuration, and references must evolve together coherently.

See [AGENTS.md](AGENTS.md) → "Engineering Principles Foundation" for details.

## Development Guide

### Adding a New Skill

```bash
# Create skill directory
mkdir my-new-skill
cd my-new-skill

# Create required files
touch SKILL.md README.md config.yaml

# Add scripts if needed
mkdir scripts
touch scripts/my-script.py
```

### Skill File Structure

```
my-skill/
├── SKILL.md           # Required: AI instructions
├── README.md          # Recommended: User guide
├── config.yaml        # Recommended: Configuration
├── CHANGELOG.md       # Optional: Version history
├── references/        # Optional: Detailed docs
│   └── advanced-guide.md
└── scripts/           # Optional: Automation
    └── process.py
```

### Best Practices

1. **YAML Frontmatter** – Keep `description` clear and semantic for discovery
2. **Progressive Disclosure** – Keep SKILL.md lean, move details to references/
3. **Header-Body Alignment** – Sync metadata with actual behavior
4. **Lazy Loading** – Don't load everything at startup
5. **Platform Agnostic** – Avoid platform-specific code when possible

## Architecture Layers

### 1. Metadata Layer (YAML Frontmatter)

- **Purpose:** Skill discovery and activation
- **Fields:** name, description, version, keywords
- **Loaded:** At session start
- **Critical:** `description` determines semantic matching

### 2. Operations Layer (SKILL.md)

- **Purpose:** AI execution instructions
- **Content:** Workflow, steps, validation
- **Loaded:** When skill triggers
- **Goal:** Keep concise (ideally <500 lines)

### 3. Knowledge Layer (references/)

- **Purpose:** Detailed background and theory
- **Content:** Standards, best practices, examples
- **Loaded:** On-demand
- **Structure:** Single-level references from SKILL.md

### 4. Tool Layer (scripts/)

- **Purpose:** Automation and computation
- **Content:** Python/bash scripts
- **Execution:** Called by AI when needed
- **Style:** Explicit error handling, documented constants

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
- [Skill Directory](https://github.com/bensz/skills) – Browse all skills

## License

MIT License – See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the AI agent ecosystem**

[agentskills.io](https://agentskills.io) • [GitHub](https://github.com/bensz/skills)

</div>
