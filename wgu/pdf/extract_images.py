"""Wyciąga obrazy osadzone w PDF (z pozycją na stronie) i opcjonalnie podmienia je na wersje
w wyższej rozdzielczości ze starszej edycji (dopasowanie po podobieństwie miniatur).

Użycie:
    python extract_images.py oryginal.pdf OUTDIR [--hires starsza_edycja.pdf] [--sheet arkusz.png]
              [--min 40] [--max 400]

Wynik: OUTDIR/pNN_i.png (+ OUTDIR/hires/… gdy --hires) oraz lista: plik, rozmiar px, bbox [pt], dopasowanie.
Arkusz (--sheet) pokazuje miniatury z nazwami — obejrzyj go narzędziem Read i nadaj plikom nazwy znaczące.
UWAGA: dopasowanie hi-res sprawdzaj wzrokowo (podobne żetony różnych jednostek potrafią się pomylić).
"""
import argparse
import os

import pymupdf


def save_images(pdf, outdir):
    os.makedirs(outdir, exist_ok=True)
    d = pymupdf.open(pdf)
    out = []
    for pno, p in enumerate(d):
        for i, info in enumerate(p.get_image_info(xrefs=True)):
            x = info["xref"]
            if not x:
                continue
            pix = pymupdf.Pixmap(d, x)
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            fn = os.path.join(outdir, f"p{pno + 1:02d}_{i}.png")
            pix.save(fn)
            out.append((fn, pix.width, pix.height, [round(v) for v in info["bbox"]]))
    return out


def thumb(fn, n=16):
    p = pymupdf.Pixmap(fn)
    if p.alpha:
        p = pymupdf.Pixmap(p, 0)
    if p.n != 3:
        p = pymupdf.Pixmap(pymupdf.csRGB, p)
    W, H = p.width, p.height
    return [p.pixel(int(x * W / n), int(y * H / n)) for y in range(n) for x in range(n)]


def dist(a, b):
    return sum((c1 - c2) ** 2 for p1, p2 in zip(a, b) for c1, c2 in zip(p1, p2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--hires", help="starsza edycja PDF z tymi samymi grafikami w wyższej rozdzielczości")
    ap.add_argument("--sheet", help="ścieżka PNG arkusza podglądu (małe obrazy, np. żetony)")
    ap.add_argument("--min", type=int, default=40, help="min szerokość px do arkusza")
    ap.add_argument("--max", type=int, default=400, help="max szerokość px do arkusza")
    ap.add_argument("--threshold", type=int, default=2_000_000, help="max odległość dopasowania hi-res")
    a = ap.parse_args()

    imgs = save_images(a.pdf, a.outdir)
    matches = {}
    if a.hires:
        hi = save_images(a.hires, os.path.join(a.outdir, "hires"))
        cand = {fn: thumb(fn) for fn, w, h, _ in hi if a.min <= w <= a.max * 3}
        for fn, w, h, _ in imgs:
            if not (a.min <= w <= a.max) or not cand:
                continue
            t = thumb(fn)
            best = min(cand, key=lambda g: dist(t, cand[g]))
            dd = dist(t, cand[best])
            bw = pymupdf.Pixmap(best).width
            if dd <= a.threshold and bw > w:
                matches[fn] = (best, bw, dd)

    for fn, w, h, bbox in imgs:
        m = matches.get(fn)
        extra = f"  -> hi-res {os.path.basename(m[0])} ({m[1]} px, d={m[2]})" if m else ""
        print(f"{os.path.basename(fn):12s} {w:5d}x{h:<5d} {bbox}{extra}")

    if a.sheet:
        small = [fn for fn, w, h, _ in imgs if a.min <= w <= a.max]
        cols = 8
        doc = pymupdf.open()
        pg = doc.new_page(width=cols * 90, height=max(1, (len(small) + cols - 1) // cols) * 100)
        for i, fn in enumerate(small):
            x, y = (i % cols) * 90, (i // cols) * 100
            pg.insert_image(pymupdf.Rect(x + 5, y + 5, x + 80, y + 80), filename=fn)
            pg.insert_text((x + 5, y + 93), os.path.basename(fn)[:-4], fontsize=9)
        pg.get_pixmap(dpi=100).save(a.sheet)
        print("arkusz:", a.sheet)


if __name__ == "__main__":
    main()
