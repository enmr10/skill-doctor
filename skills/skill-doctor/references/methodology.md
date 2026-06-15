# Methodology

How skill-doctor decides that two skills will fight over the same prompt.

## The problem

A skill triggers when its `description` matches the user's intent. When two
descriptions describe overlapping intent, the model has to guess — and guesses
wrong some fraction of the time. The more skills you install, the more pairs
exist (N skills → N·(N-1)/2 pairs), so collisions grow quadratically.

Example real collision:
- `competitors` — "competitor comparison pages, alternative pages, vs pages"
- `competitor-profiling` — "research, profile, analyze competitors"
- `customer-research` — "review mining, competitor reviews"

All three claim "competitor". A prompt like "analyze my competitors" is ambiguous.

## Three signals

We never rely on a single metric — each catches a different failure mode.

### 1. TF-IDF cosine (weight 0.50)
Captures *semantic* overlap of the whole description.

- Tokenize, drop stopwords + skill boilerplate ("use", "when", "user"…).
- Build TF-IDF vectors across the whole library (so common words like
  "marketing" get down-weighted automatically — IDF).
- Cosine of two vectors ∈ [0,1].

Catches: two skills that talk about the same domain in different words.

### 2. Trigger-phrase Jaccard (weight 0.35)
Captures *explicit* collisions — the deadliest kind.

- Extract quoted phrases ('A/B test', "split test") and slash commands (/cro).
- Jaccard = |shared triggers| / |all triggers|.

Catches: the exact same quoted trigger living in two skills. Even one shared
trigger is flagged separately as `DUPLICATE_TRIGGER` (critical), regardless of
the overall score.

### 3. Keyword Jaccard (weight 0.15)
A cheap lexical backstop on the distinctive vocabulary of each description.

## Combined score

```
collision = 0.50·cosine + 0.35·trigger_jac + 0.15·keyword_jac
```

Weights chosen so that:
- A pure semantic twin (cosine 1.0, no shared triggers) → 0.50 → HIGH.
- One shared trigger on otherwise different skills still surfaces via the
  separate DUPLICATE_TRIGGER rule.
- Two skills that share triggers AND vocabulary AND meaning → ~0.9 → CRITICAL.

### Bands
| Score | Band | Meaning |
|-------|------|---------|
| < 0.22 | LOW | Safe |
| 0.22–0.38 | MEDIUM | Watch; add boundaries |
| 0.38–0.55 | HIGH | Will mis-route sometimes |
| ≥ 0.55 | CRITICAL | Merge or hard-disambiguate |

## Clusters

We build a graph: nodes = skills, edges = pairs with collision ≥ threshold
(default 0.30). Connected components (union-find) are "confusable clusters" —
families of skills that compete as a group, not just in pairs. This is what you
actually fix together.

## Recommendations

| Action | Condition |
|--------|-----------|
| MERGE | collision ≥ merge_at AND near-equal scope (size diff ≤ 3 keywords) |
| ABSORB | one description ≥ 75% contained in the other |
| DISAMBIGUATE | collision ≥ disambig_at but distinct scope |

## Health score

```
start 100
subtract weighted penalties (CRITICAL 8, HIGH 4, MEDIUM 2, LOW 1)
normalize lightly by library size
floor at 0
```

A score is a relative signal, not an absolute grade — track whether it goes up
after you apply fixes.

## Why three signals beat embeddings here

Embeddings would need a model call per skill and a vector DB. This runs offline,
instantly, on any machine, with zero dependencies — and trigger-phrase Jaccard
catches the single most common real-world bug (copy-pasted trigger lists) that
pure embeddings would smooth over.
