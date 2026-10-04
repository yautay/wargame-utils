# Modele i skrypty: gdzie oszczędzać bez utraty jakości

## Domyślne przypisanie
| Praca | Kto | Dlaczego |
|---|---|---|
| ekstrakcja PDF, render, kompilacja LaTeX, sprzątanie | **CLI** (`wgu pdf`, `wgu tex build`, `wgu aids build`) | deterministyczne; wcześniej kosztowało wiele tur modelu |
| import starej bazy, lint, widoki, eksport, walidacja grafów | **CLI** | jw.; lint zastępuje „ręczną” kontrolę jakości przez model |
| wyszukanie reguły | **Haiku** (`/wgu:regula`) | to tylko wywołanie `kb show` i streszczenie |
| atomizacja: relacje, niejasności, scenariusze, protokół | **Fable** (`wgu:analityk-zasad`) | rozumowanie przekrojowe; tu jest prawdziwa wartość analizy |
| atomizacja: ekstrakcja reguł rozdziału | Fable (domyślnie) lub **Sonnet** (do sprawdzenia benchmarkiem) | praca lokalna, dobrze ustrukturyzowana |
| projekt pomocy | **Fable** (`wgu:projektant-pomocy`) | logika decyzji, poprawność gałęzi |
| rysowanie pomocy | **Sonnet** (`wgu:grafik`) | wierna implementacja specyfikacji, walidator pilnuje grafu |
| tłumaczenie | `inherit` (`wgu:tlumacz`) | jakość języka; ustaw model świadomie przy uruchomieniu |
| wydanie czytelne, errata na tekście | `inherit` (`wgu:redaktor`) | jw. |
| fundament digitalizacji | **Fable** (`wgu:architekt-digitalizacji`) | model stanu i kompletność decyzji |

## Benchmark przed zmianą modelu
Wzorzec: baza GCACW-PL (238 reguł, 36 scenariuszy, zbudowana przez Fable 2026-10-03).
1. Wybierz jeden rozdział (np. 7.0 Walka). Zbuduj bazę rozdziału tańszym modelem do osobnego katalogu
   (`kb.dir` w kopii `wgu.yaml`).
2. Porównaj ze wzorcem: pokrycie ID reguł, liczby w tabelach, `refs`, liczba ostrzeżeń lintu.
3. Odpowiedz na scenariusze `Q-…` tego rozdziału wyłącznie z nowej bazy. Licz trafienia i braki w łańcuchu reguł.
4. Zmień przypisanie dopiero, gdy wynik jest porównywalny. Zapisz wynik w tej tabeli.

| Data | Zakres | Model | Pokrycie reguł | Scenariusze OK | Uwagi |
|---|---|---|---|---|---|
| — | — | — | — | — | (do wypełnienia) |
