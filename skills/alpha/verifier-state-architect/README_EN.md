# verifier-state-architect — Design and Implement Verifier / State

[中文](README.md)

Give it a target Agent Skill: it understands the workflow, selects useful verifiers and states, changes the source, and verifies integration. The plan is saved first for AI execution and later human review; **implementation does not wait for plan approval**.

## Quick Start

In a host that can invoke this Skill, specify the target **development source** directory:

```text
请使用 verifier-state-architect，为 skills/beta/my-skill 设计并落地 verifier 和 state。
先判断哪些组件确实有用，计划保存后直接执行；遵循托管规范，验证实际接入并保留事后审查证据。
```

Expected result: necessary changes to target components, configuration, and invocation flow, accompanied by a plan, verification evidence, and limitations. If deletion-impact analysis shows no useful components, it delivers a justified no-integration conclusion instead.

Mechanical checks require Python 3.11+, PyYAML, and `bensz-skill-kernel` matching the target declaration. Design can proceed first, but missing dependencies or a host never count as successful execution.

## Modes

| Intent | Behavior |
| --- | --- |
| Delegate target design, implementation, integration, or simplification | Default `implement`: plan → local implementation → verification → delivery |
| Explicitly request a plan only / no source changes | `plan-only`: save the design without changing target source |
| Read-only review of existing components | `review-only`: report findings, evidence, and recommendations |
| Implement an existing plan | Check current source against the plan, update material deviations, and continue |

```text
请使用 verifier-state-architect，只读审查 skills/alpha/reporting 的 verifier/state，不修改源码。
逐项做删除影响测试，说明 Kernel 复用、Gate、迁移和恢复风险。
```

```text
请使用 verifier-state-architect，按 docs/plans/my-skill-verifier-state-design.md 落实目标 Skill。
核对当前源码后直接执行，不等待计划审批；未完成验证的部分明确标记。
```

## Design Principles

- Component count is not a goal: zero components, Verifier-only, and State-only are valid.
- Deterministic scripts check structure, paths, protocols, and facts; AI judges domain semantics against contracts and evidence.
- Inventory direct, combined, and adapted Kernel reuse before designing dedicated components; record reuse and cross-domain extraction conclusions separately.
- Keep domain rules out of the Kernel; dedicated Packs ship with the target Skill.
- When BSK manages both State and required Verifiers, deliver one Skill-owned command that handles action mapping, State reads, request preparation, required Verifiers, Gate, allowed transition, and strict response checks; any failure stops the flow.
- Unlike general Skill development through `skill-creator`, this Skill specializes in Verifier/State design and integration; Kernel development requires separate authorization.

## Deliverables and Layout

| Content | Location |
| --- | --- |
| Retained execution plan | Project `docs/plans/{skill-name}-verifier-state-design.md`, or a specified location |
| Dedicated Verifier | Target `references/verifiers/index.json` and each child directory's `VERIFIER.md` |
| Dedicated State | Target `references/states/index.json` and each child directory's `STATE.md` |
| Declarations and invocation points | Target `config.yaml`, `SKILL.md`, and necessary host/script entry points |
| Evidence, logs, and reconciliation | The same task's `.bensz-api/task-…/verifier-state-architect/` boundary |

The plan is a workflow step, no longer the default final deliverable. Existing files belonging to other work are not overwritten; delivery maps plan items to changes, checks, and results. See the [hosting specification](references/skill-pack-hosting.md) for layout, fields, contracts, and loading, and the [implementation reference](references/implementation.md) for operational steps. This Skill maintains the single authoritative hosting specification. Current BSK versions support Skill-owned Verifier collections through `runtime.verifier_roots` and explicit CLI sources; they never scan global directories automatically.

If the target uses both State and required Verifiers, it must also follow the [BSK orchestration entry contract](references/bsk-orchestration.md), declare the Agent's single normal command path in `runtime.orchestration`, and provide real success and fail-closed evidence. Static checks prove only that the declaration and path exist.

## Configuration and Checks

See [config.yaml](config.yaml) for defaults, plan paths, and safety settings, and [SKILL.md](SKILL.md) for the execution contract. Explicit read-only requests override defaults. `README.md` and `README_EN.md` describe the same usage contract.

```bash
python3 /path/to/verifier-state-architect/scripts/check_integration.py /path/to/target-skill
```

The read-only script checks standard layout, index/contract responsibilities, State graph fields, canonical/alias resolution, declarations, and actual Kernel loading. In combined scenarios it also checks the entry in the real `## 控制` section, domain-State mappings, and static transition edges, and rejects orphan orchestration declarations. It does not execute target scripts or models, write target files, access the network, or modify installed copies.

The JSON report's `execution: unchecked` means this check **does not prove business execution**. Exit code 0 means structural success or no applicable components, 1 means nonconformance, and 2 means unavailable dependencies. Actual components, missing-evidence failures, Gate behavior, state transitions, and applicable replay still require verification. Kernel compatibility with a legacy layout does not establish compliance with the new hosting convention.

## Boundaries and Recovery

- Implement only in authorized development source; no automatic publishing, remote writes, Kernel changes, or installed-copy modification.
- Preserve existing user changes; report conflicts, missing dependencies, or missing host responses as blocked, never as a fabricated pass.
- Automatic implementation does not remove necessary human business judgments or bypass required evidence and permission boundaries.
- Save the plan before implementation and retain failure evidence; rollback only this task's changes, never clear user work.
- Do not retain keys, tokens, Cookie data, private instructions, or unnecessary raw input; keep intermediate files out of release assets.

## WHICHMODEL: Model Selection

Retain task-based selection: use a high-reasoning model with adequate context for complex workflows, deletion-impact analysis, architectural choices, and cross-file implementation; capable general models can organize plans and documentation; prefer deterministic scripts for fields, paths, and loading. Do not pin model names or treat switching models as grounds to convert uncertain/unchecked into a pass.

## FAQ

**Does “design” stop at the plan?** Delegating target design to this Skill continues into implementation by default. For a proposal only, explicitly request a plan without source changes.

**Must both component types be generated?** No. Establish their value first; never add a placeholder State merely to satisfy a format or loader.

**Do generated files prove successful integration?** No. Distinguish structural loading, actual component execution, and semantic verification. Without execution evidence, state the limitation.

**Can it work in other projects?** It can design for different domains, and its installed copy includes the reference and checking script. Implementation still requires authorized source, a compatible Kernel, and a real host; unknown environments may need adaptation.

**How can I audit it later?** Follow the plan and task reconciliation to changed files, decision reasons, verification commands, and unfinished items. See [CHANGELOG.md](CHANGELOG.md) for change history.
