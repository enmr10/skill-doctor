---
name: skill-doctor
description: >
  Audits a skill library for description collisions, trigger-phrase conflicts,
  vague descriptions, and quality issues — then recommends which skills to merge,
  absorb, or disambiguate. Use when you have many installed skills and the wrong
  one keeps triggering, or before publishing a skill pack.
  Trigger: "audit my skills", "skill doctor", "skills collide", "wrong skill triggers",
  "which skills overlap", "clean up my skills", "skill conflict", "check my skill library",
  /skill-doctor. For building a single new skill, see skill-creator.
metadata:
  author: built-with-claude
  version: 1.0.0
---

# Skill-Doctor

Diagnose a skill library. Find skills whose descriptions **compete for the same prompts**, then fix the routing.

## When to run

- You installed many skills and "the wrong one keeps firing"
- Before publishing a skill pack (catch collisions reviewers will hit)
- After adding a skill (does it collide with an existing one?)
- Periodic health check on a growing library

## Input

Point the engine at EITHER:
- A **directory** of skills (`<root>/<name>/SKILL.md`), or
- A Claude Code **manifest.json** (`skills-plugin/.../manifest.json`)

## How to run

The engine lives in `scripts/` next to this file. Zero dependencies (Python 3.8+ stdlib).

```bash
# From the directory containing this SKILL.md:
python3 -m scripts <path-to-skills-or-manifest>            # Markdown report
python3 -m scripts <path> --format json --out report.json # machine output
python3 -m scripts <path> --fail-on critical               # CI gate (exit 1)
```

Common options:
- `--merge-at 0.55` — collision score that triggers a MERGE recommendation
- `--disambig-at 0.30` — score that triggers a DISAMBIGUATE recommendation
- `--vague-threshold 0.5` — flag descriptions vaguer than this
- `--top 12` — how many top collisions to list
- `--format md|json|both`

## What it detects (issue codes)

| Code | Severity | Meaning |
|------|----------|---------|
| `DUPLICATE_TRIGGER` | 🔴 | Same trigger phrase claimed by 2+ skills (top cause of mis-routing) |
| `DUPLICATE_NAME` | 🔴 | Two skills share a name |
| `MISSING_DESCRIPTION` | 🔴 | Skill can never trigger reliably |
| `HIGH_OVERLAP` | 🔴/🟠 | Two descriptions are semantically too close |
| `VAGUE_DESCRIPTION` | 🟠 | Filler-heavy, no "use when", no triggers |
| `NAME_DIR_MISMATCH` | 🟠 | name ≠ directory (breaks the spec) |
| `BAD_NAME_FORMAT` | 🟠 | name breaks lowercase/hyphen rules |
| `DESC_TOO_SHORT` / `DESC_TOO_LONG` | 🟠/🟡 | Outside 40–1024 chars |
| `NO_BOUNDARY` | 🟡 | No "For X, see <other>" cross-reference |
| `BODY_TOO_LONG` | 🔵 | SKILL.md body > 500 lines |

## How scoring works (one line)

```
collision = 0.50·cosine(TF-IDF of descriptions)
          + 0.35·jaccard(trigger phrases)
          + 0.15·jaccard(domain keywords)
```

Bands: `<0.22 LOW · 0.22 MEDIUM · 0.38 HIGH · 0.55 CRITICAL`.
See `references/scoring.md` for the full rationale.

## Workflow for the agent

1. **Run** the engine on the user's skills path → read the Markdown report.
2. **Summarize** the health score, the worst clusters, and duplicate triggers.
3. **For each top recommendation**, propose the concrete edit:
   - `MERGE` → draft one combined description, suggest the surviving name.
   - `ABSORB` → name the skill to delete and where its triggers move.
   - `DISAMBIGUATE` → write the two mirror boundary lines ("For X, see Y.").
4. **Offer to apply** the description rewrites (edit each SKILL.md frontmatter).
5. **Re-run** to confirm the health score improved.

## Output

- A Markdown report: health score, top collisions, confusable clusters,
  duplicate-trigger table, recommendations, full issue list, ASCII heatmap.
- Optional JSON (`--format json`) for CI gates or other tools.

## Rules

- The engine is **read-only** — it never edits skills. Rewrites are applied by
  the agent (you) only after the user approves.
- Never delete a skill without explicit confirmation.
- When rewriting descriptions, preserve every real trigger phrase the user relies on;
  only move/disambiguate them — don't drop them.

See `references/methodology.md` for the algorithm and `references/issue-catalog.md`
for how to fix each issue type.
