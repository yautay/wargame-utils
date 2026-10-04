"""Single JSON bundle for digitization projects (contract: schemas/kb.schema.json, format wgu/kb-bundle@1).

The bundle is a derived artifact: regenerate it, never edit it. A digitization repo pins a bundle
(commit hash of the game repo + `generated` timestamp) and reads rules, tables, decision graphs and
scenarios from it instead of from the rulebook.
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

from .lint import check
from .store import load_kb, read_yaml


def _git_rev(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def run(project, out: Path | None = None) -> str:
    errors, warnings = check(project.kb_dir)
    if errors:
        raise SystemExit(f"KB has {len(errors)} lint errors — run `wgu kb lint` first")
    kb = load_kb(project.kb_dir)
    strip = lambda e: {k: v for k, v in e.items() if k != "_file"}
    bundle = {
        "format": "wgu/kb-bundle@1",
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "source_rev": _git_rev(project.root),
        "lint_warnings": len(warnings),
        "manifest": kb["manifest"],
        "chapters": [{"chapter": c["chapter"], "rule_ids": [r["id"] for r in c.get("rules", [])]} for c in kb["chapters"]],
        "rules": kb["rules"],
        **{c: kb[c] for c in ["terms", "tables", "procedures", "relations", "ambiguities", "changes", "scenarios"]},
        "aids": [strip(a) for a in kb["aids"]],
        "digital": {f.stem: read_yaml(f) for f in sorted(project.path("digital.dir").glob("*.yaml"))}
        if project.path("digital.dir").exists() else {},
    }
    out = out or project.path("digital.export")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{out}  ({len(kb['rules'])} rules, {len(kb['aids'])} aids, {len(warnings)} lint warnings)"
