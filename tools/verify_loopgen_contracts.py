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
CONTEXT_STACK = ROOT / "loopgen/primitives/context-stack.md"
PRESSURE = ROOT / "loopgen/primitives/pressure.md"

NON_FRONTIER_BODIES = (
    GOAL_BODY,
    STORY_BODY,
    GREENFIELD_BODY,
)
PRESSURE_ACCOUNTING_INCLUDE = "{{INCLUDE primitives/pressure-accounting.md}}"
CONTEXT_STACK_INCLUDE = "{{INCLUDE primitives/context-stack.md}}"
QUEUE_INCLUDE = "{{INCLUDE primitives/queue-as-second-artifact.md}}"

# The context-stack memory model (ADR 0004). The single JOURNAL.jsonl history
# surface enumerates exactly these record types; the STATE.md keys that used to
# be append-only history now live in JOURNAL.jsonl or DERIVATION.md, so they must
# be absent from every STATE.md key list.
JOURNAL_RECORD_TYPES = (
    "attempt",
    "oracle_change",
    "pressure",
    "consult",
    "alignment_review",
    "checkpoint",
    "halt",
    "score_quarantine",
    "bootstrap",
    "consolidation",
)

NO_PROMOTION_REASONS = (
    "duplicate-of",
    "covered-by",
    "out-of-scope",
    "transient-flake",
    "criterion-local",
    "reverted-before-effect",
)
MOVED_STATE_KEYS = (
    "pressure_ledger",
    "pressure_consulted",
    "oracle_change_notes",
    "capability_list",
    "primitive_bundle",
    "divergences",
    "overlays",
    "derivation_read_set",
    "frontload",
)

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
    # Always-on emitted slots, filled for every composed prompt.
    "PROVENANCE": "> Loop provenance — composed by /loopgen (verifier fixture).",
    "FRONTLOAD_PREAMBLE": "> Frontload — resolved: [motive]; defaulted: [thresholds]; open gaps: [none].",
    # PRESSURE_SURFACE is now ALWAYS-ON (ADR 0004): render_frontier / render_body
    # substitute the pressure.md block directly, so it is not a static "" here.
    # {{SUBAGENT_PATTERNS}} stays gated — emitted only at consult-tier >= 1; the
    # verifier renders the tier-0 pure case, so it is stripped (empty) exactly as
    # composed-prompt.md step 8 strips it.
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


FRONTIER_REOPEN_POLICY_FILE = ROOT / "loopgen/templates/bodies/frontier-reopen-policy.md"

REOPEN_POLICY_HEADINGS = {
    "equilibrium": "## Equilibrium variant",
    "terminal": "## Terminal variant",
}


def reopen_policy_variant(variant: str) -> str:
    """Extract a {{FRONTIER_REOPEN_POLICY}} variant from its authoring file by
    heading (composed-prompt.md steps 3/5). The verifier never duplicates the
    block text — the file is the single source."""
    heading = REOPEN_POLICY_HEADINGS[variant]
    raw = read(FRONTIER_REOPEN_POLICY_FILE)
    start = raw.index(heading) + len(heading)
    next_headings = [
        raw.index(h, start) for h in REOPEN_POLICY_HEADINGS.values() if h in raw[start:]
    ]
    end = min(next_headings) if next_headings else len(raw)
    return raw[start:end].strip("\n")


def render_frontier(
    *,
    benchmark_overlay: bool,
    reopen_policy: str = "equilibrium",
    placeholder_overrides: dict[str, str] | None = None,
) -> str:
    prompt = frontier_template()
    mode = benchmark_mode() if benchmark_overlay else ""
    prompt = prompt.replace("{{BENCHMARK_FRONTIER_MODE}}", mode)
    prompt = prompt.replace(
        "{{FRONTIER_REOPEN_POLICY}}", reopen_policy_variant(reopen_policy)
    )
    prompt = re.sub(r"\{\{INCLUDE ([^}]+)\}\}", include_text, prompt)
    # Pressure surface is always-on (ADR 0004): substitute the pressure.md block.
    prompt = prompt.replace("{{PRESSURE_SURFACE}}", resolve_gated_block(PRESSURE))
    placeholders = dict(PLACEHOLDERS)
    if placeholder_overrides:
        placeholders.update(placeholder_overrides)
    for key, value in placeholders.items():
        prompt = prompt.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{[^}]+\}\}", prompt)))
    if leftovers:
        raise AssertionError(f"unsubstituted placeholders: {leftovers}")
    return prompt


