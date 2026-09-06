# State transition

## Verification target

Confirm that `subject.target_state` is an allowed successor of
`subject.current_state` in the Kernel's built-in lifecycle transition table. A
pass does not establish that Skill-specific entry conditions or invariants hold.

## Inputs and evidence

`subject.current_state` and `subject.target_state` are required for a meaningful
check. The verifier uses the Kernel's built-in `ALLOWED_TRANSITIONS`; it does not
consume context or separate evidence objects.

## Execution

The deterministic script looks up the current state in the lifecycle table and
tests direct membership of the target state. It does not resolve Skill-local
State Packs, aliases, wildcard policies, or persist a transition.

## Output and verdicts

It returns `pass` when the exact transition edge exists. Otherwise it returns
`fail`, records both states in `facts`, and emits an `illegal-transition` finding
for the requested target.

## Failure and boundaries

Missing or unknown states fail because no matching edge exists. Use the State
registry and transition machinery when canonicalization, entry conditions,
invariants, helper execution, evidence binding, or persistence is required.
