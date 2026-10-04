"""Load terminology layers.

Layer files live in the tool repo (`terminology/<path>.yaml`: common, era/…, series/…) and in the game repo
(`terminology.game` in wgu.yaml, default kb/terminology.yaml). Order = generality: common < era < series < game.
The game project lists the shared layers it uses in wgu.yaml → terminology.layers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..kb.store import read_yaml

TOOL_ROOT = Path(__file__).resolve().parent.parent.parent
LEVEL_ORDER = {"common": 0, "era": 1, "series": 2, "game": 3}


@dataclass
class Terminology:
    files: list[tuple[Path, dict]] = field(default_factory=list)   # (path, file data) general → specific
    concepts: dict[str, dict] = field(default_factory=dict)        # id → concept (with _layer, _file)
    effective: dict[str, dict] = field(default_factory=dict)       # id → concept after `overrides` applied

    def by_source_term(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for c in self.effective.values():
            for t in [c["source_term"], *c.get("variants", [])]:
                out.setdefault(t.lower(), []).append(c)
        return out


def layer_paths(project) -> list[Path]:
    cfg = project.data.get("terminology", {}) if project else {}
    layers = cfg.get("layers", ["common"])
    paths = [TOOL_ROOT / "terminology" / f"{l}.yaml" for l in layers]
    game = cfg.get("game", "kb/terminology.yaml")
    if project and game:
        paths.append(project.root / game)
    return paths


def load(paths: list[Path]) -> Terminology:
    t = Terminology()
    for p in paths:
        data = read_yaml(p)
        if not data:
            continue
        t.files.append((p, data))
        for c in data.get("concepts", []):
            c = dict(c)
            c["_layer"] = data["layer"]["id"]
            c["_level"] = c.get("level") or data["layer"]["level"]
            c["_file"] = str(p)
            t.concepts[c["id"]] = c
    eff = dict(t.concepts)
    for cid, c in t.concepts.items():
        if c.get("overrides") and c["overrides"] in eff:
            eff.pop(c["overrides"], None)
    t.effective = eff
    return t


def forms(c: dict) -> list[str]:
    """All allowed Polish forms of a concept (lemma + declared inflections), longest first."""
    fs = {f for f in [c.get("pl", ""), *c.get("pl_forms", [])] if f}
    if c.get("pl_abbrev"):
        fs.add(c["pl_abbrev"])
    return sorted(fs, key=len, reverse=True)


def rejected_forms(c: dict) -> list[tuple[str, str]]:
    out = []
    for r in c.get("rejected", []):
        for f in {r["pl"], *r.get("forms", [])}:
            out.append((f, r["reason"]))
    return out


def old_forms(c: dict) -> list[tuple[str, dict]]:
    out = []
    for h in c.get("history", []):
        for f in {h.get("from", ""), *h.get("from_forms", [])}:
            if f:
                out.append((f, h))
    return out


def word_re(phrase: str, ignore_case=True) -> re.Pattern:
    """Whole-word match for a (multi-word) phrase; tolerant to line breaks and LaTeX spaces (~)."""
    parts = [re.escape(p) for p in phrase.split()]
    body = r"(?:\s+|~)".join(parts)
    return re.compile(rf"(?<![\w]){body}(?![\w])", re.I if ignore_case else 0)
