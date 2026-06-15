"""
detector.py — Rule engine that turns the analysis into concrete, typed issues.

Each rule is small, named, and independently testable. Issues carry a
severity, the skill(s) involved, a human message, and a machine `code`
so downstream tools (reporter, recommender, CI gates) can act on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .analyzer import AnalysisResult
from .scanner import NAME_RULE, Skill
from .textutil import vagueness_score

# Severity ordering for sorting/printing.
SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

# Tunable thresholds (overridable from CLI).
DEFAULTS = {
    "collision_critical": 0.55,
    "collision_high": 0.38,
    "vague_threshold": 0.5,
    "desc_min": 40,
    "desc_max": 1024,
    "body_max_lines": 500,
}


@dataclass
class Issue:
    code: str
    severity: str
    skills: List[str]
    message: str
    detail: str = ""
    fix_hint: str = ""

    def sort_key(self):
        return (SEV_ORDER.get(self.severity, 9), self.code, tuple(self.skills))


def _has_boundary(desc: str) -> bool:
    low = desc.lower()
    return ("for " in low and " see " in low) or "not for" in low or "instead of" in low


def detect(result: AnalysisResult, cfg: dict = None) -> List[Issue]:
    cfg = {**DEFAULTS, **(cfg or {})}
    issues: List[Issue] = []
    skills = result.skills

    # ---- Pair-level: trigger collisions (most dangerous) ----------------
    for trigger, idxs in result.trigger_index.items():
        names = [skills[i].name for i in idxs]
        issues.append(Issue(
            code="DUPLICATE_TRIGGER",
            severity="CRITICAL",
            skills=names,
            message=f"Trigger “{trigger}” is claimed by {len(names)} skills",
            detail=f"Shared by: {', '.join(names)}",
            fix_hint="Keep the trigger in ONE skill; replace it in the others "
                     "with a distinct phrase, or merge the skills.",
        ))

    # ---- Pair-level: high semantic overlap ------------------------------
    for p in result.pairs:
        if p.collision >= cfg["collision_critical"]:
            sev = "CRITICAL"
        elif p.collision >= cfg["collision_high"]:
            sev = "HIGH"
        else:
            continue
        issues.append(Issue(
            code="HIGH_OVERLAP",
            severity=sev,
            skills=[p.name_i, p.name_j],
            message=f"{p.name_i} ↔ {p.name_j} overlap = {p.collision:.2f} ({p.band()})",
            detail=(f"cosine={p.cosine:.2f} trigger={p.trigger_jac:.2f} "
                    f"keyword={p.keyword_jac:.2f}; "
                    f"shared keywords: {', '.join(p.shared_keywords) or '—'}"),
            fix_hint="Add explicit boundaries ('For X, see <other>.') to both "
                     "descriptions, or merge if they truly do the same job.",
        ))

    # ---- Skill-level rules ----------------------------------------------
    seen_names = {}
    for i, s in enumerate(skills):
        # Missing description
        if not s.description:
            issues.append(Issue(
                "MISSING_DESCRIPTION", "CRITICAL", [s.name],
                f"{s.name} has no description",
                fix_hint="A skill with no description can never trigger reliably.",
            ))
            continue

        # Length bounds
        if s.desc_len < cfg["desc_min"]:
            issues.append(Issue(
                "DESC_TOO_SHORT", "HIGH", [s.name],
                f"{s.name} description is only {s.desc_len} chars",
                fix_hint="Add what it does + when to use it + trigger phrases.",
            ))
        if s.desc_len > cfg["desc_max"]:
            issues.append(Issue(
                "DESC_TOO_LONG", "MEDIUM", [s.name],
                f"{s.name} description is {s.desc_len} chars (max {cfg['desc_max']})",
                fix_hint="Trim to the essentials; move detail into the body.",
            ))

        # Vagueness
        vs = vagueness_score(s.description)
        if vs >= cfg["vague_threshold"]:
            issues.append(Issue(
                "VAGUE_DESCRIPTION", "HIGH", [s.name],
                f"{s.name} description is vague (score {vs:.2f})",
                detail="Leans on filler words and/or lacks 'use when' + triggers.",
                fix_hint="State the concrete job and add 3-6 real trigger phrases.",
            ))

        # No scope boundary / cross-reference
        if not _has_boundary(s.description):
            issues.append(Issue(
                "NO_BOUNDARY", "MEDIUM", [s.name],
                f"{s.name} declares no scope boundary",
                detail="No 'For X, see <other>' cross-reference found.",
                fix_hint="Name the adjacent skill to hand off to, e.g. "
                         "'For email copy, see emails.'",
            ))

        # name <-> directory mismatch (dir source only)
        if s.source == "dir" and s.dir_name and s.name != s.dir_name:
            issues.append(Issue(
                "NAME_DIR_MISMATCH", "HIGH", [s.name],
                f"name '{s.name}' != directory '{s.dir_name}'",
                fix_hint="The Agent Skills spec requires name == directory name.",
            ))

        # name format
        if s.name and not NAME_RULE.match(s.name):
            issues.append(Issue(
                "BAD_NAME_FORMAT", "HIGH", [s.name],
                f"name '{s.name}' breaks naming rules",
                fix_hint="Lowercase a-z, 0-9, single hyphens; no leading/trailing/double hyphen.",
            ))

        # over-long body
        if s.body_len and s.body_len > cfg["body_max_lines"]:
            issues.append(Issue(
                "BODY_TOO_LONG", "LOW", [s.name],
                f"{s.name} SKILL.md body is {s.body_len} lines (>{cfg['body_max_lines']})",
                fix_hint="Move detail into references/ loaded on demand.",
            ))

        # duplicate names
        seen_names.setdefault(s.name, []).append(i)

    for name, idxs in seen_names.items():
        if len(idxs) > 1:
            issues.append(Issue(
                "DUPLICATE_NAME", "CRITICAL", [name],
                f"name '{name}' is used by {len(idxs)} skills",
                fix_hint="Names must be unique; rename or merge.",
            ))

    issues.sort(key=lambda x: x.sort_key())
    return issues
