# artifact-shape (axis primitive)

## Purpose

Which durable queue artifact the loop maintains beyond `.loop/<loop-id>/PROMPT.md` and
`.loop/<loop-id>/STATE.md` — the concrete form of the pattern in
`queue-as-second-artifact.md`. Weight 3. Determines the extra file Phase 4
emits.

## Values

- `prompt-only` — no queue. Valid only for the simplest finite single-criterion
  runs.
- `acceptance-inventory` — `.loop/<loop-id>/ACCEPTANCE.md`: frozen criteria with stable
  IDs, mutable `status` / `last_verification`.
- `storyboard` — `docs/storyboard.md`: product promises, each row with
  source / confidence / proof / latest evidence.
- `rubric+intent` — `.loop/<loop-id>/RUBRIC.md` (numbered criteria with 0/2/5 anchors) +
  `.loop/<loop-id>/INTENT.md` (≥3 live target hypotheses).
- `findings-ledger` — `.loop/<loop-id>/FINDINGS.md` + `.loop/<loop-id>/TRACES.md` +
  `.loop/<loop-id>/METRICS.md`: loop ledger, structured failure trace index, and metric
  output index.

## Detection heuristics

| Task phrasing | Value |
|---|---|
| finite criteria / spec | `acceptance-inventory` |
| product promises, frontend behavior | `storyboard` |
| manufactured evaluator + shifting target | `rubric+intent` |
| existing thing to improve, with evidence | `findings-ledger` |
| one-bug single-criterion fix | `prompt-only` |

## Archetype defaults

| Archetype | Default |
|---|---|
| frontier | `findings-ledger` |
| goal | `acceptance-inventory` |
| story | `storyboard` |
| greenfield | `rubric+intent` |

## Composition rules

- Each artifact is a tier-1/2 evidence surface (`evidence-tier.md`) and an
  **index** of evidence/intent, not the source of intent
  (`queue-as-second-artifact.md`).
- Phase 4 emits the chosen artifact as canonical files alongside
  `.loop/<loop-id>/PROMPT.md` + `.loop/<loop-id>/STATE.md`:
  `.loop/<loop-id>/ACCEPTANCE.md` + `.loop/<loop-id>/VERIFY.md`, `docs/storyboard.md`,
  `.loop/<loop-id>/RUBRIC.md` + `.loop/<loop-id>/INTENT.md` + `.loop/<loop-id>/README.md`, or
  `.loop/<loop-id>/FINDINGS.md` + `.loop/<loop-id>/TRACES.md` + `.loop/<loop-id>/METRICS.md`.
  Repo-native files may be recorded as aliases, but the canonical files still
  exist every run.
- A pure frontier `findings-ledger` carries generic pressure accounting. The
  benchmark-frontier overlay additionally emits `.loop/<loop-id>/DOMAIN_SPEC.md`,
  `.loop/<loop-id>/BENCHMARK.md`, `.loop/<loop-id>/CANDIDATES.jsonl`, `.loop/<loop-id>/FRONTIER.json`, and
  `.loop/<loop-id>/traces/`, but those roles are conditional overlay artifacts and do not
  change this axis value.
- `acceptance-inventory` pairs with `target-shape: finite-criteria`.
- A divergence on this axis adds the divergent artifact contract to the nearest
  archetype's contract; forbidden divergences route away instead of composing.
  Name the added contract in provenance.
