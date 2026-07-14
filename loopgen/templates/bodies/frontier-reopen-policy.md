# frontier-reopen-policy (body block variants)

The `{{FRONTIER_REOPEN_POLICY}}` block in `frontier-body.md` — the frontier
playbook's reopen-policy semantics, selected at compose time from
`effective_halt_shape` (the guarded closed-corpus resolution,
`primitives/halt-shape.md`):

- `equilibrium` — the archetype default and every pass-through case → the
  **Equilibrium variant**, byte-for-byte.
- `terminal` — the guarded closed-corpus resolution, or an explicitly
  requested terminal frontier → the **Terminal variant**.

The variants live here as authoring content: the composer (composed-prompt.md
steps 3/5) and the verifier (`tools/verify_loopgen_contracts.py`,
`reopen_policy_variant`) both extract them from this file by variant heading;
neither duplicates the text. Everything above the `---` separator is spec,
never emitted.

---

## Equilibrium variant

### Frontier checkpoint semantics

A frontier objective has no quality pass-line: it never completes by being
good enough, and no frontier halt below is an objective-completion claim.
`homeostatic-checkpoint`, `genuine-escalate`, `derivation-gap`,
`signal-starvation`, and `wrong-loop` are valid invocation halts, but none is
completion. When halting for any frontier cause, write:

```text
iteration halted; frontier checkpointed
```

Then list either the next pressure / unresolved OPEN findings / anchors, or the
full frontier scan — homeostasis, pressure discovery, and vector adequacy —
proving no high-yield admissible intervention remains.
The episode reopens automatically on strong new signal delivered through the
reopen contract named at frontload. Do not mark a generic runner goal as
complete for any frontier halt; at most, mark the invocation complete and leave
the loop artifact checkpointed, active, or gated.

Under this policy a dimension candidate that survives its pre-registered probe
may be **admitted in-episode** through the admission transaction
(Frontier-vector adequacy): the `checkpoint` journal record commits it and the
loop continues — an admitted dimension is fresh pressure, never a reason to
halt.

## Terminal variant

### Frontier termination semantics

A frontier objective has no quality pass-line: it never completes by being
good enough, and no frontier halt below is an objective-completion claim.
This episode runs under a **terminal reopen policy**; the provenance
divergence line records its basis (a guarded closed-corpus resolution, or an
explicit request). `homeostatic-checkpoint`,
`genuine-escalate`, `derivation-gap`, `signal-starvation`, and `wrong-loop`
are valid invocation halts, but none is completion. When the full frontier
scan — homeostasis, pressure discovery, and vector adequacy — proves no
high-yield admissible intervention remains under the declared search surfaces,
the episode **terminates** — declared workset exhausted —
instead of waiting in a reopenable checkpoint. Write:

```text
iteration halted; frontier episode terminated (declared workset exhausted)
```

Then list the full frontier scan as the termination's proof, plus any OPEN
findings handed off for external routing. The episode does not auto-resume; a
new episode may start only on an allowed exceptional event — an explicit
per-row `reopen_condition`, a regression, or a new declared-workset version
(`primitives/halt-shape.md`). For any other frontier halt cause the episode is
paused, not exhausted: write `iteration halted; frontier episode paused
(<cause>)` and leave the loop artifact paused or gated with its OPEN work
listed. Do not mark a generic runner goal as complete for any frontier halt;
at most, mark the invocation complete and leave the loop artifact terminated
(declared workset exhausted), paused, or gated.

Under this policy the live frontier vector **never mutates** — the initial
vector is part of the declared workset's identity, and the episode finishes
the frame it declared. A dimension candidate gets at most one bounded probe
attempt, only inside the declared surfaces and existing budget; a candidate
that survives is recorded as `handoff` output for a new declared-workset
version (a fresh `/loopgen` derivation), attached to the halt summary. The
admission transaction does not apply in this episode.
