# Oracle Principles

The wisdom earned from real loop runs in a heavyweight oracle-loop
framework that goal-loop distills. Minus its syntax-heavy bureaucracy
(multi-agent harnesses, bash drivers, tagged lanes, Phase + TICKET-ID
decomposition), because `/loop` and `/goal` runners + LLM-native iteration
give us the iteration mechanics for free.

The point of goal-loop is to *honor these principles*, not enforce them
through structural overhead.

## The four principles

### 1. Oracle is binary

Pass or fail. Exit code, threshold, DOM attribute, text match, JSON field —
never a screenshot, never subjective quality, never self-assessment. If you
can't write a command that returns 0 or non-zero on this question, the
verifier is wrong.

### 2. Oracle independence

If the same entity that produces a bug also determines success, it's
**verification theater**. A verifier authored by the loop must first
**fail** against the unmet behavior — a mutation, a known wrong fixture,
a sentinel. If it cannot fail, it cannot prove.

Stronger form: dual-stack requires *different implementations*, not just
different languages. If both could be wrong the same way, it's not
independent.

### 3. Consumer-side oracle

Test from the user's perspective, not the producer's. *"Can the user do
Y?"* catches what *"Did I output X?"* misses — missing routes, orphaned
components, cold-start bugs, integration gaps.

For every criterion, ask: *if this passes, does the user have a working
feature?* If the answer requires inference, the verifier is wrong.

### 4. Anti-theater (FIXED ≠ CLOSED)

A fixer marking `Status: fixed` is **`FIXED_PENDING_CONFIRMATION`**, not
`CLOSED`. Closure requires either the next iteration's review pass
explicitly confirming, or the next pass not re-raising the finding.

In goal-loop's state model this is **`PASS_PENDING_FINAL`** → **`PASS`**:
a criterion's own verifier passing is *not* terminal. `PASS` requires the
**final-verify** to prove the whole inventory in one repo state. Halt
conditions count `OPEN` only; `PASS_PENDING_FINAL` does not satisfy them.

## Honest-verifier invariants

A slim subset of the heavyweight framework's full 18, scoped to what
makes a *verifier* honest (the multi-agent / harness / Phase invariants
don't apply to us — runner contract + LLM iteration replaces them).

1. **Oracle commands are concrete and runnable.** Never "review behaviour"
   or "confirm the spec." Every verifier is a command.
2. **No criterion says "decide", "investigate", "confirm with."** A
   criterion describes a finite testable state. If it requires judgment,
   it's not a goal criterion — route to the `story` or `frontier` archetype.
3. **Probes test at builder depth.** Authenticated API calls, real
   integration paths — not port pings. Manual inspection is not terminal
   proof.
4. **The final-verify proves the whole inventory in one repo state.**
   Multi-criterion runs can't terminate on serial individual passes.
5. **Scope manifest = binary in/out, not percentage.** Explicit allowed /
   forbidden globs. "Only 35% off-scope" is still drift.
6. **Reproducible from clean checkout.** No accumulated state masking
   bugs. The final-verify must pass on a fresh checkout of the same
   commit.
7. **Every criterion has named fail evidence.** A known red, a mutation
   sentinel, or `none-known` with justification. A verifier that *can't*
   fail isn't a verifier.

## Anti-patterns (trimmed)

| Pattern | Fix |
|---|---|
| Agent writes + verifies its own work | Verifier must first fail; closure requires external confirmation (`PASS_PENDING_FINAL` → `PASS`) |
| Probe pings port | Probe at builder depth (auth, real integration) |
| "Investigate" / "decide" / "confirm with" as a criterion | Phrase as a finite testable state, or route away |
| Snapshot refresh without semantic assertion | Snapshot is not a verifier without a semantic check |
| Test authored as both verifier *and* source of intent | Tests verify a frozen criterion from outside the loop |
| Gate verifies mechanism, not motivation | At derivation: does this verifier serve the criterion's purpose? Does the user get a working feature when it passes? |
| Hardcoded external URLs / ports | Caught at the Pre-flight Frontload audit |
| Ledger restates test names | Record discoveries (what broke, why, how we know), not regression-test names |

## When to spawn a separate verifier agent (optional, advanced)

For most goal-loop runs, a single iteration agent following principles
1–4 + the honest-verifier invariants is enough. The runner re-invokes;
the LLM holds the discipline.

For high-stakes goals where oracle independence matters more than
operational simplicity, derive a second emitted prompt
(`.loop/<loop-id>/PROMPT_verify.md`) and have a separate agent execute verifiers.
Use when:

- the criteria involve user-visible behavior an LLM might rationalize as
  passing,
- the loop authors both the implementation and the test (high theater
  risk),
- stakes require the strongest form of independence (e.g. payments,
  data-loss, security boundaries).

This is the heavyweight framework's default; for most goal-loop runs
it's the expensive form. Goal-loop notes the option in its derivation
but doesn't require it.

## When the heavyweight framework is the right move

The principles above are distilled — they keep the essence. The full
heavyweight framework adds:

- multi-agent Builder/Acceptance drone separation,
- a `loop.sh` runnable harness with structured config,
- Phase + TICKET-ID decomposition rather than a flat inventory,
- structured emission of separate PROGRESS / PROMPT_build / PROMPT_acceptance
  files.

Reach for the heavyweight form when: stakes require strict role
separation, the goal needs Phase-level decomposition, or you want a
generated `loop.sh` instead of using `/loop` / `/goal` / an external
harness as the runner. For everything else, `goal-loop` is the lighter
form.
