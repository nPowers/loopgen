# pressure-accounting (shared frontier primitive)

## Purpose

Frontier loops do not finish; they account for pressure. This primitive gives
generic frontier prompts a small checkpoint contract without requiring a
benchmark artifact system.

It is the **`frontier` projection of the universal `pressure` primitive**
(`primitives/pressure.md`): the pressure field rendered as a checkpoint
contract. The fields below (`pressure_status`, `pressure_debt`,
`checkpoint_reason`, `next_pressure`) are a bounded checkpoint-level aggregate
over the common in-force `pressure_objects`; the transition history they
summarize now lives in `.loop/<loop-id>/JOURNAL.jsonl` `pressure` records, not a
per-frontier ledger (`primitives/context-stack.md`).

## Include when

Every prompt whose nearest archetype is `frontier`. It is universal for
frontier, independent of any benchmark-frontier overlay.

---

## Pressure record

Record these fields in the findings ledger or `.loop/<loop-id>/STATE.md`:

```yaml
pressure_status: open | paid | blocked | exhausted
pressure_debt: none | low | medium | high | explicitly_deferred
checkpoint_reason:
  plateau_after_active_pressure
  budget_exhausted
  evaluator_invalid
  risk_limit_hit
  target_gap_unresolved
  negative_result_saved
next_pressure: <trace/artifact/dimension/intervention to try next>
```

`pressure_status` names whether useful pressure remains. `pressure_debt`
names whether the current evidence is strong enough to support the claim.
`next_pressure` names the next evidence-producing move unless pressure has
been paid or explicitly deferred. `checkpoint_reason` is required for every
frontier checkpoint.

## Generic checkpoint rule

A generic frontier loop may checkpoint only after it has applied active
pressure or recorded why active pressure is blocked. A quiet ledger, green
cheap channel, or balanced homeostasis scan is not enough by itself.

Valid checkpoint states:

- `pressure_status: paid` with `pressure_debt: none`
- `pressure_status: exhausted` with a concrete `checkpoint_reason`
- `pressure_status: blocked` with `pressure_debt: explicitly_deferred` and the
  budget, scope, or authority that blocks the next pressure

Invalid checkpoint states:

- no pressure scan
- `pressure_status: open`
- `checkpoint_reason` omitted
- a claimed improvement whose evidence did not get stronger

## Storage rule

Do not invent a **new artifact role** for generic frontier pressure — that rule
guards against benchmark-overlay creep (the heavier candidate / frontier / trace
roles belong only to the benchmark-frontier overlay). The in-force checkpoint
fields above (`pressure_status` / `pressure_debt` / `checkpoint_reason` /
`next_pressure`) are live status: keep them in the findings ledger or
`.loop/<loop-id>/STATE.md`.

This is **not** in tension with the durability split. Moving pressure's
transition history (`pressure` records) and read-backs (`consult` records) into
the common `.loop/<loop-id>/JOURNAL.jsonl` is not a new artifact *role* — it is
the same mandated content placed in its correct *tier*
(`primitives/context-stack.md`, `primitives/pressure.md`), exactly as
`PRESSURE.md` is `STATE.md` `pressure_objects` rendered rather than a competing
store. New role forbidden; correct tier required.

The frontier-vector lifecycle obeys the same rule: the live vector and
guardrail map are compact one-line `.loop/<loop-id>/STATE.md` keys
(`frontier_vector`, `guardrails` — live status), a dimension candidate is an
ordinary findings-ledger row, its probe an ordinary `attempt` record, and an
admission delta a `checkpoint` record — no vector artifact, no candidate
ledger, no parallel history surface.
