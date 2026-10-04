# Procedura analityka zasad: atomizacja

`WGU` = polecenie CLI przekazane w poleceniu (np. `python "C:/…/wgu.py"`). Pracujesz w katalogu projektu gry.
Konfiguracja: `WGU config` (źródła, kolor zmian, font nagłówków, katalogi). Kontrakt formatu:
`<katalog wgu>/wgu/schemas/kb.schema.json` oraz `docs/ARCHITECTURE.md` w repo narzędzia.

## 1. Przygotuj tekst
- `WGU pdf extract <pdf> <scratch>/src.md --accent <pdf.accent_color> --heading-font <pdf.heading_font> --columns <pdf.columns>`.
  Markup: `§…§` nagłówek, `**…**` bold, `*…*` italic, `[[B:…]]` tekst w kolorze zmian wersji.
- Ramki, tabele i przykłady mogą mieć przestawioną kolejność. Sprawdzaj render strony:
  `WGU pdf render <pdf> <scratch> --page N --dpi 130` i oglądaj PNG narzędziem Read.
- Przeczytaj **całość**: oryginał, tłumaczenie (jeśli `translation.main` jest ustawione) i erratę (`sources.errata`).
  Nie próbkuj. Czytaj partiami i od razu zapisuj rekordy do plików YAML, nie trzymaj wszystkiego w pamięci.

## 2. Pliki bazy (`kb/`, UTF-8, YAML)
| Plik | Zawartość |
|---|---|
| `manifest.yaml` | `schema: wgu/kb@1`, gra, źródła, `analysis` (model, data, metoda), `interpretation_protocol`, `warnings` |
| `rules/NN-<slug>.yaml` | `chapter: {id, title}` + `rules: [...]` w kolejności instrukcji. Rdzeń bazy. |
| `terms.yaml` | `terms: [{en, pl, kind: technical/descriptive, definition, defined_at, used_in, refs}]`, `confusables` (pary „nie mylić”) |
| `tables.yaml` | `tables: [{id: T-NN, title, tables: [{columns, rows}], notes, refs, complete}]`. Każda liczba z instrukcji. |
| `procedures.yaml` | `procedures: [{id: P-NN, title, steps: [{n, text, markers: [decision/reaction/roll/pitfall], refs}], subprocedures}]` |
| `relations.yaml` | `relations: [{from, to, type: overrides/exception-to/requires/modifies/precedes/replaces, when, note, status: verified/inferred}]` |
| `ambiguities.yaml` | `ambiguities: [{id: N-NN, title, scope, quotes, readings, recommendation, strength: certain/probable/speculative, resolution_source, status: open, refs}]` |
| `changes.yaml` | `changes: [{id: C-…, kind: version/errata/faq, from_version, to_version, place, change, effect, refs}]` |
| `scenarios.yaml` | 25–40 pozycji: `scenarios: [{id: Q-NN, question, answer, chain, refs}]`: sytuacja przy stole → wynik + łańcuch reguł; także przypadki brzegowe |
| `notes/overview.md` | gra w pigułce i model mentalny (≤ 2 strony prozy) |

### Rekord reguły
```yaml
- id: R-7.4.3                    # R-<numer reguły>.<kolejny>; opcjonalne R-OPT-<skrót>.<n>; tytułu R-<TYTUŁ>-<n>
  title: Modyfikator artyleryjski — przypadki specjalne
  section: "7.4"
  source:
    text: oryg. 7.4 „Artillery Modifier”, s. 13; PL `tex/07_1_walka.tex:142`
    pages: "13"
    translation: [{file: tex/07_1_walka.tex, lines: "142"}]
  when: obrońca bez wartości artyleryjskiej / …
  effect: …                      # FAKT: co się dzieje. Markdown, w języku bazy.
  exceptions: → R-9.0.8 (umocnienia), R-12.0.2 (deszcz)
  keywords: [artyleria, różnica, NE]
  notes: "[wniosek] …"
  flags: [changed]               # changed (kolor zmian), optional, title-specific, summary, inference, errata
  refs: [R-9.0.8, R-12.0.2]      # wszystkie ID wspomniane w rekordzie
```
ID są **stabilne** między aktualizacjami. Nie przenumerowuj. Nowe rekordy dopisuj z kolejnym numerem.
`refs` uzupełniaj zawsze: na nich opiera się lint, `kb show` i eksport.

## 3. Kontrola jakości
- `WGU kb lint` ma dawać 0 błędów. Każde ostrzeżenie „unknown id” wyjaśnij (literówka albo brakujący rekord).
- Pokrycie: każdy nagłówek ze spisu treści instrukcji ma ≥ 1 regułę. Wypisz brakujące i uzupełnij.
- Każda liczba z tabel i modyfikatorów jest w `tables.yaml`. Tabele spoza dokumentu (osobny arkusz)
  oznacz `complete: false` i dodaj niejasność lub bloker.
- Na każde pytanie ze `scenarios.yaml` odpowiedz **wyłącznie z bazy** (`WGU kb show …`). Gdzie się nie da, uzupełnij bazę.
- Zweryfikuj 10 losowych cytatów (strona, linia).
- Relacje ze statusem `imported` sprawdź ze źródłem i zmień na `verified` (lub popraw/usuń).

## 4. Protokół interpretacji (zapisz w `manifest.yaml` → `interpretation_protocol`)
1. Terminy → `terms.yaml` (czy pytający używa terminu technicznie?).
2. Reguły → `WGU kb show <ID>` (pokazuje relacje, niejasności i scenariusze), wyszukiwanie po `keywords`.
3. Pierwszeństwo: scenariusz > zasady tytułu > zasady systemowe; szczególna > ogólna; nowsza wersja/errata > starsza.
4. Niejasności → warianty i rekomendacja z siłą.
5. Odpowiedź: werdykt → łańcuch reguł z ID i cytatami → założenia → ewentualna „house rule” oznaczona jako nieoficjalna.
6. Brak w bazie → wróć do źródła i **dopisz** rekord (stabilne ID), odnotuj w `manifest.history`.

## 5. Zakończenie
- Modyfikujesz tylko `kb/` (i pliki w scratchpadzie). Nie zmieniasz tłumaczenia ani źródeł.
- `WGU kb render` generuje widoki Markdown. Nie edytuj ich ręcznie.
- Raport (≤ 250 słów): liczby rekordów, 5 najważniejszych niejasności, rozbieżności oryginał↔tłumaczenie,
  blokery, czego nie zweryfikowano.
