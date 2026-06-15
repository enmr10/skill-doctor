# AGENTS.md

Guidance for AI agents working in this repository.

## What this is
`skill-doctor` is a Claude Code skill (Agent Skills spec) plus a zero-dependency
Python engine that audits a skill library for description collisions and quality
issues.

## Layout
```
skill-doctor/
├── README.md                       # SEO/AI-SEO optimized landing doc
├── llms.txt                        # AI-context file
├── .claude-plugin/
│   ├── marketplace.json            # plugin marketplace manifest
│   └── plugin.json
└── skills/skill-doctor/
    ├── SKILL.md                    # the skill (instructions for the agent)
    ├── scripts/                    # the engine (Python 3.8+ stdlib only)
    │   ├── textutil.py             # TF-IDF, cosine, jaccard, trigger extraction
    │   ├── scanner.py              # load skills from dir or manifest.json
    │   ├── analyzer.py             # pairwise collision model + matrix
    │   ├── detector.py             # rule engine -> typed issues
    │   ├── recommender.py          # merge/absorb/disambiguate + clusters
    │   ├── reporter.py             # markdown + json + ascii heatmap
    │   ├── cli.py                  # argparse entry point + CI gate
    │   └── __main__.py
    └── references/                 # methodology, issue catalog, scoring, sample
```

## Run / test
```bash
cd skills/skill-doctor
python3 -m scripts <skills-dir-or-manifest.json>
python3 -m scripts <path> --format json --fail-on critical
```

## Conventions
- Pure standard library — never add a third-party dependency.
- Each detector rule is small, named, and emits a typed `Issue` with a `code`.
- The engine is read-only. Description rewrites are applied by the agent only
  after the user approves; never drop a real trigger phrase, only relocate it.
- Keep `SKILL.md` lean; put detail in `references/`.

## Adding a detector rule
Add a function-style block in `detector.py` that appends `Issue(code=..., severity=...)`.
Document the fix in `references/issue-catalog.md`.