# ── playbook render + frozen golden (R3, dev/plans/2026-06-23-001 U4) ──
# The playbook is the executable portion of the rendered frontier prompt:
# everything except the provenance preamble and the frontload preamble, which
# legitimately vary per composition (provenance/frontload metadata is out of
# R3's byte-identity scope). Fixed sentinels keep the render deterministic and
# independent of the metadata-bearing fixtures, so frontload/provenance
# contract changes (e.g. new reopening-contract fields) never dirty the golden.

GOLDEN_DIR = ROOT / "tools/golden"
FRONTIER_EQUILIBRIUM_GOLDEN = GOLDEN_DIR / "frontier-body.equilibrium.md"

PLAYBOOK_SENTINELS = {
    "PROVENANCE": "(provenance preamble — out of playbook scope)",
    "FRONTLOAD_PREAMBLE": "(frontload preamble — out of playbook scope)",
}


def render_frontier_playbook() -> str:
    """Pure-frontier playbook (effective-equilibrium reopen policy, no
    benchmark overlay), provenance/frontload normalized to fixed sentinels.
    This is the surface the frozen golden pins byte-for-byte.

    Regeneration path for INTENTIONAL playbook edits:
    `python3 tools/verify_loopgen_contracts.py --capture-golden` (then commit
    the golden together with the edit that moved it)."""
    return render_frontier(
        benchmark_overlay=False, placeholder_overrides=PLAYBOOK_SENTINELS
    )


# ── guarded halt-shape resolution: executable spec (U4b) ──
# Mirrors primitives/halt-shape.md's guarded closed-corpus resolution the way
# classify.py mirrors SKILL.md's axis matrix; the guard_prose_conjuncts check
# pins the prose so the two cannot drift silently. Field encoding: a named
# value is the string itself; "none" is the literal token; None means the
# field is absent (legacy artifacts / fixtures only — a fresh frontier
# composition must emit the fields); "unresolved" means frontload could not
# resolve it.


class DerivationGap(Exception):
    """Non-emittable path: an open_gaps entry, never a silent default."""


CLOSURE_BASIS_KEYS = ("work_source_domain", "declared_surfaces", "exhaustion_criterion")


def closure_basis_established(closure_basis: dict | None) -> bool:
    """The compose-time closure contract: an enumerated observable work-source
    domain, the declared search surfaces, and the criterion that will establish
    declared-workset exhaustion at runtime. All three, non-empty — a bare flag
    cannot prove a closed-world inference."""
    return isinstance(closure_basis, dict) and all(
        closure_basis.get(key) for key in CLOSURE_BASIS_KEYS
    )


def resolve_effective_halt_shape(
    *,
    archetype: str,
    requested: str,
    reopening_signal: str | None,
    reopen_contract: str | None,
    closure_basis: dict | None,
) -> tuple[str, bool]:
    """Returns (effective_halt_shape, compiler_derived_divergence)."""
    if archetype != "frontier":
        return requested, False
    if reopening_signal is None and reopen_contract is None:
        # Backward-compatibility ONLY (pre-existing artifacts, fixtures):
        # composition-side, absent fields are a derivation gap for frontier.
        return requested, False
    if reopening_signal is None or reopen_contract is None:
        # A fresh composition emits both fields together; one without the
        # other is incomplete frontload evidence, never a resolvable state.
        raise DerivationGap("partially recorded reopening contract")
    if "unresolved" in (reopening_signal, reopen_contract):
        raise DerivationGap("reopening contract unresolved")
    named_signal = reopening_signal != "none"
    named_contract = reopen_contract != "none"
    if named_signal and not named_contract:
        raise DerivationGap("named signal without an observable delivery channel")
    if named_contract and not named_signal:
        raise DerivationGap("delivery channel without a named signal")
    if not named_signal and not named_contract:
        if not closure_basis_established(closure_basis):
            raise DerivationGap(
                "reopen_contract none without an established closure basis "
                f"(needs non-empty {', '.join(CLOSURE_BASIS_KEYS)})"
            )
        if requested == "equilibrium":
            return "terminal", True  # the guarded implication
        return requested, False  # explicit terminal honored as requested
    return requested, False  # live reopen contract → pass through


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
    # PRESSURE_SURFACE is always-on (ADR 0004) — render_body substitutes the
    # pressure.md block directly. {{SUBAGENT_PATTERNS}} stays gated: stripped at
    # tier-0, filled by render_body(..., consult_tier=N).
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
        prompt = prompt.replace(
            "{{FRONTIER_REOPEN_POLICY}}", reopen_policy_variant("equilibrium")
        )
    prompt = re.sub(r"\{\{INCLUDE ([^}]+)\}\}", include_text, prompt)
    # Pressure surface is always-on (ADR 0004).
    prompt = prompt.replace("{{PRESSURE_SURFACE}}", resolve_gated_block(PRESSURE))

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


