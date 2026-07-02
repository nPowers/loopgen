#!/usr/bin/env python3
"""Verify loopgen's docs-as-runtime contracts.

This is intentionally lightweight: loopgen is a prompt generator, not a Python
runtime. The verifier renders the frontier body with and without the
benchmark-frontier overlay and checks the invariants that must be visible in
the generated prompts. It also renders all four archetype bodies against
fixture placeholders (the dead-sections contract), cross-checks SKILL.md's
derivation read contract and STATE.md key lists against the body/reference
files they name, and mirrors SKILL.md's axis matrix against classify.py.

Run via `make check` from the repo root, or directly as
`python3 tools/verify_loopgen_contracts.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify  # noqa: E402  (sibling module in tools/, mirrors SKILL.md's axis matrix)


ROOT = Path(__file__).resolve().parents[1]

FRONTIER_BODY = ROOT / "loopgen/templates/bodies/frontier-body.md"
GOAL_BODY = ROOT / "loopgen/templates/bodies/goal-body.md"
STORY_BODY = ROOT / "loopgen/templates/bodies/story-body.md"
GREENFIELD_BODY = ROOT / "loopgen/templates/bodies/greenfield-body.md"
BENCHMARK_FRONTIER = ROOT / "loopgen/primitives/benchmark-frontier.md"
PRESSURE_ACCOUNTING = ROOT / "loopgen/primitives/pressure-accounting.md"
SUBAGENT_PATTERNS = ROOT / "loopgen/primitives/subagent-patterns.md"
BENCHMARK_ARTIFACTS = ROOT / "loopgen/references/benchmark-frontier-artifacts.md"
FRONTLOAD_AUDIT = ROOT / "loopgen/primitives/frontload-audit.md"
SKILL = ROOT / "loopgen/SKILL.md"
COMPOSED_PROMPT = ROOT / "loopgen/templates/composed-prompt.md"

NON_FRONTIER_BODIES = (
    GOAL_BODY,
    STORY_BODY,
    GREENFIELD_BODY,
)
PRESSURE_ACCOUNTING_INCLUDE = "{{INCLUDE primitives/pressure-accounting.md}}"

BODY_PATHS = {
    "frontier": FRONTIER_BODY,
    "goal": GOAL_BODY,
    "story": STORY_BODY,
    "greenfield": GREENFIELD_BODY,
}


PLACEHOLDERS = {
    "MOTIVE": "Improve the repository's quality frontier without a fixed finish line.",
    "FRONTIER_VECTOR": "- correctness\n- legibility\n- evaluator trustworthiness",
    "EVALUATOR_TIER": "T3",
    "RAMP_GUIDANCE": "",
    "CHEAP_CHANNEL": "python3 tools/verify_loopgen_contracts.py",
    "EXPENSIVE_CHANNEL": "manual review of changed prompt contracts",
    "RAMP_SECTION": "",
    "RAMP_AXES_OVERRIDE": "",
    "SCOPE_MANIFEST": "Scope: loopgen prompt contracts and references.",
    "SCOPE_DRIFT_HALT": "",
    "CASH_OUT_N": "3",
    "QUIET_SIGNAL_N": "3",
    "REVIEW_CLOSURE_OVERLAY": "",
    # Always-on emitted slots, filled for every composed prompt. The verifier
    # renders the zero-pressure pure case, so PRESSURE_SURFACE is stripped (empty)
    # exactly as composed-prompt.md step 8 strips it when no pressure object exists.
    "PROVENANCE": "> Loop provenance — composed by /loopgen (verifier fixture).",
    "FRONTLOAD_PREAMBLE": "> Frontload — resolved: [motive]; defaulted: [thresholds]; open gaps: [none].",
    "PRESSURE_SURFACE": "",
    # Gated like PRESSURE_SURFACE: emitted only at consult-tier >= 1; the verifier
    # renders the tier-0 pure case, so {{SUBAGENT_PATTERNS}} is stripped (empty)
    # exactly as composed-prompt.md step 8 strips it.
    "SUBAGENT_PATTERNS": "",
}


Pattern = tuple[str, str]


PURE_FRONTIER_BANNED_PATTERNS: tuple[Pattern, ...] = (
    ("DOMAIN_SPEC role", r"\bDOMAIN_SPEC\b"),
    ("BENCHMARK role", r"\bBENCHMARK\b"),
    ("CANDIDATES role", r"\bCANDIDATES\b"),
    ("FRONTIER role", r"\bFRONTIER\b"),
    ("candidate_id", r"\bcandidate_id\b"),
    ("parent_candidate_id", r"\bparent_candidate_id\b"),
    ("candidate row contract", r"Candidate row contract"),
    ("candidate lifecycle", r"Candidate lifecycle"),
    ("operator enum", r"`operator`|operator:"),
    ("holdout role", r"\bholdout\b|holdout_trace|holdout_confirmed|holdout_regressed"),
    ("eval_health", r"\beval_health\b"),
)

PRESSURE_REQUIRED = (
    "pressure_status",
    "pressure_debt",
    "checkpoint_reason",
    "next_pressure",
)

CHECKPOINT_REASON_VALUES = (
    "plateau_after_active_pressure",
    "budget_exhausted",
    "evaluator_invalid",
    "risk_limit_hit",
    "target_gap_unresolved",
    "negative_result_saved",
)

BENCHMARK_REQUIRED_PATTERNS: tuple[Pattern, ...] = (
    ("mode header", r"^## Benchmark Frontier Mode\b"),
    ("DOMAIN_SPEC role", r"\bDOMAIN_SPEC\b"),
    ("BENCHMARK role", r"\bBENCHMARK\b"),
    ("CANDIDATES role", r"\bCANDIDATES\b"),
    ("FRONTIER role", r"\bFRONTIER\b"),
    ("trace role path", r"traces/<candidate>/<case>/evaluation\.json"),
    ("candidate_id field", r"\bcandidate_id\b"),
    (
        "operator enum",
        # Prefix-anchored: benchmark-frontier.md appends the structural-negative
        # bridge operators (consult | architect | build) after `compress`, while
        # the artifacts reference still lists only the core eight (pre-existing
        # drift, tracked separately). Match the core prefix, not the exact tail.
        r"`operator`: `draft \| debug \| improve \| ablate \| stress \| "
        r"falsify \| transfer \| compress",
    ),
    ("holdout set", r"\bholdout set\b"),
    ("eval_health token", r"\beval_health\b"),
    ("green-trace rule", r"Green search traces"),
)


class ContractError(Exception):
    """Verifier setup failed before contract assertions could run."""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontier_template() -> str:
    text = read(FRONTIER_BODY)
    notes_marker = "\n---\n\n## Derivation notes"
    notes_start = text.find(notes_marker)
    if notes_start == -1:
        raise ContractError("missing derivation-notes marker")

    pre_notes = text[:notes_start]
    md_fences = list(re.finditer(r"(?m)^```md\s*$", pre_notes))
    if len(md_fences) != 1:
        raise ContractError(
            "expected exactly one template ```md fence before derivation notes, "
            f"found {len(md_fences)}"
        )

    start = md_fences[0].end() + 1
    closing_fences = [
        match
        for match in re.finditer(r"(?m)^```\s*$", pre_notes)
        if match.start() > start
    ]
    if not closing_fences:
        raise ContractError("missing closing fence for frontier prompt template")
    end = closing_fences[-1].start()
    return text[start:end]


def include_text(match: re.Match[str]) -> str:
    """Resolve `{{INCLUDE primitives/X.md}}` to the primitive's runtime block.

    Per composed-prompt.md step 2, an include inlines only the block that
    follows the `---` spec separator (authoring scaffolding above it — title,
    Purpose, Include-when — is stripped). A primitive with no separator cannot
    be resolved; that is a hard failure, never a silent whole-file fallback.
    """
    rel = match.group(1).strip()
    raw = read(ROOT / "loopgen" / rel)
    sep = "\n---\n"
    idx = raw.find(sep)
    if idx == -1:
        raise ContractError(
            f"included primitive {rel} lacks a '---' spec separator; "
            "cannot resolve its runtime block (composed-prompt.md step 2)"
        )
    return raw[idx + len(sep):].lstrip("\n")


def benchmark_mode() -> str:
    primitive = read(BENCHMARK_FRONTIER)
    start = primitive.index("## Benchmark Frontier Mode")
    return primitive[start:]


def render_frontier(*, benchmark_overlay: bool) -> str:
    prompt = frontier_template()
    mode = benchmark_mode() if benchmark_overlay else ""
    prompt = prompt.replace("{{BENCHMARK_FRONTIER_MODE}}", mode)
    prompt = re.sub(r"\{\{INCLUDE ([^}]+)\}\}", include_text, prompt)
    for key, value in PLACEHOLDERS.items():
        prompt = prompt.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{[^}]+\}\}", prompt)))
    if leftovers:
        raise AssertionError(f"unsubstituted placeholders: {leftovers}")
    return prompt


# ── generalized render, all four archetype bodies (dead-sections contract) ──
# render_frontier() above is kept as-is (existing frontier-specific checks
# assert on its exact fixture values). This is a second, generalized renderer
# used only to prove every body's placeholders are all substitutable and that
# no {{...}} token survives (composed-prompt.md step 8's dead-section rule),
# for all four bodies, not just frontier.

COMMON_BODY_PLACEHOLDERS = {
    "PROVENANCE": "> Loop provenance — composed by /loopgen (verifier fixture).",
    "FRONTLOAD_PREAMBLE": "> Frontload — resolved: [motive]; defaulted: [thresholds]; open gaps: [none].",
    "MOTIVE": "Improve the repository's quality frontier without a fixed finish line.",
    # Gated placeholders default to stripped (tier-0 / zero-pressure pure case);
    # render_body(..., consult_tier=N) overrides SUBAGENT_PATTERNS below.
    "PRESSURE_SURFACE": "",
}

ARCHETYPE_BODY_PLACEHOLDERS = {
    "frontier": {
        "FRONTIER_VECTOR": "- correctness\n- legibility\n- evaluator trustworthiness",
        "EVALUATOR_TIER": "T3",
        "RAMP_GUIDANCE": "",
        "CHEAP_CHANNEL": "python3 tools/verify_loopgen_contracts.py",
        "EXPENSIVE_CHANNEL": "manual review of changed prompt contracts",
        "RAMP_SECTION": "",
        "RAMP_AXES_OVERRIDE": "",
        "SCOPE_MANIFEST": "Scope: loopgen prompt contracts and references.",
        "SCOPE_DRIFT_HALT": "",
        "CASH_OUT_N": "3",
        "QUIET_SIGNAL_N": "3",
        "REVIEW_CLOSURE_OVERLAY": "",
    },
    "goal": {
        "GOAL_VERSION": "goal-v1-fixture",
        "REGRESSION_MODE": "",
        "STUCK_ATTEMPT_N": "3",
        "CHEAP_CHANNEL": "make check",
        "FINAL_VERIFY": "make check",
        "TOPOLOGY": "all criteria independent.",
        "SCOPE_MANIFEST": "Scope: fixture acceptance inventory.",
        "FORBIDDEN_SHORTCUTS": "None beyond the defaults below.",
        "REPO_SPECIFIC_OVERLAY": "",
    },
    "story": {
        "LANE": "Surface Taste Lane",
        "SURFACE_CLASS": "fixture surface",
        "STORYBOARD_PATH": "docs/storyboard.md",
    },
    "greenfield": {
        "CAPABILITY_LIST": "- none yet.",
        "INVARIANTS": "1. Fixture invariant placeholder.",
        "PHASE_GATES": "- research: owner loop, status yes",
    },
}


def raw_body_template(path: Path) -> str:
    """Extract the fenced prompt template from a body file, generalizing
    frontier_template() to bodies that use a four-backtick fence (goal,
    story, greenfield nest ```yaml/```text/```json blocks, so their outer
    fence widens to four backticks) as well as frontier's three-backtick one.
    """
    text = read(path)
    notes_marker = "\n---\n\n## Derivation notes"
    notes_start = text.find(notes_marker)
    if notes_start == -1:
        raise ContractError(f"{path.name}: missing derivation-notes marker")

    pre_notes = text[:notes_start]
    fence_open = re.search(r"(?m)^(`{3,4})md\s*$", pre_notes)
    if not fence_open:
        raise ContractError(f"{path.name}: missing opening md fence before derivation notes")
    ticks = fence_open.group(1)
    start = fence_open.end() + 1
    close_re = re.compile(rf"(?m)^{ticks}\s*$")
    closing_fences = [m for m in close_re.finditer(pre_notes) if m.start() > start]
    if not closing_fences:
        raise ContractError(f"{path.name}: missing closing fence for prompt template")
    end = closing_fences[-1].start()
    return text[start:end]


