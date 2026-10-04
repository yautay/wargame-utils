"""Import a Markdown knowledge base written by the old `/indeksacja` skill (GCACW-PL, 2026-10)
into the canonical YAML layout. Lossless by design: every bullet that has no dedicated field goes to
`extra`, every paragraph that is not a bullet goes to `body`, so nothing is dropped.

Usage: wgu kb import-legacy <dir with reguly.md, definicje.md, …> [--specs <dir with PNN-*.md>]
"""
from __future__ import annotations

import re
from pathlib import Path

from .store import extract_ids, write_yaml

FIELD_RE = re.compile(r"^- \*\*(.+?):\*\*\s?(.*)$")

RULE_FIELDS = {
    "Źródło": "source", "Kiedy": "when", "Skutek": "effect", "Wyjątki / nadpisania": "exceptions",
    "Wyjątki": "exceptions", "Odwołania": "see", "Słowa kluczowe": "keywords", "Uwagi": "notes",
}
AMB_FIELDS = {
    "Cytat": "quotes", "Cytaty": "quotes", "Opis": "description", "Warianty": "readings",
    "Rekomendacja": "recommendation", "Skutek dla bazy": "impact", "Co rozstrzyga": "resolution_source",
}
STRENGTH = {"pewna": "certain", "prawdopodobna": "probable", "spekulatywna": "speculative"}


def _sections(md: str, level: int):
    """Split markdown into (heading, body_lines) at the given heading level, tracking the parent heading."""
    mark = "#" * level + " "
    parent_mark = "#" * (level - 1) + " "
    parent, cur, out, preamble = None, None, [], []
    for line in md.splitlines():
        if level > 1 and line.startswith(parent_mark):
            parent = line[len(parent_mark):].strip()
            if cur:
                out.append(cur)
                cur = None
            continue
        if line.startswith(mark):
            if cur:
                out.append(cur)
            cur = {"heading": line[len(mark):].strip(), "parent": parent, "lines": []}
        elif cur:
            cur["lines"].append(line)
        else:
            preamble.append(line)
    if cur:
        out.append(cur)
    return out, "\n".join(preamble).strip()


def _fields(lines: list[str], mapping: dict):
    """Parse '- **Label:** text' bullets (with continuation lines). Returns (fields, extra, body)."""
    fields, extra, body, cur = {}, {}, [], None
    for line in lines:
        m = FIELD_RE.match(line)
        if m:
            label, text = m.group(1).strip(), m.group(2).strip()
            base = re.sub(r"\s*\(.*\)$", "", label)
            key = mapping.get(label) or mapping.get(base)
            if key and key in fields:  # duplicate field → keep both
                fields[key] += "\n" + text
                cur = ("f", key)
            elif key:
                fields[key] = (f"({label[len(base):].strip(' ()')}) " if label != base else "") + text
                cur = ("f", key)
            else:
                extra[label] = text
                cur = ("e", label)
        elif line.strip() and cur and (line.startswith("  ") or line.startswith("\t")):
            tgt = fields if cur[0] == "f" else extra
            tgt[cur[1]] += "\n" + line.strip()
        elif line.strip():
            body.append(line.rstrip())
            cur = None
        else:
            cur = None
    return fields, extra, "\n".join(body).strip()


def _split_id(heading: str, pattern: str):
    m = re.match(rf"({pattern})\s+(.*)", heading)
    return (m.group(1), m.group(2).strip()) if m else (None, heading)


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def _parse_source(s: str) -> dict:
    out = {"text": s}
    m = re.search(r"s\.\s*([\d–\-, ]+\d)", s)
    if m:
        out["pages"] = m.group(1).strip()
    files = re.findall(r"`([^`]+?\.tex)(?::([\d\-–, ]+))?`", s)
    if files:
        out["translation"] = [_clean({"file": f, "lines": ln.strip()}) for f, ln in files]
    return out


