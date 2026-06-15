# Launch Kit — skill-doctor

Everything to make the repo discoverable and get it trending. Apply in order.

## 1. GitHub repo settings (do this first — biggest SEO lever)

**About box** (top-right of repo):
> Audit your Claude skills for collisions. Finds why the wrong skill triggers and gives the exact fixes. Zero dependencies.

**Topics** (add all — GitHub topic pages rank in search):
```
claude-code  claude-skills  agent-skills  anthropic  skill-conflict
linter  developer-tools  python  cli  ai-tools  prompt-engineering
claude  llm-tools  static-analysis
```

**Website field:** link to the README anchor or a future landing page.

## 2. Directory submissions (where AI search and devs look)

| Directory | Why | Action |
|---|---|---|
| `awesome-claude-skills` (travisvn, ComposioHQ) | Most-cited skill lists; LLMs scrape them | Open a PR adding skill-doctor under "Quality / Tooling" |
| skills.sh | npm-style installer, Vercel-backed | Submit the package |
| claudeskills.info | Free directory that ranks in Google | Submit |
| SkillsMP | Indexes 800k+ skills | Auto-indexed once public; verify listing |
| Product Hunt | Launch spike + backlinks | Schedule a Tuesday launch |

## 3. README is the citable asset (already optimized)

The README is structured so AI engines (ChatGPT, Perplexity, Claude) cite it:
- Definition block in the first 60 words
- Comparison + before/after tables (most-cited content format)
- FAQ section phrased as real search queries
- Real statistics (67 skills, 43→51, 3→0 clusters)
- Dated + keyword footer

## 4. Product Hunt post

**Tagline:** "Find out why Claude keeps picking the wrong skill."

**Description:**
> Installed a bunch of Claude skills and noticed the wrong one keeps firing?
> skill-doctor scans your skill library, scores every pair for collisions, finds
> duplicate trigger phrases, and tells you exactly which skills to merge or
> separate. Open source, zero dependencies, runs offline.

**First comment (maker):** the real 67-skill before/after story + screenshot of the report.

## 5. Launch tweet / X thread

1/ Installed 50+ Claude skills and the wrong one keeps triggering?
That's not a bug — it's a collision. Two skill descriptions claim the same intent and Claude guesses. 🧵

2/ Collisions grow quadratically. 20 skills = 190 pairs. 67 skills = 2,211 pairs. You cannot audit that by hand.

3/ So I built skill-doctor 🩺 — it scores every pair (TF-IDF + trigger overlap), finds duplicate triggers, clusters confusable skills, and tells you what to merge.

4/ Ran it on a real 67-skill library: health 43→51, confusable clusters 3→0. It even caught collisions I created by merging packs that shared boilerplate.

5/ Open source, MIT, zero dependencies, runs offline. Audit yours:
`python3 -m scripts /path/to/skills`
[repo link]

## 6. Reddit / community (authentic only)

Post the before/after writeup in r/ClaudeAI and relevant Discords as a genuine
"I built this to fix my own problem" story. Do not spam — one good post with the
real data outperforms ten low-effort drops, and Reddit threads get cited by AI.

## 7. robots / AI-bot access

If you add a landing page later, allow GPTBot, PerplexityBot, ClaudeBot, and
Google-Extended so AI engines can cite it.

## 8. Follow-up content (topical authority)

- Blog post: "Why your Claude skills mis-fire (and the quadratic math behind it)"
- Short demo GIF of the report in the README
- A `comparison`-style page: skill-doctor vs manual review
