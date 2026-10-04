---
name: tlumaczenie
description: "Profesjonalne tłumaczenie instrukcji historycznych gier wojennych i planszowych (PDF, zwykle angielski) na polski jako dokument LaTeX (LuaLaTeX) w oprawie oryginału, z eksportem do PDF. Pojęciowy glosariusz w trzech warstwach (wspólna, epoka/seria, gra/wydanie), kontrola wierności przepisów (modalność, warunki, wyjątki, limity), trzy oddzielne przebiegi weryfikacji (terminologia, znaczenie zasad, redakcja językowa), dziennik decyzji i punktowa aktualizacja po zmianie terminu. Używaj, gdy użytkownik chce przetłumaczyć, dokończyć lub zaktualizować instrukcję gry."
argument-hint: "[zakres stron/rozdziałów] [--wydanie X] [--proba] [--aktualizacja WERSJA]"
---

# Tłumaczenie instrukcji gry

Cel: przekład, który polski gracz czyta jak dobrze napisaną polską instrukcję, a którego każdy przepis znaczy
dokładnie to samo co w oryginale. **Płynność bez wierności jest błędem. Wierność bez dobrej polszczyzny nie wystarcza.**

CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`). Konfiguracja projektu: `wgu.yaml` (`wgu config`).
Brak pliku → najpierw `/wgu:nowy-projekt`. Zalecana kolejność: `/wgu:atomizacja` → tłumaczenie (baza `kb/` daje
weryfikatorowi sens reguł i ich ID).

## Materiały (przeczytaj przed startem)
`${CLAUDE_PLUGIN_ROOT}/skills/tlumaczenie/references/`:
- `polityka-terminologiczna.md`: pojęcie jako jednostka glosariusza, trzy warstwy, statusy, dowody, procedura dla nowego pojęcia.
- `styl-przepisow.md`: rejestry (przepis, przykład, komentarz historyczny, uwaga tłumacza), zakaz synonimów, kalki i neologizmy, typografia.
- `wiernosc-zasad.md`: lista kontrolna znaczenia przepisów (modalność, negacja, wyjątki, kolejność, limity, parametry).
- `weryfikacja.md`: trzy przebiegi, pliki robocze, propozycje, dziennik decyzji, zmiana terminu, szablon raportu.
- `zrodla.md`: rejestr źródeł terminologii z oceną wiarygodności i zakresem użycia.
- `przewodnik_stylu_szablon.md`, `prompt_agenta.md`; `${CLAUDE_PLUGIN_ROOT}/templates/docs/pulapki.md` (środowisko LaTeX).
Szablony: `${CLAUDE_PLUGIN_ROOT}/templates/latex/gry-style.sty`, `main-template.tex`.

## Faza 0: ustalenia z właścicielem (AskUserQuestion, tylko to, czego nie da się ustalić samemu)
1. **Wydanie źródła**: które wydanie tłumaczymy. Czy uwzględniać erratę lub nowsze wydania i jak je oznaczać.
2. **Zakres**: przepisy / + przykłady / + komentarze historyczne i uwagi autora / + scenariusze / + tabele / + słowniczek.
3. **Wygląd**: oprawa jak w oryginale (domyślnie) czy styl projektu. Kompilacja lokalna (MiKTeX) czy inna.
4. **Istniejące tłumaczenie lub glosariusz**: zachowujemy styl i decyzje autora. Konflikty z `styl-przepisow.md`
   przedstaw jako osobną listę do decyzji, nie zmieniaj ich samodzielnie.

## Faza 1: środowisko i źródło
- Gałąź robocza, nie `master`. LuaLaTeX (MiKTeX lub TeX Live), `pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements.txt`.
- **Identyfikacja wydania** ze stopki i strony tytułowej PDF-u (edycja, rok, wersja). Zapisz ją w `wgu.yaml`
  (`sources.rules[].version`) i w `translation/source.json` razem ze skrótem SHA-256 pliku.
- `wgu pdf analyze` → kolor zmian wersji, fonty, wypełnienia → `wgu.yaml` (`pdf.*`). `wgu pdf render --montage 6` → oprawa.

## Faza 2: terminologia (przed tłumaczeniem)
1. Warstwy: `wgu.yaml` → `terminology.layers` (np. `[common, era/ancient, series/gboh]`), warstwa gry `kb/terminology.yaml`.
2. Zbuduj warstwę gry: pojęcia z `kb/terms.yaml` (jeśli jest baza), nazwy faz, znaczników, tabel i stanów jednostek,
   homonimy (jedno słowo, kilka pojęć). Każde pojęcie według procedury z `polityka-terminologiczna.md` §6:
   sens, reguły, kandydaci, dowody (`supports`), odrzuceni, formy odmiany, zapis. Status `proposal`.
3. **Decyzje właściciela**: przedstaw kluczowe pojęcia w kilku turach (AskUserQuestion, do 4 pytań naraz, z sensem,
   dowodami i rekomendacją). Zatwierdzone → `status: approved`, `decided_by: user`, wpis do `translation/decisions.yaml`.
4. `wgu terms lint` → 0 błędów. Ostrzeżenia o homonimach i wspólnych formach wyjaśnij.

## Faza 3: przewodnik stylu projektu
Na podstawie `przewodnik_stylu_szablon.md` i `styl-przepisow.md`. Istniejące tłumaczenie → opisz jego styl
(szablon, „Jak analizować styl”). Glosariusz **nie** jest już tabelą w przewodniku. Przewodnik odsyła do warstw
terminologii, a słowniczek do druku generuje `wgu terms glossary-tex`.

## Faza 4: oprawa LaTeX
`gry-style.sty` → `<projekt>-style.sty` (`translation.style`); `main-template.tex` → `translation.main`. Fonty, kolory `wg*`,
paginy, okładka bez logo wydawcy z dopiskiem „Nieoficjalne tłumaczenie”. Plik testowy wszystkich ramek →
`wgu tex build test.tex --render 80` → porównaj z oryginałem.

## Faza 5: przygotowanie fragmentów
1. `wgu pdf extract <pdf> <scratch>/src.md --accent … --heading-font …`, potem `wgu text mark <scratch>/src.md <scratch>/src.marked.md`.
   Sprawdź, że markery `%@ <nr reguły>` stoją przed każdym przepisem. Komentarze i przykłady bez numeru oznacz ręcznie
   (`%@ hist-6.2`, `%@ ex-6.12`).
2. Podziel na fragmenty o spójnej treści (rozdział lub podrozdział z przykładami, nie według liczby znaków) →
   `translation/chunks/<tag>.src.md`.
3. Dla każdego fragmentu `wgu terms for-chunk translation/chunks/<tag>.src.md > translation/chunks/<tag>.terms.md`.
4. Grafiki: `wgu pdf images` / `wgu pdf render --clip` (zob. `pulapki.md`).

## Faza 6: tłumaczenie (agenci `wgu:tlumacz`, równolegle w jednej wiadomości)
Prompt z `prompt_agenta.md`: plik źródła fragmentu, tabela terminów, sąsiedni kontekst (ostatni akapit poprzedniego
i pierwszy następnego fragmentu, tylko do odczytu), przewodnik, makra, PNG. Wynik: pliki `.tex` z markerami
i `translation/proposals/<tag>.yaml`. Po każdej fali: scalanie propozycji i decyzje właściciela (`weryfikacja.md`).

## Faza 7: weryfikacja każdego fragmentu (trzy przebiegi, `weryfikacja.md`)
1. **Terminologia**: `wgu terms check <pliki>`, `wgu check fidelity translation/chunks/<tag>.src.md <pliki>`.
2. **Znaczenie zasad**: agent `wgu:weryfikator-zasad` (Fable) z flagami z kroku 1 i dostępem do `kb/`.
3. **Redakcja językowa**: agent `wgu:redaktor-jezykowy`. Poprawki dotykające treści wracają do kroku 2.
Raport: `translation/reports/<tag>.md` według szablonu, z sekcją „Nie zweryfikowano”.

## Faza 8: złożenie, kontrole końcowe, PDF
- `wgu tex build "<translation.main>" --runs 3 --render 45` → przegląd wszystkich stron (ramki, tabele, żetony, sieroty).
- `wgu terms lint`, `wgu terms check <translation.dir>` (0 błędów, 0 „update”), `wgu check fidelity` dla całości.
- Słowniczek: `wgu terms glossary-tex <translation.dir>/14_slowniczek.tex`.
- Rozbieżności oryginał↔przekład i niejasności → `kb/ambiguities.yaml` (`scope: translation` / `original`).
- Commit na gałęzi roboczej. Push tylko na prośbę właściciela.
- Raport dla właściciela: co zrobione, decyzje do podjęcia (terminy sporne, konflikty z przewodnikiem), niejasności oryginału,
  czego nie zweryfikowano.

## Tryb próbny (`--proba`)
Przed pełnym przekładem nowej gry: 4–6 krótkich fragmentów obejmujących termin wieloznaczny, limit ruchu, wyjątek,
stan jednostki i komentarz historyczny. Przeprowadź Fazy 5–7 i pokaż właścicielowi raporty. Na koniec przećwicz zmianę
jednego terminu (`wgu terms impact`).

## Zasady nadrzędne
- Treść przepisów = oryginał wskazanego wydania. Niejasności rejestrujesz, nie rozstrzygasz w tekście.
  Erratę wprowadzasz tylko jawnie.
- Jedno pojęcie = jeden zatwierdzony termin. Bez synonimów, neologizmów i kalk. Propozycje nie są decyzjami.
- Decyzje właściciela (przewodnik, glosariusz) mają pierwszeństwo przed regułami ogólnymi. Konflikty pokazujesz osobno.
- Nie podszywaj się pod wydawcę: bez logo, stopka „tłumaczenie nieoficjalne”. Pliki UTF-8 bez BOM.
