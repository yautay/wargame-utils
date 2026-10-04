# Wierność zasad: lista kontrolna przekładu przepisów

Płynność nie jest miarą jakości. Przekład, który brzmi naturalnie, ale zmienia warunek, obowiązek, wyjątek
albo skutek mechaniczny, jest **błędny**. Ten dokument służy tłumaczowi (podczas pisania) i weryfikatorowi
zasad (przebieg 2). Dotyczy wyłącznie tekstu przepisów, przykładów i tabel. Komentarze historyczne
i uwagi autora obowiązuje wierność treści, ale nie ta lista.

## 1. Modalność: możliwość, obowiązek, zakaz
| Oryginał | Przekład | Pułapka |
|---|---|---|
| *may* (uprawnienie gracza) | **może**, **wolno** | nie „musi”, nie „powinien” |
| *may* (opis możliwego skutku: „may be eliminated”) | „może zostać wyeliminowana” | to nie uprawnienie; nie zamieniać na „zostaje” |
| *may not*, *cannot*, *must not* | **nie może**, **nie wolno** | nigdy „może nie” (to możliwość, a nie zakaz) |
| *must*, *is required to* | **musi**, **należy** | „powinien” jest słabsze, więc niedopuszczalne |
| *should* | „powinien”, ale sprawdź, czy autor nie ma na myśli obowiązku | rozbieżność zgłoś jako niejasność |
| *need not*, *does not have to* | **nie musi** | to nie „nie może” |
| *is (not) allowed* | (nie) wolno, jest (nie)dozwolone | |
| *always* / *never* | zawsze / nigdy | nie osłabiać do „zwykle” / „rzadko” |
| *automatically* | automatycznie (bez rzutu) | nie gubić: często oznacza „bez testu” |

## 2. Negacja, alternatywa, koniunkcja
- *not … or …*: zakres przeczenia („nie może ruszać się ani strzelać” ≠ „nie może ruszać się lub strzelać”).
- *or*: rozstrzygnij, czy alternatywa jest rozłączna (**albo**), czy nie (**lub**). Jeśli z zasad nie wynika, użyj „lub”
  i zgłoś wątpliwość. Nie wprowadzaj rozłączności, której nie ma.
- *either … or* → „albo …, albo …”; *neither … nor* → „ani …, ani …”.
- *and* w warunkach: wszystkie warunki muszą zachodzić jednocześnie. Nie rozbijaj ich na osobne zdania,
  które czytelnik zrozumie jako alternatywę.
- *and/or* → „lub” (inkluzywne). Nie używaj „i/lub”.
- *unless* → „chyba że”, *only if* → „tylko wtedy, gdy”, *if and only if* → „wtedy i tylko wtedy, gdy”.
- *any*: w zdaniu twierdzącym „dowolny”, w przeczeniu „żaden” („no unit may” = „żadna jednostka nie może”).
  *Any* ≠ *all*.

## 3. Zakres wyjątków
- Ustal, czego dotyczy wyjątek: całej reguły, jednego zdania czy jednego elementu wyliczenia.
- *Except*, *other than*, *with the exception of* → „z wyjątkiem”, „poza”. Lista wyjątków musi zostać kompletna.
- *However* po regule ogólnej często wprowadza wyjątek. Nie zamieniaj go na „ponadto”.
- Wyjątki z innych przepisów (odsyłacze) zachowaj w tym samym miejscu zdania.

## 4. Kolejność działań
- *before*, *after*, *then*, *immediately*, *until*, *during*, *at the end of*, *simultaneously*: kolejność to mechanika.
- Kroki numerowane: ta sama liczba i kolejność. Nie łącz kroków i nie dodawaj nowych.
- „Jednocześnie” nie oznacza „po kolei”. Jeśli przepis nie mówi, kto pierwszy, przekład też tego nie mówi.

## 5. Limity i ich odniesienie
- *up to N* → „do N” lub „nie więcej niż N” (włącznie). *At least N* → „co najmniej N”. *More than N* → „więcej niż N”
  (wyłącznie). *N or more* → „N lub więcej”. *Fewer than* → „mniej niż”.
- Zachowaj **czego** dotyczy limit: na jednostkę, na rozkaz, na aktywację, na fazę, na turę, na grę, na heks, na stos.
  „Once per turn” ≠ „once per phase”. *Each* → „każda”; *per* → „na” lub „za” (np. „+1 za każdą jednostkę”).
- *Within N hexes*: przenieś sposób liczenia (czy liczy się heks wyjściowy lub docelowy), jeśli oryginał go określa.

## 6. Parametry, koszty, odległości
Nie myl pojęć, które w języku ogólnym są bliskie:
- **parametr** jednostki lub dowódcy (*Movement Allowance*, *TQ rating*, *Initiative*, *Range*),
- **koszt** (*Movement Point cost*, *cost to enter*),
- **odległość** (*hexes*, *range* jako dystans), **wynik** (*die roll*, *modified die roll*), **modyfikator** (*DRM*),
- **test** (*TQ check*) i **wartość** (*TQ rating*), **stan** (*Depleted*, *Routed*, *Disorganized*) i **znacznik** (*marker*).
Każde z nich ma w glosariuszu osobne pojęcie. Odmiana gramatyczna nie zmienia pojęcia.

## 7. Odsyłacze, liczby, tabele, przykłady
- Numery reguł, liczby, kości (1d10, 2d6), zakresy, ułamki, wartości w tabelach: identyczne z oryginałem.
- Odsyłacz wskazuje ten sam przepis. Jeśli w polskim wydaniu numeracja się zmienia, decyzję zapisz w przewodniku.
- Przykład musi być zgodny z przepisem **i** z tabelą. Rozbieżność w oryginale zgłoś (`kb/ambiguities.yaml`) i nie poprawiaj jej po cichu.
- Nazwy na komponentach (żetony, tabele, plansza) zapisuj zgodnie z decyzją z glosariusza (`notation.component_text`).

## 8. Niejasności, errata, wydania
- Niejasności autora **nie rozstrzygasz** w tekście przepisu i nie dopisujesz reguły. Tłumaczysz tak samo niejednoznacznie,
  a wątpliwość rejestrujesz osobno (plik propozycji → `kb/ambiguities.yaml`). Za zgodą właściciela możesz dodać notatkę tłumacza.
- Erraty i późniejsze wydania: przekład dotyczy **wskazanego wydania**. Zmian z erraty lub nowszego wydania nie wprowadzasz
  po cichu. Albo tłumaczysz nowe wydanie, albo oznaczasz poprawkę jawnie (makro lub ramka z przewodnika) ze źródłem
  w `kb/changes.yaml`.

## 9. Mechaniczna kontrola wstępna
`wgu check fidelity <źródło z markerami> <pliki .tex>` porównuje każdy segment (`%@ KLUCZ`): liczby, odsyłacze,
sygnały zakazu, obowiązku, uprawnienia, wyjątku i warunku oraz pokrycie terminów. To **wskazówki** dla weryfikatora,
nie werdykt: zgodna liczba słów „musi” nie dowodzi zgodności znaczenia, a rozbieżność bywa uprawniona.