# ---------------------------------------------------------------- rules
def import_rules(md: str) -> list[dict]:
    secs, _ = _sections(md, 3)
    chapters: dict[str, dict] = {}
    for s in secs:
        rid, title = _split_id(s["heading"], r"R-[\w.-]+")
        if not rid:
            continue
        f, extra, body = _fields(s["lines"], RULE_FIELDS)
        rule = {"id": rid, "title": title}
        sec = re.match(r"R-(\d+(?:\.\d+)?)", rid)
        if sec:
            rule["section"] = sec.group(1)
        if "source" in f:
            rule["source"] = _parse_source(f.pop("source"))
        if "[v1." in title or "[v" in f.get("effect", "")[:8]:
            rule["flags"] = ["changed"]
        if "keywords" in f:
            f["keywords"] = [k.strip() for k in re.split(r"[,;]", f["keywords"]) if k.strip()]
        rule.update(f)
        if extra:
            rule["extra"] = extra
        if body:
            rule["body"] = body
        rule["refs"] = [i for i in extract_ids("\n".join(s["lines"])) if i != rid]
        ch_title = s["parent"] or "—"
        chapters.setdefault(ch_title, {"chapter": {"title": ch_title}, "rules": []})["rules"].append(_clean(rule))
    return list(chapters.values())


# ---------------------------------------------------------------- terms
def _md_table(lines: list[str]):
    rows = [l for l in lines if l.strip().startswith("|")]
    if len(rows) < 2:
        return None, []
    split = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    head = split(rows[0])
    body = [split(r) for r in rows[2:] if not re.match(r"^\|[\s:\-|]+\|$", r.strip())]
    return head, body


def import_terms(md: str) -> dict:
    lines = md.splitlines()
    terms, confusables, notes, mode = [], [], [], "terms"
    head = None
    for line in lines:
        if line.startswith("## "):
            mode = "confusables" if re.search(r"myli|pomyl|confus", line, re.I) else "other"
            notes.append(line)
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if re.match(r"^[\s:\-|]+$", line.strip().strip("|")):
                continue
            if head is None or cells[0] in ("EN", "Para", "Termin"):
                head = cells
                continue
            row = dict(zip(head, cells))
            if mode == "confusables":
                confusables.append(row)
            elif "EN" in row:
                kind = {"T": "technical", "P": "descriptive"}.get(row.get("Typ", ""), row.get("Typ", ""))
                t = _clean({"en": row.get("EN"), "pl": row.get("PL"), "kind": kind,
                            "definition": row.get("Definicja (skrót)") or row.get("Definicja"),
                            "defined_at": row.get("Gdzie zdef."), "used_in": row.get("Użycie"),
                            "refs": extract_ids(row.get("Użycie", ""))})
                terms.append(t)
            else:
                notes.append(line)
        elif line.strip() and not line.startswith("# "):
            if mode == "confusables" and line.lstrip().startswith(("-", "*")):
                confusables.append({"text": line.lstrip("-* ").strip()})
            else:
                notes.append(line)
    return {"terms": terms, "confusables": confusables, "notes": "\n".join(notes).strip()}


# ---------------------------------------------------------------- ambiguities
def import_ambiguities(md: str) -> list[dict]:
    secs, _ = _sections(md, 3)
    out = []
    for s in secs:
        aid, title = _split_id(s["heading"], r"N-T?\d+")
        if not aid:
            continue
        f, extra, body = _fields(s["lines"], AMB_FIELDS)
        e = {"id": aid, "title": title, "group": s["parent"], "scope": "translation" if aid.startswith("N-T") else "original"}
        e.update(f)
        rec = f.get("recommendation", "") + " " + body
        m = re.search(r"\*\*(pewna|prawdopodobna|spekulatywna)\*\*", rec, re.I)
        if m:
            e["strength"] = STRENGTH[m.group(1).lower()]
        e["status"] = "open"
        if extra:
            e["extra"] = extra
        if body:
            e["body"] = body
        e["refs"] = extract_ids("\n".join(s["lines"]))
        out.append(_clean(e))
    return out


