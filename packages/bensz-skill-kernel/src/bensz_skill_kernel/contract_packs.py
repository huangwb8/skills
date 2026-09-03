"""Domain-neutral Contract Pack execution and hand-off protocol.

The module executes deterministic helpers and prepares bound requests for
external agents or humans.  It deliberately does not interpret State
transitions or Verifier Gates; thin adapters in :mod:`states` and
:mod:`verifiers` own those domain semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .packs import resolve_entrypoint, run_stdio


CONTRACT_EXECUTION_PROTOCOL = "bensz-contract-execution-v1"
COMPONENT_RESULT_PROTOCOL = "bensz-contract-component-result-v1"
COMPONENT_TYPES = frozenset({"script", "agent", "human"})
COMPONENT_VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})
COMPONENT_STATUSES = frozenset({"completed", "pending", "unchecked", "error", "timed_out", "skipped"})
ASSURANCE_TIERS = frozenset({"deterministic", "mixed", "llm_judge", "human", "none"})
PACK_KINDS = frozenset({"state", "verifier"})
PACK_MODES = frozenset({"rule", "prompt", "hybrid", "human", "none"})
# Public component/contract modes. ``none`` is reserved for empty legacy packs.
EXECUTION_MODES = frozenset(PACK_MODES - {"none"})
# ``none`` is retained for legacy index entries that have no executable
# components; it is not a user-facing execution style for new contracts.
STATE_MODES = frozenset((*EXECUTION_MODES, "none"))
SIDE_EFFECT_POLICIES = frozenset({"none", "read_only", "local_write", "remote_write"})
_COMPONENT_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_SENSITIVE_KEYS = ("token", "secret", "password", "cookie", "api_key", "credential")


class ContractExecutionError(ValueError):
    """The execution plan or an external component result is invalid."""


class ContractBindingError(ContractExecutionError):
    """A component result is not bound to the current contract execution."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Redact credential-shaped fields before data enters a hand-off object."""
    safe: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if any(token in key.lower() for token in _SENSITIVE_KEYS):
            safe[key] = "[REDACTED]"
        elif isinstance(raw_value, Mapping):
            safe[key] = _safe_mapping(raw_value)
        elif isinstance(raw_value, (list, tuple)):
            safe[key] = [
                _safe_mapping(item) if isinstance(item, Mapping) else item
                for item in raw_value
            ]
        else:
            safe[key] = raw_value
    return safe


def _string_tuple(value: Any, *, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ContractExecutionError(f"{label} must be a string list")
    items = tuple(value)
    if any(not item for item in items):
        raise ContractExecutionError(f"{label} cannot contain empty values")
    return items


@dataclass(frozen=True)
class ContractComponent:
    """One ordered execution unit declared by a Contract Pack."""

    id: str
    type: str
    required: bool = True
    assurance: str = "deterministic"
    depends_on: tuple[str, ...] = ()
    entrypoint: str | None = None
    side_effects: str = "none"
    allowed_tools: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    timeout: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    component_hash: str = ""

    def __post_init__(self) -> None:
        if not _COMPONENT_ID_RE.fullmatch(self.id):
            raise ContractExecutionError(f"invalid component id: {self.id!r}")
        if self.type not in COMPONENT_TYPES:
            raise ContractExecutionError(f"unsupported component type: {self.type}")
        if not isinstance(self.required, bool):
            raise ContractExecutionError(f"component required must be boolean: {self.id}")
        if self.assurance not in ASSURANCE_TIERS:
            raise ContractExecutionError(f"unsupported component assurance: {self.assurance}")
        if self.type == "script" and not self.entrypoint:
            raise ContractExecutionError(f"script component requires entrypoint: {self.id}")
        if self.type != "script" and self.entrypoint:
            raise ContractExecutionError(f"only script components may declare entrypoint: {self.id}")
        if self.side_effects not in SIDE_EFFECT_POLICIES:
            raise ContractExecutionError(f"unsupported component side-effect policy: {self.side_effects}")
        if self.timeout is not None and (not isinstance(self.timeout, int) or self.timeout < 1):
            raise ContractExecutionError(f"component timeout must be a positive integer: {self.id}")
        if not self.component_hash:
            object.__setattr__(self, "component_hash", _hash(self.binding_dict()))

    def binding_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "required": self.required,
            "assurance": self.assurance,
            "depends_on": list(self.depends_on),
            "entrypoint": self.entrypoint,
            "side_effects": self.side_effects,
            "allowed_tools": list(self.allowed_tools),
            "evidence_refs": list(self.evidence_refs),
            "timeout": self.timeout,
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.binding_dict(), "component_hash": self.component_hash}

    def audit_dict(self) -> dict[str, Any]:
        """Return plan metadata without copying free-form component content."""
        value = self.binding_dict()
        metadata = value.pop("metadata")
        value["metadata_hash"] = _hash(metadata)
        return {**value, "component_hash": self.component_hash}


