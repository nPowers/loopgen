# ADR 0002: loopgen composes loops, not one-shot builds — the loop-necessity gate

- **Status:** Accepted
- **Date:** 2026-06-22
- **Deciders:** provi, Claude (Opus 4.8)
- **Related:** ADR 0001 (loopgen does not own its runtime) — same "what loopgen is *not*" family

## Context

loopgen classifies a task to its nearest archetype (`frontier` / `goal` /
`story` / `greenfield`) and composes a loop prompt. But not every task that
*looks* like a target needs a loop. A `goal` task at **distance 0** —
`{finite-criteria, terminal, criteria-completion}` — with a *known* path and a
deterministic terminal oracle is structurally a **one-shot build**, not a loop:
its STATE would read `iteration: 1 → criteria-met`, the re-entry machinery never
firing. The `goal` *shape* (hit a fixed target, stop) **is** the *build* shape.
Composing loop scaffolding for it is wasted machinery and a miscommunication
about what the work needs.

## Decision

Before classification, run a **loop-necessity gate**. A loop is warranted only
when convergence is uncertain and the path is discovered through iteration — all
three must lean "loop":

1. **Re-entry expected** — iteration-1 success is *not* the expected case.
2. **Path discovered, not known** — the route is found by trial, not a known
   `read → transform → verify`.
3. **Oracle as gradient, not gate** — the oracle shapes successive attempts
   rather than gating one terminal completion.

If the path is known, the oracle gates one completion, and iteration-1 success is
expected → emit `{loop_warranted: false}` and **STOP**: do not classify, compose,
or emit loop artifacts. Hand the task to a build/implementation path. If
genuinely mixed (some criteria one-shot, some iterate-to-converge) or unclear →
ask the operator (loop vs build).

## Rationale

- Distance 0 to `goal` is **necessary but not sufficient** for a loop. The goal
  and build shapes coincide; only *iterate-to-converge* distinguishes a loop.
- `frontier` / `story` / `greenfield` are the genuinely-iterative archetypes;
  `goal` is the one most easily mistaken for a loop ("a build wearing loop
  clothes"). The gate exists primarily to catch that case.
- A compiler that emits scaffolding for work that converges in one pass produces
  dead machinery and trains the operator to ignore the contract.

## Consequences

Positive:

- loopgen can **decline** — it no longer always produces a loop; one-shot builds
  are routed away before any artifact is written.
- `loop_warranted` becomes a first-class classification output; the trap is
  recorded as an explicit anti-pattern guard in the skill.

Negative:

- A genuinely-mixed task needs operator judgment (an `AskUserQuestion`: loop vs
  build) rather than a fully mechanical verdict.
- A false "build" verdict denies a loop to a task that needed one; mitigated by
  the mixed-case escalation and the "all three must lean loop" conjunction.

## Revisit Triggers

- Classification gains a reliable automated signal to separate
  iterate-to-converge criteria from one-shot ones, allowing the manual mixed-case
  escalation to be automated.
- Evidence that the gate is rejecting tasks that genuinely benefited from a loop
  (false-build rate), which would argue for loosening the conjunction.

## References

- Merged: commit `296c074` — loop-necessity gate added to `SKILL.md` Phase 2,
  `loop_warranted` added to the classification output, and the
  "composing a loop for a one-shot build" anti-pattern.