def resolve_gated_block(path: Path) -> str:
    """The runtime block below a primitive's '---' spec separator (same
    resolution rule as include_text(), factored out for gated placeholders
    that are substituted directly rather than via an {{INCLUDE ...}} marker).
    """
    raw = read(path)
    sep = "\n---\n"
    idx = raw.find(sep)
    if idx == -1:
        raise ContractError(f"{path.name} lacks a '---' spec separator")
    return raw[idx + len(sep):].lstrip("\n")


def render_body(archetype: str, *, consult_tier: int = 0) -> str:
    prompt = raw_body_template(BODY_PATHS[archetype])
    if archetype == "frontier":
        prompt = prompt.replace("{{BENCHMARK_FRONTIER_MODE}}", "")
    prompt = re.sub(r"\{\{INCLUDE ([^}]+)\}\}", include_text, prompt)

    if consult_tier >= 1:
        block = resolve_gated_block(SUBAGENT_PATTERNS)
        block = block.replace("{{CONSULT_TIER}}", f"tier-{consult_tier}")
        prompt = prompt.replace("{{SUBAGENT_PATTERNS}}", block)
    else:
        prompt = prompt.replace("{{SUBAGENT_PATTERNS}}", "")

    values = dict(COMMON_BODY_PLACEHOLDERS)
    values.update(ARCHETYPE_BODY_PLACEHOLDERS[archetype])
    for key, value in values.items():
        prompt = prompt.replace("{{" + key + "}}", value)

    leftovers = sorted(set(re.findall(r"\{\{[^}]+\}\}", prompt)))
    if leftovers:
        raise AssertionError(f"{archetype}: unsubstituted placeholders: {leftovers}")
    return prompt


