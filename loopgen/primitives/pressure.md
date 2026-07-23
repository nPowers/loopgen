# pressure (shared primitive)

## Purpose

Pressure is the universal force every loop runs inside: contextual **salience
with consequence** that bends the next move *before* the gate. A constraint is a
wall (a move is illegal); pressure is a slope (a move is allowed but uphill,
costlier, or now owes an explanation). The four archetype queue artifacts —
acceptance inventory (`goal`), storyboard (`story`), rubric+intent
(`greenfield`), findings ledger (`frontier`) — are all pressure surfaces; this
primitive names the contract they share. `primitives/pressure-accounting.md` is
the `frontier` projection of this object, not a separate concept.

## Include when

**Always emitted.** Every composed prompt carries the `{{PRESSURE_SURFACE}}`
block as its pinned pressure HUD — there is **no compose-time gate**. Seeded or
mined rows are optional (a fresh loop may start with an empty in-force set), but
the surface itself is unconditional: the mandatory promotion triggers in the
emitted block are what keep it from going dead, so a loop that first discovers a
pressure mid-run already has a place in context to record it. This reverses the
former ≥1-object gate, whose measured failure was a `PRESSURE.md` that stayed a
7-line placeholder while the loop's real pressures lived in checkpoints and
`next_action` (ADR 0004; inbox note `2026-07-06-pressure-primitive-placeholder`,
Option A). This file is also a derivation-time contract: read every authoring run
so the frontload latent-pressure mining step has the modes + object schema.

## The pressure object

A pressure is a structured row in `.loop/<loop-id>/STATE.md` `pressure_objects` (rendered to
`.loop/<loop-id>/PRESSURE.md`), never prose. Prose pressure is decision-inert.

| field | values | role |
|---|---|---|
| `id` | stable string | anchor for its `pressure`/`consult` journal records + read-back |
| `source` | `authored` · `mined` · `backpressure` · `overlay` | who put it in the field (human seed · latent-mined · fed back from an outcome · seeded by a composition overlay as a fixed contract, e.g. benchmark-frontier oracle-integrity — provenance is the overlay activation + bound object, exempt from the `mined` low/salience entry rule) |
| `scope` | path / surface / criterion / dimension | what it covers |
| `mode` | `salience` · `preference` · `burden` · `constraint` | how it bends a move (authority on the surface) |
| `strength` | `low` · `medium` · `high` | how hard it tilts |
| `satisfied_by` | an `evidence-tier.md` tier-1/2 signal | what cashes it out — never the loop's own prose |
| `on_violation` | `owes_proof` · `owes_explanation` · `blocks` | the consequence half |
| `expires` | iteration / condition | mandatory decay; no row without one |
| `status` | `active` → `paid` · `hardened` · `stale` · `retired` | lifecycle |

**Modes**, weakest to strongest: `salience` (stay in attention) · `preference`
(favor unless reason not to) · `burden` (allowed but now owes proof) ·
`constraint` (hardened wall). When modes conflict on the same scope the stronger
wins: **`constraint` > `burden` > `preference` > `salience`**. Only `constraint`
is a wall; the other three are slopes.

## Placeholders

`{{PRESSURE_SURFACE}}` — **always** substituted verbatim with the block below the
`---` (no gate). The active rows themselves live in
`.loop/<loop-id>/PRESSURE.md` (re-read each pass), not inlined into the prompt;
the emitted block carries the row schema, the re-read contract, the mode law, the
mandatory promotion triggers, and the backpressure instruction.

## Authoring guidance (not emitted)

- **Always on.** Emit `{{PRESSURE_SURFACE}}` in every composed prompt regardless
  of `count(pressure_objects)`; a zero-pressure compose still carries the HUD and
  its promotion triggers, so the surface is live the moment the loop mints its
  first row. The in-force set may start empty; the block may not be absent.
