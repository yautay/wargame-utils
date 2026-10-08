"""Project and workspace configuration.

Every skill and CLI command resolves paths through this file, so nothing game-specific is hard-coded
in the tool. `find_project()` walks up from the current directory like git does. A workspace may contain
many game directories, each with its own `wgu.yaml`.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_NAME = "wgu.yaml"
WORKSPACE_NAME = "wgu-workspace.yaml"

DEFAULTS = {
    "schema": "wgu/project@1",
    "game": {"id": "", "title": "", "short": "", "rules_version": "", "publisher": "", "rule_id_prefix": "R-"},
    "language": {"source": "en", "target": "pl"},
    "sources": {"rules": [], "errata": [], "charts": [], "scenarios": []},
    "pdf": {"accent_color": "", "heading_font": "", "columns": 2},
    "translation": {"main": "", "dir": "tex", "style": "", "glossary": "docs/przewodnik_stylu.md", "images": "png"},
    "kb": {"dir": "kb", "views": "kb/_views"},
    "aids": {"specs": "kb/aids", "plan": "kb/aids/PLAN.md", "tex": "pomoce", "pdf": "pomoce/pdf",
             "style": "", "tikz": "pomoce/pomoce-tikz.sty"},
    "digital": {"dir": "kb/digital", "export": "build/wgu-kb.json"},
    "terminology": {"layers": ["common"], "game": "kb/terminology.yaml"},
    "translation_work": {"dir": "translation"},
    "tools": {"lualatex": ""},
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


@dataclass
class Project:
    root: Path
    data: dict
    workspace_root: Path | None = None
    workspace_data: dict | None = None

    def path(self, *keys: str) -> Path:
        """Resolve a config value (dotted keys) to an absolute path inside the project."""
        v = self.get(*keys)
        return (self.root / v) if v else self.root

    def get(self, *keys: str):
        v = self.data
        for k in keys:
            for part in k.split("."):
                v = v[part]
        return v

    @property
    def kb_dir(self) -> Path:
        return self.path("kb.dir")

    def source(self, role: str = "current") -> Path | None:
        for s in self.data["sources"]["rules"]:
            if s.get("role") == role:
                return self.root / s["path"]
        return None

    @property
    def terminology_root(self) -> Path | None:
        configured = self.data.get("terminology", {}).get("root")
        if configured:
            return (self.root / configured).resolve()
        if self.workspace_root and self.workspace_data:
            configured = self.workspace_data.get("terminology_root")
            if configured:
                return (self.workspace_root / configured).resolve()
        return None


@dataclass
class Workspace:
    root: Path
    data: dict

    @property
    def project_paths(self) -> list[Path]:
        return [(self.root / p).resolve() for p in self.data.get("projects", [])]


def find_workspace(start: Path | None = None, required: bool = False) -> Workspace | None:
    p = (start or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        f = d / WORKSPACE_NAME
        if f.exists():
            raw = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            return Workspace(d, raw)
    if required:
        raise SystemExit(f"{WORKSPACE_NAME} not found in {p} or its parents")
    return None


def find_project(start: Path | None = None) -> Project:
    p = (start or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        f = d / CONFIG_NAME
        if f.exists():
            raw = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            workspace = find_workspace(d)
            return Project(d, _merge(DEFAULTS, raw), workspace.root if workspace else None,
                           workspace.data if workspace else None)
    raise SystemExit(f"{CONFIG_NAME} not found in {p} or its parents — run `wgu init` in the game directory.")


def workspace_projects(workspace: Workspace) -> list[Project]:
    projects: list[Project] = []
    seen: dict[str, Path] = {}
    for root in workspace.project_paths:
        project = find_project(root)
        if project.root != root:
            raise SystemExit(f"workspace project has no {CONFIG_NAME}: {root}")
        gid = project.data["game"]["id"]
        if not gid:
            raise SystemExit(f"workspace project has an empty game.id: {root}")
        if gid in seen:
            raise SystemExit(f"duplicate game.id {gid!r}: {seen[gid]} and {root}")
        seen[gid] = root
        projects.append(project)
    return projects


def resolve_project(selector: str | None, start: Path | None = None) -> Project:
    base = (start or Path.cwd()).resolve()
    if selector is None:
        return find_project(base)
    candidate = Path(selector)
    if not candidate.is_absolute():
        candidate = base / candidate
    if candidate.exists():
        return find_project(candidate)
    workspace = find_workspace(base, required=True)
    for project in workspace_projects(workspace):
        if selector in (project.data["game"]["id"], project.root.name):
            return project
    raise SystemExit(f"unknown workspace project {selector!r}")


INIT_TEMPLATE = """\
# wargame_utils project file — read by every /wgu:* skill and the `wgu` CLI.
schema: wgu/project@1
game:
  id: {id}                 # short machine id (lowercase)
  title: ""                # full title of the rules document
  short: {short}           # abbreviation used in headings
  rules_version: ""
  publisher: ""
  rule_id_prefix: "R-"     # rule ids: R-<section>.<n>; title-specific: R-<TITLE>-<n>; optional: R-OPT-<x>.<n>
language:
  source: en
  target: pl
sources:
  rules:                   # role: current | previous | other
    - {{path: docs/rules.pdf, version: "", role: current}}
  errata: []               # errata / FAQ / designer clarifications (pdf, md, url)
  charts: []               # charts & tables sheets — needed for digitization
  scenarios: []
pdf:
  accent_color: ""         # colour of "changed in this version" text, hex without # (wgu pdf analyze)
  heading_font: ""         # fragment of the heading font name (wgu pdf analyze)
  columns: 2
translation:
  main: ""                 # main .tex file of the translation (empty = no translation)
  dir: tex
  style: ""                # project .sty (fonts, colours)
  glossary: docs/przewodnik_stylu.md
  images: png
kb:
  dir: kb                  # canonical YAML knowledge base
  views: kb/_views         # generated Markdown (wgu kb render)
aids:
  specs: kb/aids           # aid specifications (YAML)
  plan: kb/aids/PLAN.md
  tex: pomoce
  pdf: pomoce/pdf
  style: ""                # .sty with fonts/colours used by aids (default: translation.style)
  tikz: pomoce/pomoce-tikz.sty
digital:
  dir: kb/digital
  export: build/wgu-kb.json
terminology:
  layers: [common]         # shared layers from <wargame_utils>/terminology/: common, era/<x>, series/<x>
  game: kb/terminology.yaml  # this game + edition (most specific layer)
translation_work:
  dir: translation         # chunks, per-chunk term tables, agent proposals, decision log, verification reports
tools:
  lualatex: ""             # empty = find on PATH / MiKTeX default location
"""
