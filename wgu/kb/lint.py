"""KB lint: JSON-schema validation, unique IDs, dangling references, relation endpoints, aid graphs.

Errors break the KB contract (exit 1). Warnings are quality issues (exit 1 only with --strict).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from .store import COLLECTIONS, all_ids, known, load_kb, read_yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "kb.schema.json"
FILE_DEFS = {"terms": "termsFile", "tables": "tablesFile", "procedures": "proceduresFile", "relations": "relationsFile",
             "ambiguities": "ambiguitiesFile", "changes": "changesFile", "scenarios": "scenariosFile"}


def validator(defname: str) -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    sub = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{defname}"}
    return Draft202012Validator(sub)


def _schema_errors(kb_dir: Path):
    errs = []
    checks = [(kb_dir / "manifest.yaml", "manifest")]
    checks += [(f, "rulesFile") for f in sorted((kb_dir / "rules").glob("*.yaml"))]
    checks += [(kb_dir / f"{c}.yaml", FILE_DEFS[c]) for c in COLLECTIONS if (kb_dir / f"{c}.yaml").exists()]
    checks += [(f, "aid") for f in sorted((kb_dir / "aids").glob("*.yaml"))]
    for f, d in checks:
        data = read_yaml(f)
        if data is None:
            errs.append(f"{f.name}: missing or empty")
            continue
        for e in validator(d).iter_errors(data):
            loc = "/".join(map(str, e.absolute_path))
            errs.append(f"{f.relative_to(kb_dir)}:{loc}: {e.message[:200]}")
    return errs


def check(kb_dir: Path) -> tuple[list[str], list[str]]:
    errors = _schema_errors(kb_dir)
    warnings = []
    kb = load_kb(kb_dir)
    ids = all_ids(kb)

    every = [r["id"] for r in kb["rules"]] + [e["id"] for c in ["tables", "procedures", "ambiguities", "changes", "scenarios", "aids"] for e in kb[c]]
    for i, n in Counter(every).items():
        if n > 1:
            errors.append(f"duplicate id {i} ({n}×)")

    def dangling(owner, refs):
        for r in refs or []:
            if not known(r, ids):
                warnings.append(f"{owner}: reference to unknown id {r}")

    for r in kb["rules"]:
        dangling(r["id"], r.get("refs"))
    for c in ["tables", "procedures", "ambiguities", "changes", "scenarios"]:
        for e in kb[c]:
            dangling(e["id"], e.get("refs"))
    for t in kb["terms"]:
        dangling(f"term '{t.get('en')}'", t.get("refs"))
    for rel in kb["relations"]:
        for end in ("from", "to"):
            if not known(rel[end], ids):
                errors.append(f"relation {rel['from']}→{rel['to']}: unknown {end} id {rel[end]}")
    imported = sum(1 for r in kb["relations"] if r.get("status") == "imported")
    if imported:
        warnings.append(f"{imported} relations have status 'imported' (auto-parsed) — analyst should verify them")

    for a in kb["ambiguities"]:
        if a.get("status", "open") == "open" and not a.get("strength") and a.get("scope") != "translation":
            warnings.append(f"{a['id']}: open ambiguity without recommendation strength")

    for ch in kb["chapters"]:
        if not ch.get("rules"):
            warnings.append(f"{ch['_file']}: chapter without rules")

    from ..aids.validate import check_aid
    for a in kb["aids"]:
        e, w = check_aid(a, ids)
        # aid graph defects do not break the KB contract; `wgu aids validate` treats them as errors
        warnings += [f"{a['id']}: graph error: {x}" for x in e]
        warnings += [f"{a['id']}: {x}" for x in w]
    return errors, warnings


def run(project, strict=False) -> int:
    errors, warnings = check(project.kb_dir)
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    print(f"\n{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors or (strict and warnings) else 0
