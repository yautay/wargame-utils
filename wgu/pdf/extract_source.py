"""Ekstrakcja tekstu PDF w kolejności czytania (kolumnami) z markupem dla tłumaczy.

Markup:  §...§ = font nagłówkowy,  **...** = bold,  *...* = italic,
         [[B:...]] = tekst w kolorze zmian wersji (→ \\nowe{} w tłumaczeniu).
Strony oddzielone liniami "===== PAGE n =====".

Użycie:
    python extract_source.py oryginal.pdf src.md --accent 24408E --heading-font Myriad
    python extract_source.py oryginal.pdf src.md --columns 1      # układ jednokolumnowy
Kolor --accent i nazwę fontu nagłówków odczytasz z analyze_pdf.py.
"""
import argparse

import pymupdf


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def near(c, rgb, tol):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return abs(r - rgb[0]) <= tol and abs(g - rgb[1]) <= tol and abs(b - rgb[2]) <= tol


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--accent", default="24408E", help="kolor zmian wersji (hex), '' aby wyłączyć")
    ap.add_argument("--tol", type=int, default=40, help="tolerancja koloru")
    ap.add_argument("--heading-font", default="Myriad", help="fragment nazwy fontu nagłówków")
    ap.add_argument("--columns", type=int, default=2)
    a = ap.parse_args()

    accent = hex_to_rgb(a.accent) if a.accent else None
    d = pymupdf.open(a.pdf)
    res = []
    for pno, p in enumerate(d):
        W = p.rect.width
        blocks = [b for b in p.get_text("dict")["blocks"] if b["type"] == 0]

        def key(b):
            x0, y0, x1, _ = b["bbox"]
            if a.columns == 1:
                return (0, y0)
            col = 0 if x0 < W / 2 - 10 else 1
            return (col, y0)

        blocks.sort(key=key)
        res.append(f"\n===== PAGE {pno + 1} =====\n")
        for b in blocks:
            lines = []
            for l in b["lines"]:
                s = ""
                for sp in l["spans"]:
                    t = sp["text"]
                    if not t.strip():
                        s += t
                        continue
                    f = sp["font"]
                    if a.heading_font and a.heading_font in f:
                        t = "§" + t + "§"
                    elif any(x in f for x in ("Smbd", "Bold", "Semibold", "Black", "Heavy")):
                        t = "**" + t + "**"
                    elif any(x in f for x in ("It", "Italic", "Oblique")):
                        t = "*" + t + "*"
                    if accent and near(sp["color"], accent, a.tol):
                        t = "[[B:" + t + "]]"
                    s += t
                lines.append(s)
            res.append("\n".join(lines).replace("****", "").replace("§§", "") + "\n")
    open(a.out, "w", encoding="utf-8").write("".join(res))
    print(f"zapisano {a.out}; indeks: grep -n '===== PAGE' oraz grep -n '^§[0-9]'")


if __name__ == "__main__":
    main()
