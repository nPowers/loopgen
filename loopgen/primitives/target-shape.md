# target-shape (axis primitive)

## Purpose

How the loop's optimization target is defined. The single most load-bearing
axis (weight 3): it decides whether the loop is terminal or open-ended, and it
gates the forbidden-divergence and contradiction checks.

## Values

- `finite-criteria` — a frozen, machine-checkable list with a terminal pass
  line. "Done" is a known set of things that must be true at once.
- `frontier-expanding` — a quality frontier that moves (better / more robust /
  higher score) with no terminal pass line.
- `promise-discovery` — user-facing product promises discovered and verified
  one at a time, before a finite implementation target exists.
- `discovery-reframing` — the target itself is undefined and phase-shifts as
  intent reveals ("X-adjacent, I'll know it when I see it").

## Detection heuristics

| Task phrasing | Value |
|---|---|
| "make these criteria pass", "implement this spec", "close this checklist" | `finite-criteria` |
| "make it better / faster / more robust", "raise the score", no pass line | `frontier-expanding` |
| "verify the product does what it promises", "which stories are real" | `promise-discovery` |
| "build me something X-adjacent", "discover the right shape" | `discovery-reframing` |

## Archetype defaults

| Archetype | Default |
|---|---|
| frontier | `frontier-expanding` |
| goal | `finite-criteria` |
| story | `promise-discovery` |
| greenfield | `discovery-reframing` |

## Composition rules

- `finite-criteria` forces `halt-shape: terminal`, `convergence-shape:
  criteria-completion`, and `artifact-shape: acceptance-inventory`.
- `finite-criteria` is **forbidden** for `frontier` and `greenfield` — a fixed
  finite target is goal-shaped; route to `goal`.
- `frontier-expanding` and `discovery-reframing` are **forbidden** for `goal` —
  a moving target with no pass line is not goal-shaped.
- **Contradiction** (classification error → ask the user, no silent default):
  `finite-criteria` with `halt-shape: equilibrium`/`manual-gated`, or with
  `convergence-shape: homeostatic-checkpoint`.

## Underspecified targets (the preintent read)

A phrasing can classify cleanly yet name only the *shape* of the target, not its
*content*. "Improve the codebase" extracts `frontier-expanding` decisively — it
is "make it better", no pass line — but names no **dimension** to improve along
(perf? coverage? type-safety? complexity? dead-code?). Likewise "build me
something X-adjacent" extracts `discovery-reframing` but may leave the adjacency
unpinned. These are the two moving-target values, and both routinely arrive as a
*preintent*: a real target the verb only gestures at.

The read must record both halves — `{value, dimension|adjacency: <named |
UNDEFINED>}` — and an UNDEFINED dimension is a **target derivation gap** (the
frontier-vector / target-adjacency frontload item), never a silent default.
The frontload-bound dimensions are the *seed* only: once the loop bootstraps,
the live vector is runtime state whose growth is governed by the earned
dimension lifecycle (`primitives/frontier-vector-adequacy.md`) — a new
dimension is admitted by evidence at runtime, never appended by derivation
prose.
Classification succeeding is not the same as the loop being runnable: a clean
match — even an exact, distance-0 one — to `frontier`/`greenfield` yields a
**`frontier_candidate`, `runnable: false`**, not a launchable loop. A vague
frontier binds *four* slots before it can fire, not one: the **dimension** (which
quality axis — one primary, or an explicit scorecard if it is genuinely
multi-axis), the **stop rule** (no pass line ≠ no halt: equilibrium / plateau /
budget still bounds it), the **scope**, and the **evidence signal**. Each unbound
slot is an open frontload gap — never a silent default. A loop launched with no
dimension self-halts on iteration 1 (`signal-starvation`); one launched with a
dimension but no stop rule never halts at all.