# ---------------------------------------------------------------- scenarios (control questions)
def import_scenarios(md: str) -> list[dict]:
    secs, _ = _sections(md, 3)
    out = []
    for s in secs:
        qid, question = _split_id(s["heading"], r"Q-\d+")
        if not qid:
            continue
        text = "\n".join(s["lines"]).strip()
        ans = re.search(r"\*\*Odp\.:\*\*\s*(.*?)(?=\n\*\*Łańcuch|\Z)", text, re.S)
        chain = re.search(r"\*\*Łańcuch:\*\*\s*(.*)", text, re.S)
        e = {"id": qid, "question": question, "answer": ans.group(1).strip() if ans else text,
             "chain": chain.group(1).strip() if chain else "", "refs": extract_ids(chain.group(1) if chain else text),
             "group": s["parent"]}
        out.append(_clean(e))
    return out


# ---------------------------------------------------------------- tables
def import_tables(md: str) -> list[dict]:
    secs, _ = _sections(md, 2)
    out = []
    for s in secs:
        tid, title = _split_id(s["heading"], r"T-[A-Z0-9]+")
        if not tid:
            tid, title = "T-NOTE-" + str(len(out) + 1), s["heading"]
        blocks, notes, cur = [], [], []
        for line in s["lines"] + [""]:
            if line.strip().startswith("|"):
                cur.append(line)
                continue
            if cur:
                head, rows = _md_table(cur)
                blocks.append({"columns": head, "rows": rows})
                cur = []
            if line.strip():
                notes.append(line.rstrip())
        m = re.search(r"\(([^)]*R-[^)]*)\)\s*$", title)
        e = {"id": tid, "title": title, "tables": blocks, "notes": "\n".join(notes).strip(),
             "refs": extract_ids("\n".join(s["lines"]) + " " + (m.group(1) if m else ""))}
        out.append(_clean(e))
    return out


# ---------------------------------------------------------------- procedures
MARKERS = {"[D]": "decision", "[P]": "reaction", "[R]": "roll", "[!]": "pitfall"}


def _steps(lines: list[str]):
    steps, notes = [], []
    for line in lines:
        m = re.match(r"^\s*(\d+[a-z]?)\.\s+(.*)$", line) or re.match(r"^\s*[-*]\s+(?:())(.*)$", line)
        if m:
            text = m.group(2).strip()
            steps.append(_clean({"n": m.group(1) or str(len(steps) + 1) + "*", "text": text,
                                 "markers": [v for k, v in MARKERS.items() if k in text],
                                 "refs": extract_ids(text)}))
        elif line.strip() and steps and line.startswith("   "):
            steps[-1]["text"] += "\n" + line.strip()
        elif line.strip():
            notes.append(line.rstrip())
    return steps, "\n".join(notes).strip()


def import_procedures(md: str) -> tuple[list[dict], str]:
    lines = md.splitlines()
    procs, cur, legend = [], None, []
    for line in lines + ["## END"]:
        m2 = re.match(r"^(##|###) (P-[\w]+)\s+(.*)$", line)
        if m2 or line.startswith("## "):
            if cur:
                steps, notes = _steps(cur["lines"])
                e = _clean({"id": cur["id"], "title": cur["title"], "steps": steps, "notes": notes,
                            "refs": extract_ids(cur["title"])})
                if cur["sub"] and procs:
                    procs[-1].setdefault("subprocedures", []).append(e)
                else:
                    procs.append(e)
                cur = None
            if m2:
                cur = {"id": m2.group(2), "title": m2.group(3).strip(), "sub": m2.group(1) == "###", "lines": []}
            elif line != "## END":
                legend.append(line)
            continue
        if cur:
            cur["lines"].append(line)
        elif line.strip() and not line.startswith("# "):
            legend.append(line)
    return procs, "\n".join(legend).strip()


# ---------------------------------------------------------------- changes
def import_changes(md: str) -> tuple[list[dict], str]:
    secs, pre = _sections(md, 2)
    changes, notes = [], [pre] if pre else []
    for s in secs:
        head, rows = _md_table(s["lines"])
        if head and rows and "Zmiana" in " ".join(head):
            group = s["heading"]
            for r in rows:
                row = dict(zip(head, r))
                n = row.get("#", str(len(changes) + 1))
                changes.append(_clean({"id": f"C-{group[0]}{int(n):02d}" if n.isdigit() else f"C-{group[0]}{n}",
                                       "group": group, "place": row.get("Miejsce"), "change": row.get("Zmiana"),
                                       "effect": row.get("Skutek dla gry") or row.get("Skutek"),
                                       "rules": row.get("ID"), "refs": extract_ids(row.get("ID", "")),
                                       "extra": {k: v for k, v in row.items() if k not in ("#", "Miejsce", "Zmiana", "Skutek dla gry", "Skutek", "ID") and v}}))
            rest = [l for l in s["lines"] if not l.strip().startswith("|") and l.strip()]
            if rest:
                notes.append(f"## {s['heading']}\n" + "\n".join(rest))
        else:
            notes.append(f"## {s['heading']}\n" + "\n".join(s["lines"]).strip())
    return changes, "\n\n".join(notes).strip()


