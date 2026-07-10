# halt-cause-classifier (shared primitive)

## Purpose

When the loop emits `stop-and-summarize` or `escalate: <reason>`, it labels the
cause so the user — and the next derivation pass — can route it back.

## Include when

Every composed prompt, under "Halt conditions." Emit the shared causes plus the
nearest archetype's stop cause (a divergence may add a second archetype's stop
cause). For frontier, the stop cause is a checkpoint — or, under effective
`halt-shape: terminal`, an episode termination — never objective completion.

## Composition notes

- The stop cause matches the archetype's `convergence-shape`.
- `derivation-gap` is what makes the `frontload-audit` self-improving across
  runs.

---

## Shared causes (in every prompt)

- `derivation-gap` — blocked on something derivation could have asked for
  (model identity, budget cap, secret, path, fixture, …). **The feedback
  signal**: it tells the user the frontload checklist was incomplete; close it
  next run.
- `genuine-escalate` — irreversible / external / authority-needed (paid API
  budget, public-publish, secrets, product direction with unclear rollback,
  source conflict between authoritative-current sources).
- `wrong-loop` — the work belongs in a different archetype (see reroute table).

`signal-starvation` is a shared cause **only for archetypes that run a
quiet-signal checkpoint** (frontier, story): the quiet region — no new strong
evidence (no typed trace, no reviewed finding, no metric movement, no user
reframe) for the configured stretch — fired the checkpoint. `goal` is terminal
finite-criteria with no quiet-signal machinery, so it does **not** carry
`signal-starvation`.

## Completion semantics

Shared halt causes are **iteration/session halts**, not proof that the loop's
frontier or goal is complete. A prompt MUST make this distinction explicit:

- `genuine-escalate`, `derivation-gap`, `signal-starvation`, and `wrong-loop`
  mean "this invocation halted"; they must report the frontier/queue as still
  OPEN unless the queue is independently empty.
- A frontier **objective** has no quality pass-line and never completes by
  being good enough. A frontier **episode** may terminate on an extrinsic
  lifecycle reason — declared-workset exhaustion under effective
  `halt-shape: terminal` — and termination ends the execution, not the
  objective. `homeostatic-checkpoint` means no high-yield admissible
  intervention remains after a full scan; what follows — reopen on fresh
  signal, or episode termination with no auto-resume — is the composed reopen
  policy (`primitives/halt-shape.md`), stated in the body's
  checkpoint-semantics block.
- Only non-frontier archetype-terminal success causes may claim archetype
  completion (`criteria-met`, `storyboard-converged`, or `stone-converged`).
- On any non-success shared halt, final output must say the invocation halted
  and report the artifact as OPEN or checkpointed as appropriate, then list the
  unresolved queue rows and the external authorization or derivation change
  needed to resume.
- Runners that expose a generic "goal complete" switch must not use it for a
  non-success shared halt. They may mark the *invocation* complete, but the
  loop artifact remains active/paused with OPEN work.

## Non-success halt precondition

Before emitting any non-success shared halt, the loop MUST scan its full
search surface, not only the currently selected row. The scan covers **every
non-terminal row in the LIVE window** — every `OPEN` / `active` / unresolved row
still on the re-read surface — never the archived rows:

- frontier loops scan all homeostasis axes and all OPEN findings / anchors;
- goal loops scan all OPEN acceptance rows and verifier/oracle gaps;
- story loops scan storyboard lanes and unresolved promise rows;
- greenfield loops scan rubric/intent hypotheses and blocked capability
  surfaces.

**Scanning LIVE is a complete scan, not a narrowing.** Growth discipline
(`primitives/queue-as-second-artifact.md`) archives a row only once it reaches a
**terminal** status, and the live index's running totals (open / closed / reopen
counts) are updated before any archival — so the index proves the archive holds
only terminal rows, which by definition need no re-scan. Assert those running
totals as part of the scan: a non-terminal row can only be in LIVE, so if the
open count and the visible OPEN rows disagree the archive move was buggy and the
halt is blocked until reconciled. A single blocked row is not enough to halt. If
another reversible, in-scope intervention can move a different axis or strengthen
the evaluator, the loop continues with that intervention. A non-success halt is
valid only when every remaining useful intervention is blocked by the same
external authority, would violate scope/budget, or is low-yield same-family
polish with no fresh evidence.

A frontier episode termination under effective `halt-shape: terminal` is a
non-success halt and carries the same precondition: terminating because the
declared workset is exhausted requires the full scan as its proof. A terminal
reopen policy never licenses skipping the scan.

For frontier loops, the halt scan must also emit the pressure accounting fields:
`pressure_status`, `pressure_debt`, `checkpoint_reason`, and `next_pressure`.
Checkpointing with no pressure scan, open pressure, or no checkpoint reason is
invalid; the runner reports the frontier as active or externally paused instead.

### The halt-scan record (formalized once, shared by every archetype)

Every non-success halt writes the scan in exactly two places, so no body
hand-rolls its own shape (today frontier and story do; goal and greenfield omit
it):

- `.loop/<loop-id>/STATE.md` `halt_scan` — **overwrite-latest**: the most recent
  scan only (each searched surface class → its state / why no continuation),
  rewritten in place each halt. It is live status, never a history.
- a `halt` record appended to `.loop/<loop-id>/JOURNAL.jsonl` — the durable
  event: `{iter, cause, scan (surface→state), open}`. This is where halt history
  accumulates; `STATE.md` keeps only the latest scan.

The final output for a non-success halt reproduces that compact halt scan —
naming each searched axis / queue class and why no safe continuation remains —
and reports the artifact as OPEN or checkpointed per the completion semantics
above.

## Archetype stop causes

| Archetype | Stop cause(s) |
|---|---|
| frontier | `homeostatic-checkpoint` (never objective completion; the composed reopen policy decides checkpoint vs episode termination) |
| goal | `criteria-met` (success) · `partial-deadlock` · `oracle-drift` |
| story | `storyboard-converged` |
| greenfield | `stone-converged` |

## wrong-loop reroute targets

- finite checklist with a pass line → `goal`
- open-ended "make it better" with no pass line → `frontier`
- product-promise discovery / reconciliation → `story`
- target / artifact / evaluator undefined → `greenfield`
