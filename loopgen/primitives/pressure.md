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

Emitted into a composed prompt as the `{{PRESSURE_SURFACE}}` block **only when
≥1 pressure object exists at compose time** (authored or mined). With zero
pressure objects the placeholder is left unsubstituted and stripped by the
`composed-prompt.md` dead-section rule — a pure archetype with no seeded
pressure stays byte-identical. Otherwise this file is a derivation-time
contract, not emitted. No seed, no slope.

## The pressure object

A pressure is a structured row in `.loop/<loop-id>/STATE.md` `pressure_objects` (rendered to
`.loop/<loop-id>/PRESSURE.md`), never prose. Prose pressure is decision-inert.

| field | values | role |
|---|---|---|
| `id` | stable string | anchor for ledger + read-back |
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

`{{PRESSURE_SURFACE}}` — substituted verbatim with the block below the `---`
when the gate holds; else stripped. The active rows themselves live in
`.loop/<loop-id>/PRESSURE.md` (re-read each pass), not inlined into the prompt.

## Authoring guidance (not emitted)

- **Gate.** Populate `{{PRESSURE_SURFACE}}` iff `count(pressure_objects) ≥ 1` at
  compose; otherwise it is stripped, so a zero-pressure compose has no pressure section.
- **Compaction survival.** The *pointer* ("re-read `.loop/<loop-id>/PRESSURE.md` each
  pass") must sit in the durable prompt — it rides the runner's user-role
  continuation, which survives Codex compaction verbatim while the assistant
  summary is lossy. The *content* lives on disk. File-backed beats
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
  precondition of step 1 that step 0 extends. Without a written
  `pressure_consulted` record, "a pressure bent my plan" is prose the loop can
  fabricate or silently skip; the record turns it into an artifact a later
  pass — or an external trace review — can diff against the moves actually
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
  why the `pressure_ledger` is read for an alternating pattern across a short
  window, not just row by row. For `goal` this also surfaces as
  `partial-deadlock`; for `frontier` it feeds the structural-escalation
  bridge.
- **Why payment needs a pre-registered channel.** Flipping a row to `paid` on
  the loop's own say-so is FIXED≠CLOSED laundering — narrating an unmet
  pressure as met to escape it. Pre-registering `satisfied_by` at creation,
  and requiring an explicit re-stamp (recorded in `pressure_ledger`) to move
  to a *stronger* channel, closes the loophole where a cheap green channel
  that never exercised the pressured scope is swapped in only at payment
  time.
- **Why `stale` / `retired` carries the same evidence burden as `paid`.**
  Retiring is the easiest launder-and-shred exit: drop an inconvenient row to
  `stale`, then let it collapse out of the ledger. Requiring the same
  tier-1/2 cite that `expires` was met or the cause is externally gone (kept
  in the ledger summary) is what blocks that exit; without it, the
  paid-laundering escape just reroutes through `stale`.
- **Ledger bound, precisely.** The ledger is bounded by `pressure-cap`·`K` +
  `M` + 1: the in-force set (`active` + `hardened`) is capped at
  `pressure-cap` (default 12, frontload-tunable alongside stuck-attempt-N /
  quiet-signal-N when pressure is active), each row carrying at most `K`
  (default 5) recent transitions before older in-flight transitions collapse
  to a count + last state; a row that reaches a terminal status (`paid` /
  `stale` / `retired`) collapses immediately to a one-line summary (id, final
  status, evidence), and summaries beyond the most recent `M` (default 50)
  collapse further to an aggregate count. No status escapes both caps.
  `.loop/<loop-id>/PRESSURE.md`'s header is re-rendered from this rule set
  every pass, so it carries the full arithmetic and survives even when the
  emitted block below is summarized away by compaction — the emitted block
  states only the bound.

---

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

**Record the read-back.** Each pass, write a `pressure_consulted` record to
`.loop/<loop-id>/STATE.md`: every active row id mapped to the plan element it
bent, or `no-effect: <reason>`. A pass with no `pressure_consulted` record has
not completed step 0.

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
`expires`/reopen condition. Record its creation in `pressure_ledger`.

When the `pressure_ledger` shows backpressure alternating between the same
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
  adopted only by an explicit re-stamp recorded in `pressure_ledger`.
- → `stale` / retired carries the **same** evidence burden as `paid`: cite the
  tier-1/2 signal that proves `expires` met or the cause externally gone —
  never the loop's own say-so.
- → `hardened` (soft → `constraint`) only when the same soft pressure kept
  costing the same move across iterations, recorded with that evidence. A
  `hardened` row is still **in force**: re-tested every pass exactly like an
  `active` `constraint`, and can still be demoted or retired when its reopen
  condition is met.

Record every transition in `.loop/<loop-id>/STATE.md` `pressure_ledger`, each
with its evidence cite. A new `source: backpressure` row scoped to an
already-pressured scope **merges into** the existing row, never appends a
duplicate. More than `pressure-cap` in-force rows (`active` or `hardened`;
default 12, frontload-tunable), or a row that keeps oscillating its mode
(`constraint` ↔ `burden`) or re-stamping without ever reaching a terminal
status (`paid` / `stale` / `retired`), is itself a halt / checkpoint cause (a
`derivation-gap`, or `frontier`'s `checkpoint_reason`), not silent growth.
`.loop/<loop-id>/PRESSURE.md`'s header carries the full ledger-cap arithmetic
(per-row transition cap, terminal-row collapse) re-rendered each pass, so the
discipline survives even when this block is summarized away.
