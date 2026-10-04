"""Measure the layout of an original rulebook PDF and write a draft layout specification (wgu/layout@1).

    wgu pdf layout ORIGINAL.pdf OUT.yaml [--pages 4-12]

What is measured automatically: page size, text area (margins), columns and gutter, body font/size/leading,
paragraph spacing and indentation, justification, heading levels (by size/weight/colour/case and numbering
pattern), filled boxes (colour, label of the text inside: EXAMPLE, DESIGN NOTE, …), running header/footer
(text, font, rules), rule-number style, inline exception labels, images. Font substitutes are proposed from a
table of free fonts available in TeX distributions.

The result is a DRAFT: the agent must check it against page renders (`wgu pdf render`) and complete what cannot
be measured (e.g. ornaments, table style), then generate the project style with `wgu tex style`.
"""
from __future__ import annotations

import argparse
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

from ..kb.store import write_yaml

PT_MM = 25.4 / 72

# original font family (substring, case-insensitive) → free substitute with fontspec name + note
SUBSTITUTES = [
    ("times", "TeX Gyre Termes", "metrycznie zgodny z Times"),
    ("garamond", "EB Garamond", ""),
    ("minion", "Crimson Pro", "lub EB Garamond"),
    ("caslon", "Libre Caslon Text", "sprawdź dostępność; alternatywa EB Garamond"),
    ("palatino", "TeX Gyre Pagella", ""),
    ("book antiqua", "TeX Gyre Pagella", ""),
    ("baskerville", "Libre Baskerville", "sprawdź dostępność"),
    ("century", "TeX Gyre Schola", ""),
    ("bookman", "TeX Gyre Bonum", ""),
    ("myriad", "Source Sans 3", "pliki SourceSans3-*.otf"),
    ("frutiger", "Source Sans 3", ""),
    ("helvetica", "TeX Gyre Heros", ""),
    ("arial", "TeX Gyre Heros", ""),
    ("futura", "TeX Gyre Adventor", ""),
    ("optima", "URW Classico", "sprawdź dostępność"),
    ("gill", "Gillius ADF", "sprawdź dostępność"),
    ("trajan", "Cinzel", "sprawdź dostępność; kapitaliki rzymskie"),
    ("copperplate", "Cinzel", "przybliżenie"),
]

PAPERS = {"letter": (612, 792), "a4": (595, 842), "legal": (612, 1008), "a5": (420, 595)}


def substitute(font: str) -> dict:
    f = font.lower()
    for key, sub, note in SUBSTITUTES:
        if key in f:
            return {"substitute": sub, **({"note": note} if note else {})}
    return {"substitute": "?", "note": "brak w tabeli zamienników — dobierz wzrokowo"}


def family(font: str) -> str:
    base = re.sub(r"^[A-Z]{6}\+", "", font)                     # subset prefix
    base = re.split(r"[-,]", base)[0]
    return re.sub(r"(PS|MT|Std|Pro|LT)$", "", base)


def is_bold(sp) -> bool:
    return bool(sp["flags"] & 16) or bool(re.search(r"Bold|Black|Heavy|Semibold|Smbd|Bd\b", sp["font"]))


def is_italic(sp) -> bool:
    return bool(sp["flags"] & 2) or bool(re.search(r"Italic|It\b|Oblique|Ital", sp["font"]))


def hexcol(c: int) -> str:
    return f"{c:06X}"


def parse_pages(spec: str | None, n: int) -> list[int]:
    if not spec:
        return list(range(n))
    a, _, b = spec.partition("-")
    return list(range(int(a) - 1, int(b or a)))


