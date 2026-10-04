---
name: tlumaczenie
description: "Tłumaczenie instrukcji gier planszowych/wargame'ów (PDF, zwykle angielski) na polski jako dokument LaTeX (LuaLaTeX) odwzorowujący oprawę oryginału (fonty, nagłówki, ramki, tabele, żetony), z zachowaniem stylu literackiego tłumacza, słowniczkiem EN→PL, oznaczaniem zmian wersji i notatkami tłumacza. Używaj, gdy użytkownik chce przetłumaczyć, dokończyć lub zaktualizować do nowej wersji instrukcję gry albo przygotować polską wersję rulebooka."
argument-hint: "[zakres stron/rozdziałów] [--aktualizacja WERSJA]"
---

# Tłumaczenie instrukcji gry

Proces wypracowany przy *GCACW Standard Basic Game Rules v1.6* (repo GCACW-PL). Efekt to skompilowany PDF
wyglądający jak oryginał wydawcy, z polskim tekstem w spójnym stylu.

CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`). Ustawienia projektu (źródła, kolor zmian, font nagłówków,
katalogi tłumaczenia) są w `wgu.yaml` (`wgu config`). Brak pliku → najpierw `/wgu:nowy-projekt`.

Zasoby:
- `${CLAUDE_PLUGIN_ROOT}/templates/latex/gry-style.sty`: szablon stylu (makra semantyczne, ramki, tabele, paginy; kolory `wg*`).
- `${CLAUDE_PLUGIN_ROOT}/templates/latex/main-template.tex`: plik główny (okładka, spis treści, import rozdziałów).
- `${CLAUDE_PLUGIN_ROOT}/skills/tlumaczenie/references/przewodnik_stylu_szablon.md`: przewodnik stylu i bazowy słowniczek.
- `${CLAUDE_PLUGIN_ROOT}/skills/tlumaczenie/references/prompt_agenta.md`: prompt dla równoległych agentów `wgu:tlumacz`.
- `${CLAUDE_PLUGIN_ROOT}/templates/docs/pulapki.md`: znane problemy techniczne. **Przeczytaj przed startem.**
- `wgu pdf analyze | extract | images | render`, `wgu tex build`, `wgu glossary` (`--help` przy każdym).

Jeśli projekt ma bazę wiedzy (`kb/`, z `/wgu:atomizacja`), tłumacze sprawdzają w niej sens reguł i terminy
(`wgu kb show`). Kolejność „najpierw atomizacja, potem tłumaczenie” daje spójniejszą terminologię.

## Faza 0: ustalenia z użytkownikiem (AskUserQuestion)
Ustal tylko to, czego nie da się sprawdzić samemu:
1. Kompilacja: lokalny MiKTeX (zalecane) / Overleaf / inna maszyna.
2. Wygląd: zbliżony do oryginału 1:1 (domyślnie) czy obecny styl projektu.
3. Wierność vs. istniejące tłumaczenie. Domyślnie tekst zasad jest wierny oryginałowi, a pomysły dydaktyczne tłumacza trafiają do ramek.
4. Zakres: same zasady / + wstęp i eseje / + zasady opcjonalne / + słowniczek / + tabele końcowe.

## Faza 1: środowisko
- Gałąź robocza (np. `v<wersja>`), nie `master`.
- MiKTeX: `winget install --id MiKTeX.MiKTeX -e --silent --scope user --accept-source-agreements --accept-package-agreements`.
  Włącz auto-instalację i **zmień mirror** (`pulapki.md`). Brakujące pakiety: `wgu tex build` wypisuje je w raporcie
  → `miktex packages install <nazwa>`.
- Silnik **LuaLaTeX** (fontspec). `latexmk` wymaga Perla, nie używaj go. `pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements.txt`.

## Faza 2: analiza oryginału
1. `wgu pdf analyze <pdf> --pages 4-8` → fonty, kolory tekstu (kolor zmian wersji), wypełnienia, rozmiar strony.
   Wpisz kolor zmian i font nagłówków do `wgu.yaml` (`pdf.accent_color`, `pdf.heading_font`).
2. `wgu pdf render <pdf> <scratch> --dpi 70 --montage 6` → montaże + 2–3 strony w powiększeniu (`--page N --clip …`).
3. Zamienniki fontów (MiKTeX): Garamond → EB Garamond; Myriad/Frutiger → Source Sans 3; Minion → Crimson Pro;
   Times → TeX Gyre Termes; Helvetica/Arial → TeX Gyre Heros; Futura → TeX Gyre Adventor; Palatino → TeX Gyre Pagella.
4. Zanotuj rozmiar tekstu, interlinię, układ kolumn, format numeracji, kapitaliki, kolor i kształt pasków.

## Faza 3: styl literacki i słowniczek
- Istniejące tłumaczenie: przeczytaj wszystkie pliki, opisz styl według szablonu przewodnika i wypisz błędy do poprawy **bez zmiany stylu**.
- Słowniczek EN→PL ustal **przed** tłumaczeniem (bazowa lista w szablonie + terminy gry; `kb/terms.yaml`, jeśli istnieje).
- Zapisz jako `translation.glossary` (np. `docs/przewodnik_stylu.md`). To wiążąca instrukcja dla wszystkich tłumaczy.

## Faza 4: oprawa
1. Skopiuj `gry-style.sty` jako `<projekt>-style.sty` (zmień `\ProvidesPackage`), wpisz do `wgu.yaml` → `translation.style`.
2. Ustaw fonty, kolory (`wgczern`, `wgniebieski` = kolor zmian, `wgszary`, `wgjasny`, …), `\seriatytul`, `\stopkatekst`,
   numerację, marginesy, rozmiar tekstu.
3. `main-template.tex` → plik główny (`translation.main`). Okładka: ilustracja z oryginału **bez logo wydawcy**,
   dopisek „Nieoficjalne tłumaczenie na język polski” + autor.
4. Plik testowy z każdą ramką i makrem → `wgu tex build test.tex --render 80` → porównaj z oryginałem → usuń.

## Faza 5: źródło i grafiki
1. `wgu pdf extract <pdf> <scratch>/src.md --accent <kolor> --heading-font <font>`. Markup: `§…§` nagłówek,
   `**…**`, `*…*`, `[[B:…]]` → `\nowe{}`. Indeks: `grep -n "===== PAGE" src.md`, `grep -n "^§[0-9]" src.md`.
2. `wgu pdf images <pdf> <scratch>/img [--hires starsza.pdf] --sheet <scratch>/sheet.png` → nazwij pliki znacząco
   → `translation.images/<wersja>/`. Dopasowanie hi-res **sprawdź wzrokowo**.
3. Mapy rastrowe: `wgu pdf render --page N --clip x0,y0,x1,y1 --dpi 300`. Proste diagramy przerysuj w TikZ z polskimi opisami.

## Faza 6: tłumaczenie równoległe
- Podziel oryginał na 5–7 części o podobnej objętości. Duże rozdziały dziel na pliki `07_1_…`, `07_2_…`.
- Uruchom agentów `wgu:tlumacz` w tle, wszystkich w jednej wiadomości, z promptem z `prompt_agenta.md`
  (uzupełnij `<WGU>`, ścieżki, zakres linii `src.md`, numer sekcji, pliki, listę PNG). Fragment z istniejącym
  tłumaczeniem: „REVISE”. Wstęp i eseje: rejestr literacki.
- Zbieraj ukute terminy do `<scratch>/new_terms.md`. Błędy stylu poprawiaj globalnie w `.sty`.

## Faza 7: złożenie i kontrola
1. `wgu tex build "<translation.main>" --runs 3 --render 45` → błędy, Overfull, PNG wszystkich stron → przejrzyj.
2. Ujednolić terminologię (grep wariantów). Ukute terminy do słowniczka → `wgu glossary <przewodnik> tex/14_slowniczek.tex`.
3. `grep -rn "CDN\|TODO" <translation.dir>/`, kompletność nagłówków vs. spis treści oryginału, liczba `\nowe{`.
4. Jeśli istnieje baza `kb/`: rozbieżności oryginał↔tłumaczenie dopisz do `kb/ambiguities.yaml` (`scope: translation`).
5. Commit na gałęzi roboczej. Push lub PR tylko na prośbę użytkownika.
6. Raport: co zrobione, decyzje terminologiczne do akceptacji, wątpliwości w źródle, czego nie zweryfikowano.

## Zasady nadrzędne
- Treść zasad = oryginał. Dopowiedzenia → ramka `wskazowka`. Zmiany wersji → `\nowe{}` / `nowyblok`.
- Pliki UTF-8 **bez BOM**, nagłówek `%! Author = …` / `%! Date = …`.
- Nie podszywaj się pod wydawcę: bez logo, stopka „tłumaczenie nieoficjalne”.
