# frontier-vector-adequacy (shared frontier primitive)

## Purpose

The earned frontier-dimension lifecycle: whether the **live frontier vector**
can still distinguish meaningful progress, and the only path by which a new
dimension is proposed, probed, admitted, falsified, or handed off. The name is
deliberate — this repo's *axis* vocabularies are all closed (the weighted
classification axes, the five homeostasis axes, the four `disturbed_axis`
values); the one coordinate system allowed to evolve is the repo-specific
**frontier vector**, and it evolves only by evidence, never by prose.

| Vocabulary | Mutability |
|---|---|
| Compiler / classification axes (`SKILL.md` matrix) | permanently locked |
| Five homeostasis axes (frontier body) | permanently fixed |
| Four `disturbed_axis` values | permanently closed |
| Frontier-vector dimensions | repo-specific; bounded; evidence-expandable via this lifecycle |

Before this primitive, the frontier body commanded vector growth ("expansion
ramp", cash-out option "update the frontier vector") without a contract for
it. This primitive replaces that open-ended prose with a falsifiable scan and
closes every direct-mutation bypass.

## Include when

Every prompt whose nearest archetype is `frontier`, wired into the body's
provisional-balance path (the vector-adequacy scan replaces the expansion-ramp
scan line). The primitive is derivation-read and composed after Homeostasis;
non-frontier bodies never receive it.

## Authoring guidance (not emitted)

- **Why not a sixth homeostasis axis.** Homeostasis axes are *control*
  coordinates — they label interventions, and the same-family concentration
  counter counts on the closed `disturbed_axis` key. Frontier dimensions are
  *outcome* coordinates — what the repo's frontier moves along. Adding a
  control axis would ripple through counters, journal records, and goldens
  while still not giving discovered dimensions a home.
- **Why same-pass closure is legal under the independence gate.** The probe is
  **pre-registered before the intervention** — the same anti-laundering logic
  as pressure's pre-registered `satisfied_by` channel. A verdict the candidate
  could not have authored or steered is independent confirmation in the
  FIXED ≠ CLOSED sense; anything weaker waits for the next pass. (The body's
  status-taxonomy wording broadens from "independently confirmed fixed" to
  "independently confirmed resolved" when the storage unit lands.)
- **Version ≠ identity.** Workset *identity* is the four recorded closure-basis
  fields (`work_source_domain`, `declared_surfaces`, `exhaustion_criterion`,
  `initial_frontier_vector`); workset *version* is the already-minted
  zero-padded loop id. A new derivation necessarily gets a new version even
  for an identical workset — version inequality never implies the frame
  changed. A running loop cannot mint either: `DERIVATION.md` is write-once.
- **Mode-specific rendering.** The equilibrium/terminal admission-authority
  split is carried by the reopen-policy variant blocks
  (`templates/bodies/frontier-reopen-policy.md`) — the composer's only
  per-variant render point. The emitted block below and the body proper stay
  mode-neutral ("route through this lifecycle"); the variant states whether
  admission or handoff applies.
- **Candidate pressure decays.** A `scope: dimension` pressure row exists only
  while its candidate is unresolved (`expires` = the candidate's resolution).
  An admitted dimension is not permanent pressure; it is a live vector row
  whose channel and guardrail do the recurring work.

---

## Frontier-vector adequacy

The frontier vector is the repo's outcome coordinate system. It is **live
state, not prompt text**: the prompt's seeded dimensions are bootstrap input
only, and once `.loop/<loop-id>/STATE.md` `frontier_vector` exists, STATE is
the sole authority — the re-entrant prompt never overwrites it.

### Vector rows (compact, bounded)

`STATE.md` carries exactly two one-line keys for this lifecycle — no new keys:

- `frontier_vector` — a list of at most **eight** rows
  `{"id": <stable unique non-empty>, "channel_ref": <pointer | null>}`.
  `channel_ref: null` means the dimension is currently unmeasurable; the
  existing rule applies (the accepted change must be evaluator /
  observability / specification work that makes it measurable). A legacy
  name-only dimension normalizes to `{id: <original-name>, channel_ref: null}`
  — never dropped, never given an invented channel.
- `guardrails` — a map of dimension id → guardrail pointer (or null while
  unmeasurable).

At the cap, **merge, supersede, falsify, or hand off — never append a ninth
dimension.** A supersession carries the same evidence burden as an admission
and is recorded through the same transaction.

### The adequacy scan (replaces the expansion-ramp scan)

At **provisional balance** — known homeostasis axes are balanced and pressure
discovery found no ordinary pressure, but before quiescence or any checkpoint
is declared — answer one question with evidence: **is the current vector
adequate to distinguish meaningful progress?** Route the residual:

- fits an existing dimension → ordinary frontier work; no candidate.
- indicates a shared hidden cause → the Consolidation round, not a new
  dimension.
- a known dimension is unmeasurable → evaluator / observability work on its
  `channel_ref`.
- the motive itself changed → `wrong-loop` / greenfield / human authority;
  value-laden reprioritization ("polish now matters more than speed") is
  never mined autonomously.
- a genuinely new dimension is hypothesized → open **one** candidate (the
  strongest; one candidate per provisional-balance event).
- no candidate survives → the scan is recorded as adequate, provisional
  balance becomes checkpointable quiescence, and the existing halt logic
  proceeds.

A `homeostatic-checkpoint` with the vector unscanned, a candidate probe or
next-pass confirmation pending, or a newly admitted dimension requiring
continuation is invalid. The admission transaction's `checkpoint` journal
record is a commit marker, not this halt condition.

### Candidate contract

A candidate earns investigation only if it (a) explains **two independent
residuals**, or one strong impossible / external observation; (b) is not a
synonym or restatement of an existing dimension; (c) stays within the existing
motive and scope. It is an ordinary OPEN finding whose full section carries:

```yaml
dimension_candidate:
  proposed_id:
  channel_ref:
  expected_distinguishing_result:
  evidence_ref:
  guardrail_ref:
  rollback_condition:
  backfill_budget_ref: null
  dimension_outcome: pending | admitted | falsified | handoff
```

The probe is **pre-registered** (the `expected_distinguishing_result` written
before the intervention runs) and executed as an ordinary `attempt` record. A
candidate id never enters the closed `disturbed_axis` vocabulary; the probe
attempt carries one of the existing four values by the work it does:

| Probe work | `disturbed_axis` |
|---|---|
| define, split, merge, or specify a dimension | `specification-coherence` |
| build or validate its evaluator | `oracle-trustworthiness` |
| add telemetry or expose failures | `failure-legibility` |
| run a product-behavior experiment | `product-capability` |

### Outcomes and status mapping

`dimension_outcome` is a closed four-value set mapped onto the existing
finding statuses — no parallel status vocabulary:

- `pending` → `OPEN` (or `PAUSED_EXTERNAL` when blocked on budget/authority)
- `admitted` → `CLOSED_CONFIRMED`
- `falsified` → `CLOSED_CONFIRMED`
- `handoff` → `PAUSED_EXTERNAL`

**Independence gate.** A pre-registered probe permits same-pass
`CLOSED_CONFIRMED` only when its verdict comes from a tier-1 surface or a
tier-2 channel outside the candidate's change cone (`evidence-tier.md`). The
candidate may not author, mutate, or validate its own confirming channel.
Otherwise, `admitted` or `falsified` maps to `FIXED_PENDING_CONFIRMATION`
until the next pass confirms it.

### Admission (equilibrium authority only)

Admission requires all of: the pre-registered probe produced tier-1/2
evidence; a **non-null `channel_ref`** and **non-null `guardrail_ref`**; the
change is additive and reversible. Admission runs inside the existing
end-of-iteration transaction:

1. write evidence and traces first;
2. complete any overlay backfill (below);
3. update the candidate outcome, live vector, and guardrail map together;
4. append a delta-only `t: checkpoint` journal record as the commit marker —
   this **commits admission; it does not imply `stop-and-summarize`**;
5. continue: the admitted dimension is fresh pressure, worked next iteration.

Admission is authoritative iff candidate outcome, live vector, guardrail map,
checkpoint delta, and any active overlay projection agree. Interrupted before
the checkpoint record → resume reconciles from the candidate's before→after
evidence; no work may be scored against a partially admitted dimension.

### Terminal authority: never mutate the live vector

Under effective `halt-shape: terminal`, the initial frontier vector is part of
the declared workset's identity, and the episode finishes the frame it
declared:

| Situation | Handling |
|---|---|
| probe outside `declared_surfaces` | immediate `handoff` |
| probe needs new budget / authority | immediate `handoff` |
| probe inside surfaces and existing budget | at most **one** bounded probe attempt, then `handoff` |
| candidate survives its probe | `handoff` — recorded for the next declared-workset version |

A `handoff` attaches the surviving candidate to the halt summary as routing
output. Terminal probing cannot start a subordinate search loop, enlarge
`declared_surfaces`, or reset the workset identity; only a fresh `/loopgen`
derivation (a new loop id = new workset version) can admit the dimension.

### Benchmark projection parity (overlay only)

Under the benchmark-frontier overlay, admission is an atomic projection
change. The live vector cannot switch until the overlay's Pareto projection
lists the new dimension id, **every current member** carries the new metric in
its metric vector, and the cost/receipt evidence is durable (the overlay block
names the exact role fields). Partial member backfill means **not admitted
yet** — the vector remains
unchanged. Backfill cost obeys the existing frontload budget rules: free/local
scoring proceeds; one bounded paid action uses authorized-or-defer; repeated
metered evaluation requires the operative `## Budget policy` with write-ahead
spend accounting; unaffordable → the candidate stays `pending` /
`PAUSED_EXTERNAL`, never a silent overspend.

### Invariants

- `dimension_outcome: admitted` iff the live vector contains the dimension and
  the matching checkpoint delta exists.
- Under the benchmark overlay, admission additionally requires Pareto/member
  parity.
- Effective `halt-shape: terminal` implies **no live-vector delta**.
- `channel_ref: null` implies the dimension cannot be newly admitted.
- Every admitted dimension has a live guardrail reference.
- Vector ids are unique; count ≤ 8.
- Candidate ids never enter the closed `disturbed_axis` vocabulary.
- The checkpoint journal record commits admission; it does not imply
  `stop-and-summarize`.
