# context-stack (shared primitive)

## Purpose

The memory model every loop runs inside. A loop's runner (`/goal`) executes
**one continuous conversation** and re-sends the *same* bare-pointer kick-off
each iteration; the context window is a **rolling lossy cache** — user-role text
survives compaction verbatim, assistant turns and tool outputs are
lossy-summarized near the ceiling — and **files are the durable memory**. A fact
held only in context can vanish at any compaction boundary; a fact held in a file
costs tokens every time it is re-read. This primitive gives every emitted
artifact exactly one **tier**, a hard **bound**, and a keyed **access
convention**, so the loop reads keys, not files, and its per-iteration ceremony
stays flat instead of growing with loop age. It is the shared home for the
`STATE.md` register, the `JOURNAL.jsonl` history schema, the `DERIVATION.md`
contract, and the context-budget assertion — collapsing what was four divergent
per-body STATE-key boilerplates into one edit site.

The full motivating measurement (a 33h dota-market run: 51 compactions, a 105 KB
`STATE.md`, a read-set that grew 4.25×, a dead `PRESSURE.md`) and the design
decisions live in ADR 0004.

## Include when

Emitted into **every** composed prompt — all four archetype bodies carry
`{{INCLUDE primitives/context-stack.md}}` in their Artifacts-to-maintain section.
The memory model is universal, so unlike `pressure` / `subagent-patterns` this
block is **never gated**: there is no runtime in which the context window is not
a lossy cache. Read at derivation time by every authoring run (it is a Tier-2
composition read in `SKILL.md`).

## The runtime being modeled

- `/goal` re-sends the same kick-off pointer into one conversation every
  iteration. The kick-off carries no instruction content; every rule lives in
  `.loop/<loop-id>/PROMPT.md`, which the runner re-reads.
- The window runs pinned near its ceiling (measured mean ~148k of 258k,
  compacting at ~240k). Context-held facts can be summarized away at any
  boundary; file-held facts persist but are re-paid per read.
- Therefore **every fact gets one canonical home and a declared re-read
  cadence.** A file that is re-read whole every pass must be bounded independent
  of loop age, or the read-set grows without limit. A file that only grows must
  never be on the per-pass re-read path.

## The four tiers

Every emitted artifact is assigned **exactly one** tier:

- **PINNED** — re-read every pass at step 0; small enough to live in the window
  permanently. Bounded by fixed schemas, not by loop age.
- **WORKING** — read once at iteration start; the read cost is O(1) regardless of
  how long the loop has run, because the surface is an index + the live rows, not
  the whole file.
- **ON-DEMAND** — read only by key, never whole-file: the rare pass that needs
  prior art, plus human review and diagnostics.
- **WRITE-ONLY** — the loop writes it and never re-reads it within the loop; it
  exists for the terminal report or for external watchers.

## Design rationale (not emitted)

- **Live status and history have different lifetimes.** Mixing them in one
  growing `STATE.md` is what produced the 105 KB file and the 4.25× read-set
  growth. The split keeps the PINNED surface small forever while history
  accumulates where it is never read whole.
- **In-force pressure stays PINNED; transitions go to the journal.** The
  `active`/`hardened` rows are legitimately live status and are bounded by
  `pressure-cap`, so they stay in `STATE.md` (the pressure re-render / crash-
  recovery doctrine in `pressure.md` depends on `STATE.md` being the source of
  truth). Only the unbounded transition/consult histories move to the journal —
  the doctrine survives untouched.
- **One history surface, no monitor file.** A CHECKPOINTS-style human-watch file
  is a second history that drifts from the first; it is an anti-pattern. Humans
  watch via the journal one-liner; the loop records delta-only `checkpoint`
  records.
- **A bound the runner cannot see does not exist.** The cap arithmetic and access
  commands are stated in the *emitted* block, not just here, so the O(1) read-set
  is enforced at runtime rather than merely intended.

---

## Context stack — the memory model

Your runner runs **one continuous conversation** and re-sends this prompt every
iteration; the context window is a **rolling lossy cache** (user-role text
survives compaction, assistant/tool output is summarized away near the ceiling)
and **the files under `.loop/<loop-id>/` are the durable memory**. Read keys, not
files. Every artifact below has exactly one tier and a hard bound; honor its
access command and never promote an ON-DEMAND read to a per-pass whole-file read.

### Tier contract

| Tier | When read | Members | Bound |
|---|---|---|---|
| **PINNED** | every pass, step 0 | `PRESSURE.md` (HUD), `STATE.md` (live status) | fixed schemas; `STATE.md` ≤ ~50 lines; in-force pressure set ≤ `pressure-cap` (default 12) |
| **WORKING** | once at iteration start | the queue artifact's **index + OPEN/current sections**; `tail -n 20 .loop/<loop-id>/JOURNAL.jsonl` | index+sections addressing; `closed-retain-N` (default 20); tail-N |
| **ON-DEMAND** | keyed reads only, never whole-file | `JOURNAL.jsonl` history by key (`jq`), `.loop/<loop-id>/archive/*`, `DERIVATION.md`, trace/metric targets | the documented access command below |
| **WRITE-ONLY** | written, never re-read in-loop | `VERIFY.md` (terminal final-verify only), journal `checkpoint` records | delta-only ("unchanged since iter N") |

### `STATE.md` — PINNED live status (fixed keys, rewrite-in-place, **no history, ever**)

`STATE.md` holds **only** current live status: one line per key, overwritten in
place. It is never appended to. Anything that accumulates across iterations
belongs in `JOURNAL.jsonl`, not here. If `STATE.md` grows past ~50 lines the
discipline is broken — a history stream has leaked in; move it to the journal.

