# Procedura architekta digitalizacji

`WGU` = polecenie CLI z polecenia. Źródło prawdy to baza `kb/`. Instrukcję czytasz tylko wtedy, gdy baza nie
wystarcza, i wtedy najpierw uzupełniasz bazę (jak analityk: stabilne ID, `refs`, lint).
Każdy element, który zapisujesz, ma `rules: [ID…]`.

## Pliki `digital.dir` (YAML; trafiają do pakietu `WGU kb export` pod kluczem `digital`)

### `state-model.yaml`: co silnik musi pamiętać
```yaml
entities:
  - id: unit
    fields:
      - {name: fatigue, type: int, range: [0, 4], rules: [R-2.2.9, R-8.0.5]}
      - {name: strength_marker, type: enum, values: [organized, disorganized], rules: [R-2.2.8]}
      - {name: side, type: enum, values: [normal, exhausted], rules: [R-2.2.3]}
  - id: leader
  - id: hex
  - id: game            # tura, faza, inicjatywa, pogoda, VP…
derived:                # wartości liczone, nie przechowywane
  - {name: combat_value, from: [strength_marker, demoralization], rules: [R-7.2.1]}
```

### `sequence.yaml`: struktura tury jako maszyna stanów
Fazy, kroki, pętle i warunki wyjścia (z `kb/procedures.yaml` i grafów `kb/aids`). Każdy krok:
`{id, name, procedure: P-…, aid: P09?, next, loop_until, rules}`. Grafy pomocy (węzły i krawędzie) są gotowymi
szkieletami procedur. Wskaż je zamiast przepisywać.

### `decisions.yaml`: wszystko, o co silnik pyta gracza
`{id: DEC-NN, who: active|inactive|owner|both, when: <krok sequence>, options: […], constraints: [...], default?, reaction: bool, rules}`.
Reakcje przeciwnika (np. wycofanie kawalerii, odwrót dobrowolny) mają `reaction: true` i moment wyzwolenia.

### `randomness.yaml`: każde losowanie
`{id: RNG-NN, when, dice: "1d6"|"2d6"…, modifiers: [MOD-…], table: T-…, simultaneous_with?, order, rules}`.
Rzuty „jednoczesne” mają ustaloną kolejność. Jeśli instrukcja jej nie podaje, to bloker albo `INT` (patrz niżej).

### `modifiers.yaml`: potok modyfikatorów
Dla każdej wartości liczonej (np. końcowy rzut w walce): lista modyfikatorów `{id: MOD-NN, label, value|formula,
condition, cap?, stacking, order, rules}` i reguły łączenia (limity, zaokrąglenia, kolejność).

### `hidden-info.yaml`: informacja ukryta i opcjonalna
Co jest ukryte, przed kim, kiedy się odsłania (np. Limited Intelligence). Zasady opcjonalne jako przełączniki `options`.

### `interpretations.yaml`: decyzje interpretacyjne dla silnika
Dla niejasności z `kb/ambiguities.yaml`, które blokują implementację: `{id: INT-NN, ambiguity: N-…, ruling, strength,
status: proposed|accepted, rules}`. Status `accepted` nadaje tylko właściciel projektu.

### `blockers.yaml`: czego brakuje
`{id: BLK-NN, what, impact (co nie zadziała), needed (np. arkusz Charts & Tables), refs}`.
Np. tabele z `complete: false`, niejasności bez rekomendacji, sprzeczności.

## W istniejących plikach bazy
- reguły: pole `digital: {kind, decision_by, randomness, state}` (enum `kind` w schemacie),
- tabele: pole `data` w postaci maszynowej (wiersze i kolumny jako liczby i przedziały) i `complete`,
- scenariusze: `given` (stan początkowy), `when` (akcja, decyzje, rzuty), `then` (oczekiwany wynik). To są golden testy silnika.

## Kontrola
- Każda decyzja, rzut i modyfikator ma `rules`, a każde ID istnieje (`WGU kb lint`).
- Pokrycie: każdy krok `sequence.yaml` ma procedurę. Każda reguła o `digital.kind` = decision/random ma wpis w decisions/randomness.
- Na koniec `WGU kb export`.

## Raport (≤ 300 słów)
Zakres, liczba stanów, decyzji, losowań i modyfikatorów, blokery z wpływem, interpretacje `proposed` do decyzji właściciela,
ścieżka pakietu JSON.