def require(condition: bool, name: str, detail: str = "") -> tuple[bool, str]:
    if condition:
        return True, f"[PASS] {name}"
    suffix = f": {detail}" if detail else ""
    return False, f"[FAIL] {name}{suffix}"


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def missing_patterns(text: str, patterns: tuple[Pattern, ...]) -> list[str]:
    return [
        name
        for name, pattern in patterns
        if re.search(pattern, text, re.MULTILINE) is None
    ]


def leaked_patterns(text: str, patterns: tuple[Pattern, ...]) -> list[str]:
    return [
        name
        for name, pattern in patterns
        if re.search(pattern, text, re.MULTILINE) is not None
    ]


def one_line(text: str) -> str:
    return " ".join(text.split())


def stale_deferred_status(text: str) -> bool:
    return bool(re.search(r"(?m)^\s*-\s*`?DEFERRED`?\b", text))


# Candidate-row contract, verdict-driven. Mirrors the rule in
# references/benchmark-frontier-artifacts.md: a status may not outrun its
# evidence OR its verdict, and deferred pressure is a FRONTIER-level fact,
# never a candidate-row status. This is a contract fixture test (proving the
# documented rule rejects the documented-invalid states), not a runtime
# row validator.
VALID_ROW_STATUSES = {
    "proposed",
    "compliance_checked",
    "smoke_checked",
    "search_scored",
    "frontier_member",
    "rejected",
    "holdout_confirmed",
    "holdout_regressed",
    "pressure_paid",
}


def _pressure_paid_supported(traces: dict[str, object]) -> bool:
    if traces.get("holdout") == "pass":
        return True
    adversarial = traces.get("adversarial")
    if (
        isinstance(adversarial, dict)
        and adversarial.get("expected_green")
        and adversarial.get("expected_red")
    ):
        return True
    return bool(traces.get("meta_eval"))


def candidate_row_violations(row: dict[str, object]) -> list[str]:
    """Return the contract violations for a candidate row (empty == valid)."""
    violations: list[str] = []
    status = row.get("status")
    traces = row.get("traces", {})

    if status not in VALID_ROW_STATUSES:
        violations.append(f"{status!r} is not a candidate-row status")
        return violations

    holdout = traces.get("holdout")  # "pass" | "fail" | "regress" | None
    if status == "holdout_confirmed" and holdout != "pass":
        violations.append("holdout_confirmed needs a passing holdout_trace verdict")
    if status == "holdout_regressed" and holdout not in {"fail", "regress"}:
        violations.append("holdout_regressed needs a failing/regressing holdout_trace verdict")
    if status == "pressure_paid" and not _pressure_paid_supported(traces):
        violations.append("pressure_paid needs a stronger-pressure trace with a supporting verdict")
    return violations


