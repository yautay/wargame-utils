"""Analiza oprawy PDF: rozmiar strony, fonty (nazwa+rozmiar), kolory tekstu i wypełnień, obrazy.

Użycie:
    python analyze_pdf.py oryginal.pdf [--pages 4-8]
"""
import argparse
from collections import Counter

import pymupdf


def parse_pages(spec, n):
    if not spec:
        return range(n)
    a, _, b = spec.partition("-")
    return range(int(a) - 1, int(b or a))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="zakres stron 1-based, np. 4-8 (domyślnie wszystkie)")
    a = ap.parse_args()

    d = pymupdf.open(a.pdf)
    r = d[0].rect
    print(f"Stron: {len(d)}; rozmiar strony: {r.width:.0f} x {r.height:.0f} pt "
          f"({r.width / 72 * 25.4:.0f} x {r.height / 72 * 25.4:.0f} mm)")

    fonts, tcolors, fills, imgs = Counter(), Counter(), Counter(), 0
    samples = {}
    for pno in parse_pages(a.pages, len(d)):
        p = d[pno]
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for sp in l["spans"]:
                    t = sp["text"].strip()
                    if not t:
                        continue
                    k = (sp["font"], round(sp["size"], 1))
                    fonts[k] += len(t)
                    c = f"#{sp['color']:06X}"
                    tcolors[c] += len(t)
                    samples.setdefault(c, t[:50])
        for dr in p.get_drawings():
            f = dr.get("fill")
            if f:
                fills["#%02X%02X%02X" % tuple(int(x * 255) for x in f[:3])] += 1
        imgs += len(p.get_images())

    print("\nFonty (znaki):")
    for (f, s), n in fonts.most_common(25):
        print(f"  {n:7d}  {s:5.1f} pt  {f}")
    print("\nKolory tekstu (znaki) — kolor inny niż czarny to zwykle 'zmiany wersji':")
    for c, n in tcolors.most_common(10):
        print(f"  {n:7d}  {c}  np. {samples[c]!r}")
    print("\nKolory wypełnień (paski, tła, wiersze tabel):")
    for c, n in fills.most_common(10):
        print(f"  {n:5d}  {c}")
    print(f"\nObrazy osadzone: {imgs}")


if __name__ == "__main__":
    main()
