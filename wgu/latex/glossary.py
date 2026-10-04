"""Generuje rozdział słowniczka (LaTeX) z tabeli „## 6. Słowniczek” w przewodniku stylu.

Użycie:
    python gen_glossary.py docs/przewodnik_stylu.md tex/14_slowniczek.tex [--author "Imię Nazwisko"] [--cols 3]
Tabela: dwie kolumny | English | Polski |; **bold** i *italic* są zamieniane na LaTeX.
Plik wynikowy importuj POZA multicols (sam otwiera multicols).
"""
import argparse
import datetime
import re


def tex(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"\*(.+?)\*", r"\\textit{\1}", s)
    return s.replace("&", r"\&").replace('"', "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md")
    ap.add_argument("out")
    ap.add_argument("--author", default="")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--heading", default="## 6. Słowniczek")
    a = ap.parse_args()

    md = open(a.md, encoding="utf-8").read()
    sec = md.split(a.heading, 1)[1]
    rows = []
    for line in sec.splitlines():
        if line.startswith("|") and not line.startswith("|---") and "English" not in line:
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) == 2 and c[0]:
                rows.append(c)
    # usuń duplikaty (pierwsze wystąpienie wygrywa), posortuj
    seen, uniq = set(), []
    for en, pl in rows:
        if en.lower() not in seen:
            seen.add(en.lower())
            uniq.append((en, pl))
    uniq.sort(key=lambda r: r[0].lower())

    out = [
        rf"%! Author = {a.author}",
        rf"%! Date = {datetime.date.today():%d.%m.%Y}",
        rf"% Słowniczek generowany z {a.md} (scripts/gen_glossary.py) — nie edytuj ręcznie",
        r"\section*{Słowniczek angielsko-polski}",
        r"\addcontentsline{toc}{section}{Słowniczek angielsko-polski}",
        r"Zestawienie terminów z oryginalnej instrukcji wraz z odpowiednikami przyjętymi w niniejszym "
        r"tłumaczeniu. Ułatwia korzystanie z angielskojęzycznych materiałów do gry "
        r"(scenariusze, tabele, żetony).\par\medskip",
        rf"\begin{{multicols}}{{{a.cols}}}",
        r"\footnotesize",
        r"\raggedright\setlength{\parskip}{1.5pt}",
    ]
    for en, pl in uniq:
        out.append(r"\hangindent=1em\textbf{%s} -- %s\par" % (tex(en), tex(pl)))
    out.append(r"\end{multicols}")
    open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"{len(uniq)} haseł -> {a.out}")


if __name__ == "__main__":
    main()
