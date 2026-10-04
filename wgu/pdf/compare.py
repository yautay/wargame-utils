"""Side-by-side comparison of an original page and a translated page (same scale), for visual layout review.

    wgu pdf compare ORIGINAL.pdf PAGE TRANSLATION.pdf PAGE OUT.png [--dpi 70]
"""
import argparse

import pymupdf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("orig"); ap.add_argument("orig_page", type=int)
    ap.add_argument("trans"); ap.add_argument("trans_page", type=int)
    ap.add_argument("out"); ap.add_argument("--dpi", type=int, default=70)
    a = ap.parse_args()
    o, t = pymupdf.open(a.orig), pymupdf.open(a.trans)
    po, pt = o[a.orig_page - 1], t[a.trans_page - 1]
    W = po.rect.width + pt.rect.width + 20
    H = max(po.rect.height, pt.rect.height) + 24
    doc = pymupdf.open()
    pg = doc.new_page(width=W, height=H)
    pg.show_pdf_page(pymupdf.Rect(0, 24, po.rect.width, 24 + po.rect.height), o, a.orig_page - 1)
    x = po.rect.width + 20
    pg.show_pdf_page(pymupdf.Rect(x, 24, x + pt.rect.width, 24 + pt.rect.height), t, a.trans_page - 1)
    pg.insert_text((6, 16), f"ORIGINAL p. {a.orig_page}  ({po.rect.width:.0f}x{po.rect.height:.0f} pt)", fontsize=11)
    pg.insert_text((x + 6, 16), f"TRANSLATION p. {a.trans_page}  ({pt.rect.width:.0f}x{pt.rect.height:.0f} pt)", fontsize=11)
    pg.get_pixmap(dpi=a.dpi).save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
