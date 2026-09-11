#!/usr/bin/env python3
"""Read-only hosting and loader checks; never execute target components."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

INDEX_FIELDS = {
    "directory", "id", "version", "classification", "tags", "aliases",
    "contract", "mode", "assurance_tier", "components",
}
IDENTITY_FIELDS = INDEX_FIELDS - {"directory", "contract"} | {"kind", "entrypoint"}
VERIFIER_HEADINGS = [
    "Verification target", "Inputs and evidence", "Execution",
    "Output and verdicts", "Failure and boundaries",
]


class CheckFailure(ValueError):
    pass


def require(condition: object, code: str) -> None:
    if not condition:
        raise CheckFailure(code)


def contained(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    require(resolved.is_relative_to(root), "path_outside_authorized_root")
    return resolved


def read_text(path: Path, root: Path) -> str:
    return contained(path, root).read_text(encoding="utf-8")


def frontmatter(text: str, yaml: object) -> dict:
    if not text.startswith("---\n"):
        return {}
    sections = text.split("\n---", 1)
    require(len(sections) == 2, "invalid_contract_frontmatter")
    metadata = yaml.safe_load(sections[0][4:]) or {}
    require(isinstance(metadata, dict), "invalid_contract_frontmatter")
    return metadata


def check_collection(root: Path, kind: str, yaml: object) -> list[dict]:
    from bensz_skill_kernel.contract_packs import ContractPack
    from bensz_skill_kernel.packs import load_pack_entries
    from bensz_skill_kernel.states import FilesystemStateRegistry
    from bensz_skill_kernel.verifiers import FilesystemVerifierRegistry

    collection = root / "references" / f"{kind}s"
    if not collection.exists() and not collection.is_symlink():
        return []
    contained(collection, root)
    require(collection.is_dir(), "collection_not_directory")
    for child in collection.rglob("*"):
        contained(child, collection.resolve())
    require((collection / "index.json").is_file(), "missing_collection_index")
    contract_name = "VERIFIER.md" if kind == "verifier" else "STATE.md"
    entries = load_pack_entries(collection, package_kind=kind, contract_name=contract_name)
    require(entries, "empty_collection")
    declared = {entry["directory"] for _, entry in entries}
    require(
        declared == {child.name for child in collection.iterdir() if child.is_dir()},
        "unindexed_collection_directory",
    )
    for contract, entry in entries:
        require(INDEX_FIELDS <= entry.keys(), "missing_index_fields")
        require(all(isinstance(entry[field], str) and entry[field] for field in ("id", "version", "classification", "mode", "assurance_tier")), "invalid_index_string")
        require(re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", entry["directory"]), "invalid_directory_name")
        require(entry["contract"] == contract_name, "nonstandard_contract_path")
        for field in ("tags", "aliases", "components"):
            require(isinstance(entry[field], list), "index_field_not_list")
        text = read_text(contract, root)
        metadata = frontmatter(text, yaml)
        require(not IDENTITY_FIELDS.intersection(metadata), "duplicated_contract_metadata")
        if kind == "verifier":
            require(re.findall(r"^## (.+)$", text, re.MULTILINE) == VERIFIER_HEADINGS, "verifier_heading_order")
        else:
            require(entry.get("kind") == "skill", "state_kind_not_skill")
            require({"entry_conditions", "invariants", "transitions"} <= metadata.keys(), "missing_state_graph_fields")
            require(all(isinstance(metadata[field], list) for field in ("entry_conditions", "invariants", "transitions")), "state_graph_field_not_list")
        for component in entry["components"]:
            require(isinstance(component, dict), "invalid_component")
            if component.get("type") == "script":
                endpoint = component.get("entrypoint")
                require(isinstance(endpoint, str) and endpoint, "missing_component_entrypoint")
                require(not Path(endpoint).is_absolute() and ".." not in Path(endpoint).parts and "\\" not in endpoint, "invalid_component_path")
        ContractPack.from_directory(contract.parent, package_kind=kind, contract_name=contract_name, entry=entry)
    registry_type = FilesystemVerifierRegistry if kind == "verifier" else FilesystemStateRegistry
    registry = registry_type(collection)
    for _, entry in entries:
        definition = registry.resolve(entry["id"])
        for alias in entry["aliases"]:
            require(registry.resolve(alias) == definition, "alias_resolution_mismatch")
    return [entry for _, entry in entries]


def check_runtime(root: Path, runtime: dict, verifiers: list[dict], states: list[dict]) -> None:
    from bensz_skill_kernel import __version__
    from bensz_skill_kernel.states import SkillStateDeclaration
    from bensz_skill_kernel.verifiers import SkillVerifierDeclaration

    require(runtime.get("kernel") == {"name": "bensz-skill-kernel", "version": __version__}, "runtime_kernel_mismatch")
    require("## 控制" in read_text(root / "SKILL.md", root), "missing_control_section")
    if states:
        require(runtime.get("state_roots") == ["references/states"], "nonstandard_state_roots")
    if states or any(key in runtime for key in ("states", "initial_state", "state_roots")):
        declaration = SkillStateDeclaration.from_skill_root(root)
        require(list(declaration.states) == runtime.get("states"), "noncanonical_runtime_states")
        require(declaration.initial_state == runtime.get("initial_state"), "noncanonical_initial_state")
        require(declaration.initial_state in declaration.states, "initial_state_not_declared")
        selected = set(declaration.states)
        require({entry["id"] for entry in states} <= selected, "unused_local_state")
        registry = declaration.registry()
        for entry in states:
            definition = registry.resolve(entry["id"])
            for target in (*definition.entry_conditions, *definition.transitions):
                require(target in selected, "state_graph_outside_selection")
                require(registry.resolve(target).id == target, "noncanonical_state_graph")
    if verifiers:
        require(runtime.get("verifier_roots", ["references/verifiers"]) == ["references/verifiers"], "nonstandard_verifier_roots")
    requirements = runtime.get("verifiers", [])
    declaration = SkillVerifierDeclaration.from_skill_root(root)
    normalized = declaration.verifier_requirements()
    require(all(item.get("id") == result["id"] and isinstance(item.get("required"), bool) for item, result in zip(requirements, normalized)), "noncanonical_verifier_requirement")
    require({entry["id"] for entry in verifiers} <= {item["id"] for item in normalized}, "unused_local_verifier")


def check(root: Path, yaml: object) -> dict:
    require(root.is_dir(), "missing_skill_root")
    require((root / "SKILL.md").is_file(), "missing_skill_document")
    config = yaml.safe_load(read_text(root / "config.yaml", root))
    require(isinstance(config, dict), "invalid_skill_config")
    runtime = config.get("runtime", {})
    require(isinstance(runtime, dict), "invalid_runtime")
    for kind in ("verifier", "state"):
        contract_name = "VERIFIER.md" if kind == "verifier" else "STATE.md"
        for path in root.rglob(contract_name):
            contained(path, root)
            parts = path.relative_to(root).parts
            require(len(parts) == 4 and parts[:2] == ("references", f"{kind}s"), "nonstandard_pack_layout")
    has_packs = any((root / "references" / collection).exists() or (root / "references" / collection).is_symlink() for collection in ("verifiers", "states"))
    has_runtime = any(key in runtime for key in ("states", "state_roots", "initial_state", "verifiers", "verifier_roots"))
    if not has_packs and not has_runtime:
        return {"status": "not_applicable", "execution": "unchecked", "reason": "no_components_declared"}
    verifiers = check_collection(root, "verifier", yaml)
    states = check_collection(root, "state", yaml)
    check_runtime(root, runtime, verifiers, states)
    return {"status": "pass", "execution": "unchecked", "scope": "hosting_and_loader_only", "verifiers": len(verifiers), "states": len(states)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path)
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 11):
            raise ImportError("Python 3.11 required")
        import yaml

        report = check(args.skill_root.expanduser().resolve(), yaml)
        code = 0
    except ImportError:
        report = {"status": "blocked", "execution": "unchecked", "reason": "python_yaml_or_kernel_unavailable"}
        code = 2
    except CheckFailure as error:
        report = {"status": "fail", "execution": "unchecked", "reason": str(error)}
        code = 1
    except Exception as error:
        report = {"status": "fail", "execution": "unchecked", "reason": "loader_or_input_rejected", "error_type": type(error).__name__}
        code = 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
