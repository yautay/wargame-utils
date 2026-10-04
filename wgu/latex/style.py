"""Generate a project LaTeX style from a layout specification (`spec` in wgu/layout@1).

    wgu tex style layout.yaml OUT.sty [--name projekt-style]

The generated file loads `wgu-base.sty` (shared macro API, copied next to OUT if missing) and sets only the look:
fonts, page geometry, columns, paragraph, role colours, headings, running header/footer, box styles,
labels. Re-generate after editing the spec; hand edits belong in a separate `<projekt>-extra.sty`.
"""
from __future__ import annotations

import datetime
import shutil
from pathlib import Path

from ..kb.store import read_yaml

TEMPLATES = Path(__file__).resolve().parent.parent.parent / "templates" / "latex"
PAPER = {"letter": "letterpaper", "a4": "a4paper", "legal": "legalpaper", "a5": "a5paper"}
DEFAULT_LABELS = {"uwagahist": "Tło historyczne", "uwagaprojektanta": "Uwaga projektanta", "uwagagra": "Uwaga do gry"}
COLOR_ROLE = {"uwagahist": "wguwhist", "uwagaprojektanta": "wguwproj", "uwagagra": "wguwgra"}


def _font(spec_font: str | None, cmd: str) -> str:
    if not spec_font or spec_font == "?":
        return f"% {cmd}: brak zamiennika — uzupełnij spec.fonts"
    if spec_font == "Source Sans 3":
        files = "SourceSans3}[Extension=.otf,UprightFont=*-Regular,BoldFont=*-Semibold,ItalicFont=*-RegularIt,BoldItalicFont=*-SemiboldIt]"
        return f"{cmd}{{{files}"
    if spec_font.startswith("TeX Gyre "):
        # MiKTeX/TeX Live: fontspec finds TeX Gyre reliably by file name (texgyretermes-regular.otf, …)
        base = "texgyre" + spec_font.split()[-1].lower()
        return (f"{cmd}{{{base}}}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,"
                "ItalicFont=*-italic,BoldItalicFont=*-bolditalic]")
    return f"{cmd}{{{spec_font}}}"


def _shape(h: dict) -> str:
    s = ""
    if h.get("bold"):
        s += r"\bfseries"
    if h.get("italic"):
        s += r"\itshape"
    return s


def _heading(level: str, h: dict | None, color_default: str) -> str:
    if not h:
        return ""
    size = h.get("size_pt", 10)
    font = rf"\naglowekfont\fontsize{{{size}}}{{{round(size * 1.2, 1)}}}\selectfont{_shape(h)}"
    color = "wgnaglowek" if (level == "section" and color_default) else "wgtekst"
    case = r"\MakeUppercase" if h.get("case") == "upper" else (r"\scshape" if h.get("case") == "smallcaps" else "")
    sep = {"section": "10pt plus 2pt}{4pt}", "subsection": "8pt plus 2pt}{3pt}", "subsubsection": "6pt plus 2pt}{2pt}"}[level]
    if h.get("style") == "bar" and level == "section":
        return (rf"\titleformat{{\section}}[block]{{{font}}}{{}}{{0pt}}{{\wgpasek}}" "\n"
                rf"\titleformat{{name=\section,numberless}}[block]{{{font}}}{{}}{{0pt}}{{\wgpaseknn}}" "\n"
                rf"\titlespacing*{{\section}}{{0pt}}{{{sep}")
    label = {"section": r"\thesection", "subsection": r"\thesubsection", "subsubsection": ""}[level]
    after = case if case and case != r"\scshape" else ""
    pre = r"\scshape" if case == r"\scshape" else ""
    return (rf"\titleformat{{\{level}}}[hang]{{{font}{pre}\color{{{color}}}}}{{{label}}}{{{'0.5em' if label else '0pt'}}}{{{after}}}" "\n"
            rf"\titlespacing*{{\{level}}}{{0pt}}{{{sep}")


