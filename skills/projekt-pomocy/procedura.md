# Procedura projektanta pomocy

`WGU` = polecenie CLI z polecenia. Ścieżki z `WGU config`: `aids.specs` (specyfikacje YAML), `aids.plan` (plan),
`translation.glossary` (słowniczek), `translation.style` / `aids.style` (styl wizualny).

## 1. Źródła
1. Baza `kb/`: zacznij od `kb/_views/INDEX.md` (lub `WGU kb render`), potem `procedures.yaml`, `relations.yaml`,
   `tables.yaml`, `ambiguities.yaml`. Pojedyncze reguły: `WGU kb show R-… P-… T-…`. Używaj ID z bazy.
2. Tłumaczenie (teksty, terminologia) i oryginał rozstrzygają tylko wtedy, gdy baza nie wystarcza.
   Brak w bazie odnotuj w raporcie.
3. Słowniczek. **Wszystkie teksty w specyfikacjach muszą być z nim zgodne.**

## 2. Analiza logiki
W `kb/aids/analiza.md` zbuduj mapę:
- momenty decyzyjne graczy w sekwencji tury (kto, opcje, ograniczenia) i reakcje przeciwnika,
- procedury z rozgałęzieniami, warunki kwalifikacji („kto może…”), obliczenia (sumy modyfikatorów, limity),
- wyjątki i nadpisania (`relations.yaml`), typowe błędy graczy (`ambiguities.yaml`, przykłady z instrukcji),
- częstotliwość użycia przy stole.
Oceń kandydatów według wzoru: wartość dydaktyczna × częstotliwość × ryzyko błędu ÷ koszt. Odrzuconych kandydatów zapisz z powodem.

## 3. Typy pomocy
| Typ | Kiedy |
|---|---|
| `schemat-blokowy` | procedura z pętlami/rozgałęzieniami |
| `drzewo-decyzyjne` | kwalifikacja tak/nie, wybór opcji |
| `algorytm` | numerowane kroki z obliczeniami |
| `tabela-decyzyjna` | wiele warunków → wynik |
| `karta-ściąga` | sekwencja tury/fazy na jednej karcie |
| `infografika` | model mentalny (np. cykl stanów jednostki) |
| `przykład-ilustrowany` | przykład z instrukcji rozpisany na ścieżce schematu |

## 4. Specyfikacja: `kb/aids/PNN-<krotka-nazwa>.yaml`
Specyfikacja jest **samowystarczalna**: grafik nie czyta instrukcji.
```yaml
id: P09
title: Odwrót i ucieczka po walce
kind: schemat blokowy
type: schemat-blokowy
format: A4 pion, 1 strona
priority: 1                     # 1–3
complexity: L                   # S/M/L
use_moment: po wyniku „r”/„R” dla obrońcy
sources: R-7.6.1–R-7.6.11 (oryg. 7.6 s. 16–17; PL `tex/07_2_walka.tex:57-113`)
status: spec                    # spec → in-progress → done / issues
nodes:                          # shape: start | koniec | decyzja | akcja | notatka | dane | tabela | wyjątek (+ opis)
  - {id: S,  shape: start,   text: "Jednostki w heksie X wycofują się…", rules: "R-7.6.1", refs: [R-7.6.1]}
  - {id: D1, shape: decyzja, text: "Czy jest co najmniej jeden dozwolony heks?", rules: "R-7.6.5", refs: [R-7.6.5]}
  - {id: E0, shape: koniec,  text: "Kapitulacja…", rules: "R-7.6.5", refs: [R-7.6.5]}
edges:
  - {from: S,  to: D1}
  - {from: D1, to: E0, label: nie}
sections:                       # Markdown; nazwy sekcji jak niżej
  Cel: jedno zdanie, na jakie pytanie gracza odpowiada pomoc
  Elementy dodatkowe: tabele, ramka „Wyjątki”, legenda
  Przykłady przeprowadzone przez schemat: przykład z instrukcji + ścieżka (S → D1(tak) → …), co podświetlić
  Układ: kierunek, kolumny/pasy, co wyróżnić, przybliżone rozmieszczenie
  Uwagi dla grafika: pułapki układu, czego nie wolno skrócić, biblioteki TikZ
acceptance:
  - mieści się na 1 stronie A4, czcionka ≥ 7 pt
  - ID reguł widoczne małym drukiem przy węzłach
refs: [R-7.6.1, R-7.6.5]
```
Pomoce bez grafu (karta, infografika) nie mają `nodes`/`edges`, a treść opisują w `sections`.

## 5. Plan: `aids.plan` (Markdown)
Cel i odbiorca, zakres, źródła, model i data. Tabela: ID, tytuł, typ, moment użycia, priorytet, złożoność,
reguły, status. Kolejność wykonania i zależności, ryzyka uproszczeń, niejasności wpływające na schematy,
opcjonalne propozycje integracji z instrukcją (bez edycji jej plików).

## 6. Kontrola
- `WGU aids validate`: 0 błędów. Każda decyzja ma ≥ 2 wyjścia z różnymi etykietami. Każdy liść to `koniec`
  z regułą. Brak martwych gałęzi i węzłów nieosiągalnych. Każde ID reguły istnieje w bazie.
- Przykład przechodzi ścieżką zgodną z regułami. Sprawdź to ręcznie z bazą.
- Terminologia zgodna ze słowniczkiem (grep wariantów).
- Nie modyfikujesz reguł bazy. Nowe niejasności dopisz do `kb/ambiguities.yaml` (`status: open`) i zgłoś.

## 7. Raport (≤ 250 słów)
Lista pomocy (ID, tytuł, priorytet), kolejność, niejasności wpływające na schematy, polecenie `/wgu:pomoce …`.
