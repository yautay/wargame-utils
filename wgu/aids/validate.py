"""Decision-graph checks for aid specifications (kb/aids/PNN-*.yaml).

A spec that passes can be drawn without interpreting rules — and is a ready skeleton of an engine procedure:
start → (actions | decisions with all exits) → ends, every node traceable to rule IDs.
"""
from __future__ import annotations

import re
from collections import defaultdict

from ..kb.store import all_ids, known, load_kb

KINDS = [("start", r"^start"), ("end", r"^(koniec|end|wynik)"), ("decision", r"^(decyzja|decision|romb)"),
         ("note", r"^(notatka|note|uwaga)"), ("action", r".")]


def kind(shape: str) -> str:
    s = shape.strip().lower()
    for k, pat in KINDS:
        if re.match(pat, s):
            return k
    return "action"


def _base(node_id: str) -> str:
    return node_id.split("(")[0].strip()


def check_aid(aid: dict, ids: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    nodes = aid.get("nodes") or []
    edges = aid.get("edges") or []
    if not nodes:
        return [], ["no node table (card/infographic without a graph) — graph checks skipped"]
    by_id = {n["id"]: n for n in nodes}
    if len(by_id) != len(nodes):
        errors.append("duplicate node ids")
    out, inc = defaultdict(list), defaultdict(list)
    for e in edges:
        f, t = _base(e["from"]), _base(e["to"])
        for end, v in (("from", f), ("to", t)):
            if v not in by_id:
                errors.append(f"edge {e['from']}→{e['to']}: unknown {end} node '{v}'")
        out[f].append(e)
        inc[t].append(e)
    if not edges:
        return errors, warnings + ["no edges — graph checks skipped"]

    starts = [n["id"] for n in nodes if kind(n["shape"]) == "start"]
    if not starts:
        warnings.append("no start node")
    for n in nodes:
        k, nid = kind(n["shape"]), n["id"]
        if not out[nid] and not inc[nid] and k not in ("start", "note"):
            warnings.append(f"{nid} is not connected (attached frame?) - graph checks skipped for it")
            continue
        if k == "decision":
            labels = [e.get("label", "") for e in out[nid]]
            if len(out[nid]) < 2:
                errors.append(f"decision {nid} has {len(out[nid])} exit(s) — needs ≥ 2")
            elif len(set(labels)) < len(labels) or any(not l for l in labels):
                warnings.append(f"decision {nid}: exits should have distinct labels {labels}")
        elif k == "end":
            if out[nid]:
                warnings.append(f"end node {nid} has outgoing edges")
        elif k not in ("note",) and not out[nid]:
            warnings.append(f"{k} {nid} has no exit (dead end that is not an end node)")
        if k != "start" and not inc[nid] and k != "note":
            warnings.append(f"{k} {nid} is unreachable (no incoming edge)")
        if k in ("decision", "action", "end") and not n.get("refs"):
            warnings.append(f"{nid}: no rule reference")
        for r in n.get("refs") or []:
            if not known(r, ids) and not re.match(r"^P\d+$", r):
                warnings.append(f"{nid}: unknown rule id {r}")
    # reachability from starts
    seen, stack = set(), list(starts)
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack += [_base(e["to"]) for e in out[x]]
    if starts:
        unreached = [n["id"] for n in nodes if n["id"] not in seen and kind(n["shape"]) != "note" and n["id"] not in inc]
        for n in nodes:
            if n["id"] not in seen and kind(n["shape"]) not in ("note", "start") and inc[n["id"]]:
                warnings.append(f"{n['id']} not reachable from start")
    return errors, warnings


def run(project, only: list[str]) -> int:
    kb = load_kb(project.kb_dir)
    ids = all_ids(kb)
    total_e = 0
    for a in kb["aids"]:
        if only and a["id"] not in only:
            continue
        e, w = check_aid(a, ids)
        total_e += len(e)
        status = "OK " if not e and not w else ("ERR" if e else "warn")
        print(f"[{status}] {a['id']} {a.get('title', '')}  nodes={len(a.get('nodes') or [])} edges={len(a.get('edges') or [])}")
        for x in e:
            print("   ERROR  ", x)
        for x in w:
            print("   warning", x)
    return 1 if total_e else 0
