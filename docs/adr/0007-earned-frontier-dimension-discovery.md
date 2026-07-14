# ADR 0007: frontier dimensions are earned through a vector-adequacy lifecycle, never invented

- **Status:** Accepted (amended 2026-07-13; amends ADR 0006)
- **Date:** 2026-07-13
- **Deciders:** provi, Claude (Fable 5)

## Context

The frontier body already *commanded* vector growth without a contract for
it: the expansion-ramp prose told a loop at what the old contract called
quiescence to "add a new … evaluator dimension", and cash-out option 2 said
"update the frontier vector" — both
direct-mutation instructions with no evidence bar, no cap, no authority rule,
and no answer to who wins between the prompt's baked `{{FRONTIER_VECTOR}}`
and the `STATE.md` `frontier_vector` live key (both existed; neither was
declared authoritative). On a closed corpus this was also a fresh route back
into the trap ADR 0006 closed: a terminal episode could escape declared-
workset exhaustion indefinitely by hypothesizing one more dimension each time
balance was reached.

Loopgen's axis vocabularies are otherwise all closed: the weighted
classification axes, the five homeostasis axes, the four `disturbed_axis`
values. The one coordinate system that legitimately evolves per repo is the
frontier vector — the *outcome* space, not a control axis.

## Decision

**Lifecycle, not prose.** A frontier-only primitive
(`primitives/frontier-vector-adequacy.md`, inlined into the body after
Homeostasis) replaces the expansion-ramp scan with a falsifiable question at
**provisional balance**, before quiescence is declared: can the live vector
still distinguish meaningful progress? A genuinely new dimension is one
candidate per provisional-balance event (evidence bar:
two independent residuals, or one strong impossible/external observation; not
a synonym; within motive and scope), carried as an ordinary OPEN finding with
a pre-registered discriminative probe executed as an ordinary `attempt`
record. `dimension_outcome` is a closed four-value enum (`pending` /
`admitted` / `falsified` / `handoff`) mapped onto the existing finding
statuses — no parallel vocabulary. A checkpoint with the vector unscanned or
a candidate probe pending is invalid. Rejected alternatives: a sixth
homeostasis axis or fifth `disturbed_axis` (control coordinates are closed and
the same-family counter counts on them; outcome dimensions are a different
kind), and a new artifact/journal type (candidates, probes, and admission
deltas fit findings rows, `attempt` records, and `checkpoint` records).

**Independence gate.** A pre-registered probe permits same-pass
`CLOSED_CONFIRMED` only when its verdict comes from a tier-1 surface or a
tier-2 channel outside the candidate's change cone; the candidate may not
author, mutate, or validate its own confirming channel. Otherwise the outcome
waits at `FIXED_PENDING_CONFIRMATION` for next-pass confirmation. This is the
pressure `satisfied_by` pre-registration logic applied to closure, and
`CLOSED_CONFIRMED` is broadened to "independently confirmed resolved".

**Seed vs live authority.** `{{FRONTIER_VECTOR}}` is bootstrap input only:
normalized once into compact one-line `STATE.md` rows (≤ 8
`{id, channel_ref}` dimensions plus a `guardrails` map; legacy name-only
entries become `channel_ref: null`, never dropped, never given an invented
channel). Thereafter STATE is the sole authority; the re-entrant prompt never
overwrites it. At the cap: merge, supersede, falsify, or hand off — never a
ninth dimension.

**Workset identity vs version (the ADR 0006 amendment).** The closure basis a
fresh terminal composition records gains a fourth field,
`initial_frontier_vector` — the four fields *are* the declared workset's
identity, so an effective-terminal episode finishes the frame it declared and
its live vector never mutates. A candidate surviving its (at most one,
in-surface, in-budget) probe is `handoff` output for a new declared-workset
version. ADR 0006's "a new declared-workset version" re-entry event is now
defined concretely: the version **is** the zero-padded loop id, so only a
fresh `/loopgen` derivation mints one — a running loop can mint neither
version nor identity (write-once `DERIVATION.md`), and version inequality
never implies the frame changed. Legacy three-field bases keep their recorded
semantics (fourth key absent = back-compat; present-but-empty = derivation
gap). A self-computed content hash was rejected: write-once fields plus the
already-minted monotonic loop id enforce the same thing with no
canonicalization machinery.

**Every mutation path routes through the lifecycle.** Cash-out option 2 now
scores against the live vector instead of editing it; the benchmark overlay's
green-trace metric/evaluator-dimension expansion opens a candidate instead of
appending; benchmark admission is an atomic projection change
(`pareto_dimensions` gains the id, every current member scores the new metric
with durable receipts, *then* the live vector switches — partial backfill
means not admitted yet, and backfill cost obeys the frontload budget rules).
The equilibrium/terminal authority split lives exclusively in the
reopen-policy variant blocks — the composer's one per-variant render point —
so the body stays mode-neutral.

## Consequences

- Equilibrium episodes can still discover new coordinates — but a candidate
  now changes decisions or dies: it needs independent residuals going in and
  a pre-registered discriminative probe coming out, and a rejected candidate
  *permits* the checkpoint only after independent or next-pass confirmation,
  instead of blocking it forever. Terminal means "finish the declared epistemic
  frame", not "enlarge it whenever it reveals its limits".
- Homeostasis balance is now explicitly **provisional**. Quiescence is reserved
  for the post-scan state in which pressure discovery found no admissible work
  and vector adequacy has no candidate awaiting a probe or confirmation and no
  newly admitted dimension requiring continuation; this prevents the iteration
  protocol from halting before the new lifecycle runs.
- `tools/verify_loopgen_contracts.py` enforces the contract as prose pins and
  executable fixtures: the closed outcome enum and status mapping, the
  probe→`disturbed_axis` mapping (candidate ids never enter the closed four),
  terminal non-mutation with `admitted in-episode` a banned terminal token,
  the four-field/legacy closure paths in the guard fixtures, max-pack STATE
  arithmetic (all live keys + 12 pressure rows ≤ the ~50-line bound), and the
  single-source evidence bar. Two frozen goldens pin the pure and
  benchmark-overlay equilibrium renders; `--capture-golden` writes exactly
  both, committed with the edit that moved them.
- The disconfirming signal is unchanged from the design review: repeated
  adequacy scans that produce no decision-changing candidates while
  materially extending runs would justify demoting the scan from
  mandatory-before-checkpoint to contradiction-triggered.
- Existing compiled `.loop/*/PROMPT.md` artifacts are untouched; legacy
  vectors and three-field closure bases resolve under their recorded
  semantics.
- Lineage anchor: the fva series on `main` — `7100146` (dormant primitive),
  `5ead97f` (workset identity + seed-vs-live authority), `ebe6b0f` (runtime
  admission wiring + benchmark parity), plus this ADR's commit. Builds on
  ADR 0004 (STATE/JOURNAL/DERIVATION memory model), ADR 0005 (consolidation
  round), ADR 0006 (guarded closed-corpus terminal resolution).
