<div align="center">

# Bensz Agent Skills

**Turn Agent Skills from files into systems.**

A reusable Skill collection, development pipeline, and tools for checking and tracing Skill execution, built on the [Agent Skills Open Standard](https://agentskills.io).

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Open_Standard-7c3aed?style=flat-square)](https://agentskills.io)
[![Hosts](https://img.shields.io/badge/Hosts-Claude_Code_%C2%B7_Codex_%C2%B7_Cursor-2563eb?style=flat-square)](#compatibility-and-boundaries)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-Python_3.8%2B-0ea5e9?style=flat-square)](#compatibility-and-boundaries)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](LICENSE)

[Quick start](#get-started-in-30-seconds) · [Skill map](#skill-map) · [Kernel](#kernel) · [Development](#development-and-verification) · [中文](README.md)

</div>

![Agent Skills: Build · Test · Run · Know](docs/assets/agent-skills-ecosystem-v5.jpg)

| **BUILD** | **TEST** | **RUN** | **KNOW** |
| :---: | :---: | :---: | :---: |
| Create and standardize | Regression and quality gates | Install and run across hosts | State, evidence, and audit |

This is more than a collection of `SKILL.md` files. It connects Skill creation, testing, documentation, installation, and release into a repeatable engineering workflow—and explores how to know that a Skill still behaves as intended once it becomes a long-lived part of an agent system.

## What the project is building

The repository has three parts:

- **Reusable general Skills**: automated testing, multi-agent collaboration, parallel workspaces, prompt optimization, research plotting, Git operations, installation, documentation, and bug feedback.
- **A Skill development and maintenance pipeline**: a shared lifecycle from development → testing → documentation → installation → use → feedback → iteration.
- **Skill execution and checking tools**: `bensz-skill-kernel` is evolving support for task stages, automated checks, workspaces, evidence, event ledgers, audit, and replayable execution records.

These tools do not try to turn Skills into traditional programs. They make important stages, checks, and evidence in complex agent workflows explicit and easier to trace.

## Why this project exists

As Skill collections and workflows grow, a longer `SKILL.md` cannot by itself answer whether a Skill triggered correctly, skipped a step, regressed after a change, remained traceable during collaboration, recorded the right checks, or clearly located a failure. This project therefore moves from writing individual Skills toward building and maintaining them as a system.

## Design principles

- Open standards first, without binding the project to one platform.
- Separate Skills and shared tools: domain workflows stay in Skills; shared execution, checking, and record-keeping stay in the Kernel.
- Explicit state over implicit guesses, checking over default trust, and replayability over opacity.
- Progressive enhancement: keep ordinary Skills simple and use stronger execution and checking features only when needed.

## Get started in 30 seconds

Install production Skills from `skills/alpha` without cloning (Python 3.8+ and network access required):

```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --source general
```

For local development after cloning:

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --codex
```

The installer copies Skills to `~/.codex/skills/` and `~/.claude/skills/` by default. Add `--skill git-commit` to install one Skill. `skills/beta/` is processed only with an explicit `--source`.

## What this repository provides

- **Installable Skills**: `skills/alpha/`; each directory has a user-facing `README.md` and an AI-facing `SKILL.md`.
- **Development pipeline**: initialization, prompt optimization, documentation, critical testing, multi-agent work, Git release, and bug reporting.
- **Task execution kernel**: `packages/bensz-skill-kernel/` provides the `bsk` CLI to manage task stages, run checks, save evidence, record events, and replay execution records.
- **Auditable collaboration**: task artifacts live under `.bensz-api/`; contribution records live in `docs/contribution.bac`.

## Skill map

The current `skills/alpha/` source contains 15 production Skills:

| Area | Skills |
| --- | --- |
| Initialization and docs | `init-project` · `write-readme` |
| Testing and collaboration | `auto-test-code` · `auto-test-skill` · `auto-test-project` · `awesome-code` · `parallel-vibe` |
| Prompts and creation | `better-prompt` · `auto-draw-plot` · `compact-bensz-skills` |
| Installation and release | `install-bensz-skills` · `git-commit` · `git-pr-review` · `git-publish-release` |
| Governance | `bensz-collect-bugs` |

Read a Skill's `README.md` for triggers, minimal prompts, inputs/outputs, and FAQ. Maintainers should also read `SKILL.md`, `config.yaml`, and `CHANGELOG.md`.

## Installation

### Remote bootstrap

`bootstrap_install.py` uses only the Python standard library and supports Python 3.8+. It is the repository's only bootstrap/emergency entry point compatible with Python 3.8, 3.9, and 3.10; this compatibility does not extend to the full local installer or the Kernel. Its default sources are defined in `skills/alpha/install-bensz-skills/config.yaml`:

| Source | Contents |
| --- | --- |
| `general` | This repository's `skills/alpha` |
| `research` | Research Skills from `huangwb8/ChineseResearchLaTeX` |
| `anthropic-docs` | Document Skills from `anthropics/skills` |

Common options:

```bash
# Preview without writing files
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --check

# Install to Codex or Claude Code only
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --codex
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --claude
```

### Local installation and development

The full local installer and the repository's standard development environment require Python 3.11+. It supports `--source`, `--skill`, `--force`, and `--legacy-source`:

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 skills/alpha/install-bensz-skills/scripts/install.py
python3 skills/alpha/install-bensz-skills/scripts/install.py --skill write-readme
```

Install manifests, MD5 records, and remote caches live under `~/.bensz-skills/installation/`. Beta Skills are never mixed into the default source.

## Kernel

`bensz-skill-kernel` requires Python 3.11+ and only needs PyYAML plus the Python standard library to run. It is independent from Skill installation.

It provides the `bsk` command for managing task stages, running checks, saving evidence, and replaying execution records. Ordinary users can start with the commands above; State, Verifier, and Workspace are internal concepts mainly useful to maintainers. See [`docs/state-id-naming.md`](docs/state-id-naming.md), [`docs/verifier-id-naming.md`](docs/verifier-id-naming.md), and [`packages/bensz-skill-kernel/README.md`](packages/bensz-skill-kernel/README.md) for details.

```bash
python3 -m venv .bensz-api/.venv
.bensz-api/.venv/bin/python -m pip install -e packages/bensz-skill-kernel
.bensz-api/.venv/bin/bsk --version
.bensz-api/.venv/bin/bsk verifier list
```

Common entry points:

```bash
bsk state list
bsk verifier list --tag citation
bsk workspace init . --description citation-review
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

## Layout and workspaces

```text
skills/alpha/                  # Publishable, default-installed Skills
skills/beta/                   # Candidate Skills; explicit source required
packages/bensz-skill-kernel/   # Independent Python kernel package
docs/                          # Current docs, tutorials, and design records
tests/                         # Repository entry-point and cross-package tests
tmp/                           # Test reports and temporary artifacts
.bensz-api/                    # AI task workspaces and tool caches
```

Each logical task that writes files uses one `.bensz-api/task-{yyyymmdd-hhmm}-{description}/`. Final READMEs, source, and plans remain in their normal project locations.

## Development and verification

```bash
# Root tests (cache is written to .bensz-api)
python3 -m pytest

# Check bilingual README headings, fences, links, and command tokens
python3 skills/alpha/write-readme/scripts/check_readme_pair.py README.md README_EN.md

# Report normalized-structure findings for all alpha/beta Skills
python3 skills/alpha/auto-test-project/scripts/check_skill_structure.py --mode report

# Inspect the BAC contribution ledger
bac --root . --bac-file docs/contribution.bac inspect
```

When changing a Skill, keep `SKILL.md`, `config.yaml`, README, and CHANGELOG aligned. Record important repository changes under `[Unreleased]` in `CHANGELOG.md` first.

## Compatibility and boundaries

- Skill files follow the open standard; actual triggering depends on host support for Skill directories.
- Repository development, the full local installer, and the Kernel require Python 3.11+; only the remote bootstrap retains Python 3.8+ compatibility for bootstrap/emergency installation.
- Kernel process timeouts, I/O limits, and fail-closed options are not a container or OS sandbox. Run untrusted code in an isolated environment.
- Remote installation requires GitHub access. On network failure, use the local installer or an existing cache and check the exit status.

## Contributing and license

Read [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md) first. Ordinary pull requests are not currently accepted without prior discussion; contact [huangwb8](https://github.com/huangwb8) before contributing.

This project is licensed under MIT; see [`LICENSE`](LICENSE).

## More resources

These links cover releases, result checking, task stages, and Skill installation. Choose the one that matches your goal.

- [`CHANGELOG.md`](CHANGELOG.md): This is the project's release log, covering new features, fixes, and important changes; start here to see what changed recently.
- [`docs/verifier-tutorial.md`](docs/verifier-tutorial.md): This is a tutorial on checking results, with a complete example of handling failures and recording evidence; read it to see how one check works from start to finish.
- [`docs/state-machine-tutorial.md`](docs/state-machine-tutorial.md): This is a tutorial on task stages, explaining how tasks move forward and how progress is saved and restored; read it to understand how work advances step by step.
- [`skills/alpha/install-bensz-skills/README.md`](skills/alpha/install-bensz-skills/README.md): This is the Skill installer's user guide, covering installation methods, options, and common usage; follow it when you are ready to install a Skill.
- [`docs/templates/skill-body.md`](docs/templates/skill-body.md): The four-section body skeleton for creating or modifying a Skill.
- [`docs/templates/skill-common-constraints.md`](docs/templates/skill-common-constraints.md): The shared long-form constraints for workspaces, BAC, privacy, and defect reporting.