CANDIDATE_ROW_FIXTURES: tuple[tuple[str, dict[str, object], bool], ...] = (
    ("holdout_confirmed + passing holdout", {"status": "holdout_confirmed", "traces": {"holdout": "pass"}}, True),
    ("holdout_confirmed + null holdout", {"status": "holdout_confirmed", "traces": {"holdout": None}}, False),
    ("holdout_confirmed + failing holdout (verdict mismatch)", {"status": "holdout_confirmed", "traces": {"holdout": "fail"}}, False),
    ("pressure_paid + only search evidence", {"status": "pressure_paid", "traces": {}}, False),
    ("pressure_paid + adversarial without expected_red", {"status": "pressure_paid", "traces": {"adversarial": {"expected_green": True, "expected_red": False}}}, False),
    ("pressure_paid + adversarial controls recorded", {"status": "pressure_paid", "traces": {"adversarial": {"expected_green": True, "expected_red": True}}}, True),
    ("pressure_deferred is not a candidate status", {"status": "pressure_deferred", "traces": {}}, False),
    ("frontier_member with holdout deferred (null) — deferral lives in FRONTIER", {"status": "frontier_member", "traces": {"holdout": None}}, True),
)


# ── oracle-integrity contract (benchmark-frontier overlay) ──────────────────
# Guards the row -> property -> trace bijection the code review caught drifting
# (the P1 "oracle-provenance" name collision and the P4/P5 transposition). The
# eight oracle.* rows in benchmark-frontier.md, the mapping table beneath them,
# and the P1-P8 list in frontload-audit.md must all agree, 1:1, by name and order.

_ORACLE_GUARDS_HEADER = "| id | guards against |"
_ORACLE_MAP_HEADER = "| row | audit property | candidate trace |"
_PROP_NAME = r"[a-z][a-z\- ]*[a-z]"


def _table_block(text: str, header: str) -> str:
    i = text.find(header)
    if i == -1:
        return ""
    block = text[i:]
    end = block.find("\n\n")
    return block[:end] if end != -1 else block


def _guards_rows(primitive: str) -> list[str]:
    block = _table_block(primitive, _ORACLE_GUARDS_HEADER)
    return re.findall(r"(?m)^\|\s*`(oracle\.[a-z0-9-]+)`\s*\|", block)


def _mapping_rows(primitive: str) -> list[tuple[str, str, str, str]]:
    block = _table_block(primitive, _ORACLE_MAP_HEADER)
    rows: list[tuple[str, str, str, str]] = []
    for line in block.splitlines():
        m = re.match(
            rf"^\|\s*`(oracle\.[a-z0-9-]+)`\s*\|\s*(P\d)\s+({_PROP_NAME})\s*\|\s*(.+?)\s*\|$",
            line,
        )
        if m:
            rows.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    return rows


def _frontload_properties(audit_text: str) -> list[tuple[str, str, str]]:
    return re.findall(
        rf"(?m)^-\s+\*\*(P\d)\s+({_PROP_NAME})\*\*\s*\(`(oracle\.[a-z0-9-]+)`\)",
        audit_text,
    )


def oracle_integrity_bijection_violations() -> list[str]:
    primitive = read(BENCHMARK_FRONTIER)
    audit = read(FRONTLOAD_AUDIT)
    artifacts = read(BENCHMARK_ARTIFACTS)
    v: list[str] = []

    guards = _guards_rows(primitive)
    mapping = _mapping_rows(primitive)
    fl = _frontload_properties(audit)

    if len(guards) != 8:
        v.append(f"guards table has {len(guards)} oracle rows (expected 8)")
    if len(mapping) != 8:
        v.append(f"mapping table has {len(mapping)} rows (expected 8)")
    if len(fl) != 8:
        v.append(f"frontload audit lists {len(fl)} properties (expected 8)")

    guards_ids = set(guards)
    mapping_ids = {r[0] for r in mapping}
    fl_ids = {r[2] for r in fl}
    if guards_ids != mapping_ids:
        v.append(f"guards vs mapping row-id mismatch: {sorted(guards_ids ^ mapping_ids)}")
    if mapping_ids != fl_ids:
        v.append(f"mapping vs frontload row-id mismatch: {sorted(mapping_ids ^ fl_ids)}")

    map_by_id = {r[0]: (r[1], r[2]) for r in mapping}
    fl_by_id = {r[2]: (r[0], r[1]) for r in fl}
    for rid in sorted(mapping_ids & fl_ids):
        if map_by_id[rid] != fl_by_id[rid]:
            v.append(f"{rid}: mapping {map_by_id[rid]} != frontload {fl_by_id[rid]}")

    expected_pnums = [f"P{i}" for i in range(1, 9)]
    if sorted(r[1] for r in mapping) != expected_pnums:
        v.append(f"mapping P-numbers not a 1..8 bijection: {sorted(r[1] for r in mapping)}")
    if sorted(r[0] for r in fl) != expected_pnums:
        v.append(f"frontload P-numbers not a 1..8 bijection: {sorted(r[0] for r in fl)}")

    for rid, _pnum, _name, trace in mapping:
        m = re.fullmatch(r"`([a-z_]+)`", trace.strip())
        if m and m.group(1) not in artifacts:
            v.append(f"{rid}: trace field `{m.group(1)}` not present in artifacts reference")

    return v


def seed_double_gate_violations() -> list[str]:
    """The seed imperative must carry the second gate (trusted-or-mutated), so a
    deterministic-oracle overlay seeds nothing and the byte-identity negative path
    holds. A bare 'On overlay activation, seed ...' widens it to any benchmark."""
    primitive = read(BENCHMARK_FRONTIER)
    v: list[str] = []
    if re.search(r"On overlay activation,\s+seed these rows", primitive):
        v.append("seed imperative dropped the trusted-or-mutated gate (bare 'On overlay activation, seed')")
    if "trusted-or-mutated" not in one_line(primitive):
        v.append("missing 'trusted-or-mutated' seed qualifier")
    return v