# ── U11: context-stack memory-model contracts ──────────────────────────────


def _context_stack_archetype_keys(cs: str) -> dict[str, list[str]]:
    """Parse context-stack.md's `| <archetype> | <backticked keys> |` per-archetype
    STATE-key table into {archetype: [keys]}."""
    result: dict[str, list[str]] = {}
    for arch in ("goal", "story", "frontier", "greenfield"):
        m = re.search(rf"(?m)\|\s*`{arch}`\s*\|\s*(.+?)\s*\|\s*$", cs)
        if m:
            result[arch] = re.findall(r"`([a-z_]+)`", m.group(1))
    return result


def _context_stack_journal_types(cs: str) -> list[str]:
    """The record-type column of context-stack.md's JOURNAL.jsonl table (dropping
    the `t` header cell)."""
    i = cs.find("Record types (`t`)")
    if i == -1:
        return []
    block = cs[i:]
    j = block.find("Access:")
    if j != -1:
        block = block[:j]
    return [t for t in re.findall(r"(?m)^\|\s*`([a-z_]+)`\s*\|", block) if t != "t"]


def body_include_violations() -> list[str]:
    """U11: every archetype body must INCLUDE both `context-stack.md` and the
    queue-growth block — the two primitives SKILL.md claims every body carries
    (the audit caught the queue claim being false while no body wired it). A body
    that drops either INCLUDE silently loses the memory model / growth discipline."""
    v: list[str] = []
    for arch, path in BODY_PATHS.items():
        text = read(path)
        if CONTEXT_STACK_INCLUDE not in text:
            v.append(f"{arch} body missing {CONTEXT_STACK_INCLUDE}")
        if QUEUE_INCLUDE not in text:
            v.append(f"{arch} body missing {QUEUE_INCLUDE}")
    skill = read(SKILL)
    if "context-stack" not in skill:
        v.append("SKILL.md does not claim context-stack is emitted every prompt")
    if "queue-as-second-artifact" not in skill:
        v.append("SKILL.md does not claim queue-as-second-artifact is wired")
    return v


def tiered_read_violations() -> list[str]:
    """U11: no body's iteration protocol may mandate an unqualified whole-file read
    of an append-only artifact — each body's read step must carry the tiered-read
    vocabulary (a bounded `tail -n 20` journal read and an `index` queue read). A
    regression to whole-file reads drops these tokens."""
    v: list[str] = []
    for arch, path in BODY_PATHS.items():
        text = read(path)
        if "tail -n 20" not in text:
            v.append(f"{arch}: no bounded `tail -n 20` journal read in the protocol")
        if "index" not in text.lower():
            v.append(f"{arch}: no index/bounded queue-read language in the protocol")
    return v


def state_key_mirror_violations() -> list[str]:
    """U11: SKILL.md's STATE-key lists must mirror context-stack.md's schema, and
    every key moved out of STATE.md (to DERIVATION.md or JOURNAL.jsonl) must be
    absent from both SKILL STATE lists (common + per-archetype)."""
    skill = read(SKILL)
    cs = read(CONTEXT_STACK)
    v: list[str] = []

    common = _common_state_keys(skill)
    skill_state: set[str] = set(common)
    skill_arch: dict[str, set[str]] = {}
    for a in ("goal", "story", "frontier", "greenfield"):
        keys = set(_archetype_state_keys(skill, a))
        skill_arch[a] = keys
        skill_state |= keys

    for mk in MOVED_STATE_KEYS:
        if mk in skill_state:
            v.append(f"moved key `{mk}` still listed as a STATE.md key in SKILL.md")

    for k in common:
        if f"`{k}`" not in cs:
            v.append(f"SKILL common STATE key `{k}` absent from context-stack.md schema")

    cs_arch = _context_stack_archetype_keys(cs)
    for a in ("goal", "story", "frontier", "greenfield"):
        ck = set(cs_arch.get(a, []))
        if skill_arch[a] != ck:
            v.append(
                f"{a} STATE-key mirror mismatch: SKILL={sorted(skill_arch[a])} "
                f"context-stack={sorted(ck)}"
            )
    return v


