# @install - standard-library installer

`@install/install.py` is the single cross-platform installer for bensz skills.
It uses only the Python standard library: no Git, no PyYAML, no shell-specific
bootstrap logic.

## Quick Start

Download and run the installer:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.py').read())"
```

If your system exposes Python as `python3`, use:

```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.py').read())"
```

You can also download the file first, then run it:

```bash
python install.py
```

## Default Behavior

Running the installer with no arguments will:

- Check that Python is new enough for the installer.
- Download remote sources as GitHub zip archives, with retry handling for transient GitHub/network failures.
- Selectively extract the configured `skills_path`, and when `--skill` is used, extract only the requested skill directories where possible.
- Install changed production skills into both `~/.codex/skills/` and `~/.claude/skills/`.
- Skip unchanged skills by MD5.
- Remove legacy skill names from the authoritative `install-bensz-skills/config.yaml` when reachable, with a small built-in fallback list for bootstrap resilience.
- Save an install manifest under `~/.bensz-skills/installation/manifests/`.
- Print installer output in English by default.

## Requirements

- Python 3.8 or newer
- Network access to GitHub

No third-party Python package is required.

## Download Strategy

The installer intentionally keeps the bootstrap path Git-free, so it still
downloads GitHub zip archives. To keep large repositories cheaper to process,
it avoids extracting unrelated archive entries:

- `skills_path: "."`: extracts the repository root, or only requested skill directories when `--skill` is set.
- `skills_path: "skills"` or another subdirectory: extracts that subtree, or `skills_path/<skill-name>` for each requested skill.
- If a requested skill is absent from a source, the source is treated as having no matching skill instead of forcing a full extraction pass.
- Zip and raw config downloads are retried before failing, and archives are written through a temporary `.part` file so interrupted downloads do not leave a half-written zip as the final source.

## Dependency Reachability

The installer is designed for remote bootstrap use, so it does not import
`install-bensz-skills` Python modules and does not require PyYAML. For mutable
business rules such as `legacy_skill_names`, it first reads
`install-bensz-skills/config.yaml` from the `general` source via GitHub raw
content. If that is not reachable, it falls back to the config file inside a
downloaded `general` archive, then finally to a minimal built-in fallback list.

## Options

```bash
python install.py --codex                 # Install to Codex only
python install.py --claude                # Install to Claude Code only
python install.py --force                 # Reinstall even when MD5 is unchanged
python install.py --dry-run               # Print actions without writing files
python install.py --check                 # Alias for --dry-run
python install.py --skill git-commit      # Install/update one selected skill only
python install.py --skill git-commit,docx # Install/update selected skills only
python install.py --lang zh               # Use Chinese installer messages
python install.py --source general        # Install one source
python install.py --source general,research
```

Available source IDs:

| ID | Repository | Skills path |
|----|------------|-------------|
| `general` | `huangwb8/skills` | `.` |
| `research` | `huangwb8/ChineseResearchLaTeX` | `skills` |
| `anthropic-docs` | `anthropics/skills` | `skills` |

## Install Locations

| Tool | Unix/macOS | Windows |
|------|------------|---------|
| Codex | `~/.codex/skills/` | `%USERPROFILE%\.codex\skills\` |
| Claude Code | `~/.claude/skills/` | `%USERPROFILE%\.claude\skills\` |

## Troubleshooting

If Python is not found, install Python 3.8+ first:

- macOS: `brew install python`
- Ubuntu/Debian: `sudo apt install python3`
- Windows: install Python from `https://www.python.org/downloads/` and enable "Add Python to PATH"

If the one-line command is blocked by your shell policy, download `install.py`
with a browser or command-line downloader and run `python install.py`.
