"""
recommender.py — Turn issues + overlap model into prioritized actions.

Produces three kinds of recommendation:
  MERGE      — two skills overlap so heavily they should be one
  ABSORB     — one skill is a near-subset of another (delete the small one)
  DISAMBIGUATE — keep both, but rewrite descriptions to draw a hard boundary

Also emits a graph of collision "clusters" (connected components above a
threshold) so the user sees families of confusable skills at a glance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .analyzer import AnalysisResult, PairScore
from .scanner import Skill


@dataclass
class Recommendation:
    action: str            # MERGE | ABSORB | DISAMBIGUATE
    skills: List[str]
    confidence: float      # 0..1
    rationale: str
    suggestion: str = ""


def _subset_ratio(small: Set[str], big: Set[str]) -> float:
    if not small:
        return 0.0
    return len(small & big) / len(small)


def recommend(result: AnalysisResult,
              merge_at: float = 0.55,
              disambig_at: float = 0.30) -> List[Recommendation]:
    recs: List[Recommendation] = []
    kw = result.keywords
    seen_pairs: Set[Tuple[str, str]] = set()

    for p in result.pairs:
        if p.collision < disambig_at:
            break  # pairs are sorted desc; nothing below matters
        key = tuple(sorted((p.name_i, p.name_j)))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)

        si, sj = set(kw[p.i]), set(kw[p.j])
        sub_i = _subset_ratio(si, sj)   # how much of i is inside j
        sub_j = _subset_ratio(sj, si)

        if p.collision >= merge_at and abs(len(si) - len(sj)) <= 3:
            recs.append(Recommendation(
                action="MERGE",
                skills=[p.name_i, p.name_j],
                confidence=round(min(p.collision + 0.1, 0.99), 2),
                rationale=(f"Overlap {p.collision:.2f}, near-equal scope. "
                           f"Shared: {', '.join(p.shared_keywords[:5]) or '—'}"),
                suggestion=f"Merge into one skill; keep the broader name.",
            ))
        elif max(sub_i, sub_j) >= 0.75 and p.collision >= disambig_at:
            small, big = (p.name_i, p.name_j) if sub_i >= sub_j else (p.name_j, p.name_i)
            recs.append(Recommendation(
                action="ABSORB",
                skills=[small, big],
                confidence=round(max(sub_i, sub_j), 2),
                rationale=f"'{small}' is {max(sub_i, sub_j)*100:.0f}% contained in '{big}'.",
                suggestion=f"Fold '{small}' into '{big}' and delete '{small}'.",
            ))
        else:
            recs.append(Recommendation(
                action="DISAMBIGUATE",
                skills=[p.name_i, p.name_j],
                confidence=round(p.collision, 2),
                rationale=(f"Overlap {p.collision:.2f} risks mis-routing but each "
                           f"has distinct scope."),
                suggestion=(f"Add to {p.name_i}: 'For <{p.name_j}'s job>, see {p.name_j}.' "
                            f"and the mirror line to {p.name_j}."),
            ))

    recs.sort(key=lambda r: r.confidence, reverse=True)
    return recs


def clusters(result: AnalysisResult, threshold: float = 0.30) -> List[List[str]]:
    """Connected components of the collision graph above `threshold`."""
    n = len(result.skills)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in result.pairs:
        if p.collision >= threshold:
            union(p.i, p.j)

    groups: Dict[int, List[str]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(result.skills[i].name)
    return [g for g in groups.values() if len(g) > 1]
