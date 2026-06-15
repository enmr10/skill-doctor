"""
analyzer.py — Build the collision/overlap model across a set of skills.

Combines three independent similarity signals into one calibrated
collision score per skill pair:

    collision = 0.50 * cosine(description TF-IDF)
              + 0.35 * jaccard(trigger phrases)
              + 0.15 * jaccard(domain keywords)

Trigger-phrase collisions are tracked separately because an exact shared
trigger ("competitor analysis" in two skills) is the single most dangerous
cause of mis-routing, regardless of overall description similarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .scanner import Skill
from .textutil import TfidfModel, extract_triggers, jaccard, tokenize

W_COSINE = 0.50
W_TRIGGER = 0.35
W_KEYWORD = 0.15


@dataclass
class PairScore:
    i: int
    j: int
    name_i: str
    name_j: str
    cosine: float
    trigger_jac: float
    keyword_jac: float
    shared_triggers: List[str] = field(default_factory=list)
    shared_keywords: List[str] = field(default_factory=list)

    @property
    def collision(self) -> float:
        return round(
            W_COSINE * self.cosine
            + W_TRIGGER * self.trigger_jac
            + W_KEYWORD * self.keyword_jac,
            4,
        )

    def band(self) -> str:
        c = self.collision
        if c >= 0.55:
            return "CRITICAL"
        if c >= 0.38:
            return "HIGH"
        if c >= 0.22:
            return "MEDIUM"
        return "LOW"


@dataclass
class AnalysisResult:
    skills: List[Skill]
    triggers: List[List[str]]
    keywords: List[List[str]]
    pairs: List[PairScore]
    trigger_index: Dict[str, List[int]]   # trigger phrase -> skill indices
    matrix: List[List[float]]             # full NxN collision matrix
    top_terms: List[List[str]]


def analyze(skills: List[Skill]) -> AnalysisResult:
    n = len(skills)
    triggers = [extract_triggers(s.description) for s in skills]
    keywords = [tokenize(s.description) for s in skills]
    model = TfidfModel(keywords)
    top_terms = [model.top_terms(i, 6) for i in range(n)]

    # Build trigger collision index.
    trigger_index: Dict[str, List[int]] = {}
    for idx, trigs in enumerate(triggers):
        for t in trigs:
            trigger_index.setdefault(t, []).append(idx)

    pairs: List[PairScore] = []
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            cos = model.cosine(i, j)
            shared_t = sorted(set(triggers[i]) & set(triggers[j]))
            shared_k = sorted(set(keywords[i]) & set(keywords[j]))
            tj = jaccard(triggers[i], triggers[j])
            kj = jaccard(keywords[i], keywords[j])
            ps = PairScore(
                i=i, j=j,
                name_i=skills[i].name, name_j=skills[j].name,
                cosine=round(cos, 4),
                trigger_jac=round(tj, 4),
                keyword_jac=round(kj, 4),
                shared_triggers=shared_t,
                shared_keywords=shared_k[:8],
            )
            pairs.append(ps)
            matrix[i][j] = matrix[j][i] = ps.collision

    pairs.sort(key=lambda p: p.collision, reverse=True)
    return AnalysisResult(
        skills=skills,
        triggers=triggers,
        keywords=keywords,
        pairs=pairs,
        trigger_index={k: v for k, v in trigger_index.items() if len(v) > 1},
        matrix=matrix,
        top_terms=top_terms,
    )