def measure(pdf: str, pages_spec: str | None = None) -> dict:
    d = pymupdf.open(pdf)
    W, H = d[0].rect.width, d[0].rect.height
    pages = parse_pages(pages_spec, len(d))
    band_top, band_bot = H * 0.07, H * 0.93

    chars = Counter()            # (family, size, bold, italic, color) -> chars
    raw_font = {}
    lines_body, block_boxes, para_gaps, line_gaps = [], [], [], []
    header_spans, footer_spans = [], []
    heading_cands = defaultdict(list)
    fills = defaultdict(list)
    hlines_top, hlines_bot = 0, 0
    first_line_indents = []
    right_aligned, line_count = 0, 0
    images = 0
    rule_number_style = Counter()
    exception_style = Counter()

    for pno in pages:
        p = d[pno]
        images += len(p.get_images())
        td = p.get_text("dict")
        # drawings: fills and horizontal rules in header/footer bands
        for dr in p.get_drawings():
            r = dr.get("rect")
            if dr.get("fill") and r and r.width > 40 and r.height > 12:
                col = "%02X%02X%02X" % tuple(int(x * 255) for x in dr["fill"][:3])
                if col not in ("FFFFFF",):
                    fills[col].append((pno, r))
            if r is not None and r.height < 2 and r.width > W * 0.3:
                if r.y0 < band_top + 10:
                    hlines_top += 1
                elif r.y0 > band_bot - 10:
                    hlines_bot += 1
        for b in td["blocks"]:
            if b["type"] != 0:
                continue
            x0, y0, x1, y1 = b["bbox"]
            spans = [sp for l in b["lines"] for sp in l["spans"] if sp["text"].strip()]
            if not spans:
                continue
            if y1 <= band_top:
                header_spans += [(pno, sp) for sp in spans]
                continue
            if y0 >= band_bot:
                footer_spans += [(pno, sp) for sp in spans]
                continue
            block_boxes.append((pno, x0, y0, x1, y1))
            prev_base = None
            for li, l in enumerate(b["lines"]):
                ls = [sp for sp in l["spans"] if sp["text"].strip()]
                if not ls:
                    continue
                text = "".join(sp["text"] for sp in ls).strip()
                for sp in ls:
                    fam = family(sp["font"])
                    raw_font[fam] = sp["font"]
                    key = (fam, round(sp["size"], 1), is_bold(sp), is_italic(sp), hexcol(sp["color"]))
                    chars[key] += len(sp["text"].strip())
                base = l["bbox"][3]
                if prev_base is not None and 0 < base - prev_base < 30:
                    line_gaps.append(round(base - prev_base, 2))
                prev_base = base
                lines_body.append((pno, l["bbox"], ls))
                # heading candidates: whole line in one style, bigger or bold, starting with a number or upper case
                s0 = ls[0]
                if len(text) < 80 and (is_bold(s0) or s0["size"] > 0) and all(round(sp["size"], 1) == round(s0["size"], 1) for sp in ls):
                    upper = sum(ch.isupper() for ch in text if ch.isalpha()) / max(1, sum(ch.isalpha() for ch in text))
                    if re.match(r"^\d+\.0\b", text):
                        lvl = "section"
                    elif re.match(r"^\d+\.\d\s", text) and upper > 0.8:
                        lvl = "subsection"
                    elif upper > 0.85 and len(text) > 3 and is_bold(s0):
                        lvl = "subsubsection?"
                    else:
                        lvl = None
                    if lvl:
                        heading_cands[lvl].append({"text": text[:60], "font": family(s0["font"]), "size": round(s0["size"], 1),
                                                   "bold": is_bold(s0), "italic": is_italic(s0), "color": hexcol(s0["color"]),
                                                   "upper": round(upper, 2), "page": pno + 1})
                # inline rule numbers like "6.11 A combat unit…" / "Exception:"
                m = re.match(r"^(\d+\.\d{2,})\b", text)
                if m and len(ls) > 1:
                    rule_number_style[(is_bold(s0), is_italic(s0), round(s0["size"], 1))] += 1
                for sp in ls:
                    if re.match(r"^\s*(Exception|Exceptions|Note|Important)s?:", sp["text"]):
                        exception_style[(sp["text"].strip().split(":")[0], is_bold(sp), is_italic(sp))] += 1
            # paragraph/first-line indent
            if len(b["lines"]) >= 2:
                fx = b["lines"][0]["bbox"][0]
                ox = st.median([l["bbox"][0] for l in b["lines"][1:]])
                first_line_indents.append(round(fx - ox, 1))

    # body = most frequent style
    body_key = chars.most_common(1)[0][0]
    body_fam, body_size = body_key[0], body_key[1]
    leading = st.median([g for g in line_gaps if body_size * 0.9 < g < body_size * 1.8]) if line_gaps else body_size * 1.2

    # text area and columns (body blocks only)
    xs0 = [b[1] for b in block_boxes]
    xs1 = [b[3] for b in block_boxes]
    ys0 = [b[2] for b in block_boxes]
    ys1 = [b[4] for b in block_boxes]
    left_x0 = min(xs0)
    right_x1 = max(xs1)
    mid = (left_x0 + right_x1) / 2
    left_blocks = [b for b in block_boxes if b[3] < mid + 5]
    right_blocks = [b for b in block_boxes if b[1] > mid - 5]
    columns = 2 if len(left_blocks) > 5 and len(right_blocks) > 5 else 1
    col = {}
    if columns == 2:
        lx1 = st.median(sorted(b[3] for b in left_blocks)[-max(1, len(left_blocks) // 3):])
        rx0 = st.median(sorted(b[1] for b in right_blocks)[:max(1, len(right_blocks) // 3)])
        col = {"column_sep_mm": round((rx0 - lx1) * PT_MM, 1), "column_width_mm": round((lx1 - left_x0) * PT_MM, 1)}
        col_right_edges = (lx1, right_x1)
    else:
        col_right_edges = (right_x1,)
    for _, bbox, ls in lines_body:
        if ls and abs(ls[0]["size"] - body_size) < 0.3:
            line_count += 1
            if any(abs(bbox[2] - e) < 2.5 for e in col_right_edges):
                right_aligned += 1

    paper = next((k for k, (w, h) in PAPERS.items() if abs(w - W) < 3 and abs(h - H) < 3), [round(W * PT_MM), round(H * PT_MM)])
    margins = {"top_mm": round(min(ys0) * PT_MM, 1), "bottom_mm": round((H - max(ys1)) * PT_MM, 1),
               "left_mm": round(left_x0 * PT_MM, 1), "right_mm": round((W - right_x1) * PT_MM, 1)}

    # headings summary: most common style per level
    headings = {}
    for lvl, cands in heading_cands.items():
        sty = Counter((c["font"], c["size"], c["bold"], c["italic"], c["color"], c["upper"] > 0.8) for c in cands)
        (fnt, size, bold, ital, colr, upper), n = sty.most_common(1)[0]
        headings[lvl] = {"font": fnt, **substitute(raw_font.get(fnt, fnt)), "size_pt": size, "bold": bold, "italic": ital,
                         "color": colr, "case": "upper" if upper else "asis", "count": n,
                         "examples": [c["text"] for c in cands if (c["font"], c["size"]) == (fnt, size)][:3]}

    # boxes: colour + label of first text inside
    boxes = {}
    for colr, items in fills.items():
        labels = Counter()
        widths = []
        for pno, r in items:
            widths.append(r.width)
            for _, bbox, ls in lines_body:
                pass
            txt = d[pno].get_textbox(pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + 30)).strip()
            m = re.match(r"^([A-Z][A-Z /&’'-]{2,30}?)(?::|\n|$)", txt)
            labels[m.group(1).strip() if m else (txt.split("\n")[0][:30] if txt else "")] += 1
        boxes[colr] = {"count": len(items), "width_mm": round(st.median(widths) * PT_MM, 1),
                       "labels": dict(labels.most_common(4))}

    def band(spans):
        out = Counter()
        for pno, sp in spans:
            x = (sp["bbox"][0] + sp["bbox"][2]) / 2
            pos = "left" if x < W * 0.33 else "right" if x > W * 0.66 else "center"
            out[(sp["text"].strip()[:50], family(sp["font"]), round(sp["size"], 1), is_bold(sp), is_italic(sp), pos)] += 1
        return [{"text": t, "font": f, "size_pt": s, "bold": b, "italic": i, "position": p, "pages": n}
                for (t, f, s, b, i, p), n in out.most_common(6)]

    styles = [{"font": f, "size_pt": s, "bold": b, "italic": i, "color": c, "chars": n}
              for (f, s, b, i, c), n in chars.most_common(12)]
    indent = st.median(first_line_indents) if first_line_indents else 0
    gaps = []
    by_page = defaultdict(list)
    for pno, x0, y0, x1, y1 in block_boxes:
        by_page[(pno, round(x0 / 20))].append((y0, y1))
    for v in by_page.values():
        v.sort()
        gaps += [round(b[0] - a[1], 1) for a, b in zip(v, v[1:]) if 0 < b[0] - a[1] < 30]

    return {
        "schema": "wgu/layout@1",
        "source": {"pdf": str(pdf), "pages_measured": f"{pages[0] + 1}-{pages[-1] + 1}", "page_count": len(d)},
        "status": "draft — measured automatically; verify against renders and complete",
        "page": {"paper": paper, "width_pt": round(W, 1), "height_pt": round(H, 1), "twoside": True,
                 "columns": columns, **col, "text_area_margins": margins},
        "fonts": {
            "body": {"font": body_fam, "original": raw_font.get(body_fam, body_fam), **substitute(raw_font.get(body_fam, body_fam)),
                     "size_pt": body_size, "leading_pt": round(leading, 2)},
            "styles_by_frequency": styles,
        },
        "paragraph": {"first_line_indent_pt": indent, "block_gap_pt_median": st.median(gaps) if gaps else None,
                      "justified_ratio": round(right_aligned / max(1, line_count), 2)},
        "colors": {"text": body_key[4], "fills": {k: v["count"] for k, v in boxes.items()}},
        "headings": headings,
        "rule_numbers": [{"bold": b, "italic": i, "size_pt": s, "count": n} for (b, i, s), n in rule_number_style.most_common(3)],
        "inline_labels": [{"label": l, "bold": b, "italic": i, "count": n} for (l, b, i), n in exception_style.most_common(6)],
        "boxes": boxes,
        "header": {"spans": band(header_spans), "horizontal_rules": hlines_top},
        "footer": {"spans": band(footer_spans), "horizontal_rules": hlines_bot},
        "images_on_measured_pages": images,
    }


BOX_ROLES = [("DESIGN", "uwagaprojektanta"), ("HISTORICAL", "uwagahist"), ("PLAY NOTE", "uwagagra"),
             ("EXAMPLE", "przyklad"), ("SPECIAL RULE", "specjalna"), ("OPTIONAL", "opcjonalna")]


def derive_spec(m: dict, pdf: str) -> dict:
    """Decisions for the style generator, pre-filled from measurements. Everything here may be edited."""
    body = m["fonts"]["body"]
    mar = m["page"]["text_area_margins"]
    head_top = 7.0 if m["header"]["spans"] else 0.0
    spec = {
        "paper": m["page"]["paper"],
        "margins_mm": {"top": round(mar["top_mm"], 1), "bottom": round(mar["bottom_mm"], 1),
                       "inner": round(mar["left_mm"], 1), "outer": round(mar["right_mm"], 1)},
        "columns": m["page"]["columns"], "column_sep_mm": m["page"].get("column_sep_mm", 6),
        "fonts": {"main": body["substitute"], "heading": None, "size_pt": body["size_pt"], "leading_pt": body["leading_pt"]},
        "paragraph": {"indent_pt": m["paragraph"]["first_line_indent_pt"] if m["paragraph"]["first_line_indent_pt"] > 3 else 0,
                      "skip_pt": m["paragraph"]["block_gap_pt_median"] or 4,
                      "justify": m["paragraph"]["justified_ratio"] > 0.45},
        "colors": {"text": m["colors"]["text"]},
        "rule_number": {"bold": True, "italic": False},
        "labels": {"bold": True, "italic": False},
        "boxes": {},
        "example": {"style": "text"},
        "header": {"style": "rule" if m["header"]["horizontal_rules"] else "plain", "title": "", "title_bold": True,
                   "title_italic": True, "size_pt": 9, "page_number": "outer"},
        "footer": {"text": "", "italic": True, "size_pt": 8, "position": "center"},
    }
    hs = m["headings"]
    for lvl in ("section", "subsection", "subsubsection?"):
        if lvl in hs:
            h = hs[lvl]
            spec[lvl.rstrip("?")] = {"style": "text", "size_pt": h["size_pt"], "bold": h["bold"], "italic": h["italic"],
                                     "case": h["case"], "color": h["color"]}
            if h["substitute"] != body["substitute"]:
                spec["fonts"]["heading"] = h["substitute"]
    if "section" in spec and spec["section"]["color"] != m["colors"]["text"]:
        spec["colors"]["heading"] = spec["section"]["color"]
    if m["rule_numbers"]:
        r = m["rule_numbers"][0]
        spec["rule_number"] = {"bold": r["bold"], "italic": r["italic"]}
    if m["inline_labels"]:
        l = m["inline_labels"][0]
        spec["labels"] = {"bold": l["bold"], "italic": l["italic"]}
    for colr, b in m["boxes"].items():
        if b["width_mm"] < 40:
            continue
        label = next(iter(b["labels"]), "") or ""
        role = next((r for k, r in BOX_ROLES if k in label.upper()), None)
        if role and role not in spec["boxes"]:
            spec["boxes"][role] = {"fill": colr, "italic": True, "label_case": "upper" if label.isupper() else "asis",
                                   "source_label": label}
    if "przyklad" in spec["boxes"]:
        spec["example"] = {"style": "box", "fill": spec["boxes"].pop("przyklad")["fill"]}
    hdr = [s for s in m["header"]["spans"] if s["position"] == "center"]
    if hdr:
        spec["header"].update({"title": hdr[0]["text"], "title_bold": hdr[0]["bold"], "title_italic": hdr[0]["italic"],
                               "size_pt": hdr[0]["size_pt"]})
    ftr = m["footer"]["spans"]
    if ftr:
        spec["footer"].update({"text": ftr[0]["text"], "italic": ftr[0]["italic"], "size_pt": ftr[0]["size_pt"],
                               "position": ftr[0]["position"]})
    return spec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--pages", help="zakres stron do pomiaru (1-based), domyślnie wszystkie")
    a = ap.parse_args()
    data = measure(a.pdf, a.pages)
    data["spec"] = derive_spec(data, a.pdf)
    data["spec_notes"] = ("`spec` = decyzje dla `wgu tex style`. Sprawdź je z renderami stron oryginału: fonty zastępcze, "
                          "wielkość liter nagłówków, etykiety ramek po polsku, tekst paginy i stopki (bez znaków wydawcy, "
                          "z dopiskiem o nieoficjalnym tłumaczeniu), styl tabel. Pomiary powyżej zostają jako dowód.")
    write_yaml(Path(a.out), data)
    print(f"layout draft -> {a.out}")


if __name__ == "__main__":
    main()
