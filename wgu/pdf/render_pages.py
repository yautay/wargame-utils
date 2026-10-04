"""Rendery stron PDF do PNG (do oglądania narzędziem Read) i montaże.

Użycie:
    python render_pages.py plik.pdf OUTDIR [--prefix o] [--dpi 70] [--pages 1-24]
    python render_pages.py plik.pdf OUTDIR --montage 6          # arkusze po 6 stron (3x2)
    python render_pages.py plik.pdf OUTDIR --page 15 --clip 416,594,579,750 --dpi 300 --name mapa.png
Współrzędne --clip w punktach PDF (x0,y0,x1,y1; początek w lewym górnym rogu).
"""
import argparse
import os

import pymupdf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--prefix", default="p")
    ap.add_argument("--dpi", type=int, default=70)
    ap.add_argument("--pages", help="zakres 1-based, np. 4-8")
    ap.add_argument("--montage", type=int, default=0, help="liczba stron na arkusz (3 kolumny)")
    ap.add_argument("--page", type=int, help="pojedyncza strona (1-based) do wycinka")
    ap.add_argument("--clip", help="x0,y0,x1,y1 w pt")
    ap.add_argument("--name", help="nazwa pliku wycinka")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    d = pymupdf.open(a.pdf)

    if a.page:
        p = d[a.page - 1]
        clip = pymupdf.Rect(*map(float, a.clip.split(","))) if a.clip else None
        out = os.path.join(a.outdir, a.name or f"{a.prefix}_{a.page:02d}_clip.png")
        p.get_pixmap(dpi=a.dpi, clip=clip).save(out)
        print(out)
        return

    if a.pages:
        s, _, e = a.pages.partition("-")
        pages = list(range(int(s) - 1, int(e or s)))
    else:
        pages = list(range(len(d)))

    if a.montage:
        W, H = d[0].rect.width, d[0].rect.height
        cols = 3
        rows = (a.montage + cols - 1) // cols
        for k in range(0, len(pages), a.montage):
            doc = pymupdf.open()
            pg = doc.new_page(width=cols * W, height=rows * H)
            for j, pn in enumerate(pages[k:k + a.montage]):
                x, y = (j % cols) * W, (j // cols) * H
                pg.show_pdf_page(pymupdf.Rect(x, y, x + W, y + H), d, pn)
            out = os.path.join(a.outdir, f"{a.prefix}_montage{k // a.montage}.png")
            pg.get_pixmap(dpi=min(a.dpi, 45)).save(out)
            print(out)
        return

    for pn in pages:
        out = os.path.join(a.outdir, f"{a.prefix}_{pn + 1:02d}.png")
        d[pn].get_pixmap(dpi=a.dpi).save(out)
    print(f"{len(pages)} stron -> {a.outdir}")


if __name__ == "__main__":
    main()
