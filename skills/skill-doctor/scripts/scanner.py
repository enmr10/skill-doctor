"""
scanner.py — Discover and parse skills from a directory tree or a manifest.

Supports two input modes:
  1. Directory of skills:  <root>/<skill-name>/SKILL.md
  2. A manifest.json (Claude Code skills-plugin manifest) listing skills.

Frontmatter parsing is done with a tolerant, dependency-free parser that
handles YAML folded (`>`) and literal (`|`) scalars for `description`.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

NAME_RULE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Skill:
    name: str
    description: str
    path: str                      # SKILL.md path or "manifest:<file>"
    dir_name: str = ""             # parent directory name (for name-match check)
    body_len: int = 0              # lines in SKILL.md body (excl. frontmatter)
    raw_frontmatter: str = ""
    metadata: dict = field(default_factory=dict)
    source: str = "dir"            # "dir" | "manifest"

    @property
    def desc_len(self) -> int:
        return len(self.description)


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


def parse_frontmatter(text: str) -> Optional[dict]:
    """
    Extract the leading `--- ... ---` YAML block into a dict.
    Handles `key: value`, folded `key: >`, and literal `key: |` scalars.
    Returns None if no frontmatter found.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    lines = block.split("\n")
    data: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z_][\w\-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            # Folded/literal scalar: gather subsequent indented lines.
            collected = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or lines[i] == ""):
                collected.append(lines[i].strip())
                i += 1
            joiner = "\n" if val.startswith("|") else " "
            data[key] = joiner.join(c for c in collected).strip()
            continue
        data[key] = _strip_quotes(val)
        i += 1
    return data


def _body_line_count(text: str) -> int:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            body = text[nl + 1:] if nl != -1 else ""
            return body.count("\n") + 1
    return text.count("\n") + 1


def scan_directory(root: str) -> List[Skill]:
    """Walk `root` and load every SKILL.md found (one level or nested)."""
    skills: List[Skill] = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower() == "skill.md":
                full = os.path.join(dirpath, fn)
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                except OSError:
                    continue
                fm = parse_frontmatter(text) or {}
                name = (fm.get("name") or "").strip()
                dir_name = os.path.basename(dirpath)
                skills.append(Skill(
                    name=name or dir_name,
                    description=(fm.get("description") or "").strip(),
                    path=full,
                    dir_name=dir_name,
                    body_len=_body_line_count(text),
                    raw_frontmatter=text[:text.find("\n---", 3) + 4] if text.startswith("---") else "",
                    metadata={k: v for k, v in fm.items() if k not in ("name", "description")},
                    source="dir",
                ))
    return skills


def scan_manifest(manifest_path: str) -> List[Skill]:
    """Load skills from a Claude Code skills-plugin manifest.json."""
    with open(manifest_path, "r", encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    skills: List[Skill] = []
    for entry in data.get("skills", []):
        skills.append(Skill(
            name=(entry.get("name") or "").strip(),
            description=(entry.get("description") or "").strip(),
            path=f"manifest:{os.path.basename(manifest_path)}",
            dir_name=(entry.get("name") or "").strip(),
            metadata={k: v for k, v in entry.items()
                      if k not in ("name", "description")},
            source="manifest",
        ))
    return skills


def load_skills(target: str) -> List[Skill]:
    """Auto-detect input type and load skills."""
    if os.path.isfile(target) and target.lower().endswith(".json"):
        return scan_manifest(target)
    if os.path.isdir(target):
        return scan_directory(target)
    raise FileNotFoundError(f"Not a skills directory or manifest.json: {target}")
