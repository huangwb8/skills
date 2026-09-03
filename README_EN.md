# Bensz Agent Skills

A reusable Skill collection and development pipeline following the [Agent Skills Open Standard](https://agentskills.io). It turns Skill creation, testing, documentation, installation, and release into a repeatable workflow for Claude Code, OpenAI Codex, Cursor, and other compatible hosts.

[中文](README.md)

> **Turn Skills from files into systems.**

`huangwb8/skills` is more than a collection of `SKILL.md` files. It is a project for developing, running, and assuring Agent Skills. As Skills become long-lived parts of agent systems, the project asks not only “how do we write a Skill?” but also how to develop, test, run, and verify that it behaves as intended.

## What the project is building

The repository has three parts:

- **Reusable general Skills**: automated testing, multi-agent collaboration, parallel workspaces, prompt optimization, research plotting, Git operations, installation, documentation, and bug feedback.
- **A Skill development and maintenance pipeline**: a shared lifecycle from development → testing → documentation → installation → use → feedback → iteration.
- **Skill Runtime**: `bensz-skill-kernel` is evolving support for State, Verifier, Gate, Contract Pack, workspaces, evidence, event ledgers, audit, and replay.

The Runtime does not try to turn Skills into traditional programs. It makes important states, checks, and evidence in complex agent workflows explicit and traceable.

## Why this project exists

As Skill collections and workflows grow, a longer `SKILL.md` cannot by itself answer whether a Skill triggered correctly, skipped a step, regressed after a change, remained traceable during collaboration, recorded the right checks, or clearly located a failure. This project therefore moves from Skill authoring toward broader **Skill engineering**.

## Design principles

- Open standards first, without binding the project to one platform.
- Separate Skill and Runtime: domain workflows stay in Skills; shared execution stays in the Kernel.
- Explicit state over implicit guesses, checking over default trust, and replayability over opacity.
- Progressive enhancement: keep ordinary Skills simple and use stronger runtime capabilities only when needed.

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
- **Lifecycle kernel**: `packages/bensz-skill-kernel/` provides the `bsk` CLI plus replayable State, Verifier, Workspace, event-ledger, and Gate runtime.
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

`bootstrap_install.py` uses only the Python standard library and supports Python 3.8+. Its default sources are defined in `skills/alpha/install-bensz-skills/config.yaml`:

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

The full local installer follows the repository's Python 3.10+ development matrix and supports `--source`, `--skill`, `--force`, and `--legacy-source`:

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 skills/alpha/install-bensz-skills/scripts/install.py
python3 skills/alpha/install-bensz-skills/scripts/install.py --skill write-readme
```

Install manifests, MD5 records, and remote caches live under `~/.bensz-skills/installation/`. Beta Skills are never mixed into the default source.

## Kernel: State, Verifier, and Workspace

`bensz-skill-kernel` requires Python 3.11+ and uses PyYAML plus the standard library at runtime. It is independent from Skill installation.

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

States use `owner.machine.state` canonical IDs; Verifiers use `owner.domain.capability`, with legacy IDs resolved through aliases. Pack indexes and contracts are documented in [`docs/state-id-naming.md`](docs/state-id-naming.md), [`docs/verifier-id-naming.md`](docs/verifier-id-naming.md), and [`packages/bensz-skill-kernel/README.md`](packages/bensz-skill-kernel/README.md).

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

# Inspect the BAC contribution ledger
bac --root . --bac-file docs/contribution.bac inspect
```

When changing a Skill, keep `SKILL.md`, `config.yaml`, README, and CHANGELOG aligned. Record important repository changes under `[Unreleased]` in `CHANGELOG.md` first.

## Compatibility and boundaries

- Skill files follow the open standard; actual triggering depends on host support for Skill directories.
- The local installer supports Python 3.10+; remote bootstrap requires Python 3.8+; the Kernel requires Python 3.11+.
- Kernel process timeouts, I/O limits, and fail-closed options are not a container or OS sandbox. Run untrusted code in an isolated environment.
- Remote installation requires GitHub access. On network failure, use the local installer or an existing cache and check the exit status.

## Contributing and license

Read [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md) first. Ordinary pull requests are not currently accepted without prior discussion; contact [huangwb8](https://github.com/huangwb8) before contributing.

This project is licensed under MIT; see [`LICENSE`](LICENSE).

More entry points: [`CHANGELOG.md`](CHANGELOG.md) · [`docs/verifier-tutorial.md`](docs/verifier-tutorial.md) · [`docs/state-machine-tutorial.md`](docs/state-machine-tutorial.md) · [`skills/alpha/install-bensz-skills/README.md`](skills/alpha/install-bensz-skills/README.md)
