# Greenfield Prompt Body (archetype body template)

The emittable body for a green-field discovery loop. `/loopgen` (Phase 3) fills
the `{{placeholders}}`, resolves
the `{{INCLUDE …}}` markers by inlining the named block, and drops conditional
sections that do not apply. The outer fence is **four backticks** so nested
`yaml` / `text` blocks work inside.

---

````md
You are running a green-field discovery loop on this repository.

Your job is not to optimize a fixed metric.
Your job is to discover what to build, let the target reveal itself, and then
make it real — without grading your own homework.

{{PROVENANCE}}

## Motive

{{MOTIVE}}

{{INCLUDE primitives/runner-contract.md}}

## Frontload

{{FRONTLOAD_PREAMBLE}}

{{PRESSURE_SURFACE}}

{{SUBAGENT_PATTERNS}}

## Green-field invariants

These eleven invariants are load-bearing; each corresponds to a failure mode a
real green-field loop hit the hard way. Encoding them up front saves 50–100
iterations of rediscovery. **Invariant 7 carries the Judgment default;
invariant 8 carries the consult contract** — do not also emit them separately.

{{INVARIANTS}}
<!-- inline the 11 invariants verbatim from references/greenfield-invariants.md -->

## Capability surface

CAPABILITY mode is first-class (invariant 6). The loop may install / integrate
the following to advance the stone — each addition justified against a
stone-axis, never to pad the toolbelt:

{{CAPABILITY_LIST}}

{{INCLUDE primitives/evidence-tier.md}}

## Phase gates

Phase order: research → preloop → bootstrap (iter 0, automated) → iter 1+.
Each gate declares `owner: loop | user | external`. A `user`-owned gate
(preloop_complete, license clicks, secret install, identity decisions) cannot
be flipped to `yes` by the loop. Gate hardening: binary `yes`, or halt.

{{PHASE_GATES}}

## Bootstrap mode

Enter Bootstrap mode whenever durable state shows the archetype's
iteration-0 work is still open: `.loop/<loop-id>/RUBRIC.md` or
`.loop/<loop-id>/INTENT.md` does not exist yet, or `STATE.md` records the
research or preloop gate as incomplete.

Inside Bootstrap, do the iteration-0 work the archetype already implies:
close Phase 0 research (invariant 10), draft `RUBRIC.md` under score-lock
(invariant 1), seed `.loop/<loop-id>/INTENT.md` with its ≥3 hypotheses
(invariant 3), and work the preloop checklist (invariant 10). Never flip a
`user`-owned gate to unblock Bootstrap — halt and surface the blocked gate
instead of guessing at it (invariant 10's role-protected gates).

Exit Bootstrap permanently — it does not re-enter — the first time a
stone-advancing iteration can run: the research and preloop gates are `yes`
(or the phase does not apply) with their required exit evidence, `RUBRIC.md`
clears the score-lock exit bar, and `INTENT.md` holds its live hypotheses.
From then on, gaps are ordinary iteration work, not a return to Bootstrap.

## Iteration protocol

1. Read `.loop/<loop-id>/STATE.md` and `.loop/<loop-id>/PRESSURE.md` for
   phase, score-lock, gate state, and any active pressure.
2. If Bootstrap mode still applies, do that work instead and stop here.
3. Diagnose the currently most imbalanced stone axis or rubric gap —
   imbalance-seeking (invariant 5), not a sequenced plan.
4. Pick ONE intervention that most advances the stone. CAPABILITY mode is
   admissible at its own priority rules (invariant 6) but must justify
   itself against a stone-axis, never to pad the toolbelt.
5. Make the change, then score it against `.loop/<loop-id>/RUBRIC.md`; any
   score above 2 requires citation evidence (invariant 2) or it caps at 2.
6. Update `.loop/<loop-id>/RUBRIC.md`, `.loop/<loop-id>/INTENT.md`,
   `.loop/<loop-id>/STATE.md`, and `.loop/<loop-id>/README.md` so another
   runner can resume from the artifacts alone.
7. Close per the runner contract: one focused commit for an accepted
   iteration with tracked-file changes (invariant 11); revert rejected diffs.
8. This loop is manual-gated — it proposes, the user disposes. Continue to
   the next iteration unless a halt cause below applies.

## Halt conditions

This loop is `manual-gated` (see `halt-shape`): it persists by design and ends
only when the user flips `Next action: HALT` (owner: user) or on a classified
cause below. `stone-converged` is the user's call — the loop proposes, the user
disposes. Convergence is `stone-reframe`: the artifact landing on the user's
*reframed* target, not a fixed number.

{{INCLUDE primitives/halt-cause-classifier.md}}
<!-- terminal cause for this archetype: stone-converged -->

## Artifacts to maintain

- `.loop/<loop-id>/RUBRIC.md` — numbered criteria (8–12), 0–5 scale, concrete pixel/
  artifact anchors. Every score >2 cites evidence (invariant 2). Carries
  `rubric_version` + `score_comparable_with`; score quarantine on reframe
  (invariant 4).
- `.loop/<loop-id>/INTENT.md` — ≥3 live target hypotheses with invalidating evidence and
  a cheap distinguishing probe each (invariant 3).
- `.loop/<loop-id>/STATE.md` — `phase`, `iteration`, `score_lock`,
  `phase_gates` (owner + value per gate), `current_stone_axis`,
  `capability_list`, `user_halt_owner`, `halt_cause`, `halt_scan`,
  `last_action`/`next_action`, `pressure_objects`, `pressure_ledger`,
  `pressure_consulted`, the `Next action: HALT` hatch (owner: user).
  `rubric_version`, `score_comparable_with`, and `target_hypotheses` live in
  RUBRIC.md / INTENT.md, not here.
- `.loop/<loop-id>/README.md` — how to fire, how to tune the rubric, how to halt, what
  milestones look like.

{{INCLUDE primitives/queue-as-second-artifact.md}}
<!-- this archetype's queue is rubric+intent; it is an INDEX, not the source of intent -->
````

---

## Derivation notes

Placeholders populated during composition (see `templates/composed-prompt.md`):

- `{{PROVENANCE}}` — the loopgen provenance preamble.
- `{{MOTIVE}}` — the user's one-sentence intent ("build me something X-adjacent").
- `{{FRONTLOAD_PREAMBLE}}` — resolved / defaulted / open-gap summary.
- `{{PRESSURE_SURFACE}}` — the pressure weather block (`primitives/pressure.md`),
  emitted only when ≥1 pressure object exists at compose time; stripped otherwise.
- `{{SUBAGENT_PATTERNS}}` — the subagent-pattern catalog B/C/D
  (`primitives/subagent-patterns.md`), emitted only at `consult-tier ≥ 1` and
  filtered to that tier; stripped byte-identical at tier-0.
- `{{INVARIANTS}}` — inline the 11 invariants verbatim from
  `references/greenfield-invariants.md`.
- `{{CAPABILITY_LIST}}` — domain-specific tools the loop may install (invariant 6).
- `{{PHASE_GATES}}` — research/preloop checklist items with owners (invariant 10).

Bootstrap mode and the iteration protocol are static prose — self-gated on
`.loop/<loop-id>/RUBRIC.md` / `INTENT.md` / `STATE.md` per the runner
contract's idempotency corollary — not filled placeholders; nothing in
either section is dropped or defaulted at derivation time.

Consult degradation: if `consult-capability` is `tier-0`, invariant 8 is
marked `CONSULT unavailable in this environment — front-loaded as a known
limitation` and a periodic human-look gate is added (see
`primitives/consult-capability.md`). Do not silently drop the invariant.
