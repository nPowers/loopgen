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
  (goal) · `storyboard` (story) · `rubric+intent` (greenfield) ·
  `findings-ledger` (frontier).
- The queue is a tier-1/2 surface in `evidence-tier.md`.

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

## Row contract

Each row records, at minimum: source / provenance · confidence · what would
prove it · status · reopen condition.

For benchmark-frontier, candidate rows are stricter and live in the overlay
artifact roles (`CANDIDATES`, `FRONTIER`, and `traces`) described in
`references/benchmark-frontier-artifacts.md`. That stricter row contract is not
inherited by pure frontier.

## Growth discipline (bounded re-read surface)

Every queue artifact this primitive names — `.loop/<loop-id>/FINDINGS.md`,
`.loop/<loop-id>/ACCEPTANCE.md`, `docs/storyboard.md`, the `.loop/<loop-id>/TRACES.md` /
`.loop/<loop-id>/METRICS.md` indexes, `.loop/<loop-id>/CANDIDATES.jsonl` — is re-read in full
every iteration; that re-read is this primitive's whole reason to exist. Left
unbounded it only grows with loop lifetime: a 100+ iteration loop pays an
ever-larger per-pass read tax on rows that already reached a terminal status
and no longer bend any decision. `primitives/pressure.md`'s `pressure_ledger`
already solves exactly this for the pressure surface — the in-force set capped
at `pressure-cap` (default 12), each row's own transition history capped at `K`
(default 5), and terminal rows collapsed to a one-line summary beyond the most
recent `M` (default 50), so that ledger is bounded by `pressure-cap`·`K` + `M`
+ 1 no matter how long the loop runs. This section generalizes that same cap
pattern from the pressure ledger to every queue artifact:

- **LIVE holds OPEN + recent-closed only.** The canonical artifact (
  `FINDINGS.md`, `ACCEPTANCE.md`, `docs/storyboard.md`, the `TRACES.md` /
  `METRICS.md` index, `CANDIDATES.jsonl`) keeps every `OPEN` / `active` row plus
  the `closed-retain-N` most-recently-closed rows (concrete default 20,
  frontload-tunable alongside `quiet-signal-N` / `stuck-attempt-N` —
  `frontload-audit.md`). A row that ages out of that window moves out of LIVE.
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

Not yet wired: this bound is authored here, in the shared primitive, but each
archetype's inline body discipline (`templates/bodies/goal-body.md` on
`ACCEPTANCE.md`, `story-body.md` on `docs/storyboard.md`, `frontier-body.md` on
`FINDINGS.md` / `TRACES.md` / `METRICS.md`, and `greenfield-body.md` once it
grows an equivalent queue) still needs to cite `closed-retain-N` and the
`archive/<artifact>.md` move the way each body already cites its own
row-status contract. That wiring is a follow-up, not part of this change.

## When prompt-only is valid

Only the simplest finite single-criterion runs ("I found one bug, close it")
need no queue.
