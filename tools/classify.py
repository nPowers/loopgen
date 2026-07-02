#!/usr/bin/env python3
"""
classify.py — optional deterministic mirror of loopgen Phase 2 classification.

This script does NOT classify raw task text — that is the host LLM's job (the
semantic extraction). It takes the LLM's already-extracted 5-axis intent bundle
and mechanically computes the parts that are pure arithmetic + table lookup:
weighted-Hamming distance to each archetype, the nearest archetype + margin,
and any contradiction / forbidden-divergence hits.

It is a MIRROR, not a dependency. SKILL.md's prose remains the single source of
truth; loopgen works with no Python interpreter present. Use this to make the
single most consequential derivation step (classification) reproducible and
auditable, and to drop the resulting distance table into the provenance preamble.

Usage:
    classify.py --self-test
    classify.py '{"target-shape":"frontier-expanding","halt-shape":"equilibrium",
                   "artifact-shape":"findings-ledger",
                   "convergence-shape":"homeostatic-checkpoint",
                   "cadence-shape":"checkpoint-gated"}'
    echo '<bundle json>' | classify.py

`consult-capability` is environment-detected, NOT a classification axis — it is
ignored here by design (it overlays composition, it does not steer distance).
"""

import json
import sys

# --- The locked matrix (mirror of SKILL.md "Axes that vary by archetype") ---
WEIGHTS = {
    "target-shape": 3,
    "halt-shape": 3,
    "artifact-shape": 3,
    "convergence-shape": 2,
    "cadence-shape": 1,
}
MAX_DISTANCE = sum(WEIGHTS.values())  # 12

DEFAULTS = {
    "frontier":   {"target-shape": "frontier-expanding", "halt-shape": "equilibrium",
                   "artifact-shape": "findings-ledger",  "convergence-shape": "homeostatic-checkpoint",
                   "cadence-shape": "checkpoint-gated"},
    "goal":       {"target-shape": "finite-criteria",    "halt-shape": "terminal",
                   "artifact-shape": "acceptance-inventory", "convergence-shape": "criteria-completion",
                   "cadence-shape": "sync"},
    "story":      {"target-shape": "promise-discovery",  "halt-shape": "checkpoint-with-reopen",
                   "artifact-shape": "storyboard",       "convergence-shape": "capstone-plus-closer",
                   "cadence-shape": "chapter"},
    "greenfield": {"target-shape": "discovery-reframing", "halt-shape": "manual-gated",
                   "artifact-shape": "rubric+intent",    "convergence-shape": "stone-reframe",
                   "cadence-shape": "checkpoint-gated"},
}

VALUES = {
    "target-shape": {"finite-criteria", "frontier-expanding", "promise-discovery", "discovery-reframing"},
    "halt-shape": {"terminal", "equilibrium", "checkpoint-with-reopen", "manual-gated"},
    "artifact-shape": {"prompt-only", "acceptance-inventory", "storyboard", "rubric+intent", "findings-ledger"},
    "convergence-shape": {"criteria-completion", "homeostatic-checkpoint", "capstone-plus-closer",
                          "stone-reframe", "iteration-cap"},
    "cadence-shape": {"sync", "checkpoint-gated", "chapter", "deferred-fire-and-forget"},
}


def contradictions(b):
    """Classification errors regardless of archetype → caller must AskUserQuestion."""
    hits = []
    if b.get("target-shape") == "finite-criteria":
        if b.get("halt-shape") in ("equilibrium", "manual-gated"):
            hits.append(f"target=finite-criteria with halt={b['halt-shape']}")
        if b.get("convergence-shape") == "homeostatic-checkpoint":
            hits.append("target=finite-criteria with convergence=homeostatic-checkpoint")
    return hits


def forbidden(arch, b):
    """Identity-breaking divergences for a given archetype → route away, don't compose."""
    hits = []
    if arch == "goal":
        if b.get("target-shape") in ("frontier-expanding", "discovery-reframing"):
            hits.append(f"goal cannot take target={b['target-shape']}")
        if b.get("halt-shape") == "manual-gated":
            hits.append("goal cannot take halt=manual-gated")
    if arch in ("frontier", "greenfield") and b.get("target-shape") == "finite-criteria":
        hits.append(f"{arch} cannot take target=finite-criteria")
    return hits


