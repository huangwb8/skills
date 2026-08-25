<div align="center">

# Skills Development Pipeline

[![Version](https://img.shields.io/github/v/tag/huangwb8/skills?label=version&sort=semver)](https://github.com/huangwb8/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#platform-compatibility)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[中文](README.md) | [English](README_EN.md)

<strong>Reusable Agent Skills library and development pipeline built on the Agent Skills Open Standard</strong>

</div>

This repository is a skills library and development pipeline built around the Agent Skills Open Standard. It covers skill creation, testing, documentation, installation, release, and bug reporting. The repo contains both reusable production skills and the instructions, scripts, and workflows used to maintain them.

## 🎯 Who This Repository Is For

- People who want to install a set of skills system-wide and trigger them from any project
- Maintainers who want to build, refine, test, and publish their own skills
- Teams who want to reuse the engineering rules, documentation conventions, and quality workflow in this repo
- Anyone building on the Agent Skills standard across Claude Code, Codex, Cursor, and related platforms

## 💡 Recommended Development Environment

### 🧰 VS Code + Claude Code / Codex Extension

We recommend using VS Code together with the Claude Code or Codex extension for skill development, testing, and maintenance.

| Benefit | Description |
|---------|-------------|
| Native skill integration | Loads installed skills directly from system-level skill directories |
| Real-time validation | Test skill triggering and execution with natural language prompts |
| Context-aware editing | Lets the AI understand relationships across skills, scripts, and docs |
| Integrated workflow | Edit, test, install, and iterate in one place |
| Documentation maintenance | Makes it easier to keep `SKILL.md`, `README.md`, `config.yaml`, and `CHANGELOG.md` in sync |

📺 [Watch Demo Video (Bilibili)](https://www.bilibili.com/video/BV1tpcezbERB)

## ⚡ AI Compute

For background on AI compute and the broader setup around this repository, see:

📺 [Watch AI Compute Overview (Bilibili)](https://www.bilibili.com/video/BV1a7ZLBuE5z)

## 🧩 Core Skills

`skills/alpha/` contains publishable skills; `skills/beta/` contains immature candidates and is never installed by default:

| Skill | Primary purpose | Typical use case |
|-------|------------------|------------------|
| `init-project` | Initialize project instruction files | Generate `AGENTS.md`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `.gitignore`, plus `docs/` and `docs/plans/` |
| `install-bensz-skills` | Install skills system-wide | Copy this repo's skills into `~/.codex/skills/` and `~/.claude/skills/` |
| `write-skill-readme` | Generate user-facing skill docs | Produce a `README.md` for a skill |
| `auto-test-skill` | Skill-level critical testing | Evaluate a skill's workflow, output quality, and robustness |
| `auto-test-project` | Project-level critical testing | Review an entire project through repeated finding, fixing, and verification rounds |
| `better-prompt` | Prompt optimization | Rewrite rough prompts into clearer, more executable versions |
| `awesome-code` | Multi-agent collaborative development | Break down work, classify agents into three dispatch levels, enforce required-agent gates, and coordinate parallel execution |
| `parallel-vibe` | Multi-workspace parallel exploration | Run the same instruction across isolated workspaces to compare solutions |
| `git-commit` | Git commit automation | Generate conventional commits and optionally push automatically |
| `git-pr-review` | Read-only GitHub PR review | Decide whether a PR is worth merging and generate a structured report |
| `git-publish-release` | GitHub release publishing | Generate release notes and create GitHub releases |
| `bensz-collect-bugs` | Collect and report skill-design bugs | Record skill design issues and, when explicitly requested, report them via `gh` |

For detailed usage, open the corresponding `README.md` and `SKILL.md` inside each skill directory.

## ✨ Repository Capabilities

- A standardized way to build Agent Skills for multiple platforms
- A set of reusable general-purpose skills
- A full maintenance chain covering creation, testing, documentation, installation, release, and bug reporting
- A system-level installation model that improves discoverability across projects
- Long-term engineering guardrails built around KISS, YAGNI, DRY, Single Source of Truth, and organic updates

## 🗂️ Task Workspaces

Skills that need to write files keep their process artifacts under `.bensz-api/task-{yyyymmdd-hhmm}-{short-description}/`, so plans, logs, and temporary output do not spill into the project root. A single-skill task creates only that skill's boundary; `shared/` is used only when several skills collaborate.

```text
.bensz-api/task-20260717-1432-optimize-skill-workspace/
├── shared/                 # Shared inputs and provenance for multi-skill tasks only
└── {skill-name}/
    ├── input/              # Inputs, parameter snapshots, and upstream references
    ├── output/             # Drafts and intermediate results for later stages
    └── log/                # Commands, validation, errors, and decision summaries
```

Final deliverables, user-requested files, project documentation, and source changes still follow the project's normal directory conventions; they are not written to this hidden workspace by default. Older hidden directories are only for explicitly requested compatibility reads, migrations, or cleanup.

## 🌐 Platform Compatibility

Based on this repository's conventions and the surrounding Agent Skills ecosystem, the primary compatible platforms include:

| Platform | Status | Common skill directory |
|----------|--------|------------------------|
| [Claude Code](https://code.anthropic.com) | Verified | `~/.claude/skills/` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | Verified | `~/.codex/skills/` |
| Cursor | Compatible | `~/.cursor/skills/` |
| GitHub | Compatible | `.github/skills/` |
| VS Code | Compatible | `.vscode/skills/` |
| Amp | Compatible | Platform-specific |
| Letta | Compatible | Platform-specific |
| Goose | Compatible | Platform-specific |

## 🚀 Quick Start

### ⚡ Recommended: One-Line Remote Installation

Install directly to system-level skill directories with the standard-library bootstrap bundled inside `install-bensz-skills`, without cloning the repo first. It downloads GitHub zip archives, skips unchanged skills by MD5, and writes install manifests. The repository's `general` source is fixed to `skills/alpha`.

| Platform | Command |
|----------|---------|
| All platforms with Python | `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())"` |
| macOS / Linux fallback | `python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())"` |

Support matrix: repository development and the full local installer use Python 3.10+; the dependency-free bootstrap requires Python 3.8+ and uses only the standard library.

Default remote sources:

- `general`: general-purpose skills from `huangwb8/skills`
- `research`: research skills from `huangwb8/ChineseResearchLaTeX`
- `anthropic-docs`: document-processing skills from `anthropics/skills`

Default install locations:

- `~/.claude/skills/`
- `~/.codex/skills/`

Common options:

```bash
# Install only the general skills from this repository
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --source general

# Install only to Codex or Claude Code
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --codex
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --claude

# Preview actions without writing files
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --check

# Print installer output in Chinese
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --lang zh
```

### 🛠️ Local Development Installation

If you have cloned this repository, or you are actively developing these skills, use the local installer. It auto-detects `skills/alpha/` only; `skills/beta/` requires an explicit `--source`.

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 skills/alpha/install-bensz-skills/scripts/install.py
```

If you only want one target platform:

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --codex
python3 skills/alpha/install-bensz-skills/scripts/install.py --claude
```

If the installer skill is already installed system-wide, you can also call it from another project and point it at a local source directory:

```bash
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --source ./skills/alpha
python3 ~/.claude/skills/install-bensz-skills/scripts/install.py --source ./skills/alpha

# Only for an explicit migration from the historical pipelines layout
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --legacy-source
```

### 🤖 Ask the AI to Run the Installer Skill

After opening this repository in Claude Code or Codex, you can say:

```text
Please use the install-bensz-skills skill to install the skills in this repository into the system-level skills directories so they can be discovered from any project.
```

This is useful if you want installation itself to stay inside a natural-language workflow.

## 📘 Development Rules and Core Docs

- [AGENTS.md](AGENTS.md): Cross-platform project instructions and the single source of truth for repository-level rules
- [CLAUDE.md](CLAUDE.md): Claude Code specific adaptation notes
- [CHANGELOG.md](CHANGELOG.md): All important updates should be recorded under `Unreleased` first

If you plan to change project instructions, workflow, or the README files, start with `AGENTS.md`. This repository expects documentation updates to stay aligned with engineering rules and to be recorded in `CHANGELOG.md`.

## 🤝 Contribution Notes

- Prefer improving existing assets over rewriting them from scratch
- When changing a skill, check whether `SKILL.md`, `README.md`, and `config.yaml` still match
- Record important repository-level updates in `CHANGELOG.md`
- Validate system-level discoverability, not just behavior inside this repository

## 🔗 Resources

- [Agent Skills Open Standard](https://agentskills.io)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [install-bensz-skills User Guide](skills/alpha/install-bensz-skills/README.md)
