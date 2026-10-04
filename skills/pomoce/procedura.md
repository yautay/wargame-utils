# Procedura grafika

`WGU` = polecenie CLI z polecenia. Zasada nadrzędna: **nie zmieniasz treści zasad.** Teksty węzłów, krawędzie,
wyjątki i przykłady przenosisz ze specyfikacji 1:1. Problemy zgłaszasz w raporcie i ustawiasz `status: issues`
w specyfikacji (tylko to pole wolno Ci w niej zmienić).

## 1. Wejście
- Specyfikacje: `kb/aids/PNN-*.yaml` (`WGU kb show PNN` pokazuje je jako Markdown).
- Styl projektu: `aids.style` (lub `translation.style`) z `WGU config`: fonty, kolory, ramki.
- Środowisko: LuaLaTeX (MiKTeX/TeX Live). Znane pułapki: `templates/docs/pulapki.md` w repo narzędzia.

## 2. Styl: `aids.tikz` (np. `pomoce/pomoce-tikz.sty`) i `pomoce/styl.md`
- Jeśli `aids.tikz` nie istnieje, skopiuj szablon `templates/latex/pomoce-tikz.sty` z repo narzędzia
  i podłącz kolory projektu przez `\colorlet` (sekcja „Kolory ról” w szablonie). Szablon używa kolorów ról
  (`wgtekst`, `wgtlo`, `wgdecyzja`, `wgprzyklad`, `wgopcja`, `wgspecjalna`; stopka `\wgstopka`), a nie kolorów konkretnej gry.
- Zapisz `pomoce/styl.md`: źródło stylu, paleta (nazwy + HEX), fonty, kształty, grubości linii, wyróżnienie
  przykładu, minimalne rozmiary fontów, format. Zalecenia użytkownika (`--styl`) mają pierwszeństwo, ale
  **czytelność i kontrast** są nienaruszalne: tekst ≥ 7 pt, kontrast tekstu do tła ≥ 4,5:1.
- Kształty: `start`, `koniec`, `decyzja` (romb), `akcja`, `dane`, `tabela`, `wyjatek`, `regula` (tag ID),
  `przyklad` (podświetlenie ścieżki). Strzałki z etykietami, `\legendapomocy`, `\naglowekpomocy{ID}{tytuł}`,
  stopka ze źródłem („tłumaczenie nieoficjalne”, jeśli dotyczy).

## 3. Pliki
```
<aids.tex>/
  tresc/PNN-nazwa.tex      # sama grafika (tikzpicture/tabele), bez preambuły
  PNN-nazwa.tex            # dokument samodzielny: preambuła + \input{<aids.tex>/tresc/PNN-nazwa}
  Pomoce PL.tex            # zeszyt zbiorczy: okładka, spis, wszystkie gotowe pomoce
<aids.pdf>/                # wyniki (WGU aids build)
```
Dokument samodzielny jest kompilowany **z katalogu głównego repo** (tak robi `WGU aids build`):
```latex
\documentclass[10pt,a4paper]{article}
\usepackage{<styl projektu bez .sty>}
\usepackage{<aids.tikz bez .sty>}
\graphicspath{{./png/}}
\pagestyle{empty}
\begin{document}
\input{pomoce/tresc/P04-odwrot}
\end{document}
```

## 4. Implementacja każdej pomocy
1. Przeczytaj specyfikację w całości. Przepisz węzły i krawędzie 1:1, ID reguł jako tagi `regula`.
2. Rozmieść według sekcji „Układ”: najczęstsza ścieżka prosto w dół, wyjątki z boku.
3. Przykład według specyfikacji: podświetlona ścieżka i wartości przy węzłach.
4. `WGU aids build PNN` → przeczytaj raport (błędy, Overfull, brakujące pakiety) → obejrzyj PNG → popraw.
   Powtarzaj, aż spełnione są **kryteria akceptacji** (brak nachodzenia tekstu, krawędzie nie przecinają węzłów,
   mieści się na stronie, fonty ≥ 7 pt).
5. W specyfikacji ustaw `status: done` (lub `issues`) i zaktualizuj status w planie (`aids.plan`).

## 5. Zeszyt zbiorczy
Zaktualizuj `Pomoce PL.tex` (okładka w stylu instrukcji, spis treści, gotowe pomoce w kolejności z planu,
każda od nowej strony) i skompiluj: `WGU tex build "<aids.tex>/Pomoce PL.tex" --outdir <aids.pdf>`.

## 6. Raport (≤ 200 słów)
Wykonane pomoce (ścieżki PDF), odstępstwa od specyfikacji i ich powód, problemy ze specyfikacjami, zastosowany styl.
Nie edytujesz tłumaczenia, bazy reguł ani treści specyfikacji.
