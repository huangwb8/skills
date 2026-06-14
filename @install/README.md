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
- Download remote sources as GitHub zip archives.
- Install changed production skills into both `~/.codex/skills/` and `~/.claude/skills/`.
- Skip unchanged skills by MD5.
- Remove configured legacy skill names.
- Save an install manifest under `~/.bensz-skills/installation/manifests/`.
- Print installer output in English by default.

## Requirements

- Python 3.8 or newer
- Network access to GitHub

No third-party Python package is required.

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
