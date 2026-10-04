"""Terminology operations: lint, check (translation consistency), impact (term change), show, LaTeX glossary, import.

`check` and `impact` are mechanical aids. Finding the approved forms in a text does NOT prove the translation is
correct — the meaning check (pass 2) and language editing (pass 3) are separate steps of the skill.
"""
from __future__ import annotations

import datetime
import json
import re
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

from ..kb.store import dump, read_yaml, write_yaml
from .store import forms, layer_paths, load, old_forms, rejected_forms, word_re

SCHEMA = Path(__file__).resolve().parent.parent / "schemas" / "terminology.schema.json"


def _strip_tex_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", line)


def _files(paths: list[str]) -> list[Path]:
    out = []
    for p in paths:
        p = Path(p)
        out += sorted(p.rglob("*.tex")) if p.is_dir() else [p]
    return out


# ------------------------------------------------------------------ lint
def lint(project) -> int:
    paths = layer_paths(project)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    errors, warnings = [], []
    for p in paths:
        data = read_yaml(p)
        if data is None:
            warnings.append(f"{p}: missing layer file")
            continue
        for e in v.iter_errors(data):
            errors.append(f"{p.name}:{'/'.join(map(str, e.absolute_path))}: {e.message[:160]}")
    t = load(paths)
    seen = defaultdict(list)
    for p, data in t.files:
        for c in data.get("concepts", []):
            seen[c["id"]].append(p.name)
    for cid, fs in seen.items():
        if len(fs) > 1:
            errors.append(f"duplicate concept id {cid} in {fs}")
    for c in t.concepts.values():
        cid = c["id"]
        if c["status"] == "approved":
            if not c.get("pl"):
                errors.append(f"{cid}: approved without `pl`")
            if not c.get("rationale") and c.get("decided_by") not in ("user", "imported"):
                warnings.append(f"{cid}: approved by {c.get('decided_by')} without rationale")
            if not c.get("evidence") and c.get("decided_by") == "analyst":
                warnings.append(f"{cid}: approved by analyst without evidence")
        if c.get("overrides") and c["overrides"] not in t.concepts:
            errors.append(f"{cid}: overrides unknown concept {c['overrides']}")
        for r in c.get("related", []):
            if r not in t.concepts:
                warnings.append(f"{cid}: related to unknown concept {r}")
        if c["status"] in ("approved", "proposal") and c.get("pl") and not c.get("pl_forms"):
            warnings.append(f"{cid}: no pl_forms — consistency checks only see the lemma '{c['pl']}'")
    # same source term, several effective concepts → must be disambiguated
    for term, cs in t.by_source_term().items():
        ids = sorted({c["id"] for c in cs})
        if len(ids) > 1:
            undis = [c["id"] for c in cs if not c.get("disambiguation")]
            if undis:
                warnings.append(f"source term '{term}' has {len(ids)} concepts {ids}; missing `disambiguation` in {undis}")
    # one Polish form used for different concepts with different senses (possible conflation)
    owner = defaultdict(set)
    for c in t.effective.values():
        if c["status"] in ("approved", "proposal"):
            for f in forms(c):
                owner[f.lower()].add(c["id"])
    for f, ids in owner.items():
        if len(ids) > 1:
            warnings.append(f"Polish form '{f}' shared by concepts {sorted(ids)} — intended? (merging distinct mechanics is not allowed)")
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    st = defaultdict(int)
    for c in t.effective.values():
        st[c["status"]] += 1
    print(f"\n{len(t.effective)} concepts ({dict(st)}) in {len(t.files)} layers; {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


# ------------------------------------------------------------------ check
def check(project, paths: list[str]) -> int:
    t = load(layer_paths(project))
    findings = []
    for f in _files(paths):
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, raw in enumerate(lines, 1):
            line = _strip_tex_comments(raw)
            if not line.strip():
                continue
            for c in t.effective.values():
                for form, reason in rejected_forms(c):
                    if word_re(form).search(line) and not any(word_re(ok).search(line) and form.lower() in ok.lower() for ok in forms(c)):
                        findings.append(("ERROR", f, i, c["id"], f"rejected form '{form}' ({reason}); approved: '{c.get('pl')}'"))
                olds = sorted({form for form, h in old_forms(c) if word_re(form).search(line)})
                if olds and not any(word_re(ok).search(line) for ok in forms(c)):
                    date = (c.get("history") or [{}])[-1].get("date")
                    findings.append(("update", f, i, c["id"], f"old equivalent {', '.join(repr(o) for o in olds)} (changed {date} → '{c.get('pl')}')"))
                if c["status"] == "disputed":
                    for form in forms(c):
                        if word_re(form).search(line):
                            findings.append(("info", f, i, c["id"], f"disputed term '{form}' used"))
                            break
    for sev, f, i, cid, msg in findings:
        print(f"{sev:6s} {f}:{i}  [{cid}] {msg}")
    print(f"\n{sum(1 for x in findings if x[0] == 'ERROR')} errors, {sum(1 for x in findings if x[0] == 'update')} to update, "
          f"{sum(1 for x in findings if x[0] == 'info')} info")
    return 1 if any(x[0] == "ERROR" for x in findings) else 0


# ------------------------------------------------------------------ impact
def impact(project, cid: str, tex_paths: list[str], src_paths: list[str]) -> int:
    """Where would a change of concept `cid` matter? Lists translation lines with current/old/rejected forms and
    source segments (by `%@ KEY` markers) that contain the source term, mapped to translation segments with the same key."""
    t = load(layer_paths(project))
    c = t.concepts.get(cid)
    if not c:
        raise SystemExit(f"unknown concept {cid}")
    pats = [(f, "current") for f in forms(c)] + [(f, "old") for f, _ in old_forms(c)] + [(f, "rejected") for f, _ in rejected_forms(c)]
    print(f"# {cid}: {c['source_term']} → {c.get('pl')} ({c['status']})")
    print("\n## Translation lines")
    hits_by_key = defaultdict(list)
    for f in _files(tex_paths):
        key = None
        for i, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"\s*%@\s*(\S+)", raw)
            if m:
                key = m.group(1)
                continue
            line = _strip_tex_comments(raw)
            for form, kind in pats:
                if word_re(form).search(line):
                    print(f"{f}:{i}  [{key or '-'}] {kind}: {form}")
                    hits_by_key[key].append((f, i))
                    break
    if src_paths:
        print("\n## Source segments containing the term (by %@ key)")
        src_terms = [c["source_term"], *c.get("variants", [])]
        from ..check.segments import segments_of
        for sp in src_paths:
            for key, text in segments_of(Path(sp)).items():
                if any(word_re(s, ignore_case=False).search(text) for s in src_terms):
                    flag = "translated with term" if hits_by_key.get(key) else "CHECK: no current/old form in translation segment"
                    print(f"{sp} [{key}]  {flag}")
    return 0