# ---------------------------------------------------------------- relations (overrides graph)
def import_relations(md: str) -> list[dict]:
    """Best-effort: lines 'R-a (…) ← nadpisane przez / wyjątki: R-b (…), R-c (…)' → edges b overrides a.
    The narrative stays in notes/dependencies.md; edges are a starting point for the analyst to verify."""
    rels = []
    for line in md.splitlines():
        if "←" not in line:
            continue
        left, right = line.split("←", 1)
        targets = [i for i in extract_ids(left) if i.startswith("R-")]
        if not targets:
            continue
        for part in re.split(r"[,;]\s*(?=R-)|←", right):
            ids = [i for i in extract_ids(part) if i.startswith("R-")]
            if not ids:
                continue
            cond = re.sub(r"^\s*(nadpisane przez|wyjątki?:?)\s*", "", part).strip(" ,.;")
            rels.append({"from": ids[0], "to": targets[0], "type": "overrides", "note": cond[:300],
                         "status": "imported"})
    seen, out = set(), []
    for r in rels:
        k = (r["from"], r["to"])
        if k not in seen and r["from"] != r["to"]:
            seen.add(k)
            out.append(r)
    return out


# ---------------------------------------------------------------- aid specs (PNN-*.md)
def import_aid(md: str) -> dict:
    lines = md.splitlines()
    m = re.match(r"#\s+(P\d+)\s+(.*?)(?:\s+—\s+(.*))?$", lines[0])
    aid = {"id": m.group(1), "title": m.group(2).strip(), "kind": (m.group(3) or "").strip()} if m else {"id": "?", "title": lines[0]}
    secs, pre = _sections("\n".join(lines[1:]), 2)
    aid["header"] = lines[0].lstrip("# ").strip()
    for line in pre.splitlines():
        line = line.lstrip("- ").strip()
        for part in line.split(" · "):
            k, _, v = part.partition(":")
            key = {"Typ": "type", "Format": "format", "Priorytet": "priority", "Złożoność": "complexity",
                   "Moment użycia": "use_moment", "Reguły źródłowe": "sources"}.get(k.strip())
            if key:
                aid[key] = int(v.strip()) if key == "priority" and v.strip().isdigit() else v.strip()
    aid["sections"] = {}
    nodes, edges = [], []
    for s in secs:
        h = s["heading"]
        if h.startswith("Kryteria akceptacji"):
            aid["acceptance"] = [l.lstrip("-* ").strip() for l in s["lines"] if l.strip().startswith(("-", "*"))]
            continue
        # Node tables (| ID | Kształt | Tekst | Reguła |) and edge tables (| Z | Do | Etykieta |) may appear in any
        # section or subsection; they become nodes/edges (with the subsection as `group`), the rest stays as text.
        rest, table, group = [], [], None
        for line in s["lines"] + [""]:
            if line.strip().startswith("|"):
                table.append(line)
                continue
            if table:
                head, rows = _md_table(table)
                hk = [c.lower() for c in head or []]
                if hk[:3] == ["id", "kształt", "tekst"]:
                    nodes += [_clean({"id": r[0], "shape": r[1], "text": r[2], "rules": r[3] if len(r) > 3 else "",
                                      "refs": extract_ids(r[3] if len(r) > 3 else ""), "group": group}) for r in rows]
                    rest.append(f"<!-- nodes: {', '.join(r[0] for r in rows)} -->")
                elif hk[:2] == ["z", "do"]:
                    edges += [_clean({"from": r[0], "to": r[1], "label": r[2] if len(r) > 2 else ""}) for r in rows]
                    rest.append(f"<!-- edges: {len(rows)} -->")
                else:
                    rest += table
                table = []
            if line.startswith("### "):
                group = line[4:].strip()
            rest.append(line)
        text = "\n".join(rest).strip()
        if re.sub(r"<!--.*?-->", "", text).strip():
            aid["sections"][h] = text
    if nodes:
        aid["nodes"] = nodes
    if edges:
        aid["edges"] = edges
    aid["refs"] = extract_ids(md)
    aid["status"] = "spec"
    return _clean(aid)