def oracle_integrity_authority_violations() -> list[str]:
    """Guards the two Codex P2 findings on PR #3:
    (1) overlay-seeded rows must be `source: overlay`, not `source: mined` (which
        would conflict with the latent-mining low/salience + provenance contract);
    (2) the gate caps `claim_scope`, never an undefined candidate status -- the
        candidate-status enum has no `pending-needs-cross-seed` / `pending`."""
    primitive = read(BENCHMARK_FRONTIER)
    audit = read(FRONTLOAD_AUDIT)
    v: list[str] = []

    if "`source: overlay`" not in primitive:
        v.append("oracle rows are not declared `source: overlay`")
    if re.search(r"seed these rows.*?`source: mined`", primitive, re.S):
        v.append("oracle rows still declared `source: mined` (conflicts with the mined entry rule)")

    for text, where in ((primitive, "benchmark-frontier"), (audit, "frontload-audit")):
        for tok in ("pending-needs-cross-seed", "caps status at", "caps the candidate at"):
            if tok in text:
                v.append(f"{where}: undefined-candidate-status phrasing {tok!r} (cap via claim_scope instead)")
    return v


def halt_shared_cause_violations() -> list[str]:
    """signal-starvation is a quiet-signal-checkpoint cause: frontier+story carry
    it; goal (terminal, no quiet-signal machinery) must not. frontier's
    genuine-escalate must keep the recovered 'source conflict' detail (U2)."""
    v: list[str] = []
    goal = read(ROOT / "loopgen/templates/bodies/goal-body.md")
    story = read(ROOT / "loopgen/templates/bodies/story-body.md")
    frontier = read(FRONTIER_BODY)
    if "signal-starvation" not in frontier:
        v.append("frontier body missing signal-starvation")
    if "signal-starvation" not in story:
        v.append("story body missing signal-starvation")
    if "signal-starvation" in goal:
        v.append("goal body must not carry signal-starvation (no quiet-signal checkpoint)")
    if "source conflict" not in frontier:
        v.append("frontier genuine-escalate dropped 'source conflict'")
    return v


def _flat(s: str) -> str:
    return " ".join(s.split())


def _section_body(text: str, heading: str) -> str | None:
    """The flattened body of a section, from `heading` to the next ##/### heading."""
    i = text.find(heading)
    if i == -1:
        return None
    rest = text[i + len(heading):]
    end = len(rest)
    for marker in ("\n## ", "\n### "):
        j = rest.find(marker)
        if j != -1:
            end = min(end, j)
    return _flat(rest[:end])


HOMEOSTASIS_AXES = (
    "Oracle trustworthiness",
    "Product capability",
    "Failure legibility",
    "Specification coherence",
    "Intervention diversity",
)


def cross_file_pin_violations() -> list[str]:
    """U4: pin drift-prone restatements at the right granularity (dev/-local).

    NOT the locked classification matrix (SKILL.md target/halt/artifact/
    convergence/cadence-shape) — these are the five *homeostasis* axes, a
    disjoint set. AskUserQuestion has 5 sites; only judgment-default (owner) and
    the greenfield-invariants copy share line 1 verbatim — the others are
    intentional paraphrases and are not pinned.
    """
    v: list[str] = []
    frontier = read(FRONTIER_BODY)
    goal = read(ROOT / "loopgen/templates/bodies/goal-body.md")
    oracle = read(ROOT / "loopgen/references/oracle-principles.md")
    judgment = read(ROOT / "loopgen/primitives/judgment-default.md")
    greenfield_inv = read(ROOT / "loopgen/references/greenfield-invariants.md")
    frontier_flat = _flat(frontier)

    # (a) status-theater prohibition — byte-identical block in goal + frontier
    st_f = _section_body(frontier, "### Status-theater prohibition")
    st_g = _section_body(goal, "### Status-theater prohibition")
    if not st_f or not st_g:
        v.append("status-theater block missing from a body")
    elif st_f != st_g:
        v.append("status-theater block drifted between frontier and goal")

    # (b) FIXED != CLOSED — one shared sentence amid divergent framing
    closure = (
        "Closure requires either the next iteration's review pass "
        "explicitly confirming, or the next pass not re-raising the finding"
    )
    if closure not in frontier_flat:
        v.append("FIXED!=CLOSED shared sentence missing from frontier")
    if closure not in _flat(oracle):
        v.append("FIXED!=CLOSED shared sentence missing from oracle-principles")

    # (c) AskUserQuestion ban — shared opening (owner + greenfield copy)
    ban = "Never call `AskUserQuestion` or any interactive / blocking / approval-prompt"
    if ban not in _flat(judgment):
        v.append("AskUserQuestion ban missing from judgment-default")
    if ban not in _flat(greenfield_inv):
        v.append("AskUserQuestion ban missing from greenfield-invariants")

    # (d) homeostasis axes — the existing five, named; never extend
    axes_block = _section_body(frontier, "### Axes") or ""
    for name in HOMEOSTASIS_AXES:
        if name not in axes_block:
            v.append(f"homeostasis axis missing: {name}")
    if axes_block.count("- **") != len(HOMEOSTASIS_AXES):
        v.append("Axes block does not enumerate exactly five axes")
    if "all five homeostasis axes" not in frontier_flat:
        v.append("'all five homeostasis axes' literal missing")
    return v


def checkpoint_reason_closedset_violations() -> list[str]:
    """U5: the FRONTIER.json checkpoint_reason field must be EXACTLY the 6 prose
    enum values plus an explicitly-labeled `null` resting value — closing the
    pipe-delimited form where `| null` leaked past the presence-only check."""
    text = read(BENCHMARK_ARTIFACTS)
    line = next(
        (ln for ln in text.splitlines() if ln.strip().startswith("checkpoint_reason:")),
        None,
    )
    if line is None:
        return ["checkpoint_reason field missing from FRONTIER.json schema"]
    rhs = line.split(":", 1)[1].split("#", 1)[0]
    tokens = {t.strip() for t in rhs.split("|") if t.strip()}
    allowed = set(CHECKPOINT_REASON_VALUES) | {"null"}
    v: list[str] = []
    if tokens - allowed:
        v.append(f"non-enum checkpoint_reason tokens: {sorted(tokens - allowed)}")
    if set(CHECKPOINT_REASON_VALUES) - tokens:
        v.append(f"missing checkpoint_reason values: {sorted(set(CHECKPOINT_REASON_VALUES) - tokens)}")
    if "null" in tokens and "resting value" not in line:
        v.append("checkpoint_reason `null` present without labeling it the resting value")
    return v


