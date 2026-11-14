<div align="center">

# Bensz Skill Identity (BSI)

**Verify the identity, files, and trust policy of a Skill release.**

[![PyPI](https://img.shields.io/pypi/v/bensz-skill-identity?style=flat-square)](https://pypi.org/project/bensz-skill-identity/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-2563eb?style=flat-square)](https://pypi.org/project/bensz-skill-identity/)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/LICENSE)

[Installation and commands](#installation-and-commands) · [Python API](#python-api) · [Protocol](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-protocol.md) · [简体中文](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/README.md)

</div>

Bensz Skill Identity (**BSI**, distributed as `bensz-skill-identity`) is an independent Python 3.11+ library by Bensz Conan. It complements Bensz Skill Kernel (BSK), with the commands `bsi` and `bsk`, respectively. BSI builds Ed25519-signed releases, checks actual files, applies explicit trust and bounded revocation policies, and locks exact dependencies. It does not depend on BSK or router.

The current assurance is `files_verified`. Signatures establish the publishing relationship and file integrity. Code safety, the bytes a host actually loads, and tool permissions need separate policies and host evidence. See the [protocol](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-protocol.md) and [host capability report](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-host-capability.md) for the scope.

## How it works

![Skill identity and release workflow: a root key authorizes a release key; signed releases are checked against actual files, explicit administrator trust, and security revisions. Only allow decisions proceed to strict installation; trust_required and deny stop.](https://chevereto.hwb0307.com/images/2026/11/14/skill-identity-workflow.jpg)

A root public-key fingerprint and a stable key identify a Skill; its version identifies a release. Publishers sign the complete file inventory. Recipients reread files and apply explicit trust, revocation information, and local security revisions to decide whether installation is allowed. Strict installation checks staging again and retains signed evidence for later verification.

## Installation and commands

```sh
python -m pip install "bensz-skill-identity==1.0.0"
bsi capabilities
python -c "from importlib.metadata import version; print(version('bensz-skill-identity'))"
```

Requires Python 3.11+; installation resolves PyYAML and cryptography. The capability query needs no keys or trust files and returns:

```json
{"assurance": "files_verified", "host_binding": false, "protocol": 1, "schema": "bensz-skill-identity/v1/capabilities", "strict_install": true}
```

The package version query should print `1.0.0`. Protocol version `1` in JSON and the example Skill's version are independent of the Python package version.

Once a signed release has arrived through a trusted channel and an explicit trust policy is ready, verify or install it. These commands maintain local security revision state:

```sh
bsi verify --release ./release --trust-store ./trust.json --state ./security-state.json
bsi install --release ./release --trust-store ./trust.json --target ./temporary-skills
```

An administrator explicitly maintains `trust.json`, including root public keys, root-signed security metadata, and the minimum revision accepted initially. Verification does not automatically trust roots shipped with a release. `--state` stores accepted revisions and observed releases. Preserve it: corrupt state is rejected, and deleting it cannot establish that revocation information is still fresh.

Installing this library installs no Skills. To manage Codex or Claude Code directories, use the repository installer's strict `--release` / `--trust-store` entry; see the [installer guide](https://github.com/huangwb8/skills/blob/main/skills/alpha/install-bensz-skills/README.md).

## Python API

```python
from pathlib import Path
from bensz_skill_identity import TrustPolicy, verify_persisted
from bensz_skill_identity.protocol import load_json

policy = TrustPolicy.from_dict(load_json(Path("trust.json")))
result = verify_persisted(
    Path("release"), policy, state_path=Path("security-state.json")
)
if result.decision == "allow":
    exact_requirement = result.as_requirement()
```

`verify_release(..., state=dict)` explicitly uses in-memory state; callers handle persistence and serialization. Production callers should use `verify_persisted` or installation transactions. Results expose `verification`, `decision`, `assurance`, and a stable `reason`, binding the request, policy, manifest, content, and security metadata digests. No API accepts a previous passing receipt to skip file checks.

`resolve_lock(requirements, candidates, policy, state=...)` resolves the signed dependency closure; `verify_lock` rereads content and policy; `resolve_name` rejects ambiguity in trusted name mappings supplied by the caller. Locks contain full IDs, exact versions, and digests, with no absolute paths. Policy changes require resolving the lock again.

`snapshot_release` saves a complete release in a separate directory without cleaning existing snapshots. Callers must recheck content and revocation at each controlled use boundary. Local processes with write access can alter these directories, so snapshots alone do not bind host loading. `verify_installation(target, name, policy)` rechecks installed files and retained signatures, persisting security revision state.

## Creating releases

Source identity lives in `config.yaml`:

```yaml
skill_info:
  name: sample
  version: "0.1.0"
  identity:
    publisher_id: ed25519-<SHA256 of raw root public-key bytes>
    skill_key: sample
```

Publishers establish an Ed25519 root key and a separate release key through trusted channels. The library does not create production identities or store private keys. Python callers pass in-memory `Ed25519PrivateKey` objects to `authorize`, `security_metadata`, and `build_release`. The CLI can read explicit PEM file paths supplied by a publisher; errors and output exclude key contents:

```sh
bsi authorize --private-key root.pem --release-public-key PUBLIC_HEX \
  --skill-key sample --expires-at UNIX_SECONDS --output authorization.json
bsi build --content ./sample --output ./release --private-key release.pem \
  --authorization authorization.json --history ./publisher-history.json
bsi security --private-key root.pem --revision 1 --issued-at UNIX_SECONDS \
  --expires-at LATER_UNIX_SECONDS --output security.json
```

Administrators place security metadata in the trust policy through a trusted channel. The tool does not check online freshness. Third-party content without `config.yaml` can use `--external-identity` to supply `{skill_id, version}` JSON; this identifies the distributor and does not authenticate upstream authors. External identity cannot override an existing configuration. Dependencies are exact requirements supplied through `--dependencies`, never inferred from prose.

Release building does not filter files automatically. Prepare a clean content directory first; hidden resources, READMEs, scripts, and sub-agents are all covered. Links, special files, path collisions, and limit violations are rejected. Version immutability applies to releases already observed locally and does not establish globally consistent history.

## Strict installation and recovery

Installed directories use the stable `skill_key`. A different identity with the same name cannot overwrite one. Evidence lives under the target root's `.bensz-skill-identity/`; installation records do not alter signed content. Strict installation rechecks candidates and staging, using same-filesystem backups, an installation lock, and a recovery journal. `bsi recover --target DIR` recovers unfinished transactions. Record submission is the commit point: interruption after it retains the new installation; interruption before it restores the old one. Recovery covers process termination, without a sudden-power-loss durability guarantee.

Compatible installers cannot update these managed directories through ordinary installation; they must use the strict entry. Historical clients and direct Shell operations are outside this guard's enforcement. Target platforms commit separately, without a cross-platform atomic transaction. Windows executable-bit and lock behavior have not been independently accepted; current execution evidence comes from macOS.

## Verification

From the repository root, create an isolated development environment and install the local package and test dependency:

```sh
python -m venv .bensz-api/identity-dev
.bensz-api/identity-dev/bin/python -m pip install ./packages/bensz-skill-identity pytest
PYTHONPYCACHEPREFIX="$PWD/.bensz-api/pycache" \
  .bensz-api/identity-dev/bin/python -m pytest packages/bensz-skill-identity/tests \
  --basetemp=tmp/skill-identity -o cache_dir=.bensz-api/.pytest_cache
```

CLI exit codes are 0 for success, 2 when an unknown publisher needs trust, 3 for verification or policy rejection, and 4 for I/O or invocation errors. Argument parsing follows argparse's exit code 2. JSON `reason` gives the specific cause; normal process completion or a valid signature alone does not establish policy approval.

The [validation record](https://github.com/huangwb8/skills/blob/main/docs/events/2026-11-14-skill-identity-validation.md) describes earlier API, installation recovery, tampering rejection, and independent wheel checks. It does not establish acceptance on every platform or host.

## License and support

Licensed under [MIT](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/LICENSE). See the [CHANGELOG](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/CHANGELOG.md) for releases and [repository Issues](https://github.com/huangwb8/skills/issues) for support.
