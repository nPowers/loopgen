# ADR 0005: the consolidation round is the contract-layer checkpoint

- **Status:** Accepted
- **Date:** 2026-07-09
- **Deciders:** provi, Claude (Fable 5)

## Context

The dota-market Supabase pooler incident (inbox note
`2026-07-06-contract-layer-checkpoint`, now archived to `.inbox/.read/`)
measured a failure class no per-row mechanism sees: the market-movement loop
applied several **locally correct** app-layer fixes — durable receipts, plan
coverage, proof-path hardening — while the actually violated contract sat one
layer *below* the code it was modeling (Supabase transaction-pooler mode on
port 6543 silently rolling back multi-statement transactions that the driver
reported as committed). Every fix was reasonable; the target never moved; the
loop kept chasing downstream symptoms and accumulating defensive code. The
decisive shift came only when a fresh prompt stopped advancing the acceptance
queue and attacked the contradiction directly.

The note asked loopgen to encode this as a **triggerable loop primitive**
(candidate names: `contract_layer_checkpoint`, `substrate_reflection`,
`impossible_observation_audit`), with two constraints from the maintainer:
no private/custom skill names as required dependencies in emitted prompts, and
compile-time borrowing of adjacent conceptual lenses is welcome but the
emitted loop must stand alone.

Separately, the context-stack refactor (ADR 0004, U13) had already introduced
a `consolidation` journal record — the journal's lessons layer, written every
~10 iterations — without yet specifying what the consolidation *round* does.

## Decision

**The contract-layer checkpoint is not a new primitive. It is the trigger set
and substrate-audit step of the consolidation round**, specified in
`primitives/context-stack.md` (the round's procedure and triggers) and
`primitives/pressure.md` (the field read: debt-conserving merge, substrate
stamp, lesson promotion).

1. **Scheduled + forced.** The round runs on cadence (~10 iterations, closure
   boundaries, pre-final-verify) **and is forced early** by any of: a scope
   surviving 2+ correct-looking fixes; a target metric unmoved by fixes that
   should have moved it; local proof vs production/durable state disagreeing;
   an impossible observation (two facts mutually exclusive under the current
   model); defensive code accumulating without reducing uncertainty. The
   context-health check gains line 7 (consolidation within cadence and no
   unserviced trigger), so an overdue round is a step-0 routing, not a hope.
2. **The round reads the pressure field, not the queue.** Cluster in-force
   rows around shared suspected causes; name the impossible observation;
   enumerate the contracts beneath the code (deploy identity, env parity, DB
   transport/pooler mode, driver transaction semantics, queue ownership,
   external API authority) and classify each as **checked at runtime /
   inferred from config / unverified**. Unverified-but-relied-on guarantees
   become runtime checks, launch invariants, or explicit blocked conditions.
3. **Merges conserve debt.** Cross-scope merge at a shared cause inherits the
   strongest mode/strength and the union of pre-registered `satisfied_by`
   channels; absorbed rows leave `merged-into:<id>` journal records. A merge
   is never a launder — this closes the exit where consolidation could quietly
   retire rows that were losing their argument.
4. **The decision is recorded.** The `consolidation` record gains optional
   `field`, `suspected_substrate`, and `decision` (continue / fork a fresh
   root-cause attack on the contradiction via the consult channel / mint a
   cleanup row auditing symptom-era defenses).
5. **Lens borrowing at compose time.** The composer may sharpen the round's
   substrate-audit wording with adjacent lenses found in the host repo
   (meta/reflection, substrate-audit, invariant-check, environment-parity
   skills or docs) — concepts only, never named private skills, never a
   dependency: the emitted loop stands alone (`templates/composed-prompt.md`
   assembly step 2).

## Why not a new primitive

- **The trigger data already exists.** "Survived 2+ correct-looking fixes" and
  "metric unmoved" are exactly what the pressure machinery records for free:
  `no-effect` consult streaks and rows paid on their channels without target
  movement. A separate primitive would either duplicate that bookkeeping or
  depend on pressure anyway.
- **The storage rules forbid a fifth surface.** Frontier's storage rule (and
  the ADR 0004 no-monitor-file decision) treat new artifact roles as creep; a
  `SUBSTRATE.md` or standalone checkpoint file would be the exact anti-pattern
  the refactor removed.
- **Haptics framing.** The round is the loop's one bounded moment of feeling
  where the pressure is — reading the whole field instead of the next row.
  Splitting "summarize lessons" (consolidation) from "audit the substrate"
  (checkpoint) would put the field read and its strongest consumer in two
  different rituals that fire at different times.

## Consequences

- Emitted prompts (all four archetypes, via the always-on context-stack and
  pressure includes) now carry the round: triggers, field read, substrate
  audit, decision recording. `tools/verify_loopgen_contracts.py` enforces the
  markers (`u14_consolidation_contracts`, `consolidation_emitted`).
- The `PRESSURE.md` HUD header carries a `last consolidation: iter N · next
  due ~N+10` stamp, so field-read recency is visible every pass.
- Cost: the round is one bounded read-and-write over an already-capped set
  (≤ `pressure-cap` rows) roughly every 10 iterations — amortized noise next
  to the ~7k/iteration ceremony budget (ADR 0004).
- dota-market's cleanup pattern (VID-458: "permanent invariant, or
  compensation for the old broken world?") is generalized as the round's
  `cleanup` decision, so post-root-cause symptom-era defenses get audited
  instead of enshrined.