def journal_enum_violations() -> list[str]:
    """U11: the JOURNAL.jsonl record-type enumeration must agree across
    context-stack.md (the schema table) and SKILL.md (the common-file contract),
    and context-stack.md's table must list exactly the canonical set."""
    cs = read(CONTEXT_STACK)
    skill = read(SKILL)
    v: list[str] = []
    canonical = set(JOURNAL_RECORD_TYPES)
    for t in JOURNAL_RECORD_TYPES:
        if f"`{t}`" not in cs:
            v.append(f"context-stack.md missing journal record type `{t}`")
        if f"`{t}`" not in skill:
            v.append(f"SKILL.md missing journal record type `{t}`")
    table = set(_context_stack_journal_types(cs))
    if table - canonical:
        v.append(f"context-stack journal table has non-canonical types: {sorted(table - canonical)}")
    if canonical - table:
        v.append(f"context-stack journal table missing types: {sorted(canonical - table)}")
    return v


def u13_hardening_violations() -> list[str]:
    """U13: the pre-ship hardening contracts (ADR 0004 amendment). The static
    verifier cannot prove runtime obedience, but it can prove the in-loop
    detector and the authority rules actually ride the emitted text:
    context-health check present and routed, tiers bound to access paths (no
    stale one-tier-per-artifact phrasing), queue index authoritative
    (single-writer), evidence write-ahead, structured no-promotion enum, and
    pressure decay/merge-before-halt."""
    v: list[str] = []
    cs = read(CONTEXT_STACK)
    composed = read(COMPOSED_PROMPT)
    queue = read(ROOT / "loopgen/primitives/queue-as-second-artifact.md")
    pressure = read(ROOT / "loopgen/primitives/pressure.md")

    emitted = cs.split("\n---\n", 1)[-1]
    if "### Context-health check" not in emitted:
        v.append("context-stack emitted block missing `### Context-health check`")
    for marker in ("parses as JSONL", "resolve", "index row", "pressure-cap", "derivation-gap"):
        if marker not in emitted:
            v.append(f"context-health block missing marker `{marker}`")
    if "write-ahead" not in emitted:
        v.append("context-stack emitted block missing evidence write-ahead rule")
    if "never truncate a required field" not in emitted:
        v.append("context-stack emitted block missing the no-truncation rule on journal records")
    if "access path" not in cs.split("\n---\n", 1)[0] or "access path" not in emitted:
        v.append("context-stack tiers not bound to access paths on both sides of ---")
    for stale in ("artifact is assigned **exactly one** tier", "artifact below has exactly one tier"):
        if stale in cs:
            v.append(f"stale one-tier-per-artifact phrasing survives: `{stale}`")
    if composed.lower().count("context-health check") < 2:
        v.append("composed-prompt.md Operational core spec must name the context-health check in §3a and assembly step 4")
    if "single-writer" not in queue or "index is authoritative" not in queue.lower():
        v.append("queue-as-second-artifact missing the index-authoritative single-writer rule")
    for reason in NO_PROMOTION_REASONS:
        if reason not in pressure:
            v.append(f"pressure.md no-promotion enum missing `{reason}`")
    if "no-effect" not in pressure or "consecutive consults" not in pressure:
        v.append("pressure.md missing repeated-no-effect decay rule")
    if "merge/retire pass first" not in pressure:
        v.append("pressure.md cap overflow must run a merge/retire pass before halting")
    return v


