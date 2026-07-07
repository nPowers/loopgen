# diagnostic-pattern (shared primitive)

## Purpose

Used by `SKILL.md` Diagnostic mode to retrofit a **drifting** loop — not to
author a new one.

## Include when

Diagnostic mode only. Not part of an emitted prompt.

## Procedure

1. **Read** the current `.loop/<loop-id>/PROMPT.md`, `.loop/<loop-id>/STATE.md`, the queue artifact
   (`artifact-shape`), and the ledger / recent diffs.
2. **Classify which archetype the loop currently is** — extract its live
   primitive values. It may have **drifted from its declared archetype** (the
   loopgen addition).
3. **Score** against that archetype's failure modes (`archetypes/*.md`).
4. **Name** the dominant disturbed axis / missing invariant.
5. **Emit a minimal mutation** — an inline `.loop/<loop-id>/PROMPT.md` edit, never a
   rewrite. The hand-evolved prompt has hard-won lessons; add what is missing
   without losing them.
6. **Write a ⚠️ block** to `.loop/<loop-id>/STATE.md` telling the next iteration what
   changed and why.

## Drift-from-declared check (loopgen addition)

If the loop's current primitive values no longer match its declared archetype,
**flag the drift in the ⚠️ block before suggesting a mutation**. A loop whose
`target-shape` has changed (e.g. a frontier loop that has discovered a finite
checklist) may need re-derivation via the full Phase 1–4 flow, not a patch.

## Pre-context-stack recognition (loopgen addition)

A loop composed before the context-stack model (ADR 0004) has the **old STATE
shape**: an unbounded `attempt_log` / `pressure_ledger` / `pressure_consulted`
living in `.loop/<loop-id>/STATE.md`, no `.loop/<loop-id>/JOURNAL.jsonl`, and no
`.loop/<loop-id>/DERIVATION.md`. Recognize it when diagnosing and name it in the
⚠️ block. **Do not migrate the existing `.loop/` dir** — it is gitignored
execution scratch (ADR 0003), not a deliverable, so rewriting its accumulated
history is churn with no payoff. The minimal mutation adds the journal + tier
discipline to `.loop/<loop-id>/PROMPT.md` **going forward** (new records land in
`JOURNAL.jsonl`; `STATE.md` stops growing and sheds its history keys), leaving
the old history in place as-is.

## Composition notes

- Reuses the `evidence-tier` ranking to decide which surfaces to trust when
  diagnosing.
- The mutation's success criterion is itself a frontier anchor: the next
  iteration should confirm the drift closed.
