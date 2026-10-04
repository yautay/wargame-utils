# Szablon promptu agenta-tłumacza

Uruchamiaj 5–7 agentów `subagent_type: "wgu:tlumacz"`, `run_in_background: true`, wszystkich w **jednej** wiadomości.
`<WGU>` = pełne polecenie CLI narzędzia (`python "<plugin>/wgu.py"`). Agent nie zna tej ścieżki, więc wpisz ją.
Wspólna część (CZĘŚĆ A) jest identyczna dla wszystkich; CZĘŚĆ B to przydział. Uzupełnij `<…>`.
Prompt po angielsku działa najpewniej (agent pisze tekst polski).

---

## CZĘŚĆ A (wspólna)

You are translating part of the board-game rulebook "<Original title, version>" (<publisher>) into Polish, inside the LaTeX project at <repo path> (Windows; Bash tool is Git Bash; PowerShell also available). <One sentence about project history, e.g. "The owner started the translation earlier based on v1.4; we are completing it and updating it to v1.6">, with a layout imitating the publisher's original. Other agents translate other chapters in parallel — touch only your files.

MANDATORY reading before writing anything:
1. <repo>\docs\przewodnik_stylu.md — style guide + EN→PL glossary. Follow it strictly (register, bilingual terms via \ang{}, macros, colours, glossary terms).
2. <repo>\<projekt>-style.sty — available macros/environments: \nowe{} / nowyblok (text in the original's change colour = new in this version), \gra{XYZ} (game abbrev, italic), \ang{english} (gives "/english"), \wyjatek \wyjatki \uwaga \opcja, environments kroki/podkroki (numbered procedures), przyklad[optional source], przykladtytul{title}, specjalna{title}, podsumowanie{title}, opcjonalna, wskazowka (translator's note box — ONLY for content beyond the original, sparingly), \zeton[l|r]{png}, \zetony{a}{b}, \zetonwiersz{a}, \zetonobok{text}{png} (use instead of \zeton right before lists/boxes), table helpers \naglowektabeli \tn{} \szarywiersz, column types C and L for tabularx, \natopiechota \natokawaleria \natoartyleria, \szerokostart/\szerokostop (top level only; for big full-width boxes prefer a figure*[tbp] float).
3. Style samples of the existing translation: <repo>\tex\<file1>.tex and <file2>.tex (imitate tone, sentence shape, bilingual terms, bold emphasis, "Wyjątek:" style). <If no prior translation: "Follow sections 1–4 of the style guide.">

SOURCE TEXT: <scratch>\src.md — text extracted in reading order. Markup: §...§ = heading-font text, **bold**, *italic*, [[B:...]] = text in the CHANGE colour (new/changed in this version → wrap in \nowe{} in Polish). Page markers "===== PAGE n =====". Running headers/footers (page numbers, copyright, address) are noise. Column sorting may misorder a block (esp. boxes/examples/tables); verify with the original PDF <repo>\docs\<original>.pdf — render a page: `<WGU> pdf render <pdf> <scratch> --page PAGE --dpi 130 --name x_<tag>_PAGE.png` and view it with Read (unique filenames). If the project has a rules knowledge base (kb/), check rule meaning and terms with `<WGU> kb show <ID or term>`. Low-res page renders exist in <scratch> as <prefix>_NN.png.

Translate EVERYTHING in your range faithfully and completely (every rule, exception, note, example, table row). Do not invent rules. Tables: tabularx \linewidth in the original's style (header row \naglowektabeli + \tn{}, alternating \szarywiersz). "Special Rule …" boxes → specjalna; "Example (from X):" → przyklad[z \gra{X}]; "(Optional)" paragraphs → opcjonalna. Place counter images where the original shows counters next to text (PNG names in the style guide; files in <repo>\png\<wersja>).

Files: UTF-8 WITHOUT BOM. Each file starts with `%! Author = <autor>` and `%! Date = <data>`. Chapter files contain only body content (no preamble, no multicols — the main file wraps everything in \begin{multicols}{2}). Do NOT edit the .sty, the main .tex, docs/, or other agents' files. If you need a macro, define it locally with \providecommand and report it. If you find a bug in the .sty, work around it locally AND report it.

COMPILE CHECK (required): create <repo>\_t_<tag>.tex:
```
\documentclass[10pt,twoside,a4paper]{article}
\usepackage{<projekt>-style}
\graphicspath{{./png/<wersja>/}{./png/}}
\begin{document}
\begin{multicols}{2}
\setcounter{section}{<N-1>}   % so your \section gets number N.0; for a continuation file also \setcounter{subsection}{<k>}
\import{./tex/}{<your file>}
\end{multicols}
\end{document}
```
Compile from <repo>: `<WGU> tex build _t_<tag>.tex --render 110` (LuaLaTeX ×2, error/overfull summary, PNG pages in `_png/`). Fix all errors; fix overfull boxes > 10pt. Check the PNGs with Read (boxes, tables, counters, orphaned box titles). Afterwards DELETE your _t_<tag>.* files and their `_png/` renders.

FINAL REPORT (≤200 words): files written, local macros, EN→PL terms you coined beyond the glossary (as "EN → PL" list), doubts about the source (typos, contradictions), layout deviations.

---

## CZĘŚĆ B (przydział) — przykłady

**Nowy rozdział:**
YOUR ASSIGNMENT (tag: c): NEW file tex/06_marsz_ruch.tex — Chapter 6.0 March and Movement, src.md lines ~1249–1522 (original pages 9–11): 6.1 …, 6.2 …, 6.3 …. Start the file with \section{Marsz i ruch} so it becomes 6.0. Counters: force_usa/force_csa (\zetony) next to Force Markers.

**Kontynuacja rozdziału w osobnym pliku:**
… NEW file tex/07_2_walka.tex — continuation of Chapter 7.0 (do NOT start with \section; first heading is \subsection{Wyniki walki} → 7.5). Source lines … EXCLUDING the big example box on page 15 (another agent does it).

**Rewizja istniejącego tłumaczenia:**
REVISE existing tex/01_….tex … against the new version (src.md lines …). Keep the author's wording and tone wherever correct; fix what differs from the new version, factual errors and typos; unify terminology to the glossary; convert manual \textcolor/\textit exceptions to the macros; replace old images with \zeton using the new PNGs. Keep file names.

**Wstęp/esej (poza multicols):**
NEW tex/00_powitanie.tex: page 2 (welcome, essay, links, photo). Imported OUTSIDE multicols — manage columns yourself; use \section* headings. Translate the essay in literary, warm but faithful Polish — the regulatory tone does NOT apply here.

**Strona tabel końcowych:**
NEW tex/15_tabele.tex — appendix rebuilt from the last page (full-width table + two columns of boxes/tables), imported OUTSIDE multicols; \section*{Tabele i podsumowania} + \addcontentsline{toc}{section}{…}. Render and compare visually with the original page.
