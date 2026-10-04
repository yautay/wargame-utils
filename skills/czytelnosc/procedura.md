# Procedura redaktora: wydanie o lepszej czytelności

`WGU` = polecenie CLI z polecenia. Zasada nadrzędna: **forma się zmienia, treść zasad nie.**

## 1. Plan struktury (`<katalog wydania>/PLAN.md`)
- Kolejność wykładu dla odbiorcy: od pętli gry (`kb/notes/overview.md`, `kb/procedures.yaml`) do szczegółów.
  Wyjątki obok reguły, której dotyczą (`kb/relations.yaml`).
- Mapa: każdy rozdział wydania → lista ID reguł z bazy. **Każda reguła z bazy musi trafić dokładnie w jedno miejsce**
  (wyjątki: odsyłacze). Sprawdź pokrycie skryptem: wypisz ID z planu i porównaj z `WGU kb export` / `kb/rules/*.yaml`.
- Proponowane środki: numerowane kroki, tabele zbiorcze, ramki „Wyjątki”, przykłady (z instrukcji lub `kb/scenarios.yaml`),
  miniatury pomocy (`kb/aids`), słowniczek na marginesie.

## 2. Pisanie
- Styl i makra projektu (`translation.style`, przewodnik stylu). Plik główny wydania na wzór `translation.main`.
- Przy każdej regule odsyłacz do numeru oryginału (np. `\odsylacz{7.6}`), żeby gracz mógł sprawdzić źródło.
- Uproszczenie sformułowania jest dozwolone, jeśli warunki, liczby i wyjątki pozostają te same. Gdy masz wątpliwość,
  zostaw brzmienie tłumaczenia.
- Errata i rozstrzygnięcia: tylko z `kb/changes.yaml` i `kb/ambiguities.yaml` (`resolved`), oznaczone zgodnie z przewodnikiem.
  Rekomendacje bez rozstrzygnięcia podawaj w ramce „Interpretacja” z siłą rekomendacji, nigdy jako regułę.

## 3. Kontrola wierności (po każdym rozdziale)
- Dla każdej reguły z mapy: `WGU kb show <ID>` → porównaj warunki, liczby, wyjątki z tekstem wydania.
- `WGU tex build <plik> --render 60` → obejrzyj strony.
- Zapisz `<katalog wydania>/WIERNOSC.md`: tabela ID → miejsce w wydaniu → status (ok / uproszczone / rozbieżność).

## 4. Raport (≤ 250 słów)
Pokrycie (ile reguł, braki), rozbieżności do decyzji, zastosowane środki, czego nie zweryfikowano.
Nie zmieniasz `kb/` ani tłumaczenia wiernego. Wyjątek: nowe niejasności dopisz do `kb/ambiguities.yaml` (`status: open`).
