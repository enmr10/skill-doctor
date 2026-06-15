# skill-doctor 🩺 — Audit Your Claude Skills for Conflicts & Collisions

> **skill-doctor is an open-source Claude Code skill that scans a skill library and finds descriptions that collide — the root cause of "the wrong skill keeps triggering." It scores every skill pair, flags duplicate trigger phrases, groups confusable skills into clusters, and tells you exactly which skills to merge, absorb, or disambiguate.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-blue.svg)](#requirements)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#requirements)
[![Works offline](https://img.shields.io/badge/runs-offline-success.svg)](#requirements)

If you have installed more than ~20 Claude skills and noticed Claude picking the
**wrong skill** for a prompt, this is the fix. skill-doctor diagnoses *why* skills
mis-route and gives you the exact edits to resolve it.

---

## The problem: why the wrong Claude skill keeps triggering

A skill fires when its `description` matches your intent. When two descriptions
describe **overlapping** intent, the model has to guess — and guesses wrong some
of the time. Because every new skill adds a pair with every existing skill, the
number of possible collisions grows **quadratically**: 20 skills = 190 pairs,
67 skills = 2,211 pairs. No human can audit that by hand.

**Real example (3 skills, 1 prompt):** the prompt *"analyze my competitors"* can
match `competitors`, `competitor-profiling`, **and** `customer-research` — all
three claim the word "competitor." Claude picks one, often the wrong one, and you
get a worse result with no obvious cause.

---

## What skill-doctor does

| Capability | Detail |
|---|---|
| 🔍 **Collision scoring** | Scores every skill pair with a 3-signal model (TF-IDF + trigger overlap + keyword overlap) |
| ⚠️ **Duplicate trigger detection** | Finds the exact same trigger phrase claimed by 2+ skills — the #1 cause of mis-routing |
| 🧩 **Confusable clusters** | Groups whole families of skills that compete for the same prompts |
| 🛠️ **Actionable fixes** | Recommends MERGE / ABSORB / DISAMBIGUATE per pair, with confidence |
| 📊 **Health score** | A single 0–100 number so you can track improvement over time |
| 🌡️ **Heatmap + report** | Markdown report, ASCII heatmap, and JSON output for CI gates |
| 🚦 **CI gate** | `--fail-on critical` blocks a PR that adds a collision |

---

## Quick start

skill-doctor reads either a **directory of skills** (`<name>/SKILL.md`) or a
Claude Code **`manifest.json`**.

```bash
# Markdown report to your console
python3 -m scripts /path/to/skills

# Save a report
python3 -m scripts /path/to/skills --out report.md

# Machine-readable output for CI
python3 -m scripts /path/to/skills --format json --fail-on critical
```

No install, no pip, no API key. Pure Python standard library.

---

## Real results (audit of a 67-skill library)

We ran skill-doctor on a real installed library of **67 skills**, then applied its
recommendations and re-ran it:

| Metric | Before | After | Change |
|---|:--:|:--:|:--:|
| Health score | 43/100 | 51/100 | ▲ +8 |
| Confusable clusters | 3 | **0** | ✅ eliminated |
| HIGH-severity overlaps | 5 | **0** | ✅ eliminated |
| Total HIGH issues | 9 | 4 | ▼ |

It even caught collisions introduced by *merging* skills that shared a boilerplate
description — exactly the mistake most skill-pack authors make.

---

## How the collision score works

```
collision = 0.50 · cosine(TF-IDF of descriptions)   # semantic overlap
          + 0.35 · jaccard(trigger phrases)          # explicit, deadliest
          + 0.15 · jaccard(domain keywords)          # lexical backstop
```

| Score | Band | Meaning |
|---|---|---|
| < 0.22 | LOW | Safe |
| 0.22–0.38 | MEDIUM | Add a boundary line |
| 0.38–0.55 | HIGH | Will mis-route sometimes |
| ≥ 0.55 | CRITICAL | Merge or hard-disambiguate |

Three independent signals beat a single one: trigger-phrase overlap catches
copy-pasted trigger lists that pure embeddings would smooth over, while TF-IDF
cosine catches skills that describe the same job in different words. Full rationale
in [`methodology.md`](skills/skill-doctor/references/methodology.md).

---

## Installation

### Option A — Claude Code plugin marketplace
```
/plugin marketplace add <your-username>/skill-doctor
/plugin install skill-doctor
```

### Option B — Manual
Download the latest release and upload `skill-doctor.zip` via **Add Skill**, or copy
`skills/skill-doctor/` into your skills directory.

---

## Requirements

- Python **3.8+** (standard library only — **zero third-party dependencies**)
- Runs fully **offline**; no API key, no network calls, no telemetry
- Cross-platform (Windows / macOS / Linux). Emits UTF-8 safely even on Windows consoles.

---

## FAQ

### Why does Claude trigger the wrong skill?
Because two or more skill `description` fields claim overlapping intent or share an
identical trigger phrase. The model can't tell them apart, so it guesses.
skill-doctor finds every such overlap and tells you how to separate them.

### How do I audit my Claude skills for conflicts?
Point skill-doctor at your skills directory or `manifest.json`:
`python3 -m scripts /path/to/skills`. It returns a ranked list of colliding pairs,
duplicate triggers, confusable clusters, and concrete fixes.

### How many skills before collisions become a problem?
Around 20. At 20 skills there are 190 possible pairs; collisions scale
quadratically, so libraries of 30+ skills almost always contain at least one.

### Does it edit my skills automatically?
No. The engine is **read-only**. It produces a report and recommendations; you (or
your agent) apply the edits after review, so nothing changes without your approval.

### Does it work with the Agent Skills standard / cross-agent skills?
Yes. Any skill with standard `SKILL.md` frontmatter (`name` + `description`) is
supported, plus Claude Code `manifest.json` files.

### Can I use it in CI?
Yes. `--fail-on critical` exits non-zero when a critical issue exists, so a PR that
introduces a colliding skill fails the build.

---

## Use cases

- **Personal libraries** — stop the wrong skill from firing
- **Skill-pack authors** — ship a pack with zero internal collisions
- **Teams** — keep a shared skill library clean as it grows
- **Marketplaces / reviewers** — vet submissions for description quality

---

## Keywords

Claude Code skills · skill conflict · skill collision detector · wrong skill triggers ·
audit Claude skills · skill description overlap · Agent Skills linter · skill router ·
Claude skill quality · skill library health · trigger phrase conflict · skill marketplace QA

---

## Contributing

Issues and PRs welcome. New issue-detection rules live in
[`detector.py`](skills/skill-doctor/scripts/detector.py); each rule is small and
self-contained. See [`AGENTS.md`](AGENTS.md) for the architecture.

## License

MIT — see [LICENSE](LICENSE).

---

*Built with Claude. Last updated: 2026-06-16.*
