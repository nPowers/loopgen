# ADR 0004: the context-stack memory model

- **Status:** Accepted
- **Date:** 2026-07-07
- **Deciders:** provi, Claude (Opus 4.8)

## Context

A loop composed by `/loopgen` runs inside a runner (`/goal`) whose behaviour
loopgen had never explicitly modeled: **one continuous conversation** into which
the runner re-sends the *same* bare-pointer kick-off every iteration. User-role
messages survive compaction verbatim; assistant turns and tool outputs get
lossy-summarized whenever the window nears its ceiling. The window therefore is a
**rolling lossy cache**, not fresh context per turn — a fact held only in context
can vanish at any compaction boundary, while a fact held in a file costs tokens
every time it is re-read.

A 33-hour Codex `/goal` run in dota-market (session
`019f3110-3d25-7861-aefb-e2c5cf3f2ef3`, `.loop/004-market-movement/`) measured
what loopgen loops actually cost against that runtime:

- **51 context compactions** over the run; mean window ~148k of a 258k ceiling,
  compacting at ~240k.
- **~2.3M tokens of pure scaffolding traffic** — re-reading state/ledgers/queues,
  not producing the deliverable.
- **More tokens spent writing ledgers than writing the fix** — 288k on ledger
  prose vs 197k on the actual change.
- **`STATE.md` reached 105 KB**, 88% of it a single unbounded `attempt_log` — an
  append-only history masquerading as live status.
- **The mandatory per-iteration read-set grew 4.25×** over the run
  (8,821 → 37,537 tokens) because the iteration protocol mandated whole-file
  reads of files that only grow with loop age.
- **`PRESSURE.md` was a dead 7-line file** that never carried any of the loop's
  four real pressures — the pressure surface was gated off and never populated.

The root causes were loopgen spec gaps, not runner bugs: whole-file read mandates
on unbounded files; the growth-cap discipline wired into only 1 of 4 archetype
bodies; five `STATE.md` keys that were append-only history in disguise
(`attempt_log`, `pressure_ledger`, `pressure_consulted`, `oracle_change_notes`,
and the derivation record); a compose-time gate that let the pressure surface be
stripped to nothing; and no artifact of the real runtime anywhere in the skill.

## Decision

Rebuild the skill around the runtime: **the context window is a rolling lossy
cache; files are the durable memory; every emitted artifact is assigned exactly
one tier, a hard bound, and a keyed access convention so the loop reads keys, not
files.** The model is defined once in `primitives/context-stack.md` (authoring
rationale above the `---`, the emitted contract below it, INCLUDEd by all four
archetype bodies) and enforced by `tools/verify_loopgen_contracts.py`.

**1. Four tiers, one per artifact.**

| Tier | Contract | Bound |
|---|---|---|
| **PINNED** | re-read every pass (step 0); small enough to live in the window permanently — `PRESSURE.md`, `STATE.md` | fixed schemas; STATE ≤ ~50 lines; in-force pressure set ≤ `pressure-cap` (12) |
| **WORKING** | read once at iteration start; O(1) regardless of loop age — the queue artifact's index + OPEN/current rows, `tail -n 20 JOURNAL.jsonl` | index+sections addressing; `closed-retain-N`; tail-N |
| **ON-DEMAND** | keyed reads only, never full-file — journal history by key (`jq`), `archive/*`, `DERIVATION.md`, traces | documented access commands |
| **WRITE-ONLY** | the loop writes, never re-reads — `VERIFY.md` (terminal only), journal `checkpoint` records | delta-only ("unchanged since iter N") |

**2. `STATE.md` splits from `JOURNAL.jsonl` along the live/history seam.**
`STATE.md` becomes **live status only** — fixed keys, one line each,
rewrite-in-place, **no history, ever**. Every append-only stream it used to carry
moves to a single `JOURNAL.jsonl`: one typed record per line, target ≤300 chars,
evidence carried as pointers not inlined blobs. The **in-force** pressure set
(`active`/`hardened` rows, bounded ≤ `pressure-cap`) stays in `STATE.md` because
it is legitimately live status; only the unbounded **transition histories**
(`pressure_ledger` → `pressure` records, `pressure_consulted` → `consult`
records) move to the journal. The write-once derivation record
(`primitive_bundle`, `divergences`, `overlays`, `derivation_read_set`,
`frontload`) moves out of `STATE.md` into a new write-once `DERIVATION.md`, read
on demand (diagnostic / resume), never per pass.

**3. One history surface — `JOURNAL.jsonl` — and no monitor file.** A
CHECKPOINTS-style human-watch file is named an anti-pattern: it is a second
history surface that drifts from the first. Humans watch the loop with a
documented one-liner over the journal
(`tail -5 .loop/<loop-id>/JOURNAL.jsonl | jq -r '[.iter,.t,.ac//.id,.verdict//.to//.changed]|@tsv'`),
and the loop records delta-only `checkpoint` records for status changes worth a
timestamp. No separate monitor artifact exists in the contract.

**4. The pressure surface is always-on.** The ≥1-object compose gate is removed.
`PRESSURE.md` is emitted in every composed prompt as the pinned HUD — a
projection of `STATE.md` `pressure_objects`, re-rendered and read at step 0 every
pass. Promotion becomes **mandatory**: every failed verify / probe / review a
pass produces either mints a backpressure row or appends an explicit `consult`
record carrying `no-promotion: <reason>`. Silence is a protocol violation. (This
implements inbox note `2026-07-06-pressure-primitive-placeholder`, Option A.) The
`{{SUBAGENT_PATTERNS}}` block keeps its `consult-tier ≥ 1` gate — it remains the
reference example of a compose-gated block.

