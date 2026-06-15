"""
reporter.py — Render the analysis as a Markdown report, an ASCII heatmap,
and a machine-readable JSON payload.

The Markdown report is what the agent shows the user; the JSON is what a CI
gate or another tool consumes.
"""

from __future__ import annotations

import json
from typing import List

from .analyzer import AnalysisResult
from .detector import Issue, SEV_ORDER
from .recommender import Recommendation, clusters

_HEAT_CHARS = " .:-=+*#%@"   # 10 levels, light -> dark


def health_score(result: AnalysisResult, issues: List[Issue]) -> int:
    """0..100. Starts at 100, subtracts weighted penalties, floors at 0."""
    penalty = 0
    weights = {"CRITICAL": 8, "HIGH": 4, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    for it in issues:
        penalty += weights.get(it.severity, 0)
    # normalize a little by library size so big libs aren't auto-zero
    n = max(len(result.skills), 1)
    score = 100 - int(penalty * 12 / n) - min(penalty, 40)
    return max(0, min(100, score))


def ascii_heatmap(result: AnalysisResult, limit: int = 24) -> str:
    skills = result.skills[:limit]
    n = len(skills)
    if n == 0:
        return "(no skills)"
    labels = [s.name[:10].rjust(10) for s in skills]
    lines = []
    header = " " * 12 + "".join(f"{i:>3}" for i in range(n))
    lines.append(header)
    for i in range(n):
        row = [f"{labels[i]} {i:>2} "]
        for j in range(n):
            if i == j:
                row.append(" \\ ")
                continue
            v = result.matrix[i][j]
            ch = _HEAT_CHARS[min(int(v * 10), 9)]
            row.append(f" {ch} ")
        lines.append("".join(row))
    lines.append("")
    lines.append("legend: ' '=0.0  '.'=0.1  '+'=0.5  '@'=0.9+  (collision score)")
    return "\n".join(lines)


def to_markdown(result: AnalysisResult, issues: List[Issue],
                recs: List[Recommendation]) -> str:
    n = len(result.skills)
    score = health_score(result, issues)
    crit = sum(1 for i in issues if i.severity == "CRITICAL")
    high = sum(1 for i in issues if i.severity == "HIGH")
    med = sum(1 for i in issues if i.severity == "MEDIUM")
    low = sum(1 for i in issues if i.severity == "LOW")

    bar_filled = "█" * (score // 5)
    bar_empty = "░" * (20 - score // 5)

    out = []
    out.append(f"# 🩺 Skill-Doctor Report\n")
    out.append(f"**Library health:** `{bar_filled}{bar_empty}` **{score}/100**\n")
    out.append(f"- Skills scanned: **{n}**")
    out.append(f"- Issues: 🔴 {crit} critical · 🟠 {high} high · 🟡 {med} medium · 🔵 {low} low")
    out.append(f"- Confusable clusters: **{len(clusters(result))}**\n")

    # Top collisions
    out.append("## 🔥 Top collisions\n")
    out.append("| Skill A | Skill B | Collision | Band | Shared signal |")
    out.append("|---|---|:--:|:--:|---|")
    for p in result.pairs[:12]:
        if p.collision < 0.15:
            break
        sig = ", ".join(p.shared_triggers[:2] or p.shared_keywords[:3]) or "—"
        out.append(f"| {p.name_i} | {p.name_j} | {p.collision:.2f} | {p.band()} | {sig} |")
    out.append("")

    # Clusters
    cl = clusters(result)
    if cl:
        out.append("## 🧩 Confusable clusters\n")
        out.append("These groups will compete for the same prompts:\n")
        for i, group in enumerate(sorted(cl, key=len, reverse=True), 1):
            out.append(f"{i}. **{' · '.join(sorted(group))}** ({len(group)} skills)")
        out.append("")

    # Duplicate triggers
    if result.trigger_index:
        out.append("## ⚠️ Duplicate trigger phrases\n")
        out.append("| Trigger | Claimed by |")
        out.append("|---|---|")
        for trig, idxs in sorted(result.trigger_index.items(),
                                 key=lambda kv: len(kv[1]), reverse=True):
            names = ", ".join(result.skills[i].name for i in idxs)
            out.append(f"| `{trig}` | {names} |")
        out.append("")

    # Recommendations
    if recs:
        out.append("## 🛠️ Recommendations\n")
        emoji = {"MERGE": "🔗", "ABSORB": "📥", "DISAMBIGUATE": "✂️"}
        out.append("| Action | Skills | Conf. | Why |")
        out.append("|---|---|:--:|---|")
        for r in recs[:20]:
            out.append(f"| {emoji.get(r.action,'')} {r.action} | "
                       f"{' + '.join(r.skills)} | {r.confidence:.0%} | {r.rationale} |")
        out.append("")

    # Issues grouped by severity
    out.append("## 📋 All issues\n")
    cur = None
    for it in issues:
        if it.severity != cur:
            cur = it.severity
            badge = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🔵","INFO":"⚪"}.get(cur,"")
            out.append(f"\n### {badge} {cur}\n")
        sk = ", ".join(it.skills)
        out.append(f"- **[{it.code}]** {it.message}")
        if it.detail:
            out.append(f"  - {it.detail}")
        if it.fix_hint:
            out.append(f"  - 💡 {it.fix_hint}")
    out.append("")

    # Heatmap
    out.append("## 🌡️ Collision heatmap (top 24)\n")
    out.append("```")
    out.append(ascii_heatmap(result))
    out.append("```")
    return "\n".join(out)


def to_json(result: AnalysisResult, issues: List[Issue],
            recs: List[Recommendation]) -> str:
    payload = {
        "summary": {
            "skills": len(result.skills),
            "health_score": health_score(result, issues),
            "issues": {
                "critical": sum(1 for i in issues if i.severity == "CRITICAL"),
                "high": sum(1 for i in issues if i.severity == "HIGH"),
                "medium": sum(1 for i in issues if i.severity == "MEDIUM"),
                "low": sum(1 for i in issues if i.severity == "LOW"),
            },
            "clusters": clusters(result),
        },
        "top_collisions": [
            {
                "a": p.name_i, "b": p.name_j, "collision": p.collision,
                "cosine": p.cosine, "trigger_jaccard": p.trigger_jac,
                "keyword_jaccard": p.keyword_jac,
                "shared_triggers": p.shared_triggers,
                "shared_keywords": p.shared_keywords,
            }
            for p in result.pairs if p.collision >= 0.15
        ],
        "duplicate_triggers": {
            t: [result.skills[i].name for i in idxs]
            for t, idxs in result.trigger_index.items()
        },
        "issues": [
            {"code": i.code, "severity": i.severity, "skills": i.skills,
             "message": i.message, "detail": i.detail, "fix_hint": i.fix_hint}
            for i in issues
        ],
        "recommendations": [
            {"action": r.action, "skills": r.skills, "confidence": r.confidence,
             "rationale": r.rationale, "suggestion": r.suggestion}
            for r in recs
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
