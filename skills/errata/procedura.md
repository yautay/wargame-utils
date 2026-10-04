# Procedura: wersje, errata, rozstrzygnięcia

`WGU` = polecenie CLI z polecenia. Zmieniasz wyłącznie `kb/`.

## A. Nowa wersja instrukcji
1. `WGU pdf extract` dla starej i nowej wersji (kolor zmian z `pdf.accent_color`). Porównaj rozdział po rozdziale.
   Fragmenty `[[B:…]]` są oznaczone przez wydawcę, ale szukaj też zmian **nieoznaczonych** (porównanie tekstu).
2. Każda zmiana → rekord w `kb/changes.yaml`:
   `{id: C-<wersja>-NN, kind: version, from_version, to_version, place, change, effect (skutek dla gry), refs}`.
3. Zaktualizuj dotknięte reguły w `kb/rules/*.yaml`: treść, `source` (nowe strony), `flags: [changed]`,
   `version.changed_in`. **ID zostają.** Reguła usunięta: `flags: [removed]` + notatka, rekordu nie kasuj.
   Nowa reguła: kolejny wolny numer.
4. Zaktualizuj `relations.yaml`, `tables.yaml`, `scenarios.yaml` (odpowiedzi mogą się zmienić — sprawdź każdą z `refs`).

## B. Errata, FAQ, wyjaśnienia autora
1. Każdy punkt → `kb/changes.yaml` z `kind: errata | faq | clarification` i `source` (dokument, data, strona/link).
2. Jeśli punkt rozstrzyga niejasność: w `kb/ambiguities.yaml` ustaw `status: resolved`, dopisz `resolution`
   (co i na jakiej podstawie) i ID zmiany w `refs`.
3. Zmiana treści reguły → jak w A.3, z `flags: [errata]`.

## C. Rozstrzygnięcia bez oficjalnego źródła (`--niejasnosci`)
Dla wskazanych niejasności: przeczytaj źródła, przykłady i powiązane reguły (`WGU kb show`). Zaktualizuj
`readings`, `recommendation` i `strength`. Nie oznaczaj `resolved` bez źródła zewnętrznego.
Decyzja właściciela projektu → `status: house-rule`, `resolution: "decyzja właściciela, <data>"`.

## D. Kontrola i raport
- `WGU kb lint` (0 błędów). Każda zmiana ma `refs` do reguł.
- Lista dotkniętych miejsc: pliki tłumaczenia z `source.translation` zmienionych reguł i pomoce z pasującymi `refs`.
- Raport (≤ 250 słów): liczba zmian według rodzaju, zmiany o największym wpływie na grę, rozstrzygnięte i nowe
  niejasności, dotknięte pliki i pomoce.
