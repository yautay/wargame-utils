"""`wgu init --setup`: prepare a game directory for work with the tool.

Mechanical part of `/wgu:nowy-projekt`: sort the sources into docs/ and png/, create wgu.yaml with measured
PDF values, .gitignore, .claude/settings.json (enables the plugin) and a git repository. Never overwrites.
"""
from __future__ import annotations

import collections
import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import CONFIG_NAME, INIT_TEMPLATE

IMAGE_EXT = {".png", ".jpg", ".jpeg"}
GITIGNORE = ["build/", "kb/_views/", "pomoce/pdf/_png/", "__pycache__/", "*.aux", "*.log", "*.out", "*.toc",
             "*.fls", "*.fdb_latexmk", "*.synctex.gz", "_t_*"]
PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def measure_pdf(pdf: Path, max_pages: int = 12) -> dict:
    """Heuristic: heading font = most frequent font other than the body font; accent = most frequent saturated colour."""
    import pymupdf
    fonts, colors = collections.Counter(), collections.Counter()
    doc = pymupdf.open(pdf)
    for page in list(doc)[:max_pages]:
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    n = len(s["text"].strip())
                    if not n:
                        continue
                    fonts[s["font"]] += n
                    colors[s["color"]] += n
    body = fonts.most_common(1)[0][0] if fonts else ""
    def family(f):   # TimesNewRomanPSMT / TimesNewRomanPS-ItalicMT / TimesNewRomanPS-BoldMT -> one family
        f = f.split("+")[-1].split("-")[0]
        return f[:-2] if f.endswith("MT") else f
    others = collections.Counter({f: c for f, c in fonts.items() if family(f) != family(body)})
    heading = others.most_common(1)[0][0].rstrip("-") if others else ""
    accent = ""
    for col, _ in colors.most_common():
        r, g, b = (col >> 16) & 255, (col >> 8) & 255, col & 255
        if max(r, g, b) - min(r, g, b) > 80:     # saturated, not black/grey
            accent = f"{col:06X}"
            break
    return {"pages": len(doc), "body_font": body, "heading_font": heading, "accent_color": accent}


def find_claude() -> str | None:
    """`claude` on PATH, else the newest copy bundled with the Claude desktop app (Windows).

    The MSIX build of the app virtualizes %APPDATA%: a plain shell sees the copy only under
    %LOCALAPPDATA%/Packages/Claude_*/LocalCache/Roaming, so both locations are searched."""
    exe = shutil.which("claude")
    if exe:
        return exe
    roots = []
    if os.environ.get("APPDATA"):
        roots.append(Path(os.environ["APPDATA"]) / "Claude" / "claude-code")
    if os.environ.get("LOCALAPPDATA"):
        roots += sorted((Path(os.environ["LOCALAPPDATA"]) / "Packages").glob("Claude_*/LocalCache/Roaming/Claude/claude-code"))
    found = [p for r in roots for p in r.glob("*/*/claude.exe")]
    if found:
        return str(max(found, key=lambda p: p.stat().st_mtime))
    return None


def install_plugin(root: Path, plugin_path: Path, log: list[str]) -> None:
    """Register the marketplace and install `wgu` in project scope (settings.json alone does not load it)."""
    manual = (f"zainstaluj plugin ręcznie w katalogu gry: `claude plugin marketplace add {plugin_path.as_posix()} "
              "--scope project` i `claude plugin install wgu@wargame-utils --scope project`")
    exe = find_claude()
    if not exe:
        log.append(f"nie znaleziono `claude` — {manual}")
        return
    for args in (["marketplace", "add", plugin_path.as_posix(), "--scope", "project"],
                 ["install", "wgu@wargame-utils", "--scope", "project"]):
        r = subprocess.run([exe, "plugin", *args], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            log.append(f"`claude plugin {args[0]}` nie powiodło się ({(r.stderr or r.stdout).strip()[:200]}) — {manual}")
            return
    log.append("zainstalowano plugin wgu@wargame-utils (zakres: projekt) — uruchom NOWĄ sesję Claude Code w tym "
               "katalogu; po zmianach w narzędziu: `claude plugin update wgu@wargame-utils`")


def _move(src: Path, dst_dir: Path, log: list[str]) -> Path:
    dst_dir.mkdir(exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        log.append(f"pominięto (już istnieje): {dst}")
        return dst
    shutil.move(str(src), str(dst))
    log.append(f"przeniesiono {src.name} → {dst_dir.name}/")
    return dst


def setup(root: Path, gid: str | None, short: str | None, pdf: Path | None, images: list[Path],
          git: bool = True, plugin_path: Path = PLUGIN_ROOT, plugin: bool = True) -> list[str]:
    log: list[str] = []
    if (root / CONFIG_NAME).exists():
        raise SystemExit(f"{root / CONFIG_NAME} już istnieje — nic nie zmieniono")
    if pdf is None:
        found = sorted(root.glob("*.pdf")) or sorted((root / "docs").glob("*.pdf"))
        if len(found) != 1:
            raise SystemExit(f"podaj --pdf (znaleziono PDF-ów: {len(found)})")
        pdf = found[0]
    if not images:
        images = sorted(p for p in root.iterdir() if p.suffix.lower() in IMAGE_EXT)
    pdf = _move(pdf, root / "docs", log) if pdf.parent != root / "docs" else pdf
    for im in images:
        if im.parent != root / "png":
            _move(im, root / "png", log)
    for d in ("kb", "translation"):
        (root / d).mkdir(exist_ok=True)

    gid = gid or root.name.lower().split("-")[0]
    text = INIT_TEMPLATE.format(id=gid, short=short or gid.upper())
    m = measure_pdf(pdf)
    rel = f"docs/{pdf.name}"
    text = text.replace("{path: docs/rules.pdf, version: \"\", role: current}", f"{{path: {rel}, version: \"\", role: current}}")
    text = text.replace('accent_color: ""', f'accent_color: "{m["accent_color"]}"')
    text = text.replace('heading_font: ""', f'heading_font: "{m["heading_font"]}"')
    (root / CONFIG_NAME).write_text(text, encoding="utf-8", newline="\n")
    log.append(f"utworzono {CONFIG_NAME} (PDF: {rel}; zmierzone: {json.dumps(m, ensure_ascii=False)}) — "
               "sprawdź kolor zmian i font nagłówków, uzupełnij tytuł, wydanie, wydawcę")

    gi = root / ".gitignore"
    have = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    add = [x for x in GITIGNORE if x not in have]
    if add:
        gi.write_text("\n".join(have + add) + "\n", encoding="utf-8", newline="\n")
        log.append(f".gitignore: dodano {len(add)} wpisów")

    st = root / ".claude" / "settings.json"
    if st.exists():
        log.append("pominięto .claude/settings.json (już istnieje) — włącz plugin ręcznie, jeśli go brak")
    else:
        st.parent.mkdir(exist_ok=True)
        cfg = {"extraKnownMarketplaces": {"wargame-utils": {"source": {"source": "directory",
                                                                       "path": plugin_path.as_posix()}}},
               "enabledPlugins": {"wgu@wargame-utils": True}}
        st.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
        log.append(f"utworzono .claude/settings.json (plugin z {plugin_path.as_posix()})")

    if plugin:
        install_plugin(root, plugin_path, log)

    if git and not (root / ".git").exists():
        r = subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, capture_output=True, text=True)
        log.append("git init (gałąź main)" if r.returncode == 0 else f"git init nie powiodło się: {r.stderr.strip()}")
    return log