Common keys, every archetype:

- `archetype`, `identity`
- `consult_tier`, `evaluator_tier`
- `artifacts` (`{canonical, repo_aliases}`)
- `iteration`, `phase`, `current_artifact`, `last_action`, `next_action`
- `halt_cause`, `halt_scan` (overwrite-latest: the most recent full-surface scan
  only; the durable event is the `halt` journal record)
- `pressure_objects` — **in-force rows only** (`active` / `hardened`), bounded
  ≤ `pressure-cap`. The transition history is *not* here; it is the `pressure`
  journal record type.

Per-archetype live keys (your archetype's row applies; the rest are for readers
resuming a hybrid):

| Archetype | Added live keys |
|---|---|
| `goal` | `goal_version`, `current_criterion`, `stuck_counters`, `final_verify` |
| `story` | `storyboard_path`, `lane`, `surface_class`, `current_story`, `last_surface`, `last_story_family`, `same_family_count`, `fixture_mode`, `evidence_manifest`, `last_validation_commands`, `remaining_findings_classified` |
| `frontier` | `frontier_vector`, `current_anchor`, `reward_channels`, `pressure_status`, `pressure_debt`, `checkpoint_reason`, `next_pressure`, `trace_locations`, `metric_locations`, `guardrails` |
| `greenfield` | `score_lock`, `phase_gates`, `current_stone_axis`, `user_halt_owner` |

**Moved out of `STATE.md`** (they were append-only history in disguise): the
former `pressure_ledger` → `pressure` journal records; `pressure_consulted` →
`consult` journal records; goal's `oracle_change_notes` → `oracle_change` journal
records; greenfield's `capability_list` → the `README.md` capability surface. The
write-once derivation record moved to `DERIVATION.md` (below). Frontier's
`pressure_status` / `pressure_debt` / `checkpoint_reason` / `next_pressure` stay
— they are a bounded checkpoint-level aggregate over the in-force rows, not a
transition log.

### `JOURNAL.jsonl` — the single append-only history

One typed JSON record per line, **target ≤300 chars**, evidence carried as
**pointers** (a path, an `AC-id`, a commit) never inlined blobs. `JOURNAL.jsonl`
is the *only* history surface — there is no separate CHECKPOINTS / monitor file.

Record types (`t`), each with `iter` (iteration) plus type-specific fields:

| `t` | Written when | Key fields | Archetypes |
|---|---|---|---|
| `attempt` | each iteration's attempt resolves | `ac`/`anchor`, `action`, `verdict`, `evidence` (pointer) | all |
| `oracle_change` | an oracle / criterion is added, edited, or re-scoped | `ac`, `from`, `to`, `why` | goal (+ any with an oracle) |
| `pressure` | a pressure row transitions (replaces `pressure_ledger`) | `id`, `from`, `to`, `evidence` | all |
| `consult` | step-0 pressure read-back (replaces `pressure_consulted`) | `consulted` (id→plan-element) or `no-promotion: <reason>` | all |
| `alignment_review` | a defaulted judgment / Alignment Review is recorded | `item`, `decision`, `anchor` | all |
| `checkpoint` | a delta-only status change worth a timestamp | `changed` (field→new), else omit | all |
| `halt` | a full halt-scan event fires | `cause`, `scan` (surface→state), `open` | all |
| `score_quarantine` | greenfield reframes the rubric and quarantines old scores | `rubric_from`, `rubric_to`, `quarantined` | greenfield |
| `bootstrap` | one-time setup completes | `what`, `files` | all |

Access:

- **Per pass (WORKING):** `tail -n 20 .loop/<loop-id>/JOURNAL.jsonl` — recent
  history only; never read the whole file per pass.
- **Keyed (ON-DEMAND):** `jq -c 'select(.ac=="AC-006")' .loop/<loop-id>/JOURNAL.jsonl`
  (swap the selector for `.id`, `.t`, `.anchor`, …) — pull one thread on the rare
  pass that needs prior art.
- **Human watch (WRITE-ONLY, external):**
  `tail -5 .loop/<loop-id>/JOURNAL.jsonl | jq -r '[.iter,.t,.ac//.id,.verdict//.to//.changed]|@tsv'`.

### `DERIVATION.md` — write-once derivation record (ON-DEMAND)

Written once at bootstrap, read on demand (diagnostics / resume), **never per
pass**. Records how this loop was composed:

- `primitive_bundle` — the classified axis values.
- `divergences` — each axis whose value differs from the nearest archetype, with
  its source.
- `overlays` — active composition overlays.
- `derivation_read_set` — the files `/loopgen` read to compose this loop.
- `frontload` — `{resolved, defaulted, open_gaps}`.

### Context budget

The Operational core near the top of `PROMPT.md` restates this budget as a table
(file → tier → cap → access command → human watch command) so post-compaction
rehydration is a bounded `sed -n '1,80p' .loop/<loop-id>/PROMPT.md`, not a
whole-file re-read.

**Budget assertion.** A PINNED or WORKING read that exceeds its declared cap
means the file discipline is broken, not that the cap is wrong: a `STATE.md` past
~50 lines, an in-force pressure set past `pressure-cap`, or a queue LIVE window
past `closed-retain-N` is a signal to **archive or collapse first**, before the
next decision — symmetric with the oracle-integrity checks that treat a violated
invariant as a `derivation-gap`, never as a reason to widen the bound. Silent
growth is the failure this whole model exists to prevent.
