# Weryfikacja przekładu: trzy oddzielne przebiegi

Każdy fragment (*chunk*) przechodzi trzy przebiegi wykonywane przez **różnych** wykonawców. Kolejność jest stała,
bo poprawka językowa nie może zmienić treści przepisu.

| Przebieg | Kto | Sprawdza | Nie sprawdza |
|---|---|---|---|
| 1. Terminologia | skrypt `wgu terms check` + orkiestrator | odrzucone i nieaktualne formy, terminy sporne, skróty, nazwy z komponentów, pokrycie terminów w segmentach (`wgu check fidelity`) | znaczenia przepisu ani stylu |
| 2. Znaczenie zasad | agent `wgu:weryfikator-zasad` | `wiernosc-zasad.md` §1–8 dla każdego segmentu, porównanie z oryginałem i bazą `kb/` | stylu (chyba że styl zmienia sens) |
| 3. Redakcja językowa | agent `wgu:redaktor-jezykowy` | `styl-przepisow.md`, przewodnik projektu, typografia, polszczyzna | terminów zatwierdzonych (nie wolno ich zmieniać) |

**Obecność terminów z glosariusza nie dowodzi poprawności przekładu.** Przebieg 1 wyłapuje tylko niespójność
słownictwa. Za poprawność treści odpowiada przebieg 2.

Poprawka z przebiegu 3, która dotyka warunku, liczby, modalności lub terminu, wraca do przebiegu 2.

## Pliki robocze (`translation_work.dir`, domyślnie `translation/`)
```
translation/
  source.json               # odcisk SHA-256 źródłowych PDF-ów i wydanie (wykryj zmianę źródła)
  chunks/<tag>.src.md       # fragment źródła z markerami %@ (wgu text mark)
  chunks/<tag>.terms.md     # tabela terminów dla fragmentu (wgu terms for-chunk)
  proposals/<tag>.yaml      # propozycje i wątpliwości zgłoszone przez tłumacza (format niżej)
  decisions.yaml            # dziennik decyzji terminologicznych i redakcyjnych (tylko dopisywanie)
  context.md                # stan prac: ustalenia, otwarte kwestie, postęp (czytany przy wznowieniu)
  reports/<tag>.md          # raport weryfikacji fragmentu (szablon niżej)
```
**Wznowienie pracy:** nie kontynuuj z pamięci. Przeczytaj `context.md`, `decisions.yaml`, otwarte `proposals/`
i raporty, sprawdź `source.json` (czy źródło się nie zmieniło).

## Plik propozycji tłumacza (`proposals/<tag>.yaml`)
Tłumacz **nie edytuje glosariusza**. Zgłasza:
```yaml
chunk: c3
new_terms:                       # pojęcia spoza tabeli fragmentu
  - {source_term: "Orderly Withdrawal", where: "6.5 (src s. 14)", proposal: "planowe wycofanie", alternatives: ["odwrót w porządku"],
     sense: "…", reason: "…", evidence: "…"}
conflicts:                       # zatwierdzony termin nie pasuje w tym miejscu
  - {concept: gboh.cohesion-hit, where: "8.4", issue: "…", proposal: "…", evidence: "cytat ≤ 15 słów"}
source_doubts:                   # niejasności i błędy oryginału (→ kb/ambiguities.yaml)
  - {where: "10.21", issue: "…"}
translator_notes_suggested: []   # proponowane notatki tłumacza (wymagają zgody)
used_concepts: [gboh.rout, common.zoc]
```
Pusty plik (`new_terms: []` itd.) jest poprawnym wynikiem.

## Scalanie propozycji (orkiestrator, po każdej fali tłumaczy)
1. Zbierz `proposals/*.yaml`. Pogrupuj po pojęciach i usuń duplikaty.
2. Każdą propozycję przedstaw właścicielowi jako decyzję zamkniętą (AskUserQuestion: zatwierdź / wybierz wariant /
   zostaw jako spór), z sensem, dowodami i skutkiem.
3. Zapisz wynik w warstwie glosariusza (`status`, `decided_by`, `rationale`, `evidence`) i dopisz wpis do `decisions.yaml`:
   `{date, concept, change: "X → Y" lub "nowe", reason, by, affected: [...]}`.
4. Zmiana zatwierdzonego terminu: przenieś starą formę do `history` pojęcia, potem
   `wgu terms impact <id> --tex <pliki> --src translation/chunks/*.src.md`. Wynik to lista **konkretnych miejsc** do poprawy.
   Poprawiaj je punktowo, nie tłumacz fragmentów od nowa (zachowasz ręczne poprawki i styl).
   Na koniec `wgu terms check` nie może zgłaszać pozycji „update”.

## Szablon raportu fragmentu (`reports/<tag>.md`)
```markdown
# Raport weryfikacji: <tag> (<zakres: reguły / strony>)
Źródło: <plik, wydanie, SHA-256 skrót> · Przekład: <pliki .tex> · Data · Wykonawcy przebiegów (model)

## 1. Terminologia
- `wgu terms check`: <liczba błędów / do aktualizacji / info>; lista
- `wgu check fidelity` (pokrycie terminów): <flagi>
- Propozycje tłumacza: <liczba, status>

## 2. Znaczenie zasad
| Segment | Ustalenie | Kategoria (§ wiernosc-zasad) | Waga (krytyczna/istotna/drobna) | Poprawka |
- Flagi mechaniczne `wgu check fidelity` i ich ocena (uzasadniona różnica / błąd)
- Niejasności oryginału zgłoszone do `kb/ambiguities.yaml`

## 3. Redakcja językowa
- Zmiany (rodzaj, liczba), wątpliwości stylistyczne do decyzji

## Nie zweryfikowano
- <np. zgodność z tabelą spoza dokumentu, układ strony>
```

## Kontrole końcowe całości
- `wgu terms lint` (0 błędów) i `wgu terms check <translation.dir>` (0 błędów, 0 „update”).
- `wgu check fidelity` dla wszystkich fragmentów. Każda flaga ma ocenę w raportach.
- Kompletność: każdy segment źródła ma odpowiednik (`MISSING` = 0). Jeśli istnieje baza `kb/`, każde ID reguły ma miejsce w przekładzie.
- `wgu tex build` bez błędów, przegląd renderów stron.
- Słowniczek w dokumencie: `wgu terms glossary-tex <plik>`, tylko pojęcia zatwierdzone.
