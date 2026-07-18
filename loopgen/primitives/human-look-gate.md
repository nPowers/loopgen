# human-look-gate (shared block, gated)

## Purpose

The tier-0 consult substitute the capability authority promises
(`primitives/consult-capability.md`: drop consult sections, "substitute a
periodic human-look gate"). At `tier-0` there is no consult channel at all —
not even an async relay — so any emitted instruction shaped "ask the consult
channel" would be a phantom the runner cannot execute. This block is the real,
noninteractive substitute: the loop packages what a human should look at as a
**review packet** and keeps moving under `primitives/judgment-default.md`; it
never blocks and never prompts.

## Include when

**Gated on the `consult-capability` tier with the opposite polarity to
`{{SUBAGENT_PATTERNS}}`:** emitted **only at `tier-0`**, stripped
byte-identical at `tier ≥ 1` (where the consult sections themselves emit and
this substitute would be dead weight). Every body carries the
`{{HUMAN_LOOK_GATE}}` slot immediately after `{{SUBAGENT_PATTERNS}}`.

## Placeholders

`{{HUMAN_LOOK_GATE}}` — substituted with the block below the `---` at
`tier-0`; stripped byte-identical (placeholder + trailing blank line) at
`tier ≥ 1` — the mirror of the `{{SUBAGENT_PATTERNS}}` strip rule
(`templates/composed-prompt.md` steps 7b/8).

## Authoring guidance (not emitted)

- **Noninteractive by construction.** The gate writes and continues (or halts
  on the archetype's own contract); it never calls an interactive tool and
  never waits (`primitives/runner-contract.md`,
  `primitives/judgment-default.md`).
- **Reuse the existing record.** The review packet is an `alignment_review`
  journal record — the Judgment default's own record already carries the
  "review question for the human" field — never a new record type or a new
  monitor file (`primitives/context-stack.md`: one history surface).
- **One surface, three consumers.** The consolidation `fork`
  (`primitives/context-stack.md`), the frontier structural-escalation bridge
  (`templates/bodies/frontier-body.md`), and the benchmark-frontier `consult`
  lineage row (`primitives/benchmark-frontier.md`) all route here at tier-0 —
  route new consult-shaped actions here too rather than inventing another
  substitute.

---

## Human-look gate (tier-0 consult substitute)

This loop has **no consult channel** (`consult-capability` tier-0). Every
instruction shaped "route it to the consult channel" resolves here instead —
never to a phantom tool, never to an interactive prompt:

- **Write a review packet, then keep moving.** Record an `alignment_review`
  in `.loop/<loop-id>/JOURNAL.jsonl` (the Judgment default's record): problem ·
  evidence pointers · options considered · the disposition taken · and the
  **review question a consult would have answered**. Surface it as one line in
  that iteration's summary; the human reads it asynchronously via the journal
  watch command.
- **Periodic, not per-pass.** Mint a packet whenever a consult-shaped need
  arises (a consolidation `fork`, a structural diagnosis, a wanted second
  look), and at latest at each consolidation round.
- **Never block.** Proceed under the Judgment default (smallest reversible
  action + the packet); irreversible or authority-needing calls still route to
  `escalate` / `stop-and-summarize` with the question in the summary — async
  always, interactive never.