def include_target_violations() -> list[str]:
    """U6: every {{INCLUDE x}} a body pulls must RESOLVE — the target needs a
    `---` spec separator (else include_text() raises a ContractError at render),
    and the runtime block below it must not leak authoring scaffolding
    (## Purpose / ## Include when). Greenfield's evidence-tier / halt-cause /
    queue INCLUDEs went dark here because the verifier only rendered frontier."""
    v: list[str] = []
    bodies = (FRONTIER_BODY,) + NON_FRONTIER_BODIES
    seen: set[str] = set()
    for body in bodies:
        for m in re.finditer(r"\{\{INCLUDE ([^}]+)\}\}", read(body)):
            rel = m.group(1).strip()
            if not rel.endswith(".md"):
                continue  # prose example (e.g. greenfield-body's "{{INCLUDE …}}"), not a real target
            if rel in seen:
                continue
            seen.add(rel)
            raw = read(ROOT / "loopgen" / rel)
            if "\n---\n" not in raw:
                v.append(f"{rel}: no '---' separator (INCLUDE would crash)")
                continue
            block = raw.split("\n---\n", 1)[1]
            if "## Purpose" in block or "## Include when" in block:
                v.append(f"{rel}: authoring scaffolding leaks below '---'")
    return v


# ── I2/I10: read-set existence, STATE-key cross-check, classify-mirror ──────


def _section_between(text: str, start_marker: str, end_marker: str) -> str:
    i = text.index(start_marker) + len(start_marker)
    j = text.index(end_marker, i)
    return text[i:j]


def derivation_read_set_violations() -> list[str]:
    """R1: every concrete `path.md` backtick-cited in SKILL.md's Derivation
    read contract (both tiers, plus the 'After classification, also read'
    conditional list) must exist under loopgen/. Placeholder paths like
    `archetypes/<nearest>.md` or `primitives/<axis>.md` are intentionally
    unresolvable at this level (the `<...>` template variable is not a
    filename character) and are skipped, not asserted."""
    skill = read(SKILL)
    start = skill.index("## Derivation read contract")
    end = skill.index("## Phase 1", start)
    section = skill[start:end]
    paths = sorted(set(re.findall(r"`([a-z][a-z0-9_-]*(?:/[a-z0-9_.-]+)*\.md)`", section)))
    if not paths:
        return ["no concrete read-set paths parsed from SKILL.md (parser drift?)"]
    return [p for p in paths if not (ROOT / "loopgen" / p).exists()]


def _common_state_keys(skill: str) -> list[str]:
    block = _section_between(
        skill,
        "**Required `.loop/<loop-id>/STATE.md` keys, every archetype:**",
        "**Archetype-specific `.loop/<loop-id>/STATE.md` keys:**",
    )
    keys: list[str] = []
    for span in re.findall(r"`([^`]+)`", block):
        m = re.match(r"[a-z][a-z0-9_]*", span)
        if m:
            keys.append(m.group(0))
    return keys


def _archetype_state_keys(skill: str, archetype: str) -> list[str]:
    m = re.search(rf"-\s*`{archetype}`\s*—\s*((?:`[a-z_]+`,?\s*)+)\.", skill)
    if not m:
        return []
    return re.findall(r"`([a-z_]+)`", m.group(1))


# Composer/provenance bookkeeping keys: SKILL.md's Phase 4 writes these once
# at emit time (archetype, identity, primitive_bundle, divergences, overlays,
# consult_tier, evaluator_tier, derivation_read_set, current_artifact); no
# archetype body's iteration-protocol prose narrates them in its own
# "Artifacts to maintain" section, and that gap is consistent across all four
# bodies — i.e. it is an intentional split between emit-time provenance and
# runner-facing iteration state, not per-archetype drift. `archetype` is left
# checkable since every body happens to name its own or a sibling archetype
# in prose (routing / wrong-loop text); the rest are excluded from R2 so the
# check stays focused on genuine iteration-state gaps.
_BOOKKEEPING_KEYS = frozenset(
    {
        "identity",
        "primitive_bundle",
        "divergences",
        "overlays",
        "consult_tier",
        "evaluator_tier",
        "derivation_read_set",
        "current_artifact",
    }
)


def state_key_body_violations() -> dict[str, list[str]]:
    """R2: every STATE.md key SKILL.md requires for an archetype (common +
    archetype-specific), excluding the emit-time bookkeeping keys in
    `_BOOKKEEPING_KEYS` (see comment above), should be mentioned somewhere in
    that archetype's body text — tolerant of `snake_case` vs "spaced words"
    (goal-body says "goal version", not `goal_version`), case, and a body's
    own soft line-wrap (e.g. "stuck\ncounters" across two source lines still
    reads as "stuck counters"). Returns {archetype: [missing keys]} for
    archetypes with a gap; empty dict if none."""
    skill = read(SKILL)
    common = _common_state_keys(skill)
    violations: dict[str, list[str]] = {}
    for archetype, path in BODY_PATHS.items():
        keys = [k for k in common + _archetype_state_keys(skill, archetype) if k not in _BOOKKEEPING_KEYS]
        body_text = re.sub(r"\s+", " ", read(path))
        missing = [
            key
            for key in keys
            if re.search(re.sub("_", "[_ ]", key), body_text, re.IGNORECASE) is None
        ]
        if missing:
            violations[archetype] = missing
    return violations