- **Compaction recovery.** The *pointer* ("re-read `.loop/<loop-id>/PRESSURE.md`
  each pass") must sit in the durable prompt. The runner's user-role
  continuation carries only the bare kick-off, so the agent must rehydrate the
  Operational core on its declared cadence to recover this instruction after
  compaction. The *content* lives on disk. File-backed beats
  context-trusted.
- **Salience without consequence is bloat; consequence without salience is
  review after the whistle.** Every row carries both halves or it is cut.
- **Re-render, never trust the file directly.** `.loop/<loop-id>/PRESSURE.md` is
  a pure projection of `.loop/<loop-id>/STATE.md` `pressure_objects`, re-derived
  every pass rather than read as a standalone store. A crash between the STATE
  mutation and the render then self-heals on the next re-render instead of
  stranding the loop on a stale half; trusting the file directly would let a
  torn write persist. It is not a second artifact — where a frontier
  checkpoint contract says to keep pressure in the findings ledger /
  `.loop/<loop-id>/STATE.md` and not invent a new artifact, `PRESSURE.md` is
  that same store rendered, not a competing one.
- **Write-ahead, not carried in context.** Flushing every pressure mutation to
  `.loop/<loop-id>/STATE.md` and re-rendering `.loop/<loop-id>/PRESSURE.md`
  within the same tool-call sequence — never holding a pending write across a
  call — is the budget spend-ledger's write-ahead discipline applied to
  pressure state: a compaction boundary can drop context-held state, and the
  surviving re-read pointer would then resume against a stale field with no
  signal a write was lost.
- **Why the read-back is recorded.** The numbered iteration protocol in the
  body does not list `.loop/<loop-id>/PRESSURE.md`; the pressure read is a
  precondition of step 1 that step 0 extends. Without a written `consult`
  journal record (`.loop/<loop-id>/JOURNAL.jsonl` — the record type that replaces
  the former `pressure_consulted` STATE key), "a pressure bent my plan" is prose
  the loop can fabricate or silently skip; the record turns it into an artifact a
  later pass — or an external trace review — can diff against the moves actually
  made.
- **Why walls fail open.** The loop self-polices these rules, so a neglected
  `constraint` must un-brick rather than stay locked. The alternative
  (fail-closed) would let a stale or false-negative wall permanently brick the
  loop with no human in the loop to release it — the only safe default is one
  where neglect errs toward the slope, never toward the locked door.
- **Why constraint-deadlock escalates.** Two independent walls that jointly
  empty the legal-move set toward an `OPEN` criterion is not a stuck criterion
  to keep re-selecting; only a human can relax or re-scope one of the walls,
  so the loop names both and stops rather than mislabeling it `STUCK`.
- **Backpressure closes the loop.** Turning a failed verify/eval/probe/review
  into a pressure row for the next pass is how late consequence becomes early
  pressure: the next iteration starts already bent away from the failure
  instead of re-discovering it cold. The loop improves not because the model
  got smarter but because failure stops being wasted.
- **Coupled regression.** Backpressure can ping-pong: fixing scope A regresses
  scope B (minting backpressure on B), the next pass fixes B and regresses A,
  and the loop runs all night minting alternating rows. Each row is a real
  tier-1/2 failure, so no per-criterion stuck counter ever trips — a
  *different* scope fails each pass, and some move is always legal — the
  oscillation itself is the failure and nothing per-criterion sees it. That is
  why the `pressure` journal records are read (`jq` over
  `.loop/<loop-id>/JOURNAL.jsonl`) for an alternating pattern across a short
  window of recent passes, not just row by row. For `goal` this also surfaces as
  `partial-deadlock`; for `frontier` it feeds the structural-escalation
  bridge.
- **Why consolidation reads the whole field.** Everything above is per-row
  hygiene, and per-row hygiene has a measured blind spot: in the dota-market
  pooler incident four rows were each individually justified — durable
  receipts, plan coverage, proof-path gaps, a local-pass/prod-disagree
  salience — while their shared cause (transaction transport semantics) sat one
  layer below anything any single row scoped. Rows are maintained one at a
  time; a field is read all at once. The consolidation round
  (`primitives/context-stack.md`) is that read, and the emitted field-read
  block below is its pressure-side half: clustering, debt-conserving merge,
  and the substrate stamp.
- **Why payment needs a pre-registered channel.** Flipping a row to `paid` on
  the loop's own say-so is FIXED≠CLOSED laundering — narrating an unmet
  pressure as met to escape it. Pre-registering `satisfied_by` at creation,
  and requiring an explicit re-stamp (recorded as a `pressure` journal record)
  to move to a *stronger* channel, closes the loophole where a cheap green channel
  that never exercised the pressured scope is swapped in only at payment
  time.
- **Why `stale` / `retired` carries the same evidence burden as `paid`.**
  Retiring is the easiest launder-and-shred exit: drop an inconvenient row to
  `stale`, then let it drop out of the in-force set. Requiring the same
  tier-1/2 cite that `expires` was met or the cause is externally gone (kept in
  the `pressure` journal record for that transition) is what blocks that exit;
  without it, the paid-laundering escape just reroutes through `stale`.
- **Bound, precisely (two surfaces).** Pressure now lives across two tiers, each
  with its own bound. **In-force set (PINNED):** the `active` + `hardened` rows in
  `.loop/<loop-id>/STATE.md` `pressure_objects` are capped at `pressure-cap`
  (default 12, frontload-tunable alongside stuck-attempt-N / quiet-signal-N when
  pressure is active) — the only pressure surface re-read whole every pass, and
  bounded by construction. **Transition history (ON-DEMAND):** every lifecycle
  transition is a `pressure` journal record and every read-back a `consult`
  record in `.loop/<loop-id>/JOURNAL.jsonl` — append-only, one line each, read
  per pass only as `tail -n 20` and otherwise by `jq` key, so it carries no
  per-pass re-read tax no matter how long the loop runs. This is what the old
  `pressure_ledger`'s `K`/`M` collapse arithmetic bought, now bought instead by
  the journal's tail-N + keyed-read discipline (`primitives/context-stack.md`).
  `.loop/<loop-id>/PRESSURE.md`'s header is re-rendered every pass and carries
  the in-force cap, the journal pointer, and the last-consolidation stamp
  (`last consolidation: iter N · next due ~N+10`), so the discipline survives
  even when the emitted block below is summarized away by compaction — and the
  HUD itself shows when the loop last read its field.

---

## Pressure rows

Every pressure is a structured row in `.loop/<loop-id>/STATE.md` `pressure_objects`
(the in-force set, `active` / `hardened` only, bounded ≤ `pressure-cap`; rendered
to `.loop/<loop-id>/PRESSURE.md`), never prose — prose pressure is decision-inert.
Each row carries: `id` · `source` (`authored` / `mined` / `backpressure` /
`overlay`) · `scope` · `mode` (`salience` / `preference` / `burden` /
`constraint`) · `strength` (`low` / `medium` / `high`) · `satisfied_by` (a
tier-1/2 signal from `evidence-tier.md`, never the loop's own prose) ·
`on_violation` (`owes_proof` / `owes_explanation` / `blocks`) · `expires`
(mandatory decay — no row without one) · `status` (`active` → `paid` /
`hardened` / `stale` / `retired`). A row whose `satisfied_by` cannot cite tier-1/2
evidence is cut, not rendered. Lifecycle transitions and read-backs are **not**
stored here — they are `pressure` and `consult` records in
`.loop/<loop-id>/JOURNAL.jsonl`.

## Pressure weather

**Step 0, every pass, before step 1:** re-render `.loop/<loop-id>/PRESSURE.md`
from `.loop/<loop-id>/STATE.md` `pressure_objects` (the source of truth), read
it, and run its maintenance pass below. Flush every pressure mutation — a new
backpressure row, any lifecycle transition — to `.loop/<loop-id>/STATE.md` and
re-render `.loop/<loop-id>/PRESSURE.md` within the same tool-call sequence
that computed it, before the next decision; never carry a pending pressure
write across a tool call.

Let each active row tilt the plan while you are still planning, before any
gate:

- `salience` — keep it in attention; name it in the plan.
- `preference` — favor the move it points to unless you have a reason not to.
- `burden` — the move is allowed but now owes proof; cite tier-1/2 evidence
  (`evidence-tier.md`) or do not claim it.
- `constraint` — a wall; the move is refused.

When modes conflict on one scope, the stronger wins: `constraint` > `burden` >
`preference` > `salience`. A row whose `satisfied_by` cannot cite tier-1/2
evidence is cut, not rendered.

**Record the read-back.** Each pass, append a `consult` record to
`.loop/<loop-id>/JOURNAL.jsonl`: every active row id mapped to the plan element
it bent, or `no-effect: <reason>`. A pass with no `consult` record has not
completed step 0. **Repeated no-effect is a decay signal:** a row logging
`no-effect` on ~3 consecutive consults must be retired, narrowed, or explicitly
re-justified in that pass's `consult` record — under the same evidence burden as
any lifecycle transition. A stale row with consequence is worse than no row: it
bends every plan while wearing the authority of a live invariant.

**Mandatory promotion trigger.** Every failed verify, probe, eval, or review
this pass **either** mints a `source: backpressure` row into
`.loop/<loop-id>/STATE.md` `pressure_objects` (it renders into `PRESSURE.md`)
**or** appends a `consult` record carrying `no-promotion: <reason>` — where
`<reason>` is one of the closed set `duplicate-of:<id>` · `covered-by:<id>` ·
`out-of-scope` · `transient-flake` · `criterion-local` ·
`reverted-before-effect`, never free prose (free-text reasons decay into
compliance dust that satisfies the letter of this trigger while carrying
nothing). Silence is a protocol violation: a failure
that neither mints a row nor logs a reasoned no-promotion is late consequence the
next pass rediscovers cold — the exact dead-`PRESSURE.md` failure this always-on
surface exists to prevent. This obligation is what makes the HUD carry the loop's
real pressures instead of an empty placeholder.

**Maintain walls or they fall.** Each pass, re-test every enforced
`constraint` row — `status: active` **or** `hardened`, both still in force —
against its reopen / `expires` condition before treating it as a wall. A
`constraint` not re-tested this pass is read as a `burden`, never as a wall.

Pressure shapes **how** a move is chosen, never **whether** a gate is met. No
mode — not even `constraint` — can deprioritize an `OPEN` acceptance
criterion, suppress a required verify, or let an archetype halt with its
terminal contract unmet. The archetype gate outranks every pressure.

**Constraint deadlock escalates.** When two `constraint` rows on different but
overlapping scopes make the set of legal moves toward an `OPEN` gate empty, do
not spin re-selecting the criterion or mislabel it `STUCK`: that is a
`constraint-deadlock`, which routes to `genuine-escalate` — a human must relax
or re-scope one wall. Name both constraints in the halt summary.

## Backpressure

When an attempt resolves against the world — a failed verify, eval, probe, or
review — append a `source: backpressure` object to `.loop/<loop-id>/STATE.md`
`pressure_objects` (it renders into `.loop/<loop-id>/PRESSURE.md`), scoped to
what failed, in the **softest** mode the failure justifies — default `burden`,
never `constraint` from a single signal. A backpressure `constraint` requires
the failure reproduced on a tier-1/2 channel, and even then carries an
`expires`/reopen condition. Record its creation as a `pressure` journal record.
(A failure that mints no row must instead be logged as a `no-promotion` `consult`
record — see the mandatory promotion trigger above.)

When the `pressure` journal records show backpressure alternating between the same
two (or N) scopes over a short window of recent passes, with no net
criterion-count progress, that is a **coupled-regression** signal, not endless
work: halt with `genuine-escalate` (reason `coupled-regression`), naming the
coupled scopes.

## Lifecycle

Each pass, retire what no longer earns its place — a transition is a claim
that owes evidence, exactly like a queue row:

- → `paid` **only** when `satisfied_by` cites fresh tier-1/2 evidence produced
  this run, on the channel **pre-registered at creation** — never a weaker or
  different one chosen at payment time. A strictly *stronger* channel may be
  adopted only by an explicit re-stamp recorded as a `pressure` journal record.
- → `stale` / retired carries the **same** evidence burden as `paid`: cite the
  tier-1/2 signal that proves `expires` met or the cause externally gone —
  never the loop's own say-so.
- → `hardened` (soft → `constraint`) only when the same soft pressure kept
  costing the same move across iterations, recorded with that evidence. A
  `hardened` row is still **in force**: re-tested every pass exactly like an
  `active` `constraint`, and can still be demoted or retired when its reopen
  condition is met.

Record every transition as a `pressure` journal record in
`.loop/<loop-id>/JOURNAL.jsonl`, each with its evidence cite; the in-force row in
`.loop/<loop-id>/STATE.md` `pressure_objects` is rewritten in place to its new
status (a row that reaches a terminal status leaves the in-force set entirely —
its history stays in the journal). A new `source: backpressure` row scoped to an
already-pressured scope **merges into** the existing row, never appends a
duplicate. On `pressure-cap` overflow (more than the cap in force; default 12,
frontload-tunable), run one merge/retire pass first — merge same-scope rows,
retire rows with repeated `no-effect` consults or met `expires` conditions
(evidence burden unchanged) — and only if the set is *still* over cap halt on
it; a loop that halts because its pressure bookkeeping is noisy, rather than
because the task is blocked, has inverted the tool. A row that keeps
oscillating its mode (`constraint` ↔ `burden`) or re-stamping without ever
reaching a terminal status (`paid` / `stale` / `retired`) is likewise a halt /
checkpoint cause (a `derivation-gap`, or `frontier`'s `checkpoint_reason`), not
silent growth.
`.loop/<loop-id>/PRESSURE.md`'s header carries the in-force cap, the journal
pointer, and the last-consolidation stamp (`last consolidation: iter N · next
due ~N+10`), re-rendered each pass, so the discipline survives even when this
block is summarized away.

## Consolidation — the field read

At the consolidation round (scheduled or forced — triggers and procedure in
the Context stack's Consolidation section), read the in-force set as **one
field**, not row by row: which rows cluster around a shared suspected cause?
Per-row maintenance cannot see a cause that several individually-justified
rows share.

- **Merge across scopes, conserving the debt.** Rows clustered at a shared
  cause merge into a single row scoped at that cause. The merged row inherits
  the **strongest** mode and strength among its members and the **union** of
  their pre-registered `satisfied_by` channels — paying it still means paying
  those channels; a merge is never a launder and never a retirement. Each
  absorbed row is recorded as a `pressure` journal record with
  `merged-into: <id>`; its unpaid obligation survives in the merged row.
- **Stamp the substrate.** When the cluster's members were each locally
  correct — paid or verified on their own channels — yet the target did not
  move, set `suspected_substrate: <layer>` on the merged row and in the
  `consolidation` record: the violated contract likely sits below the code
  (transport, pooler mode, driver semantics, deploy/env parity, service
  identity). That stamp is what routes the next pass at the layer instead of
  the symptoms.
- **Promote the lesson.** What the field reading taught goes in the
  `consolidation` record's `lesson`; a lesson that must keep bending future
  passes is minted (or re-scoped) as a row — the round is a mint/merge channel,
  never a quiet exit for rows that were losing their argument.
