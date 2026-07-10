# halt-shape (axis primitive)

## Purpose

The **reopen policy** — once the loop stops, is that final, reopenable, or only
the human's call? Weight 3. Distinct from `convergence-shape`, which names the
*stop signal*; halt-shape names what happens *after* the stop. A composed
prompt names both.

## Values

- `terminal` — the current execution does not auto-resume; a new execution may
  start only on an allowed exceptional event — an explicit per-row
  `reopen_condition`, a regression, or a new declared-workset version.
- `equilibrium` — checkpoints at homeostatic balance; reopens
  **automatically** on strong new signal (externally reviewed finding, typed
  failing trace, oracle verdict, metric movement). Requires a live **reopen
  contract**: a named external signal plus the observable channel through which
  the runner will receive it (the Reopening-contract frontload item,
  `primitives/frontload-audit.md`). An equilibrium that cannot name its reopen
  channel is not an equilibrium — see the guarded resolution below.
- `checkpoint-with-reopen` — halts on convergence but explicitly reopens when a
  new authoritative source / route / fixture appears (the story shape; bodytxt
  keeps it, sourced from story).
- `manual-gated` — the loop persists by design and only the human ends it, via a
  `Next action: HALT` hatch (owner: user).

## Detection heuristics

| Task phrasing | Value |
|---|---|
| finite spec, "done when criteria pass" | `terminal` |
| "keep improving until balanced", "stop when nothing's disturbed" | `equilibrium` |
| "living contract, revisit when sources change" | `checkpoint-with-reopen` |
| "run until I say stop", "I'll keep reframing" | `manual-gated` |
| frozen branch / fixed corpus / no observable inbound channel | effective `terminal` via the guarded resolution below — even for a `frontier-expanding` target |

## Archetype defaults

| Archetype | Default |
|---|---|
| frontier | `equilibrium` |
| goal | `terminal` |
| story | `checkpoint-with-reopen` |
| greenfield | `manual-gated` |

## Composition rules

- `manual-gated` is **forbidden** for `goal` — a terminal loop only the human
  ends is not terminal.
- Orthogonal to `convergence-shape`: one names the reopen policy, the other the
  stop signal. Provenance lists both when either diverges.
- `checkpoint-with-reopen` is `story`'s default, which is why bodytxt (a story
  loop with a `frontier-expanding` target) sources it from the story archetype
  (not as a brand-new value).
- **Contradiction** (ask the user): `equilibrium`/`manual-gated` with
  `target-shape: finite-criteria`.
- **Guarded closed-corpus resolution** (frontier only; an implication, **not**
  a biconditional):

  ```text
  archetype == frontier
    AND requested halt-shape == equilibrium   (the archetype default)
    AND reopen_contract == none               (frontload, closed-world proven)
    AND closure_basis established             (compose-time closure contract)
  → effective halt-shape := terminal
  ```

  Anything else passes through unchanged (`effective := requested`).
  Provenance records both sides when they differ —
  `halt-shape: requested=equilibrium → effective=terminal
  (reopen_contract=none; closure_basis: <…>)` — and emits no divergence line
  when they agree. The episode always stops at quiescence under both policies;
  only the reactivation policy and the halt label differ.
  `reopening_signal: none` means no *normal, non-regression* reopen signal —
  regression is exceptional re-entry under both policies, never a reopen
  contract. An explicitly requested `terminal` frontier is honored as
  requested, with no compiler-derived divergence line. This resolution is a
  frontload-resolved **divergence, not a contradiction**: the target stays
  `frontier-expanding`; nothing here weakens the `finite-criteria` +
  `equilibrium` contradiction above.
- For frontier compositions the reopening-contract fields are **required** —
  their absence is a derivation gap (`open_gaps`), not a default. Treating
  absent fields as legacy `equilibrium` is backward-compatibility for
  pre-existing loop artifacts and verifier fixtures only, never a fresh
  composition path.
