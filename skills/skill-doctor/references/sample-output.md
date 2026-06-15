# Sample output

Running skill-doctor on a small library containing the known marketing
collisions produces a report like this (abridged):

```
# 🩺 Skill-Doctor Report

**Library health:** `███████████░░░░░░░░░` 56/100

- Skills scanned: 6
- Issues: 🔴 3 critical · 🟠 4 high · 🟡 5 medium · 🔵 0 low
- Confusable clusters: 2

## 🔥 Top collisions
| Skill A | Skill B | Collision | Band | Shared signal |
|---|---|:--:|:--:|---|
| competitors | competitor-profiling | 0.61 | CRITICAL | competitor |
| copywriting | copy-editing | 0.44 | HIGH | copy, page |
| competitor-profiling | customer-research | 0.39 | HIGH | reviews |

## 🧩 Confusable clusters
1. **competitor-profiling · competitors · customer-research** (3 skills)
2. **copy-editing · copywriting** (2 skills)

## ⚠️ Duplicate trigger phrases
| Trigger | Claimed by |
|---|---|
| `competitor analysis` | competitors, competitor-profiling |

## 🛠️ Recommendations
| Action | Skills | Conf. | Why |
|---|---|:--:|---|
| ✂️ DISAMBIGUATE | competitors + competitor-profiling | 61% | Distinct scope but collide on "competitor" |
| 🔗 MERGE | copy-editing + copywriting | 54% | Near-equal scope, shared vocabulary |
```

The agent then proposes the concrete description rewrites and, on approval,
edits each SKILL.md frontmatter — then re-runs to confirm the score climbs.
