"""wgu — wargame_utils command line.

    wgu init [--id ID --short ABBR]          create wgu.yaml in the current directory
    wgu config                               print the resolved project configuration
    wgu pdf analyze|extract|images|render …  PDF tools (fonts/colours, text with markup, images, page renders)
    wgu kb import-legacy DIR [--specs DIR]   convert an old Markdown index (docs/indeks) to the YAML KB
    wgu kb lint [--strict]                   schema + referential integrity + coverage checks
    wgu kb render                            generate Markdown views (kb.views)
    wgu kb show ID…                          print entities (rule, term, table, ambiguity, scenario, aid…)
    wgu kb stats                             counts per collection
    wgu kb export [--out FILE]               single JSON bundle for digitization projects
    wgu aids validate [ID…]                  check decision graphs of aid specs
    wgu aids build ID… [--dpi N]             compile aid .tex (LuaLaTeX ×2), render PNG, report errors
    wgu tex build FILE [--runs N]            compile any .tex with LuaLaTeX and summarise the log
    wgu glossary MD OUT                      LaTeX glossary chapter from the style guide table
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _forward(module: str, argv: list[str]):
    import importlib
    mod = importlib.import_module(f"wgu.{module}")
    sys.argv = [module] + argv
    mod.main()


def cmd_init(a):
    from .config import CONFIG_NAME, INIT_TEMPLATE
    p = Path.cwd() / CONFIG_NAME
    if p.exists():
        raise SystemExit(f"{p} already exists")
    gid = a.id or Path.cwd().name.lower().split("-")[0]
    p.write_text(INIT_TEMPLATE.format(id=gid, short=a.short or gid.upper()), encoding="utf-8", newline="\n")
    print(f"created {p}")


def cmd_config(a):
    from .config import find_project
    pr = find_project()
    print(f"# root: {pr.root}")
    from .kb.store import dump
    print(dump(pr.data))


def cmd_kb(a):
    from .config import find_project
    pr = find_project()
    kb_dir = pr.kb_dir
    if a.action == "import-legacy":
        from .kb import legacy_import
        if (kb_dir / "manifest.yaml").exists() and not a.force:
            raise SystemExit(f"{kb_dir} already has a KB; use --force to overwrite")
        manifest = {"schema": "wgu/kb@1", "game": pr.data["game"],
                    "sources": pr.data["sources"]["rules"], "language": pr.data["language"]}
        idx = Path(a.dir) / "INDEX.md"
        if idx.exists():
            txt = idx.read_text(encoding="utf-8")
            import re
            m = re.search(r"## Protokół interpretacji.*?\n(.*?)(?=\n## |\Z)", txt, re.S)
            if m:
                manifest["interpretation_protocol"] = m.group(1).strip()
            m = re.search(r"## Najważniejsze ostrzeżenia.*?\n(.*?)(?=\n## |\Z)", txt, re.S)
            if m:
                manifest["warnings"] = m.group(1).strip()
            m = re.search(r"## Metadane indeksacji\n(.*?)(?=\n## |\Z)", txt, re.S)
            if m:
                manifest["analysis"] = m.group(1).strip()
        stats = legacy_import.run(Path(a.dir), kb_dir, Path(a.specs) if a.specs else None, manifest)
        print(json.dumps(stats, ensure_ascii=False))
    elif a.action == "lint":
        from .kb import lint
        sys.exit(lint.run(pr, strict=a.strict))
    elif a.action == "render":
        from .kb import render
        print(render.run(pr))
    elif a.action == "show":
        from .kb import show
        show.run(pr, a.ids, fmt=a.format)
    elif a.action == "stats":
        from .kb.store import load_kb
        kb = load_kb(kb_dir)
        for k in ["rules", "terms", "tables", "procedures", "relations", "ambiguities", "changes", "scenarios", "aids"]:
            print(f"{k:12s} {len(kb[k])}")
    elif a.action == "export":
        from .kb import export
        print(export.run(pr, Path(a.out) if a.out else None))


def cmd_aids(a):
    from .config import find_project
    pr = find_project()
    if a.action == "validate":
        from .aids import validate
        sys.exit(validate.run(pr, a.ids))
    elif a.action == "build":
        from .latex import build
        sys.exit(build.build_aids(pr, a.ids, dpi=a.dpi))


def cmd_tex(a):
    from .latex import build
    sys.exit(build.cli_build(Path(a.file), runs=a.runs, outdir=a.outdir, render_dpi=a.render))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "pdf":
        sub = {"analyze": "pdf.analyze", "extract": "pdf.extract_source", "images": "pdf.extract_images",
               "render": "pdf.render_pages"}
        if len(argv) < 2 or argv[1] not in sub:
            raise SystemExit("usage: wgu pdf {analyze|extract|images|render} …  (--help per command)")
        return _forward(sub[argv[1]], argv[2:])
    if argv and argv[0] == "glossary":
        return _forward("latex.glossary", argv[1:])

    ap = argparse.ArgumentParser(prog="wgu", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init"); p.add_argument("--id"); p.add_argument("--short"); p.set_defaults(fn=cmd_init)
    p = sp.add_parser("config"); p.set_defaults(fn=cmd_config)
    p = sp.add_parser("kb"); p.set_defaults(fn=cmd_kb)
    p.add_argument("action", choices=["import-legacy", "lint", "render", "show", "stats", "export"])
    p.add_argument("dir", nargs="?"); p.add_argument("ids", nargs="*")
    p.add_argument("--specs"); p.add_argument("--force", action="store_true"); p.add_argument("--strict", action="store_true")
    p.add_argument("--out"); p.add_argument("--format", choices=["md", "yaml", "json"], default="md")
    p = sp.add_parser("aids"); p.set_defaults(fn=cmd_aids)
    p.add_argument("action", choices=["validate", "build"]); p.add_argument("ids", nargs="*")
    p.add_argument("--dpi", type=int, default=110)
    p = sp.add_parser("tex"); p.set_defaults(fn=cmd_tex)
    p.add_argument("action", choices=["build"]); p.add_argument("file")
    p.add_argument("--runs", type=int, default=2); p.add_argument("--outdir")
    p.add_argument("--render", type=int, default=0, help="render pages to PNG at this DPI (0 = no)")
    a = ap.parse_args(argv)
    if a.cmd == "kb" and a.action == "show" and a.dir:
        a.ids = [a.dir] + a.ids
    a.fn(a)


if __name__ == "__main__":
    main()
