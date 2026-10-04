"""Load and save the canonical YAML knowledge base (layout: docs/ARCHITECTURE.md §3)."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

# Collections stored one file each in kb/<name>.yaml under the top-level key of the same name.
COLLECTIONS = ["terms", "tables", "procedures", "relations", "ambiguities", "changes", "scenarios"]

ID_RE = re.compile(r"\b(?:R-[A-Z0-9][A-Za-z0-9]*(?:[.-][A-Za-z0-9]+)*|N-T?\d+|Q-\d+|T-[A-Z0-9]+|P-\d+[A-Za-z]?|C-[A-Z]?\d+|P\d{2})\b")


class _Dumper(yaml.SafeDumper):
    pass


def _str_repr(dumper, s: str):
    style = "|" if "\n" in s else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)


_Dumper.add_representer(str, _str_repr)


def dump(data) -> str:
    return yaml.dump(data, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=10_000, indent=2)


def write_yaml(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(data), encoding="utf-8", newline="\n")


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None


def load_kb(kb_dir: Path) -> dict:
    """Return {'manifest', 'chapters': [{chapter, rules}], 'rules': [flat], <collections>, 'aids': [...]}"""
    kb = {"manifest": read_yaml(kb_dir / "manifest.yaml") or {}, "chapters": [], "rules": []}
    for f in sorted((kb_dir / "rules").glob("*.yaml")):
        ch = read_yaml(f) or {}
        ch["_file"] = str(f.relative_to(kb_dir)).replace("\\", "/")
        kb["chapters"].append(ch)
        for r in ch.get("rules", []):
            kb["rules"].append(r)
    for c in COLLECTIONS:
        kb[c] = (read_yaml(kb_dir / f"{c}.yaml") or {}).get(c, [])
    kb["aids"] = []
    for f in sorted((kb_dir / "aids").glob("*.yaml")):
        a = read_yaml(f) or {}
        a["_file"] = str(f.relative_to(kb_dir)).replace("\\", "/")
        kb["aids"].append(a)
    return kb


def all_ids(kb: dict) -> dict[str, str]:
    """id -> kind for every addressable entity."""
    ids = {}
    for r in kb["rules"]:
        ids[r["id"]] = "rule"
    for t in kb["terms"]:
        if t.get("id"):
            ids[t["id"]] = "term"
    for c in ["tables", "procedures", "ambiguities", "changes", "scenarios"]:
        for e in kb[c]:
            ids[e["id"]] = c[:-1]
            for s in e.get("subprocedures", []) or []:
                ids[s["id"]] = "procedure"
    for a in kb["aids"]:
        ids[a["id"]] = "aid"
    return ids


def extract_ids(text: str) -> list[str]:
    """IDs mentioned in free text, in order, unique. Expands ranges like R-7.6.1–R-7.6.11."""
    if not text:
        return []
    out = []
    for m in re.finditer(r"(R-[\w.-]*?\.)(\d+)\s*[–-]\s*(R-[\w.-]*\.)?(\d+)\b", text):
        prefix, a, prefix2, b = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        if (prefix2 is None or prefix2 == prefix) and 0 < b - a < 40:
            out += [f"{prefix}{i}" for i in range(a, b + 1)]
    out += [m.group(0).rstrip(".-") for m in ID_RE.finditer(text)]
    seen, res = set(), []
    for i in out:
        if i not in seen:
            seen.add(i)
            res.append(i)
    return res


def text_of(entity) -> str:
    """All string content of an entity, for reference extraction."""
    if isinstance(entity, str):
        return entity
    if isinstance(entity, dict):
        return "\n".join(text_of(v) for k, v in entity.items() if k not in ("id", "refs", "_file"))
    if isinstance(entity, list):
        return "\n".join(text_of(v) for v in entity)
    return ""


def known(ref: str, ids: dict) -> bool:
    """True if ref is a known id, a sub-point of one (R-6.3.6a -> R-6.3.6) or a wildcard (R-OPT-LI.x)."""
    if ref in ids or ref.endswith(".x"):
        return True
    base = re.sub(r"[a-z]+$", "", ref)
    return base != ref and base in ids
