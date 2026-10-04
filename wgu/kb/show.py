"""Print KB entities by id — the cheap lookup used by /wgu:regula and by agents instead of reading whole files.

Rules also print their outgoing/incoming relations and the ambiguities and scenarios that cite them,
so an answer never misses an overriding exception.
"""
from __future__ import annotations

import json

from . import render
from .store import dump, load_kb


def run(project, ids: list[str], fmt="md"):
    kb = load_kb(project.kb_dir)
    index = {}
    for r in kb["rules"]:
        index[r["id"]] = ("rule", r)
    for c, f in [("tables", render.table_md), ("procedures", render.proc_md), ("ambiguities", render.amb_md),
                 ("scenarios", render.scen_md), ("aids", render.aid_md)]:
        for e in kb[c]:
            index[e["id"]] = (c, e)
            for s in e.get("subprocedures", []) or []:
                index[s["id"]] = (c, s)
    fmts = {"rule": render.rule_md, "tables": render.table_md, "procedures": render.proc_md,
            "ambiguities": render.amb_md, "scenarios": render.scen_md, "aids": render.aid_md}
    for q in ids:
        hits = [k for k in index if k == q] or [k for k in index if k.startswith(q + ".")]
        if not hits:
            terms = [t for t in kb["terms"] if q.lower() in (t.get("en", "") + " " + t.get("pl", "")).lower()]
            if terms:
                for t in terms:
                    print(dump(t) if fmt == "yaml" else render.term_row(t))
                continue
            print(f"{q}: not found")
            continue
        for h in hits:
            kind, e = index[h]
            e = {k: v for k, v in e.items() if k != "_file"}
            if fmt == "json":
                print(json.dumps(e, ensure_ascii=False, indent=1))
            elif fmt == "yaml":
                print(dump(e))
            else:
                print(fmts[kind](e))
            if kind == "rule" and fmt == "md":
                rel_out = [r for r in kb["relations"] if r["from"] == h]
                rel_in = [r for r in kb["relations"] if r["to"] == h]
                for r in rel_in:
                    print(f"  ⟵ {r['from']} {r['type']} this: {r.get('note') or r.get('when', '')}")
                for r in rel_out:
                    print(f"  ⟶ this {r['type']} {r['to']}: {r.get('note') or r.get('when', '')}")
                amb = [a["id"] for a in kb["ambiguities"] if h in (a.get("refs") or [])]
                sc = [s["id"] for s in kb["scenarios"] if h in (s.get("refs") or [])]
                if amb:
                    print(f"  ambiguities: {', '.join(amb)}")
                if sc:
                    print(f"  scenarios: {', '.join(sc)}")
            print()