def distance(arch, b):
    d, div = 0, []
    for axis, w in WEIGHTS.items():
        if b.get(axis) != DEFAULTS[arch][axis]:
            d += w
            div.append(f"{axis}: {b.get(axis)} (vs {arch} default {DEFAULTS[arch][axis]})")
    return d, div


def classify(bundle):
    unknown = {ax: v for ax, v in bundle.items()
               if ax in VALUES and v not in VALUES[ax]}
    missing = [ax for ax in WEIGHTS if ax not in bundle]

    dists = {arch: distance(arch, bundle)[0] for arch in DEFAULTS}
    ordered = sorted(dists.items(), key=lambda kv: kv[1])
    nearest, nearest_d = ordered[0]
    second_d = ordered[1][1]
    tie = [a for a, d in dists.items() if d == nearest_d]

    return {
        "distances": dists,
        "nearest": nearest if len(tie) == 1 else None,
        "nearest_distance": nearest_d,
        "margin_to_second": second_d - nearest_d,
        "tie": tie if len(tie) > 1 else [],
        "divergences": distance(nearest, bundle)[1],
        "contradictions": contradictions(bundle),
        "forbidden_for_nearest": forbidden(nearest, bundle),
        "unknown_values": unknown,
        "missing_axes": missing,
        "max_distance": MAX_DISTANCE,
    }


# ----------------------------- self-test -----------------------------
def _self_test():
    cases = [
        ("pure frontier", DEFAULTS["frontier"], {"nearest": "frontier", "nearest_distance": 0}),
        ("pure goal", DEFAULTS["goal"], {"nearest": "goal", "nearest_distance": 0}),
        ("pure story", DEFAULTS["story"], {"nearest": "story", "nearest_distance": 0}),
        ("pure greenfield", DEFAULTS["greenfield"], {"nearest": "greenfield", "nearest_distance": 0}),
        # bodytxt hybrid: the handoff note called this "nearest=frontier + 4 story
        # divergences" by eye. The math disagrees — only target-shape is
        # frontier-flavoured; the other four axes are pure story, so nearest=story
        # (distance 3) with a single target divergence. This mismatch is exactly
        # why classification should not be eyeballed. Ground truth = the math.
        ("bodytxt hybrid (1 frontier axis on a story skeleton)",
         {"target-shape": "frontier-expanding", "halt-shape": "checkpoint-with-reopen",
          "artifact-shape": "storyboard", "convergence-shape": "capstone-plus-closer",
          "cadence-shape": "chapter"},
         {"nearest": "story", "nearest_distance": 3}),
        ("contradiction (finite + manual-gated)",
         {"target-shape": "finite-criteria", "halt-shape": "manual-gated",
          "artifact-shape": "acceptance-inventory", "convergence-shape": "criteria-completion",
          "cadence-shape": "sync"},
         {"contradiction_nonempty": True}),
        ("legacy frontier-exhaustion is stale",
         {"target-shape": "frontier-expanding", "halt-shape": "equilibrium",
          "artifact-shape": "findings-ledger", "convergence-shape": "frontier-exhaustion",
          "cadence-shape": "checkpoint-gated"},
         {"unknown_nonempty": True}),
    ]
    ok = True
    for name, bundle, expect in cases:
        r = classify(bundle)
        checks = []
        if "nearest" in expect:
            checks.append(("nearest", r["nearest"] == expect["nearest"], r["nearest"]))
        if "nearest_distance" in expect:
            checks.append(("dist", r["nearest_distance"] == expect["nearest_distance"], r["nearest_distance"]))
        if expect.get("contradiction_nonempty"):
            checks.append(("contradiction", len(r["contradictions"]) > 0, r["contradictions"]))
        if expect.get("unknown_nonempty"):
            checks.append(("unknown", len(r["unknown_values"]) > 0, r["unknown_values"]))
        passed = all(c[1] for c in checks)
        ok = ok and passed
        flag = "PASS" if passed else "FAIL"
        detail = "; ".join(f"{k}={v}" for k, _, v in checks)
        print(f"[{flag}] {name}: {detail}")
    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    raw = argv[1] if len(argv) > 1 else sys.stdin.read()
    if not raw.strip():
        print(__doc__)
        return 2
    bundle = json.loads(raw)
    print(json.dumps(classify(bundle), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
