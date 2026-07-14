# convergence-shape (axis primitive)

## Purpose

The **stop signal** — the evidence pattern that says "converged." Weight 2.
Distinct from `halt-shape` (the reopen policy); this names what triggers the
stop. A composed prompt names both.

## Values

- `criteria-completion` — the final-verify proves the whole frozen inventory in
  one repo state (`criteria-met`).
- `homeostatic-checkpoint` — all homeostasis axes are currently balanced and no
  high-yield admissible intervention is available. This stops the invocation
  without claiming the frontier is complete. For frontier, quiescence includes
  a recorded vector-adequacy result
  (`primitives/frontier-vector-adequacy.md`): balanced axes with the frontier
  vector unscanned, a dimension-candidate probe or confirmation pending, or a
  newly admitted dimension requiring continuation is not checkpointable
  quiescence.
- `capstone-plus-closer` — the run completes a capstone deliverable, then a
  closer pass that reconciles / seals the queue (a chapter ends with a closer).
- `stone-reframe` — the artifact lands on the user's *reframed* target and
  further iteration has no positive yield (`stone-converged`; the user's call).
- `iteration-cap` — a hard budget / iteration ceiling. Cross-cutting; rarely a
  default.

`signal-starvation` is the cross-cutting **quiet-region sub-signal** (N green
iters with no new strong evidence) that forces the outer channel or an honest
halt under any convergence-shape.

## Detection heuristics

| Task phrasing | Value |
|---|---|
| finite verifier matrix | `criteria-completion` |
| known homeostasis axes balanced, vector adequacy resolved | `homeostatic-checkpoint` |
| chapters / episodes with closers | `capstone-plus-closer` |
| reframable creative target | `stone-reframe` |
| explicit budget / iteration cap | `iteration-cap` |

## Archetype defaults

| Archetype | Default |
|---|---|
| frontier | `homeostatic-checkpoint` |
| goal | `criteria-completion` |
| story | `capstone-plus-closer` |
| greenfield | `stone-reframe` |

Refinement over the source blueprint: `story`'s default is
`capstone-plus-closer` post-bodytxt — not a brand-new value; `frontier`'s
default is `homeostatic-checkpoint` — its self-pausing equilibrium, not
completion or `manual-only`.

## Composition rules

- `criteria-completion` requires `target-shape: finite-criteria`.
- Orthogonal to `halt-shape`; both appear in the composed prompt and in
  provenance when either diverges.
- **Contradiction** (ask the user): `homeostatic-checkpoint` with
  `target-shape: finite-criteria`.
