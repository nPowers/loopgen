# ADR 0006: closed-corpus frontier resolves to effective-terminal via a frontload reopening contract

- **Status:** Accepted (amended by ADR 0007: `closure_basis` gains
  `initial_frontier_vector` as a fourth identity field, and "a new
  declared-workset version" is defined as a fresh derivation's loop id —
  only operator action mints one)
- **Date:** 2026-07-09
- **Deciders:** provi, Claude (Fable 5)

## Context

The iching "Asymptote" run — a 159-round autonomous `/refactor` loop on a
frozen single-dev feature branch (117 gated commits / 42 honest no-commits;
inbox note `2026-06-20-asymptote-axis-aware-admissibility`, now archived to
`.inbox/.read/`) — dogfooded two frontier contract gaps at once, and was the
third independent confirmation of the same-family drift family
(`references/same-family-drift.md`).

**Gap 1 — the closed-corpus equilibrium trap.** Frontier's default
`halt-shape: equilibrium` means "checkpoint at balance; reopen automatically
on strong new signal." On a corpus whose only change source is the loop's own
commits (banned as positive signal by same-family-drift fix #1), no normal
reopen signal can ever arrive, so equilibrium degenerates into indefinite
polishing *by construction*. Asymptote reached quiescence and recommended stop
five times; nothing in the contract said terminate.

**Gap 2 — the expensive false mode-break.** The same-family admissibility
trigger was keyed on *invariant-kind*. Asymptote rotated its search probe
(duplication → magic-constants → regex literals → …): a new invariant-kind
every round, every find real, gated, non-cosmetic — and 159 rounds on one
homeostasis axis, with a known product defect sitting OPEN for ~12 rounds
alongside naming nits. An admissibility rule keyed on cosmetic-vs-real waves
probe rotation through, because the output is real.

Objective-completion, execution-quiescence, and future-reactivation are three
different state transitions; loopgen conflated them under one `halt-shape`
label and one "frontier loops do not self-complete" sentence.

## Decision

**Detector.** Frontier frontload asks the reactivation question (the
Reopening-contract item, `primitives/frontload-audit.md`): *what event outside
this execution can add admissible work after quiescence, and through what
channel will the runner observe and deliver it?* Records `reopening_signal`,
`reopen_contract`, and — when the contract is `none` — `closure_basis`, all
under `DERIVATION.md` `frontload:`. `none` is a closed-world inference, legal
only with the runner's observable work-source domain enumerated; asserted
staticness without enumeration is an `open_gaps` entry. `closure_basis` is a
compose-time closure *contract* (domain + declared search surfaces + the
criterion that will establish workset exhaustion at runtime) — never a
runtime quiescence observation.

**Rule.** A guarded implication — explicitly not a biconditional
(`primitives/halt-shape.md`): `frontier AND requested=equilibrium AND
reopen_contract=none AND closure_basis established → effective=terminal`.
Everything else passes through. Provenance records requested and effective
when they differ. `terminal` is redefined archetype-neutrally: the execution
does not auto-resume; a new execution starts only on an exceptional event
(per-row `reopen_condition`, regression, or a new declared-workset version).
Regression is exceptional re-entry under both policies, never a reopen
contract. No new vocabulary value (H2 `converge-and-stop` rejected — fails
the ≥2-archetype locked-matrix test; H3 "bounded equilibrium" rejected as
primary — an equilibrium that cannot reopen is not one).

**Target.** The frontier body's reopen-policy block is parameterized as
`{{FRONTIER_REOPEN_POLICY}}`, selected from `effective_halt_shape`; both
variants live as authoring content in
`templates/bodies/frontier-reopen-policy.md` (equilibrium = the prior inline
text byte-for-byte; terminal = "declared workset exhausted" termination with
episode-pause semantics for non-quiescence halts). The composer and verifier
extract by heading; neither duplicates the text.

**Identity.** The ambiguous "frontier loops do not self-complete" claim is
replaced everywhere by one two-level scoped invariant: a frontier *objective*
has no quality pass-line and never completes by being good enough; a frontier
*episode* may terminate on an extrinsic lifecycle reason — termination ends
the execution, not the objective. "Non-terminal halt" is renamed "non-success
halt" wherever the distinction is objective-completion, and an
effective-terminal episode termination carries the same full
search-surface-scan precondition as every non-success halt.

**Admissibility (the D2 residual, landed with this series).** Same-family
concentration is counted on the closed `disturbed_axis` vocabulary
(`oracle-trustworthiness` · `product-capability` · `failure-legibility` ·
`specification-coherence`; intervention-diversity is the meta-axis and never a
recorded value): once five accepted changes exist, ≥3 of the most recent five
on one key. Probe rotation is named as a trigger signature, and a genuine,
non-cosmetic same-axis find does not satisfy the mode break — qualifying
signals must predate intervention selection and be independent of the
candidate change.

## Consequences

- A frontier loop on a frozen corpus now composes with a contract that says
  *terminate at quiescence* instead of waiting for a signal that cannot
  arrive. The **actuator** — making a dumb cron honor that contract — remains
  runner-side and deferred per ADR 0001 (loopgen writes the contract; the
  runner owns delivery and halt).
- `tools/verify_loopgen_contracts.py` (50 checks) enforces: equilibrium
  playbook byte-identity against the frozen golden
  (`tools/golden/frontier-body.equilibrium.md`, regenerated only via
  `--capture-golden` committed with the moving edit), terminal-variant
  semantics with no equilibrium residue, frontier-only policy placement, the
  guarded resolution over twelve input paths via an executable spec
  (`resolve_effective_halt_shape`), and the prose conjuncts pinned against
  silent drift.
- Reopening-contract fields are required for fresh frontier compositions;
  the absent→legacy-equilibrium path survives only for pre-existing artifacts
  and verifier fixtures.
- Follow-up direction (audit note `2026-07-01-audit-direction-candidates`,
  archived to `.inbox/.read/`): D3 golden drift/admissibility fixtures now
  encode the *new* rule; D4 Diagnostic-mode stays gated on a dogfooding
  citation; D5 (route real story/greenfield tasks through `/loopgen`) is a
  standing routing rule, not a task.
- Lineage anchor: the reopening-signal commit series on `main`
  (`fd6ea6d..66f95dc`: D2, U1, U2, U3a, U4a, U3b, U4b; review-round fixes
  `8c9eed2..2a2f2c0`: journal-counted concentration, policy-neutral halt
  prose, cause-neutral terminal variant, guard evidence hardening, durable
  divergence triple), plan
  `dev/plans/2026-06-23-001` (local, GPT-Pro-reviewed v2). Builds on ADR 0001
  (runtime ownership), ADR 0004 (DERIVATION.md as the write-once derivation
  record).
