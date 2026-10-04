"""LuaLaTeX build loop as one command: compile N×, summarise the log, render PNG previews, clean aux files.

Replaces the compile → grep log → render → clean sequence that agents used to run turn by turn.
The model only has to look at the PNGs and fix the layout.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

AUX = (".aux", ".log", ".out", ".toc", ".synctex.gz", ".fls", ".fdb_latexmk")


def find_lualatex(configured: str = "") -> str:
    if configured:
        return configured
    exe = shutil.which("lualatex")
    if exe:
        return exe
    cand = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/MiKTeX/miktex/bin/x64/lualatex.exe"
    if cand.exists():
        return str(cand)
    raise SystemExit("lualatex not found — install MiKTeX/TeX Live or set tools.lualatex in wgu.yaml")


def summarise_log(log: str) -> dict:
    errors = []
    lines = log.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("!"):
            ctx = " | ".join(x.strip() for x in lines[i + 1:i + 3] if x.strip())
            errors.append(f"{l} {ctx}"[:300])
    return {
        "errors": errors,
        "missing": sorted(set(re.findall(r"File `([^']+)' not found", log))),
        "overfull": len(re.findall(r"^Overfull \\hbox", log, re.M)),
        "underfull": len(re.findall(r"^Underfull \\[hv]box", log, re.M)),
        "undefined_refs": len(re.findall(r"Reference `[^']+' on page \d+ undefined", log)),
        "rerun": "Rerun to get" in log,
        "pages": (m.group(1) if (m := re.search(r"Output written on .*?\((\d+) page", log)) else "?"),
    }


def render_png(pdf: Path, outdir: Path, dpi: int) -> list[Path]:
    import pymupdf
    outdir.mkdir(parents=True, exist_ok=True)
    out = []
    with pymupdf.open(pdf) as d:
        for i, p in enumerate(d):
            f = outdir / f"{pdf.stem}_{i + 1:02d}.png"
            p.get_pixmap(dpi=dpi).save(f)
            out.append(f)
    return out


def compile_tex(tex: Path, cwd: Path, outdir: Path, runs=2, lualatex="", clean=True) -> tuple[Path, dict]:
    exe = find_lualatex(lualatex)
    outdir.mkdir(parents=True, exist_ok=True)
    rel = os.path.relpath(tex, cwd)
    info = {}
    for _ in range(max(1, runs)):
        subprocess.run([exe, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={outdir}", rel],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = (outdir / (tex.stem + ".log"))
        info = summarise_log(log.read_text(encoding="utf-8", errors="replace") if log.exists() else "")
        if info["errors"]:
            break
    pdf = outdir / (tex.stem + ".pdf")
    if clean and not info["errors"]:
        for ext in AUX:
            f = outdir / (tex.stem + ext)
            if f.exists():
                f.unlink()
    return pdf, info


def _report(name, pdf, info, pngs):
    ok = not info["errors"] and pdf.exists()
    print(f"[{'OK ' if ok else 'ERR'}] {name}: {pdf if pdf.exists() else '(no pdf)'}  pages={info.get('pages')} "
          f"overfull={info.get('overfull')} underfull={info.get('underfull')} undefined_refs={info.get('undefined_refs')}")
    for e in info.get("errors", []):
        print("   ", e)
    if info.get("missing"):
        print("    missing files:", ", ".join(info["missing"]), "(MiKTeX: miktex packages install <name>)")
    for p in pngs:
        print("    png:", p)
    return ok


def cli_build(tex: Path, runs=2, outdir=None, render_dpi=0) -> int:
    tex = tex.resolve()
    try:
        from ..config import find_project
        pr = find_project(tex.parent)
        cwd, exe = pr.root, pr.data["tools"]["lualatex"]
    except SystemExit:
        cwd, exe = tex.parent, ""
    out = Path(outdir).resolve() if outdir else tex.parent
    pdf, info = compile_tex(tex, cwd, out, runs, exe)
    pngs = render_png(pdf, out / "_png", render_dpi) if render_dpi and pdf.exists() and not info["errors"] else []
    return 0 if _report(tex.name, pdf, info, pngs) else 1


def build_aids(project, ids: list[str], dpi=110) -> int:
    texdir, pdfdir = project.path("aids.tex"), project.path("aids.pdf")
    if not ids:
        raise SystemExit("give aid ids, e.g. wgu aids build P01 P09")
    ok = True
    for aid in ids:
        files = sorted(texdir.glob(f"{aid}-*.tex")) or sorted(texdir.glob(f"{aid}*.tex"))
        if not files:
            print(f"[ERR] {aid}: no {texdir}/{aid}-*.tex")
            ok = False
            continue
        pdf, info = compile_tex(files[0], project.root, pdfdir, 2, project.data["tools"]["lualatex"])
        pngs = render_png(pdf, pdfdir / "_png", dpi) if pdf.exists() and not info["errors"] else []
        ok &= _report(aid, pdf, info, pngs)
    return 0 if ok else 1
