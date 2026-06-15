"""
textutil.py — Zero-dependency text analysis core for skill-doctor.

Provides tokenization, trigger-phrase extraction, TF-IDF vectorization,
cosine similarity, and Jaccard similarity. Pure Python stdlib only
(works on any Python 3.8+ with no pip installs).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Sequence, Tuple

# ----------------------------------------------------------------------------
# Stopwords: generic English + skill-description boilerplate. These words carry
# little signal for *domain* similarity, so we strip them before TF-IDF.
# ----------------------------------------------------------------------------
_STOPWORDS = frozenset("""
a an the and or but if then else for to of in on at by with from into over
this that these those it its as is are was were be been being do does did
use uses used using user users want wants wanted when where what which who
also see help skill skills mention mentions mentioned say says said make makes
your you their them they we our us i me my will would should could can may
about any all more most some such via per not no yes need needs needed get
gets getting include includes including across whenever whatever something
""".split())

# Words that, if they DOMINATE a description, signal vagueness.
_VAGUE_MARKERS = frozenset("""
powerful comprehensive various stuff things general generic flexible robust
amazing awesome simple easy nice good great helpful useful advanced modern
""".split())

_WORD_RE = re.compile(r"[a-z][a-z0-9\-]+")

# Matches quoted trigger phrases in several quote styles, plus slash commands.
_QUOTE_RES = [
    re.compile(r"'([^']{2,60})'"),
    re.compile(r'"([^"]{2,60})"'),
    re.compile(r"[‘’]([^‘’]{2,60})[‘’]"),
    re.compile(r"[“”]([^“”]{2,60})[“”]"),
]
_SLASH_RE = re.compile(r"(?<!\w)(/[a-z][a-z0-9\-]{1,40})")


def tokenize(text: str, keep_stop: bool = False) -> List[str]:
    """Lowercase, extract word tokens, drop stopwords by default."""
    toks = _WORD_RE.findall(text.lower())
    if keep_stop:
        return toks
    return [t for t in toks if t not in _STOPWORDS and len(t) > 2]


def extract_triggers(description: str) -> List[str]:
    """
    Pull explicit trigger phrases out of a skill description:
      - quoted phrases ('A/B test', "split test")
      - slash commands (/cro, /context-query)
    Returns normalized (lowercased, whitespace-collapsed) phrases.
    """
    found: List[str] = []
    for rx in _QUOTE_RES:
        found.extend(rx.findall(description))
    found.extend(_SLASH_RE.findall(description))
    out, seen = [], set()
    for f in found:
        norm = re.sub(r"\s+", " ", f.strip().lower())
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """Jaccard similarity of two token/phrase sets. 0..1."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


class TfidfModel:
    """
    Minimal TF-IDF model + cosine similarity. Built once over the corpus,
    then queried pairwise. No external dependencies.
    """

    def __init__(self, docs: Sequence[Sequence[str]]):
        self.docs = [list(d) for d in docs]
        self.n = len(self.docs)
        self._df: Counter = Counter()
        for d in self.docs:
            for term in set(d):
                self._df[term] += 1
        self._idf: Dict[str, float] = {
            term: math.log((self.n + 1) / (df + 1)) + 1.0
            for term, df in self._df.items()
        }
        self._vectors: List[Dict[str, float]] = [self._vectorize(d) for d in self.docs]
        self._norms: List[float] = [
            math.sqrt(sum(w * w for w in v.values())) for v in self._vectors
        ]

    def _vectorize(self, doc: Sequence[str]) -> Dict[str, float]:
        if not doc:
            return {}
        counts = Counter(doc)
        total = sum(counts.values())
        return {
            term: (c / total) * self._idf.get(term, 0.0)
            for term, c in counts.items()
        }

    def cosine(self, i: int, j: int) -> float:
        vi, vj = self._vectors[i], self._vectors[j]
        ni, nj = self._norms[i], self._norms[j]
        if ni == 0 or nj == 0:
            return 0.0
        # iterate over the smaller vector for speed
        if len(vi) > len(vj):
            vi, vj = vj, vi
        dot = sum(w * vj.get(term, 0.0) for term, w in vi.items())
        return dot / (ni * nj)

    def top_terms(self, i: int, k: int = 6) -> List[str]:
        """Most distinctive terms for a document (highest tf-idf weight)."""
        return [t for t, _ in sorted(
            self._vectors[i].items(), key=lambda kv: kv[1], reverse=True
        )[:k]]


def vagueness_score(description: str) -> float:
    """
    0 (sharp) .. 1 (vague). High when the description leans on filler markers
    and lacks concrete trigger phrases.
    """
    toks = tokenize(description, keep_stop=True)
    if not toks:
        return 1.0
    vague_hits = sum(1 for t in toks if t in _VAGUE_MARKERS)
    has_when = 1 if re.search(r"\buse when\b", description.lower()) else 0
    n_triggers = len(extract_triggers(description))
    density = vague_hits / max(len(toks), 1)
    score = 0.0
    score += min(density * 4.0, 0.5)            # filler density
    score += 0.3 if not has_when else 0.0       # no "use when" clause
    score += 0.2 if n_triggers == 0 else 0.0    # no concrete triggers
    return round(min(score, 1.0), 3)
