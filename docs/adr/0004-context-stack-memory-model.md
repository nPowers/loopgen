# ADR 0004: the context-stack memory model

- **Status:** Accepted (amended 2026-07-07, U13 hardening; amended 2026-07-17,
  U2–U3 context-lifecycle modes; amended 2026-07-22, ownership boundary)
- **Date:** 2026-07-07
- **Deciders:** provi, Claude (Fable 5)

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
(`tail -5 .loop/<loop-id>/JOURNAL.jsonl | jq -r '[.iter,.t,.ac//.id//.packet,(.verdict//.to//.question//.changed)|if (type=="object" or type=="array") then tojson else . end]|@tsv'`),
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

## Hardening amendment (U13, 2026-07-07)

A pre-ship external design review (two independent GPT-5.5 Pro extended-thinking
passes over H1–H5 hypotheses; both converged, confidence 0.74/0.76) confirmed
the direction and broke one hypothesis: prompt-level access commands plus an
authoring-time verifier prove the contract *exists*, not that a degraded
post-compaction agent *obeys* it. Amendments landed as U13:

- **Context-health check** — a bounded step-0 command ritual in the emitted
  block and the Operational core (caps, journal-tail parse, evidence pointers
  resolve, index/section agreement); a failed line routes to repair/archive
  *before* task work, or halts `derivation-gap`.
- **Tiers bind access paths, not files** — `JOURNAL.tail-20` is WORKING while
  `JOURNAL.by-key` is ON-DEMAND; the "one tier per artifact" phrasing was a
  doctrinal contradiction with the design's own split paths.
- **Index is authoritative (single-writer)** — queue `status`/counters live in
  the INDEX row only; sections carry detail; reconciliation is always from the
  index.
- **Evidence write-ahead** — the trace file is written before the journal
  record that points at it; the ≤300-char target never truncates required
  fields.
- **Structured `no-promotion`** — a closed reason set replaces free prose.
- **Pressure decay** — repeated `no-effect` consults force retire/narrow/
  re-justify; cap overflow runs a merge/retire pass before it may halt.
- **`consolidation` journal records** — a lessons layer (every ~10 iterations /
  on closure) so the tail-20 read resurfaces distilled learning, not raw
  attempts.

Considered and **declined**: a generated, overwrite-only STATUS view for human
watching. Defensible as a projection, but it adds an emit obligation and a
surface that can rot; the "one JOURNAL, no monitor file" decision stands until a
real overnight run shows the jq one-liner insufficient.

## Context-lifecycle amendment (U2–U3, 2026-07-17)

The first revisit trigger below partially fired — from research, not a
measured run: the AutoFyn → loopgen synthesis (maintainer-local research,
`.research/synthesis-autofyn-loopgen-2026-07-17.md`, gitignored) surfaced
runners whose episodes start cold (fresh context each episode) rather than
rolling one conversation through compaction. The resolution keeps this
memory model and names the lifecycle instead of forking the model:

- **The mode split.** The compiler records `context_mode_requested`
  (`fresh-episode` / `rolling-lossy` / `unknown`) with its
  `context_mode_compose_basis` in the write-once DERIVATION frontload; the
  run host resolves `context_mode_effective` in `STATE.md`.
- **Strict resolution basis.** `context_mode_resolution_basis` is a closed
  set: `operator-declared` / `runner-attested` / `unknown` — never
  observation. Model-visible history proves neither mode (a fresh runner may
  be handed replayed context; a rolling window may already be compacted);
  what the window shows is recorded separately as
  `history_visibility_observed` and never converts into a mode claim.
  `runner-attested` is reserved — no current runner attests, and no runner
  protocol is invented for it; a future runner handshake is its only
  producer.
- **One branching site.** Behavior branches on `context_mode_effective`
  alone — requested mode and observed visibility never select behavior — and
  the only branch is the Operational core's rehydration cadence:
  `rolling-lossy` → after any detected compaction; `fresh-episode` → at
  every episode start; `unknown` → **at every iteration start**. The
  `unknown` cadence is deterministic: it is derived from the mode value, not
  from inspecting whether the window looks continuous — "rehydrate whenever
  continuity is not evident" was rejected precisely because judging evidentness
  is window observation, the branch-on-visibility this ADR forbids. Unknown
  therefore takes the most conservative cadence (re-read the bounded core
  every iteration) and claims neither lifecycle.
