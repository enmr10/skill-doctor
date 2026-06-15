# Issue Catalog — how to fix each finding

For every issue code the engine emits, here is the concrete fix the agent
should propose.

## 🔴 DUPLICATE_TRIGGER
**Problem:** The same trigger phrase appears in 2+ skills. The model cannot tell
which to fire.
**Fix:** Decide the single owner of that phrase. In the other skills, replace the
phrase with one specific to *their* job, or add a boundary line. If the skills
genuinely do the same thing, MERGE them.

Before:
```
# skill A: ... "competitor analysis" ...
# skill B: ... "competitor analysis" ...
```
After:
```
# skill A (competitors):           ... "competitor comparison page", "vs page" ...
# skill B (competitor-profiling):  ... "competitor research", "competitor dossier" ...
```

## 🔴 DUPLICATE_NAME
**Fix:** Names must be unique. Rename one, or merge if duplicated by accident.

## 🔴 MISSING_DESCRIPTION
**Fix:** Write `what it does + when to use it + 3-6 trigger phrases`. Without a
description a skill is dead weight.

## 🔴/🟠 HIGH_OVERLAP
**Fix:** Two options:
1. If they do the same job → MERGE into one skill, keep the broader name.
2. If scopes differ → add the mirror boundary lines:
   - In A: `For <B's job>, see <B>.`
   - In B: `For <A's job>, see <A>.`

## 🟠 VAGUE_DESCRIPTION
**Problem:** Filler-heavy ("powerful, comprehensive tool…"), no "use when", no
triggers.
**Fix:** Rewrite to the formula:
```
<Concrete job>. Use when the user <situation> or says "<trigger1>", "<trigger2>".
For <adjacent job>, see <other-skill>.
```

## 🟠 NAME_DIR_MISMATCH
**Fix:** Rename the directory or the `name:` field so they match exactly
(Agent Skills spec requirement).

## 🟠 BAD_NAME_FORMAT
**Fix:** Lowercase `a-z`, digits, single hyphens. No leading/trailing hyphen, no
`--`. e.g. `Page-CRO` → `page-cro`.

## 🟠/🟡 DESC_TOO_SHORT / DESC_TOO_LONG
**Fix:** Target 40–1024 chars. Too short → add triggers + when-to-use.
Too long → move detail into the SKILL.md body or `references/`.

## 🟡 NO_BOUNDARY
**Fix:** Add at least one cross-reference: `For <related job>, see <skill>.`
Boundaries are what stop neighbors from colliding as the library grows.

## 🔵 BODY_TOO_LONG
**Fix:** SKILL.md body > 500 lines. Move detail into `references/*.md` loaded on
demand so the core stays token-light.

## Rewrite checklist (apply to every description you touch)
- [ ] One concrete sentence on what it does
- [ ] Explicit "Use when…" clause
- [ ] 3–6 real trigger phrases in quotes
- [ ] At least one `For X, see Y.` boundary
- [ ] No filler adjectives (powerful, comprehensive, robust…)
- [ ] ≤ 1024 chars
- [ ] Every pre-existing trigger the user relies on is preserved or relocated, never dropped