def _axis_matrix_from_skill(skill: str) -> tuple[dict[str, int], dict[str, dict[str, str]], dict[str, set[str]]]:
    start = skill.index("**Axes that vary by archetype**")
    end = skill.index("Max weighted-Hamming distance", start)
    table = skill[start:end]
    rows = [
        ln.strip()
        for ln in table.splitlines()
        if ln.strip().startswith("|") and not re.match(r"^\|[-\s|]+\|$", ln.strip())
    ]

    weights: dict[str, int] = {}
    defaults: dict[str, dict[str, str]] = {"frontier": {}, "goal": {}, "story": {}, "greenfield": {}}
    values: dict[str, set[str]] = {}
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if cells[0].lower() == "axis":
            continue
        axis = cells[0].strip("`")
        values[axis] = {v.strip() for v in cells[1].split("·")}
        defaults["frontier"][axis] = cells[2]
        defaults["goal"][axis] = cells[3]
        defaults["story"][axis] = cells[4]
        defaults["greenfield"][axis] = cells[5]
        weights[axis] = int(cells[6])
    return weights, defaults, values


def classify_mirror_violations() -> list[str]:
    """R3: SKILL.md's locked axis matrix (weights, per-archetype defaults,
    the value sets) must equal classify.py's WEIGHTS/DEFAULTS/VALUES —
    classify.py is documented as a mirror, not a second source of truth, so
    the two must never silently diverge. Also cross-checks the three
    documented contradiction pairs (finite-criteria + equilibrium /
    manual-gated / homeostatic-checkpoint) against classify.contradictions(),
    best-effort — SKILL.md's contradiction prose is not a table, so this half
    is a targeted match on the documented pairs, not a generic parser."""
    skill = read(SKILL)
    v: list[str] = []

    weights, defaults, values = _axis_matrix_from_skill(skill)
    if weights != classify.WEIGHTS:
        v.append(f"weights mismatch: SKILL.md={weights} classify.py={classify.WEIGHTS}")
    for archetype in defaults:
        if defaults[archetype] != classify.DEFAULTS.get(archetype):
            v.append(
                f"{archetype} defaults mismatch: SKILL.md={defaults[archetype]} "
                f"classify.py={classify.DEFAULTS.get(archetype)}"
            )
    for axis, vals in values.items():
        classify_vals = classify.VALUES.get(axis)
        if classify_vals != vals:
            v.append(
                f"{axis} values mismatch: SKILL.md={sorted(vals)} "
                f"classify.py={sorted(classify_vals) if classify_vals else None}"
            )

    contra_start = skill.find("**Contradictions**")
    contra_text = skill[contra_start:contra_start + 400] if contra_start != -1 else ""
    required_tokens = (
        "target: finite-criteria",
        "halt: equilibrium",
        "manual-gated",
        "convergence: homeostatic-checkpoint",
    )
    if contra_start == -1 or any(tok not in contra_text for tok in required_tokens):
        v.append("could not locate the documented contradiction pair text in SKILL.md (mirror check skipped)")
    else:
        documented_bundles = (
            {"target-shape": "finite-criteria", "halt-shape": "equilibrium"},
            {"target-shape": "finite-criteria", "halt-shape": "manual-gated"},
            {"target-shape": "finite-criteria", "convergence-shape": "homeostatic-checkpoint"},
        )
        for bundle in documented_bundles:
            if not classify.contradictions(bundle):
                v.append(f"classify.contradictions() does not flag documented pair: {bundle}")
    return v