@dataclass(frozen=True)
class ContractPack:
    """Versioned executable description shared by State and Verifier packs."""

    root: Path
    package_kind: str
    pack_id: str
    version: str
    contract_ref: str
    instructions: str
    contract_hash: str
    components: tuple[ContractComponent, ...]
    mode: str
    assurance_tier: str
    plan_hash: str
    aliases: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    index_entry: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_directory(
        cls,
        root: str | Path,
        *,
        package_kind: str,
        contract_name: str,
        entry: Mapping[str, Any],
    ) -> "ContractPack":
        base = Path(root).expanduser().resolve()
        if package_kind not in PACK_KINDS:
            raise ContractExecutionError(f"unsupported Contract Pack kind: {package_kind}")
        target = (base / str(entry.get("contract", contract_name))).resolve()
        if base not in target.parents or not target.is_file():
            raise ContractExecutionError(f"contract must be a file inside its Pack directory: {target.name}")
        pack_id = str(entry.get("id", ""))
        version = str(entry.get("version", ""))
        if not pack_id or not version:
            raise ContractExecutionError("Contract Pack requires id and version")
        instructions = target.read_text(encoding="utf-8")
        contract_hash = _text_hash(instructions)
        raw_components = entry.get("components")
        diagnostics: list[str] = []
        if raw_components is None:
            legacy_entrypoint = entry.get("entrypoint")
            if legacy_entrypoint:
                raw_components = [{"id": "main", "type": "script", "entrypoint": legacy_entrypoint}]
            else:
                component_type = "human" if str(entry.get("mode", "")) == "human" else "agent"
                raw_components = [{"id": "contract-review", "type": component_type}]
            diagnostics.append("legacy Pack inferred execution components; declare components in index.json")
        if not isinstance(raw_components, list):
            raise ContractExecutionError("Contract Pack components must be a list")
        components: list[ContractComponent] = []
        seen: set[str] = set()
        for raw in raw_components:
            if not isinstance(raw, Mapping):
                raise ContractExecutionError("Contract Pack components must be objects")
            component_id = str(raw.get("id", ""))
            dependencies = _string_tuple(raw.get("depends_on", ()), label=f"component dependencies ({component_id})")
            if component_id in seen:
                raise ContractExecutionError(f"duplicate component id: {component_id}")
            missing = set(dependencies) - seen
            if missing:
                raise ContractExecutionError(
                    f"component dependencies must reference earlier components: {component_id}: {', '.join(sorted(missing))}"
                )
            component_type = str(raw.get("type", ""))
            entrypoint = raw.get("entrypoint")
            if component_type == "script":
                entrypoint = resolve_entrypoint(base, entrypoint, error_type=ContractExecutionError, label="component")
            reserved = {
                "id", "type", "required", "assurance", "depends_on", "entrypoint",
                "side_effects", "allowed_tools", "evidence_refs", "evidence", "timeout",
            }
            component = ContractComponent(
                id=component_id,
                type=component_type,
                required=raw.get("required", True),
                assurance=str(raw.get("assurance", "deterministic" if component_type == "script" else ("human" if component_type == "human" else "llm_judge"))),
                depends_on=dependencies,
                entrypoint=entrypoint,
                side_effects=str(raw.get("side_effects", "none")),
                allowed_tools=_string_tuple(raw.get("allowed_tools", ()), label=f"component allowed_tools ({component_id})"),
                evidence_refs=_string_tuple(raw.get("evidence_refs", raw.get("evidence", ())), label=f"component evidence_refs ({component_id})"),
                timeout=raw.get("timeout"),
                metadata={key: raw[key] for key in raw if key not in reserved},
            )
            components.append(component)
            seen.add(component_id)
        declared_entrypoint = entry.get("entrypoint")
        if declared_entrypoint:
            normalized_entrypoint = resolve_entrypoint(base, declared_entrypoint, error_type=ContractExecutionError, label="Pack")
            if not any(item.type == "script" and item.entrypoint == normalized_entrypoint for item in components):
                raise ContractExecutionError("Pack entrypoint must match a declared script component")
        component_types = {item.type for item in components}
        inferred_mode = (
            "hybrid"
            if len(component_types) > 1
            else {"script": "rule", "agent": "prompt", "human": "human"}.get(
                next(iter(component_types), ""), "none"
            )
        )
        mode = str(entry.get("mode", inferred_mode))
        assurance = str(entry.get("assurance_tier", "mixed" if len({item.assurance for item in components}) > 1 else (components[0].assurance if components else "none")))
        if mode not in PACK_MODES:
            raise ContractExecutionError(f"unsupported Pack mode: {mode}")
        if assurance not in ASSURANCE_TIERS:
            raise ContractExecutionError(f"unsupported Pack assurance tier: {assurance}")
        if package_kind == "verifier" and not components:
            raise ContractExecutionError("Verifier Contract Pack requires at least one component")
        plan = {
            "protocol": CONTRACT_EXECUTION_PROTOCOL,
            "package_kind": package_kind,
            "pack_id": pack_id,
            "version": version,
            "contract_hash": contract_hash,
            "mode": mode,
            "assurance_tier": assurance,
            "components": [item.audit_dict() for item in components],
        }
        return cls(
            root=base,
            package_kind=package_kind,
            pack_id=pack_id,
            version=version,
            contract_ref=str(target.relative_to(base)),
            instructions=instructions,
            contract_hash=contract_hash,
            components=tuple(components),
            mode=mode,
            assurance_tier=assurance,
            plan_hash=_hash(plan),
            aliases=_string_tuple(entry.get("aliases", ()), label="aliases"),
            diagnostics=tuple(diagnostics),
            index_entry=dict(entry),
        )

    def component(self, component_id: str) -> ContractComponent:
        for component in self.components:
            if component.id == component_id:
                return component
        raise KeyError(component_id)

    def audit_dict(self) -> dict[str, Any]:
        return {
            "protocol": CONTRACT_EXECUTION_PROTOCOL,
            "package_kind": self.package_kind,
            "pack_id": self.pack_id,
            "version": self.version,
            "contract_ref": self.contract_ref,
            "contract_hash": self.contract_hash,
            "plan_hash": self.plan_hash,
            "mode": self.mode,
            "assurance_tier": self.assurance_tier,
            "components": [item.audit_dict() for item in self.components],
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True)
class ComponentHandoff:
    """Ephemeral request for an external agent or human component."""

    pack_id: str
    pack_version: str
    package_kind: str
    component_id: str
    component_type: str
    contract_ref: str
    contract_hash: str
    component_hash: str
    plan_hash: str
    run_id: str
    attempt_id: str
    subject: Mapping[str, Any]
    context: Mapping[str, Any]
    evidence: tuple[Mapping[str, Any], ...]
    upstream_facts: Mapping[str, Mapping[str, Any]]
    instructions: str
    output_schema: Mapping[str, Any]
    allowed_tools: tuple[str, ...] = ()
    side_effects: str = "none"
    protocol: str = CONTRACT_EXECUTION_PROTOCOL
    handoff_hash: str = ""

    def __post_init__(self) -> None:
        if not self.handoff_hash:
            object.__setattr__(self, "handoff_hash", _hash(self._binding_dict()))

    def _binding_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "package_kind": self.package_kind,
            "component_id": self.component_id,
            "component_type": self.component_type,
            "contract_ref": self.contract_ref,
            "contract_hash": self.contract_hash,
            "component_hash": self.component_hash,
            "plan_hash": self.plan_hash,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "subject_hash": _hash(self.subject),
            "context_hash": _hash(self.context),
            "evidence_hash": _hash(self.evidence),
            "upstream_fact_hash": _hash(self.upstream_facts),
            "instructions_hash": _text_hash(self.instructions),
            "output_schema_hash": _hash(self.output_schema),
            "allowed_tools": list(self.allowed_tools),
            "side_effects": self.side_effects,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return the complete, ephemeral hand-off for an external executor."""
        return {
            **self.to_audit_dict(),
            "subject": dict(self.subject),
            "context": dict(self.context),
            "evidence": [dict(item) for item in self.evidence],
            "upstream_facts": {key: dict(value) for key, value in self.upstream_facts.items()},
            "instructions": self.instructions,
            "output_schema": dict(self.output_schema),
        }

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            **self._binding_dict(),
            "handoff_hash": self.handoff_hash,
            "evidence_refs": [str(item.get("ref")) for item in self.evidence],
        }

    def bind_result(
        self,
        *,
        verdict: str,
        execution_status: str = "completed",
        findings: Iterable[Mapping[str, Any]] = (),
        facts: Mapping[str, Any] | None = None,
        evidence_refs: Iterable[str] = (),
        executor: Mapping[str, Any],
        uncertainty_reason: str | None = None,
    ) -> dict[str, Any]:
        return {
            "protocol": COMPONENT_RESULT_PROTOCOL,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "package_kind": self.package_kind,
            "component_id": self.component_id,
            "component_type": self.component_type,
            "contract_hash": self.contract_hash,
            "component_hash": self.component_hash,
            "plan_hash": self.plan_hash,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "handoff_hash": self.handoff_hash,
            "execution_status": execution_status,
            "verdict": verdict,
            "findings": list(findings),
            "facts": dict(facts or {}),
            "evidence_refs": list(evidence_refs),
            "executor": dict(executor),
            "uncertainty_reason": uncertainty_reason,
        }


@dataclass(frozen=True)
class ComponentResult:
    pack_id: str
    pack_version: str
    package_kind: str
    component_id: str
    component_type: str
    execution_status: str
    verdict: str
    contract_hash: str
    component_hash: str
    plan_hash: str
    run_id: str
    attempt_id: str
    required: bool = True
    assurance: str = "deterministic"
    findings: tuple[Mapping[str, Any], ...] = ()
    facts: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    executor: Mapping[str, Any] = field(default_factory=dict)
    uncertainty_reason: str | None = None
    handoff_hash: str | None = None
    protocol: str = COMPONENT_RESULT_PROTOCOL

    def __post_init__(self) -> None:
        if self.execution_status not in COMPONENT_STATUSES:
            raise ContractExecutionError(f"invalid component execution status: {self.execution_status}")
        if self.verdict not in COMPONENT_VERDICTS:
            raise ContractExecutionError(f"invalid component verdict: {self.verdict}")
        if self.execution_status != "completed" and self.verdict == "pass":
            raise ContractExecutionError("non-completed component cannot pass")
        if self.verdict == "timed_out" and self.execution_status != "timed_out":
            raise ContractExecutionError("timed_out verdict requires timed_out execution")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContractExecutionReport:
    pack_id: str
    pack_version: str
    package_kind: str
    contract_hash: str
    plan_hash: str
    run_id: str
    attempt_id: str
    execution_plan: Mapping[str, Any]
    decision: str
    results: tuple[ComponentResult, ...]
    handoffs: tuple[ComponentHandoff, ...] = ()
    unresolved: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    protocol: str = CONTRACT_EXECUTION_PROTOCOL

    def to_dict(self, *, include_handoffs: bool = False) -> dict[str, Any]:
        value = {
            "protocol": self.protocol,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "package_kind": self.package_kind,
            "contract_hash": self.contract_hash,
            "plan_hash": self.plan_hash,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "execution_plan": dict(self.execution_plan),
            "decision": self.decision,
            "results": [item.to_dict() for item in self.results],
            "unresolved": list(self.unresolved),
            "diagnostics": list(self.diagnostics),
        }
        if include_handoffs:
            value["handoffs"] = [item.to_audit_dict() for item in self.handoffs]
        return value


class ContractPackExecutor:
    """Execute scripts and validate external component submissions in order."""

    def execute(
        self,
        pack: ContractPack,
        *,
        request: Mapping[str, Any],
        submissions: Iterable[Mapping[str, Any]] = (),
        run_id: str = "run",
        attempt_id: str = "default",
        timeout: int = 30,
        allow_side_effects: bool = False,
    ) -> ContractExecutionReport:
        if not isinstance(request, Mapping):
            raise ContractExecutionError("Contract Pack request must be an object")
        submission_map: dict[str, Mapping[str, Any]] = {}
        for submission in submissions:
            if not isinstance(submission, Mapping):
                raise ContractBindingError("component submission must be an object")
            component_id = str(submission.get("component_id", ""))
            if component_id in submission_map:
                raise ContractBindingError(f"duplicate component submission: {component_id}")
            submission_map[component_id] = submission
        component_by_id = {item.id: item for item in pack.components}
        unknown = set(submission_map) - set(component_by_id)
        if unknown:
            raise ContractBindingError("unknown component submission: " + ", ".join(sorted(unknown)))
        submitted_scripts = tuple(
            component_id
            for component_id in submission_map
            if component_by_id[component_id].type == "script"
        )
        if submitted_scripts:
            raise ContractBindingError(
                "script component results must be produced by the local executor: "
                + ", ".join(submitted_scripts)
            )

        subject = request.get("subject", {})
        context = request.get("context", {})
        evidence = request.get("evidence", ())
        if not isinstance(subject, Mapping) or not isinstance(context, Mapping):
            raise ContractExecutionError("subject and context must be objects")
        if not isinstance(evidence, (list, tuple)) or not all(isinstance(item, Mapping) for item in evidence):
            raise ContractExecutionError("evidence must be a list of objects")
        safe_evidence = tuple(
            {
                "ref": str(item.get("ref", "")),
                "summary": item.get("summary"),
                "content_hash": item.get("content_hash"),
                "source_type": item.get("source_type"),
            }
            for item in evidence
            if item.get("ref")
        )
        evidence_refs = {str(item["ref"]) for item in safe_evidence}
        results: list[ComponentResult] = []
        handoffs: list[ComponentHandoff] = []
        by_id: dict[str, ComponentResult] = {}

        for component in pack.components:
            dependencies = [by_id[item] for item in component.depends_on]
            dependency_pending = [item.component_id for item in dependencies if item.execution_status != "completed"]
            missing_evidence = tuple(ref for ref in component.evidence_refs if ref not in evidence_refs)
            submitted = component.id in submission_map
            if missing_evidence:
                if submitted:
                    raise ContractBindingError(f"submission evidence mismatch for component {component.id}")
                result = self._bound_result(
                    pack,
                    component,
                    run_id,
                    attempt_id,
                    execution_status="unchecked",
                    verdict="unchecked",
                    evidence_refs=tuple(sorted(evidence_refs)),
                    uncertainty_reason="missing required evidence: " + ", ".join(missing_evidence),
                )
            elif dependency_pending:
                if submitted:
                    raise ContractBindingError(f"submission order violation for component {component.id}")
                result = self._bound_result(
                    pack,
                    component,
                    run_id,
                    attempt_id,
                    execution_status="skipped",
                    verdict="skipped",
                    uncertainty_reason="dependency incomplete: " + ", ".join(dependency_pending),
                )
            elif component.type == "script":
                if component.side_effects not in {"none", "read_only"} and not allow_side_effects:
                    result = self._bound_result(
                        pack,
                        component,
                        run_id,
                        attempt_id,
                        execution_status="error",
                        verdict="error",
                        uncertainty_reason="component side effects require explicit authorization",
                    )
                else:
                    result = self._run_script(pack, component, request, by_id, run_id, attempt_id, timeout, evidence_refs, allow_side_effects)
            else:
                handoff = self._handoff(
                    pack,
                    component,
                    subject,
                    context,
                    safe_evidence,
                    by_id,
                    run_id,
                    attempt_id,
                )
                submission = submission_map.get(component.id)
                if submission is None:
                    handoffs.append(handoff)
                    result = self._bound_result(
                        pack,
                        component,
                        run_id,
                        attempt_id,
                        execution_status="pending",
                        verdict="unchecked",
                        evidence_refs=tuple(str(item["ref"]) for item in safe_evidence),
                        uncertainty_reason=f"{component.type} result pending",
                    )
                else:
                    result = self._validate_submission(pack, component, handoff, submission, run_id, attempt_id, evidence_refs)
            results.append(result)
            by_id[component.id] = result

        decision, unresolved = self._merge(tuple(results))
        return ContractExecutionReport(
            pack_id=pack.pack_id,
            pack_version=pack.version,
            package_kind=pack.package_kind,
            contract_hash=pack.contract_hash,
            plan_hash=pack.plan_hash,
            run_id=run_id,
            attempt_id=attempt_id,
            execution_plan=pack.audit_dict(),
            decision=decision,
            results=tuple(results),
            handoffs=tuple(handoffs),
            unresolved=unresolved,
            diagnostics=pack.diagnostics,
        )

    def _run_script(
        self,
        pack: ContractPack,
        component: ContractComponent,
        request: Mapping[str, Any],
        previous: Mapping[str, ComponentResult],
        run_id: str,
        attempt_id: str,
        timeout: int,
        known_evidence_refs: set[str],
        allow_side_effects: bool,
    ) -> ComponentResult:
        payload = dict(request)
        payload["_contract_execution"] = {
            **pack.audit_dict(),
            "component": component.to_dict(),
            "run_id": run_id,
            "attempt_id": attempt_id,
            "upstream_facts": {key: dict(value.facts) for key, value in previous.items()},
        }
        execution = run_stdio(
            pack.root,
            str(component.entrypoint),
            payload,
            timeout=component.timeout or timeout,
            allow_side_effects=allow_side_effects and component.side_effects not in {"none", "read_only"},
        )
        if execution.status == "timed_out":
            return self._bound_result(pack, component, run_id, attempt_id, execution_status="timed_out", verdict="timed_out", uncertainty_reason=execution.detail)
        if execution.status != "completed":
            return self._bound_result(pack, component, run_id, attempt_id, execution_status="error", verdict="error", uncertainty_reason=execution.detail)
        if not isinstance(execution.value, Mapping):
            return self._bound_result(pack, component, run_id, attempt_id, execution_status="error", verdict="error", uncertainty_reason="component output must be a JSON object")
        raw = execution.value
        verdict = str(raw.get("verdict", "unchecked"))
        status = str(raw.get("execution_status", "completed"))
        try:
            raw_refs = raw.get("evidence_refs", ())
            raw_findings = raw.get("findings", ())
            raw_facts = raw.get("facts", {})
            if (
                not isinstance(raw_refs, (list, tuple))
                or not all(isinstance(item, str) for item in raw_refs)
                or not isinstance(raw_findings, (list, tuple))
                or not all(isinstance(item, Mapping) for item in raw_findings)
                or not isinstance(raw_facts, Mapping)
            ):
                raise ValueError("invalid component output collections")
            refs = tuple(raw_refs)
            unknown_refs = set(refs) - known_evidence_refs
            if unknown_refs:
                raise ValueError("unknown evidence reference")
            return self._bound_result(
                pack,
                component,
                run_id,
                attempt_id,
                execution_status=status,
                verdict=verdict,
                findings=tuple(dict(item) for item in raw_findings),
                facts=dict(raw_facts),
                evidence_refs=refs,
                executor={"type": "script", "id": component.entrypoint},
                uncertainty_reason=raw.get("uncertainty_reason"),
            )
        except (TypeError, ValueError):
            return self._bound_result(pack, component, run_id, attempt_id, execution_status="error", verdict="error", uncertainty_reason="invalid component output")

    def _handoff(
        self,
        pack: ContractPack,
        component: ContractComponent,
        subject: Mapping[str, Any],
        context: Mapping[str, Any],
        evidence: tuple[Mapping[str, Any], ...],
        previous: Mapping[str, ComponentResult],
        run_id: str,
        attempt_id: str,
    ) -> ComponentHandoff:
        return ComponentHandoff(
            pack_id=pack.pack_id,
            pack_version=pack.version,
            package_kind=pack.package_kind,
            component_id=component.id,
            component_type=component.type,
            contract_ref=pack.contract_ref,
            contract_hash=pack.contract_hash,
            component_hash=component.component_hash,
            plan_hash=pack.plan_hash,
            run_id=run_id,
            attempt_id=attempt_id,
            subject=_safe_mapping(subject),
            context=_safe_mapping(context),
            evidence=evidence,
            upstream_facts={key: dict(value.facts) for key, value in previous.items()},
            instructions=pack.instructions,
            output_schema={
                "protocol": COMPONENT_RESULT_PROTOCOL,
                "required": ["component_id", "component_type", "execution_status", "verdict", "evidence_refs", "executor"],
                "verdicts": sorted(COMPONENT_VERDICTS),
                "uncertainty": "Use uncertain/unchecked; never infer pass from missing evidence.",
            },
            allowed_tools=component.allowed_tools,
            side_effects=component.side_effects,
        )

    def _validate_submission(
        self,
        pack: ContractPack,
        component: ContractComponent,
        handoff: ComponentHandoff,
        raw: Mapping[str, Any],
        run_id: str,
        attempt_id: str,
        evidence_refs: set[str],
    ) -> ComponentResult:
        if raw.get("protocol") != COMPONENT_RESULT_PROTOCOL:
            raise ContractBindingError(f"unsupported component result protocol: {component.id}")
        expected = {
            "pack_id": pack.pack_id,
            "pack_version": pack.version,
            "package_kind": pack.package_kind,
            "component_id": component.id,
            "component_type": component.type,
            "component_hash": component.component_hash,
        }
        for key, value in expected.items():
            if raw.get(key) != value:
                raise ContractBindingError(f"{key.replace('_', ' ')} mismatch for component {component.id}")
        if raw.get("contract_hash") != pack.contract_hash:
            raise ContractBindingError(f"contract hash mismatch for component {component.id}")
        if raw.get("plan_hash") != pack.plan_hash:
            raise ContractBindingError(f"plan hash mismatch for component {component.id}")
        if raw.get("run_id") != run_id or raw.get("attempt_id") != attempt_id:
            raise ContractBindingError(f"run identity mismatch for component {component.id}")
        if raw.get("handoff_hash") != handoff.handoff_hash:
            raise ContractBindingError(f"handoff binding mismatch for component {component.id}")
        executor = raw.get("executor")
        if not isinstance(executor, Mapping) or executor.get("type") != component.type or not executor.get("id"):
            raise ContractBindingError(f"executor identity mismatch for component {component.id}")
        if component.type == "agent" and not executor.get("model"):
            raise ContractBindingError(f"agent model identity required: {component.id}")
        if component.type == "human" and not executor.get("confirmed_at"):
            raise ContractBindingError(f"human confirmation timestamp required: {component.id}")
        raw_refs = raw.get("evidence_refs", ())
        if not isinstance(raw_refs, (list, tuple)) or not all(isinstance(item, str) for item in raw_refs):
            raise ContractBindingError(f"evidence refs must be a string list: {component.id}")
        refs = tuple(raw_refs)
        unknown_refs = set(refs) - evidence_refs
        if unknown_refs:
            raise ContractBindingError("unknown evidence reference: " + ", ".join(sorted(unknown_refs)))
        findings = raw.get("findings", ())
        facts = raw.get("facts", {})
        if not isinstance(findings, (list, tuple)) or not all(isinstance(item, Mapping) for item in findings) or not isinstance(facts, Mapping):
            raise ContractBindingError(f"invalid result facts/findings for component {component.id}")
        return self._bound_result(
            pack,
            component,
            run_id,
            attempt_id,
            execution_status=str(raw.get("execution_status", "completed")),
            verdict=str(raw.get("verdict", "unchecked")),
            findings=tuple(dict(item) for item in findings),
            facts=_safe_mapping(facts),
            evidence_refs=refs,
            executor=_safe_mapping(executor),
            uncertainty_reason=str(raw["uncertainty_reason"]) if raw.get("uncertainty_reason") else None,
            handoff_hash=handoff.handoff_hash,
        )

    @staticmethod
    def _bound_result(
        pack: ContractPack,
        component: ContractComponent,
        run_id: str,
        attempt_id: str,
        *,
        execution_status: str,
        verdict: str,
        findings: tuple[Mapping[str, Any], ...] = (),
        facts: Mapping[str, Any] | None = None,
        evidence_refs: tuple[str, ...] = (),
        executor: Mapping[str, Any] | None = None,
        uncertainty_reason: str | None = None,
        handoff_hash: str | None = None,
    ) -> ComponentResult:
        return ComponentResult(
            pack_id=pack.pack_id,
            pack_version=pack.version,
            package_kind=pack.package_kind,
            component_id=component.id,
            component_type=component.type,
            execution_status=execution_status,
            verdict=verdict,
            contract_hash=pack.contract_hash,
            component_hash=component.component_hash,
            plan_hash=pack.plan_hash,
            run_id=run_id,
            attempt_id=attempt_id,
            required=component.required,
            assurance=component.assurance,
            findings=findings,
            facts=dict(facts or {}),
            evidence_refs=evidence_refs,
            executor=dict(executor or {}),
            uncertainty_reason=uncertainty_reason,
            handoff_hash=handoff_hash,
        )

    @staticmethod
    def _merge(results: tuple[ComponentResult, ...]) -> tuple[str, tuple[str, ...]]:
        required = tuple(item for item in results if item.required)
        failures = tuple(item.component_id for item in required if item.verdict == "fail")
        if failures:
            return "reject", failures
        uncertain = tuple(item.component_id for item in required if item.verdict in {"uncertain", "error", "timed_out"})
        skipped = tuple(item.component_id for item in required if item.verdict == "skipped")
        pending = tuple(item.component_id for item in required if item.verdict == "unchecked")
        if uncertain:
            return "manual_review", tuple(dict.fromkeys((*uncertain, *pending, *skipped)))
        if pending or skipped:
            return "wait", tuple(dict.fromkeys((*pending, *skipped)))
        optional_failures = tuple(item.component_id for item in results if not item.required and item.verdict != "pass")
        if optional_failures:
            return "completed_with_warnings", optional_failures
        return "completed", ()