def u14_consolidation_violations() -> list[str]:
    """U14: the consolidation round is the contract-layer checkpoint (ADR 0005).
    Prove the emitted contracts carry the round: forced triggers alongside the
    cadence, the field read over the pressure set, the three-way substrate
    classification, debt-conserving merge, the recorded decision, the
    context-health consolidation line, the HUD recency stamp, and the
    stand-alone constraint on compose-time lens borrowing."""
    v: list[str] = []
    cs = read(CONTEXT_STACK)
    composed = read(COMPOSED_PROMPT)
    pressure = read(ROOT / "loopgen/primitives/pressure.md")

    emitted = cs.split("\n---\n", 1)[-1]
    if "### Consolidation round" not in emitted:
        v.append("context-stack emitted block missing the `### Consolidation round` section")
    for marker in (
        "correct-looking fixes",
        "impossible observation",
        "checked at\n   runtime",
        "inferred from config",
        "unverified",
        "suspected_substrate",
    ):
        if marker.replace("\n   ", " ") not in emitted.replace("\n   ", " "):
            v.append(f"consolidation round missing marker `{marker}`")
    health = emitted.split("### Context-health check", 1)[-1]
    if "consolidation" not in health:
        v.append("context-health check missing the consolidation-due line (line 7)")
    if "run the Consolidation round now" not in health:
        v.append("context-health routing missing the overdue/triggered-consolidation route")

    pressure_emitted = pressure.split("\n---\n", 1)[-1]
    if "## Consolidation" not in pressure_emitted:
        v.append("pressure.md emitted block missing the consolidation field-read section")
    for marker in ("one\nfield", "merged-into", "suspected_substrate", "last consolidation: iter N"):
        if marker.replace("\n", " ") not in pressure_emitted.replace("\n", " "):
            v.append(f"pressure.md field read missing marker `{marker}`")
    if "never a launder" not in pressure_emitted:
        v.append("pressure.md merge must be marked as never a launder (debt conserved)")

    flat_composed = " ".join(composed.split())
    if "never as a required dependency" not in flat_composed or "stand alone" not in flat_composed:
        v.append("composed-prompt.md lens borrowing missing the stand-alone / no-required-dependency constraint")
    return v


