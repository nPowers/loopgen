# human-look-gate (shared block, always emitted, effective-gated)

## Purpose

The consult fallback the capability authority promises
(`primitives/consult-capability.md`): when consult capability resolves to
**tier-0** — at compose time, or at runtime when the Run-host channel check
downgrades a promised channel — every "ask the consult channel" instruction
needs a real, noninteractive substitute. The loop packages what a human
should look at as a **review packet** and keeps moving under
`primitives/judgment-default.md`; it never blocks and never prompts. A
packet is self-authored, so everything it carries is **provisional** — it
can never stand in for the consult verdict it substitutes.

## Include when

**Always emitted, every body, every tier** — like `{{PRESSURE_SURFACE}}`,
never stripped. A consulted prompt (`tier ≥ 1`) may lawfully become
effectively tier-0 mid-run (the Run-host channel check degrades per channel,
ultimately to this gate), so the fallback must already be in the prompt when
that happens: the gate is **dormant while live channels cover the need,
live wherever `consult_tier_effective` resolves a need to tier-0**. Compose
gating would strip the very block the downgrade path lands on.

## Placeholders

`{{HUMAN_LOOK_GATE}}` — always substituted with the block below the `---`
(no compose gate; the liveness gate is the runtime condition stated inside
the block). Sits immediately after `{{SUBAGENT_PATTERNS}}` in every body.

## Authoring guidance (not emitted)

- **Noninteractive by construction.** The gate writes and continues (or halts
  on the archetype's own contract); it never calls an interactive tool and
  never waits (`primitives/runner-contract.md`,
  `primitives/judgment-default.md`).
- **Reuse the existing record, join the schema.** The review packet is an
  `alignment_review` journal record — `item` / `decision` / `anchor` plus the
  packet fields `packet` (stable id) and `question`
  (`primitives/context-stack.md` names them in the record table, and the
  human watch projection surfaces them) — never a new record type or a new
  monitor file.
- **Provisional, never authority.** A packet cannot pay a pressure row, close
  a finding, or serve as acceptance authority; tier-0 classifications are
  self-authored hypotheses that license only reversible probes.
- **One surface, three consumers.** The consolidation `fork`
  (`primitives/context-stack.md`), the frontier structural-escalation bridge
  (`templates/bodies/frontier-body.md`), and the benchmark-frontier `consult`
  lineage row (`primitives/benchmark-frontier.md`) all resolve here when
  effectively tier-0 — route new consult-shaped actions here too rather than
  inventing another substitute.

---

## Human-look gate (consult fallback)

**Live condition.** This gate is live wherever consult capability is
*effectively* tier-0: for the whole loop when no channel was detected at
compose, or per channel whenever the Run-host channel check degrades a
promised channel down to this substitute (`consult_tier_effective`,
`STATE.md`). While a live consult channel covers a need, the gate stays
dormant. When live, every instruction shaped "route it to the consult
channel" resolves here — never to a phantom tool, never to an interactive
prompt:

- **Write a review packet, then keep moving.** Record an `alignment_review`
  in `.loop/<loop-id>/JOURNAL.jsonl` carrying its usual fields plus the
  packet pair: `item` (the consult-shaped need), `decision` (the disposition
  taken), `anchor` (evidence pointer), `packet` (stable id, `hlp-<iter>-<n>`),
  `question` (what a consult would have answered). Surface `packet` +
  `question` as one line in that iteration's summary; the human reads them
  asynchronously via the journal watch command.
- **Self-authored means provisional.** A packet records your own judgment,
  not a consult verdict — it cannot pay a pressure row, close a finding, or
  serve as acceptance authority; those still require the archetype's own
  tier-1/2 evidence. A tier-0 classification licenses **reversible probes
  only**, under the Judgment default; irreversible or authority-needing calls
  route to `escalate` / `stop-and-summarize` with the question in the
  summary — async always, interactive never.
- **Periodic, not per-pass.** Mint a packet whenever a consult-shaped need
  arises (a consolidation `fork`, a structural diagnosis, a wanted second
  look), and at latest at each consolidation round.
