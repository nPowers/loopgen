# queue-as-second-artifact (shared primitive)

## Purpose

The pattern behind `artifact-shape.md`: every loop maintains `.loop/<loop-id>/PROMPT.md` +
`.loop/<loop-id>/STATE.md`, and **most also maintain one or more durable queue artifacts**
— reviewable inventories of discovered-but-not-yet-closed work — because durable
loop mechanics live in artifacts, not memory, and must survive context
compaction.

## Include when

Any composed prompt whose `artifact-shape` is not `prompt-only` (i.e. almost
all of them), as a framing note above the queue section.

## Composition notes

- The concrete queue is chosen by `artifact-shape`: `acceptance-inventory`
  (goal, `ACCEPTANCE.md`) · `storyboard` (story, `docs/storyboard.md`) ·
  `rubric+intent` (greenfield, `RUBRIC.md` + `INTENT.md`) · `findings-ledger`
  (frontier, `FINDINGS.md` + the `TRACES.md` / `METRICS.md` indexes). The
  Growth-discipline block below is **parameterized on that `<artifact>`** — it
  names `<artifact>` and `.loop/<loop-id>/archive/<artifact>.md`, so one wired
  block serves every archetype rather than four hand-rolled copies.
- The queue is a tier-1/2 surface in `evidence-tier.md`.
- **Wired, not aspirational.** Every archetype body INCLUDEs the block below via
  `{{INCLUDE primitives/queue-as-second-artifact.md}}`, so the `closed-retain-N`
  bound and the `archive/<artifact>.md` move ride into every composed prompt —
  not only the ones that happened to inline the discipline. (This replaces the
  earlier state where the bound lived in prose here but was carried by no body.)
- **Benchmark overlay rows are stricter (authoring only).** Under the
  benchmark-frontier overlay, candidate rows live in the stricter overlay
  artifact roles described in `references/benchmark-frontier-artifacts.md`; that
  contract is not inherited by pure frontier. Those overlay role names stay out
  of the generic emitted block below, so a pure archetype that INCLUDEs this
  block never carries them.

---

## Why it is load-bearing

- **Human-reviewable** after a long autonomous run or a context compaction.
- **Prevents re-discovery** — the loop doesn't re-find the same work each pass.
- **Encodes what repo state can't** — reverted hypotheses, dead directions,
  oscillation history. Current repo state carries landed signal only.

## The queue is an index, not the source of intent

The story-loop learning: the queue is an *index of evidence and intent*, not
intent itself. Before treating an old row as truth, re-check the authority
source (human prompt, current docs, accepted issue/PR, reviewer guidance). An
old row, prior evidence, or a prior screenshot cannot certify that a promise /
criterion is still intended.

## Row contract — INDEX row vs FULL row

The queue is stored as an **index table up top + one `## <id>` section per row**,
so the per-pass read is the index plus the OPEN / current sections only, never
the whole growing file (`primitives/context-stack.md`, WORKING tier). The two
surfaces carry different fields:

- **INDEX row** (in the table, re-read every pass): `id` · `status` · a
  one-line summary · the running counters (open / closed / reopen, plus any
  per-row stuck counter). Small and fixed-width, so the index stays cheap in the
  live-row count.
- **FULL row** (in the row's `## <id>` section, read on demand when acting on
  that row): source / provenance · confidence · `satisfied_by` (what would prove
  it) · reopen condition · `last_verification` (≤140 chars + an evidence
  pointer). The heavy evidence is a pointer into a trace or `JOURNAL.jsonl`,
  never an inlined blob in the row.

## Growth discipline (bounded re-read surface)

The queue artifact `<artifact>` — whichever one `artifact-shape` selected
(goal's `ACCEPTANCE.md`, story's `docs/storyboard.md`, frontier's `FINDINGS.md`
plus the `TRACES.md` / `METRICS.md` indexes, or the benchmark overlay's
candidate ledger) — is on the WORKING re-read path every iteration; that
re-read is this primitive's whole reason to exist. Left unbounded it only grows
with loop lifetime: a 100+ iteration loop pays an ever-larger per-pass read tax
on rows that already reached a terminal status and no longer bend any decision.
`primitives/context-stack.md` states the general rule — a WORKING surface must be
O(1) in loop age, read as an index + live rows, never whole-file — and
`primitives/pressure.md` applies it to the pressure surface (in-force set capped
at `pressure-cap`, transition history off-loaded to `JOURNAL.jsonl`). This
section applies the same cap to the queue:

- **LIVE holds OPEN + recent-closed only.** The canonical `<artifact>` keeps
  every `OPEN` / `active` row plus the `closed-retain-N` most-recently-closed
  rows (concrete default 20, frontload-tunable alongside `quiet-signal-N` /
  `stuck-attempt-N` — `frontload-audit.md`). A row that ages out of that window
  moves out of LIVE into the archive appendix below.
- **Archival is a move, never a delete.** A row that ages out relocates
  losslessly to a per-artifact appendix at `.loop/<loop-id>/archive/<artifact>.md`
  (e.g. `.loop/<loop-id>/archive/FINDINGS.md`, `.loop/<loop-id>/archive/ACCEPTANCE.md`) —
  the same gitignored `.loop/<loop-id>/` tree ADR 0003 already scopes execution
  state to, even for an artifact whose live copy is a tracked repo-native file
  (`docs/storyboard.md`'s archive still lands under `.loop/`, because closed
  history is scratch, not the deliverable). Relocation never rewrites a row's
  content and never touches its `status` — whether a row is closeable at all is
  governed entirely by the FIXED ≠ CLOSED discipline that already gates that
  transition; growth discipline only decides where an already-closed row is
  re-read from, never whether it may close.
- **The appendix is read on demand, not every pass.** Nothing in the numbered
  iteration protocol re-reads `archive/<artifact>.md` by default; it exists for
  human review after a long run or a context compaction, and for the rare pass
  that needs prior art before re-opening a reopen condition — mirroring
  `PRESSURE.md`'s re-read-every-pass vs. the ledger's collapsed-history split.
- **Totals survive in the live header.** A row's closure is already counted in
  the live artifact's running totals / counters (open count, closed count,
  reopen count) before it is ever archived — archival moves the row, not the
  count — so nothing is silently forgotten even once the row itself leaves the
  re-read surface.
- **Greenfield's `rubric+intent` is exempt from index/splitting and archival.**
  `RUBRIC.md` (8–12 criteria) and `INTENT.md` (≥3 live hypotheses) are bounded
  small by construction — they carry no OPEN/closed backlog that grows with loop
  age — so they are re-read whole every pass without an index table or an archive
  move, and the INDEX/FULL split above does not apply to them. Their one
  unbounded-growth risk is old-rubric-version scores accumulating across a
  reframe; that is handled by `score_quarantine` journal records
  (`templates/bodies/greenfield-body.md`), not by aging rows out of the rubric.

## When prompt-only is valid

Only the simplest finite single-criterion runs ("I found one bug, close it")
need no queue.