def run_checks() -> int:
    try:
        pure = render_frontier(benchmark_overlay=False)
        benchmark = render_frontier(benchmark_overlay=True)
    except (ContractError, AssertionError) as exc:
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

    # ── U11: context-stack memory-model contracts ──────────────────────────
    body_includes = body_include_violations()
    checks.append(
        require(
            not body_includes,
            "bodies_include_context_stack_and_queue",
            "; ".join(body_includes),
        )
    )

    tiered = tiered_read_violations()
    checks.append(
        require(
            not tiered,
            "bodies_use_tiered_reads",
            "; ".join(tiered),
        )
    )

    key_mirror = state_key_mirror_violations()
    checks.append(
        require(
            not key_mirror,
            "state_key_skill_context_stack_mirror",
            "; ".join(key_mirror),
        )
    )

    journal_enum = journal_enum_violations()
    checks.append(
        require(
            not journal_enum,
            "journal_record_types_consistent",
            "; ".join(journal_enum),
        )
    )

    # Always-on pressure surface + context budget must actually reach the emitted
    # prompt now (fixtures render PRESSURE_SURFACE always-on, ADR 0004).
    checks.append(
        require(
            "Mandatory promotion" in pure and "Context budget" in pure,
            "frontier_pressure_and_budget_emitted",
        )
    )
    goal_render = render_body("goal")
    checks.append(
        require(
            "final-verify not yet run" in goal_render,
            "goal_verify_header_only_guard",
        )
    )
    checks.append(
        require(
            "Mandatory promotion" in goal_render and "Context budget" in goal_render,
            "goal_pressure_and_budget_emitted",
        )
    )

    # ── U13: pre-ship hardening (ADR 0004 amendment) ────────────────────────
    hardening = u13_hardening_violations()
    checks.append(
        require(
            not hardening,
            "u13_hardening_contracts",
            "; ".join(hardening),
        )
    )
    checks.append(
        require(
            "Context-health check" in pure and "Context-health check" in goal_render,
            "context_health_emitted",
        )
    )

    # ── U14: consolidation round = contract-layer checkpoint (ADR 0005) ─────
    consolidation = u14_consolidation_violations()
    checks.append(
        require(
            not consolidation,
            "u14_consolidation_contracts",
            "; ".join(consolidation),
        )
    )
    checks.append(
        require(
            all(
                "Consolidation round" in render and "suspected_substrate" in render
                for render in (pure, goal_render)
            ),
            "consolidation_emitted",
        )
    )

    # ── reopen-policy block + guarded halt-shape resolution (U4b) ──
    playbook_equilibrium = render_frontier_playbook()
    golden_exists = FRONTIER_EQUILIBRIUM_GOLDEN.exists()
    checks.append(
        require(
            golden_exists,
            "frontier_playbook_golden_present",
            "missing tools/golden/frontier-body.equilibrium.md — run --capture-golden",
        )
    )
    if golden_exists:
        golden = FRONTIER_EQUILIBRIUM_GOLDEN.read_text(encoding="utf-8")
        checks.append(
            require(
                playbook_equilibrium == golden,
                "body_equilibrium_byte_identical",
                "playbook drifted from the frozen golden; if the edit was "
                "intentional, re-run --capture-golden and commit the golden "
                "with the edit that moved it",
            )
        )

    try:
        playbook_terminal = render_frontier(
            benchmark_overlay=False,
            reopen_policy="terminal",
            placeholder_overrides=PLAYBOOK_SENTINELS,
        )
        terminal_render_error = ""
    except (ContractError, AssertionError, KeyError) as exc:
        playbook_terminal = ""
        terminal_render_error = str(exc)
    checks.append(
        require(
            not terminal_render_error,
            "reopen_policy_terminal_renders",
            terminal_render_error,
        )
    )
    terminal_flat = one_line(playbook_terminal)
    equilibrium_flat = one_line(playbook_equilibrium)
    required_terminal_tokens = (
        "iteration halted; frontier episode terminated (declared workset exhausted)",
        "terminal reopen policy",
        "does not auto-resume",
        "an explicit per-row `reopen_condition`, a regression, or a new "
        "declared-workset version",
        "frontier episode paused",
    )
    banned_terminal_tokens = (
        "iteration halted; frontier checkpointed",
        "reopens automatically on strong new signal",
        # Policy-assuming common prose repaired in the review round: a terminal
        # render carrying any of these contradicts its own policy block.
        "A frontier halt is a checkpoint",
        "legitimate checkpoint",
        "the loop is at frontier equilibrium",
        "homeostatic-checkpoint` equilibrium",
        # The variant text serves BOTH the guarded resolution and an explicitly
        # requested terminal (which may hold a live contract): it must never
        # assert frontload field values.
        "reopen_contract: none",
    )
    checks.append(
        require(
            not missing_tokens(terminal_flat, required_terminal_tokens),
            "body_terminal_semantics",
            ", ".join(missing_tokens(terminal_flat, required_terminal_tokens)),
        )
    )
    checks.append(
        require(
            bool(terminal_flat)
            and all(token not in terminal_flat for token in banned_terminal_tokens),
            "body_terminal_no_equilibrium_residue",
            "; ".join(t for t in banned_terminal_tokens if t in terminal_flat),
        )
    )
    checks.append(
        require(
            "has no quality pass-line" in terminal_flat
            and "has no quality pass-line" in equilibrium_flat,
            "objective_no_pass_line_claim_in_both_variants",
        )
    )

    reopen_policy_leaks = [
        path.name
        for path in NON_FRONTIER_BODIES
        if "FRONTIER_REOPEN_POLICY" in read(path)
        or "frontier episode terminated" in one_line(read(path))
    ]
    checks.append(
        require(
            not reopen_policy_leaks,
            "reopen_policy_frontier_only",
            ", ".join(reopen_policy_leaks),
        )
    )

    full_closure = dict(
        work_source_domain="enumerated: no inbound CI/review/schedule/dep-alert",
        declared_surfaces="duplication scan + findings ledger + oracle gaps",
        exhaustion_criterion="full homeostasis scan quiescent under declared surfaces",
    )
    guard_cases: list[tuple[str, dict, object]] = [
        (
            "named signal + channel → equilibrium, no divergence",
            dict(
                requested="equilibrium",
                reopening_signal="new reviewed findings",
                reopen_contract="inbox note delivered via scheduled re-run",
                closure_basis=None,
            ),
            ("equilibrium", False),
        ),
        (
            "none + enumerated domain + closure basis → guarded terminal",
            dict(
                requested="equilibrium",
                reopening_signal="none",
                reopen_contract="none",
                closure_basis=full_closure,
            ),
            ("terminal", True),
        ),
        (
            "none without closure basis → gap",
            dict(
                requested="equilibrium",
                reopening_signal="none",
                reopen_contract="none",
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "named signal without delivery channel → gap",
            dict(
                requested="equilibrium",
                reopening_signal="upstream release",
                reopen_contract="none",
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "delivery channel without named signal → gap",
            dict(
                requested="equilibrium",
                reopening_signal="none",
                reopen_contract="ci webhook",
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "fields absent → legacy equilibrium, no divergence",
            dict(
                requested="equilibrium",
                reopening_signal=None,
                reopen_contract=None,
                closure_basis=None,
            ),
            ("equilibrium", False),
        ),
        (
            "unresolved → non-emittable",
            dict(
                requested="equilibrium",
                reopening_signal="unresolved",
                reopen_contract="unresolved",
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "explicitly requested terminal → terminal, no compiler divergence",
            dict(
                requested="terminal",
                reopening_signal="none",
                reopen_contract="none",
                closure_basis=full_closure,
            ),
            ("terminal", False),
        ),
        (
            "explicit terminal + live contract → terminal, no compiler divergence",
            dict(
                requested="terminal",
                reopening_signal="upstream release",
                reopen_contract="dep-alert delivered via scheduled re-run",
                closure_basis=None,
            ),
            ("terminal", False),
        ),
        (
            "signal recorded without the contract field → gap (partial absence)",
            dict(
                requested="equilibrium",
                reopening_signal="upstream release",
                reopen_contract=None,
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "contract recorded without the signal field → gap (partial absence)",
            dict(
                requested="equilibrium",
                reopening_signal=None,
                reopen_contract="none",
                closure_basis=None,
            ),
            DerivationGap,
        ),
        (
            "none + incomplete closure evidence → gap (bare flag insufficient)",
            dict(
                requested="equilibrium",
                reopening_signal="none",
                reopen_contract="none",
                closure_basis=dict(
                    work_source_domain="enumerated: none inbound",
                    declared_surfaces="",
                    exhaustion_criterion="",
                ),
            ),
            DerivationGap,
        ),
    ]
    guard_failures: list[str] = []
    for case_name, kwargs, expected in guard_cases:
        try:
            got: object = resolve_effective_halt_shape(archetype="frontier", **kwargs)
        except DerivationGap:
            got = DerivationGap
        if got != expected:
            guard_failures.append(f"{case_name} (got {got!r})")
    if resolve_effective_halt_shape(
        archetype="goal",
        requested="terminal",
        reopening_signal=None,
        reopen_contract=None,
        closure_basis=None,
    ) != ("terminal", False):
        guard_failures.append("non-frontier passthrough")
    checks.append(
        require(
            not guard_failures,
            "guarded_halt_resolution_paths",
            "; ".join(guard_failures),
        )
    )

    halt_shape_flat = one_line(read(ROOT / "loopgen/primitives/halt-shape.md"))
    guard_conjunct_tokens = (
        "requested halt-shape == equilibrium",
        "reopen_contract == none",
        "closure_basis established",
        "not** a biconditional",
        "effective halt-shape := terminal",
        "{requested, effective, resolution_basis}",
    )
    checks.append(
        require(
            not missing_tokens(halt_shape_flat, guard_conjunct_tokens),
            "guard_prose_conjuncts",
            ", ".join(missing_tokens(halt_shape_flat, guard_conjunct_tokens)),
        )
    )
    context_stack_flat = one_line(read(CONTEXT_STACK))
    checks.append(
        require(
            "{requested, effective, resolution_basis}" in context_stack_flat,
            "divergence_triple_durable_in_derivation",
            "DERIVATION.md divergences must define the "
            "{requested, effective, resolution_basis} triple for "
            "compiler-derived halt-shape resolution",
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
    print(
        "frontier_terminal_policy_delta="
        f"{len(playbook_terminal.splitlines()) - len(playbook_equilibrium.splitlines())}"
    )
    return 0 if ok else 1


USAGE = (
    "usage: verify_loopgen_contracts.py "
    "[--print pure-frontier|benchmark-frontier|frontier-playbook] "
    "[--capture-golden]"
)


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--print":
        if argv[2] == "pure-frontier":
            print(render_frontier(benchmark_overlay=False))
            return 0
        if argv[2] == "benchmark-frontier":
            print(render_frontier(benchmark_overlay=True))
            return 0
        if argv[2] == "frontier-playbook":
            print(render_frontier_playbook())
            return 0
        print(USAGE, file=sys.stderr)
        return 2
    if len(argv) == 2 and argv[1] == "--capture-golden":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        FRONTIER_EQUILIBRIUM_GOLDEN.write_text(
            render_frontier_playbook(), encoding="utf-8"
        )
        print(f"captured {FRONTIER_EQUILIBRIUM_GOLDEN.relative_to(ROOT)}")
        return 0
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    return run_checks()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