- **What does not change.** Bounded files, one history surface, runner
  ownership, and the PINNED/WORKING/ON-DEMAND/WRITE-ONLY tiers hold under
  every mode: the tiers were never about compaction per se but about keeping
  the per-iteration read set O(1) in loop age — a fresh episode pays the
  same bounded reads at episode start that a rolling window pays after a
  compaction. `rolling-lossy` remains the modeled default; the mode
  vocabulary makes that assumption declared instead of silent.

## Ownership-boundary amendment (2026-07-22)

This ADR already made `primitives/context-stack.md` the single model and the
Operational core a bounded rehydration surface. It never said which of the two
**owns** a rule when both carry it. A clause-level parity audit of every emitted
projection — each Operational-core clause mapped to the authority obligation it
restates — found the gap was not theoretical: two rules lived **only** in the
projection.

**The boundary, stated:**

- **`context-stack` is the full semantic authority.** Every runtime rule the
  memory model governs is defined there, once.
- **The Operational core is a compact, verifier-pinned projection.** It may
  repeat essential *actions* for bounded re-entry; it may carry **no unique
  semantics**. A rule that exists only in the Operational core is a defect.
- **Every projection clause carries co-emitted `authority_refs[]`.** The
  authority must render wherever the projection renders — evaluated over the
  composition lattice (family × consult tier × overlay × effective halt variant),
  not per archetype. A projection whose authority is absent in any variant it
  emits in is not a projection; it is an orphan.

**Why promotion, not deletion.** Deleting the projection breaks the bounded
`sed -n '1,80p'` re-entry this ADR established. Making the Operational core
authoritative replicates the contract across four bodies and recreates the drift
the model exists to remove. Both rules were therefore **promoted into the
authority**, and the projections left in place:

- **Consult-tier freshness.** The per-pass "is `consult_tier_effective` still
  true for this host" check existed only as line 6 of each body's Operational
  core. Worse, its nominal authority was circular: `consult-capability` said
  *"health line 6 keeps it fresh"* — the authority delegated the rule to the
  projection, and the projection was its only home. `consult-capability` could
  not adopt it either: that block is tier-gated (42 of 56 variants) while the
  check emits in all 56, so tier-0 would lose the rule entirely. Promoted into
  the Context-health ritual, which is ungated; the run-host block now *references*
  it and re-fires on **absence or staleness**, not on mere presence.
- **Rehydration cadence.** The 2026-07-17 amendment above already *decided* the
  cadence — `rolling-lossy` → after any detected compaction; `fresh-episode` → at
  every episode start; `unknown` → at every iteration start. But only `unknown`
  had a runtime authority; the other two mappings existed solely in the four
  Operational-core intros. A decided rule with no authority is still an orphan.
  Promoted to `### Rehydration cadence`, carrying the complete table plus an
  explicit **trigger-is-not-a-basis** firewall: detecting a compaction, or what
  the window shows, *fires* the cadence for an already-resolved mode and never
  *resolves* the mode — preserving this ADR's "never observation" rule, which
  cadence language could otherwise erode by the back door.

**Parity is enforced against canonical contracts, not prose similarity.** The
cadence is a single table in the verifier checked against the authority **and**
all four projections; the freshness rule is pinned as independent semantic
conjuncts (tier-0 has no consult contract; runner change or channel failure
invalidates; re-verification is non-interactive; value **and** basis are
overwritten; only missing channels degrade) inside the boundary that already owns
run-host gating. Whitespace is normalised; the conjuncts are not, so a partial
rewrite fails rather than passes.

**Alternatives rejected:**

- **Operational core as authority.** Would put the full contract in four bodies
  and reintroduce four-way drift — the failure mode this ADR was written against.
- **Duplicated co-authority** (both surfaces authoritative, kept in sync). No
  single definition to check against; "in sync" is only ever asserted, and the
  two orphans found here are exactly what unasserted synchrony produces.

## Revisit Triggers

- A **runner-attested** `fresh-episode` runtime whose episodes are short
  enough that per-episode bootstrap reads dominate task work would pressure
  the WORKING tier's once-per-iteration economics — revisit with
  measurements, not inference (the 2026-07-17 amendment already covers the
  lifecycle vocabulary itself).
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
- Context-lifecycle amendment (U2–U3) source: the AutoFyn → loopgen research
  synthesis, `.research/synthesis-autofyn-loopgen-2026-07-17.md`
  (maintainer-local, gitignored — the five-lesson study that surfaced the
  fresh-episode runtime); landed as the U2–U3 commit series on `main`.
