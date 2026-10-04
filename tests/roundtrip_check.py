"""Lossless-import check: every non-trivial line of the legacy Markdown must appear (normalised) in the YAML KB.

Usage: python tests/roundtrip_check.py <legacy dir> <kb dir> [<specs dir>]
"""
import re
import sys
from pathlib import Path

import yaml


def norm(s: str) -> str:
    s = re.sub(r"^\s*(#+|[-*]|\d+[a-z]?\.)\s+", "", s)
    s = re.sub(r"\*\*[^*]+?:\*\*", "", s)          # field labels
    s = re.sub(r"[`*|>\s]+", "", s)
    return s


def flatten(o):
    if isinstance(o, dict):
        return " ".join(flatten(v) for v in o.values()) + " " + " ".join(map(str, o.keys()))
    if isinstance(o, list):
        return " ".join(flatten(v) for v in o)
    return str(o)


def main():
    legacy, kb = Path(sys.argv[1]), Path(sys.argv[2])
    specs = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    corpus = ""
    for f in kb.rglob("*.yaml"):
        corpus += flatten(yaml.safe_load(f.read_text(encoding="utf-8")))
    for f in kb.rglob("*.md"):
        corpus += f.read_text(encoding="utf-8")
    corpus = norm(corpus.replace("\n", " "))
    files = list(legacy.glob("*.md")) + (list(specs.glob("*.md")) if specs else [])
    missing = 0
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^\s*\|[\s:\-|]+\|\s*$", line):
                continue
            cells = [c for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else [line]
            for c in cells:
                n = norm(c)
                if len(n) > 3 and n not in corpus:
                    missing += 1
                    if missing <= 40:
                        print(f"{f.name}:{i}: {c.strip()[:120]}")
    print(f"missing fragments: {missing}")
    sys.exit(1 if missing else 0)


main()
