"""
cli.py — Command-line entry point for skill-doctor.

Usage:
    python3 -m scripts <path> [options]

<path> is either a directory of skills (each <name>/SKILL.md) or a
Claude Code manifest.json.

Options:
    --format md|json|both     Output format (default: md)
    --out FILE                Write report to FILE instead of stdout
    --merge-at FLOAT          Collision score to recommend MERGE (default 0.55)
    --disambig-at FLOAT       Collision score to recommend DISAMBIGUATE (0.30)
    --fail-on critical|high   Exit non-zero if issues at/above this severity (CI)
    --top N                   Limit top-collision listing
    --quiet                   Suppress progress messages
"""

from __future__ import annotations

import argparse
import sys

from .analyzer import analyze
from .detector import DEFAULTS, detect
from .recommender import recommend
from .reporter import health_score, to_json, to_markdown
from .scanner import load_skills


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skill-doctor",
        description="Audit a skill library for description collisions and quality issues.",
    )
    p.add_argument("path", help="skills directory or manifest.json")
    p.add_argument("--format", choices=["md", "json", "both"], default="md")
    p.add_argument("--out", default=None, help="write report to file")
    p.add_argument("--merge-at", type=float, default=0.55)
    p.add_argument("--disambig-at", type=float, default=0.30)
    p.add_argument("--collision-critical", type=float, default=DEFAULTS["collision_critical"])
    p.add_argument("--collision-high", type=float, default=DEFAULTS["collision_high"])
    p.add_argument("--vague-threshold", type=float, default=DEFAULTS["vague_threshold"])
    p.add_argument("--fail-on", choices=["critical", "high", "medium"], default=None)
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--quiet", action="store_true")
    return p


def _force_utf8_stdio():
    """
    Windows consoles default to cp1252 and crash on emoji/Unicode in the
    report. Reconfigure stdout/stderr to UTF-8 where supported; fall back to
    a wrapper for older interpreters.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except (ValueError, OSError):
                pass
        try:
            import io
            buffer = getattr(stream, "buffer", None)
            if buffer is not None:
                setattr(sys, stream_name,
                        io.TextIOWrapper(buffer, encoding="utf-8",
                                         errors="replace", line_buffering=True))
        except (ValueError, OSError, AttributeError):
            pass


def main(argv=None) -> int:
    _force_utf8_stdio()
    args = build_parser().parse_args(argv)

    def log(msg):
        if not args.quiet:
            print(msg, file=sys.stderr)

    log(f"[skill-doctor] loading skills from {args.path} ...")
    try:
        skills = load_skills(args.path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not skills:
        print("ERROR: no skills found.", file=sys.stderr)
        return 2

    log(f"[skill-doctor] {len(skills)} skills loaded. Analyzing ...")
    result = analyze(skills)
    cfg = {
        "collision_critical": args.collision_critical,
        "collision_high": args.collision_high,
        "vague_threshold": args.vague_threshold,
    }
    issues = detect(result, cfg)
    recs = recommend(result, merge_at=args.merge_at, disambig_at=args.disambig_at)

    md = to_markdown(result, issues, recs)
    js = to_json(result, issues, recs)

    if args.format == "json":
        output = js
    elif args.format == "both":
        output = md + "\n\n<!-- JSON -->\n```json\n" + js + "\n```"
    else:
        output = md

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output)
        log(f"[skill-doctor] report written to {args.out}")
    else:
        print(output)

    log(f"[skill-doctor] health score: {health_score(result, issues)}/100")

    # CI gate
    if args.fail_on:
        order = {"critical": 0, "high": 1, "medium": 2}
        thresh = order[args.fail_on]
        sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        worst = min((sev_rank.get(i.severity, 9) for i in issues), default=9)
        if worst <= thresh:
            log(f"[skill-doctor] FAIL: issues at/above '{args.fail_on}' present.")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