**5. Addressability — read keys, not files.** The composed `PROMPT.md` carries a
**Context budget** table (file → tier → cap → access command → human watch
command) and a **budget assertion**: a PINNED or WORKING read that exceeds its
declared cap means the file discipline is broken — archive or collapse first,
symmetric with the oracle-integrity checks. `PROMPT.md` also gains an
always-emitted **Operational core** near the top (protocol skeleton + context
budget + halt-cause list) so post-compaction rehydration is a bounded
`sed -n '1,80p'`, not a two-chunk whole-file read. Queue artifacts gain an index
table + one `## <id>` section per row, so the per-pass read is
index + OPEN/current sections, never the whole growing file.

## Rationale

- **Live status and history have different lifetimes.** Conflating them in one
  growing `STATE.md` is what produced the 105 KB file and the 4.25× read-set
  growth. Splitting them lets the PINNED surface stay small forever while history
  accumulates in a tier that is never read whole.
- **A bound the runner cannot see is a bound that does not exist.** Wiring the
  growth discipline into every body (not 1 of 4) and stating the cap arithmetic
  in the emitted prompt is what makes the O(1) read-set real rather than
  aspirational.
- **Pressure that can be gated to nothing carries nothing.** The dead
  `PRESSURE.md` is the direct evidence; an always-on HUD with mandatory promotion
  triggers guarantees each iteration's context contains the loop's real slopes.
- **One keyed history beats four overlapping prose files.** `jq` over one typed
  stream replaces re-reading four divergent ledgers, and the single append point
  removes the drift between them.

## Consequences

Positive:

- Per-iteration ceremony drops from ~19k+ tokens (growing with loop age) to a
  projected **~6.5k flat** read-set + **~1k flat** write ceremony (see Projected
  token model below), because every re-read surface is now O(1) in loop age.
- History becomes one keyed, capped journal instead of four overlapping prose
  files; pressure is guaranteed a place in every iteration's context.
- The verifier enforces the model, so the next archetype body cannot silently
  regress it.

Negative:

- One more common file (`JOURNAL.jsonl`) and one more (`DERIVATION.md`) in the
  emitted set; the schema is denser to author.
- Existing `.loop/` dirs from before this change carry the old `STATE.md` shape;
  they are not migrated (execution scratch, per ADR 0003) — Diagnostic mode
  recognizes the old shape when retrofitting a live loop.

## Projected token model

The refactor's target is a per-iteration mandatory read-set that is **flat in
loop age**, replacing the measured 8,821 → 37,537-token growth. These numbers are
a projection derived from the contract caps, **not** a re-measured 33h run (the
spec change does not make reproducing that run feasible here); each bound is what
holds the estimate regardless of iteration count, and the verifier enforces the
bound.

**Per-iteration read-set (flat):**

- PINNED ≈ 1.5k tok — `STATE.md` (fixed keys, ≤ ~50 lines) + `PRESSURE.md`
  (in-force set ≤ `pressure-cap` = 12 rows + header). Bounded by fixed schema +
  the pressure cap.
- WORKING ≈ 5k tok — the queue **index** (`closed-retain-N` = 20 recent-closed +
  the OPEN rows) + the handful of OPEN / current `## <id>` sections actually acted
  on + `tail -n 20 JOURNAL.jsonl` (≤300 chars/record ≈ 1.5k). Bounded by
  index+sections addressing + tail-N.
- **Total ≈ 6.5k tok, flat** vs the measured 8.8k → 37.5k growing (the mandatory
  read-set grew 4.25× over the baseline run).

**Per-iteration write ceremony ≈ 1k tok** — one `attempt` record (≈75 tok) + an
in-place `STATE.md` rewrite + a `pressure`/`consult` record + the `PRESSURE.md`
re-render — vs the measured ~4k, and critically the write no longer *grows*:
history appends to `JOURNAL.jsonl` (never re-read whole) instead of inflating a
re-read `STATE.md` (which reached 105 KB, 88% one unbounded `attempt_log`).

The number that matters is the slope, not the constant: every re-read surface is
O(1) in loop age, so a 300-iteration loop pays the same per-pass ceremony as a
3-iteration one. `bodies_use_tiered_reads` and
`state_key_skill_context_stack_mirror` (in `tools/verify_loopgen_contracts.py`)
enforce the caps that make this hold.

## Revisit Triggers

- A runtime whose context is genuinely fresh per turn (no rolling cache) would
  invalidate the PINNED/WORKING distinction and warrant a different model.
- A measured loop whose journal itself becomes a re-read hot-spot despite the
  tail-N / keyed-read contract would justify sharding the history surface.

## References

- Design artifact (human-facing spec, memory-location paradigm):
  https://claude.ai/code/artifact/85ea880b-7712-4e28-af92-78a70ddd2cb8
- Motivating evidence: token-consumption audit of Codex session
  `019f3110-3d25-7861-aefb-e2c5cf3f2ef3` (dota-market
  `.loop/004-market-movement/`, 33h run).
- Implements inbox note `.inbox/2026-07-06-pressure-primitive-placeholder.md`
  (always-on pressure, Option A).
- Lineage anchor: the context-stack refactor commit series on `main` (units
  U1–U12); `primitives/context-stack.md` is the model's single in-tree source.
- Builds on ADR 0003 (loop records live in gitignored `.loop/<loop-id>/`).
