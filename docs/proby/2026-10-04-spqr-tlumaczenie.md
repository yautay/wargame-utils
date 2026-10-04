# Próba procesu tłumaczenia: SPQR Deluxe 5th Ed., 8 segmentów (2026-10-04)

Cel: sprawdzić nowy proces `/wgu:tlumaczenie` (glosariusz pojęciowy, markery segmentów, trzy przebiegi weryfikacji,
zmiana terminu) na krótkich fragmentach obejmujących różne trudności. Plugin nie był załadowany w sesji próby,
dlatego agentów `wgu:tlumacz`, `wgu:weryfikator-zasad` i `wgu:redaktor-jezykowy` emulowano agentami ogólnymi
z tymi samymi instrukcjami. Pliki próby (źródło, przekład, raporty, PDF) leżą poza repozytorium (scratchpad sesji),
bo zawierają fragmenty chronionego tekstu.

## Materiał
Źródło: `C:/dev/spqr/sources/SPQR+Deluxe_Rule+book_WEB.pdf` (5th Ed., © 2026 GMT), segmenty:
| Klucz | Co sprawdza |
|---|---|
| 4.34 | termin wieloznaczny (*line* vs *Line Command*), modalność „may—not must” |
| 6.11, 6.12 | limit ruchu (MA na rozkaz; bez limitu na turę, raz na Fazę Rozkazów) |
| 6.13 | wyjątek (harcownicy) i zakres kary (tylko rozkaz Move) |
| hist-6.2 | komentarz historyczny (rejestr, nazwa własna Cynoscephalae) |
| 10.11, 10.14 | stan i parametr (TQ rating vs TQ check; próg ≥ TQ) |
| 10.31 | stan jednostki (*Depleted*), zakaz kumulacji |

Glosariusz: warstwy `common` (5 pojęć), `era/ancient` (3), `series/gboh` (20). Wszystkie mają status `proposal`
lub `disputed`, bo nic nie zostało zatwierdzone przez właściciela.

## Wyniki
**Przekład** (Opus, 1 agent): 8/8 segmentów, markery zachowane. Plik propozycji: 9 nowych terminów, 4 konflikty,
3 wątpliwości co do źródła. `terms check`: 0 błędów. Kompilacja do PDF: 1 strona, 0 przepełnień.
Komentarz historyczny w osobnej ramce „Tło historyczne”.

**Przebieg 1, kontrola mechaniczna (`wgu check fidelity`)**
- Wersja pierwsza narzędzia: 8/8 fałszywych alarmów. Przyczyny: „single/once” liczone jako liczba 1, „ale” jako wyjątek,
  makro `\wyjatek` niewidoczne, „Cohesion” wewnątrz „Cohesion Hit”, przeniesienia wyrazów w źródle.
  Wszystkie poprawiono w narzędziu.
- Po poprawkach: poprawny przekład **0 flag**. Kopia z 6 wstrzykniętymi błędami znaczenia: **5/6 wykrytych**
  (modalność, usunięty limit „tylko raz”, usunięty wyjątek, zmieniona liczba, zakaz zamieniony na pozwolenie).
  **Niewykryte**: zawężenie progu „osiągnie lub przekroczy” → „przekroczy” (≥ → >).

**Przebieg 2, weryfikator zasad (Fable)**
- Ślepy test na kopii z błędami (bez flag mechanicznych): **6/6 wykrytych**, w tym próg ≥/>. Każdy z kategorią
  i poprawką. Dodatkowo 2 trafne niejasności oryginału (zakres warunku w 6.13; „absorbed” w 10.14), nierozstrzygnięte.
- Właściwy przekład: 0 błędów znaczenia. 2 uwagi drobne: składnia „zasięg dowodzenia jednej z jednostek” sugeruje
  parametr jednostki; „uciekające” dla *Routed* może sugerować ruch zamiast stanu, co jest kwestią glosariusza.

**Przebieg 3, redaktor językowy (Opus)**: około 19 zmian bez naruszenia treści. Przykłady:
- „jest podstawowym limitem” → „to podstawowy limit”,
- „kara w postaci trafienia” → „kara”,
- „jednostek harcowników” → „harcowników”,
- „przejść test” → „wykonać test”,
- „osłaniać przeszkodami naturalnymi” → „oprzeć skrzydła o przeszkody naturalne”.
Usunięto 7 zbędnych glos `\ang{}`. Zmianę sformułowania limitu w 6.12 oflagowała kontrola mechaniczna i ponownie
sprawdzono znaczenie: bez zmiany sensu.

**Zmiana terminu (symulacja: *Depleted* „osłabiona” → „uszczuplona”)**: `wgu terms impact` wskazał 3 linie
w segmencie 10.31, `wgu terms check` oznaczył je jako „update” (z listą starych form). Ograniczenie: wyszukiwanie
opiera się na liście form `pl_forms` / `from_forms`. Forma spoza listy nie zostanie znaleziona.

## Wykryte problemy i wnioski
1. Kontrola mechaniczna jest dobrym, tanim filtrem (5/6), ale **nie zastępuje** przebiegu 2. Granice przedziałów
   i zakres przeczeń wymagają czytania ze zrozumieniem.
2. Pierwsza wersja heurystyk była bezużyteczna przez nadmiar fałszywych alarmów. Każdą zmianę heurystyk testuj na parze
   „poprawny przekład / przekład z wstrzykniętymi błędami” (do zrobienia jako test regresyjny z własnym, niechronionym tekstem).
3. Zapis pierwszego użycia w glosariuszu („trafienie (utrata spójności)” + glosa) jest w zdaniu ciężki.
   Do decyzji: rozwinięcie w słowniczku zamiast w tekście.
4. Symulacja zmiany terminu w warstwie gry wpłynęła na równoległą weryfikację (flaga w 10.31). Eksperymenty
   z glosariuszem prowadź na kopii projektu.
5. Redaktor dobrze odróżnia glosy przydatne (nazwy z komponentów i tabel) od zbędnych. Reguła trafiła do przewodnika
   (`notation.first_use` tylko dla terminów z komponentów).
6. Ślepy weryfikator Fable działał szybko (~1 min na 8 segmentów). Koszt przebiegu 2 jest umiarkowany, więc warto go
   stosować do całości, nie tylko próbek.
