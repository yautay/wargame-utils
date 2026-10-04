# Szablon promptu agenta-tłumacza

Uruchamiaj 5–7 agentów `subagent_type: "wgu:tlumacz"`, `run_in_background: true`, wszystkich w **jednej** wiadomości.
`<WGU>` = pełne polecenie CLI narzędzia (`python "<plugin>/wgu.py"`), `<PLUGIN>` = katalog pluginu. Agent nie zna tych ścieżek, więc wpisz je.
Wspólna część (CZĘŚĆ A) jest identyczna dla wszystkich; CZĘŚĆ B to przydział. Uzupełnij `<…>`.
Prompt po angielsku działa najpewniej (agent pisze tekst polski).

---

## CZĘŚĆ A (wspólna)

You are translating part of the board-game rulebook "<Original title, version>" (<publisher>) into Polish, inside the LaTeX project at <repo path> (Windows; Bash tool is Git Bash; PowerShell also available). <One sentence about project history, e.g. "The owner started the translation earlier based on v1.4; we are completing it and updating it to v1.6">, with a layout imitating the publisher's original. Other agents translate other chapters in parallel — touch only your files.

QUALITY BAR: the result must read like a rulebook written by a careful Polish author — precise in rules, polished in historical commentary — and every rule must mean exactly what the original means. Fluency that changes a condition, obligation, prohibition, exception, limit or order of steps is an ERROR. No calques, no coined words, no synonyms for defined terms.

MANDATORY reading before writing anything:
0. <PLUGIN>\skills\tlumaczenie\references\wiernosc-zasad.md (rule-fidelity checklist: may/must/may not, negation, or/and, exception scope, order, limits per unit/order/phase/turn, parameters vs costs vs distances) and styl-przepisow.md (registers; forbidden calques and AI-style constructions; typography). The project style guide below OVERRIDES styl-przepisow.md where they differ.
1. <repo>\docs\przewodnik_stylu.md — the project's style guide (register, bilingual terms via \ang{}, macros, colours). TERMS: use ONLY the term table of your chunk, <repo>\translation\chunks\<tag>.terms.md (approved + proposed concepts, rejected forms, disambiguation of homonyms). One concept = one Polish term everywhere; never vary it for style. A source word with several concepts (see the table's homonym list): choose the concept by its sense in the sentence.
2. <repo>\<projekt>-style.sty — available macros/environments: \nowe{} / nowyblok (text in the original's change colour = new in this version), \gra{XYZ} (game abbrev, italic), \ang{english} (gives "/english"), \wyjatek \wyjatki \uwaga \opcja, environments kroki/podkroki (numbered procedures), przyklad[optional source], przykladtytul{title}, specjalna{title}, podsumowanie{title}, opcjonalna, wskazowka (translator's note box — ONLY for content beyond the original, sparingly), \zeton[l|r]{png}, \zetony{a}{b}, \zetonwiersz{a}, \zetonobok{text}{png} (use instead of \zeton right before lists/boxes), table helpers \naglowektabeli \tn{} \szarywiersz, column types C and L for tabularx, \natopiechota \natokawaleria \natoartyleria, \szerokostart/\szerokostop (top level only; for big full-width boxes prefer a figure*[tbp] float).
3. Style samples of the existing translation: <repo>\tex\<file1>.tex and <file2>.tex (imitate tone, sentence shape, bilingual terms, bold emphasis, "Wyjątek:" style). <If no prior translation: "Follow sections 1–4 of the style guide.">

SOURCE TEXT: <scratch>\src.md — text extracted in reading order. Markup: §...§ = heading-font text, **bold**, *italic*, [[B:...]] = text in the CHANGE colour (new/changed in this version → wrap in \nowe{} in Polish). Page markers "===== PAGE n =====". Running headers/footers (page numbers, copyright, address) are noise. Column sorting may misorder a block (esp. boxes/examples/tables); verify with the original PDF <repo>\docs\<original>.pdf — render a page: `<WGU> pdf render <pdf> <scratch> --page PAGE --dpi 130 --name x_<tag>_PAGE.png` and view it with Read (unique filenames). If the project has a rules knowledge base (kb/), check rule meaning and terms with `<WGU> kb show <ID or term>`. Low-res page renders exist in <scratch> as <prefix>_NN.png.

SEGMENT MARKERS: the source chunk <repo>\translation\chunks\<tag>.src.md contains lines `%@ KEY` (rule number or id like hist-6.2). Copy each marker line unchanged into your .tex, directly before the Polish text of that segment. Never drop, merge or renumber markers — the verification tools align source and translation by them.

NEIGHBOUR CONTEXT (read-only, do not translate): <last paragraph of the previous chunk, EN + PL if already translated> / <first paragraph of the next chunk, EN>.

TEXT TYPES: rules, examples, historical/design notes and translator's notes have different registers (styl-przepisow.md §1). Historical notes: careful Polish prose with terms established in Polish historiography for the era, no archaizing, no modern NATO jargon for ancient/19th-c. realities.

PROPOSALS FILE (required, may be empty): write <repo>\translation\proposals\<tag>.yaml with `new_terms` (concepts not in your table: source_term, where, proposal, alternatives, sense, reason), `conflicts` (an approved term that does not fit a place: concept id, where, issue, proposal, evidence ≤15 words), `source_doubts` (ambiguities/errors in the original — translate them faithfully, do NOT resolve them in the text), `translator_notes_suggested`, `used_concepts`. Do NOT edit any glossary file. Do NOT apply errata or later-edition changes unless told to.

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

SELF-CHECK before reporting: `<WGU> terms check <your .tex>` (no ERROR lines) and `<WGU> check fidelity translation\chunks\<tag>.src.md <your .tex>` — read every flag against the source and fix real errors (flags are hints, not verdicts).

FINAL REPORT (≤200 words): files written, local macros, number of entries in your proposals file (new terms, conflicts, source doubts), fidelity flags you judged legitimate and why, layout deviations.

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
