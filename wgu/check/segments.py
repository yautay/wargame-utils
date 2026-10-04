"""Source ↔ translation alignment by segment markers.

A marker is a line `%@ KEY` (KEY = rule number or chunk id, e.g. `6.52`, `7.6.3`, `hist-1`) placed before the
segment it opens, in BOTH the prepared source chunk (plain text/Markdown from `wgu pdf extract`) and the LaTeX
translation. Translators copy markers unchanged. `wgu text mark` inserts markers into a source chunk automatically
before numbered rule headings.
"""
from __future__ import annotations

import re
from pathlib import Path

MARK = re.compile(r"^\s*%@\s*(\S+)\s*$")
HYPHEN = re.compile(r"([^\W\d_])-\**[ \t]*\n[ \t*]*([a-ząćęłńóśźż])")


def dehyphenate(text: str) -> str:
    """Join words split by end-of-line hyphenation in PDF extracts (Skir- / misher -> Skirmisher)."""
    return HYPHEN.sub(r"\1\2", text)


def segments_of(path: Path) -> dict[str, str]:
    segs, key, buf = {}, None, []
    for line in dehyphenate(path.read_text(encoding="utf-8")).splitlines():
        m = MARK.match(line)
        if m:
            if key is not None:
                segs[key] = "\n".join(buf).strip()
            key, buf = m.group(1), []
        elif key is not None:
            buf.append(line)
    if key is not None:
        segs[key] = "\n".join(buf).strip()
    return segs


DEFAULT_HEADING = r"^\s*(?:§|\*\*|\[\[B:)*\s*(\d+(?:\.\d+)+)\b"


def mark(src: Path, out: Path, pattern: str = DEFAULT_HEADING) -> int:
    rx = re.compile(pattern)
    lines, n = [], 0
    for line in src.read_text(encoding="utf-8").splitlines():
        m = rx.match(line)
        if m:
            lines.append(f"%@ {m.group(1)}")
            n += 1
        lines.append(line)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{n} markers -> {out}")
    return 0