def generate(layout_path: Path, out: Path, name: str | None = None) -> Path:
    data = read_yaml(layout_path)
    spec = data.get("spec") or {}
    name = name or out.stem
    col = spec.get("colors", {})
    lines = [
        rf"%! {name}.sty — styl projektu wygenerowany przez `wgu tex style` z {layout_path.name} ({datetime.date.today()}).",
        r"%! Nie edytuj ręcznie: zmień `spec` w specyfikacji oprawy i wygeneruj ponownie.",
        r"%! Źródło pomiaru: " + str(data.get("source", {}).get("pdf", "?")),
        r"\NeedsTeXFormat{LaTeX2e}",
        rf"\ProvidesPackage{{{name}}}[{datetime.date.today():%Y/%m/%d} wgu]",
        r"\RequirePackage[svgnames,table]{xcolor}",
        "% --- kolory ról ---",
        rf"\definecolor{{wgtekst}}{{HTML}}{{{col.get('text', '231F20')}}}",
        rf"\definecolor{{wgnaglowek}}{{HTML}}{{{col.get('heading', col.get('text', '231F20'))}}}",
    ]
    if col.get("change"):
        lines.append(rf"\definecolor{{wgzmiana}}{{HTML}}{{{col['change']}}}")
    for role, b in (spec.get("boxes") or {}).items():
        if role in COLOR_ROLE and b.get("fill"):
            lines.append(rf"\definecolor{{{COLOR_ROLE[role]}}}{{HTML}}{{{b['fill']}}}")
    ex = spec.get("example", {})
    if ex.get("fill"):
        lines.append(rf"\definecolor{{wgprzyklad}}{{HTML}}{{{ex['fill']}}}")
    for k, role in [("table_head", "wgtabnagl"), ("table_row", "wgtabwiersz")]:
        if col.get(k):
            lines.append(rf"\definecolor{{{role}}}{{HTML}}{{{col[k]}}}")
    cols = spec.get("columns", 2)
    lines += [rf"\newcommand{{\wgkolumny}}{{{cols}}}", r"\RequirePackage{wgu-base}", "% --- fonty ---"]
    f = spec.get("fonts", {})
    lines.append(_font(f.get("main"), r"\setmainfont"))
    heading_font = f.get("heading") or f.get("main")
    lines.append(_font(heading_font, r"\newfontfamily\wgnaglowekfont").replace(r"\newfontfamily\wgnaglowekfont{", r"\newfontfamily\wgnaglowekfont{", 1))
    lines.append(r"\renewcommand{\naglowekfont}{\wgnaglowekfont}")
    size, lead = f.get("size_pt", 10), f.get("leading_pt", 12)
    lines += [rf"\renewcommand{{\normalsize}}{{\fontsize{{{size}}}{{{lead}}}\selectfont}}",
              rf"\AtBeginDocument{{\fontsize{{{size}}}{{{lead}}}\selectfont}}"]
    m = spec.get("margins_mm", {})
    hdr = spec.get("header", {})
    lines += ["% --- strona ---",
              rf"\RequirePackage[{PAPER.get(spec.get('paper'), 'a4paper') if isinstance(spec.get('paper'), str) else 'paperwidth=' + str(spec['paper'][0]) + 'mm,paperheight=' + str(spec['paper'][1]) + 'mm'},"
              rf"top={m.get('top', 18)}mm,bottom={m.get('bottom', 18)}mm,inner={m.get('inner', 15)}mm,outer={m.get('outer', 15)}mm,"
              r"headheight=14pt,headsep=4mm,footskip=8mm,includehead=false]{geometry}",
              rf"\setlength{{\columnsep}}{{{spec.get('column_sep_mm', 6)}mm}}"]
    p = spec.get("paragraph", {})
    lines += [rf"\setlength{{\parindent}}{{{p.get('indent_pt', 0)}pt}}", rf"\setlength{{\parskip}}{{{p.get('skip_pt', 4)}pt plus 1pt}}"]
    if not p.get("justify", True):
        lines.append(r"\AtBeginDocument{\raggedright}")
    lines.append("% --- nagłówki ---")
    has_heading_color = "heading" in col
    for lvl in ("section", "subsection", "subsubsection"):
        lines.append(_heading(lvl, spec.get(lvl), has_heading_color))
    rn = spec.get("rule_number", {})
    lb = spec.get("labels", {})
    lines += ["% --- numery reguł i etykiety ---",
              rf"\renewcommand{{\wgregulastyl}}{{{_shape(rn) or r'\relax'}}}",
              rf"\renewcommand{{\wgetykietastyl}}{{{_shape(lb) or r'\relax'}}}"]
    lines.append("% --- ramki uwag autora i przykład ---")
    upper_any = any((b.get("label_case") == "upper") for b in (spec.get("boxes") or {}).values())
    if upper_any:
        lines.append(r"\renewcommand{\wgetykietacase}[1]{\MakeUppercase{#1}}")
    lines.append(r"\renewcommand{\wgkomentarzstyl}{\itshape}")
    for role, b in (spec.get("boxes") or {}).items():
        if role in COLOR_ROLE:
            shape = r",fontupper=\itshape" if b.get("italic", True) else r",fontupper=\upshape"
            lines.append(rf"\tcbset{{wg/{role}/.style={{wg/uwaga,colback={COLOR_ROLE[role]},left=4pt,right=4pt,top=2pt,bottom=2pt"
                         + shape + "}}")
        if b.get("label_pl"):
            macro = {"uwagahist": "wgnazwahist", "uwagaprojektanta": "wgnazwaproj", "uwagagra": "wgnazwagra"}.get(role)
            if macro:
                lines.append(rf"\renewcommand{{\{macro}}}{{{b['label_pl']}}}")
    if ex.get("style") == "text":
        lines.append(r"\wgprzykladramkafalse")
    lines.append("% --- paginy ---")
    lines += [r"\pagestyle{fancy}", r"\fancyhf{}"]
    tshape = (r"\bfseries" if hdr.get("title_bold") else "") + (r"\itshape" if hdr.get("title_italic") else "")
    title = rf"{{\fontsize{{{hdr.get('size_pt', 9)}}}{{11}}\selectfont{tshape}\seriatytul}}\ifdefempty{{\wydanie}}{{}}{{{{\footnotesize\ --~\wydanie}}}}"
    if hdr.get("style") == "bar":
        lines += [r"\renewcommand{\headrulewidth}{0pt}",
                  rf"\fancyhead[LE,RO]{{\colorbox{{wgnaglowek}}{{\color{{white}}{title}}}}}",
                  r"\fancyfoot[LE,RO]{\colorbox{wgnaglowek}{\color{white}\thepage}}"]
    else:
        lines += [rf"\renewcommand{{\headrulewidth}}{{{'0.4pt' if hdr.get('style') == 'rule' else '0pt'}}}",
                  rf"\fancyhead[C]{{{title}}}",
                  r"\fancyhead[LE,RO]{\thepage}" if hdr.get("page_number", "outer") == "outer" else r"\fancyfoot[C]{\thepage}"]
    ft = spec.get("footer", {})
    fshape = r"\itshape" if ft.get("italic") else ""
    pos = {"center": "C", "left": "LE,RO", "right": "RE,LO"}.get(ft.get("position", "center"), "C")
    lines.append(rf"\fancyfoot[{pos}]{{\fontsize{{{ft.get('size_pt', 8)}}}{{10}}\selectfont{fshape}\stopkatekst}}")
    lines.append(r"\fancypagestyle{plain}{}")
    lines += [r"\renewcommand{\stopkatekst}{" + (ft.get("text_pl") or "tłumaczenie nieoficjalne") + "}"]
    if hdr.get("title_pl"):
        lines.append(r"\renewcommand{\seriatytul}{" + hdr["title_pl"] + "}")
    lines.append(r"\endinput")
    out.write_text("\n".join(l for l in lines if l is not None) + "\n", encoding="utf-8", newline="\n")
    base = out.parent / "wgu-base.sty"
    if not base.exists() or base.read_text(encoding="utf-8") != (TEMPLATES / "wgu-base.sty").read_text(encoding="utf-8"):
        shutil.copy(TEMPLATES / "wgu-base.sty", base)
    return out