# ---------------------------------------------------------------- driver
def _preamble(md: str) -> str:
    """Text between the H1 title and the first H2/H3 (file conventions)."""
    out = []
    for line in md.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            break
        out.append(line)
    return "\n".join(out).strip()


def run(legacy_dir: Path, kb_dir: Path, specs_dir: Path | None, manifest: dict) -> dict:
    rd = lambda n: (legacy_dir / n).read_text(encoding="utf-8") if (legacy_dir / n).exists() else ""
    stats = {}
    manifest = dict(manifest)
    manifest["legacy_conventions"] = {n: _preamble(rd(n)) for n in
                                      ["reguly.md", "definicje.md", "tabele.md", "procedury.md", "niejasnosci.md",
                                       "pytania_kontrolne.md", "zmiany.md"] if _preamble(rd(n))}
    chapters = import_rules(rd("reguly.md"))
    for i, ch in enumerate(chapters, 1):
        m = re.match(r"(\d+(?:\.\d+)?|[A-Z][\w ]*?)\b", ch["chapter"]["title"])
        slug = re.sub(r"[^a-z0-9]+", "-", ch["chapter"]["title"].lower().split("/")[0]).strip("-")[:40]
        ch["chapter"]["id"] = f"CH-{i:02d}"
        write_yaml(kb_dir / "rules" / f"{i:02d}-{slug or 'misc'}.yaml", ch)
    stats["rules"] = sum(len(c["rules"]) for c in chapters)

    t = import_terms(rd("definicje.md"))
    write_yaml(kb_dir / "terms.yaml", t)
    stats["terms"] = len(t["terms"])
    write_yaml(kb_dir / "tables.yaml", {"tables": (tabs := import_tables(rd("tabele.md")))})
    stats["tables"] = len(tabs)
    procs, legend = import_procedures(rd("procedury.md"))
    write_yaml(kb_dir / "procedures.yaml", {"legend": legend, "procedures": procs})
    stats["procedures"] = len(procs)
    write_yaml(kb_dir / "ambiguities.yaml", {"ambiguities": (amb := import_ambiguities(rd("niejasnosci.md")))})
    stats["ambiguities"] = len(amb)
    write_yaml(kb_dir / "scenarios.yaml", {"scenarios": (sc := import_scenarios(rd("pytania_kontrolne.md")))})
    stats["scenarios"] = len(sc)
    ch_list, ch_notes = import_changes(rd("zmiany.md"))
    write_yaml(kb_dir / "changes.yaml", {"changes": ch_list, "notes": ch_notes})
    stats["changes"] = len(ch_list)
    rels = import_relations(rd("zaleznosci.md"))
    write_yaml(kb_dir / "relations.yaml", {"relations": rels})
    stats["relations"] = len(rels)

    notes = kb_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    for src, dst in [("przeglad.md", "overview.md"), ("zaleznosci.md", "dependencies.md"), ("INDEX.md", "legacy-index.md")]:
        if (legacy_dir / src).exists():
            (notes / dst).write_text(rd(src), encoding="utf-8", newline="\n")

    if specs_dir and specs_dir.exists():
        n = 0
        for f in sorted(specs_dir.glob("P*.md")):
            write_yaml(kb_dir / "aids" / (f.stem + ".yaml"), import_aid(f.read_text(encoding="utf-8")))
            n += 1
        stats["aids"] = n

    manifest.setdefault("history", []).append({"event": "import-legacy", "from": str(legacy_dir), "stats": stats})
    write_yaml(kb_dir / "manifest.yaml", manifest)
    return stats