# ------------------------------------------------------------------ show
def show(project, query: str) -> int:
    t = load(layer_paths(project))
    q = query.lower()
    hits = [c for c in t.concepts.values() if q == c["id"] or q in c["source_term"].lower()
            or q in (c.get("pl") or "").lower() or any(q == v.lower() for v in c.get("variants", []))]
    for c in hits:
        c = {k: v for k, v in c.items() if k not in ("_file",)}
        print(dump(c))
    if not hits:
        print(f"{query}: not found")
    return 0 if hits else 1


# ------------------------------------------------------------------ LaTeX glossary
def _tex(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"\*(.+?)\*", r"\\textit{\1}", s)
    return s.replace("&", r"\&")


def glossary_tex(project, out: Path, statuses=("approved",), author="", cols=3) -> int:
    t = load(layer_paths(project))
    rows = sorted({(c["source_term"], c["pl"]) for c in t.effective.values() if c["status"] in statuses and c.get("pl")},
                  key=lambda r: r[0].lower())
    lines = [rf"%! Author = {author}", rf"%! Date = {datetime.date.today():%d.%m.%Y}",
             r"% Generated by `wgu terms glossary-tex` from the terminology layers — do not edit by hand",
             r"\section*{Słowniczek angielsko-polski}", r"\addcontentsline{toc}{section}{Słowniczek angielsko-polski}",
             r"Zestawienie terminów oryginalnej instrukcji z odpowiednikami przyjętymi w tłumaczeniu.\par\medskip",
             rf"\begin{{multicols}}{{{cols}}}", r"\footnotesize", r"\raggedright\setlength{\parskip}{1.5pt}"]
    lines += [r"\hangindent=1em\textbf{%s} -- %s\par" % (_tex(en), _tex(pl)) for en, pl in rows]
    lines.append(r"\end{multicols}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} entries -> {out}")
    return 0


# ------------------------------------------------------------------ import from a 2-column Markdown table
def import_md(md_path: Path, out: Path, layer_id: str, level: str, prefix: str, source_label: str) -> int:
    """Convert an approved 'English | Polski' table (old style guide §6) into concept records.
    Rows like 'A / B | X / Y' are split when the parts match; otherwise kept whole and flagged for splitting.
    Status: approved, decided_by: user (the table was the owner's binding glossary)."""
    text = md_path.read_text(encoding="utf-8")
    sec = text.split("## 6.", 1)[1] if "## 6." in text else text
    concepts, used = [], set()
    today = datetime.date.today().isoformat()
    for line in sec.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "English" in line:
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not cells[0]:
            continue
        en, pl = cells
        rejected = [{"pl": m, "reason": f"decyzja właściciela ({source_label})"} for m in re.findall(r"\(\*\*nie\*\* „([^”]+)”\)", pl)]
        pl = re.sub(r"\s*\(\*\*nie\*\* „[^”]+”\)", "", pl).strip()
        ens, pls = [x.strip() for x in en.split(" / ")], [x.strip() for x in pl.split(" / ")]
        pairs = list(zip(ens, pls)) if len(ens) == len(pls) and len(ens) > 1 else [(en, pl)]
        for e, p in pairs:
            slug = re.sub(r"[^a-z0-9]+", "-", e.lower()).strip("-")[:40] or "x"
            cid = f"{prefix}.{slug}"
            n = 2
            while cid in used:
                cid, n = f"{prefix}.{slug}-{n}", n + 1
            used.add(cid)
            rec = {"id": cid, "source_term": e, "sense": "(do uzupełnienia — import z tabeli 2-kolumnowej)",
                   "pl": p, "status": "approved", "decided_by": "user",
                   "evidence": [{"source": source_label, "where": "§6 Słowniczek", "form": p, "supports": "usage-in-games", "checked": today}]}
            if rejected:
                rec["rejected"] = rejected
            if len(pairs) == 1 and (" / " in e or " / " in p or "," in e):
                rec["notes"] = "wiersz łączy kilka pojęć — do rozbicia na osobne rekordy"
            concepts.append(rec)
    write_yaml(out, {"layer": {"id": layer_id, "level": level, "title": f"import: {md_path.name}", "sources": [source_label]},
                     "concepts": concepts})
    print(f"{len(concepts)} concepts -> {out}")
    return 0
