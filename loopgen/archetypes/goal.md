# goal (archetype)

## Loop shape

A terminal closing loop. A finite, frozen acceptance inventory; one
discriminative binary verifier per criterion; a two-step proof — a criterion's
own verifier passing marks `PASS_PENDING_FINAL`, and only the single
**final-verify** (one command that proves the whole inventory in the same repo
state) moves it to `PASS`. The run is complete only when every criterion
reaches `PASS` without the loop weakening any criterion to get there
(`criteria-met`). Partial completion is `partial-deadlock`, never success.

## Default primitive values

| Axis | Default |
|---|---|
| `target-shape` | `finite-criteria` |
| `halt-shape` | `terminal` |
| `artifact-shape` | `acceptance-inventory` |
| `convergence-shape` | `criteria-completion` |
| `cadence-shape` | `sync` |
| `consult-capability` | detect (`tier-0` default) |

## Forbidden divergences

- `target-shape ≠ finite-criteria` — a moving target is not goal-shaped; route
  to `frontier` (make-it-better), `story` (promise discovery), or `greenfield`
  (undefined target).
- `halt-shape: manual-gated` — a terminal loop only the human ends is not
  terminal.
- `convergence-shape ≠ criteria-completion`.

## Failure modes

- **Oracle drift** — the loop weakens criteria / verifiers / expected evidence
  to pass. Mitigation: frozen inventory + Oracle Change Notes + final-verify.
- **Verification theater** — the same entity produces and verifies. Mitigation:
  oracle independence (a loop-authored verifier must first fail).
- **Pass theater** — one verifier green claimed as completion. Mitigation:
  `criteria-met` requires the final-verify to prove the whole inventory in one
  repo state.
- **Partial-victory laundering** — "7 of 10 is basically done." Mitigation:
  partial completion is `partial-deadlock`.
- **Verifier vanity** — tests exist but don't distinguish wrong behavior.
  Mitigation: every criterion has named `fail_evidence` (mutation / sentinel /
  known red).
- **Scope escape** — editing adjacent surfaces to make proof easier. Mitigation:
  scope manifest (binary in/out, not percentage).
- **Frontier masquerade** — a moving target forced into a terminal checklist.
  Mitigation: the `wrong-loop` halt-cause with reroute targets.

## Extras

- Includes `references/oracle-principles.md` (the four principles + the
  honest-verifier invariants).
- Emits `.loop/<loop-id>/ACCEPTANCE.md` + `.loop/<loop-id>/VERIFY.md` as required artifacts.
- Optional `.loop/<loop-id>/PROMPT_verify.md` (a separate verifier agent) for high-stakes
  oracle independence — payments, data-loss, security boundaries.
- Body template: `templates/bodies/goal-body.md`.