def run_checks() -> int:
    try:
        pure = render_frontier(benchmark_overlay=False)
        benchmark = render_frontier(benchmark_overlay=True)
    except ContractError as exc:
        print(f"[FAIL] render_resolves_cleanly: {exc}")
        return 1

    skill = read(SKILL)
    composed = read(COMPOSED_PROMPT)
    benchmark_primitive = read(BENCHMARK_FRONTIER)
    pressure_primitive = read(PRESSURE_ACCOUNTING)
    benchmark_artifacts = read(BENCHMARK_ARTIFACTS)
    benchmark_flat = one_line(benchmark)
    primitive_flat = one_line(benchmark_primitive)
    stale_completion_token = "frontier" + "_complete"

    checks: list[tuple[bool, str]] = []

    checks.append(require(True, "render_resolves_cleanly"))

    checks.append(
        require(
            not missing_tokens(pure, PRESSURE_REQUIRED),
            "pure_frontier_has_pressure_accounting",
            ", ".join(missing_tokens(pure, PRESSURE_REQUIRED)),
        )
    )
    checks.append(
        require(
            not leaked_patterns(pure, PURE_FRONTIER_BANNED_PATTERNS),
            "pure_frontier_excludes_benchmark_roles",
            ", ".join(leaked_patterns(pure, PURE_FRONTIER_BANNED_PATTERNS)),
        )
    )
    checks.append(
        require(
            not missing_patterns(benchmark, BENCHMARK_REQUIRED_PATTERNS),
            "benchmark_frontier_includes_candidate_frontier_trace_eval_roles",
            ", ".join(missing_patterns(benchmark, BENCHMARK_REQUIRED_PATTERNS)),
        )
    )
    checks.append(
        require(
            not leaked_patterns(pure, BENCHMARK_REQUIRED_PATTERNS),
            "pure_frontier_excludes_overlay_specific_required_tokens",
            ", ".join(leaked_patterns(pure, BENCHMARK_REQUIRED_PATTERNS)),
        )
    )
    checks.append(
        require(
            "do **not** participate in classification distance" in skill
            and "benchmark-frontier" in skill,
            "benchmark_overlay_documented_outside_weighted_hamming",
        )
    )
    checks.append(
        require(
            "not a fifth archetype" in primitive_flat
            and "not a weighted classification axis" in primitive_flat,
            "benchmark_overlay_not_fifth_archetype",
        )
    )
    checks.append(
        require(
            "{{BENCHMARK_FRONTIER_MODE}}" in read(FRONTIER_BODY)
            and "Pure frontier keeps" in composed,
            "composition_has_conditional_benchmark_insert",
        )
    )
    checks.append(
        require(
            stale_completion_token not in pure
            and stale_completion_token not in benchmark
            and not stale_deferred_status(pure)
            and not stale_deferred_status(benchmark),
            "stale_completion_and_deferred_statuses_absent",
        )
    )
    checks.append(
        require(
            "Green search traces, zero OPEN generic findings" in benchmark_flat
            and "are not a checkpoint" in benchmark_flat
            and "must expand one of: candidate, case, control" in benchmark_flat,
            "weave_green_traces_shape_rejected",
        )
    )
    checkpoint_reason_missing = sorted(
        {
            token
            for text in (pure, pressure_primitive, benchmark_artifacts)
            for token in missing_tokens(text, CHECKPOINT_REASON_VALUES)
        }
    )
    checks.append(
        require(
            not checkpoint_reason_missing,
            "checkpoint_reason_enum_consistent",
            ", ".join(checkpoint_reason_missing),
        )
    )

    checkpoint_closedset = checkpoint_reason_closedset_violations()
    checks.append(
        require(
            not checkpoint_closedset,
            "checkpoint_reason_closed_set",
            "; ".join(checkpoint_closedset),
        )
    )

    include_targets = include_target_violations()
    checks.append(
        require(
            not include_targets,
            "include_targets_resolvable",
            "; ".join(include_targets),
        )
    )

    pressure_leaks: list[str] = []
    if PRESSURE_ACCOUNTING_INCLUDE not in read(FRONTIER_BODY):
        pressure_leaks.append("frontier body missing pressure-accounting include")
    for body in NON_FRONTIER_BODIES:
        if not body.exists():
            pressure_leaks.append(f"{body.name}: missing body template")
            continue
        body_text = read(body)
        if PRESSURE_ACCOUNTING_INCLUDE in body_text:
            pressure_leaks.append(f"{body.name}: pressure-accounting include marker")
        present = [token for token in PRESSURE_REQUIRED if token in body_text]
        if present:
            pressure_leaks.append(f"{body.name}: {', '.join(present)}")
    checks.append(
        require(
            not pressure_leaks,
            "pressure_accounting_only_in_pure_frontier",
            ", ".join(pressure_leaks),
        )
    )

    fixture_failures = [
        label
        for label, row, expect_valid in CANDIDATE_ROW_FIXTURES
        if (not candidate_row_violations(row)) != expect_valid
    ]
    checks.append(
        require(
            not fixture_failures,
            "candidate_row_contract_fixtures",
            ", ".join(fixture_failures),
        )
    )

    bijection = oracle_integrity_bijection_violations()
    checks.append(
        require(
            not bijection,
            "oracle_integrity_row_property_trace_bijection",
            "; ".join(bijection),
        )
    )

    seed_gate = seed_double_gate_violations()
    checks.append(
        require(
            not seed_gate,
            "oracle_integrity_seed_double_gated",
            "; ".join(seed_gate),
        )
    )

    authority = oracle_integrity_authority_violations()
    checks.append(
        require(
            not authority,
            "oracle_integrity_source_and_status_well_defined",
            "; ".join(authority),
        )
    )

    shared_causes = halt_shared_cause_violations()
    checks.append(
        require(
            not shared_causes,
            "halt_shared_causes_consistent",
            "; ".join(shared_causes),
        )
    )

    checks.append(
        require(
            "Never emit language that pretends anti-collapse" in pure,
            "frontier_degraded_coverage_present",
        )
    )

    cross_pins = cross_file_pin_violations()
    checks.append(
        require(
            not cross_pins,
            "cross_file_restatements_pinned",
            "; ".join(cross_pins),
        )
    )

    for archetype in ("frontier", "goal", "story", "greenfield"):
        try:
            render_body(archetype)
            checks.append(require(True, f"render_body_dead_sections_{archetype}"))
        except (ContractError, AssertionError) as exc:
            checks.append(require(False, f"render_body_dead_sections_{archetype}", str(exc)))

    try:
        render_body("story", consult_tier=1)
        checks.append(require(True, "render_body_subagent_patterns_tier1"))
    except (ContractError, AssertionError) as exc:
        checks.append(require(False, "render_body_subagent_patterns_tier1", str(exc)))

    read_set_missing = derivation_read_set_violations()
    checks.append(
        require(
            not read_set_missing,
            "derivation_read_set_paths_exist",
            ", ".join(read_set_missing),
        )
    )

    state_key_missing = state_key_body_violations()
    checks.append(
        require(
            not state_key_missing,
            "state_keys_mentioned_in_body",
            "; ".join(f"{archetype}: {', '.join(keys)}" for archetype, keys in state_key_missing.items()),
        )
    )

    classify_mirror = classify_mirror_violations()
    checks.append(
        require(
            not classify_mirror,
            "classify_py_mirrors_skill_axis_matrix",
            "; ".join(classify_mirror),
        )
    )

    ok = True
    for passed, line in checks:
        ok = ok and passed
        print(line)

    pure_lines = len(pure.splitlines())
    benchmark_lines = len(benchmark.splitlines())
    print(f"pure_frontier_lines={pure_lines}")
    print(f"benchmark_frontier_lines={benchmark_lines}")
    print(f"benchmark_overlay_delta={benchmark_lines - pure_lines}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--print":
        if argv[2] == "pure-frontier":
            print(render_frontier(benchmark_overlay=False))
            return 0
        if argv[2] == "benchmark-frontier":
            print(render_frontier(benchmark_overlay=True))
            return 0
        print("usage: verify_loopgen_contracts.py [--print pure-frontier|benchmark-frontier]", file=sys.stderr)
        return 2
    if len(argv) != 1:
        print("usage: verify_loopgen_contracts.py [--print pure-frontier|benchmark-frontier]", file=sys.stderr)
        return 2
    return run_checks()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
