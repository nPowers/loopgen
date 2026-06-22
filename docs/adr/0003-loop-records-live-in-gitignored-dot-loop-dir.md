# ADR 0003: loop records live in a gitignored `.loop/<loop-id>/` tree

- **Status:** Accepted
- **Date:** 2026-06-22
- **Deciders:** provi, Claude (Opus 4.8)

## Context

A loopgen-emitted loop needs a place to keep its execution state — `PROMPT.md`,
`STATE.md`, `PRESSURE.md`, and the archetype artifacts (`FINDINGS.md`,
`ACCEPTANCE.md`, `RUBRIC.md`, etc.). These originally lived in a single shared
`loop/` directory at the host-repo root. That shared, ambiguously-tracked
location has two problems: concurrent loops in one repo **collide** on the same
files, and execution state risks being **committed as if it were a deliverable**.

## Decision

All loop records live under a **gitignored, per-loop `.loop/<loop-id>/` tree**,
where `<loop-id>` is a **zero-padded sequence prefix + kebab-case identity** — a
per-repo 3-digit monotonic number (`max(existing .loop/NNN-*) + 1`, first is
`001`) joined to the kebab of the one-phrase kick-off identity (e.g. the first
loop with identity "weave cross-product OOD loop" → `.loop/001-weave-eval/`). The
prefix orders loops by creation and disambiguates two loops that share a slug.
Records are
**local-only execution state by default** — not version-controlled. Durable
conclusions **graduate** to `docs/` / `specs/` / code, never the loop dir. The
skill ensures the host repo's `.gitignore` ignores `.loop/` at emit, and the
kick-off points the runner at `.loop/<loop-id>/PROMPT.md`.

## Rationale

- **Execution state ≠ deliverable.** A loop's working files are scratch; they
  should not pollute the host repo's tracked history.
- **Per-loop-id isolation** lets multiple loops coexist in one repo without
  clobbering each other's `STATE.md` / `PROMPT.md`.
- **Gitignored** keeps the host repo clean by default and makes the
  graduate-conclusions-to-real-paths discipline the only way state becomes
  durable.
- **Uniform** with the frontier-loop scratch convention already kept under
  `.loop/`.

## Consequences

Positive:

- Multiple loops in one repo no longer collide; nothing is committed by default.
- One uniform record location across all archetypes and overlays.

Negative:

- Host repos must gitignore `.loop/`. The skill ensures this at emit, but a
  pre-existing host `.gitignore` may need a one-time add.
- Loop state is not shared via git by default; resuming a loop on another machine
  needs explicit promotion of its conclusions or a manual copy of the dir.

## Revisit Triggers

- A use case needs **version-controlled** loop state (auditable or shared loops),
  which would justify a tracked-mode opt-in alongside the default local-only mode.

## References

- Merged: commit `296c074` — `loop/` → `.loop/<loop-id>/` migration across
  `SKILL.md`, `primitives/`, `templates/bodies/`, and `composed-prompt.md`.
