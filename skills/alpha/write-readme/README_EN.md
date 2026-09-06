# write-readme — GitHub README Writing Guide

`write-readme` creates two aligned project documents: Chinese `README.md` and English `README_EN.md`. It reads repository facts first, then organizes a Quick Start, examples, configuration, limitations, security, contribution, and license sections for the project type.

## Quick Start

```text
Please use the write-readme skill to write a polished GitHub README for /path/to/project.
Choose a template from the repository evidence, and output README.md in Chinese and README_EN.md in English with identical sections, commands, links, and facts.
```

For an Agent Skill:

```text
Please use the write-readme skill to create a user guide for skills/beta/my-skill.
Read SKILL.md, config.yaml, scripts/, and references/; output README.md (Chinese) and README_EN.md (English) without modifying the Skill source.
```

## How it writes

The first screen defaults to a complete GitHub Hero: a centered title or real mark, evidence-backed badges, language and documentation navigation, a value proposition, a short explanation, then real visual proof or the shortest Quick Start. It answers three questions: what the project is, why it is useful, and how to run it quickly. Examples are organized around user tasks, followed by architecture, deployment, limitations, and contribution details. Features, numbers, badges, and commands that cannot be verified from the repository are marked for confirmation instead of being invented.

### Template selection

| Project shape | First-screen focus | Reference template |
|---|---|---|
| Python/JS/Rust library or SDK | Install + smallest API + supported versions | `references/templates/library.md` |
| CLI, HTTP service, or Worker | One-command run + configuration + health check | `references/templates/cli-service.md` |
| Web/desktop application | Screenshot or Demo + user journey + deployment | `references/templates/web-app.md` |
| Dataset, training, or inference project | Data/model license + reproducibility + resources | `references/templates/data-ml.md` |
| Agent Skill or plugin | Trigger prompt + inputs/outputs + host installation | `references/templates/agent-skill.md` |

## Recommended checks

- A clean environment can complete Quick Start, including prerequisites and expected results.
- Examples start with the smallest runnable snippet; larger material links to deeper documentation.
- Badges, images, links, versions, and performance numbers have repository or public evidence.
- Heading trees, code blocks, commands, environment variables, paths, links, and license facts stay aligned across Chinese and English.
- Limitations, security, data licenses, and unverified items are explicit; marketing language does not replace evidence.

## Deterministic check after generation

```bash
# Run from the project root
python3 /path/to/write-readme/scripts/check_readme_pair.py README.md README_EN.md
```

The script checks file presence, heading trees, code fences, relative links, and command/environment-token drift. It does not replace a human review of semantic accuracy.

## Optional runtime verification

When `bensz-skill-kernel` is available, the host can read `config.yaml.runtime`
and record the domain phases `input-ready → facts-collected →
bilingual-draft-ready → delivery-ready → reported`. The
`bensz.document.readme-pair-alignment` Pack performs deterministic bilingual
structure checks, while path scope, file existence, Markdown links, redaction,
and provenance reuse kernel atomic Verifiers. Structural, scope, or secret
findings block delivery; token drift, unobservable network checks, and semantic
fact gaps remain uncertain and require human review. Without the Kernel, the
script above is still useful, but it must not be presented as a runtime Gate.

## FAQ

### Why always produce two READMEs?

The Chinese version serves Chinese readers, while the English version supports international collaboration. They share the same facts and structure so one side does not silently become stale.

### What if the project has no screenshot or live Demo?

Do not invent visual material. Use a smallest terminal output, API response, or real example, and state that no Demo is currently available.

### Can I request English only?

Yes, when explicitly requested. The repository default remains bilingual; record the exception in the task summary.

### Can I still use `write-skill-readme`?

Its Agent Skill README capability is now part of this Skill. The old directory remains as legacy source, is no longer installed by default, and is cleaned from system-level directories by the installer.

## Further reading

- `SKILL.md`: AI execution contract and safety boundaries
- `references/readme-principles.md`: distilled community and Trending research
- `references/github-hero-patterns.md`: complete GitHub Hero anatomy, four reusable patterns, accessibility gates, and sources
- `references/research-notes.md`: sources and sample notes
- `references/templates/`: section skeletons by project type
- `scripts/check_readme_pair.py`: bilingual README structure checker
- `references/states/` and `references/verifiers/`: optional Kernel phase and verification contracts
