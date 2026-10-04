from pathlib import Path

from wgu.kb.store import write_yaml
from wgu.latex.style import generate
from wgu.pdf.layout import substitute


def test_font_substitutes():
    assert substitute("TimesNewRomanPSMT")["substitute"] == "TeX Gyre Termes"
    assert substitute("MyriadPro-Bold")["substitute"] == "Source Sans 3"
    assert substitute("WeirdFont")["substitute"] == "?"


def test_style_generation(tmp_path: Path):
    spec = {
        "paper": "letter", "margins_mm": {"top": 17, "bottom": 17, "inner": 16, "outer": 15}, "columns": 2, "column_sep_mm": 5.4,
        "fonts": {"main": "TeX Gyre Termes", "size_pt": 10, "leading_pt": 12},
        "paragraph": {"indent_pt": 0, "skip_pt": 4, "justify": True},
        "colors": {"text": "231F20", "heading": "3953A4"},
        "rule_number": {"bold": True}, "labels": {"bold": True, "italic": True},
        "boxes": {"uwagahist": {"fill": "EFE5D5", "italic": True, "label_case": "upper", "label_pl": "Tło historyczne"}},
        "example": {"style": "text"},
        "header": {"style": "rule", "title_pl": "SPQR", "title_bold": True, "title_italic": True, "size_pt": 9},
        "footer": {"text_pl": "tłumaczenie nieoficjalne", "italic": True, "size_pt": 8, "position": "center"},
        "section": {"style": "text", "size_pt": 17, "bold": True, "case": "upper", "color": "3953A4"},
    }
    lay = tmp_path / "layout.yaml"
    write_yaml(lay, {"schema": "wgu/layout@1", "spec": spec})
    out = generate(lay, tmp_path / "gra-style.sty")
    s = out.read_text(encoding="utf-8")
    assert r"\RequirePackage{wgu-base}" in s and (tmp_path / "wgu-base.sty").exists()
    assert "letterpaper" in s and r"\definecolor{wgnaglowek}{HTML}{3953A4}" in s
    assert r"\setmainfont{texgyretermes}" in s and r"\wgprzykladramkafalse" in s
    assert r"\renewcommand{\wgetykietastyl}{\bfseries\itshape}" in s
    assert r"\definecolor{wguwhist}{HTML}{EFE5D5}" in s and r"\renewcommand{\seriatytul}{SPQR}" in s
